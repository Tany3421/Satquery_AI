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

import hashlib
import os
import secrets

DB_PATH = Path(__file__).parent / "satquery.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    salt TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS images (
    id TEXT PRIMARY KEY,
    filename TEXT NOT NULL,
    uploaded_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS queries (
    id TEXT PRIMARY KEY,
    user_id TEXT,
    image_id TEXT NOT NULL,
    image_url TEXT NOT NULL,
    mode TEXT NOT NULL,
    data_source TEXT DEFAULT 'sentinel2',
    engine_used TEXT DEFAULT 'Gemini API',
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
    coordinates_json TEXT,
    feature_masks_json TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (image_id) REFERENCES images(id),
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS comparisons (
    id TEXT PRIMARY KEY,
    user_id TEXT,
    image_before_url TEXT NOT NULL,
    image_after_url TEXT NOT NULL,
    label_before TEXT,
    label_after TEXT,
    narrative TEXT NOT NULL,
    changes_json TEXT NOT NULL,
    anomaly_flagged INTEGER NOT NULL,
    confidence INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
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


def hash_password(password: str, salt: str = None) -> tuple[str, str]:
    if not salt:
        salt = secrets.token_hex(16)
    key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100000)
    return key.hex(), salt


def verify_password(password: str, password_hash: str, salt: str) -> bool:
    key, _ = hash_password(password, salt)
    return secrets.compare_digest(key, password_hash)


def init_db():
    with get_conn() as conn:
        conn.executescript(SCHEMA)
        # Migration for existing databases
        columns = [row["name"] for row in conn.execute("PRAGMA table_info(queries)").fetchall()]
        if "data_source" not in columns:
            conn.execute("ALTER TABLE queries ADD COLUMN data_source TEXT DEFAULT 'sentinel2'")
        if "engine_used" not in columns:
            conn.execute("ALTER TABLE queries ADD COLUMN engine_used TEXT DEFAULT 'Gemini API'")
        if "coordinates_json" not in columns:
            conn.execute("ALTER TABLE queries ADD COLUMN coordinates_json TEXT")
        if "feature_masks_json" not in columns:
            conn.execute("ALTER TABLE queries ADD COLUMN feature_masks_json TEXT")
        if "user_id" not in columns:
            conn.execute("ALTER TABLE queries ADD COLUMN user_id TEXT")


def create_user(user_id: str, username: str, email: str, password: str, created_at: str) -> dict:
    pwd_hash, salt = hash_password(password)
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO users (id, username, email, password_hash, salt, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (user_id, username.lower().strip(), email.lower().strip(), pwd_hash, salt, created_at),
        )
    return {"id": user_id, "username": username, "email": email, "created_at": created_at}


def get_user_by_username(username: str) -> dict | None:
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM users WHERE LOWER(username) = ?", (username.lower().strip(),)).fetchone()
        return dict(row) if row else None


def get_user_by_email(email: str) -> dict | None:
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM users WHERE LOWER(email) = ?", (email.lower().strip(),)).fetchone()
        return dict(row) if row else None


def get_user_by_id(user_id: str) -> dict | None:
    with get_conn() as conn:
        row = conn.execute("SELECT id, username, email, created_at FROM users WHERE id = ?", (user_id,)).fetchone()
        return dict(row) if row else None


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
                id, user_id, image_id, image_url, mode, data_source, engine_used, question, answer,
                land_cover_json, detected_features_json, evidence_json,
                confidence, uncertainty_reason, cloud_cover_percent,
                image_quality, region_note, coordinates_json, feature_masks_json, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record["id"],
                record.get("user_id"),
                record["image_id"],
                record["image_url"],
                record["mode"],
                record.get("data_source", "sentinel2"),
                record.get("engine_used", "Gemini API"),
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
                json.dumps(record.get("coordinates")) if record.get("coordinates") else None,
                json.dumps(record.get("feature_masks")) if record.get("feature_masks") else None,
                record["created_at"],
            ),
        )


def _row_to_query_dict(row: sqlite3.Row) -> dict:
    row_keys = row.keys()
    coords = None
    if "coordinates_json" in row_keys and row["coordinates_json"]:
        try:
            coords = json.loads(row["coordinates_json"])
        except Exception:
            coords = None

    masks = None
    if "feature_masks_json" in row_keys and row["feature_masks_json"]:
        try:
            masks = json.loads(row["feature_masks_json"])
        except Exception:
            masks = None

    return {
        "id": row["id"],
        "user_id": row["user_id"] if "user_id" in row_keys else None,
        "image_id": row["image_id"],
        "image_url": row["image_url"],
        "mode": row["mode"],
        "data_source": row["data_source"] if "data_source" in row_keys else "sentinel2",
        "engine_used": row["engine_used"] if "engine_used" in row_keys else "Gemini API",
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
        "coordinates": coords,
        "feature_masks": masks,
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
