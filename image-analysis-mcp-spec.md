# Image Analysis MCP Server - Software Engineering Specification

**Version:** 2.0
**Date:** October 28, 2025
**Author:** Jim Dasher
**Target Framework:** FastMCP (Python)

---

## 1. Executive Summary

This specification defines a Model Context Protocol (MCP) server that provides Claude with comprehensive **read-only** image analysis capabilities. The server implements a fully **stateless architecture** where each tool call independently loads, analyzes, and returns results without maintaining any conversation state.

**Primary Use Cases:**
- Image metadata extraction and EXIF reading
- Histogram and tonal analysis
- Color analysis and temperature estimation
- Sharpness, noise, and spatial property analysis
- Frequency domain analysis (optional FFT)
- Optional preview generation during analysis

**Target Users:**
- Photographers needing detailed image analysis
- Developers building image processing workflows
- Anyone requiring comprehensive image inspection without modification

**Key Design Principles:**
- **Stateless**: No session state, no image caching, no conversation memory
- **Read-Only**: No image modification capabilities
- **No AI/ML**: No semantic segmentation, masking, or AI-based features
- **Pure Analysis**: Returns data only, with optional preview generation

---

## 2. System Architecture

### 2.1 Architectural Philosophy

**Fully Stateless Model:**
- Every tool call receives a file path as input
- Image is loaded, analyzed, and immediately discarded
- No caching between calls
- No session or conversation state
- Each operation is completely independent

**Rationale:** 
- Simplicity: No state management complexity
- Safety: No memory leaks or stale data
- Predictability: Same input always produces same output
- Scalability: No per-session resource limits

### 2.2 Component Overview

