-- Populate staging.g6_observation_cross_checked

BEGIN;



-- ============================================================
-- 1. Working copy
--
-- effective_support_count follows the currently accepted value.
--
-- If arithmetic reconstructs/replaces a value, its effective
-- support becomes the weakest support among the observations
-- used to calculate it.
-- ============================================================

CREATE TEMP TABLE g6_crosscheck_work
ON COMMIT DROP
AS
SELECT
    c.g6_observation_consensus_id,
    c.observation_date,
    c.measure_canonical,
    c.adjustment_status,
    c.category_definition_id,
    c.geography_canonical,
    c.customer_type_canonical,
    c.unit_id,
    c.value_numeric,
    c.value_status,

    c.selected_value_support_count
        AS effective_support_count,

    false::boolean
        AS cross_checked_value_replaced

FROM staging.g6_observation_consensus AS c;


CREATE INDEX ix_g6_crosscheck_work_dimensions
    ON g6_crosscheck_work (
        category_definition_id,
        observation_date,
        adjustment_status,
        measure_canonical,
        geography_canonical,
        customer_type_canonical
    );

CREATE UNIQUE INDEX ix_g6_crosscheck_work_id
    ON g6_crosscheck_work (
        g6_observation_consensus_id
    );

ANALYZE g6_crosscheck_work;

-- ============================================================
-- 2. SAVINGS TOTAL CROSS-CHECK
--
-- Era 1:
--     savings total = business + other
--
-- Era 2:
--     savings total = ATS/NOW + business + other
--
-- IMPORTANT:
--
-- In the controlled economic definitions, the Era 2 ATS/NOW
-- observation is stored under its own category definition,
-- not under the savings category_definition_id.
--
-- Therefore Era 2 must explicitly join the ATS/NOW series to
-- the savings total/business/other series.
--
-- Applies only to:
--     debits
--     average_deposits
--
-- Turnover is NOT additive.
-- ============================================================

CREATE TEMP TABLE savings_actions
ON COMMIT DROP
AS

WITH definition_ids AS (
    SELECT
        MAX(category_definition_id)
            FILTER (
                WHERE definition_code =
                    'savings_pre_ats_now_v1'
            ) AS era1_savings_definition_id,

        MAX(category_definition_id)
            FILTER (
                WHERE definition_code =
                    'savings_including_ats_now_v2'
            ) AS era2_savings_definition_id,

        MAX(category_definition_id)
            FILTER (
                WHERE definition_code =
                    'other_checkable_narrow_v1'
            ) AS ats_now_definition_id

    FROM staging.g6_deposit_category_definition
),


-- ------------------------------------------------------------
-- Era 1:
-- total = business + other
-- ------------------------------------------------------------

era1_groups AS (
    SELECT
        w.observation_date,
        w.measure_canonical,
        w.adjustment_status,
        w.category_definition_id,
        w.geography_canonical,
        w.unit_id,

        'savings_pre_ats_now_v1'::text
            AS definition_code,

        MAX(w.g6_observation_consensus_id)
            FILTER (
                WHERE w.customer_type_canonical = 'total'
            ) AS total_id,

        MAX(w.g6_observation_consensus_id)
            FILTER (
                WHERE w.customer_type_canonical = 'business'
            ) AS business_id,

        MAX(w.g6_observation_consensus_id)
            FILTER (
                WHERE w.customer_type_canonical = 'other'
            ) AS other_id,

        NULL::smallint AS ats_now_id,


        MAX(w.value_numeric)
            FILTER (
                WHERE w.customer_type_canonical = 'total'
            ) AS total_value,

        MAX(w.value_numeric)
            FILTER (
                WHERE w.customer_type_canonical = 'business'
            ) AS business_value,

        MAX(w.value_numeric)
            FILTER (
                WHERE w.customer_type_canonical = 'other'
            ) AS other_value,

        NULL::numeric AS ats_now_value,


        MAX(w.value_status)
            FILTER (
                WHERE w.customer_type_canonical = 'total'
            ) AS total_status,

        MAX(w.value_status)
            FILTER (
                WHERE w.customer_type_canonical = 'business'
            ) AS business_status,

        MAX(w.value_status)
            FILTER (
                WHERE w.customer_type_canonical = 'other'
            ) AS other_status,

        NULL::text AS ats_now_status,


        MAX(w.effective_support_count)
            FILTER (
                WHERE w.customer_type_canonical = 'total'
            ) AS total_support,

        MAX(w.effective_support_count)
            FILTER (
                WHERE w.customer_type_canonical = 'business'
            ) AS business_support,

        MAX(w.effective_support_count)
            FILTER (
                WHERE w.customer_type_canonical = 'other'
            ) AS other_support,

        NULL::smallint AS ats_now_support

    FROM g6_crosscheck_work AS w

    CROSS JOIN definition_ids AS d

    WHERE w.category_definition_id =
          d.era1_savings_definition_id

      AND w.measure_canonical IN (
          'debits',
          'average_deposits'
      )

    GROUP BY
        w.observation_date,
        w.measure_canonical,
        w.adjustment_status,
        w.category_definition_id,
        w.geography_canonical,
        w.unit_id
),


