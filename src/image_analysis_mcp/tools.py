"""MCP tool implementations for image analysis."""

import os
from pathlib import Path
from typing import Dict, Any
import numpy as np
from PIL import Image
import rawpy
import cv2

from .utils import validate_filepath, is_raw_format
from .analysis.metadata import extract_metadata
from .analysis.histogram import calculate_histogram, extract_histogram_only
from .analysis.tonal import analyze_tonal_properties
from .analysis.color import analyze_color_properties
from .analysis.spatial import analyze_spatial_properties
from .analysis.frequency import analyze_frequency_domain
from .analysis.preview import generate_preview


def get_image_metadata(filepath: str) -> Dict[str, Any]:
    """
    Extract basic metadata and EXIF information from an image file.

    Args:
        filepath: Absolute or relative path to image file

    Returns:
        Dictionary with metadata or error
    """
    try:
        # Validate filepath
        is_valid, error_msg, resolved_path = validate_filepath(filepath)
        if not is_valid:
            return {
                "success": False,
                "error": {
                    "code": "FILE_NOT_FOUND" if "not found" in error_msg else
                            "PERMISSION_DENIED" if "Permission" in error_msg else
                            "UNSUPPORTED_FORMAT" if "Unsupported" in error_msg else
                            "INVALID_PARAMETER",
                    "message": error_msg,
                    "details": None,
                },
            }

        # Extract metadata
        metadata = extract_metadata(resolved_path)

        return {
            "success": True,
            "filepath": str(resolved_path),
            "metadata": metadata,
        }

    except Exception as e:
        error_msg = str(e)
        error_code = "CORRUPTED_FILE" if "corrupted" in error_msg.lower() or "failed to read" in error_msg.lower() else "INVALID_PARAMETER"

        return {
            "success": False,
            "error": {
                "code": error_code,
                "message": error_msg,
                "details": {"exception_type": type(e).__name__},
            },
        }


def get_image_histogram(filepath: str, process_raw: bool = True) -> Dict[str, Any]:
    """
    Fast histogram-only extraction without full analysis.

    Args:
        filepath: Absolute or relative path to image file
        process_raw: Apply default RAW processing if applicable

    Returns:
        Dictionary with histogram data or error
    """
    try:
        # Validate filepath
        is_valid, error_msg, resolved_path = validate_filepath(filepath)
        if not is_valid:
            return {
                "success": False,
                "error": {
                    "code": "FILE_NOT_FOUND" if "not found" in error_msg else
                            "PERMISSION_DENIED" if "Permission" in error_msg else
                            "UNSUPPORTED_FORMAT" if "Unsupported" in error_msg else
                            "INVALID_PARAMETER",
                    "message": error_msg,
                    "details": None,
                },
            }

        # Load image
        image = _load_image(resolved_path, process_raw)

        # Calculate histogram
        histogram, statistics = extract_histogram_only(image)

        return {
            "success": True,
            "filepath": str(resolved_path),
            "histogram": histogram,
            "statistics": statistics,
        }

    except Exception as e:
        error_msg = str(e)
        error_code = "RAW_PROCESSING_FAILED" if "RAW" in error_msg else \
                     "CORRUPTED_FILE" if "corrupted" in error_msg.lower() else \
                     "OUT_OF_MEMORY" if "memory" in error_msg.lower() else \
                     "INVALID_PARAMETER"

        return {
            "success": False,
            "error": {
                "code": error_code,
                "message": error_msg,
                "details": {"exception_type": type(e).__name__},
            },
        }


