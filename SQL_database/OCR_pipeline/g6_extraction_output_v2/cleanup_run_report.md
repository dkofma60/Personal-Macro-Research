# G.6 extraction cleanup run

- Pipeline version: `date-reconciliation-v4-20260808`
- Resolved input root: `/Users/danie/Personal-Macro-Research/SQL_database/OCR_pipeline/fraser_g6_issues`
- Era map: `/Users/danie/Personal-Macro-Research/SQL_database/OCR_pipeline/g6_era_map.csv`
- Baseline metrics: `/Users/danie/Personal-Macro-Research/SQL_database/OCR_pipeline/g6_extraction_output/_cleanup_baseline_metrics.json`
- Full corpus run completed: `yes`

## Diagnostic paths

- `1980-08-14_491143_August_14_1980.pdf`: `/Users/danie/Personal-Macro-Research/SQL_database/OCR_pipeline/fraser_g6_issues/1980s/1980-08-14_491143_August_14_1980.pdf`
- `1980-08-18_491144_August_18_1980_Corrected_copy.pdf`: `/Users/danie/Personal-Macro-Research/SQL_database/OCR_pipeline/fraser_g6_issues/1980s/1980-08-18_491144_August_18_1980_Corrected_copy.pdf`
- `1982-10-14_491170_October_14_1982.pdf`: `/Users/danie/Personal-Macro-Research/SQL_database/OCR_pipeline/fraser_g6_issues/1980s/1982-10-14_491170_October_14_1982.pdf`
- `1982-12-10_491172_December_10_1982.pdf`: `/Users/danie/Personal-Macro-Research/SQL_database/OCR_pipeline/fraser_g6_issues/1980s/1982-12-10_491172_December_10_1982.pdf`
- `1984-07-13_491191_July_13_1984.pdf`: `/Users/danie/Personal-Macro-Research/SQL_database/OCR_pipeline/fraser_g6_issues/1980s/1984-07-13_491191_July_13_1984.pdf`
- `1985-12-13_491209_December_13_1985.pdf`: `/Users/danie/Personal-Macro-Research/SQL_database/OCR_pipeline/fraser_g6_issues/1980s/1985-12-13_491209_December_13_1985.pdf`
- `1986-11-19_491220_November_19_1986.pdf`: `/Users/danie/Personal-Macro-Research/SQL_database/OCR_pipeline/fraser_g6_issues/1980s/1986-11-19_491220_November_19_1986.pdf`
- `1987-05-15_491226_May_15_1987.pdf`: `/Users/danie/Personal-Macro-Research/SQL_database/OCR_pipeline/fraser_g6_issues/1980s/1987-05-15_491226_May_15_1987.pdf`
- `1987-07-15_491228_July_15_1987.pdf`: `/Users/danie/Personal-Macro-Research/SQL_database/OCR_pipeline/fraser_g6_issues/1980s/1987-07-15_491228_July_15_1987.pdf`
- `1989-03-15_491244_March_15_1989.pdf`: `/Users/danie/Personal-Macro-Research/SQL_database/OCR_pipeline/fraser_g6_issues/1980s/1989-03-15_491244_March_15_1989.pdf`
- `1989-05-22_491246_May_22_1989.pdf`: `/Users/danie/Personal-Macro-Research/SQL_database/OCR_pipeline/fraser_g6_issues/1980s/1989-05-22_491246_May_22_1989.pdf`
- `1991-08-16_491273_August_16_1991.pdf`: `/Users/danie/Personal-Macro-Research/SQL_database/OCR_pipeline/fraser_g6_issues/1990s/1991-08-16_491273_August_16_1991.pdf`
- `1992-12-17_491289_December_17_1992.pdf`: `/Users/danie/Personal-Macro-Research/SQL_database/OCR_pipeline/fraser_g6_issues/1990s/1992-12-17_491289_December_17_1992.pdf`
- `1993-08-16_491297_August_16_1993.pdf`: `/Users/danie/Personal-Macro-Research/SQL_database/OCR_pipeline/fraser_g6_issues/1990s/1993-08-16_491297_August_16_1993.pdf`
- `1995-01-12_491314_January_12_1995.pdf`: `/Users/danie/Personal-Macro-Research/SQL_database/OCR_pipeline/fraser_g6_issues/1990s/1995-01-12_491314_January_12_1995.pdf`

## Diagnostic assertions