-- ------------------------------------------------------------
-- Era 2 savings portion:
-- total/business/other
-- ------------------------------------------------------------

era2_savings AS (
    SELECT
        w.observation_date,
        w.measure_canonical,
        w.adjustment_status,
        w.category_definition_id,
        w.geography_canonical,
        w.unit_id,

        MAX(w.g6_observation_consensus_id)
            FILTER (
                WHERE w.customer_type_canonical = 'total'
            ) AS total_id,

        MAX(w.g6_observation_consensus_id)
            FILTER (
                WHERE w.customer_type_canonical = 'business'
            ) AS business_id,

        MAX(w.g6_observation_consensus_id)
            FILTER (
                WHERE w.customer_type_canonical = 'other'
            ) AS other_id,


        MAX(w.value_numeric)
            FILTER (
                WHERE w.customer_type_canonical = 'total'
            ) AS total_value,

        MAX(w.value_numeric)
            FILTER (
                WHERE w.customer_type_canonical = 'business'
            ) AS business_value,

        MAX(w.value_numeric)
            FILTER (
                WHERE w.customer_type_canonical = 'other'
            ) AS other_value,


        MAX(w.value_status)
            FILTER (
                WHERE w.customer_type_canonical = 'total'
            ) AS total_status,

        MAX(w.value_status)
            FILTER (
                WHERE w.customer_type_canonical = 'business'
            ) AS business_status,

        MAX(w.value_status)
            FILTER (
                WHERE w.customer_type_canonical = 'other'
            ) AS other_status,


        MAX(w.effective_support_count)
            FILTER (
                WHERE w.customer_type_canonical = 'total'
            ) AS total_support,

        MAX(w.effective_support_count)
            FILTER (
                WHERE w.customer_type_canonical = 'business'
            ) AS business_support,

        MAX(w.effective_support_count)
            FILTER (
                WHERE w.customer_type_canonical = 'other'
            ) AS other_support

    FROM g6_crosscheck_work AS w

    CROSS JOIN definition_ids AS d

    WHERE w.category_definition_id =
          d.era2_savings_definition_id

      AND w.measure_canonical IN (
          'debits',
          'average_deposits'
      )

    GROUP BY
        w.observation_date,
        w.measure_canonical,
        w.adjustment_status,
        w.category_definition_id,
        w.geography_canonical,
        w.unit_id
),


-- ------------------------------------------------------------
-- Era 2 ATS/NOW portion.
--
-- It has its own category definition but is one component of
-- the published Era 2 savings total.
-- ------------------------------------------------------------

era2_ats_now AS (
    SELECT
        w.observation_date,
        w.measure_canonical,
        w.adjustment_status,
        w.unit_id,

        w.g6_observation_consensus_id
            AS ats_now_id,

        w.value_numeric
            AS ats_now_value,

        w.value_status
            AS ats_now_status,

        w.effective_support_count
            AS ats_now_support

    FROM g6_crosscheck_work AS w

    CROSS JOIN definition_ids AS d

    WHERE w.category_definition_id =
          d.ats_now_definition_id

      AND w.customer_type_canonical = 'ats_now'

      AND w.measure_canonical IN (
          'debits',
          'average_deposits'
      )
),


