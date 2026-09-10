"""Focused tests for Worthwear's model and SQLite persistence layers."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import db
from models import ProductAnalysis, product_analysis_from_dict


def make_analysis() -> ProductAnalysis:
    """Create a valid analysis fixture for database tests."""
    return ProductAnalysis(
        category="jacket",
        estimated_material="cotton blend",
        durability_score=8,
        repairability_score=7,
        versatility_score=9,
        estimated_lifespan_years=5.0,
        cost_per_use=2.4,
        confidence_note="AI estimate based on photo alone.",
        recommendation="buy",
        reasoning="It appears durable and versatile. Repeated use could justify the price.",
        product_name="Test jacket",
        price=120.0,
    )


class WorthwearCoreTests(unittest.TestCase):
    """Verify typed analysis conversion and SQLite persistence."""

    def test_analysis_round_trip_and_summary(self) -> None:
        """Save an analysis and verify retrieval and aggregate statistics."""
        with tempfile.TemporaryDirectory() as directory:
            database_path = Path(directory) / "worthwear.db"
            with patch.object(db, "DATABASE_PATH", database_path):
                db.init_db()
                record_id = db.save_analysis(make_analysis(), "uploads/test.png")
                rows = db.get_all_analyses()
                summary = db.get_summary_stats()

        self.assertEqual(record_id, 1)
        self.assertEqual(rows[0]["image_path"], "uploads/test.png")
        self.assertEqual(summary["total_items_analyzed"], 1)
        self.assertEqual(summary["count_buy_vs_skip"], {"buy": 1, "skip": 0})
        self.assertEqual(summary["avg_cost_per_use"], 2.4)

    def test_raw_analysis_conversion_rejects_invalid_score(self) -> None:
        """Reject a model response with a score outside the allowed range."""
        raw_data = {
            "category": "jacket",
            "estimated_material": "cotton",
            "durability_score": 11,
            "repairability_score": 7,
            "versatility_score": 9,
            "estimated_lifespan_years": 5.0,
            "confidence_note": "Low confidence.",
            "cost_per_use": None,
            "recommendation": "skip",
            "reasoning": "The image does not provide enough evidence. Skip this purchase.",
        }

        with self.assertRaises(ValueError):
            product_analysis_from_dict(raw_data)


if __name__ == "__main__":
    unittest.main()
