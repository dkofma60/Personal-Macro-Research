-- Construct staging schema, reference tables, and parsed-observation tables

BEGIN;

CREATE SCHEMA staging;

-- ============================================================
-- 1. Python-preprocessed physical cells
-- ============================================================

CREATE TABLE staging.g6_parsed_observation_preprocessed (
    g6_cell_extraction_id
                            integer PRIMARY KEY,
    selected_candidate_order
                            integer,
    release_date            date NOT NULL,
    observation_date        date NOT NULL,
    observation_date_status text NOT NULL,
    measure_canonical       text NOT NULL,
    adjustment_status       text NOT NULL,
    deposit_type_canonical  text NOT NULL,
    geography_canonical     text,
    customer_type_canonical text,
    units_raw               text,
    value_numeric           numeric,
    value_status            text NOT NULL,
    validation_flags        jsonb NOT NULL DEFAULT '[]'::jsonb,
    cross_release_support_count
                            integer NOT NULL DEFAULT 0,
    created_at              timestamptz NOT NULL
                            DEFAULT current_timestamp,

    CONSTRAINT fk_preprocessed_raw_cell
        FOREIGN KEY (g6_cell_extraction_id)
        REFERENCES raw.g6_cell_extraction (
            g6_cell_extraction_id
        )
        ON DELETE RESTRICT,

    CONSTRAINT fk_preprocessed_selected_candidate
        FOREIGN KEY (
            g6_cell_extraction_id,
            selected_candidate_order
        )
        REFERENCES raw.g6_ocr_candidate (
            g6_cell_extraction_id,
            candidate_order
        )
        ON DELETE RESTRICT,

    CONSTRAINT ck_preprocessed_candidate_order
        CHECK (
            selected_candidate_order IS NULL
            OR selected_candidate_order >= 0
        ),

    CONSTRAINT ck_preprocessed_adjustment_status
        CHECK (adjustment_status IN ('SA', 'NSA', 'unknown')),

    CONSTRAINT ck_preprocessed_value_status
        CHECK (
            value_status IN (
                'reported',
                'not_available',
                'blank',
                'extraction_error'
            )
        ),

    CONSTRAINT ck_preprocessed_value_consistency
        CHECK (
            (
                value_status = 'reported'
                AND value_numeric IS NOT NULL
                AND selected_candidate_order IS NOT NULL
            )
            OR
            (
                value_status = 'not_available'
                AND value_numeric IS NULL
                AND selected_candidate_order IS NOT NULL
            )
            OR
            (
                value_status IN ('blank', 'extraction_error')
                AND value_numeric IS NULL
                AND selected_candidate_order IS NULL
            )
        ),

    CONSTRAINT ck_preprocessed_validation_flags
        CHECK (jsonb_typeof(validation_flags) = 'array'),

    CONSTRAINT ck_preprocessed_cross_release_support
        CHECK (cross_release_support_count >= 0)
);

COMMENT ON TABLE staging.g6_parsed_observation_preprocessed IS
'Analysis-facing representation of the Python-preprocessed G.6 physical cells. One row per raw.g6_cell_extraction row. Detailed physical, document, and OCR provenance remains in the raw schema.';

COMMENT ON COLUMN
    staging.g6_parsed_observation_preprocessed.g6_cell_extraction_id IS
'Primary key and one-to-one foreign key to the originating raw physical cell.';

COMMENT ON COLUMN
    staging.g6_parsed_observation_preprocessed.selected_candidate_order IS
'Candidate order of the OCR candidate selected by the Python pipeline; null for blank or extraction-error cells.';

COMMENT ON COLUMN
    staging.g6_parsed_observation_preprocessed.release_date IS
'Publication date of the source G.6 document. Materialized because release vintage is central to economic analysis.';

COMMENT ON COLUMN
    staging.g6_parsed_observation_preprocessed.units_raw IS
'Pipeline-extracted unit label retained for mapping to a controlled unit definition in the post-processed staging table.';


-- ============================================================
-- 2. Controlled economic units
-- ============================================================

