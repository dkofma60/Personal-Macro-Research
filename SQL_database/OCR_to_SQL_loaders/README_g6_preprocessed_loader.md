# G.6 preprocessed staging loader

Run these commands from `SQL_database/` after the raw load succeeds and
`SQL_queries/02_construct_staging_reference_tables_and_staging_g6_parsed_observation_post_processed.sql`
has created the empty preprocessed staging table.

Install the PostgreSQL driver and set `PGHOST`, `PGPORT`, `PGDATABASE`,
`PGUSER`, and `PGPASSWORD`:

```bash
python3 -m pip install -r OCR_to_SQL_loaders/requirements.txt
```

The default dry-run opens a read-only transaction, resolves every CSV row to
raw provenance, and performs all validations without changing staging:

```bash
python3 OCR_to_SQL_loaders/load_g6_preprocessed.py \
  --csv OCR_pipeline/g6_extraction_output_v2/g6_all_eras.csv
```

Populate the empty destination only after the dry-run succeeds:

```bash
python3 OCR_to_SQL_loaders/load_g6_preprocessed.py \
  --csv OCR_pipeline/g6_extraction_output_v2/g6_all_eras.csv \
  --load
```

The loader checks the live raw and staging columns, refuses a nonempty
`staging.g6_parsed_observation_preprocessed`, preserves exact decimal values,
and rolls back the complete load on any resolution, validation, or constraint
failure.
