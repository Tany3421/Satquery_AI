"""
backend/services/segmentation/__init__.py
Segmentation services package for SatQuery AI.
"""

from .sam2_service import get_sam2_service
from .mask_processor import MaskProcessor
from .prompt_processor import PromptProcessor
from .grounding_service import DenseGroundingService
from .grounding_dino_service import GroundingDINOService, get_grounding_dino_service
from .segmentation_router import SegmentationRouter, get_segmentation_router
from .semantic_service import SemanticSegmentationService, get_semantic_segmentation_service
from .change_segmentation_service import ChangeSegmentationService, get_change_segmentation_service

__all__ = [
    "get_sam2_service",
    "MaskProcessor",
    "PromptProcessor",
    "DenseGroundingService",
    "GroundingDINOService",
    "get_grounding_dino_service",
    "SegmentationRouter",
    "get_segmentation_router",
    "SemanticSegmentationService",
    "get_semantic_segmentation_service",
    "ChangeSegmentationService",
    "get_change_segmentation_service",
]
