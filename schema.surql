OPTION IMPORT;

-- ============================================================
-- Namespace & Database
-- ============================================================

DEFINE NAMESPACE education;
DEFINE DATABASE learning_management_db;

USE NS education DB learning_management_db;

DEFINE ANALYZER text_analyzer TOKENIZERS blank,class FILTERS lowercase;

-- ============================================================
-- TABLE: subject
-- ============================================================

DEFINE TABLE subject SCHEMAFULL;
DEFINE FIELD id        ON subject TYPE string;
DEFINE FIELD domain    ON subject TYPE string;
DEFINE FIELD subdomain ON subject TYPE string;

DEFINE INDEX domain_subdomain_idx ON subject FIELDS domain, subdomain UNIQUE;

-- ============================================================
-- TABLE: topic
-- ============================================================

DEFINE TABLE topic SCHEMAFULL;
DEFINE FIELD id          ON topic TYPE string;
DEFINE FIELD name        ON topic TYPE string;
DEFINE FIELD description ON topic TYPE option<string>;

DEFINE INDEX topic_name_idx ON topic FIELDS name UNIQUE;

-- ============================================================
-- TABLE: tool
-- ============================================================

DEFINE TABLE tool SCHEMAFULL;
DEFINE FIELD id   ON tool TYPE string;
DEFINE FIELD name ON tool TYPE string;

DEFINE INDEX tool_name_idx ON tool FIELDS name UNIQUE;

-- ============================================================
-- TABLE: language
-- ============================================================

DEFINE TABLE language SCHEMAFULL;
DEFINE FIELD id        ON language TYPE string;
DEFINE FIELD shorthand ON language TYPE string;

DEFINE INDEX language_name_idx ON language FIELDS shorthand UNIQUE;

-- ============================================================
-- TABLE: lecture
-- ============================================================

DEFINE TABLE lecture SCHEMAFULL;
DEFINE FIELD id         ON lecture TYPE string;
DEFINE FIELD type       ON lecture TYPE string;
DEFINE FIELD title      ON lecture TYPE string;
DEFINE FIELD source     ON lecture TYPE string;
DEFINE FIELD page_count ON lecture TYPE option<int>;
DEFINE FIELD content    ON lecture TYPE option<string>;
DEFINE FIELD topics     ON lecture TYPE option<array>;

DEFINE INDEX lecture_content_idx ON lecture FIELDS content;
DEFINE INDEX lecture_title_idx   ON lecture FIELDS title UNIQUE;

-- ============================================================
-- TABLE: image
-- ============================================================

DEFINE TABLE image SCHEMAFULL;
DEFINE FIELD id              ON image TYPE string;
DEFINE FIELD name            ON image TYPE string;
DEFINE FIELD type            ON image TYPE string;
DEFINE FIELD source          ON image TYPE string;
DEFINE FIELD format          ON image TYPE string;
DEFINE FIELD file_size_bytes ON image TYPE int;
DEFINE FIELD width           ON image TYPE option<int>;
DEFINE FIELD height          ON image TYPE option<int>;
DEFINE FIELD mode            ON image TYPE option<string>;

-- ============================================================
-- TABLE: video
-- ============================================================

DEFINE TABLE video SCHEMAFULL;
DEFINE FIELD id              ON video TYPE string;
DEFINE FIELD name            ON video TYPE string;
DEFINE FIELD source          ON video TYPE string;
DEFINE FIELD format          ON video TYPE option<string>;
DEFINE FIELD file_size_bytes ON video TYPE option<int>;
DEFINE FIELD resolution      ON video TYPE option<int>;

-- ============================================================
-- TABLE: metadata (schemaless for flexibility)
-- ============================================================

DEFINE TABLE metadata SCHEMALESS;
DEFINE FIELD id        ON metadata TYPE string;
DEFINE FIELD source    ON metadata TYPE string;
DEFINE FIELD course_id ON metadata TYPE string;
DEFINE FIELD valid     ON metadata TYPE bool;
DEFINE FIELD warnings  ON metadata TYPE array;
DEFINE FIELD data      ON metadata TYPE object;

-- ============================================================
-- TABLE: course
-- ============================================================

DEFINE TABLE course SCHEMAFULL;
DEFINE FIELD id                 ON course TYPE string;
DEFINE FIELD source             ON course TYPE string;
DEFINE FIELD name               ON course TYPE string;
DEFINE FIELD description        ON course TYPE option<string>;
DEFINE FIELD url                ON course TYPE option<string>;
DEFINE FIELD partner            ON course TYPE option<string>;
DEFINE FIELD objective          ON course TYPE array<string>;
DEFINE FIELD difficulty         ON course TYPE option<string>;
DEFINE FIELD rating             ON course TYPE option<float>;
DEFINE FIELD num_rating         ON course TYPE option<int>;
DEFINE FIELD hours              ON course TYPE option<float>;
DEFINE FIELD weeks              ON course TYPE option<int>;
DEFINE FIELD total_modules      ON course TYPE option<int>;
DEFINE FIELD total_videos       ON course TYPE option<int>;
DEFINE FIELD total_readings     ON course TYPE option<int>;
DEFINE FIELD total_assignments  ON course TYPE option<int>;
DEFINE FIELD total_discussions  ON course TYPE option<float>;
DEFINE FIELD certificate        ON course TYPE option<bool>;

