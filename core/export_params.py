"""Convert paper/scale/DPI export parameters to pixel dimensions and tile zoom."""

import math

R_EARTH = 6378137  # WGS84 equatorial radius, metres

# Paper dimensions in mm (width × height in portrait orientation)
PAPER_SIZES = {
    'A4':            (210, 297),
    'A4-landscape':  (297, 210),
    'A3':            (297, 420),
    'A3-landscape':  (420, 297),
}


def compute_zoom(scale_m_per_cm, dpi, lat):
    """Return the integer tile zoom level that best matches scale+DPI at a given latitude.

    scale_m_per_cm — map metres represented by 1 cm on the image (e.g. 500 means 500 m/cm)
    dpi            — output resolution in dots per inch
    lat            — centre latitude in decimal degrees
    """
    # 1 cm on paper = (dpi / 2.54) pixels
    # 1 cm on paper = scale_m_per_cm metres on the ground
    # → 1 pixel = scale_m_per_cm / (dpi / 2.54) = scale_m_per_cm * 2.54 / dpi metres
    desired_m_per_px = scale_m_per_cm * 2.54 / dpi

    # Web Mercator: m_per_px = 2π·R·cos(lat) / (256·2^z)
    z = math.log2(
        2 * math.pi * R_EARTH * math.cos(math.radians(lat))
        / (256 * desired_m_per_px)
    )
    return round(z)


def paper_pixels(paper, dpi):
    """Return (width_px, height_px) for the given paper name and DPI."""
    if paper not in PAPER_SIZES:
        known = ', '.join(PAPER_SIZES)
        raise ValueError(f"Unknown paper size {paper!r}. Known sizes: {known}")
    w_mm, h_mm = PAPER_SIZES[paper]
    return round(w_mm / 25.4 * dpi), round(h_mm / 25.4 * dpi)


def resolve_export(cfg_map, cfg_export, center_lat):
    """Return (width_px, height_px, zoom) from config dicts.

    cfg_export takes priority over raw width_px/height_px in cfg_map.
    center_lat is needed to compute the zoom from scale.
    """
    if cfg_export:
        paper = cfg_export.get('paper', 'A4')
        scale = cfg_export.get('scale', 500)
        dpi = cfg_export.get('dpi', 300)
        width_px, height_px = paper_pixels(paper, dpi)
        zoom = compute_zoom(scale, dpi, center_lat)
        return width_px, height_px, zoom

    # Fallback: explicit pixel size + zoom from URL
    return (
        cfg_map.get('width_px', 2000),
        cfg_map.get('height_px', 1200),
        None,  # caller must use URL zoom
    )
