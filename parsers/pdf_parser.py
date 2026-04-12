"""
parsers/pdf_parser.py
Extracts text, title, and page count from PDF files.
"""

import os
import json
from pathlib import Path


def parse_pdf(filepathStr: str) -> dict:
    """
    Parse a PDF file and return structured metadata + text content.

    Args:
        filepathStr: Path to the PDF file.

    Returns:
        dict with keys: id, source, title, page_count, content, type
    """
    filepath = Path(filepathStr)
    if not filepath.exists():
        raise FileNotFoundError(f"PDF not found: {filepath}")

    result = {
        "id": f"lecture:{filepath.stem}",
        "type": "pdf",
        "source": filepathStr,
        "title": None,
        "page_count": None,
        "content": None,
        "topics": [],
    }

    # Try PyMuPDF (fitz) first — best quality
    try:
        import fitz  # PyMuPDF
        doc = fitz.open(str(filepath))
        result["page_count"] = len(doc)

        # Extract title from metadata
        meta = doc.metadata
        result["title"] = meta.get("title") if meta else None
        if not result["title"]:
            result["title"] = filepath.stem.replace("_", " ").title()

        # Extract all text
        text_parts = []
        for page in doc:
            text_parts.append(page.get_text())
        result["content"] = "\n".join(text_parts).strip()
        doc.close()
        return result

    except ImportError:
        pass

    # Fallback: pdfplumber
    try:
        import pdfplumber
        with pdfplumber.open(str(filepath)) as pdf:
            result["page_count"] = len(pdf.pages)
            result["title"] = filepath.stem.replace("_", " ").title()
            text_parts = []
            for page in pdf.pages:
                t = page.extract_text()
                if t:
                    text_parts.append(t)
            result["content"] = "\n".join(text_parts).strip()
        return result

    except ImportError:
        pass

    # Fallback: pypdf
    try:
        from pypdf import PdfReader
        reader = PdfReader(str(filepath))
        result["page_count"] = len(reader.pages)
        result["title"] = (
            reader.metadata.title if reader.metadata and reader.metadata.title
            else filepath.stem.replace("_", " ").title()
        )
        text_parts = []
        for page in reader.pages:
            t = page.extract_text()
            if t:
                text_parts.append(t)
        result["content"] = "\n".join(text_parts).strip()
        return result

    except ImportError:
        pass

    # Last resort: file size only
    result["title"] = filepath.stem.replace("_", " ").title()
    result["page_count"] = 0
    result["content"] = f"[Binary PDF — install PyMuPDF, pdfplumber, or pypdf to extract text] Path: {filepath}"
    return result


if __name__ == "__main__":
    import sys
    path = sys.argv[1] if len(sys.argv) > 1 else "dataset/text/lecture_notes.pdf"
    data = parse_pdf(path)
    print(json.dumps(data, indent=2, default=str))
