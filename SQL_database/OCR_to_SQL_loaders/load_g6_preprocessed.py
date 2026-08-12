#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from collections import Counter
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Iterator, Mapping, Sequence


EXPECTED_ROWS = 87_963
EXPECTED_SELECTED = 86_024
EXPECTED_STATUSES = {
    "reported": 85_397,
    "not_available": 627,
    "blank": 447,
    "extraction_error": 1_492,
}

VALUE_STATUSES = set(EXPECTED_STATUSES)
ADJUSTMENT_STATUSES = {"SA", "NSA", "unknown"}
MEASURE_BY_TABLE = {1: "debits", 2: "average_deposits", 3: "turnover"}
CSV_COLUMNS = (
    "era_id", "source_file", "release_date", "page_number", "table_number",
    "table_instance_id", "table_name_raw", "units_raw", "measure_canonical",
    "adjustment_status", "observation_date", "observation_date_status",
    "observation_date_source", "row_index", "row_label_raw", "row_annotation_raw",
    "row_level_1_raw", "row_level_2_raw", "column_level_1_raw",
    "column_level_2_raw", "column_level_3_raw", "column_index", "column_count",
    "cell_bbox", "page_classification", "deposit_type_canonical",
    "geography_canonical", "customer_type_canonical", "cell_annotation_raw",
    "value_raw", "value_numeric", "value_status", "ocr_confidence",
    "selected_source", "selection_reason", "normalization_rule", "validation_flags",
    "cross_release_support_count", "true_high_resolution_attempted",
)
STAGING_COLUMNS = (
    "g6_cell_extraction_id", "selected_candidate_order", "release_date",
    "observation_date", "observation_date_status", "measure_canonical",
    "adjustment_status", "deposit_type_canonical", "geography_canonical",
    "customer_type_canonical", "units_raw", "value_numeric", "value_status",
    "validation_flags", "cross_release_support_count",
)
STAGING_SCHEMA = {
    "g6_cell_extraction_id": ("integer", "NO"),
    "selected_candidate_order": ("integer", "YES"),
    "release_date": ("date", "NO"),
    "observation_date": ("date", "NO"),
    "observation_date_status": ("text", "NO"),
    "measure_canonical": ("text", "NO"),
    "adjustment_status": ("text", "NO"),
    "deposit_type_canonical": ("text", "NO"),
    "geography_canonical": ("text", "YES"),
    "customer_type_canonical": ("text", "YES"),
    "units_raw": ("text", "YES"),
    "value_numeric": ("numeric", "YES"),
    "value_status": ("text", "NO"),
    "validation_flags": ("jsonb", "NO"),
    "cross_release_support_count": ("integer", "NO"),
    "created_at": ("timestamp with time zone", "NO"),
}
RAW_SCHEMA = {
    "source_document": {
        "source_document_id": "smallint", "document_date": "date",
        "source_relative_path": "text",
    },
    "source_page_extraction": {
        "source_page_extraction_id": "smallint", "source_document_id": "smallint",
        "page_number": "smallint", "page_adjustment_status": "text",
    },
    "g6_cell_extraction": {
        "g6_cell_extraction_id": "integer", "source_page_extraction_id": "smallint",
        "source_document_id": "smallint", "page_number": "smallint",
        "table_number": "smallint", "table_instance_id": "text",
        "row_index": "integer", "column_index": "integer",
        "pipeline_observation_date": "date", "observation_date_status": "text",
        "canonical_column": "jsonb", "pipeline_cell_status": "text",
        "cross_release_support_count": "integer", "validation_flags": "jsonb",
    },
    "g6_ocr_candidate": {
        "g6_ocr_candidate_id": "integer", "g6_cell_extraction_id": "integer",
        "candidate_order": "integer",
        "candidate_numeric": "numeric", "candidate_status": "text",
        "is_selected": "boolean", "measure_canonical": "text",
    },
}


class LoaderError(RuntimeError):
    pass


PhysicalKey = tuple[str, int, str, int, int]


