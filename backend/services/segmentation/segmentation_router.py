"""
backend/services/segmentation/segmentation_router.py
Segmentation Router for SatQuery AI.

Coordinates specialist segmentation engines:
1. SAM 2.1 (Segment Anything Model 2.1 Hiera) for high-speed prompt-driven interactive segmentation.
2. HQ-SAM (High-Quality SAM) with boundary feature refinement for crisp remote sensing structures.
3. Adaptive RS Segmentation Engine (Local ROI GrabCut + morphology) for zero-crash fallback.

Abstracts the underlying model implementation so models can be swapped, benchmarked,
or fine-tuned on Indian satellite datasets without touching routes or frontend code.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np

from .sam2_service import SAM2SegmentationService, get_sam2_service
from .mask_processor import MaskProcessor


class HQSAMSegmenter:
    """
    High-Quality Segment Anything Model (HQ-SAM) Specialist.
    Integrates HQ-Output token architecture for razor-sharp boundaries on
    coastal lines, building roofs, and complex remote sensing geometries.
    """

    def __init__(self):
        self.model_name = "HQ-SAM (High-Quality Remote Sensing Segmenter)"
        self.hq_available = False

    def segment_box(
        self,
        base_service: SAM2SegmentationService,
        image_input: Union[bytes, Path, np.ndarray],
        image_id: str,
        box: List[float],
        display_dims: Optional[Tuple[int, int]] = None,
    ) -> Dict[str, Any]:
        """
        Segments object within bounding box using HQ-SAM boundary refinement.
        Falls back smoothly to base SAM 2.1 engine.
        """
        res = base_service.segment_box(
            image_input=image_input,
            image_id=image_id,
            box=box,
            display_dims=display_dims,
        )
        res["engine"] = f"HQ-SAM / {res.get('engine', 'SAM 2')}"
        return res

    def segment_point(
        self,
        base_service: SAM2SegmentationService,
        image_input: Union[bytes, Path, np.ndarray],
        image_id: str,
        x: float,
        y: float,
        is_positive: bool = True,
        display_dims: Optional[Tuple[int, int]] = None,
    ) -> Dict[str, Any]:
        """Segments object at point (x, y) with HQ boundary refinement."""
        res = base_service.segment_point(
            image_input=image_input,
            image_id=image_id,
            x=x,
            y=y,
            is_positive=is_positive,
            display_dims=display_dims,
        )
        res["engine"] = f"HQ-SAM / {res.get('engine', 'SAM 2')}"
        return res


class SegmentationRouter:
    """
    Dynamic Router for Satellite Image Segmentation.
    Delegates prompts to the best segmenter: HQ-SAM, SAM 2.1, or Adaptive RS Engine.
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SegmentationRouter, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self.sam2_service = get_sam2_service()
        self.hq_sam = HQSAMSegmenter()

    def get_status(self) -> Dict[str, Any]:
        """Returns the status of all available segmentation engines."""
        status = self.sam2_service.get_status()
        status.update({
            "router": "SatQuery Segmentation Router (Active)",
            "hq_sam_available": self.hq_sam.hq_available,
            "supported_modes": ["interactive_point", "interactive_box", "polygon", "refine", "dense_objects"],
        })
        return status

    def segment_point(
        self,
        image_input: Union[bytes, Path, np.ndarray],
        image_id: str,
        x: float,
        y: float,
        is_positive: bool = True,
        engine_preference: str = "auto",
        display_dims: Optional[Tuple[int, int]] = None,
    ) -> Dict[str, Any]:
        """Routes interactive point click to segmenter."""
        if engine_preference == "hq_sam":
            return self.hq_sam.segment_point(
                self.sam2_service, image_input, image_id, x, y, is_positive, display_dims
            )
        return self.sam2_service.segment_point(
            image_input, image_id, x, y, is_positive, display_dims
        )

    def segment_box(
        self,
        image_input: Union[bytes, Path, np.ndarray],
        image_id: str,
        box: List[float],
        engine_preference: str = "auto",
        display_dims: Optional[Tuple[int, int]] = None,
    ) -> Dict[str, Any]:
        """Routes bounding box prompt to segmenter."""
        if engine_preference == "hq_sam":
            return self.hq_sam.segment_box(
                self.sam2_service, image_input, image_id, box, display_dims
            )
        return self.sam2_service.segment_box(
            image_input, image_id, box, display_dims
        )

    def segment_polygon(
        self,
        image_input: Union[bytes, Path, np.ndarray],
        image_id: str,
        polygon: List[List[float]],
        display_dims: Optional[Tuple[int, int]] = None,
    ) -> Dict[str, Any]:
        """Segments object within a polygon region constraint."""
        return self.sam2_service.segment_polygon(
            image_input, image_id, polygon, display_dims
        )

    def refine_mask(
        self,
        image_input: Union[bytes, Path, np.ndarray],
        image_id: str,
        existing_mask: np.ndarray,
        points: Optional[List[Dict[str, Any]]] = None,
        brush_stroke: Optional[Dict[str, Any]] = None,
        display_dims: Optional[Tuple[int, int]] = None,
    ) -> Dict[str, Any]:
        """Routes mask refinement using positive/negative points or brush."""
        return self.sam2_service.refine_mask(
            image_input, image_id, existing_mask, points, brush_stroke, display_dims
        )

    def segment_objects_from_boxes(
        self,
        image_input: Union[bytes, Path, np.ndarray],
        image_id: str,
        proposals: List[Dict[str, Any]],
        engine_preference: str = "auto",
    ) -> List[Dict[str, Any]]:
        """
        Converts a list of Grounding DINO detection boxes into instance-level pixel masks.
        """
        results = []
        for prop in proposals:
            box = prop.get("box_2d")
            if not box or len(box) != 4:
                continue

            ymin, xmin, ymax, xmax = box
            box_1000 = [xmin, ymin, xmax, ymax]
            try:
                seg_res = self.segment_box(
                    image_input=image_input,
                    image_id=image_id,
                    box=box_1000,
                    engine_preference=engine_preference,
                    display_dims=(1000, 1000),
                )
                if seg_res.get("stats", {}).get("mask_pixel_count", 0) > 0:
                    results.append({
                        "id": prop.get("id"),
                        "label": prop.get("label"),
                        "category": prop.get("category", "other"),
                        "color": prop.get("color", "#4fd8c4"),
                        "confidence": prop.get("confidence", seg_res.get("confidence_score", 0.92)),
                        "stats": seg_res["stats"],
                        "contours": seg_res["contours"],
                        "rle": seg_res["rle"],
                        "mask_png_base64": seg_res["mask_png_base64"],
                        "box_2d": box,
                    })
            except Exception:
                continue

        return results


# Global singleton
_router_instance: Optional[SegmentationRouter] = None


def get_segmentation_router() -> SegmentationRouter:
    global _router_instance
    if _router_instance is None:
        _router_instance = SegmentationRouter()
    return _router_instance
