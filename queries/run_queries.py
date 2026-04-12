"""
queries/run_queries.py
Executes all SurrealQL multimodal queries and pretty-prints results.

Usage:
    python -m queries.run_queries [--http] [--query N]

Options:
    --http      Use HTTP REST API instead of the Python SDK.
    --query N   Run only query number N (1–7). Default: run all.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from ingestion.surreal_client import SurrealClient


# ── Query definitions ─────────────────────────────────────────────────────────

QUERIES = {
    1: {
        "title": "Full-Text Keyword Search Over Extracted Text",
        "description": (
            "Uses BM25 full-text search to find lectures and assignments "
            "that mention 'normalization', ranked by relevance."
        ),
        "sql": """
            USE NS education DB learning_management_db;
            LET $keyword = 'normalization';
            SELECT id, title, type, search::score(1) AS relevance_score
            FROM lecture WHERE content @1@ $keyword
            UNION ALL
            SELECT id, title, type, search::score(1) AS relevance_score
            FROM assignment WHERE content @1@ $keyword
            ORDER BY relevance_score DESC;
        """,
    },
    2: {
        "title": "Join CSV Student Scores with Assignment Metadata",
        "description": (
            "Computes average score per student across all assessments "
            "and enriches with assignment context."
        ),
        "sql": """
            USE NS education DB learning_management_db;
            SELECT
                student_id, name, assignment_1, assignment_2,
                midterm, final, grade,
                math::mean([assignment_1, assignment_2, midterm, final]) AS avg_score
            FROM student_score
            ORDER BY avg_score DESC;
        """,
    },
    3: {
        "title": "Link Lecture Content to Metadata Topics",
        "description": (
            "Joins lecture records with their corresponding metadata "
            "material entries to compare topic lists."
        ),
        "sql": """
            USE NS education DB learning_management_db;
            SELECT
                id AS lecture_id,
                title AS lecture_title,
                topics AS lecture_topics,
                page_count,
                source
            FROM lecture;
        """,
    },
    4: {
        "title": "Graph Traversal — Topics Shared by Lectures and Assignments",
        "description": (
            "Traverses the graph to find topics that appear in both a "
            "lecture (via covers) and an assignment (via requires)."
        ),
        "sql": """
            USE NS education DB learning_management_db;
            SELECT
                id AS topic_id,
                name AS topic_name,
                <-covers<-lecture.title AS covered_by_lectures,
                <-requires<-assignment.title AS required_by_assignments
            FROM topic
            ORDER BY topic_name;
        """,
    },
    5: {
        "title": "Grade Distribution Summary",
        "description": "Aggregates student grades and computes per-grade statistics.",
        "sql": """
            USE NS education DB learning_management_db;
            SELECT
                grade,
                count() AS num_students,
                math::mean(final) AS avg_final,
                math::min(final) AS min_final,
                math::max(final) AS max_final
            FROM student_score
            GROUP BY grade
            ORDER BY avg_final DESC;
        """,
    },
    6: {
        "title": "All Materials Described by Metadata (Graph Traversal)",
        "description": "Follows describes edges from metadata to linked materials.",
        "sql": """
            USE NS education DB learning_management_db;
            SELECT id, course_id, ->describes->*.id AS described_materials
            FROM metadata;
        """,
    },
    7: {
        "title": "At-Risk Students Scoring Below 75 on Final",
        "description": "Identifies students who may need additional support.",
        "sql": """
            USE NS education DB learning_management_db;
            SELECT student_id, name, final AS final_score, grade
            FROM student_score
            WHERE final < 75
            ORDER BY final ASC;
        """,
    },
}


# ── Helpers ───────────────────────────────────────────────────────────────────

def header(text: str):
    print(f"\n{'═'*64}")
    print(f"  {text}")
    print('═'*64)


def run_query(client: SurrealClient, qnum: int, use_http: bool):
    q = QUERIES[qnum]
    header(f"Query {qnum}: {q['title']}")
    print(f"  {q['description']}\n")

    try:
        if use_http:
            result = client.http_query(q["sql"])
        else:
            result = client.query_sync(q["sql"])

        print(json.dumps(result, indent=2, default=str))
    except Exception as e:
        print(f"  ✗ Query failed: {e}")


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Run multimodal SurrealQL queries")
    parser.add_argument("--http", action="store_true", help="Use HTTP REST API")
    parser.add_argument("--query", type=int, default=0,
                        help="Run only this query number (1-7). Default: all.")
    args = parser.parse_args()

    client = SurrealClient()

    try:
        if not args.http:
            client.connect_sync()
            print("✓ Connected to SurrealDB (SDK)")
        else:
            print("Using HTTP REST API")
    except Exception as e:
        print(f"✗ Connection failed: {e}")
        sys.exit(1)

    query_nums = [args.query] if args.query else list(QUERIES.keys())

    for qnum in query_nums:
        if qnum not in QUERIES:
            print(f"Unknown query number: {qnum}")
            continue
        run_query(client, qnum, args.http)

    if not args.http:
        client.close_sync()

    print("\n✓ All queries complete.")


if __name__ == "__main__":
    main()