@dataclass(frozen=True)
class CsvObservation:
    row_number: int
    source_file: str
    release_date: date
    page_number: int
    table_number: int
    table_instance_id: str
    row_index: int
    column_index: int
    observation_date: date
    observation_date_status: str
    measure_canonical: str
    adjustment_status: str
    deposit_type_canonical: str
    geography_canonical: str | None
    customer_type_canonical: str | None
    units_raw: str | None
    value_numeric: Decimal | None
    value_status: str
    validation_flags: list[Any]
    cross_release_support_count: int

    @property
    def key(self) -> PhysicalKey:
        return (
            self.source_file, self.page_number, self.table_instance_id,
            self.row_index, self.column_index,
        )

    def staging_values(self, raw: RawCell) -> tuple[Any, ...]:
        return (
            raw.cell_id, raw.selected_candidate_order, self.release_date,
            self.observation_date, self.observation_date_status, self.measure_canonical,
            self.adjustment_status, self.deposit_type_canonical,
            self.geography_canonical, self.customer_type_canonical, self.units_raw,
            self.value_numeric, self.value_status, self.validation_flags,
            self.cross_release_support_count,
        )


@dataclass(frozen=True)
class RawCell:
    key: PhysicalKey
    cell_id: int
    document_date: date
    page_adjustment_status: str
    table_number: int
    observation_date: date | None
    observation_date_status: str | None
    canonical_column: dict[str, Any]
    cell_status: str
    cross_release_support_count: int
    validation_flags: list[Any]
    selected_candidate_order: int | None
    selected_candidate_status: str | None
    selected_candidate_numeric: Decimal | None
    selected_measure_canonical: str | None


@dataclass(frozen=True)
class ValidationSummary:
    rows: int
    statuses: Counter[str]
    selected_candidates: int


def optional_text(value: str | None) -> str | None:
    return None if value is None or value == "" else value


def required_text(value: str | None, label: str) -> str:
    parsed = optional_text(value)
    if parsed is None:
        raise LoaderError(f"{label} is blank")
    return parsed


def parse_integer(value: str | None, label: str, minimum: int = 0) -> int:
    try:
        parsed = int(required_text(value, label))
    except ValueError as error:
        raise LoaderError(f"{label} is not an integer: {value!r}") from error
    if parsed < minimum:
        raise LoaderError(f"{label} must be >= {minimum}: {parsed}")
    return parsed


def parse_date(value: str | None, label: str) -> date:
    try:
        return date.fromisoformat(required_text(value, label))
    except ValueError as error:
        raise LoaderError(f"{label} is not an ISO date: {value!r}") from error


def parse_decimal(value: str | None, label: str) -> Decimal | None:
    if value is None or value == "":
        return None
    try:
        parsed = Decimal(value)
    except InvalidOperation as error:
        raise LoaderError(f"{label} is not an exact decimal: {value!r}") from error
    if not parsed.is_finite():
        raise LoaderError(f"{label} is not a finite decimal: {value!r}")
    return parsed


def parse_json_array(value: str | None, label: str) -> list[Any]:
    try:
        parsed = json.loads(required_text(value, label))
    except json.JSONDecodeError as error:
        raise LoaderError(f"{label} is invalid JSON: {value!r}") from error
    if not isinstance(parsed, list):
        raise LoaderError(f"{label} must be a JSON array: {value!r}")
    return parsed


def parse_csv_row(row: Mapping[str, str], row_number: int) -> CsvObservation:
    context = f"CSV row {row_number}"
    try:
        status = required_text(row.get("value_status"), f"{context} value_status")
        if status not in VALUE_STATUSES:
            raise LoaderError(f"{context} unknown value_status: {status!r}")
        adjustment = required_text(row.get("adjustment_status"), f"{context} adjustment_status")
        if adjustment not in ADJUSTMENT_STATUSES:
            raise LoaderError(f"{context} unknown adjustment_status: {adjustment!r}")
        numeric = parse_decimal(row.get("value_numeric"), f"{context} value_numeric")
        if (status == "reported") != (numeric is not None):
            raise LoaderError(
                f"{context} value consistency failure: status={status!r}, numeric={numeric!r}"
            )
        return CsvObservation(
            row_number=row_number,
            source_file=required_text(row.get("source_file"), f"{context} source_file"),
            release_date=parse_date(row.get("release_date"), f"{context} release_date"),
            page_number=parse_integer(row.get("page_number"), f"{context} page_number", 1),
            table_number=parse_integer(row.get("table_number"), f"{context} table_number", 1),
            table_instance_id=required_text(
                row.get("table_instance_id"), f"{context} table_instance_id"
            ),
            row_index=parse_integer(row.get("row_index"), f"{context} row_index"),
            column_index=parse_integer(
                row.get("column_index"), f"{context} column_index"
            ),
            observation_date=parse_date(
                row.get("observation_date"), f"{context} observation_date"
            ),
            observation_date_status=required_text(
                row.get("observation_date_status"), f"{context} observation_date_status"
            ),
            measure_canonical=required_text(
                row.get("measure_canonical"), f"{context} measure_canonical"
            ),
            adjustment_status=adjustment,
            deposit_type_canonical=required_text(
                row.get("deposit_type_canonical"), f"{context} deposit_type_canonical"
            ),
            geography_canonical=optional_text(row.get("geography_canonical")),
            customer_type_canonical=optional_text(row.get("customer_type_canonical")),
            units_raw=optional_text(row.get("units_raw")),
            value_numeric=numeric,
            value_status=status,
            validation_flags=parse_json_array(
                row.get("validation_flags"), f"{context} validation_flags"
            ),
            cross_release_support_count=parse_integer(
                row.get("cross_release_support_count"),
                f"{context} cross_release_support_count",
            ),
        )
    except LoaderError as error:
        if str(error).startswith(context):
            raise
        raise LoaderError(f"{context}: {error}") from error


