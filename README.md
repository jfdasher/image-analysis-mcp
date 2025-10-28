# Image Analysis MCP Server

A comprehensive **read-only** image analysis MCP (Model Context Protocol) server that provides Claude with detailed image inspection capabilities.

## Features

- **Metadata & EXIF Extraction**: Camera settings, GPS, timestamps, and more
- **Histogram Analysis**: RGB and luminance histograms with statistics
- **Tonal Analysis**: Shadows, midtones, highlights, dynamic range, and clipping detection
- **Color Analysis**: Dominant colors, color temperature, saturation, and color cast detection
- **Spatial Properties**: Sharpness scoring, noise estimation, edge density, and blur detection
- **Frequency Analysis**: FFT-based detail level assessment (optional)
- **Preview Generation**: Base64-encoded preview images (optional)

## Supported Formats

### Standard Formats
- JPEG (.jpg, .jpeg)
- PNG (.png)
- TIFF (.tif, .tiff)
- WebP (.webp)

### RAW Formats
- Canon RAW (.cr2, .cr3)
- Nikon RAW (.nef)
- Sony RAW (.arw)
- Adobe DNG (.dng)
- Fuji RAW (.raf)
- Olympus RAW (.orf)

## Installation

### Option 1: Docker (Recommended)

The easiest way to get started - no Python setup required!

```bash
# Build the Docker image
cd image_analysis
docker build -t image-analysis-mcp:latest .

# Test it works
docker run --rm image-analysis-mcp:latest python -c "import image_analysis_mcp; print('✓ OK')"
```

See **[DOCKER.md](DOCKER.md)** for complete Docker documentation.

### Option 2: Poetry

```bash
# Prerequisites: Python 3.12+, Poetry
cd image_analysis

# Install dependencies
poetry install

# Activate the virtual environment
poetry shell
```

### Option 3: pip

```bash
# Prerequisites: Python 3.12+
cd image_analysis

# Install the package
pip install -e .
```

## Usage

### Running the MCP Server

The server can be run directly:

```bash
# Using Poetry
poetry run image-analysis-mcp

# Or if in activated virtual environment
image-analysis-mcp
```

### Configuration for Claude Desktop

Add to your Claude Desktop configuration file (`claude_desktop_config.json`):

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
**Linux**: `~/.config/Claude/claude_desktop_config.json`

#### Using Docker (Recommended)

```json
{
  "mcpServers": {
    "image-analysis": {
      "command": "docker",
      "args": [
        "run",
        "--rm",
        "-i",
        "-v",
        "/path/to/your/images:/images:ro",
        "image-analysis-mcp:latest"
      ]
    }
  }
}
```

Then reference images as `/images/photo.jpg` in Claude.

#### Using Poetry

```json
{
  "mcpServers": {
    "image-analysis": {
      "command": "poetry",
      "args": ["run", "image-analysis-mcp"],
      "cwd": "/absolute/path/to/image_analysis"
    }
  }
}
```

#### Using pip (Global Install)

```json
{
  "mcpServers": {
    "image-analysis": {
      "command": "image-analysis-mcp"
    }
  }
}
```

## Available Tools

### 1. `get_metadata`

Fast metadata and EXIF extraction without loading full image data.

**Parameters:**
- `filepath` (str): Path to image file

**Example:**
```
What camera was used for IMG_1234.CR2?
```

### 2. `get_histogram`

Extract RGB and luminance histograms with channel statistics.

**Parameters:**
- `filepath` (str): Path to image file
- `process_raw` (bool, optional): Process RAW files (default: True)

**Example:**
```
Show me the histogram for landscape.jpg
```

### 3. `analyze_image`

Comprehensive image analysis including all properties.

**Parameters:**
- `filepath` (str): Path to image file
- `include_frequency` (bool, optional): Include FFT analysis (default: False)
- `include_preview` (bool, optional): Generate preview image (default: False)
- `preview_max_dimension` (int, optional): Preview max size (default: 1920)
- `preview_format` (str, optional): "JPEG", "PNG", or "WEBP" (default: "JPEG")
- `preview_quality` (int, optional): Quality 1-100 (default: 85)
- `process_raw` (bool, optional): Process RAW files (default: True)

**Example:**
```
Analyze photo.jpg and tell me if it's sharp enough for printing
```

```
Analyze this RAW file and show me a preview
```

## Architecture

This server follows a **fully stateless** architecture:

- Each tool call is independent
- Images are loaded, analyzed, and immediately discarded
- No caching or session state
- Predictable and reproducible results

## Performance

Typical performance on modern hardware:

| Operation | 2MP Image | 12MP Image | 50MP Image |
|-----------|-----------|------------|------------|
| `get_metadata` | 10ms | 15ms | 25ms |
| `get_histogram` | 50ms | 150ms | 600ms |
| `analyze_image` | 200ms | 800ms | 3000ms |
| `analyze_image` (with preview) | 300ms | 1100ms | 4000ms |
| `analyze_image` (with FFT) | 500ms | 2000ms | 8000ms |

## Example Conversations

### Check Image Quality
```
User: Is wedding_photo.jpg sharp enough for a large print?
Claude: [Uses analyze_image to check sharpness, noise, and resolution]
```

### Exposure Analysis
```
User: Is this sunset photo overexposed?
Claude: [Uses analyze_image to check histogram and clipping]
```

### Color Analysis
```
User: What are the dominant colors in this landscape?
Claude: [Uses analyze_image to extract dominant colors and temperature]
```

### Metadata Extraction
```
User: What camera settings were used for IMG_5678.NEF?
Claude: [Uses get_metadata to extract EXIF data]
```

## Error Handling

The server provides clear error messages:

- `FILE_NOT_FOUND`: File doesn't exist
- `PERMISSION_DENIED`: Cannot read file
- `UNSUPPORTED_FORMAT`: Format not supported
- `CORRUPTED_FILE`: File is corrupted
- `OUT_OF_MEMORY`: Image too large
- `INVALID_PARAMETER`: Bad parameter value
- `RAW_PROCESSING_FAILED`: RAW conversion failed

## Development

### Running Tests

```bash
poetry run pytest
```

### Code Formatting

```bash
poetry run black src/
```

### Type Checking

```bash
poetry run mypy src/
```

## License

This project is provided as-is for use with Claude Desktop and MCP.

## Author

Jim Dasher

## Version

1.0.0 - October 28, 2025