CREATE TABLE staging.g6_unit_dimension (
    unit_id                smallint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    unit_code              text NOT NULL UNIQUE,
    measure_canonical      text NOT NULL,
    quantity_kind          text NOT NULL,
    currency_code          character(3),
    scale_to_base_unit     numeric NOT NULL,
    annualization_basis    text NOT NULL,
    display_label          text NOT NULL,

    CONSTRAINT uq_g6_unit_measure
        UNIQUE (unit_id, measure_canonical),

    CONSTRAINT ck_g6_unit_measure
        CHECK (
            measure_canonical IN (
                'debits',
                'average_deposits',
                'turnover'
            )
        ),

    CONSTRAINT ck_g6_unit_quantity_kind
        CHECK (
            quantity_kind IN (
                'currency_flow',
                'currency_stock',
                'frequency'
            )
        ),

    CONSTRAINT ck_g6_unit_annualization
        CHECK (
            annualization_basis IN (
                'annual_rate',
                'not_annualized',
                'per_year'
            )
        ),

    CONSTRAINT ck_g6_unit_scale
        CHECK (scale_to_base_unit > 0)
);

INSERT INTO staging.g6_unit_dimension (
    unit_code,
    measure_canonical,
    quantity_kind,
    currency_code,
    scale_to_base_unit,
    annualization_basis,
    display_label
)
VALUES
    (
        'usd_billions_annual_rate',
        'debits',
        'currency_flow',
        'USD',
        1000000000,
        'annual_rate',
        'Annual rate, billions of U.S. dollars'
    ),
    (
        'usd_billions',
        'average_deposits',
        'currency_stock',
        'USD',
        1000000000,
        'not_annualized',
        'Billions of U.S. dollars'
    ),
    (
        'times_per_year',
        'turnover',
        'frequency',
        NULL,
        1,
        'per_year',
        'Times per year'
    );


-- ============================================================
-- 3. Economically precise deposit-category definitions
-- ============================================================

CREATE TABLE staging.g6_deposit_category_definition (
    category_definition_id
        smallint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    definition_code         text NOT NULL UNIQUE,
    concept_family_code     text NOT NULL,
    definition_version      smallint NOT NULL,

    includes_mmda           boolean NOT NULL DEFAULT false,
    includes_telephone_or_preauthorized_transfers
                            boolean NOT NULL DEFAULT false,
    is_separately_reported  boolean NOT NULL DEFAULT true,

    definition_description  text NOT NULL,

    CONSTRAINT uq_g6_category_family_version
        UNIQUE (concept_family_code, definition_version),

    CONSTRAINT ck_g6_category_family
        CHECK (
            concept_family_code IN (
                'demand',
                'savings',
                'other_checkable',
                'mmda'
            )
        ),

    CONSTRAINT ck_g6_category_version
        CHECK (definition_version > 0)
);

INSERT INTO staging.g6_deposit_category_definition (
    definition_code,
    concept_family_code,
    definition_version,
    includes_mmda,
    includes_telephone_or_preauthorized_transfers,
    is_separately_reported,
    definition_description
)
VALUES
    (
        'demand_v1',
        'demand',
        1,
        false,
        false,
        true,
        'Demand deposits under the G.6 reporting framework.'
    ),
    (
        'savings_pre_ats_now_v1',
        'savings',
        1,
        false,
        false,
        true,
        'Savings deposits before the August 1980 ATS/NOW presentation; reported with business and other customer components.'
    ),
    (
        'savings_including_ats_now_v2',
        'savings',
        2,
        false,
        false,
        true,
        'Savings-deposit presentation from August 1980 through August 1982, including ATS/NOW accounts within the savings classification.'
    ),
    (
        'savings_excluding_ats_now_and_mmda_v3',
        'savings',
        3,
        false,
        false,
        true,
        'Savings deposits after the October 1982 reclassification; ATS/NOW is separate and MMDA is excluded when separately reported.'
    ),
    (
        'savings_including_mmda_v4',
        'savings',
        4,
        true,
        false,
        true,
        'Savings deposits beginning with September 1991 observations, including MMDA balances.'
    ),
    (
        'other_checkable_narrow_v1',
        'other_checkable',
        1,
        false,
        false,
        true,
        'ATS/NOW account concept, including the December 1992 relabeling to other checkable deposits without an intended conceptual change.'
    ),
    (
        'other_checkable_expanded_v2',
        'other_checkable',
        2,
        false,
        true,
        true,
        'Other checkable deposits after the March 1994 expansion to include telephone and preauthorized-transfer accounts.'
    ),
    (
        'mmda_separately_reported_v1',
        'mmda',
        1,
        false,
        false,
        true,
        'MMDA reported as a separate deposit category.'
    ),
    (
        'mmda_absorbed_into_savings_v2',
        'mmda',
        2,
        false,
        false,
        false,
        'MMDA no longer separately reported beginning with September 1991 observations because it is included in savings.'
    );


