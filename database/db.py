"""
database/db.py
Production MongoDB persistence for SatQuery AI (MongoDB Compass compatible).

Stores all application state in a MongoDB database (default: 'satquery' at mongodb://localhost:27017/):
- users: User credentials, roles, reset tokens
- images: Raster and GeoTIFF upload metadata
- queries: Single-image analysis, VQA, land cover, masks, and auditable traces
- comparisons: Bi-temporal change comparisons, transition metrics, and CDVQA
- crossmodals: Co-registered Optical + SAR joint feature extractions

Account Isolation:
- Every record stores `user_id`.
- Queries, comparisons, and crossmodal histories are partitioned specifically by account.
"""

import hashlib
import json
import os
import secrets
import time
from typing import Any, Dict, List, Optional

# Optional fallback to sqlite3 if MongoDB daemon is unavailable
import sqlite3
from pathlib import Path

MONGO_URI = os.getenv("MONGO_URI") or os.getenv("MONGODB_URI") or "mongodb://localhost:27017/"
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "satquery")

_mongo_client = None
_mongo_db = None
_using_mongodb = False
_mongo_last_check = 0
_MONGO_RETRY_INTERVAL = 30  # Cooldown in seconds before re-checking if MongoDB is running


def _get_mongo():
    global _mongo_client, _mongo_db, _using_mongodb, _mongo_last_check
    if _mongo_db is not None:
        return _mongo_db

    now = time.time()
    if now - _mongo_last_check < _MONGO_RETRY_INTERVAL:
        return None

    _mongo_last_check = now
    try:
        import pymongo
        client = pymongo.MongoClient(MONGO_URI, serverSelectionTimeoutMS=800, connectTimeoutMS=800)
        # Verify server connection
        client.admin.command("ping")
        db = client[MONGO_DB_NAME]

        # Setup collection indexes
        db.users.create_index("username", unique=True)
        db.users.create_index("email", unique=True)
        db.queries.create_index([("user_id", 1), ("created_at", -1)])
        db.comparisons.create_index([("user_id", 1), ("created_at", -1)])
        db.crossmodals.create_index([("user_id", 1), ("created_at", -1)])

        _mongo_client = client
        _mongo_db = db
        _using_mongodb = True
        return _mongo_db
    except Exception:
        _using_mongodb = False
        return None


# SQLite fallback configuration if MongoDB service is stopped
SQLITE_PATH = Path(__file__).parent / "satquery.db"


def hash_password(password: str, salt: str = None) -> tuple[str, str]:
    if not salt:
        salt = secrets.token_hex(16)
    key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100000)
    return key.hex(), salt


def verify_password(password: str, password_hash: str, salt: str) -> bool:
    key, _ = hash_password(password, salt)
    return secrets.compare_digest(key, password_hash)


def init_db():
    """Initializes MongoDB database and performs migration from SQLite if needed."""
    mdb = _get_mongo()
    if mdb is not None:
        # Migrate existing SQLite records if SQLite file exists
        if SQLITE_PATH.exists():
            _migrate_sqlite_to_mongodb(mdb)
        return

    # Fallback to SQLite if MongoDB daemon is unreachable
    _init_sqlite_fallback()


