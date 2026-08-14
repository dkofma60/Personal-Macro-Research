# Federal Reserve G.6 deposit-turnover database

This PostgreSQL database digitizes the Federal Reserve's historical G.6 Debits and Deposit Turnover at Commercial Banks releases for 1977-1996 into a fully auditable research dataset. Prior to July 1977, only demand deposit data was collected. The release was retired in October 1996.

Auditability is essential because the archived documents combine poor scans with recurring layout changes, shifting deposit definitions, revised releases, and occasional internal inconsistencies that make OCR uncertain. PDF embedded OCR has errors and is used for corroboration rather than a source of truth.

For each detected table cell, the raw layer preserves competing OCR readings, confidence and repair evidence, page geometry, document version, and extraction run. Staging then resolves selected readings into controlled economic observations, reconciles repeated release appearances, and applies rounding-aware arithmetic checks before core receives one accepted fact.

In parallel, versioned category definitions organize the publication's many concept changes into distinct direct series. Core combines only segments that are directly compatible, producing coherent continuous series for plotting and analysis without hiding real definition breaks.



## Project contents

- `OCR_pipeline/`: source PDFs, era map, extraction code, QA output, and OCR data
- `OCR_to_SQL_loaders/`: validated loaders for raw JSONL and the all-era CSV
- `SQL_queries/`: ordered schema, population, view, and validation scripts
- GitHub release asset: compressed custom-format snapshot of the completed database

## Requirements

- PostgreSQL 15 or later (`psql`; PostgreSQL 18 is recommended for the snapshot)
- Python 3
- Tesseract OCR and Poppler (`pdftoppm` and `pdftotext`)
- Python packages: `numpy`, `Pillow`, and
  `OCR_to_SQL_loaders/requirements.txt`

Run the commands below from this `SQL_database/` directory. Set `PGHOST`,
`PGPORT`, `PGDATABASE`, `PGUSER`, and `PGPASSWORD` for all database steps.

## Rebuild workflow

### 1. Construct the raw schema

```bash
psql -X -v ON_ERROR_STOP=1 -f SQL_queries/01_construct_raw_schema.sql
```

### 2. Run the OCR pipeline

The pipeline reads the PDFs under `OCR_pipeline/fraser_g6_issues/`, uses
`OCR_pipeline/g6_era_map.csv`, runs diagnostic gates first, and writes the
accepted output to `OCR_pipeline/g6_extraction_output_v2/`.

```bash
python3 -m pip install numpy Pillow
python3 OCR_pipeline/g6_spatial_extraction_pipeline.py
python3 OCR_pipeline/g6_extraction_output_v2/split_ocr_raw_jsonl.py
```

The final command splits `ocr_raw.jsonl` into the five JSONL parts expected by
the raw loader. The committed final outputs may be used instead of rerunning
the expensive OCR step. `deposit_turnover_SQL_database.ipynb` is retained as
historical exploration; the Python file above is the current entry point.

### 3. Load the five JSONL parts into `raw`

```bash
python3 -m pip install -r OCR_to_SQL_loaders/requirements.txt

# Validate without connecting to PostgreSQL.
python3 OCR_to_SQL_loaders/load_g6_raw.py \
  --jsonl-dir OCR_pipeline/g6_extraction_output_v2/ocr_raw_chunks \
  --era-map OCR_pipeline/g6_era_map.csv \
  --run-label date-reconciliation-v4-20260808

# Load after validation succeeds.
python3 OCR_to_SQL_loaders/load_g6_raw.py \
  --jsonl-dir OCR_pipeline/g6_extraction_output_v2/ocr_raw_chunks \
  --era-map OCR_pipeline/g6_era_map.csv \
  --input-root OCR_pipeline/fraser_g6_issues \
  --run-label date-reconciliation-v4-20260808 \
  --cleanup-report-path OCR_pipeline/g6_extraction_output_v2/cleanup_run_report.md \
  --load
```

### 4. Construct staging

This creates the `staging` schema, the empty preprocessed destination, the
controlled reference tables, and the post-processed table.

```bash
psql -X -v ON_ERROR_STOP=1 -f SQL_queries/02_construct_staging_reference_tables_and_staging_g6_parsed_observation_post_processed.sql
```

### 5. Populate preprocessed staging from `g6_all_eras.csv`

```bash
# Read-only database validation.
python3 OCR_to_SQL_loaders/load_g6_preprocessed.py \
  --csv OCR_pipeline/g6_extraction_output_v2/g6_all_eras.csv

# Load after validation succeeds.
python3 OCR_to_SQL_loaders/load_g6_preprocessed.py \
  --csv OCR_pipeline/g6_extraction_output_v2/g6_all_eras.csv \
  --load
```

### 6. Build the remaining staging refinement tables

Run these in order:

```bash
psql -X -v ON_ERROR_STOP=1 -f SQL_queries/03_populate_staging_g6_parsed_observation_post_processed.sql
psql -X -v ON_ERROR_STOP=1 -f SQL_queries/04_construct_staging_g6_observation_consensus.sql
psql -X -v ON_ERROR_STOP=1 -f SQL_queries/05_populate_staging_g6_observation_consensus.sql
psql -X -v ON_ERROR_STOP=1 -f SQL_queries/06_construct_staging_g6_observation_cross_checked.sql
psql -X -v ON_ERROR_STOP=1 -f SQL_queries/07_populate_staging_g6_observation_cross_checked.sql
psql -X -v ON_ERROR_STOP=1 -f SQL_queries/08_apply_manual_adjustments_to_staging_g6_observation_cross_checked.sql
```

### 7. Construct, populate, and validate `core`

```bash
psql -X -v ON_ERROR_STOP=1 -f SQL_queries/09_construct_core_schema.sql
psql -X -v ON_ERROR_STOP=1 -f SQL_queries/10_populate_core_schema.sql
psql -X -v ON_ERROR_STOP=1 -f SQL_queries/11_create_core_views.sql
psql -X -v ON_ERROR_STOP=1 -f SQL_queries/12_validate_core_schema.sql
```

`core.g6_observation.g6_observation_cross_checked_id` is the direct lineage key
to final staging; the remaining staging and raw foreign keys lead back to the
source document, page, physical cell, and competing OCR candidates.

Paths retained as provenance are relative to this `SQL_database/` directory.

## Publish or restore the completed snapshot

Export the completed database as a compressed PostgreSQL custom-format `.dump`
and attach it to a GitHub release rather than committing it to the repository.
Restore the downloaded release asset into an empty database with PostgreSQL 18
or later:

```bash
pg_restore --exit-on-error --no-owner \
  --dbname "$PGDATABASE" /path/to/g6_turnover_full_database.dump
```

The release asset is a convenience snapshot; the numbered SQL, loaders, and
retained OCR artifacts remain the reproducible build path.
