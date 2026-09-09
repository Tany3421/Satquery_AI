"""
tests/test_interactive_segmentation.py
Automated end-to-end verification suite for SatQuery AI's SAM 2 Interactive Segmentation.
"""

import io
import json
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
from backend.services.segmentation import get_sam2_service, MaskProcessor, PromptProcessor


class TestInteractiveSegmentation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

        # Create synthetic test satellite image (300x300 RGB) with distinct features:
        # - Water pond at top-left (blue)
        # - Vegetation forest at center (green)
        # - Urban building at bottom-right (orange/gray)
        cls.img_arr = np.zeros((300, 300, 3), dtype=np.uint8)
        # Background: dry soil (tan)
        cls.img_arr[:, :] = [180, 160, 130]
        # Pond: (20:100, 20:100)
        cls.img_arr[20:100, 20:100] = [30, 90, 180]
        # Forest: (120:200, 120:200)
        cls.img_arr[120:200, 120:200] = [20, 160, 40]
        # Building: (220:280, 220:280)
        cls.img_arr[220:280, 220:280] = [210, 120, 40]

        buf = io.BytesIO()
        Image.fromarray(cls.img_arr).save(buf, format="JPEG")
        cls.img_bytes = buf.getvalue()

        # Save upload directly
        img_id, _, disp_path, _, _, _ = _save_upload(cls.img_bytes, "test_satellite.jpg")
        cls.image_id = img_id
        cls.image_url = f"/uploads/{disp_path.name}"
        print(f"Setup complete. Created test image_id={cls.image_id}")

    def test_01_health_and_existing_apis(self):
        """Verify that existing SatQuery AI functionality remains intact."""
        res = self.client.get("/api/health")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "ok")
        self.assertIn("sentinel2", data["data_sources"])

    def test_02_segment_status(self):
        """Verify SAM 2 model and execution device status endpoint."""
        res = self.client.get("/api/segment/status")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("engine", data)
        self.assertIn("device", data)
        self.assertIn("cached_embeddings_count", data)
        print(f"Status check passed: {data['engine']} on {data['device']}")

    def test_03_point_segmentation(self):
        """Test point prompt segmentation (clicking on water pond)."""
        res = self.client.post(
            "/api/segment/point",
            data={
                "image_id": self.image_id,
                "x": 60,
                "y": 60,
                "is_positive": "true",
                "label": "Water Pond",
                "color": "#3498db",
            },
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data["success"])
        self.assertGreater(data["stats"]["mask_pixel_count"], 0)
        self.assertIn("rle", data)
        self.assertIn("mask_png_base64", data)
        self.assertIn("contours", data)
        print(f"Point segmentation passed: area={data['stats']['mask_pixel_count']}px ({data['stats']['area_percentage']}%)")

    def test_04_box_segmentation(self):
        """Test bounding box prompt segmentation (around forest patch)."""
        res = self.client.post(
            "/api/segment/box",
            data={
                "image_id": self.image_id,
                "xmin": 115,
                "ymin": 115,
                "xmax": 205,
                "ymax": 205,
                "label": "Forest Canopy",
                "color": "#2ecc71",
            },
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data["success"])
        self.assertGreater(data["stats"]["mask_pixel_count"], 1000)
        self.assertEqual(len(data["prompt_coords"]["box"]), 4)
        print(f"Box segmentation passed: area={data['stats']['mask_pixel_count']}px")

    def test_05_polygon_segmentation(self):
        """Test polygon region constraint segmentation."""
        poly_pts = [[215, 215], [285, 215], [285, 285], [215, 285]]
        res = self.client.post(
            "/api/segment/polygon",
            data={
                "image_id": self.image_id,
                "points": json.dumps(poly_pts),
                "label": "Urban Footprint",
                "color": "#e67e22",
            },
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data["success"])
        self.assertGreater(data["stats"]["mask_pixel_count"], 500)
        print(f"Polygon segmentation passed: area={data['stats']['mask_pixel_count']}px")

    def test_06_mask_refine_brush(self):
        """Test mask refinement using manual erase brush stroke."""
        res_box = self.client.post(
            "/api/segment/box",
            data={"image_id": self.image_id, "xmin": 120, "ymin": 120, "xmax": 200, "ymax": 200},
        )
        init_mask_rle = res_box.json()["rle"]
        init_pixels = res_box.json()["stats"]["mask_pixel_count"]

        # Refine with erase brush
        brush = {"points": [[120, 160], [200, 160]], "radius": 8, "mode": "erase"}
        res_refine = self.client.post(
            "/api/segment/refine",
            data={
                "image_id": self.image_id,
                "mask_rle": json.dumps(init_mask_rle),
                "brush_stroke": json.dumps(brush),
            },
        )
        self.assertEqual(res_refine.status_code, 200)
        data = res_refine.json()
        self.assertTrue(data["success"])
        new_pixels = data["stats"]["mask_pixel_count"]
        self.assertLess(new_pixels, init_pixels)
        print(f"Refinement passed: {init_pixels}px reduced to {new_pixels}px")

    def test_07_text_based_highlighting(self):
        """Test Mode 2 — Natural-language AI Highlighting."""
        res = self.client.post(
            "/api/segment/text",
            data={"image_id": self.image_id, "query": "Highlight all water bodies"},
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data["success"])
        self.assertGreaterEqual(data["regions_count"], 1)
        first_reg = data["regions"][0]
        self.assertIn("label", first_reg)
        self.assertIn("color", first_reg)
        self.assertIn("contours", first_reg)
        self.assertIn("rle", first_reg)
        print(f"AI text highlighting passed: {data['regions_count']} region(s) detected for query.")

    def test_08_change_segmentation(self):
        """Test bi-temporal change segmentation."""
        after_arr = self.img_arr.copy()
        after_arr[120:200, 120:200] = [210, 180, 120]  # Forest cleared to bare soil
        buf_after = io.BytesIO()
        Image.fromarray(after_arr).save(buf_after, format="JPEG")
        after_bytes = buf_after.getvalue()

        after_id, _, _, _, _, _ = _save_upload(after_bytes, "after.jpg")

        res_change = self.client.post(
            "/api/segment/change",
            data={
                "before_image_id": self.image_id,
                "after_image_id": after_id,
                "query": "Highlight areas where vegetation decreased",
            },
        )
        self.assertEqual(res_change.status_code, 200)
        data = res_change.json()
        self.assertTrue(data["success"])
        self.assertIn("change_regions", data)
        self.assertIn("change_heatmap_url", data)
        print(f"Bi-temporal change segmentation passed: {len(data['change_regions'])} change region(s) generated.")

    def test_09_export_endpoints(self):
        """Test exporting segmentation mask to PNG composite, binary PNG, and GeoTIFF."""
        mask = np.zeros((100, 100), dtype=np.uint8)
        mask[20:60, 20:60] = 1
        rle = MaskProcessor.mask_to_rle(mask)

        # 1. Composite PNG
        res_png = self.client.post(
            "/api/segment/export",
            data={"image_id": self.image_id, "mask_rle": json.dumps(rle), "export_format": "png_overlay"},
        )
        self.assertEqual(res_png.status_code, 200)
        self.assertEqual(res_png.headers["content-type"], "image/png")

        # 2. Binary PNG
        res_bin = self.client.post(
            "/api/segment/export",
            data={"image_id": self.image_id, "mask_rle": json.dumps(rle), "export_format": "binary_png"},
        )
        self.assertEqual(res_bin.status_code, 200)
        self.assertEqual(res_bin.headers["content-type"], "image/png")

        # 3. GeoTIFF
        res_geo = self.client.post(
            "/api/segment/export",
            data={"image_id": self.image_id, "mask_rle": json.dumps(rle), "export_format": "geotiff"},
        )
        self.assertEqual(res_geo.status_code, 200)
        self.assertEqual(res_geo.headers["content-type"], "image/tiff")
        print("All 3 export formats (PNG composite, binary PNG, GeoTIFF) verified successfully.")

    def test_10_embedding_cache_performance(self):
        """Verify that embedding cache avoids reloading/recomputing image representations."""
        service = get_sam2_service()
        self.client.post("/api/segment/point", data={"image_id": self.image_id, "x": 50, "y": 50})
        self.client.post("/api/segment/point", data={"image_id": self.image_id, "x": 60, "y": 60})
        self.assertIn(self.image_id, service.embedding_cache)
        print(f"Embedding cache verified: image_id={self.image_id} cached successfully.")


if __name__ == "__main__":
    unittest.main()
