
---

## Quick Start

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Start SurrealDB (in-memory for development)
```bash
# Requires subrealdb version = 3.0.5 to be installed externally
surreal start --user root --pass root memory
```

### 3. Apply the schema
```bash
surreal import --conn http://localhost:8000 \
               --user root --pass root \
               --ns education --db learning_management_db \
               schema.surql
```

```bash
surreal import --endpoint http://localhost:8000 \
      --user root --pass root \
      --namespace education --database learning_management_db \
      schema.surql
```

### 4. Run ingestion
<!-- # Dry run (no DB required — just parses and prints)
python -m ingestion.ingest --dry-run 
-->
```bash
# Full ingestion via HTTP REST
python -m ingestion.ingest --http
```
<!-- 
# Full ingestion via Python SDK
python -m ingestion.ingest
 -->

### 5. Run queries
```bash
streamlit run ./queries/run_queries_interface.py
```
<!-- # Run all 7 queries
python -m queries.run_queries --http

# Run a specific query (e.g. query 4 — graph traversal)
python -m queries.run_queries --http --query 4 -->

### OR Open demo notebook
```bash
pip install jupytext jupyter
jupyter notebook notebooks/demo_queries.ipynb
```

---

## Project Structure

```
surrealdb_project/
├── dataset/
|   ├── code_workout_data
|   |   └── (all files in downloaded dataset)
(provided in repo)
|   ├── knowledge_graph
|   |   └── cs_dataset.csv
│   ├── text/
│   │   ├── lecture_notes.pdf     ← Place your PDF here
│   │   └── assignment.txt        ← Sample assignment 
│   ├── tables/
│   │   └── student_scores.csv    ← 10-student score dataset 
│   ├── metadata/
│   │   └── metadata.json         ← Course metadata
│   └── images/
│       └── sample_plot.png       ← Place your image here
│
├── parsers/
│   ├── __init__.py
│   ├── code_workout_parsers.py   ← Code workout dataset extraction
│   ├── kg_parser.py              ← Coursera dataset extraction
│   ├── video_parser.py           ← File duration + dimensions etc
│   ├── work_parser.py            ← File size + context etc
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
│   ├── run_queries_interface     ← Streamlit interface for code workout queries
│   └── run_queries.py            ← Python runner with pretty output
│
├── notebooks/
│   ├── demo_notebook.py          ← Jupytext-format demo notebook
|   ├── demo_queries.ipynb        ← Code workout query tests
│
├── report/
│   └── final_report.md           ← Concluding info
│
├── schema.surql                  ← Full SurrealDB schema definition
├── requirements.txt
└── README.md
```
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
