"""
backend/io_geotiff.py
Geospatial TIFF / GeoTIFF Ingestion & Radiometric Normalization Module.

Supports:
- GeoTIFF (.tif, .tiff) and standard imagery (.jpg, .jpeg, .png, .webp).
- Multi-band satellite rasters:
    * 1-band SAR (RISAT / Sentinel-1 intensity or amplitude)
    * 3-band Optical RGB (Cartosat-2S / Sentinel-2 True Color)
    * 4-band & N-band Multispectral (extracts true-color preview)
- Robust 2%–98% percentile stretching for 12-bit / 16-bit rasters to prevent
  washed out or pitch black rendering.
- GeoTIFF metadata extraction: ModelTiepoint, ModelPixelScale, GeoKeys, and
  geographic bounding box calculation.
"""

import io
import json
from pathlib import Path
from typing import Any, Optional, Tuple

import numpy as np
from PIL import Image

try:
    import tifffile
    HAS_TIFFFILE = True
except ImportError:
    HAS_TIFFFILE = False


TIFF_EXTENSIONS = {".tif", ".tiff"}


def is_geotiff_file(filename: str, raw_bytes: Optional[bytes] = None) -> bool:
    """Check if the filename or byte magic indicates a TIFF/GeoTIFF."""
    ext = Path(filename or "").suffix.lower()
    if ext in TIFF_EXTENSIONS:
        return True
    if raw_bytes and len(raw_bytes) >= 4:
        # Standard TIFF magic numbers: 'II*\x00' (little-endian) or 'MM\x00*' (big-endian)
        if raw_bytes[:4] in (b"II*\x00", b"MM\x00*"):
            return True
        # BigTIFF magic numbers: 'II+\x00' or 'MM\x00+'
        if raw_bytes[:4] in (b"II+\x00", b"MM\x00+"):
            return True
    return False


def _percentile_stretch(band: np.ndarray, lower_percentile: float = 2.0, upper_percentile: float = 98.0) -> np.ndarray:
    """
    Applies robust 2%-98% percentile stretch to convert arbitrary dynamic range
    (float32, uint16, int16, etc.) to 8-bit [0, 255] for visual interpretation.
    """
    valid = band[np.isfinite(band)]
    if valid.size == 0:
        return np.zeros_like(band, dtype=np.uint8)

    p_low = np.percentile(valid, lower_percentile)
    p_high = np.percentile(valid, upper_percentile)

    if p_high <= p_low:
        p_high = p_low + 1.0

    stretched = np.clip((band - p_low) / (p_high - p_low), 0.0, 1.0) * 255.0
    return stretched.astype(np.uint8)


def _extract_geotiff_metadata(tif: "tifffile.TiffFile") -> dict[str, Any]:
    """Extract spatial reference, scale, tiepoints, and bounding box from GeoTIFF tags."""
    meta = {
        "is_geotiff": True,
        "pixel_scale": None,
        "tiepoints": None,
        "bounding_box": None,
        "crs": "WGS84 / Geospatial Grid",
        "tags": {}
    }

    try:
        page = tif.pages[0]
        tags = page.tags

        # ModelPixelScaleTag (33550): [ScaleX, ScaleY, ScaleZ]
        if 33550 in tags:
            scale = tags[33550].value
            meta["pixel_scale"] = [float(s) for s in scale]

        # ModelTiepointTag (33922): [I, J, K, X, Y, Z]
        if 33922 in tags:
            tiepoints = tags[33922].value
            meta["tiepoints"] = [float(tp) for tp in tiepoints]

        # Calculate bounding box if tiepoints and scale exist
        if meta["tiepoints"] and meta["pixel_scale"] and len(meta["tiepoints"]) >= 6:
            _, _, _, x0, y0, _ = meta["tiepoints"][:6]
            sx, sy = meta["pixel_scale"][:2]
            h, w = page.shape[:2]

            x1 = x0 + (w * sx)
            y1 = y0 - (h * sy)

            min_x, max_x = min(x0, x1), max(x0, x1)
            min_y, max_y = min(y0, y1), max(y0, y1)

            # Plausible lat/lon range check (WGS84)
            if -180 <= min_x <= 180 and -90 <= min_y <= 90 and -180 <= max_x <= 180 and -90 <= max_y <= 90:
                meta["bounding_box"] = [round(min_y, 6), round(min_x, 6), round(max_y, 6), round(max_x, 6)]
                meta["crs"] = "EPSG:4326 (WGS84 Geographic)"
            else:
                meta["bounding_box"] = [round(min_y, 2), round(min_x, 2), round(max_y, 2), round(max_x, 2)]
                meta["crs"] = "Projected CRS (UTM / National Grid)"

        # GeoKeyDirectoryTag (34735)
        if 34735 in tags:
            meta["tags"]["has_geokeys"] = True

    except Exception:
        pass

    return meta


