# G.6 raw PostgreSQL loader

Run these commands from the loader project directory:

```bash
cd "/Users/danie/Personal-Macro-Research/SQL database: Deposit Turnover by Type, 1977–1996"
```

Install the PostgreSQL driver:

```bash
python3 -m pip install -r requirements.txt
```

Set the connection environment variables before a real load:

```bash
export PGHOST=localhost
export PGPORT=5432
export PGDATABASE=your_database
export PGUSER=your_user
export PGPASSWORD=your_password
```

Dry-run is the default and never opens a database connection:

```bash
python3 load_g6_raw.py \
  --jsonl-dir g6_extraction_output/ocr_raw_chunks \
  --era-map g6_era_map.csv \
  --input-root "/Users/danie/Personal-Macro-Research/SQL database: Deposit Turnover by Type, 1977–1996/fraser_g6_issues" \
  --run-label cleanup-v3-20260724
```

Load only after a successful dry-run:

```bash
python3 load_g6_raw.py \
  --jsonl-dir g6_extraction_output/ocr_raw_chunks \
  --era-map g6_era_map.csv \
  --input-root "/Users/danie/Personal-Macro-Research/SQL database: Deposit Turnover by Type, 1977–1996/fraser_g6_issues" \
  --run-label cleanup-v3-20260724 \
  --cleanup-report-path g6_extraction_output/cleanup_run_report.md \
  --load
```

To validate selected files without loading, repeat `--jsonl-file` and use `--dry-run`:

```bash
python3 load_g6_raw.py \
  --jsonl-file g6_extraction_output/ocr_raw_chunks/ocr_raw.part_003.jsonl \
  --era-map g6_era_map.csv \
  --input-root "/Users/danie/Personal-Macro-Research/SQL database: Deposit Turnover by Type, 1977–1996/fraser_g6_issues" \
  --run-label validation-only \
  --dry-run
```

The loader verifies the live `raw` table columns before inserting anything, refuses nonempty raw extraction tables or a reused run label, validates each document transaction, and marks the extraction run complete only after all post-load checks pass. Oversized OCR and cache files are read in streaming mode and are never modified.
