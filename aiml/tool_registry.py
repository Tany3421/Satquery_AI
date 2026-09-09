"""
aiml/tool_registry.py
Predefined Specialist Tool Registry & Parameter Validation for SatQuery AI.

Adheres strictly to the SIH26167 Problem Statement:
- Predefined registry of remote sensing specialist models and tools.
- Strict permitted task parameters contract (no arbitrary parameters).
- Supports single-image VQA/captioning/grounding, bi-temporal change analysis,
  and cross-modal Optical + SAR fusion.
"""

from typing import Any, Dict, List, Optional


# Canonical Remote Sensing Tasks (Mandatory Functional Scope)
TASK_SINGLE_VQA = "TASK_SINGLE_VQA"
TASK_SCENE_CAPTIONING = "TASK_SCENE_CAPTIONING"
TASK_TEXT_GROUNDING = "TASK_TEXT_GROUNDING"
TASK_BITEMPORAL_CHANGE = "TASK_BITEMPORAL_CHANGE"
TASK_CROSSMODAL_OPTICAL_SAR = "TASK_CROSSMODAL_OPTICAL_SAR"

# Specialized Highlighting Subtasks
HIGHLIGHT_INTERACTIVE = "HIGHLIGHT_INTERACTIVE"
HIGHLIGHT_OBJECT = "HIGHLIGHT_OBJECT"
HIGHLIGHT_SEMANTIC = "HIGHLIGHT_SEMANTIC"
HIGHLIGHT_CHANGE = "HIGHLIGHT_CHANGE"

ALL_CANONICAL_TASKS = [
    TASK_SINGLE_VQA,
    TASK_SCENE_CAPTIONING,
    TASK_TEXT_GROUNDING,
    TASK_BITEMPORAL_CHANGE,
    TASK_CROSSMODAL_OPTICAL_SAR,
    HIGHLIGHT_INTERACTIVE,
    HIGHLIGHT_OBJECT,
    HIGHLIGHT_SEMANTIC,
    HIGHLIGHT_CHANGE,
]

TASK_DESCRIPTIONS = {
    TASK_SINGLE_VQA: "Single-Image Visual Question Answering on optical, multispectral, or SAR imagery.",
    TASK_SCENE_CAPTIONING: "Comprehensive remote sensing scene description & BigEarthNet land-cover breakdown.",
    TASK_TEXT_GROUNDING: "Text-guided visual object and spatial region grounding with 2D bounding boxes.",
    TASK_BITEMPORAL_CHANGE: "Multi-temporal bi-temporal pair change detection, change description, and CDVQA.",
    TASK_CROSSMODAL_OPTICAL_SAR: "Joint information extraction from co-registered Optical and SAR image pairs.",
    HIGHLIGHT_INTERACTIVE: "User-prompted interactive point/box/brush segmentation using SAM 2.1 or HQ-SAM.",
    HIGHLIGHT_OBJECT: "Instance-level discrete object detection and mask generation via Grounding DINO + HQ-SAM.",
    HIGHLIGHT_SEMANTIC: "Class-level remote sensing semantic segmentation (urban, water, vegetation, roads) via SegFormer / Mask2Former.",
    HIGHLIGHT_CHANGE: "Bi-temporal transition and change mask segmentation via ChangeFormer and temporal diff engine.",
}


