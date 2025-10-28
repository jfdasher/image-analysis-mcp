"""Spatial property analysis including sharpness, noise, edges, and texture."""

from typing import Dict, Any
import numpy as np
import cv2
from skimage import filters
from skimage.measure import shannon_entropy

from ..utils import classify_sharpness, classify_noise


def analyze_spatial_properties(image: np.ndarray) -> Dict[str, Any]:
    """
    Analyze spatial properties of an image.

    Args:
        image: Image as numpy array in RGB format (H, W, 3)

    Returns:
        Dictionary with spatial analysis results
    """
    # Convert to grayscale for most analyses
    gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)

    # Calculate sharpness using Laplacian variance
    sharpness_score = calculate_sharpness(gray)
    sharpness_rating = classify_sharpness(sharpness_score)

    # Estimate noise level
    noise_level = estimate_noise(gray)
    noise_rating = classify_noise(noise_level)

    # Calculate edge density
    edge_density_pct = calculate_edge_density(gray)

    # Calculate texture entropy
    texture_entropy = calculate_texture_entropy(gray)

    # Detect blur
    blur_detection = detect_blur(gray, sharpness_score)

    return {
        "sharpness_score": round(sharpness_score, 2),
        "sharpness_rating": sharpness_rating,
        "noise_level": round(noise_level, 2),
        "noise_rating": noise_rating,
        "edge_density_pct": round(edge_density_pct, 2),
        "texture_entropy": round(texture_entropy, 2),
        "blur_detection": blur_detection,
    }


def calculate_sharpness(gray: np.ndarray) -> float:
    """
    Calculate sharpness score using Laplacian variance.

    Args:
        gray: Grayscale image

    Returns:
        Sharpness score (higher = sharper)
    """
    # Apply Laplacian operator
    laplacian = cv2.Laplacian(gray, cv2.CV_64F)

    # Calculate variance of Laplacian
    # This measures the spread of edge responses
    variance = float(laplacian.var())

    return variance


def estimate_noise(gray: np.ndarray) -> float:
    """
    Estimate noise level by analyzing variance in flat regions.

    Uses a method based on detecting low-variance regions and measuring
    their standard deviation.

    Args:
        gray: Grayscale image

    Returns:
        Noise level (standard deviation in flat regions)
    """
    # Divide image into blocks and find flat regions
    block_size = 32
    h, w = gray.shape
    noise_estimates = []

    for i in range(0, h - block_size, block_size):
        for j in range(0, w - block_size, block_size):
            block = gray[i:i+block_size, j:j+block_size]

            # Check if block is relatively flat (low variance)
            variance = np.var(block)
            if variance < 100:  # Threshold for "flat" region
                noise_estimates.append(np.std(block))

    # If we found flat regions, return median noise estimate
    if noise_estimates:
        return float(np.median(noise_estimates))

    # Fallback: use global estimate based on high-frequency content
    # Apply median filter and measure deviation
    median_filtered = cv2.medianBlur(gray, 5)
    noise = gray.astype(float) - median_filtered.astype(float)
    return float(np.std(noise))


def calculate_edge_density(gray: np.ndarray) -> float:
    """
    Calculate percentage of pixels that are edges.

    Args:
        gray: Grayscale image

    Returns:
        Percentage of edge pixels
    """
    # Use Canny edge detection
    edges = cv2.Canny(gray, 100, 200)

    # Calculate percentage of edge pixels
    edge_pixels = np.sum(edges > 0)
    total_pixels = edges.size

    edge_density_pct = (edge_pixels / total_pixels) * 100

    return float(edge_density_pct)


def calculate_texture_entropy(gray: np.ndarray) -> float:
    """
    Calculate texture entropy (measure of image complexity).

    Args:
        gray: Grayscale image

    Returns:
        Entropy value (0-8, higher = more complex)
    """
    # Calculate Shannon entropy
    # Downsample for performance if image is very large
    if gray.size > 1_000_000:
        scale_factor = int(np.sqrt(gray.size / 1_000_000))
        gray = gray[::scale_factor, ::scale_factor]

    entropy = shannon_entropy(gray)
    return float(entropy)


def detect_blur(gray: np.ndarray, sharpness_score: float) -> Dict[str, Any]:
    """
    Detect if image is blurry based on sharpness score.

    Args:
        gray: Grayscale image
        sharpness_score: Pre-calculated sharpness score

    Returns:
        Dictionary with blur detection results
    """
    # Thresholds based on sharpness score
    # These are heuristic values that work well in practice
    blur_threshold = 150  # Below this is considered blurry

    is_blurry = sharpness_score < blur_threshold

    # Calculate confidence based on how far from threshold
    if is_blurry:
        # More blurry = higher confidence
        confidence = min(1.0, (blur_threshold - sharpness_score) / blur_threshold)
    else:
        # Sharper = higher confidence
        confidence = min(1.0, (sharpness_score - blur_threshold) / blur_threshold)

    return {
        "is_blurry": bool(is_blurry),
        "confidence": round(float(confidence), 2),
    }
