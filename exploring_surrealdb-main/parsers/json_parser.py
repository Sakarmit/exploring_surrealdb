"""
parsers/json_parser.py
Loads and validates JSON metadata files.
"""

import json
from pathlib import Path
from typing import Any


# ── Minimal schema validation ──────────────────────────────────────────────────

REQUIRED_TOP_KEYS = {"course", "materials"}
REQUIRED_COURSE_KEYS = {"id", "title"}
REQUIRED_MATERIAL_KEYS = {"id", "type", "filename"}


def _validate(data: dict) -> list[str]:
    """Return a list of validation warnings (empty = valid)."""
    warnings = []

    missing_top = REQUIRED_TOP_KEYS - set(data.keys())
    if missing_top:
        warnings.append(f"Missing top-level keys: {missing_top}")

    course = data.get("course", {})
    missing_course = REQUIRED_COURSE_KEYS - set(course.keys())
    if missing_course:
        warnings.append(f"course block missing keys: {missing_course}")

    for mat in data.get("materials", []):
        missing_mat = REQUIRED_MATERIAL_KEYS - set(mat.keys())
        if missing_mat:
            warnings.append(
                f"Material '{mat.get('id', '?')}' missing keys: {missing_mat}"
            )

    return warnings


def parse_json_metadata(filepathStr: str) -> dict:
    """
    Load and validate a JSON metadata file.

    Args:
        filepathStr: Path to the .json file.

    Returns:
        dict with:
          - id           : metadata:<stem>
          - type         : "metadata"
          - source       : original filepath
          - data         : the parsed JSON content
          - valid        : bool
          - warnings     : list of validation messages
          - course_id    : convenience shortcut
          - material_ids : list of material ids found
    """
    filepath = Path(filepathStr)
    if not filepath.exists():
        raise FileNotFoundError(f"JSON file not found: {filepath}")

    with open(filepath, "r", encoding="utf-8") as f:
        data: Any = json.load(f)

    if not isinstance(data, dict):
        raise ValueError(f"Expected a JSON object at top level, got {type(data)}")

    warnings = _validate(data)

    course_id = data.get("course", {}).get("id", "unknown")
    material_ids = [m.get("id") for m in data.get("materials", [])]

    return {
        "id": f"metadata:{filepath.stem}",
        "type": "metadata",
        "source": str(filepath),
        "filename": filepath.name,
        "data": data,
        "valid": len(warnings) == 0,
        "warnings": warnings,
        "course_id": course_id,
        "material_ids": material_ids,
    }


if __name__ == "__main__":
    import sys
    path = sys.argv[1] if len(sys.argv) > 1 else "dataset/metadata/metadata.json"
    result = parse_json_metadata(path)
    # Pretty-print without the full nested data for brevity
    display = {k: v for k, v in result.items() if k != "data"}
    print(json.dumps(display, indent=2))
    print(f"\nCourse: {result['data'].get('course', {}).get('title')}")
    print(f"Materials: {result['material_ids']}")
