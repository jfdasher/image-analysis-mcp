"""Color analysis including dominant colors, temperature, and saturation."""

from typing import Dict, Any, List, Tuple
import numpy as np
from sklearn.cluster import KMeans
import cv2

from ..utils import get_nearest_color_name, rgb_to_hex, estimate_color_temperature


def analyze_color_properties(image: np.ndarray) -> Dict[str, Any]:
    """
    Analyze color properties of an image.

    Args:
        image: Image as numpy array in RGB format (H, W, 3)

    Returns:
        Dictionary with color analysis results
    """
    # Extract dominant colors
    dominant_colors = extract_dominant_colors(image, n_colors=5)

    # Calculate average RGB values
    avg_r = float(np.mean(image[:, :, 0]))
    avg_g = float(np.mean(image[:, :, 1]))
    avg_b = float(np.mean(image[:, :, 2]))

    # Estimate color temperature
    temp_category, temp_kelvin = estimate_color_temperature(avg_r, avg_g, avg_b)

    # Calculate white balance RGB ratios (normalized to green)
    # Green is typically the reference channel
    avg_g_safe = max(avg_g, 1.0)
    wb_ratios = {
        "r": round(avg_r / avg_g_safe, 3),
        "g": 1.0,
        "b": round(avg_b / avg_g_safe, 3),
    }

    # Calculate saturation statistics in HSV space
    hsv = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)
    saturation = hsv[:, :, 1] / 255.0  # Normalize to 0-1

    saturation_mean = float(np.mean(saturation))
    saturation_median = float(np.median(saturation))
    saturation_std = float(np.std(saturation))

    # Detect color cast
    color_cast = detect_color_cast(avg_r, avg_g, avg_b)

    return {
        "dominant_colors": dominant_colors,
        "color_temperature": temp_category,
        "temperature_kelvin": temp_kelvin,
        "saturation_mean": round(saturation_mean, 3),
        "saturation_median": round(saturation_median, 3),
        "saturation_std": round(saturation_std, 3),
        "white_balance_rgb_ratios": wb_ratios,
        "color_cast": color_cast,
    }


def extract_dominant_colors(image: np.ndarray, n_colors: int = 5) -> List[Dict[str, Any]]:
    """
    Extract dominant colors using K-means clustering.

    Args:
        image: Image as numpy array in RGB format
        n_colors: Number of dominant colors to extract

    Returns:
        List of dominant color dictionaries
    """
    # Reshape image to be a list of pixels
    pixels = image.reshape(-1, 3)

    # Sample pixels for performance (use max 10000 pixels)
    if len(pixels) > 10000:
        indices = np.random.choice(len(pixels), 10000, replace=False)
        pixels = pixels[indices]

    # Perform K-means clustering
    try:
        kmeans = KMeans(n_clusters=n_colors, random_state=42, n_init=10)
        kmeans.fit(pixels)

        # Get cluster centers (dominant colors) and labels
        centers = kmeans.cluster_centers_.astype(int)
        labels = kmeans.labels_

        # Count pixels in each cluster
        unique, counts = np.unique(labels, return_counts=True)
        total_sampled = len(labels)

        # Create dominant color entries
        dominant_colors = []
        for i, (center, count) in enumerate(zip(centers, counts)):
            rgb = tuple(int(c) for c in center)
            percentage = (count / total_sampled) * 100

            color_entry = {
                "rgb": list(rgb),
                "hex": rgb_to_hex(rgb),
                "percentage": round(percentage, 2),
                "name": get_nearest_color_name(rgb),
            }
            dominant_colors.append(color_entry)

        # Sort by percentage (descending)
        dominant_colors.sort(key=lambda x: x["percentage"], reverse=True)

        return dominant_colors

    except Exception as e:
        # Fallback: return average color if clustering fails
        avg_color = tuple(int(c) for c in np.mean(pixels, axis=0))
        return [{
            "rgb": list(avg_color),
            "hex": rgb_to_hex(avg_color),
            "percentage": 100.0,
            "name": get_nearest_color_name(avg_color),
        }]


def detect_color_cast(avg_r: float, avg_g: float, avg_b: float) -> Dict[str, Any]:
    """
    Detect color cast in an image based on RGB channel imbalance.

    Args:
        avg_r: Average red channel value
        avg_g: Average green channel value
        avg_b: Average blue channel value

    Returns:
        Dictionary with color cast information
    """
    # Calculate deviations from neutral gray
    avg_all = (avg_r + avg_g + avg_b) / 3.0
    if avg_all < 1:
        avg_all = 1

    r_deviation = (avg_r - avg_all) / avg_all
    g_deviation = (avg_g - avg_all) / avg_all
    b_deviation = (avg_b - avg_all) / avg_all

    # Threshold for detecting cast (5% deviation)
    threshold = 0.05
    max_deviation = max(abs(r_deviation), abs(g_deviation), abs(b_deviation))

    if max_deviation < threshold:
        return {
            "detected": False,
            "direction": "none",
            "severity": 0.0,
        }

    # Determine direction
    if abs(r_deviation) > abs(g_deviation) and abs(r_deviation) > abs(b_deviation):
        direction = "red" if r_deviation > 0 else "cyan"
        severity = abs(r_deviation)
    elif abs(g_deviation) > abs(b_deviation):
        direction = "green" if g_deviation > 0 else "magenta"
        severity = abs(g_deviation)
    else:
        direction = "blue" if b_deviation > 0 else "yellow"
        severity = abs(b_deviation)

    # Clamp severity to 0-1 range
    severity = min(severity, 1.0)

    return {
        "detected": True,
        "direction": direction,
        "severity": round(severity, 3),
    }
