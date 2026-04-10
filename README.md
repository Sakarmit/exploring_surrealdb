
---

## Quick Start

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Start SurrealDB (in-memory for development)
```bash
surreal start --user root --pass root memory
```

### 3. Apply the schema
```bash
surreal import --conn http://localhost:8000 \
               --user root --pass root \
               --ns education --db learning_management_db \
               schema.surql
```

### 4. Run ingestion
```bash
# Dry run (no DB required — just parses and prints)
python -m ingestion.ingest --dry-run

# Full ingestion via HTTP REST
python -m ingestion.ingest --http

# Full ingestion via Python SDK
python -m ingestion.ingest
```

### 5. Run queries
```bash
# Run all 7 queries
python -m queries.run_queries --http

# Run a specific query (e.g. query 4 — graph traversal)
python -m queries.run_queries --http --query 4
```

### 6. Open demo notebook
```bash
# Convert .py notebook to .ipynb, then launch Jupyter
pip install jupytext jupyter
jupytext --to notebook notebooks/demo_notebook.py
jupyter notebook notebooks/demo_notebook.ipynb
```

---

## Project Structure

```
surrealdb_project/
├── dataset/
│   ├── text/
│   │   ├── lecture_notes.pdf     ← Place your PDF here
│   │   └── assignment.txt        ← Sample assignment (provided)
│   ├── tables/
│   │   └── student_scores.csv    ← 10-student score dataset (provided)
│   ├── metadata/
│   │   └── metadata.json         ← Course metadata (provided)
│   └── images/
│       └── sample_plot.png       ← Place your image here
│
├── parsers/
│   ├── __init__.py
│   ├── pdf_parser.py             ← PDF text + metadata extraction
│   ├── txt_parser.py             ← Full text + heuristic field extraction
│   ├── csv_parser.py             ← CSV → list of JSON records
│   ├── json_parser.py            ← JSON load + validation
│   └── image_parser.py           ← File size + pixel dimensions
│
├── ingestion/
│   ├── __init__.py
│   ├── surreal_client.py         ← SDK + HTTP REST client wrapper
│   └── ingest.py                 ← Full pipeline: parse → connect → insert → graph
│
├── queries/
│   ├── queries.surql             ← All SurrealQL queries (raw)
│   └── run_queries.py            ← Python runner with pretty output
│
├── notebooks/
│   └── demo_notebook.py          ← Jupytext-format demo notebook
│
├── report/
│   └── final_report.md           ← 4–6 page final report
│
├── schema.surql                  ← Full SurrealDB schema definition
├── requirements.txt
└── README.md
```

---

## Dataset Files

| File | Modality | Parser | SurrealDB Table |
|------|----------|--------|-----------------|
| `lecture_notes.pdf` | PDF | `pdf_parser.py` | `lecture` |
| `assignment.txt` | Text | `txt_parser.py` | `assignment` |
| `student_scores.csv` | Table | `csv_parser.py` | `student_score` |
| `metadata.json` | JSON | `json_parser.py` | `metadata` |
| `images/*.png` | Image | `image_parser.py` | `image` |

> **Note:** A `lecture_notes.pdf` placeholder is not included — place any PDF in `dataset/text/` and rename it, or create a simple one. All other files are provided.

---

## Schema Overview

```
┌─────────────┐    covers     ┌─────────────┐    requires   ┌──────────────┐
│   lecture   │──────────────►│   concept   │◄──────────────│  assignment  │
└─────────────┘               └─────────────┘               └──────────────┘
       │                                                             ▲
       │                                                             │
       │           ┌─────────────┐    describes                     │
       └───────────│  metadata   │──────────────────────────────────┘
                   └─────────────┘
                         │ describes
                         ▼
                   ┌─────────────┐
                   │    image    │
                   └─────────────┘

┌───────────────┐   submitted_for   ┌──────────────┐
│ student_score │──────────────────►│  assignment  │
└───────────────┘                   └──────────────┘
```

---

## Queries

| # | Type | Description |
|---|------|-------------|
| 1 | Full-text search | BM25 keyword search across lectures + assignments |
| 2 | Relational join | Student scores with computed averages |
| 3 | Cross-modal join | Lecture content linked to metadata topics |
| 4 | Graph traversal | Concepts shared between lectures and assignments |
| 5 | Aggregation | Grade distribution summary |
| 6 | Graph traversal | Materials described by metadata |
| 7 | Filter | At-risk students (final < 75) |

---

## SurrealDB Connection Defaults

| Setting | Value |
|---------|-------|
| URL | `http://localhost:8000` |
| User | `root` |
| Password | `root` |
| Namespace | `education` |
| Database | `learning_management_db` |

Override via environment variables or by editing `ingestion/surreal_client.py`.

---

## PDF Library Support

The PDF parser auto-detects available libraries in priority order:

1. **PyMuPDF** (`pip install PyMuPDF`) — recommended, fastest
2. **pdfplumber** (`pip install pdfplumber`) — good layout extraction
3. **pypdf** (`pip install pypdf`) — lightweight
4. **Fallback** — stores file path + size only (no text extraction)

---

## Week-by-Week Progress

| Week | Goals | Key Files |
|------|-------|-----------|
| 1 | Dataset exploration, schema proposal | `schema.surql`, parsers (read-only tests) |
| 2 | Parsers + ingestion | `parsers/`, `ingestion/ingest.py` |
| 3 | Queries + graph relationships | `queries/queries.surql`, `run_queries.py` |
| 4 | Integration, demo, report | `notebooks/demo_notebook.py`, `report/final_report.md` |