| Result | Blocking | Criterion | Expected | Observed |
|:--|:--:|:--|:--|:--|
| PASS | yes | 1980-08-14_491143_August_14_1980.pdf: diagnostic path recorded | existing corpus path or explicit fallback path | /Users/danie/Personal-Macro-Research/SQL_database/OCR_pipeline/fraser_g6_issues/1980s/1980-08-14_491143_August_14_1980.pdf |
| PASS | yes | 1980-08-14_491143_August_14_1980.pdf page 1: page classification | table_page | table_page |
| PASS | yes | 1980-08-14_491143_August_14_1980.pdf page 1: semantic tables | [1, 2, 3] | [1, 2, 3] |
| PASS | yes | 1980-08-14_491143_August_14_1980.pdf page 1: table dimensions | {"1": {"columns": 7, "rows": 13}, "2": {"columns": 7, "rows": 13}, "3": {"columns": 7, "rows": 13}} | {"1": {"columns": 7, "rows": 13}, "2": {"columns": 7, "rows": 13}, "3": {"columns": 7, "rows": 13}} |
| PASS | yes | 1980-08-14_491143_August_14_1980.pdf page 1: complete ordered row-date sequence | {"1": ["1979-06-01", "1979-07-01", "1979-08-01", "1979-09-01", "1979-10-01", "1979-11-01", "1979-12-01", "1980-01-01", "1980-02-01", "1980-03-01", "1980-04-01", "1980-05-01", "1980-06-01"], "2": ["1979-06-01", "1979-07-01", "1979-08-01", "1979-09-01", "1979-10-01", "1979-11-01", "1979-12-01", "1980-01-01", "1980-02-01", "1980-03-01", "1980-04-01", "1980-05-01", "1980-06-01"], "3": ["1979-06-01", "1979-07-01", "1979-08-01", "1979-09-01", "1979-10-01", "1979-11-01", "1979-12-01", "1980-01-01", "1980-02-01", "1980-03-01", "1980-04-01", "1980-05-01", "1980-06-01"]} | {"1": ["1979-06-01", "1979-07-01", "1979-08-01", "1979-09-01", "1979-10-01", "1979-11-01", "1979-12-01", "1980-01-01", "1980-02-01", "1980-03-01", "1980-04-01", "1980-05-01", "1980-06-01"], "2": ["1979-06-01", "1979-07-01", "1979-08-01", "1979-09-01", "1979-10-01", "1979-11-01", "1979-12-01", "1980-01-01", "1980-02-01", "1980-03-01", "1980-04-01", "1980-05-01", "1980-06-01"], "3": ["1979-06-01", "1979-07-01", "1979-08-01", "1979-09-01", "1979-10-01", "1979-11-01", "1979-12-01", "1980-01-01", "1980-02-01", "1980-03-01", "1980-04-01", "1980-05-01", "1980-06-01"]} |
| PASS | yes | 1980-08-14_491143_August_14_1980.pdf page 1: title/grid/row/column evidence | all four evidence flags true for tables 1, 2, and 3 | {"1": {"aligned_numeric_columns": true, "coherent_month_rows": true, "credible_title": true, "visible_grid": true}, "2": {"aligned_numeric_columns": true, "coherent_month_rows": true, "credible_title": true, "visible_grid": true}, "3": {"aligned_numeric_columns": true, "coherent_month_rows": true, "credible_title": true, "visible_grid": true}} |
| PASS | yes | 1980-08-14_491143_August_14_1980.pdf page 2: page classification | table_page | table_page |
| PASS | yes | 1980-08-14_491143_August_14_1980.pdf page 2: semantic tables | [1, 2, 3] | [1, 2, 3] |
| PASS | yes | 1980-08-14_491143_August_14_1980.pdf page 2: table dimensions | {"1": {"columns": 7, "rows": 13}, "2": {"columns": 7, "rows": 13}, "3": {"columns": 7, "rows": 13}} | {"1": {"columns": 7, "rows": 13}, "2": {"columns": 7, "rows": 13}, "3": {"columns": 7, "rows": 13}} |
| PASS | yes | 1980-08-14_491143_August_14_1980.pdf page 2: complete ordered row-date sequence | {"1": ["1978-12-01", "1979-01-01", "1979-02-01", "1979-03-01", "1979-04-01", "1979-05-01", "1979-06-01", "1979-07-01", "1979-08-01", "1979-09-01", "1979-10-01", "1979-11-01", "1979-12-01"], "2": ["1978-12-01", "1979-01-01", "1979-02-01", "1979-03-01", "1979-04-01", "1979-05-01", "1979-06-01", "1979-07-01", "1979-08-01", "1979-09-01", "1979-10-01", "1979-11-01", "1979-12-01"], "3": ["1978-12-01", "1979-01-01", "1979-02-01", "1979-03-01", "1979-04-01", "1979-05-01", "1979-06-01", "1979-07-01", "1979-08-01", "1979-09-01", "1979-10-01", "1979-11-01", "1979-12-01"]} | {"1": ["1978-12-01", "1979-01-01", "1979-02-01", "1979-03-01", "1979-04-01", "1979-05-01", "1979-06-01", "1979-07-01", "1979-08-01", "1979-09-01", "1979-10-01", "1979-11-01", "1979-12-01"], "2": ["1978-12-01", "1979-01-01", "1979-02-01", "1979-03-01", "1979-04-01", "1979-05-01", "1979-06-01", "1979-07-01", "1979-08-01", "1979-09-01", "1979-10-01", "1979-11-01", "1979-12-01"], "3": ["1978-12-01", "1979-01-01", "1979-02-01", "1979-03-01", "1979-04-01", "1979-05-01", "1979-06-01", "1979-07-01", "1979-08-01", "1979-09-01", "1979-10-01", "1979-11-01", "1979-12-01"]} |
| PASS | yes | 1980-08-14_491143_August_14_1980.pdf page 2: title/grid/row/column evidence | all four evidence flags true for tables 1, 2, and 3 | {"1": {"aligned_numeric_columns": true, "coherent_month_rows": true, "credible_title": true, "visible_grid": true}, "2": {"aligned_numeric_columns": true, "coherent_month_rows": true, "credible_title": true, "visible_grid": true}, "3": {"aligned_numeric_columns": true, "coherent_month_rows": true, "credible_title": true, "visible_grid": true}} |
| PASS | yes | 1980-08-18_491144_August_18_1980_Corrected_copy.pdf: diagnostic path recorded | existing corpus path or explicit fallback path | /Users/danie/Personal-Macro-Research/SQL_database/OCR_pipeline/fraser_g6_issues/1980s/1980-08-18_491144_August_18_1980_Corrected_copy.pdf |
| PASS | yes | 1980-08-18_491144_August_18_1980_Corrected_copy.pdf page 1: page classification | table_page | table_page |
| PASS | yes | 1980-08-18_491144_August_18_1980_Corrected_copy.pdf page 1: semantic tables | [1, 2, 3] | [1, 2, 3] |
| PASS | yes | 1980-08-18_491144_August_18_1980_Corrected_copy.pdf page 1: table dimensions | {"1": {"columns": 7, "rows": 13}, "2": {"columns": 7, "rows": 13}, "3": {"columns": 7, "rows": 13}} | {"1": {"columns": 7, "rows": 13}, "2": {"columns": 7, "rows": 13}, "3": {"columns": 7, "rows": 13}} |
| PASS | yes | 1980-08-18_491144_August_18_1980_Corrected_copy.pdf page 1: complete ordered row-date sequence | {"1": ["1979-06-01", "1979-07-01", "1979-08-01", "1979-09-01", "1979-10-01", "1979-11-01", "1979-12-01", "1980-01-01", "1980-02-01", "1980-03-01", "1980-04-01", "1980-05-01", "1980-06-01"], "2": ["1979-06-01", "1979-07-01", "1979-08-01", "1979-09-01", "1979-10-01", "1979-11-01", "1979-12-01", "1980-01-01", "1980-02-01", "1980-03-01", "1980-04-01", "1980-05-01", "1980-06-01"], "3": ["1979-06-01", "1979-07-01", "1979-08-01", "1979-09-01", "1979-10-01", "1979-11-01", "1979-12-01", "1980-01-01", "1980-02-01", "1980-03-01", "1980-04-01", "1980-05-01", "1980-06-01"]} | {"1": ["1979-06-01", "1979-07-01", "1979-08-01", "1979-09-01", "1979-10-01", "1979-11-01", "1979-12-01", "1980-01-01", "1980-02-01", "1980-03-01", "1980-04-01", "1980-05-01", "1980-06-01"], "2": ["1979-06-01", "1979-07-01", "1979-08-01", "1979-09-01", "1979-10-01", "1979-11-01", "1979-12-01", "1980-01-01", "1980-02-01", "1980-03-01", "1980-04-01", "1980-05-01", "1980-06-01"], "3": ["1979-06-01", "1979-07-01", "1979-08-01", "1979-09-01", "1979-10-01", "1979-11-01", "1979-12-01", "1980-01-01", "1980-02-01", "1980-03-01", "1980-04-01", "1980-05-01", "1980-06-01"]} |
| PASS | yes | 1980-08-18_491144_August_18_1980_Corrected_copy.pdf page 1: title/grid/row/column evidence | all four evidence flags true for tables 1, 2, and 3 | {"1": {"aligned_numeric_columns": true, "coherent_month_rows": true, "credible_title": true, "visible_grid": true}, "2": {"aligned_numeric_columns": true, "coherent_month_rows": true, "credible_title": true, "visible_grid": true}, "3": {"aligned_numeric_columns": true, "coherent_month_rows": true, "credible_title": true, "visible_grid": true}} |
| PASS | yes | 1980-08-18_491144_August_18_1980_Corrected_copy.pdf page 2: page classification | table_page | table_page |
| PASS | yes | 1980-08-18_491144_August_18_1980_Corrected_copy.pdf page 2: semantic tables | [1, 2, 3] | [1, 2, 3] |
| PASS | yes | 1980-08-18_491144_August_18_1980_Corrected_copy.pdf page 2: table dimensions | {"1": {"columns": 7, "rows": 13}, "2": {"columns": 7, "rows": 13}, "3": {"columns": 7, "rows": 13}} | {"1": {"columns": 7, "rows": 13}, "2": {"columns": 7, "rows": 13}, "3": {"columns": 7, "rows": 13}} |
| PASS | yes | 1980-08-18_491144_August_18_1980_Corrected_copy.pdf page 2: complete ordered row-date sequence | {"1": ["1978-12-01", "1979-01-01", "1979-02-01", "1979-03-01", "1979-04-01", "1979-05-01", "1979-06-01", "1979-07-01", "1979-08-01", "1979-09-01", "1979-10-01", "1979-11-01", "1979-12-01"], "2": ["1978-12-01", "1979-01-01", "1979-02-01", "1979-03-01", "1979-04-01", "1979-05-01", "1979-06-01", "1979-07-01", "1979-08-01", "1979-09-01", "1979-10-01", "1979-11-01", "1979-12-01"], "3": ["1978-12-01", "1979-01-01", "1979-02-01", "1979-03-01", "1979-04-01", "1979-05-01", "1979-06-01", "1979-07-01", "1979-08-01", "1979-09-01", "1979-10-01", "1979-11-01", "1979-12-01"]} | {"1": ["1978-12-01", "1979-01-01", "1979-02-01", "1979-03-01", "1979-04-01", "1979-05-01", "1979-06-01", "1979-07-01", "1979-08-01", "1979-09-01", "1979-10-01", "1979-11-01", "1979-12-01"], "2": ["1978-12-01", "1979-01-01", "1979-02-01", "1979-03-01", "1979-04-01", "1979-05-01", "1979-06-01", "1979-07-01", "1979-08-01", "1979-09-01", "1979-10-01", "1979-11-01", "1979-12-01"], "3": ["1978-12-01", "1979-01-01", "1979-02-01", "1979-03-01", "1979-04-01", "1979-05-01", "1979-06-01", "1979-07-01", "1979-08-01", "1979-09-01", "1979-10-01", "1979-11-01", "1979-12-01"]} |
| PASS | yes | 1980-08-18_491144_August_18_1980_Corrected_copy.pdf page 2: title/grid/row/column evidence | all four evidence flags true for tables 1, 2, and 3 | {"1": {"aligned_numeric_columns": true, "coherent_month_rows": true, "credible_title": true, "visible_grid": true}, "2": {"aligned_numeric_columns": true, "coherent_month_rows": true, "credible_title": true, "visible_grid": true}, "3": {"aligned_numeric_columns": true, "coherent_month_rows": true, "credible_title": true, "visible_grid": true}} |
| PASS | yes | 1982-10-14_491170_October_14_1982.pdf: diagnostic path recorded | existing corpus path or explicit fallback path | /Users/danie/Personal-Macro-Research/SQL_database/OCR_pipeline/fraser_g6_issues/1980s/1982-10-14_491170_October_14_1982.pdf |
| PASS | yes | 1982-10-14_491170_October_14_1982.pdf page 1: page classification | metadata_page | metadata_page |
| PASS | yes | 1982-10-14_491170_October_14_1982.pdf page 1: non-table cells | 0 | 0 |
| PASS | yes | 1982-10-14_491170_October_14_1982.pdf page 2: page classification | table_page | table_page |
| PASS | yes | 1982-10-14_491170_October_14_1982.pdf page 2: adjustment status | SA | SA |
| PASS | yes | 1982-10-14_491170_October_14_1982.pdf page 2: semantic tables | [1, 2, 3] | [1, 2, 3] |
| PASS | yes | 1982-10-14_491170_October_14_1982.pdf page 2: table dimensions | {"1": {"columns": 5, "rows": 13}, "2": {"columns": 5, "rows": 13}, "3": {"columns": 5, "rows": 13}} | {"1": {"columns": 5, "rows": 13}, "2": {"columns": 5, "rows": 13}, "3": {"columns": 5, "rows": 13}} |
| PASS | yes | 1982-10-14_491170_October_14_1982.pdf page 2: complete ordered row-date sequence | {"1": ["1981-08-01", "1981-09-01", "1981-10-01", "1981-11-01", "1981-12-01", "1982-01-01", "1982-02-01", "1982-03-01", "1982-04-01", "1982-05-01", "1982-06-01", "1982-07-01", "1982-08-01"], "2": ["1981-08-01", "1981-09-01", "1981-10-01", "1981-11-01", "1981-12-01", "1982-01-01", "1982-02-01", "1982-03-01", "1982-04-01", "1982-05-01", "1982-06-01", "1982-07-01", "1982-08-01"], "3": ["1981-08-01", "1981-09-01", "1981-10-01", "1981-11-01", "1981-12-01", "1982-01-01", "1982-02-01", "1982-03-01", "1982-04-01", "1982-05-01", "1982-06-01", "1982-07-01", "1982-08-01"]} | {"1": ["1981-08-01", "1981-09-01", "1981-10-01", "1981-11-01", "1981-12-01", "1982-01-01", "1982-02-01", "1982-03-01", "1982-04-01", "1982-05-01", "1982-06-01", "1982-07-01", "1982-08-01"], "2": ["1981-08-01", "1981-09-01", "1981-10-01", "1981-11-01", "1981-12-01", "1982-01-01", "1982-02-01", "1982-03-01", "1982-04-01", "1982-05-01", "1982-06-01", "1982-07-01", "1982-08-01"], "3": ["1981-08-01", "1981-09-01", "1981-10-01", "1981-11-01", "1981-12-01", "1982-01-01", "1982-02-01", "1982-03-01", "1982-04-01", "1982-05-01", "1982-06-01", "1982-07-01", "1982-08-01"]} |
| PASS | yes | 1982-10-14_491170_October_14_1982.pdf page 2: title/grid/row/column evidence | all four evidence flags true for tables 1, 2, and 3 | {"1": {"aligned_numeric_columns": true, "coherent_month_rows": true, "credible_title": true, "visible_grid": true}, "2": {"aligned_numeric_columns": true, "coherent_month_rows": true, "credible_title": true, "visible_grid": true}, "3": {"aligned_numeric_columns": true, "coherent_month_rows": true, "credible_title": true, "visible_grid": true}} |
| PASS | yes | 1982-10-14_491170_October_14_1982.pdf page 3: page classification | table_page | table_page |
| PASS | yes | 1982-10-14_491170_October_14_1982.pdf page 3: adjustment status | NSA | NSA |
| PASS | yes | 1982-10-14_491170_October_14_1982.pdf page 3: semantic tables | [1, 2, 3] | [1, 2, 3] |
| PASS | yes | 1982-10-14_491170_October_14_1982.pdf page 3: table dimensions | {"1": {"columns": 5, "rows": 13}, "2": {"columns": 5, "rows": 13}, "3": {"columns": 5, "rows": 13}} | {"1": {"columns": 5, "rows": 13}, "2": {"columns": 5, "rows": 13}, "3": {"columns": 5, "rows": 13}} |
| PASS | yes | 1982-10-14_491170_October_14_1982.pdf page 3: complete ordered row-date sequence | {"1": ["1981-08-01", "1981-09-01", "1981-10-01", "1981-11-01", "1981-12-01", "1982-01-01", "1982-02-01", "1982-03-01", "1982-04-01", "1982-05-01", "1982-06-01", "1982-07-01", "1982-08-01"], "2": ["1981-08-01", "1981-09-01", "1981-10-01", "1981-11-01", "1981-12-01", "1982-01-01", "1982-02-01", "1982-03-01", "1982-04-01", "1982-05-01", "1982-06-01", "1982-07-01", "1982-08-01"], "3": ["1981-08-01", "1981-09-01", "1981-10-01", "1981-11-01", "1981-12-01", "1982-01-01", "1982-02-01", "1982-03-01", "1982-04-01", "1982-05-01", "1982-06-01", "1982-07-01", "1982-08-01"]} | {"1": ["1981-08-01", "1981-09-01", "1981-10-01", "1981-11-01", "1981-12-01", "1982-01-01", "1982-02-01", "1982-03-01", "1982-04-01", "1982-05-01", "1982-06-01", "1982-07-01", "1982-08-01"], "2": ["1981-08-01", "1981-09-01", "1981-10-01", "1981-11-01", "1981-12-01", "1982-01-01", "1982-02-01", "1982-03-01", "1982-04-01", "1982-05-01", "1982-06-01", "1982-07-01", "1982-08-01"], "3": ["1981-08-01", "1981-09-01", "1981-10-01", "1981-11-01", "1981-12-01", "1982-01-01", "1982-02-01", "1982-03-01", "1982-04-01", "1982-05-01", "1982-06-01", "1982-07-01", "1982-08-01"]} |
| PASS | yes | 1982-10-14_491170_October_14_1982.pdf page 3: title/grid/row/column evidence | all four evidence flags true for tables 1, 2, and 3 | {"1": {"aligned_numeric_columns": true, "coherent_month_rows": true, "credible_title": true, "visible_grid": true}, "2": {"aligned_numeric_columns": true, "coherent_month_rows": true, "credible_title": true, "visible_grid": true}, "3": {"aligned_numeric_columns": true, "coherent_month_rows": true, "credible_title": true, "visible_grid": true}} |
| PASS | yes | 1982-12-10_491172_December_10_1982.pdf: diagnostic path recorded | existing corpus path or explicit fallback path | /Users/danie/Personal-Macro-Research/SQL_database/OCR_pipeline/fraser_g6_issues/1980s/1982-12-10_491172_December_10_1982.pdf |
| PASS | yes | 1982-12-10_491172_December_10_1982.pdf page 1: page classification | table_page | table_page |
| PASS | yes | 1982-12-10_491172_December_10_1982.pdf page 1: adjustment status | NSA | NSA |
| PASS | yes | 1982-12-10_491172_December_10_1982.pdf page 1: semantic tables | [1, 2, 3] | [1, 2, 3] |
| PASS | yes | 1982-12-10_491172_December_10_1982.pdf page 1: table dimensions | {"1": {"columns": 5, "rows": 13}, "2": {"columns": 5, "rows": 13}, "3": {"columns": 5, "rows": 13}} | {"1": {"columns": 5, "rows": 13}, "2": {"columns": 5, "rows": 13}, "3": {"columns": 5, "rows": 13}} |
| PASS | yes | 1982-12-10_491172_December_10_1982.pdf page 1: complete ordered row-date sequence | {"1": ["1981-10-01", "1981-11-01", "1981-12-01", "1982-01-01", "1982-02-01", "1982-03-01", "1982-04-01", "1982-05-01", "1982-06-01", "1982-07-01", "1982-08-01", "1982-09-01", "1982-10-01"], "2": ["1981-10-01", "1981-11-01", "1981-12-01", "1982-01-01", "1982-02-01", "1982-03-01", "1982-04-01", "1982-05-01", "1982-06-01", "1982-07-01", "1982-08-01", "1982-09-01", "1982-10-01"], "3": ["1981-10-01", "1981-11-01", "1981-12-01", "1982-01-01", "1982-02-01", "1982-03-01", "1982-04-01", "1982-05-01", "1982-06-01", "1982-07-01", "1982-08-01", "1982-09-01", "1982-10-01"]} | {"1": ["1981-10-01", "1981-11-01", "1981-12-01", "1982-01-01", "1982-02-01", "1982-03-01", "1982-04-01", "1982-05-01", "1982-06-01", "1982-07-01", "1982-08-01", "1982-09-01", "1982-10-01"], "2": ["1981-10-01", "1981-11-01", "1981-12-01", "1982-01-01", "1982-02-01", "1982-03-01", "1982-04-01", "1982-05-01", "1982-06-01", "1982-07-01", "1982-08-01", "1982-09-01", "1982-10-01"], "3": ["1981-10-01", "1981-11-01", "1981-12-01", "1982-01-01", "1982-02-01", "1982-03-01", "1982-04-01", "1982-05-01", "1982-06-01", "1982-07-01", "1982-08-01", "1982-09-01", "1982-10-01"]} |
| PASS | yes | 1982-12-10_491172_December_10_1982.pdf page 1: title/grid/row/column evidence | all four evidence flags true for tables 1, 2, and 3 | {"1": {"aligned_numeric_columns": true, "coherent_month_rows": true, "credible_title": true, "visible_grid": true}, "2": {"aligned_numeric_columns": true, "coherent_month_rows": true, "credible_title": true, "visible_grid": true}, "3": {"aligned_numeric_columns": true, "coherent_month_rows": true, "credible_title": true, "visible_grid": true}} |
| PASS | yes | 1982-12-10_491172_December_10_1982.pdf page 2: page classification | table_page | table_page |
| PASS | yes | 1982-12-10_491172_December_10_1982.pdf page 2: adjustment status | SA | SA |
| PASS | yes | 1982-12-10_491172_December_10_1982.pdf page 2: semantic tables | [1, 2, 3] | [1, 2, 3] |
| PASS | yes | 1982-12-10_491172_December_10_1982.pdf page 2: table dimensions | {"1": {"columns": 5, "rows": 13}, "2": {"columns": 5, "rows": 13}, "3": {"columns": 5, "rows": 13}} | {"1": {"columns": 5, "rows": 13}, "2": {"columns": 5, "rows": 13}, "3": {"columns": 5, "rows": 13}} |
| PASS | yes | 1982-12-10_491172_December_10_1982.pdf page 2: complete ordered row-date sequence | {"1": ["1981-10-01", "1981-11-01", "1981-12-01", "1982-01-01", "1982-02-01", "1982-03-01", "1982-04-01", "1982-05-01", "1982-06-01", "1982-07-01", "1982-08-01", "1982-09-01", "1982-10-01"], "2": ["1981-10-01", "1981-11-01", "1981-12-01", "1982-01-01", "1982-02-01", "1982-03-01", "1982-04-01", "1982-05-01", "1982-06-01", "1982-07-01", "1982-08-01", "1982-09-01", "1982-10-01"], "3": ["1981-10-01", "1981-11-01", "1981-12-01", "1982-01-01", "1982-02-01", "1982-03-01", "1982-04-01", "1982-05-01", "1982-06-01", "1982-07-01", "1982-08-01", "1982-09-01", "1982-10-01"]} | {"1": ["1981-10-01", "1981-11-01", "1981-12-01", "1982-01-01", "1982-02-01", "1982-03-01", "1982-04-01", "1982-05-01", "1982-06-01", "1982-07-01", "1982-08-01", "1982-09-01", "1982-10-01"], "2": ["1981-10-01", "1981-11-01", "1981-12-01", "1982-01-01", "1982-02-01", "1982-03-01", "1982-04-01", "1982-05-01", "1982-06-01", "1982-07-01", "1982-08-01", "1982-09-01", "1982-10-01"], "3": ["1981-10-01", "1981-11-01", "1981-12-01", "1982-01-01", "1982-02-01", "1982-03-01", "1982-04-01", "1982-05-01", "1982-06-01", "1982-07-01", "1982-08-01", "1982-09-01", "1982-10-01"]} |
| PASS | yes | 1982-12-10_491172_December_10_1982.pdf page 2: title/grid/row/column evidence | all four evidence flags true for tables 1, 2, and 3 | {"1": {"aligned_numeric_columns": true, "coherent_month_rows": true, "credible_title": true, "visible_grid": true}, "2": {"aligned_numeric_columns": true, "coherent_month_rows": true, "credible_title": true, "visible_grid": true}, "3": {"aligned_numeric_columns": true, "coherent_month_rows": true, "credible_title": true, "visible_grid": true}} |
| PASS | yes | 1984-07-13_491191_July_13_1984.pdf: diagnostic path recorded | existing corpus path or explicit fallback path | /Users/danie/Personal-Macro-Research/SQL_database/OCR_pipeline/fraser_g6_issues/1980s/1984-07-13_491191_July_13_1984.pdf |
| PASS | yes | 1984-07-13_491191_July_13_1984.pdf page 1: page classification | table_page | table_page |
| PASS | yes | 1984-07-13_491191_July_13_1984.pdf page 1: adjustment status | NSA | NSA |
| PASS | yes | 1984-07-13_491191_July_13_1984.pdf page 1: semantic tables | [1, 2, 3] | [1, 2, 3] |
| PASS | yes | 1984-07-13_491191_July_13_1984.pdf page 1: table dimensions | {"1": {"columns": 6, "rows": 13}, "2": {"columns": 6, "rows": 13}, "3": {"columns": 6, "rows": 13}} | {"1": {"columns": 6, "rows": 13}, "2": {"columns": 6, "rows": 13}, "3": {"columns": 6, "rows": 13}} |
| PASS | yes | 1984-07-13_491191_July_13_1984.pdf page 1: complete ordered row-date sequence | {"1": ["1983-05-01", "1983-06-01", "1983-07-01", "1983-08-01", "1983-09-01", "1983-10-01", "1983-11-01", "1983-12-01", "1984-01-01", "1984-02-01", "1984-03-01", "1984-04-01", "1984-05-01"], "2": ["1983-05-01", "1983-06-01", "1983-07-01", "1983-08-01", "1983-09-01", "1983-10-01", "1983-11-01", "1983-12-01", "1984-01-01", "1984-02-01", "1984-03-01", "1984-04-01", "1984-05-01"], "3": ["1983-05-01", "1983-06-01", "1983-07-01", "1983-08-01", "1983-09-01", "1983-10-01", "1983-11-01", "1983-12-01", "1984-01-01", "1984-02-01", "1984-03-01", "1984-04-01", "1984-05-01"]} | {"1": ["1983-05-01", "1983-06-01", "1983-07-01", "1983-08-01", "1983-09-01", "1983-10-01", "1983-11-01", "1983-12-01", "1984-01-01", "1984-02-01", "1984-03-01", "1984-04-01", "1984-05-01"], "2": ["1983-05-01", "1983-06-01", "1983-07-01", "1983-08-01", "1983-09-01", "1983-10-01", "1983-11-01", "1983-12-01", "1984-01-01", "1984-02-01", "1984-03-01", "1984-04-01", "1984-05-01"], "3": ["1983-05-01", "1983-06-01", "1983-07-01", "1983-08-01", "1983-09-01", "1983-10-01", "1983-11-01", "1983-12-01", "1984-01-01", "1984-02-01", "1984-03-01", "1984-04-01", "1984-05-01"]} |
| PASS | yes | 1984-07-13_491191_July_13_1984.pdf page 1: title/grid/row/column evidence | all four evidence flags true for tables 1, 2, and 3 | {"1": {"aligned_numeric_columns": true, "coherent_month_rows": true, "credible_title": true, "visible_grid": true}, "2": {"aligned_numeric_columns": true, "coherent_month_rows": true, "credible_title": true, "visible_grid": true}, "3": {"aligned_numeric_columns": true, "coherent_month_rows": true, "credible_title": true, "visible_grid": true}} |
| PASS | yes | 1984-07-13_491191_July_13_1984.pdf page 2: page classification | table_page | table_page |
| PASS | yes | 1984-07-13_491191_July_13_1984.pdf page 2: adjustment status | SA | SA |
| PASS | yes | 1984-07-13_491191_July_13_1984.pdf page 2: semantic tables | [1, 2, 3] | [1, 2, 3] |
| PASS | yes | 1984-07-13_491191_July_13_1984.pdf page 2: table dimensions | {"1": {"columns": 5, "rows": 13}, "2": {"columns": 5, "rows": 13}, "3": {"columns": 5, "rows": 13}} | {"1": {"columns": 5, "rows": 13}, "2": {"columns": 5, "rows": 13}, "3": {"columns": 5, "rows": 13}} |
| PASS | yes | 1984-07-13_491191_July_13_1984.pdf page 2: complete ordered row-date sequence | {"1": ["1983-05-01", "1983-06-01", "1983-07-01", "1983-08-01", "1983-09-01", "1983-10-01", "1983-11-01", "1983-12-01", "1984-01-01", "1984-02-01", "1984-03-01", "1984-04-01", "1984-05-01"], "2": ["1983-05-01", "1983-06-01", "1983-07-01", "1983-08-01", "1983-09-01", "1983-10-01", "1983-11-01", "1983-12-01", "1984-01-01", "1984-02-01", "1984-03-01", "1984-04-01", "1984-05-01"], "3": ["1983-05-01", "1983-06-01", "1983-07-01", "1983-08-01", "1983-09-01", "1983-10-01", "1983-11-01", "1983-12-01", "1984-01-01", "1984-02-01", "1984-03-01", "1984-04-01", "1984-05-01"]} | {"1": ["1983-05-01", "1983-06-01", "1983-07-01", "1983-08-01", "1983-09-01", "1983-10-01", "1983-11-01", "1983-12-01", "1984-01-01", "1984-02-01", "1984-03-01", "1984-04-01", "1984-05-01"], "2": ["1983-05-01", "1983-06-01", "1983-07-01", "1983-08-01", "1983-09-01", "1983-10-01", "1983-11-01", "1983-12-01", "1984-01-01", "1984-02-01", "1984-03-01", "1984-04-01", "1984-05-01"], "3": ["1983-05-01", "1983-06-01", "1983-07-01", "1983-08-01", "1983-09-01", "1983-10-01", "1983-11-01", "1983-12-01", "1984-01-01", "1984-02-01", "1984-03-01", "1984-04-01", "1984-05-01"]} |
| PASS | yes | 1984-07-13_491191_July_13_1984.pdf page 2: title/grid/row/column evidence | all four evidence flags true for tables 1, 2, and 3 | {"1": {"aligned_numeric_columns": true, "coherent_month_rows": true, "credible_title": true, "visible_grid": true}, "2": {"aligned_numeric_columns": true, "coherent_month_rows": true, "credible_title": true, "visible_grid": true}, "3": {"aligned_numeric_columns": true, "coherent_month_rows": true, "credible_title": true, "visible_grid": true}} |
| PASS | yes | 1986-11-19_491220_November_19_1986.pdf: diagnostic path recorded | existing corpus path or explicit fallback path | /Users/danie/Personal-Macro-Research/SQL_database/OCR_pipeline/fraser_g6_issues/1980s/1986-11-19_491220_November_19_1986.pdf |
| PASS | yes | 1986-11-19_491220_November_19_1986.pdf page 1: page classification | table_page | table_page |
| PASS | yes | 1986-11-19_491220_November_19_1986.pdf page 1: adjustment status | NSA | NSA |
| PASS | yes | 1986-11-19_491220_November_19_1986.pdf page 1: semantic tables | [1, 2, 3] | [1, 2, 3] |
| PASS | yes | 1986-11-19_491220_November_19_1986.pdf page 1: table dimensions | {"1": {"columns": 6, "rows": 13}, "2": {"columns": 6, "rows": 13}, "3": {"columns": 6, "rows": 13}} | {"1": {"columns": 6, "rows": 13}, "2": {"columns": 6, "rows": 13}, "3": {"columns": 6, "rows": 13}} |
| PASS | yes | 1986-11-19_491220_November_19_1986.pdf page 1: complete ordered row-date sequence | {"1": ["1985-09-01", "1985-10-01", "1985-11-01", "1985-12-01", "1986-01-01", "1986-02-01", "1986-03-01", "1986-04-01", "1986-05-01", "1986-06-01", "1986-07-01", "1986-08-01", "1986-09-01"], "2": ["1985-09-01", "1985-10-01", "1985-11-01", "1985-12-01", "1986-01-01", "1986-02-01", "1986-03-01", "1986-04-01", "1986-05-01", "1986-06-01", "1986-07-01", "1986-08-01", "1986-09-01"], "3": ["1985-09-01", "1985-10-01", "1985-11-01", "1985-12-01", "1986-01-01", "1986-02-01", "1986-03-01", "1986-04-01", "1986-05-01", "1986-06-01", "1986-07-01", "1986-08-01", "1986-09-01"]} | {"1": ["1985-09-01", "1985-10-01", "1985-11-01", "1985-12-01", "1986-01-01", "1986-02-01", "1986-03-01", "1986-04-01", "1986-05-01", "1986-06-01", "1986-07-01", "1986-08-01", "1986-09-01"], "2": ["1985-09-01", "1985-10-01", "1985-11-01", "1985-12-01", "1986-01-01", "1986-02-01", "1986-03-01", "1986-04-01", "1986-05-01", "1986-06-01", "1986-07-01", "1986-08-01", "1986-09-01"], "3": ["1985-09-01", "1985-10-01", "1985-11-01", "1985-12-01", "1986-01-01", "1986-02-01", "1986-03-01", "1986-04-01", "1986-05-01", "1986-06-01", "1986-07-01", "1986-08-01", "1986-09-01"]} |
| PASS | yes | 1986-11-19_491220_November_19_1986.pdf page 1: title/grid/row/column evidence | all four evidence flags true for tables 1, 2, and 3 | {"1": {"aligned_numeric_columns": true, "coherent_month_rows": true, "credible_title": true, "visible_grid": true}, "2": {"aligned_numeric_columns": true, "coherent_month_rows": true, "credible_title": true, "visible_grid": true}, "3": {"aligned_numeric_columns": true, "coherent_month_rows": true, "credible_title": true, "visible_grid": true}} |
| PASS | yes | 1986-11-19_491220_November_19_1986.pdf page 2: page classification | table_page | table_page |
| PASS | yes | 1986-11-19_491220_November_19_1986.pdf page 2: adjustment status | SA | SA |
| PASS | yes | 1986-11-19_491220_November_19_1986.pdf page 2: semantic tables | [1, 2, 3] | [1, 2, 3] |
| PASS | yes | 1986-11-19_491220_November_19_1986.pdf page 2: table dimensions | {"1": {"columns": 5, "rows": 13}, "2": {"columns": 5, "rows": 13}, "3": {"columns": 5, "rows": 13}} | {"1": {"columns": 5, "rows": 13}, "2": {"columns": 5, "rows": 13}, "3": {"columns": 5, "rows": 13}} |
| PASS | yes | 1986-11-19_491220_November_19_1986.pdf page 2: complete ordered row-date sequence | {"1": ["1985-09-01", "1985-10-01", "1985-11-01", "1985-12-01", "1986-01-01", "1986-02-01", "1986-03-01", "1986-04-01", "1986-05-01", "1986-06-01", "1986-07-01", "1986-08-01", "1986-09-01"], "2": ["1985-09-01", "1985-10-01", "1985-11-01", "1985-12-01", "1986-01-01", "1986-02-01", "1986-03-01", "1986-04-01", "1986-05-01", "1986-06-01", "1986-07-01", "1986-08-01", "1986-09-01"], "3": ["1985-09-01", "1985-10-01", "1985-11-01", "1985-12-01", "1986-01-01", "1986-02-01", "1986-03-01", "1986-04-01", "1986-05-01", "1986-06-01", "1986-07-01", "1986-08-01", "1986-09-01"]} | {"1": ["1985-09-01", "1985-10-01", "1985-11-01", "1985-12-01", "1986-01-01", "1986-02-01", "1986-03-01", "1986-04-01", "1986-05-01", "1986-06-01", "1986-07-01", "1986-08-01", "1986-09-01"], "2": ["1985-09-01", "1985-10-01", "1985-11-01", "1985-12-01", "1986-01-01", "1986-02-01", "1986-03-01", "1986-04-01", "1986-05-01", "1986-06-01", "1986-07-01", "1986-08-01", "1986-09-01"], "3": ["1985-09-01", "1985-10-01", "1985-11-01", "1985-12-01", "1986-01-01", "1986-02-01", "1986-03-01", "1986-04-01", "1986-05-01", "1986-06-01", "1986-07-01", "1986-08-01", "1986-09-01"]} |
| PASS | yes | 1986-11-19_491220_November_19_1986.pdf page 2: title/grid/row/column evidence | all four evidence flags true for tables 1, 2, and 3 | {"1": {"aligned_numeric_columns": true, "coherent_month_rows": true, "credible_title": true, "visible_grid": true}, "2": {"aligned_numeric_columns": true, "coherent_month_rows": true, "credible_title": true, "visible_grid": true}, "3": {"aligned_numeric_columns": true, "coherent_month_rows": true, "credible_title": true, "visible_grid": true}} |
| PASS | yes | 1987-05-15_491226_May_15_1987.pdf: diagnostic path recorded | existing corpus path or explicit fallback path | /Users/danie/Personal-Macro-Research/SQL_database/OCR_pipeline/fraser_g6_issues/1980s/1987-05-15_491226_May_15_1987.pdf |
| PASS | yes | 1987-05-15_491226_May_15_1987.pdf page 1: page classification | table_page | table_page |
| PASS | yes | 1987-05-15_491226_May_15_1987.pdf page 1: adjustment status | NSA | NSA |
| PASS | yes | 1987-05-15_491226_May_15_1987.pdf page 1: semantic tables | [1, 2, 3] | [1, 2, 3] |
| PASS | yes | 1987-05-15_491226_May_15_1987.pdf page 1: table dimensions | {"1": {"columns": 6, "rows": 13}, "2": {"columns": 6, "rows": 13}, "3": {"columns": 6, "rows": 13}} | {"1": {"columns": 6, "rows": 13}, "2": {"columns": 6, "rows": 13}, "3": {"columns": 6, "rows": 13}} |
| PASS | yes | 1987-05-15_491226_May_15_1987.pdf page 1: complete ordered row-date sequence | {"1": ["1986-03-01", "1986-04-01", "1986-05-01", "1986-06-01", "1986-07-01", "1986-08-01", "1986-09-01", "1986-10-01", "1986-11-01", "1986-12-01", "1987-01-01", "1987-02-01", "1987-03-01"], "2": ["1986-03-01", "1986-04-01", "1986-05-01", "1986-06-01", "1986-07-01", "1986-08-01", "1986-09-01", "1986-10-01", "1986-11-01", "1986-12-01", "1987-01-01", "1987-02-01", "1987-03-01"], "3": ["1986-03-01", "1986-04-01", "1986-05-01", "1986-06-01", "1986-07-01", "1986-08-01", "1986-09-01", "1986-10-01", "1986-11-01", "1986-12-01", "1987-01-01", "1987-02-01", "1987-03-01"]} | {"1": ["1986-03-01", "1986-04-01", "1986-05-01", "1986-06-01", "1986-07-01", "1986-08-01", "1986-09-01", "1986-10-01", "1986-11-01", "1986-12-01", "1987-01-01", "1987-02-01", "1987-03-01"], "2": ["1986-03-01", "1986-04-01", "1986-05-01", "1986-06-01", "1986-07-01", "1986-08-01", "1986-09-01", "1986-10-01", "1986-11-01", "1986-12-01", "1987-01-01", "1987-02-01", "1987-03-01"], "3": ["1986-03-01", "1986-04-01", "1986-05-01", "1986-06-01", "1986-07-01", "1986-08-01", "1986-09-01", "1986-10-01", "1986-11-01", "1986-12-01", "1987-01-01", "1987-02-01", "1987-03-01"]} |
| PASS | yes | 1987-05-15_491226_May_15_1987.pdf page 1: title/grid/row/column evidence | all four evidence flags true for tables 1, 2, and 3 | {"1": {"aligned_numeric_columns": true, "coherent_month_rows": true, "credible_title": true, "visible_grid": true}, "2": {"aligned_numeric_columns": true, "coherent_month_rows": true, "credible_title": true, "visible_grid": true}, "3": {"aligned_numeric_columns": true, "coherent_month_rows": true, "credible_title": true, "visible_grid": true}} |
| PASS | yes | 1987-05-15_491226_May_15_1987.pdf page 2: page classification | table_page | table_page |
| PASS | yes | 1987-05-15_491226_May_15_1987.pdf page 2: adjustment status | SA | SA |
| PASS | yes | 1987-05-15_491226_May_15_1987.pdf page 2: semantic tables | [1, 2, 3] | [1, 2, 3] |
| PASS | yes | 1987-05-15_491226_May_15_1987.pdf page 2: table dimensions | {"1": {"columns": 5, "rows": 13}, "2": {"columns": 5, "rows": 13}, "3": {"columns": 5, "rows": 13}} | {"1": {"columns": 5, "rows": 13}, "2": {"columns": 5, "rows": 13}, "3": {"columns": 5, "rows": 13}} |
| PASS | yes | 1987-05-15_491226_May_15_1987.pdf page 2: complete ordered row-date sequence | {"1": ["1986-03-01", "1986-04-01", "1986-05-01", "1986-06-01", "1986-07-01", "1986-08-01", "1986-09-01", "1986-10-01", "1986-11-01", "1986-12-01", "1987-01-01", "1987-02-01", "1987-03-01"], "2": ["1986-03-01", "1986-04-01", "1986-05-01", "1986-06-01", "1986-07-01", "1986-08-01", "1986-09-01", "1986-10-01", "1986-11-01", "1986-12-01", "1987-01-01", "1987-02-01", "1987-03-01"], "3": ["1986-03-01", "1986-04-01", "1986-05-01", "1986-06-01", "1986-07-01", "1986-08-01", "1986-09-01", "1986-10-01", "1986-11-01", "1986-12-01", "1987-01-01", "1987-02-01", "1987-03-01"]} | {"1": ["1986-03-01", "1986-04-01", "1986-05-01", "1986-06-01", "1986-07-01", "1986-08-01", "1986-09-01", "1986-10-01", "1986-11-01", "1986-12-01", "1987-01-01", "1987-02-01", "1987-03-01"], "2": ["1986-03-01", "1986-04-01", "1986-05-01", "1986-06-01", "1986-07-01", "1986-08-01", "1986-09-01", "1986-10-01", "1986-11-01", "1986-12-01", "1987-01-01", "1987-02-01", "1987-03-01"], "3": ["1986-03-01", "1986-04-01", "1986-05-01", "1986-06-01", "1986-07-01", "1986-08-01", "1986-09-01", "1986-10-01", "1986-11-01", "1986-12-01", "1987-01-01", "1987-02-01", "1987-03-01"]} |
| PASS | yes | 1987-05-15_491226_May_15_1987.pdf page 2: title/grid/row/column evidence | all four evidence flags true for tables 1, 2, and 3 | {"1": {"aligned_numeric_columns": true, "coherent_month_rows": true, "credible_title": true, "visible_grid": true}, "2": {"aligned_numeric_columns": true, "coherent_month_rows": true, "credible_title": true, "visible_grid": true}, "3": {"aligned_numeric_columns": true, "coherent_month_rows": true, "credible_title": true, "visible_grid": true}} |
| PASS | yes | 1987-07-15_491228_July_15_1987.pdf: diagnostic path recorded | existing corpus path or explicit fallback path | /Users/danie/Personal-Macro-Research/SQL_database/OCR_pipeline/fraser_g6_issues/1980s/1987-07-15_491228_July_15_1987.pdf |
| PASS | yes | 1987-07-15_491228_July_15_1987.pdf page 1: page classification | table_page | table_page |
| PASS | yes | 1987-07-15_491228_July_15_1987.pdf page 1: adjustment status | NSA | NSA |
| PASS | yes | 1987-07-15_491228_July_15_1987.pdf page 1: semantic tables | [1, 2, 3] | [1, 2, 3] |
| PASS | yes | 1987-07-15_491228_July_15_1987.pdf page 1: table dimensions | {"1": {"columns": 6, "rows": 13}, "2": {"columns": 6, "rows": 13}, "3": {"columns": 6, "rows": 13}} | {"1": {"columns": 6, "rows": 13}, "2": {"columns": 6, "rows": 13}, "3": {"columns": 6, "rows": 13}} |
| PASS | yes | 1987-07-15_491228_July_15_1987.pdf page 1: complete ordered row-date sequence | {"1": ["1986-05-01", "1986-06-01", "1986-07-01", "1986-08-01", "1986-09-01", "1986-10-01", "1986-11-01", "1986-12-01", "1987-01-01", "1987-02-01", "1987-03-01", "1987-04-01", "1987-05-01"], "2": ["1986-05-01", "1986-06-01", "1986-07-01", "1986-08-01", "1986-09-01", "1986-10-01", "1986-11-01", "1986-12-01", "1987-01-01", "1987-02-01", "1987-03-01", "1987-04-01", "1987-05-01"], "3": ["1986-05-01", "1986-06-01", "1986-07-01", "1986-08-01", "1986-09-01", "1986-10-01", "1986-11-01", "1986-12-01", "1987-01-01", "1987-02-01", "1987-03-01", "1987-04-01", "1987-05-01"]} | {"1": ["1986-05-01", "1986-06-01", "1986-07-01", "1986-08-01", "1986-09-01", "1986-10-01", "1986-11-01", "1986-12-01", "1987-01-01", "1987-02-01", "1987-03-01", "1987-04-01", "1987-05-01"], "2": ["1986-05-01", "1986-06-01", "1986-07-01", "1986-08-01", "1986-09-01", "1986-10-01", "1986-11-01", "1986-12-01", "1987-01-01", "1987-02-01", "1987-03-01", "1987-04-01", "1987-05-01"], "3": ["1986-05-01", "1986-06-01", "1986-07-01", "1986-08-01", "1986-09-01", "1986-10-01", "1986-11-01", "1986-12-01", "1987-01-01", "1987-02-01", "1987-03-01", "1987-04-01", "1987-05-01"]} |
| PASS | yes | 1987-07-15_491228_July_15_1987.pdf page 1: title/grid/row/column evidence | all four evidence flags true for tables 1, 2, and 3 | {"1": {"aligned_numeric_columns": true, "coherent_month_rows": true, "credible_title": true, "visible_grid": true}, "2": {"aligned_numeric_columns": true, "coherent_month_rows": true, "credible_title": true, "visible_grid": true}, "3": {"aligned_numeric_columns": true, "coherent_month_rows": true, "credible_title": true, "visible_grid": true}} |
| PASS | yes | 1987-07-15_491228_July_15_1987.pdf page 2: page classification | table_page | table_page |
| PASS | yes | 1987-07-15_491228_July_15_1987.pdf page 2: adjustment status | SA | SA |
| PASS | yes | 1987-07-15_491228_July_15_1987.pdf page 2: semantic tables | [1, 2, 3] | [1, 2, 3] |
| PASS | yes | 1987-07-15_491228_July_15_1987.pdf page 2: table dimensions | {"1": {"columns": 5, "rows": 13}, "2": {"columns": 5, "rows": 13}, "3": {"columns": 5, "rows": 13}} | {"1": {"columns": 5, "rows": 13}, "2": {"columns": 5, "rows": 13}, "3": {"columns": 5, "rows": 13}} |
| PASS | yes | 1987-07-15_491228_July_15_1987.pdf page 2: complete ordered row-date sequence | {"1": ["1986-05-01", "1986-06-01", "1986-07-01", "1986-08-01", "1986-09-01", "1986-10-01", "1986-11-01", "1986-12-01", "1987-01-01", "1987-02-01", "1987-03-01", "1987-04-01", "1987-05-01"], "2": ["1986-05-01", "1986-06-01", "1986-07-01", "1986-08-01", "1986-09-01", "1986-10-01", "1986-11-01", "1986-12-01", "1987-01-01", "1987-02-01", "1987-03-01", "1987-04-01", "1987-05-01"], "3": ["1986-05-01", "1986-06-01", "1986-07-01", "1986-08-01", "1986-09-01", "1986-10-01", "1986-11-01", "1986-12-01", "1987-01-01", "1987-02-01", "1987-03-01", "1987-04-01", "1987-05-01"]} | {"1": ["1986-05-01", "1986-06-01", "1986-07-01", "1986-08-01", "1986-09-01", "1986-10-01", "1986-11-01", "1986-12-01", "1987-01-01", "1987-02-01", "1987-03-01", "1987-04-01", "1987-05-01"], "2": ["1986-05-01", "1986-06-01", "1986-07-01", "1986-08-01", "1986-09-01", "1986-10-01", "1986-11-01", "1986-12-01", "1987-01-01", "1987-02-01", "1987-03-01", "1987-04-01", "1987-05-01"], "3": ["1986-05-01", "1986-06-01", "1986-07-01", "1986-08-01", "1986-09-01", "1986-10-01", "1986-11-01", "1986-12-01", "1987-01-01", "1987-02-01", "1987-03-01", "1987-04-01", "1987-05-01"]} |
| PASS | yes | 1987-07-15_491228_July_15_1987.pdf page 2: title/grid/row/column evidence | all four evidence flags true for tables 1, 2, and 3 | {"1": {"aligned_numeric_columns": true, "coherent_month_rows": true, "credible_title": true, "visible_grid": true}, "2": {"aligned_numeric_columns": true, "coherent_month_rows": true, "credible_title": true, "visible_grid": true}, "3": {"aligned_numeric_columns": true, "coherent_month_rows": true, "credible_title": true, "visible_grid": true}} |
| PASS | yes | 1989-05-22_491246_May_22_1989.pdf: diagnostic path recorded | existing corpus path or explicit fallback path | /Users/danie/Personal-Macro-Research/SQL_database/OCR_pipeline/fraser_g6_issues/1980s/1989-05-22_491246_May_22_1989.pdf |
| PASS | yes | 1989-05-22_491246_May_22_1989.pdf page 1: page classification | table_page | table_page |
| PASS | yes | 1989-05-22_491246_May_22_1989.pdf page 1: adjustment status | NSA | NSA |
| PASS | yes | 1989-05-22_491246_May_22_1989.pdf page 1: semantic tables | [1, 2, 3] | [1, 2, 3] |
| PASS | yes | 1989-05-22_491246_May_22_1989.pdf page 1: table dimensions | {"1": {"columns": 6, "rows": 14}, "2": {"columns": 6, "rows": 14}, "3": {"columns": 6, "rows": 14}} | {"1": {"columns": 6, "rows": 14}, "2": {"columns": 6, "rows": 14}, "3": {"columns": 6, "rows": 14}} |
| PASS | yes | 1989-05-22_491246_May_22_1989.pdf page 1: complete ordered row-date sequence | {"1": ["1988-02-01", "1988-03-01", "1988-04-01", "1988-05-01", "1988-06-01", "1988-07-01", "1988-08-01", "1988-09-01", "1988-10-01", "1988-11-01", "1988-12-01", "1989-01-01", "1989-02-01", "1989-03-01"], "2": ["1988-02-01", "1988-03-01", "1988-04-01", "1988-05-01", "1988-06-01", "1988-07-01", "1988-08-01", "1988-09-01", "1988-10-01", "1988-11-01", "1988-12-01", "1989-01-01", "1989-02-01", "1989-03-01"], "3": ["1988-02-01", "1988-03-01", "1988-04-01", "1988-05-01", "1988-06-01", "1988-07-01", "1988-08-01", "1988-09-01", "1988-10-01", "1988-11-01", "1988-12-01", "1989-01-01", "1989-02-01", "1989-03-01"]} | {"1": ["1988-02-01", "1988-03-01", "1988-04-01", "1988-05-01", "1988-06-01", "1988-07-01", "1988-08-01", "1988-09-01", "1988-10-01", "1988-11-01", "1988-12-01", "1989-01-01", "1989-02-01", "1989-03-01"], "2": ["1988-02-01", "1988-03-01", "1988-04-01", "1988-05-01", "1988-06-01", "1988-07-01", "1988-08-01", "1988-09-01", "1988-10-01", "1988-11-01", "1988-12-01", "1989-01-01", "1989-02-01", "1989-03-01"], "3": ["1988-02-01", "1988-03-01", "1988-04-01", "1988-05-01", "1988-06-01", "1988-07-01", "1988-08-01", "1988-09-01", "1988-10-01", "1988-11-01", "1988-12-01", "1989-01-01", "1989-02-01", "1989-03-01"]} |
| PASS | yes | 1989-05-22_491246_May_22_1989.pdf page 1: title/grid/row/column evidence | all four evidence flags true for tables 1, 2, and 3 | {"1": {"aligned_numeric_columns": true, "coherent_month_rows": true, "credible_title": true, "visible_grid": true}, "2": {"aligned_numeric_columns": true, "coherent_month_rows": true, "credible_title": true, "visible_grid": true}, "3": {"aligned_numeric_columns": true, "coherent_month_rows": true, "credible_title": true, "visible_grid": true}} |
| PASS | yes | 1989-05-22_491246_May_22_1989.pdf page 2: page classification | table_page | table_page |
| PASS | yes | 1989-05-22_491246_May_22_1989.pdf page 2: adjustment status | SA | SA |
| PASS | yes | 1989-05-22_491246_May_22_1989.pdf page 2: semantic tables | [1, 2, 3] | [1, 2, 3] |
| PASS | yes | 1989-05-22_491246_May_22_1989.pdf page 2: table dimensions | {"1": {"columns": 5, "rows": 14}, "2": {"columns": 5, "rows": 14}, "3": {"columns": 5, "rows": 14}} | {"1": {"columns": 5, "rows": 14}, "2": {"columns": 5, "rows": 14}, "3": {"columns": 5, "rows": 14}} |
| PASS | yes | 1989-05-22_491246_May_22_1989.pdf page 2: complete ordered row-date sequence | {"1": ["1988-02-01", "1988-03-01", "1988-04-01", "1988-05-01", "1988-06-01", "1988-07-01", "1988-08-01", "1988-09-01", "1988-10-01", "1988-11-01", "1988-12-01", "1989-01-01", "1989-02-01", "1989-03-01"], "2": ["1988-02-01", "1988-03-01", "1988-04-01", "1988-05-01", "1988-06-01", "1988-07-01", "1988-08-01", "1988-09-01", "1988-10-01", "1988-11-01", "1988-12-01", "1989-01-01", "1989-02-01", "1989-03-01"], "3": ["1988-02-01", "1988-03-01", "1988-04-01", "1988-05-01", "1988-06-01", "1988-07-01", "1988-08-01", "1988-09-01", "1988-10-01", "1988-11-01", "1988-12-01", "1989-01-01", "1989-02-01", "1989-03-01"]} | {"1": ["1988-02-01", "1988-03-01", "1988-04-01", "1988-05-01", "1988-06-01", "1988-07-01", "1988-08-01", "1988-09-01", "1988-10-01", "1988-11-01", "1988-12-01", "1989-01-01", "1989-02-01", "1989-03-01"], "2": ["1988-02-01", "1988-03-01", "1988-04-01", "1988-05-01", "1988-06-01", "1988-07-01", "1988-08-01", "1988-09-01", "1988-10-01", "1988-11-01", "1988-12-01", "1989-01-01", "1989-02-01", "1989-03-01"], "3": ["1988-02-01", "1988-03-01", "1988-04-01", "1988-05-01", "1988-06-01", "1988-07-01", "1988-08-01", "1988-09-01", "1988-10-01", "1988-11-01", "1988-12-01", "1989-01-01", "1989-02-01", "1989-03-01"]} |
| PASS | yes | 1989-05-22_491246_May_22_1989.pdf page 2: title/grid/row/column evidence | all four evidence flags true for tables 1, 2, and 3 | {"1": {"aligned_numeric_columns": true, "coherent_month_rows": true, "credible_title": true, "visible_grid": true}, "2": {"aligned_numeric_columns": true, "coherent_month_rows": true, "credible_title": true, "visible_grid": true}, "3": {"aligned_numeric_columns": true, "coherent_month_rows": true, "credible_title": true, "visible_grid": true}} |
| PASS | yes | 1991-08-16_491273_August_16_1991.pdf: diagnostic path recorded | existing corpus path or explicit fallback path | /Users/danie/Personal-Macro-Research/SQL_database/OCR_pipeline/fraser_g6_issues/1990s/1991-08-16_491273_August_16_1991.pdf |
| PASS | yes | 1991-08-16_491273_August_16_1991.pdf page 1: page classification | unrelated_release_page | unrelated_release_page |
| PASS | yes | 1991-08-16_491273_August_16_1991.pdf page 1: non-table cells | 0 | 0 |
| PASS | yes | 1991-08-16_491273_August_16_1991.pdf page 2: page classification | table_page | table_page |
| PASS | yes | 1991-08-16_491273_August_16_1991.pdf page 2: adjustment status | SA | SA |
| PASS | yes | 1991-08-16_491273_August_16_1991.pdf page 2: semantic tables | [1, 2, 3] | [1, 2, 3] |
| PASS | yes | 1991-08-16_491273_August_16_1991.pdf page 2: table dimensions | {"1": {"columns": 6, "rows": 14}, "2": {"columns": 6, "rows": 14}, "3": {"columns": 6, "rows": 14}} | {"1": {"columns": 6, "rows": 14}, "2": {"columns": 6, "rows": 14}, "3": {"columns": 6, "rows": 14}} |
| PASS | yes | 1991-08-16_491273_August_16_1991.pdf page 2: complete ordered row-date sequence | {"1": ["1990-05-01", "1990-06-01", "1990-07-01", "1990-08-01", "1990-09-01", "1990-10-01", "1990-11-01", "1990-12-01", "1991-01-01", "1991-02-01", "1991-03-01", "1991-04-01", "1991-05-01", "1991-06-01"], "2": ["1990-05-01", "1990-06-01", "1990-07-01", "1990-08-01", "1990-09-01", "1990-10-01", "1990-11-01", "1990-12-01", "1991-01-01", "1991-02-01", "1991-03-01", "1991-04-01", "1991-05-01", "1991-06-01"], "3": ["1990-05-01", "1990-06-01", "1990-07-01", "1990-08-01", "1990-09-01", "1990-10-01", "1990-11-01", "1990-12-01", "1991-01-01", "1991-02-01", "1991-03-01", "1991-04-01", "1991-05-01", "1991-06-01"]} | {"1": ["1990-05-01", "1990-06-01", "1990-07-01", "1990-08-01", "1990-09-01", "1990-10-01", "1990-11-01", "1990-12-01", "1991-01-01", "1991-02-01", "1991-03-01", "1991-04-01", "1991-05-01", "1991-06-01"], "2": ["1990-05-01", "1990-06-01", "1990-07-01", "1990-08-01", "1990-09-01", "1990-10-01", "1990-11-01", "1990-12-01", "1991-01-01", "1991-02-01", "1991-03-01", "1991-04-01", "1991-05-01", "1991-06-01"], "3": ["1990-05-01", "1990-06-01", "1990-07-01", "1990-08-01", "1990-09-01", "1990-10-01", "1990-11-01", "1990-12-01", "1991-01-01", "1991-02-01", "1991-03-01", "1991-04-01", "1991-05-01", "1991-06-01"]} |
| PASS | yes | 1991-08-16_491273_August_16_1991.pdf page 2: title/grid/row/column evidence | all four evidence flags true for tables 1, 2, and 3 | {"1": {"aligned_numeric_columns": true, "coherent_month_rows": true, "credible_title": true, "visible_grid": true}, "2": {"aligned_numeric_columns": true, "coherent_month_rows": true, "credible_title": true, "visible_grid": true}, "3": {"aligned_numeric_columns": true, "coherent_month_rows": true, "credible_title": true, "visible_grid": true}} |
| PASS | yes | 1991-08-16_491273_August_16_1991.pdf page 3: page classification | table_page | table_page |
| PASS | yes | 1991-08-16_491273_August_16_1991.pdf page 3: adjustment status | NSA | NSA |
| PASS | yes | 1991-08-16_491273_August_16_1991.pdf page 3: semantic tables | [1, 2, 3] | [1, 2, 3] |
| PASS | yes | 1991-08-16_491273_August_16_1991.pdf page 3: table dimensions | {"1": {"columns": 6, "rows": 14}, "2": {"columns": 6, "rows": 14}, "3": {"columns": 6, "rows": 14}} | {"1": {"columns": 6, "rows": 14}, "2": {"columns": 6, "rows": 14}, "3": {"columns": 6, "rows": 14}} |
| PASS | yes | 1991-08-16_491273_August_16_1991.pdf page 3: complete ordered row-date sequence | {"1": ["1990-05-01", "1990-06-01", "1990-07-01", "1990-08-01", "1990-09-01", "1990-10-01", "1990-11-01", "1990-12-01", "1991-01-01", "1991-02-01", "1991-03-01", "1991-04-01", "1991-05-01", "1991-06-01"], "2": ["1990-05-01", "1990-06-01", "1990-07-01", "1990-08-01", "1990-09-01", "1990-10-01", "1990-11-01", "1990-12-01", "1991-01-01", "1991-02-01", "1991-03-01", "1991-04-01", "1991-05-01", "1991-06-01"], "3": ["1990-05-01", "1990-06-01", "1990-07-01", "1990-08-01", "1990-09-01", "1990-10-01", "1990-11-01", "1990-12-01", "1991-01-01", "1991-02-01", "1991-03-01", "1991-04-01", "1991-05-01", "1991-06-01"]} | {"1": ["1990-05-01", "1990-06-01", "1990-07-01", "1990-08-01", "1990-09-01", "1990-10-01", "1990-11-01", "1990-12-01", "1991-01-01", "1991-02-01", "1991-03-01", "1991-04-01", "1991-05-01", "1991-06-01"], "2": ["1990-05-01", "1990-06-01", "1990-07-01", "1990-08-01", "1990-09-01", "1990-10-01", "1990-11-01", "1990-12-01", "1991-01-01", "1991-02-01", "1991-03-01", "1991-04-01", "1991-05-01", "1991-06-01"], "3": ["1990-05-01", "1990-06-01", "1990-07-01", "1990-08-01", "1990-09-01", "1990-10-01", "1990-11-01", "1990-12-01", "1991-01-01", "1991-02-01", "1991-03-01", "1991-04-01", "1991-05-01", "1991-06-01"]} |
| PASS | yes | 1991-08-16_491273_August_16_1991.pdf page 3: title/grid/row/column evidence | all four evidence flags true for tables 1, 2, and 3 | {"1": {"aligned_numeric_columns": true, "coherent_month_rows": true, "credible_title": true, "visible_grid": true}, "2": {"aligned_numeric_columns": true, "coherent_month_rows": true, "credible_title": true, "visible_grid": true}, "3": {"aligned_numeric_columns": true, "coherent_month_rows": true, "credible_title": true, "visible_grid": true}} |
| PASS | yes | 1993-08-16_491297_August_16_1993.pdf: diagnostic path recorded | existing corpus path or explicit fallback path | /Users/danie/Personal-Macro-Research/SQL_database/OCR_pipeline/fraser_g6_issues/1990s/1993-08-16_491297_August_16_1993.pdf |
| PASS | yes | 1993-08-16_491297_August_16_1993.pdf page 1: page classification | table_page | table_page |
| PASS | yes | 1993-08-16_491297_August_16_1993.pdf page 1: adjustment status | NSA | NSA |
| PASS | yes | 1993-08-16_491297_August_16_1993.pdf page 1: semantic tables | [1, 2, 3] | [1, 2, 3] |
| PASS | yes | 1993-08-16_491297_August_16_1993.pdf page 1: table dimensions | {"1": {"columns": 5, "rows": 14}, "2": {"columns": 5, "rows": 14}, "3": {"columns": 5, "rows": 14}} | {"1": {"columns": 5, "rows": 14}, "2": {"columns": 5, "rows": 14}, "3": {"columns": 5, "rows": 14}} |
| PASS | yes | 1993-08-16_491297_August_16_1993.pdf page 1: complete ordered row-date sequence | {"1": ["1992-05-01", "1992-06-01", "1992-07-01", "1992-08-01", "1992-09-01", "1992-10-01", "1992-11-01", "1992-12-01", "1993-01-01", "1993-02-01", "1993-03-01", "1993-04-01", "1993-05-01", "1993-06-01"], "2": ["1992-05-01", "1992-06-01", "1992-07-01", "1992-08-01", "1992-09-01", "1992-10-01", "1992-11-01", "1992-12-01", "1993-01-01", "1993-02-01", "1993-03-01", "1993-04-01", "1993-05-01", "1993-06-01"], "3": ["1992-05-01", "1992-06-01", "1992-07-01", "1992-08-01", "1992-09-01", "1992-10-01", "1992-11-01", "1992-12-01", "1993-01-01", "1993-02-01", "1993-03-01", "1993-04-01", "1993-05-01", "1993-06-01"]} | {"1": ["1992-05-01", "1992-06-01", "1992-07-01", "1992-08-01", "1992-09-01", "1992-10-01", "1992-11-01", "1992-12-01", "1993-01-01", "1993-02-01", "1993-03-01", "1993-04-01", "1993-05-01", "1993-06-01"], "2": ["1992-05-01", "1992-06-01", "1992-07-01", "1992-08-01", "1992-09-01", "1992-10-01", "1992-11-01", "1992-12-01", "1993-01-01", "1993-02-01", "1993-03-01", "1993-04-01", "1993-05-01", "1993-06-01"], "3": ["1992-05-01", "1992-06-01", "1992-07-01", "1992-08-01", "1992-09-01", "1992-10-01", "1992-11-01", "1992-12-01", "1993-01-01", "1993-02-01", "1993-03-01", "1993-04-01", "1993-05-01", "1993-06-01"]} |
| PASS | yes | 1993-08-16_491297_August_16_1993.pdf page 1: title/grid/row/column evidence | all four evidence flags true for tables 1, 2, and 3 | {"1": {"aligned_numeric_columns": true, "coherent_month_rows": true, "credible_title": true, "visible_grid": true}, "2": {"aligned_numeric_columns": true, "coherent_month_rows": true, "credible_title": true, "visible_grid": true}, "3": {"aligned_numeric_columns": true, "coherent_month_rows": true, "credible_title": true, "visible_grid": true}} |
| PASS | yes | 1993-08-16_491297_August_16_1993.pdf page 2: page classification | table_page | table_page |
| PASS | yes | 1993-08-16_491297_August_16_1993.pdf page 2: adjustment status | SA | SA |
| PASS | yes | 1993-08-16_491297_August_16_1993.pdf page 2: semantic tables | [1, 2, 3] | [1, 2, 3] |
| PASS | yes | 1993-08-16_491297_August_16_1993.pdf page 2: table dimensions | {"1": {"columns": 5, "rows": 14}, "2": {"columns": 5, "rows": 14}, "3": {"columns": 5, "rows": 14}} | {"1": {"columns": 5, "rows": 14}, "2": {"columns": 5, "rows": 14}, "3": {"columns": 5, "rows": 14}} |
| PASS | yes | 1993-08-16_491297_August_16_1993.pdf page 2: complete ordered row-date sequence | {"1": ["1992-05-01", "1992-06-01", "1992-07-01", "1992-08-01", "1992-09-01", "1992-10-01", "1992-11-01", "1992-12-01", "1993-01-01", "1993-02-01", "1993-03-01", "1993-04-01", "1993-05-01", "1993-06-01"], "2": ["1992-05-01", "1992-06-01", "1992-07-01", "1992-08-01", "1992-09-01", "1992-10-01", "1992-11-01", "1992-12-01", "1993-01-01", "1993-02-01", "1993-03-01", "1993-04-01", "1993-05-01", "1993-06-01"], "3": ["1992-05-01", "1992-06-01", "1992-07-01", "1992-08-01", "1992-09-01", "1992-10-01", "1992-11-01", "1992-12-01", "1993-01-01", "1993-02-01", "1993-03-01", "1993-04-01", "1993-05-01", "1993-06-01"]} | {"1": ["1992-05-01", "1992-06-01", "1992-07-01", "1992-08-01", "1992-09-01", "1992-10-01", "1992-11-01", "1992-12-01", "1993-01-01", "1993-02-01", "1993-03-01", "1993-04-01", "1993-05-01", "1993-06-01"], "2": ["1992-05-01", "1992-06-01", "1992-07-01", "1992-08-01", "1992-09-01", "1992-10-01", "1992-11-01", "1992-12-01", "1993-01-01", "1993-02-01", "1993-03-01", "1993-04-01", "1993-05-01", "1993-06-01"], "3": ["1992-05-01", "1992-06-01", "1992-07-01", "1992-08-01", "1992-09-01", "1992-10-01", "1992-11-01", "1992-12-01", "1993-01-01", "1993-02-01", "1993-03-01", "1993-04-01", "1993-05-01", "1993-06-01"]} |
| PASS | yes | 1993-08-16_491297_August_16_1993.pdf page 2: title/grid/row/column evidence | all four evidence flags true for tables 1, 2, and 3 | {"1": {"aligned_numeric_columns": true, "coherent_month_rows": true, "credible_title": true, "visible_grid": true}, "2": {"aligned_numeric_columns": true, "coherent_month_rows": true, "credible_title": true, "visible_grid": true}, "3": {"aligned_numeric_columns": true, "coherent_month_rows": true, "credible_title": true, "visible_grid": true}} |
| PASS | yes | 1985-12-13_491209_December_13_1985.pdf: diagnostic path recorded | existing corpus path or explicit fallback path | /Users/danie/Personal-Macro-Research/SQL_database/OCR_pipeline/fraser_g6_issues/1980s/1985-12-13_491209_December_13_1985.pdf |
| PASS | yes | 1985-12-13_491209_December_13_1985.pdf page 1: page classification | table_page | table_page |
| PASS | yes | 1985-12-13_491209_December_13_1985.pdf page 1: adjustment status | SA | SA |
| PASS | yes | 1985-12-13_491209_December_13_1985.pdf page 1: semantic tables | [1, 2, 3] | [1, 2, 3] |
| PASS | yes | 1985-12-13_491209_December_13_1985.pdf page 1: table dimensions | {"1": {"columns": 5, "rows": 13}, "2": {"columns": 5, "rows": 13}, "3": {"columns": 5, "rows": 13}} | {"1": {"columns": 5, "rows": 13}, "2": {"columns": 5, "rows": 13}, "3": {"columns": 5, "rows": 13}} |
| PASS | yes | 1985-12-13_491209_December_13_1985.pdf page 1: complete ordered row-date sequence | {"1": ["1984-10-01", "1984-11-01", "1984-12-01", "1985-01-01", "1985-02-01", "1985-03-01", "1985-04-01", "1985-05-01", "1985-06-01", "1985-07-01", "1985-08-01", "1985-09-01", "1985-10-01"], "2": ["1984-10-01", "1984-11-01", "1984-12-01", "1985-01-01", "1985-02-01", "1985-03-01", "1985-04-01", "1985-05-01", "1985-06-01", "1985-07-01", "1985-08-01", "1985-09-01", "1985-10-01"], "3": ["1984-10-01", "1984-11-01", "1984-12-01", "1985-01-01", "1985-02-01", "1985-03-01", "1985-04-01", "1985-05-01", "1985-06-01", "1985-07-01", "1985-08-01", "1985-09-01", "1985-10-01"]} | {"1": ["1984-10-01", "1984-11-01", "1984-12-01", "1985-01-01", "1985-02-01", "1985-03-01", "1985-04-01", "1985-05-01", "1985-06-01", "1985-07-01", "1985-08-01", "1985-09-01", "1985-10-01"], "2": ["1984-10-01", "1984-11-01", "1984-12-01", "1985-01-01", "1985-02-01", "1985-03-01", "1985-04-01", "1985-05-01", "1985-06-01", "1985-07-01", "1985-08-01", "1985-09-01", "1985-10-01"], "3": ["1984-10-01", "1984-11-01", "1984-12-01", "1985-01-01", "1985-02-01", "1985-03-01", "1985-04-01", "1985-05-01", "1985-06-01", "1985-07-01", "1985-08-01", "1985-09-01", "1985-10-01"]} |
| PASS | yes | 1985-12-13_491209_December_13_1985.pdf page 1: title/grid/row/column evidence | all four evidence flags true for tables 1, 2, and 3 | {"1": {"aligned_numeric_columns": true, "coherent_month_rows": true, "credible_title": true, "visible_grid": true}, "2": {"aligned_numeric_columns": true, "coherent_month_rows": true, "credible_title": true, "visible_grid": true}, "3": {"aligned_numeric_columns": true, "coherent_month_rows": true, "credible_title": true, "visible_grid": true}} |
| PASS | yes | 1985-12-13_491209_December_13_1985.pdf page 2: page classification | table_page | table_page |
| PASS | yes | 1985-12-13_491209_December_13_1985.pdf page 2: adjustment status | NSA | NSA |
| PASS | yes | 1985-12-13_491209_December_13_1985.pdf page 2: semantic tables | [1, 2, 3] | [1, 2, 3] |
| PASS | yes | 1985-12-13_491209_December_13_1985.pdf page 2: table dimensions | {"1": {"columns": 6, "rows": 13}, "2": {"columns": 6, "rows": 13}, "3": {"columns": 6, "rows": 13}} | {"1": {"columns": 6, "rows": 13}, "2": {"columns": 6, "rows": 13}, "3": {"columns": 6, "rows": 13}} |
| PASS | yes | 1985-12-13_491209_December_13_1985.pdf page 2: complete ordered row-date sequence | {"1": ["1984-10-01", "1984-11-01", "1984-12-01", "1985-01-01", "1985-02-01", "1985-03-01", "1985-04-01", "1985-05-01", "1985-06-01", "1985-07-01", "1985-08-01", "1985-09-01", "1985-10-01"], "2": ["1984-10-01", "1984-11-01", "1984-12-01", "1985-01-01", "1985-02-01", "1985-03-01", "1985-04-01", "1985-05-01", "1985-06-01", "1985-07-01", "1985-08-01", "1985-09-01", "1985-10-01"], "3": ["1984-10-01", "1984-11-01", "1984-12-01", "1985-01-01", "1985-02-01", "1985-03-01", "1985-04-01", "1985-05-01", "1985-06-01", "1985-07-01", "1985-08-01", "1985-09-01", "1985-10-01"]} | {"1": ["1984-10-01", "1984-11-01", "1984-12-01", "1985-01-01", "1985-02-01", "1985-03-01", "1985-04-01", "1985-05-01", "1985-06-01", "1985-07-01", "1985-08-01", "1985-09-01", "1985-10-01"], "2": ["1984-10-01", "1984-11-01", "1984-12-01", "1985-01-01", "1985-02-01", "1985-03-01", "1985-04-01", "1985-05-01", "1985-06-01", "1985-07-01", "1985-08-01", "1985-09-01", "1985-10-01"], "3": ["1984-10-01", "1984-11-01", "1984-12-01", "1985-01-01", "1985-02-01", "1985-03-01", "1985-04-01", "1985-05-01", "1985-06-01", "1985-07-01", "1985-08-01", "1985-09-01", "1985-10-01"]} |
| PASS | yes | 1985-12-13_491209_December_13_1985.pdf page 2: title/grid/row/column evidence | all four evidence flags true for tables 1, 2, and 3 | {"1": {"aligned_numeric_columns": true, "coherent_month_rows": true, "credible_title": true, "visible_grid": true}, "2": {"aligned_numeric_columns": true, "coherent_month_rows": true, "credible_title": true, "visible_grid": true}, "3": {"aligned_numeric_columns": true, "coherent_month_rows": true, "credible_title": true, "visible_grid": true}} |
| PASS | yes | 1989-03-15_491244_March_15_1989.pdf: diagnostic path recorded | existing corpus path or explicit fallback path | /Users/danie/Personal-Macro-Research/SQL_database/OCR_pipeline/fraser_g6_issues/1980s/1989-03-15_491244_March_15_1989.pdf |
| PASS | yes | 1989-03-15_491244_March_15_1989.pdf page 1: page classification | table_page | table_page |
| PASS | yes | 1989-03-15_491244_March_15_1989.pdf page 1: adjustment status | SA | SA |
| PASS | yes | 1989-03-15_491244_March_15_1989.pdf page 1: semantic tables | [1, 2, 3] | [1, 2, 3] |
| PASS | yes | 1989-03-15_491244_March_15_1989.pdf page 1: table dimensions | {"1": {"columns": 5, "rows": 14}, "2": {"columns": 5, "rows": 14}, "3": {"columns": 5, "rows": 14}} | {"1": {"columns": 5, "rows": 14}, "2": {"columns": 5, "rows": 14}, "3": {"columns": 5, "rows": 14}} |
| PASS | yes | 1989-03-15_491244_March_15_1989.pdf page 1: complete ordered row-date sequence | {"1": ["1987-12-01", "1988-01-01", "1988-02-01", "1988-03-01", "1988-04-01", "1988-05-01", "1988-06-01", "1988-07-01", "1988-08-01", "1988-09-01", "1988-10-01", "1988-11-01", "1988-12-01", "1989-01-01"], "2": ["1987-12-01", "1988-01-01", "1988-02-01", "1988-03-01", "1988-04-01", "1988-05-01", "1988-06-01", "1988-07-01", "1988-08-01", "1988-09-01", "1988-10-01", "1988-11-01", "1988-12-01", "1989-01-01"], "3": ["1987-12-01", "1988-01-01", "1988-02-01", "1988-03-01", "1988-04-01", "1988-05-01", "1988-06-01", "1988-07-01", "1988-08-01", "1988-09-01", "1988-10-01", "1988-11-01", "1988-12-01", "1989-01-01"]} | {"1": ["1987-12-01", "1988-01-01", "1988-02-01", "1988-03-01", "1988-04-01", "1988-05-01", "1988-06-01", "1988-07-01", "1988-08-01", "1988-09-01", "1988-10-01", "1988-11-01", "1988-12-01", "1989-01-01"], "2": ["1987-12-01", "1988-01-01", "1988-02-01", "1988-03-01", "1988-04-01", "1988-05-01", "1988-06-01", "1988-07-01", "1988-08-01", "1988-09-01", "1988-10-01", "1988-11-01", "1988-12-01", "1989-01-01"], "3": ["1987-12-01", "1988-01-01", "1988-02-01", "1988-03-01", "1988-04-01", "1988-05-01", "1988-06-01", "1988-07-01", "1988-08-01", "1988-09-01", "1988-10-01", "1988-11-01", "1988-12-01", "1989-01-01"]} |
| PASS | yes | 1989-03-15_491244_March_15_1989.pdf page 1: title/grid/row/column evidence | all four evidence flags true for tables 1, 2, and 3 | {"1": {"aligned_numeric_columns": true, "coherent_month_rows": true, "credible_title": true, "visible_grid": true}, "2": {"aligned_numeric_columns": true, "coherent_month_rows": true, "credible_title": true, "visible_grid": true}, "3": {"aligned_numeric_columns": true, "coherent_month_rows": true, "credible_title": true, "visible_grid": true}} |
| PASS | yes | 1989-03-15_491244_March_15_1989.pdf page 2: page classification | table_page | table_page |
| PASS | yes | 1989-03-15_491244_March_15_1989.pdf page 2: adjustment status | NSA | NSA |
| PASS | yes | 1989-03-15_491244_March_15_1989.pdf page 2: semantic tables | [1, 2, 3] | [1, 2, 3] |
| PASS | yes | 1989-03-15_491244_March_15_1989.pdf page 2: table dimensions | {"1": {"columns": 6, "rows": 14}, "2": {"columns": 6, "rows": 14}, "3": {"columns": 6, "rows": 14}} | {"1": {"columns": 6, "rows": 14}, "2": {"columns": 6, "rows": 14}, "3": {"columns": 6, "rows": 14}} |
| PASS | yes | 1989-03-15_491244_March_15_1989.pdf page 2: complete ordered row-date sequence | {"1": ["1987-12-01", "1988-01-01", "1988-02-01", "1988-03-01", "1988-04-01", "1988-05-01", "1988-06-01", "1988-07-01", "1988-08-01", "1988-09-01", "1988-10-01", "1988-11-01", "1988-12-01", "1989-01-01"], "2": ["1987-12-01", "1988-01-01", "1988-02-01", "1988-03-01", "1988-04-01", "1988-05-01", "1988-06-01", "1988-07-01", "1988-08-01", "1988-09-01", "1988-10-01", "1988-11-01", "1988-12-01", "1989-01-01"], "3": ["1987-12-01", "1988-01-01", "1988-02-01", "1988-03-01", "1988-04-01", "1988-05-01", "1988-06-01", "1988-07-01", "1988-08-01", "1988-09-01", "1988-10-01", "1988-11-01", "1988-12-01", "1989-01-01"]} | {"1": ["1987-12-01", "1988-01-01", "1988-02-01", "1988-03-01", "1988-04-01", "1988-05-01", "1988-06-01", "1988-07-01", "1988-08-01", "1988-09-01", "1988-10-01", "1988-11-01", "1988-12-01", "1989-01-01"], "2": ["1987-12-01", "1988-01-01", "1988-02-01", "1988-03-01", "1988-04-01", "1988-05-01", "1988-06-01", "1988-07-01", "1988-08-01", "1988-09-01", "1988-10-01", "1988-11-01", "1988-12-01", "1989-01-01"], "3": ["1987-12-01", "1988-01-01", "1988-02-01", "1988-03-01", "1988-04-01", "1988-05-01", "1988-06-01", "1988-07-01", "1988-08-01", "1988-09-01", "1988-10-01", "1988-11-01", "1988-12-01", "1989-01-01"]} |
| PASS | yes | 1989-03-15_491244_March_15_1989.pdf page 2: title/grid/row/column evidence | all four evidence flags true for tables 1, 2, and 3 | {"1": {"aligned_numeric_columns": true, "coherent_month_rows": true, "credible_title": true, "visible_grid": true}, "2": {"aligned_numeric_columns": true, "coherent_month_rows": true, "credible_title": true, "visible_grid": true}, "3": {"aligned_numeric_columns": true, "coherent_month_rows": true, "credible_title": true, "visible_grid": true}} |
| PASS | yes | 1992-12-17_491289_December_17_1992.pdf: diagnostic path recorded | existing corpus path or explicit fallback path | /Users/danie/Personal-Macro-Research/SQL_database/OCR_pipeline/fraser_g6_issues/1990s/1992-12-17_491289_December_17_1992.pdf |
| PASS | yes | 1992-12-17_491289_December_17_1992.pdf page 1: page classification | table_page | table_page |
| PASS | yes | 1992-12-17_491289_December_17_1992.pdf page 1: adjustment status | SA | SA |
| PASS | yes | 1992-12-17_491289_December_17_1992.pdf page 1: semantic tables | [1, 2, 3] | [1, 2, 3] |
| PASS | yes | 1992-12-17_491289_December_17_1992.pdf page 1: table dimensions | {"1": {"columns": 5, "rows": 14}, "2": {"columns": 5, "rows": 14}, "3": {"columns": 5, "rows": 14}} | {"1": {"columns": 5, "rows": 14}, "2": {"columns": 5, "rows": 14}, "3": {"columns": 5, "rows": 14}} |
| PASS | yes | 1992-12-17_491289_December_17_1992.pdf page 1: complete ordered row-date sequence | {"1": ["1991-09-01", "1991-10-01", "1991-11-01", "1991-12-01", "1992-01-01", "1992-02-01", "1992-03-01", "1992-04-01", "1992-05-01", "1992-06-01", "1992-07-01", "1992-08-01", "1992-09-01", "1992-10-01"], "2": ["1991-09-01", "1991-10-01", "1991-11-01", "1991-12-01", "1992-01-01", "1992-02-01", "1992-03-01", "1992-04-01", "1992-05-01", "1992-06-01", "1992-07-01", "1992-08-01", "1992-09-01", "1992-10-01"], "3": ["1991-09-01", "1991-10-01", "1991-11-01", "1991-12-01", "1992-01-01", "1992-02-01", "1992-03-01", "1992-04-01", "1992-05-01", "1992-06-01", "1992-07-01", "1992-08-01", "1992-09-01", "1992-10-01"]} | {"1": ["1991-09-01", "1991-10-01", "1991-11-01", "1991-12-01", "1992-01-01", "1992-02-01", "1992-03-01", "1992-04-01", "1992-05-01", "1992-06-01", "1992-07-01", "1992-08-01", "1992-09-01", "1992-10-01"], "2": ["1991-09-01", "1991-10-01", "1991-11-01", "1991-12-01", "1992-01-01", "1992-02-01", "1992-03-01", "1992-04-01", "1992-05-01", "1992-06-01", "1992-07-01", "1992-08-01", "1992-09-01", "1992-10-01"], "3": ["1991-09-01", "1991-10-01", "1991-11-01", "1991-12-01", "1992-01-01", "1992-02-01", "1992-03-01", "1992-04-01", "1992-05-01", "1992-06-01", "1992-07-01", "1992-08-01", "1992-09-01", "1992-10-01"]} |
| PASS | yes | 1992-12-17_491289_December_17_1992.pdf page 1: title/grid/row/column evidence | all four evidence flags true for tables 1, 2, and 3 | {"1": {"aligned_numeric_columns": true, "coherent_month_rows": true, "credible_title": true, "visible_grid": true}, "2": {"aligned_numeric_columns": true, "coherent_month_rows": true, "credible_title": true, "visible_grid": true}, "3": {"aligned_numeric_columns": true, "coherent_month_rows": true, "credible_title": true, "visible_grid": true}} |
| PASS | yes | 1992-12-17_491289_December_17_1992.pdf page 2: page classification | table_page | table_page |
| PASS | yes | 1992-12-17_491289_December_17_1992.pdf page 2: adjustment status | NSA | NSA |
| PASS | yes | 1992-12-17_491289_December_17_1992.pdf page 2: semantic tables | [1, 2, 3] | [1, 2, 3] |
| PASS | yes | 1992-12-17_491289_December_17_1992.pdf page 2: table dimensions | {"1": {"columns": 5, "rows": 14}, "2": {"columns": 5, "rows": 14}, "3": {"columns": 5, "rows": 14}} | {"1": {"columns": 5, "rows": 14}, "2": {"columns": 5, "rows": 14}, "3": {"columns": 5, "rows": 14}} |
| PASS | yes | 1992-12-17_491289_December_17_1992.pdf page 2: complete ordered row-date sequence | {"1": ["1991-09-01", "1991-10-01", "1991-11-01", "1991-12-01", "1992-01-01", "1992-02-01", "1992-03-01", "1992-04-01", "1992-05-01", "1992-06-01", "1992-07-01", "1992-08-01", "1992-09-01", "1992-10-01"], "2": ["1991-09-01", "1991-10-01", "1991-11-01", "1991-12-01", "1992-01-01", "1992-02-01", "1992-03-01", "1992-04-01", "1992-05-01", "1992-06-01", "1992-07-01", "1992-08-01", "1992-09-01", "1992-10-01"], "3": ["1991-09-01", "1991-10-01", "1991-11-01", "1991-12-01", "1992-01-01", "1992-02-01", "1992-03-01", "1992-04-01", "1992-05-01", "1992-06-01", "1992-07-01", "1992-08-01", "1992-09-01", "1992-10-01"]} | {"1": ["1991-09-01", "1991-10-01", "1991-11-01", "1991-12-01", "1992-01-01", "1992-02-01", "1992-03-01", "1992-04-01", "1992-05-01", "1992-06-01", "1992-07-01", "1992-08-01", "1992-09-01", "1992-10-01"], "2": ["1991-09-01", "1991-10-01", "1991-11-01", "1991-12-01", "1992-01-01", "1992-02-01", "1992-03-01", "1992-04-01", "1992-05-01", "1992-06-01", "1992-07-01", "1992-08-01", "1992-09-01", "1992-10-01"], "3": ["1991-09-01", "1991-10-01", "1991-11-01", "1991-12-01", "1992-01-01", "1992-02-01", "1992-03-01", "1992-04-01", "1992-05-01", "1992-06-01", "1992-07-01", "1992-08-01", "1992-09-01", "1992-10-01"]} |
| PASS | yes | 1992-12-17_491289_December_17_1992.pdf page 2: title/grid/row/column evidence | all four evidence flags true for tables 1, 2, and 3 | {"1": {"aligned_numeric_columns": true, "coherent_month_rows": true, "credible_title": true, "visible_grid": true}, "2": {"aligned_numeric_columns": true, "coherent_month_rows": true, "credible_title": true, "visible_grid": true}, "3": {"aligned_numeric_columns": true, "coherent_month_rows": true, "credible_title": true, "visible_grid": true}} |
| PASS | yes | 1995-01-12_491314_January_12_1995.pdf: diagnostic path recorded | existing corpus path or explicit fallback path | /Users/danie/Personal-Macro-Research/SQL_database/OCR_pipeline/fraser_g6_issues/1990s/1995-01-12_491314_January_12_1995.pdf |
| PASS | yes | 1995-01-12_491314_January_12_1995.pdf page 1: page classification | table_page | table_page |
| PASS | yes | 1995-01-12_491314_January_12_1995.pdf page 1: adjustment status | NSA | NSA |
| PASS | yes | 1995-01-12_491314_January_12_1995.pdf page 1: semantic tables | [1, 2, 3] | [1, 2, 3] |
| PASS | yes | 1995-01-12_491314_January_12_1995.pdf page 1: table dimensions | {"1": {"columns": 5, "rows": 14}, "2": {"columns": 5, "rows": 14}, "3": {"columns": 5, "rows": 14}} | {"1": {"columns": 5, "rows": 14}, "2": {"columns": 5, "rows": 14}, "3": {"columns": 5, "rows": 14}} |
| PASS | yes | 1995-01-12_491314_January_12_1995.pdf page 1: complete ordered row-date sequence | {"1": ["1993-10-01", "1993-11-01", "1993-12-01", "1994-01-01", "1994-02-01", "1994-03-01", "1994-04-01", "1994-05-01", "1994-06-01", "1994-07-01", "1994-08-01", "1994-09-01", "1994-10-01", "1994-11-01"], "2": ["1993-10-01", "1993-11-01", "1993-12-01", "1994-01-01", "1994-02-01", "1994-03-01", "1994-04-01", "1994-05-01", "1994-06-01", "1994-07-01", "1994-08-01", "1994-09-01", "1994-10-01", "1994-11-01"], "3": ["1993-10-01", "1993-11-01", "1993-12-01", "1994-01-01", "1994-02-01", "1994-03-01", "1994-04-01", "1994-05-01", "1994-06-01", "1994-07-01", "1994-08-01", "1994-09-01", "1994-10-01", "1994-11-01"]} | {"1": ["1993-10-01", "1993-11-01", "1993-12-01", "1994-01-01", "1994-02-01", "1994-03-01", "1994-04-01", "1994-05-01", "1994-06-01", "1994-07-01", "1994-08-01", "1994-09-01", "1994-10-01", "1994-11-01"], "2": ["1993-10-01", "1993-11-01", "1993-12-01", "1994-01-01", "1994-02-01", "1994-03-01", "1994-04-01", "1994-05-01", "1994-06-01", "1994-07-01", "1994-08-01", "1994-09-01", "1994-10-01", "1994-11-01"], "3": ["1993-10-01", "1993-11-01", "1993-12-01", "1994-01-01", "1994-02-01", "1994-03-01", "1994-04-01", "1994-05-01", "1994-06-01", "1994-07-01", "1994-08-01", "1994-09-01", "1994-10-01", "1994-11-01"]} |
| PASS | yes | 1995-01-12_491314_January_12_1995.pdf page 1: title/grid/row/column evidence | all four evidence flags true for tables 1, 2, and 3 | {"1": {"aligned_numeric_columns": true, "coherent_month_rows": true, "credible_title": true, "visible_grid": true}, "2": {"aligned_numeric_columns": true, "coherent_month_rows": true, "credible_title": true, "visible_grid": true}, "3": {"aligned_numeric_columns": true, "coherent_month_rows": true, "credible_title": true, "visible_grid": true}} |
| PASS | yes | 1995-01-12_491314_January_12_1995.pdf page 2: page classification | table_page | table_page |
| PASS | yes | 1995-01-12_491314_January_12_1995.pdf page 2: adjustment status | SA | SA |
| PASS | yes | 1995-01-12_491314_January_12_1995.pdf page 2: semantic tables | [1, 2, 3] | [1, 2, 3] |
| PASS | yes | 1995-01-12_491314_January_12_1995.pdf page 2: table dimensions | {"1": {"columns": 5, "rows": 14}, "2": {"columns": 5, "rows": 14}, "3": {"columns": 5, "rows": 14}} | {"1": {"columns": 5, "rows": 14}, "2": {"columns": 5, "rows": 14}, "3": {"columns": 5, "rows": 14}} |
| PASS | yes | 1995-01-12_491314_January_12_1995.pdf page 2: complete ordered row-date sequence | {"1": ["1993-10-01", "1993-11-01", "1993-12-01", "1994-01-01", "1994-02-01", "1994-03-01", "1994-04-01", "1994-05-01", "1994-06-01", "1994-07-01", "1994-08-01", "1994-09-01", "1994-10-01", "1994-11-01"], "2": ["1993-10-01", "1993-11-01", "1993-12-01", "1994-01-01", "1994-02-01", "1994-03-01", "1994-04-01", "1994-05-01", "1994-06-01", "1994-07-01", "1994-08-01", "1994-09-01", "1994-10-01", "1994-11-01"], "3": ["1993-10-01", "1993-11-01", "1993-12-01", "1994-01-01", "1994-02-01", "1994-03-01", "1994-04-01", "1994-05-01", "1994-06-01", "1994-07-01", "1994-08-01", "1994-09-01", "1994-10-01", "1994-11-01"]} | {"1": ["1993-10-01", "1993-11-01", "1993-12-01", "1994-01-01", "1994-02-01", "1994-03-01", "1994-04-01", "1994-05-01", "1994-06-01", "1994-07-01", "1994-08-01", "1994-09-01", "1994-10-01", "1994-11-01"], "2": ["1993-10-01", "1993-11-01", "1993-12-01", "1994-01-01", "1994-02-01", "1994-03-01", "1994-04-01", "1994-05-01", "1994-06-01", "1994-07-01", "1994-08-01", "1994-09-01", "1994-10-01", "1994-11-01"], "3": ["1993-10-01", "1993-11-01", "1993-12-01", "1994-01-01", "1994-02-01", "1994-03-01", "1994-04-01", "1994-05-01", "1994-06-01", "1994-07-01", "1994-08-01", "1994-09-01", "1994-10-01", "1994-11-01"]} |
| PASS | yes | 1995-01-12_491314_January_12_1995.pdf page 2: title/grid/row/column evidence | all four evidence flags true for tables 1, 2, and 3 | {"1": {"aligned_numeric_columns": true, "coherent_month_rows": true, "credible_title": true, "visible_grid": true}, "2": {"aligned_numeric_columns": true, "coherent_month_rows": true, "credible_title": true, "visible_grid": true}, "3": {"aligned_numeric_columns": true, "coherent_month_rows": true, "credible_title": true, "visible_grid": true}} |
| PASS | yes | 1991-08-16 page 1: conflicting release code | G.10 | G.10 |
| PASS | yes | 1982-10-14 page 1: revision/methodology text preserved | metadata record containing revised, benchmark, or seasonal adjustment text | ["revision_notice"] |
| PASS | yes | 1980-08-14_491143_August_14_1980.pdf: rendered sample value | 50478.0 | 50478.0 |
| PASS | yes | 1980-08-18_491144_August_18_1980_Corrected_copy.pdf: rendered sample value | 50878.0 | 50878.0 |
| PASS | yes | 1982-10-14_491170_October_14_1982.pdf: rendered sample value | 87495.5 | 87495.5 |
| PASS | yes | 1982-12-10_491172_December_10_1982.pdf: rendered sample value | 84194.9 | 84194.9 |
| PASS | yes | 1987-05-15_491226_May_15_1987.pdf: rendered sample value | 179715.2 | 179715.2 |
| PASS | yes | 1987-07-15_491228_July_15_1987.pdf: rendered sample value | 184827.4 | 184827.4 |
| PASS | yes | 1989-05-22_491246_May_22_1989.pdf: rendered sample value | 208899.2 | 208899.2 |
| PASS | yes | 1991-08-16_491273_August_16_1991.pdf: rendered sample value | 278383.5 | 278383.5 |
| PASS | yes | 1993-08-16_491297_August_16_1993.pdf: rendered sample value | 293706.9 | 293706.9 |
| PASS | yes | 1985-12-13_491209_December_13_1985.pdf page 1 table 1 1984-10-01 demand/all_banks: value and provenance | {"eligible_image_source": true, "normalization_recorded": true, "one_decimal": true, "value_numeric": "142907.2"} | {"normalization_rule": "exact_one_decimal", "selected_source": "true_high_resolution_600dpi_crop", "selection_reason": "accepted reported candidate '142907.2'; score=21.40, independent_support=6, embedded_locator_support=False, margin=9.599999999999998", "value_numeric": "142907.2", "value_status": "reported"} |
| PASS | yes | 1985-12-13_491209_December_13_1985.pdf page 2 table 1 1984-10-01 demand/all_banks: value and provenance | {"eligible_image_source": true, "normalization_recorded": true, "one_decimal": true, "value_numeric": "141249.5"} | {"normalization_rule": "merged_trailing_decimal_digit_across_image_ocr_passes", "selected_source": "true_high_resolution_480dpi_crop", "selection_reason": "accepted reported candidate '141249.5'; score=23.90, independent_support=2, embedded_locator_support=True, margin=7.999999999999998", "value_numeric": "141249.5", "value_status": "reported"} |
| PASS | yes | 1985-12-13_491209_December_13_1985.pdf page 2 table 2 1984-10-01 demand/all_banks: value and provenance | {"eligible_image_source": true, "normalization_recorded": true, "one_decimal": true, "value_numeric": "294.3"} | {"normalization_rule": "exact_one_decimal", "selected_source": "true_high_resolution_480dpi_crop", "selection_reason": "accepted reported candidate '294.3'; score=31.88, independent_support=6, embedded_locator_support=True, margin=inf", "value_numeric": "294.3", "value_status": "reported"} |
| PASS | yes | 1985-12-13_491209_December_13_1985.pdf page 2 table 3 1984-10-01 demand/all_banks: value and provenance | {"eligible_image_source": true, "normalization_recorded": true, "one_decimal": true, "value_numeric": "479.9"} | {"normalization_rule": "exact_one_decimal", "selected_source": "true_high_resolution_480dpi_crop", "selection_reason": "accepted reported candidate '479.9'; score=28.02, independent_support=3, embedded_locator_support=True, margin=13.7104", "value_numeric": "479.9", "value_status": "reported"} |
| PASS | yes | 1989-03-15_491244_March_15_1989.pdf page 1 table 1 1987-12-01 demand/all_banks: value and provenance | {"eligible_image_source": true, "normalization_recorded": true, "one_decimal": true, "value_numeric": "203290.6"} | {"normalization_rule": "removed_extra_trailing_decimal_digit", "selected_source": "rendered_sparse_ocr", "selection_reason": "accepted reported candidate '203290.6'; score=19.17, independent_support=2, embedded_locator_support=True, margin=6.1364", "value_numeric": "203290.6", "value_status": "reported"} |
| PASS | yes | 1989-03-15_491244_March_15_1989.pdf page 1 table 2 1987-12-01 demand/all_banks: value and provenance | {"eligible_image_source": true, "normalization_recorded": true, "one_decimal": true, "value_numeric": "344.3"} | {"normalization_rule": "exact_one_decimal", "selected_source": "rendered_ocr", "selection_reason": "accepted reported candidate '344.3'; score=22.24, independent_support=2, embedded_locator_support=True, margin=10.2424", "value_numeric": "344.3", "value_status": "reported"} |
| PASS | yes | 1989-03-15_491244_March_15_1989.pdf page 1 table 3 1987-12-01 demand/all_banks: value and provenance | {"eligible_image_source": true, "normalization_recorded": true, "one_decimal": true, "value_numeric": "590.4"} | {"normalization_rule": "exact_one_decimal", "selected_source": "targeted_upscaled_240dpi_crop", "selection_reason": "accepted reported candidate '590.4'; score=22.19, independent_support=2, embedded_locator_support=True, margin=12.502799999999997", "value_numeric": "590.4", "value_status": "reported"} |
| PASS | yes | 1989-03-15_491244_March_15_1989.pdf page 2 table 1 1988-02-01 demand/all_banks: value and provenance | {"eligible_image_source": true, "normalization_recorded": true, "one_decimal": true, "value_numeric": "208899.2"} | {"normalization_rule": "exact_one_decimal", "selected_source": "targeted_upscaled_240dpi_crop", "selection_reason": "accepted reported candidate '208899.2'; score=33.48, independent_support=9, embedded_locator_support=True, margin=21.6808", "value_numeric": "208899.2", "value_status": "reported"} |
| PASS | yes | 1989-03-15_491244_March_15_1989.pdf page 2 table 2 1988-02-01 demand/all_banks: value and provenance | {"eligible_image_source": true, "normalization_recorded": true, "one_decimal": true, "value_numeric": "342.2"} | {"normalization_rule": "exact_one_decimal", "selected_source": "targeted_upscaled_240dpi_crop", "selection_reason": "accepted reported candidate '342.2'; score=20.70, independent_support=2, embedded_locator_support=True, margin=7.865600000000001", "value_numeric": "342.2", "value_status": "reported"} |
| PASS | yes | 1989-03-15_491244_March_15_1989.pdf page 2 table 3 1988-02-01 demand/all_banks: value and provenance | {"eligible_image_source": true, "normalization_recorded": true, "one_decimal": true, "value_numeric": "610.5"} | {"normalization_rule": "exact_one_decimal", "selected_source": "rendered_ocr", "selection_reason": "accepted reported candidate '610.5'; score=22.50, independent_support=2, embedded_locator_support=True, margin=inf", "value_numeric": "610.5", "value_status": "reported"} |
| PASS | yes | 1992-12-17_491289_December_17_1992.pdf page 1 table 1 1991-09-01 demand/all_banks: value and provenance | {"eligible_image_source": true, "normalization_recorded": true, "one_decimal": true, "value_numeric": "281469.0"} | {"normalization_rule": "exact_one_decimal", "selected_source": "rendered_ocr", "selection_reason": "accepted reported candidate '281469.0'; score=22.48, independent_support=2, embedded_locator_support=True, margin=inf", "value_numeric": "281469.0", "value_status": "reported"} |
| PASS | yes | 1992-12-17_491289_December_17_1992.pdf page 1 table 2 1991-09-01 demand/all_banks: value and provenance | {"eligible_image_source": true, "normalization_recorded": true, "one_decimal": true, "value_numeric": "344.1"} | {"normalization_rule": "exact_one_decimal", "selected_source": "rendered_ocr", "selection_reason": "accepted reported candidate '344.1'; score=22.55, independent_support=2, embedded_locator_support=True, margin=inf", "value_numeric": "344.1", "value_status": "reported"} |
| PASS | yes | 1992-12-17_491289_December_17_1992.pdf page 1 table 3 1991-09-01 demand/all_banks: value and provenance | {"eligible_image_source": true, "normalization_recorded": true, "one_decimal": true, "value_numeric": "817.9"} | {"normalization_rule": "exact_one_decimal", "selected_source": "rendered_ocr", "selection_reason": "accepted reported candidate '817.9'; score=21.64, independent_support=1, embedded_locator_support=True, margin=inf", "value_numeric": "817.9", "value_status": "reported"} |
| PASS | yes | 1992-12-17_491289_December_17_1992.pdf page 1 table 1 1991-10-01 demand/all_banks: value and provenance | {"eligible_image_source": true, "normalization_recorded": true, "one_decimal": true, "value_numeric": "287974.5"} | {"normalization_rule": "exact_one_decimal", "selected_source": "rendered_sparse_ocr", "selection_reason": "accepted reported candidate '287974.5'; score=21.95, independent_support=2, embedded_locator_support=True, margin=16.9432", "value_numeric": "287974.5", "value_status": "reported"} |
| PASS | yes | 1992-12-17_491289_December_17_1992.pdf page 1 table 2 1991-10-01 demand/all_banks: value and provenance | {"eligible_image_source": true, "normalization_recorded": true, "one_decimal": true, "value_numeric": "344.0"} | {"normalization_rule": "exact_one_decimal", "selected_source": "rendered_ocr", "selection_reason": "accepted reported candidate '344.0'; score=22.66, independent_support=2, embedded_locator_support=True, margin=inf", "value_numeric": "344.0", "value_status": "reported"} |
| PASS | yes | 1992-12-17_491289_December_17_1992.pdf page 1 table 3 1991-10-01 demand/all_banks: value and provenance | {"eligible_image_source": true, "normalization_recorded": true, "one_decimal": true, "value_numeric": "837.1"} | {"normalization_rule": "exact_one_decimal", "selected_source": "rendered_ocr", "selection_reason": "accepted reported candidate '837.1'; score=22.64, independent_support=2, embedded_locator_support=True, margin=inf", "value_numeric": "837.1", "value_status": "reported"} |
| PASS | yes | 1992-12-17_491289_December_17_1992.pdf page 1 table 1 1992-10-01 demand/all_banks: value and provenance | {"eligible_image_source": true, "normalization_recorded": true, "one_decimal": true, "value_numeric": "328491.6"} | {"normalization_rule": "exact_one_decimal", "selected_source": "rendered_ocr", "selection_reason": "accepted reported candidate '328491.6'; score=22.43, independent_support=2, embedded_locator_support=True, margin=inf", "value_numeric": "328491.6", "value_status": "reported"} |
| PASS | yes | 1992-12-17_491289_December_17_1992.pdf page 1 table 2 1992-10-01 demand/all_banks: value and provenance | {"eligible_image_source": true, "normalization_recorded": true, "one_decimal": true, "value_numeric": "398.9"} | {"normalization_rule": "exact_one_decimal", "selected_source": "rendered_ocr", "selection_reason": "accepted reported candidate '398.9'; score=22.67, independent_support=2, embedded_locator_support=True, margin=inf", "value_numeric": "398.9", "value_status": "reported"} |
| PASS | yes | 1992-12-17_491289_December_17_1992.pdf page 1 table 3 1992-10-01 demand/all_banks: value and provenance | {"eligible_image_source": true, "normalization_recorded": true, "one_decimal": true, "value_numeric": "823.4"} | {"normalization_rule": "exact_one_decimal", "selected_source": "rendered_ocr", "selection_reason": "accepted reported candidate '823.4'; score=22.64, independent_support=2, embedded_locator_support=True, margin=inf", "value_numeric": "823.4", "value_status": "reported"} |
| PASS | yes | 1992-12-17_491289_December_17_1992.pdf page 2 table 1 1991-09-01 demand/all_banks: value and provenance | {"eligible_image_source": true, "normalization_recorded": true, "one_decimal": true, "value_numeric": "271983.5"} | {"normalization_rule": "exact_one_decimal", "selected_source": "rendered_ocr", "selection_reason": "accepted reported candidate '271983.5'; score=22.47, independent_support=2, embedded_locator_support=True, margin=inf", "value_numeric": "271983.5", "value_status": "reported"} |
| PASS | yes | 1995-01-12_491314_January_12_1995.pdf page 1 table 1 1994-03-01 demand/all_banks: value and provenance | {"eligible_image_source": true, "normalization_recorded": true, "one_decimal": true, "value_numeric": "406806.7"} | {"normalization_rule": "spatially_separated_trailing_decimal_digit", "selected_source": "rendered_ocr", "selection_reason": "accepted reported candidate '406806.7'; score=22.26, independent_support=2, embedded_locator_support=True, margin=6.5", "value_numeric": "406806.7", "value_status": "reported"} |
| PASS | yes | 1995-01-12_491314_January_12_1995.pdf page 1 table 1 1994-05-01 demand/other_banks: value and provenance | {"eligible_image_source": true, "normalization_recorded": true, "one_decimal": true, "value_numeric": "175563.0"} | {"normalization_rule": "spatially_separated_trailing_decimal_digit", "selected_source": "rendered_ocr", "selection_reason": "selected existing OCR candidate by turnover_equals_debits_divided_by_deposits; residual=0.0118441, tolerance=0.104934, sources=['rendered_ocr:page', 'rendered_sparse_ocr:page', 'targeted_upscaled_240dpi_crop:gray_numeric_psm7', 'targeted_upscaled_240dpi_crop:gray_psm7']", "value_numeric": "175563.0", "value_status": "reported"} |
| PASS | yes | 1995-01-12_491314_January_12_1995.pdf page 1 table 1 1994-11-01 demand/other_banks: value and provenance | {"eligible_image_source": true, "normalization_recorded": true, "one_decimal": true, "value_numeric": "174620.5"} | {"normalization_rule": "spatially_separated_trailing_decimal_digit", "selected_source": "rendered_ocr", "selection_reason": "accepted reported candidate '174620.5'; score=24.56, independent_support=5, embedded_locator_support=True, margin=17.5", "value_numeric": "174620.5", "value_status": "reported"} |
| PASS | yes | 1995-01-12_491314_January_12_1995.pdf page 1 table 2 1994-11-01 demand/all_banks: value and provenance | {"eligible_image_source": true, "normalization_recorded": true, "one_decimal": true, "value_numeric": "456.9"} | {"normalization_rule": "spatially_separated_trailing_decimal_digit", "selected_source": "rendered_sparse_ocr", "selection_reason": "accepted reported candidate '456.9'; score=22.02, independent_support=2, embedded_locator_support=True, margin=inf", "value_numeric": "456.9", "value_status": "reported"} |
| PASS | yes | 1995-01-12_491314_January_12_1995.pdf page 1 table 3 1994-11-01 demand/all_banks: value and provenance | {"eligible_image_source": true, "normalization_recorded": true, "one_decimal": true, "value_numeric": "786.4"} | {"normalization_rule": "spatially_separated_trailing_decimal_digit", "selected_source": "rendered_ocr", "selection_reason": "accepted reported candidate '786.4'; score=22.59, independent_support=2, embedded_locator_support=True, margin=inf", "value_numeric": "786.4", "value_status": "reported"} |
| PASS | yes | 1995-01-12_491314_January_12_1995.pdf page 2 table 1 1994-02-01 demand/all_banks: value and provenance | {"eligible_image_source": true, "normalization_recorded": true, "one_decimal": true, "value_numeric": "371844.5"} | {"normalization_rule": "spatially_separated_trailing_decimal_digit", "selected_source": "rendered_ocr", "selection_reason": "accepted reported candidate '371844.5'; score=22.42, independent_support=4, embedded_locator_support=True, margin=9.5", "value_numeric": "371844.5", "value_status": "reported"} |
| PASS | yes | 1995-01-12_491314_January_12_1995.pdf page 2 table 1 1994-03-01 demand/new_york_city: value and provenance | {"eligible_image_source": true, "normalization_recorded": true, "one_decimal": true, "value_numeric": "210684.6"} | {"normalization_rule": "spatially_separated_trailing_decimal_digit", "selected_source": "rendered_ocr", "selection_reason": "accepted reported candidate '210684.6'; score=20.71, independent_support=3, embedded_locator_support=True, margin=8.500000000000002", "value_numeric": "210684.6", "value_status": "reported"} |
| PASS | yes | 1995-01-12_491314_January_12_1995.pdf page 2 table 1 1994-04-01 other_checkable/: value and provenance | {"eligible_image_source": true, "normalization_recorded": true, "one_decimal": true, "value_numeric": "3589.4"} | {"normalization_rule": "spatially_separated_trailing_decimal_digit", "selected_source": "rendered_ocr", "selection_reason": "accepted reported candidate '3589.4'; score=30.37, independent_support=6, embedded_locator_support=True, margin=17.3672", "value_numeric": "3589.4", "value_status": "reported"} |
| PASS | yes | 1995-01-12_491314_January_12_1995.pdf page 2 table 1 1994-10-01 demand/all_banks: value and provenance | {"eligible_image_source": true, "normalization_recorded": true, "one_decimal": true, "value_numeric": "345939.9"} | {"normalization_rule": "periods_interpreted_as_thousands_separators", "selected_source": "targeted_upscaled_240dpi_crop", "selection_reason": "accepted reported candidate '345939.9'; score=17.80, independent_support=3, embedded_locator_support=True, margin=3.4292000000000016", "value_numeric": "345939.9", "value_status": "reported"} |
| PASS | yes | 1995-01-12_491314_January_12_1995.pdf page 2 table 3 1993-10-01 demand/all_banks: value and provenance | {"eligible_image_source": true, "normalization_recorded": true, "one_decimal": true, "value_numeric": "740.4"} | {"normalization_rule": "exact_one_decimal", "selected_source": "rendered_ocr", "selection_reason": "accepted reported candidate '740.4'; score=21.65, independent_support=1, embedded_locator_support=True, margin=inf", "value_numeric": "740.4", "value_status": "reported"} |
| PASS | yes | 1980-08-18_491144_August_18_1980_Corrected_copy.pdf: overlapping page vintages retained | at least one logical overlap on distinct physical pages | 147 |
| PASS | yes | 1980-08-14_491143_August_14_1980.pdf: overlapping page vintages retained | at least one logical overlap on distinct physical pages | 147 |
| PASS | yes | 1980-08-18 corrected copy: C annotations preserved separately | at least one C annotation and numeric values without a concatenated C | ["C", "R", "c", "c C", "r"] |
| PASS | yes | 1982-12-10 page 2: targeted cell-crop OCR attempted | > 0 targeted cells | 183 |
| PASS | yes | diagnostic set: duplicate physical cell keys | 0 | 0 |
| PASS | yes | diagnostic set: recognized months silently reassigned | 0 | 0 |
| PASS | yes | diagnostic set: cells from non-table pages | 0 | 0 |
| PASS | yes | diagnostic set: unresolved conflicts retain full OCR audit | all unresolved cells have candidates, sources, confidence, normalization, and selection status | {"fully_auditable": true, "unresolved_cells": 267} |
| PASS | yes | diagnostic set: reported embedded-selected values | 0 | 0 |
| PASS | yes | diagnostic set: reported values outside one-decimal grammar | 0 | 0 |
| PASS | yes | diagnostic set: unresolved or strong nonzero row shifts | 0 | 0 |
| PASS | yes | diagnostic set: Era 2 seven-column component mappings | ["ats_now", "business", "other", "total"] | all complete |
| PASS | yes | 1985-12-13_491209_December_13_1985.pdf: true high-resolution OCR coverage | {"attempts": "> 0", "unresolved_without_attempt": 0} | {"attempts": 369, "final_unresolved": 42, "recoveries": 148, "unresolved_without_attempt": 0} |
| PASS | yes | 1989-03-15_491244_March_15_1989.pdf: true high-resolution OCR coverage | {"attempts": "> 0", "unresolved_without_attempt": 0} | {"attempts": 346, "final_unresolved": 73, "recoveries": 101, "unresolved_without_attempt": 0} |
| PASS | yes | diagnostic set: final extraction-error issue consistency | 267 | 267 |

