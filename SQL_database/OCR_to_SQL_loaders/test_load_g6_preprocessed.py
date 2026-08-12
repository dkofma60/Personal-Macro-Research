import csv
import tempfile
import unittest
from datetime import date
from decimal import Decimal
from pathlib import Path

from load_g6_preprocessed import (
    CSV_COLUMNS,
    LoaderError,
    RawCell,
    parse_csv_row,
    parse_json_array,
    validate_csv,
    validate_observation,
)


def sample_row(**changes):
    row = {name: "unused" for name in CSV_COLUMNS}
    row.update(
        source_file="1970s/sample.pdf",
        release_date="1977-10-13",
        page_number="2",
        table_number="1",
        table_instance_id="p002_t01_i01",
        observation_date="1976-08-01",
        observation_date_status="recognized",
        measure_canonical="debits",
        adjustment_status="SA",
        row_index="0",
        column_index="1",
        deposit_type_canonical="demand",
        geography_canonical="",
        customer_type_canonical="",
        units_raw="BILLIONS OF DOLLARS",
        value_numeric="30347.8",
        value_status="reported",
        validation_flags='["ocr_candidate_conflict"]',
        cross_release_support_count="0",
    )
    row.update(changes)
    return row


def matching_raw(observation, **changes):
    values = dict(
        key=observation.key,
        cell_id=42,
        document_date=observation.release_date,
        page_adjustment_status=observation.adjustment_status,
        table_number=observation.table_number,
        observation_date=observation.observation_date,
        observation_date_status=observation.observation_date_status,
        canonical_column={
            "deposit_type": observation.deposit_type_canonical,
            "geography": observation.geography_canonical or "",
            "customer_type": observation.customer_type_canonical or "",
        },
        cell_status=observation.value_status,
        cross_release_support_count=observation.cross_release_support_count,
        validation_flags=observation.validation_flags,
        selected_candidate_order=0,
        selected_candidate_status=observation.value_status,
        selected_candidate_numeric=observation.value_numeric,
        selected_measure_canonical=observation.measure_canonical,
    )
    values.update(changes)
    return RawCell(**values)


class ParserTests(unittest.TestCase):
    def test_typed_row_uses_decimal_dates_json_and_nulls(self):
        parsed = parse_csv_row(sample_row(), 2)
        self.assertEqual(parsed.release_date, date(1977, 10, 13))
        self.assertEqual(parsed.value_numeric, Decimal("30347.8"))
        self.assertEqual(parsed.validation_flags, ["ocr_candidate_conflict"])
        self.assertIsNone(parsed.geography_canonical)
        self.assertEqual(
            parsed.key,
            ("1970s/sample.pdf", 2, "p002_t01_i01", 0, 1),
        )

    def test_json_flags_must_be_array(self):
        with self.assertRaisesRegex(LoaderError, "must be a JSON array"):
            parse_json_array('{"flag": true}', "flags")

    def test_reported_requires_numeric_value(self):
        with self.assertRaisesRegex(LoaderError, "value consistency failure"):
            parse_csv_row(sample_row(value_numeric=""), 9)

    def test_nonreported_rejects_numeric_value(self):
        with self.assertRaisesRegex(LoaderError, "value consistency failure"):
            parse_csv_row(sample_row(value_status="blank"), 10)

    def test_nonfinite_numeric_value_is_rejected(self):
        with self.assertRaisesRegex(LoaderError, "not a finite decimal"):
            parse_csv_row(sample_row(value_numeric="NaN"), 11)

    def test_observation_matches_raw_cell(self):
        observation = parse_csv_row(sample_row(), 12)
        validate_observation(observation, matching_raw(observation))

    def test_raw_mismatch_reports_row_key_and_cell(self):
        observation = parse_csv_row(sample_row(), 13)
        with self.assertRaisesRegex(
            LoaderError, "CSV row 13.*value_numeric mismatch.*cell_id=42"
        ):
            validate_observation(
                observation,
                matching_raw(observation, selected_candidate_numeric=Decimal("30347.9")),
            )

    def test_header_mismatch_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bad.csv"
            path.write_text("source_file,page_number\na.pdf,1\n", encoding="utf-8")
            with self.assertRaisesRegex(LoaderError, "CSV columns differ"):
                validate_csv(path, {})


if __name__ == "__main__":
    unittest.main()