```
┌─────────────────────────────────────────────────────────────┐
│                        Claude Desktop                        │
│                    (MCP Client / Host)                       │
└────────────────────────┬────────────────────────────────────┘
                         │ JSON-RPC 2.0
                         │ stdio transport
┌────────────────────────┴────────────────────────────────────┐
│                  Image Analysis MCP Server                   │
│  ┌───────────────────────────────────────────────────────┐  │
│  │              Stateless Analysis Tools                  │  │
│  │  - get_image_metadata()                               │  │
│  │  - get_image_histogram()                              │  │
│  │  - analyze_image_file()                               │  │
│  │      (with optional preview generation)               │  │
│  └───────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────┐  │
│  │              Core Image Processing                     │  │
│  │  - NumPy/OpenCV (operations)                          │  │
│  │  - Pillow (I/O, EXIF)                                 │  │
│  │  - rawpy (RAW processing)                             │  │
│  │  - scikit-image (analysis)                            │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### 2.3 Data Flow

Every tool follows this pattern:
1. Receive file path as parameter
2. Validate file exists and is readable
3. Load image from disk
4. Perform analysis
5. Return results
6. Discard image from memory

**No state persists between calls.**

---

## 3. Tool Specifications

### 3.1 `get_image_metadata`

**Purpose:** Extract basic metadata and EXIF information from an image file without performing expensive analysis.

**Parameters:**
```python
{
  "filepath": str  # Absolute or relative file path
}
```

**Returns:**
```json
{
  "success": bool,
  "filepath": str,
  "metadata": {
    "dimensions": {
      "width": int,
      "height": int,
      "megapixels": float
    },
    "color_mode": str,      // "RGB", "RGBA", "L", "CMYK"
    "bit_depth": int,       // 8 or 16
    "file_format": str,     // "JPEG", "PNG", "TIFF", "CR2", etc.
    "file_size_mb": float,
    "color_space": str,     // "sRGB", "Adobe RGB", "ProPhoto RGB", "Unknown"
    "exif": {
      "camera": str,
      "lens": str,
      "iso": int,
      "aperture": float,
      "shutter_speed": str,
      "focal_length": int,
      "date_taken": str,    // ISO 8601 format
      "gps": {
        "latitude": float,
        "longitude": float,
        "altitude": float
      } | null,
      "raw": dict           // All EXIF tags as key-value pairs
    }
  }
}
```

**Behavior:**
- Supports JPEG, PNG, TIFF, RAW formats (CR2, NEF, ARW, DNG, etc.)
- Reads EXIF without loading full image data
- Fast operation (<100ms for most files)
- Returns null for missing EXIF fields
- Raw dictionary includes all available EXIF tags

**Error Handling:**
- File not found → 404 error with filepath
- Unsupported format → List supported formats
- Corrupted file → Detailed error from underlying library
- Permission denied → Clear permission error message

---

### 3.2 `analyze_image_file`

**Purpose:** Comprehensive analysis of an image file including histogram, tonal, color, and spatial properties.

**Parameters:**
```python
{
  "filepath": str,
  "include_frequency": bool = False,  # Expensive FFT analysis
  "include_preview": bool = False,    # Include base64-encoded preview image
  "preview_max_dimension": int = 1920, # Max width or height for preview
  "preview_format": str = "JPEG",     # "JPEG", "PNG", "WEBP"
  "preview_quality": int = 85,        # 1-100 for JPEG/WEBP
  "process_raw": bool = True          # Apply default RAW processing if applicable
}
```

**Returns:**
```json
{
  "success": bool,
  "filepath": str,
  "metadata": {
    "dimensions": {"width": int, "height": int, "megapixels": float},
    "color_mode": str,
    "bit_depth": int,
    "file_format": str,
    "file_size_mb": float,
    "color_space": str
  },
  "histogram": {
    "red": [int] × 256,
    "green": [int] × 256,
    "blue": [int] × 256,
    "luminance": [int] × 256
  },
  "tonal_analysis": {
    "shadows_pixels": int,           // Pixels in 0-64 range
    "midtones_pixels": int,           // 65-192 range
    "highlights_pixels": int,         // 193-255 range
    "clipped_shadows_pct": float,    // Percentage at 0
    "clipped_highlights_pct": float, // Percentage at 255
    "dynamic_range_stops": float,    // Estimated usable DR
    "mean_luminance": float,         // 0-255
    "median_luminance": float,       // 0-255
    "contrast_ratio": float,         // (max-min)/mean
    "tonal_distribution": {
      "shadows_pct": float,
      "midtones_pct": float,
      "highlights_pct": float
    }
  },
  "color_analysis": {
    "dominant_colors": [
      {
        "rgb": [int, int, int],
        "hex": str,
        "percentage": float,
        "name": str                   // Closest CSS color name
      }
    ] × 5,
    "color_temperature": str,         // "warm", "neutral", "cool"
    "temperature_kelvin": int,        // Estimated
    "saturation_mean": float,         // 0-1
    "saturation_median": float,       // 0-1
    "saturation_std": float,          // Standard deviation
    "white_balance_rgb_ratios": {
      "r": float,
      "g": float,
      "b": float
    },
    "color_cast": {
      "detected": bool,
      "direction": str,               // "red", "blue", "green", "magenta", etc.
      "severity": float               // 0-1
    }
  },
  "spatial_properties": {
    "sharpness_score": float,         // Laplacian variance
    "sharpness_rating": str,          // "very_soft", "soft", "moderate", "sharp", "very_sharp"
    "noise_level": float,             // Std in flat regions
    "noise_rating": str,              // "very_low", "low", "moderate", "high", "very_high"
    "edge_density_pct": float,        // Percentage edge pixels
    "texture_entropy": float,         // Measure of complexity (0-8)
    "blur_detection": {
      "is_blurry": bool,
      "confidence": float
    }
  },
  "frequency_analysis": {             // Only if include_frequency=True
    "high_freq_energy": float,        // Texture/detail content
    "low_freq_energy": float,         // Smooth gradients
    "frequency_ratio": float,         // high/low ratio
    "dominant_frequency": float,      // Peak in FFT
    "detail_level": str               // "low", "moderate", "high"
  } | null,
  "preview": {                        // Only if include_preview=True
    "base64": str,                    // Base64-encoded image data
    "format": str,                    // "JPEG", "PNG", "WEBP"
    "dimensions": {
      "width": int,
      "height": int
    },
    "size_bytes": int,                // Size of base64-decoded data
    "data_uri": str                   // Complete data URI (data:image/jpeg;base64,...)
  } | null
}
```

**Behavior:**
- Loads entire image into memory for analysis
- RAW files processed with default white balance if `process_raw=True`
- Histogram calculated on 8-bit normalized values
- FFT analysis optional due to performance cost (~1-2s for large images)
- All analysis performed in RGB color space
- If `include_preview=True`, generates a downsampled preview:
  - Scales image so largest dimension = `preview_max_dimension`
  - Maintains aspect ratio
  - Encodes to specified format with specified quality
  - Returns base64-encoded data and complete data URI
  - Preview generation adds ~100-300ms to response time
- Image discarded after analysis complete

**Preview Defaults:**
- `preview_max_dimension`: 1920 (full HD longest edge)
- `preview_format`: "JPEG" (best balance of size/quality)
- `preview_quality`: 85 (high quality, reasonable size)

**Performance:**
- Small images (<2MP): <500ms
- Medium images (2-12MP): 500ms-2s
- Large images (12-50MP): 2-5s
- Add 1-3s if `include_frequency=True`

**Error Handling:**
- Same as `get_image_metadata`
- Out of memory → Suggest reducing image size
- Timeout for very large files (>100MP)

---

### 3.3 `get_image_histogram`

**Purpose:** Fast histogram-only extraction without full analysis.

**Parameters:**
```python
{
  "filepath": str,
  "process_raw": bool = True
}
```

**Returns:**
```json
{
  "success": bool,
  "filepath": str,
  "histogram": {
    "red": [int] × 256,
    "green": [int] × 256,
    "blue": [int] × 256,
    "luminance": [int] × 256
  },
  "statistics": {
    "red": {"mean": float, "median": float, "std": float},
    "green": {"mean": float, "median": float, "std": float},
    "blue": {"mean": float, "median": float, "std": float},
    "luminance": {"mean": float, "median": float, "std": float}
  }
}
```

**Behavior:**
- Optimized for speed - only calculates histogram
- Useful when full analysis is not needed
- ~50-200ms for most images

---

## 4. Supported Image Formats

### 4.1 Input Formats (Reading)

| Format | Extension | Bit Depth | Color Modes | RAW Processing |
|--------|-----------|-----------|-------------|----------------|
| JPEG | .jpg, .jpeg | 8-bit | RGB, Grayscale | N/A |
| PNG | .png | 8-bit, 16-bit | RGB, RGBA, Grayscale | N/A |
| TIFF | .tif, .tiff | 8-bit, 16-bit | RGB, RGBA, CMYK | N/A |
| Canon RAW | .cr2, .cr3 | 14-bit | Bayer | ✅ |
| Nikon RAW | .nef | 14-bit | Bayer | ✅ |
| Sony RAW | .arw | 14-bit | Bayer | ✅ |
| Adobe DNG | .dng | 14-bit | Bayer | ✅ |
| Fuji RAW | .raf | 14-bit | X-Trans | ✅ |
| Olympus RAW | .orf | 12-bit | Bayer | ✅ |
| WebP | .webp | 8-bit | RGB, RGBA | N/A |

### 4.2 Preview Output Formats

When using `include_preview=True` with `analyze_image_file`, the preview is returned as base64-encoded data in one of these formats:

| Format | Compression | Best For | Quality Range |
|--------|-------------|----------|---------------|
| JPEG | Lossy | Photos, general use (default) | 1-100 |
| PNG | Lossless | Graphics, transparency | N/A |
| WebP | Lossy/Lossless | Modern web, smaller sizes | 1-100 |

### 4.3 RAW Processing Defaults

When `process_raw=True`:
- **White Balance:** Camera embedded (as-shot)
- **Demosaicing:** High-quality (AHD or DHT algorithm)
- **Color Space:** sRGB
- **Gamma:** 2.2
- **Highlight Recovery:** Moderate (clip at 98%)
- **Noise Reduction:** None
- **Sharpening:** None

---

## 5. Error Handling

### 5.1 Error Response Format

All tools return errors in consistent format:
```json
{
  "success": false,
  "error": {
    "code": str,           // "FILE_NOT_FOUND", "UNSUPPORTED_FORMAT", etc.
    "message": str,        // Human-readable error
    "details": dict | null // Additional context
  }
}
```

### 5.2 Error Codes

| Code | Description | User Action |
|------|-------------|-------------|
| `FILE_NOT_FOUND` | File does not exist | Check filepath |
| `PERMISSION_DENIED` | Cannot read file | Check permissions |
| `UNSUPPORTED_FORMAT` | Format not supported | Convert file or use supported format |
| `CORRUPTED_FILE` | File is corrupted | Re-export or repair file |
| `OUT_OF_MEMORY` | Image too large | Reduce image size |
| `INVALID_PARAMETER` | Bad parameter value | Check parameter constraints |
| `RAW_PROCESSING_FAILED` | RAW conversion failed | Try `process_raw=False` |

### 5.3 Validation

**File Path Validation:**
- Must be non-empty string
- File must exist and be readable
- Extension must match supported format

**Parameter Validation:**
- `preview_max_dimension`: 1-10000
- `preview_quality`: 1-100
- `preview_format`: Must be in ["JPEG", "PNG", "WEBP"]

---

## 6. Performance Characteristics

### 6.1 Benchmarks

Typical performance on modern hardware (2024):

| Operation | 2MP Image | 12MP Image | 50MP Image |
|-----------|-----------|------------|------------|
| `get_image_metadata` | 10ms | 15ms | 25ms |
| `get_image_histogram` | 50ms | 150ms | 600ms |
| `analyze_image_file` (no options) | 200ms | 800ms | 3000ms |
| `analyze_image_file` (with preview) | 300ms | 1100ms | 4000ms |
| `analyze_image_file` (with FFT) | 500ms | 2000ms | 8000ms |
| `analyze_image_file` (FFT + preview) | 600ms | 2300ms | 9000ms |

### 6.2 Memory Usage

| Operation | Peak Memory |
|-----------|-------------|
| `get_image_metadata` | <10MB |
| `get_image_histogram` | 1.5× image size |
| `analyze_image_file` | 2× image size |
| `analyze_image_file` (with preview) | 3× image size (source + preview + temp) |

**Typical Image Sizes:**
- 2MP: 6MB in memory (RGB)
- 12MP: 36MB in memory
- 50MP: 150MB in memory

**No persistent memory usage** - all memory released after each call.

### 6.3 Optimization Recommendations

For best performance:
1. Use `get_image_metadata` when you only need EXIF/basic info
2. Use `get_image_histogram` when you only need histogram data
3. Avoid `include_frequency=True` unless needed
4. Use `include_preview=True` only when you need to see the image
5. For RAW files, metadata extraction is fast without full processing

---

## 7. Dependencies

### 7.1 Python Packages

```toml
[tool.poetry.dependencies]
python = "^3.10"
fastmcp = "^1.0.0"
numpy = "^1.26.0"
opencv-python = "^4.9.0"
pillow = "^10.2.0"
rawpy = "^0.19.0"
scikit-image = "^0.22.0"
exifread = "^3.0.0"
```

### 7.2 System Requirements

- **Python:** 3.10+
- **RAM:** 4GB minimum, 8GB recommended
- **CPU:** Multi-core recommended for FFT analysis
- **Disk:** Temporary space for RAW processing (2-3× RAW file size)

### 7.3 Optional Dependencies

```toml
[tool.poetry.group.dev.dependencies]
pytest = "^8.0.0"
pytest-asyncio = "^0.23.0"
black = "^24.0.0"
mypy = "^1.8.0"
```

---

## 8. Testing Strategy

### 8.1 Unit Tests

Each tool must have tests covering:
- Happy path with various formats
- Error conditions (file not found, corrupted, etc.)
- Boundary conditions (very small/large images)
- Parameter validation
- RAW processing with and without `process_raw` flag

### 8.2 Test Dataset

Required test images:
- **JPEG:** 2MP, 12MP, 50MP (8-bit sRGB)
- **PNG:** 8-bit and 16-bit (with/without alpha)
- **TIFF:** 8-bit and 16-bit
- **RAW:** CR2, NEF, ARW, DNG samples
- **Corrupted:** Invalid headers, truncated files
- **Edge Cases:** 1×1 pixel, 100MP, grayscale, CMYK

### 8.3 Integration Tests

Test complete workflows:
1. Analyze RAW → Generate preview → Analyze preview
2. Get metadata → Get histogram → Full analysis (verify consistency)
3. Large batch processing (memory stability)

### 8.4 Performance Tests

Benchmark each tool against target performance metrics:
- No regression in response times
- Memory cleanup verified (no leaks)
- Consistent performance across formats

---

## 9. Usage Examples

### 9.1 Basic Metadata Extraction

**User:** "What camera took this photo?"

**Claude:**
```python
metadata = get_image_metadata(filepath="IMG_1234.CR2")
print(f"Camera: {metadata['metadata']['exif']['camera']}")
print(f"Lens: {metadata['metadata']['exif']['lens']}")
print(f"Settings: ISO {metadata['metadata']['exif']['iso']}, "
      f"f/{metadata['metadata']['exif']['aperture']}, "
      f"{metadata['metadata']['exif']['shutter_speed']}")