## Before / after

| Metric | Before | After | Change |
|:--|--:|--:|--:|
| cells_total | 87963 | 87963 | 0 |
| reported_cells | 85034 | 85397 | 363 |
| extraction_errors | 1912 | 1492 | -420 |
| ocr_candidate_conflicts | 14644 | 30966 | 16322 |
| blank_cells | 451 | 447 | -4 |
| not_available_cells | 566 | 627 | 61 |
| missing_tables | 0 | 0 | 0 |
| false_positive_table_pages |  | 0 |  |
| inferred_dates | 652 | 758 | 106 |
| contradictory_month_assignments | 16 | 0 | -16 |
| duplicate_physical_keys | 0 | 0 | 0 |
| failed_all_bank_checks | 505 | 1356 | 851 |
| failed_component_total_checks | 757 | 143 | -614 |
| failed_turnover_ratio_checks | 2904 | 3783 | 879 |
| low_confidence_cells | 7899 | 12490 | 4591 |
| embedded_only_numeric_candidates | 344 | 118 | -226 |
| selected_embedded_values | 3361 | 0 | -3361 |
| non_one_decimal_reported_values | 1367 | 0 | -1367 |
| true_high_resolution_attempts | 0 | 27300 | 27300 |
| true_high_resolution_recoveries | 0 | 3868 | 3868 |
| unresolved_row_offsets | 0 | 0 | 0 |
| complete_date_sequence_failures | 4 | 0 | -4 |
| additive_validation_failures | 1262 | 1499 | 237 |
| component_mapping_failures | 0 | 0 | 0 |
| stale_issue_count_mismatches | 2996 | 0 | -2996 |
| manual_review_queue_size |  | 15795 |  |
| demoted_reported_cells | 0 | 0 | 0 |

