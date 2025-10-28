# Quick Start Guide

Get the Image Analysis MCP Server running in 5 minutes.

## 1. Choose Installation Method

### Option A: Docker (Easiest - No Python Setup Needed!)

```bash
cd /home/jfd/prj/image_analysis

# Build the image (5-10 minutes first time)
docker build -t image-analysis-mcp:latest .

# Test it
docker run --rm image-analysis-mcp:latest python -c "import image_analysis_mcp; print('✓ OK')"
```

**Then skip to step 3** and use the Docker configuration.

### Option B: Poetry

```bash
cd /home/jfd/prj/image_analysis
curl -sSL https://install.python-poetry.org | python3 -
poetry install
```

### Option C: pip

```bash
cd /home/jfd/prj/image_analysis
pip install -r requirements.txt
pip install -e .
```

## 2. Test Installation

```bash
# Validate structure
python validate_structure.py

# Run tests (after installing dependencies)
pytest tests/
```

## 3. Configure Claude Desktop

**Find your config file:**
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`
- Linux: `~/.config/Claude/claude_desktop_config.json`

**Choose configuration based on installation method:**

### If using Docker:
```json
{
  "mcpServers": {
    "image-analysis": {
      "command": "docker",
      "args": [
        "run", "--rm", "-i",
        "-v", "/path/to/your/images:/images:ro",
        "image-analysis-mcp:latest"
      ]
    }
  }
}
```
Then reference images as `/images/photo.jpg` in Claude.

### If using Poetry:
```json
{
  "mcpServers": {
    "image-analysis": {
      "command": "poetry",
      "args": ["run", "image-analysis-mcp"],
      "cwd": "/home/jfd/prj/image_analysis"
    }
  }
}
```

### If using pip:
```json
{
  "mcpServers": {
    "image-analysis": {
      "command": "python",
      "args": ["-m", "image_analysis_mcp.server"],
      "cwd": "/home/jfd/prj/image_analysis",
      "env": {
        "PYTHONPATH": "/home/jfd/prj/image_analysis/src"
      }
    }
  }
}
```

## 4. Restart Claude Desktop

Close and reopen Claude Desktop completely.

## 5. Test with Claude

Try these example prompts:

### Basic Metadata
```
I have an image at /path/to/photo.jpg - what camera was it taken with?
```

### Image Quality
```
Analyze /path/to/photo.jpg and tell me if it's sharp enough for printing
```

### Exposure Check
```
Is /path/to/photo.jpg overexposed? Check the histogram
```

### Color Analysis
```
What are the dominant colors in /path/to/landscape.jpg?
```

### With Preview
```
Analyze /path/to/photo.CR2 and show me a preview
```

## Troubleshooting

### Server not showing up in Claude
1. Check config file path and JSON syntax
2. Ensure absolute paths are used for `cwd`
3. Restart Claude Desktop completely
4. Check Claude Desktop logs

### Import errors
```bash
# Install missing dependencies
pip install -r requirements.txt
```

### Can't find Poetry
```bash
# Install Poetry
curl -sSL https://install.python-poetry.org | python3 -

# Or use pip instead (see step 1)
```

### RAW file processing fails
- Ensure rawpy is installed: `pip install rawpy`
- Some camera models may not be supported
- Try `process_raw=False` to skip RAW processing

## File Paths

When testing, use absolute paths:
```
/home/jfd/Pictures/photo.jpg  ✓
~/Pictures/photo.jpg          ✓  (will be resolved)
photo.jpg                     ✗  (relative paths may fail)
```

## Available Tools

1. **get_metadata** - Fast EXIF extraction (~15ms)
2. **get_histogram** - Histogram only (~150ms)
3. **analyze_image** - Full analysis (~800ms)

## Common Use Cases

| What you want | Tool used | Example prompt |
|---------------|-----------|----------------|
| Camera settings | get_metadata | "What ISO was this shot at?" |
| Exposure check | analyze_image | "Is this overexposed?" |
| Sharpness | analyze_image | "Is this sharp?" |
| Colors | analyze_image | "What colors are in this?" |
| See the image | analyze_image | "Show me what this looks like" |

## Performance Tips

1. Use `get_metadata` when you only need EXIF
2. Use `get_histogram` when you only need histogram
3. Avoid `include_frequency=True` unless needed (adds 1-2s)
4. Set `preview_max_dimension=1280` for faster previews

## Next Steps

- See **README.md** for full documentation
- See **IMPLEMENTATION_SUMMARY.md** for technical details
- See **image-analysis-mcp-spec.md** for complete specification

## Support

If something isn't working:
1. Check the error message in Claude
2. Verify file paths are correct
3. Ensure dependencies are installed
4. Check Claude Desktop configuration
5. Restart Claude Desktop

---

Ready to analyze images! 📸