-- ------------------------------------------------------------
-- Combine the Era 2 savings observations with their ATS/NOW
-- component.
-- ------------------------------------------------------------

era2_groups AS (
    SELECT
        s.observation_date,
        s.measure_canonical,
        s.adjustment_status,
        s.category_definition_id,
        s.geography_canonical,
        s.unit_id,

        'savings_including_ats_now_v2'::text
            AS definition_code,

        s.total_id,
        s.business_id,
        s.other_id,
        a.ats_now_id,

        s.total_value,
        s.business_value,
        s.other_value,
        a.ats_now_value,

        s.total_status,
        s.business_status,
        s.other_status,
        a.ats_now_status,

        s.total_support,
        s.business_support,
        s.other_support,
        a.ats_now_support

    FROM era2_savings AS s

    LEFT JOIN era2_ats_now AS a
        ON a.observation_date =
           s.observation_date

       AND a.measure_canonical =
           s.measure_canonical

       AND a.adjustment_status =
           s.adjustment_status

       AND a.unit_id =
           s.unit_id
),


all_groups AS (
    SELECT * FROM era1_groups

    UNION ALL

    SELECT * FROM era2_groups
),


complete AS (
    SELECT
        *,

        CASE
            -- Era 1
            WHEN definition_code =
                 'savings_pre_ats_now_v1'
            THEN ROUND(
                business_value
                + other_value,
                1
            )

            -- Era 2
            WHEN definition_code =
                 'savings_including_ats_now_v2'
            THEN ROUND(
                ats_now_value
                + business_value
                + other_value,
                1
            )
        END AS calculated_total,


        CASE
            -- Era 1
            WHEN definition_code =
                 'savings_pre_ats_now_v1'
            THEN LEAST(
                business_support,
                other_support
            )

            -- Era 2
            WHEN definition_code =
                 'savings_including_ats_now_v2'
            THEN LEAST(
                ats_now_support,
                business_support,
                other_support
            )
        END AS component_support,


        CASE
            WHEN definition_code =
                 'savings_pre_ats_now_v1'
                THEN 0.1::numeric

            WHEN definition_code =
                 'savings_including_ats_now_v2'
                THEN 0.2::numeric
        END AS rounding_tolerance

    FROM all_groups

    WHERE total_id IS NOT NULL
      AND business_id IS NOT NULL
      AND other_id IS NOT NULL

      AND business_status = 'reported'
      AND other_status = 'reported'

      AND business_value IS NOT NULL
      AND other_value IS NOT NULL

      AND (
          definition_code =
              'savings_pre_ats_now_v1'

          OR (
              definition_code =
                  'savings_including_ats_now_v2'

              AND ats_now_id IS NOT NULL
              AND ats_now_status = 'reported'
              AND ats_now_value IS NOT NULL
          )
      )
)

SELECT
    *,

    CASE
        -- Missing total can be reconstructed.
        WHEN total_status IN (
            'blank',
            'extraction_error'
        )
            THEN 'replace_total'


        -- Reported total agrees within rounding tolerance.
        WHEN total_status = 'reported'
         AND ABS(
                total_value - calculated_total
             ) <= rounding_tolerance
            THEN 'consistent'


        -- Arithmetic wins only with strictly stronger support.
        WHEN total_status = 'reported'
         AND ABS(
                total_value - calculated_total
             ) > rounding_tolerance
         AND component_support > total_support
            THEN 'replace_total'


        -- Direct total wins ties and stronger-support cases.
        WHEN total_status = 'reported'
         AND ABS(
                total_value - calculated_total
             ) > rounding_tolerance
         AND component_support <= total_support
            THEN 'remove_components'


        ELSE 'no_action'
    END AS action

FROM complete;


CREATE INDEX ix_savings_actions_total_id
    ON savings_actions (total_id);

ANALYZE savings_actions;


