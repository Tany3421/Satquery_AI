"""
aiml/highlight_router.py
Highlight Task & Specialist Router for SatQuery AI.

Classifies natural language highlighting and segmentation intents:
1. HIGHLIGHT_INTERACTIVE: User-supplied interactive point, box, or brush prompt
2. HIGHLIGHT_OBJECT: Countable discrete instances ("buildings", "ships", "planes", "runways")
3. HIGHLIGHT_SEMANTIC: Land-cover semantic classes ("urban area", "vegetation", "water", "roads")
4. HIGHLIGHT_CHANGE: Multi-temporal modifications ("newly constructed buildings", "flood damage")
"""

import re
from typing import Any, Dict, List, Optional, Tuple

from .tool_registry import (
    HIGHLIGHT_CHANGE,
    HIGHLIGHT_INTERACTIVE,
    HIGHLIGHT_OBJECT,
    HIGHLIGHT_SEMANTIC,
)


OBJECT_KEYWORDS = {
    "building", "buildings", "house", "houses", "structure", "structures",
    "ship", "ships", "vessel", "vessels", "boat", "boats",
    "plane", "planes", "aircraft", "airplane", "airplanes",
    "runway", "runways", "airfield", "bridge", "bridges",
    "storage tank", "tanks", "pier", "dock", "docks", "car", "cars", "vehicle", "vehicles",
}

SEMANTIC_KEYWORDS = {
    "urban", "built-up", "settlement", "city",
    "vegetation", "canopy", "forest", "trees", "crop", "agriculture", "grassland",
    "water", "water body", "ocean", "sea", "bay", "lake", "river", "reservoir",
    "beach", "sand", "coastline", "shoreline", "coast",
    "road", "roads", "highway", "transit", "street", "corridor", "pavement",
    "bare soil", "mud", "wetland",
}

CHANGE_KEYWORDS = {
    "newly", "constructed", "built", "demolished", "destroyed",
    "changed", "change", "difference", "before", "after", "temporal",
    "expansion", "encroachment", "disaster damage", "flood extent",
}


def classify_highlight_subtask(
    query: str = "",
    has_interactive_prompts: bool = False,
    is_bitemporal: bool = False,
) -> Tuple[str, float, Dict[str, Any]]:
    """
    Determines the appropriate highlighting subtask and specialist toolchain.

    Returns:
        (subtask_type, confidence_score, routing_metadata)
    """
    q_lower = (query or "").lower().strip()

    # 1. Interactive clicks/boxes always take precedence
    if has_interactive_prompts:
        return HIGHLIGHT_INTERACTIVE, 1.0, {
            "subtask": HIGHLIGHT_INTERACTIVE,
            "pipeline": ["interactive_segmenter", "mask_processor"],
            "primary_model": "SAM 2.1 / HQ-SAM",
            "reason": "Direct user interactive prompt provided.",
        }

    # 2. Bi-temporal change queries
    if is_bitemporal or any(k in q_lower for k in CHANGE_KEYWORDS):
        return HIGHLIGHT_CHANGE, 0.95, {
            "subtask": HIGHLIGHT_CHANGE,
            "pipeline": ["change_segmenter", "grounding_detector", "interactive_segmenter", "mask_processor"],
            "primary_model": "ChangeFormer + Grounding DINO + HQ-SAM",
            "reason": "Temporal comparison or change keyword detected in query.",
        }

    # 3. Discrete instance object queries ("buildings", "ships", "planes", "individual")
    words = set(re.findall(r"\b\w+\b", q_lower))
    has_object_kw = bool(words.intersection(OBJECT_KEYWORDS)) or any(k in q_lower for k in ["each", "individual", "every building"])
    has_semantic_kw = bool(words.intersection(SEMANTIC_KEYWORDS))

    if has_object_kw:
        return HIGHLIGHT_OBJECT, 0.92, {
            "subtask": HIGHLIGHT_OBJECT,
            "pipeline": ["grounding_detector", "interactive_segmenter", "mask_processor"],
            "primary_model": "Grounding DINO + HQ-SAM / SAM 2.1",
            "reason": "Discrete object instance targets identified in query.",
        }

    # 4. Land-cover / semantic class regions
    if has_semantic_kw or any(w in q_lower for w in ["area", "land cover", "water", "roads", "vegetation"]):
        return HIGHLIGHT_SEMANTIC, 0.90, {
            "subtask": HIGHLIGHT_SEMANTIC,
            "pipeline": ["semantic_segmenter", "mask_processor"],
            "primary_model": "SegFormer / Mask2Former RS",
            "reason": "Continuous geographic semantic class identified in query.",
        }

    # Default fallback: Object grounding
    return HIGHLIGHT_OBJECT, 0.80, {
        "subtask": HIGHLIGHT_OBJECT,
        "pipeline": ["grounding_detector", "interactive_segmenter", "mask_processor"],
        "primary_model": "Grounding DINO + HQ-SAM",
        "reason": "General entity grounding default.",
    }
