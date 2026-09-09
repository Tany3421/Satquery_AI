"""
aiml/specialists/grounding.py
Text-Guided Visual Region Grounding Specialist for SatQuery AI.

Interprets queries like:
- "Highlight the water body referred to in the query"
- "Locate the airfield runway and airport structures"
- "Find where the ships are docked in the port"

Extracts, validates, and normalizes 2D bounding boxes [ymin, xmin, ymax, xmax]
scaled to 0-1000 standard format with semantic category assignment.
"""

from typing import Any, Dict, List, Optional


TARGET_CATEGORIES = {
    "beach": ["beach", "coast", "shore", "sand", "shoreline", "coastline", "seashore"],
    "water": ["water", "ocean", "sea", "bay", "lake", "river", "reservoir", "canal", "pond", "flood", "estuary"],
    "road": ["road", "highway", "transit", "street", "arterial", "expressway", "bridge", "rail", "railway"],
    "vegetation": ["vegetation", "forest", "crop", "agriculture", "trees", "canopy", "grassland", "park"],
    "urban": ["building", "urban", "built-up", "house", "residential", "commercial", "settlement", "structure"],
    "infrastructure": ["runway", "airport", "airfield", "road", "bridge", "highway", "port", "dock", "facility"],
    "disaster": ["burn", "fire", "damage", "landslide", "debris", "flood zone"],
}


def infer_target_category(query: str) -> str:
    """Infers the primary semantic category targeted by the user query."""
    q_lower = (query or "").lower()
    for cat, keywords in TARGET_CATEGORIES.items():
        for kw in keywords:
            if kw in q_lower:
                return cat
    return "other"


def format_grounding_masks(
    masks: Optional[List[Dict[str, Any]]],
    query: str = "",
) -> List[Dict[str, Any]]:
    """
    Standardizes and validates grounding bounding boxes.
    Guarantees [ymin, xmin, ymax, xmax] are clamped between 0 and 1000.
    """
    if not masks:
        return []

    formatted = []
    for m in masks:
        box = m.get("box_2d")
        if not box or len(box) != 4:
            continue

        ymin, xmin, ymax, xmax = box
        # Clamp to 0-1000
        ymin_c = max(0, min(1000, int(ymin)))
        xmin_c = max(0, min(1000, int(xmin)))
        ymax_c = max(0, min(1000, int(ymax)))
        xmax_c = max(0, min(1000, int(xmax)))

        # Ensure min < max
        if ymax_c <= ymin_c:
            ymax_c = min(1000, ymin_c + 50)
        if xmax_c <= xmin_c:
            xmax_c = min(1000, xmin_c + 50)

        name = m.get("feature_name", "Detected Feature")
        cat = m.get("category") or infer_target_category(name)

        formatted.append({
            "feature_name": name,
            "category": cat.lower(),
            "box_2d": [ymin_c, xmin_c, ymax_c, xmax_c],
            "confidence": m.get("confidence", 0.90),
        })

    return formatted


CATEGORY_COLORS = {
    "water": "#1e90ff",
    "ocean": "#1e90ff",
    "sea": "#1e90ff",
    "beach": "#d4a373",
    "sand": "#d4a373",
    "coastline": "#d4a373",
    "building": "#e67e22",
    "urban": "#e67e22",
    "road": "#f1c40f",
    "infrastructure": "#f1c40f",
    "vegetation": "#2ecc71",
    "forest": "#2ecc71",
    "disaster": "#e74c3c",
    "change": "#9b59b6",
    "other": "#4fd8c4",
}


def ground_text_query_to_prompts(
    query: str,
    vlm_result: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """
    Translates a natural language highlighting query (e.g. "Highlight all buildings",
    "Highlight water bodies", "Highlight the newly constructed building") into
    structured prompts for SAM 2 segmentation.
    """
    raw_masks = None
    if vlm_result and isinstance(vlm_result, dict):
        raw_masks = vlm_result.get("feature_masks")

    formatted = format_grounding_masks(raw_masks, query)
    target_cat = infer_target_category(query)

    prompts = []
    for idx, item in enumerate(formatted):
        cat = item.get("category", target_cat)
        color = CATEGORY_COLORS.get(cat, CATEGORY_COLORS["other"])
        ymin, xmin, ymax, xmax = item["box_2d"]

        # Calculate seed center point
        cx = int((xmin + xmax) / 2.0)
        cy = int((ymin + ymax) / 2.0)

        prompts.append({
            "id": f"prompt-{idx + 1}",
            "label": item.get("feature_name", f"{cat.title()} Region"),
            "category": cat,
            "color": color,
            "box_2d": [ymin, xmin, ymax, xmax],  # 0-1000 format
            # [xmin, ymin, xmax, ymax] format for SAM 2
            "box_norm": [xmin / 1000.0, ymin / 1000.0, xmax / 1000.0, ymax / 1000.0],
            "seed_point_norm": [cx / 1000.0, cy / 1000.0],
            "confidence": item.get("confidence", 0.90),
        })

    return prompts


def ground_query_with_dino(
    rgb_array: Any,
    query: str,
    max_instances: int = 16,
    nms_threshold: float = 0.50,
) -> List[Dict[str, Any]]:
    """
    Direct interface to Grounding DINO object detector for natural language
    instance-level feature detection with Non-Maximum Suppression.
    """
    try:
        from backend.services.segmentation.grounding_dino_service import get_grounding_dino_service
        service = get_grounding_dino_service()
        return service.detect_objects(
            rgb_array=rgb_array,
            query=query,
            nms_threshold=nms_threshold,
            max_instances=max_instances,
        )
    except Exception:
        # Fallback to text prompt extraction
        return ground_text_query_to_prompts(query)