- The pre-pass manual-review queue did not exist; its baseline size is therefore reported as unavailable.

## Core metrics by era

| Era | Cells | Reported | Extraction errors | Embedded selected | Non-one-decimal | Manual review |
|--:|--:|--:|--:|--:|--:|--:|
| 1 | 7722 | 7100 | 240 | 0 | 0 | 972 |
| 2 | 7917 | 7853 | 54 | 0 | 0 | 1253 |
| 3 | 1950 | 1835 | 105 | 0 | 0 | 762 |
| 4 | 40008 | 38916 | 988 | 0 | 0 | 11113 |
| 5 | 4284 | 4278 | 6 | 0 | 0 | 696 |
| 6 | 6552 | 6004 | 2 | 0 | 0 | 310 |
| 7 | 6090 | 6073 | 10 | 0 | 0 | 219 |
| 8 | 13440 | 13338 | 87 | 0 | 0 | 470 |

## Demotions

- Previously reported cells demoted to unresolved because eligible image support was absent: 0.

## Full-corpus structural gate

- PASS: no blocking skipped-table, false-positive-page, physical-key, column-coverage, or file-processing failures.

## Remaining high-error files

| Source file | Unresolved OCR cells | Page classification | Date alignment | Column template | Arithmetic validation |
|:--|--:|--:|--:|--:|--:|
| 1980s/1989-03-15_491244_March_15_1989.pdf | 64 | 0 | 0 | 0 | 66 |
| 1980s/1984-02-13_491186_February_13_1984.pdf | 56 | 0 | 0 | 0 | 43 |
| 1980s/1986-08-12_491217_August_12_1986.pdf | 48 | 0 | 0 | 0 | 42 |
| 1980s/1983-02-09_491174_February_9_1983.pdf | 44 | 0 | 0 | 0 | 63 |
| 1970s/1977-10-13_491110_October_13_1977.pdf | 41 | 0 | 0 | 0 | 0 |
| 1980s/1985-12-13_491209_December_13_1985.pdf | 37 | 0 | 0 | 0 | 101 |
| 1980s/1982-12-10_491172_December_10_1982.pdf | 36 | 0 | 0 | 0 | 101 |
| 1980s/1989-09-19_491250_September_19_1989.pdf | 36 | 0 | 0 | 0 | 31 |
| 1980s/1988-03-15_491234_March_15_1988.pdf | 36 | 0 | 0 | 0 | 58 |
| 1980s/1983-11-17_491183_November_17_1983.pdf | 36 | 0 | 0 | 0 | 38 |
| 1980s/1984-04-17_491188_April_17_1984.pdf | 35 | 0 | 0 | 0 | 39 |
| 1970s/1978-01-11_491113_January_11_1978.pdf | 34 | 0 | 0 | 0 | 3 |
| 1980s/1983-08-12_491180_August_12_1983.pdf | 32 | 0 | 0 | 0 | 27 |
| 1980s/1989-12-26_491253_December_26_1989.pdf | 30 | 0 | 0 | 0 | 64 |
| 1980s/1987-07-15_491228_July_15_1987.pdf | 30 | 0 | 0 | 0 | 89 |
| 1980s/1984-08-13_491192_August_13_1984.pdf | 29 | 0 | 0 | 0 | 91 |
| 1980s/1983-12-27_491184_December_27_1983.pdf | 28 | 0 | 0 | 0 | 64 |
| 1970s/1977-11-10_491111_November_10_1977.pdf | 27 | 0 | 0 | 0 | 13 |
| 1980s/1984-01-10_491185_January_10_1984.pdf | 25 | 0 | 0 | 0 | 114 |
| 1970s/1977-12-08_491112_December_8_1977.pdf | 25 | 0 | 0 | 0 | 10 |

