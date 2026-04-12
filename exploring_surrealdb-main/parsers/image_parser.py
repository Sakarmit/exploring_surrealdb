"""
parsers/image_parser.py
Extracts file path, dimensions, and file size from image files.
"""

import os
import json
from pathlib import Path


SUPPORTED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp", ".tiff"}


def parse_image(filepathStr: str) -> dict:
    """
    Extract metadata from an image file.

    Args:
        filepathStr: Path to the image file.

    Returns:
        dict with id, source, filename, file_size_bytes, width, height, format, type
    """
    filepath = Path(filepathStr)
    if not filepath.exists():
        raise FileNotFoundError(f"Image not found: {filepath}")

    ext = filepath.suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise ValueError(f"Unsupported image extension: {ext}")

    file_size = os.path.getsize(filepath)

    result = {
        "id": f"image:{filepath.stem}",
        "type": "image",
        "source": str(filepath),
        "filename": filepath.name,
        "format": ext.lstrip(".").upper(),
        "file_size_bytes": file_size,
        "width": None,
        "height": None,
        "mode": None,
    }

    # Try Pillow for dimensions
    try:
        from PIL import Image
        with Image.open(filepath) as img:
            result["width"], result["height"] = img.size
            result["mode"] = img.mode
        return result
    except ImportError:
        pass

    # Fallback: read PNG dimensions from raw bytes (no library needed)
    if ext == ".png":
        try:
            with open(filepath, "rb") as f:
                header = f.read(24)
            if header[:8] == b"\x89PNG\r\n\x1a\n":
                import struct
                width = struct.unpack(">I", header[16:20])[0]
                height = struct.unpack(">I", header[20:24])[0]
                result["width"] = width
                result["height"] = height
        except Exception:
            pass

    # Fallback: JPEG dimensions from raw bytes
    if ext in {".jpg", ".jpeg"}:
        try:
            with open(filepath, "rb") as f:
                data = f.read()
            i = 2  # skip SOI marker
            while i < len(data):
                if data[i] != 0xFF:
                    break
                marker = data[i + 1]
                if marker in (0xC0, 0xC1, 0xC2):
                    import struct
                    height, width = struct.unpack(">HH", data[i + 5:i + 9])
                    result["height"] = height
                    result["width"] = width
                    break
                length = int.from_bytes(data[i + 2:i + 4], "big")
                i += 2 + length
        except Exception:
            pass

    return result


def parse_images_in_directory(directoryStr: str) -> list[dict]:
    """Parse all supported images in a directory."""
    directory = Path(directoryStr)
    results = []
    for f in sorted(directory.iterdir()):
        if f.suffix.lower() in SUPPORTED_EXTENSIONS:
            try:
                results.append(parse_image(str(f)))
            except Exception as e:
                results.append({"id": f"image:{f.stem}", "error": str(e), "source": str(f)})
    return results


if __name__ == "__main__":
    import sys
    path = sys.argv[1] if len(sys.argv) > 1 else "dataset/images/sample_plot.png"
    data = parse_image(path)
    print(json.dumps(data, indent=2))