```

### 9.2 Image Quality Analysis

**User:** "Is this image sharp enough for printing?"

**Claude:**
```python
analysis = analyze_image_file(
    filepath="wedding_photo.jpg",
    include_frequency=False
)

sharpness = analysis['spatial_properties']['sharpness_score']
rating = analysis['spatial_properties']['sharpness_rating']
noise = analysis['spatial_properties']['noise_rating']

print(f"Sharpness: {rating} (score: {sharpness:.2f})")
print(f"Noise: {noise}")
print(f"Resolution: {analysis['metadata']['dimensions']['megapixels']}MP")

if rating in ["sharp", "very_sharp"] and noise in ["very_low", "low"]:
    print("✓ Suitable for printing")
else:
    print("⚠ May not be optimal for large prints")
```

### 9.3 Exposure Analysis

**User:** "Is this photo overexposed?"

**Claude:**
```python
analysis = analyze_image_file(filepath="sunset.jpg")

tonal = analysis['tonal_analysis']
print(f"Clipped highlights: {tonal['clipped_highlights_pct']:.1f}%")
print(f"Clipped shadows: {tonal['clipped_shadows_pct']:.1f}%")
print(f"Mean luminance: {tonal['mean_luminance']:.0f}/255")

if tonal['clipped_highlights_pct'] > 5.0:
    print("⚠ Significant highlight clipping detected")
