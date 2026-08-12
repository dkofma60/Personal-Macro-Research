import os
import unittest
from datetime import date

import SQL_database.OCR_pipeline.g6_spatial_extraction_pipeline as pipeline


def sequence(months, anchors=None):
    anchors = anchors or {}
    return [
        {
            "month": month,
            "year_options": anchors.get(index, []),
        }
        for index, month in enumerate(months)
    ]


def anchor(year, source="rendered_ocr", weight=12.0):
    return {"year": year, "source": source, "weight": weight}


class SequenceYearTests(unittest.TestCase):
    def test_1984_page_2_corrupt_anchor_does_not_shift_four_years(self):
        rows = sequence(
            [5, 6, 7, 8, 9, 10, 11, 12, 1, 2, 3, 4, 5],
            {8: [anchor(1980)]},
        )
        years = pipeline.resolve_sequence_years(rows, 5, date(1984, 7, 13), 5)
        self.assertEqual(years, [1983] * 8 + [1984] * 5)

    def test_1986_page_1_conflicting_anchor_does_not_shift_six_years(self):
        rows = sequence(
            [9, 10, 11, 12, 1, 2, 3, 4, 5, 6, 7, 8, 9],
            {
                0: [anchor(1985), anchor(1985, "embedded_locator", 4.8)],
                4: [anchor(1980)],
            },
        )
        years = pipeline.resolve_sequence_years(rows, 9, date(1986, 11, 19), 9)
        self.assertEqual(years, [1985] * 4 + [1986] * 9)

    def test_august_1980_backdata_is_preserved_by_two_anchor_rows(self):
        rows = sequence(
            [12, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
            {0: [anchor(1978)], 1: [anchor(1979)]},
        )
        years = pipeline.resolve_sequence_years(rows, 12, date(1980, 8, 18), 6)
        self.assertEqual(years, [1978] + [1979] * 12)

    def test_december_to_january_rollover(self):
        rows = sequence([12, 1])
        years = pipeline.resolve_sequence_years(rows, 12, date(1980, 3, 11), 1)
        self.assertEqual(years, [1979, 1980])

    def test_ordinary_current_window_uses_release_context(self):
        rows = sequence([5, 6, 7, 8, 9, 10, 11, 12, 1, 2, 3, 4, 5])
        years = pipeline.resolve_sequence_years(rows, 5, date(1990, 7, 16), 5)
        self.assertEqual(years, [1989] * 8 + [1990] * 5)


@unittest.skipUnless(
    os.environ.get("G6_RUN_DATE_INTEGRATION_TESTS") == "1",
    "set G6_RUN_DATE_INTEGRATION_TESTS=1 for cached-PDF regressions",
)
class CachedPdfRegressionTests(unittest.TestCase):
    CASES = {
        "1984-07-13_491191_July_13_1984.pdf": (2, "1983-05-01", "1984-05-01"),
        "1986-11-19_491220_November_19_1986.pdf": (1, "1985-09-01", "1986-09-01"),
        "1980-08-18_491144_August_18_1980_Corrected_copy.pdf": (
            2,
            "1978-12-01",
            "1979-12-01",
        ),
    }

    @classmethod
    def setUpClass(cls):
        cls.results = {}
        for filename in cls.CASES:
            paths = list(pipeline.INPUT_ROOT.rglob(filename))
            if len(paths) != 1:
                raise AssertionError(f"expected one PDF named {filename}, found {paths}")
            rows, _, issues, _, _ = pipeline.safe_extract(paths[0])
            processing_errors = [
                issue for issue in issues if issue["issue_type"] == "file_processing_error"
            ]
            if processing_errors:
                raise AssertionError(processing_errors)
            cls.results[filename] = rows

    def test_real_pdf_page_windows(self):
        for filename, (page_number, first_date, last_date) in self.CASES.items():
            with self.subTest(filename=filename, page=page_number):
                rows = self.results[filename]
                table_windows = {}
                for table_number in (1, 2, 3):
                    dates = sorted(
                        {
                            row["observation_date"]
                            for row in rows
                            if int(row["page_number"]) == page_number
                            and int(row["table_number"]) == table_number
                        }
                    )
                    table_windows[table_number] = (dates[0], dates[-1], len(dates))
                self.assertEqual(
                    table_windows,
                    {table_number: (first_date, last_date, 13) for table_number in (1, 2, 3)},
                )


if __name__ == "__main__":
    unittest.main()