def process_raster_upload(raw_bytes: bytes, filename: str) -> dict[str, Any]:
    """
    Unified raster processing pipeline.
    
    Returns a dict with:
      - is_geotiff: bool
      - preview_bytes: bytes (JPEG ready for browser display and VLM)
      - preview_media_type: "image/jpeg"
      - width: int
      - height: int
      - bands: int
      - dtype: str
      - metadata: dict (bounding box, crs, pixel scale, etc.)
    """
    if not is_geotiff_file(filename, raw_bytes):
        # Standard format (JPG, PNG, WEBP)
        try:
            with Image.open(io.BytesIO(raw_bytes)) as img:
                w, h = img.size
                channels = len(img.getbands())
                if img.format == "JPEG":
                    preview_bytes = raw_bytes
                else:
                    rgb = img.convert("RGB")
                    out = io.BytesIO()
                    rgb.save(out, format="JPEG", quality=90)
                    preview_bytes = out.getvalue()

                return {
                    "is_geotiff": False,
                    "filename": filename,
                    "preview_bytes": preview_bytes,
                    "preview_media_type": "image/jpeg",
                    "width": w,
                    "height": h,
                    "bands": channels,
                    "dtype": "uint8",
                    "metadata": {
                        "format": img.format or "Standard Image",
                        "color_mode": img.mode,
                    }
                }
        except Exception:
            return {
                "is_geotiff": False,
                "filename": filename,
                "preview_bytes": raw_bytes,
                "preview_media_type": "image/jpeg",
                "width": 800,
                "height": 800,
                "bands": 3,
                "dtype": "uint8",
                "metadata": {}
            }

    # Process GeoTIFF / TIFF
    if not HAS_TIFFFILE:
        with Image.open(io.BytesIO(raw_bytes)) as img:
            rgb = img.convert("RGB")
            out = io.BytesIO()
            rgb.save(out, format="JPEG", quality=90)
            return {
                "is_geotiff": True,
                "filename": filename,
                "preview_bytes": out.getvalue(),
                "preview_media_type": "image/jpeg",
                "width": img.size[0],
                "height": img.size[1],
                "bands": len(img.getbands()),
                "dtype": "uint8",
                "metadata": {"source": "Pillow TIFF Parser"}
            }

    with tifffile.TiffFile(io.BytesIO(raw_bytes)) as tif:
        meta = _extract_geotiff_metadata(tif)
        array = tif.asarray()

    shape = array.shape
    dtype_str = str(array.dtype)

    # Determine bands and spatial dimensions
    # Shapes could be (H, W), (H, W, C), or (C, H, W)
    if array.ndim == 2:
        # Single band (e.g. SAR backscatter amplitude/intensity or DEM)
        h, w = shape
        bands = 1
        stretched = _percentile_stretch(array)
        rgb_preview = np.stack([stretched, stretched, stretched], axis=-1)

    elif array.ndim == 3:
        if shape[0] in (1, 2, 3, 4, 8, 12, 13) and shape[0] < shape[1] and shape[0] < shape[2]:
            # Shape is (C, H, W)
            bands, h, w = shape
            if bands == 1:
                stretched = _percentile_stretch(array[0])
                rgb_preview = np.stack([stretched, stretched, stretched], axis=-1)
            elif bands == 2:
                # e.g. Dual-pol SAR (VV, VH)
                b0 = _percentile_stretch(array[0])
                b1 = _percentile_stretch(array[1])
                ratio = _percentile_stretch(array[0] / (array[1] + 1e-6))
                rgb_preview = np.stack([b0, b1, ratio], axis=-1)
            elif bands >= 3:
                # Use bands 0, 1, 2 as RGB preview
                r = _percentile_stretch(array[0])
                g = _percentile_stretch(array[1])
                b = _percentile_stretch(array[2])
                rgb_preview = np.stack([r, g, b], axis=-1)
        else:
            # Shape is (H, W, C)
            h, w, bands = shape
            if bands == 1:
                stretched = _percentile_stretch(array[:, :, 0])
                rgb_preview = np.stack([stretched, stretched, stretched], axis=-1)
            elif bands >= 3:
                r = _percentile_stretch(array[:, :, 0])
                g = _percentile_stretch(array[:, :, 1])
                b = _percentile_stretch(array[:, :, 2])
                rgb_preview = np.stack([r, g, b], axis=-1)
            else:
                stretched = _percentile_stretch(array[:, :, 0])
                rgb_preview = np.stack([stretched, stretched, stretched], axis=-1)
    else:
        h, w = 512, 512
        bands = 1
        rgb_preview = np.zeros((h, w, 3), dtype=np.uint8)

    # Encode RGB preview to JPEG bytes
    img_preview = Image.fromarray(rgb_preview, mode="RGB")
    out = io.BytesIO()
    img_preview.save(out, format="JPEG", quality=90, optimize=True)
    preview_bytes = out.getvalue()

    meta.update({
        "width": w,
        "height": h,
        "bands": bands,
        "dtype": dtype_str,
        "is_geotiff": True,
        "filename": filename
    })

    return {
        "is_geotiff": True,
        "filename": filename,
        "preview_bytes": preview_bytes,
        "preview_media_type": "image/jpeg",
        "width": w,
        "height": h,
        "bands": bands,
        "dtype": dtype_str,
        "metadata": meta
    }