# Predefined Registry of Specialist Models and Tools
TOOL_REGISTRY: Dict[str, Dict[str, Any]] = {
    "vqa_specialist": {
        "tool_name": "vqa_specialist",
        "description": "Remote sensing adapted vision-language reasoning engine for single-image VQA, RS captioning, and scene understanding.",
        "model_id": "GeoChat / EarthGPT (RS-VLM) + Gemini Synthesizer",
        "supported_tasks": [TASK_SINGLE_VQA, TASK_SCENE_CAPTIONING],
        "permitted_parameters": {
            "mode": {"type": str, "allowed": ["general", "agriculture", "disaster", "urban", "environment", "segmentation"], "default": "general"},
            "data_source": {"type": str, "allowed": ["sentinel2", "sentinel1", "bhuvan", "fusion"], "default": "sentinel2"},
            "temperature": {"type": float, "min": 0.0, "max": 1.0, "default": 0.2},
            "max_tokens": {"type": int, "min": 64, "max": 2048, "default": 512},
        },
    },
    "grounding_detector": {
        "tool_name": "grounding_detector",
        "description": "Open-vocabulary remote sensing object detector predicting discrete bounding boxes from natural language queries.",
        "model_id": "GeoChat-Grounding / Grounding-DINO-RS",
        "supported_tasks": [TASK_TEXT_GROUNDING, HIGHLIGHT_OBJECT],
        "permitted_parameters": {
            "box_threshold": {"type": float, "min": 0.1, "max": 0.95, "default": 0.35},
            "text_threshold": {"type": float, "min": 0.1, "max": 0.95, "default": 0.25},
            "nms_threshold": {"type": float, "min": 0.1, "max": 0.95, "default": 0.50},
            "max_instances": {"type": int, "min": 1, "max": 64, "default": 16},
        },
    },
    "interactive_segmenter": {
        "tool_name": "interactive_segmenter",
        "description": "Prompted pixel-level segmentation engine (Meta SAM 2.1) converting clicks and boxes into high-resolution masks.",
        "model_id": "SAM 2.1 (Segment Anything Model 2.1)",
        "supported_tasks": [HIGHLIGHT_INTERACTIVE, HIGHLIGHT_OBJECT],
        "permitted_parameters": {
            "engine_preference": {"type": str, "allowed": ["auto", "hq_sam", "sam2"], "default": "auto"},
            "multimask_output": {"type": bool, "default": False},
            "refine_iterations": {"type": int, "min": 1, "max": 5, "default": 2},
        },
    },
    "semantic_segmenter": {
        "tool_name": "semantic_segmenter",
        "description": "Remote sensing land-cover semantic segmenter (SegFormer / Mask2Former) predicting per-pixel class probability maps.",
        "model_id": "SegFormer-B2-RS / Mask2Former-Swin",
        "supported_tasks": [HIGHLIGHT_SEMANTIC],
        "permitted_parameters": {
            "target_classes": {"type": list, "default": ["urban", "water", "vegetation", "roads"]},
            "confidence_threshold": {"type": float, "min": 0.2, "max": 0.95, "default": 0.50},
            "min_region_pixels": {"type": int, "min": 10, "max": 5000, "default": 100},
        },
    },
    "change_segmenter": {
        "tool_name": "change_segmenter",
        "description": "Bi-temporal change segmentation engine (ChangeFormer) isolating newly constructed or modified geographic features.",
        "model_id": "ChangeFormer-V2-RS",
        "supported_tasks": [TASK_BITEMPORAL_CHANGE, HIGHLIGHT_CHANGE],
        "permitted_parameters": {
            "change_threshold": {"type": float, "min": 0.1, "max": 0.9, "default": 0.45},
            "target_object_filter": {"type": str, "allowed": ["all", "buildings", "infrastructure", "vegetation"], "default": "all"},
        },
    },
    "mask_processor": {
        "tool_name": "mask_processor",
        "description": "Post-processing pipeline: IoU NMS deduplication, hole filling, small-object removal, RLE, and contour vectorization.",
        "model_id": "RS-Mask-Processor",
        "supported_tasks": ALL_CANONICAL_TASKS,
        "permitted_parameters": {
            "iou_threshold": {"type": float, "min": 0.1, "max": 0.9, "default": 0.45},
            "min_area_pixels": {"type": int, "min": 4, "max": 2000, "default": 16},
            "simplify_epsilon": {"type": float, "min": 0.1, "max": 5.0, "default": 1.5},
        },
    },
    "grounding_specialist": {
        "tool_name": "grounding_specialist",
        "description": "Text-guided spatial region locator predicting normalized 2D bounding boxes for requested geographic features.",
        "model_id": "GeoChat / Grounding-DINO-RS",
        "supported_tasks": [TASK_TEXT_GROUNDING],
        "permitted_parameters": {
            "target_category": {"type": str, "allowed": ["water", "vegetation", "urban", "disaster", "infrastructure", "all"], "default": "all"},
            "confidence_threshold": {"type": float, "min": 0.1, "max": 0.99, "default": 0.65},
            "max_boxes": {"type": int, "min": 1, "max": 10, "default": 5},
            "coordinate_format": {"type": str, "allowed": ["normalized_1000", "pixel", "geojson"], "default": "normalized_1000"},
        },
    },
    "change_detection_specialist": {
        "tool_name": "change_detection_specialist",
        "description": "Bi-temporal change detection & CDVQA specialist analyzing spatial transitions between two observation dates.",
        "model_id": "CDVQA / Dedicated Temporal Change Model",
        "supported_tasks": [TASK_BITEMPORAL_CHANGE],
        "permitted_parameters": {
            "temporal_order": {"type": str, "allowed": ["chronological", "reverse"], "default": "chronological"},
            "anomaly_sensitivity": {"type": str, "allowed": ["conservative", "moderate", "high"], "default": "moderate"},
            "generate_spatial_mask": {"type": bool, "default": True},
        },
    },
    "optical_sar_fusion_specialist": {
        "tool_name": "optical_sar_fusion_specialist",
        "description": "Cross-modal information extraction combining Optical spectral reflectance with SAR microwave backscatter.",
        "model_id": "EarthGPT / Dedicated Optical+SAR Fusion",
        "supported_tasks": [TASK_CROSSMODAL_OPTICAL_SAR],
        "permitted_parameters": {
            "sar_polarization": {"type": str, "allowed": ["VV", "VH", "VV/VH", "dual"], "default": "VV/VH"},
            "cloud_penetration_enabled": {"type": bool, "default": True},
            "fusion_level": {"type": str, "allowed": ["feature_level", "decision_level"], "default": "feature_level"},
        },
    },
    "raster_metadata_specialist": {
        "tool_name": "raster_metadata_specialist",
        "description": "Geospatial TIFF raster inspector extracting CRS, ModelTiepoint bounds, and multi-band statistics.",
        "model_id": "GeoTIFF-Raster-Inspector",
        "supported_tasks": ALL_CANONICAL_TASKS,
        "permitted_parameters": {
            "extract_crs": {"type": bool, "default": True},
            "percentile_bounds": {"type": list, "default": [2.0, 98.0]},
        },
    },
}


