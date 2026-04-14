"""
ingestion/ingest.py
Orchestrates parsing all dataset files and inserting them into SurrealDB.

Usage:
    python -m ingestion.ingest [--dry-run] [--http]

Options:
    --dry-run   Parse files and print JSON without writing to SurrealDB.
    --http      Use REST HTTP API instead of the Python SDK.
"""

from __future__ import annotations

import argparse
import json
import sys
import os
from pathlib import Path

# Allow running from project root
sys.path.insert(0, str(Path(__file__).parent.parent))

from parsers.code_workout_parser import parse_problem_concepts, parse_students, parse_submissions
from parsers.pdf_parser import parse_pdf
from parsers.txt_parser import parse_txt
from parsers.csv_parser import parse_csv
from parsers.json_parser import parse_json_metadata
from parsers.image_parser import parse_images_in_directory
from parsers.kg_parser import parse_kg
from ingestion.surreal_client import SurrealClient


# ── Dataset paths ─────────────────────────────────────────────────────────────

DATASET_ROOT = Path(__file__).parent.parent / "dataset"

FILES = {
    "pdf":    DATASET_ROOT / "text" / "lecture_notes.pdf",
    "txt":    DATASET_ROOT / "text" / "assignment.txt",
    "csv":    DATASET_ROOT / "tables" / "student_scores.csv",
    "json":   DATASET_ROOT / "metadata" / "metadata.json",
    "images": DATASET_ROOT / "images",
    "kg_csv": DATASET_ROOT / "knowledge_graph" / "cs_dataset.csv",
    "cw_students": DATASET_ROOT / "code_workout_data"/ "studentIDMapping_canvas_codeworkout.csv",
    "cw_submissions": DATASET_ROOT / "code_workout_data" / "MainTable.csv",
    "cw_concepts": DATASET_ROOT / "code_workout_data" / "matrix_interation_concepts_outcomes_w_ori_order.csv"
}


# ── Helpers ───────────────────────────────────────────────────────────────────

def log(msg: str):
    print(f"[ingest] {msg}")


def safe_parse(label: str, fn, *args, **kwargs):
    try:
        result = fn(*args, **kwargs)
        log(f"✓ Parsed {label}")
        return result
    except FileNotFoundError as e:
        log(f"⚠  Skipped {label} — file not found: {e}")
        return None
    except Exception as e:
        log(f"✗ Error parsing {label}: {e}")
        return None
    

def clean_record(data: dict):
    """Remove None values so SurrealDB doesn't receive NULL."""
    return {k: v for k, v in data.items() if v is not None}


# ── Insert helpers ────────────────────────────────────────────────────────────

def insert(client: SurrealClient, table: str, data: dict, use_http: bool):
    """Insert a single record, choosing SDK vs HTTP path."""
    data = clean_record(data)  # ← ADD THIS

    if use_http:
        res = client.http_create(table, data)
    else:
        res = client.create_sync(table, data)

    print(f'[DEBUG] Insert {table} -> {res}')
    return res

def insert_batch(client: SurrealClient, table: str, records: list[dict], use_http: bool):
    for rec in records:
        try:
            insert(client, table, rec, use_http)
        except Exception as e:
            log(f"  ✗ Failed to insert {rec.get('id', '?')}: {e}")

def insert_batch_bulk(client: SurrealClient, table: str, records: list[dict], use_http: bool, bulk_size: int = 10):
    for i in range(0, len(records), bulk_size):
        batch = records[i:i+bulk_size]
        log(f"Inserting batch of {len(batch)} records into '{table}' …")
        try:
            if use_http:
                res = client.http_create_bulk(table, batch)
                #print(f'[DEBUG] Bulk insert {table} -> {res}')
            else:
                for record in batch:
                    client.create_sync(table, record)
                    #print(f'[DEBUG] Insert {table} -> {record}')
            log(f"✓ Batch inserted {i+len(batch)}/{len(records)} records")
        except Exception as e:
            log(f"✗ Batch insert error: {e}")


