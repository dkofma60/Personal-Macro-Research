#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
from itertools import groupby
from pathlib import Path, PurePosixPath
from typing import Any, Iterable, Iterator, Sequence


PUBLICATION_CODE = "G.6"
RELEASE_TITLE = "Debits and Deposit Turnover at Commercial Banks"
VALUE_STATUSES = {"reported", "not_available", "blank", "extraction_error"}
PAGE_CLASSES = {
    "table_page",
    "metadata_page",
    "unrelated_release_page",
    "uncertain_page",
}
ADJUSTMENT_STATUSES = {"SA", "NSA", "unknown"}
KNOWN_DUPLICATE_CYCLES = {
    date(1980, 5, 1),
    date(1980, 8, 1),
    date(1981, 3, 1),
    date(1982, 2, 1),
    date(1990, 12, 1),
}
FULL_CORPUS_PARTS = {f"ocr_raw.part_{number:03d}.jsonl" for number in range(1, 6)}
FULL_CORPUS_TOTALS = {
    "releases": 220,
    "documents": 225,
    "pages": 397,
    "cells": 87_963,
    "table_page": 389,
    "metadata_page": 7,
    "unrelated_release_page": 1,
}

SQL_DATABASE_ROOT = Path(__file__).resolve().parents[1]

EXPECTED_COLUMNS = {
    "g6_era": (
        "era_id",
        "first_document_date",
        "last_document_date",
        "source_reported_doc_count",
        "era_description",
    ),
    "g6_release": (
        "g6_release_id",
        "release_cycle_month",
        "publication_code",
        "release_title",
        "era_id",
        "release_notes",
        "created_at",
    ),
    "source_document": (
        "source_document_id",
        "g6_release_id",
        "document_date",
        "source_filename",
        "source_relative_path",
        "source_format",
        "document_version",
        "version_type",
        "is_preferred_version",
        "supersedes_source_document_id",
        "page_count",
        "source_notes",
        "created_at",
    ),
    "extraction_run": (
        "extraction_run_id",
        "run_label",
        "pipeline_version",
        "input_root",
        "full_corpus_completed",
        "input_artifact_manifest",
        "cleanup_report_path",
        "run_notes",
        "loaded_at",
    ),
    "source_page_extraction": (
        "source_page_extraction_id",
        "source_document_id",
        "extraction_run_id",
        "page_number",
        "input_part_name",
        "input_line_number",
        "page_classification",
        "classification_score",
        "classification_reason",
        "printed_release_code",
        "printed_release_title",
        "printed_release_date",
        "page_adjustment_status",
        "mean_ocr_confidence",
        "raw_ocr_text",
        "sparse_ocr_text",
        "embedded_locator_text",
        "date_reconciliation",
        "rendered_ocr_words",
        "sparse_ocr_words",
        "embedded_locator_words",
        "table_anchors",
        "table_structure",
        "created_at",
    ),
    "g6_cell_extraction": (
        "g6_cell_extraction_id",
        "source_page_extraction_id",
        "source_document_id",
        "page_number",
        "table_number",
        "table_instance_id",
        "row_index",
        "column_index",
        "physical_row_center",
        "physical_row_bounds",
        "cell_bbox",
        "ink_density",
        "row_label_raw",
        "matched_month_label_candidates",
        "pipeline_observation_date",
        "observation_date_status",
        "observation_date_source",
        "column_path",
        "canonical_column",
        "pipeline_cell_status",
        "pipeline_selection_reason",
        "cross_release_support_count",
        "adjacent_release_values",
        "validation_flags",
        "arithmetic_selection",
        "cross_release_selection",
        "created_at",
    ),
    "g6_ocr_candidate": (
        "g6_ocr_candidate_id",
        "g6_cell_extraction_id",
        "candidate_order",
        "ocr_source",
        "ocr_variant",
        "raw_recognized_string",
        "candidate_numeric",
        "candidate_status",
        "ocr_confidence",
        "normalization_rule",
        "is_eligible",
        "is_selected",
        "selection_reason",
        "measure_canonical",
        "unsafe_decimal_relocation",
        "trimmed_trailing_digits",
        "supporting_raw_strings",
        "created_at",
    ),
}

IDENTITY_COLUMNS = {
    ("g6_release", "g6_release_id"): "smallint",
    ("source_document", "source_document_id"): "smallint",
    ("extraction_run", "extraction_run_id"): "smallint",
    ("source_page_extraction", "source_page_extraction_id"): "smallint",
    ("g6_cell_extraction", "g6_cell_extraction_id"): "integer",
    ("g6_ocr_candidate", "g6_ocr_candidate_id"): "integer",
}


class LoaderError(RuntimeError):
    pass


def project_relative_path(value: str) -> str:
    resolved = Path(value).expanduser().resolve()
    try:
        return str(resolved.relative_to(SQL_DATABASE_ROOT))
    except ValueError:
        return str(resolved)


@dataclass(frozen=True)
class Era:
    era_id: int
    first: date
    last: date
    source_doc_count: int | None
    description: str


@dataclass
class DocumentInfo:
    source_file: str
    release_date: date
    era_id: int
    pipeline_version: str
    max_page_number: int
    page_records: int = 1

    @property
    def cycle(self) -> date:
        return self.release_date.replace(day=1)


@dataclass(frozen=True)
class DocumentVersion:
    version: int
    version_type: str
    preferred: bool
    supersedes_source_file: str | None
    notes: str | None


@dataclass(frozen=True)
class Record:
    part: Path
    line_number: int
    page: dict[str, Any]


@dataclass
class ScanResult:
    files: list[Path]
    manifest: list[dict[str, Any]]
    eras: dict[int, Era]
    pipeline_version: str
    documents: dict[str, DocumentInfo]
    release_eras: dict[date, int]
    versions: dict[str, DocumentVersion]
    page_classes: Counter[str]
    full_corpus: bool


@dataclass
class LoadCounts:
    pages: int = 0
    cells: int = 0
    candidates: int = 0
    selected_candidates: int = 0
    page_classes: Counter[str] | None = None

    def __post_init__(self) -> None:
        if self.page_classes is None:
            self.page_classes = Counter()


@dataclass(frozen=True)
class PreparedCell:
    cell: dict[str, Any]
    selected_order: int | None
    candidates: list[tuple[Any, ...]]


def parse_iso_date(value: Any, label: str, optional: bool = False) -> date | None:
    if value in (None, "") and optional:
        return None
    try:
        return date.fromisoformat(str(value))
    except (TypeError, ValueError) as error:
        raise LoaderError(f"invalid {label}: {value!r}") from error


