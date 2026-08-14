# G.6 raw PostgreSQL loader

Run these commands from `SQL_database/` after constructing the raw schema with
`SQL_queries/01_construct_raw_schema.sql`.

Install the PostgreSQL driver:

```bash
python3 -m pip install -r OCR_to_SQL_loaders/requirements.txt
```

Set `PGHOST`, `PGPORT`, `PGDATABASE`, `PGUSER`, and `PGPASSWORD` before a real
load. The default dry-run parses and validates the five JSONL parts without
opening a database connection:

```bash
python3 OCR_to_SQL_loaders/load_g6_raw.py \
  --jsonl-dir OCR_pipeline/g6_extraction_output_v2/ocr_raw_chunks \
  --era-map OCR_pipeline/g6_era_map.csv \
  --run-label date-reconciliation-v4-20260808
```

Load only after the dry-run succeeds:

```bash
python3 OCR_to_SQL_loaders/load_g6_raw.py \
  --jsonl-dir OCR_pipeline/g6_extraction_output_v2/ocr_raw_chunks \
  --era-map OCR_pipeline/g6_era_map.csv \
  --input-root OCR_pipeline/fraser_g6_issues \
  --run-label date-reconciliation-v4-20260808 \
  --cleanup-report-path OCR_pipeline/g6_extraction_output_v2/cleanup_run_report.md \
  --load
```

For a validation-only check of selected parts, repeat `--jsonl-file` and keep
dry-run mode:

```bash
python3 OCR_to_SQL_loaders/load_g6_raw.py \
  --jsonl-file OCR_pipeline/g6_extraction_output_v2/ocr_raw_chunks/ocr_raw.part_003.jsonl \
  --era-map OCR_pipeline/g6_era_map.csv \
  --run-label validation-only \
  --dry-run
```

Load mode requires the five canonical part names. The loader verifies the live
raw schema, refuses nonempty extraction tables or a reused run label, validates
each document transaction, and marks the extraction run complete only after
all post-load checks pass. Paths inside this project are stored relative to the
`SQL_database/` directory.