def iter_csv(path: Path) -> Iterator[CsvObservation]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        actual = tuple(reader.fieldnames or ())
        if actual != CSV_COLUMNS:
            raise LoaderError(f"CSV columns differ from expected header: expected={CSV_COLUMNS}, actual={actual}")
        for row in reader:
            yield parse_csv_row(row, reader.line_num)


def verify_live_schema(connection: Any) -> None:
    tables = list(RAW_SCHEMA) + ["g6_parsed_observation_preprocessed"]
    rows = connection.execute(
        """
        SELECT table_schema, table_name, column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_schema IN ('raw', 'staging') AND table_name = ANY(%s)
        ORDER BY table_schema, table_name, ordinal_position
        """,
        (tables,),
    ).fetchall()
    actual: dict[tuple[str, str], list[tuple[str, str, str]]] = {}
    for row in rows:
        actual.setdefault((row["table_schema"], row["table_name"]), []).append(
            (row["column_name"], row["data_type"], row["is_nullable"])
        )
    differences = []
    staging = actual.get(("staging", "g6_parsed_observation_preprocessed"), [])
    expected_staging = [(name, *metadata) for name, metadata in STAGING_SCHEMA.items()]
    if staging != expected_staging:
        differences.append(
            "staging.g6_parsed_observation_preprocessed: "
            f"expected={expected_staging}, actual={staging}"
        )
    for table, expected_columns in RAW_SCHEMA.items():
        available = {name: data_type for name, data_type, _ in actual.get(("raw", table), [])}
        for name, expected_type in expected_columns.items():
            if available.get(name) != expected_type:
                differences.append(
                    f"raw.{table}.{name}: expected={expected_type!r}, actual={available.get(name)!r}"
                )
    if differences:
        raise LoaderError("live schema differs from loader contract:\n" + "\n".join(differences))


def ensure_destination_empty(connection: Any) -> None:
    populated = connection.execute(
        "SELECT EXISTS (SELECT 1 FROM staging.g6_parsed_observation_preprocessed LIMIT 1) AS populated"
    ).fetchone()["populated"]
    if populated:
        raise LoaderError("staging.g6_parsed_observation_preprocessed is not empty; refusing to append")