elif tonal['clipped_highlights_pct'] > 1.0:
    print("⚠ Minor highlight clipping")
else:
    print("✓ Good exposure")
```

### 9.4 Color Analysis

**User:** "What are the dominant colors in this landscape?"

**Claude:**
```python
analysis = analyze_image_file(filepath="landscape.jpg")

colors = analysis['color_analysis']['dominant_colors']
for i, color in enumerate(colors, 1):
    print(f"{i}. {color['name']} - {color['percentage']:.1f}%")
    print(f"   RGB: {color['rgb']}, Hex: {color['hex']}")

temp = analysis['color_analysis']['color_temperature']
kelvin = analysis['color_analysis']['temperature_kelvin']
print(f"\nOverall tone: {temp} ({kelvin}K)")
```

### 9.6 Analysis with Preview

**User:** "Analyze this image and show me what it looks like."

**Claude:**
```python
analysis = analyze_image_file(
    filepath="photo.CR2",
    include_preview=True,
    preview_max_dimension=1920,
    preview_format="JPEG",
    preview_quality=85
)

# Access the analysis data
print(f"Sharpness: {analysis['spatial_properties']['sharpness_rating']}")
print(f"Exposure: {analysis['tonal_analysis']['mean_luminance']:.0f}/255")

# The preview is available as base64 or data URI
preview_data_uri = analysis['preview']['data_uri']
# Can be used directly in HTML: <img src="{preview_data_uri}">

