"""
database/db.py
Minimal SQLite persistence for SatQuery AI.

Kept intentionally simple (stdlib sqlite3, no ORM) so it's easy to read and
easy to swap for Postgres/MongoDB later — every function here is the seam
you'd replace. The schema mirrors the brief's own Users / Images / Queries
tables.
"""

import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path

DB_PATH = Path(__file__).parent / "satquery.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS images (
    id TEXT PRIMARY KEY,
    filename TEXT NOT NULL,
    uploaded_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS queries (
    id TEXT PRIMARY KEY,
    image_id TEXT NOT NULL,
    image_url TEXT NOT NULL,
    mode TEXT NOT NULL,
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    land_cover_json TEXT NOT NULL,
    detected_features_json TEXT NOT NULL,
    evidence_json TEXT NOT NULL,
    confidence INTEGER NOT NULL,
    uncertainty_reason TEXT,
    cloud_cover_percent INTEGER,
    image_quality TEXT,
    region_note TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (image_id) REFERENCES images(id)
);

CREATE TABLE IF NOT EXISTS comparisons (
    id TEXT PRIMARY KEY,
    image_before_url TEXT NOT NULL,
    image_after_url TEXT NOT NULL,
    label_before TEXT,
    label_after TEXT,
    narrative TEXT NOT NULL,
    changes_json TEXT NOT NULL,
    anomaly_flagged INTEGER NOT NULL,
    confidence INTEGER NOT NULL,
    created_at TEXT NOT NULL
);

-- EXTEND: add a `users` table + a `user_id` foreign key on queries/comparisons
-- once you build auth.
"""


@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with get_conn() as conn:
        conn.executescript(SCHEMA)


def insert_image(image_id: str, filename: str, uploaded_at: str):
    with get_conn() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO images (id, filename, uploaded_at) VALUES (?, ?, ?)",
            (image_id, filename, uploaded_at),
        )


def insert_query(record: dict):
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO queries (
                id, image_id, image_url, mode, question, answer,
                land_cover_json, detected_features_json, evidence_json,
                confidence, uncertainty_reason, cloud_cover_percent,
                image_quality, region_note, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record["id"],
                record["image_id"],
                record["image_url"],
                record["mode"],
                record["question"],
                record["answer"],
                json.dumps(record["land_cover"]),
                json.dumps(record["detected_features"]),
                json.dumps(record["evidence"]),
                record["confidence"],
                record.get("uncertainty_reason"),
                record.get("cloud_cover_percent"),
                record.get("image_quality"),
                record.get("region_note"),
                record["created_at"],
            ),
        )


def _row_to_query_dict(row: sqlite3.Row) -> dict:
    return {
        "id": row["id"],
        "image_id": row["image_id"],
        "image_url": row["image_url"],
        "mode": row["mode"],
        "question": row["question"],
        "answer": row["answer"],
        "land_cover": json.loads(row["land_cover_json"]),
        "detected_features": json.loads(row["detected_features_json"]),
        "evidence": json.loads(row["evidence_json"]),
        "confidence": row["confidence"],
        "uncertainty_reason": row["uncertainty_reason"],
        "cloud_cover_percent": row["cloud_cover_percent"],
        "image_quality": row["image_quality"],
        "region_note": row["region_note"],
        "created_at": row["created_at"],
    }


def get_history(limit: int = 20) -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM queries ORDER BY created_at DESC LIMIT ?", (limit,)
        ).fetchall()
        return [_row_to_query_dict(r) for r in rows]


def get_query(query_id: str) -> dict | None:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM queries WHERE id = ?", (query_id,)
        ).fetchone()
        return _row_to_query_dict(row) if row else None


def clear_history():
    with get_conn() as conn:
        conn.execute("DELETE FROM queries")
        conn.execute("DELETE FROM comparisons")


def insert_comparison(record: dict):
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO comparisons (
                id, image_before_url, image_after_url, label_before, label_after,
                narrative, changes_json, anomaly_flagged, confidence, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record["id"],
                record["image_before_url"],
                record["image_after_url"],
                record.get("label_before"),
                record.get("label_after"),
                record["narrative"],
                json.dumps(record["changes"]),
                int(record["anomaly_flagged"]),
                record["confidence"],
                record["created_at"],
            ),
        )


def get_comparisons(limit: int = 10) -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM comparisons ORDER BY created_at DESC LIMIT ?", (limit,)
        ).fetchall()
        return [
            {
                "id": r["id"],
                "image_before_url": r["image_before_url"],
                "image_after_url": r["image_after_url"],
                "label_before": r["label_before"],
                "label_after": r["label_after"],
                "narrative": r["narrative"],
                "changes": json.loads(r["changes_json"]),
                "anomaly_flagged": bool(r["anomaly_flagged"]),
                "confidence": r["confidence"],
                "created_at": r["created_at"],
            }
            for r in rows
        ]
