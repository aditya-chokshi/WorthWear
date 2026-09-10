"""Validated data models for Worthwear product analyses."""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Literal

Recommendation = Literal["buy", "skip"]


@dataclass(frozen=True)
class ProductAnalysis:
    category: str
    estimated_material: str
    durability_score: int
    repairability_score: int
    versatility_score: int
    estimated_lifespan_years: float
    cost_per_use: float | None
    confidence_note: str
    recommendation: Recommendation
    reasoning: str
    product_name: str | None = None
    price: float | None = None
    analyzed_at: str | None = None
    id: int | None = None

    def __post_init__(self) -> None:
        for field_name in (
            "durability_score",
            "repairability_score",
            "versatility_score",
        ):
            score = getattr(self, field_name)
            if not 1 <= score <= 10:
                raise ValueError(f"{field_name} must be between 1 and 10")

        if self.estimated_lifespan_years < 0:
            raise ValueError("estimated_lifespan_years cannot be negative")
        if self.estimated_lifespan_years == 0 and self.category != "unclear":
            raise ValueError("estimated_lifespan_years must be positive")
        if self.price is not None and self.price < 0:
            raise ValueError("price cannot be negative")
        if self.cost_per_use is not None and self.cost_per_use < 0:
            raise ValueError("cost_per_use cannot be negative")

    @property
    def average_score(self) -> float:
        return round(
            (
                self.durability_score
                + self.repairability_score
                + self.versatility_score
            )
            / 3,
            1,
        )

    @property
    def timestamp(self) -> str:
        return self.analyzed_at or datetime.now(timezone.utc).isoformat()


def product_analysis_from_dict(
    data: dict[str, Any],
    *,
    product_name: str | None = None,
    price: float | None = None,
) -> ProductAnalysis:
    """Convert and validate a Gemini response dictionary.

    Args:
        data: Parsed JSON containing the required analysis fields.
        product_name: Optional name entered by the user.
        price: Optional price entered by the user.

    Raises:
        ValueError: If fields are missing, have the wrong type, or are out of range.
    """
    required_fields = {
        "category",
        "estimated_material",
        "durability_score",
        "repairability_score",
        "versatility_score",
        "estimated_lifespan_years",
        "confidence_note",
        "cost_per_use",
        "recommendation",
        "reasoning",
    }
    missing_fields = required_fields - data.keys()
    if missing_fields:
        missing = ", ".join(sorted(missing_fields))
        raise ValueError(f"Analysis is missing required fields: {missing}")

    for field_name in (
        "durability_score",
        "repairability_score",
        "versatility_score",
    ):
        score = data[field_name]
        if isinstance(score, bool) or not isinstance(score, int):
            raise ValueError(f"{field_name} must be an integer")
        if not 1 <= score <= 10:
            raise ValueError(f"{field_name} must be between 1 and 10")

    lifespan = data["estimated_lifespan_years"]
    if isinstance(lifespan, bool) or not isinstance(lifespan, (int, float)):
        raise ValueError("estimated_lifespan_years must be a number")

    cost_per_use = data["cost_per_use"]
    if cost_per_use is not None and (
        isinstance(cost_per_use, bool) or not isinstance(cost_per_use, (int, float))
    ):
        raise ValueError("cost_per_use must be a number or null")

    if data["recommendation"] not in ("buy", "skip"):
        raise ValueError('recommendation must be either "buy" or "skip"')

    for field_name in ("category", "estimated_material", "confidence_note", "reasoning"):
        if not isinstance(data[field_name], str) or not data[field_name].strip():
            raise ValueError(f"{field_name} must be a non-empty string")

    return ProductAnalysis(
        category=data["category"],
        estimated_material=data["estimated_material"],
        durability_score=data["durability_score"],
        repairability_score=data["repairability_score"],
        versatility_score=data["versatility_score"],
        estimated_lifespan_years=float(lifespan),
        cost_per_use=(None if cost_per_use is None else float(cost_per_use)),
        confidence_note=data["confidence_note"],
        recommendation=data["recommendation"],
        reasoning=data["reasoning"],
        product_name=product_name,
        price=price,
    )