def load_raw_cells(connection: Any) -> dict[PhysicalKey, RawCell]:
    duplicate = connection.execute(
        """
        SELECT g6_cell_extraction_id, count(*) AS selected_count
        FROM raw.g6_ocr_candidate
        WHERE is_selected
        GROUP BY g6_cell_extraction_id
        HAVING count(*) > 1
        LIMIT 1
        """
    ).fetchone()
    if duplicate:
        raise LoaderError(f"raw cell has multiple selected candidates: {dict(duplicate)}")
    counts = connection.execute(
        """
        SELECT
            (SELECT count(*) FROM raw.g6_cell_extraction) AS cells,
            (SELECT count(*) FROM raw.g6_ocr_candidate WHERE is_selected) AS selected
        """
    ).fetchone()
    if counts["cells"] != EXPECTED_ROWS or counts["selected"] != EXPECTED_SELECTED:
        raise LoaderError(
            f"unexpected raw totals: cells={counts['cells']}, selected={counts['selected']}; "
            f"expected cells={EXPECTED_ROWS}, selected={EXPECTED_SELECTED}"
        )
    query = """
        SELECT
            d.source_relative_path, d.document_date, p.page_adjustment_status,
            c.g6_cell_extraction_id, c.page_number, c.table_number,
            c.table_instance_id, c.row_index, c.column_index,
            c.pipeline_observation_date, c.observation_date_status,
            c.canonical_column, c.pipeline_cell_status,
            c.cross_release_support_count, c.validation_flags,
            o.candidate_order, o.candidate_status, o.candidate_numeric,
            o.measure_canonical AS selected_measure_canonical
        FROM raw.source_document d
        JOIN raw.source_page_extraction p USING (source_document_id)
        JOIN raw.g6_cell_extraction c
          ON c.source_page_extraction_id = p.source_page_extraction_id
         AND c.source_document_id = p.source_document_id
         AND c.page_number = p.page_number
        LEFT JOIN raw.g6_ocr_candidate o
          ON o.g6_cell_extraction_id = c.g6_cell_extraction_id
         AND o.is_selected
        ORDER BY c.g6_cell_extraction_id
    """
    raw_cells: dict[PhysicalKey, RawCell] = {}
    cell_ids: set[int] = set()
    with connection.cursor(name="g6_preprocessed_raw_cells") as cursor:
        cursor.execute(query)
        for row in cursor:
            key: PhysicalKey = (
                row["source_relative_path"], row["page_number"], row["table_instance_id"],
                row["row_index"], row["column_index"],
            )
            if key in raw_cells:
                raise LoaderError(f"raw physical key resolves to multiple cells: key={key!r}")
            cell_id = row["g6_cell_extraction_id"]
            if cell_id in cell_ids:
                raise LoaderError(f"duplicate raw cell ID returned by resolution query: {cell_id}")
            status = row["pipeline_cell_status"]
            selected_order = row["candidate_order"]
            if status in {"reported", "not_available"} and selected_order is None:
                raise LoaderError(f"raw cell {cell_id} status={status!r} has no selected candidate")
            if status in {"blank", "extraction_error"} and selected_order is not None:
                raise LoaderError(f"raw cell {cell_id} status={status!r} has a selected candidate")
            if selected_order is not None and row["candidate_status"] != status:
                raise LoaderError(
                    f"raw cell {cell_id} status differs from selected candidate: "
                    f"cell={status!r}, candidate={row['candidate_status']!r}"
                )
            canonical = row["canonical_column"]
            flags = row["validation_flags"]
            if not isinstance(canonical, dict) or not isinstance(flags, list):
                raise LoaderError(f"raw cell {cell_id} has invalid canonical/validation JSON")
            raw_cells[key] = RawCell(
                key=key,
                cell_id=cell_id,
                document_date=row["document_date"],
                page_adjustment_status=row["page_adjustment_status"],
                table_number=row["table_number"],
                observation_date=row["pipeline_observation_date"],
                observation_date_status=row["observation_date_status"],
                canonical_column=canonical,
                cell_status=status,
                cross_release_support_count=row["cross_release_support_count"],
                validation_flags=flags,
                selected_candidate_order=selected_order,
                selected_candidate_status=row["candidate_status"],
                selected_candidate_numeric=row["candidate_numeric"],
                selected_measure_canonical=row["selected_measure_canonical"],
            )
            cell_ids.add(cell_id)
    if len(raw_cells) != EXPECTED_ROWS:
        raise LoaderError(f"resolution query returned {len(raw_cells)} unique cells; expected {EXPECTED_ROWS}")
    return raw_cells


def mismatch(
    observation: CsvObservation,
    raw: RawCell,
    field: str,
    csv_value: Any,
    raw_value: Any,
) -> None:
    raise LoaderError(
        f"CSV row {observation.row_number} key={observation.key!r}: {field} mismatch; "
        f"csv={csv_value!r}, raw={raw_value!r}, cell_id={raw.cell_id}"
    )