preview_dimensions = analysis['preview']['dimensions']
print(f"Preview: {preview_dimensions['width']}×{preview_dimensions['height']}")
```

---

## 10. Future Enhancements (Post-V1)

### 10.1 Additional Analysis Features

- **Face detection count** (without identification)
- **Scene classification** (landscape, portrait, macro, etc.)
- **Quality scoring** (composite score based on multiple factors)
- **Chromatic aberration detection**
- **Lens distortion measurement**
- **Motion blur detection and quantification**

### 10.2 Format Support

- **HEIF/HEIC** (Apple's format)
- **AVIF** (modern format)
- **BMP** (legacy format)
- **SVG** (vector graphics, rasterize for analysis)

### 10.3 Performance Improvements

- **GPU acceleration** for FFT and large image processing
- **Parallel processing** for batch operations
- **Streaming analysis** for very large files (partial loading)
- **Smart caching** at filesystem level (optional)

### 10.4 Analysis Enhancements

- **Optical flow analysis** (motion between frames)
- **Lens metadata extraction** (from database)
- **Color grading detection** (film emulation identification)
- **Histogram matching** (find similar images by histogram)

---

## 11. Implementation Decisions (RESOLVED)

All open questions have been resolved with the following decisions:

1. **RAW Processing Library:** ✅ rawpy - Better Python integration and more actively maintained
2. **Preview Compression:** ✅ Default JPEG quality of 85 - Good balance of quality/size, user can override
3. **Error Verbosity:** ✅ User-friendly messages by default, optional FASTMCP_DEBUG env var for stack traces
4. **Histogram Bins:** ✅ Fixed 256 bins - Consistent with 8-bit normalization, simplifies implementation
5. **Color Space Conversions:** ✅ RGB only for v1.0 - LAB/HSV analysis deferred to future enhancements
6. **EXIF Timezone Handling:** ✅ Return as-is from EXIF (usually naive), include timezone info if present
7. **Timeout Value:** ✅ 60 seconds for images >100MP
8. **Color Temperature Calculation:** ✅ R/B ratio method with mapping to Kelvin ranges
9. **Noise Detection Algorithm:** ✅ Variance threshold (variance < 100) in 32×32 blocks
10. **Dynamic Range Formula:** ✅ `log2((p98_luminance - p2_luminance) / noise_floor)` with 0-20 stop bounds

---

## 12. Success Criteria

**Functional Requirements:**
- ✅ Read and analyze JPEG, PNG, TIFF, RAW formats
- ✅ Extract complete EXIF metadata
- ✅ Generate accurate histograms and tonal analysis
- ✅ Color analysis with dominant color extraction
- ✅ Spatial property analysis (sharpness, noise, edges)
- ✅ Optional frequency domain analysis
- ✅ Optional preview generation during analysis

**Non-Functional Requirements:**
- ✅ <5s response time for common operations (12MP images)
- ✅ No memory leaks - memory released after each call
- ✅ Graceful error handling with actionable messages
- ✅ 90%+ test coverage for critical paths
- ✅ Consistent output format across all tools

**User Experience:**
- ✅ Photographers can quickly assess image quality
- ✅ Developers can build automated workflows
- ✅ Clear, structured JSON responses
- ✅ Predictable behavior (stateless = reproducible)

---

## Appendix A: Tool Quick Reference

| Tool | Purpose | Avg Time (12MP) | Memory | Returns Data |
|------|---------|-----------------|--------|--------------|
| `get_image_metadata` | EXIF & basic info | 15ms | <10MB | Metadata dict |
| `get_image_histogram` | Histogram only | 150ms | 36MB | Histogram arrays |
| `analyze_image_file` | Full analysis | 800ms | 72MB | Comprehensive dict |
| `analyze_image_file` (preview) | Analysis + preview | 1100ms | 108MB | + Base64 preview |
| `analyze_image_file` (FFT) | With frequency | 2000ms | 72MB | + Frequency data |

**All tools are stateless** - no session state maintained.

---

## Appendix B: Color Name Mapping

The `dominant_colors` field includes CSS color names for user-friendly output. Mapping uses nearest color in RGB space:

**Common Color Names:**
```
Red, Green, Blue, Yellow, Orange, Purple, Pink, Brown,
Black, White, Gray, Cyan, Magenta, Lime, Navy, Teal,
Olive, Maroon, Silver, Indigo, Violet, Gold, Beige, Tan
```

**Algorithm:** Euclidean distance in RGB space to nearest CSS3 extended color.

---

## Appendix C: Sharpness Rating Scale

Sharpness score → Rating mapping:

| Score Range | Rating | Description |
|-------------|--------|-------------|
| 0-50 | `very_soft` | Severe blur or focus issues |
| 51-150 | `soft` | Noticeable softness, not ideal |
| 151-500 | `moderate` | Acceptable for web/casual |
| 501-1000 | `sharp` | Good for most uses |
| 1000+ | `very_sharp` | Excellent, suitable for large prints |

**Note:** Scores are Laplacian variance and scale with image resolution.

---

## Appendix D: Noise Rating Scale

Noise level → Rating mapping:

| Noise Level | Rating | Description |
|-------------|--------|-------------|
| 0-5 | `very_low` | Clean, professional quality |
| 6-15 | `low` | Minimal noise, acceptable |
| 16-30 | `moderate` | Visible but manageable |
| 31-50 | `high` | Significant noise |
| 50+ | `very_high` | Severe noise, quality concerns |

**Note:** Noise level is standard deviation in flat regions.

---

**End of Specification**

Version: 2.0
Last Updated: October 28, 2025
Status: ✅ IMPLEMENTED
Architecture: Fully Stateless, Read-Only Analysis

---

## Implementation Notes

This specification has been fully implemented in Python using the FastMCP framework.

**Implementation Location:** `/home/jfd/prj/image_analysis/`

**Key Files:**
- `src/image_analysis_mcp/server.py` - FastMCP server with 3 tools
- `src/image_analysis_mcp/tools.py` - Tool implementations
- `src/image_analysis_mcp/analysis/` - Analysis modules (7 files)
- `README.md` - User documentation
- `QUICKSTART.md` - 5-minute setup guide
- `IMPLEMENTATION_SUMMARY.md` - Technical implementation details

**Changes from Original Spec:**
1. Removed invalid validation parameters (target_width, percent) - Section 5.3
2. Removed WRITE_FAILED error code (read-only server) - Section 5.2
3. Resolved all open questions with documented decisions - Section 11

All functional and non-functional requirements have been met.
