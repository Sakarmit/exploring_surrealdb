"""
parsers/video_parser.py
Extracts file path, size, duration, frame count, FPS, resolution, and format from video files.
"""

import os
import json
from pathlib import Path


SUPPORTED_EXTENSIONS = {
    ".mp4",
    ".mov",
    ".avi",
    ".mkv",
    ".webm",
    ".m4v",
    ".wmv",
    ".flv",
    ".mpeg",
    ".mpg",
}


def parse_video(filepathStr: str) -> dict:
    """
    Extract metadata from a video file.

    Args:
        filepathStr: Path to the video file.

    Returns:
        dict with:
          - id
          - type
          - source
          - filename
          - format
          - file_size_bytes
          - duration_seconds
          - frame_count
          - fps
          - width
          - height
          - codec
    """
    filepath = Path(filepathStr)
    if not filepath.exists():
        raise FileNotFoundError(f"Video not found: {filepath}")

    ext = filepath.suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise ValueError(f"Unsupported video extension: {ext}")

    file_size = os.path.getsize(filepath)

    result = {
        "id": f"video:{filepath.stem}",
        "type": "video",
        "source": str(filepath),
        "filename": filepath.name,
        "format": ext.lstrip(".").upper(),
        "file_size_bytes": file_size,
        "duration_seconds": None,
        "frame_count": None,
        "fps": None,
        "width": None,
        "height": None,
        "codec": None,
    }

    # Try OpenCV first
    try:
        import cv2

        cap = cv2.VideoCapture(str(filepath))
        if cap.isOpened():
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
            width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
            height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)

            result["fps"] = float(fps) if fps and fps > 0 else None
            result["frame_count"] = int(frame_count) if frame_count and frame_count > 0 else None
            result["width"] = int(width) if width and width > 0 else None
            result["height"] = int(height) if height and height > 0 else None

            if result["fps"] and result["frame_count"]:
                result["duration_seconds"] = round(result["frame_count"] / result["fps"], 3)

        cap.release()
        return result

    except ImportError:
        pass
    except Exception:
        pass

    # Fallback: imageio metadata
    try:
        import imageio.v3 as iio

        meta = iio.immeta(str(filepath))

        fps = meta.get("fps")
        duration = meta.get("duration")
        size = meta.get("size")
        codec = meta.get("codec")
        nframes = meta.get("nframes")

        result["fps"] = float(fps) if fps is not None else result["fps"]
        result["duration_seconds"] = float(duration) if duration is not None else result["duration_seconds"]
        result["frame_count"] = int(nframes) if nframes is not None else result["frame_count"]
        result["codec"] = str(codec) if codec is not None else result["codec"]

        if isinstance(size, (list, tuple)) and len(size) >= 2:
            result["width"] = int(size[0])
            result["height"] = int(size[1])

        if result["duration_seconds"] is None and result["fps"] and result["frame_count"]:
            result["duration_seconds"] = round(result["frame_count"] / result["fps"], 3)

        return result

    except ImportError:
        pass
    except Exception:
        pass

    # Fallback: moviepy
    try:
        from moviepy.video.io.VideoFileClip import VideoFileClip

        with VideoFileClip(str(filepath)) as clip:
            result["duration_seconds"] = round(float(clip.duration), 3) if clip.duration else None
            result["fps"] = float(clip.fps) if clip.fps else None
            result["width"] = int(clip.w) if clip.w else None
            result["height"] = int(clip.h) if clip.h else None

            if result["duration_seconds"] and result["fps"]:
                result["frame_count"] = int(result["duration_seconds"] * result["fps"])

        return result

    except ImportError:
        pass
    except Exception:
        pass

    # Last resort: return basic file metadata only
    return result


def parse_videos_in_directory(directoryStr: str) -> list[dict]:
    """Parse all supported videos in a directory."""
    directory = Path(directoryStr)
    if not directory.exists():
        raise FileNotFoundError(f"Directory not found: {directory}")
    if not directory.is_dir():
        raise NotADirectoryError(f"Not a directory: {directory}")

    results = []
    for f in sorted(directory.iterdir()):
        if f.suffix.lower() in SUPPORTED_EXTENSIONS:
            try:
                results.append(parse_video(str(f)))
            except Exception as e:
                results.append(
                    {
                        "id": f"video:{f.stem}",
                        "error": str(e),
                        "source": str(f),
                    }
                )
    return results


if __name__ == "__main__":
    import sys

    path = sys.argv[1] if len(sys.argv) > 1 else "dataset/videos/sample.mp4"
    filepath = Path(path)

    if filepath.is_dir():
        data = parse_videos_in_directory(path)
    else:
        data = parse_video(path)

    print(json.dumps(data, indent=2, default=str))