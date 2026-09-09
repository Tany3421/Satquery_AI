"""
backend/services/segmentation/change_segmentation_service.py
Bi-Temporal Change Segmentation Engine for SatQuery AI.

Performs pair-wise multi-temporal satellite observation analysis (T1 Before -> T2 After):
1. Radiometric and spectral difference tensor computation.
2. Category-aware spatial transition mapping:
   - Water expansion / Flood inundation
   - Vegetation loss / Deforestation / Clearing
   - Vegetation gain / Agricultural growth
   - Urban expansion / New construction
3. Hotspot bounding box extraction and instance-level change mask segmentation
   via HQ-SAM / SAM 2.1.
4. Quantitative delta metrics (total % changed, category breakdown, affected pixel counts).
"""

import io
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
from PIL import Image

try:
    import cv2
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False

from .mask_processor import MaskProcessor
from .segmentation_router import get_segmentation_router


class ChangeSegmentationService:
    """
    Bi-Temporal Change Segmentation Engine.
    Coordinates radiometric change detection, category-aware difference analysis,
    and instance-level SAM 2.1 mask generation.
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ChangeSegmentationService, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self.router = get_segmentation_router()
        self.palette = {
            "water_expansion": {"color": "#00b4ff", "rgb": (0, 180, 255), "label": "Water Expansion / Inundation"},
            "vegetation_loss": {"color": "#e63232", "rgb": (230, 50, 50), "label": "Vegetation Loss / Clearing"},
            "vegetation_gain": {"color": "#2ecc71", "rgb": (46, 204, 113), "label": "Vegetation Growth / Regreening"},
            "urban_expansion": {"color": "#f39c12", "rgb": (243, 156, 18), "label": "Urban Expansion / New Construction"},
            "general_change": {"color": "#9b59b6", "rgb": (155, 89, 182), "label": "Surface Transition"},
        }

    def _load_bytes(self, image_input: Union[bytes, Path, str, np.ndarray]) -> bytes:
        """Standardizes image inputs into raw image bytes."""
        if isinstance(image_input, bytes):
            return image_input
        if isinstance(image_input, (str, Path)):
            return Path(image_input).read_bytes()
        if isinstance(image_input, np.ndarray):
            pil_img = Image.fromarray(image_input)
            buf = io.BytesIO()
            pil_img.save(buf, format="PNG")
            return buf.getvalue()
        raise ValueError(f"Unsupported image input type: {type(image_input)}")

    def _align_and_convert_images(
        self,
        before_bytes: bytes,
        after_bytes: bytes,
    ) -> Tuple[np.ndarray, np.ndarray, int, int]:
        """Loads both images, aligns dimensions if needed, and returns RGB numpy arrays."""
        with Image.open(io.BytesIO(before_bytes)) as img_b, Image.open(io.BytesIO(after_bytes)) as img_a:
            rgb_b = img_b.convert("RGB")
            rgb_a = img_a.convert("RGB")

            if rgb_b.size != rgb_a.size:
                rgb_a = rgb_a.resize(rgb_b.size, Image.Resampling.BILINEAR)

            arr_b = np.asarray(rgb_b, dtype=np.float32)
            arr_a = np.asarray(rgb_a, dtype=np.float32)

        h, w = arr_b.shape[:2]
        return arr_b, arr_a, h, w

    def detect_changes(
        self,
        before_input: Union[bytes, Path, str, np.ndarray],
        after_input: Union[bytes, Path, str, np.ndarray],
        after_image_id: str,
        query: str = "Highlight changes between the two images",
        difference_threshold: float = 24.0,
        max_change_instances: int = 6,
    ) -> Dict[str, Any]:
        """
        Main entrypoint for bi-temporal change detection and instance segmentation.
        """
        before_bytes = self._load_bytes(before_input)
        after_bytes = self._load_bytes(after_input)

        arr_b, arr_a, h, w = self._align_and_convert_images(before_bytes, after_bytes)
        total_pixels = h * w

        # Channel differences
        diff_r = arr_a[:, :, 0] - arr_b[:, :, 0]
        diff_g = arr_a[:, :, 1] - arr_b[:, :, 1]
        diff_b = arr_a[:, :, 2] - arr_b[:, :, 2]

        # Euclidean distance
        euclidean_dist = np.sqrt(diff_r**2 + diff_g**2 + diff_b**2)
        change_mask = euclidean_dist > difference_threshold

        # Categorized masks
        water_mask = change_mask & (diff_b > diff_r + 6) & (diff_b > diff_g)
        veg_loss_mask = change_mask & (~water_mask) & (diff_g < -14) & (diff_r > diff_g)
        veg_gain_mask = change_mask & (~water_mask) & (~veg_loss_mask) & (diff_g > 14) & (diff_g > diff_r)
        urban_mask = change_mask & (~water_mask) & (~veg_loss_mask) & (~veg_gain_mask)

        # Composite transparent RGBA heatmap
        rgba_heatmap = np.zeros((h, w, 4), dtype=np.uint8)
        rgba_heatmap[water_mask] = [*self.palette["water_expansion"]["rgb"], 185]
        rgba_heatmap[veg_loss_mask] = [*self.palette["vegetation_loss"]["rgb"], 185]
        rgba_heatmap[veg_gain_mask] = [*self.palette["vegetation_gain"]["rgb"], 185]
        rgba_heatmap[urban_mask] = [*self.palette["urban_expansion"]["rgb"], 185]

        # Quantitative spatial stats
        total_changed = int(np.sum(change_mask))
        pct_total = round((total_changed / max(total_pixels, 1)) * 100.0, 2)
        pct_water = round((int(np.sum(water_mask)) / max(total_pixels, 1)) * 100.0, 2)
        pct_veg_loss = round((int(np.sum(veg_loss_mask)) / max(total_pixels, 1)) * 100.0, 2)
        pct_veg_gain = round((int(np.sum(veg_gain_mask)) / max(total_pixels, 1)) * 100.0, 2)
        pct_urban = round((int(np.sum(urban_mask)) / max(total_pixels, 1)) * 100.0, 2)

        stats = {
            "total_changed_percent": pct_total,
            "water_expansion_percent": pct_water,
            "vegetation_loss_percent": pct_veg_loss,
            "vegetation_gain_percent": pct_veg_gain,
            "urban_expansion_percent": pct_urban,
            "total_pixels_evaluated": total_pixels,
            "changed_pixel_count": total_changed,
            "resolution": f"{w}x{h}",
        }

        # Heatmap PNG bytes
        heatmap_pil = Image.fromarray(rgba_heatmap, mode="RGBA")
        heatmap_buf = io.BytesIO()
        heatmap_pil.save(heatmap_buf, format="PNG", optimize=True)
        heatmap_bytes = heatmap_buf.getvalue()

        # Extract localized change hotspot boxes
        hotspots = self._extract_hotspot_boxes(
            change_mask,
            urban_mask,
            veg_loss_mask,
            water_mask,
            query=query,
            image_shape=(h, w),
            max_boxes=max_change_instances,
        )

        # Convert hotspot boxes into true SAM 2.1 / HQ-SAM instance segmentation masks
        change_regions = []
        for idx, hotspot in enumerate(hotspots):
            box_1000 = hotspot["box_1000"]
            cat = hotspot["category"]
            meta = self.palette.get(cat, self.palette["general_change"])

            try:
                seg_res = self.router.segment_box(
                    image_input=after_bytes,
                    image_id=after_image_id,
                    box=box_1000,
                    engine_preference="auto",
                    display_dims=(1000, 1000),
                )
                if seg_res.get("stats", {}).get("mask_pixel_count", 0) > 0:
                    change_regions.append({
                        "id": f"change-instance-{idx + 1}",
                        "label": f"{meta['label']} #{idx + 1}",
                        "category": cat,
                        "color": meta["color"],
                        "confidence": seg_res.get("confidence_score", 0.93),
                        "stats": seg_res["stats"],
                        "contours": seg_res["contours"],
                        "rle": seg_res["rle"],
                        "mask_png_base64": seg_res["mask_png_base64"],
                        "box_2d": [box_1000[1], box_1000[0], box_1000[3], box_1000[2]],  # [ymin, xmin, ymax, xmax]
                    })
            except Exception:
                continue

        return {
            "success": True,
            "query": query,
            "spatial_change_stats": stats,
            "heatmap_png_bytes": heatmap_bytes,
            "change_regions": change_regions,
            "hotspots_count": len(change_regions),
        }

    def _extract_hotspot_boxes(
        self,
        change_mask: np.ndarray,
        urban_mask: np.ndarray,
        veg_loss_mask: np.ndarray,
        water_mask: np.ndarray,
        query: str,
        image_shape: Tuple[int, int],
        max_boxes: int = 6,
    ) -> List[Dict[str, Any]]:
        """Extracts top change bounding boxes ranked by query relevance and component size."""
        h, w = image_shape
        q_lower = (query or "").lower()

        # Pick primary mask based on user query intent
        if any(k in q_lower for k in ["building", "urban", "construction", "structure"]):
            active_mask = urban_mask
            primary_cat = "urban_expansion"
        elif any(k in q_lower for k in ["tree", "forest", "vegetation", "clearing", "loss"]):
            active_mask = veg_loss_mask
            primary_cat = "vegetation_loss"
        elif any(k in q_lower for k in ["water", "flood", "lake", "ocean"]):
            active_mask = water_mask
            primary_cat = "water_expansion"
        else:
            active_mask = change_mask
            primary_cat = "general_change"

        bin_mask = (active_mask > 0).astype(np.uint8)
        hotspots = []

        if HAS_CV2:
            # Morphological dilation to group adjacent pixel differences into clusters
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (11, 11))
            clustered = cv2.morphologyEx(bin_mask, cv2.MORPH_CLOSE, kernel)
            contours, _ = cv2.findContours(clustered, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            # Sort contours by area descending
            sorted_cnts = sorted(contours, key=cv2.contourArea, reverse=True)

            for cnt in sorted_cnts[:max_boxes]:
                area = cv2.contourArea(cnt)
                if area < 40:
                    continue

                x, y, bw, bh = cv2.boundingRect(cnt)
                # Expand box slightly to give SAM 2 context
                pad_x = int(bw * 0.10)
                pad_y = int(bh * 0.10)
                xmin = max(0, x - pad_x)
                ymin = max(0, y - pad_y)
                xmax = min(w, x + bw + pad_x)
                ymax = min(h, y + bh + pad_y)

                # Normalize to 0-1000 scale [xmin, ymin, xmax, ymax]
                b_1000 = [
                    int(round((xmin / w) * 1000)),
                    int(round((ymin / h) * 1000)),
                    int(round((xmax / w) * 1000)),
                    int(round((ymax / h) * 1000)),
                ]
                hotspots.append({
                    "box_1000": b_1000,
                    "category": primary_cat,
                    "area": area,
                })

        if not hotspots and np.any(change_mask):
            # Fallback to single bounding box of entire changed area
            rows = np.any(change_mask, axis=1)
            cols = np.any(change_mask, axis=0)
            if np.any(rows) and np.any(cols):
                ymin, ymax = np.where(rows)[0][[0, -1]]
                xmin, xmax = np.where(cols)[0][[0, -1]]
                hotspots.append({
                    "box_1000": [
                        int(round((xmin / w) * 1000)),
                        int(round((ymin / h) * 1000)),
                        int(round((xmax / w) * 1000)),
                        int(round((ymax / h) * 1000)),
                    ],
                    "category": primary_cat,
                    "area": (xmax - xmin) * (ymax - ymin),
                })

        return hotspots


# Global singleton
_change_instance: Optional[ChangeSegmentationService] = None


def get_change_segmentation_service() -> ChangeSegmentationService:
    global _change_instance
    if _change_instance is None:
        _change_instance = ChangeSegmentationService()
    return _change_instance
