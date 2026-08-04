import tempfile
import unittest
from pathlib import Path

from load_g6_raw import (
    LoaderError,
    Record,
    exact_decimal,
    load_era_map,
    selected_candidate_order,
)


def candidate(variant="page", selected=None):
    value = {
        "source": "rendered_ocr",
        "ocr_variant": variant,
        "raw": "1,234.5",
        "value_numeric": "1234.5",
        "value_status": "reported",
        "confidence": 90.0,
        "normalization": "exact_one_decimal",
        "eligible": True,
        "measure_canonical": "debits",
    }
    if selected is not None:
        value["is_selected"] = selected
    return value


def cell(candidates):
    return {
        "table_instance_id": "p001_t01_i01",
        "row_index": 0,
        "column_index": 0,
        "selected_source": "rendered_ocr",
        "value_raw": "1,234.5",
        "value_numeric": "1234.5",
        "value_status": "reported",
        "normalization_rule": "exact_one_decimal",
        "ocr_confidence": 90.0,
        "ocr_candidates": candidates,
    }


def record():
    return Record(
        Path("ocr_raw.part_001.jsonl"),
        1,
        {"source_file": "1970s/sample.pdf", "page_number": 1},
    )


class LoaderTests(unittest.TestCase):
    def test_decimal_is_exact(self):
        self.assertEqual(exact_decimal("0.1", "test"), exact_decimal("0.10", "test"))

    def test_explicit_selected_flag_wins(self):
        self.assertEqual(
            selected_candidate_order(record(), cell([candidate(selected=False), candidate(selected=True)])),
            1,
        )

    def test_unique_parent_match(self):
        other = candidate()
        other["confidence"] = 80.0
        self.assertEqual(selected_candidate_order(record(), cell([other, candidate()])), 1)

    def test_identical_candidates_use_lowest_order(self):
        self.assertEqual(selected_candidate_order(record(), cell([candidate(), candidate()])), 0)

    def test_variant_only_tie_uses_lowest_order(self):
        self.assertEqual(
            selected_candidate_order(
                record(), cell([candidate("gray_psm7"), candidate("gray_numeric_psm7")])
            ),
            0,
        )

    def test_genuinely_distinct_tied_candidates_are_rejected(self):
        distinct = candidate("gray_numeric_psm7")
        distinct["unsafe_decimal_relocation"] = True
        with self.assertRaisesRegex(LoaderError, "ambiguous"):
            selected_candidate_order(record(), cell([candidate("gray_psm7"), distinct]))

    def test_no_parent_match_is_rejected(self):
        unmatched = candidate()
        unmatched["confidence"] = 80.0
        with self.assertRaisesRegex(LoaderError, "found no candidate matching parent"):
            selected_candidate_order(record(), cell([unmatched]))

    def test_era_map_requires_eight_rows(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "eras.csv"
            path.write_text(
                "Era,First,Last,# of docs,description\n1,1977-01-01,1977-12-31,1,test\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(LoaderError, "exactly era IDs 1-8"):
                load_era_map(path)


if __name__ == "__main__":
    unittest.main()
