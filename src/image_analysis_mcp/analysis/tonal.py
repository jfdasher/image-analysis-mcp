"""Tonal analysis for images (shadows, midtones, highlights, dynamic range)."""

from typing import Dict, Any
import numpy as np


def analyze_tonal_properties(image: np.ndarray, histogram_lum: list) -> Dict[str, Any]:
    """
    Analyze tonal properties including shadows, highlights, and dynamic range.

    Args:
        image: Image as numpy array in RGB format (H, W, 3)
        histogram_lum: Luminance histogram (256 bins)

    Returns:
        Dictionary with tonal analysis results
    """
    # Convert to luminance if not already
    if len(image.shape) == 3:
        luminance = (0.299 * image[:, :, 0] + 0.587 * image[:, :, 1] + 0.114 * image[:, :, 2]).astype(np.uint8)
    else:
        luminance = image.astype(np.uint8)

    total_pixels = luminance.size

    # Count pixels in each tonal range
    # Shadows: 0-64, Midtones: 65-192, Highlights: 193-255
    shadows_pixels = int(np.sum(luminance <= 64))
    midtones_pixels = int(np.sum((luminance > 64) & (luminance < 193)))
    highlights_pixels = int(np.sum(luminance >= 193))

    # Calculate clipping
    clipped_shadows = int(histogram_lum[0])  # Pixels at value 0
    clipped_highlights = int(histogram_lum[255])  # Pixels at value 255

    clipped_shadows_pct = (clipped_shadows / total_pixels) * 100
    clipped_highlights_pct = (clipped_highlights / total_pixels) * 100

    # Calculate tonal distribution percentages
    shadows_pct = (shadows_pixels / total_pixels) * 100
    midtones_pct = (midtones_pixels / total_pixels) * 100
    highlights_pct = (highlights_pixels / total_pixels) * 100

    # Calculate mean and median luminance
    mean_luminance = float(np.mean(luminance))
    median_luminance = float(np.median(luminance))

    # Calculate contrast ratio
    max_val = float(np.max(luminance))
    min_val = float(np.min(luminance))
    if mean_luminance > 0:
        contrast_ratio = (max_val - min_val) / mean_luminance
    else:
        contrast_ratio = 0.0

    # Estimate dynamic range in stops
    # Find the range excluding clipped pixels (bottom/top 2%)
    sorted_lum = np.sort(luminance.flatten())
    p2_idx = int(total_pixels * 0.02)
    p98_idx = int(total_pixels * 0.98)

    if p98_idx < len(sorted_lum) and p2_idx >= 0:
        low_val = float(sorted_lum[p2_idx])
        high_val = float(sorted_lum[p98_idx])
    else:
        low_val = min_val
        high_val = max_val

    # Estimate noise floor (std dev in darkest areas)
    dark_pixels = luminance[luminance < 32]
    if len(dark_pixels) > 100:
        noise_floor = max(float(np.std(dark_pixels)), 1.0)
    else:
        noise_floor = 1.0

    # Calculate dynamic range in stops
    usable_range = max(high_val - low_val, 1.0)
    dynamic_range_stops = float(np.log2(usable_range / noise_floor))

    # Ensure reasonable bounds
    dynamic_range_stops = max(0.0, min(dynamic_range_stops, 20.0))

    return {
        "shadows_pixels": shadows_pixels,
        "midtones_pixels": midtones_pixels,
        "highlights_pixels": highlights_pixels,
        "clipped_shadows_pct": round(clipped_shadows_pct, 2),
        "clipped_highlights_pct": round(clipped_highlights_pct, 2),
        "dynamic_range_stops": round(dynamic_range_stops, 2),
        "mean_luminance": round(mean_luminance, 2),
        "median_luminance": round(median_luminance, 2),
        "contrast_ratio": round(contrast_ratio, 2),
        "tonal_distribution": {
            "shadows_pct": round(shadows_pct, 2),
            "midtones_pct": round(midtones_pct, 2),
            "highlights_pct": round(highlights_pct, 2),
        },
    }
