"""Frequency domain analysis using FFT."""

from typing import Dict, Any, Optional
import numpy as np
import cv2

from ..utils import classify_detail_level


def analyze_frequency_domain(image: np.ndarray) -> Dict[str, Any]:
    """
    Analyze frequency domain properties using FFT.

    This is an expensive operation and should only be performed when needed.

    Args:
        image: Image as numpy array in RGB format (H, W, 3)

    Returns:
        Dictionary with frequency analysis results
    """
    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY).astype(np.float32)

    # Downsample if image is very large (for performance)
    max_dimension = 2048
    h, w = gray.shape
    if max(h, w) > max_dimension:
        scale = max_dimension / max(h, w)
        new_h = int(h * scale)
        new_w = int(w * scale)
        gray = cv2.resize(gray, (new_w, new_h), interpolation=cv2.INTER_AREA)

    # Compute 2D FFT
    fft = np.fft.fft2(gray)
    fft_shift = np.fft.fftshift(fft)  # Shift zero frequency to center

    # Calculate magnitude spectrum
    magnitude_spectrum = np.abs(fft_shift)

    # Get dimensions
    h, w = magnitude_spectrum.shape
    center_y, center_x = h // 2, w // 2

    # Calculate high and low frequency energy
    # Low frequency: central region (inner 10%)
    # High frequency: outer regions
    low_freq_radius = int(min(h, w) * 0.1)
    high_freq_radius = int(min(h, w) * 0.5)

    # Create masks for low and high frequency regions
    y, x = np.ogrid[:h, :w]
    distance_from_center = np.sqrt((x - center_x)**2 + (y - center_y)**2)

    low_freq_mask = distance_from_center <= low_freq_radius
    high_freq_mask = (distance_from_center > low_freq_radius) & (distance_from_center <= high_freq_radius)

    # Calculate energy in each region
    low_freq_energy = float(np.sum(magnitude_spectrum[low_freq_mask]))
    high_freq_energy = float(np.sum(magnitude_spectrum[high_freq_mask]))

    # Avoid division by zero
    if low_freq_energy < 1:
        low_freq_energy = 1

    frequency_ratio = high_freq_energy / low_freq_energy

    # Find dominant frequency (peak in FFT)
    # Exclude the DC component (center)
    magnitude_no_dc = magnitude_spectrum.copy()
    dc_region_size = 5
    magnitude_no_dc[center_y-dc_region_size:center_y+dc_region_size,
                     center_x-dc_region_size:center_x+dc_region_size] = 0

    # Find peak
    peak_idx = np.unravel_index(np.argmax(magnitude_no_dc), magnitude_no_dc.shape)
    peak_y, peak_x = peak_idx
    dominant_frequency = float(np.sqrt((peak_x - center_x)**2 + (peak_y - center_y)**2))

    # Classify detail level
    detail_level = classify_detail_level(frequency_ratio)

    return {
        "high_freq_energy": round(high_freq_energy, 2),
        "low_freq_energy": round(low_freq_energy, 2),
        "frequency_ratio": round(frequency_ratio, 3),
        "dominant_frequency": round(dominant_frequency, 2),
        "detail_level": detail_level,
    }
