"""
backend/services/segmentation/grounding_service.py
Dense Instance Grounding, Multi-Scale Tiling, and Physical Feature Proposal Engine.

Decomposes satellite and aerial imagery into distinct physical features:
- 🌊 Ocean / Sea / Water bodies (Deep Blue: #1e90ff)
- 🏖️ Beach / Sand / Coastline (Warm Sand: #d4a373)
- 🏙️ Buildings & Urban Footprints (Amber Orange: #e67e22)
- 🛣️ Roads & Transit Networks (Highway Yellow: #f1c40f)
- 🌲 Vegetation / Forests / Parks (Emerald Green: #2ecc71)

Replaces generic compass quadrant bounding boxes ("Northwest...", "Southwest...")
with precise, separate physical feature proposals.
"""

import io
import time
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
from PIL import Image

try:
    import cv2
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False

from .prompt_processor import PromptProcessor
from .mask_processor import MaskProcessor


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
    "other": "#9b59b6",
}


def calculate_iou(box1: List[float], box2: List[float]) -> float:
    """Calculates Intersection over Union (IoU) between two [ymin, xmin, ymax, xmax] boxes."""
    y1 = max(box1[0], box2[0])
    x1 = max(box1[1], box2[1])
    y2 = min(box1[2], box2[2])
    x2 = min(box1[3], box2[3])

    inter_w = max(0.0, x2 - x1)
    inter_h = max(0.0, y2 - y1)
    inter_area = inter_w * inter_h

    area1 = max(0.0, box1[2] - box1[0]) * max(0.0, box1[3] - box1[1])
    area2 = max(0.0, box2[2] - box2[0]) * max(0.0, box2[3] - box2[1])
    union_area = area1 + area2 - inter_area

    if union_area <= 0:
        return 0.0
    return inter_area / union_area


def nms_boxes(boxes: List[Dict[str, Any]], iou_threshold: float = 0.40) -> List[Dict[str, Any]]:
    """Applies Non-Maximum Suppression to eliminate overlapping redundant candidate boxes."""
    if not boxes:
        return []

    sorted_boxes = sorted(boxes, key=lambda b: b.get("score", 0.0), reverse=True)
    selected = []

    while sorted_boxes:
        best = sorted_boxes.pop(0)
        selected.append(best)
        sorted_boxes = [
            b for b in sorted_boxes
            if calculate_iou(best["box_2d"], b["box_2d"]) < iou_threshold
        ]

    return selected


