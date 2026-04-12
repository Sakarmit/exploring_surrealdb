-- ============================================================
-- schema.surql
-- ============================================================
-- Run with:
--   surreal import --conn http://localhost:8000 \
--                  --user root --pass root \
--                  --ns education --db learning_management_db \
--                  schema.surql
-- ============================================================


-- ── Namespace & Database ──────────────────────────────────────
DEFINE NAMESPACE education;
DEFINE DATABASE learning_management_db;

USE NS education DB learning_management_db;

DEFINE ANALYZER text_analyzer TOKENIZERS blank,class FILTERS lowercase;

-- ── TABLE: subject ────────────────────────────────────────────
DEFINE TABLE subject SCHEMAFULL;
DEFINE FIELD id          ON subject TYPE string;
DEFINE FIELD domain      ON subject TYPE string;
DEFINE FIELD subdomain   ON subject TYPE string;

DEFINE INDEX domain_subdomain_idx ON subject FIELDS domain, subdomain UNIQUE;

-- ── TABLE: topic ────────────────────────────────────────────
DEFINE TABLE topic SCHEMAFULL;
DEFINE FIELD id          ON topic TYPE string;
DEFINE FIELD name        ON topic TYPE string;
DEFINE FIELD description ON topic TYPE string;

DEFINE INDEX topic_name_idx ON topic FIELDS name UNIQUE;

-- ── TABLE: tool ────────────────────────────────────────────
DEFINE TABLE tool SCHEMAFULL;
DEFINE FIELD id          ON tools TYPE string;
DEFINE FIELD name        ON tools TYPE string;

DEFINE INDEX tool_name_idx ON tool FIELDS name UNIQUE;

-- ── TABLE: objective ────────────────────────────────────────────
DEFINE TABLE objective SCHEMAFULL;
DEFINE FIELD id          ON objective TYPE string;
DEFINE FIELD name        ON objective TYPE string;

DEFINE INDEX objective_name_idx ON objective FIELDS name UNIQUE;

-- ── TABLE: language ────────────────────────────────────────────
DEFINE TABLE language SCHEMAFULL;
DEFINE FIELD id          ON language TYPE string;
DEFINE FIELD shorthand   ON language TYPE string;

DEFINE INDEX language_name_idx ON language FIELDS shorthand UNIQUE;

-- ── TABLE: lecture ────────────────────────────────────────────
DEFINE TABLE lecture SCHEMAFULL;
DEFINE FIELD id          ON lecture TYPE string;
DEFINE FIELD title       ON lecture TYPE string;
DEFINE FIELD source      ON lecture TYPE string;
DEFINE FIELD page_count  ON lecture TYPE option<int>;
DEFINE FIELD content     ON lecture TYPE string;
-- DEFINE FIELD created_at  ON lecture TYPE datetime VALUE time::now();

-- Full-text search index on content
DEFINE INDEX lecture_content_idx ON lecture FIELDS content SEARCH ANALYZER text_analyzer BM25;
DEFINE INDEX lecture_title_idx   ON lecture FIELDS title   UNIQUE;

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
-- DEFINE FIELD created_at       ON image TYPE datetime VALUE time::now();

-- ── TABLE: video ──────────────────────────────────────────────
DEFINE TABLE video SCHEMAFULL;
DEFINE FIELD id               ON video TYPE string;
DEFINE FIELD source           ON video TYPE string;
DEFINE FIELD filename         ON video TYPE string;
DEFINE FIELD format           ON video TYPE string;
DEFINE FIELD file_size_bytes  ON video TYPE int;
DEFINE FIELD resolution       ON video TYPE option<int>;

-- ── TABLE: metadata ───────────────────────────────────────────
-- Stores parsed JSON metadata documents (flexible / document-style).
DEFINE TABLE metadata SCHEMALESS;  -- flexible to accommodate varied metadata shapes
DEFINE FIELD id          ON metadata TYPE string;
DEFINE FIELD source      ON metadata TYPE string;
DEFINE FIELD filename    ON metadata TYPE string;
DEFINE FIELD course_id   ON metadata TYPE string;
DEFINE FIELD valid       ON metadata TYPE bool;
DEFINE FIELD warnings    ON metadata TYPE array;
-- DEFINE FIELD created_at  ON metadata TYPE datetime VALUE time::now();
-- `data` field is intentionally schemaless (flexible nested document)

-- ── TABLE: course ───────────────────────────────────────────
DEFINE TABLE course SCHEMAFULL;
DEFINE FIELD id          ON course TYPE string;
DEFINE FIELD name        ON course TYPE string;
DEFINE FIELD description ON course TYPE string;
DEFINE FIELD url         ON course TYPE option<string>;
DEFINE FIELD partner     ON course TYPE option<string>;
DEFINE FIELD difficulty  ON course TYPE option<string>;
DEFINE FIELD rating      ON course TYPE option<int>;
DEFINE FIELD num_rating  ON course TYPE option<int>;
DEFINE FIELD hours       ON course TYPE option<hours>;
DEFINE FIELD certificate      ON course TYPE bool;
DEFINE FIELD weeks       ON course TYPE int;

DEFINE INDEX course_description_idx ON course FIELDS description SEARCH ANALYZER text_analyzer BM25;