-- ------------------------------------------------------------
-- Replace/reconstruct total
-- ------------------------------------------------------------

UPDATE g6_crosscheck_work AS w

SET
    value_numeric = a.calculated_total,
    value_status = 'reported',
    effective_support_count = a.component_support,
    cross_checked_value_replaced = true

FROM savings_actions AS a

WHERE a.action = 'replace_total'

  AND w.g6_observation_consensus_id =
      a.total_id;


-- ------------------------------------------------------------
-- Direct total wins.
--
-- Era 1 removes:
--     business + other
--
-- Era 2 removes:
--     ATS/NOW + business + other
-- ------------------------------------------------------------

DELETE FROM g6_crosscheck_work AS w

USING (
    SELECT business_id AS id
    FROM savings_actions
    WHERE action = 'remove_components'

    UNION

    SELECT other_id AS id
    FROM savings_actions
    WHERE action = 'remove_components'

    UNION

    SELECT ats_now_id AS id
    FROM savings_actions
    WHERE action = 'remove_components'
      AND definition_code =
          'savings_including_ats_now_v2'
      AND ats_now_id IS NOT NULL

) AS remove

WHERE w.g6_observation_consensus_id =
      remove.id;


ANALYZE g6_crosscheck_work;

-- ============================================================
-- 3. TURNOVER CROSS-CHECK
--
--     turnover = debits / average deposits
--
-- Debits and average deposits are rounded to one decimal in
-- the publication. Therefore their simple displayed ratio does
-- not always round to the separately published turnover.
--
-- Instead, construct the range of possible ratios compatible
-- with the rounding intervals of the displayed inputs.
--
-- If published X has one decimal place, its underlying value is
-- approximately:
--
--     [X - 0.05, X + 0.05]
--
-- A reported turnover is considered arithmetically consistent
-- if its own rounding interval overlaps the possible ratio range.
--
-- For a genuine disagreement:
--
--     component_support > turnover_support
--         -> calculated turnover wins
--
--     component_support <= turnover_support
--         -> directly reported turnover wins
--
-- Arithmetic therefore does NOT win a support tie.
-- ============================================================

CREATE TEMP TABLE turnover_actions
ON COMMIT DROP
AS

WITH groups AS (
    SELECT
        w.observation_date,
        w.adjustment_status,
        w.category_definition_id,
        w.geography_canonical,
        w.customer_type_canonical,


        MAX(w.g6_observation_consensus_id)
            FILTER (
                WHERE w.measure_canonical = 'debits'
            ) AS debit_id,

        MAX(w.g6_observation_consensus_id)
            FILTER (
                WHERE w.measure_canonical =
                      'average_deposits'
            ) AS average_deposit_id,

        MAX(w.g6_observation_consensus_id)
            FILTER (
                WHERE w.measure_canonical = 'turnover'
            ) AS turnover_id,


        MAX(w.value_numeric)
            FILTER (
                WHERE w.measure_canonical = 'debits'
            ) AS debit_value,

        MAX(w.value_numeric)
            FILTER (
                WHERE w.measure_canonical =
                      'average_deposits'
            ) AS average_deposit_value,

        MAX(w.value_numeric)
            FILTER (
                WHERE w.measure_canonical = 'turnover'
            ) AS turnover_value,


        MAX(w.value_status)
            FILTER (
                WHERE w.measure_canonical = 'debits'
            ) AS debit_status,

        MAX(w.value_status)
            FILTER (
                WHERE w.measure_canonical =
                      'average_deposits'
            ) AS average_deposit_status,

        MAX(w.value_status)
            FILTER (
                WHERE w.measure_canonical = 'turnover'
            ) AS turnover_status,


        MAX(w.effective_support_count)
            FILTER (
                WHERE w.measure_canonical = 'debits'
            ) AS debit_support,

        MAX(w.effective_support_count)
            FILTER (
                WHERE w.measure_canonical =
                      'average_deposits'
            ) AS average_deposit_support,

        MAX(w.effective_support_count)
            FILTER (
                WHERE w.measure_canonical = 'turnover'
            ) AS turnover_support

    FROM g6_crosscheck_work AS w

    GROUP BY
        w.observation_date,
        w.adjustment_status,
        w.category_definition_id,
        w.geography_canonical,
        w.customer_type_canonical
),