-- ============================================================
-- 4. Reproducible category-definition assignment rules
-- ============================================================

CREATE TABLE staging.g6_deposit_definition_rule (
    definition_rule_id
        smallint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    rule_code                  text NOT NULL UNIQUE,
    deposit_type_canonical     text NOT NULL,
    category_definition_id     smallint NOT NULL,

    release_date_from          date,
    release_date_to            date,
    observation_date_from      date,
    observation_date_to        date,

    rule_description           text NOT NULL,

    CONSTRAINT fk_g6_definition_rule_definition
        FOREIGN KEY (category_definition_id)
        REFERENCES staging.g6_deposit_category_definition (
            category_definition_id
        )
        ON DELETE RESTRICT,

    CONSTRAINT uq_g6_definition_rule_mapping
        UNIQUE (
            definition_rule_id,
            category_definition_id
        ),

    CONSTRAINT ck_g6_definition_rule_deposit_type
        CHECK (
            deposit_type_canonical IN (
                'demand',
                'savings',
                'ats_now',
                'mmda',
                'other_checkable'
            )
        ),

    CONSTRAINT ck_g6_definition_rule_release_range
        CHECK (
            release_date_from IS NULL
            OR release_date_to IS NULL
            OR release_date_from <= release_date_to
        ),

    CONSTRAINT ck_g6_definition_rule_observation_range
        CHECK (
            observation_date_from IS NULL
            OR observation_date_to IS NULL
            OR observation_date_from <= observation_date_to
        )
);


-- Demand: stable category scope
INSERT INTO staging.g6_deposit_definition_rule (
    rule_code,
    deposit_type_canonical,
    category_definition_id,
    rule_description
)
SELECT
    'demand_all_releases',
    'demand',
    category_definition_id,
    'Assign the stable demand-deposit definition.'
FROM staging.g6_deposit_category_definition
WHERE definition_code = 'demand_v1';


-- Savings before ATS/NOW presentation
INSERT INTO staging.g6_deposit_definition_rule (
    rule_code,
    deposit_type_canonical,
    category_definition_id,
    release_date_to,
    rule_description
)
SELECT
    'savings_before_1980_08',
    'savings',
    category_definition_id,
    DATE '1980-07-09',
    'Savings definition used through the final release of era 1.'
FROM staging.g6_deposit_category_definition
WHERE definition_code = 'savings_pre_ats_now_v1';


-- Savings during ATS/NOW-as-savings era
INSERT INTO staging.g6_deposit_definition_rule (
    rule_code,
    deposit_type_canonical,
    category_definition_id,
    release_date_from,
    release_date_to,
    rule_description
)
SELECT
    'savings_1980_08_through_1982_08',
    'savings',
    category_definition_id,
    DATE '1980-08-14',
    DATE '1982-08-04',
    'Savings definition during the period in which ATS/NOW was classified within savings.'
FROM staging.g6_deposit_category_definition
WHERE definition_code = 'savings_including_ats_now_v2';


-- Savings after ATS/NOW separation but before MMDA inclusion
INSERT INTO staging.g6_deposit_definition_rule (
    rule_code,
    deposit_type_canonical,
    category_definition_id,
    release_date_from,
    observation_date_to,
    rule_description
)
SELECT
    'savings_post_1982_pre_mmda_inclusion',
    'savings',
    category_definition_id,
    DATE '1982-10-14',
    DATE '1991-08-01',
    'Savings excluding ATS/NOW and separately reported MMDA.'
FROM staging.g6_deposit_category_definition
WHERE definition_code = 'savings_excluding_ats_now_and_mmda_v3';


