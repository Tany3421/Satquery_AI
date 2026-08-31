"""
backend/main.py
SatQuery AI — API layer.

This file should stay thin: routing, validation, file handling. All prompt
engineering lives in ../aiml, all persistence lives in ../database. That
split is deliberate so your team can work in parallel — see README.md for
who owns what.
"""

import base64
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# Allow `import database.db` / `import aiml.engine` regardless of whether
# this is run from the project root or from inside backend/.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from aiml import engine  # noqa: E402
from aiml.prompts import MODE_PROMPTS  # noqa: E402
from database import db  # noqa: E402

APP_DIR = Path(__file__).parent
UPLOAD_DIR = APP_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

app = FastAPI(title="SatQuery AI", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # EXTEND: lock this down before deploying
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")


@app.on_event("startup")
def on_startup():
    db.init_db()


VALID_MODES = set(MODE_PROMPTS.keys())


class QueryResponse(BaseModel):
    id: str
    image_id: str
    image_url: str
    mode: str
    question: str
    answer: str
    land_cover: list
    detected_features: list
    evidence: list
    confidence: int
    uncertainty_reason: Optional[str] = None
    cloud_cover_percent: Optional[int] = None
    image_quality: Optional[str] = None
    region_note: Optional[str] = None
    created_at: str


class CompareResponse(BaseModel):
    id: str
    image_before_url: str
    image_after_url: str
    label_before: Optional[str] = None
    label_after: Optional[str] = None
    narrative: str
    changes: list
    anomaly_flagged: bool
    anomaly_reason: Optional[str] = None
    confidence: int
    created_at: str


def _media_type_for(filename: str) -> str:
    ext = filename.lower().rsplit(".", 1)[-1]
    return {
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "png": "image/png",
        "webp": "image/webp",
        "gif": "image/gif",
    }.get(ext, "image/jpeg")


def _save_upload(raw: bytes, filename: str) -> tuple[str, Path, str]:
    img_id = str(uuid.uuid4())
    ext = (filename or "image.jpg").rsplit(".", 1)[-1].lower()
    stored_path = UPLOAD_DIR / f"{img_id}.{ext}"
    stored_path.write_bytes(raw)
    media_type = _media_type_for(filename or "image.jpg")
    db.insert_image(img_id, filename, datetime.now(timezone.utc).isoformat())
    return img_id, stored_path, media_type


# --------------------------------------------------------------------------
# Routes
# --------------------------------------------------------------------------


@app.get("/api/health")
def health():
    return {"status": "ok", "modes": sorted(VALID_MODES)}


@app.post("/api/analyze", response_model=QueryResponse)
async def analyze(
    question: str = Form(...),
    mode: str = Form("general"),
    image: Optional[UploadFile] = File(None),
    image_id: Optional[str] = Form(None),
):
    if not question or not question.strip():
        raise HTTPException(status_code=400, detail="question is required")
    if mode not in VALID_MODES:
        raise HTTPException(
            status_code=400, detail=f"mode must be one of {sorted(VALID_MODES)}"
        )

    if image is not None:
        raw = await image.read()
        img_id, stored_path, media_type = _save_upload(raw, image.filename or "image.jpg")
    elif image_id:
        matches = list(UPLOAD_DIR.glob(f"{image_id}.*"))
        if not matches:
            raise HTTPException(status_code=404, detail="image_id not found")
        stored_path = matches[0]
        img_id = image_id
        media_type = _media_type_for(stored_path.name)
        raw = stored_path.read_bytes()
    else:
        raise HTTPException(status_code=400, detail="Provide either 'image' or 'image_id'")

    image_b64 = base64.b64encode(raw).decode("utf-8")

    try:
        parsed = engine.analyze_image(image_b64, media_type, question, mode)
    except engine.EngineError as exc:
        raise HTTPException(status_code=502, detail=str(exc))

    record = {
        "id": str(uuid.uuid4()),
        "image_id": img_id,
        "image_url": f"/uploads/{stored_path.name}",
        "mode": mode,
        "question": question,
        "answer": parsed.get("answer", ""),
        "land_cover": parsed.get("land_cover", []),
        "detected_features": parsed.get("detected_features", []),
        "evidence": parsed.get("evidence", []),
        "confidence": parsed.get("confidence", 0),
        "uncertainty_reason": parsed.get("uncertainty_reason", ""),
        "cloud_cover_percent": parsed.get("cloud_cover_percent"),
        "image_quality": parsed.get("image_quality"),
        "region_note": parsed.get("region_note", ""),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    db.insert_query(record)
    return record


@app.post("/api/compare", response_model=CompareResponse)
async def compare(
    before: UploadFile = File(...),
    after: UploadFile = File(...),
    label_before: str = Form(""),
    label_after: str = Form(""),
):
    """Multi-temporal change detection + anomaly flagging (build-plan Day 5-6)."""
    before_raw = await before.read()
    after_raw = await after.read()

    _, before_path, before_media = _save_upload(before_raw, before.filename or "before.jpg")
    _, after_path, after_media = _save_upload(after_raw, after.filename or "after.jpg")

    before_b64 = base64.b64encode(before_raw).decode("utf-8")
    after_b64 = base64.b64encode(after_raw).decode("utf-8")

    try:
        parsed = engine.compare_images(
            before_b64, before_media, after_b64, after_media, label_before, label_after
        )
    except engine.EngineError as exc:
        raise HTTPException(status_code=502, detail=str(exc))

    record = {
        "id": str(uuid.uuid4()),
        "image_before_url": f"/uploads/{before_path.name}",
        "image_after_url": f"/uploads/{after_path.name}",
        "label_before": label_before,
        "label_after": label_after,
        "narrative": parsed.get("narrative", ""),
        "changes": parsed.get("changes", []),
        "anomaly_flagged": bool(parsed.get("anomaly_flagged", False)),
        "confidence": parsed.get("confidence", 0),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    db.insert_comparison(record)
    return {**record, "anomaly_reason": parsed.get("anomaly_reason", "")}


@app.get("/api/history")
def get_history(limit: int = 20):
    return db.get_history(limit=limit)


@app.get("/api/comparisons")
def get_comparisons(limit: int = 10):
    return db.get_comparisons(limit=limit)


@app.delete("/api/history")
def clear_history():
    db.clear_history()
    return {"cleared": True}


@app.get("/api/report/{query_id}")
def get_report(query_id: str):
    """
    ISRO-style analysis report for a single query — plain structured JSON;
    the frontend renders it as a printable report (see 'Generate Report' in
    the dashboard). EXTEND: render this as an actual PDF with reportlab/
    the pdf skill if you want a downloadable file instead of print-to-PDF.
    """
    record = db.get_query(query_id)
    if not record:
        raise HTTPException(status_code=404, detail="query not found")
    return {
        "title": "Remote Sensing Analysis Report",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_image": record["image_url"],
        "query_date": record["created_at"],
        "mode": record["mode"],
        "question": record["question"],
        "findings": record["answer"],
        "land_cover": record["land_cover"],
        "detected_features": record["detected_features"],
        "evidence": record["evidence"],
        "confidence": record["confidence"],
        "limitations": record.get("uncertainty_reason") or "None noted.",
        "image_quality": record.get("image_quality"),
        "cloud_cover_percent": record.get("cloud_cover_percent"),
    }


# EXTEND: /api/anomaly-scan — run compare_images across a sequence of >2
# images and surface only the anomaly_flagged transitions (Day 6 "wow"
# feature: automatic anomaly investigation).
