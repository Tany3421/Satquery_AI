"""
backend/services/segmentation/mask_processor.py
Mask Processing, Contour Extraction, Statistics, Topological Cleaning, and Geospatial Export.
"""

import base64
import io
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from PIL import Image

try:
    import cv2
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False

try:
    import tifffile
    HAS_TIFFFILE = True
except ImportError:
    HAS_TIFFFILE = False


class MaskProcessor:
    """Utility class for post-processing and topological refining of segmentation masks."""

    @staticmethod
    def clean_binary_mask(mask: np.ndarray, kernel_size: int = 3) -> np.ndarray:
        """Applies morphological smoothing and fills small pinholes."""
        bin_mask = (mask > 0).astype(np.uint8)
        if not HAS_CV2:
            return bin_mask

        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kernel_size, kernel_size))
        opened = cv2.morphologyEx(bin_mask, cv2.MORPH_OPEN, kernel)
        closed = cv2.morphologyEx(opened, cv2.MORPH_CLOSE, kernel)
        return closed

    @staticmethod
    def smooth_boundaries(mask: np.ndarray, kernel_size: int = 3) -> np.ndarray:
        """Regularizes jagged pixel edges along building boundaries, coastlines, and roads."""
        return MaskProcessor.clean_binary_mask(mask, kernel_size=kernel_size)

    @staticmethod
    def fill_holes(mask: np.ndarray, max_hole_area: int = 200) -> np.ndarray:
        """
        Fills internal enclosed voids/pinholes in segmentation masks
        (e.g., roof HVAC units, water reflections, canopy gaps) without altering outer boundaries.
        """
        bin_mask = (mask > 0).astype(np.uint8)
        if not HAS_CV2:
            return bin_mask

        # Use two-level contour hierarchy to find inner holes
        contours, hierarchy = cv2.findContours(
            bin_mask.copy(), cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE
        )
        if hierarchy is None:
            return bin_mask

        filled = bin_mask.copy()
        # hierarchy format: [Next, Previous, First_Child, Parent]
        for idx, h in enumerate(hierarchy[0]):
            parent_idx = h[3]
            if parent_idx != -1:  # Indicates an inner hole
                area = cv2.contourArea(contours[idx])
                if area <= max_hole_area:
                    cv2.drawContours(filled, contours, idx, color=1, thickness=-1)

        return filled

    @staticmethod
    def filter_small_components(mask: np.ndarray, min_area_pixels: int = 25) -> np.ndarray:
        """
        Eliminates tiny disconnected island noise pixels using connected-component analysis.
        """
        bin_mask = (mask > 0).astype(np.uint8)
        if not HAS_CV2:
            return bin_mask

        num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(
            bin_mask, connectivity=8
        )
        filtered = np.zeros_like(bin_mask)
        for label_idx in range(1, num_labels):
            area = stats[label_idx, cv2.CC_STAT_AREA]
            if area >= min_area_pixels:
                filtered[labels == label_idx] = 1

        return filtered

    @staticmethod
    def calculate_box_iou(box_a: List[int], box_b: List[int]) -> float:
        """
        Computes Intersection over Union (IoU) between two bounding boxes
        specified as [ymin, xmin, ymax, xmax].
        """
        y_top = max(box_a[0], box_b[0])
        x_left = max(box_a[1], box_b[1])
        y_bottom = min(box_a[2], box_b[2])
        x_right = min(box_a[3], box_b[3])

        if y_bottom <= y_top or x_right <= x_left:
            return 0.0

        inter_area = (y_bottom - y_top) * (x_right - x_left)
        area_a = (box_a[2] - box_a[0]) * (box_a[3] - box_a[1])
        area_b = (box_b[2] - box_b[0]) * (box_b[3] - box_b[1])
        union_area = area_a + area_b - inter_area

        return float(inter_area / max(union_area, 1))

    @staticmethod
    def calculate_mask_iou(mask_a: np.ndarray, mask_b: np.ndarray) -> float:
        """Computes pixel-level Intersection over Union between two binary masks."""
        bin_a = mask_a > 0
        bin_b = mask_b > 0
        intersection = np.logical_and(bin_a, bin_b).sum()
        union = np.logical_or(bin_a, bin_b).sum()
        if union == 0:
            return 0.0
        return float(intersection / union)

    @staticmethod
    def deduplicate_masks(
        regions: List[Dict[str, Any]],
        iou_threshold: float = 0.55,
    ) -> List[Dict[str, Any]]:
        """
        Non-Maximum Suppression (NMS) for overlapping instance segmentations.
        Suppresses duplicate candidate proposals targeting the same physical ground object.
        """
        if not regions:
            return []

        # Sort descending by confidence score, then by pixel area
        def sort_key(r):
            conf = float(r.get("confidence", 0.5))
            area = float(r.get("stats", {}).get("mask_pixel_count", 0))
            return (conf, area)

        sorted_regions = sorted(regions, key=sort_key, reverse=True)
        kept_regions = []

        for cand in sorted_regions:
            cand_box = cand.get("box_2d")
            cand_rle = cand.get("rle")
            is_dup = False

            for kept in kept_regions:
                # 1. Box IoU check (fast rejection)
                kept_box = kept.get("box_2d")
                if cand_box and kept_box:
                    b_iou = MaskProcessor.calculate_box_iou(cand_box, kept_box)
                    if b_iou > iou_threshold:
                        # 2. Detailed mask IoU check if RLE available
                        if cand_rle and kept.get("rle"):
                            m_cand = MaskProcessor.rle_to_mask(cand_rle)
                            m_kept = MaskProcessor.rle_to_mask(kept["rle"])
                            m_iou = MaskProcessor.calculate_mask_iou(m_cand, m_kept)
                            if m_iou > (iou_threshold - 0.10):
                                is_dup = True
                                break
                        else:
                            is_dup = True
                            break

            if not is_dup:
                kept_regions.append(cand)

        return kept_regions

    @staticmethod
    def assign_instance_ids(masks: List[np.ndarray]) -> np.ndarray:
        """
        Compiles multiple binary instance masks into a single 2D integer instance map
        where 0 is background and 1..N are unique instance IDs.
        """
        if not masks:
            return np.zeros((1, 1), dtype=np.int32)

        h, w = masks[0].shape[:2]
        instance_map = np.zeros((h, w), dtype=np.int32)

        for idx, m in enumerate(masks):
            inst_id = idx + 1
            instance_map[m > 0] = inst_id

        return instance_map

    @staticmethod
    def extract_contours(mask: np.ndarray, simplify: bool = True) -> List[List[List[float]]]:
        """
        Extracts polygon contours representing region boundaries.
        Returns list of polygons, each is a list of [x, y] coordinates.
        """
        bin_mask = (mask > 0).astype(np.uint8)
        if not HAS_CV2:
            return []

        contours, _ = cv2.findContours(bin_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        result = []

        for cnt in contours:
            if len(cnt) < 3:
                continue
            if cv2.contourArea(cnt) < 12:
                continue
            if simplify:
                arc_len = cv2.arcLength(cnt, True)
                epsilon = min(2.2, max(0.6, 0.002 * arc_len))
                cnt = cv2.approxPolyDP(cnt, epsilon, True)

            poly = []
            for pt in cnt:
                x = float(pt[0][0])
                y = float(pt[0][1])
                poly.append([round(x, 1), round(y, 1)])
            if len(poly) >= 3:
                result.append(poly)
        return result

    @staticmethod
    def mask_to_bbox(mask: np.ndarray) -> Optional[List[int]]:
        """Returns [ymin, xmin, ymax, xmax] of the non-zero mask pixels."""
        rows = np.any(mask > 0, axis=1)
        cols = np.any(mask > 0, axis=0)
        if not np.any(rows) or not np.any(cols):
            return None
        ymin, ymax = np.where(rows)[0][[0, -1]]
        xmin, xmax = np.where(cols)[0][[0, -1]]
        return [int(ymin), int(xmin), int(ymax), int(xmax)]

    @staticmethod
    def calculate_stats(mask: np.ndarray) -> Dict[str, Any]:
        """Calculates area, percentage, centroid, and bounding box."""
        h, w = mask.shape[:2]
        total_pixels = h * w
        mask_pixels = int(np.count_nonzero(mask > 0))
        area_pct = round((mask_pixels / max(total_pixels, 1)) * 100, 2)
        bbox = MaskProcessor.mask_to_bbox(mask)

        centroid = None
        if mask_pixels > 0:
            y_coords, x_coords = np.where(mask > 0)
            centroid = [float(np.mean(x_coords)), float(np.mean(y_coords))]

        return {
            "mask_pixel_count": mask_pixels,
            "total_pixels": total_pixels,
            "area_percentage": area_pct,
            "bounding_box": bbox,
            "centroid": centroid,
        }

    @staticmethod
    def mask_to_binary_png_bytes(mask: np.ndarray) -> bytes:
        """Converts mask to black/white binary PNG bytes."""
        bin_img = (mask > 0).astype(np.uint8) * 255
        pil_img = Image.fromarray(bin_img, mode="L")
        buf = io.BytesIO()
        pil_img.save(buf, format="PNG", optimize=True)
        return buf.getvalue()

    @staticmethod
    def mask_to_rgba_overlay_bytes(
        mask: np.ndarray,
        color_rgb: Tuple[int, int, int] = (79, 216, 196),
        opacity: float = 0.5,
    ) -> bytes:
        """Generates transparent RGBA overlay PNG bytes."""
        h, w = mask.shape[:2]
        rgba = np.zeros((h, w, 4), dtype=np.uint8)
        bin_mask = mask > 0

        r, g, b = color_rgb
        alpha = int(np.clip(opacity, 0.0, 1.0) * 255)

        rgba[bin_mask, 0] = r
        rgba[bin_mask, 1] = g
        rgba[bin_mask, 2] = b
        rgba[bin_mask, 3] = alpha

        pil_img = Image.fromarray(rgba, mode="RGBA")
        buf = io.BytesIO()
        pil_img.save(buf, format="PNG")
        return buf.getvalue()

    @staticmethod
    def mask_to_base64_png(mask: np.ndarray) -> str:
        """Encodes binary mask as base64 data URI."""
        png_bytes = MaskProcessor.mask_to_binary_png_bytes(mask)
        b64 = base64.b64encode(png_bytes).decode("utf-8")
        return f"data:image/png;base64,{b64}"

    @staticmethod
    def mask_to_rle(mask: np.ndarray) -> Dict[str, Any]:
        """Simple Run-Length Encoding for efficient network transport."""
        bin_mask = (mask > 0).astype(np.uint8).flatten(order="F")
        diffs = np.diff(bin_mask)
        change_indices = np.where(diffs != 0)[0] + 1
        runs = np.split(bin_mask, change_indices)
        counts = [len(run) for run in runs]

        # First count represents 0s; if mask starts with 1, prepend 0
        if len(bin_mask) > 0 and bin_mask[0] == 1:
            counts = [0] + counts

        return {
            "size": [int(mask.shape[0]), int(mask.shape[1])],
            "counts": counts,
        }

    @staticmethod
    def rle_to_mask(rle: Dict[str, Any]) -> np.ndarray:
        """Decodes RLE back into 2D numpy boolean array."""
        h, w = rle["size"]
        counts = rle["counts"]
        flat = []
        val = 0
        for cnt in counts:
            flat.extend([val] * cnt)
            val = 1 - val
        return np.array(flat, dtype=np.uint8).reshape((h, w), order="F")

    @staticmethod
    def export_geotiff_mask(
        mask: np.ndarray,
        reference_raster_meta: Dict[str, Any],
        output_path: Path,
    ) -> Path:
        """
        Saves the binary mask as a GeoTIFF, preserving spatial CRS,
        ModelTiepoint, and ModelPixelScale if present in the reference raster.
        """
        bin_mask = (mask > 0).astype(np.uint8) * 255
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if not HAS_TIFFFILE:
            # Fallback to standard Pillow TIFF
            pil_img = Image.fromarray(bin_mask, mode="L")
            pil_img.save(str(output_path), format="TIFF")
            return output_path

        # If we have geotiff metadata, attach tags
        extratags = []
        if reference_raster_meta:
            pixel_scale = reference_raster_meta.get("pixel_scale")
            tiepoints = reference_raster_meta.get("tiepoints")

            if pixel_scale and len(pixel_scale) >= 3:
                # 33550: ModelPixelScaleTag
                extratags.append((33550, "d", len(pixel_scale), tuple(pixel_scale), False))
            if tiepoints and len(tiepoints) >= 6:
                # 33922: ModelTiepointTag
                extratags.append((33922, "d", len(tiepoints), tuple(tiepoints), False))

        tifffile.imwrite(
            str(output_path),
            bin_mask,
            dtype=np.uint8,
            extratags=extratags if extratags else None,
        )
        return output_path
