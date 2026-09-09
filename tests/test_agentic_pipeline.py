"""
tests/test_agentic_pipeline.py
Comprehensive end-to-end integration test suite for the SatQuery AI Agentic Controller:
- Mode 1: Single Image VQA & BigEarthNet-19 Radiometric Adaptation
- Mode 2: Cross-Modal Optical + SAR Joint Information Fusion
- Mode 3: Bi-Temporal Change Detection & CDVQA Difference Grounding
- Auditable Execution Trace Verification (SIH26167 Compliance Target)
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

from aiml import bigearthnet, change_engine, engine
from aiml.orchestrator import AgenticOrchestrator, InputCompatibilityError, default_orchestrator
from aiml.tool_registry import (
    TASK_BITEMPORAL_CHANGE,
    TASK_CROSSMODAL_OPTICAL_SAR,
    TASK_SINGLE_VQA,
)


class TestAgenticPipeline(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # 1. Create synthetic Optical satellite image (256x256 RGB)
        # Left: Water (NDWI positive), Middle: Forest (NDVI positive), Right: Urban
        opt_arr = np.zeros((256, 256, 3), dtype=np.uint8)
        opt_arr[:, :80] = [20, 60, 150]       # Water
        opt_arr[:, 80:170] = [30, 160, 40]     # Forest / Vegetation
        opt_arr[:, 170:] = [180, 120, 100]    # Urban fabric
        opt_arr[50:100, 190:240] = [230, 230, 230]  # Bright concrete buildings

        opt_buf = io.BytesIO()
        Image.fromarray(opt_arr).save(opt_buf, format="JPEG")
        cls.optical_bytes = opt_buf.getvalue()

        # 2. Create synthetic SAR satellite image (256x256 single-channel / radar backscatter)
        # Water reflects away (dark < 35), Forest has moderate diffuse scatter, Urban has corner double-bounce (>200)
        sar_arr = np.full((256, 256), 110, dtype=np.uint8)
        sar_arr[:, :80] = 15                   # Smooth water specular absorption (low backscatter)
        sar_arr[:, 80:170] = 120               # Vegetation diffuse backscatter
        sar_arr[:, 170:] = 160                 # Built-up background
        sar_arr[50:100, 190:240] = 245         # Corner reflector double-bounce (intense radar return)

        sar_buf = io.BytesIO()
        Image.fromarray(sar_arr).convert("RGB").save(sar_buf, format="JPEG")
        cls.sar_bytes = sar_buf.getvalue()

        # 3. Create synthetic Bi-temporal T2 After image (new industrial structure in vegetation zone)
        after_arr = opt_arr.copy()
        after_arr[120:180, 90:150] = [240, 210, 180]  # New clearing & construction

        after_buf = io.BytesIO()
        Image.fromarray(after_arr).save(after_buf, format="JPEG")
        cls.after_bytes = after_buf.getvalue()

    def test_01_single_image_rs_adaptation(self):
        """Mode 1: Verify that BigEarthNet-19 classification & spectral radiometry are extracted."""
        features = bigearthnet.extract_radiometric_features(self.optical_bytes)
        self.assertIn("ben19_distribution", features)
        self.assertIn("radiometric_indices", features)
        self.assertIn("domain_summary", features)

        # Verify radiometric indices exist
        indices = features["radiometric_indices"]
        self.assertIn("ndvi_mean", indices)
        self.assertIn("ndwi_mean", indices)
        self.assertIn("ndbi_mean", indices)

        # Dispatch via orchestrator
        images = [{
            "filename": "sentinel2_scene.jpg",
            "preview_bytes": self.optical_bytes,
            "modality": "optical",
        }]
        res = default_orchestrator.dispatch(
            images=images,
            query="What land-cover types are present and what is the vegetation health?",
            input_mode="single",
            task_parameters={"engine_type": "offline"},
        )

        self.assertEqual(res["task"], TASK_SINGLE_VQA)
        self.assertIn("auditable_trace", res)
        trace = res["auditable_trace"]
        self.assertEqual(trace["selected_task"], TASK_SINGLE_VQA)
        self.assertIsNotNone(trace["rs_adaptation"])
        self.assertEqual(trace["rs_adaptation"]["status"], "CALIBRATED_BEN19")
        self.assertTrue(len(res.get("land_cover", [])) > 0)

    def test_02_crossmodal_optical_sar_fusion(self):
        """Mode 2: Verify complementary information extraction from Optical + SAR image pair."""
        images = [
            {"filename": "cartosat_optical.jpg", "preview_bytes": self.optical_bytes, "modality": "optical"},
            {"filename": "risat_sar.jpg", "preview_bytes": self.sar_bytes, "modality": "sar"},
        ]
        res = default_orchestrator.dispatch(
            images=images,
            query="Identify built-up and water bodies using both optical and SAR sensors.",
            input_mode="crossmodal",
        )

        self.assertEqual(res["task"], TASK_CROSSMODAL_OPTICAL_SAR)
        self.assertIn("crossmodal_fusion", res)
        fusion = res["crossmodal_fusion"]
        self.assertIn("sar_features", fusion)
        self.assertIn("optical_features", fusion)

        # Verify SAR specific metrics
        sar_f = fusion["sar_features"]
        self.assertTrue(sar_f["specular_water_percent"] > 0)
        self.assertTrue(sar_f["double_bounce_urban_percent"] > 0)

        # Verify trace
        trace = res["auditable_trace"]
        self.assertEqual(trace["selected_task"], TASK_CROSSMODAL_OPTICAL_SAR)
        self.assertEqual(trace["rs_adaptation"]["status"], "COMPLEMENTARY_FUSION_VERIFIED")

    def test_03_bitemporal_change_detection(self):
        """Mode 3: Verify difference heatmap generation, transition statistics, and CDVQA grounding."""
        images = [
            {"filename": "t1_before.jpg", "preview_bytes": self.optical_bytes, "modality": "optical", "label": "2023-01"},
            {"filename": "t2_after.jpg", "preview_bytes": self.after_bytes, "modality": "optical", "label": "2024-01"},
        ]
        res = default_orchestrator.dispatch(
            images=images,
            query="What changed between these two observation dates?",
            input_mode="bitemporal",
        )

        self.assertEqual(res["task"], TASK_BITEMPORAL_CHANGE)
        self.assertIn("heatmap_png_bytes", res)
        self.assertIsNotNone(res["heatmap_png_bytes"])
        self.assertIn("spatial_change_stats", res)

        stats = res["spatial_change_stats"]
        self.assertTrue(stats["total_changed_pixel_pct"] > 0.5)

        trace = res["auditable_trace"]
        self.assertEqual(trace["selected_task"], TASK_BITEMPORAL_CHANGE)
        self.assertEqual(trace["rs_adaptation"]["status"], "TEMPORAL_TRANSITION_CALCULATED")

    def test_04_input_compatibility_checker(self):
        """Verify strict input validation catches count and format mismatches."""
        # Bi-temporal requires 2 images, providing 1 should raise InputCompatibilityError
        single_img = [{"filename": "t1.jpg", "preview_bytes": self.optical_bytes, "modality": "optical"}]
        with self.assertRaises(InputCompatibilityError):
            default_orchestrator.dispatch(
                images=single_img,
                query="Compare changes",
                input_mode="bitemporal",
                task_override=TASK_BITEMPORAL_CHANGE,
            )


if __name__ == "__main__":
    unittest.main()
