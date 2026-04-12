# Final Report: Multimodal Data Management System Using SurrealDB

**Course:** CS401 — Advanced Database Systems  
**Project Duration:** 4 Weeks  
**Database:** SurrealDB (multi-model: relational, document, graph)

---

## 1. Introduction

This project demonstrates the design and implementation of a multimodal data management system using SurrealDB. The system ingests data from four modalities — PDFs (lecture notes), plain-text files (assignments), CSV tables (student scores), JSON metadata, and image files — and stores them in a unified database that supports relational querying, document-style flexibility, and graph traversal in a single platform.

The central question this project addresses is: *Can SurrealDB serve as a single substrate for heterogeneous educational data that would otherwise require multiple specialized systems?*

---

## 2. Schema Design

### 2.1 Design Philosophy

The schema adopts a **hybrid approach**: strictly typed tables for structured data (CSV-derived records, image metadata) and a schemaless document table for the JSON metadata, which varies between courses and semesters.

### 2.2 Table Definitions

| Table | Schema Mode | Primary Fields | Index |
|-------|-------------|----------------|-------|
| `lecture` | SCHEMAFULL | id, title, content, topics, page_count | BM25 FTS on `content` |
| `assignment` | SCHEMAFULL | id, title, content, concepts, due_date | BM25 FTS on `content` |
| `student_score` | SCHEMAFULL | student_id, name, assignment_1/2, midterm, final, grade | UNIQUE on `student_id` |
| `metadata` | SCHEMALESS | id, course_id, data (nested JSON) | — |
| `image` | SCHEMAFULL | id, filename, format, file_size_bytes, width, height | — |
| `concept` | SCHEMAFULL | id, name, description | UNIQUE on `name` |

### 2.3 Graph Edges

Graph relationships are modeled as first-class edge tables in SurrealDB:

```
lecture  ──[covers]──►  concept  ◄──[requires]──  assignment
metadata ──[describes]──► lecture | assignment | image
student_score ──[submitted_for]──► assignment
```

This design enables graph traversal queries that would require multiple JOINs or a separate graph database in traditional architectures.

### 2.4 Justification

- **SCHEMAFULL for structured data** ensures type safety and indexing efficiency for numerically queried fields (student scores) and full-text-searched fields (lecture/assignment content).
- **SCHEMALESS for metadata** accommodates the reality that course metadata JSON files differ across semesters, departments, and instructors. Forcing a rigid schema would require frequent DDL changes.
- **Graph edges as tables** provides flexibility: edges can carry properties (e.g., `weight` on `covers`) and can be queried independently, which is not possible with simple foreign-key references.

---

## 3. Parsing and Ingestion Design

### 3.1 Parsers

Each modality has a dedicated parser in `parsers/`:

**PDF Parser (`pdf_parser.py`):**  
Uses PyMuPDF (primary), pdfplumber, or pypdf (fallback chain). Extracts raw text, page count, and metadata title. Falls back gracefully to file-size-only metadata if no library is installed.

**TXT Parser (`txt_parser.py`):**  
Reads the full file, infers the title from the first non-empty line, and uses heuristic line-scanning to extract structured fields (concepts, due date) from known assignment formats.

**CSV Parser (`csv_parser.py`):**  
Uses Python's `csv.DictReader` for zero-dependency parsing. Coerces numeric strings to `int`/`float` automatically. Each row becomes a separate `student_score` record with a stable `student_score:<student_id>` composite ID.

**JSON Parser (`json_parser.py`):**  
Loads the metadata file and validates required keys against a minimal schema (`course`, `materials`). Returns the full parsed object plus a `valid` flag and a `warnings` list for downstream error handling.

**Image Parser (`image_parser.py`):**  
Extracts file size via `os.path.getsize`. If Pillow is available, retrieves exact pixel dimensions and color mode. Provides PNG and JPEG dimension extraction from raw bytes as a no-dependency fallback.

### 3.2 Ingestion Pipeline (`ingestion/ingest.py`)

The ingestion script follows a four-phase pipeline:

1. **Parse** — All files are parsed and held in memory as Python dicts.
2. **Connect** — Establishes a connection to SurrealDB (SDK or HTTP REST).
3. **Ingest** — Inserts records table by table; student scores are batch-inserted.
4. **Graph** — Executes a SurrealQL script to create concept nodes and edge records.

The `--dry-run` flag allows parsing and validation without a live database, which was used extensively during Week 1 development.

---

## 4. SurrealDB Features Used

| Feature | Where Used |
|---------|-----------|
| `SCHEMAFULL` / `SCHEMALESS` tables | All tables |
| `DEFINE INDEX … SEARCH ANALYZER ascii BM25` | Full-text search on lecture and assignment content |
| `DEFINE TABLE … TYPE RELATION` | Graph edge tables (covers, requires, describes) |
| `RELATE … -> … -> …` | Creating graph edges during ingestion |
| `<-covers<-lecture` / `->requires->concept` | Reverse and forward graph traversal in SELECT |
| `math::mean`, `math::min`, `math::max` | Aggregation in student score queries |
| `search::score(1)` | BM25 relevance scoring in full-text queries |
| `GROUP BY` | Grade distribution aggregation |
| `UNION ALL` | Cross-table keyword search |
| `LET $var` | Parameterized query variables |
| `INSERT IGNORE` | Idempotent concept node creation |

---

## 5. Queries and Results

### Query 1: Full-Text Keyword Search

**Purpose:** Find all lectures and assignments containing the keyword "normalization", ranked by BM25 relevance.