DEFINE INDEX course_description_idx ON course FIELDS description;

-- ============================================================
-- TABLE: instructor
-- ============================================================

DEFINE TABLE instructor SCHEMAFULL;
DEFINE FIELD id    ON instructor TYPE string;
DEFINE FIELD name  ON instructor TYPE string;
DEFINE FIELD title ON instructor TYPE option<string>;
DEFINE FIELD bio   ON instructor TYPE option<string>;

DEFINE INDEX instructor_bio_idx ON instructor FIELDS bio;

-- ============================================================
-- TABLE: module
-- ============================================================

DEFINE TABLE module SCHEMAFULL;
DEFINE FIELD id                 ON module TYPE string;
DEFINE FIELD description        ON module TYPE option<string>;
DEFINE FIELD video_count        ON module TYPE option<int>;
DEFINE FIELD minutes            ON module TYPE option<float>;
DEFINE FIELD assignment_count   ON module TYPE option<int>;

-- ============================================================
-- TABLE: student
-- ============================================================

DEFINE TABLE student SCHEMALESS;
DEFINE FIELD id    ON student TYPE string;
DEFINE FIELD name  ON student TYPE string;
DEFINE FIELD email ON student TYPE string;
DEFINE FIELD major ON student TYPE string;

-- ============================================================
-- TABLE: student_score
-- ============================================================

DEFINE TABLE student_score SCHEMALESS;
DEFINE FIELD id    ON student_score TYPE string;
DEFINE FIELD name  ON student_score TYPE string;
DEFINE FIELD grade ON student_score TYPE string;

-- ============================================================
-- TABLE: assignment
-- ============================================================

DEFINE TABLE assignment SCHEMAFULL;
DEFINE FIELD id         ON assignment TYPE string;
DEFINE FIELD type       ON assignment TYPE string;
DEFINE FIELD title      ON assignment TYPE string;
DEFINE FIELD source     ON assignment TYPE string;
DEFINE FIELD content    ON assignment TYPE option<string>;
DEFINE FIELD word_count ON assignment TYPE option<int>;
DEFINE FIELD due_date   ON assignment TYPE option<string>;
DEFINE FIELD concepts   ON assignment TYPE option<array>;

DEFINE INDEX assignment_content_idx ON assignment FIELDS content;
DEFINE INDEX assignment_title_idx   ON assignment FIELDS title UNIQUE;

-- ============================================================
-- TABLE: announcement
-- ============================================================

DEFINE TABLE announcement SCHEMAFULL;
DEFINE FIELD id      ON announcement TYPE string;
DEFINE FIELD title   ON announcement TYPE string;
DEFINE FIELD content ON announcement TYPE string;

DEFINE INDEX announcement_title_idx   ON announcement FIELDS title;
DEFINE INDEX announcement_content_idx ON announcement FIELDS content;

-- ============================================================
-- TABLE: discussion
-- ============================================================

DEFINE TABLE discussion SCHEMAFULL;
DEFINE FIELD id      ON discussion TYPE string;
DEFINE FIELD title   ON discussion TYPE string;
DEFINE FIELD message ON discussion TYPE string;

DEFINE INDEX discussion_title_idx   ON discussion FIELDS title;
DEFINE INDEX discussion_message_idx ON discussion FIELDS message;

-- ============================================================
-- GRAPH RELATIONS (compatible with ingestion.py)
-- ============================================================

DEFINE TABLE covers SCHEMAFULL TYPE RELATION
    IN course | lecture | assignment
    OUT topic;

DEFINE TABLE belongs_to SCHEMAFULL TYPE RELATION IN course OUT subject;
DEFINE TABLE uses SCHEMAFULL TYPE RELATION IN course OUT tool;
DEFINE TABLE taught_in SCHEMAFULL TYPE RELATION IN course OUT language;
DEFINE TABLE taught_by SCHEMAFULL TYPE RELATION IN course OUT instructor;
DEFINE TABLE contains SCHEMAFULL TYPE RELATION IN course OUT module;
DEFINE TABLE includes SCHEMAFULL TYPE RELATION IN course OUT lecture;
DEFINE TABLE assigns SCHEMAFULL TYPE RELATION IN course OUT assignment;

DEFINE TABLE assignment_grade SCHEMAFULL TYPE RELATION IN student_score OUT assignment;
DEFINE TABLE student_enrolled_in SCHEMAFULL TYPE RELATION IN student OUT course;