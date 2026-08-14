-- Populate core schema

BEGIN;

INSERT INTO core.measure_definitions (
    measure_id,
    measure_code,
    unit_code,
    quantity_kind,
    currency_code,
    scale_to_base_unit,
    annualization_basis,
    display_label
)
SELECT
    unit_id,
    measure_canonical,
    unit_code,
    quantity_kind,
    coalesce(currency_code::text, 'not_applicable'),
    scale_to_base_unit,
    annualization_basis,
    display_label
FROM staging.g6_unit_dimension;


-- Explicit not-applicable member for demand facts.
INSERT INTO core.non_demand_variant_definitions (
    non_demand_variant_id,
    variant_code,
    source_category_definition_id,
    source_customer_type_canonical,
    deNULLed_customer_type_canonical,
    definition_code,
    definition_version,
    includes_mmda,
    includes_telephone_or_preauthorized_transfers,
    definition_description,
    introduced_in_era_id,
    last_applicable_era_id
)
VALUES (
    0,
    'not_applicable',
    NULL,
    NULL,
    'not_applicable',
    'not_applicable',
    0,
    false,
    false,
    'Not applicable because the observation is for demand deposits.',
    NULL,
    NULL
);


-- These 12 members are the exact category-definition/customer combinations
-- present in accepted non-demand numeric facts. Era IDs describe the release
-- presentation, not the observation month; later-era releases contain backdata.
WITH variant_map (
    non_demand_variant_id,
    variant_code,
    definition_code,
    source_customer_type_canonical,
    deNULLed_customer_type_canonical,
    introduced_in_era_id,
    last_applicable_era_id
) AS (
    VALUES
        (1,  'savings_pre_ats_now_v1__business',
             'savings_pre_ats_now_v1', 'business', 'business', 1, 1),
        (2,  'savings_pre_ats_now_v1__other',
             'savings_pre_ats_now_v1', 'other', 'other', 1, 1),
        (3,  'savings_pre_ats_now_v1__total',
             'savings_pre_ats_now_v1', 'total', 'total', 1, 1),

        (4,  'savings_including_ats_now_v2__business',
             'savings_including_ats_now_v2', 'business', 'business', 2, 2),
        (5,  'savings_including_ats_now_v2__other',
             'savings_including_ats_now_v2', 'other', 'other', 2, 2),
        (6,  'savings_including_ats_now_v2__total',
             'savings_including_ats_now_v2', 'total', 'total', 2, 2),

        (7,  'savings_excluding_ats_now_and_mmda_v3__not_applicable',
             'savings_excluding_ats_now_and_mmda_v3', NULL, 'not_applicable', 3, 6),
        (8,  'savings_including_mmda_v4__not_applicable',
             'savings_including_mmda_v4', NULL, 'not_applicable', 6, 8),

        (9,  'other_checkable_narrow_v1__ats_now',
             'other_checkable_narrow_v1', 'ats_now', 'ats_now', 2, 2),
        (10, 'other_checkable_narrow_v1__not_applicable',
             'other_checkable_narrow_v1', NULL, 'not_applicable', 3, 7),
        (11, 'other_checkable_expanded_v2__not_applicable',
             'other_checkable_expanded_v2', NULL, 'not_applicable', 8, 8),

        (12, 'mmda_separately_reported_v1__not_applicable',
             'mmda_separately_reported_v1', NULL, 'not_applicable', 4, 6)
)
INSERT INTO core.non_demand_variant_definitions (
    non_demand_variant_id,
    variant_code,
    source_category_definition_id,
    source_customer_type_canonical,
    deNULLed_customer_type_canonical,
    definition_code,
    definition_version,
    includes_mmda,
    includes_telephone_or_preauthorized_transfers,
    definition_description,
    introduced_in_era_id,
    last_applicable_era_id
)
SELECT
    v.non_demand_variant_id,
    v.variant_code,
    d.category_definition_id,
    v.source_customer_type_canonical,
    v.deNULLed_customer_type_canonical,
    d.definition_code,
    d.definition_version,
    d.includes_mmda,
    d.includes_telephone_or_preauthorized_transfers,
    d.definition_description,
    v.introduced_in_era_id,
    v.last_applicable_era_id
FROM variant_map AS v
JOIN staging.g6_deposit_category_definition AS d
  USING (definition_code);