def _migrate_sqlite_to_mongodb(mdb):
    """Seamless one-time migration from SQLite to MongoDB Compass database."""
    try:
        s_conn = sqlite3.connect(SQLITE_PATH)
        s_conn.row_factory = sqlite3.Row

        # Migrate users
        users = [dict(r) for r in s_conn.execute("SELECT * FROM users").fetchall()]
        for u in users:
            mdb.users.update_one({"id": u["id"]}, {"$set": u}, upsert=True)

        # Migrate queries
        queries = [dict(r) for r in s_conn.execute("SELECT * FROM queries").fetchall()]
        for q in queries:
            for f in ["land_cover_json", "detected_features_json", "evidence_json", "coordinates_json", "feature_masks_json", "auditable_trace_json"]:
                if f in q and q[f]:
                    try:
                        q[f.replace("_json", "")] = json.loads(q[f])
                    except Exception:
                        pass
                    del q[f]
            mdb.queries.update_one({"id": q["id"]}, {"$set": q}, upsert=True)

        # Migrate comparisons
        comps = [dict(r) for r in s_conn.execute("SELECT * FROM comparisons").fetchall()]
        for c in comps:
            if "changes_json" in c and c["changes_json"]:
                try:
                    c["changes"] = json.loads(c["changes_json"])
                except Exception:
                    pass
                del c["changes_json"]
            mdb.comparisons.update_one({"id": c["id"]}, {"$set": c}, upsert=True)

        # Migrate crossmodals
        crosses = [dict(r) for r in s_conn.execute("SELECT * FROM crossmodals").fetchall()]
        for cr in crosses:
            for f in ["land_cover_json", "detected_features_json", "evidence_json", "coordinates_json", "feature_masks_json", "optical_meta_json", "sar_meta_json"]:
                if f in cr and cr[f]:
                    try:
                        cr[f.replace("_json", "")] = json.loads(cr[f])
                    except Exception:
                        pass
                    del cr[f]
            mdb.crossmodals.update_one({"id": cr["id"]}, {"$set": cr}, upsert=True)

        s_conn.close()
    except Exception:
        pass