## Manual review workload

- Unresolved OCR cells: 1,492
- Page-classification issues: 0
- Date-alignment issues: 0
- Release-date metadata issues: 1
- Column-template issues: 0
- Arithmetic-validation issues: 5,282

## Manual review by era

| Era | Unresolved OCR cells | Review-queue cells |
|--:|--:|--:|
| 1 | 240 | 972 |
| 2 | 54 | 1253 |
| 3 | 105 | 762 |
| 4 | 988 | 11113 |
| 5 | 6 | 696 |
| 6 | 2 | 310 |
| 7 | 10 | 219 |
| 8 | 87 | 470 |

## Manual review by source file

| Source file | Review-queue cells | Unresolved OCR cells |
|:--|--:|--:|
| 1980s/1984-01-10_491185_January_10_1984.pdf | 324 | 25 |
| 1980s/1988-08-15_491239_August_15_1988.pdf | 309 | 13 |
| 1980s/1982-12-10_491172_December_10_1982.pdf | 300 | 36 |
| 1980s/1985-12-13_491209_December_13_1985.pdf | 291 | 37 |
| 1980s/1987-07-15_491228_July_15_1987.pdf | 286 | 30 |
| 1980s/1984-08-13_491192_August_13_1984.pdf | 275 | 29 |
| 1980s/1989-02-21_491243_February_21_1989.pdf | 260 | 18 |
| 1980s/1987-02-20_491223_February_20_1987.pdf | 235 | 4 |
| 1980s/1989-03-15_491244_March_15_1989.pdf | 232 | 64 |
| 1980s/1988-05-17_491236_May_17_1988.pdf | 228 | 2 |
| 1980s/1983-02-09_491174_February_9_1983.pdf | 222 | 44 |
| 1980s/1983-03-22_491175_March_22_1983.pdf | 220 | 21 |
| 1980s/1983-04-15_491176_April_15_1983.pdf | 219 | 10 |
| 1980s/1987-06-15_491227_June_15_1987.pdf | 217 | 4 |
| 1980s/1984-07-13_491191_July_13_1984.pdf | 212 | 2 |
| 1980s/1984-06-15_491190_June_15_1984.pdf | 211 | 10 |
| 1990s/1991-09-19_491274_September_19_1991.pdf | 211 | 0 |
| 1980s/1983-12-27_491184_December_27_1983.pdf | 207 | 28 |
| 1980s/1986-07-14_491216_July_14_1986.pdf | 201 | 21 |
| 1980s/1989-12-26_491253_December_26_1989.pdf | 199 | 30 |
| 1980s/1988-03-15_491234_March_15_1988.pdf | 194 | 36 |
| 1980s/1984-09-11_491193_September_11_1984.pdf | 189 | 4 |
| 1990s/1991-06-27_491271_June_27_1991.pdf | 188 | 0 |
| 1980s/1984-10-15_491194_October_15_1984.pdf | 187 | 18 |
| 1990s/1991-10-22_491275_October_22_1991.pdf | 179 | 0 |
| 1980s/1980-08-18_491144_August_18_1980_Corrected_copy.pdf | 178 | 14 |
| 1980s/1984-02-13_491186_February_13_1984.pdf | 175 | 56 |
| 1990s/1993-06-15_491295_June_15_1993.pdf | 170 | 0 |
| 1980s/1980-08-14_491143_August_14_1980.pdf | 169 | 4 |
| 1980s/1984-12-14_491196_December_14_1984.pdf | 167 | 8 |
| 1980s/1989-11-22_491252_November_22_1989.pdf | 167 | 23 |
| 1980s/1986-03-18_491212_March_18_1986.pdf | 166 | 9 |
| 1980s/1986-08-12_491217_August_12_1986.pdf | 165 | 48 |
| 1980s/1989-10-18_491251_October_18_1989.pdf | 163 | 20 |
| 1990s/1992-10-21_491287_October_21_1992.pdf | 152 | 1 |
| 1980s/1983-06-21_491178_June_21_1983.pdf | 149 | 3 |
| 1980s/1986-11-19_491220_November_19_1986.pdf | 149 | 7 |
| 1990s/1990-12-06_491264_December_6_1990.pdf | 148 | 9 |
| 1990s/1990-06-12_491259_June_12_1990.pdf | 144 | 14 |
| 1980s/1981-10-15_491158_October_15_1981.pdf | 143 | 0 |
| 1980s/1983-07-12_491179_July_12_1983.pdf | 143 | 1 |
| 1980s/1981-04-07_491152_April_7_1981.pdf | 138 | 4 |
| 1980s/1984-04-17_491188_April_17_1984.pdf | 136 | 35 |
| 1980s/1987-08-14_491229_August_14_1987.pdf | 136 | 12 |
| 1980s/1985-11-15_491207_November_15_1985.pdf | 133 | 10 |
| 1980s/1988-02-16_491233_February_16_1988.pdf | 133 | 7 |
| 1980s/1982-10-14_491170_October_14_1982.pdf | 132 | 11 |
| 1990s/1994-11-17_491312_November_17_1994.pdf | 128 | 20 |
| 1980s/1983-11-17_491183_November_17_1983.pdf | 126 | 36 |
| 1980s/1989-09-19_491250_September_19_1989.pdf | 122 | 36 |
| 1980s/1988-12-27_491241_December_27_1988.pdf | 118 | 9 |
| 1980s/1986-05-14_491214_May_14_1986.pdf | 114 | 14 |
| 1980s/1988-06-15_491237_June_15_1988.pdf | 113 | 5 |
| 1980s/1989-01-27_491242_January_27_1989.pdf | 113 | 11 |
| 1980s/1985-10-15_491206_October_15_1985.pdf | 112 | 3 |
| 1980s/1984-03-20_491187_March_20_1984.pdf | 111 | 0 |
| 1980s/1983-09-26_491181_September_26_1983.pdf | 110 | 1 |
| 1980s/1984-11-20_491195_November_20_1984.pdf | 108 | 15 |
| 1980s/1983-08-12_491180_August_12_1983.pdf | 107 | 32 |
| 1980s/1988-01-25_491232_January_25_1988.pdf | 105 | 3 |
| 1980s/1988-07-15_491238_July_15_1988.pdf | 104 | 5 |
| 1980s/1989-05-22_491246_May_22_1989.pdf | 104 | 2 |
| 1990s/1994-03-21_491304_March_21_1994.pdf | 98 | 14 |
| 1990s/1990-04-19_491257_April_19_1990.pdf | 97 | 0 |
| 1980s/1988-04-15_491235_April_15_1988.pdf | 94 | 1 |
| 1980s/1986-12-16_491221_December_16_1986.pdf | 93 | 7 |
| 1980s/1986-06-13_491215_June_13_1986.pdf | 92 | 8 |
| 1980s/1983-10-13_491182_October_13_1983.pdf | 91 | 17 |
| 1980s/1987-11-20_491230_November_20_1987.pdf | 90 | 7 |
| 1980s/1982-02-23_491163_February_23_1982.pdf | 89 | 9 |
| 1980s/1985-07-12_491203_July_12_1985.pdf | 89 | 5 |
| 1980s/1983-05-09_491177_May_9_1983.pdf | 88 | 4 |
| 1980s/1982-11-10_491171_November_10_1982.pdf | 85 | 14 |
| 1970s/1978-10-13_491122_October_13_1978.pdf | 83 | 5 |
| 1970s/1978-12-12_491124_December_12_1978.pdf | 82 | 1 |
| 1990s/1990-08-16_491261_August_16_1990.pdf | 81 | 1 |
| 1980s/1989-07-14_491248_July_14_1989.pdf | 79 | 1 |
| 1980s/1989-06-14_491247_June_14_1989.pdf | 78 | 0 |
| 1970s/1978-06-05_491118_June_5_1978.pdf | 77 | 18 |
| 1980s/1985-09-13_491205_September_13_1985.pdf | 77 | 3 |
| 1980s/1987-12-28_491231_December_28_1987.pdf | 76 | 3 |
| 1980s/1986-10-14_491219_October_14_1986.pdf | 75 | 20 |
| 1980s/1989-04-14_491245_April_14_1989.pdf | 75 | 5 |
| 1970s/1978-08-02_491120_August_2_1978.pdf | 73 | 7 |
| 1980s/1986-02-12_491211_February_12_1986.pdf | 73 | 1 |
| 1980s/1985-06-14_491202_June_14_1985.pdf | 70 | 0 |
| 1990s/1996-04-18_491329_April_18_1996.pdf | 70 | 10 |
| 1970s/1978-05-16_491117_May_16_1978.pdf | 69 | 15 |
| 1990s/1995-01-12_491314_January_12_1995.pdf | 69 | 12 |
| 1980s/1984-05-11_491189_May_11_1984.pdf | 68 | 2 |
| 1990s/1990-12-14_491265_December_14_1990.pdf | 67 | 6 |
| 1980s/1985-03-12_491199_March_12_1985.pdf | 66 | 3 |
| 1980s/1987-03-13_491224_March_13_1987.pdf | 66 | 6 |
| 1980s/1980-10-09_491146_October_9_1980.pdf | 65 | 7 |
| 1980s/1987-01-14_491222_January_14_1987.pdf | 64 | 3 |
| 1970s/1977-11-10_491111_November_10_1977.pdf | 63 | 27 |
| 1990s/1995-12-18_491325_December_18_1995.pdf | 63 | 12 |
| 1980s/1987-04-15_491225_April_15_1987.pdf | 62 | 7 |
| 1980s/1986-04-21_491213_April_21_1986.pdf | 61 | 5 |
| 1990s/1991-01-22_491266_January_22_1991.pdf | 60 | 5 |
| 1980s/1985-05-13_491201_May_13_1985.pdf | 58 | 4 |
| 1980s/1982-02-16_491162_February_16_1982.pdf | 57 | 1 |
| 1980s/1987-05-15_491226_May_15_1987.pdf | 55 | 3 |
| 1970s/1978-09-11_491121_September_11_1978.pdf | 54 | 1 |
| 1980s/1981-03-03_491150_March_3_1981.pdf | 52 | 6 |
| 1980s/1982-07-15_491168_July_15_1982.pdf | 52 | 1 |
| 1980s/1986-09-15_491218_September_15_1986.pdf | 52 | 1 |
| 1990s/1990-05-22_491258_May_22_1990.pdf | 52 | 3 |
| 1980s/1988-11-04_491240_November_4_1988.pdf | 51 | 2 |
| 1970s/1977-12-08_491112_December_8_1977.pdf | 50 | 25 |
| 1980s/1989-08-16_491249_August_16_1989.pdf | 49 | 1 |
| 1980s/1986-01-15_491210_January_15_1986.pdf | 48 | 0 |
| 1980s/1985-01-11_491197_January_11_1985.pdf | 45 | 0 |
| 1970s/1978-03-22_491115_March_22_1978.pdf | 44 | 18 |
| 1970s/1978-04-13_491116_April_13_1978.pdf | 43 | 15 |
| 1990s/1991-04-19_491269_April_19_1991.pdf | 43 | 6 |
| 1980s/1985-04-12_491200_April_12_1985.pdf | 42 | 3 |
| 1970s/1977-10-13_491110_October_13_1977.pdf | 41 | 41 |
| 1970s/1978-01-11_491113_January_11_1978.pdf | 41 | 34 |
| 1980s/1985-08-12_491204_August_12_1985.pdf | 41 | 2 |
| 1980s/1982-05-13_491166_May_13_1982.pdf | 40 | 2 |
| 1980s/1985-02-12_491198_February_12_1985.pdf | 38 | 8 |
| 1970s/1978-02-09_491114_February_9_1978.pdf | 33 | 15 |
| 1980s/1981-06-08_491154_June_8_1981.pdf | 33 | 1 |
| 1980s/1982-08-04_491169_August_4_1982.pdf | 33 | 0 |
| 1970s/1978-07-20_491119_July_20_1978.pdf | 30 | 7 |
| 1980s/1981-11-12_491159_November_12_1981.pdf | 30 | 1 |
| 1990s/1990-07-19_491260_July_19_1990.pdf | 30 | 0 |
| 1980s/1981-12-14_491160_December_14_1981.pdf | 29 | 2 |
| 1970s/1979-08-10_491131_August_10_1979.pdf | 28 | 0 |
| 1980s/1981-09-15_491157_September_15_1981.pdf | 26 | 0 |
| 1990s/1992-08-21_491285_August_21_1992.pdf | 26 | 0 |
| 1970s/1979-05-11_491128_May_11_1979.pdf | 24 | 2 |
| 1980s/1982-06-14_491167_June_14_1982.pdf | 24 | 0 |
| 1980s/1983-01-13_491173_January_13_1983.pdf | 23 | 0 |
| 1970s/1979-11-15_491134_November_15_1979.pdf | 22 | 2 |
| 1990s/1990-01-16_491254_January_16_1990.pdf | 21 | 1 |
| 1990s/1991-05-22_491270_May_22_1991.pdf | 21 | 0 |
| 1990s/1992-04-28_491281_April_28_1992.pdf | 21 | 0 |
| 1980s/1981-05-12_491153_May_12_1981.pdf | 20 | 1 |
| 1970s/1978-11-14_491123_November_14_1978.pdf | 19 | 1 |
| 1990s/1990-10-15_491263_October_15_1990.pdf | 19 | 0 |
| 1990s/1991-11-18_491276_November_18_1991.pdf | 18 | 0 |
| 1990s/1991-12-16_491277_December_16_1991.pdf | 18 | 0 |
| 1970s/1979-06-13_491129_June_13_1979.pdf | 17 | 0 |
| 1980s/1980-09-10_491145_September_10_1980.pdf | 17 | 0 |
| 1990s/1990-03-20_491256_March_20_1990.pdf | 17 | 0 |
| 1990s/1996-02-20_491327_February_20_1996.pdf | 17 | 0 |
| 1970s/1979-02-15_491126_February_15_1979.pdf | 16 | 0 |
| 1990s/1992-01-15_491278_January_15_1992.pdf | 16 | 1 |
| 1990s/1993-12-15_491301_December_15_1993.pdf | 16 | 1 |
| 1970s/1979-01-09_491125_January_9_1979.pdf | 15 | 0 |
| 1990s/1991-02-19_491267_February_19_1991.pdf | 15 | 0 |
| 1990s/1991-08-16_491273_August_16_1991.pdf | 15 | 0 |
| 1990s/1994-02-15_491303_February_15_1994.pdf | 15 | 0 |
| 1980s/1982-01-19_491161_January_19_1982.pdf | 14 | 0 |
| 1980s/1982-03-17_491164_March_17_1982.pdf | 14 | 0 |
| 1990s/1990-02-14_491255_February_14_1990.pdf | 14 | 0 |
| 1990s/1992-07-17_491284_July_17_1992.pdf | 14 | 0 |
| 1990s/1990-09-19_491262_September_19_1990.pdf | 12 | 0 |
| 1990s/1991-03-22_491268_March_22_1991.pdf | 12 | 0 |
| 1990s/1991-07-15_491272_July_15_1991.pdf | 12 | 0 |
| 1970s/1979-04-24_491127_April_24_1979.pdf | 11 | 0 |
| 1980s/1981-08-13_491156_August_13_1981.pdf | 10 | 0 |
| 1990s/1993-11-16_491300_November_16_1993.pdf | 10 | 7 |
| 1980s/1980-03-11_491137_March_11_1980.pdf | 9 | 0 |
| 1990s/1992-02-14_491279_February_14_1992.pdf | 9 | 0 |
| 1990s/1992-03-24_491280_March_24_1992.pdf | 9 | 0 |
| 1990s/1992-06-15_491283_June_15_1992.pdf | 9 | 0 |
| 1990s/1996-10-23_491335_October_23_1996.pdf | 9 | 9 |
| 1980s/1980-01-14_491136_January_14_1980.pdf | 8 | 2 |
| 1970s/1979-07-12_491130_July_12_1979.pdf | 6 | 1 |
| 1970s/1979-09-13_491132_September_13_1979.pdf | 6 | 1 |
| 1980s/1980-11-10_491147_November_10_1980.pdf | 6 | 0 |
| 1980s/1982-04-13_491165_April_13_1982.pdf | 6 | 0 |
| 1990s/1992-05-28_491282_May_28_1992.pdf | 6 | 0 |
| 1990s/1992-09-18_491286_September_18_1992.pdf | 6 | 0 |
| 1990s/1992-11-16_491288_November_16_1992.pdf | 6 | 0 |
| 1990s/1992-12-17_491289_December_17_1992.pdf | 6 | 0 |
| 1990s/1996-05-20_491330_May_20_1996.pdf | 6 | 3 |
| 1980s/1981-03-26_491151_March_26_1981.pdf | 4 | 0 |
| 1980s/1980-04-02_491138_April_2_1980.pdf | 3 | 0 |
| 1980s/1980-07-09_491142_July_9_1980.pdf | 3 | 0 |
| 1980s/1981-01-12_491149_January_12_1981.pdf | 3 | 0 |
| 1990s/1995-03-16_491316_March_16_1995.pdf | 3 | 0 |
| 1990s/1996-01-18_491326_January_18_1996.pdf | 3 | 3 |
| 1970s/1979-12-26_491135_December_26_1979.pdf | 2 | 2 |
| 1990s/1994-01-24_491302_January_24_1994.pdf | 2 | 2 |
| 1990s/1994-10-19_491311_October_19_1994.pdf | 2 | 2 |
| 1990s/1996-06-19_491331_June_19_1996.pdf | 2 | 2 |
| 1980s/1981-07-13_491155_July_13_1981.pdf | 1 | 1 |

