-- Validate core schema

DO $$
DECLARE
    v_complete_triplets bigint;
    v_bad_triplets      bigint;
    v_complete_geo      bigint;
    v_bad_geo           bigint;
BEGIN
    IF (SELECT count(*) FROM core.g6_observation) <> 7087 THEN
        RAISE EXCEPTION 'Core fact count is not 7,087';
    END IF;

    IF (SELECT count(*) FROM staging.g6_observation_cross_checked) <> 7087 THEN
        RAISE EXCEPTION 'Final staging count is not 7,087';
    END IF;

    IF EXISTS (
        SELECT 1
        FROM staging.g6_observation_cross_checked AS x
        FULL JOIN core.g6_observation AS o
          USING (g6_observation_cross_checked_id)
        WHERE x.g6_observation_cross_checked_id IS NULL
           OR o.g6_observation_cross_checked_id IS NULL
    ) THEN
        RAISE EXCEPTION 'Core/final-staging lineage is not one-to-one';
    END IF;

    IF (SELECT count(*) FROM core.g6_observation WHERE manually_adjusted) <> 2
       OR NOT EXISTS (
           SELECT 1
           FROM core.g6_observation AS o
           JOIN staging.g6_observation_cross_checked AS x
             USING (g6_observation_cross_checked_id)
           WHERE x.g6_observation_consensus_id = 8254
             AND o.manually_adjusted
       )
       OR NOT EXISTS (
           SELECT 1
           FROM core.g6_observation AS o
           JOIN staging.g6_observation_cross_checked AS x
             USING (g6_observation_cross_checked_id)
           WHERE x.g6_observation_consensus_id = 15228
             AND o.manually_adjusted
       ) THEN
        RAISE EXCEPTION 'The two expected manual adjustments are not preserved';
    END IF;

    IF (SELECT min(observation_date) FROM core.g6_observation)
           <> DATE '1976-08-01'
       OR (SELECT max(observation_date) FROM core.g6_observation)
           <> DATE '1996-08-01' THEN
        RAISE EXCEPTION 'Unexpected core observation-date range';
    END IF;

    IF EXISTS (
        SELECT 1
        FROM core.g6_observation
        WHERE value_numeric <= 0
           OR value_numeric <> round(value_numeric, 1)
    ) THEN
        RAISE EXCEPTION 'Core contains a nonpositive or non-one-decimal value';
    END IF;

    IF (SELECT count(*) FROM core.g6_direct_series_catalog) <> 69 THEN
        RAISE EXCEPTION 'Expected 69 direct economic series';
    END IF;

    -- Rounding-aware turnover = debits / average deposits.
    WITH triplets AS (
        SELECT
            o.observation_date,
            o.is_demand_deposit,
            o.demand_deposit_geography,
            o.non_demand_variant_id,
            o.seasonally_adjusted,
            max(o.value_numeric) FILTER (WHERE m.measure_code = 'debits')
                AS debits,
            max(o.value_numeric) FILTER (
                WHERE m.measure_code = 'average_deposits'
            ) AS average_deposits,
            max(o.value_numeric) FILTER (WHERE m.measure_code = 'turnover')
                AS turnover
        FROM core.g6_observation AS o
        JOIN core.measure_definitions AS m
          USING (measure_id)
        GROUP BY
            o.observation_date,
            o.is_demand_deposit,
            o.demand_deposit_geography,
            o.non_demand_variant_id,
            o.seasonally_adjusted
    )
    SELECT
        count(*) FILTER (
            WHERE debits IS NOT NULL
              AND average_deposits IS NOT NULL
              AND turnover IS NOT NULL
        ),
        count(*) FILTER (
            WHERE debits IS NOT NULL
              AND average_deposits IS NOT NULL
              AND turnover IS NOT NULL
              AND (
                  (debits + 0.05) / (average_deposits - 0.05)
                      < turnover - 0.05
                  OR
                  (debits - 0.05) / (average_deposits + 0.05)
                      > turnover + 0.05
              )
        )
    INTO v_complete_triplets, v_bad_triplets
    FROM triplets;

    IF v_complete_triplets <> 2326 OR v_bad_triplets <> 0 THEN
        RAISE EXCEPTION
            'Turnover QA failed: % complete triplets, % violations',
            v_complete_triplets,
            v_bad_triplets;
    END IF;

    -- Demand geography is additive only for debits and average deposits.
    WITH geography_groups AS (
        SELECT
            o.observation_date,
            o.measure_id,
            o.seasonally_adjusted,
            max(o.value_numeric) FILTER (
                WHERE o.demand_deposit_geography = 'all_banks'
            ) AS all_banks,
            max(o.value_numeric) FILTER (
                WHERE o.demand_deposit_geography = 'new_york_city'
            ) AS new_york_city,
            max(o.value_numeric) FILTER (
                WHERE o.demand_deposit_geography = 'other_banks'
            ) AS other_banks
        FROM core.g6_observation AS o
        JOIN core.measure_definitions AS m
          USING (measure_id)
        WHERE o.is_demand_deposit
          AND m.measure_code IN ('debits', 'average_deposits')
        GROUP BY o.observation_date, o.measure_id, o.seasonally_adjusted
    )
    SELECT
        count(*) FILTER (
            WHERE all_banks IS NOT NULL
              AND new_york_city IS NOT NULL
              AND other_banks IS NOT NULL
        ),
        count(*) FILTER (
            WHERE all_banks IS NOT NULL
              AND new_york_city IS NOT NULL
              AND other_banks IS NOT NULL
              AND abs(all_banks - new_york_city - other_banks) > 0.1
        )
    INTO v_complete_geo, v_bad_geo
    FROM geography_groups;

    IF v_complete_geo <> 778 OR v_bad_geo <> 0 THEN
        RAISE EXCEPTION
            'Geography QA failed: % complete groups, % violations',
            v_complete_geo,
            v_bad_geo;
    END IF;

    IF (SELECT count(*) FROM core.continuous_sa_demand_turnover) <> 723
       OR EXISTS (
           SELECT 1
           FROM core.continuous_sa_demand_turnover
           GROUP BY demand_deposit_geography
           HAVING count(*) <> 241
              OR min(observation_date) <> DATE '1976-08-01'
              OR max(observation_date) <> DATE '1996-08-01'
       ) THEN
        RAISE EXCEPTION 'SA demand turnover continuity failed';
    END IF;

    IF (SELECT count(*) FROM core.continuous_nsa_savings_turnover) <> 170
       OR (SELECT min(observation_date)
           FROM core.continuous_nsa_savings_turnover) <> DATE '1977-07-01'
       OR (SELECT max(observation_date)
           FROM core.continuous_nsa_savings_turnover) <> DATE '1991-08-01'
       OR EXISTS (
           SELECT observation_date
           FROM core.continuous_nsa_savings_turnover
           GROUP BY observation_date
           HAVING count(*) <> 1
       ) THEN
        RAISE EXCEPTION 'NSA savings turnover continuity failed';
    END IF;

    IF (SELECT count(*)
        FROM core.continuous_nsa_narrow_other_checkable_turnover) <> 181
       OR (SELECT min(observation_date)
           FROM core.continuous_nsa_narrow_other_checkable_turnover)
           <> DATE '1978-12-01'
       OR (SELECT max(observation_date)
           FROM core.continuous_nsa_narrow_other_checkable_turnover)
           <> DATE '1993-12-01'
       OR EXISTS (
           SELECT observation_date
           FROM core.continuous_nsa_narrow_other_checkable_turnover
           GROUP BY observation_date
           HAVING count(*) <> 1
       ) THEN
        RAISE EXCEPTION 'NSA narrow-other-checkable turnover continuity failed';
    END IF;

    IF EXISTS (
        SELECT month_start::date
        FROM generate_series(
            DATE '1977-07-01', DATE '1991-08-01', INTERVAL '1 month'
        ) AS months(month_start)
        EXCEPT
        SELECT observation_date
        FROM core.continuous_nsa_savings_turnover
    ) OR EXISTS (
        SELECT month_start::date
        FROM generate_series(
            DATE '1978-12-01', DATE '1993-12-01', INTERVAL '1 month'
        ) AS months(month_start)
        EXCEPT
        SELECT observation_date
        FROM core.continuous_nsa_narrow_other_checkable_turnover
    ) THEN
        RAISE EXCEPTION 'A requested continuous view contains a monthly gap';
    END IF;
END
$$;


-- Human-readable completion summary.
SELECT 'core facts' AS check_name, count(*)::bigint AS result
FROM core.g6_observation
UNION ALL
SELECT 'direct series', count(*)
FROM core.g6_direct_series_catalog
UNION ALL
SELECT 'SA demand turnover rows', count(*)
FROM core.continuous_sa_demand_turnover
UNION ALL
SELECT 'NSA savings turnover rows', count(*)
FROM core.continuous_nsa_savings_turnover
UNION ALL
SELECT 'NSA narrow other-checkable turnover rows', count(*)
FROM core.continuous_nsa_narrow_other_checkable_turnover;
