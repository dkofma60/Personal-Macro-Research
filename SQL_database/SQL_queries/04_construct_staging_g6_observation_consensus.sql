-- Construct staging.g6_observation_consensus

BEGIN;

-- ============================================================
-- 1. Create consensus table
-- ============================================================

CREATE TABLE staging.g6_observation_consensus (
    g6_observation_consensus_id
        smallint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    -- Economic-observation key
    observation_date              date NOT NULL,
    measure_canonical             text NOT NULL,
    adjustment_status             text NOT NULL,
    category_definition_id        smallint NOT NULL,
    geography_canonical           text,
    customer_type_canonical       text,
    unit_id                       smallint NOT NULL,

    -- Selected consensus result
    value_numeric                 numeric,
    value_status                  text NOT NULL,
    consensus_method              text NOT NULL,

    -- Potentially authoritative candidate-set summary
    potentially_authoritative_cell_count
                                  smallint NOT NULL,

    selected_value_support_count  smallint NOT NULL,

    distinct_potentially_authoritative_cell_count
                                  smallint NOT NULL,

    -- Null when neither calculation-method break affects the group
    revision_cutoff_date          date,

    created_at                    timestamptz NOT NULL
                                  DEFAULT current_timestamp,

    CONSTRAINT fk_g6_consensus_definition
        FOREIGN KEY (category_definition_id)
        REFERENCES staging.g6_deposit_category_definition (
            category_definition_id
        )
        ON DELETE RESTRICT,

    CONSTRAINT fk_g6_consensus_unit_measure
        FOREIGN KEY (
            unit_id,
            measure_canonical
        )
        REFERENCES staging.g6_unit_dimension (
            unit_id,
            measure_canonical
        )
        ON DELETE RESTRICT,

    CONSTRAINT uq_g6_consensus_economic_observation
        UNIQUE NULLS NOT DISTINCT (
            observation_date,
            measure_canonical,
            adjustment_status,
            category_definition_id,
            geography_canonical,
            customer_type_canonical,
            unit_id
        ),

    CONSTRAINT ck_g6_consensus_measure
        CHECK (
            measure_canonical IN (
                'debits',
                'average_deposits',
                'turnover'
            )
        ),

    CONSTRAINT ck_g6_consensus_adjustment
        CHECK (
            adjustment_status IN (
                'SA',
                'NSA',
                'unknown'
            )
        ),

    CONSTRAINT ck_g6_consensus_value_status
        CHECK (
            value_status IN (
                'reported',
                'not_available',
                'blank',
                'extraction_error'
            )
        ),

    CONSTRAINT ck_g6_consensus_value_consistency
        CHECK (
            (
                value_status = 'reported'
                AND value_numeric IS NOT NULL
            )
            OR
            (
                value_status IN (
                    'not_available',
                    'blank',
                    'extraction_error'
                )
                AND value_numeric IS NULL
            )
        ),

    CONSTRAINT ck_g6_consensus_method
        CHECK (
            consensus_method IN (
                'singleton',
                'unanimous',
                'plurality',
                'other_tiebreaking_support'
            )
        ),

    CONSTRAINT ck_g6_consensus_revision_cutoff
        CHECK (
            revision_cutoff_date IS NULL
            OR revision_cutoff_date IN (
                DATE '1982-10-14',
                DATE '1991-02-19'
            )
        ),

    CONSTRAINT ck_g6_consensus_counts
        CHECK (
            potentially_authoritative_cell_count > 0
            AND selected_value_support_count > 0
            AND selected_value_support_count
                <= potentially_authoritative_cell_count
            AND distinct_potentially_authoritative_cell_count > 0
        )
);

COMMENT ON TABLE staging.g6_observation_consensus IS
    'One row per economically distinct G.6 observation after excluding superseded source documents, respecting category-definition versions and calculation-method revision regimes, and reconciling repeated physical observations.';

COMMENT ON COLUMN
    staging.g6_observation_consensus.revision_cutoff_date
IS
    'When populated, preferred-document observations from releases before this calculation-method break were excluded from the potentially authoritative candidate set.';
-- 2. Supporting indexes
-- ============================================================
CREATE INDEX ix_dates_per_measure_type_efficent
    ON staging.g6_observation_consensus (
        unit_id,
        category_definition_id,
        geography_canonical,
        customer_type_canonical,
        adjustment_status,
        observation_date
    );
COMMIT;