class DenseGroundingService:
    """Multi-Scale Instance Grounding and Physical Feature Extractor for Satellite Rasters."""

    @staticmethod
    def infer_category(query: str) -> str:
        q = (query or "").lower()
        multi_indicators = ["separat", "all", "each", "breakdown", "different", "distinct", "individual", "landscape", "landforms", "constituent"]
        if any(k in q for k in multi_indicators):
            return "all"

        has_beach = any(k in q for k in ["beach", "coast", "shore", "sand", "shoreline", "coastline", "seashore"])
        has_water = any(k in q for k in ["ocean", "sea", "bay", "water", "river", "lake", "canal", "reservoir", "pond", "water body", "water bodies"])
        has_road = any(k in q for k in ["road", "highway", "transit", "street", "arterial", "expressway", "bridge", "rail", "railway"])
        has_veg = any(k in q for k in ["vegetation", "forest", "tree", "canopy", "crop", "agriculture", "grass", "park", "greenery"])
        has_disaster = any(k in q for k in ["flood", "burn", "fire", "damage", "disaster", "debris"])
        has_bldg = any(k in q for k in ["building", "urban", "house", "built-up", "roof", "settlement", "structure", "structures", "commercial", "residential"])

        matches = [has_beach, has_water, has_road, has_veg, has_disaster, has_bldg]
        if sum(matches) > 1:
            return "all"

        if has_beach:
            return "beach"
        if has_water:
            return "water"
        if has_road:
            return "road"
        if has_veg:
            return "vegetation"
        if has_disaster:
            return "disaster"
        if has_bldg:
            return "building"
        return "all"

    @classmethod
    def decompose_scene_features(
        cls,
        rgb_arr: np.ndarray,
        query: str = "",
        max_total_instances: int = 16,
    ) -> List[Dict[str, Any]]:
        """
        Decomposes a satellite scene into separate physical feature proposals:
        - Ocean / Sea
        - Beach & Coastline
        - Roads & Transit
        - Buildings & Urban Structures
        - Vegetation / Greenery
        """
        target_cat = cls.infer_category(query)
        all_proposals = []

        # If user explicitly specified a single isolated category without asking for separate/all
        if target_cat not in ["all", "building"] and not any(w in (query or "").lower() for w in ["separat", "all", "each", "both", "and"]):
            return cls.generate_candidate_instances(rgb_arr, target_cat, max_instances=max_total_instances)

        # Full multi-feature physical scene decomposition:
        # Extract each physical layer separately
        water_cands = cls.generate_candidate_instances(rgb_arr, "water", max_instances=3)
        beach_cands = cls.generate_candidate_instances(rgb_arr, "beach", max_instances=2)
        road_cands = cls.generate_candidate_instances(rgb_arr, "road", max_instances=4)
        bldg_cands = cls.generate_candidate_instances(rgb_arr, "building", max_instances=6)
        veg_cands = cls.generate_candidate_instances(rgb_arr, "vegetation", max_instances=3)

        all_proposals.extend(water_cands)
        all_proposals.extend(beach_cands)
        all_proposals.extend(road_cands)
        all_proposals.extend(bldg_cands)
        all_proposals.extend(veg_cands)
        return all_proposals[:max_total_instances]

    @classmethod
    def generate_candidate_instances(
        cls,
        rgb_arr: np.ndarray,
        category: str,
        max_instances: int = 12,
        tile_size: int = 512,
        overlap: int = 64,
    ) -> List[Dict[str, Any]]:
        """
        Extracts discrete candidate bounding boxes for individual physical objects
        (e.g., individual buildings, distinct water bodies, beach coastlines, roads)
        using multi-scale tiled computer vision and morphological analysis.
        """
        h, w = rgb_arr.shape[:2]
        candidates = []

        if h > tile_size or w > tile_size:
            y_steps = max(1, int(np.ceil((h - overlap) / (tile_size - overlap))))
            x_steps = max(1, int(np.ceil((w - overlap) / (tile_size - overlap))))
            tiles = []
            for yi in range(y_steps):
                y0 = min(yi * (tile_size - overlap), max(0, h - tile_size))
                y1 = min(h, y0 + tile_size)
                for xi in range(x_steps):
                    x0 = min(xi * (tile_size - overlap), max(0, w - tile_size))
                    x1 = min(w, x0 + tile_size)
                    tiles.append((y0, x0, y1, x1))
        else:
            tiles = [(0, 0, h, w)]

        for (y0, x0, y1, x1) in tiles:
            tile_rgb = rgb_arr[y0:y1, x0:x1]
            tile_candidates = cls._detect_tile_candidates(tile_rgb, category)

            for tc in tile_candidates:
                ty_min, tx_min, ty_max, tx_max = tc["box"]
                gy_min = max(0, min(h - 1, y0 + ty_min))
                gx_min = max(0, min(w - 1, x0 + tx_min))
                gy_max = max(0, min(h, y0 + ty_max))
                gx_max = max(0, min(w, x0 + tx_max))

                if gy_max <= gy_min + 5 or gx_max <= gx_min + 5:
                    continue

                box_1000 = [
                    int((gy_min / h) * 1000.0),
                    int((gx_min / w) * 1000.0),
                    int((gy_max / h) * 1000.0),
                    int((gx_max / w) * 1000.0),
                ]
                candidates.append({
                    "box_2d": box_1000,
                    "native_box": [gy_min, gx_min, gy_max, gx_max],
                    "score": tc.get("score", 0.90),
                    "area": (gy_max - gy_min) * (gx_max - gx_min),
                    "category": category,
                    "label": tc.get("label"),
                })

        filtered = nms_boxes(candidates, iou_threshold=0.35)
        filtered = sorted(filtered, key=lambda c: c["score"], reverse=True)[:max_instances]
        return filtered

    @classmethod
    def _detect_tile_candidates(cls, tile_rgb: np.ndarray, category: str) -> List[Dict[str, Any]]:
        """Detects discrete instance candidate bounding boxes within a tile."""
        th, tw = tile_rgb.shape[:2]
        tile_area = th * tw
        proposals = []

        if not HAS_CV2:
            return proposals

        r = tile_rgb[:, :, 0].astype(np.float32)
        g = tile_rgb[:, :, 1].astype(np.float32)
        b = tile_rgb[:, :, 2].astype(np.float32)
        gray = cv2.cvtColor(tile_rgb, cv2.COLOR_RGB2GRAY)
        canny = cv2.Canny(gray, 50, 150)

        # ---------------------------------------------------------------------
        # 1. BEACH & SANDY COASTLINE
        # ---------------------------------------------------------------------
        if category in ["beach", "sand", "coastline"]:
            # Real beach has warm golden sand reflectance AND low internal edge density (smooth sand, not textured rooftops)
            sand_cand = (
                (r > 165) & (g > 140) & (b > 90) &
                (r > b + 25) & (g > b + 10) &
                (r + g + b > 420) &
                (canny == 0)
            ).astype(np.uint8) * 255
            sand_cand = cv2.morphologyEx(sand_cand, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7)))
            contours, _ = cv2.findContours(sand_cand, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            for cnt in contours:
                cnt_area = cv2.contourArea(cnt)
                if cnt_area >= 1800:  # Real sand beach is a contiguous geographical band, not a 100px roof
                    bx, by, bw, bh = cv2.boundingRect(cnt)
                    roi_canny = canny[by:by+bh, bx:bx+bw]
                    edge_density = np.mean(roi_canny > 0)
                    if edge_density < 0.06:
                        pad_x = max(2, int(bw * 0.05))
                        pad_y = max(2, int(bh * 0.05))
                        proposals.append({
                            "box": [max(0, by - pad_y), max(0, bx - pad_x), min(th, by + bh + pad_y), min(tw, bx + bw + pad_x)],
                            "score": 0.95,
                            "label": "Beach & Coastline Sand Strip",
                        })

        # ---------------------------------------------------------------------
        # 2. OCEAN / SEA & WATER BODIES
        # ---------------------------------------------------------------------
        elif category in ["water", "ocean", "sea", "river"]:
            # Real water bodies in satellite imagery have:
            # 1. Low red reflectance & higher blue/green: (r < 95) & (b > r + 6)
            # 2. Very low internal edge density (water surface is smooth)
            water_cand = (((r < 95) & (b > r + 6)) | ((r + g + b < 120) & (b >= r))).astype(np.uint8) * 255
            water_cand = cv2.morphologyEx(water_cand, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)))
            contours, _ = cv2.findContours(water_cand, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            for cnt in contours:
                cnt_area = cv2.contourArea(cnt)
                if cnt_area >= 300:  # Recognizes lakes, ponds, reservoirs, and sea
                    bx, by, bw, bh = cv2.boundingRect(cnt)
                    roi_canny = canny[by:by+bh, bx:bx+bw]
                    edge_density = np.mean(roi_canny > 0)
                    solidity = cnt_area / max(bw * bh, 1)

                    if edge_density < 0.12 and solidity > 0.20:
                        label = "Ocean / Sea Water Body" if cnt_area > (tile_area * 0.15) else "Water Body / Lake / Canal"
                        proposals.append({
                            "box": [max(0, by - 4), max(0, bx - 4), min(th, by + bh + 4), min(tw, bx + bw + 4)],
                            "score": 0.96,
                            "label": label,
                        })

        # ---------------------------------------------------------------------
        # 3. ROADS & TRANSIT NETWORKS
        # ---------------------------------------------------------------------
        elif category in ["road", "infrastructure"]:
            neutral = ((np.abs(r - g) < 22) & (np.abs(g - b) < 22) & (gray > 80) & (gray < 175)).astype(np.uint8) * 255
            k_diag1 = np.eye(15, dtype=np.uint8)
            k_diag2 = np.fliplr(k_diag1)
            k_h = cv2.getStructuringElement(cv2.MORPH_RECT, (17, 3))
            k_v = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 17))
            road_resp = np.zeros_like(neutral)
            for k in [k_diag1, k_diag2, k_h, k_v]:
                road_resp = np.maximum(road_resp, cv2.morphologyEx(neutral, cv2.MORPH_OPEN, k))

            contours, _ = cv2.findContours(road_resp, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            for cnt in contours:
                bx, by, bw, bh = cv2.boundingRect(cnt)
                area = bw * bh
                aspect = max(bw, bh) / max(min(bw, bh), 1)
                if area >= 1000 and aspect >= 1.6:
                    proposals.append({
                        "box": [by, bx, min(th, by + bh), min(tw, bx + bw)],
                        "score": 0.91,
                        "label": "Road & Transit Corridor",
                    })

        # ---------------------------------------------------------------------
        # 4. BUILDINGS & BUILT STRUCTURES
        # ---------------------------------------------------------------------
        elif category in ["building", "urban"]:
            # Method A: Adaptive thresholding for dense urban fabric
            blur = cv2.GaussianBlur(gray, (5, 5), 0)
            thresh = cv2.adaptiveThreshold(blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 17, 2)
            opened = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3)))
            contours_a, _ = cv2.findContours(opened, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            for cnt in contours_a:
                bx, by, bw, bh = cv2.boundingRect(cnt)
                area = bw * bh
                aspect = bw / max(bh, 1)
                # Allow wide building sizes from small houses (120px) to large commercial complexes (40000px)
                if 120 <= area <= 45000 and 0.25 <= aspect <= 4.0:
                    pad_x = max(3, int(bw * 0.08))
                    pad_y = max(3, int(bh * 0.08))
                    proposals.append({
                        "box": [max(0, by - pad_y), max(0, bx - pad_x), min(th, by + bh + pad_y), min(tw, bx + bw + pad_x)],
                        "score": 0.90 + min(0.08, area / 10000.0),
                        "label": "Building / Built Structure",
                    })

            # Method B: Gradient edges for discrete/isolated structures
            if len(proposals) < 8:
                grad_x = cv2.Sobel(gray, cv2.CV_32F, 1, 0, ksize=3)
                grad_y = cv2.Sobel(gray, cv2.CV_32F, 0, 1, ksize=3)
                norm_grad = cv2.normalize(cv2.magnitude(grad_x, grad_y), None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
                _, edges = cv2.threshold(norm_grad, 35, 255, cv2.THRESH_BINARY)
                contours_b, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                for cnt in contours_b:
                    bx, by, bw, bh = cv2.boundingRect(cnt)
                    area = bw * bh
                    aspect = bw / max(bh, 1)
                    if 120 <= area <= (tile_area * 0.35) and 0.2 <= aspect <= 4.5:
                        pad_x = max(3, int(bw * 0.08))
                        pad_y = max(3, int(bh * 0.08))
                        proposals.append({
                            "box": [max(0, by - pad_y), max(0, bx - pad_x), min(th, by + bh + pad_y), min(tw, bx + bw + pad_x)],
                            "score": 0.90 + min(0.08, area / (tile_area * 0.15)),
                            "label": "Building / Built Structure",
                        })

        # ---------------------------------------------------------------------
        # 5. VEGETATION / CANOPY & PARKS
        # ---------------------------------------------------------------------
        elif category in ["vegetation", "forest"]:
            exg = 2.0 * g - r - b
            veg_bin = (exg > 18.0).astype(np.uint8) * 255
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
            veg_bin = cv2.morphologyEx(veg_bin, cv2.MORPH_CLOSE, kernel)
            contours, _ = cv2.findContours(veg_bin, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            for cnt in contours:
                x, y, w, h = cv2.boundingRect(cnt)
                area = w * h
                if area >= 140:
                    proposals.append({
                        "box": [y, x, min(th, y + h), min(tw, x + w)],
                        "score": 0.92,
                        "label": "Vegetation / Canopy Cover",
                    })

        return proposals
