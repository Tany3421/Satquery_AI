"""
database/sync_db.py
Database Synchronization and Seeding Utility for SatQuery AI.

Allows developers across multiple laptops to:
1. Check database connectivity and status:
   python database/sync_db.py --status

2. Export local accounts & data to a portable seed file:
   python database/sync_db.py --export-seed

3. Import seed data on a new laptop:
   python database/sync_db.py --import-seed

4. Migrate data directly to a remote MongoDB Atlas cluster:
   python database/sync_db.py --sync-to-atlas "mongodb+srv://<user>:<password>@cluster0.mongodb.net/satquery"
"""

import argparse
import json
import os
import sqlite3
import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Load .env
try:
    from dotenv import load_dotenv
    for env_path in [PROJECT_ROOT / "backend" / ".env", PROJECT_ROOT / ".env"]:
        if env_path.exists():
            load_dotenv(dotenv_path=env_path)
            break
except ImportError:
    pass

from database import db

SEED_FILE = Path(__file__).resolve().parent / "seed_data.json"
SQLITE_FILE = Path(__file__).resolve().parent / "satquery.db"


def get_status():
    mdb = db._get_mongo()
    mode = "MongoDB" if mdb is not None else "SQLite Fallback"
    target = db.MONGO_URI if mdb is not None else str(SQLITE_FILE)
    
    print("\n" + "=" * 55)
    print("  SatQuery AI - Database Status")
    print("=" * 55)
    print(f"  Active Engine : {mode}")
    print(f"  Target URI    : {target}")
    
    if mdb is not None:
        try:
            u_count = mdb.users.count_documents({})
            q_count = mdb.queries.count_documents({})
            c_count = mdb.comparisons.count_documents({})
            cr_count = mdb.crossmodals.count_documents({})
            print(f"  Users         : {u_count}")
            print(f"  Queries       : {q_count}")
            print(f"  Comparisons   : {c_count}")
            print(f"  Cross-modals  : {cr_count}")
            print("  Status        : CONNECTED & HEALTHY (MongoDB)")
        except Exception as e:
            print(f"  Status        : MongoDB Connection Warning: {e}")
    else:
        if SQLITE_FILE.exists():
            conn = sqlite3.connect(SQLITE_FILE)
            conn.row_factory = sqlite3.Row
            u_count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
            q_count = conn.execute("SELECT COUNT(*) FROM queries").fetchone()[0]
            c_count = conn.execute("SELECT COUNT(*) FROM comparisons").fetchone()[0]
            cr_count = conn.execute("SELECT COUNT(*) FROM crossmodals").fetchone()[0]
            conn.close()
            print(f"  Users         : {u_count}")
            print(f"  Queries       : {q_count}")
            print(f"  Comparisons   : {c_count}")
            print(f"  Cross-modals  : {cr_count}")
            print("  Status        : CONNECTED (Local SQLite satquery.db)")
        else:
            print("  Status        : No SQLite database found yet.")
    print("=" * 55 + "\n")


def export_seed(output_path: Path = SEED_FILE):
    mdb = db._get_mongo()
    data = {"users": [], "queries": [], "comparisons": [], "crossmodals": []}
    
    if mdb is not None:
        data["users"] = list(mdb.users.find({}, {"_id": 0}))
        data["queries"] = list(mdb.queries.find({}, {"_id": 0}))
        data["comparisons"] = list(mdb.comparisons.find({}, {"_id": 0}))
        data["crossmodals"] = list(mdb.crossmodals.find({}, {"_id": 0}))
    elif SQLITE_FILE.exists():
        conn = sqlite3.connect(SQLITE_FILE)
        conn.row_factory = sqlite3.Row
        data["users"] = [dict(r) for r in conn.execute("SELECT * FROM users").fetchall()]
        data["queries"] = [dict(r) for r in conn.execute("SELECT * FROM queries").fetchall()]
        data["comparisons"] = [dict(r) for r in conn.execute("SELECT * FROM comparisons").fetchall()]
        data["crossmodals"] = [dict(r) for r in conn.execute("SELECT * FROM crossmodals").fetchall()]
        conn.close()
    
    output_path.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")
    print(f" Successfully exported {len(data['users'])} users and {len(data['queries'])} queries to:")
    print(f"  -> {output_path}")


