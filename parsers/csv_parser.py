"""
parsers/csv_parser.py
Loads CSV rows into structured JSON objects for SurrealDB ingestion.
"""

import csv
import json
from pathlib import Path


def _coerce(value: str):
    """Try to coerce a string value to int or float; leave as str otherwise."""
    value = value.strip()
    try:
        return int(value)
    except ValueError:
        pass
    try:
        return float(value)
    except ValueError:
        pass
    return value


def parse_csv(filepathStr: str) -> dict:
    """
    Parse a CSV file and return a list of row records plus table-level metadata.

    Args:
        filepathStr: Path to the .csv file.

    Returns:
        dict with:
          - id          : table-level identifier
          - type        : "student_score"
          - source      : original filepath
          - columns     : list of column names
          - row_count   : number of data rows
          - records     : list of dicts, one per row (for ingestion)
    """
    filepath = Path(filepathStr)
    if not filepath.exists():
        raise FileNotFoundError(f"CSV file not found: {filepath}")

    records = []
    columns = []

    with open(filepath, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        columns = list(reader.fieldnames or [])
        for i, row in enumerate(reader):
            record = {col: _coerce(val) for col, val in row.items()}
            # Generate a stable SurrealDB-style record id
            student_id = record.get("student_id", f"row{i}")
            record["id"] = f"student_score:{student_id}"
            record["source"] = filepathStr
            record["type"] = "student_score"
            records.append(record)

    return {
        "id": f"table:{filepath.stem}",
        "type": "csv_table",
        "source": filepathStr,
        "columns": columns,
        "row_count": len(records),
        "records": records,
    }


if __name__ == "__main__":
    import sys
    path = sys.argv[1] if len(sys.argv) > 1 else "dataset/tables/student_scores.csv"
    data = parse_csv(path)
    # Print summary + first 3 records
    summary = {k: v for k, v in data.items() if k != "records"}
    print("=== Table Summary ===")
    print(json.dumps(summary, indent=2))
    print("\n=== First 3 Records ===")
    print(json.dumps(data["records"][:3], indent=2))
