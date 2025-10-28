"""Utility functions for image analysis."""

import os
from pathlib import Path
from typing import Tuple, Optional
import math


# Supported file extensions by category
SUPPORTED_FORMATS = {
    "raster": [".jpg", ".jpeg", ".png", ".tif", ".tiff", ".webp"],
    "raw": [".cr2", ".cr3", ".nef", ".arw", ".dng", ".raf", ".orf"],
}

ALL_SUPPORTED_EXTENSIONS = SUPPORTED_FORMATS["raster"] + SUPPORTED_FORMATS["raw"]


# CSS3 Extended color names with RGB values
CSS_COLORS = {
    "black": (0, 0, 0),
    "white": (255, 255, 255),
    "red": (255, 0, 0),
    "lime": (0, 255, 0),
    "blue": (0, 0, 255),
    "yellow": (255, 255, 0),
    "cyan": (0, 255, 255),
    "magenta": (255, 0, 255),
    "silver": (192, 192, 192),
    "gray": (128, 128, 128),
    "maroon": (128, 0, 0),
    "olive": (128, 128, 0),
    "green": (0, 128, 0),
    "purple": (128, 0, 128),
    "teal": (0, 128, 128),
    "navy": (0, 0, 128),
    "orange": (255, 165, 0),
    "pink": (255, 192, 203),
    "brown": (165, 42, 42),
    "beige": (245, 245, 220),
    "tan": (210, 180, 140),
    "gold": (255, 215, 0),
    "indigo": (75, 0, 130),
    "violet": (238, 130, 238),
}


def validate_filepath(filepath: str) -> Tuple[bool, Optional[str], Optional[Path]]:
    """
    Validate that a file path exists and is a supported image format.

    Args:
        filepath: Path to validate

    Returns:
        Tuple of (is_valid, error_message, resolved_path)
    """
    if not filepath:
        return False, "Filepath cannot be empty", None

    path = Path(filepath).resolve()

    # Check if file exists
    if not path.exists():
        return False, f"File not found: {filepath}", None

    # Check if it's a file (not a directory)
    if not path.is_file():
        return False, f"Path is not a file: {filepath}", None

    # Check if readable
    if not os.access(path, os.R_OK):
        return False, f"Permission denied: cannot read {filepath}", None

    # Check extension
    ext = path.suffix.lower()
    if ext not in ALL_SUPPORTED_EXTENSIONS:
        supported = ", ".join(ALL_SUPPORTED_EXTENSIONS)
        return False, f"Unsupported format '{ext}'. Supported formats: {supported}", None

    return True, None, path


def is_raw_format(filepath: Path) -> bool:
    """Check if file is a RAW format."""
    return filepath.suffix.lower() in SUPPORTED_FORMATS["raw"]


def rgb_to_hex(rgb: Tuple[int, int, int]) -> str:
    """Convert RGB tuple to hex string."""
    return "#{:02x}{:02x}{:02x}".format(rgb[0], rgb[1], rgb[2])


def euclidean_distance(color1: Tuple[int, int, int], color2: Tuple[int, int, int]) -> float:
    """Calculate Euclidean distance between two RGB colors."""
    return math.sqrt(
        (color1[0] - color2[0]) ** 2 +
        (color1[1] - color2[1]) ** 2 +
        (color1[2] - color2[2]) ** 2
    )


def get_nearest_color_name(rgb: Tuple[int, int, int]) -> str:
    """
    Find the nearest CSS color name for an RGB value.

    Args:
        rgb: RGB tuple (r, g, b) with values 0-255

    Returns:
        Name of the nearest CSS color
    """
    min_distance = float('inf')
    nearest_name = "gray"

    for name, color_rgb in CSS_COLORS.items():
        distance = euclidean_distance(rgb, color_rgb)
        if distance < min_distance:
            min_distance = distance
            nearest_name = name

    return nearest_name


def classify_sharpness(score: float) -> str:
    """
    Classify sharpness score into a rating.

    Args:
        score: Laplacian variance sharpness score

    Returns:
        Rating string: very_soft, soft, moderate, sharp, very_sharp
    """
    if score >= 1000:
        return "very_sharp"
    elif score >= 500:
        return "sharp"
    elif score >= 150:
        return "moderate"
    elif score >= 50:
        return "soft"
    else:
        return "very_soft"


def classify_noise(noise_level: float) -> str:
    """
    Classify noise level into a rating.

    Args:
        noise_level: Standard deviation in flat regions

    Returns:
        Rating string: very_low, low, moderate, high, very_high
    """
    if noise_level >= 50:
        return "very_high"
    elif noise_level >= 30:
        return "high"
    elif noise_level >= 15:
        return "moderate"
    elif noise_level >= 5:
        return "low"
    else:
        return "very_low"


def estimate_color_temperature(avg_r: float, avg_g: float, avg_b: float) -> Tuple[str, int]:
    """
    Estimate color temperature from average RGB values.

    Uses the R/B ratio to estimate color temperature in Kelvin.
    Warmer images have more red (lower Kelvin), cooler have more blue (higher Kelvin).

    Args:
        avg_r: Average red channel value (0-255)
        avg_g: Average green channel value (0-255)
        avg_b: Average blue channel value (0-255)

    Returns:
        Tuple of (temperature_category, kelvin_estimate)
        temperature_category: "warm", "neutral", or "cool"
        kelvin_estimate: Estimated temperature in Kelvin
    """
    # Avoid division by zero
    if avg_b < 1:
        avg_b = 1

    # Calculate R/B ratio - key metric for color temperature
    rb_ratio = avg_r / avg_b

    # Map R/B ratio to approximate Kelvin values
    # Based on typical color temperature charts:
    # - Warm (candlelight, tungsten): 2500-4000K, R/B ratio ~1.5-2.0
    # - Neutral (daylight): 5000-6500K, R/B ratio ~0.9-1.1
    # - Cool (shade, overcast): 7000-10000K, R/B ratio ~0.6-0.8

    if rb_ratio > 1.3:
        # Warm
        kelvin = int(2500 + (2.0 - rb_ratio) / 0.7 * 1500)
        kelvin = max(2000, min(kelvin, 4000))
        category = "warm"
    elif rb_ratio < 0.85:
        # Cool
        kelvin = int(7000 + (0.85 - rb_ratio) / 0.25 * 3000)
        kelvin = max(7000, min(kelvin, 10000))
        category = "cool"
    else:
        # Neutral
        kelvin = int(5000 + (1.0 - rb_ratio) / 0.45 * 1500)
        kelvin = max(5000, min(kelvin, 6500))
        category = "neutral"

    return category, kelvin


def classify_detail_level(frequency_ratio: float) -> str:
    """
    Classify image detail level based on frequency ratio.

    Args:
        frequency_ratio: Ratio of high to low frequency energy

    Returns:
        Detail level: "low", "moderate", or "high"
    """
    if frequency_ratio > 0.5:
        return "high"
    elif frequency_ratio > 0.2:
        return "moderate"
    else:
        return "low"
