"""FastMCP server for image analysis."""

from fastmcp import FastMCP
from .tools import get_image_metadata, get_image_histogram, analyze_image_file

# Initialize FastMCP server
mcp = FastMCP("Image Analysis MCP Server")


@mcp.tool()
def get_metadata(filepath: str) -> dict:
    """
    Extract basic metadata and EXIF information from an image file without performing expensive analysis.

    This is a fast operation (<100ms for most files) that reads metadata without loading the full image.

    Args:
        filepath: Absolute or relative file path to the image

    Returns:
        Dictionary containing:
        - dimensions (width, height, megapixels)
        - color_mode (RGB, RGBA, L, CMYK, etc.)
        - bit_depth (8 or 16)
        - file_format (JPEG, PNG, TIFF, CR2, etc.)
        - file_size_mb
        - color_space (sRGB, Adobe RGB, etc.)
        - exif (camera, lens, ISO, aperture, shutter speed, focal length, date, GPS, and all raw tags)

    Supported formats: JPEG, PNG, TIFF, WebP, and RAW formats (CR2, CR3, NEF, ARW, DNG, RAF, ORF)
    """
    return get_image_metadata(filepath)


@mcp.tool()
def get_histogram(filepath: str, process_raw: bool = True) -> dict:
    """
    Fast histogram-only extraction without full analysis.

    This tool is optimized for speed when you only need histogram data (~50-200ms for most images).

    Args:
        filepath: Absolute or relative file path to the image
        process_raw: Apply default RAW processing if the file is a RAW format (default: True)

    Returns:
        Dictionary containing:
        - histogram: Red, green, blue, and luminance histograms (256 bins each)
        - statistics: Mean, median, and standard deviation for each channel

    Supported formats: JPEG, PNG, TIFF, WebP, and RAW formats (CR2, CR3, NEF, ARW, DNG, RAF, ORF)
    """
    return get_image_histogram(filepath, process_raw)


@mcp.tool()
def analyze_image(
    filepath: str,
    include_frequency: bool = False,
    include_preview: bool = False,
    preview_max_dimension: int = 1920,
    preview_format: str = "JPEG",
    preview_quality: int = 85,
    process_raw: bool = True
) -> dict:
    """
    Comprehensive analysis of an image file including histogram, tonal, color, and spatial properties.

    This performs a complete analysis of the image. Performance varies by image size:
    - Small images (<2MP): <500ms
    - Medium images (2-12MP): 500ms-2s
    - Large images (12-50MP): 2-5s
    - Add 1-3s if include_frequency=True

    Args:
        filepath: Absolute or relative file path to the image
        include_frequency: Include expensive FFT frequency domain analysis (default: False)
        include_preview: Include base64-encoded preview image in results (default: False)
        preview_max_dimension: Maximum width or height for preview (default: 1920)
        preview_format: Preview format - "JPEG", "PNG", or "WEBP" (default: "JPEG")
        preview_quality: JPEG/WEBP quality, 1-100 (default: 85)
        process_raw: Apply default RAW processing if applicable (default: True)

    Returns:
        Dictionary containing:
        - metadata: Basic image information and EXIF data
        - histogram: Red, green, blue, and luminance histograms
        - tonal_analysis: Shadows/midtones/highlights distribution, clipping, dynamic range, contrast
        - color_analysis: Dominant colors (top 5), color temperature, saturation, white balance, color cast
        - spatial_properties: Sharpness score/rating, noise level/rating, edge density, texture entropy, blur detection
        - frequency_analysis: High/low frequency energy, frequency ratio, detail level (only if include_frequency=True)
        - preview: Base64-encoded preview with data URI (only if include_preview=True)

    Supported formats: JPEG, PNG, TIFF, WebP, and RAW formats (CR2, CR3, NEF, ARW, DNG, RAF, ORF)

    RAW Processing Defaults (when process_raw=True):
    - White Balance: Camera embedded (as-shot)
    - Demosaicing: High-quality algorithm
    - Color Space: sRGB
    - Gamma: 2.2
    - No noise reduction or sharpening applied
    """
    return analyze_image_file(
        filepath,
        include_frequency,
        include_preview,
        preview_max_dimension,
        preview_format,
        preview_quality,
        process_raw
    )


def main():
    """Entry point for running the MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
