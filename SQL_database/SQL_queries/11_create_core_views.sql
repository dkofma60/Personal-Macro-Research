-- Create core views

BEGIN;

-- Logical series partitioning without creating 69 duplicate physical tables.
CREATE VIEW core.g6_direct_series AS
SELECT
    CASE
        WHEN o.is_demand_deposit THEN
            'demand__' || o.demand_deposit_geography
        ELSE v.variant_code
    END
    || '__' || m.measure_code
    || '__' || CASE WHEN o.seasonally_adjusted THEN 'sa' ELSE 'nsa' END
        AS series_code,
    o.g6_observation_cross_checked_id,
    o.observation_date,
    o.measure_id,
    m.measure_code,
    o.is_demand_deposit,
    o.demand_deposit_geography,
    o.non_demand_variant_id,
    v.variant_code AS non_demand_variant_code,
    o.seasonally_adjusted,
    o.value_numeric,
    o.manually_adjusted
FROM core.g6_observation AS o
JOIN core.measure_definitions AS m
  USING (measure_id)
JOIN core.non_demand_variant_definitions AS v
  USING (non_demand_variant_id);

COMMENT ON VIEW core.g6_direct_series IS
'Direct accepted observations with a stable series code derived from the economic key. No facts are copied.';


CREATE VIEW core.g6_direct_series_catalog AS
SELECT
    series_code,
    measure_id,
    measure_code,
    is_demand_deposit,
    demand_deposit_geography,
    non_demand_variant_id,
    non_demand_variant_code,
    seasonally_adjusted,
    min(observation_date) AS first_observation_date,
    max(observation_date) AS last_observation_date,
    count(*)::integer AS observation_count
FROM core.g6_direct_series
GROUP BY
    series_code,
    measure_id,
    measure_code,
    is_demand_deposit,
    demand_deposit_geography,
    non_demand_variant_id,
    non_demand_variant_code,
    seasonally_adjusted;

COMMENT ON VIEW core.g6_direct_series_catalog IS
'One row per direct economic series, with coverage dates and observation count.';


-- Demand has one stable definition. This is one continuous view with geography
-- retained as a column; filtering yields the three requested 241-month series.
CREATE VIEW core.continuous_sa_demand_turnover AS
SELECT
    o.demand_deposit_geography,
    o.observation_date,
    o.value_numeric,
    o.g6_observation_cross_checked_id
        AS source_g6_observation_cross_checked_id,
    o.manually_adjusted
FROM core.g6_observation AS o
JOIN core.measure_definitions AS m
  USING (measure_id)
WHERE o.is_demand_deposit
  AND o.seasonally_adjusted
  AND m.measure_code = 'turnover';

COMMENT ON VIEW core.continuous_sa_demand_turnover IS
'Continuous August 1976-August 1996 seasonally adjusted demand-deposit turnover for all banks, New York City, and other banks.';