def insert_relations(client: SurrealClient, relations: dict, use_http: bool):
    """Insert graph edges using RELATE statements."""
    for rel_name, edges in relations.items():
        if not edges:
            continue

        log(f"Inserting {len(edges)} '{rel_name}' relations …")

        for edge in edges:
            try:
                query = f"""
                RELATE {edge['in']} -> {rel_name} -> {edge['out']}
                CONTENT {{ id: "{edge['id']}" }};
                """

                if use_http:
                    client.http_query(query)
                else:
                    client.query_sync(query)

            except Exception as e:
                log(f"  ✗ Failed relation {edge['id']}: {e}")

# ── Graph relationship helpers ────────────────────────────────────────────────

GRAPH_RELATIONS_SQL = """
-- Create topic nodes from lecture topics
LET $topics = SELECT topics FROM lecture;
FOR $lecture IN (SELECT id, topics FROM lecture) {
    LET $lid = $lecture.id;
    FOR $topic IN $lecture.topics {
        LET $tid = type::record('topic', string::lowercase(string::replace($topic, ' ', '_')));
        INSERT IGNORE INTO topic { id: $tid, name: $topic };
        RELATE $lid -> covers -> $tid;
    }
};

-- Create topic nodes from assignment concepts
FOR $asgn IN (SELECT id, concepts FROM assignment) {
    LET $aid = $asgn.id;
    FOR $concept IN $asgn.concepts {
        LET $tid = type::record('topic', string::lowercase(string::replace($concept, ' ', '_')));
        INSERT IGNORE INTO topic { id: $tid, name: $concept };
        RELATE $aid -> requires -> $tid;
    }
};

-- Link metadata to materials it describes
FOR $mat IN (SELECT * FROM metadata) {
    LET $materials = $mat.data.materials ?? [];
    FOR $m IN $materials {
        LET $target_table = IF $m.type = 'lecture' THEN 'lecture'
                            ELSE IF $m.type = 'assignment' THEN 'assignment'
                            ELSE IF $m.type = 'image' THEN 'image'
                            ELSE NULL END;
        IF $target_table != NULL {
            LET $mid = $mat.id;
            LET $tid = type::record($target_table, string::replace($m.filename, '.', '_'));
            RELATE $mid -> describes -> $tid;
        }
    }
};
"""


def create_graph_relations(client: SurrealClient, use_http: bool):
    """Create graph edges between records."""
    log("Creating graph relationships …")
    try:
        if use_http:
            client.http_query(GRAPH_RELATIONS_SQL)
        else:
            client.query_sync(GRAPH_RELATIONS_SQL)
        log("✓ Graph relationships created")
    except Exception as e:
        log(f"✗ Graph relations error (non-fatal): {e}")


# ── Main ingestion flow ───────────────────────────────────────────────────────

