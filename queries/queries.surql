-- ============================================================
-- queries/queries.surql
-- SurrealQL multimodal queries for learning_management_db project
-- ============================================================
-- Run individual queries by selecting a block and executing
-- via the SurrealDB REPL, CLI, or HTTP /sql endpoint.
-- ============================================================

USE NS education DB learning_management_db;


-- ════════════════════════════════════════════════════════════
-- QUERY 1: Full-Text Keyword Search Over Extracted Text
-- ════════════════════════════════════════════════════════════
-- Find all lectures and assignments that mention a keyword.
-- Uses the BM25 full-text search indexes defined in schema.surql.

LET $keyword = "normalization";

SELECT
    id,
    title,
    type,
    search::score(1) AS relevance_score
FROM lecture
WHERE content @1@ $keyword

UNION ALL

SELECT
    id,
    title,
    type,
    search::score(1) AS relevance_score
FROM assignment
WHERE content @1@ $keyword

ORDER BY relevance_score DESC;


-- ════════════════════════════════════════════════════════════
-- QUERY 2: Join CSV Student Scores with Assignment Metadata
-- ════════════════════════════════════════════════════════════
-- Compute summary statistics for student scores and link back
-- to the assignment metadata for context.

SELECT
    ss.student_id,
    ss.name,
    ss.assignment_1,
    ss.assignment_2,
    ss.midterm,
    ss.final,
    ss.grade,
    -- Computed average across all assessments
    math::mean([ss.assignment_1, ss.assignment_2, ss.midterm, ss.final]) AS avg_score,
    -- Pull assignment title from assignment table for enrichment
    (SELECT title, due_date FROM assignment LIMIT 1) AS assignment_info
FROM student_score AS ss
ORDER BY avg_score DESC;


-- ════════════════════════════════════════════════════════════
-- QUERY 3: Linking Lecture Content to Metadata Topics
-- ════════════════════════════════════════════════════════════
-- For each lecture, show topics from lecture record alongside
-- metadata-provided topics to compare coverage.

SELECT
    l.id           AS lecture_id,
    l.title        AS lecture_title,
    l.topics       AS lecture_topics,
    l.page_count,
    -- Subselect matching metadata material entry
    (
        SELECT
            m.data.materials[WHERE filename = l.filename][0].topics AS meta_topics,
            m.data.course.title AS course_title,
            m.data.course.instructor AS instructor
        FROM metadata AS m
        LIMIT 1
    ) AS metadata_context
FROM lecture AS l;


-- ════════════════════════════════════════════════════════════
-- QUERY 4: Graph Traversal —Topics Shared Between
--          Lectures and Assignments
-- ════════════════════════════════════════════════════════════
-- Walk the graph:
--   lecture -[covers]-> topic <-[requires]- assignment
-- Find which topics appear in BOTH a lecture AND an assignment.

SELECT
    topic.id          AS topic_id,
    topic.name        AS topic_name,
    -- All lectures covering this topic
    array::group(
        SELECT VALUE in FROM covers WHERE out = topic.id
    )                   AS covered_by_lectures,
    -- All assignments requiring this topic
    array::group(
        SELECT VALUE in FROM requires WHERE out = topic.id
    )                   AS required_by_assignments
FROM topic
WHERE
    (SELECT count() FROM covers   WHERE out = topic.id) > 0
AND (SELECT count() FROM requires WHERE out = topic.id) > 0
ORDER BY topic_name;


-- ════════════════════════════════════════════════════════════
-- QUERY 5 (Bonus): Grade Distribution Summary
-- ════════════════════════════════════════════════════════════
-- Aggregate student grades and compute class statistics.

SELECT
    grade,
    count()                                              AS num_students,
    math::mean(final)                                    AS avg_final,
    math::min(final)                                     AS min_final,
    math::max(final)                                     AS max_final
FROM student_score
GROUP BY grade
ORDER BY avg_final DESC;


-- ════════════════════════════════════════════════════════════
-- QUERY 6 (Bonus): All Materials Described by Metadata
-- ════════════════════════════════════════════════════════════
-- Graph traversal: metadata -[describes]-> <any table>

SELECT
    meta.id       AS metadata_id,
    meta.course_id,
    ->describes.out AS described_material_ids
FROM metadata AS meta;


-- ════════════════════════════════════════════════════════════
-- QUERY 7 (Bonus): Students Scoring Below 75 on Final
-- ════════════════════════════════════════════════════════════
-- Identify at-risk students for the final exam, joining with
-- topic coverage so instructors know which topics to review.

SELECT
    ss.student_id,
    ss.name,
    ss.final       AS final_score,
    ss.grade,
    -- Topics tested in the assignment (via graph)
    (SELECT ->requires->topic.name AS topics FROM assignment LIMIT 1) AS tested_topics
FROM student_score AS ss
WHERE ss.final < 75
ORDER BY ss.final ASC;