## True high-resolution OCR

- 1985 diagnostic unresolved before true high-resolution OCR: 208.
- 1985 diagnostic unresolved after final reconciliation: 37.
- 1985 true high-resolution attempts: 369.
- 1985 direct true high-resolution recoveries: 148.

## Remaining automation

- Another broad automated pass is not justified: all structural gates pass, and remaining cells are preserved in the auditable manual-review queue.

## Code changes

- Replaced label-only shifts with unified physical-row windows and audited offset candidates from -2 through +2.
- Added monotonic sparse-label binding to unified physical rows, prioritizing complete release-consistent month sequences over baseline pixel offsets.
- Added complete ordered date-sequence reconciliation across all three same-page tables and blocking row-shift checks.
- Fixed Era 2 alias-token canonicalization for total, ATS/NOW, business, and other savings components.
- Made embedded FRASER OCR locator-only across initial selection, arithmetic reconciliation, and cross-release reconciliation.
- Enforced canonical one-decimal final values and retained every repair rule, OCR pass, confidence, and selection reason.
- Added genuine page-specific 480/600-DPI rerendering, normalized coordinate crops, deskew audit, and cached OCR variants.
- Replaced magnitude and percentage tolerances with fixed additive rounding bounds and propagated turnover rounding bounds.
- Rebuilt final issues only after OCR, arithmetic, and cross-release reconciliation; extraction-error rows and issues now match exactly.
- Strengthened the full-corpus gate to reject missing row dates and wrote strict JSONL audit records without non-finite constants.
- Appended final provenance fields to every observation CSV and created the deduplicated manual-review queue.
- Corrected two legacy diagnostic expectations to the rendered source values: corrected-copy 1980 `50878.0` and 1985 SA `142907.2`.