def analyze_image_file(
    filepath: str,
    include_frequency: bool = False,
    include_preview: bool = False,
    preview_max_dimension: int = 1920,
    preview_format: str = "JPEG",
    preview_quality: int = 85,
    process_raw: bool = True
) -> Dict[str, Any]:
    """
    Comprehensive analysis of an image file.

    Args:
        filepath: Absolute or relative path to image file
        include_frequency: Include expensive FFT analysis
        include_preview: Include base64-encoded preview image
        preview_max_dimension: Max width or height for preview
        preview_format: Preview format ("JPEG", "PNG", "WEBP")
        preview_quality: Quality for JPEG/WEBP (1-100)
        process_raw: Apply default RAW processing if applicable

    Returns:
        Dictionary with comprehensive analysis or error
    """
    try:
        # Validate filepath
        is_valid, error_msg, resolved_path = validate_filepath(filepath)
        if not is_valid:
            return {
                "success": False,
                "error": {
                    "code": "FILE_NOT_FOUND" if "not found" in error_msg else
                            "PERMISSION_DENIED" if "Permission" in error_msg else
                            "UNSUPPORTED_FORMAT" if "Unsupported" in error_msg else
                            "INVALID_PARAMETER",
                    "message": error_msg,
                    "details": None,
                },
            }

        # Validate parameters
        if preview_max_dimension < 1 or preview_max_dimension > 10000:
            return {
                "success": False,
                "error": {
                    "code": "INVALID_PARAMETER",
                    "message": "preview_max_dimension must be between 1 and 10000",
                    "details": {"provided_value": preview_max_dimension},
                },
            }

        if preview_quality < 1 or preview_quality > 100:
            return {
                "success": False,
                "error": {
                    "code": "INVALID_PARAMETER",
                    "message": "preview_quality must be between 1 and 100",
                    "details": {"provided_value": preview_quality},
                },
            }

        if preview_format.upper() not in ["JPEG", "PNG", "WEBP"]:
            return {
                "success": False,
                "error": {
                    "code": "INVALID_PARAMETER",
                    "message": "preview_format must be 'JPEG', 'PNG', or 'WEBP'",
                    "details": {"provided_value": preview_format},
                },
            }

        # Extract metadata (fast operation)
        metadata = extract_metadata(resolved_path)

        # Load image for analysis
        image = _load_image(resolved_path, process_raw)

        # Calculate histogram
        hist_result = calculate_histogram(image)
        histogram = hist_result["histogram"]

        # Tonal analysis
        tonal_analysis = analyze_tonal_properties(image, histogram["luminance"])

        # Color analysis
        color_analysis = analyze_color_properties(image)

        # Spatial properties
        spatial_properties = analyze_spatial_properties(image)

        # Optional: Frequency analysis
        frequency_analysis = None
        if include_frequency:
            frequency_analysis = analyze_frequency_domain(image)

        # Optional: Preview generation
        preview = None
        if include_preview:
            preview = generate_preview(
                image,
                max_dimension=preview_max_dimension,
                format=preview_format,
                quality=preview_quality
            )

        return {
            "success": True,
            "filepath": str(resolved_path),
            "metadata": metadata,
            "histogram": histogram,
            "tonal_analysis": tonal_analysis,
            "color_analysis": color_analysis,
            "spatial_properties": spatial_properties,
            "frequency_analysis": frequency_analysis,
            "preview": preview,
        }

    except Exception as e:
        error_msg = str(e)
        error_code = "RAW_PROCESSING_FAILED" if "RAW" in error_msg else \
                     "CORRUPTED_FILE" if "corrupted" in error_msg.lower() else \
                     "OUT_OF_MEMORY" if "memory" in error_msg.lower() else \
                     "INVALID_PARAMETER"

        return {
            "success": False,
            "error": {
                "code": error_code,
                "message": error_msg,
                "details": {"exception_type": type(e).__name__},
            },
        }


def _load_image(filepath: Path, process_raw: bool = True) -> np.ndarray:
    """
    Load an image from file, handling RAW formats if needed.

    Args:
        filepath: Path to image file
        process_raw: Whether to process RAW files

    Returns:
        Image as numpy array in RGB format (H, W, 3)

    Raises:
        ValueError: If image cannot be loaded
    """
    # Handle RAW files
    if is_raw_format(filepath):
        if not process_raw:
            raise ValueError("RAW file processing disabled (process_raw=False)")

        try:
            with rawpy.imread(str(filepath)) as raw:
                # Process with default settings
                rgb = raw.postprocess(
                    use_camera_wb=True,  # Use camera white balance
                    half_size=False,     # Full resolution
                    no_auto_bright=True, # No auto brightness
                    output_bps=8,        # 8-bit output
                )
                return rgb
        except Exception as e:
            raise ValueError(f"RAW processing failed: {e}")

    # Handle standard image formats
    try:
        # Use PIL to load the image
        with Image.open(filepath) as img:
            # Convert to RGB if necessary
            if img.mode != "RGB":
                img = img.convert("RGB")

            # Convert to numpy array
            image = np.array(img)

            return image

    except Exception as e:
        raise ValueError(f"Failed to load image: {e}")