-- Savings beginning with September 1991 observations
INSERT INTO staging.g6_deposit_definition_rule (
    rule_code,
    deposit_type_canonical,
    category_definition_id,
    release_date_from,
    observation_date_from,
    rule_description
)
SELECT
    'savings_from_1991_09_observation',
    'savings',
    category_definition_id,
    DATE '1991-11-18',
    DATE '1991-09-01',
    'Savings including MMDA beginning with September 1991 observations.'
FROM staging.g6_deposit_category_definition
WHERE definition_code = 'savings_including_mmda_v4';


-- ATS/NOW and the narrow other-checkable concept are continuous
INSERT INTO staging.g6_deposit_definition_rule (
    rule_code,
    deposit_type_canonical,
    category_definition_id,
    release_date_from,
    release_date_to,
    rule_description
)
SELECT
    'ats_now_narrow_definition',
    'ats_now',
    category_definition_id,
    DATE '1980-08-14',
    DATE '1992-11-16',
    'ATS/NOW label under the narrow other-checkable concept.'
FROM staging.g6_deposit_category_definition
WHERE definition_code = 'other_checkable_narrow_v1';


INSERT INTO staging.g6_deposit_definition_rule (
    rule_code,
    deposit_type_canonical,
    category_definition_id,
    release_date_from,
    release_date_to,
    rule_description
)
SELECT
    'other_checkable_narrow_1992_12_to_1994_02',
    'other_checkable',
    category_definition_id,
    DATE '1992-12-17',
    DATE '1994-02-15',
    'Other-checkable label with the same narrow conceptual scope as ATS/NOW.'
FROM staging.g6_deposit_category_definition
WHERE definition_code = 'other_checkable_narrow_v1';


INSERT INTO staging.g6_deposit_definition_rule (
    rule_code,
    deposit_type_canonical,
    category_definition_id,
    release_date_from,
    rule_description
)
SELECT
    'other_checkable_expanded_from_1994_03',
    'other_checkable',
    category_definition_id,
    DATE '1994-03-21',
    'Expanded other-checkable definition including telephone and preauthorized transfers.'
FROM staging.g6_deposit_category_definition
WHERE definition_code = 'other_checkable_expanded_v2';


-- MMDA before and after absorption into savings
INSERT INTO staging.g6_deposit_definition_rule (
    rule_code,
    deposit_type_canonical,
    category_definition_id,
    release_date_from,
    observation_date_to,
    rule_description
)
SELECT
    'mmda_separate_through_1991_08_observation',
    'mmda',
    category_definition_id,
    DATE '1983-03-22',
    DATE '1991-08-01',
    'MMDA values reported as a separate category.'
FROM staging.g6_deposit_category_definition
WHERE definition_code = 'mmda_separately_reported_v1';


INSERT INTO staging.g6_deposit_definition_rule (
    rule_code,
    deposit_type_canonical,
    category_definition_id,
    release_date_from,
    release_date_to,
    observation_date_from,
    rule_description
)
SELECT
    'mmda_absorbed_from_1991_09_observation',
    'mmda',
    category_definition_id,
    DATE '1991-11-18',
    DATE '1992-11-16',
    DATE '1991-09-01',
    'MMDA column retained as not available after MMDA was absorbed into savings.'
FROM staging.g6_deposit_category_definition
WHERE definition_code = 'mmda_absorbed_into_savings_v2';


-- ============================================================
-- 5. One-to-one economically oriented observation table
-- ============================================================

