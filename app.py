"""Streamlit entrypoint for the Worthwear shopping companion."""

from io import BytesIO
from pathlib import Path
from uuid import uuid4

from PIL import Image
import streamlit as st

from analyzer import AnalysisError, analyze_product
from db import get_all_analyses, get_summary_stats, init_db, save_analysis
from models import ProductAnalysis, product_analysis_from_dict


UPLOADS_DIR = Path(__file__).resolve().parent / "uploads"
init_db()


def _parse_price(price_text: str) -> float | None:
    """Convert optional price text into a non-negative number."""
    if not price_text.strip():
        return None
    try:
        price = float(price_text)
    except ValueError as error:
        raise ValueError("Enter a valid number for the product price.") from error
    if price < 0:
        raise ValueError("Product price cannot be negative.")
    return price


def _save_uploaded_image(uploaded_image: object) -> tuple[Path, bytes]:
    """Save an uploaded image under `uploads` and return its path and bytes."""
    image_bytes = uploaded_image.getvalue()  # type: ignore[attr-defined]
    suffix = Path(uploaded_image.name).suffix.lower()  # type: ignore[attr-defined]
    if suffix not in {".jpg", ".jpeg", ".png"}:
        suffix = ".png"
    UPLOADS_DIR.mkdir(exist_ok=True)
    image_path = UPLOADS_DIR / f"{uuid4().hex}{suffix}"
    image_path.write_bytes(image_bytes)
    return image_path, image_bytes


def _display_analysis(analysis: ProductAnalysis) -> None:
    """Render a saved product analysis as a score card."""
    st.subheader("Analysis result")
    score_columns = st.columns(4)
    score_columns[0].metric("Durability", f"{analysis.durability_score}/10")
    score_columns[1].metric("Repairability", f"{analysis.repairability_score}/10")
    score_columns[2].metric("Versatility", f"{analysis.versatility_score}/10")
    lifespan = (
        "Unknown"
        if analysis.estimated_lifespan_years == 0
        else f"{analysis.estimated_lifespan_years:g} years"
    )
    score_columns[3].metric("Lifespan", lifespan)

    if analysis.recommendation == "buy":
        st.success("Recommendation: BUY")
    else:
        st.error("Recommendation: SKIP")

    st.write(analysis.reasoning)
    if analysis.cost_per_use is None:
        st.metric("Estimated cost per use", "N/A")
    else:
        st.metric("Estimated cost per use", f"{analysis.cost_per_use:.2f}")
    st.caption(f"AI-estimated from the product photo: {analysis.confidence_note}")


def _render_wardrobe_log() -> None:
    """Render summary metrics, history table, and cost-per-use chart."""
    rows = get_all_analyses()
    stats = get_summary_stats()
    buy_skip = stats["count_buy_vs_skip"]
    average_cost = stats["avg_cost_per_use"]

    metric_columns = st.columns(3)
    metric_columns[0].metric("Items analyzed", stats["total_items_analyzed"])
    metric_columns[1].metric(
        "Avg. cost per use",
        "N/A" if average_cost is None else f"{average_cost:.2f}",
    )
    metric_columns[2].metric("Buy vs skip", f"{buy_skip['buy']} / {buy_skip['skip']}")

    st.subheader("Analysis history")
    if not rows:
        st.info("Your wardrobe log is empty. Analyze a product to start building it.")
        return

    st.dataframe(rows, use_container_width=True, hide_index=True)

    chart_rows = [
        {"timestamp": row["timestamp"], "cost_per_use": row["cost_per_use"]}
        for row in reversed(rows)
        if row["cost_per_use"] is not None
    ]
    if chart_rows:
        st.subheader("Cost per use over time")
        st.line_chart(chart_rows, x="timestamp", y="cost_per_use")
    else:
        st.info("Cost-per-use history will appear when a price is provided.")


def main() -> None:
    """Render the Analyze and Wardrobe Log tabs."""
    st.set_page_config(page_title="Worthwear", layout="wide")
    st.title("Worthwear")
    st.write("Buy fewer. Choose better.")

    analyze_tab, wardrobe_tab = st.tabs(["Analyze", "Wardrobe Log"])
    with analyze_tab:
        uploaded_image = st.file_uploader(
            "Upload a product photo",
            type=["jpg", "jpeg", "png"],
        )
        if uploaded_image is not None:
            st.image(uploaded_image, caption="Uploaded product photo")

        price_text = st.text_input("Product price (optional)")
        product_name = st.text_input("Product name (optional)")

        if st.button("Analyze", disabled=uploaded_image is None):
            try:
                price = _parse_price(price_text)
                image_path, image_bytes = _save_uploaded_image(uploaded_image)
                with Image.open(BytesIO(image_bytes)) as image:
                    raw_result = analyze_product(image, product_name, price)
                analysis = product_analysis_from_dict(
                    raw_result,
                    product_name=product_name or None,
                    price=price,
                )
                save_analysis(analysis, str(image_path))
                st.session_state["last_analysis"] = analysis
            except (AnalysisError, ValueError, OSError) as error:
                st.error(str(error))

        if "last_analysis" in st.session_state:
            _display_analysis(st.session_state["last_analysis"])

    with wardrobe_tab:
        _render_wardrobe_log()


if __name__ == "__main__":
    main()