complete AS (
    SELECT
        *,

        -- Point estimate used only when turnover is actually
        -- reconstructed or replaced.
        ROUND(
            debit_value
            / average_deposit_value,
            1
        ) AS calculated_turnover,


        -- Confidence of the arithmetic evidence is limited by
        -- its weaker input.
        LEAST(
            debit_support,
            average_deposit_support
        ) AS component_support,


        -- Lowest possible ratio compatible with rounding.
        (
            (debit_value - 0.05)
            /
            (average_deposit_value + 0.05)
        ) AS minimum_possible_turnover,


        -- Highest possible ratio compatible with rounding.
        (
            (debit_value + 0.05)
            /
            (average_deposit_value - 0.05)
        ) AS maximum_possible_turnover

    FROM groups

    WHERE debit_id IS NOT NULL
      AND average_deposit_id IS NOT NULL
      AND turnover_id IS NOT NULL

      AND debit_status = 'reported'
      AND average_deposit_status = 'reported'

      AND debit_value IS NOT NULL
      AND average_deposit_value IS NOT NULL

      -- Ensures lower denominator bound is positive.
      AND average_deposit_value > 0.05
),

classified AS (
    SELECT
        *,

        CASE
            -- Missing turnover cannot itself be checked.
            WHEN turnover_status IN (
                'blank',
                'extraction_error'
            )
                THEN false


            -- Turnover's underlying interval is approximately:
            --
            -- [turnover - 0.05, turnover + 0.05]
            --
            -- An overlap means the three displayed values can
            -- all be simultaneously correct despite rounding.
            WHEN turnover_status = 'reported'
             AND turnover_value IS NOT NULL

             AND
                 (turnover_value + 0.05)
                     >= minimum_possible_turnover

             AND
                 (turnover_value - 0.05)
                     <= maximum_possible_turnover

                THEN true


            ELSE false
        END AS turnover_is_rounding_consistent

    FROM complete
)

SELECT
    *,

    CASE
        -- Missing turnover: calculate it because no usable
        -- directly observed turnover exists.
        WHEN turnover_status IN (
            'blank',
            'extraction_error'
        )
            THEN 'replace_turnover'


        -- Published turnover is compatible with the two
        -- published inputs after allowing for rounding.
        WHEN turnover_status = 'reported'
         AND turnover_is_rounding_consistent
            THEN 'consistent'


        -- Genuine disagreement:
        -- arithmetic wins ONLY with strictly greater support.
        WHEN turnover_status = 'reported'
         AND NOT turnover_is_rounding_consistent
         AND component_support > turnover_support
            THEN 'replace_turnover'


        -- Genuine disagreement:
        -- direct turnover wins ties and stronger-support cases.
        WHEN turnover_status = 'reported'
         AND NOT turnover_is_rounding_consistent
         AND component_support <= turnover_support
            THEN 'remove_inputs'


        ELSE 'no_action'
    END AS action

FROM classified;


CREATE INDEX ix_turnover_actions_turnover_id
    ON turnover_actions (turnover_id);

ANALYZE turnover_actions;


-- ------------------------------------------------------------
-- Fill or replace turnover
-- ------------------------------------------------------------

UPDATE g6_crosscheck_work AS w

SET
    value_numeric = a.calculated_turnover,
    value_status = 'reported',
    effective_support_count = a.component_support,
    cross_checked_value_replaced = true

FROM turnover_actions AS a

WHERE a.action = 'replace_turnover'

  AND w.g6_observation_consensus_id =
      a.turnover_id;


-- ------------------------------------------------------------
-- Direct turnover wins.
--
-- Remove the conflicting debit and average-deposit observations
-- rather than propagating them into later analysis.
-- ------------------------------------------------------------

DELETE FROM g6_crosscheck_work AS w

USING (
    SELECT debit_id AS id
    FROM turnover_actions
    WHERE action = 'remove_inputs'

    UNION

    SELECT average_deposit_id AS id
    FROM turnover_actions
    WHERE action = 'remove_inputs'

) AS remove