-- Harmonized savings definition: excludes ATS/NOW and separately reported MMDA.
-- Era 2 turnover is derived correctly from summed debits divided by summed
-- average deposits; turnover rates themselves must never be added.
CREATE VIEW core.continuous_nsa_savings_turnover AS
WITH era_1_direct AS (
    SELECT
        o.observation_date,
        o.value_numeric,
        ARRAY[o.g6_observation_cross_checked_id]::smallint[]
            AS source_g6_observation_cross_checked_ids,
        'era_1_published_total'::text AS continuity_segment,
        false AS is_derived
    FROM core.g6_observation AS o
    JOIN core.measure_definitions AS m
      USING (measure_id)
    JOIN core.non_demand_variant_definitions AS v
      USING (non_demand_variant_id)
    WHERE NOT o.seasonally_adjusted
      AND m.measure_code = 'turnover'
      AND v.variant_code = 'savings_pre_ats_now_v1__total'
      AND o.observation_date < DATE '1980-06-01'
),
era_2_derived AS (
    SELECT
        o.observation_date,
        round(
            sum(o.value_numeric) FILTER (WHERE m.measure_code = 'debits')
            /
            sum(o.value_numeric) FILTER (
                WHERE m.measure_code = 'average_deposits'
            ),
            1
        ) AS value_numeric,
        array_agg(o.g6_observation_cross_checked_id
                  ORDER BY o.g6_observation_cross_checked_id)::smallint[]
            AS source_g6_observation_cross_checked_ids,
        'era_2_business_plus_other'::text AS continuity_segment,
        true AS is_derived
    FROM core.g6_observation AS o
    JOIN core.measure_definitions AS m
      USING (measure_id)
    JOIN core.non_demand_variant_definitions AS v
      USING (non_demand_variant_id)
    WHERE NOT o.seasonally_adjusted
      AND m.measure_code IN ('debits', 'average_deposits')
      AND v.variant_code IN (
          'savings_including_ats_now_v2__business',
          'savings_including_ats_now_v2__other'
      )
      AND o.observation_date >= DATE '1980-06-01'
      AND o.observation_date <  DATE '1981-08-01'
    GROUP BY o.observation_date
    HAVING count(*) = 4
),
era_3_definition_direct AS (
    SELECT
        o.observation_date,
        o.value_numeric,
        ARRAY[o.g6_observation_cross_checked_id]::smallint[]
            AS source_g6_observation_cross_checked_ids,
        'era_3_definition_published_total'::text AS continuity_segment,
        false AS is_derived
    FROM core.g6_observation AS o
    JOIN core.measure_definitions AS m
      USING (measure_id)
    JOIN core.non_demand_variant_definitions AS v
      USING (non_demand_variant_id)
    WHERE NOT o.seasonally_adjusted
      AND m.measure_code = 'turnover'
      AND v.variant_code =
          'savings_excluding_ats_now_and_mmda_v3__not_applicable'
      AND o.observation_date >= DATE '1981-08-01'
)
SELECT * FROM era_1_direct
UNION ALL
SELECT * FROM era_2_derived
UNION ALL
SELECT * FROM era_3_definition_direct;

COMMENT ON VIEW core.continuous_nsa_savings_turnover IS
'Harmonized July 1977-August 1991 NSA savings turnover excluding ATS/NOW and separately reported MMDA. Revised era-3-definition backdata takes precedence from August 1981.';


-- The narrow ATS/NOW/other-checkable concept is continuous across its relabeling.
-- The expanded definition is deliberately excluded.
CREATE VIEW core.continuous_nsa_narrow_other_checkable_turnover AS
SELECT
    o.observation_date,
    o.value_numeric,
    o.g6_observation_cross_checked_id
        AS source_g6_observation_cross_checked_id,
    'era_2_ats_now'::text AS continuity_segment,
    o.manually_adjusted
FROM core.g6_observation AS o
JOIN core.measure_definitions AS m
  USING (measure_id)
JOIN core.non_demand_variant_definitions AS v
  USING (non_demand_variant_id)
WHERE NOT o.seasonally_adjusted
  AND m.measure_code = 'turnover'
  AND v.variant_code = 'other_checkable_narrow_v1__ats_now'
  AND o.observation_date < DATE '1981-08-01'

UNION ALL

SELECT
    o.observation_date,
    o.value_numeric,
    o.g6_observation_cross_checked_id
        AS source_g6_observation_cross_checked_id,
    'separately_reported_narrow_other_checkable'::text AS continuity_segment,
    o.manually_adjusted
FROM core.g6_observation AS o
JOIN core.measure_definitions AS m
  USING (measure_id)
JOIN core.non_demand_variant_definitions AS v
  USING (non_demand_variant_id)
WHERE NOT o.seasonally_adjusted
  AND m.measure_code = 'turnover'
  AND v.variant_code = 'other_checkable_narrow_v1__not_applicable'
  AND o.observation_date >= DATE '1981-08-01';

COMMENT ON VIEW core.continuous_nsa_narrow_other_checkable_turnover IS
'Continuous December 1978-December 1993 NSA ATS/NOW/narrow-other-checkable turnover. The expanded 1994 definition is excluded; revised backdata takes precedence from August 1981.';

COMMIT;
