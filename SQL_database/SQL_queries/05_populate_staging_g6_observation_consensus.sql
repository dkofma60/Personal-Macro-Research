-- Populate staging.g6_observation_consensus

BEGIN;



-- ============================================================
-- 1. Preflight validation
-- ============================================================

DO $$
DECLARE
    v_total bigint;
BEGIN
    SELECT COUNT(*)
    INTO v_total
    FROM staging.g6_parsed_observation_post_processed;

    IF v_total <> 87963 THEN
        RAISE EXCEPTION
            'Unexpected post-processed row count: %, expected 87963',
            v_total;
    END IF;

    IF EXISTS (
        SELECT 1
        FROM staging.g6_observation_consensus
    ) THEN
        RAISE EXCEPTION
            'staging.g6_observation_consensus is not empty';
    END IF;
END
$$;


-- ============================================================
-- 2. Build potentially authoritative sets and select consensus
-- ============================================================

WITH preferred_base AS (
    SELECT
        post.*,
        pre.validation_flags,
        pre.cross_release_support_count,

        DENSE_RANK() OVER (
            ORDER BY
                post.observation_date,
                post.measure_canonical,
                post.adjustment_status,
                post.category_definition_id,
                post.geography_canonical NULLS FIRST,
                post.customer_type_canonical NULLS FIRST,
                post.unit_id
        ) AS economic_group_id

    FROM staging.g6_parsed_observation_post_processed AS post

    JOIN staging.g6_parsed_observation_preprocessed AS pre
        USING (g6_cell_extraction_id)

    WHERE post.source_document_precedence = 'preferred'
),

preferred_with_bounds AS (
    SELECT
        preferred_base.*,

        MIN(release_date) OVER (
            PARTITION BY economic_group_id
        ) AS minimum_preferred_release_date,

        MAX(release_date) OVER (
            PARTITION BY economic_group_id
        ) AS maximum_preferred_release_date

    FROM preferred_base
),

preferred_with_cutoff AS (
    SELECT
        preferred_with_bounds.*,

        CASE
            -- Later calculation-method break takes precedence
            -- when a group spans both breaks.
            WHEN minimum_preferred_release_date
                    < DATE '1991-02-19'
             AND maximum_preferred_release_date
                    >= DATE '1991-02-19'
                THEN DATE '1991-02-19'

            WHEN minimum_preferred_release_date
                    < DATE '1982-10-14'
             AND maximum_preferred_release_date
                    >= DATE '1982-10-14'
                THEN DATE '1982-10-14'

            ELSE NULL
        END AS revision_cutoff_date

    FROM preferred_with_bounds
),

potentially_authoritative AS (
    SELECT *
    FROM preferred_with_cutoff
    WHERE revision_cutoff_date IS NULL
       OR release_date >= revision_cutoff_date
),

group_dimensions AS (
    SELECT DISTINCT ON (economic_group_id)
        economic_group_id,
        observation_date,
        measure_canonical,
        adjustment_status,
        category_definition_id,
        geography_canonical,
        customer_type_canonical,
        unit_id

    FROM potentially_authoritative

    ORDER BY economic_group_id
),

potentially_authoritative_group_stats AS (
    SELECT
        economic_group_id,

        COUNT(*)::smallint
            AS potentially_authoritative_cell_count,

        MAX(revision_cutoff_date)
            AS revision_cutoff_date

    FROM potentially_authoritative

    GROUP BY economic_group_id
),

-- One result is one distinct combination of value status
-- and numeric value.
result_stats AS (
    SELECT
        economic_group_id,
        value_status,
        value_numeric,

        COUNT(*)::smallint
            AS result_support_count,

        MIN(jsonb_array_length(validation_flags))
            AS minimum_validation_flag_count,

        MAX(cross_release_support_count)
            AS maximum_cross_release_support_count,

        -- Used only as a final deterministic ranking criterion.
        MAX(g6_cell_extraction_id)
            AS deterministic_tiebreak_cell_id

    FROM potentially_authoritative

    GROUP BY
        economic_group_id,
        value_status,
        value_numeric
),

result_with_max_support AS (
    SELECT
        result_stats.*,

        MAX(result_support_count) OVER (
            PARTITION BY economic_group_id
        ) AS maximum_result_support_count

    FROM result_stats
),

ranked_results AS (
    SELECT
        result_with_max_support.*,

        COUNT(*) OVER (
            PARTITION BY economic_group_id
        )::smallint
            AS distinct_potentially_authoritative_cell_count,

        SUM(
            (
                result_support_count
                    = maximum_result_support_count
            )::integer
        ) OVER (
            PARTITION BY economic_group_id
        ) AS top_support_tie_count,

        ROW_NUMBER() OVER (
            PARTITION BY economic_group_id
            ORDER BY
                result_support_count DESC,

                CASE value_status
                    WHEN 'reported'         THEN 1
                    WHEN 'not_available'    THEN 2
                    WHEN 'blank'            THEN 3
                    WHEN 'extraction_error' THEN 4
                END,

                minimum_validation_flag_count ASC,
                maximum_cross_release_support_count DESC,
                deterministic_tiebreak_cell_id DESC
        ) AS result_rank

    FROM result_with_max_support
),

winner AS (
    SELECT *
    FROM ranked_results
    WHERE result_rank = 1
)

INSERT INTO staging.g6_observation_consensus (
    observation_date,
    measure_canonical,
    adjustment_status,
    category_definition_id,
    geography_canonical,
    customer_type_canonical,
    unit_id,
    value_numeric,
    value_status,
    consensus_method,
    potentially_authoritative_cell_count,
    selected_value_support_count,
    distinct_potentially_authoritative_cell_count,
    revision_cutoff_date
)
SELECT
    dimensions.observation_date,
    dimensions.measure_canonical,
    dimensions.adjustment_status,
    dimensions.category_definition_id,
    dimensions.geography_canonical,
    dimensions.customer_type_canonical,
    dimensions.unit_id,

    winner.value_numeric,
    winner.value_status,

    CASE
        WHEN group_stats.potentially_authoritative_cell_count = 1
            THEN 'singleton'

        WHEN winner.distinct_potentially_authoritative_cell_count = 1
            THEN 'unanimous'

        WHEN winner.top_support_tie_count = 1
            THEN 'plurality'

        ELSE 'other_tiebreaking_support'
    END AS consensus_method,

    group_stats.potentially_authoritative_cell_count,
    winner.result_support_count,
    winner.distinct_potentially_authoritative_cell_count,
    group_stats.revision_cutoff_date

FROM winner

JOIN group_dimensions AS dimensions
    USING (economic_group_id)

JOIN potentially_authoritative_group_stats AS group_stats
    USING (economic_group_id);


-- ============================================================
-- ============================================================
-- 3. Post-load validation
-- ============================================================

DO $$
DECLARE
    v_consensus_count                     bigint;
    v_potentially_authoritative_cell_total bigint;
BEGIN
    SELECT
        COUNT(*),
        SUM(potentially_authoritative_cell_count)
    INTO
        v_consensus_count,
        v_potentially_authoritative_cell_total
    FROM staging.g6_observation_consensus;

    IF v_consensus_count <> 7665 THEN
        RAISE EXCEPTION
            'Consensus row count %, expected 7665',
            v_consensus_count;
    END IF;

    IF v_potentially_authoritative_cell_total <> 82977 THEN
        RAISE EXCEPTION
            'Potentially authoritative cell total %, expected 82977',
            v_potentially_authoritative_cell_total;
    END IF;
END
$$;

COMMIT;
