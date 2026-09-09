"""
backend/main.py
SatQuery AI — API layer.

This file should stay thin: routing, validation, file handling. All prompt
engineering lives in ../aiml, all persistence lives in ../database. That
split is deliberate so your team can work in parallel — see README.md for
who owns what.
"""

import base64
import io
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional
import time

import numpy as np
from PIL import Image

from fastapi import Depends, FastAPI, File, Form, Header, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# Allow `import database.db` / `import aiml.engine` regardless of whether
# this is run from the project root or from inside backend/.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from aiml import engine  # noqa: E402
from aiml.orchestrator import default_orchestrator, OrchestratorError  # noqa: E402
from aiml.prompts import MODE_PROMPTS  # noqa: E402
from database import db  # noqa: E402

try:
    from backend import auth_jwt
except ImportError:
    import auth_jwt

try:
    from backend import io_geotiff
except ImportError:
    import io_geotiff

try:
    from backend.services.segmentation import (
        get_sam2_service,
        MaskProcessor,
        PromptProcessor,
        DenseGroundingService,
        GroundingDINOService,
        get_grounding_dino_service,
        SegmentationRouter,
        get_segmentation_router,
        SemanticSegmentationService,
        get_semantic_segmentation_service,
        ChangeSegmentationService,
        get_change_segmentation_service,
    )
except ImportError:
    from services.segmentation import (
        get_sam2_service,
        MaskProcessor,
        PromptProcessor,
        DenseGroundingService,
        GroundingDINOService,
        get_grounding_dino_service,
        SegmentationRouter,
        get_segmentation_router,
        SemanticSegmentationService,
        get_semantic_segmentation_service,
        ChangeSegmentationService,
        get_change_segmentation_service,
    )

from aiml.highlight_router import classify_highlight_subtask, HIGHLIGHT_SEMANTIC, HIGHLIGHT_OBJECT, HIGHLIGHT_CHANGE

from aiml.specialists import grounding as rs_grounding
from fastapi.responses import Response, FileResponse
import json

APP_DIR = Path(__file__).parent
UPLOAD_DIR = APP_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

app = FastAPI(title="SatQuery AI", version="0.3.0")

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
VALID_DATA_SOURCES = {"sentinel2", "sentinel1", "bhuvan", "fusion"}


class UserSignup(BaseModel):
    username: str
    email: str
    password: str


class UserLogin(BaseModel):
    email: Optional[str] = None
    username: Optional[str] = None
    password: str


class ForgotPasswordRequest(BaseModel):
    email: str


class ResetPasswordRequest(BaseModel):
    token: str
    password: str


class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    role: Optional[str] = "researcher"
    created_at: str


class AuthTokenResponse(BaseModel):
    token: str
    user: dict


class QueryResponse(BaseModel):
    id: str
    user_id: Optional[str] = None
    image_id: str
    image_url: str
    mode: str
    data_source: Optional[str] = "sentinel2"
    engine_used: Optional[str] = "Gemini API"
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
    coordinates: Optional[dict] = None
    feature_masks: Optional[list] = None
    raster_meta: Optional[dict] = None
    auditable_trace: Optional[dict] = None
    created_at: str


class FastQueryRequest(BaseModel):
    question: str
    context: Optional[str] = ""


class CompareResponse(BaseModel):
    id: str
    user_id: Optional[str] = None
    image_before_url: str
    image_after_url: str
    label_before: Optional[str] = None
    label_after: Optional[str] = None
    narrative: str
    changes: list
    anomaly_flagged: bool
    anomaly_reason: Optional[str] = None
    confidence: int
    change_heatmap_url: Optional[str] = None
    spatial_change_stats: Optional[dict] = None
    auditable_trace: Optional[dict] = None
    created_at: str


class CrossModalResponse(BaseModel):
    id: str
    user_id: Optional[str] = None
    image_optical_url: str
    image_sar_url: str
    question: str
    answer: str
    optical_insights: Optional[str] = None
    sar_insights: Optional[str] = None
    cloud_penetration_noted: Optional[bool] = False
    land_cover: list
    detected_features: list
    evidence: list
    confidence: int
    uncertainty_reason: Optional[str] = None
    coordinates: Optional[dict] = None
    feature_masks: Optional[list] = None
    optical_meta: Optional[dict] = None
    sar_meta: Optional[dict] = None
    auditable_trace: Optional[dict] = None
    created_at: str


def _media_type_for(filename: str) -> str:
    ext = filename.lower().rsplit(".", 1)[-1]
    return {
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "png": "image/png",
        "webp": "image/webp",
        "gif": "image/gif",
        "tif": "image/tiff",
        "tiff": "image/tiff",
    }.get(ext, "image/jpeg")


def _save_upload(raw: bytes, filename: str) -> tuple[str, Path, Path, bytes, str, dict]:
    """
    Saves raw upload, extracts GeoTIFF metadata & RGB preview if applicable,
    and returns (img_id, stored_raw_path, display_path, inference_bytes, inference_media_type, metadata).
    """
    img_id = str(uuid.uuid4())
    ext = (filename or "image.jpg").rsplit(".", 1)[-1].lower()
    stored_raw_path = UPLOAD_DIR / f"{img_id}.{ext}"
    stored_raw_path.write_bytes(raw)

    raster_info = io_geotiff.process_raster_upload(raw, filename or f"image.{ext}")
    is_geo = raster_info.get("is_geotiff", False)

    if is_geo:
        preview_path = UPLOAD_DIR / f"{img_id}_preview.jpg"
        preview_path.write_bytes(raster_info["preview_bytes"])
        display_path = preview_path
        inference_bytes = raster_info["preview_bytes"]
        inference_media = "image/jpeg"
    else:
        display_path = stored_raw_path
        inference_bytes = raw
        inference_media = _media_type_for(filename or "image.jpg")

    db.insert_image(img_id, filename or f"image.{ext}", datetime.now(timezone.utc).isoformat())
    return img_id, stored_raw_path, display_path, inference_bytes, inference_media, raster_info.get("metadata", {})