def exact_decimal(value: Any, label: str) -> Decimal | None:
    if value in (None, ""):
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError) as error:
        raise LoaderError(f"invalid exact numeric value for {label}: {value!r}") from error


def json_text(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def require_type(value: Any, expected: type, label: str) -> Any:
    if not isinstance(value, expected):
        raise LoaderError(f"{label} must be {expected.__name__}, got {type(value).__name__}")
    return value


def load_era_map(path: Path) -> dict[int, Era]:
    try:
        with path.open(newline="", encoding="utf-8-sig") as handle:
            rows = list(csv.DictReader(handle))
    except OSError as error:
        raise LoaderError(f"cannot read era map {path}: {error}") from error
    eras: dict[int, Era] = {}
    for row_number, row in enumerate(rows, 2):
        try:
            era_id = int(row["Era"])
            count_text = (row.get("# of docs") or "").strip()
            era = Era(
                era_id=era_id,
                first=parse_iso_date(row["First"], f"era-map row {row_number} First"),
                last=parse_iso_date(row["Last"], f"era-map row {row_number} Last"),
                source_doc_count=int(count_text) if count_text else None,
                description=(row.get("description") or "").strip(),
            )
        except (KeyError, TypeError, ValueError) as error:
            raise LoaderError(f"invalid era-map row {row_number}: {row}") from error
        if era_id in eras or not 1 <= era_id <= 8 or era.first > era.last or not era.description:
            raise LoaderError(f"invalid or duplicate era-map row {row_number}: {row}")
        eras[era_id] = era
    if set(eras) != set(range(1, 9)):
        raise LoaderError(f"era map must contain exactly era IDs 1-8; found {sorted(eras)}")
    return eras


def resolve_jsonl_files(jsonl_dir: str | None, jsonl_files: Sequence[str] | None) -> list[Path]:
    if jsonl_dir:
        root = Path(jsonl_dir).expanduser().resolve()
        files = sorted(root.rglob("ocr_raw.part_*.jsonl"))
    else:
        files = sorted(Path(item).expanduser().resolve() for item in (jsonl_files or []))
    if not files:
        raise LoaderError("no JSONL parts found")
    if len(set(files)) != len(files):
        raise LoaderError("the same JSONL file was supplied more than once")
    missing = [str(path) for path in files if not path.is_file()]
    if missing:
        raise LoaderError(f"JSONL files do not exist: {missing}")
    names = [path.name for path in files]
    if len(set(names)) != len(names):
        raise LoaderError(f"JSONL part filenames must be unique: {names}")
    return files


def decode_record(path: Path, line_number: int, line: str) -> dict[str, Any]:
    try:
        page = json.loads(line)
    except json.JSONDecodeError as error:
        raise LoaderError(f"invalid JSON at {path}:{line_number}: {error}") from error
    if not isinstance(page, dict):
        raise LoaderError(f"JSONL record at {path}:{line_number} is not an object")
    return page


def iter_records(files: Sequence[Path]) -> Iterator[Record]:
    for path in files:
        with path.open(encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, 1):
                if not line.strip():
                    raise LoaderError(f"blank JSONL line at {path}:{line_number}")
                yield Record(path, line_number, decode_record(path, line_number, line))


def page_context(record: Record, cell: dict[str, Any] | None = None) -> str:
    page = record.page
    context = (
        f"source_file={page.get('source_file')!r}, part={record.part.name!r}, "
        f"line={record.line_number}, page={page.get('page_number')!r}"
    )
    if cell is not None:
        context += (
            f", table={cell.get('table_instance_id')!r}, row={cell.get('row_index')!r}, "
            f"column={cell.get('column_index')!r}"
        )
    return context


def classify_later_version(document: DocumentInfo, era: Era) -> str:
    evidence = f"{document.source_file} {era.description}".lower()
    return "corrected" if "correct" in evidence else "revised"


def build_version_plan(
    documents: dict[str, DocumentInfo], eras: dict[int, Era], full_corpus: bool
) -> tuple[dict[date, int], dict[str, DocumentVersion]]:
    by_cycle: dict[date, list[DocumentInfo]] = defaultdict(list)
    for document in documents.values():
        by_cycle[document.cycle].append(document)
    release_eras: dict[date, int] = {}
    versions: dict[str, DocumentVersion] = {}
    observed_duplicates: set[date] = set()
    for cycle, cycle_documents in sorted(by_cycle.items()):
        cycle_documents.sort(key=lambda item: (item.release_date, item.source_file))
        era_ids = {item.era_id for item in cycle_documents}
        if len(era_ids) != 1:
            raise LoaderError(f"release cycle {cycle:%Y-%m} spans eras {sorted(era_ids)}")
        release_eras[cycle] = next(iter(era_ids))
        if len(cycle_documents) > 1:
            if cycle not in KNOWN_DUPLICATE_CYCLES or len(cycle_documents) != 2:
                raise LoaderError(
                    f"unrecorded formatting/version break: release cycle {cycle:%Y-%m} "
                    f"contains {[item.source_file for item in cycle_documents]}"
                )
            observed_duplicates.add(cycle)
            earlier, later = cycle_documents
            note = "Known duplicate release cycle; later document preferred per g6_era_map.csv."
            versions[earlier.source_file] = DocumentVersion(1, "original", False, None, note)
            versions[later.source_file] = DocumentVersion(
                2,
                classify_later_version(later, eras[later.era_id]),
                True,
                earlier.source_file,
                note,
            )
        else:
            only = cycle_documents[0]
            versions[only.source_file] = DocumentVersion(1, "original", True, None, None)
    if full_corpus and observed_duplicates != KNOWN_DUPLICATE_CYCLES:
        missing = sorted(item.isoformat() for item in KNOWN_DUPLICATE_CYCLES - observed_duplicates)
        extra = sorted(item.isoformat() for item in observed_duplicates - KNOWN_DUPLICATE_CYCLES)
        raise LoaderError(f"full-corpus duplicate cycles differ; missing={missing}, extra={extra}")
    return release_eras, versions


def scan_registry(files: list[Path], eras: dict[int, Era]) -> ScanResult:
    documents: dict[str, DocumentInfo] = {}
    manifest: list[dict[str, Any]] = []
    pipelines: set[str] = set()
    page_classes: Counter[str] = Counter()
    page_keys: set[tuple[str, int]] = set()
    closed_sources: set[str] = set()
    current_source: str | None = None
    for path in files:
        line_count = 0
        with path.open(encoding="utf-8") as handle:
            for line_count, line in enumerate(handle, 1):
                page = decode_record(path, line_count, line)
                try:
                    source_file = str(page["source_file"])
                    release_date = parse_iso_date(page["release_date"], "release_date")
                    era_id = int(page["era_id"])
                    pipeline_version = str(page["pipeline_version"])
                    page_number = int(page["page_number"])
                    page_class = str(page["page_classification"])
                except (KeyError, TypeError, ValueError) as error:
                    raise LoaderError(f"invalid page registry fields at {path}:{line_count}") from error
                if not source_file or not pipeline_version or page_number <= 0:
                    raise LoaderError(f"invalid page registry values at {path}:{line_count}")
                if era_id not in eras or not eras[era_id].first <= release_date <= eras[era_id].last:
                    raise LoaderError(
                        f"release date/era mismatch at {path}:{line_count}: "
                        f"date={release_date}, era={era_id}"
                    )
                if page_class not in PAGE_CLASSES:
                    raise LoaderError(f"invalid page classification at {path}:{line_count}: {page_class!r}")
                if current_source != source_file:
                    if current_source is not None:
                        closed_sources.add(current_source)
                    if source_file in closed_sources:
                        raise LoaderError(f"source document is not contiguous in JSONL order: {source_file}")
                    current_source = source_file
                page_key = (source_file, page_number)
                if page_key in page_keys:
                    raise LoaderError(f"duplicate source page in JSONL: {page_key}")
                page_keys.add(page_key)
                pipelines.add(pipeline_version)
                page_classes[page_class] += 1
                existing = documents.get(source_file)
                if existing is None:
                    documents[source_file] = DocumentInfo(
                        source_file,
                        release_date,
                        era_id,
                        pipeline_version,
                        page_number,
                    )
                else:
                    expected = (existing.release_date, existing.era_id, existing.pipeline_version)
                    actual = (release_date, era_id, pipeline_version)
                    if actual != expected:
                        raise LoaderError(
                            f"inconsistent page registry for {source_file}: expected={expected}, actual={actual}"
                        )
                    existing.max_page_number = max(existing.max_page_number, page_number)
                    existing.page_records += 1
        manifest.append(
            {"filename": path.name, "byte_size": path.stat().st_size, "line_count": line_count}
        )
    if len(pipelines) != 1:
        raise LoaderError(f"all JSONL records must use one pipeline_version; found {sorted(pipelines)}")
    full_corpus = {path.name for path in files} == FULL_CORPUS_PARTS
    release_eras, versions = build_version_plan(documents, eras, full_corpus)
    return ScanResult(
        files=files,
        manifest=manifest,
        eras=eras,
        pipeline_version=next(iter(pipelines)),
        documents=documents,
        release_eras=release_eras,
        versions=versions,
        page_classes=page_classes,
        full_corpus=full_corpus,
    )


def candidate_numeric(candidate: dict[str, Any], label: str) -> Decimal | None:
    return exact_decimal(candidate.get("value_numeric"), label)


def candidate_matches_parent(candidate: dict[str, Any], cell: dict[str, Any]) -> bool:
    if candidate.get("eligible") is not True or candidate.get("value_status") != cell.get("value_status"):
        return False
    comparisons = (
        ("selected_source", "source"),
        ("value_raw", "raw"),
        ("normalization_rule", "normalization"),
    )
    for parent_key, candidate_key in comparisons:
        parent_value = cell.get(parent_key)
        if parent_value not in (None, "") and candidate.get(candidate_key) != parent_value:
            return False
    if cell.get("value_numeric") not in (None, ""):
        if candidate_numeric(candidate, "candidate value_numeric") != exact_decimal(
            cell.get("value_numeric"), "cell value_numeric"
        ):
            return False
    if cell.get("ocr_confidence") is not None and candidate.get("confidence") != cell.get(
        "ocr_confidence"
    ):
        return False
    return True


def candidate_fingerprint(candidate: dict[str, Any]) -> str:
    ignored = {"ocr_variant", "selected", "is_selected"}
    return json_text({key: value for key, value in candidate.items() if key not in ignored})


def selection_error(record: Record, cell: dict[str, Any], reason: str, orders: Iterable[int]) -> LoaderError:
    candidates = cell.get("ocr_candidates", [])
    details = []
    for order in orders:
        candidate = candidates[order]
        details.append(
            {
                "candidate_order": order,
                "ocr_source": candidate.get("source"),
                "ocr_variant": candidate.get("ocr_variant"),
                "raw": candidate.get("raw"),
                "numeric": candidate.get("value_numeric"),
                "status": candidate.get("value_status"),
                "confidence": candidate.get("confidence"),
                "normalization": candidate.get("normalization"),
                "eligible": candidate.get("eligible"),
            }
        )
    return LoaderError(
        f"candidate selection {reason}; {page_context(record, cell)}; "
        f"parent_final={json_text({key: cell.get(key) for key in ('selected_source', 'value_raw', 'value_numeric', 'value_status', 'normalization_rule', 'ocr_confidence')})}; "
        f"competing_candidates={json_text(details)}"
    )


def selected_candidate_order(record: Record, cell: dict[str, Any]) -> int | None:
    candidates = require_type(cell.get("ocr_candidates"), list, "cell ocr_candidates")
    status = cell.get("value_status")
    if status not in VALUE_STATUSES:
        raise LoaderError(f"invalid cell value_status {status!r}; {page_context(record, cell)}")
    explicit_fields_present = any(
        "selected" in candidate or "is_selected" in candidate for candidate in candidates
    )
    explicit_selected: list[int] = []
    if explicit_fields_present:
        for order, candidate in enumerate(candidates):
            values = []
            for key in ("selected", "is_selected"):
                if key in candidate:
                    if not isinstance(candidate[key], bool):
                        raise selection_error(record, cell, f"has non-boolean {key}", [order])
                    values.append(candidate[key])
            if len(set(values)) > 1:
                raise selection_error(record, cell, "has conflicting explicit flags", [order])
            if values and values[0]:
                explicit_selected.append(order)
        if status in {"reported", "not_available"}:
            if len(explicit_selected) != 1:
                raise selection_error(record, cell, "requires exactly one explicit selection", explicit_selected)
            order = explicit_selected[0]
            if not candidate_matches_parent(candidates[order], cell):
                raise selection_error(record, cell, "explicit selection disagrees with parent", [order])
            return order
        if explicit_selected:
            raise selection_error(record, cell, "blank/error cell has an explicit selection", explicit_selected)
        return None
    if status in {"blank", "extraction_error"}:
        return None
    matches = [
        order for order, candidate in enumerate(candidates) if candidate_matches_parent(candidate, cell)
    ]
    if len(matches) == 1:
        return matches[0]
    if not matches:
        raise selection_error(record, cell, "found no candidate matching parent final fields", range(len(candidates)))
    if len({candidate_fingerprint(candidates[order]) for order in matches}) == 1:
        return min(matches)
    raise selection_error(record, cell, "is ambiguous after matching all parent final fields", matches)


def map_candidate(
    candidate: dict[str, Any], order: int, selected_order: int | None, selection_reason: Any
) -> tuple[Any, ...]:
    source = candidate.get("source")
    status = candidate.get("value_status")
    eligible = candidate.get("eligible")
    if not isinstance(source, str) or not source:
        raise LoaderError(f"candidate {order} has invalid source: {source!r}")
    if status not in VALUE_STATUSES:
        raise LoaderError(f"candidate {order} has invalid value_status: {status!r}")
    if not isinstance(eligible, bool):
        raise LoaderError(f"candidate {order} has non-boolean eligible value: {eligible!r}")
    supporting = candidate.get("supporting_raw_strings")
    if supporting is not None and not isinstance(supporting, list):
        raise LoaderError(f"candidate {order} supporting_raw_strings must be an array or null")
    selected = order == selected_order
    return (
        order,
        source,
        candidate.get("ocr_variant") or None,
        candidate.get("raw"),
        candidate_numeric(candidate, f"candidate {order} value_numeric"),
        status,
        candidate.get("confidence"),
        candidate.get("normalization") or None,
        eligible,
        selected,
        selection_reason if selected else None,
        candidate.get("measure_canonical") or None,
        candidate.get("unsafe_decimal_relocation"),
        candidate.get("trimmed_trailing_digits"),
        json_text(supporting) if supporting is not None else None,
    )


def prepare_page(record: Record) -> list[PreparedCell]:
    page = record.page
    required = (
        "source_file",
        "release_date",
        "era_id",
        "pipeline_version",
        "page_number",
        "page_classification",
        "page_adjustment_status",
        "date_reconciliation",
        "words",
        "sparse_ocr_words",
        "embedded_locator_words",
        "table_anchors",
        "table_structure",
        "cells",
    )
    missing = [key for key in required if key not in page]
    if missing:
        raise LoaderError(f"missing page keys {missing}; {page_context(record)}")
    page_class = page["page_classification"]
    if page_class not in PAGE_CLASSES:
        raise LoaderError(f"invalid page classification {page_class!r}; {page_context(record)}")
    if page["page_adjustment_status"] not in ADJUSTMENT_STATUSES:
        raise LoaderError(
            f"invalid page adjustment status {page['page_adjustment_status']!r}; {page_context(record)}"
        )
    for key in ("words", "sparse_ocr_words", "embedded_locator_words", "table_anchors", "table_structure", "cells"):
        require_type(page[key], list, f"page {key}")
    require_type(page["date_reconciliation"], dict, "page date_reconciliation")
    parse_iso_date(page["release_date"], "release_date")
    parse_iso_date(page.get("printed_release_date"), "printed_release_date", optional=True)
    cells = page["cells"]
    if cells and page_class != "table_page":
        raise LoaderError(f"non-table page emitted cells; {page_context(record)}")
    if page_class == "table_page" and not cells:
        raise LoaderError(f"table page emitted no cells; {page_context(record)}")
    seen: set[tuple[str, int, int]] = set()
    prepared: list[PreparedCell] = []
    for cell in cells:
        require_type(cell, dict, "cell")
        try:
            physical_key = (
                str(cell["table_instance_id"]),
                int(cell["row_index"]),
                int(cell["column_index"]),
            )
            table_number = int(cell["table_number"])
        except (KeyError, TypeError, ValueError) as error:
            raise LoaderError(f"invalid physical cell key; {page_context(record, cell)}") from error
        if table_number <= 0 or physical_key[1] < 0 or physical_key[2] < 0:
            raise LoaderError(f"invalid cell indices; {page_context(record, cell)}")
        if physical_key in seen:
            raise LoaderError(f"duplicate physical cell key {physical_key}; {page_context(record, cell)}")
        seen.add(physical_key)
        for key in (
            "physical_row_bounds",
            "bbox",
            "matched_month_label_candidates",
            "column_path",
            "adjacent_release_values",
            "validation_flags",
        ):
            require_type(cell.get(key), list, f"cell {key}")
        require_type(cell.get("canonical_column"), dict, "cell canonical_column")
        parse_iso_date(cell.get("observation_date"), "cell observation_date", optional=True)
        selected_order = selected_candidate_order(record, cell)
        candidates = [
            map_candidate(candidate, order, selected_order, cell.get("selection_reason"))
            for order, candidate in enumerate(cell["ocr_candidates"])
        ]
        prepared.append(PreparedCell(cell, selected_order, candidates))
    return prepared


def validate_counts(scan: ScanResult, counts: LoadCounts) -> None:
    failures: list[str] = []
    manifest_lines = sum(item["line_count"] for item in scan.manifest)
    if counts.pages != manifest_lines:
        failures.append(f"pages={counts.pages}, manifest lines={manifest_lines}")
    if counts.page_classes != scan.page_classes:
        failures.append(
            f"page classifications changed between passes: {counts.page_classes} != {scan.page_classes}"
        )
    if scan.full_corpus:
        actual = {
            "releases": len(scan.release_eras),
            "documents": len(scan.documents),
            "pages": counts.pages,
            "cells": counts.cells,
            **counts.page_classes,
        }
        for key, expected in FULL_CORPUS_TOTALS.items():
            if actual.get(key, 0) != expected:
                failures.append(f"full-corpus {key}={actual.get(key, 0)}, expected={expected}")
    if failures:
        raise LoaderError("validation failed: " + "; ".join(failures))


def validate_jsonl_pass(scan: ScanResult) -> LoadCounts:
    counts = LoadCounts()
    for record in iter_records(scan.files):
        page = record.page
        source_file = page.get("source_file")
        document = scan.documents.get(source_file)
        if document is None:
            raise LoaderError(f"page source file is absent from registry; {page_context(record)}")
        expected = (
            document.release_date.isoformat(),
            document.era_id,
            document.pipeline_version,
        )
        actual = (page.get("release_date"), page.get("era_id"), page.get("pipeline_version"))
        if actual != expected:
            raise LoaderError(f"page fields changed between passes; {page_context(record)}")
        prepared = prepare_page(record)
        counts.pages += 1
        counts.cells += len(prepared)
        counts.candidates += sum(len(cell.candidates) for cell in prepared)
        counts.selected_candidates += sum(cell.selected_order is not None for cell in prepared)
        counts.page_classes[page["page_classification"]] += 1
    validate_counts(scan, counts)
    return counts


def verify_live_schema(connection: Any) -> None:
    table_names = tuple(EXPECTED_COLUMNS)
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT table_name, column_name, data_type, is_identity
            FROM information_schema.columns
            WHERE table_schema = 'raw' AND table_name = ANY(%s)
            ORDER BY table_name, ordinal_position
            """,
            (list(table_names),),
        )
        rows = cursor.fetchall()
    actual_columns: dict[str, list[str]] = defaultdict(list)
    column_metadata: dict[tuple[str, str], tuple[str, str]] = {}
    for table_name, column_name, data_type, is_identity in rows:
        actual_columns[table_name].append(column_name)
        column_metadata[(table_name, column_name)] = (data_type, is_identity)
    differences = []
    for table_name, expected in EXPECTED_COLUMNS.items():
        actual = tuple(actual_columns.get(table_name, []))
        if actual != expected:
            differences.append(f"raw.{table_name}: expected={expected}, actual={actual}")
    for key, expected_type in IDENTITY_COLUMNS.items():
        actual_type, is_identity = column_metadata.get(key, (None, None))
        if actual_type != expected_type or is_identity != "YES":
            differences.append(
                f"raw.{key[0]}.{key[1]}: expected identity {expected_type}, "
                f"actual type={actual_type!r}, is_identity={is_identity!r}"
            )
    if differences:
        raise LoaderError("live raw schema differs from loader contract:\n" + "\n".join(differences))


def ensure_empty_database(connection: Any, run_label: str) -> None:
    with connection.cursor() as cursor:
        cursor.execute("SELECT EXISTS (SELECT 1 FROM raw.extraction_run WHERE run_label = %s)", (run_label,))
        if cursor.fetchone()[0]:
            raise LoaderError(f"run_label already exists: {run_label!r}")
        populated = []
        for table_name in EXPECTED_COLUMNS:
            cursor.execute(f"SELECT EXISTS (SELECT 1 FROM raw.{table_name} LIMIT 1)")
            if cursor.fetchone()[0]:
                populated.append(f"raw.{table_name}")
    if populated:
        raise LoaderError(
            "raw extraction tables are not empty; refusing to append: " + ", ".join(populated)
        )


def insert_registry(
    connection: Any,
    scan: ScanResult,
    run_label: str,
    input_root: str,
    cleanup_report_path: str | None,
) -> tuple[int, dict[date, int], dict[str, int]]:
    with connection.transaction(), connection.cursor() as cursor:
        cursor.executemany(
            """
            INSERT INTO raw.g6_era
                (era_id, first_document_date, last_document_date,
                 source_reported_doc_count, era_description)
            VALUES (%s, %s, %s, %s, %s)
            """,
            [
                (era.era_id, era.first, era.last, era.source_doc_count, era.description)
                for era in scan.eras.values()
            ],
        )
        cursor.execute(
            """
            INSERT INTO raw.extraction_run
                (run_label, pipeline_version, input_root, input_artifact_manifest,
                 cleanup_report_path, full_corpus_completed)
            VALUES (%s, %s, %s, %s::jsonb, %s, false)
            RETURNING extraction_run_id
            """,
            (
                run_label,
                scan.pipeline_version,
                input_root,
                json_text(scan.manifest),
                cleanup_report_path,
            ),
        )
        extraction_run_id = cursor.fetchone()[0]
        release_ids: dict[date, int] = {}
        for cycle, era_id in sorted(scan.release_eras.items()):
            cursor.execute(
                """
                INSERT INTO raw.g6_release
                    (release_cycle_month, publication_code, release_title, era_id)
                VALUES (%s, %s, %s, %s)
                RETURNING g6_release_id
                """,
                (cycle, PUBLICATION_CODE, RELEASE_TITLE, era_id),
            )
            release_ids[cycle] = cursor.fetchone()[0]
        source_document_ids: dict[str, int] = {}
        by_cycle: dict[date, list[DocumentInfo]] = defaultdict(list)
        for document in scan.documents.values():
            by_cycle[document.cycle].append(document)
        for cycle, documents in sorted(by_cycle.items()):
            documents.sort(key=lambda item: scan.versions[item.source_file].version)
            for document in documents:
                version = scan.versions[document.source_file]
                supersedes_id = (
                    source_document_ids[version.supersedes_source_file]
                    if version.supersedes_source_file
                    else None
                )
                cursor.execute(
                    """
                    INSERT INTO raw.source_document
                        (g6_release_id, document_date, source_filename,
                         source_relative_path, source_format, document_version,
                         version_type, is_preferred_version,
                         supersedes_source_document_id, page_count, source_notes)
                    VALUES (%s, %s, %s, %s, 'pdf', %s, %s, %s, %s, %s, %s)
                    RETURNING source_document_id
                    """,
                    (
                        release_ids[cycle],
                        document.release_date,
                        PurePosixPath(document.source_file).name,
                        document.source_file,
                        version.version,
                        version.version_type,
                        version.preferred,
                        supersedes_id,
                        document.max_page_number,
                        version.notes,
                    ),
                )
                source_document_ids[document.source_file] = cursor.fetchone()[0]
    return extraction_run_id, release_ids, source_document_ids


PAGE_COLUMNS = (
    "source_document_id",
    "extraction_run_id",
    "page_number",
    "input_part_name",
    "input_line_number",
    "page_classification",
    "classification_score",
    "classification_reason",
    "printed_release_code",
    "printed_release_title",
    "printed_release_date",
    "page_adjustment_status",
    "mean_ocr_confidence",
    "raw_ocr_text",
    "sparse_ocr_text",
    "embedded_locator_text",
    "date_reconciliation",
    "rendered_ocr_words",
    "sparse_ocr_words",
    "embedded_locator_words",
    "table_anchors",
    "table_structure",
)
PAGE_JSON_COLUMNS = {
    "date_reconciliation",
    "rendered_ocr_words",
    "sparse_ocr_words",
    "embedded_locator_words",
    "table_anchors",
    "table_structure",
}
CELL_COLUMNS = (
    "source_page_extraction_id",
    "source_document_id",
    "page_number",
    "table_number",
    "table_instance_id",
    "row_index",
    "column_index",
    "physical_row_center",
    "physical_row_bounds",
    "cell_bbox",
    "ink_density",
    "row_label_raw",
    "matched_month_label_candidates",
    "pipeline_observation_date",
    "observation_date_status",
    "observation_date_source",
    "column_path",
    "canonical_column",
    "pipeline_cell_status",
    "pipeline_selection_reason",
    "cross_release_support_count",
    "adjacent_release_values",
    "validation_flags",
    "arithmetic_selection",
    "cross_release_selection",
)
CELL_JSON_COLUMNS = {
    "physical_row_bounds",
    "cell_bbox",
    "matched_month_label_candidates",
    "column_path",
    "canonical_column",
    "adjacent_release_values",
    "validation_flags",
    "arithmetic_selection",
    "cross_release_selection",
}
CANDIDATE_COLUMNS = (
    "g6_cell_extraction_id",
    "candidate_order",
    "ocr_source",
    "ocr_variant",
    "raw_recognized_string",
    "candidate_numeric",
    "candidate_status",
    "ocr_confidence",
    "normalization_rule",
    "is_eligible",
    "is_selected",
    "selection_reason",
    "measure_canonical",
    "unsafe_decimal_relocation",
    "trimmed_trailing_digits",
    "supporting_raw_strings",
)


def placeholders(columns: Sequence[str], json_columns: set[str]) -> str:
    return "(" + ",".join("%s::jsonb" if item in json_columns else "%s" for item in columns) + ")"


def page_values(
    record: Record, source_document_id: int, extraction_run_id: int
) -> tuple[Any, ...]:
    page = record.page
    values: dict[str, Any] = {
        "source_document_id": source_document_id,
        "extraction_run_id": extraction_run_id,
        "page_number": int(page["page_number"]),
        "input_part_name": record.part.name,
        "input_line_number": record.line_number,
        "page_classification": page["page_classification"],
        "classification_score": page.get("classification_score"),
        "classification_reason": page.get("classification_reason"),
        "printed_release_code": page.get("printed_release_code"),
        "printed_release_title": page.get("printed_release_title"),
        "printed_release_date": parse_iso_date(
            page.get("printed_release_date"), "printed_release_date", optional=True
        ),
        "page_adjustment_status": page["page_adjustment_status"],
        "mean_ocr_confidence": page.get("mean_confidence"),
        "raw_ocr_text": page.get("raw_text"),
        "sparse_ocr_text": page.get("sparse_ocr_text"),
        "embedded_locator_text": page.get("embedded_locator_text"),
        "date_reconciliation": json_text(page["date_reconciliation"]),
        "rendered_ocr_words": json_text(page["words"]),
        "sparse_ocr_words": json_text(page["sparse_ocr_words"]),
        "embedded_locator_words": json_text(page["embedded_locator_words"]),
        "table_anchors": json_text(page["table_anchors"]),
        "table_structure": json_text(page["table_structure"]),
    }
    return tuple(values[column] for column in PAGE_COLUMNS)


def cell_values(
    prepared: PreparedCell,
    source_page_extraction_id: int,
    source_document_id: int,
    page_number: int,
) -> tuple[Any, ...]:
    cell = prepared.cell
    values: dict[str, Any] = {
        "source_page_extraction_id": source_page_extraction_id,
        "source_document_id": source_document_id,
        "page_number": page_number,
        "table_number": int(cell["table_number"]),
        "table_instance_id": str(cell["table_instance_id"]),
        "row_index": int(cell["row_index"]),
        "column_index": int(cell["column_index"]),
        "physical_row_center": cell.get("physical_row_center"),
        "physical_row_bounds": json_text(cell["physical_row_bounds"]),
        "cell_bbox": json_text(cell["bbox"]),
        "ink_density": cell.get("ink_density"),
        "row_label_raw": cell.get("row_label_raw"),
        "matched_month_label_candidates": json_text(cell["matched_month_label_candidates"]),
        "pipeline_observation_date": parse_iso_date(
            cell.get("observation_date"), "cell observation_date", optional=True
        ),
        "observation_date_status": cell.get("observation_date_status") or None,
        "observation_date_source": cell.get("observation_date_source") or None,
        "column_path": json_text(cell["column_path"]),
        "canonical_column": json_text(cell["canonical_column"]),
        "pipeline_cell_status": cell["value_status"],
        "pipeline_selection_reason": cell.get("selection_reason") or None,
        "cross_release_support_count": int(cell.get("cross_release_support_count") or 0),
        "adjacent_release_values": json_text(cell["adjacent_release_values"]),
        "validation_flags": json_text(cell["validation_flags"]),
        "arithmetic_selection": (
            json_text(cell["arithmetic_selection"]) if cell.get("arithmetic_selection") is not None else None
        ),
        "cross_release_selection": (
            json_text(cell["cross_release_selection"])
            if cell.get("cross_release_selection") is not None
            else None
        ),
    }
    return tuple(values[column] for column in CELL_COLUMNS)


def insert_page(
    cursor: Any,
    record: Record,
    source_document_id: int,
    extraction_run_id: int,
    counts: LoadCounts,
) -> None:
    prepared_cells = prepare_page(record)
    page = record.page
    cursor.execute(
        f"INSERT INTO raw.source_page_extraction ({','.join(PAGE_COLUMNS)}) "
        f"VALUES {placeholders(PAGE_COLUMNS, PAGE_JSON_COLUMNS)} "
        "RETURNING source_page_extraction_id",
        page_values(record, source_document_id, extraction_run_id),
    )
    source_page_extraction_id = cursor.fetchone()[0]
    page_number = int(page["page_number"])
    cell_id_by_key: dict[tuple[str, int, int], int] = {}
    if prepared_cells:
        template = placeholders(CELL_COLUMNS, CELL_JSON_COLUMNS)
        rows = [
            cell_values(item, source_page_extraction_id, source_document_id, page_number)
            for item in prepared_cells
        ]
        cursor.execute(
            f"INSERT INTO raw.g6_cell_extraction ({','.join(CELL_COLUMNS)}) VALUES "
            + ",".join(template for _ in rows)
            + " RETURNING g6_cell_extraction_id, table_instance_id, row_index, column_index",
            tuple(value for row in rows for value in row),
        )
        for cell_id, table_instance_id, row_index, column_index in cursor.fetchall():
            cell_id_by_key[(table_instance_id, row_index, column_index)] = cell_id
        if len(cell_id_by_key) != len(prepared_cells):
            raise LoaderError(f"cell ID capture mismatch; {page_context(record)}")
        copy_sql = f"COPY raw.g6_ocr_candidate ({','.join(CANDIDATE_COLUMNS)}) FROM STDIN"
        with cursor.copy(copy_sql) as copy:
            for item in prepared_cells:
                cell = item.cell
                key = (str(cell["table_instance_id"]), int(cell["row_index"]), int(cell["column_index"]))
                cell_id = cell_id_by_key[key]
                for candidate in item.candidates:
                    copy.write_row((cell_id, *candidate))
    counts.pages += 1
    counts.cells += len(prepared_cells)
    counts.candidates += sum(len(item.candidates) for item in prepared_cells)
    counts.selected_candidates += sum(item.selected_order is not None for item in prepared_cells)
    counts.page_classes[page["page_classification"]] += 1


def load_documents(
    connection: Any,
    scan: ScanResult,
    extraction_run_id: int,
    source_document_ids: dict[str, int],
) -> LoadCounts:
    counts = LoadCounts()
    records = iter_records(scan.files)
    for source_file, document_records in groupby(records, key=lambda item: item.page.get("source_file")):
        if source_file not in source_document_ids:
            raise LoaderError(f"source file absent from registry lookup: {source_file!r}")
        last_record: Record | None = None
        try:
            with connection.transaction(), connection.cursor() as cursor:
                for record in document_records:
                    last_record = record
                    insert_page(
                        cursor,
                        record,
                        source_document_ids[source_file],
                        extraction_run_id,
                        counts,
                    )
        except Exception as error:
            location = page_context(last_record) if last_record else f"source_file={source_file!r}"
            if isinstance(error, LoaderError):
                raise LoaderError(f"document transaction rolled back; {location}: {error}") from error
            raise LoaderError(f"document transaction rolled back; {location}: {error}") from error
    validate_counts(scan, counts)
    return counts


def scalar(cursor: Any, query: str, parameters: tuple[Any, ...] = ()) -> int:
    cursor.execute(query, parameters)
    return int(cursor.fetchone()[0])


def validate_database(
    connection: Any,
    scan: ScanResult,
    extraction_run_id: int,
    counts: LoadCounts,
) -> None:
    failures: list[str] = []
    with connection.transaction(), connection.cursor() as cursor:
        checks = {
            "eras": ("SELECT count(*) FROM raw.g6_era", 8),
            "extraction_runs": ("SELECT count(*) FROM raw.extraction_run", 1),
            "releases": ("SELECT count(*) FROM raw.g6_release", len(scan.release_eras)),
            "documents": ("SELECT count(*) FROM raw.source_document", len(scan.documents)),
            "pages": ("SELECT count(*) FROM raw.source_page_extraction", counts.pages),
            "cells": ("SELECT count(*) FROM raw.g6_cell_extraction", counts.cells),
            "candidates": ("SELECT count(*) FROM raw.g6_ocr_candidate", counts.candidates),
        }
        for label, (query, expected) in checks.items():
            actual = scalar(cursor, query)
            if actual != expected:
                failures.append(f"{label}={actual}, expected={expected}")
        duplicate_pages = scalar(
            cursor,
            """
            SELECT count(*) FROM (
                SELECT source_document_id, extraction_run_id, page_number
                FROM raw.source_page_extraction
                GROUP BY 1,2,3 HAVING count(*) > 1
            ) duplicates
            """,
        )
        duplicate_cells = scalar(
            cursor,
            """
            SELECT count(*) FROM (
                SELECT source_page_extraction_id, table_instance_id, row_index, column_index
                FROM raw.g6_cell_extraction
                GROUP BY 1,2,3,4 HAVING count(*) > 1
            ) duplicates
            """,
        )
        orphan_pages = scalar(
            cursor,
            """
            SELECT count(*) FROM raw.source_page_extraction page
            LEFT JOIN raw.source_document document USING (source_document_id)
            LEFT JOIN raw.extraction_run run USING (extraction_run_id)
            WHERE document.source_document_id IS NULL OR run.extraction_run_id IS NULL
            """,
        )
        orphan_cells = scalar(
            cursor,
            """
            SELECT count(*) FROM raw.g6_cell_extraction cell
            LEFT JOIN raw.source_page_extraction page USING (source_page_extraction_id)
            WHERE page.source_page_extraction_id IS NULL
            """,
        )
        orphan_candidates = scalar(
            cursor,
            """
            SELECT count(*) FROM raw.g6_ocr_candidate candidate
            LEFT JOIN raw.g6_cell_extraction cell USING (g6_cell_extraction_id)
            WHERE cell.g6_cell_extraction_id IS NULL
            """,
        )
        non_table_cells = scalar(
            cursor,
            """
            SELECT count(*) FROM raw.g6_cell_extraction cell
            JOIN raw.source_page_extraction page USING (source_page_extraction_id)
            WHERE page.page_classification <> 'table_page'
            """,
        )
        bad_selection = scalar(
            cursor,
            """
            SELECT count(*) FROM (
                SELECT cell.g6_cell_extraction_id, cell.pipeline_cell_status,
                       count(candidate.*) FILTER (WHERE candidate.is_selected) AS selected_count
                FROM raw.g6_cell_extraction cell
                LEFT JOIN raw.g6_ocr_candidate candidate USING (g6_cell_extraction_id)
                GROUP BY cell.g6_cell_extraction_id, cell.pipeline_cell_status
                HAVING
                    (cell.pipeline_cell_status IN ('reported','not_available')
                     AND count(candidate.*) FILTER (WHERE candidate.is_selected) <> 1)
                    OR
                    (cell.pipeline_cell_status IN ('blank','extraction_error')
                     AND count(candidate.*) FILTER (WHERE candidate.is_selected) <> 0)
                    OR count(candidate.*) FILTER (WHERE candidate.is_selected) > 1
            ) invalid
            """,
        )
        bad_preferred = scalar(
            cursor,
            """
            SELECT count(*) FROM (
                SELECT release.g6_release_id
                FROM raw.g6_release release
                LEFT JOIN raw.source_document document USING (g6_release_id)
                GROUP BY release.g6_release_id
                HAVING count(document.*) FILTER (WHERE document.is_preferred_version) <> 1
            ) invalid
            """,
        )
        two_document_cycles = scalar(
            cursor,
            """
            SELECT count(*) FROM (
                SELECT release.g6_release_id
                FROM raw.g6_release release
                JOIN raw.source_document document USING (g6_release_id)
                GROUP BY release.g6_release_id HAVING count(*) = 2
            ) duplicate_cycles
            """,
        )
        invalid_document_counts = scalar(
            cursor,
            """
            SELECT count(*) FROM (
                SELECT release.g6_release_id
                FROM raw.g6_release release
                LEFT JOIN raw.source_document document USING (g6_release_id)
                GROUP BY release.g6_release_id HAVING count(document.*) NOT IN (1,2)
            ) invalid
            """,
        )
        for label, value in (
            ("duplicate pages", duplicate_pages),
            ("duplicate cells", duplicate_cells),
            ("orphan pages", orphan_pages),
            ("orphan cells", orphan_cells),
            ("orphan candidates", orphan_candidates),
            ("cells on non-table pages", non_table_cells),
            ("candidate-selection violations", bad_selection),
            ("preferred-document violations", bad_preferred),
            ("invalid document counts", invalid_document_counts),
        ):
            if value:
                failures.append(f"{label}={value}")
        if two_document_cycles != 5:
            failures.append(f"two-document release cycles={two_document_cycles}, expected=5")
        cursor.execute(
            """
            SELECT document.source_relative_path, count(page.*)
            FROM raw.source_document document
            LEFT JOIN raw.source_page_extraction page USING (source_document_id)
            GROUP BY document.source_relative_path
            """
        )
        actual_pages = {source_file: int(page_count) for source_file, page_count in cursor.fetchall()}
        expected_pages = {
            source_file: document.page_records for source_file, document in scan.documents.items()
        }
        if actual_pages != expected_pages:
            failures.append("page-to-document source-file mapping differs from JSONL registry")
        if scan.full_corpus:
            cursor.execute(
                "SELECT page_classification, count(*) FROM raw.source_page_extraction GROUP BY 1"
            )
            classes = {classification: int(count) for classification, count in cursor.fetchall()}
            for key in ("table_page", "metadata_page", "unrelated_release_page"):
                if classes.get(key, 0) != FULL_CORPUS_TOTALS[key]:
                    failures.append(
                        f"database {key}={classes.get(key, 0)}, expected={FULL_CORPUS_TOTALS[key]}"
                    )
        if failures:
            raise LoaderError("post-load validation failed: " + "; ".join(failures))
        cursor.execute(
            """
            UPDATE raw.extraction_run
            SET full_corpus_completed = true
            WHERE extraction_run_id = %s AND full_corpus_completed = false
            RETURNING extraction_run_id
            """,
            (extraction_run_id,),
        )
        if cursor.fetchone() is None:
            raise LoaderError("could not mark extraction run complete")


def load_database(
    scan: ScanResult, run_label: str, input_root: str, cleanup_report_path: str | None
) -> LoadCounts:
    missing_env = [
        name for name in ("PGHOST", "PGPORT", "PGDATABASE", "PGUSER", "PGPASSWORD") if not os.getenv(name)
    ]
    if missing_env:
        raise LoaderError(f"missing PostgreSQL environment variables: {', '.join(missing_env)}")
    try:
        import psycopg
    except ImportError as error:
        raise LoaderError("psycopg 3 is required; install requirements.txt") from error
    with psycopg.connect() as connection:
        connection.autocommit = True
        verify_live_schema(connection)
        ensure_empty_database(connection, run_label)
        connection.autocommit = False
        extraction_run_id, _, source_document_ids = insert_registry(
            connection, scan, run_label, input_root, cleanup_report_path
        )
        counts = load_documents(connection, scan, extraction_run_id, source_document_ids)
        validate_database(connection, scan, extraction_run_id, counts)
        return counts


def print_summary(scan: ScanResult, counts: LoadCounts | None = None) -> None:
    print(f"Artifacts: {len(scan.files)} ({sum(item['line_count'] for item in scan.manifest)} lines)")
    print(f"Pipeline version: {scan.pipeline_version}")
    print(f"Logical releases: {len(scan.release_eras)}")
    print(f"Source documents: {len(scan.documents)}")
    print(f"Known duplicate cycles present: {sum(1 for cycle in scan.release_eras if cycle in KNOWN_DUPLICATE_CYCLES)}")
    if counts is not None:
        print(f"Pages: {counts.pages} ({dict(sorted(counts.page_classes.items()))})")
        print(f"Cells: {counts.cells}")
        print(f"OCR candidates: {counts.candidates}")
        print(f"Selected candidates: {counts.selected_candidates}")


def parse_arguments(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Load G.6 OCR JSONL into the existing PostgreSQL raw schema.")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--jsonl-dir", help="Directory recursively containing ocr_raw.part_*.jsonl files.")
    source.add_argument("--jsonl-file", action="append", dest="jsonl_files", help="JSONL part; repeat as needed.")
    parser.add_argument("--era-map", required=True, help="Path to g6_era_map.csv.")
    parser.add_argument("--run-label", required=True)
    parser.add_argument("--input-root", help="Original scanned-document/PDF input root; required with --load.")
    parser.add_argument("--cleanup-report-path")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="Parse and validate without connecting to PostgreSQL.")
    mode.add_argument("--load", action="store_true", help="Perform the database load after validation of pass 1.")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    try:
        args = parse_arguments(argv)
        if args.load and not args.input_root:
            raise LoaderError("--input-root is required with --load")
        input_root = project_relative_path(args.input_root) if args.input_root else None
        cleanup_report_path = (
            project_relative_path(args.cleanup_report_path)
            if args.cleanup_report_path
            else None
        )
        files = resolve_jsonl_files(args.jsonl_dir, args.jsonl_files)
        eras = load_era_map(Path(args.era_map).expanduser().resolve())
        print("Pass 1: scanning artifact manifest and document registry")
        scan = scan_registry(files, eras)
        print_summary(scan)
        if args.load:
            if not scan.full_corpus:
                raise LoaderError(
                    "--load requires the five canonical full-corpus JSONL parts; "
                    "use dry-run for partial inputs"
                )
            print("Pass 2: loading pages, cells, and candidates")
            counts = load_database(
                scan,
                args.run_label,
                input_root,
                cleanup_report_path,
            )
            print_summary(scan, counts)
            print("Load and post-load validation completed; full_corpus_completed=true")
        else:
            print("Pass 2: validating pages, cells, and candidates (dry-run)")
            counts = validate_jsonl_pass(scan)
            print_summary(scan, counts)
            print("Dry-run validation completed; no database connection was opened")
        return 0
    except (LoaderError, OSError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
