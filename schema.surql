-- ============================================================
-- schema.surql
-- SurrealDB multimodal schema for CS401 Advanced Database Systems
-- ============================================================
-- Run with:
--   surreal import --conn http://localhost:8000 \
--                  --user root --pass root \
--                  --ns education --db cs401 \
--                  schema.surql
-- ============================================================


-- ── Namespace & Database ──────────────────────────────────────
DEFINE NAMESPACE education;
DEFINE DATABASE cs401;

USE NS education DB cs401;

DEFINE ANALYZER ascii TOKENIZERS blank,class FILTERS lowercase,ascii;

-- ── TABLE: lecture ────────────────────────────────────────────
-- Stores parsed PDF lecture notes.
DEFINE TABLE lecture SCHEMAFULL;

DEFINE FIELD id          ON lecture TYPE string;
DEFINE FIELD title       ON lecture TYPE string;
DEFINE FIELD source      ON lecture TYPE string;
DEFINE FIELD filename    ON lecture TYPE string;
DEFINE FIELD page_count  ON lecture TYPE int;
DEFINE FIELD content     ON lecture TYPE string;
DEFINE FIELD topics      ON lecture TYPE array;
DEFINE FIELD created_at  ON lecture TYPE datetime VALUE time::now();

-- Full-text search index on content
DEFINE INDEX lecture_content_idx ON lecture FIELDS content SEARCH ANALYZER ascii BM25;
DEFINE INDEX lecture_title_idx   ON lecture FIELDS title   UNIQUE;


-- ── TABLE: assignment ─────────────────────────────────────────
-- Stores parsed TXT assignment files.
DEFINE TABLE assignment SCHEMAFULL;

DEFINE FIELD id          ON assignment TYPE string;
DEFINE FIELD title       ON assignment TYPE string;
DEFINE FIELD source      ON assignment TYPE string;
DEFINE FIELD filename    ON assignment TYPE string;
DEFINE FIELD content     ON assignment TYPE string;
DEFINE FIELD word_count  ON assignment TYPE int;
DEFINE FIELD concepts    ON assignment TYPE array;
DEFINE FIELD due_date    ON assignment TYPE string;
DEFINE FIELD created_at  ON assignment TYPE datetime VALUE time::now();

DEFINE INDEX assignment_content_idx ON assignment FIELDS content SEARCH ANALYZER ascii BM25;
DEFINE INDEX assignment_title_idx   ON assignment FIELDS title   UNIQUE;


-- ── TABLE: student_score ──────────────────────────────────────
-- Stores individual student score rows from CSV.
DEFINE TABLE student_score SCHEMAFULL;

DEFINE FIELD id           ON student_score TYPE string;
DEFINE FIELD student_id   ON student_score TYPE string;
DEFINE FIELD name         ON student_score TYPE string;
DEFINE FIELD assignment_1 ON student_score TYPE float;
DEFINE FIELD assignment_2 ON student_score TYPE float;
DEFINE FIELD midterm      ON student_score TYPE float;
DEFINE FIELD final        ON student_score TYPE float;
DEFINE FIELD grade        ON student_score TYPE string;
DEFINE FIELD source       ON student_score TYPE string;
DEFINE FIELD created_at   ON student_score TYPE datetime VALUE time::now();

DEFINE INDEX student_id_idx ON student_score FIELDS student_id UNIQUE;


-- ── TABLE: metadata ───────────────────────────────────────────
-- Stores parsed JSON metadata documents (flexible / document-style).
DEFINE TABLE metadata SCHEMALESS;  -- flexible to accommodate varied metadata shapes

DEFINE FIELD id          ON metadata TYPE string;
DEFINE FIELD source      ON metadata TYPE string;
DEFINE FIELD filename    ON metadata TYPE string;
DEFINE FIELD course_id   ON metadata TYPE string;
DEFINE FIELD valid       ON metadata TYPE bool;
DEFINE FIELD warnings    ON metadata TYPE array;
DEFINE FIELD created_at  ON metadata TYPE datetime VALUE time::now();
-- `data` field is intentionally schemaless (flexible nested document)


-- ── TABLE: image ──────────────────────────────────────────────
-- Stores image file metadata.
DEFINE TABLE image SCHEMAFULL;

DEFINE FIELD id               ON image TYPE string;
DEFINE FIELD source           ON image TYPE string;
DEFINE FIELD filename         ON image TYPE string;
DEFINE FIELD format           ON image TYPE string;
DEFINE FIELD file_size_bytes  ON image TYPE int;
DEFINE FIELD width            ON image TYPE option<int>;
DEFINE FIELD height           ON image TYPE option<int>;
DEFINE FIELD mode             ON image TYPE option<string>;
DEFINE FIELD created_at       ON image TYPE datetime VALUE time::now();


-- ── GRAPH EDGES ───────────────────────────────────────────────

-- lecture -[covers]-> concept
-- Connects lecture records to the abstract topics/concepts they cover.
DEFINE TABLE covers SCHEMAFULL TYPE RELATION IN lecture OUT concept;
DEFINE FIELD weight  ON covers TYPE float DEFAULT 1.0;   -- optional relevance weight
DEFINE FIELD created_at ON covers TYPE datetime VALUE time::now();

-- assignment -[requires]-> concept
-- Connects assignments to the prerequisite concepts they test.
DEFINE TABLE requires SCHEMAFULL TYPE RELATION IN assignment OUT concept;
DEFINE FIELD created_at ON requires TYPE datetime VALUE time::now();

-- metadata -[describes]-> lecture | assignment | image
-- Connects metadata records to the materials they describe.
DEFINE TABLE describes SCHEMAFULL TYPE RELATION;
DEFINE FIELD created_at ON describes TYPE datetime VALUE time::now();

-- student_score -[submitted_for]-> assignment
-- Links a student's score record to the corresponding assignment.
DEFINE TABLE submitted_for SCHEMAFULL TYPE RELATION IN student_score OUT assignment;
DEFINE FIELD created_at ON submitted_for TYPE datetime VALUE time::now();


-- ── TABLE: concept ────────────────────────────────────────────
-- Abstract nodes used in graph traversals.
DEFINE TABLE concept SCHEMAFULL;

DEFINE FIELD id          ON concept TYPE string;
DEFINE FIELD name        ON concept TYPE string;
DEFINE FIELD description ON concept TYPE option<string>;
DEFINE FIELD created_at  ON concept TYPE datetime VALUE time::now();

DEFINE INDEX concept_name_idx ON concept FIELDS name UNIQUE;
