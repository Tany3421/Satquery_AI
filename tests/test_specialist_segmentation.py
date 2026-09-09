"""
tests/test_specialist_segmentation.py
Unit and integration tests for Batch 2:
- SemanticSegmentationService (SegFormer / Mask2Former RS paradigm)
- ChangeSegmentationService (Bi-temporal difference & SAM 2.1 change masks)
- MaskProcessor enhancements (Box & Mask IoU, NMS deduplication, hole filling, small component pruning, instance IDs)
"""

import io
import sys
import unittest
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np
from PIL import Image

from backend.services.segmentation.semantic_service import get_semantic_segmentation_service
from backend.services.segmentation.change_segmentation_service import get_change_segmentation_service
from backend.services.segmentation.mask_processor import MaskProcessor
from aiml.highlight_router import (
    classify_highlight_subtask,
    HIGHLIGHT_CHANGE,
    HIGHLIGHT_OBJECT,
    HIGHLIGHT_SEMANTIC,
    HIGHLIGHT_INTERACTIVE,
)


class TestSpecialistSegmentation(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Create synthetic synthetic satellite image (300x300 RGB)
        # Left half: water (blueish), Middle strip: beach (sand/yellow), Right half: vegetation & urban
        arr = np.zeros((300, 300, 3), dtype=np.uint8)
        # Water area (left 100 cols)
        arr[:, :100] = [20, 60, 140]
        # Beach strip (cols 100 to 130)
        arr[:, 100:130] = [210, 180, 130]
        # Vegetation area (cols 130 to 220)
        arr[:, 130:220] = [35, 150, 45]
        # Urban / Built-up area with bright roof structures (cols 220 to 300)
        arr[:, 220:300] = [170, 120, 95]
        # Draw high contrast building blocks in urban zone
        arr[40:90, 230:280] = [220, 220, 220]
        arr[140:190, 230:280] = [210, 210, 210]

        img = Image.fromarray(arr)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        cls.test_image_bytes = buf.getvalue()
        cls.test_rgb = arr

        # Create "After" image with new construction in vegetation zone
        arr_after = arr.copy()
        arr_after[50:110, 140:200] = [230, 210, 190]  # New building where vegetation was
        img_after = Image.fromarray(arr_after)
        buf_after = io.BytesIO()
        img_after.save(buf_after, format="PNG")
        cls.test_after_bytes = buf_after.getvalue()

    def test_01_highlight_router_intent(self):
        """Test subtask classifier routing accuracy."""
        sub, conf, meta = classify_highlight_subtask("Highlight urban area")
        self.assertEqual(sub, HIGHLIGHT_SEMANTIC)

        sub, conf, meta = classify_highlight_subtask("Highlight water bodies")
        self.assertEqual(sub, HIGHLIGHT_SEMANTIC)

        sub, conf, meta = classify_highlight_subtask("Highlight all buildings")
        self.assertEqual(sub, HIGHLIGHT_OBJECT)

        sub, conf, meta = classify_highlight_subtask("Highlight newly constructed buildings", is_bitemporal=True)
        self.assertEqual(sub, HIGHLIGHT_CHANGE)

        sub, conf, meta = classify_highlight_subtask(has_interactive_prompts=True)
        self.assertEqual(sub, HIGHLIGHT_INTERACTIVE)

    def test_02_semantic_service_classes(self):
        """Test RS Semantic Segmentation service class extraction."""
        service = get_semantic_segmentation_service()
        status = service.get_status()
        self.assertIn("supported_classes", status)
        self.assertIn("water", status["supported_classes"])
        self.assertIn("vegetation", status["supported_classes"])

        # Segment water
        water_res = service.segment_class(self.test_rgb, "water")
        self.assertIsNotNone(water_res)
        self.assertEqual(water_res["category"], "water")
        self.assertGreater(water_res["stats"]["mask_pixel_count"], 500)
        self.assertIn("contours", water_res)
        self.assertIn("rle", water_res)

        # Segment vegetation
        veg_res = service.segment_class(self.test_rgb, "vegetation")
        self.assertIsNotNone(veg_res)
        self.assertEqual(veg_res["category"], "vegetation")
        self.assertGreater(veg_res["stats"]["mask_pixel_count"], 500)

        # Multi-class scene segmentation
        scene_res = service.segment_scene(self.test_rgb, min_area_pct=1.0)
        self.assertGreaterEqual(len(scene_res), 2)
        categories = [r["category"] for r in scene_res]
        self.assertIn("water", categories)

    def test_03_change_segmentation_service(self):
        """Test Bi-temporal Change Detection and SAM 2.1 mask generation."""
        change_service = get_change_segmentation_service()
        res = change_service.detect_changes(
            before_input=self.test_image_bytes,
            after_input=self.test_after_bytes,
            after_image_id="test-change-id",
            query="Highlight new construction",
        )

        self.assertTrue(res["success"])
        stats = res["spatial_change_stats"]
        self.assertGreater(stats["total_changed_percent"], 0.5)
        self.assertIn("heatmap_png_bytes", res)
        self.assertGreater(len(res["heatmap_png_bytes"]), 100)
        self.assertIn("change_regions", res)

    def test_04_mask_processor_iou_and_nms(self):
        """Test Box IoU, Mask IoU, and NMS deduplication."""
        # Box IoU
        b1 = [10, 10, 50, 50]
        b2 = [10, 10, 50, 50]  # Identical
        b3 = [60, 60, 100, 100]  # Non-overlapping
        self.assertAlmostEqual(MaskProcessor.calculate_box_iou(b1, b2), 1.0, places=2)
        self.assertAlmostEqual(MaskProcessor.calculate_box_iou(b1, b3), 0.0, places=2)

        # Mask IoU
        m1 = np.zeros((50, 50), dtype=np.uint8)
        m1[10:30, 10:30] = 1
        m2 = m1.copy()
        m3 = np.zeros((50, 50), dtype=np.uint8)
        m3[35:45, 35:45] = 1
        self.assertAlmostEqual(MaskProcessor.calculate_mask_iou(m1, m2), 1.0, places=2)
        self.assertAlmostEqual(MaskProcessor.calculate_mask_iou(m1, m3), 0.0, places=2)

        # Deduplicate masks
        rle1 = MaskProcessor.mask_to_rle(m1)
        rle2 = MaskProcessor.mask_to_rle(m2)
        regions = [
            {"id": "cand-1", "confidence": 0.95, "box_2d": [10, 10, 30, 30], "rle": rle1, "stats": {"mask_pixel_count": 400}},
            {"id": "cand-2", "confidence": 0.90, "box_2d": [10, 10, 30, 30], "rle": rle2, "stats": {"mask_pixel_count": 400}},  # Duplicate
            {"id": "cand-3", "confidence": 0.88, "box_2d": [35, 35, 45, 45], "rle": MaskProcessor.mask_to_rle(m3), "stats": {"mask_pixel_count": 100}},
        ]
        kept = MaskProcessor.deduplicate_masks(regions, iou_threshold=0.5)
        self.assertEqual(len(kept), 2)
        kept_ids = [k["id"] for k in kept]
        self.assertIn("cand-1", kept_ids)
        self.assertIn("cand-3", kept_ids)
        self.assertNotIn("cand-2", kept_ids)

    def test_05_mask_processor_hole_filling_and_filtering(self):
        """Test topological hole filling and small component pruning."""
        # Create mask with an enclosed hole
        mask = np.zeros((60, 60), dtype=np.uint8)
        mask[10:50, 10:50] = 1
        mask[20:30, 20:30] = 0  # 10x10 = 100 pixel hole

        filled = MaskProcessor.fill_holes(mask, max_hole_area=150)
        self.assertEqual(filled[25, 25], 1, "Inner hole should be filled")

        # Create mask with tiny noise components
        noise_mask = np.zeros((60, 60), dtype=np.uint8)
        noise_mask[10:40, 10:40] = 1  # Big component (900 px)
        noise_mask[2, 2] = 1          # 1 px noise
        noise_mask[5, 5:8] = 1        # 3 px noise

        pruned = MaskProcessor.filter_small_components(noise_mask, min_area_pixels=15)
        self.assertEqual(pruned[2, 2], 0, "1 px noise should be pruned")
        self.assertEqual(pruned[5, 6], 0, "3 px noise should be pruned")
        self.assertEqual(pruned[20, 20], 1, "Big component should be preserved")

        # Test assign_instance_ids
        m_a = np.zeros((40, 40), dtype=np.uint8)
        m_a[5:15, 5:15] = 1
        m_b = np.zeros((40, 40), dtype=np.uint8)
        m_b[20:30, 20:30] = 1

        inst_map = MaskProcessor.assign_instance_ids([m_a, m_b])
        self.assertEqual(inst_map[10, 10], 1)
        self.assertEqual(inst_map[25, 25], 2)
        self.assertEqual(inst_map[0, 0], 0)


if __name__ == "__main__":
    unittest.main()
