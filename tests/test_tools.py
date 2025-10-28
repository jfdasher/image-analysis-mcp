"""Basic tests for image analysis tools."""

import pytest
import numpy as np
from PIL import Image
import tempfile
import os
from pathlib import Path


@pytest.fixture
def test_image_path():
    """Create a temporary test image."""
    # Create a simple test image (100x100 RGB)
    img_array = np.random.randint(0, 256, (100, 100, 3), dtype=np.uint8)
    img = Image.fromarray(img_array, 'RGB')

    # Save to temporary file
    with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
        img.save(f, format='JPEG')
        temp_path = f.name

    yield temp_path

    # Cleanup
    if os.path.exists(temp_path):
        os.unlink(temp_path)


def test_get_image_metadata(test_image_path):
    """Test metadata extraction."""
    from image_analysis_mcp.tools import get_image_metadata

    result = get_image_metadata(test_image_path)

    assert result["success"] is True
    assert "metadata" in result
    assert result["metadata"]["dimensions"]["width"] == 100
    assert result["metadata"]["dimensions"]["height"] == 100
    assert result["metadata"]["file_format"] == "JPG"


def test_get_image_histogram(test_image_path):
    """Test histogram extraction."""
    from image_analysis_mcp.tools import get_image_histogram

    result = get_image_histogram(test_image_path)

    assert result["success"] is True
    assert "histogram" in result
    assert len(result["histogram"]["red"]) == 256
    assert len(result["histogram"]["green"]) == 256
    assert len(result["histogram"]["blue"]) == 256
    assert len(result["histogram"]["luminance"]) == 256

    assert "statistics" in result
    assert "red" in result["statistics"]
    assert "mean" in result["statistics"]["red"]


def test_analyze_image_file(test_image_path):
    """Test comprehensive image analysis."""
    from image_analysis_mcp.tools import analyze_image_file

    result = analyze_image_file(test_image_path)

    assert result["success"] is True
    assert "metadata" in result
    assert "histogram" in result
    assert "tonal_analysis" in result
    assert "color_analysis" in result
    assert "spatial_properties" in result

    # Check tonal analysis fields
    assert "shadows_pixels" in result["tonal_analysis"]
    assert "highlights_pixels" in result["tonal_analysis"]
    assert "dynamic_range_stops" in result["tonal_analysis"]

    # Check color analysis fields
    assert "dominant_colors" in result["color_analysis"]
    assert len(result["color_analysis"]["dominant_colors"]) == 5
    assert "color_temperature" in result["color_analysis"]

    # Check spatial properties
    assert "sharpness_score" in result["spatial_properties"]
    assert "noise_level" in result["spatial_properties"]


def test_analyze_with_preview(test_image_path):
    """Test analysis with preview generation."""
    from image_analysis_mcp.tools import analyze_image_file

    result = analyze_image_file(
        test_image_path,
        include_preview=True,
        preview_max_dimension=50
    )

    assert result["success"] is True
    assert result["preview"] is not None
    assert "base64" in result["preview"]
    assert "data_uri" in result["preview"]
    assert result["preview"]["dimensions"]["width"] <= 50
    assert result["preview"]["dimensions"]["height"] <= 50


def test_analyze_with_frequency(test_image_path):
    """Test analysis with frequency domain."""
    from image_analysis_mcp.tools import analyze_image_file

    result = analyze_image_file(
        test_image_path,
        include_frequency=True
    )

    assert result["success"] is True
    assert result["frequency_analysis"] is not None
    assert "high_freq_energy" in result["frequency_analysis"]
    assert "low_freq_energy" in result["frequency_analysis"]
    assert "detail_level" in result["frequency_analysis"]


def test_file_not_found():
    """Test error handling for non-existent file."""
    from image_analysis_mcp.tools import get_image_metadata

    result = get_image_metadata("/path/to/nonexistent/file.jpg")

    assert result["success"] is False
    assert "error" in result
    assert result["error"]["code"] == "FILE_NOT_FOUND"


def test_unsupported_format():
    """Test error handling for unsupported format."""
    from image_analysis_mcp.tools import get_image_metadata

    # Create a temporary text file
    with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as f:
        f.write(b"not an image")
        temp_path = f.name

    try:
        result = get_image_metadata(temp_path)

        assert result["success"] is False
        assert "error" in result
        assert result["error"]["code"] == "UNSUPPORTED_FORMAT"
    finally:
        os.unlink(temp_path)


def test_invalid_parameters():
    """Test error handling for invalid parameters."""
    from image_analysis_mcp.tools import analyze_image_file

    # Create a temporary test image
    img_array = np.random.randint(0, 256, (100, 100, 3), dtype=np.uint8)
    img = Image.fromarray(img_array, 'RGB')

    with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
        img.save(f, format='JPEG')
        temp_path = f.name

    try:
        # Test invalid preview_quality
        result = analyze_image_file(
            temp_path,
            preview_quality=150  # Invalid: must be 1-100
        )

        assert result["success"] is False
        assert result["error"]["code"] == "INVALID_PARAMETER"

        # Test invalid preview_format
        result = analyze_image_file(
            temp_path,
            preview_format="INVALID"
        )

        assert result["success"] is False
        assert result["error"]["code"] == "INVALID_PARAMETER"
    finally:
        os.unlink(temp_path)
