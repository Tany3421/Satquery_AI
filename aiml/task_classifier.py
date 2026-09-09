"""
aiml/task_classifier.py
Task Intent Interpretation & Query Classifier for SatQuery AI.

Interprets the natural-language query and input configuration (single image,
cross-modal pair, or bi-temporal pair) to route to the appropriate canonical task.
"""

import re
from typing import Any, Dict, Tuple

from .tool_registry import (
    TASK_BITEMPORAL_CHANGE,
    TASK_CROSSMODAL_OPTICAL_SAR,
    TASK_SCENE_CAPTIONING,
    TASK_SINGLE_VQA,
    TASK_TEXT_GROUNDING,
)


GROUNDING_KEYWORDS = [
    r"\bhighlight\b",
    r"\blocate\b",
    r"\bpinpoint\b",
    r"\bwhere is\b",
    r"\bwhere are\b",
    r"\bbounding box\b",
    r"\bfind the\b",
    r"\bshow me the\b",
    r"\bmark the\b",
    r"\bdetect\b",
    r"\bgrounding\b",
]

CAPTIONING_KEYWORDS = [
    r"\bdescribe\b",
    r"\bcaption\b",
    r"\boverview\b",
    r"\bsummarize\b",
    r"\bscene description\b",
    r"\bland[- ]cover breakdown\b",
    r"\bwhat does this scene contain\b",
    r"\bgeneral description\b",
]

CHANGE_KEYWORDS = [
    r"\bchange\b",
    r"\bchanged\b",
    r"\bdifference\b",
    r"\bbefore and after\b",
    r"\btemporal\b",
    r"\bbetween these two\b",
    r"\bover time\b",
    r"\bincreased or decreased\b",
    r"\bexpansion\b",
]

CROSSMODAL_KEYWORDS = [
    r"\boptical and sar\b",
    r"\bsar and optical\b",
    r"\bradar and optical\b",
    r"\boptical and radar\b",
    r"\bboth images\b",
    r"\btogether\b",
    r"\bcloud penetration\b",
    r"\bbackscatter and spectral\b",
    r"\bcross[- ]modal\b",
    r"\bjoint\b",
]


def classify_task(
    query: str,
    input_config: Dict[str, Any],
) -> Tuple[str, float, str]:
    """
    Interprets the user's natural language query and input configuration.

    Args:
        query: User question or natural language instruction.
        input_config: Dict with metadata like:
            - image_count: int (1 or 2)
            - input_mode: str ("single", "bitemporal", "crossmodal", or "auto")
            - modalities: list of str (e.g. ["optical", "sar"] or ["optical", "optical"])

    Returns:
        tuple (selected_task, confidence_score, classification_rationale)
    """
    q_lower = (query or "").lower().strip()
    image_count = input_config.get("image_count", 1)
    input_mode = input_config.get("input_mode", "auto")
    modalities = [m.lower() for m in input_config.get("modalities", [])]

    # Rule 1: Explicit Cross-Modal Pair input configuration
    if input_mode == "crossmodal" or ("optical" in modalities and "sar" in modalities):
        return (
            TASK_CROSSMODAL_OPTICAL_SAR,
            0.98,
            "Detected paired cross-modal optical + SAR observation input.",
        )

    # Rule 2: Explicit Bi-Temporal Pair input configuration
    if input_mode == "bitemporal" or (image_count == 2 and "crossmodal" not in input_mode):
        return (
            TASK_BITEMPORAL_CHANGE,
            0.96,
            "Detected bi-temporal image pair for temporal change detection.",
        )

    # Rule 3: Query explicitly references Optical + SAR fusion with 2 images
    if image_count == 2:
        for pattern in CROSSMODAL_KEYWORDS:
            if re.search(pattern, q_lower):
                return (
                    TASK_CROSSMODAL_OPTICAL_SAR,
                    0.95,
                    f"Query matched cross-modal reasoning intent ('{pattern}').",
                )
        return (
            TASK_BITEMPORAL_CHANGE,
            0.90,
            "Defaulted dual-image input to bi-temporal change analysis.",
        )

    # Rule 4: Single image - check for Text-Guided Spatial Grounding
    for pattern in GROUNDING_KEYWORDS:
        if re.search(pattern, q_lower):
            return (
                TASK_TEXT_GROUNDING,
                0.93,
                f"Query matched spatial region grounding intent ('{pattern}').",
            )

    # Rule 5: Single image - check for Scene Captioning
    for pattern in CAPTIONING_KEYWORDS:
        if re.search(pattern, q_lower):
            return (
                TASK_SCENE_CAPTIONING,
                0.91,
                f"Query matched comprehensive scene captioning intent ('{pattern}').",
            )

    # Rule 6: Default single image baseline is Visual Question Answering
    return (
        TASK_SINGLE_VQA,
        0.88,
        "Query interpreted as single-image domain Visual Question Answering.",
    )
