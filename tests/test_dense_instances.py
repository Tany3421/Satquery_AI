"""
tests/test_dense_instances.py
Verification test for Dense Grounding, Multi-Instance Segmentation,
and No Giant Coarse Polygon generation.
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
from fastapi.testclient import TestClient

from backend.main import app, _save_upload
from backend.services.segmentation.grounding_service import DenseGroundingService, calculate_iou, nms_boxes


class TestDenseInstances(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

        # Create a synthetic dense satellite image with 3 distinct buildings and 1 water canal
        cls.img_arr = np.zeros((400, 400, 3), dtype=np.uint8)
        # Background: dark soil / vegetation (30, 80, 40)
        cls.img_arr[:, :] = [30, 80, 40]

        # Building 1 (amber/concrete roof)
        cls.img_arr[30:70, 30:80] = [210, 180, 140]
        # Building 2 (another structure)
        cls.img_arr[120:170, 140:190] = [220, 190, 150]
        # Building 3 (third structure)
        cls.img_arr[240:290, 260:320] = [205, 175, 135]
        # Water canal (linear blue channel)
        cls.img_arr[340:370, 20:380] = [20, 70, 180]

        buf = io.BytesIO()
        Image.fromarray(cls.img_arr).save(buf, format="JPEG")
        cls.img_bytes = buf.getvalue()

        # Save upload directly without network latency
        img_id, _, disp_path, _, _, _ = _save_upload(cls.img_bytes, "dense_sat.jpg")
        cls.image_id = img_id

    def test_01_iou_and_nms(self):
        """Test IoU calculation and NMS suppression."""
        b1 = [100, 100, 200, 200]
        b2 = [110, 110, 210, 210]  # High overlap with b1
        b3 = [300, 300, 400, 400]  # Disjoint
        iou = calculate_iou(b1, b2)
        self.assertGreater(iou, 0.6)

        boxes = [
            {"box_2d": b1, "score": 0.95},
            {"box_2d": b2, "score": 0.85},
            {"box_2d": b3, "score": 0.90},
        ]
        suppressed = nms_boxes(boxes, iou_threshold=0.4)
        self.assertEqual(len(suppressed), 2)
        self.assertEqual(suppressed[0]["score"], 0.95)
        self.assertEqual(suppressed[1]["score"], 0.90)

    def test_02_dense_candidate_instance_detection(self):
        """Test candidate instance generation on synthetic dense satellite raster."""
        cands = DenseGroundingService.generate_candidate_instances(self.img_arr, "urban", max_instances=10)
        self.assertGreaterEqual(len(cands), 2)
        # Ensure individual boxes are discrete and not 80% coverage
        for c in cands:
            ymin, xmin, ymax, xmax = c["box_2d"]
            box_area_pct = ((ymax - ymin) * (xmax - xmin)) / 10000.0
            self.assertLess(box_area_pct, 40.0, "Candidate instance should not cover whole image")

    def test_03_text_query_discrete_buildings(self):
        """Test 'Highlight buildings' produces discrete building instances (Building 1, Building 2, ...)."""
        res = self.client.post(
            "/api/segment/text",
            data={"image_id": self.image_id, "query": "Highlight buildings"},
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data["success"])
        self.assertGreaterEqual(data["regions_count"], 2)

        labels = [r["label"] for r in data["regions"]]
        self.assertTrue(any("Building" in l for l in labels))

        # Verify pixel contours exist for each individual instance
        for r in data["regions"]:
            self.assertIn("contours", r)
            self.assertGreater(len(r["contours"]), 0)
            self.assertIn("stats", r)
            self.assertGreater(r["stats"]["mask_pixel_count"], 0)

    def test_04_text_query_water_body(self):
        """Test 'Highlight water' segments water correctly."""
        res = self.client.post(
            "/api/segment/text",
            data={"image_id": self.image_id, "query": "Highlight water"},
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data["success"])
        self.assertGreaterEqual(data["regions_count"], 1)
        first_water = data["regions"][0]
        self.assertEqual(first_water["category"], "water")
        self.assertIn(first_water["color"], ["#1e90ff", "#3498db"])

    def test_05_separate_physical_features_decomposition(self):
        """Test decomposing a coastal satellite scene into beach, ocean, roads, and buildings separately."""
        # Create a synthetic coastal scene:
        # Left (0:150): Urban zone with buildings & road
        # Mid (150:230): Sandy beach
        # Right (230:400): Ocean / sea water
        coastal_arr = np.zeros((400, 400, 3), dtype=np.uint8)
        # Ocean on right
        coastal_arr[:, 230:400] = [15, 60, 140]
        # Beach in middle (warm sand: R=210, G=180, B=130)
        coastal_arr[:, 150:230] = [210, 180, 130]
        # Urban background on left (dark soil/greens)
        coastal_arr[:, 0:150] = [40, 60, 40]
        # Road corridor running vertically in urban area
        coastal_arr[:, 70:90] = [100, 100, 105]
        # Buildings on left
        coastal_arr[30:80, 20:60] = [220, 140, 80]
        coastal_arr[150:200, 100:140] = [230, 150, 90]

        buf = io.BytesIO()
        Image.fromarray(coastal_arr).save(buf, format="JPEG")
        c_id, _, _, _, _, _ = _save_upload(buf.getvalue(), "coastal_sat.jpg")

        res = self.client.post(
            "/api/segment/text",
            data={"image_id": c_id, "query": "Highlight the beach, ocean, buildings, and roads separately."},
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data["success"])
        self.assertGreaterEqual(data["regions_count"], 2)

        categories = [r["category"] for r in data["regions"]]
        labels = [r["label"] for r in data["regions"]]
        # Ensure separate categories are recognized
        self.assertTrue(any(c in ("water", "ocean") for c in categories), f"Categories found: {categories}")
        self.assertTrue(any(c in ("beach", "sand") for c in categories), f"Categories found: {categories}")
        print(f"Decomposition passed. Categories detected separately: {categories}, labels: {labels}")


if __name__ == "__main__":
    unittest.main()