def validate_observation(observation: CsvObservation, raw: RawCell) -> None:
    checks = {
        "release_date": (observation.release_date, raw.document_date),
        "table_number": (observation.table_number, raw.table_number),
        "observation_date": (observation.observation_date, raw.observation_date),
        "observation_date_status": (
            observation.observation_date_status, raw.observation_date_status,
        ),
        "value_status": (observation.value_status, raw.cell_status),
        "deposit_type_canonical": (
            observation.deposit_type_canonical,
            optional_text(raw.canonical_column.get("deposit_type")),
        ),
        "geography_canonical": (
            observation.geography_canonical,
            optional_text(raw.canonical_column.get("geography")),
        ),
        "customer_type_canonical": (
            observation.customer_type_canonical,
            optional_text(raw.canonical_column.get("customer_type")),
        ),
        "validation_flags": (observation.validation_flags, raw.validation_flags),
        "cross_release_support_count": (
            observation.cross_release_support_count, raw.cross_release_support_count,
        ),
        "measure_from_table": (
            observation.measure_canonical, MEASURE_BY_TABLE.get(raw.table_number),
        ),
    }
    if raw.page_adjustment_status != "unknown":
        checks["adjustment_status"] = (
            observation.adjustment_status, raw.page_adjustment_status,
        )
    if raw.selected_candidate_order is not None:
        checks["selected_candidate_status"] = (
            observation.value_status, raw.selected_candidate_status,
        )
        checks["selected_measure_canonical"] = (
            observation.measure_canonical, raw.selected_measure_canonical,
        )
    if observation.value_status == "reported":
        checks["value_numeric"] = (
            observation.value_numeric, raw.selected_candidate_numeric,
        )
    elif raw.selected_candidate_numeric is not None:
        checks["value_numeric"] = (None, raw.selected_candidate_numeric)
    for field, (csv_value, raw_value) in checks.items():
        if csv_value != raw_value:
            mismatch(observation, raw, field, csv_value, raw_value)


def validate_csv(path: Path, raw_cells: Mapping[PhysicalKey, RawCell]) -> ValidationSummary:
    statuses: Counter[str] = Counter()
    resolved_ids: set[int] = set()
    remaining = set(raw_cells)
    rows = 0
    selected = 0
    for observation in iter_csv(path):
        rows += 1
        statuses[observation.value_status] += 1
        raw = raw_cells.get(observation.key)
        if raw is None:
            raise LoaderError(
                f"CSV row {observation.row_number} key={observation.key!r} resolves to no raw cell"
            )
        if raw.cell_id in resolved_ids:
            raise LoaderError(
                f"CSV row {observation.row_number} key={observation.key!r} duplicates raw cell "
                f"{raw.cell_id}"
            )
        validate_observation(observation, raw)
        resolved_ids.add(raw.cell_id)
        remaining.discard(observation.key)
        selected += raw.selected_candidate_order is not None
    if rows != EXPECTED_ROWS:
        raise LoaderError(f"CSV contains {rows} rows; expected {EXPECTED_ROWS}")
    if dict(statuses) != EXPECTED_STATUSES:
        raise LoaderError(f"CSV status distribution differs: actual={dict(statuses)}, expected={EXPECTED_STATUSES}")
    if selected != EXPECTED_SELECTED:
        raise LoaderError(f"resolved selected candidate count={selected}; expected {EXPECTED_SELECTED}")
    if remaining:
        key = next(iter(remaining))
        raise LoaderError(f"raw cell is missing from CSV: key={key!r}, cell_id={raw_cells[key].cell_id}")
    return ValidationSummary(rows, statuses, selected)


def copy_to_staging(connection: Any, path: Path, raw_cells: Mapping[PhysicalKey, RawCell]) -> None:
    from psycopg.types.json import Jsonb

    sql = f"COPY staging.g6_parsed_observation_preprocessed ({','.join(STAGING_COLUMNS)}) FROM STDIN"
    rows = 0
    with connection.cursor() as cursor, cursor.copy(sql) as copy:
        for observation in iter_csv(path):
            raw = raw_cells.get(observation.key)
            if raw is None:
                raise LoaderError(
                    f"CSV changed between validation and load at row {observation.row_number}: "
                    f"key={observation.key!r}"
                )
            validate_observation(observation, raw)
            values = list(observation.staging_values(raw))
            values[13] = Jsonb(values[13])
            copy.write_row(values)
            rows += 1
    if rows != EXPECTED_ROWS:
        raise LoaderError(f"COPY wrote {rows} rows; expected {EXPECTED_ROWS}")


