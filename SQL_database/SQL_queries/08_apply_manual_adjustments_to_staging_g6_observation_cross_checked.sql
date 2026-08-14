-- Apply manual adjustments to staging.g6_observation_cross_checked

BEGIN;

-- ------------------------------------------------------------
-- 1979-02 savings / other turnover
--
-- OCR selected 11.8 from "1 1.8".
-- Manually verified published value: 1.8.
-- ------------------------------------------------------------

UPDATE staging.g6_observation_cross_checked
SET
    value_numeric = 1.8,
    manually_adjusted = true
WHERE observation_date = DATE '1979-02-01'
  AND measure_canonical = 'turnover'
  AND adjustment_status = 'NSA'
  AND category_definition_id = 3
  AND geography_canonical IS NULL
  AND customer_type_canonical = 'other';


-- ------------------------------------------------------------
-- 1996-05 demand debits / other banks / SA
--
-- OCR selected 218355.3.
-- Manually verified published value: 218353.6.
-- ------------------------------------------------------------

UPDATE staging.g6_observation_cross_checked
SET
    value_numeric = 218353.6,
    manually_adjusted = true
WHERE observation_date = DATE '1996-05-01'
  AND measure_canonical = 'debits'
  AND adjustment_status = 'SA'
  AND category_definition_id = 1
  AND geography_canonical = 'other_banks'
  AND customer_type_canonical IS NULL;


-- Validate exactly two manual changes.
DO $$
DECLARE
    v_count bigint;
BEGIN
    SELECT COUNT(*)
    INTO v_count
    FROM staging.g6_observation_cross_checked
    WHERE manually_adjusted;

    IF v_count <> 2 THEN
        RAISE EXCEPTION
            'Expected exactly 2 manually adjusted observations, found %',
            v_count;
    END IF;
END
$$;

COMMIT;
