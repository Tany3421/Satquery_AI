"""
backend/services/segmentation/prompt_processor.py
Prompt translation, coordinate mapping, and geometric validation for SAM 2.
"""

from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np

try:
    import cv2
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False


class PromptProcessor:
    """Helper for converting frontend user interactions into SAM 2 prompts."""

    @staticmethod
    def map_coord(
        x: float,
        y: float,
        from_dims: Optional[Tuple[int, int]],
        to_dims: Tuple[int, int],
    ) -> Tuple[int, int]:
        """
        Maps a 2D point (x, y) from source dimensions to target dimensions.
        Handles normalized coords (0-1 or 0-1000) and display pixel coords.
        to_dims is (height, width).
        """
        to_h, to_w = to_dims

        if from_dims == (1000, 1000):
            target_x = int(round((x / 1000.0) * (to_w - 1)))
            target_y = int(round((y / 1000.0) * (to_h - 1)))
        elif from_dims is not None and from_dims != (to_h, to_w):
            from_h, from_w = from_dims
            scale_x = to_w / max(from_w, 1)
            scale_y = to_h / max(from_h, 1)
            target_x = int(round(x * scale_x))
            target_y = int(round(y * scale_y))
        elif from_dims is None and 0.0 <= x <= 1.0 and 0.0 <= y <= 1.0 and (isinstance(x, float) or isinstance(y, float)) and (x < 1.0 or y < 1.0):
            target_x = int(round(x * (to_w - 1)))
            target_y = int(round(y * (to_h - 1)))
        else:
            target_x = int(round(x))
            target_y = int(round(y))

        # Clamp to bounds
        target_x = max(0, min(to_w - 1, target_x))
        target_y = max(0, min(to_h - 1, target_y))
        return target_x, target_y

    @staticmethod
    def map_box(
        box: List[float],
        from_dims: Optional[Tuple[int, int]],
        to_dims: Tuple[int, int],
    ) -> List[int]:
        """
        Maps box [xmin, ymin, xmax, ymax] or [ymin, xmin, ymax, xmax] to target coords [xmin, ymin, xmax, ymax].
        """
        to_h, to_w = to_dims
        b = [float(v) for v in box]

        if len(b) != 4:
            raise ValueError(f"Expected 4 box coordinates, received: {box}")

        # Check if box is in VLM normalized format [ymin, xmin, ymax, xmax]
        # In SatQuery AI grounding, VLM returns [ymin, xmin, ymax, xmax] in 0-1000
        # While frontend user box draw sends [xmin, ymin, xmax, ymax]
        x1, y1 = PromptProcessor.map_coord(b[0], b[1], from_dims, to_dims)
        x2, y2 = PromptProcessor.map_coord(b[2], b[3], from_dims, to_dims)

        xmin, xmax = min(x1, x2), max(x1, x2)
        ymin, ymax = min(y1, y2), max(y1, y2)

        # Ensure box has non-zero area
        if xmax <= xmin:
            xmax = min(to_w - 1, xmin + 5)
        if ymax <= ymin:
            ymax = min(to_h - 1, ymin + 5)

        return [int(xmin), int(ymin), int(xmax), int(ymax)]

    @staticmethod
    def map_polygon(
        points: List[List[float]],
        from_dims: Optional[Tuple[int, int]],
        to_dims: Tuple[int, int],
    ) -> List[List[int]]:
        """Maps a list of polygon vertices [[x1, y1], [x2, y2], ...] to target coords."""
        mapped = []
        for pt in points:
            if len(pt) >= 2:
                mx, my = PromptProcessor.map_coord(pt[0], pt[1], from_dims, to_dims)
                mapped.append([mx, my])
        return mapped

    @staticmethod
    def polygon_to_mask(
        polygon: List[List[int]],
        dims: Tuple[int, int],
    ) -> np.ndarray:
        """Rasterizes a closed polygon into a binary mask of shape (H, W)."""
        h, w = dims
        mask = np.zeros((h, w), dtype=np.uint8)
        if len(polygon) < 3:
            return mask

        pts = np.array(polygon, dtype=np.int32).reshape((-1, 1, 2))
        if HAS_CV2:
            cv2.fillPoly(mask, [pts], color=1)
        else:
            # Fallback simple bounding box fill if cv2 is absent
            xmin = min(p[0] for p in polygon)
            xmax = max(p[0] for p in polygon)
            ymin = min(p[1] for p in polygon)
            ymax = max(p[1] for p in polygon)
            mask[ymin:ymax, xmin:xmax] = 1

        return mask

    @staticmethod
    def rasterize_brush_stroke(
        stroke_points: List[List[int]],
        radius: int,
        dims: Tuple[int, int],
    ) -> np.ndarray:
        """Rasterizes a brush stroke path into a binary mask with given brush radius."""
        h, w = dims
        mask = np.zeros((h, w), dtype=np.uint8)
        if not stroke_points:
            return mask

        r = max(1, int(radius))
        if HAS_CV2:
            for i in range(len(stroke_points)):
                pt = stroke_points[i]
                cv2.circle(mask, (int(pt[0]), int(pt[1])), r, color=1, thickness=-1)
                if i > 0:
                    prev_pt = stroke_points[i - 1]
                    cv2.line(mask, (int(prev_pt[0]), int(prev_pt[1])), (int(pt[0]), int(pt[1])), color=1, thickness=r * 2)
        else:
            for pt in stroke_points:
                px, py = int(pt[0]), int(pt[1])
                y0, y1 = max(0, py - r), min(h, py + r + 1)
                x0, x1 = max(0, px - r), min(w, px + r + 1)
                mask[y0:y1, x0:x1] = 1

        return mask
