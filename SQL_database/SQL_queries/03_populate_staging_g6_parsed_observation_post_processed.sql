-- Populate staging.g6_parsed_observation_post_processed

BEGIN;

-- Prevent concurrent population attempts.
LOCK TABLE staging.g6_parsed_observation_post_processed
    IN ACCESS EXCLUSIVE MODE;


-- ============================================================
-- 1. Preflight checks
-- ============================================================

DO $$
DECLARE
    v_preprocessed_count bigint;
BEGIN
    IF EXISTS (
        SELECT 1
        FROM staging.g6_parsed_observation_post_processed
    ) THEN
        RAISE EXCEPTION
            'staging.g6_parsed_observation_post_processed is not empty';
    END IF;

    SELECT COUNT(*)
    INTO v_preprocessed_count
    FROM staging.g6_parsed_observation_preprocessed;

    IF v_preprocessed_count <> 87963 THEN
        RAISE EXCEPTION
            'Unexpected preprocessed row count: %, expected 87963',
            v_preprocessed_count;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM staging.g6_unit_dimension
    ) THEN
        RAISE EXCEPTION 'staging.g6_unit_dimension is empty';
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM staging.g6_deposit_category_definition
    ) THEN
        RAISE EXCEPTION
            'staging.g6_deposit_category_definition is empty';
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM staging.g6_deposit_definition_rule
    ) THEN
        RAISE EXCEPTION
            'staging.g6_deposit_definition_rule is empty';
    END IF;
END
$$;


-- ============================================================
-- 2. Require exactly one definition rule per observation
-- ============================================================

DO $$
DECLARE
    v_cell_id          integer;
    v_deposit_type     text;
    v_release_date     date;
    v_observation_date date;
    v_match_count      bigint;
BEGIN
    SELECT
        matched.g6_cell_extraction_id,
        matched.deposit_type_canonical,
        matched.release_date,
        matched.observation_date,
        matched.match_count
    INTO
        v_cell_id,
        v_deposit_type,
        v_release_date,
        v_observation_date,
        v_match_count
    FROM (
        SELECT
            pre.g6_cell_extraction_id,
            pre.deposit_type_canonical,
            pre.release_date,
            pre.observation_date,
            COUNT(rule.definition_rule_id) AS match_count
        FROM staging.g6_parsed_observation_preprocessed AS pre
        LEFT JOIN staging.g6_deposit_definition_rule AS rule
            ON rule.deposit_type_canonical =
               pre.deposit_type_canonical

           AND (
                rule.release_date_from IS NULL
                OR pre.release_date >= rule.release_date_from
           )

           AND (
                rule.release_date_to IS NULL
                OR pre.release_date <= rule.release_date_to
           )

           AND (
                rule.observation_date_from IS NULL
                OR pre.observation_date >= rule.observation_date_from
           )

           AND (
                rule.observation_date_to IS NULL
                OR pre.observation_date <= rule.observation_date_to
           )

        GROUP BY
            pre.g6_cell_extraction_id,
            pre.deposit_type_canonical,
            pre.release_date,
            pre.observation_date

        HAVING COUNT(rule.definition_rule_id) <> 1
    ) AS matched
    LIMIT 1;

    IF FOUND THEN
        RAISE EXCEPTION
            'Cell %: deposit type %, release date %, observation date % matches % definition rules; expected exactly one',
            v_cell_id,
            v_deposit_type,
            v_release_date,
            v_observation_date,
            v_match_count;
    END IF;
END
$$;


-- ============================================================
-- 3. Validate raw provenance and document precedence
-- ============================================================

DO $$
DECLARE
    v_bad_cell_id integer;
BEGIN
    -- The preprocessed release date must equal the physical
    -- source document's publication date.
    SELECT pre.g6_cell_extraction_id
    INTO v_bad_cell_id
    FROM staging.g6_parsed_observation_preprocessed AS pre
    JOIN raw.g6_cell_extraction AS cell
        USING (g6_cell_extraction_id)
    JOIN raw.source_document AS document
        ON document.source_document_id =
           cell.source_document_id
    WHERE pre.release_date <> document.document_date
    LIMIT 1;

    IF FOUND THEN
        RAISE EXCEPTION
            'Release date differs from raw source-document date for cell %',
            v_bad_cell_id;
    END IF;

    -- Every nonpreferred source document must be explicitly
    -- superseded by another source document.
    SELECT pre.g6_cell_extraction_id
    INTO v_bad_cell_id
    FROM staging.g6_parsed_observation_preprocessed AS pre
    JOIN raw.g6_cell_extraction AS cell
        USING (g6_cell_extraction_id)
    JOIN raw.source_document AS document
        ON document.source_document_id =
           cell.source_document_id
    WHERE document.is_preferred_version = false
      AND NOT EXISTS (
          SELECT 1
          FROM raw.source_document AS replacement
          WHERE replacement.supersedes_source_document_id =
                document.source_document_id
      )
    LIMIT 1;

    IF FOUND THEN
        RAISE EXCEPTION
            'Cell % belongs to a nonpreferred document that is not explicitly superseded',
            v_bad_cell_id;
    END IF;
END
$$;


-- ============================================================
-- 4. Validate controlled-unit coverage
-- ============================================================

DO $$
DECLARE
    v_measure text;
