"""Image metadata and EXIF extraction."""

import os
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

import exifread
from PIL import Image
import rawpy


def extract_metadata(filepath: Path) -> Dict[str, Any]:
    """
    Extract basic metadata and EXIF information from an image file.

    Args:
        filepath: Path to the image file

    Returns:
        Dictionary containing metadata and EXIF information
    """
    # Get file size
    file_size_bytes = os.path.getsize(filepath)
    file_size_mb = file_size_bytes / (1024 * 1024)

    # Determine file format from extension
    file_format = filepath.suffix.upper().replace(".", "")

    # Extract EXIF data
    exif_data = _extract_exif(filepath)

    # Get image dimensions and color info
    dimensions, color_mode, bit_depth, color_space = _get_image_info(filepath)

    metadata = {
        "dimensions": {
            "width": dimensions[0],
            "height": dimensions[1],
            "megapixels": round((dimensions[0] * dimensions[1]) / 1_000_000, 2),
        },
        "color_mode": color_mode,
        "bit_depth": bit_depth,
        "file_format": file_format,
        "file_size_mb": round(file_size_mb, 2),
        "color_space": color_space,
        "exif": exif_data,
    }

    return metadata


def _extract_exif(filepath: Path) -> Dict[str, Any]:
    """
    Extract EXIF data from image file.

    Args:
        filepath: Path to image file

    Returns:
        Dictionary with EXIF data
    """
    exif_dict = {
        "camera": None,
        "lens": None,
        "iso": None,
        "aperture": None,
        "shutter_speed": None,
        "focal_length": None,
        "date_taken": None,
        "gps": None,
        "raw": {},
    }

    try:
        # Read EXIF tags
        with open(filepath, "rb") as f:
            tags = exifread.process_file(f, details=False)

        # Store all raw tags
        exif_dict["raw"] = {k: str(v) for k, v in tags.items() if not k.startswith("Thumbnail")}

        # Extract specific fields
        # Camera make and model
        make = tags.get("Image Make", None)
        model = tags.get("Image Model", None)
        if make and model:
            exif_dict["camera"] = f"{str(make).strip()} {str(model).strip()}"
        elif model:
            exif_dict["camera"] = str(model).strip()

        # Lens
        lens = tags.get("EXIF LensModel", None)
        if lens:
            exif_dict["lens"] = str(lens).strip()

        # ISO
        iso = tags.get("EXIF ISOSpeedRatings", None)
        if iso:
            try:
                exif_dict["iso"] = int(str(iso))
            except (ValueError, TypeError):
                pass

        # Aperture (F-number)
        fnumber = tags.get("EXIF FNumber", None)
        if fnumber:
            try:
                # FNumber is often stored as a ratio
                val = str(fnumber)
                if "/" in val:
                    num, denom = val.split("/")
                    exif_dict["aperture"] = round(float(num) / float(denom), 1)
                else:
                    exif_dict["aperture"] = round(float(val), 1)
            except (ValueError, TypeError, ZeroDivisionError):
                pass

        # Shutter speed (exposure time)
        exposure = tags.get("EXIF ExposureTime", None)
        if exposure:
            exif_dict["shutter_speed"] = str(exposure)

        # Focal length
        focal = tags.get("EXIF FocalLength", None)
        if focal:
            try:
                val = str(focal)
                if "/" in val:
                    num, denom = val.split("/")
                    exif_dict["focal_length"] = int(float(num) / float(denom))
                else:
                    exif_dict["focal_length"] = int(float(val))
            except (ValueError, TypeError, ZeroDivisionError):
                pass

        # Date taken
        date_taken = tags.get("EXIF DateTimeOriginal", None) or tags.get("Image DateTime", None)
        if date_taken:
            try:
                # Convert to ISO 8601 format
                dt = datetime.strptime(str(date_taken), "%Y:%m:%d %H:%M:%S")
                exif_dict["date_taken"] = dt.isoformat()
            except (ValueError, TypeError):
                exif_dict["date_taken"] = str(date_taken)

        # GPS data
        gps_lat = tags.get("GPS GPSLatitude", None)
        gps_lat_ref = tags.get("GPS GPSLatitudeRef", None)
        gps_lon = tags.get("GPS GPSLongitude", None)
        gps_lon_ref = tags.get("GPS GPSLongitudeRef", None)
        gps_alt = tags.get("GPS GPSAltitude", None)

        if gps_lat and gps_lon:
            try:
                lat = _convert_gps_to_decimal(str(gps_lat), str(gps_lat_ref) if gps_lat_ref else "N")
                lon = _convert_gps_to_decimal(str(gps_lon), str(gps_lon_ref) if gps_lon_ref else "E")

                gps_data = {
                    "latitude": lat,
                    "longitude": lon,
                    "altitude": None,
                }

                if gps_alt:
                    try:
                        alt_str = str(gps_alt)
                        if "/" in alt_str:
                            num, denom = alt_str.split("/")
                            gps_data["altitude"] = round(float(num) / float(denom), 2)
                        else:
                            gps_data["altitude"] = round(float(alt_str), 2)
                    except (ValueError, TypeError, ZeroDivisionError):
                        pass

                exif_dict["gps"] = gps_data
            except (ValueError, TypeError):
                pass

    except Exception as e:
        # If EXIF reading fails, return empty dict with error in raw
        exif_dict["raw"]["_error"] = str(e)

    return exif_dict


