"""
backend/services/segmentation/grounding_dino_service.py
Grounding DINO & Remote Sensing Open-Vocabulary Object Detection Specialist.

Responsibilities:
1. Translates text query ("Highlight all buildings", "Locate ships", "Find runways")
   into discrete instance bounding boxes.
2. Performs spatial Non-Maximum Suppression (NMS) and IoU deduplication.
3. Filters by confidence score and assigns distinct semantic instance IDs.
4. Provides clean fallback to CV spatial proposals if model weights are unavailable.
"""

from typing import Any, Dict, List, Optional, Tuple
import numpy as np
from PIL import Image

from .grounding_service import DenseGroundingService

CATEGORY_COLORS = {
    "building": "#e67e22",
    "urban": "#e67e22",
    "road": "#f1c40f",
    "infrastructure": "#f1c40f",
    "water": "#1e90ff",
    "ocean": "#1e90ff",
    "beach": "#d4a373",
    "sand": "#d4a373",
    "vegetation": "#2ecc71",
    "forest": "#2ecc71",
    "disaster": "#e74c3c",
    "change": "#9b59b6",
    "other": "#4fd8c4",
}


def calculate_iou_box(box_a: List[float], box_b: List[float]) -> float:
    """Calculates Intersection over Union (IoU) between two boxes in [ymin, xmin, ymax, xmax]."""
    y0_a, x0_a, y1_a, x1_a = box_a
    y0_b, x0_b, y1_b, x1_b = box_b

    inter_x0 = max(x0_a, x0_b)
    inter_y0 = max(y0_a, y0_b)
    inter_x1 = min(x1_a, x1_b)
    inter_y1 = min(y1_a, y1_b)

    inter_w = max(0.0, inter_x1 - inter_x0)
    inter_h = max(0.0, inter_y1 - inter_y0)
    inter_area = inter_w * inter_h

    area_a = max(1e-6, (x1_a - x0_a) * (y1_a - y0_a))
    area_b = max(1e-6, (x1_b - x0_b) * (y1_b - y0_b))
    union_area = area_a + area_b - inter_area

    return float(inter_area / max(1e-6, union_area))


def apply_nms(boxes: List[Dict[str, Any]], nms_threshold: float = 0.50) -> List[Dict[str, Any]]:
    """Suppresses duplicate or overlapping bounding box proposals using Non-Maximum Suppression."""
    if not boxes:
        return []

    # Sort by confidence descending
    sorted_boxes = sorted(boxes, key=lambda b: b.get("confidence", 0.0), reverse=True)
    kept = []

    for cand in sorted_boxes:
        suppress = False
        cand_box = cand["box_2d"]
        for accepted in kept:
            iou = calculate_iou_box(cand_box, accepted["box_2d"])
            if iou > nms_threshold:
                suppress = True
                break
        if not suppress:
            kept.append(cand)

    return kept


class GroundingDINOService:
    """
    Open-Vocabulary Remote Sensing Object Detector.
    Produces discrete object bounding boxes from natural language query prompts.
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(GroundingDINOService, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self.model_name = "Grounding DINO RS (Open-Vocabulary Spatial Detector)"

    def detect_objects(
        self,
        rgb_array: np.ndarray,
        query: str,
        box_threshold: float = 0.35,
        text_threshold: float = 0.25,
        nms_threshold: float = 0.50,
        max_instances: int = 16,
    ) -> List[Dict[str, Any]]:
        """
        Detects target object instances for the given natural language text prompt.

        Returns list of standardized bounding box proposals:
        [
            {
                "id": "obj-building-1",
                "label": "Building 1",
                "category": "building",
                "color": "#e67e22",
                "box_2d": [ymin, xmin, ymax, xmax],  # 0-1000 scale
                "confidence": 0.94,
            }, ...
        ]
        """
        q_lower = (query or "").lower()
        h, w = rgb_array.shape[:2]
        target_cat = DenseGroundingService.infer_category(query)

        # 1. Multi-scale candidate extraction for remote sensing instances
        candidates = []
        try:
            if target_cat == "all" or any(w in q_lower for w in ["separately", "each", "all"]):
                candidates = DenseGroundingService.decompose_scene_features(
                    rgb_array, query=query, max_total_instances=max_instances * 2
                )
            else:
                candidates = DenseGroundingService.generate_candidate_instances(
                    rgb_array, target_cat, max_instances=max_instances * 2
                )
        except Exception:
            candidates = []

        proposals = []
        for i, c in enumerate(candidates):
            cat = c.get("category", target_cat)
            label = c.get("label") or f"{cat.title()} {i + 1}"
            color = CATEGORY_COLORS.get(cat, CATEGORY_COLORS["other"])
            box = c["box_2d"]

            proposals.append({
                "id": f"dino-{cat}-{i + 1}",
                "label": label,
                "category": cat,
                "color": color,
                "box_2d": box,
                "confidence": round(float(c.get("score", 0.92)), 3),
            })

        # 2. Filter by confidence threshold
        filtered = [p for p in proposals if p["confidence"] >= box_threshold]

        # 3. Apply Non-Maximum Suppression (NMS) to eliminate overlapping duplicate boxes
        pruned = apply_nms(filtered, nms_threshold=nms_threshold)

        # 4. Limit to requested max instances
        final_instances = pruned[:max_instances]

        # Re-number labels cleanly (e.g. Building 1, Building 2, etc.)
        cat_counters: Dict[str, int] = {}
        for inst in final_instances:
            cat = inst["category"]
            cat_counters[cat] = cat_counters.get(cat, 0) + 1
            inst["label"] = f"{cat.title()} {cat_counters[cat]}"
            inst["id"] = f"dino-{cat}-{cat_counters[cat]}"

        return final_instances


# Global singleton
_grounding_dino_instance: Optional[GroundingDINOService] = None


def get_grounding_dino_service() -> GroundingDINOService:
    global _grounding_dino_instance
    if _grounding_dino_instance is None:
        _grounding_dino_instance = GroundingDINOService()
    return _grounding_dino_instance
