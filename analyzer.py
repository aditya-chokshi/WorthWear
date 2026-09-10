"""Gemini-powered product photo analysis for Worthwear."""

import json
import re
from typing import Any

from PIL import Image
import google.generativeai as genai

from config import GEMINI_API_KEY, MODEL_NAME
from models import product_analysis_from_dict


ANALYSIS_PROMPT = """
You are Worthwear, a careful clothing and product-buying advisor. Analyze the
provided product photo and return ONLY valid JSON. Do not use markdown fences,
do not add a preamble, and do not add any text before or after the JSON object.

The optional product name is: {product_name}
The optional product price is: {price}

Return exactly this schema:
{{
  "category": string,
  "estimated_material": string,
  "durability_score": integer 1-10,
  "repairability_score": integer 1-10,
  "versatility_score": integer 1-10,
  "estimated_lifespan_years": float,
  "confidence_note": string,
  "cost_per_use": float or null,
  "recommendation": "buy" or "skip",
  "reasoning": string
}}

The confidence_note must be a short caveat explaining how confident you are
because this estimate is based on a photo alone. If a price was provided,
estimate realistic uses per year and compute cost_per_use as price divided by
(estimated_lifespan_years * estimated_uses_per_year). If no price was provided,
cost_per_use must be null. The reasoning must be 2-3 sentences explaining the
recommendation.

If the image is unclear, not a product photo, or does not provide enough
evidence for a responsible assessment, return category "unclear", use
recommendation "skip", and explain in the reasoning why the image cannot
support a reliable assessment. Do not invent specific material or construction
details in that case. Scores must still be integers from 1 to 10 because they
are required by the schema, and should reflect uncertainty rather than claimed
product quality.
""".strip()


class AnalysisError(RuntimeError):
    """User-facing error raised when Gemini analysis cannot be completed."""


def _clean_json_response(response_text: str) -> str:
    """Extract a likely JSON object after removing common model wrappers."""
    cleaned = response_text.strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start == -1 or end <= start:
        raise ValueError("The model response did not contain a JSON object")
    return cleaned[start : end + 1]


def _parse_json_response(response_text: str) -> dict[str, Any]:
    """Parse raw model text, retrying once after stripping common wrappers."""
    parse_errors: list[str] = []
    candidates = [response_text.strip()]
    try:
        candidates.append(_clean_json_response(response_text))
    except ValueError as error:
        parse_errors.append(str(error))

    for candidate in candidates:
        try:
            parsed = json.loads(candidate)
        except (json.JSONDecodeError, ValueError) as error:
            parse_errors.append(str(error))
            continue
        if not isinstance(parsed, dict):
            parse_errors.append("The model response JSON was not an object")
            continue
        return parsed
    raise ValueError(f"Gemini returned invalid JSON: {parse_errors[-1]}")


def analyze_product(
    image: Image.Image,
    product_name: str,
    price: float | None,
) -> dict[str, Any]:
    """Analyze a product image with Gemini and return validated JSON data.

    Args:
        image: PIL image containing the product to evaluate.
        product_name: Optional product name supplied by the user.
        price: Optional product price used for cost-per-use estimation.

    Raises:
        AnalysisError: If configuration, the Gemini API, JSON parsing, or data
            validation fails with an error suitable for display in Streamlit.
    """
    if not GEMINI_API_KEY:
        raise AnalysisError(
            "Gemini is not configured. Add GEMINI_API_KEY to your .env file."
        )
    if price is not None and price < 0:
        raise AnalysisError("Product price cannot be negative.")

    try:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel(MODEL_NAME)
        prompt = ANALYSIS_PROMPT.format(
            product_name=product_name or "not provided",
            price="not provided" if price is None else price,
        )
        response = model.generate_content([prompt, image])
        raw_data = _parse_json_response(response.text)
        product_analysis_from_dict(raw_data, product_name=product_name, price=price)
        return raw_data
    except AnalysisError:
        raise
    except (ValueError, TypeError) as error:
        raise AnalysisError(f"Gemini returned an unusable analysis: {error}") from error
    except Exception as error:
        detail = str(error).strip()
        if "429" in detail or "ResourceExhausted" in detail or "quota" in detail.lower():
            raise AnalysisError(
                "Gemini quota has been exceeded. Wait for the quota to reset or "
                "check your Google AI Studio plan and billing details."
            ) from error
        if len(detail) > 300:
            detail = f"{detail[:297]}..."
        error_detail = f" {type(error).__name__}: {detail}" if detail else ""
        raise AnalysisError(
            "Gemini could not analyze this image right now. Please check your "
            f"connection, API key, model availability, and quota.{error_detail}"
        ) from error
