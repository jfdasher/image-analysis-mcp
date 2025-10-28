"""Histogram analysis for images."""

from typing import Dict, Any, Tuple
import numpy as np
import cv2


def calculate_histogram(image: np.ndarray) -> Dict[str, Any]:
    """
    Calculate RGB and luminance histograms from an image.

    Args:
        image: Image as numpy array in RGB format (H, W, 3)

    Returns:
        Dictionary with histogram data and statistics
    """
    # Ensure image is 8-bit
    if image.dtype != np.uint8:
        image = (image / image.max() * 255).astype(np.uint8)

    # Calculate histograms for each channel
    hist_r = cv2.calcHist([image], [0], None, [256], [0, 256]).flatten().astype(int)
    hist_g = cv2.calcHist([image], [1], None, [256], [0, 256]).flatten().astype(int)
    hist_b = cv2.calcHist([image], [2], None, [256], [0, 256]).flatten().astype(int)

    # Calculate luminance (Y in YUV color space)
    # Standard formula: Y = 0.299*R + 0.587*G + 0.114*B
    luminance = (0.299 * image[:, :, 0] + 0.587 * image[:, :, 1] + 0.114 * image[:, :, 2]).astype(np.uint8)
    hist_lum = cv2.calcHist([luminance], [0], None, [256], [0, 256]).flatten().astype(int)

    # Calculate statistics for each channel
    stats_r = _calculate_channel_statistics(image[:, :, 0])
    stats_g = _calculate_channel_statistics(image[:, :, 1])
    stats_b = _calculate_channel_statistics(image[:, :, 2])
    stats_lum = _calculate_channel_statistics(luminance)

    return {
        "histogram": {
            "red": hist_r.tolist(),
            "green": hist_g.tolist(),
            "blue": hist_b.tolist(),
            "luminance": hist_lum.tolist(),
        },
        "statistics": {
            "red": stats_r,
            "green": stats_g,
            "blue": stats_b,
            "luminance": stats_lum,
        },
    }


def _calculate_channel_statistics(channel: np.ndarray) -> Dict[str, float]:
    """
    Calculate mean, median, and standard deviation for a channel.

    Args:
        channel: Single channel image data

    Returns:
        Dictionary with statistics
    """
    return {
        "mean": float(np.mean(channel)),
        "median": float(np.median(channel)),
        "std": float(np.std(channel)),
    }


def extract_histogram_only(image: np.ndarray) -> Tuple[Dict[str, list], Dict[str, Dict[str, float]]]:
    """
    Extract just histogram and statistics (optimized for speed).

    Args:
        image: Image as numpy array in RGB format

    Returns:
        Tuple of (histogram_dict, statistics_dict)
    """
    result = calculate_histogram(image)
    return result["histogram"], result["statistics"]