WHERE w.g6_observation_consensus_id =
      remove.id;


-- ============================================================
-- 4. Remove observations unsuitable for final numeric analysis

DELETE FROM g6_crosscheck_work AS w
USING staging.g6_deposit_category_definition AS d
WHERE d.category_definition_id = w.category_definition_id
  AND (
         w.value_numeric IS NULL
      OR w.adjustment_status = 'unknown'
      OR w.value_numeric = 0
      OR NOT d.is_separately_reported
  );

-- ============================================================
-- 5. Populate final table
-- ============================================================
INSERT INTO staging.g6_observation_cross_checked (
    g6_observation_consensus_id,
    observation_date,
    measure_canonical,
    adjustment_status,
    category_definition_id,
    geography_canonical,
    customer_type_canonical,
    unit_id,
    value_numeric,
    cross_checked_value_replaced
)
SELECT
    g6_observation_consensus_id,
    observation_date,
    measure_canonical,
    adjustment_status,
    category_definition_id,
    geography_canonical,
    customer_type_canonical,
    unit_id,
    value_numeric,
    cross_checked_value_replaced
FROM g6_crosscheck_work
ORDER BY g6_observation_consensus_id;

-- ============================================================


-- ============================================================
-- 6. Validation
-- ============================================================

DO $$
BEGIN

    IF EXISTS (
        SELECT 1
        FROM staging.g6_observation_cross_checked
        WHERE value_numeric IS NULL
    ) THEN
        RAISE EXCEPTION
            'Final table contains NULL numeric values';
    END IF;


    IF EXISTS (
        SELECT 1
        FROM staging.g6_observation_cross_checked
        WHERE value_numeric <> ROUND(value_numeric, 1)
    ) THEN
        RAISE EXCEPTION
            'Final table contains values with more than one decimal place';
    END IF;


    IF EXISTS (
        SELECT 1

        FROM staging.g6_observation_cross_checked AS final

        LEFT JOIN staging.g6_observation_consensus AS consensus
            USING (g6_observation_consensus_id)

        WHERE consensus.g6_observation_consensus_id IS NULL
    ) THEN
        RAISE EXCEPTION
            'Final table contains a row without a consensus source';
    END IF;

IF EXISTS (
    SELECT 1
    FROM staging.g6_observation_cross_checked
    WHERE adjustment_status = 'unknown'
) THEN
    RAISE EXCEPTION
        'Final table contains unknown adjustment-status observations';
END IF;


IF EXISTS (
    SELECT 1
    FROM staging.g6_observation_cross_checked
    WHERE value_numeric = 0
) THEN
    RAISE EXCEPTION
        'Final table contains zero placeholders';
END IF;

IF (
    SELECT COUNT(*)
    FROM staging.g6_observation_cross_checked
) <> 7087 THEN
    RAISE EXCEPTION
        'Expected 7,087 final cross-checked observations';
END IF;

-- diagnostic4.csv contains 30 automated replacements. Consensus row
-- 9785 has adjustment_status = 'unknown' and is removed above,
-- leaving 29 retained replacement flags in the accepted final table.
IF (
    SELECT COUNT(*)
    FROM staging.g6_observation_cross_checked
    WHERE cross_checked_value_replaced
) <> 29 THEN
    RAISE EXCEPTION
        'Expected 29 retained automated cross-check replacements';
END IF;

IF EXISTS (
    SELECT 1
    FROM staging.g6_observation_cross_checked AS x
    JOIN staging.g6_deposit_category_definition AS d
      ON d.category_definition_id = x.category_definition_id
    WHERE NOT d.is_separately_reported
) THEN
    RAISE EXCEPTION
        'Final table contains a non-separately-reported category';
END IF;
IF EXISTS (
    SELECT 1
    FROM staging.g6_observation_cross_checked
    WHERE manually_adjusted
) THEN
    RAISE EXCEPTION
        'Automated cross-check population unexpectedly created manually adjusted rows';
END IF;
END
$$;
COMMIT;