# --------------------------------------------------------------------------
# Routes
# --------------------------------------------------------------------------


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "modes": sorted(VALID_MODES),
        "data_sources": sorted(VALID_DATA_SOURCES),
        "engines": ["Gemini API (Image + Reasoning)", "Groq API (Fast Queries)"],
        "mapbox_token": os.getenv("MAPBOX_ACCESS_TOKEN", "").strip(),
    }


@app.post("/api/auth/register", response_model=AuthTokenResponse)
@app.post("/api/auth/signup", response_model=AuthTokenResponse)
def auth_register(req: UserSignup):
    username = (req.username or "").strip()
    email = (req.email or "").strip()
    password = req.password

    if not username:
        raise HTTPException(status_code=400, detail="Username is required")
    if not email or "@" not in email:
        raise HTTPException(status_code=400, detail="Valid email is required")
    if len(password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")

    if db.get_user_by_username(username):
        raise HTTPException(status_code=409, detail="Email or username already taken")
    if db.get_user_by_email(email):
        raise HTTPException(status_code=409, detail="Email or username already taken")

    user_id = str(uuid.uuid4())
    created_at = datetime.now(timezone.utc).isoformat()
    new_user = db.create_user(user_id, username, email, password, created_at, role="researcher")
    token = auth_jwt.make_token(new_user)
    return {"token": token, "user": auth_jwt.safe_user(new_user)}


@app.post("/api/auth/login", response_model=AuthTokenResponse)
def auth_login(req: UserLogin):
    identifier = req.email or req.username
    if not identifier or not identifier.strip():
        raise HTTPException(status_code=400, detail="Email or username is required")
    if not req.password:
        raise HTTPException(status_code=400, detail="Password is required")

    user = db.get_user_by_email_or_username(identifier)
    if not user or not db.verify_password(req.password, user["password_hash"], user["salt"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = auth_jwt.make_token(user)
    return {"token": token, "user": auth_jwt.safe_user(user)}


@app.get("/api/auth/me")
def auth_me(request: Request):
    auth_header = request.headers.get("Authorization", "")
    token_data = auth_jwt.verify_token(auth_header)
    if not token_data:
        raise HTTPException(status_code=401, detail="Invalid or expired JWT token")
    user = db.get_user_by_id(token_data["id"])
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return auth_jwt.safe_user(user)


@app.get("/api/auth/me/{user_id}", response_model=UserResponse)
def auth_me_by_id(user_id: str):
    user = db.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@app.post("/api/auth/forgot-password")
def auth_forgot_password(req: ForgotPasswordRequest):
    email = (req.email or "").strip()
    if not email:
        raise HTTPException(status_code=400, detail="Email is required")

    user = db.get_user_by_email(email)
    if not user:
        raise HTTPException(status_code=404, detail="No account with that email")

    token = str(uuid.uuid4())
    expiry = int(time.time()) + 3600  # 1 hour
    db.set_user_reset_token(email, token, expiry)

    reset_link = f"reset-password.html?token={token}"
    return {
        "success": True,
        "message": f"Password reset link generated for {user['username']}",
        "reset_token": token,
        "reset_link": reset_link,
    }


@app.post("/api/auth/reset-password")
def auth_reset_password(req: ResetPasswordRequest):
    if not req.token or not req.password:
        raise HTTPException(status_code=400, detail="Token and new password are required")
    if len(req.password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")

    success = db.reset_user_password(req.token, req.password)
    if not success:
        raise HTTPException(status_code=400, detail="Invalid or expired reset link")

    return {"success": True, "message": "Password successfully updated. You can now log in."}


@app.post("/api/fast-query")
def fast_query(req: FastQueryRequest):
    """Fast text-only query engine endpoint using Groq API / Gemini fast fallback."""
    if not req.question or not req.question.strip():
        raise HTTPException(status_code=400, detail="question is required")
    try:
        res = engine.run_groq_fast_query(req.question.strip(), req.context or "")
        return res
    except engine.EngineError as exc:
        raise HTTPException(status_code=502, detail=str(exc))


def _enrich_feature_masks_with_sam2(
    feature_masks: Optional[list],
    image_bytes: bytes,
    image_id: str,
    query: str = "",
) -> list:
    """
    Converts detected visual features (buildings, water, roads, vegetation)
    into true pixel-level SAM 2.1 segmentation masks with distinct category colors
    and boundary contours. Avoids coarse whole-image bounding boxes by using
    dense multi-scale instance proposals.
    """
    service = get_sam2_service()
    enriched = []

    # Check if we have fine-grained boxes from VLM that are NOT generic compass quadrants
    has_fine_boxes = False
    if feature_masks and isinstance(feature_masks, list):
        valid_boxes = [m for m in feature_masks if m.get("box_2d") and len(m["box_2d"]) == 4]
        if valid_boxes:
            is_generic_quadrant = any(
                any(kw in (m.get("feature_name") or "").lower() for kw in ["northwest", "southwest", "northeast", "southeast", "northern", "southern", "eastern", "western", "quadrant", "zone", "fabric"])
                for m in valid_boxes
            )
            box_areas = [
                abs(b["box_2d"][2] - b["box_2d"][0]) * abs(b["box_2d"][3] - b["box_2d"][1])
                for b in valid_boxes
            ]
            if not is_generic_quadrant and any(a < 350000 for a in box_areas):
                has_fine_boxes = True

    if has_fine_boxes:
        prompts = rs_grounding.ground_text_query_to_prompts(query, {"feature_masks": feature_masks})
    else:
        # Separate physical feature decomposition: Ocean, Beach, Buildings, Roads, Vegetation
        try:
            rgb_arr = np.array(Image.open(io.BytesIO(image_bytes)).convert("RGB"))
            candidates = DenseGroundingService.decompose_scene_features(
                rgb_arr, query=query, max_total_instances=14
            )
        except Exception:
            candidates = []

        if candidates:
            prompts = []
            for i, cand in enumerate(candidates):
                cat = cand.get("category", "other")
                label = cand.get("label") or f"{cat.title()} {i + 1}"
                color = cand.get("color") or rs_grounding.CATEGORY_COLORS.get(cat, "#4fd8c4")

                prompts.append({
                    "id": f"feat-{cat}-{i + 1}",
                    "label": label,
                    "category": cat,
                    "color": color,
                    "box_2d": cand["box_2d"],
                    "confidence": cand.get("score", 0.92),
                })
        else:
            prompts = rs_grounding.ground_text_query_to_prompts(query, None)

    for p in prompts:
        cat = p.get("category", "other")
        color = p.get("color") or rs_grounding.CATEGORY_COLORS.get(cat, "#4fd8c4")
        ymin, xmin, ymax, xmax = p["box_2d"]
        box_1000 = [xmin, ymin, xmax, ymax]

        try:
            seg_res = service.segment_box(
                image_input=image_bytes,
                image_id=image_id,
                box=box_1000,
                display_dims=(1000, 1000),
            )
            if seg_res.get("stats", {}).get("mask_pixel_count", 0) > 0:
                enriched.append({
                    "feature_name": p.get("label", f"{cat.title()} Region"),
                    "category": cat,
                    "color": color,
                    "box_2d": [ymin, xmin, ymax, xmax],
                    "confidence": p.get("confidence", 0.90),
                    "stats": seg_res.get("stats"),
                    "contours": seg_res.get("contours", []),
                    "mask_png_base64": seg_res.get("mask_png_base64"),
                    "rle": seg_res.get("rle"),
                })
        except Exception:
            continue

    return enriched


@app.post("/api/analyze", response_model=QueryResponse)
async def analyze(
    question: str = Form(...),
    mode: str = Form("general"),
    data_source: str = Form("sentinel2"),
    engine_type: str = Form("auto"),
    user_id: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None),
    image_id: Optional[str] = Form(None),
):
    if not question or not question.strip():
        raise HTTPException(status_code=400, detail="question is required")
    if mode not in VALID_MODES:
        raise HTTPException(
            status_code=400, detail=f"mode must be one of {sorted(VALID_MODES)}"
        )
    if data_source not in VALID_DATA_SOURCES:
        raise HTTPException(
            status_code=400, detail=f"data_source must be one of {sorted(VALID_DATA_SOURCES)}"
        )

    if image is not None:
        raw = await image.read()
        img_id, stored_raw, display_path, inf_bytes, inf_media, r_meta = _save_upload(raw, image.filename or "image.jpg")
    elif image_id:
        matches = list(UPLOAD_DIR.glob(f"{image_id}.*"))
        if not matches:
            raise HTTPException(status_code=404, detail="image_id not found")
        stored_raw = matches[0]
        img_id = image_id
        raw = stored_raw.read_bytes()
        raster_info = io_geotiff.process_raster_upload(raw, stored_raw.name)
        if raster_info.get("is_geotiff"):
            preview_matches = list(UPLOAD_DIR.glob(f"{image_id}_preview.jpg"))
            display_path = preview_matches[0] if preview_matches else stored_raw
            inf_bytes = raster_info["preview_bytes"]
            inf_media = "image/jpeg"
        else:
            display_path = stored_raw
            inf_bytes = raw
            inf_media = _media_type_for(stored_raw.name)
        r_meta = raster_info.get("metadata", {})
    else:
        raise HTTPException(status_code=400, detail="Provide either 'image' or 'image_id'")

    images = [{
        "filename": image.filename if image else stored_raw.name,
        "preview_bytes": inf_bytes,
        "is_geotiff": r_meta.get("is_geotiff", False),
        "modality": "sar" if data_source == "sentinel1" else "optical",
        "raster_meta": r_meta,
    }]

    try:
        parsed = default_orchestrator.dispatch(
            images=images,
            query=question,
            input_mode="single",
            task_parameters={"mode": mode, "data_source": data_source, "engine_type": engine_type},
        )
    except OrchestratorError as exc:
        raise HTTPException(status_code=502, detail=str(exc))

    # Automatically compute pixel-level segmentation masks for detected features (buildings, roads, water, vegetation)
    raw_feature_masks = parsed.get("feature_masks")
    enriched_feature_masks = _enrich_feature_masks_with_sam2(raw_feature_masks, inf_bytes, img_id, query=question)

    record = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "image_id": img_id,
        "image_url": f"/uploads/{display_path.name}",
        "mode": mode,
        "data_source": data_source,
        "engine_used": parsed.get("engine_used", "Gemini API"),
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
        "coordinates": parsed.get("coordinates"),
        "feature_masks": enriched_feature_masks,
        "raster_meta": r_meta,
        "auditable_trace": parsed.get("auditable_trace"),
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
    user_id: Optional[str] = Form(None),
):
    """Multi-temporal change detection + anomaly flagging over bi-temporal image pair."""
    before_raw = await before.read()
    after_raw = await after.read()

    _, _, before_disp, before_bytes, before_media, before_meta = _save_upload(before_raw, before.filename or "before.jpg")
    _, _, after_disp, after_bytes, after_media, after_meta = _save_upload(after_raw, after.filename or "after.jpg")

    images = [
        {"filename": before.filename or "before.jpg", "preview_bytes": before_bytes, "is_geotiff": before_meta.get("is_geotiff", False), "label": label_before, "modality": "optical"},
        {"filename": after.filename or "after.jpg", "preview_bytes": after_bytes, "is_geotiff": after_meta.get("is_geotiff", False), "label": label_after, "modality": "optical"},
    ]

    try:
        parsed = default_orchestrator.dispatch(
            images=images,
            query="What changed between these two observation dates?",
            input_mode="bitemporal",
        )
    except OrchestratorError as exc:
        raise HTTPException(status_code=502, detail=str(exc))

    comp_id = str(uuid.uuid4())
    heatmap_url = None
    if parsed.get("heatmap_png_bytes"):
        h_path = UPLOAD_DIR / f"{comp_id}_heatmap.png"
        h_path.write_bytes(parsed["heatmap_png_bytes"])
        heatmap_url = f"/uploads/{comp_id}_heatmap.png"

    record = {
        "id": comp_id,
        "user_id": user_id,
        "image_before_url": f"/uploads/{before_disp.name}",
        "image_after_url": f"/uploads/{after_disp.name}",
        "label_before": label_before,
        "label_after": label_after,
        "narrative": parsed.get("narrative", ""),
        "changes": parsed.get("changes", []),
        "anomaly_flagged": bool(parsed.get("anomaly_flagged", False)),
        "confidence": parsed.get("confidence", 0),
        "change_heatmap_url": heatmap_url,
        "spatial_change_stats": parsed.get("spatial_change_stats"),
        "auditable_trace": parsed.get("auditable_trace"),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    db.insert_comparison(record)
    return {**record, "anomaly_reason": parsed.get("anomaly_reason", "")}


@app.post("/api/crossmodal", response_model=CrossModalResponse)
async def crossmodal(
    optical: UploadFile = File(...),
    sar: UploadFile = File(...),
    question: str = Form(""),
    user_id: Optional[str] = Form(None),
):
    """Co-registered Optical + SAR joint information extraction (Cartosat-2S + RISAT / S2 + S1)."""
    opt_raw = await optical.read()
    sar_raw = await sar.read()

    _, _, opt_disp, opt_bytes, opt_media, opt_meta = _save_upload(opt_raw, optical.filename or "optical.tif")
    _, _, sar_disp, sar_bytes, sar_media, sar_meta = _save_upload(sar_raw, sar.filename or "sar.tif")

    images = [
        {"filename": optical.filename or "optical.tif", "preview_bytes": opt_bytes, "is_geotiff": opt_meta.get("is_geotiff", False), "modality": "optical", "raster_meta": opt_meta},
        {"filename": sar.filename or "sar.tif", "preview_bytes": sar_bytes, "is_geotiff": sar_meta.get("is_geotiff", False), "modality": "sar", "raster_meta": sar_meta},
    ]

    try:
        parsed = default_orchestrator.dispatch(
            images=images,
            query=question or "Use the optical and SAR images together to identify built-up and water-covered regions.",
            input_mode="crossmodal",
        )
    except OrchestratorError as exc:
        raise HTTPException(status_code=502, detail=str(exc))

    record = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "image_optical_url": f"/uploads/{opt_disp.name}",
        "image_sar_url": f"/uploads/{sar_disp.name}",
        "question": question or "Joint Optical-SAR Feature & Land Cover Extraction",
        "answer": parsed.get("answer", ""),
        "optical_insights": parsed.get("optical_insights", ""),
        "sar_insights": parsed.get("sar_insights", ""),
        "cloud_penetration_noted": bool(parsed.get("cloud_penetration_noted", False)),
        "land_cover": parsed.get("land_cover", []),
        "detected_features": parsed.get("detected_features", []),
        "evidence": parsed.get("evidence", []),
        "confidence": parsed.get("confidence", 0),
        "uncertainty_reason": parsed.get("uncertainty_reason", ""),
        "coordinates": parsed.get("coordinates"),
        "feature_masks": parsed.get("feature_masks"),
        "optical_meta": opt_meta,
        "sar_meta": sar_meta,
        "auditable_trace": parsed.get("auditable_trace"),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    db.insert_crossmodal(record)
    return record


@app.post("/api/agent/dispatch")
async def agent_dispatch(
    query: str = Form(...),
    files: List[UploadFile] = File(...),
    input_mode: str = Form("auto"),
):
    """
    Unified Autonomous Agent Dispatch Endpoint.
    Accepts natural-language query and 1 or 2 satellite rasters/images, autonomously classifies
    the requested task, validates input compatibility, sequences specialist tools,
    and returns an evidence-grounded response with an observable auditable execution trace.
    """
    if not files:
        raise HTTPException(status_code=400, detail="At least 1 image file is required.")

    processed_images = []
    for f in files:
        raw = await f.read()
        _, _, disp, p_bytes, _, r_meta = _save_upload(raw, f.filename or "image.jpg")
        mod = "sar" if "sar" in (f.filename or "").lower() or r_meta.get("bands") == 1 else "optical"
        processed_images.append({
            "filename": f.filename or "image.jpg",
            "preview_bytes": p_bytes,
            "display_url": f"/uploads/{disp.name}",
            "is_geotiff": r_meta.get("is_geotiff", False),
            "modality": mod,
            "raster_meta": r_meta,
        })

    try:
        res = default_orchestrator.dispatch(
            images=processed_images,
            query=query,
            input_mode=input_mode,
        )
        res["uploaded_images"] = [img["display_url"] for img in processed_images]
        return res
    except OrchestratorError as exc:
        raise HTTPException(status_code=502, detail=str(exc))


def _resolve_user_id(user_id: Optional[str], authorization: Optional[str]) -> Optional[str]:
    """Helper to extract user_id from query param or Bearer token."""
    if user_id and user_id.strip():
        return user_id.strip()
    if authorization:
        payload = auth_jwt.verify_token(authorization)
        if payload and payload.get("id"):
            return str(payload["id"])
    return None


@app.get("/api/crossmodals")
def get_crossmodals(
    limit: int = 10,
    user_id: Optional[str] = None,
    authorization: Optional[str] = Header(None),
):
    resolved_uid = _resolve_user_id(user_id, authorization)
    return db.get_crossmodals(limit=limit, user_id=resolved_uid)


@app.get("/api/history")
def get_history(
    limit: int = 20,
    user_id: Optional[str] = None,
    authorization: Optional[str] = Header(None),
):
    resolved_uid = _resolve_user_id(user_id, authorization)
    return db.get_history(limit=limit, user_id=resolved_uid)


@app.get("/api/comparisons")
def get_comparisons(
    limit: int = 10,
    user_id: Optional[str] = None,
    authorization: Optional[str] = Header(None),
):
    resolved_uid = _resolve_user_id(user_id, authorization)
    return db.get_comparisons(limit=limit, user_id=resolved_uid)


@app.delete("/api/history")
def clear_history(
    user_id: Optional[str] = None,
    authorization: Optional[str] = Header(None),
):
    resolved_uid = _resolve_user_id(user_id, authorization)
    db.clear_history(user_id=resolved_uid)
    return {"cleared": True}


@app.get("/api/benchmark")
def get_benchmark():
    """Runs the 4-part SIH26167 benchmark evaluation harness (BigEarthNet, RSVQA, VRSBench, CDVQA)."""
    try:
        from eval.benchmark_harness import run_full_benchmark_suite
        return run_full_benchmark_suite()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/api/report/{query_id}")
def get_report(query_id: str):
    """
    Quantitative Remote Sensing Analysis Report.
    Calculates detailed area coverage metrics (Urban Density, Vegetation Canopy,
    Water Surface, Agriculture, Atmospheric Obstruction) and includes clean
    Model Confidence and Response Time metrics with Auditable Trace as an extension.
    """
    record = db.get_query(query_id)
    if not record:
        raise HTTPException(status_code=404, detail="query not found")

    land_cover = record.get("land_cover") or []

    # Calculate detailed area coverage breakdown
    urban_pct = round(sum(item.get("percent", 0) for item in land_cover if any(k in item.get("label", "").lower() for k in ["urban", "industrial", "commercial", "building", "fabric"])), 1)
    veg_pct = round(sum(item.get("percent", 0) for item in land_cover if any(k in item.get("label", "").lower() for k in ["forest", "tree", "wood", "canopy", "vegetation"])), 1)
    agri_pct = round(sum(item.get("percent", 0) for item in land_cover if any(k in item.get("label", "").lower() for k in ["arable", "crop", "pasture", "cultivation", "agriculture", "farm"])), 1)
    water_pct = round(sum(item.get("percent", 0) for item in land_cover if any(k in item.get("label", "").lower() for k in ["water", "marine", "lake", "river", "inundation"])), 1)
    bare_pct = round(sum(item.get("percent", 0) for item in land_cover if any(k in item.get("label", "").lower() for k in ["bare", "rock", "sand", "soil", "sparse", "peat"])), 1)

    # Urban Density classification
    if urban_pct >= 30:
        urban_density_desc = f"High Density ({urban_pct}% built-up coverage — compact urban core with commercial/residential grid)"
    elif urban_pct >= 12:
        urban_density_desc = f"Moderate Density ({urban_pct}% built-up coverage — suburban fabric with transit corridors)"
    elif urban_pct > 0:
        urban_density_desc = f"Low Density ({urban_pct}% built-up coverage — dispersed rural settlements / isolated structures)"
    else:
        urban_density_desc = "Non-Urbanized Surface (0.0% built-up fabric detected)"

    # Vegetation Cover classification
    if veg_pct >= 35:
        veg_cover_desc = f"Dense Vegetated Biomass ({veg_pct}% coverage — closed forest canopy with strong chlorophyll absorption)"
    elif veg_pct >= 10:
        veg_cover_desc = f"Moderate Canopy ({veg_pct}% coverage — open woodland / seasonal agrarian greenery)"
    else:
        veg_cover_desc = f"Sparse Canopy ({veg_pct}% coverage)"

    # Water Cover classification
    if water_pct >= 15:
        water_desc = f"Expansive Water Body ({water_pct}% coverage — reservoir / fluvial drainage basin)"
    elif water_pct > 0:
        water_desc = f"Localized Water Feature ({water_pct}% coverage — retention basins / minor water channels)"
    else:
        water_desc = "No surface water bodies detected (0.0% hydrological footprint)"

    trace = record.get("auditable_trace") or {}
    response_time_ms = trace.get("latency_ms") or 280

    return {
        "title": "Multimodal Remote Sensing Analysis Report",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_image": record["image_url"],
        "query_date": record["created_at"],
        "mode": record["mode"],
        "data_source": record.get("data_source", "sentinel2"),
        "engine_used": record.get("engine_used", "Gemini API"),
        "question": record["question"],
        "findings": record["answer"],
        "model_confidence": record["confidence"],
        "response_time_ms": response_time_ms,
        "area_coverage_metrics": {
            "urban_density_analysis": urban_density_desc,
            "urban_area_percent": urban_pct,
            "vegetation_area_percent": veg_pct,
            "vegetation_canopy_analysis": veg_cover_desc,
            "water_surface_percent": water_pct,
            "water_surface_analysis": water_desc,
            "agricultural_area_percent": agri_pct,
            "bare_soil_percent": bare_pct,
        },
        "land_cover": land_cover,
        "detected_features": record["detected_features"],
        "evidence": record["evidence"],
        "image_quality": record.get("image_quality") or "Good",
        "cloud_cover_percent": record.get("cloud_cover_percent") or 0,
        "coordinates": record.get("coordinates"),
        "feature_masks": record.get("feature_masks"),
        "limitations": record.get("uncertainty_reason") or "None noted.",
        "auditable_trace": trace,
    }


# --------------------------------------------------------------------------
# SAM 2 Interactive Segmentation & Region Highlighter API Endpoints
# --------------------------------------------------------------------------


def _resolve_image_source(
    image: Optional[UploadFile] = None,
    image_id: Optional[str] = None,
) -> tuple[str, bytes, dict, str]:
    """
    Resolves image bytes and metadata from an uploaded file or existing image_id.
    Returns (img_id, preview_bytes, raster_meta, display_url).
    """
    if image is not None:
        raw = image.file.read()
        img_id, stored_raw, disp_path, preview_bytes, _, r_meta = _save_upload(raw, image.filename or "image.jpg")
        return img_id, preview_bytes, r_meta, f"/uploads/{disp_path.name}"
    elif image_id:
        matches = list(UPLOAD_DIR.glob(f"{image_id}.*"))
        if not matches:
            raise HTTPException(status_code=404, detail=f"Image ID '{image_id}' not found.")
        stored_raw = matches[0]
        raw = stored_raw.read_bytes()
        raster_info = io_geotiff.process_raster_upload(raw, stored_raw.name)
        if raster_info.get("is_geotiff"):
            p_matches = list(UPLOAD_DIR.glob(f"{image_id}_preview.jpg"))
            disp_path = p_matches[0] if p_matches else stored_raw
            preview_bytes = raster_info["preview_bytes"]
        else:
            disp_path = stored_raw
            preview_bytes = raw
        return image_id, preview_bytes, raster_info.get("metadata", {}), f"/uploads/{disp_path.name}"
    else:
        raise HTTPException(status_code=400, detail="Provide either 'image' or 'image_id'")


@app.get("/api/segment/status")
def segment_status():
    """Returns SAM 2 model, GPU/CUDA device status, and embedding cache metrics."""
    service = get_sam2_service()
    return service.get_status()


@app.post("/api/segment/download-weights")
def segment_download_weights(variant: str = Form("tiny")):
    """Downloads official Meta SAM 2 weights checkpoint."""
    service = get_sam2_service()
    return service.download_weights(variant)


@app.post("/api/segment/point")
async def segment_point(
    image: Optional[UploadFile] = File(None),
    image_id: Optional[str] = Form(None),
    x: float = Form(...),
    y: float = Form(...),
    is_positive: bool = Form(True),
    display_width: Optional[int] = Form(None),
    display_height: Optional[int] = Form(None),
    label: str = Form("Selected Region"),
    color: str = Form("#4fd8c4"),
):
    """
    Point-based interactive segmentation prompt (supports Positive & Negative points).
    """
    img_id, img_bytes, r_meta, disp_url = _resolve_image_source(image, image_id)
    service = get_sam2_service()
    display_dims = (display_height, display_width) if (display_width and display_height) else None

    try:
        res = service.segment_point(
            image_input=img_bytes,
            image_id=img_id,
            x=x,
            y=y,
            is_positive=is_positive,
            display_dims=display_dims,
        )
        res.update({
            "image_id": img_id,
            "image_url": disp_url,
            "label": label,
            "color": color,
            "is_geotiff": r_meta.get("is_geotiff", False),
            "crs": r_meta.get("crs", "Pixel Coordinates"),
        })
        return res
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Point segmentation failed: {exc}")


@app.post("/api/segment/box")
async def segment_box(
    image: Optional[UploadFile] = File(None),
    image_id: Optional[str] = Form(None),
    xmin: float = Form(...),
    ymin: float = Form(...),
    xmax: float = Form(...),
    ymax: float = Form(...),
    display_width: Optional[int] = Form(None),
    display_height: Optional[int] = Form(None),
    label: str = Form("Bounding Box Region"),
    color: str = Form("#4fd8c4"),
):
    """
    Bounding box interactive segmentation prompt.
    """
    img_id, img_bytes, r_meta, disp_url = _resolve_image_source(image, image_id)
    service = get_sam2_service()
    display_dims = (display_height, display_width) if (display_width and display_height) else None

    try:
        res = service.segment_box(
            image_input=img_bytes,
            image_id=img_id,
            box=[xmin, ymin, xmax, ymax],
            display_dims=display_dims,
        )
        res.update({
            "image_id": img_id,
            "image_url": disp_url,
            "label": label,
            "color": color,
            "is_geotiff": r_meta.get("is_geotiff", False),
            "crs": r_meta.get("crs", "Pixel Coordinates"),
        })
        return res
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Box segmentation failed: {exc}")


@app.post("/api/segment/polygon")
async def segment_polygon(
    image: Optional[UploadFile] = File(None),
    image_id: Optional[str] = Form(None),
    points: str = Form(...),  # JSON string of [[x1, y1], [x2, y2], ...]
    display_width: Optional[int] = Form(None),
    display_height: Optional[int] = Form(None),
    label: str = Form("Polygon Area"),
    color: str = Form("#4fd8c4"),
):
    """
    Polygon region constraint segmentation prompt.
    """
    img_id, img_bytes, r_meta, disp_url = _resolve_image_source(image, image_id)
    service = get_sam2_service()
    display_dims = (display_height, display_width) if (display_width and display_height) else None

    try:
        parsed_pts = json.loads(points)
    except Exception:
        raise HTTPException(status_code=400, detail="points must be a valid JSON array of coordinate pairs [[x, y], ...]")

    try:
        res = service.segment_polygon(
            image_input=img_bytes,
            image_id=img_id,
            polygon=parsed_pts,
            display_dims=display_dims,
        )
        res.update({
            "image_id": img_id,
            "image_url": disp_url,
            "label": label,
            "color": color,
            "is_geotiff": r_meta.get("is_geotiff", False),
            "crs": r_meta.get("crs", "Pixel Coordinates"),
        })
        return res
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Polygon segmentation failed: {exc}")


@app.post("/api/segment/refine")
async def segment_refine(
    image_id: str = Form(...),
    mask_rle: str = Form(...),  # JSON string of {size, counts}
    points: Optional[str] = Form(None),  # JSON string of [{x, y, is_positive}]
    brush_stroke: Optional[str] = Form(None),  # JSON string of {points, radius, mode}
    display_width: Optional[int] = Form(None),
    display_height: Optional[int] = Form(None),
):
    """
    Iteratively refines an existing mask using positive/negative points or brush paint/erase.
    """
    _, img_bytes, r_meta, disp_url = _resolve_image_source(image_id=image_id)
    service = get_sam2_service()
    display_dims = (display_height, display_width) if (display_width and display_height) else None

    try:
        rle_dict = json.loads(mask_rle)
        existing_mask = MaskProcessor.rle_to_mask(rle_dict)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Invalid mask_rle: {exc}")

    pts_list = None
    if points:
        try:
            pts_list = json.loads(points)
        except Exception:
            pass

    brush_dict = None
    if brush_stroke:
        try:
            brush_dict = json.loads(brush_stroke)
        except Exception:
            pass

    try:
        res = service.refine_mask(
            image_input=img_bytes,
            image_id=image_id,
            existing_mask=existing_mask,
            points=pts_list,
            brush_stroke=brush_dict,
            display_dims=display_dims,
        )
        res.update({
            "image_id": image_id,
            "image_url": disp_url,
            "is_geotiff": r_meta.get("is_geotiff", False),
        })
        return res
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Refinement failed: {exc}")


@app.post("/api/segment/text")
async def segment_text(
    image: Optional[UploadFile] = File(None),
    image_id: Optional[str] = Form(None),
    query: str = Form(...),
    display_width: Optional[int] = Form(None),
    display_height: Optional[int] = Form(None),
):
    """
    Mode 2 — AI Text-Based Region Highlighting.
    Flow: User query -> Specialist Subtask Classifier -> Semantic / Object Specialist -> SAM 2 / HQ-SAM -> Mask Deduplication.
    """
    if not query or not query.strip():
        raise HTTPException(status_code=400, detail="Query is required for AI text highlighting.")

    img_id, img_bytes, r_meta, disp_url = _resolve_image_source(image, image_id)
    service = get_sam2_service()
    router = get_segmentation_router()
    semantic_service = get_semantic_segmentation_service()
    vlm_res = {}
    segmented_regions = []

    try:
        rgb_arr = np.array(Image.open(io.BytesIO(img_bytes)).convert("RGB"))
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Failed to decode image: {exc}")

    # Subtask intent classification
    subtask, conf, routing_meta = classify_highlight_subtask(query=query)

    # 1. Semantic Class Segmentation Route
    if subtask == HIGHLIGHT_SEMANTIC:
        q_lower = query.lower()
        if any(w in q_lower for w in ["all", "separately", "each", "land cover", "scene"]):
            sem_results = semantic_service.segment_scene(rgb_arr)
            segmented_regions.extend(sem_results)
        else:
            single_res = semantic_service.segment_class(rgb_arr, query)
            if single_res:
                segmented_regions.append(single_res)

    # 2. Object / Discrete Instance Grounding Route (or fallback if semantic returned empty)
    if not segmented_regions:
        target_cat = DenseGroundingService.infer_category(query)
        candidates = []

        try:
            # Use Grounding DINO service with NMS
            dino_service = get_grounding_dino_service()
            dino_boxes = dino_service.detect_objects(rgb_arr, query=query, max_instances=16)

            if dino_boxes:
                candidates = dino_boxes
            elif target_cat == "all" or any(w in query.lower() for w in ["separately", "beach", "ocean", "all", "each"]):
                candidates = DenseGroundingService.decompose_scene_features(
                    rgb_arr, query=query, max_total_instances=16
                )
            else:
                candidates = DenseGroundingService.generate_candidate_instances(
                    rgb_arr, target_cat, max_instances=16
                )
        except Exception:
            candidates = []

        prompts = []
        if candidates:
            for i, cand in enumerate(candidates):
                cat = cand.get("category", target_cat)
                label = cand.get("label") or f"{cat.title()} {i + 1}"
                color = cand.get("color") or rs_grounding.CATEGORY_COLORS.get(cat, "#4fd8c4")

                prompts.append({
                    "id": cand.get("id") or f"ai-{cat}-{i + 1}",
                    "label": label,
                    "category": cat,
                    "color": color,
                    "box_2d": cand["box_2d"],
                    "confidence": cand.get("confidence") or cand.get("score", 0.92),
                })
        else:
            # Secondary fallback to VLM text grounding
            try:
                img_b64 = base64.b64encode(img_bytes).decode("utf-8")
                vlm_res = engine.analyze_image(
                    image_b64=img_b64,
                    media_type="image/jpeg",
                    question=query,
                    mode="grounding",
                    data_source="sentinel2",
                    raster_meta=r_meta,
                )
            except Exception:
                vlm_res = {"feature_masks": []}
            prompts = rs_grounding.ground_text_query_to_prompts(query, vlm_res)

        # Generate SAM 2 / HQ-SAM pixel-level masks for each prompt
        for p in prompts:
            try:
                ymin, xmin, ymax, xmax = p["box_2d"]
                box_1000 = [xmin, ymin, xmax, ymax]
                seg_res = router.segment_box(
                    image_input=img_bytes,
                    image_id=img_id,
                    box=box_1000,
                    engine_preference="auto",
                    display_dims=(1000, 1000),
                )
                if seg_res.get("stats", {}).get("mask_pixel_count", 0) > 0:
                    segmented_regions.append({
                        "id": p["id"],
                        "label": p["label"],
                        "category": p["category"],
                        "color": p["color"],
                        "confidence": p.get("confidence", seg_res.get("confidence_score", 0.9)),
                        "stats": seg_res["stats"],
                        "contours": seg_res["contours"],
                        "rle": seg_res["rle"],
                        "mask_png_base64": seg_res["mask_png_base64"],
                        "box_2d": p["box_2d"],
                    })
            except Exception:
                continue

    # Step 3: Mask deduplication (NMS) & clean-up
    segmented_regions = MaskProcessor.deduplicate_masks(segmented_regions, iou_threshold=0.55)

    engine_name = service.get_status()["engine"]
    return {
        "success": True,
        "query": query,
        "subtask": subtask,
        "engine": engine_name,
        "image_id": img_id,
        "image_url": disp_url,
        "regions_count": len(segmented_regions),
        "regions": segmented_regions,
        "vlm_summary": vlm_res.get("answer", f"Identified {len(segmented_regions)} candidate region(s) matching '{query}'."),
        "is_geotiff": r_meta.get("is_geotiff", False),
    }


@app.post("/api/segment/change")
async def segment_change(
    before: Optional[UploadFile] = File(None),
    after: Optional[UploadFile] = File(None),
    before_image_id: Optional[str] = Form(None),
    after_image_id: Optional[str] = Form(None),
    query: str = Form("Highlight changes between the two images"),
):
    """
    Bi-Temporal Change Segmentation:
    Image A (Before) + Image B (After) -> Change Difference Localization -> SAM 2 Change Masks.
    """
    _, before_bytes, _, before_url = _resolve_image_source(before, before_image_id)
    after_id, after_bytes, after_meta, after_url = _resolve_image_source(after, after_image_id)

    change_service = get_change_segmentation_service()
    try:
        change_res = change_service.detect_changes(
            before_input=before_bytes,
            after_input=after_bytes,
            after_image_id=after_id,
            query=query,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Change detection failed: {exc}")

    h_path = UPLOAD_DIR / f"{after_id}_change_heatmap.png"
    h_path.write_bytes(change_res["heatmap_png_bytes"])

    return {
        "success": True,
        "query": query,
        "before_image_url": before_url,
        "after_image_url": after_url,
        "change_heatmap_url": f"/uploads/{h_path.name}",
        "spatial_change_stats": change_res["spatial_change_stats"],
        "change_regions": change_res["change_regions"],
        "is_geotiff": after_meta.get("is_geotiff", False),
    }


@app.post("/api/segment/export")
async def segment_export(
    image_id: str = Form(...),
    mask_rle: str = Form(...),  # JSON string of {size, counts}
    export_format: str = Form("png_overlay"),  # "png_overlay", "binary_png", "geotiff"
    color: str = Form("#4fd8c4"),
    opacity: float = Form(0.5),
):
    """
    Exports the segmentation mask as a PNG overlay, binary PNG, or GeoTIFF (preserving spatial georeferencing).
    """
    _, _, r_meta, _ = _resolve_image_source(image_id=image_id)

    try:
        rle_dict = json.loads(mask_rle)
        mask = MaskProcessor.rle_to_mask(rle_dict)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Invalid mask_rle: {exc}")

    export_id = str(uuid.uuid4())[:8]

    if export_format == "geotiff":
        out_filename = f"mask_{image_id}_{export_id}.tif"
        out_path = UPLOAD_DIR / out_filename
        MaskProcessor.export_geotiff_mask(mask, r_meta, out_path)
        return FileResponse(
            path=str(out_path),
            filename=out_filename,
            media_type="image/tiff",
        )
    elif export_format == "binary_png":
        png_bytes = MaskProcessor.mask_to_binary_png_bytes(mask)
        return Response(
            content=png_bytes,
            media_type="image/png",
            headers={"Content-Disposition": f"attachment; filename=binary_mask_{image_id}_{export_id}.png"},
        )
    else:
        # png_overlay
        rgb_color = _hex_to_rgb(color)
        rgba_bytes = MaskProcessor.mask_to_rgba_overlay_bytes(mask, color_rgb=rgb_color, opacity=opacity)
        return Response(
            content=rgba_bytes,
            media_type="image/png",
            headers={"Content-Disposition": f"attachment; filename=overlay_mask_{image_id}_{export_id}.png"},
        )


def _hex_to_rgb(hex_str: str) -> tuple[int, int, int]:
    h = (hex_str or "").lstrip("#")
    if len(h) == 6:
        try:
            return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
        except Exception:
            pass
    return (79, 216, 196)


# Mount frontend static directory to serve index.html, login.html, reset-password.html
FRONTEND_DIR = PROJECT_ROOT / "frontend"
if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")