CREATE TABLE staging.g6_parsed_observation_post_processed (
    -- Primary key and one-to-one FK to the preprocessed row
    g6_cell_extraction_id       integer PRIMARY KEY,

    -- Direct relational links for release-vintage analysis
    g6_release_id               smallint NOT NULL,
    source_document_id          smallint NOT NULL,

    -- Identifies whether the cell came from the preferred document
    -- or from an earlier superseded document.
    source_document_precedence  text NOT NULL,

    -- Economic time dimensions
    release_date                date NOT NULL,
    observation_date            date NOT NULL,
    observation_date_status     text NOT NULL,

    -- Controlled analytical dimensions
    measure_canonical           text NOT NULL,
    adjustment_status           text NOT NULL,

    definition_rule_id          smallint NOT NULL,
    category_definition_id      smallint NOT NULL,

    geography_canonical         text,
    customer_type_canonical     text,

    unit_id                     smallint NOT NULL,

    -- Economic value
    value_numeric               numeric,
    value_status                text NOT NULL,

    created_at                  timestamptz NOT NULL
                                DEFAULT current_timestamp,

    CONSTRAINT fk_g6_post_preprocessed
        FOREIGN KEY (g6_cell_extraction_id)
        REFERENCES staging.g6_parsed_observation_preprocessed (
            g6_cell_extraction_id
        )
        ON DELETE RESTRICT,

    CONSTRAINT fk_g6_post_release
        FOREIGN KEY (g6_release_id)
        REFERENCES raw.g6_release (g6_release_id)
        ON DELETE RESTRICT,

    CONSTRAINT fk_g6_post_source_document
        FOREIGN KEY (source_document_id)
        REFERENCES raw.source_document (source_document_id)
        ON DELETE RESTRICT,

    -- Enforces that the selected rule and definition form a recognized assignment.
    CONSTRAINT fk_g6_post_definition_rule
        FOREIGN KEY (
            definition_rule_id,
            category_definition_id
        )
        REFERENCES staging.g6_deposit_definition_rule (
            definition_rule_id,
            category_definition_id
        )
        ON DELETE RESTRICT,

    -- Enforces that each canonical measure uses the correct unit.
    CONSTRAINT fk_g6_post_unit_measure
        FOREIGN KEY (
            unit_id,
            measure_canonical
        )
        REFERENCES staging.g6_unit_dimension (
            unit_id,
            measure_canonical
        )
        ON DELETE RESTRICT,

    CONSTRAINT ck_g6_post_document_precedence
        CHECK (
            source_document_precedence IN (
                'preferred',
                'superseded'
            )
        ),

    CONSTRAINT ck_g6_post_observation_date_status
        CHECK (
            observation_date_status IN (
                'recognized',
                'inferred',
                'page_consensus_reconciled'
            )
        ),

    CONSTRAINT ck_g6_post_measure
        CHECK (
            measure_canonical IN (
                'debits',
                'average_deposits',
                'turnover'
            )
        ),

    CONSTRAINT ck_g6_post_adjustment
        CHECK (
            adjustment_status IN (
                'SA',
                'NSA',
                'unknown'
            )
        ),


    CONSTRAINT ck_g6_post_geography
        CHECK (
            geography_canonical IS NULL
            OR geography_canonical IN (
                'all_banks',
                'new_york_city',
                'other_banks'
            )
        ),

    CONSTRAINT ck_g6_post_customer_type
        CHECK (
            customer_type_canonical IS NULL
            OR customer_type_canonical IN (
                'total',
                'business',
                'other',
                'ats_now'
            )
        ),

    CONSTRAINT ck_g6_post_value_status
        CHECK (
            value_status IN (
                'reported',
                'not_available',
                'blank',
                'extraction_error'
            )
        ),

    CONSTRAINT ck_g6_post_value_consistency
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
        );


-- ============================================================
-- 6. Indexes supporting the later consensus stage
-- ============================================================

CREATE INDEX ix_g6_post_source_document
    ON staging.g6_parsed_observation_post_processed (
        source_document_id
    );

CREATE INDEX ix_g6_post_release
    ON staging.g6_parsed_observation_post_processed (
        g6_release_id,
        source_document_precedence
    );

CREATE INDEX ix_g6_post_economic_series
    ON staging.g6_parsed_observation_post_processed (
        observation_date,
        measure_canonical,
        adjustment_status,
        category_definition_id,
        geography_canonical,
        customer_type_canonical
    );


COMMENT ON TABLE staging.g6_parsed_observation_post_processed IS
    'One-to-one economically oriented transformation of g6_parsed_observation_preprocessed. Units and deposit definitions are controlled; raw and Python provenance remain reachable through foreign keys.';

COMMENT ON COLUMN
    staging.g6_parsed_observation_post_processed.source_document_precedence
IS
    'Preferred when sourced from the selected document version for a release; superseded when sourced from an earlier nonpreferred document.';

COMMENT ON COLUMN
    staging.g6_parsed_observation_post_processed.category_definition_id
IS
    'Economically precise deposit-category definition, including changes in ATS/NOW, MMDA, savings and other-checkable scope.';

COMMIT;