def run(dry_run: bool = False, use_http: bool = False):
    log("=== Multimodal Ingestion Pipeline ===")

    # 1. Parse all files
    log("--- Phase 1: Parsing ---")

    for label, path in FILES.items():
        if not path.exists():
            raise FileNotFoundError(f"{label} file not found: {path}")

    lecture = safe_parse("PDF lecture notes", parse_pdf, str(FILES["pdf"]))
    assignment = safe_parse("TXT assignment", parse_txt, str(FILES["txt"]))
    csv_data = safe_parse("CSV scores", parse_csv, str(FILES["csv"]))
    metadata = safe_parse("JSON metadata", parse_json_metadata, str(FILES["json"]))
    images = safe_parse("Images directory", parse_images_in_directory, str(FILES["images"]))
    kg_graph = safe_parse("Knowledge Graph CSV", parse_kg, str(FILES["kg_csv"]),10) # NOTE: will only inject 10 of each
    students = safe_parse("Code Workout Students", parse_students, str(FILES["cw_students"]))
    submissions = safe_parse("Code Workout Submissions", parse_submissions, str(FILES["cw_submissions"]), only_section_ids=["1266"])
    cw_problem_concepts = safe_parse("Code Workout Problem Concepts", parse_problem_concepts, str(FILES["cw_concepts"]))

    # Derive topic list for lecture from metadata if PDF parsing was empty
    if lecture and metadata and not lecture.get("topics"):
        materials = metadata.get("data", {}).get("materials", [])
        for m in materials:
            if m.get("type") == "lecture":
                lecture["topics"] = m.get("topics", [])
                break

    if dry_run:
        log("--- DRY RUN: Printing parsed records ---")
        for label, data in [
            ("lecture", lecture),
            ("assignment", assignment),
            ("csv_table", csv_data),
            ("metadata", metadata),
            ("images", images),            
            ("kg_graph", kg_graph),
            ("students", students),
            ("submissions", submissions),
            ("cw_problem_concepts", cw_problem_concepts)
        ]:
            print(f"\n{'='*60}")
            print(f"  {label.upper()}")
            print('='*60)
            if data is None:
                print("  [Not parsed]")
            elif isinstance(data, list):
                print(json.dumps(data, indent=2, default=str))
            elif label == "kg_graph" and data:
                print(json.dumps({
                    "tables": {k: len(v) for k, v in data["tables"].items()},
                    "relations": {k: len(v) for k, v in data["relations"].items()}
                }, indent=2))
            else:
                # Truncate long content fields for readability
                display = {k: (v[:200] + "…" if isinstance(v, str) and len(v) > 200 else v)
                           for k, v in data.items() if k != "records"}
                print(json.dumps(display, indent=2, default=str))
                if "records" in data:
                    print(f"  … plus {len(data['records'])} student score records")
        log("Dry run complete.")
        return

    # 2. Connect to SurrealDB
    log("--- Phase 2: Connecting to SurrealDB ---")
    client = SurrealClient()
    try:
        if use_http:
            log("Using HTTP REST API")
            # Apply schema
            schema_path = Path(__file__).parent.parent / "schema.surql"
            if schema_path.exists():
                log("Applying schema …")
                client.execute_schema_file(str(schema_path))
                log("✓ Schema applied")
        else:
            log("Using Python SDK")
            client.connect_sync()
            log("✓ Connected")
    except Exception as e:
        log(f"✗ Connection failed: {e}")
        log("Tip: Start SurrealDB with: surreal start --user root --pass root memory")
        sys.exit(1)

    # 3. Insert records
    log("--- Phase 3: Ingesting records ---")

    if lecture:
        insert(client, "lecture", lecture, use_http)
        log(f"✓ Inserted lecture: {lecture.get('title')}")

    if assignment:
        insert(client, "assignment", assignment, use_http)
        log(f"✓ Inserted assignment: {assignment.get('title')}")

    if csv_data:
        log(f"Inserting {csv_data['row_count']} student score records …")
        insert_batch(client, "student_score", csv_data["records"], use_http)
        log("✓ Student scores inserted")

    if metadata:
        insert(client, "metadata", metadata, use_http)
        log(f"✓ Inserted metadata (course: {metadata.get('course_id')})")

    if images:
        log(f"Inserting {len(images)} image records …")
        insert_batch(client, "image", images, use_http)
        log("✓ Images inserted")

    if kg_graph:
        log("--- Inserting Knowledge Graph Tables ---")

        # Insert all tables
        for table_name, records in kg_graph["tables"].items():
            if not records:
                continue
            log(f"Inserting {len(records)} records into '{table_name}' …")
            insert_batch(client, table_name, records, use_http)

        log("✓ KG tables inserted")

        log("--- Inserting Knowledge Graph Relations ---")
        insert_relations(client, kg_graph["relations"], use_http)
        log("✓ KG relations inserted")

    if students:
        log(f"Inserting {len(students)} student records …")
        insert_batch_bulk(client, "student", students, use_http, bulk_size=100)
        log("✓ Code Workout students inserted")

    if submissions:
        log(f"Inserting {len(submissions)} code workout submission records …")
        insert_batch_bulk(client, "submission", submissions, use_http, bulk_size=5000)
        log("✓ Code Workout submissions inserted")
    
    if cw_problem_concepts:
        log(f"Inserting {len(cw_problem_concepts)} code workout problem records …")
        insert_batch_bulk(client, "cw_problem", cw_problem_concepts, use_http, bulk_size=100)
        log("✓ Code Workout problems inserted")

    # 4. Create graph relationships
    log("--- Phase 4: Graph Relationships ---")
    create_graph_relations(client, use_http)

    # 5. Cleanup
    if not use_http:
        client.close_sync()

    log("=== Ingestion complete ===")


# ── CLI entry point ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest multimodal dataset into SurrealDB")
    parser.add_argument("--dry-run", action="store_true", help="Parse only, do not write to DB")
    parser.add_argument("--http", action="store_true", help="Use HTTP REST API instead of SDK")
    args = parser.parse_args()
    run(dry_run=args.dry_run, use_http=args.http)
