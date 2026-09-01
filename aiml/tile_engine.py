"""
aiml/tile_engine.py
Satellite Image Tile Slicing & Mask Stitching Engine for SatQuery AI.

Provides sliding-window tile patchifying (e.g. 512x512 with overlap)
and seamless mask fusion/stitching for high-resolution satellite rasters.
"""

import io
import json
import numpy as np

try:
    from PIL import Image
    has_pillow = True
except ImportError:
    has_pillow = False


def slice_image_into_tiles(image_bytes: bytes, tile_size: int = 512, overlap: int = 64) -> tuple[list[dict], int, int]:
    """
    Slices a large satellite image into overlapping grid tiles (patchifying).
    
    Returns:
        tiles: List of tile dicts containing tile_bytes, coordinates (x, y, w, h).
        orig_w: Original image width.
        orig_h: Original image height.
    """
    if not has_pillow:
        return [], 0, 0

    with Image.open(io.BytesIO(image_bytes)) as img:
        img_rgb = img.convert("RGB")
        orig_w, orig_h = img_rgb.size

        # If image is smaller than tile_size, return single tile
        if orig_w <= tile_size and orig_h <= tile_size:
            out = io.BytesIO()
            img_rgb.save(out, format="JPEG", quality=90)
            return [{
                "tile_id": 0,
                "x": 0,
                "y": 0,
                "w": orig_w,
                "h": orig_h,
                "tile_bytes": out.getvalue()
            }], orig_w, orig_h

        stride = tile_size - overlap
        tiles = []
        tile_id = 0

        for y in range(0, orig_h, stride):
            for x in range(0, orig_w, stride):
                # Calculate tile crop boundaries
                w = min(tile_size, orig_w - x)
                h = min(tile_size, orig_h - y)
                
                box = (x, y, x + w, y + h)
                tile_crop = img_rgb.crop(box)
                
                out = io.BytesIO()
                tile_crop.save(out, format="JPEG", quality=85)
                
                tiles.append({
                    "tile_id": tile_id,
                    "x": x,
                    "y": y,
                    "w": w,
                    "h": h,
                    "tile_bytes": out.getvalue()
                })
                tile_id += 1

        return tiles, orig_w, orig_h


def stitch_tile_masks(tile_predictions: list[dict], orig_w: int, orig_h: int) -> dict:
    """
    Stitches individual tile detection/mask predictions back onto the full spatial resolution canvas.
    Converts tile bounding boxes into full-image normalized [ymin, xmin, ymax, xmax] (0-1000 scale).
    """
    full_feature_masks = []
    
    if orig_w == 0 or orig_h == 0:
        return {"feature_masks": []}

    for item in tile_predictions:
        x_off = item["x"]
        y_off = item["y"]
        tile_w = item["w"]
        tile_h = item["h"]
        masks = item.get("masks", [])

        for m in masks:
            feature_name = m.get("feature_name", "Satellite Feature")
            category = m.get("category", "vegetation")
            box_2d = m.get("box_2d")

            if box_2d and len(box_2d) == 4:
                # box_2d relative to tile in 0-1000 scale
                ymin_t, xmin_t, ymax_t, xmax_t = box_2d

                # Convert tile relative coords to tile pixel coords
                px_xmin = x_off + (xmin_t / 1000.0) * tile_w
                px_ymin = y_off + (ymin_t / 1000.0) * tile_h
                px_xmax = x_off + (xmax_t / 1000.0) * tile_w
                px_ymax = y_off + (ymax_t / 1000.0) * tile_h

                # Convert full pixel coords to full image 0-1000 scale
                norm_ymin = int(round((px_ymin / float(orig_h)) * 1000.0))
                norm_xmin = int(round((px_xmin / float(orig_w)) * 1000.0))
                norm_ymax = int(round((px_ymax / float(orig_h)) * 1000.0))
                norm_xmax = int(round((px_xmax / float(orig_w)) * 1000.0))

                # Clamp to [0, 1000]
                norm_ymin = max(0, min(1000, norm_ymin))
                norm_xmin = max(0, min(1000, norm_xmin))
                norm_ymax = max(0, min(1000, norm_ymax))
                norm_xmax = max(0, min(1000, norm_xmax))

                full_feature_masks.append({
                    "feature_name": feature_name,
                    "category": category,
                    "box_2d": [norm_ymin, norm_xmin, norm_ymax, norm_xmax],
                    "tile_origin": [x_off, y_off]
                })

    return {
        "tile_count": len(tile_predictions),
        "canvas_size": [orig_w, orig_h],
        "feature_masks": full_feature_masks
    }
