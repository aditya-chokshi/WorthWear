"""SQLite persistence for Worthwear product analyses."""

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from collections.abc import Iterator
from typing import Any

from models import ProductAnalysis


DATABASE_PATH = Path(__file__).resolve().parent / "worthwear.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS analyses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    product_name TEXT,
    price REAL,
    category TEXT NOT NULL,
    durability_score INTEGER NOT NULL CHECK (durability_score BETWEEN 1 AND 10),
    repairability_score INTEGER NOT NULL CHECK (repairability_score BETWEEN 1 AND 10),
    versatility_score INTEGER NOT NULL CHECK (versatility_score BETWEEN 1 AND 10),
    estimated_lifespan_years REAL NOT NULL,
    cost_per_use REAL,
    recommendation TEXT NOT NULL CHECK (recommendation IN ('buy', 'skip')),
    reasoning TEXT NOT NULL,
    image_path TEXT NOT NULL
)
"""


@contextmanager
def _connection() -> Iterator[sqlite3.Connection]:
    """Open a database connection and always close it after use."""
    connection = sqlite3.connect(DATABASE_PATH)
    try:
        yield connection
        connection.commit()
    finally:
        connection.close()


def init_db() -> None:
    """Create the local SQLite database and analyses table if needed."""
    with _connection() as connection:
        connection.execute(SCHEMA)


def save_analysis(analysis: ProductAnalysis, image_path: str) -> int:
    """Save one product analysis and return its generated database ID."""
    with _connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO analyses (
                timestamp, product_name, price, category,
                durability_score, repairability_score, versatility_score,
                estimated_lifespan_years, cost_per_use, recommendation,
                reasoning, image_path
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                analysis.timestamp,
                analysis.product_name,
                analysis.price,
                analysis.category,
                analysis.durability_score,
                analysis.repairability_score,
                analysis.versatility_score,
                analysis.estimated_lifespan_years,
                analysis.cost_per_use,
                analysis.recommendation,
                analysis.reasoning,
                image_path,
            ),
        )
        return int(cursor.lastrowid)


def get_all_analyses() -> list[dict[str, Any]]:
    """Return all saved analyses as dictionaries, newest first."""
    with _connection() as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            "SELECT * FROM analyses ORDER BY timestamp DESC, id DESC"
        ).fetchall()
    return [dict(row) for row in rows]


def get_summary_stats() -> dict[str, Any]:
    """Return aggregate item counts, cost-per-use, and durability statistics."""
    with _connection() as connection:
        summary = connection.execute(
            """
            SELECT
                COUNT(*) AS total_items_analyzed,
                AVG(cost_per_use) AS avg_cost_per_use,
                AVG(durability_score) AS avg_durability_score,
                SUM(CASE WHEN recommendation = 'buy' THEN 1 ELSE 0 END) AS buy_count,
                SUM(CASE WHEN recommendation = 'skip' THEN 1 ELSE 0 END) AS skip_count
            FROM analyses
            """
        ).fetchone()

    return {
        "total_items_analyzed": summary[0] or 0,
        "avg_cost_per_use": summary[1],
        "count_buy_vs_skip": {
            "buy": summary[3] or 0,
            "skip": summary[4] or 0,
        },
        "avg_durability_score": summary[2],
    }
