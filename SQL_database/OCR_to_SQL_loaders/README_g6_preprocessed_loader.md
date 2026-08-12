# G.6 preprocessed staging loader

Install Psycopg 3:

```bash
python3 -m pip install -r requirements.txt
```

Set `PGHOST`, `PGPORT`, `PGDATABASE`, `PGUSER`, and `PGPASSWORD`. Dry-run is the default; it opens a read-only transaction, resolves all CSV rows against `raw`, performs every validation, and does not modify staging:

```bash
python3 load_g6_preprocessed.py \
  --csv ../OCR_pipeline/g6_extraction_output_v2/g6_all_eras.csv
```

After a successful dry-run, populate the empty destination in one transaction:

```bash
python3 load_g6_preprocessed.py \
  --csv ../OCR_pipeline/g6_extraction_output_v2/g6_all_eras.csv \
  --load
```

The loader verifies the live raw/staging columns before work, refuses a nonempty `staging.g6_parsed_observation_preprocessed`, uses exact `Decimal` values, and rolls back the complete load on any resolution, validation, or database-constraint failure.
