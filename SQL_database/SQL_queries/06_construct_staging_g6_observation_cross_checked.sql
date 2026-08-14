-- Construct staging.g6_observation_cross_checked

BEGIN;


-- ============================================================
-- 1. Final staging table
-- ============================================================

CREATE TABLE staging.g6_observation_cross_checked (
    g6_observation_cross_checked_id
        smallint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    g6_observation_consensus_id
        smallint NOT NULL UNIQUE,

    observation_date          date NOT NULL,
    measure_canonical         text NOT NULL,
    adjustment_status         text NOT NULL,
    category_definition_id    smallint NOT NULL,
    geography_canonical       text,
    customer_type_canonical   text,
    unit_id                   smallint NOT NULL,

    value_numeric             numeric NOT NULL,

    cross_checked_value_replaced
        boolean NOT NULL DEFAULT false,

manually_adjusted
    boolean NOT NULL DEFAULT false,

    created_at                timestamptz NOT NULL
                              DEFAULT current_timestamp,

    CONSTRAINT fk_g6_crosscheck_consensus
        FOREIGN KEY (g6_observation_consensus_id)
        REFERENCES staging.g6_observation_consensus (
            g6_observation_consensus_id
        )
        ON DELETE RESTRICT,

    CONSTRAINT fk_g6_crosscheck_definition
        FOREIGN KEY (category_definition_id)
        REFERENCES staging.g6_deposit_category_definition (
            category_definition_id
        )
        ON DELETE RESTRICT,

    CONSTRAINT fk_g6_crosscheck_unit_measure
        FOREIGN KEY (
            unit_id,
            measure_canonical
        )
        REFERENCES staging.g6_unit_dimension (
            unit_id,
            measure_canonical
        )
        ON DELETE RESTRICT,

    CONSTRAINT uq_g6_crosscheck_economic_observation
        UNIQUE NULLS NOT DISTINCT (
            observation_date,
            measure_canonical,
            adjustment_status,
            category_definition_id,
            geography_canonical,
            customer_type_canonical,
            unit_id
        ),

    CONSTRAINT ck_g6_crosscheck_measure
        CHECK (
            measure_canonical IN (
                'debits',
                'average_deposits',
                'turnover'
            )
        ),

    CONSTRAINT ck_g6_crosscheck_adjustment
        CHECK (
            adjustment_status IN (
                'SA',
                'NSA',
                'unknown'
            )
        ),

    CONSTRAINT ck_g6_crosscheck_one_decimal
        CHECK (
            value_numeric = ROUND(value_numeric, 1)
        )
);
-- 2. Analysis index
-- ============================================================

CREATE INDEX ix_g6_crosscheck_dates_per_measure_type
    ON staging.g6_observation_cross_checked (
        unit_id,
        category_definition_id,
        geography_canonical,
        customer_type_canonical,
        adjustment_status,
        observation_date
    );
COMMIT;
