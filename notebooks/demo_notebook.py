# %% [markdown]
# # CS401 — Multimodal Data Management with SurrealDB
# ### Demo Notebook: Parsing, Ingestion, and Queries
#
# This notebook walks through all four project phases:
# 1. Data Parsing
# 2. Schema & SurrealDB Setup
# 3. Ingestion
# 4. Multimodal Queries

# %%
import sys, json
from pathlib import Path

# Make sure project root is on path
sys.path.insert(0, str(Path(".").resolve()))

# %% [markdown]
# ## Phase 1 — Data Parsing

# %% [markdown]
# ### 1a. Parse Lecture Notes (PDF)

# %%
from parsers.pdf_parser import parse_pdf

lecture = parse_pdf("dataset/text/lecture_notes.pdf")

# Print everything except the full content body
summary = {k: v for k, v in lecture.items() if k != "content"}
print(json.dumps(summary, indent=2))
print(f"\nContent preview (first 400 chars):\n{lecture.get('content','')[:400]}")

# %% [markdown]
# ### 1b. Parse Assignment (TXT)

# %%
from parsers.txt_parser import parse_txt

assignment = parse_txt("dataset/text/assignment.txt")
print(json.dumps({k: v for k, v in assignment.items() if k != "content"}, indent=2))
print(f"\nContent preview:\n{assignment['content'][:300]}")

# %% [markdown]
# ### 1c. Parse Student Scores (CSV)

# %%
from parsers.csv_parser import parse_csv

csv_data = parse_csv("dataset/tables/student_scores.csv")
print(f"Columns : {csv_data['columns']}")
print(f"Rows    : {csv_data['row_count']}")
print("\nFirst 3 records:")
print(json.dumps(csv_data["records"][:3], indent=2))

# %% [markdown]
# ### 1d. Parse JSON Metadata

# %%
from parsers.json_parser import parse_json_metadata

metadata = parse_json_metadata("dataset/metadata/metadata.json")
print(f"Valid    : {metadata['valid']}")
print(f"Warnings : {metadata['warnings']}")
print(f"Course   : {metadata['data']['course']['title']}")
print(f"Materials: {metadata['material_ids']}")

# %% [markdown]
# ### 1e. Parse Images

# %%
from parsers.image_parser import parse_images_in_directory

images = parse_images_in_directory("dataset/images")
print(json.dumps(images, indent=2))

# %% [markdown]
# ## Phase 2 — Schema Design
#
# The schema is defined in `schema.surql`. Key design decisions:
#
# | Table | Type | Rationale |
# |-------|------|-----------|
# | `lecture` | SCHEMAFULL | Consistent PDF-derived fields; BM25 FTS index |
# | `assignment` | SCHEMAFULL | Consistent TXT-derived fields; BM25 FTS index |
# | `student_score` | SCHEMAFULL | Typed numeric fields; UNIQUE student_id index |
# | `metadata` | SCHEMALESS | Flexible JSON document; shape varies per course |
# | `image` | SCHEMAFULL | File metadata; optional width/height |
# | `concept` | SCHEMAFULL | Graph nodes representing abstract topics |
#
# **Graph edges:** `covers`, `requires`, `describes`, `submitted_for`

# %%
with open("schema.surql") as f:
    schema_text = f.read()
print(schema_text[:2000], "…")

# %% [markdown]
# ## Phase 3 — Ingestion
#
# The ingestion script handles the full pipeline in one command:
# ```bash
# python -m ingestion.ingest --http
# ```
# Below we demonstrate a dry run (no DB connection required).

# %%
from ingestion.ingest import run as ingest_all

ingest_all(dry_run=True)

# %% [markdown]
# ## Phase 4 — Multimodal Queries
#
# > **Note:** The cells below require a running SurrealDB instance.
# > Start one with:
# > ```bash
# > surreal start --user root --pass root memory
# > ```
# > Then re-run: `ingest_all(use_http=True)` to populate the DB.

# %%
# ── Query 1: Full-Text Keyword Search ──────────────────────────────────────────
QUERY_1 = """
USE NS education DB cs401;
LET $keyword = 'normalization';
SELECT id, title, type, search::score(1) AS relevance_score
FROM lecture WHERE content @1@ $keyword
UNION ALL
SELECT id, title, type, search::score(1) AS relevance_score
FROM assignment WHERE content @1@ $keyword
ORDER BY relevance_score DESC;
"""
print("Query 1: Full-Text Keyword Search")
print(QUERY_1)

# %%
# ── Query 2: Student Scores with Average ───────────────────────────────────────
QUERY_2 = """
USE NS education DB cs401;
SELECT
    student_id, name,
    assignment_1, assignment_2, midterm, final, grade,
    math::mean([assignment_1, assignment_2, midterm, final]) AS avg_score
FROM student_score
ORDER BY avg_score DESC;
"""
print("Query 2: Student Scores Join")
print(QUERY_2)

# %%
# ── Query 3: Lecture ↔ Metadata Topic Linkage ──────────────────────────────────
QUERY_3 = """
USE NS education DB cs401;
SELECT id, title, topics, page_count, source FROM lecture;
"""
print("Query 3: Lecture Content Linked to Metadata")
print(QUERY_3)

# %%
# ── Query 4: Graph Traversal ───────────────────────────────────────────────────
QUERY_4 = """
USE NS education DB cs401;
SELECT
    id AS concept_id,
    name AS concept_name,
    <-covers<-lecture.title AS covered_by_lectures,
    <-requires<-assignment.title AS required_by_assignments
FROM concept
ORDER BY concept_name;
"""
print("Query 4: Graph Traversal — Shared Concepts")
print(QUERY_4)

# %%
# ── Query 5: Grade Distribution Summary ───────────────────────────────────────
QUERY_5 = """
USE NS education DB cs401;
SELECT
    grade,
    count() AS num_students,
    math::mean(final) AS avg_final,
    math::min(final) AS min_final,
    math::max(final) AS max_final
FROM student_score
GROUP BY grade
ORDER BY avg_final DESC;
"""
print("Query 5: Grade Distribution")
print(QUERY_5)

# %% [markdown]
# ## Summary Statistics from Parsed Data
# (No DB required — computed from parsed CSV)

# %%
import statistics

scores = csv_data["records"]
finals = [r["final"] for r in scores]
avgs   = [round((r["assignment_1"] + r["assignment_2"] + r["midterm"] + r["final"]) / 4, 2)
          for r in scores]

print(f"Students      : {len(scores)}")
print(f"Final avg     : {statistics.mean(finals):.1f}")
print(f"Final median  : {statistics.median(finals):.1f}")
print(f"Final stdev   : {statistics.stdev(finals):.1f}")
print(f"Top student   : {max(scores, key=lambda r: r['final'])['name']}")
print(f"At-risk (<75) : {[r['name'] for r in scores if r['final'] < 75]}")

grade_dist = {}
for r in scores:
    grade_dist[r["grade"]] = grade_dist.get(r["grade"], 0) + 1
print(f"\nGrade distribution: {dict(sorted(grade_dist.items()))}")

# %% [markdown]
# ## End of Demo Notebook
#
# For the full project report, see `report/final_report.md`.