-- Fail before loading facts if final staging is not in the accepted state.
DO $$
BEGIN
    IF (SELECT count(*) FROM core.measure_definitions) <> 3 THEN
        RAISE EXCEPTION 'Expected exactly three measure definitions';
    END IF;

    IF (SELECT count(*) FROM core.non_demand_variant_definitions) <> 13 THEN
        RAISE EXCEPTION 'Expected 12 real non-demand variants plus member 0';
    END IF;

    IF (SELECT count(*) FROM staging.g6_observation_cross_checked) <> 7087 THEN
        RAISE EXCEPTION
            'Expected 7,087 final staging rows after removal of invalid consensus row 13788';
    END IF;

    IF EXISTS (
        SELECT 1
        FROM staging.g6_observation_cross_checked
        WHERE value_numeric IS NULL
           OR value_numeric <= 0
           OR value_numeric <> round(value_numeric, 1)
           OR adjustment_status NOT IN ('SA', 'NSA')
           OR extract(day FROM observation_date) <> 1
    ) THEN
        RAISE EXCEPTION 'Final staging contains an invalid value, status, or date';
    END IF;

    IF EXISTS (
        SELECT 1
        FROM staging.g6_observation_cross_checked AS x
        JOIN staging.g6_deposit_category_definition AS d
          USING (category_definition_id)
        WHERE NOT (
            d.concept_family_code = 'demand'
            AND x.geography_canonical IN (
                'all_banks', 'new_york_city', 'other_banks'
            )
            AND x.customer_type_canonical IS NULL
        )
        AND NOT (
            d.concept_family_code <> 'demand'
            AND x.geography_canonical IS NULL
        )
    ) THEN
        RAISE EXCEPTION 'A source row has invalid demand/non-demand applicability';
    END IF;

    IF EXISTS (
        SELECT 1
        FROM staging.g6_observation_cross_checked AS x
        LEFT JOIN core.measure_definitions AS m
          ON m.measure_id = x.unit_id
         AND m.measure_code = x.measure_canonical
        WHERE m.measure_id IS NULL
    ) THEN
        RAISE EXCEPTION 'A source measure/unit pair is unmapped';
    END IF;

    IF EXISTS (
        SELECT 1
        FROM staging.g6_observation_cross_checked AS x
        JOIN staging.g6_deposit_category_definition AS d
          USING (category_definition_id)
        LEFT JOIN core.non_demand_variant_definitions AS v
          ON v.source_category_definition_id = x.category_definition_id
         AND v.source_customer_type_canonical
             IS NOT DISTINCT FROM x.customer_type_canonical
        WHERE d.concept_family_code <> 'demand'
          AND v.non_demand_variant_id IS NULL
    ) THEN
        RAISE EXCEPTION 'A non-demand category/customer combination is unmapped';
    END IF;
END
$$;


INSERT INTO core.g6_observation (
    g6_observation_cross_checked_id,
    observation_date,
    measure_id,
    is_demand_deposit,
    demand_deposit_geography,
    non_demand_variant_id,
    seasonally_adjusted,
    value_numeric,
    manually_adjusted
)
SELECT
    x.g6_observation_cross_checked_id,
    x.observation_date,
    x.unit_id,
    d.concept_family_code = 'demand',
    CASE
        WHEN d.concept_family_code = 'demand' THEN x.geography_canonical
        ELSE 'not_applicable'
    END,
    CASE
        WHEN d.concept_family_code = 'demand' THEN 0
        ELSE v.non_demand_variant_id
    END,
    x.adjustment_status = 'SA',
    x.value_numeric,
    x.manually_adjusted
FROM staging.g6_observation_cross_checked AS x
JOIN staging.g6_deposit_category_definition AS d
  USING (category_definition_id)
LEFT JOIN core.non_demand_variant_definitions AS v
  ON v.source_category_definition_id = x.category_definition_id
 AND v.source_customer_type_canonical
     IS NOT DISTINCT FROM x.customer_type_canonical;


DO $$
BEGIN
    IF (SELECT count(*) FROM core.g6_observation) <> 7087 THEN
        RAISE EXCEPTION 'Expected 7,087 core facts';
    END IF;

    IF (SELECT count(*) FROM core.g6_observation WHERE manually_adjusted) <> 2 THEN
        RAISE EXCEPTION 'Expected exactly two manually adjusted core facts';
    END IF;

    IF EXISTS (
        SELECT 1
        FROM staging.g6_observation_cross_checked AS x
        FULL JOIN core.g6_observation AS o
          USING (g6_observation_cross_checked_id)
        WHERE x.g6_observation_cross_checked_id IS NULL
           OR o.g6_observation_cross_checked_id IS NULL
           OR o.observation_date <> x.observation_date
           OR o.measure_id <> x.unit_id
           OR o.seasonally_adjusted <> (x.adjustment_status = 'SA')
           OR o.value_numeric <> x.value_numeric
           OR o.manually_adjusted <> x.manually_adjusted
    ) THEN
        RAISE EXCEPTION 'Core does not reproduce final staging one-to-one';
    END IF;
END
$$;

COMMIT;
