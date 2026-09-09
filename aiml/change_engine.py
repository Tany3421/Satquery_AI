"""
aiml/change_engine.py
Pixel-Level Spatial Difference & Change Heatmap Generation Engine for SatQuery AI.

Computes:
1. Radiometric and spectral difference tensors between bi-temporal observation pairs (T1 Before -> T2 After).
2. Category-aware spatial delta:
   - Water expansion / flood inundation (Cyan/Blue)
   - Vegetation loss / clearing / harvest (Red)
   - Vegetation growth / re-greening (Green)
   - Built-up / infrastructure expansion (Amber)
3. Transparent RGBA heatmap overlay for interactive frontend rendering.
"""

import io
from typing import Any, Dict, Tuple

import numpy as np
from PIL import Image


def compute_spatial_change(
    before_bytes: bytes,
    after_bytes: bytes,
    threshold: float = 25.0,
) -> Tuple[np.ndarray, Dict[str, Any]]:
    """
    Computes pixel-level difference and categorized change map between T1 and T2.

    Returns:
        rgba_heatmap: np.ndarray of shape (H, W, 4), uint8
        stats: dict containing changed area percentages and metrics
    """
    with Image.open(io.BytesIO(before_bytes)) as img_b, Image.open(io.BytesIO(after_bytes)) as img_a:
        rgb_b = img_b.convert("RGB")
        rgb_a = img_a.convert("RGB")

        # Align dimensions if images differ in size
        if rgb_b.size != rgb_a.size:
            rgb_a = rgb_a.resize(rgb_b.size, Image.Resampling.BILINEAR)

        arr_b = np.asarray(rgb_b, dtype=np.float32)
        arr_a = np.asarray(rgb_a, dtype=np.float32)

    h, w, _ = arr_b.shape
    total_pixels = h * w

    # Channel deltas: R=0, G=1, B=2
    diff_r = arr_a[:, :, 0] - arr_b[:, :, 0]
    diff_g = arr_a[:, :, 1] - arr_b[:, :, 1]
    diff_b = arr_a[:, :, 2] - arr_b[:, :, 2]

    # Euclidean color difference
    dist = np.sqrt(diff_r**2 + diff_g**2 + diff_b**2)
    change_mask = dist > threshold

    # Initialize transparent RGBA heatmap overlay
    rgba = np.zeros((h, w, 4), dtype=np.uint8)

    # Classify change types by spectral delta
    # 1. Water expansion / Flood inundation: Significant increase in blue/dark specular reflection
    # or drop in overall brightness with blue dominance
    water_flood_mask = change_mask & (diff_b > diff_r + 5) & (diff_b > diff_g)
    rgba[water_flood_mask] = [0, 180, 255, 190]  # Vibrant Cyan/Blue

    # 2. Vegetation Loss / Soil Exposure / Deforestation: Decrease in green, increase in red/brown
    veg_loss_mask = change_mask & (~water_flood_mask) & (diff_g < -15) & (diff_r > diff_g)
    rgba[veg_loss_mask] = [230, 50, 50, 190]  # Red

    # 3. Vegetation Growth / New Canopy: Increase in green reflectance
    veg_gain_mask = change_mask & (~water_flood_mask) & (~veg_loss_mask) & (diff_g > 15) & (diff_g > diff_r)
    rgba[veg_gain_mask] = [46, 204, 113, 190]  # Green

    # 4. Built-up / Urban / Ground Construction: Brightness increase or high contrast structural change
    urban_mask = change_mask & (~water_flood_mask) & (~veg_loss_mask) & (~veg_gain_mask)
    rgba[urban_mask] = [240, 169, 78, 190]  # Amber / Yellow

    # Calculate statistics
    changed_count = int(np.sum(change_mask))
    pct_changed = round((changed_count / float(total_pixels)) * 100.0, 1)

    pct_water = round((int(np.sum(water_flood_mask)) / float(total_pixels)) * 100.0, 1)
    pct_veg_loss = round((int(np.sum(veg_loss_mask)) / float(total_pixels)) * 100.0, 1)
    pct_veg_gain = round((int(np.sum(veg_gain_mask)) / float(total_pixels)) * 100.0, 1)
    pct_urban = round((int(np.sum(urban_mask)) / float(total_pixels)) * 100.0, 1)

    anomaly = pct_changed > 4.0
    stats = {
        "total_changed_percent": pct_changed,
        "total_changed_pixel_pct": pct_changed,
        "anomaly_detected": anomaly,
        "water_expansion_percent": pct_water,
        "vegetation_loss_percent": pct_veg_loss,
        "vegetation_gain_percent": pct_veg_gain,
        "urban_expansion_percent": pct_urban,
        "resolution": f"{w}x{h}",
        "total_pixels_evaluated": total_pixels,
    }

    return rgba, stats


def generate_change_heatmap_png(
    before_bytes: bytes,
    after_bytes: bytes,
    threshold: float = 25.0,
) -> Tuple[bytes, Dict[str, Any]]:
    """
    Generates a high-quality transparent PNG change heatmap overlay.
    """
    rgba, stats = compute_spatial_change(before_bytes, after_bytes, threshold=threshold)
    img_out = Image.fromarray(rgba, mode="RGBA")

    out_buf = io.BytesIO()
    img_out.save(out_buf, format="PNG", optimize=True)
    return out_buf.getvalue(), stats