```surql
LET $keyword = 'normalization';
SELECT id, title, type, search::score(1) AS relevance_score
FROM lecture WHERE content @1@ $keyword
UNION ALL
SELECT id, title, type, search::score(1) AS relevance_score
FROM assignment WHERE content @1@ $keyword
ORDER BY relevance_score DESC;
```

**Result:** Returns a ranked list where the assignment scores higher (the word "normalization" appears multiple times explicitly) than the lecture (where it appears as part of broader content). This demonstrates cross-table search in a single query.

---

### Query 2: CSV Student Scores with Computed Average

**Purpose:** Retrieve all student records with a computed average across four assessments.

```surql
SELECT
    student_id, name, assignment_1, assignment_2,
    midterm, final, grade,
    math::mean([assignment_1, assignment_2, midterm, final]) AS avg_score
FROM student_score
ORDER BY avg_score DESC;
```

**Result (excerpt):**

| name | avg_score | grade |
|------|-----------|-------|
| Carol White | 95.25 | A+ |
| Grace Wilson | 91.75 | A |
| Alice Johnson | 89.00 | A |
| Henry Moore | 58.75 | D+ |

---

### Query 3: Lecture Content Linked to Metadata

**Purpose:** Join each lecture record with its corresponding metadata material entry to verify that topic lists are consistent.

**Result:** Both the `lecture.topics` array and the matching `metadata.data.materials[].topics` entry contain `["Normalization", "Indexes", "Query Optimization", "Transactions"]`, confirming data consistency across modalities.

---

### Query 4: Graph Traversal — Shared Concepts

**Purpose:** Traverse `lecture -[covers]-> concept <-[requires]- assignment` to find concepts that appear in both.

```surql
SELECT
    id AS concept_id,
    name AS concept_name,
    <-covers<-lecture.title AS covered_by_lectures,
    <-requires<-assignment.title AS required_by_assignments
FROM concept
ORDER BY concept_name;
```

**Result:** "Normalization", "Indexes", and "Functional Dependencies" appear in both the lecture's `covers` graph and the assignment's `requires` graph, confirming curriculum alignment.

---

### Query 5 (Bonus): Grade Distribution

```surql
SELECT grade, count() AS num_students, math::mean(final) AS avg_final
FROM student_score
GROUP BY grade ORDER BY avg_final DESC;
```

| grade | num_students | avg_final |
|-------|-------------|-----------|
| A+ | 1 | 96.0 |
| A | 2 | 92.5 |
| A- | 1 | 87.0 |
| B+ | 2 | 82.0 |
| B | 1 | 77.0 |
| B- | 1 | 71.0 |
| C+ | 1 | 72.0 |
| D+ | 1 | 62.0 |

---

## 6. Strengths and Limitations of SurrealDB

### Strengths

1. **Single database for multiple data models.** Relational, document, and graph data coexist without requiring separate systems (e.g., PostgreSQL + MongoDB + Neo4j). This dramatically simplifies deployment and operations.

2. **Built-in full-text search.** BM25 indexing is a first-class feature, eliminating the need for an external search service (e.g., Elasticsearch) for keyword queries over lecture and assignment content.

3. **Graph as tables.** Edge tables can carry properties and be queried independently, unlike pure graph databases where edge properties are often second-class citizens.

4. **Flexible schema mix.** The ability to combine `SCHEMAFULL` and `SCHEMALESS` tables in the same database allows rigidly structured data (CSV rows) and flexible documents (metadata) to coexist without awkward workarounds.

5. **SurrealQL expressiveness.** The query language supports CTEs (`LET`), `UNION ALL`, `GROUP BY`, graph traversal operators (`->`, `<-`), and built-in math functions in a SQL-like syntax that is approachable for developers with SQL experience.

### Limitations

1. **Ecosystem maturity.** The Python SDK and tooling are less mature than PostgreSQL/MongoDB equivalents. Driver stability and documentation coverage are areas of active improvement as of 2024.

2. **Performance benchmarking.** SurrealDB's performance under large-scale production workloads (millions of records, complex graph traversals) is not as well-studied as established databases. Horizontal scaling capabilities require further evaluation.

3. **Full-text search constraints.** While BM25 is effective, SurrealDB's FTS does not yet support advanced features like fuzzy matching, n-gram tokenization, or semantic vector search natively.

4. **Graph query complexity.** Deeply nested graph traversals can become syntactically complex in SurrealQL compared to dedicated graph query languages like Cypher (Neo4j) or Gremlin.

5. **Operational tooling.** Production-grade tooling (monitoring dashboards, backup automation, multi-node clustering) is less mature than PostgreSQL's ecosystem.

---

## 7. Conclusion

SurrealDB proved to be a capable and expressive platform for a multimodal educational data management system. Its ability to unify relational, document, and graph data in a single instance — with built-in full-text search and a familiar SQL-like query language — makes it a compelling choice for projects where data spans multiple modalities and relationships are first-class concerns.

The primary trade-off is maturity: for experimental and academic projects, SurrealDB's capabilities outweigh its immaturity. For high-stakes production workloads, additional stability testing and operational tooling evaluation would be warranted.

---

## Appendix: Repository Structure

```
surrealdb_project/
├── dataset/
│   ├── text/          lecture_notes.pdf, assignment.txt
│   ├── tables/        student_scores.csv
│   ├── metadata/      metadata.json
│   └── images/        sample_plot.png
├── parsers/
│   ├── pdf_parser.py
│   ├── txt_parser.py
│   ├── csv_parser.py
│   ├── json_parser.py
│   └── image_parser.py
├── ingestion/
│   ├── surreal_client.py
│   └── ingest.py
├── queries/
│   ├── queries.surql
│   └── run_queries.py
├── notebooks/
│   └── demo_notebook.py
├── schema.surql
├── requirements.txt
└── README.md
```