-- ── TABLE: instructor ─────────────────────────────────────────
DEFINE TABLE instructor SCHEMAFULL;
DEFINE FIELD id          ON instructor TYPE string;
DEFINE FIELD title       ON instructor TYPE string;
DEFINE FIELD bio         ON instructor TYPE string;

DEFINE INDEX instructor_bio_idx ON instructor FIELDS bio SEARCH ANALYZER text_analyzer BM25;

-- ── TABLE: module ─────────────────────────────────────────
DEFINE TABLE module SCHEMALESS;
DEFINE FIELD id          ON module TYPE string;
DEFINE FIELD description ON module TYPE string;

-- ── TABLE: student ─────────────────────────────────────────
DEFINE TABLE student SCHEMALESS;
DEFINE FIELD id          ON student TYPE string;
DEFINE FIELD name        ON student TYPE string;
DEFINE FIELD email       ON student TYPE string;
DEFINE FIELD major       ON student TYPE string;

-- ── TABLE: student_grade ─────────────────────────────────────────
DEFINE TABLE student_grade SCHEMALESS;
DEFINE FIELD id          ON student_grade TYPE string;
DEFINE FIELD name        ON student_grade TYPE string;
DEFINE FIELD grade       ON student_grade TYPE decimal VALUE math::fixed($value, 2);

-- ── TABLE: assignment ─────────────────────────────────────────
-- Stores parsed TXT assignment files.
DEFINE TABLE assignment SCHEMAFULL;
DEFINE FIELD id          ON assignment TYPE string;
DEFINE FIELD title       ON assignment TYPE string;
DEFINE FIELD source      ON assignment TYPE string;
DEFINE FIELD filename    ON assignment TYPE string;
DEFINE FIELD content     ON assignment TYPE string;
DEFINE FIELD word_count  ON assignment TYPE int;
DEFINE FIELD due_date    ON assignment TYPE string;
-- DEFINE FIELD created_at  ON assignment TYPE datetime VALUE time::now();

DEFINE INDEX assignment_content_idx ON assignment FIELDS content SEARCH ANALYZER text_analyzer BM25;
DEFINE INDEX assignment_title_idx   ON assignment FIELDS title   UNIQUE;

-- ── TABLE: exam ─────────────────────────────────────────
DEFINE TABLE exam SCHEMAFULL;
DEFINE FIELD id          ON exam TYPE string;
DEFINE FIELD questions   ON exam TYPE object;  -- flexible field to store varied question formats

-- ── TABLE: annoucement ─────────────────────────────────────────
DEFINE TABLE annoucement SCHEMAFULL;
DEFINE FIELD id          ON annoucement TYPE string;
DEFINE FIELD title       ON annoucement TYPE string;
DEFINE FIELD content     ON annoucement TYPE string;
DEFINE FIELD course      ON announcement TYPE record<course>;

DEFINE INDEX annoucement_title_idx ON annoucement FIELDS title SEARCH ANALYZER text_analyzer BM25;
DEFINE INDEX annoucement_content_idx ON annoucement FIELDS content SEARCH ANALYZER text_analyzer BM25;

-- ── TABLE: discussion ─────────────────────────────────────────
DEFINE TABLE discussion SCHEMAFULL;
DEFINE FIELD id          ON discussion TYPE string;
DEFINE FIELD title       ON discussion TYPE string;
DEFINE FIELD message     ON discussion TYPE string;
DEFINE FIELD course      ON discussion   TYPE record<course>;

DEFINE INDEX discussion_title_idx ON discussion FIELDS title SEARCH ANALYZER text_analyzer BM25;
DEFINE INDEX discussion_message_idx ON discussion FIELDS message SEARCH ANALYZER text_analyzer BM25;

-- ── TABLE: student_score ──────────────────────────────────────
-- Stores individual student score rows from CSV.
/*DEFINE TABLE student_score SCHEMAFULL;

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

DEFINE INDEX student_id_idx ON student_score FIELDS student_id UNIQUE;*/

-- ── GRAPH EDGES ───────────────────────────────────────────────

DEFINE TABLE covers SCHEMAFULL TYPE RELATION IN lecture OUT topic;
DEFINE TABLE requires SCHEMAFULL TYPE RELATION IN assignment OUT topic;

DEFINE TABLE describes SCHEMAFULL TYPE RELATION;

DEFINE TABLE belongs_to SCHEMAFULL TYPE RELATION IN course OUT subject;
DEFINE TABLE covers SCHEMAFULL TYPE RELATION IN course OUT topic;
DEFINE TABLE uses SCHEMAFULL TYPE RELATION IN course OUT tool;
DEFINE TABLE targets SCHEMAFULL TYPE RELATION IN course OUT objective;
DEFINE TABLE taught_in SCHEMAFULL TYPE RELATION IN course OUT language;
DEFINE TABLE taught_by SCHEMAFULL TYPE RELATION IN course OUT instructor;
DEFINE TABLE contains SCHEMAFULL TYPE RELATION IN course OUT module;
DEFINE TABLE requires SCHEMAFULL TYPE RELATION IN course OUT assignment;
DEFINE TABLE includes SCHEMAFULL TYPE RELATION IN course OUT lecture;


DEFINE TABLE assignment_grade SCHEMAFULL TYPE RELATION IN student_score OUT assignment;
DEFINE TABLE exam_grade SCHEMAFULL TYPE RELATION IN student_score OUT exam;
DEFINE TABLE student_enrolled_in SCHEMAFULL TYPE RELATION IN student OUT course;