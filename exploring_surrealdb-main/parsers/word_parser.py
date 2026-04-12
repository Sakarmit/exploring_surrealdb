"""
parsers/doc_parser.py
Extracts text, title, and paragraph count from Word (.docx) files.
"""

import os
import json
from pathlib import Path


def parse_word(filepathStr: str) -> dict:
    """
    Parse a Word (.docx) file and return structured metadata + text content.

    Args:
        filepathStr: Path to the .docx file.

    Returns:
        dict with keys: id, source, title, filename, content, type
    """
    filepath = Path(filepathStr)
    if not filepath.exists():
        raise FileNotFoundError(f"Document not found: {filepath}")

    # Standardized result structure consistent with pdf_parser.py
    result = {
        "id": f"lecture:{filepath.stem}",
        "type": "lecture",
        "source": str(filepath),
        "filename": filepath.name,
        "title": None,
        "content": None,
        "topics": [],
    }

    try:
        from docx import Document
        doc = Document(str(filepath))

        # Extract title from core properties or fallback to filename
        result["title"] = doc.core_properties.title if doc.core_properties.title else None
        if not result["title"]:
            result["title"] = filepath.stem.replace("_", " ").title()

        # Extract text from all paragraphs
        # Using concat-style logic (joining a list) for performance
        text_parts = [para.text for para in doc.paragraphs if para.text.strip()]
        result["content"] = "\n".join(text_parts).strip()
        
        return result

    except ImportError:
        # Fallback if python-docx is not installed
        result["title"] = filepath.stem.replace("_", " ").title()
        result["content"] = f"[Binary DOCX — install python-docx to extract text] Path: {filepath}"
        return result
    
    except Exception as e:
        result["content"] = f"Error parsing Word file: {str(e)}"
        return result


if __name__ == "__main__":
    import sys
    # Default to a sample file path if none provided
    path = sys.argv[1] if len(sys.argv) > 1 else "dataset/text/lecture_notes.docx"
    
    # Simple check to handle file existence for local testing
    if os.path.exists(path):
        data = parse_word(path)
        print(json.dumps(data, indent=2, default=str))
    else:
        print(f"File not found for testing: {path}")