class ParameterValidationError(Exception):
    pass


def validate_permitted_parameters(
    tool_name: str,
    passed_params: Optional[Dict[str, Any]] = None,
    strict_filter: bool = True
) -> Dict[str, Any]:
    """
    Validates that ONLY permitted task parameters are used and assigns strict defaults.
    If strict_filter is True, parameters intended for other tools are ignored and only
    permitted parameters are extracted and validated.
    """
    if tool_name not in TOOL_REGISTRY:
        raise ParameterValidationError(f"Tool '{tool_name}' is not registered in TOOL_REGISTRY.")

    permitted_spec = TOOL_REGISTRY[tool_name]["permitted_parameters"]
    configured_params = {}
    passed_params = passed_params or {}

    # Check unpermitted parameters if not filtering
    if not strict_filter:
        for param_name in passed_params:
            if param_name not in permitted_spec:
                raise ParameterValidationError(
                    f"Parameter '{param_name}' is not permitted for tool '{tool_name}'. "
                    f"Permitted parameters: {list(permitted_spec.keys())}"
                )

    # Validate and assign permitted parameters
    for param_name, spec in permitted_spec.items():
        if param_name in passed_params:
            val = passed_params[param_name]
            expected_type = spec["type"]

            # Type check
            if not isinstance(val, expected_type):
                try:
                    val = expected_type(val)
                except (ValueError, TypeError):
                    raise ParameterValidationError(
                        f"Parameter '{param_name}' for '{tool_name}' must be of type {expected_type.__name__}."
                    )

            # Allowed set check
            if "allowed" in spec and val not in spec["allowed"]:
                raise ParameterValidationError(
                    f"Invalid value '{val}' for parameter '{param_name}'. Must be one of {spec['allowed']}."
                )

            # Range checks
            if "min" in spec and val < spec["min"]:
                raise ParameterValidationError(
                    f"Parameter '{param_name}' value {val} is below minimum {spec['min']}."
                )
            if "max" in spec and val > spec["max"]:
                raise ParameterValidationError(
                    f"Parameter '{param_name}' value {val} exceeds maximum {spec['max']}."
                )

            configured_params[param_name] = val
        else:
            configured_params[param_name] = spec["default"]

    return configured_params


def get_tools_for_task(task: str) -> List[Dict[str, Any]]:
    """Returns all registered specialist tools capable of fulfilling the given task."""
    tools = []
    for tool_name, tool_info in TOOL_REGISTRY.items():
        if task in tool_info["supported_tasks"]:
            tools.append(tool_info)
    return tools