def import_seed(input_path: Path = SEED_FILE):
    if not input_path.exists():
        print(f" Seed file not found at: {input_path}")
        return
    
    data = json.loads(input_path.read_text(encoding="utf-8"))
    users = data.get("users", [])
    queries = data.get("queries", [])
    comparisons = data.get("comparisons", [])
    crossmodals = data.get("crossmodals", [])
    
    mdb = db._get_mongo()
    if mdb is not None:
        for u in users:
            mdb.users.update_one({"id": u["id"]}, {"$set": u}, upsert=True)
        for q in queries:
            mdb.queries.update_one({"id": q["id"]}, {"$set": q}, upsert=True)
        for c in comparisons:
            mdb.comparisons.update_one({"id": c["id"]}, {"$set": c}, upsert=True)
        for cr in crossmodals:
            mdb.crossmodals.update_one({"id": cr["id"]}, {"$set": cr}, upsert=True)
        print(f" Successfully imported into MongoDB ({len(users)} users, {len(queries)} queries).")
    else:
        conn = sqlite3.connect(SQLITE_FILE)
        conn.row_factory = sqlite3.Row
        for u in users:
            conn.execute(
                """INSERT OR REPLACE INTO users (id, username, email, password_hash, salt, role, reset_token, reset_expiry, created_at)
                   VALUES (:id, :username, :email, :password_hash, :salt, :role, :reset_token, :reset_expiry, :created_at)""",
                u
            )
        conn.commit()
        conn.close()
        print(f" Successfully imported into SQLite satquery.db ({len(users)} users).")


def sync_to_atlas(target_uri: str, db_name: str = "satquery"):
    import pymongo
    print(f" Connecting to remote target: {target_uri} ...")
    remote_client = pymongo.MongoClient(target_uri, serverSelectionTimeoutMS=5000)
    remote_client.admin.command("ping")
    remote_db = remote_client[db_name]
    print(f" Connected to target MongoDB Atlas database '{db_name}'.")

    # Read from local SQLite or local Mongo
    mdb = db._get_mongo()
    users, queries, comps, crosses = [], [], [], []
    if mdb is not None:
        users = list(mdb.users.find({}, {"_id": 0}))
        queries = list(mdb.queries.find({}, {"_id": 0}))
        comps = list(mdb.comparisons.find({}, {"_id": 0}))
        crosses = list(mdb.crossmodals.find({}, {"_id": 0}))
    elif SQLITE_FILE.exists():
        conn = sqlite3.connect(SQLITE_FILE)
        conn.row_factory = sqlite3.Row
        users = [dict(r) for r in conn.execute("SELECT * FROM users").fetchall()]
        queries = [dict(r) for r in conn.execute("SELECT * FROM queries").fetchall()]
        comps = [dict(r) for r in conn.execute("SELECT * FROM comparisons").fetchall()]
        crosses = [dict(r) for r in conn.execute("SELECT * FROM crossmodals").fetchall()]
        conn.close()

    for u in users:
        remote_db.users.update_one({"id": u["id"]}, {"$set": u}, upsert=True)
    for q in queries:
        remote_db.queries.update_one({"id": q["id"]}, {"$set": q}, upsert=True)
    for c in comps:
        remote_db.comparisons.update_one({"id": c["id"]}, {"$set": c}, upsert=True)
    for cr in crosses:
        remote_db.crossmodals.update_one({"id": cr["id"]}, {"$set": cr}, upsert=True)

    print(f" Synced to Atlas: {len(users)} users, {len(queries)} queries, {len(comps)} comparisons.")
    print(" To make both laptops use this shared database, add this line to .env on both laptops:")
    print(f" MONGO_URI={target_uri}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SatQuery AI Database Synchronization Tool")
    parser.add_argument("--status", action="store_true", help="Show active database health and record counts")
    parser.add_argument("--export-seed", action="store_true", help="Export users & queries to database/seed_data.json")
    parser.add_argument("--import-seed", action="store_true", help="Import users & queries from database/seed_data.json")
    parser.add_argument("--sync-to-atlas", type=str, help="Upload local data directly to remote MongoDB Atlas URI")

    args = parser.parse_args()

    if args.status:
        get_status()
    elif args.export_seed:
        export_seed()
    elif args.import_seed:
        import_seed()
    elif args.sync_to_atlas:
        sync_to_atlas(args.sync_to_atlas)
    else:
        get_status()
        print("Usage:")
        print("  python database/sync_db.py --status")
        print("  python database/sync_db.py --export-seed")
        print("  python database/sync_db.py --import-seed")
        print("  python database/sync_db.py --sync-to-atlas <MONGO_URI>")