def _convert_gps_to_decimal(gps_coord: str, ref: str) -> float:
    """
    Convert GPS coordinates from degrees/minutes/seconds to decimal.

    Args:
        gps_coord: String like "[41, 53, 23]" or similar
        ref: Reference (N/S for latitude, E/W for longitude)

    Returns:
        Decimal coordinate
    """
    # Parse the coordinate string
    # Format is usually like "[41, 53, 23]" for degrees, minutes, seconds
    coord_str = gps_coord.strip("[]")
    parts = [p.strip() for p in coord_str.split(",")]

    if len(parts) != 3:
        raise ValueError(f"Invalid GPS coordinate format: {gps_coord}")

    # Convert each part (may be fractions)
    degrees = _parse_fraction(parts[0])
    minutes = _parse_fraction(parts[1])
    seconds = _parse_fraction(parts[2])

    # Convert to decimal
    decimal = degrees + (minutes / 60.0) + (seconds / 3600.0)

    # Apply reference (negative for S/W)
    if ref in ["S", "W"]:
        decimal = -decimal

    return round(decimal, 6)


def _parse_fraction(value: str) -> float:
    """Parse a value that might be a fraction or decimal."""
    value = value.strip()
    if "/" in value:
        num, denom = value.split("/")
        return float(num) / float(denom)
    return float(value)


def _get_image_info(filepath: Path) -> tuple:
    """
    Get image dimensions, color mode, bit depth, and color space.

    Args:
        filepath: Path to image file

    Returns:
        Tuple of (dimensions, color_mode, bit_depth, color_space)
    """
    ext = filepath.suffix.lower()

    # Handle RAW files
    if ext in [".cr2", ".cr3", ".nef", ".arw", ".dng", ".raf", ".orf"]:
        try:
            with rawpy.imread(str(filepath)) as raw:
                # Get RAW dimensions
                sizes = raw.sizes
                width = sizes.width
                height = sizes.height
                return (width, height), "Bayer", 14, "Raw"
        except Exception as e:
            raise ValueError(f"Failed to read RAW file: {e}")

    # Handle standard image formats
    try:
        with Image.open(filepath) as img:
            width, height = img.size
            color_mode = img.mode  # RGB, RGBA, L, CMYK, etc.

            # Determine bit depth
            # PIL doesn't directly expose bit depth, but we can infer from mode
            if img.mode in ["1", "L", "P", "RGB", "RGBA", "CMYK", "YCbCr", "LAB", "HSV"]:
                bit_depth = 8
            elif img.mode in ["I", "F", "I;16", "I;16L", "I;16B"]:
                bit_depth = 16
            else:
                bit_depth = 8  # Default

            # Try to get color space from ICC profile or EXIF
            color_space = "Unknown"

            # Check ICC profile
            if "icc_profile" in img.info:
                color_space = "ICC Profile"

            # Try to get from EXIF
            try:
                exif = img.getexif()
                if exif:
                    # ColorSpace tag (0x0001 = sRGB, 0xFFFF = Uncalibrated, 0x0002 = Adobe RGB)
                    color_space_tag = exif.get(0xA001)  # ColorSpace tag
                    if color_space_tag == 1:
                        color_space = "sRGB"
                    elif color_space_tag == 2:
                        color_space = "Adobe RGB"
                    elif color_space_tag == 0xFFFF:
                        color_space = "Uncalibrated"
            except Exception:
                pass

            # Default to sRGB for common formats if unknown
            if color_space == "Unknown" and img.mode == "RGB":
                color_space = "sRGB"

            return (width, height), color_mode, bit_depth, color_space

    except Exception as e:
        raise ValueError(f"Failed to read image file: {e}")