def _init_sqlite_fallback():
    conn = sqlite3.connect(SQLITE_PATH)
    conn.row_factory = sqlite3.Row
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY, username TEXT UNIQUE NOT NULL, email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL, salt TEXT NOT NULL, role TEXT DEFAULT 'researcher',
        reset_token TEXT, reset_expiry INTEGER, created_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS images (
        id TEXT PRIMARY KEY, filename TEXT NOT NULL, uploaded_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS queries (
        id TEXT PRIMARY KEY, user_id TEXT, image_id TEXT NOT NULL, image_url TEXT NOT NULL,
        mode TEXT NOT NULL, data_source TEXT DEFAULT 'sentinel2', engine_used TEXT DEFAULT 'Gemini API',
        question TEXT NOT NULL, answer TEXT NOT NULL, land_cover_json TEXT NOT NULL,
        detected_features_json TEXT NOT NULL, evidence_json TEXT NOT NULL,
        confidence INTEGER NOT NULL, uncertainty_reason TEXT, cloud_cover_percent INTEGER,
        image_quality TEXT, region_note TEXT, coordinates_json TEXT, feature_masks_json TEXT,
        auditable_trace_json TEXT, created_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS comparisons (
        id TEXT PRIMARY KEY, user_id TEXT, image_before_url TEXT NOT NULL, image_after_url TEXT NOT NULL,
        label_before TEXT, label_after TEXT, narrative TEXT NOT NULL, changes_json TEXT NOT NULL,
        anomaly_flagged INTEGER NOT NULL, confidence INTEGER NOT NULL, created_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS crossmodals (
        id TEXT PRIMARY KEY, user_id TEXT, image_optical_url TEXT NOT NULL, image_sar_url TEXT NOT NULL,
        question TEXT NOT NULL, answer TEXT NOT NULL, optical_insights TEXT, sar_insights TEXT,
        cloud_penetration_noted INTEGER DEFAULT 0, land_cover_json TEXT NOT NULL,
        detected_features_json TEXT NOT NULL, evidence_json TEXT NOT NULL, confidence INTEGER NOT NULL,
        uncertainty_reason TEXT, coordinates_json TEXT, feature_masks_json TEXT,
        optical_meta_json TEXT, sar_meta_json TEXT, created_at TEXT NOT NULL
    );
    """)
    conn.commit()
    conn.close()


# Ensure SQLite schema always exists immediately as reliable fallback
try:
    _init_sqlite_fallback()
except Exception:
    pass
# ---------------------------------------------------------------------------

def create_user(user_id: str, username: str, email: str, password: str, created_at: str, role: str = "researcher") -> dict:
    pwd_hash, salt = hash_password(password)
    user_doc = {
        "id": user_id,
        "username": username.lower().strip(),
        "email": email.lower().strip(),
        "password_hash": pwd_hash,
        "salt": salt,
        "role": role,
        "created_at": created_at,
        "reset_token": None,
        "reset_expiry": None,
    }

    mdb = _get_mongo()
    if mdb is not None:
        mdb.users.insert_one(user_doc)
    else:
        conn = sqlite3.connect(SQLITE_PATH)
        conn.execute(
            "INSERT INTO users (id, username, email, password_hash, salt, role, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (user_id, username.lower().strip(), email.lower().strip(), pwd_hash, salt, role, created_at),
        )
        conn.commit()
        conn.close()

    return {"id": user_id, "username": username, "email": email, "role": role, "created_at": created_at}


def get_user_by_username(username: str) -> Optional[dict]:
    clean = (username or "").lower().strip()
    mdb = _get_mongo()
    if mdb is not None:
        user = mdb.users.find_one({"username": clean}, {"_id": 0})
        return user

    conn = sqlite3.connect(SQLITE_PATH)
    conn.row_factory = sqlite3.Row
    row = conn.execute("SELECT * FROM users WHERE LOWER(username) = ?", (clean,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_user_by_email(email: str) -> Optional[dict]:
    clean = (email or "").lower().strip()
    mdb = _get_mongo()
    if mdb is not None:
        user = mdb.users.find_one({"email": clean}, {"_id": 0})
        return user

    conn = sqlite3.connect(SQLITE_PATH)
    conn.row_factory = sqlite3.Row
    row = conn.execute("SELECT * FROM users WHERE LOWER(email) = ?", (clean,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_user_by_email_or_username(identifier: str) -> Optional[dict]:
    clean = (identifier or "").lower().strip()
    mdb = _get_mongo()
    if mdb is not None:
        user = mdb.users.find_one({"$or": [{"email": clean}, {"username": clean}]}, {"_id": 0})
        return user

    conn = sqlite3.connect(SQLITE_PATH)
    conn.row_factory = sqlite3.Row
    row = conn.execute(
        "SELECT * FROM users WHERE LOWER(email) = ? OR LOWER(username) = ?", (clean, clean)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def get_user_by_id(user_id: str) -> Optional[dict]:
    mdb = _get_mongo()
    if mdb is not None:
        user = mdb.users.find_one({"id": user_id}, {"_id": 0, "password_hash": 0, "salt": 0})
        return user

    conn = sqlite3.connect(SQLITE_PATH)
    conn.row_factory = sqlite3.Row
    row = conn.execute("SELECT id, username, email, role, created_at FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def set_user_reset_token(email: str, token: str, expiry: int) -> Optional[dict]:
    clean_email = (email or "").lower().strip()
    mdb = _get_mongo()
    if mdb is not None:
        user = mdb.users.find_one_and_update(
            {"email": clean_email},
            {"$set": {"reset_token": token, "reset_expiry": expiry}},
            projection={"_id": 0},
        )
        return user

    conn = sqlite3.connect(SQLITE_PATH)
    conn.row_factory = sqlite3.Row
    user = conn.execute("SELECT * FROM users WHERE LOWER(email) = ?", (clean_email,)).fetchone()
    if not user:
        conn.close()
        return None
    conn.execute("UPDATE users SET reset_token = ?, reset_expiry = ? WHERE id = ?", (token, expiry, user["id"]))
    conn.commit()
    conn.close()
    return dict(user)


def get_user_by_reset_token(token: str) -> Optional[dict]:
    now = int(time.time())
    mdb = _get_mongo()
    if mdb is not None:
        user = mdb.users.find_one({"reset_token": token, "reset_expiry": {"$gt": now}}, {"_id": 0})
        return user

    conn = sqlite3.connect(SQLITE_PATH)
    conn.row_factory = sqlite3.Row
    row = conn.execute("SELECT * FROM users WHERE reset_token = ? AND reset_expiry > ?", (token, now)).fetchone()
    conn.close()
    return dict(row) if row else None


def reset_user_password(token: str, new_password: str) -> bool:
    user = get_user_by_reset_token(token)
    if not user:
        return False
    pwd_hash, salt = hash_password(new_password)

    mdb = _get_mongo()
    if mdb is not None:
        mdb.users.update_one(
            {"id": user["id"]},
            {"$set": {"password_hash": pwd_hash, "salt": salt, "reset_token": None, "reset_expiry": None}}
        )
        return True

    conn = sqlite3.connect(SQLITE_PATH)
    conn.execute(
        "UPDATE users SET password_hash = ?, salt = ?, reset_token = NULL, reset_expiry = NULL WHERE id = ?",
        (pwd_hash, salt, user["id"])
    )
    conn.commit()
    conn.close()
    return True


def insert_image(image_id: str, filename: str, uploaded_at: str):
    doc = {"id": image_id, "filename": filename, "uploaded_at": uploaded_at}
    mdb = _get_mongo()
    if mdb is not None:
        mdb.images.update_one({"id": image_id}, {"$set": doc}, upsert=True)
    else:
        conn = sqlite3.connect(SQLITE_PATH)
        conn.execute("INSERT OR IGNORE INTO images (id, filename, uploaded_at) VALUES (?, ?, ?)", (image_id, filename, uploaded_at))
        conn.commit()
        conn.close()


# ---------------------------------------------------------------------------
# Queries (Single Image VQA & Analysis) — Account Specific
# ---------------------------------------------------------------------------

def insert_query(record: dict):
    clean_record = dict(record)
    clean_record.pop("_id", None)

    mdb = _get_mongo()
    if mdb is not None:
        mdb.queries.update_one({"id": clean_record["id"]}, {"$set": clean_record}, upsert=True)
    else:
        conn = sqlite3.connect(SQLITE_PATH)
        conn.execute(
            """
            INSERT OR REPLACE INTO queries (
                id, user_id, image_id, image_url, mode, data_source, engine_used, question, answer,
                land_cover_json, detected_features_json, evidence_json,
                confidence, uncertainty_reason, cloud_cover_percent,
                image_quality, region_note, coordinates_json, feature_masks_json, auditable_trace_json, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                clean_record["id"],
                clean_record.get("user_id"),
                clean_record["image_id"],
                clean_record["image_url"],
                clean_record["mode"],
                clean_record.get("data_source", "sentinel2"),
                clean_record.get("engine_used", "Gemini API"),
                clean_record["question"],
                clean_record["answer"],
                json.dumps(clean_record.get("land_cover", [])),
                json.dumps(clean_record.get("detected_features", [])),
                json.dumps(clean_record.get("evidence", [])),
                clean_record["confidence"],
                clean_record.get("uncertainty_reason"),
                clean_record.get("cloud_cover_percent"),
                clean_record.get("image_quality"),
                clean_record.get("region_note"),
                json.dumps(clean_record.get("coordinates")) if clean_record.get("coordinates") else None,
                json.dumps(clean_record.get("feature_masks")) if clean_record.get("feature_masks") else None,
                json.dumps(clean_record.get("auditable_trace")) if clean_record.get("auditable_trace") else None,
                clean_record["created_at"],
            ),
        )
        conn.commit()
        conn.close()


def get_history(limit: int = 20, user_id: Optional[str] = None) -> List[dict]:
    """Retrieves analysis query history, strictly isolated to the specified user_id if provided."""
    mdb = _get_mongo()
    if mdb is not None:
        query_filter = {"user_id": user_id} if user_id else {}
        cursor = mdb.queries.find(query_filter, {"_id": 0}).sort("created_at", -1).limit(limit)
        return list(cursor)

    # SQLite fallback
    conn = sqlite3.connect(SQLITE_PATH)
    conn.row_factory = sqlite3.Row
    if user_id:
        rows = conn.execute("SELECT * FROM queries WHERE user_id = ? ORDER BY created_at DESC LIMIT ?", (user_id, limit)).fetchall()
    else:
        rows = conn.execute("SELECT * FROM queries ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
    conn.close()

    result = []
    for r in rows:
        r_dict = dict(r)
        for field in ["land_cover_json", "detected_features_json", "evidence_json", "coordinates_json", "feature_masks_json", "auditable_trace_json"]:
            if field in r_dict and r_dict[field]:
                try:
                    r_dict[field.replace("_json", "")] = json.loads(r_dict[field])
                except Exception:
                    pass
                del r_dict[field]
        result.append(r_dict)
    return result


def get_query(query_id: str) -> Optional[dict]:
    mdb = _get_mongo()
    if mdb is not None:
        return mdb.queries.find_one({"id": query_id}, {"_id": 0})

    conn = sqlite3.connect(SQLITE_PATH)
    conn.row_factory = sqlite3.Row
    row = conn.execute("SELECT * FROM queries WHERE id = ?", (query_id,)).fetchone()
    conn.close()
    if not row:
        return None
    r_dict = dict(row)
    for field in ["land_cover_json", "detected_features_json", "evidence_json", "coordinates_json", "feature_masks_json", "auditable_trace_json"]:
        if field in r_dict and r_dict[field]:
            try:
                r_dict[field.replace("_json", "")] = json.loads(r_dict[field])
            except Exception:
                pass
            del r_dict[field]
    return r_dict


def clear_history(user_id: Optional[str] = None):
    """Clears history. If user_id is provided, deletes ONLY that specific account's history."""
    mdb = _get_mongo()
    if mdb is not None:
        query_filter = {"user_id": user_id} if user_id else {}
        mdb.queries.delete_many(query_filter)
        mdb.comparisons.delete_many(query_filter)
        mdb.crossmodals.delete_many(query_filter)
        return

    conn = sqlite3.connect(SQLITE_PATH)
    if user_id:
        conn.execute("DELETE FROM queries WHERE user_id = ?", (user_id,))
        conn.execute("DELETE FROM comparisons WHERE user_id = ?", (user_id,))
        conn.execute("DELETE FROM crossmodals WHERE user_id = ?", (user_id,))
    else:
        conn.execute("DELETE FROM queries")
        conn.execute("DELETE FROM comparisons")
        conn.execute("DELETE FROM crossmodals")
    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# Bi-Temporal Comparisons — Account Specific
# ---------------------------------------------------------------------------

def insert_comparison(record: dict):
    clean_record = dict(record)
    clean_record.pop("_id", None)

    mdb = _get_mongo()
    if mdb is not None:
        mdb.comparisons.update_one({"id": clean_record["id"]}, {"$set": clean_record}, upsert=True)
    else:
        conn = sqlite3.connect(SQLITE_PATH)
        conn.execute(
            """
            INSERT OR REPLACE INTO comparisons (
                id, user_id, image_before_url, image_after_url, label_before, label_after,
                narrative, changes_json, anomaly_flagged, confidence, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                clean_record["id"],
                clean_record.get("user_id"),
                clean_record["image_before_url"],
                clean_record["image_after_url"],
                clean_record.get("label_before"),
                clean_record.get("label_after"),
                clean_record["narrative"],
                json.dumps(clean_record.get("changes", [])),
                int(clean_record.get("anomaly_flagged", False)),
                clean_record["confidence"],
                clean_record["created_at"],
            ),
        )
        conn.commit()
        conn.close()


def get_comparisons(limit: int = 10, user_id: Optional[str] = None) -> List[dict]:
    """Retrieves bi-temporal comparisons, strictly isolated to the specified user_id if provided."""
    mdb = _get_mongo()
    if mdb is not None:
        query_filter = {"user_id": user_id} if user_id else {}
        cursor = mdb.comparisons.find(query_filter, {"_id": 0}).sort("created_at", -1).limit(limit)
        return list(cursor)

    conn = sqlite3.connect(SQLITE_PATH)
    conn.row_factory = sqlite3.Row
    if user_id:
        rows = conn.execute("SELECT * FROM comparisons WHERE user_id = ? ORDER BY created_at DESC LIMIT ?", (user_id, limit)).fetchall()
    else:
        rows = conn.execute("SELECT * FROM comparisons ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
    conn.close()

    result = []
    for r in rows:
        r_dict = dict(r)
        if "changes_json" in r_dict and r_dict["changes_json"]:
            try:
                r_dict["changes"] = json.loads(r_dict["changes_json"])
            except Exception:
                pass
            del r_dict["changes_json"]
        r_dict["anomaly_flagged"] = bool(r_dict.get("anomaly_flagged", 0))
        result.append(r_dict)
    return result


# ---------------------------------------------------------------------------
# Cross-Modal (Optical + SAR) Extractions — Account Specific
# ---------------------------------------------------------------------------

def insert_crossmodal(record: dict):
    clean_record = dict(record)
    clean_record.pop("_id", None)

    mdb = _get_mongo()
    if mdb is not None:
        mdb.crossmodals.update_one({"id": clean_record["id"]}, {"$set": clean_record}, upsert=True)
    else:
        conn = sqlite3.connect(SQLITE_PATH)
        conn.execute(
            """
            INSERT OR REPLACE INTO crossmodals (
                id, user_id, image_optical_url, image_sar_url, question, answer,
                optical_insights, sar_insights, cloud_penetration_noted,
                land_cover_json, detected_features_json, evidence_json,
                confidence, uncertainty_reason, coordinates_json, feature_masks_json,
                optical_meta_json, sar_meta_json, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                clean_record["id"],
                clean_record.get("user_id"),
                clean_record["image_optical_url"],
                clean_record["image_sar_url"],
                clean_record["question"],
                clean_record["answer"],
                clean_record.get("optical_insights"),
                clean_record.get("sar_insights"),
                1 if clean_record.get("cloud_penetration_noted") else 0,
                json.dumps(clean_record.get("land_cover", [])),
                json.dumps(clean_record.get("detected_features", [])),
                json.dumps(clean_record.get("evidence", [])),
                clean_record["confidence"],
                clean_record.get("uncertainty_reason"),
                json.dumps(clean_record.get("coordinates")) if clean_record.get("coordinates") else None,
                json.dumps(clean_record.get("feature_masks")) if clean_record.get("feature_masks") else None,
                json.dumps(clean_record.get("optical_meta")) if clean_record.get("optical_meta") else None,
                json.dumps(clean_record.get("sar_meta")) if clean_record.get("sar_meta") else None,
                clean_record["created_at"],
            ),
        )
        conn.commit()
        conn.close()


def get_crossmodals(limit: int = 10, user_id: Optional[str] = None) -> List[dict]:
    """Retrieves crossmodal analysis pairs, strictly isolated to the specified user_id if provided."""
    mdb = _get_mongo()
    if mdb is not None:
        query_filter = {"user_id": user_id} if user_id else {}
        cursor = mdb.crossmodals.find(query_filter, {"_id": 0}).sort("created_at", -1).limit(limit)
        return list(cursor)

    conn = sqlite3.connect(SQLITE_PATH)
    conn.row_factory = sqlite3.Row
    if user_id:
        rows = conn.execute("SELECT * FROM crossmodals WHERE user_id = ? ORDER BY created_at DESC LIMIT ?", (user_id, limit)).fetchall()
    else:
        rows = conn.execute("SELECT * FROM crossmodals ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
    conn.close()

    result = []
    for r in rows:
        r_dict = dict(r)
        for field in ["land_cover_json", "detected_features_json", "evidence_json", "coordinates_json", "feature_masks_json", "optical_meta_json", "sar_meta_json"]:
            if field in r_dict and r_dict[field]:
                try:
                    r_dict[field.replace("_json", "")] = json.loads(r_dict[field])
                except Exception:
                    pass
                del r_dict[field]
        r_dict["cloud_penetration_noted"] = bool(r_dict.get("cloud_penetration_noted", 0))
        result.append(r_dict)
    return result


# Auto-initialize database on import
init_db()
