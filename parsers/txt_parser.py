"""
parsers/txt_parser.py
Extracts full text content from .txt files.
"""

import os
import json
from pathlib import Path


def parse_txt(filepathStr: str) -> dict:
    """
    Parse a plain text file and return structured content.

    Args:
        filepathStr: Path to the .txt file.

    Returns:
        dict with id, source, content, type, and extracted metadata.
    """
    filepath = Path(filepathStr)
    if not filepath.exists():
        raise FileNotFoundError(f"TXT file not found: {filepath}")

    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        raw_text = f.read()

    # Simple heuristic: first non-empty line is often the title
    lines = [ln.strip() for ln in raw_text.splitlines() if ln.strip()]
    title = lines[0] if lines else filepath.stem.replace("_", " ").title()

    # Extract concepts mentioned after "Concepts covered:" line if present
    concepts = []
    for line in lines:
        if line.lower().startswith("concepts covered:") or line.lower().startswith("concepts:"):
            after = line.split(":", 1)[1].strip()
            concepts = [c.strip() for c in after.split(",") if c.strip()]

    # Extract due date if present
    due_date = None
    for line in lines:
        if "due date" in line.lower() or "due:" in line.lower():
            due_date = line.split(":", 1)[-1].strip() if ":" in line else None

    result = {
        "id": f"assignment:{filepath.stem}",
        "type": "assignment",
        "source": str(filepath),
        "filename": filepath.name,
        "title": title,
        "content": raw_text,
        "word_count": len(raw_text.split()),
        "concepts": concepts,
        "due_date": due_date,
    }

    return result


if __name__ == "__main__":
    import sys
    path = sys.argv[1] if len(sys.argv) > 1 else "dataset/text/assignment.txt"
    data = parse_txt(path)
    print(json.dumps(data, indent=2, default=str))
