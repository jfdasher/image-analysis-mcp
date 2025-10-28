"""Preview image generation with base64 encoding."""

import base64
from io import BytesIO
from typing import Dict, Any, Optional
import numpy as np
from PIL import Image


def generate_preview(
    image: np.ndarray,
    max_dimension: int = 1920,
    format: str = "JPEG",
    quality: int = 85
) -> Optional[Dict[str, Any]]:
    """
    Generate a downsampled preview image encoded as base64.

    Args:
        image: Image as numpy array in RGB format (H, W, 3)
        max_dimension: Maximum width or height for preview
        format: Output format ("JPEG", "PNG", "WEBP")
        quality: Quality for lossy formats (1-100)

    Returns:
        Dictionary with preview data or None if generation fails
    """
    try:
        # Convert numpy array to PIL Image
        pil_image = Image.fromarray(image)

        # Calculate new dimensions maintaining aspect ratio
        width, height = pil_image.size
        if max(width, height) > max_dimension:
            if width > height:
                new_width = max_dimension
                new_height = int(height * (max_dimension / width))
            else:
                new_height = max_dimension
                new_width = int(width * (max_dimension / height))

            # Resize image
            pil_image = pil_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        else:
            new_width, new_height = width, height

        # Encode to bytes
        buffer = BytesIO()

        # Format-specific encoding
        if format.upper() == "PNG":
            pil_image.save(buffer, format="PNG", optimize=True)
        elif format.upper() == "WEBP":
            pil_image.save(buffer, format="WEBP", quality=quality)
        else:  # Default to JPEG
            # Convert RGBA to RGB for JPEG
            if pil_image.mode == "RGBA":
                pil_image = pil_image.convert("RGB")
            pil_image.save(buffer, format="JPEG", quality=quality, optimize=True)
            format = "JPEG"

        # Get bytes
        image_bytes = buffer.getvalue()

        # Encode to base64
        base64_encoded = base64.b64encode(image_bytes).decode('utf-8')

        # Create data URI
        mime_type = f"image/{format.lower()}"
        data_uri = f"data:{mime_type};base64,{base64_encoded}"

        return {
            "base64": base64_encoded,
            "format": format,
            "dimensions": {
                "width": new_width,
                "height": new_height,
            },
            "size_bytes": len(image_bytes),
            "data_uri": data_uri,
        }

    except Exception as e:
        # Return None if preview generation fails
        return None