BEGIN
    SELECT pre.measure_canonical
    INTO v_measure
    FROM staging.g6_parsed_observation_preprocessed AS pre
    LEFT JOIN staging.g6_unit_dimension AS unit
        ON unit.unit_code =
           CASE pre.measure_canonical
               WHEN 'debits'
                   THEN 'usd_billions_annual_rate'
               WHEN 'average_deposits'
                   THEN 'usd_billions'
               WHEN 'turnover'
                   THEN 'times_per_year'
           END
       AND unit.measure_canonical = pre.measure_canonical
    WHERE unit.unit_id IS NULL
    LIMIT 1;

    IF FOUND THEN
        RAISE EXCEPTION
            'No controlled unit exists for measure %',
            v_measure;
    END IF;
END
$$;


-- ============================================================
-- 5. Populate the post-processed table
-- ============================================================

WITH matched_rule AS (
    SELECT
        pre.g6_cell_extraction_id,
        rule.definition_rule_id,
        rule.category_definition_id
    FROM staging.g6_parsed_observation_preprocessed AS pre
    JOIN staging.g6_deposit_definition_rule AS rule
        ON rule.deposit_type_canonical =
           pre.deposit_type_canonical

       AND (
            rule.release_date_from IS NULL
            OR pre.release_date >= rule.release_date_from
       )

       AND (
            rule.release_date_to IS NULL
            OR pre.release_date <= rule.release_date_to
       )

       AND (
            rule.observation_date_from IS NULL
            OR pre.observation_date >= rule.observation_date_from
       )

       AND (
            rule.observation_date_to IS NULL
            OR pre.observation_date <= rule.observation_date_to
       )
)

INSERT INTO staging.g6_parsed_observation_post_processed (
    g6_cell_extraction_id,
    g6_release_id,
    source_document_id,
    source_document_precedence,
    release_date,
    observation_date,
    observation_date_status,
    measure_canonical,
    adjustment_status,
    definition_rule_id,
    category_definition_id,
    geography_canonical,
    customer_type_canonical,
    unit_id,
    value_numeric,
    value_status
)
SELECT
    pre.g6_cell_extraction_id,
    document.g6_release_id,
    document.source_document_id,

    CASE
        WHEN document.is_preferred_version
            THEN 'preferred'
        ELSE 'superseded'
    END AS source_document_precedence,

    pre.release_date,
    pre.observation_date,
    pre.observation_date_status,
    pre.measure_canonical,
    pre.adjustment_status,

    matched.definition_rule_id,
    matched.category_definition_id,

    pre.geography_canonical,
    pre.customer_type_canonical,

    unit.unit_id,

    pre.value_numeric,
    pre.value_status

FROM staging.g6_parsed_observation_preprocessed AS pre

JOIN raw.g6_cell_extraction AS cell
    USING (g6_cell_extraction_id)

JOIN raw.source_document AS document
    ON document.source_document_id =
       cell.source_document_id

JOIN matched_rule AS matched
    USING (g6_cell_extraction_id)

JOIN staging.g6_unit_dimension AS unit
    ON unit.unit_code =
       CASE pre.measure_canonical
           WHEN 'debits'
               THEN 'usd_billions_annual_rate'
           WHEN 'average_deposits'
               THEN 'usd_billions'
           WHEN 'turnover'
               THEN 'times_per_year'
       END
   AND unit.measure_canonical = pre.measure_canonical;


-- ============================================================
-- 6. Post-load validation
-- ============================================================

DO $$
DECLARE
    v_preprocessed_count bigint;
    v_postprocessed_count bigint;
    v_missing_count bigint;
    v_bad_precedence_count bigint;
BEGIN
    SELECT COUNT(*)
    INTO v_preprocessed_count
    FROM staging.g6_parsed_observation_preprocessed;

    SELECT COUNT(*)
    INTO v_postprocessed_count
    FROM staging.g6_parsed_observation_post_processed;

    IF v_postprocessed_count <> v_preprocessed_count THEN
        RAISE EXCEPTION
            'Post-processed row count %, expected %',
            v_postprocessed_count,
            v_preprocessed_count;
    END IF;

    SELECT COUNT(*)
    INTO v_missing_count
    FROM staging.g6_parsed_observation_preprocessed AS pre
    LEFT JOIN staging.g6_parsed_observation_post_processed AS post
        USING (g6_cell_extraction_id)
    WHERE post.g6_cell_extraction_id IS NULL;

    IF v_missing_count <> 0 THEN
        RAISE EXCEPTION
            '% preprocessed rows are missing from the post-processed table',
            v_missing_count;
    END IF;

    SELECT COUNT(*)
    INTO v_bad_precedence_count
    FROM staging.g6_parsed_observation_post_processed AS post
    JOIN raw.source_document AS document
        USING (source_document_id)
    WHERE
        (
            document.is_preferred_version
            AND post.source_document_precedence <> 'preferred'
        )
        OR
        (
            NOT document.is_preferred_version
            AND post.source_document_precedence <> 'superseded'
        );

    IF v_bad_precedence_count <> 0 THEN
        RAISE EXCEPTION
            '% rows have an incorrect source-document precedence classification',
            v_bad_precedence_count;
    END IF;
END
$$;

COMMIT;