def validate_loaded_staging(connection: Any) -> ValidationSummary:
    counts = connection.execute(
        """
        SELECT count(*) AS rows,
               count(DISTINCT g6_cell_extraction_id) AS distinct_cells,
               count(selected_candidate_order) AS selected
        FROM staging.g6_parsed_observation_preprocessed
        """
    ).fetchone()
    if (counts["rows"], counts["distinct_cells"], counts["selected"]) != (
        EXPECTED_ROWS, EXPECTED_ROWS, EXPECTED_SELECTED,
    ):
        raise LoaderError(f"post-load staging totals are invalid: {dict(counts)}")
    orphan = connection.execute(
        """
        SELECT s.g6_cell_extraction_id
        FROM staging.g6_parsed_observation_preprocessed s
        LEFT JOIN raw.g6_cell_extraction c USING (g6_cell_extraction_id)
        WHERE c.g6_cell_extraction_id IS NULL
        LIMIT 1
        """
    ).fetchone()
    if orphan:
        raise LoaderError(f"staging row has no raw-cell FK target: {dict(orphan)}")
    invalid_candidate = connection.execute(
        """
        SELECT s.g6_cell_extraction_id, s.selected_candidate_order
        FROM staging.g6_parsed_observation_preprocessed s
        LEFT JOIN raw.g6_ocr_candidate o
          ON o.g6_cell_extraction_id = s.g6_cell_extraction_id
         AND o.candidate_order = s.selected_candidate_order
         AND o.is_selected
        WHERE s.selected_candidate_order IS NOT NULL
          AND o.g6_ocr_candidate_id IS NULL
        LIMIT 1
        """
    ).fetchone()
    if invalid_candidate:
        raise LoaderError(f"invalid selected-candidate reference: {dict(invalid_candidate)}")
    rows = connection.execute(
        """
        SELECT value_status, count(*) AS count
        FROM staging.g6_parsed_observation_preprocessed
        GROUP BY value_status
        """
    ).fetchall()
    statuses = Counter({row["value_status"]: row["count"] for row in rows})
    if dict(statuses) != EXPECTED_STATUSES:
        raise LoaderError(f"post-load status distribution differs: {dict(statuses)}")
    return ValidationSummary(counts["rows"], statuses, counts["selected"])


def run(path: Path, load: bool) -> ValidationSummary:
    missing = [
        name for name in ("PGHOST", "PGPORT", "PGDATABASE", "PGUSER", "PGPASSWORD")
        if not os.getenv(name)
    ]
    if missing:
        raise LoaderError(f"missing PostgreSQL environment variables: {', '.join(missing)}")
    try:
        import psycopg
        from psycopg.rows import dict_row
    except ImportError as error:
        raise LoaderError("psycopg 3 is required; install requirements.txt") from error
    try:
        with psycopg.connect(row_factory=dict_row) as connection:
            connection.read_only = not load
            verify_live_schema(connection)
            if load:
                connection.execute(
                    "LOCK TABLE staging.g6_parsed_observation_preprocessed "
                    "IN ACCESS EXCLUSIVE MODE"
                )
            ensure_destination_empty(connection)
            raw_cells = load_raw_cells(connection)
            summary = validate_csv(path, raw_cells)
            if load:
                copy_to_staging(connection, path, raw_cells)
                summary = validate_loaded_staging(connection)
            return summary
    except psycopg.Error as error:
        raise LoaderError(f"PostgreSQL operation failed: {error}") from error


def parse_arguments(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Resolve G.6 analytical CSV rows to raw cells and load preprocessed staging."
    )
    parser.add_argument("--csv", required=True, help="Path to g6_all_eras.csv")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="Validate against raw without inserting (default)")
    mode.add_argument("--load", action="store_true", help="Validate and populate staging in one transaction")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    try:
        args = parse_arguments(argv)
        path = Path(args.csv).expanduser().resolve()
        if not path.is_file():
            raise LoaderError(f"CSV does not exist: {path}")
        summary = run(path, args.load)
        print(f"CSV rows: {summary.rows}")
        print(f"Status distribution: {dict(summary.statuses)}")
        print(f"Selected candidates: {summary.selected_candidates}")
        if args.load:
            print("Load and post-load validation completed in one transaction")
        else:
            print("Dry-run validation completed; staging was not modified")
        return 0
    except (LoaderError, OSError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
