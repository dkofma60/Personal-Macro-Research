-- Construct core schema

BEGIN;

CREATE SCHEMA core;

CREATE TABLE core.measure_definitions (
    measure_id             smallint PRIMARY KEY,
    measure_code           text NOT NULL UNIQUE,
    unit_code              text NOT NULL UNIQUE,
    quantity_kind          text NOT NULL,
    currency_code          text NOT NULL,
    scale_to_base_unit     numeric NOT NULL,
    annualization_basis    text NOT NULL,
    display_label          text NOT NULL,

    CONSTRAINT fk_core_measure_source
        FOREIGN KEY (measure_id, measure_code)
        REFERENCES staging.g6_unit_dimension (unit_id, measure_canonical)
        ON DELETE RESTRICT,

    CONSTRAINT ck_core_measure_code
        CHECK (measure_code IN ('debits', 'average_deposits', 'turnover')),
    CONSTRAINT ck_core_measure_currency
        CHECK (currency_code IN ('USD', 'not_applicable')),
    CONSTRAINT ck_core_measure_scale
        CHECK (scale_to_base_unit > 0)
);

COMMENT ON TABLE core.measure_definitions IS
'Core measure and unit definitions. Measure and unit are one-to-one in G.6, so the fact needs only measure_id.';


CREATE TABLE core.non_demand_variant_definitions (
    non_demand_variant_id              smallint PRIMARY KEY,
    variant_code                       text NOT NULL UNIQUE,

    source_category_definition_id      smallint,
    source_customer_type_canonical     text,
    deNULLed_customer_type_canonical                text NOT NULL,

    definition_code                    text NOT NULL,
    definition_version                 smallint NOT NULL,
    includes_mmda                      boolean NOT NULL,
    includes_telephone_or_preauthorized_transfers
                                        boolean NOT NULL,
    definition_description             text NOT NULL,

    introduced_in_era_id               smallint,
    last_applicable_era_id             smallint,

    CONSTRAINT fk_core_variant_source_definition
        FOREIGN KEY (source_category_definition_id)
        REFERENCES staging.g6_deposit_category_definition (category_definition_id)
        ON DELETE RESTRICT,
    CONSTRAINT fk_core_variant_first_era
        FOREIGN KEY (introduced_in_era_id)
        REFERENCES raw.g6_era (era_id)
        ON DELETE RESTRICT,
    CONSTRAINT fk_core_variant_last_era
        FOREIGN KEY (last_applicable_era_id)
        REFERENCES raw.g6_era (era_id)
        ON DELETE RESTRICT,

    CONSTRAINT uq_core_variant_source_combination
        UNIQUE NULLS NOT DISTINCT (
            source_category_definition_id,
            source_customer_type_canonical
        ),

    CONSTRAINT ck_core_variant_customer_scope
        CHECK (
            deNULLed_customer_type_canonical IN (
                'business', 'other', 'total', 'ats_now', 'not_applicable'
            )
            AND (
                (source_customer_type_canonical IS NULL
                 AND deNULLed_customer_type_canonical = 'not_applicable')
                OR (
                    source_customer_type_canonical IS NOT NULL
                    AND source_customer_type_canonical = deNULLed_customer_type_canonical
                    AND deNULLed_customer_type_canonical <> 'not_applicable'
                )
            )
        ),

    CONSTRAINT ck_core_variant_era_order
        CHECK (
            introduced_in_era_id IS NULL
            OR last_applicable_era_id IS NULL
            OR introduced_in_era_id <= last_applicable_era_id
        ),
    CONSTRAINT ck_core_variant_shape
        CHECK (
            (
                non_demand_variant_id = 0
                AND variant_code = 'not_applicable'
                AND source_category_definition_id IS NULL
                AND definition_version = 0
                AND introduced_in_era_id IS NULL
                AND last_applicable_era_id IS NULL
            )
            OR
            (
                non_demand_variant_id > 0
                AND source_category_definition_id IS NOT NULL
                AND definition_version > 0
                AND introduced_in_era_id IS NOT NULL
                AND last_applicable_era_id IS NOT NULL
            )
        )
);

COMMENT ON TABLE core.non_demand_variant_definitions IS
'One member per observed non-demand category-definition/customer combination. Member 0 is the explicit not-applicable member used by demand facts.';

COMMENT ON COLUMN core.non_demand_variant_definitions.introduced_in_era_id IS
'Release era in which this exact presentation was introduced. It is not the era of every observation, because revised releases contain backdata.';


CREATE TABLE core.g6_observation (
    g6_observation_cross_checked_id    smallint PRIMARY KEY,
    observation_date              date NOT NULL,
    measure_id                    smallint NOT NULL,
    is_demand_deposit             boolean NOT NULL,
    demand_deposit_geography      text NOT NULL,
    non_demand_variant_id         smallint NOT NULL,
    seasonally_adjusted           boolean NOT NULL,
    value_numeric                 numeric(14,1) NOT NULL,
    manually_adjusted             boolean NOT NULL DEFAULT false,
    loaded_at                     timestamptz NOT NULL DEFAULT current_timestamp,

    CONSTRAINT fk_core_observation_source
        FOREIGN KEY (g6_observation_cross_checked_id)
        REFERENCES staging.g6_observation_cross_checked (g6_observation_cross_checked_id)
        ON DELETE RESTRICT,
    CONSTRAINT fk_core_observation_measure
        FOREIGN KEY (measure_id)
        REFERENCES core.measure_definitions (measure_id)
        ON DELETE RESTRICT,
    CONSTRAINT fk_core_observation_variant
        FOREIGN KEY (non_demand_variant_id)
        REFERENCES core.non_demand_variant_definitions (non_demand_variant_id)
        ON DELETE RESTRICT,

    CONSTRAINT uq_core_observation_economic_grain
        UNIQUE (
            observation_date,
            is_demand_deposit,
            demand_deposit_geography,
            non_demand_variant_id,
            measure_id,
            seasonally_adjusted
        ),

    CONSTRAINT ck_core_observation_month
        CHECK (extract(day FROM observation_date) = 1),
    CONSTRAINT ck_core_observation_geography
        CHECK (
            demand_deposit_geography IN (
                'all_banks', 'new_york_city', 'other_banks', 'not_applicable'
            )
        ),
    CONSTRAINT ck_core_observation_deposit_shape
        CHECK (
            (
                is_demand_deposit
                AND demand_deposit_geography IN (
                    'all_banks', 'new_york_city', 'other_banks'
                )
                AND non_demand_variant_id = 0
            )
            OR
            (
                NOT is_demand_deposit
                AND demand_deposit_geography = 'not_applicable'
                AND non_demand_variant_id <> 0
            )
        ),
    CONSTRAINT ck_core_observation_positive
        CHECK (value_numeric > 0),
    CONSTRAINT ck_core_observation_one_decimal
        CHECK (value_numeric = round(value_numeric, 1))
);

COMMENT ON TABLE core.g6_observation IS
'Authoritative numeric G.6 facts at monthly economic-observation grain. The primary key is also the direct one-to-one lineage key to final staging.';

COMMENT ON COLUMN core.g6_observation.demand_deposit_geography IS
'Demand geography; explicit not_applicable for every non-demand fact.';

COMMENT ON COLUMN core.g6_observation.non_demand_variant_id IS
'Collapsed non-demand definition/customer variant; member 0 means not_applicable for demand facts.';

CREATE INDEX ix_core_g6_observation_series_date
    ON core.g6_observation (
        measure_id,
        seasonally_adjusted,
        is_demand_deposit,
        demand_deposit_geography,
        non_demand_variant_id,
        observation_date
    );

COMMIT;
