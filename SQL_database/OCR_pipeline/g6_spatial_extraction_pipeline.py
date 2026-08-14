from __future__ import annotations

import csv
import difflib
import hashlib
import json
import math
import os
import re
import shutil
import statistics
import subprocess
import sys
import time
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime
from itertools import combinations, product
from pathlib import Path
from xml.etree import ElementTree

try:
    import numpy as np
    from PIL import Image, ImageEnhance, ImageFilter, ImageOps
except ImportError:
    subprocess.run(
        [sys.executable, "-m", "pip", "install", "numpy", "pillow"],
        check=True,
    )
    import numpy as np
    from PIL import Image, ImageEnhance, ImageFilter, ImageOps


ROOT = Path(__file__).resolve().parent
PIPELINE_ROOT = ROOT
PROJECT_ROOT = PIPELINE_ROOT.parent
INPUT_ROOT = PIPELINE_ROOT / "fraser_g6_releases"
if not INPUT_ROOT.exists() and (PIPELINE_ROOT / "fraser_g6_issues").exists():
    INPUT_ROOT = PIPELINE_ROOT / "fraser_g6_issues"
ERA_MAP_PATH = PIPELINE_ROOT / "g6_era_map.csv"
OUTPUT_DIR = Path(
    os.environ.get(
        "G6_OUTPUT_DIR",
        PIPELINE_ROOT / "g6_extraction_output_v2",
    )
).expanduser()
CACHE_DIR = OUTPUT_DIR / "_cache"
BASELINE_METRICS_PATH = PIPELINE_ROOT / "g6_cleanup_baseline_metrics.json"
OCR_CACHE_VERSION = "cleanup-v3-20260724"
PIPELINE_VERSION = "date-reconciliation-v4-20260808"
RENDER_DPI = 240
TRUE_HIGH_RESOLUTION_DPI = 480
LOW_CONFIDENCE = 70.0
CANONICAL_NUMERIC_RE = re.compile(r"^-?\d+\.\d$")
ADDITIVE_ROUNDING_TOLERANCE = 0.2000001
PROCESS_STATS = {}
MAX_UNCORROBORATED_YEAR_DISTANCE_MONTHS = 18
MIN_HISTORICAL_YEAR_ANCHOR_ROWS = 2

OBSERVATION_COLUMNS = [
    "era_id",
    "source_file",
    "release_date",
    "page_number",
    "table_number",
    "table_instance_id",
    "table_name_raw",
    "units_raw",
    "measure_canonical",
    "adjustment_status",
    "observation_date",
    "observation_date_status",
    "observation_date_source",
    "row_index",
    "row_label_raw",
    "row_annotation_raw",
    "row_level_1_raw",
    "row_level_2_raw",
    "column_level_1_raw",
    "column_level_2_raw",
    "column_level_3_raw",
    "column_index",
    "column_count",
    "cell_bbox",
    "page_classification",
    "deposit_type_canonical",
    "geography_canonical",
    "customer_type_canonical",
    "cell_annotation_raw",
    "value_raw",
    "value_numeric",
    "value_status",
    "ocr_confidence",
    "selected_source",
    "selection_reason",
    "normalization_rule",
    "validation_flags",
    "cross_release_support_count",
    "true_high_resolution_attempted",
]
ISSUE_COLUMNS = [
    "era_id",
    "source_file",
    "release_date",
    "page_number",
    "table_number",
    "observation_date",
    "column_path",
    "severity",
    "issue_type",
    "detail",
]
METADATA_COLUMNS = [
    "era_id",
    "source_file",
    "release_date",
    "page_number",
    "metadata_type",
    "text_raw",
    "ocr_confidence",
]
PAGE_MANIFEST_COLUMNS = [
    "era_id",
    "source_file",
    "total_pages",
    "page_number",
    "printed_release_code",
    "printed_release_title",
    "printed_release_date",
    "page_adjustment_status",
    "direct_table_title_count",
    "inferred_table_title_count",
    "detected_month_row_count",
    "detected_numeric_column_count",
    "cells_extracted",
    "page_classification",
    "classification_score",
    "classification_reason",
]
MANUAL_REVIEW_COLUMNS = [
    "physical_cell_key",
    "source_file",
    "release_date",
    "page_number",
    "table_number",
    "table_instance_id",
    "adjustment_status",
    "observation_date",
    "measure_canonical",
    "deposit_type_canonical",
    "geography_canonical",
    "customer_type_canonical",
    "row_index",
    "column_index",
    "cell_bbox",
    "value_raw",
    "value_numeric",
    "value_status",
    "selected_source",
    "normalization_rule",
    "raw_ocr_strings",
    "all_numeric_candidates",
    "true_high_resolution_candidates",
    "adjacent_release_values",
    "validation_failures",
    "review_reason",
    "suggested_candidate",
    "rendered_cell_crop_path",
]
TABLE_TARGETS = [
    "Debits During the Month",
    "Average Deposits Outstanding",
    "Annual Rate of Deposit Turnover",
]
MONTHS = {
    name.lower(): number
    for number, name in enumerate(
        [
            "January",
            "February",
            "March",
            "April",
            "May",
            "June",
            "July",
            "August",
            "September",
            "October",
            "November",
            "December",
        ],
        1,
    )
}
FURNITURE_PATTERNS = (
    "federal reserve statistical release",
    "debits and deposit turnover at commercial banks",
    "for immediate release",
    "digitized for fraser",
    "fraser stlouisfed org",
    "federal reserve bank of st louis",
)


def group(parent, leaves, status):
    return {"parent": parent, "leaves": leaves, "status": status}


ERA_CONFIGS = {
    1: {
        "edges": [0.250, 0.372, 0.486, 0.596, 0.710, 0.825, 0.937],
        "groups": [
            group(
                ["To Demand Deposits", "Demand Deposits"],
                [["All Banks"], ["New York City"], ["Other Banks"]],
                "SA",
            ),
            group(
                ["To Savings Deposits By Type Of Customer", "Savings Deposits By Type Of Customer"],
                [["Total"], ["Business"], ["Other"]],
                "NSA",
            ),
        ],
        "rows": (13, 14),
    },
    2: {
        "edges": [0.197, 0.313, 0.418, 0.526, 0.634, 0.737, 0.846, 0.954],
        "groups": [
            group(
                ["To Demand Deposits", "Demand Deposits"],
                [["All Banks"], ["New York City"], ["Other Banks"]],
                "SA",
            ),
            group(
                ["To Savings Deposits By Type Of Customer", "Savings Deposits By Type Of Customer"],
                [["ATS/NOW"], ["Business"], ["Others", "Other"], ["Total"]],
                "NSA",
            ),
        ],
        "rows": (13, 14),
    },
    3: {
        "edges": [0.267, 0.402, 0.525, 0.657, 0.768, 0.920],
        "groups": [
            group(
                ["To Demand Deposits", "Demand Deposits"],
                [["All Banks"], ["New York City"], ["Other Banks"]],
                None,
            ),
            group(["To ATS/NOW Accounts", "ATS/NOW Accounts"], [None], None),
            group(["To Savings Deposits", "Savings Deposits"], [None], None),
        ],
        "rows": (13, 14),
    },
    4: {
        "edges": [0.197, 0.322, 0.447, 0.574, 0.699, 0.825, 0.998],
        "groups": [
            group(
                ["To Demand Deposits", "Demand Deposits"],
                [["All Banks"], ["New York City"], ["Other Banks"]],
                None,
            ),
            group(["To ATS/NOW Accounts", "ATS/NOW Accounts", "To NOW/ATS Accounts"], [None], None),
            group(["To MMDA", "MMDA"], [None], None),
            group(["To Savings Deposits", "Savings Deposits"], [None], None),
        ],
        "rows": (13, 14),
    },
    5: {
        "edges": [0.221, 0.342, 0.464, 0.584, 0.702, 0.825, 0.943],
        "groups": [
            group(
                ["To Demand Deposits", "Demand Deposits"],
                [["All Banks"], ["New York City"], ["Other Banks"]],
                None,
            ),
            group(["To NOW/ATS Accounts", "NOW/ATS Accounts", "To ATS/NOW Accounts"], [None], None),
            group(["To MMDA", "MMDA"], [None], None),
            group(["To Savings Deposits", "Savings Deposits"], [None], None),
        ],
        "rows": (14, 14),
    },
    6: {
        "edges": [0.221, 0.342, 0.464, 0.584, 0.702, 0.825, 0.943],
        "groups": [
            group(
                ["To Demand Deposits", "Demand Deposits"],
                [["All Banks"], ["New York City"], ["Other Banks"]],
                None,
            ),
            group(["To NOW/ATS Accounts", "NOW/ATS Accounts", "To ATS/NOW Accounts"], [None], None),
            group(["To MMDA", "MMDA"], [None], None),
            group(["To Savings Deposits", "Savings Deposits"], [None], None),
        ],
        "rows": (14, 14),
    },
    7: {
        "edges": [0.232, 0.377, 0.519, 0.661, 0.804, 0.945],
        "groups": [
            group(
                ["To Demand Deposits", "Demand Deposits"],
                [["All Banks"], ["New York City"], ["Other Banks"]],
                None,
            ),
            group(["To Other Checkable Deposits", "Other Checkable Deposits"], [None], None),
            group(["To Savings Deposits", "Savings Deposits"], [None], None),
        ],
        "rows": (14, 14),
    },
    8: {
        "edges": [0.232, 0.377, 0.519, 0.661, 0.804, 0.945],
        "groups": [
            group(
                ["To Demand Deposits", "Demand Deposits"],
                [["All Banks"], ["New York City"], ["Other Banks"]],
                None,
            ),
            group(["To Other Checkable Deposits", "Other Checkable Deposits"], [None], None),
            group(["To Savings Deposits", "Savings Deposits"], [None], None),
        ],
        "rows": (14, 14),
    },
}

NO_MMDA_CONFIG = {
    "edges": [0.223, 0.372, 0.521, 0.670, 0.821, 0.996],
    "groups": [
        group(
            ["To Demand Deposits", "Demand Deposits"],
            [["All Banks"], ["New York City"], ["Other Banks"]],
            None,
        ),
        group(
            [
                "To ATS/NOW Accounts",
                "ATS/NOW Accounts",
                "To NOW/ATS Accounts",
                "NOW/ATS Accounts",
            ],
            [None],
            None,
        ),
        group(["To Savings Deposits", "Savings Deposits"], [None], None),
    ],
}

ERA3_RIGHT_SHIFTED_EDGES = [
    0.354,
    0.467,
    0.572,
    0.681,
    0.776,
    0.905,
]


def project_relative_path(path):
    resolved = Path(path).expanduser().resolve()
    try:
        return str(resolved.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(resolved)


def executable(name):
    found = shutil.which(name)
    if found:
        return found
    patterns = [
        Path.home() / ".cache/codex-runtimes/codex-primary-runtime/dependencies/bin/override" / name,
        Path.home() / ".cache/codex-runtimes/codex-primary-runtime/dependencies/bin/fallback" / name,
        Path.home()
        / ".cache/codex-runtimes/codex-primary-runtime/dependencies/native/poppler/poppler/bin"
        / name,
        Path("/opt/homebrew/bin") / name,
    ]
    for path in patterns:
        if path.exists():
            return str(path)
    raise FileNotFoundError(
        f"{name} is required. Install tesseract and poppler, then rerun."
    )


PDFTOPPM = executable("pdftoppm")
PDFTOTEXT = executable("pdftotext")
TESSERACT = executable("tesseract")


def normalized(text):
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def remove_footnote_marker(text):
    text = text.strip()
    text = re.sub(
        r"(?<=[A-Za-z)])\s*[1-9](?:\s*[,/&»]\s*[1-9])?/?"
        r"(?=\s*(?:\((?:SA|NSA)\)|by\b|$))",
        "",
        text,
        flags=re.I,
    )
    text = re.sub(
        r"(?<=[A-Za-z)])\s*[\^*!?'\"|’®]+\s*(?=\((?:SA|NSA)\))",
        " ",
        text,
        flags=re.I,
    )
    text = re.sub(
        r"\s*(?:[\^*!?'\"|’®]+|[1-9]+[A-Za-z]?[\./]?)\s*$",
        "",
        text,
    )
    return text.strip()


def release_date_from_name(path):
    match = re.search(r"(19\d{2})[-_]?(\d{2})[-_]?(\d{2})", path.name)
    if not match:
        raise ValueError(f"No release date in filename: {path.name}")
    return date(*map(int, match.groups()))


def load_eras():
    rows = []
    with ERA_MAP_PATH.open(newline="", encoding="utf-8-sig") as handle:
        for row in csv.DictReader(handle):
            rows.append(
                {
                    "id": int(row["Era"]),
                    "first": date.fromisoformat(row["First"]),
                    "last": date.fromisoformat(row["Last"]),
                    "description": row.get("description", ""),
                }
            )
    return rows


ERAS = load_eras()


def era_for(release_date):
    for era in ERAS:
        if era["first"] <= release_date <= era["last"]:
            return era["id"]
    return None


def expected_row_range(era_id, release_date):
    if era_id >= 5 or (
        era_id == 4 and release_date >= date(1987, 11, 20)
    ):
        return (14, 14)
    return (13, 13)


def sha1_file(path):
    digest = hashlib.sha1()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()[:16]


def estimate_deskew(image):
    probe = image.copy()
    probe.thumbnail((1000, 1400))
    scores = {}
    for angle in np.arange(-1.25, 1.26, 0.25):
        rotated = probe.rotate(float(angle), resample=Image.Resampling.BILINEAR, fillcolor=255)
        ink = np.asarray(rotated) < 150
        projection = ink.sum(axis=1)
        scores[float(angle)] = float(np.sort(projection)[-20:].sum())
    best = max(scores, key=scores.get)
    baseline = scores.get(0.0, 1.0)
    return best if abs(best) >= 0.4 and scores[best] > baseline * 1.025 else 0.0


def preprocess(source, destination):
    image = Image.open(source).convert("L")
    image = ImageOps.autocontrast(image, cutoff=1)
    image = image.filter(ImageFilter.MedianFilter(3))
    angle = estimate_deskew(image)
    if angle:
        image = image.rotate(angle, resample=Image.Resampling.BICUBIC, fillcolor=255)
    image = ImageEnhance.Contrast(image).enhance(1.25)
    image.save(destination)
    return image, angle


def parse_tsv(text):
    words = []
    for row in csv.DictReader(text.splitlines(), delimiter="\t"):
        raw = (row.get("text") or "").strip()
        if not raw:
            continue
        try:
            confidence = float(row.get("conf", -1))
            x, y, width, height = (
                int(row["left"]),
                int(row["top"]),
                int(row["width"]),
                int(row["height"]),
            )
        except (ValueError, KeyError):
            continue
        words.append(
            {
                "text": raw,
                "confidence": confidence,
                "bbox": [x, y, x + width, y + height],
                "block": int(row.get("block_num", 0)),
                "paragraph": int(row.get("par_num", 0)),
                "line": int(row.get("line_num", 0)),
            }
        )
    return words


def line_records(words, x_range=None, y_range=None):
    grouped = defaultdict(list)
    for word in words:
        x1, y1, x2, y2 = word["bbox"]
        cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
        if x_range and not (x_range[0] <= cx <= x_range[1]):
            continue
        if y_range and not (y_range[0] <= cy <= y_range[1]):
            continue
        grouped[(word["block"], word["paragraph"], word["line"])].append(word)
    lines = []
    for grouped_words in grouped.values():
        grouped_words.sort(key=lambda item: item["bbox"][0])
        text_parts = []
        for item in grouped_words:
            if text_parts and item.get("join_left"):
                text_parts[-1] += item["text"]
            else:
                text_parts.append(item["text"])
        lines.append(
            {
                "text": " ".join(text_parts),
                "confidence": statistics.mean(
                    max(0.0, item["confidence"]) for item in grouped_words
                ),
                "bbox": [
                    min(item["bbox"][0] for item in grouped_words),
                    min(item["bbox"][1] for item in grouped_words),
                    max(item["bbox"][2] for item in grouped_words),
                    max(item["bbox"][3] for item in grouped_words),
                ],
                "words": grouped_words,
            }
        )
    return sorted(lines, key=lambda item: (item["bbox"][1], item["bbox"][0]))


def embedded_ocr(pdf_path, cache_path):
    if cache_path.exists():
        try:
            return json.loads(cache_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            cache_path.unlink(missing_ok=True)
    completed = subprocess.run(
        [PDFTOTEXT, "-bbox-layout", str(pdf_path), "-"],
        check=True,
        capture_output=True,
        text=True,
    )
    root = ElementTree.fromstring(completed.stdout)
    pages = []
    for page_element in root.findall(".//{*}page"):
        page_width = float(page_element.attrib["width"])
        page_height = float(page_element.attrib["height"])
        words = []
        for block_number, block in enumerate(page_element.findall(".//{*}block"), 1):
            for line_number, line in enumerate(block.findall("./{*}line"), 1):
                previous_right = None
                for word_element in line.findall("./{*}word"):
                    raw = "".join(word_element.itertext()).strip()
                    if not raw:
                        continue
                    x1 = float(word_element.attrib["xMin"])
                    y1 = float(word_element.attrib["yMin"])
                    x2 = float(word_element.attrib["xMax"])
                    y2 = float(word_element.attrib["yMax"])
                    gap = x1 - previous_right if previous_right is not None else None
                    words.append(
                        {
                            "text": raw,
                            "confidence": 0.0,
                            "bbox": [x1, y1, x2, y2],
                            "block": block_number,
                            "paragraph": 0,
                            "line": line_number,
                            "join_left": gap is not None and gap <= 1.8,
                        }
                    )
                    previous_right = x2
        pages.append(
            {
                "width": page_width,
                "height": page_height,
                "words": words,
                "raw_text": "\n".join(
                    line["text"] for line in line_records(words)
                ),
            }
        )
    cache_path.write_text(json.dumps(pages), encoding="utf-8")
    return pages


def scale_embedded_page(page, width, height):
    scale_x = width / page["width"]
    scale_y = height / page["height"]
    words = []
    for word in page["words"]:
        x1, y1, x2, y2 = word["bbox"]
        scaled = dict(word)
        scaled["bbox"] = [
            x1 * scale_x,
            y1 * scale_y,
            x2 * scale_x,
            y2 * scale_y,
        ]
        words.append(scaled)
    return {
        "words": words,
        "raw_text": "\n".join(line["text"] for line in line_records(words)),
    }


def ocr_page(image_path, cache_path, psm):
    if cache_path.exists():
        try:
            return json.loads(cache_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            cache_path.unlink(missing_ok=True)
    completed = subprocess.run(
        [TESSERACT, str(image_path), "stdout", "--psm", str(psm), "tsv"],
        check=True,
        capture_output=True,
        text=True,
    )
    words = parse_tsv(completed.stdout)
    lines = line_records(words)
    page = {
        "raw_text": "\n".join(line["text"] for line in lines),
        "words": words,
        "mean_confidence": round(
            statistics.mean(max(0.0, word["confidence"]) for word in words), 2
        )
        if words
        else 0.0,
    }
    cache_path.write_text(json.dumps(page), encoding="utf-8")
    return page


def render_and_ocr(pdf_path):
    pdf_sha = sha1_file(pdf_path)
    cache = CACHE_DIR / OCR_CACHE_VERSION / pdf_sha
    cache.mkdir(parents=True, exist_ok=True)
    embedded_pages = embedded_ocr(pdf_path, cache / "embedded.json")
    rendered = sorted(cache.glob("render-*.png"))
    if rendered:
        try:
            for rendered_path in rendered:
                with Image.open(rendered_path) as candidate:
                    candidate.verify()
        except (OSError, SyntaxError):
            for rendered_path in rendered:
                rendered_path.unlink(missing_ok=True)
            rendered = []
    if not rendered:
        subprocess.run(
            [
                PDFTOPPM,
                "-r",
                str(RENDER_DPI),
                "-gray",
                "-png",
                str(pdf_path),
                str(cache / "render"),
            ],
            check=True,
            capture_output=True,
        )
        rendered = sorted(cache.glob("render-*.png"))
    pages = []
    for page_number, rendered_path in enumerate(rendered, 1):
        processed_path = cache / f"processed-{page_number:03d}.png"
        angle_path = cache / f"processed-{page_number:03d}.angle"
        if processed_path.exists():
            try:
                image = Image.open(processed_path).convert("L")
                image.load()
                angle = (
                    float(angle_path.read_text())
                    if angle_path.exists()
                    else 0.0
                )
            except (OSError, SyntaxError, ValueError):
                processed_path.unlink(missing_ok=True)
                angle_path.unlink(missing_ok=True)
                image, angle = preprocess(rendered_path, processed_path)
                angle_path.write_text(str(angle))
        else:
            image, angle = preprocess(rendered_path, processed_path)
            angle_path.write_text(str(angle))
        page = ocr_page(
            processed_path, cache / f"ocr-{page_number:03d}.json", psm=6
        )
        sparse_page = ocr_page(
            processed_path,
            cache / f"ocr-sparse-{page_number:03d}.json",
            psm=11,
        )
        embedded_page = (
            scale_embedded_page(
                embedded_pages[page_number - 1], image.width, image.height
            )
            if page_number <= len(embedded_pages)
            else {"words": [], "raw_text": ""}
        )
        page.update(
            {
                "page_number": page_number,
                "pdf_path": project_relative_path(pdf_path),
                "pdf_sha": pdf_sha,
                "cache_dir": project_relative_path(cache),
                "source_rendered_image": project_relative_path(rendered_path),
                "processed_image": project_relative_path(processed_path),
                "width": image.width,
                "height": image.height,
                "deskew_angle": angle,
                "sparse_words": sparse_page["words"],
                "sparse_raw_text": sparse_page["raw_text"],
                "embedded_words": embedded_page["words"],
                "embedded_raw_text": embedded_page["raw_text"],
            }
        )
        pages.append(page)
    return pages


def true_high_resolution_page(page, dpi=TRUE_HIGH_RESOLUTION_DPI):
    cache_dir = Path(page["cache_dir"])
    page_number = int(page["page_number"])
    processed_path = (
        cache_dir / f"true-highres-{dpi}-processed-{page_number:03d}.png"
    )
    angle_path = (
        cache_dir / f"true-highres-{dpi}-processed-{page_number:03d}.angle"
    )
    if processed_path.exists():
        try:
            image = Image.open(processed_path).convert("L")
            image.load()
            angle = (
                float(angle_path.read_text(encoding="utf-8"))
                if angle_path.exists()
                else 0.0
            )
            return image, processed_path, angle
        except (OSError, SyntaxError, ValueError):
            processed_path.unlink(missing_ok=True)
            angle_path.unlink(missing_ok=True)
    prefix = cache_dir / f"true-highres-{dpi}-raw-{page_number:03d}"
    raw_path = prefix.with_suffix(".png")
    subprocess.run(
        [
            PDFTOPPM,
            "-f",
            str(page_number),
            "-l",
            str(page_number),
            "-singlefile",
            "-r",
            str(dpi),
            "-gray",
            "-png",
            page["pdf_path"],
            str(prefix),
        ],
        check=True,
        capture_output=True,
    )
    try:
        image, angle = preprocess(raw_path, processed_path)
        angle_path.write_text(str(angle), encoding="utf-8")
    finally:
        raw_path.unlink(missing_ok=True)
    return image, processed_path, angle


def similarity(left, right):
    left_normalized, right_normalized = normalized(left), normalized(right)
    if not left_normalized or not right_normalized:
        return 0.0
    shorter, longer = sorted(
        (left_normalized, right_normalized), key=len
    )
    if shorter in longer and len(shorter) / len(longer) >= 0.65:
        return 1.0
    return difflib.SequenceMatcher(None, left_normalized, right_normalized).ratio()


def best_line(lines, targets, minimum=0.48):
    choices = []
    for line in lines:
        line_normalized = normalized(line["text"])
        line_tokens = {token for token in line_normalized.split() if len(token) >= 2}
        line_compact = line_normalized.replace(" ", "")
        scores = []
        for target in targets:
            target_normalized = normalized(target)
            target_tokens = {
                token for token in target_normalized.split() if len(token) >= 2
            }
            target_compact = target_normalized.replace(" ", "")
            matched_terms = sum(
                any(
                    token in line_compact
                    or difflib.SequenceMatcher(None, token, line_token).ratio() >= 0.76
                    for line_token in line_tokens
                )
                for token in target_tokens
            )
            coverage = matched_terms / len(target_tokens) if target_tokens else 0.0
            length_ratio = (
                min(len(line_compact), len(target_compact))
                / max(len(line_compact), len(target_compact))
                if line_compact and target_compact
                else 0.0
            )
            sequence_score = difflib.SequenceMatcher(
                None, line_normalized, target_normalized
            ).ratio()
            if target_compact in line_compact:
                scores.append(1.0)
            elif (
                matched_terms >= min(2, len(target_tokens))
                or (length_ratio >= 0.65 and sequence_score >= 0.72)
            ):
                scores.append(max(coverage, sequence_score))
            else:
                scores.append(0.0)
        score = max(scores)
        choices.append((score, line))
    if not choices:
        return None
    score, line = max(choices, key=lambda item: item[0])
    return line if score >= minimum else None


def page_text(page, top_fraction=None):
    parts = []
    for word_key in ("words", "sparse_words", "embedded_words"):
        words = page.get(word_key, [])
        if top_fraction is not None:
            words = [
                word
                for word in words
                if (word["bbox"][1] + word["bbox"][3]) / 2
                <= page["height"] * top_fraction
            ]
        parts.extend(line["text"] for line in line_records(words))
    return "\n".join(parts)


def page_adjustment(page):
    text = normalized(page_text(page, 0.34))
    if re.search(r"\bnot\s+season\w*\s*adjust\w*", text):
        return "NSA"
    if re.search(r"\bseason\w*\s*adjust\w*", text):
        return "SA"
    header_words = ocr_region(
        page,
        0,
        page["height"] * 0.08,
        page["width"],
        page["height"] * 0.30,
        psm=6,
        purpose="page-adjustment",
        border=0,
    )
    text = normalized(" ".join(word["text"] for word in header_words))
    if re.search(r"\bnot\s+season\w*\s*adjust\w*", text):
        return "NSA"
    if re.search(r"\bseason\w*\s*adjust\w*", text):
        return "SA"
    return "unknown"


def printed_release_date(page):
    pattern = (
        r"\b(" + "|".join(MONTHS) + r")\s+(\d{1,2})\s*,?\s*(19\d{2})\b"
    )
    raw_text = page_text(page, 0.34)
    matches = list(re.finditer(pattern, raw_text.lower()))
    if not matches:
        return None
    month_name, day_value, year_value = matches[-1].groups()
    return date(int(year_value), MONTHS[month_name], int(day_value))


def page_header_fields(page):
    lines = []
    for word_key, source in (
        ("words", "rendered_ocr"),
        ("sparse_words", "rendered_sparse_ocr"),
        ("embedded_words", "embedded_locator"),
    ):
        for line in line_records(
            page.get(word_key, []),
            y_range=(0, page["height"] * 0.34),
        ):
            if (
                len(line["text"]) <= 220
                and line["text"].count("\t") < 3
                and len(re.findall(r"\b\d+\b", line["text"])) < 12
            ):
                lines.append({**line, "source": source})
    raw = "\n".join(line["text"] for line in lines)
    compact = normalized(raw)
    code_numbers = [
        int(match.group(1))
        for match in re.finditer(
            r"\bG\s*[\.\-]?\s*(\d{1,2})(?=\s*(?:\(|\b))",
            raw,
            flags=re.I,
        )
    ]
    if "major nondeposit funds" in compact:
        code_numbers.append(10)
    if "debits and deposit turnover" in compact and not code_numbers:
        code_numbers.append(6)
    printed_code = ""
    if code_numbers:
        selected = 10 if 10 in code_numbers else Counter(code_numbers).most_common(1)[0][0]
        printed_code = f"G.{selected}"
    title_targets = (
        "Debits and Deposit Turnover at Commercial Banks",
        "Debits and Deposit Turnover",
        "Major Nondeposit Funds of Commercial Banks",
    )
    title_line = best_line(lines, title_targets, minimum=0.48)
    printed_title = remove_footnote_marker(title_line["text"]) if title_line else ""
    incompatible_title = "major nondeposit funds" in normalized(printed_title or raw)
    g6_title_present = (
        "debits and deposit turnover at commercial banks" in compact
        or similarity(
            printed_title,
            "Debits and Deposit Turnover at Commercial Banks",
        )
        >= 0.82
    )
    if g6_title_present and 10 not in code_numbers:
        printed_code = "G.6"
    conflicting_code = bool(printed_code and printed_code != "G.6")
    return {
        "printed_release_code": printed_code,
        "printed_release_title": printed_title,
        "printed_release_date": (
            printed_release_date(page).isoformat()
            if printed_release_date(page)
            else ""
        ),
        "conflicting_release": conflicting_code or incompatible_title,
    }


TITLE_KEYWORDS = {
    "Debits During the Month": {"debits", "during", "month"},
    "Average Deposits Outstanding": {"average", "deposits", "outstanding"},
    "Annual Rate of Deposit Turnover": {
        "annual",
        "rate",
        "deposit",
        "turnover",
    },
}


def title_candidates(words, page_height):
    lines = line_records(words)
    candidates = list(lines)
    for first, second in zip(lines, lines[1:]):
        vertical_gap = second["bbox"][1] - first["bbox"][3]
        if vertical_gap > page_height * 0.025:
            continue
        candidates.append(
            {
                "text": f"{first['text']} {second['text']}".strip(),
                "confidence": statistics.mean(
                    [first["confidence"], second["confidence"]]
                ),
                "bbox": [
                    min(first["bbox"][0], second["bbox"][0]),
                    min(first["bbox"][1], second["bbox"][1]),
                    max(first["bbox"][2], second["bbox"][2]),
                    max(first["bbox"][3], second["bbox"][3]),
                ],
                "words": first["words"] + second["words"],
            }
        )
    return candidates


def title_score(text, target):
    text_normalized = normalized(text)
    token_list = text_normalized.split()
    tokens = set(token_list)
    token_fragments = list(token_list) + [
        first + second for first, second in zip(token_list, token_list[1:])
    ]
    compact = text_normalized.replace(" ", "")
    keywords = TITLE_KEYWORDS[target]
    present = {
        keyword
        for keyword in keywords
        if keyword in tokens
        or (
            keyword != "month"
            and any(
                difflib.SequenceMatcher(None, token, keyword).ratio()
                >= (
                    0.64
                    if target == "Annual Rate of Deposit Turnover"
                    else 0.72
                )
                for token in token_fragments
            )
        )
    }
    if (
        target == "Debits During the Month"
        and {"during", "month"} <= tokens
        and any(
            difflib.SequenceMatcher(None, token, "debits").ratio() >= 0.50
            for token in token_list
            if 4 <= len(token) <= 8
        )
    ):
        present.add("debits")
    target_compact = normalized(target).replace(" ", "")
    if target_compact in compact:
        present = set(keywords)
    if target == "Debits During the Month" and not {"debits", "month"} <= present:
        return 0.0
    if target == "Average Deposits Outstanding" and not (
        {"average", "outstanding"} <= present
    ):
        return 0.0
    if target == "Annual Rate of Deposit Turnover" and not (
        {"annual", "turnover"} <= present
        and ({"rate", "deposit"} & present)
    ):
        return 0.0
    if len(text_normalized) > 220:
        return 0.0
    return len(present) / len(keywords)


def compact_title_similarity(text, target):
    text_tokens = re.findall(r"[a-z]+", text.lower())
    target_compact = re.sub(r"[^a-z]", "", target.lower())
    variants = ["".join(text_tokens)]
    for token_count in range(2, min(len(text_tokens), 6) + 1):
        variants.extend(
            "".join(text_tokens[start : start + token_count])
            for start in range(len(text_tokens) - token_count + 1)
        )
    return max(
        (
            difflib.SequenceMatcher(None, variant, target_compact).ratio()
            for variant in variants
            if 8 <= len(variant) <= 60
        ),
        default=0.0,
    )


def title_from_words(words, target, page_height, source):
    scored = []
    for candidate in title_candidates(words, page_height):
        score = (
            0.0
            if (
                target == "Annual Rate of Deposit Turnover"
                and (
                    candidate["bbox"][1] > page_height * 0.80
                    or len(candidate["text"]) > 120
                )
            )
            else title_score(candidate["text"], target)
        )
        if (
            target == "Annual Rate of Deposit Turnover"
            and page_height * 0.45
            < candidate["bbox"][1]
            < page_height * 0.80
            and len(candidate["text"]) <= 120
        ):
            similarity = compact_title_similarity(candidate["text"], target)
            token_fragments = []
            for token in normalized(candidate["text"]).split():
                token_fragments.append(token)
                token_fragments.extend(
                    token[index:]
                    for index, character in enumerate(token)
                    if character == "t" and len(token) - index >= 4
                )
            turnover_similarity = max(
                (
                    difflib.SequenceMatcher(None, token, "turnover").ratio()
                    for token in token_fragments
                    if token.startswith("t")
                ),
                default=0.0,
            )
            if similarity >= 0.45 and turnover_similarity >= 0.40:
                score = max(score, similarity)
        scored.append((score, candidate))
    scored = [item for item in scored if item[0] > 0]
    if not scored:
        return None
    _, match = max(
        scored,
        key=lambda item: (item[0], -len(item[1]["text"]), -item[1]["bbox"][1]),
    )
    match = dict(match)
    match["source"] = source
    return match


def ocr_region(page, x1, y1, x2, y2, psm, purpose, border=12):
    image = Image.open(page["processed_image"]).convert("L")
    left = max(0, int(x1))
    top = max(0, int(y1))
    right = min(image.width, int(x2))
    bottom = min(image.height, int(y2))
    if right <= left or bottom <= top:
        return []
    cache_key = hashlib.sha1(
        f"{left}:{top}:{right}:{bottom}:{psm}:{purpose}:{border}".encode()
    ).hexdigest()[:14]
    cache_dir = Path(page["processed_image"]).parent
    crop_path = cache_dir / f"region-{cache_key}.png"
    cache_path = cache_dir / f"region-{cache_key}.json"
    if not crop_path.exists():
        crop = image.crop((left, top, right, bottom))
        (
            ImageOps.expand(crop, border=border, fill=255)
            if border
            else crop
        ).save(crop_path)
    region = ocr_page(crop_path, cache_path, psm=psm)
    words = []
    for word in region["words"]:
        local_x1, local_y1, local_x2, local_y2 = word["bbox"]
        translated = dict(word)
        translated["bbox"] = [
            local_x1 + left - border,
            local_y1 + top - border,
            local_x2 + left - border,
            local_y2 + top - border,
        ]
        words.append(translated)
    return words


def recover_missing_titles(page, found):
    present = {target for target, _ in found}
    known = {
        TABLE_TARGETS.index(target): line["bbox"][1] for target, line in found
    }
    if len(known) < 2:
        return found
    recovered = list(found)
    for target in TABLE_TARGETS:
        if target in present:
            continue
        target_index = TABLE_TARGETS.index(target)
        lower = [(index, y) for index, y in known.items() if index < target_index]
        upper = [(index, y) for index, y in known.items() if index > target_index]
        if lower and upper:
            lower_index, lower_y = max(lower)
            upper_index, upper_y = min(upper)
            expected_y = lower_y + (
                (upper_y - lower_y)
                * (target_index - lower_index)
                / (upper_index - lower_index)
            )
        else:
            ordered = sorted(known.items())
            spacing = (ordered[-1][1] - ordered[0][1]) / (
                ordered[-1][0] - ordered[0][0]
            )
            anchor_index, anchor_y = min(
                ordered, key=lambda item: abs(item[0] - target_index)
            )
            expected_y = anchor_y + spacing * (target_index - anchor_index)
        matches = []
        weak_matches = []
        for offset in (-30, 0, 30):
            for psm in (7, 11):
                words = ocr_region(
                    page,
                    page["width"] * 0.05,
                    expected_y + offset - 38,
                    page["width"] * 0.95,
                    expected_y + offset + 42,
                    psm=psm,
                    purpose=f"title-{target_index}",
                    border=0,
                )
                match = title_from_words(
                    words, target, page["height"], "rendered_region_ocr"
                )
                if match:
                    matches.append(match)
                for line in line_records(words):
                    similarity = compact_title_similarity(line["text"], target)
                    if similarity >= 0.32:
                        weak_line = dict(line)
                        weak_line["source"] = "spatial_title_inference"
                        weak_matches.append((similarity, weak_line))
        if matches:
            recovered.append(
                (
                    target,
                    min(
                        matches,
                        key=lambda item: abs(item["bbox"][1] - expected_y),
                    ),
                )
            )
        elif weak_matches:
            _, match = max(
                weak_matches,
                key=lambda item: (
                    -abs(item[1]["bbox"][1] - expected_y),
                    item[0],
                    item[1]["confidence"],
                ),
            )
            recovered.append((target, match))
    return recovered


def scan_missing_titles(page, found):
    if not found or len(found) == len(TABLE_TARGETS):
        return found
    recovered = list(found)
    present = {target for target, _ in recovered}
    known_y = [line["bbox"][1] for _, line in recovered]
    half_height = max(35, int(page["height"] * 0.018))
    step = max(40, int(page["height"] * 0.025))
    candidates = defaultdict(list)
    for center_y in range(
        int(page["height"] * 0.20),
        int(page["height"] * 0.78),
        step,
    ):
        if any(abs(center_y - y) < step for y in known_y):
            continue
        words = ocr_region(
            page,
            page["width"] * 0.10,
            center_y - half_height,
            page["width"] * 0.96,
            center_y + half_height,
            psm=7,
            purpose=f"title-scan-{center_y}",
            border=0,
        )
        for target in TABLE_TARGETS:
            if target in present:
                continue
            match = title_from_words(
                words,
                target,
                page["height"],
                "rendered_region_ocr",
            )
            if match:
                candidates[target].append(
                    (title_score(match["text"], target), match)
                )
    for target, matches in candidates.items():
        _, match = max(
            matches,
            key=lambda item: (
                item[0],
                item[1]["confidence"],
                -len(item[1]["text"]),
            ),
        )
        recovered.append((target, match))
    return recovered


def title_matches_from_words(words, target, page_height, source):
    matches = []
    for candidate in title_candidates(words, page_height):
        score = title_score(candidate["text"], target)
        if score < 0.72:
            continue
        if (
            target == "Annual Rate of Deposit Turnover"
            and candidate["bbox"][1] > page_height * 0.80
        ):
            continue
        matches.append({**candidate, "source": source, "title_score": score})
    return matches


def table_title_lines(page):
    found = []
    for target in TABLE_TARGETS:
        matches = []
        for word_key, source in (
            ("words", "rendered_ocr"),
            ("sparse_words", "rendered_sparse_ocr"),
            ("embedded_words", "embedded_locator"),
        ):
            matches.extend(
                title_matches_from_words(
                    page.get(word_key, []),
                    target,
                    page["height"],
                    source,
                )
            )
        clusters = []
        for match in sorted(matches, key=lambda item: item["bbox"][1]):
            if (
                not clusters
                or match["bbox"][1] - clusters[-1][-1]["bbox"][1]
                > page["height"] * 0.035
            ):
                clusters.append([match])
            else:
                clusters[-1].append(match)
        if not clusters:
            continue
        cluster = max(
            clusters,
            key=lambda items: (
                len({item["source"] for item in items}),
                max(item["title_score"] for item in items),
                -abs(
                    statistics.mean(item["bbox"][1] for item in items)
                    - page["height"]
                    * (0.20 + TABLE_TARGETS.index(target) * 0.20)
                ),
            ),
        )
        rendered = [
            item for item in cluster if item["source"] != "embedded_locator"
        ]
        anchor_pool = rendered or cluster
        anchor = max(
            anchor_pool,
            key=lambda item: (
                item["bbox"][1],
                item["title_score"],
                item["confidence"],
            ),
        )
        anchor = dict(anchor)
        anchor["alternatives"] = [
            {
                "text": item["text"],
                "bbox": item["bbox"],
                "source": item["source"],
                "score": round(item["title_score"], 4),
            }
            for item in cluster
            if item is not anchor
        ]
        found.append((target, anchor))
    if len(found) >= 2:
        found = recover_missing_titles(page, found)
    elif found and page_has_repeated_table_geometry(page):
        found = scan_missing_titles(page, found)
        present = {target for target, _ in found}
        if len(present) < 3:
            anchor_target, anchor_line = found[0]
            anchor_index = TABLE_TARGETS.index(anchor_target)
            for target in TABLE_TARGETS:
                if target in present:
                    continue
                target_index = TABLE_TARGETS.index(target)
                expected_y = (
                    anchor_line["bbox"][1]
                    + (target_index - anchor_index)
                    * page["height"]
                    * 0.19
                )
                region_words = ocr_region(
                    page,
                    page["width"] * 0.10,
                    expected_y - page["height"] * 0.025,
                    page["width"] * 0.96,
                    expected_y + page["height"] * 0.030,
                    psm=7,
                    purpose=f"geometry-backed-title-{target_index}",
                    border=0,
                )
                region_lines = line_records(region_words)
                nearest = min(
                    region_lines,
                    key=lambda line: abs(line["bbox"][1] - expected_y),
                    default={
                        "text": "",
                        "confidence": 0.0,
                        "bbox": [
                            page["width"] * 0.25,
                            expected_y,
                            page["width"] * 0.75,
                            expected_y + page["height"] * 0.012,
                        ],
                        "words": [],
                    },
                )
                found.append(
                    (
                        target,
                        {
                            **nearest,
                            "source": "spatial_title_inference",
                            "title_score": 0.72,
                            "alternatives": [],
                        },
                    )
                )
    found.sort(key=lambda item: item[1]["bbox"][1])
    semantic = {}
    for target, line in found:
        current = semantic.get(target)
        if current is None or line["bbox"][1] > current["bbox"][1]:
            semantic[target] = line
    return sorted(
        semantic.items(),
        key=lambda item: item[1]["bbox"][1],
    )


def page_has_repeated_table_geometry(page):
    image = np.asarray(
        Image.open(page["processed_image"]).convert("L")
    )
    y1 = int(page["height"] * 0.12)
    y2 = int(page["height"] * 0.80)
    dark = image[y1:y2] < 165
    if not dark.size:
        return False
    horizontal = dark.mean(axis=1) > 0.28
    bands = [
        (start, end)
        for start, end in runs(horizontal)
        if end - start <= max(10, page["height"] * 0.006)
    ]
    return len(bands) >= 6


def month_from_text(text):
    raw_tokens = re.findall(r"[A-Za-z0-9]+", text)
    tokens = [
        re.sub(r"[^a-z]", "", token.lower())
        for token in raw_tokens
    ]
    tokens.extend(
        (left + right).lower()
        for left, right in zip(raw_tokens, raw_tokens[1:])
        if left.isalpha() and right.isalpha()
    )
    prefix_choices = []
    for name, number in MONTHS.items():
        for token in tokens:
            if token.startswith(name[:3]):
                prefix_choices.append(
                    (
                        difflib.SequenceMatcher(None, token, name).ratio(),
                        number,
                        name,
                    )
                )
    if prefix_choices:
        score, number, name = max(prefix_choices)
        if score >= 0.68:
            return number, name
    choices = []
    for name, number in MONTHS.items():
        for token in tokens:
            if len(token) < 3:
                continue
            score = difflib.SequenceMatcher(None, token, name).ratio()
            if token[:1] == name[:1]:
                score += 0.08
            choices.append((score, number, name))
    if choices:
        score, number, name = max(choices)
        if score >= 0.68:
            return number, name
    return None, None


def date_label_details(text, release_date):
    month_number, month_name = month_from_text(text)
    year_candidates = []
    tokens = re.findall(r"[A-Za-z0-9]+", text)
    for token in tokens:
        exact_plausible_year = False
        if re.fullmatch(r"\d{4}", token):
            value = int(token)
            if 1960 <= value <= release_date.year + 1:
                exact_plausible_year = True
                year_candidates.append(
                    {
                        "year": value,
                        "raw": token,
                        "normalization": "exact_printed_year",
                        "weight": 4.0,
                    }
                )
            if (
                70 <= int(token[:2]) <= 99
                and 1 <= int(token[2:]) <= 12
            ):
                year_candidates.append(
                    {
                        "year": 1900 + int(token[:2]),
                        "raw": token,
                        "normalization": "yymm_row_code",
                        "weight": 3.5,
                    }
                )
                if month_number is None:
                    month_number = int(token[2:])
                    month_name = next(
                        name for name, number in MONTHS.items()
                        if number == month_number
                    )
        elif re.fullmatch(r"1[0-9A-Za-z]{3}", token):
            translated = token.lower().translate(
                str.maketrans({"b": "6", "o": "0", "i": "1", "l": "1", "s": "5"})
            )
            if translated.isdigit():
                value = int(translated)
                if 1960 <= value <= release_date.year + 1:
                    year_candidates.append(
                        {
                            "year": value,
                            "raw": token,
                            "normalization": "ocr_digit_substitution",
                            "weight": 3.0,
                        }
                    )
        if len(token) == 4 and not exact_plausible_year:
            for plausible in range(max(1960, release_date.year - 12), release_date.year + 2):
                if sum(left != right for left, right in zip(token.lower(), str(plausible))) == 1:
                    year_candidates.append(
                        {
                            "year": plausible,
                            "raw": token,
                            "normalization": "single_digit_year_repair",
                            "weight": 2.5,
                        }
                    )
    unique_years = {}
    for candidate in year_candidates:
        key = (candidate["year"], candidate["normalization"])
        if key not in unique_years or candidate["weight"] > unique_years[key]["weight"]:
            unique_years[key] = candidate
    annotation_tokens = re.findall(r"(?<![A-Za-z])[rRcC](?![A-Za-z])", text)
    return {
        "month": month_number,
        "month_name": month_name or "",
        "year_candidates": list(unique_years.values()),
        "annotation": " ".join(dict.fromkeys(annotation_tokens)),
    }


def date_rows_from_words(
    words,
    y_top,
    y_bottom,
    data_start,
    source,
    release_date,
):
    candidates = []
    for line in line_records(
        words, x_range=(0, data_start), y_range=(y_top, y_bottom)
    ):
        details = date_label_details(line["text"], release_date)
        month_number = details["month"]
        if month_number:
            month_word = next(
                (
                    word["text"]
                    for word in line["words"]
                    if month_from_text(word["text"])[0] == month_number
                ),
                details["month_name"],
            )
            month_token = re.sub(r"[^a-z]", "", month_word.lower())
            month_reliable = (
                month_token == details["month_name"]
                or (
                    len(month_token) >= 4
                    and difflib.SequenceMatcher(
                        None,
                        month_token,
                        details["month_name"],
                    ).ratio()
                    >= 0.68
                )
            )
            candidates.append(
                {
                    "y": (line["bbox"][1] + line["bbox"][3]) / 2,
                    "bbox": line["bbox"],
                    "raw": line["text"].strip(),
                    "month": month_number,
                    "month_raw": month_word,
                    "month_reliable": month_reliable,
                    "year_candidates": details["year_candidates"],
                    "annotation": details["annotation"],
                    "confidence": line["confidence"],
                    "source": source,
                }
            )
    candidates.sort(key=lambda item: item["y"])
    deduplicated = []
    for candidate in candidates:
        if not deduplicated or abs(candidate["y"] - deduplicated[-1]["y"]) > 10:
            deduplicated.append(candidate)
    return deduplicated


def spatial_value_rows(page, y_top, y_bottom, data_start, maximum_count):
    samples = []
    for word_key in ("sparse_words", "words", "embedded_words"):
        for word in page.get(word_key, []):
            x1, top, x2, bottom = word["bbox"]
            center_x = (x1 + x2) / 2
            center_y = (top + bottom) / 2
            if (
                center_x < data_start
                or not y_top <= center_y <= y_bottom
                or not re.search(r"\d", word["text"])
            ):
                continue
            samples.append((center_y, center_x))
    tolerance = max(10, page["height"] * 0.005)
    clusters = []
    for center_y, center_x in sorted(samples):
        if not clusters or center_y - clusters[-1]["y"] > tolerance:
            clusters.append(
                {"y": center_y, "count": 1, "x_bins": {round(center_x / 45)}}
            )
            continue
        cluster = clusters[-1]
        cluster["y"] = (
            cluster["y"] * cluster["count"] + center_y
        ) / (cluster["count"] + 1)
        cluster["count"] += 1
        cluster["x_bins"].add(round(center_x / 45))
    centers = [
        cluster["y"]
        for cluster in clusters
        if cluster["count"] >= 3 and len(cluster["x_bins"]) >= 2
    ]
    image = np.asarray(
        Image.open(page["processed_image"]).convert("L")
    )
    left = max(0, int(data_start))
    right = min(image.shape[1], int(page["width"] * 0.97))
    top = max(0, int(y_top))
    bottom = min(image.shape[0], int(y_bottom))
    if right > left and bottom > top:
        profile = (image[top:bottom, left:right] < 165).mean(axis=1)
        text_rows = (profile >= 0.004) & (profile <= 0.22)
        image_centers = [
            top + (start + end) / 2
            for start, end in runs(text_rows)
            if 2 <= end - start + 1 <= max(28, page["height"] * 0.014)
        ]
        existing_gaps = np.diff(sorted(centers))
        merge_distance = max(
            page["height"] * 0.004,
            (
                float(np.median(existing_gaps)) * 0.60
                if len(existing_gaps)
                else 0.0
            ),
        )
        for center_y in image_centers:
            if not any(
                abs(center_y - existing) <= merge_distance
                for existing in centers
            ):
                centers.append(center_y)
        centers.sort()
    if len(centers) >= 3:
        gaps = np.diff(centers)
        typical_gap = float(
            np.median(sorted(gaps)[: max(2, math.ceil(len(gaps) * 0.65))])
        )
        segments = [[]]
        for index, center in enumerate(centers):
            if (
                index
                and typical_gap
                and center - centers[index - 1] > typical_gap * 1.8
            ):
                segments.append([])
            segments[-1].append(center)
        centers = max(
            segments,
            key=lambda segment: (
                len(segment),
                -abs(len(segment) - maximum_count),
            ),
        )
    return [
        {
            "y": center_y,
            "bbox": [0, center_y, data_start, center_y],
            "raw": "",
            "month": None,
            "month_raw": "",
            "year_candidates": [],
            "source": "spatial_value_grid",
            "row_inserted": True,
        }
        for center_y in centers
    ]


def select_physical_row_centers(
    spatial_rows,
    label_candidates,
    minimum_count,
    maximum_count,
    page_height,
):
    numeric_centers = sorted(row["y"] for row in spatial_rows)
    if not numeric_centers:
        numeric_centers = sorted(
            {
                round(candidate["y"], 1)
                for candidate in label_candidates
            }
        )
    if not numeric_centers:
        return []
    choices = []
    for count in range(minimum_count, maximum_count + 1):
        if len(numeric_centers) < count:
            continue
        for start in range(len(numeric_centers) - count + 1):
            selected = numeric_centers[start : start + count]
            gaps = np.diff(selected)
            typical_gap = float(np.median(gaps)) if len(gaps) else 0.0
            dispersion = (
                float(np.median(np.abs(gaps - typical_gap))) / typical_gap
                if typical_gap
                else 1.0
            )
            assignment_distance = max(
                page_height * 0.005,
                typical_gap * 0.65,
            )
            assigned_labels = [[] for _ in selected]
            for label in label_candidates:
                nearest_index = min(
                    range(len(selected)),
                    key=lambda index: abs(selected[index] - label["y"]),
                )
                if (
                    abs(selected[nearest_index] - label["y"])
                    <= assignment_distance
                ):
                    assigned_labels[nearest_index].append(label)
            label_count = sum(bool(labels) for labels in assigned_labels)
            reliable_count = sum(
                any(label.get("month_reliable", True) for label in labels)
                for labels in assigned_labels
            )
            recognized = []
            for labels in assigned_labels:
                votes = Counter(
                    label["month"] for label in labels
                    if label.get("month")
                    and label.get("month_reliable", True)
                )
                recognized.append(
                    votes.most_common(1)[0][0] if votes else None
                )
            mismatch = min(
                (
                    sum(
                        month is not None
                        and month != (first_month - 1 + index) % 12 + 1
                        for index, month in enumerate(recognized)
                    )
                    for first_month in range(1, 13)
                ),
                default=count,
            )
            label_distances = [
                min(abs(center - label["y"]) for label in labels)
                for center, labels in zip(selected, assigned_labels)
                if labels
            ]
            distance_penalty = (
                statistics.mean(label_distances) / typical_gap
                if label_distances and typical_gap
                else 1.0
            )
            gap_variation = (
                float(np.std(gaps)) / typical_gap
                if len(gaps) and typical_gap
                else 1.0
            )
            first_year_anchor = any(
                label.get("year_candidates")
                for label in assigned_labels[0]
            )
            score = (
                label_count * 20.0
                + reliable_count * 2.0
                + first_year_anchor * 6.0
                - (count - label_count) * 5.0
                - mismatch * 25.0
                - dispersion * 30.0
                - gap_variation * 60.0
                - distance_penalty * 2.0
            )
            choices.append(
                (
                    score,
                    label_count,
                    reliable_count,
                    -dispersion,
                    -count,
                    selected,
                )
            )
    if not choices:
        return numeric_centers
    return max(choices, key=lambda item: item[:-1])[-1]


def ordered_month_cluster_mapping(
    cluster_months,
    cluster_centers,
    row_centers,
    fallback_first_month,
):
    recognized = [
        (index, month)
        for index, month in enumerate(cluster_months)
        if month is not None
    ]
    if not recognized or not row_centers:
        return {}, 0
    cluster_low, cluster_high = min(cluster_centers), max(cluster_centers)
    row_low, row_high = min(row_centers), max(row_centers)

    def normalized_position(value, low, high):
        return (value - low) / (high - low) if high != low else 0.5

    best_overall = None
    for first_month in range(1, 13):
        expected = [
            (first_month - 1 + index) % 12 + 1
            for index in range(len(row_centers))
        ]
        states = {-1: (0, 0.0, {})}
        for cluster_index, month in recognized:
            next_states = dict(states)
            cluster_position = normalized_position(
                cluster_centers[cluster_index],
                cluster_low,
                cluster_high,
            )
            for last_row, (matches, distance, mapping) in states.items():
                for row_index in range(last_row + 1, len(row_centers)):
                    if expected[row_index] != month:
                        continue
                    row_position = normalized_position(
                        row_centers[row_index],
                        row_low,
                        row_high,
                    )
                    candidate = (
                        matches + 1,
                        distance + abs(cluster_position - row_position),
                        {**mapping, cluster_index: row_index},
                    )
                    incumbent = next_states.get(row_index)
                    if (
                        incumbent is None
                        or (candidate[0], -candidate[1])
                        > (incumbent[0], -incumbent[1])
                    ):
                        next_states[row_index] = candidate
            states = next_states
        matches, distance, mapping = max(
            states.values(),
            key=lambda item: (item[0], -item[1]),
        )
        fallback_distance = min(
            (first_month - fallback_first_month) % 12,
            (fallback_first_month - first_month) % 12,
        )
        candidate = (
            matches,
            -fallback_distance,
            -distance,
            mapping,
        )
        if (
            best_overall is None
            or candidate[:3] > best_overall[:3]
        ):
            best_overall = candidate
    return best_overall[3], best_overall[0]


def resolve_sequence_years(rows, first_month, release_date, fallback_last_month):
    if not rows:
        return []
    earliest_year = max(1960, release_date.year - 12)
    preferred_last = date(
        release_date.year - (fallback_last_month > release_date.month),
        fallback_last_month,
        1,
    )
    candidates = []
    for start_year in range(earliest_year, release_date.year + 1):
        generated_year = start_year
        previous_month = first_month
        generated = []
        anchor_penalty = 0.0
        supporting_anchor_rows = 0
        for index, row in enumerate(rows):
            if index and row["month"] < previous_month:
                generated_year += 1
            generated.append(generated_year)
            previous_month = row["month"]
            options = [
                option
                for option in row["year_options"]
                if earliest_year <= option["year"] <= release_date.year + 1
            ]
            if any(
                option["year"] == generated_year
                and option.get("weight", 0) >= 2.5
                for option in options
            ):
                supporting_anchor_rows += 1
            by_source = defaultdict(list)
            for option in options:
                by_source[option.get("source", "unknown")].append(option)
            for source_options in by_source.values():
                if not any(
                    option["year"] == generated_year
                    for option in source_options
                ):
                    anchor_penalty += min(
                        option["weight"] for option in source_options
                    )
        last_date = date(generated[-1], rows[-1]["month"], 1)
        distance = abs(
            (last_date.year - preferred_last.year) * 12
            + last_date.month
            - preferred_last.month
        )
        candidates.append(
            (
                last_date > release_date,
                distance > MAX_UNCORROBORATED_YEAR_DISTANCE_MONTHS
                and supporting_anchor_rows < MIN_HISTORICAL_YEAR_ANCHOR_ROWS,
                anchor_penalty + distance * 0.02,
                distance,
                start_year,
                generated,
            )
        )
    return min(candidates, default=(False, False, 0, 0, 0, []))[-1]


def date_rows(
    page,
    y_top,
    y_bottom,
    label_end,
    numeric_start,
    release_date,
    expected_range,
):
    minimum_count, maximum_count = expected_range
    rendered = date_rows_from_words(
        page["words"],
        y_top,
        y_bottom,
        label_end,
        "rendered_ocr",
        release_date,
    )
    sparse = date_rows_from_words(
        page.get("sparse_words", []),
        y_top,
        y_bottom,
        label_end,
        "rendered_sparse_ocr",
        release_date,
    )
    embedded = date_rows_from_words(
        page.get("embedded_words", []),
        y_top,
        y_bottom,
        label_end,
        "embedded_locator",
        release_date,
    )
    candidates = list(rendered)
    merge_tolerance = max(12, page["height"] * 0.007)
    for candidate in sparse + embedded:
        nearby = [
            existing
            for existing in candidates
            if abs(candidate["y"] - existing["y"]) <= merge_tolerance
        ]
        if nearby:
            existing = min(
                nearby, key=lambda item: abs(candidate["y"] - item["y"])
            )
            existing.setdefault("alternatives", []).append(candidate)
        else:
            candidates.append(candidate)
    spatial = spatial_value_rows(
        page,
        y_top,
        y_bottom,
        numeric_start,
        maximum_count,
    )
    selected_centers = select_physical_row_centers(
        spatial,
        rendered + sparse + embedded,
        minimum_count,
        maximum_count,
        page["height"],
    )
    if selected_centers:
        spatial = [
            {
                "y": center_y,
                "bbox": [0, center_y, label_end, center_y],
                "raw": "",
                "month": None,
                "month_raw": "",
                "year_candidates": [],
                "source": "spatial_value_grid",
                "row_inserted": True,
            }
            for center_y in selected_centers
        ]
    if len(spatial) >= minimum_count - 1:
        spatial_gaps = [
            current["y"] - previous["y"]
            for previous, current in zip(spatial, spatial[1:])
        ]
        label_tolerance = min(
            merge_tolerance,
            (statistics.median(spatial_gaps) * 0.62)
            if spatial_gaps
            else merge_tolerance,
        )
        all_labels = rendered + sparse + embedded
        label_clusters = []
        cluster_tolerance = min(
            merge_tolerance,
            max(8.0, page["height"] * 0.0035),
        )
        for candidate in sorted(all_labels, key=lambda item: item["y"]):
            nearby_clusters = [
                cluster
                for cluster in label_clusters
                if abs(
                    candidate["y"]
                    - statistics.median(item["y"] for item in cluster)
                )
                <= cluster_tolerance
            ]
            if nearby_clusters:
                cluster = min(
                    nearby_clusters,
                    key=lambda item: abs(
                        candidate["y"]
                        - statistics.median(value["y"] for value in item)
                    ),
                )
                cluster.append(candidate)
            else:
                label_clusters.append([candidate])
        label_clusters.sort(
            key=lambda cluster: statistics.median(
                item["y"] for item in cluster
            )
        )
        label_centers = [
            statistics.median(item["y"] for item in cluster)
            for cluster in label_clusters
        ]
        cluster_months = []
        for cluster in label_clusters:
            votes = Counter(
                candidate["month"]
                for candidate in cluster
                if candidate.get("month")
                and candidate.get("month_reliable", True)
            )
            cluster_months.append(
                votes.most_common(1)[0][0] if votes else None
            )
        recognized_cluster_count = sum(
            month is not None for month in cluster_months
        )
        sequence_mismatch = min(
            (
                sum(
                    month is not None
                    and month
                    != (first_month - 1 + index) % 12 + 1
                    for index, month in enumerate(cluster_months)
                )
                for first_month in range(1, 13)
            ),
            default=len(label_clusters),
        )
        coherent_ordered_labels = (
            minimum_count <= len(label_clusters) <= maximum_count
            and recognized_cluster_count >= max(
                3,
                len(label_clusters) - 1,
            )
            and sequence_mismatch <= 1
        )
        if (
            coherent_ordered_labels
            and len(spatial) != len(label_clusters)
            and len(spatial) >= max(2, minimum_count - 1)
        ):
            numeric_centers = [row["y"] for row in spatial]
            if label_centers[-1] != label_centers[0]:
                scale = (
                    numeric_centers[-1] - numeric_centers[0]
                ) / (label_centers[-1] - label_centers[0])
                unified_centers = [
                    numeric_centers[0]
                    + (center - label_centers[0]) * scale
                    for center in label_centers
                ]
            else:
                unified_centers = label_centers
            spatial = [
                {
                    "y": center_y,
                    "bbox": [0, center_y, label_end, center_y],
                    "raw": "",
                    "month": None,
                    "month_raw": "",
                    "year_candidates": [],
                    "source": "unified_spatial_row_mapping",
                    "row_inserted": False,
                }
                for center_y in unified_centers
            ]
        typical_spatial_gap = (
            statistics.median(spatial_gaps)
            if spatial_gaps
            else merge_tolerance
        )
        label_offset = 0.0
        label_assignments = [[] for _ in spatial]
        if (
            coherent_ordered_labels
            and len(label_clusters) == len(spatial)
        ):
            label_assignments = [
                list(cluster) for cluster in label_clusters
            ]
        else:
            assignment_last_month = (
                release_date.month - 3
            ) % 12 + 1
            assignment_first_month = (
                assignment_last_month
                - max(0, len(spatial) - 1)
                - 1
            ) % 12 + 1
            sequence_mapping, sequence_matches = (
                ordered_month_cluster_mapping(
                    cluster_months,
                    label_centers,
                    [row["y"] for row in spatial],
                    assignment_first_month,
                )
            )
            use_sequence_mapping = (
                recognized_cluster_count >= 5
                and sequence_matches
                >= max(5, recognized_cluster_count - 1)
            )
            if use_sequence_mapping:
                for cluster_index, row_index in sequence_mapping.items():
                    label_assignments[row_index].extend(
                        label_clusters[cluster_index]
                    )
            else:
                for candidate in all_labels:
                    nearest_index = min(
                        range(len(spatial)),
                        key=lambda index: abs(
                            candidate["y"]
                            + label_offset
                            - spatial[index]["y"]
                        ),
                    )
                    if (
                        abs(
                            candidate["y"]
                            + label_offset
                            - spatial[nearest_index]["y"]
                        )
                        <= label_tolerance
                    ):
                        label_assignments[nearest_index].append(candidate)
        deduplicated = []
        for row_index, spatial_row in enumerate(spatial):
            matches = sorted(
                label_assignments[row_index],
                key=lambda item: (
                    abs(item["y"] - spatial_row["y"]),
                    {"rendered_ocr": 0, "rendered_sparse_ocr": 1, "embedded_locator": 2}.get(item["source"], 3),
                    -item.get("confidence", 0),
                ),
            )
            row = dict(spatial_row)
            row["label_candidates"] = matches
            if matches:
                row.update(
                    {
                        "raw": matches[0]["raw"],
                        "bbox": matches[0]["bbox"],
                        "month_raw": matches[0]["month_raw"],
                    }
                )
            deduplicated.append(row)
    else:
        candidates.sort(key=lambda item: item["y"])
        deduplicated = []
        for candidate in candidates:
            if (
                not deduplicated
                or abs(candidate["y"] - deduplicated[-1]["y"]) > merge_tolerance
            ):
                row = dict(candidate)
                row["label_candidates"] = [candidate]
                deduplicated.append(row)
            else:
                deduplicated[-1]["label_candidates"].append(candidate)
        segments = []
        for candidate in deduplicated:
            if (
                not segments
                or candidate["y"] - segments[-1][-1]["y"] > page["height"] * 0.04
            ):
                segments.append([candidate])
            else:
                segments[-1].append(candidate)
        deduplicated = max(segments, key=len, default=[])
    gaps = [
        current["y"] - previous["y"]
        for previous, current in zip(deduplicated, deduplicated[1:])
    ]
    typical_gap = None
    if gaps:
        lower_gaps = sorted(gaps)[: max(2, math.ceil(len(gaps) * 0.6))]
        typical_gap = statistics.median(lower_gaps)
        expanded = [deduplicated[0]]
        remaining_inserts = max(0, maximum_count - len(deduplicated))
        for candidate in deduplicated[1:]:
            gap = candidate["y"] - expanded[-1]["y"]
            missing = (
                max(0, round(gap / typical_gap) - 1)
                if typical_gap and gap > typical_gap * 1.55
                else 0
            )
            missing = min(missing, remaining_inserts)
            remaining_inserts -= missing
            for offset in range(1, missing + 1):
                expanded.append(
                    {
                        "y": expanded[-1]["y"] + gap / (missing + 1),
                        "bbox": [0, 0, label_end, 0],
                        "raw": "",
                        "month": None,
                        "month_raw": "",
                        "year_candidates": [],
                        "source": "spatial_inference",
                        "row_inserted": True,
                        "label_candidates": [],
                    }
                )
            expanded.append(candidate)
        deduplicated = expanded
    if len(deduplicated) > maximum_count:
        deduplicated = deduplicated[:maximum_count]
    source_weights = {
        "rendered_ocr": 3.0,
        "rendered_sparse_ocr": 2.2,
        "embedded_locator": 1.2,
    }
    for row in deduplicated:
        month_votes = defaultdict(float)
        year_options = []
        annotations = []
        raw_candidates = []
        for candidate in row.get("label_candidates", []):
            weight = source_weights.get(candidate["source"], 1.0)
            weight *= max(0.4, min(1.0, candidate.get("confidence", 70) / 70))
            if not candidate.get("month_reliable", True):
                weight *= 0.30
            month_votes[candidate["month"]] += weight
            for year_candidate in candidate.get("year_candidates", []):
                year_options.append(
                    {
                        **year_candidate,
                        "weight": year_candidate["weight"] * weight,
                        "source": candidate["source"],
                    }
                )
            if candidate.get("annotation"):
                annotations.append(candidate["annotation"])
            raw_candidates.append(
                {
                    "raw": candidate["raw"],
                    "month": candidate["month"],
                    "year_candidates": candidate.get("year_candidates", []),
                    "source": candidate["source"],
                    "confidence": candidate.get("confidence", 0),
                }
            )
        row["month_votes"] = dict(month_votes)
        row["year_options"] = year_options
        row["alternate_date_candidates"] = raw_candidates
        row["row_annotation_raw"] = " ".join(dict.fromkeys(annotations))
        if month_votes:
            row["recognized_month"] = max(
                month_votes,
                key=lambda month: (month_votes[month], -month),
            )
            row["recognized_month_weight"] = month_votes[row["recognized_month"]]
            matching_labels = [
                candidate
                for candidate in row.get("label_candidates", [])
                if candidate["month"] == row["recognized_month"]
            ]
            if matching_labels:
                best_label = max(
                    matching_labels,
                    key=lambda candidate: (
                        source_weights.get(candidate["source"], 1.0),
                        candidate.get("confidence", 0),
                    ),
                )
                row["raw"] = best_label["raw"]
                row["month_raw"] = best_label["month_raw"]
        else:
            row["recognized_month"] = None
            row["recognized_month_weight"] = 0.0
    fallback_last_month = (release_date.month - 3) % 12 + 1
    fallback_first_month = (
        fallback_last_month - max(0, len(deduplicated) - 1) - 1
    ) % 12 + 1
    month_scores = []
    for first_month in range(1, 13):
        score = 0.0
        for index, row in enumerate(deduplicated):
            expected_month = (first_month - 1 + index) % 12 + 1
            if row["recognized_month"] is not None:
                if row["recognized_month"] != expected_month:
                    score += row["recognized_month_weight"]
        distance = min(
            (first_month - fallback_first_month) % 12,
            (fallback_first_month - first_month) % 12,
        )
        month_scores.append((score, distance * 0.01, first_month))
    first_month = min(month_scores)[2] if month_scores else fallback_first_month
    for index, row in enumerate(deduplicated):
        expected_month = (first_month - 1 + index) % 12 + 1
        recognized = row["recognized_month"]
        if (
            recognized is not None
            and recognized != expected_month
            and row["recognized_month_weight"] >= 2.5
        ):
            row["month"] = recognized
            row["observation_date_status"] = "date_alignment_error"
            row["observation_date_source"] = "recognized_month_conflicts_with_sequence"
        elif recognized is not None and recognized == expected_month:
            row["month"] = recognized
            row["observation_date_status"] = "recognized"
            row["observation_date_source"] = "explicit_month_label"
        else:
            row["month"] = expected_month
            row["observation_date_status"] = "inferred"
            row["observation_date_source"] = "aligned_month_sequence"
        row["month_inferred"] = row["observation_date_status"] == "inferred"
    generated_years = resolve_sequence_years(
        deduplicated,
        first_month,
        release_date,
        fallback_last_month,
    )
    for row, resolved_year in zip(deduplicated, generated_years):
        row["resolved_year"] = resolved_year
        strong_years = {
            option["year"]
            for option in row["year_options"]
            if option["weight"] >= 4.0
            and max(1960, release_date.year - 12)
            <= option["year"]
            <= release_date.year + 1
        }
        if strong_years and resolved_year not in strong_years:
            if all(
                abs(year - resolved_year) * 12
                > MAX_UNCORROBORATED_YEAR_DISTANCE_MONTHS
                for year in strong_years
            ):
                row["observation_date_source"] += (
                    "+implausible_year_anchor_ignored"
                )
            else:
                row["observation_date_status"] = "date_alignment_error"
                row["observation_date_source"] = (
                    "recognized_year_conflicts_with_sequence"
                )
        elif row["year_options"] and row["observation_date_status"] != "date_alignment_error":
            row["observation_date_source"] += "+explicit_year_anchor"
        elif row["observation_date_status"] != "date_alignment_error":
            row["observation_date_source"] += "+inferred_year"
        row["year_inferred"] = not bool(row["year_options"])
        row["observation_date"] = (
            ""
            if row["observation_date_status"] == "date_alignment_error"
            else date(resolved_year, row["month"], 1).isoformat()
        )
    return deduplicated


def runs(values):
    output = []
    start = None
    for index, value in enumerate(values):
        if value and start is None:
            start = index
        elif not value and start is not None:
            output.append((start, index - 1))
            start = None
    if start is not None:
        output.append((start, len(values) - 1))
    return output


def refined_edges(
    image_array,
    expected,
    y_top,
    y_bottom,
    minimum_left=0.0,
    header_top=None,
):
    height, width = image_array.shape
    expected_pixels = [fraction * width for fraction in expected]
    body = image_array[max(0, int(y_top)):min(height, int(y_bottom))]
    dark = body < 180
    scores = dark.mean(axis=0) if body.size else np.zeros(width)
    continuity = np.zeros(width)
    if body.size:
        for x_position in np.flatnonzero(scores > 0.08):
            column_runs = runs(dark[:, x_position])
            if column_runs:
                continuity[x_position] = max(
                    end - start + 1 for start, end in column_runs
                ) / body.shape[0]
    candidate_details = []
    for start, end in runs((continuity > 0.25) | (scores > 0.70)):
        if end - start > max(12, width * 0.008):
            continue
        center = (start + end) / 2
        center_index = min(width - 1, max(0, int(round(center))))
        if width * 0.08 <= center <= width * 0.995:
            candidate_details.append(
                {
                    "x": center,
                    "continuity": float(continuity[center_index]),
                    "density": float(scores[center_index]),
                }
            )
    if header_top is not None and y_top - header_top >= 20:
        header = image_array[
            max(0, int(header_top)):min(height, int(y_top))
        ]
        header_dark = header < 190
        header_scores = (
            header_dark.mean(axis=0)
            if header.size
            else np.zeros(width)
        )
        header_continuity = np.zeros(width)
        if header.size:
            for x_position in np.flatnonzero(header_scores > 0.03):
                column_runs = runs(header_dark[:, x_position])
                if column_runs:
                    header_continuity[x_position] = max(
                        end - start + 1 for start, end in column_runs
                    ) / header.shape[0]
        for start, end in runs(
            (header_continuity > 0.18) | (header_scores > 0.55)
        ):
            if end - start > max(14, width * 0.009):
                continue
            center = (start + end) / 2
            center_index = min(width - 1, max(0, int(round(center))))
            if width * 0.08 <= center <= width * 0.995:
                candidate_details.append(
                    {
                        "x": center,
                        "continuity": float(
                            header_continuity[center_index]
                        ),
                        "density": float(header_scores[center_index]),
                    }
                )
    merged_candidates = []
    for candidate in sorted(candidate_details, key=lambda item: item["x"]):
        if (
            merged_candidates
            and candidate["x"] - merged_candidates[-1]["x"]
            <= width * 0.006
        ):
            previous = merged_candidates[-1]
            if (
                candidate["continuity"],
                candidate["density"],
            ) > (
                previous["continuity"],
                previous["density"],
            ):
                previous["x"] = candidate["x"]
            previous["continuity"] = max(
                previous["continuity"],
                candidate["continuity"],
            )
            previous["density"] = max(
                previous["density"],
                candidate["density"],
            )
        else:
            merged_candidates.append(dict(candidate))
    candidate_details = merged_candidates
    plausible = [candidate["x"] for candidate in candidate_details]
    strong = [
        candidate["x"]
        for candidate in candidate_details
        if candidate["continuity"] > 0.18
    ]
    edge_count = len(expected_pixels)
    body_profile = (
        (body < 165).mean(axis=0)
        if body.size
        else np.zeros(width)
    )

    def ink_support(edges):
        supported = 0
        total_density = 0.0
        for left, right in zip(edges, edges[1:]):
            inset = max(3, int((right - left) * 0.10))
            profile = body_profile[
                max(0, int(left) + inset):min(width, int(right) - inset)
            ]
            density = float(profile.mean()) if profile.size else 0.0
            total_density += min(density, 0.08)
            supported += density >= 0.002
        return supported, total_density

    minimum_support = max(3, edge_count - 4)
    model_pool = strong if len(strong) >= minimum_support else plausible
    if len(model_pool) > edge_count + 2:
        ranked_candidates = sorted(
            candidate_details,
            key=lambda candidate: (
                candidate["x"] in strong,
                candidate["continuity"],
                candidate["density"],
            ),
            reverse=True,
        )[: edge_count + 2]
        model_pool = sorted(candidate["x"] for candidate in ranked_candidates)
    affine_choices = []
    if edge_count >= 4 and minimum_support <= len(model_pool) <= edge_count + 4:
        maximum_support = min(edge_count, len(model_pool))
        for support_count in range(maximum_support, minimum_support - 1, -1):
            for selected in combinations(model_pool, support_count):
                for expected_indexes in combinations(range(edge_count), support_count):
                    selected_array = np.asarray(selected)
                    expected_subset = np.asarray(
                        [expected_pixels[index] for index in expected_indexes]
                    )
                    slope, intercept = np.polyfit(
                        expected_subset,
                        selected_array,
                        1,
                    )
                    inferred = intercept + slope * np.asarray(expected_pixels)
                    residual = float(
                        np.mean(
                            (
                                selected_array
                                - (intercept + slope * expected_subset)
                            )
                            ** 2
                        )
                    )
                    if (
                        slope <= 0
                        or inferred[0] < max(width * 0.08, minimum_left)
                        or inferred[-1] > width * 1.04
                        or inferred[-1] - inferred[0] < width * 0.45
                        or residual > (width * 0.012) ** 2
                    ):
                        continue
                    bounded = inferred.copy()
                    if (
                        expected_indexes[-1] != edge_count - 1
                        and bounded[-1] > width * 0.995
                    ):
                        bounded[-1] = width * 0.995
                    if np.any(np.diff(bounded) <= width * 0.035):
                        continue
                    supported_columns, ink_density = ink_support(bounded)
                    location_error = float(
                        np.mean(
                            np.abs(bounded - np.asarray(expected_pixels))
                        )
                    ) / width
                    affine_choices.append(
                        (
                            supported_columns,
                            support_count,
                            ink_density,
                            -residual,
                            -location_error,
                            bounded.tolist(),
                        )
                    )
        if affine_choices:
            selected_model = max(
                affine_choices,
                key=lambda item: item[:-1],
            )
            return selected_model[-1], selected_model[1]
    result, matched = [], 0
    for expected_x in expected_pixels:
        nearby = [
            candidate
            for candidate in plausible
            if abs(candidate - expected_x) <= width * 0.035
        ]
        if nearby:
            result.append(min(nearby, key=lambda value: abs(value - expected_x)))
            matched += 1
        else:
            result.append(expected_x)
    for index in range(1, len(result)):
        if result[index] <= result[index - 1] + width * 0.035:
            result[index] = expected_pixels[index]
    return result, matched


def header_label(page, x1, x2, y1, y2, targets):
    lines = line_records(page["words"], x_range=(x1, x2), y_range=(y1, y2))
    match = best_line(lines, targets, minimum=0.42)
    if match is None:
        lines = line_records(
            page.get("sparse_words", []),
            x_range=(x1, x2),
            y_range=(y1, y2),
        )
        match = best_line(lines, targets, minimum=0.42)
    if match is None:
        lines = line_records(
            page.get("embedded_words", []),
            x_range=(x1, x2),
            y_range=(y1, y2),
        )
        match = best_line(lines, targets, minimum=0.42)
    if match is None:
        lines = line_records(
            ocr_region(
                page,
                x1,
                y1,
                x2,
                y2,
                psm=6,
                purpose="header",
            )
        )
        match = best_line(lines, targets, minimum=0.42)
    return remove_footnote_marker(match["text"]) if match else ""


def title_and_units(raw):
    cleaned = remove_footnote_marker(raw)
    units_match = re.search(
        r"\(([^()]*(?:dollars|rate)[^()]*)\)", cleaned, re.I
    )
    units = units_match.group(1).strip() if units_match else ""
    title = (
        (cleaned[: units_match.start()] + cleaned[units_match.end() :]).strip()
        if units_match
        else cleaned
    )
    return re.sub(r"\s+", " ", title), units


def table_config_variants(era_id, base_config):
    variants = [{**base_config, "variant": "standard"}]
    if era_id == 3:
        variants.append(
            {
                **base_config,
                "edges": ERA3_RIGHT_SHIFTED_EDGES,
                "variant": "right_shifted",
            }
        )
    if era_id == 4:
        variants.append(
            {
                **base_config,
                "edges": NO_MMDA_CONFIG["edges"],
                "groups": NO_MMDA_CONFIG["groups"],
                "variant": "no_mmda",
            }
        )
    return variants


def words_in_region(page, y1, y2):
    output = []
    for word_key, source in (
        ("words", "rendered_ocr"),
        ("sparse_words", "rendered_sparse_ocr"),
        ("embedded_words", "embedded_locator"),
    ):
        for word in page.get(word_key, []):
            center_y = (word["bbox"][1] + word["bbox"][3]) / 2
            if y1 <= center_y <= y2:
                output.append({**word, "ocr_source": source})
    return output


def represented_numeric_columns(page, image_array, edges, row_bounds):
    represented = 0
    coverages = []
    for x1, x2 in zip(edges, edges[1:]):
        populated_rows = 0
        for top, bottom in row_bounds:
            found = False
            for word_key in ("words", "sparse_words"):
                if any(
                    re.search(r"\d", word["text"])
                    for word in cell_words(
                        page,
                        x1 + 2,
                        top,
                        x2 - 2,
                        bottom,
                        word_key=word_key,
                    )
                ):
                    found = True
                    break
            if not found:
                height, width = image_array.shape
                crop = image_array[
                    max(0, int(top + (bottom - top) * 0.18)):
                    min(height, int(bottom - (bottom - top) * 0.18)),
                    max(0, int(x1 + (x2 - x1) * 0.08)):
                    min(width, int(x2 - (x2 - x1) * 0.08)),
                ]
                found = bool(crop.size and (crop < 165).mean() >= 0.006)
            populated_rows += found
        coverage = populated_rows / len(row_bounds) if row_bounds else 0.0
        coverages.append(coverage)
        represented += coverage >= 0.45
    return represented, coverages


def row_bounds_from_dates(date_candidates):
    row_centers = [item["y"] for item in date_candidates]
    if not row_centers:
        return [], 0.0, 0.0
    row_top = row_centers[0] - (
        (row_centers[1] - row_centers[0]) / 2
        if len(row_centers) > 1
        else 15
    )
    row_bottom = row_centers[-1] + (
        (row_centers[-1] - row_centers[-2]) / 2
        if len(row_centers) > 1
        else 15
    )
    bounds = []
    for index, center in enumerate(row_centers):
        top = row_top if index == 0 else (row_centers[index - 1] + center) / 2
        bottom = (
            row_bottom
            if index == len(row_centers) - 1
            else (center + row_centers[index + 1]) / 2
        )
        bounds.append((top, bottom))
    return bounds, row_top, row_bottom


def analyze_table_structure(
    era_id,
    base_config,
    page,
    image_array,
    target,
    title_line,
    next_y,
    release_date,
    page_status,
):
    evaluations = []
    variants = table_config_variants(era_id, base_config)
    label_end = min(
        config["edges"][0] for config in variants
    ) * page["width"]
    numeric_start = label_end + page["width"] * 0.02
    raw_label_candidates = []
    for word_key, source in (
        ("words", "rendered_ocr"),
        ("sparse_words", "rendered_sparse_ocr"),
        ("embedded_words", "embedded_locator"),
    ):
        raw_label_candidates.extend(
            date_rows_from_words(
                page.get(word_key, []),
                title_line["bbox"][3],
                next_y,
                label_end,
                source,
                release_date,
            )
        )
    for config in variants:
        date_candidates = date_rows(
            page,
            title_line["bbox"][3],
            next_y,
            label_end,
            numeric_start,
            release_date,
            config["rows"],
        )
        row_bounds, row_top, row_bottom = row_bounds_from_dates(date_candidates)
        physical_row_pool = spatial_value_rows(
            page,
            title_line["bbox"][3],
            next_y,
            numeric_start,
            config["rows"][1] + 2,
        )
        if not row_bounds:
            evaluations.append(
                {
                    "config": config,
                    "date_candidates": [],
                    "row_bounds": [],
                    "edges": [fraction * page["width"] for fraction in config["edges"]],
                    "matched_edges": 0,
                    "represented_columns": 0,
                    "column_coverages": [],
                    "physical_row_pool": physical_row_pool,
                    "raw_label_candidates": raw_label_candidates,
                    "candidate_row_offsets": [],
                    "selected_row_offset": 0,
                    "row_offset_score_margin": 0.0,
                    "row_offset_selection_reason": (
                        "offset evaluation not applicable; "
                        "no unified physical rows"
                    ),
                    "row_offset_unresolved": False,
                    "score": -100.0,
                    "valid": False,
                }
            )
            continue
        edges, matched_edges = refined_edges(
            image_array,
            config["edges"],
            row_top,
            row_bottom,
            minimum_left=(
                float(
                    np.percentile(
                        [
                            candidate["bbox"][2]
                            for candidate in date_candidates
                            if candidate.get("raw")
                        ],
                        50,
                    )
                )
                - page["width"] * 0.005
                if any(candidate.get("raw") for candidate in date_candidates)
                else 0.0
            ),
            header_top=title_line["bbox"][3],
        )
        numeric_represented, coverages = represented_numeric_columns(
            page,
            image_array,
            edges,
            row_bounds,
        )
        expected_columns = len(config["edges"]) - 1
        represented = (
            expected_columns
            if matched_edges >= len(edges) - 2
            else numeric_represented
        )
        header_text = normalized(
            " ".join(
                word["text"]
                for word in words_in_region(
                    page,
                    title_line["bbox"][1],
                    row_top,
                )
            )
        )
        has_mmda = bool(
            re.search(r"\bm+m*d+a\b", header_text)
            or any(
                difflib.SequenceMatcher(None, token, "mmda").ratio() >= 0.72
                for token in header_text.split()
                if token.startswith("m") and 3 <= len(token) <= 6
            )
        )
        row_count = len(date_candidates)
        minimum_rows, maximum_rows = config["rows"]
        row_score = 2.0 if minimum_rows <= row_count <= maximum_rows else -4.0
        geometry_score = matched_edges / len(edges) * 4.0
        coverage_score = represented / expected_columns * 4.0
        header_score = 0.0
        if has_mmda:
            header_score = 3.0 if config["variant"] == "standard" else -4.0
        elif config["variant"] == "no_mmda":
            header_score = 0.6
        if page_status == "SA" and era_id == 4 and config["variant"] == "no_mmda":
            header_score += 0.3
        score = row_score + geometry_score + coverage_score + header_score
        valid = (
            minimum_rows <= row_count <= maximum_rows
            and represented == expected_columns
            and matched_edges >= 2
            and title_line.get("title_score", 1.0) >= 0.70
        )
        evaluations.append(
            {
                "config": config,
                "date_candidates": date_candidates,
                "row_bounds": row_bounds,
                "row_top": row_top,
                "row_bottom": row_bottom,
                "edges": edges,
                "matched_edges": matched_edges,
                "represented_columns": represented,
                "numeric_represented_columns": numeric_represented,
                "column_coverages": coverages,
                "physical_row_pool": physical_row_pool,
                "raw_label_candidates": raw_label_candidates,
                "candidate_row_offsets": [],
                "selected_row_offset": 0,
                "row_offset_score_margin": 0.0,
                "row_offset_selection_reason": "zero-offset default",
                "row_offset_unresolved": False,
                "header_has_mmda": has_mmda,
                "score": score,
                "valid": valid,
            }
        )
    mmda_evidence = any(
        item.get("header_has_mmda") for item in evaluations
    )
    valid_standard = [
        item
        for item in evaluations
        if item["valid"] and item["config"]["variant"] == "standard"
    ]
    valid_no_mmda = [
        item
        for item in evaluations
        if item["valid"] and item["config"]["variant"] == "no_mmda"
    ]
    if era_id == 4 and page_status == "NSA" and valid_standard:
        selection_pool = valid_standard
    elif era_id == 4 and page_status == "SA" and valid_no_mmda:
        selection_pool = valid_no_mmda
    elif mmda_evidence:
        selection_pool = [
            item
            for item in evaluations
            if item["config"]["variant"] == "standard"
        ]
    else:
        selection_pool = evaluations
    selected = max(
        selection_pool,
        key=lambda item: (
            item["valid"],
            item["score"],
            item["represented_columns"],
            item["matched_edges"],
            item["config"]["variant"] == "standard",
        ),
    )
    selected["target"] = target
    selected["title_line"] = title_line
    selected["table_number"] = TABLE_TARGETS.index(target) + 1
    selected["_page_height"] = page["height"]
    selected["evidence"] = {
        "credible_title": title_line.get("title_score", 1.0) >= 0.70,
        "visible_grid": selected["matched_edges"] >= 2,
        "coherent_month_rows": (
            selected["config"]["rows"][0]
            <= len(selected["date_candidates"])
            <= selected["config"]["rows"][1]
        ),
        "aligned_numeric_columns": (
            selected["represented_columns"]
            == len(selected["config"]["edges"]) - 1
        ),
    }
    return selected


def labels_for_physical_centers(centers, label_candidates, page_height):
    assignments = [[] for _ in centers]
    if not centers:
        return assignments
    gaps = [
        current - previous for previous, current in zip(centers, centers[1:])
    ]
    typical_gap = statistics.median(gaps) if gaps else page_height * 0.012
    tolerance = max(8.0, typical_gap * 0.48)
    for candidate in label_candidates:
        nearest_index = min(
            range(len(centers)),
            key=lambda index: abs(candidate["y"] - centers[index]),
        )
        if abs(candidate["y"] - centers[nearest_index]) <= tolerance:
            assignments[nearest_index].append(candidate)
    return assignments


def row_window_score(centers, assignments, reference):
    source_weights = {
        "rendered_ocr": 3.0,
        "rendered_sparse_ocr": 2.2,
        "embedded_locator": 1.2,
    }
    matches = 0
    mismatches = 0
    year_matches = 0
    year_mismatches = 0
    labeled_rows = 0
    distances = []
    for center, labels, expected_text in zip(
        centers,
        assignments,
        reference,
    ):
        expected = date.fromisoformat(expected_text)
        month_votes = defaultdict(float)
        for label in labels:
            if label.get("month"):
                month_votes[label["month"]] += source_weights.get(
                    label["source"],
                    1.0,
                )
            distances.append(abs(label["y"] - center))
        if month_votes:
            labeled_rows += 1
            recognized_month = max(
                month_votes,
                key=lambda month: (month_votes[month], -month),
            )
            if recognized_month == expected.month:
                matches += 1
            else:
                mismatches += 1
        explicit_years = {
            option["year"]
            for label in labels
            for option in label.get("year_candidates", [])
            if option.get("weight", 0) >= 2.5
        }
        if explicit_years:
            if expected.year in explicit_years:
                year_matches += 1
            else:
                year_mismatches += 1
    gaps = [
        current - previous for previous, current in zip(centers, centers[1:])
    ]
    typical_gap = statistics.median(gaps) if gaps else 1.0
    distance_penalty = (
        statistics.mean(distances) / typical_gap
        if distances and typical_gap
        else 1.0
    )
    score = (
        matches * 12.0
        - mismatches * 18.0
        + labeled_rows * 1.5
        + year_matches * 6.0
        - year_mismatches * 10.0
        - distance_penalty * 2.0
    )
    return {
        "score": round(score, 6),
        "month_matches": matches,
        "month_mismatches": mismatches,
        "explicit_year_matches": year_matches,
        "explicit_year_mismatches": year_mismatches,
        "labeled_rows": labeled_rows,
        "mean_vertical_distance_rows": round(distance_penalty, 6),
    }


def unified_rows_for_window(centers, assignments, reference, prior_rows):
    source_weights = {
        "rendered_ocr": 3.0,
        "rendered_sparse_ocr": 2.2,
        "embedded_locator": 1.2,
    }
    unified = []
    for row_index, (center, labels, expected_text) in enumerate(
        zip(centers, assignments, reference)
    ):
        expected = date.fromisoformat(expected_text)
        month_votes = defaultdict(float)
        year_options = []
        annotations = []
        alternate_candidates = []
        for label in labels:
            weight = source_weights.get(label["source"], 1.0)
            month_votes[label["month"]] += weight
            for option in label.get("year_candidates", []):
                year_options.append(
                    {
                        **option,
                        "weight": option.get("weight", 0) * weight,
                        "source": label["source"],
                    }
                )
            if label.get("annotation"):
                annotations.append(label["annotation"])
            alternate_candidates.append(
                {
                    "raw": label.get("raw", ""),
                    "month": label.get("month"),
                    "year_candidates": label.get("year_candidates", []),
                    "source": label.get("source", ""),
                    "confidence": label.get("confidence", 0),
                }
            )
        recognized_month = (
            max(
                month_votes,
                key=lambda month: (month_votes[month], -month),
            )
            if month_votes
            else None
        )
        matching_labels = [
            label
            for label in labels
            if label.get("month") == recognized_month
        ]
        best_label = (
            max(
                matching_labels,
                key=lambda label: (
                    source_weights.get(label["source"], 1.0),
                    label.get("confidence", 0),
                ),
            )
            if matching_labels
            else None
        )
        strong_conflict = (
            recognized_month is not None
            and recognized_month != expected.month
            and month_votes[recognized_month] >= 2.5
        )
        previous = (
            prior_rows[row_index]
            if row_index < len(prior_rows)
            else {}
        )
        unified.append(
            {
                **previous,
                "y": center,
                "physical_row_center": center,
                "bbox": (
                    best_label["bbox"]
                    if best_label
                    else [0, center, 0, center]
                ),
                "raw": best_label.get("raw", "") if best_label else "",
                "month": expected.month,
                "month_raw": (
                    best_label.get("month_raw", "") if best_label else ""
                ),
                "recognized_month": recognized_month,
                "recognized_month_weight": (
                    month_votes.get(recognized_month, 0.0)
                    if recognized_month is not None
                    else 0.0
                ),
                "month_votes": dict(month_votes),
                "year_options": year_options,
                "resolved_year": expected.year,
                "observation_date": "" if strong_conflict else expected_text,
                "observation_date_status": (
                    "date_alignment_error"
                    if strong_conflict
                    else "page_consensus_reconciled"
                ),
                "observation_date_source": (
                    "unified_physical_row_mapping_conflict"
                    if strong_conflict
                    else "unified_physical_row_mapping"
                ),
                "row_annotation_raw": " ".join(
                    dict.fromkeys(annotations)
                ),
                "alternate_date_candidates": alternate_candidates,
                "source": "unified_physical_row_mapping",
                "row_inserted": False,
                "month_inferred": recognized_month is None,
                "year_inferred": not bool(year_options),
                "label_candidates": labels,
                "matched_month_label_candidates": alternate_candidates,
            }
        )
    return unified


def evaluate_physical_row_offsets(analysis, reference):
    rows = analysis["date_candidates"]
    count = len(reference)
    current_centers = [row["y"] for row in rows]
    pool_centers = sorted(
        {
            round(item["y"], 6)
            for item in analysis.get("physical_row_pool", [])
        }
    )
    if len(pool_centers) < count:
        pool_centers = current_centers
    possible_starts = range(max(1, len(pool_centers) - count + 1))
    current_start = min(
        possible_starts,
        key=lambda start: sum(
            abs(pool_centers[start + index] - current_centers[index])
            for index in range(min(count, len(current_centers)))
        ),
    )
    candidates = []
    assignments_by_offset = {}
    centers_by_offset = {}
    for offset in range(-2, 3):
        start = current_start + offset
        feasible = 0 <= start and start + count <= len(pool_centers)
        centers = (
            pool_centers[start : start + count]
            if feasible
            else []
        )
        if offset == 0 and len(current_centers) == count:
            centers = current_centers
            feasible = True
        assignments = labels_for_physical_centers(
            centers,
            analysis.get("raw_label_candidates", []),
            analysis["_page_height"],
        )
        score = (
            row_window_score(centers, assignments, reference)
            if feasible
            else {
                "score": None,
                "month_matches": 0,
                "month_mismatches": 0,
                "explicit_year_matches": 0,
                "explicit_year_mismatches": 0,
                "labeled_rows": 0,
                "mean_vertical_distance_rows": None,
            }
        )
        record = {
            "offset": offset,
            "feasible": feasible,
            "physical_row_centers": [
                round(value, 3) for value in centers
            ],
            **score,
        }
        candidates.append(record)
        assignments_by_offset[offset] = assignments
        centers_by_offset[offset] = centers
    feasible_candidates = [
        item for item in candidates if item["feasible"]
    ]
    ranked = sorted(
        feasible_candidates,
        key=lambda item: (
            item["score"],
            item["month_matches"],
            -item["month_mismatches"],
            -abs(item["offset"]),
        ),
        reverse=True,
    )
    best = ranked[0]
    zero = next(item for item in candidates if item["offset"] == 0)
    second_score = ranked[1]["score"] if len(ranked) > 1 else -math.inf
    margin = (
        best["score"] - second_score
        if math.isfinite(second_score)
        else math.inf
    )
    nonzero_decisive = (
        best["offset"] != 0
        and best["score"] >= zero["score"] + 12.0
        and best["month_matches"] >= max(5, count - 2)
        and best["month_mismatches"] == 0
        and best["explicit_year_mismatches"] == 0
    )
    selected_offset = best["offset"] if nonzero_decisive else 0
    unresolved = (
        best["offset"] != 0
        and not nonzero_decisive
        and best["score"] >= zero["score"] + 4.0
        and best["month_matches"] >= max(5, count - 4)
        and best["month_mismatches"] <= 2
    )
    reason = (
        "decisive nonzero physical-row window selected"
        if nonzero_decisive
        else "zero-offset physical-row window retained"
        if not unresolved
        else "nonzero mapping was suggestive but not decisive"
    )
    return {
        "candidates": candidates,
        "selected_offset": selected_offset,
        "margin": round(margin, 6) if math.isfinite(margin) else "inf",
        "reason": reason,
        "unresolved": unresolved,
        "selected_centers": centers_by_offset[selected_offset],
        "selected_assignments": assignments_by_offset[selected_offset],
    }


def reconcile_page_table_dates(analyses):
    complete_sequences = defaultdict(
        lambda: {
            "support": 0,
            "maximum_recognized": 0,
            "recognized_total": 0,
            "maximum_year_anchors": 0,
            "inferred_total": 0,
        }
    )
    for analysis in analyses:
        rows = analysis["date_candidates"]
        sequence = tuple(row["observation_date"] for row in rows)
        if (
            analysis["valid"]
            and sequence
            and all(sequence)
            and not any(
                row["observation_date_status"] == "date_alignment_error"
                for row in rows
            )
        ):
            recognized = sum(
                row.get("recognized_month")
                == date.fromisoformat(resolved).month
                for row, resolved in zip(rows, sequence)
            )
            year_anchors = sum(
                any(
                    option["year"] == date.fromisoformat(resolved).year
                    and option.get("weight", 0) >= 2.5
                    for option in row.get("year_options", [])
                )
                for row, resolved in zip(rows, sequence)
            )
            sequence_metrics = complete_sequences[sequence]
            sequence_metrics["support"] += 1
            sequence_metrics["maximum_recognized"] = max(
                sequence_metrics["maximum_recognized"],
                recognized,
            )
            sequence_metrics["recognized_total"] += recognized
            sequence_metrics["maximum_year_anchors"] = max(
                sequence_metrics["maximum_year_anchors"],
                year_anchors,
            )
            sequence_metrics["inferred_total"] += sum(
                row["observation_date_status"] == "inferred"
                for row in rows
            )
    if not complete_sequences:
        return {}
    strongly_labeled = [
        item
        for item in complete_sequences.items()
        if item[1]["maximum_recognized"] >= len(item[0]) - 1
    ]
    reference_pool = (
        strongly_labeled
        if strongly_labeled
        else list(complete_sequences.items())
    )
    reference, reference_metrics = max(
        reference_pool,
        key=lambda item: (
            item[1]["support"],
            item[1]["maximum_recognized"],
            item[1]["maximum_year_anchors"],
            item[1]["recognized_total"],
            -item[1]["inferred_total"],
            item[0],
        ),
    )
    support = reference_metrics["support"]
    strong_page_consensus = (
        support >= 2
        or reference_metrics["maximum_recognized"] >= len(reference) - 1
    )
    repairable_short_tables = sum(
        len(analysis["date_candidates"]) == len(reference) - 1
        and all(
            analysis["evidence"].get(key, False)
            for key in (
                "credible_title",
                "visible_grid",
                "aligned_numeric_columns",
            )
        )
        for analysis in analyses
    )
    if (
        support < 2
        and reference_metrics["maximum_recognized"] < len(reference) - 1
        and repairable_short_tables == 0
    ):
        return {}
    reconciled = {}
    reference_count = len(reference)
    reference_years = [
        date.fromisoformat(value).year for value in reference
    ]
    plausible_year_low = min(reference_years) - 1
    plausible_year_high = max(reference_years) + 1
    for analysis in analyses:
        rows = analysis["date_candidates"]
        original_count = len(rows)
        other_structure_valid = all(
            analysis["evidence"].get(key, False)
            for key in (
                "credible_title",
                "visible_grid",
                "aligned_numeric_columns",
            )
        )
        if (
            other_structure_valid
            and len(rows) == reference_count - 1
        ):
            insertion_choices = []
            for missing_index in range(reference_count):
                expected_without_missing = [
                    value
                    for index, value in enumerate(reference)
                    if index != missing_index
                ]
                score = 0.0
                conflicts = 0
                for row, expected_date in zip(
                    rows,
                    expected_without_missing,
                ):
                    expected_month = date.fromisoformat(
                        expected_date
                    ).month
                    if row.get("observation_date") == expected_date:
                        score += 5.0
                    if row.get("recognized_month") == expected_month:
                        score += 3.0
                    elif (
                        row.get("recognized_month")
                        and row.get("recognized_month_weight", 0) >= 2.5
                    ):
                        score -= 5.0
                        conflicts += 1
                insertion_choices.append(
                    (score, -conflicts, -missing_index, missing_index)
                )
            _, _, _, missing_index = max(insertion_choices)
            gaps = [
                current["y"] - previous["y"]
                for previous, current in zip(rows, rows[1:])
            ]
            typical_gap = statistics.median(gaps) if gaps else 20.0
            if missing_index == 0:
                inferred_y = rows[0]["y"] - typical_gap
            elif missing_index == len(rows):
                inferred_y = rows[-1]["y"] + typical_gap
            else:
                inferred_y = (
                    rows[missing_index - 1]["y"]
                    + rows[missing_index]["y"]
                ) / 2
            expected = date.fromisoformat(reference[missing_index])
            rows.insert(
                missing_index,
                {
                    "y": inferred_y,
                    "bbox": [0, inferred_y, 0, inferred_y],
                    "raw": "",
                    "month": expected.month,
                    "month_raw": "",
                    "recognized_month": None,
                    "recognized_month_weight": 0.0,
                    "month_votes": {},
                    "year_options": [],
                    "resolved_year": expected.year,
                    "observation_date": expected.isoformat(),
                    "observation_date_status": "inferred",
                    "observation_date_source": (
                        "page_table_consensus_missing_physical_row"
                    ),
                    "row_annotation_raw": "",
                    "alternate_date_candidates": [],
                    "source": "spatial_inference",
                    "row_inserted": True,
                    "month_inferred": True,
                    "year_inferred": True,
                    "label_candidates": [],
                },
            )
            analysis["date_candidates"] = rows
            (
                analysis["row_bounds"],
                analysis["row_top"],
                analysis["row_bottom"],
            ) = row_bounds_from_dates(rows)
            analysis["evidence"]["coherent_month_rows"] = True
            analysis["valid"] = True
        if not analysis["valid"] or len(rows) < reference_count:
            continue
        if len(rows) > reference_count:
            windows = []
            for start in range(len(rows) - reference_count + 1):
                candidate_rows = rows[start : start + reference_count]
                score = 0.0
                for candidate, expected_date in zip(
                    candidate_rows,
                    reference,
                ):
                    expected_month = date.fromisoformat(expected_date).month
                    if candidate.get("observation_date") == expected_date:
                        score += 5.0
                    if candidate.get("recognized_month") == expected_month:
                        score += 2.0
                    elif (
                        candidate.get("recognized_month")
                        and candidate.get("recognized_month_weight", 0) >= 2.5
                    ):
                        score -= 3.0
                windows.append((score, -start, candidate_rows))
            rows = max(windows, key=lambda item: item[:2])[2]
            analysis["date_candidates"] = rows
            (
                analysis["row_bounds"],
                analysis["row_top"],
                analysis["row_bottom"],
            ) = row_bounds_from_dates(rows)
        if len(rows) != reference_count:
            continue
        offset_evaluation = evaluate_physical_row_offsets(
            analysis,
            reference,
        )
        analysis["candidate_row_offsets"] = offset_evaluation[
            "candidates"
        ]
        analysis["selected_row_offset"] = offset_evaluation[
            "selected_offset"
        ]
        analysis["row_offset_score_margin"] = offset_evaluation[
            "margin"
        ]
        analysis["row_offset_selection_reason"] = offset_evaluation[
            "reason"
        ]
        analysis["row_offset_unresolved"] = offset_evaluation[
            "unresolved"
        ]
        if offset_evaluation["selected_offset"] != 0:
            rows = unified_rows_for_window(
                offset_evaluation["selected_centers"],
                offset_evaluation["selected_assignments"],
                reference,
                rows,
            )
            analysis["date_candidates"] = rows
            (
                analysis["row_bounds"],
                analysis["row_top"],
                analysis["row_bottom"],
            ) = row_bounds_from_dates(rows)
        changed = 0
        for row, expected_date in zip(rows, reference):
            if row.get("observation_date") == expected_date:
                continue
            expected = date.fromisoformat(expected_date)
            recognized_month = row.get("recognized_month")
            if (
                not strong_page_consensus
                and
                recognized_month is not None
                and row.get("recognized_month_weight", 0) >= 2.5
                and recognized_month != expected.month
            ):
                row["observation_date_status"] = "date_alignment_error"
                row["observation_date_source"] = (
                    row.get("observation_date_source", "")
                    + "+page_consensus_conflict_preserved"
                ).strip("+")
                continue
            strong_years = {
                option["year"]
                for option in row.get("year_options", [])
                if option.get("weight", 0) >= 4.0
                and plausible_year_low
                <= option["year"]
                <= plausible_year_high
            }
            candidate_years = {
                option["year"]
                for option in row.get("year_options", [])
                if plausible_year_low
                <= option["year"]
                <= plausible_year_high
            }
            if (
                not strong_page_consensus
                and
                strong_years
                and expected.year not in strong_years
                and expected.year not in candidate_years
            ):
                row["observation_date_status"] = "date_alignment_error"
                row["observation_date_source"] = (
                    row.get("observation_date_source", "")
                    + "+page_consensus_year_conflict_preserved"
                ).strip("+")
                continue
            previous_date = row.get("observation_date", "")
            row.setdefault("alternate_date_candidates", []).append(
                {
                    "raw": row.get("raw", ""),
                    "month": row.get("recognized_month"),
                    "resolved_date": previous_date,
                    "source": "pre_page_table_consensus",
                    "confidence": row.get("recognized_month_weight", 0),
                }
            )
            row["observation_date"] = expected_date
            row["resolved_year"] = expected.year
            row["month"] = expected.month
            row["observation_date_status"] = "page_consensus_reconciled"
            row["observation_date_source"] = (
                row.get("observation_date_source", "")
                + "+page_table_consensus"
            ).strip("+")
            changed += 1
        if changed or original_count != reference_count:
            reconciled[analysis["table_number"]] = {
                "dates_changed": changed,
                "rows_before": original_count,
                "rows_after": len(analysis["date_candidates"]),
                "selected_row_offset": analysis.get(
                    "selected_row_offset",
                    0,
                ),
            }
        (
            analysis["row_bounds"],
            analysis["row_top"],
            analysis["row_bottom"],
        ) = row_bounds_from_dates(analysis["date_candidates"])
        for row, bounds in zip(
            analysis["date_candidates"],
            analysis["row_bounds"],
        ):
            row["physical_row_center"] = row["y"]
            row["physical_row_bounds"] = [
                round(bounds[0], 3),
                round(bounds[1], 3),
            ]
    return {
        "reference_dates": list(reference),
        "supporting_tables": support,
        "reconciled_tables": reconciled,
    }


def column_definitions(config, page, edges, y1, y2, page_status):
    columns = []
    column_index = 0
    for group_config in config["groups"]:
        leaves = group_config["leaves"]
        group_start, group_end = edges[column_index], edges[column_index + len(leaves)]
        parent_raw = header_label(
            page, group_start, group_end, y1, y2, group_config["parent"]
        )
        for leaf_targets in leaves:
            x1, x2 = edges[column_index], edges[column_index + 1]
            leaf_raw = (
                header_label(page, x1, x2, y1 + (y2 - y1) * 0.35, y2, leaf_targets)
                if leaf_targets
                else ""
            )
            columns.append(
                {
                    "x1": x1,
                    "x2": x2,
                    "level_1": parent_raw,
                    "level_2": leaf_raw,
                    "level_3": "",
                    "adjustment": group_config["status"] or page_status,
                    "parent_targets": group_config["parent"],
                    "leaf_targets": leaf_targets or [],
                    **canonical_column(group_config, leaf_targets, column_index),
                }
            )
            column_index += 1
    return columns


def canonical_column(group_config, leaf_targets, column_index):
    parent = normalized(" ".join(group_config["parent"]))
    leaf_tokens = {
        normalized(target)
        for target in (leaf_targets or [])
        if normalized(target)
    }

    def leaf_is(*aliases):
        normalized_aliases = {normalized(alias) for alias in aliases}
        return bool(leaf_tokens & normalized_aliases)

    if "demand deposit" in parent:
        geography = (
            "all_banks"
            if leaf_is("all banks")
            else "new_york_city"
            if leaf_is("new york city")
            else "other_banks"
            if leaf_is("other banks")
            else ""
        )
        return {
            "deposit_type_canonical": "demand",
            "geography_canonical": geography,
            "customer_type_canonical": "",
        }
    if "other checkable" in parent:
        deposit_type = "other_checkable"
    elif "mmda" in parent:
        deposit_type = "mmda"
    elif "ats now" in parent or "now ats" in parent:
        deposit_type = "ats_now"
    elif "savings" in parent:
        deposit_type = (
            "ats_now"
            if leaf_is("ats/now", "now/ats", "ats now", "now ats")
            else "savings"
        )
    else:
        deposit_type = ""
    customer_type = (
        "ats_now"
        if leaf_is("ats/now", "now/ats", "ats now", "now ats")
        else
        "business"
        if leaf_is("business")
        else "other"
        if leaf_is("other", "others")
        else "total"
        if leaf_is("total")
        else ""
    )
    return {
        "deposit_type_canonical": deposit_type,
        "geography_canonical": "",
        "customer_type_canonical": customer_type,
    }


def cell_words(page, x1, y1, x2, y2, word_key="words"):
    selected = []
    for word in page.get(word_key, []):
        left, top, right, bottom = word["bbox"]
        center_x, center_y = (left + right) / 2, (top + bottom) / 2
        if x1 < center_x < x2 and y1 < center_y < y2:
            selected.append(word)
    selected.sort(key=lambda item: item["bbox"][0])
    return selected


def value_candidate(words, ink_density):
    raw = " ".join(word["text"] for word in words)
    confidence = (
        round(
            statistics.mean(max(0.0, word["confidence"]) for word in words),
            2,
        )
        if words
        else 0.0
    )
    numeric_value, status = parse_value(raw, ink_density)
    return {
        "raw": raw,
        "numeric": numeric_value,
        "status": status,
        "confidence": confidence,
    }


def parse_value(raw, ink_density):
    candidates = numeric_interpretations(
        raw,
        0.0,
        "compatibility_parser",
        ink_density,
    )
    selected, _ = select_numeric_candidate(candidates, ink_density)
    return selected["value_numeric"], selected["value_status"]


def split_annotation(raw):
    stripped = raw.strip()
    annotations = []
    for pattern in (
        r"^\s*([rRcC])(?=\s*[+\-]?\d)",
        r"(?<=\d)\s*([rRcC])\s*$",
        r"^\s*([rRcC])\s*$",
    ):
        match = re.search(pattern, stripped)
        if match:
            annotations.append(match.group(1))
            stripped = (stripped[: match.start(1)] + stripped[match.end(1) :]).strip()
    return stripped, " ".join(dict.fromkeys(annotations))


def numeric_interpretations(
    raw,
    confidence,
    source,
    ink_density,
    eligible=True,
    word_geometry=None,
    ocr_variant="",
):
    stripped, annotation = split_annotation(raw)
    compact = re.sub(r"\s+", "", stripped.lower())
    base = {
        "raw": raw,
        "source": source,
        "ocr_variant": ocr_variant,
        "confidence": round(confidence, 2),
        "annotation": annotation,
        "eligible": eligible,
    }

    def candidate(normalization, value_numeric, value_status, **extra):
        return {
            **base,
            "normalization": normalization,
            "repaired_candidate": value_numeric,
            "value_numeric": value_numeric,
            "value_status": value_status,
            **extra,
        }

    unavailable = bool(
        re.fullmatch(r"n[\W_]*a[\W_]*", compact)
        or compact in {"--", "—", "–", "...", "…", "notavailable"}
    )
    if unavailable:
        return [
            candidate(
                "printed_unavailable_marker",
                "",
                "not_available",
            )
        ]
    if not stripped:
        return [
            candidate(
                "no_ocr_text",
                "",
                "blank" if ink_density < 0.004 else "extraction_error",
            )
        ]
    interpretations = []
    canonical_printed_pattern = (
        r"^[+-]?(?:\d{1,3}(?:,\d{3})*|\d+)\.\d$"
    )
    if re.fullmatch(canonical_printed_pattern, stripped):
        interpretations.append(
            candidate(
                "exact_one_decimal",
                stripped.replace(",", ""),
                "reported",
            )
        )
    spacing_cleaned = re.sub(r"(?<=\d)[·•](?=\d)", ".", stripped)
    period_match = re.fullmatch(
        r"([+\-]?\d{1,3}(?:\.\d{3})+)\.(\d)",
        re.sub(r"\s+", "", spacing_cleaned),
    )
    if period_match:
        normalized_value = (
            period_match.group(1).replace(".", "")
            + "."
            + period_match.group(2)
        )
        interpretations.append(
            candidate(
                "periods_interpreted_as_thousands_separators",
                normalized_value,
                "reported",
            )
        )
    punctuation_cleaned = re.sub(r"\s+", "", spacing_cleaned).strip(
        "|[](){}_:;"
    )
    if (
        punctuation_cleaned != stripped
        and re.fullmatch(canonical_printed_pattern, punctuation_cleaned)
    ):
        interpretations.append(
            candidate(
                "removed_border_punctuation",
                punctuation_cleaned.replace(",", ""),
                "reported",
            )
        )
    spatial_match = re.fullmatch(
        r"([+\-]?[0-9][0-9,.\s]*?)\s+([0-9])",
        stripped,
    )
    if spatial_match:
        sign = "-" if spatial_match.group(1).lstrip().startswith("-") else ""
        leading_digits = re.sub(r"\D", "", spatial_match.group(1))
        spatial_support = False
        spatial_gap = None
        if word_geometry and len(word_geometry) >= 2:
            last_word = word_geometry[-1]
            previous_word = word_geometry[-2]
            if re.fullmatch(r"\d", last_word.get("text", "").strip()):
                spatial_gap = (
                    last_word["bbox"][0] - previous_word["bbox"][2]
                )
                spatial_support = spatial_gap >= -1.0
        if leading_digits:
            interpretations.append(
                candidate(
                    "spatially_separated_trailing_decimal_digit",
                    f"{sign}{leading_digits}.{spatial_match.group(2)}",
                    "reported",
                    spatial_decimal_gap=spatial_gap,
                    spatial_evidence=spatial_support,
                )
            )
    sign = "-" if stripped.lstrip().startswith("-") else ""
    digits = re.sub(r"\D", "", stripped)
    if digits == "0":
        interpretations.append(
            candidate(
                "integer_zero_to_one_decimal",
                "0.0",
                "reported",
            )
        )
    elif len(digits) >= 2 and not re.fullmatch(
        canonical_printed_pattern,
        stripped,
    ):
        normalization = (
            "inferred_trailing_decimal_from_integer"
            if re.fullmatch(r"[+\-]?\d+", stripped)
            else "repaired_misplaced_separator_to_one_decimal"
        )
        interpretations.append(
            candidate(
                normalization,
                f"{sign}{digits[:-1]}.{digits[-1]}",
                "reported",
                unsafe_decimal_relocation=bool(
                    re.search(r"[.,]\d{2}\D*$", stripped)
                ),
            )
        )
        separator_count = len(re.findall(r"[,.\s]", stripped))
        if separator_count >= 2 and len(digits) >= 6:
            for trim_count in (1, 2):
                trimmed = digits[:-trim_count]
                if len(trimmed) >= 2:
                    interpretations.append(
                        candidate(
                            (
                                "removed_extra_trailing_decimal_digit"
                                if trim_count == 1
                                and re.search(
                                    r"[.,]\d{2}\D*$",
                                    stripped,
                                )
                                else
                                "trimmed_trailing_ocr_artifact_then_decimal"
                            ),
                            f"{sign}{trimmed[:-1]}.{trimmed[-1]}",
                            "reported",
                            trimmed_trailing_digits=trim_count,
                        )
                    )
            if len(digits) >= 4:
                without_penultimate = digits[:-2] + digits[-1]
                interpretations.append(
                    candidate(
                        "removed_adjacent_ocr_artifact_before_final_decimal_digit",
                        (
                            f"{sign}{without_penultimate[:-1]}."
                            f"{without_penultimate[-1]}"
                        ),
                        "reported",
                        removed_digit=digits[-2],
                    )
                )
    unique = {}
    for interpretation in interpretations:
        if (
            interpretation["value_status"] == "reported"
            and not CANONICAL_NUMERIC_RE.fullmatch(
                interpretation["value_numeric"]
            )
        ):
            continue
        key = (
            interpretation["value_status"],
            interpretation["value_numeric"],
            interpretation["normalization"],
        )
        unique[key] = interpretation
    if unique:
        return list(unique.values())
    return [
        candidate(
            "unparsed",
            "",
            "extraction_error",
        )
    ]


def annotate_candidate_context(candidates, table_number, column):
    for candidate in candidates:
        candidate["measure_canonical"] = {
            1: "debits",
            2: "average_deposits",
            3: "turnover",
        }[table_number]
        candidate["series_context"] = {
            "deposit_type": column["deposit_type_canonical"],
            "geography": column["geography_canonical"],
            "customer_type": column["customer_type_canonical"],
        }
        if candidate["value_status"] != "reported":
            continue
        try:
            value = abs(float(candidate["value_numeric"]))
        except (TypeError, ValueError):
            candidate["scale_score"] = -10.0
            continue
        demand_geography = (
            column["deposit_type_canonical"] == "demand"
            and bool(column["geography_canonical"])
        )
        if table_number == 1:
            if (
                column["deposit_type_canonical"] == "demand"
                and column["geography_canonical"] == "all_banks"
            ):
                lower, upper = (20_000.0, 2_000_000.0)
            elif demand_geography:
                lower, upper = (5_000.0, 2_000_000.0)
            else:
                lower, upper = (0.0, 500_000.0)
        elif table_number == 2:
            lower, upper = (
                (1.0, 10_000.0)
                if demand_geography
                else (0.0, 10_000.0)
            )
        else:
            lower, upper = (
                (1.0, 20_000.0)
                if demand_geography
                else (0.0, 5_000.0)
            )
        candidate["scale_score"] = (
            1.0 if lower <= value <= upper else -7.0
        )


def numeric_candidate_score(candidate):
    normalization_scores = {
        "exact_one_decimal": 7.0,
        "spatially_separated_trailing_decimal_digit": 5.8,
        "removed_border_punctuation": 5.0,
        "periods_interpreted_as_thousands_separators": 4.8,
        "integer_zero_to_one_decimal": 4.0,
        "inferred_trailing_decimal_from_integer": 2.8,
        "repaired_misplaced_separator_to_one_decimal": 2.6,
        "trimmed_trailing_ocr_artifact_then_decimal": 0.5,
        "removed_extra_trailing_decimal_digit": 6.2,
        "removed_adjacent_ocr_artifact_before_final_decimal_digit": 0.3,
        "merged_trailing_decimal_digit_across_image_ocr_passes": 5.5,
        "printed_unavailable_marker": 6.0,
    }
    source_scores = {
        "rendered_ocr": 2.0,
        "rendered_sparse_ocr": 1.6,
        "targeted_upscaled_240dpi_crop": 2.2,
        "true_high_resolution_480dpi_crop": 3.4,
        "true_high_resolution_600dpi_crop": 3.6,
        "embedded_locator": -5.0,
    }
    score = normalization_scores.get(candidate["normalization"], -2.0)
    score += source_scores.get(candidate["source"], 0.0)
    score += max(0.0, candidate["confidence"]) / 25.0
    score += float(candidate.get("scale_score", 0.0))
    if candidate.get("spatial_evidence"):
        score += 1.2
    if candidate.get("unsafe_decimal_relocation"):
        score -= 5.0
    if candidate["value_status"] == "reported":
        if not CANONICAL_NUMERIC_RE.fullmatch(candidate["value_numeric"]):
            return -100.0
        try:
            numeric_value = abs(float(candidate["value_numeric"]))
        except ValueError:
            return -100.0
        if numeric_value > 10_000_000:
            score -= 8.0
        score += 0.8
    return score


def select_numeric_candidate(candidates, ink_density):
    eligible = [candidate for candidate in candidates if candidate.get("eligible", True)]
    locator_values = {
        (candidate["value_status"], candidate["value_numeric"])
        for candidate in candidates
        if not candidate.get("eligible", True)
        and candidate["value_status"] in {"reported", "not_available"}
    }
    groups = defaultdict(list)
    for candidate in eligible:
        if candidate["value_status"] in {"reported", "not_available"}:
            groups[(candidate["value_status"], candidate["value_numeric"])].append(candidate)
    ranked = []
    for key, members in groups.items():
        source_families = {
            (
                member["source"],
                member.get("ocr_variant") or "page",
            )
            for member in members
        }
        score = max(numeric_candidate_score(member) for member in members)
        score += max(0, len(source_families) - 1) * 1.0
        locator_support = key in locator_values
        score += 7.0 if locator_support else 0.0
        true_high_resolution_support = any(
            member["source"].startswith("true_high_resolution_")
            for member in members
        )
        if true_high_resolution_support:
            score += 4.0
        effective_support = len(source_families)
        ranked.append(
            (
                score,
                effective_support,
                locator_support,
                key,
                members,
            )
        )
    ranked.sort(
        reverse=True,
        key=lambda item: (item[0], item[1], item[2], item[3]),
    )
    if ranked:
        (
            best_score,
            support,
            locator_support,
            (status, numeric_value),
            members,
        ) = ranked[0]
        competing = [
            item for item in ranked[1:]
            if item[3] != (status, numeric_value)
        ]
        margin = best_score - competing[0][0] if competing else math.inf
        best_member = max(members, key=numeric_candidate_score)
        true_high_resolution_support = any(
            member["source"].startswith("true_high_resolution_")
            for member in members
        )
        normalized = best_member["normalization"] != "exact_one_decimal"
        accepted = (
            status == "not_available"
            or support >= 2
            or (
                not normalized
                and best_member["confidence"] >= 60
                and margin >= 2.0
            )
            or (
                normalized
                and locator_support
                and support >= 1
                and best_member["confidence"] >= 65
                and margin >= 2.0
            )
            or (normalized and support >= 2 and margin >= 1.0)
            or (
                true_high_resolution_support
                and best_member["confidence"] >= 45
                and margin >= 1.0
            )
            or (
                true_high_resolution_support
                and locator_support
                and best_member["normalization"]
                in {
                    "removed_extra_trailing_decimal_digit",
                    "merged_trailing_decimal_digit_across_image_ocr_passes",
                }
                and margin >= 0.0
            )
        )
        if accepted:
            return (
                {
                    "value_raw": best_member["raw"],
                    "value_numeric": numeric_value,
                    "value_status": status,
                    "ocr_confidence": best_member["confidence"],
                    "cell_annotation_raw": best_member.get("annotation", ""),
                    "selected_source": best_member["source"],
                    "normalization_rule": best_member["normalization"],
                },
                (
                    f"accepted {status} candidate {numeric_value!r}; "
                    f"score={best_score:.2f}, independent_support={support}, "
                    f"embedded_locator_support={locator_support}, "
                    f"margin={margin if math.isfinite(margin) else 'inf'}"
                ),
            )
    raw_candidates = [
        candidate for candidate in eligible if candidate.get("raw", "").strip()
    ]
    best_raw = max(
        raw_candidates,
        key=lambda item: (item["confidence"], numeric_candidate_score(item)),
        default=None,
    )
    if not raw_candidates and ink_density < 0.004:
        return (
            {
                "value_raw": "",
                "value_numeric": "",
                "value_status": "blank",
                "ocr_confidence": 0.0,
            "cell_annotation_raw": "",
            "selected_source": "none",
            "normalization_rule": "",
        },
            "no OCR text and no visible cell ink",
        )
    return (
        {
            "value_raw": best_raw["raw"] if best_raw else "",
            "value_numeric": "",
            "value_status": "extraction_error",
            "ocr_confidence": best_raw["confidence"] if best_raw else 0.0,
            "cell_annotation_raw": best_raw.get("annotation", "") if best_raw else "",
            "selected_source": (
                best_raw["source"]
                if best_raw
                and best_raw.get("eligible", True)
                and best_raw["source"] != "embedded_locator"
                else "none"
            ),
            "normalization_rule": "",
        },
        "no numeric candidate was clearly superior",
    )


def targeted_cell_candidates(
    page,
    bbox,
    ink_density,
    true_high_resolution_dpi=None,
):
    if true_high_resolution_dpi:
        image, rendered_path, high_resolution_angle = (
            true_high_resolution_page(
                page,
                dpi=true_high_resolution_dpi,
            )
        )
        source = f"true_high_resolution_{true_high_resolution_dpi}dpi_crop"
        source_bbox = [
            bbox[0] / page["width"] * image.width,
            bbox[1] / page["height"] * image.height,
            bbox[2] / page["width"] * image.width,
            bbox[3] / page["height"] * image.height,
        ]
        scale = 2
    else:
        image = Image.open(page["processed_image"]).convert("L")
        rendered_path = Path(page["processed_image"])
        high_resolution_angle = None
        source = "targeted_upscaled_240dpi_crop"
        source_bbox = bbox
        scale = 3
    x1, y1, x2, y2 = source_bbox
    right_extension = (
        int((x2 - x1) * 0.05)
        if true_high_resolution_dpi
        else 0
    )
    inset_x = max(
        1,
        int((x2 - x1) * (0.005 if true_high_resolution_dpi else 0.01)),
    )
    inset_y = (
        1
        if true_high_resolution_dpi
        else max(1, int((y2 - y1) * 0.08))
    )
    crop = image.crop(
        (
            max(0, int(x1) + inset_x),
            max(0, int(y1) + inset_y),
            min(
                image.width,
                int(
                    x2
                    + (
                        (x2 - x1) * 0.05
                        if true_high_resolution_dpi
                        else 0
                    )
                ),
            ),
            min(image.height, int(y2) - inset_y),
        )
    )
    variants = [
        (
            "gray_psm7",
            7,
            ImageOps.autocontrast(crop),
            "0123456789.,-+nNaArRcC",
        ),
        (
            "threshold_psm8",
            8,
            ImageOps.autocontrast(crop).point(
                lambda value: 255 if value > 175 else 0
            ),
            "0123456789.,-+nNaArRcC",
        ),
        (
            "gray_numeric_psm7",
            7,
            ImageEnhance.Contrast(
                ImageOps.autocontrast(crop)
            ).enhance(1.35),
            "0123456789.,-+",
        ),
    ]
    if true_high_resolution_dpi:
        tight_inset_y = max(1, int((y2 - y1) * 0.08))
        tight_crop = image.crop(
            (
                max(0, int(x1) + inset_x),
                max(0, int(y1) + tight_inset_y),
                min(image.width, int(x2) - inset_x),
                min(image.height, int(y2) - tight_inset_y),
            )
        )
        variants.append(
            (
                "gray_psm8",
                8,
                ImageOps.autocontrast(crop),
                "0123456789.,-+nNaArRcC",
            )
        )
        variants.append(
            (
                "tight_gray_psm7",
                7,
                ImageOps.autocontrast(tight_crop),
                "0123456789.,-+nNaArRcC",
            )
        )
    output = []
    pass_payloads = []
    cache_dir = Path(page["processed_image"]).parent
    for variant, psm, variant_image, whitelist in variants:
        resized = variant_image.resize(
            (max(1, variant_image.width * scale), max(1, variant_image.height * scale)),
            Image.Resampling.LANCZOS,
        )
        key = hashlib.sha1(
            (
                f"{OCR_CACHE_VERSION}:{bbox}:{variant}:{psm}:"
                f"{true_high_resolution_dpi or RENDER_DPI}:"
                f"{high_resolution_angle}:crop-v3:scale-{scale}:"
                f"inset-{inset_x}-{inset_y}:extend-{right_extension}"
            ).encode()
        ).hexdigest()[:18]
        image_path = cache_dir / f"cell-{key}.png"
        json_path = cache_dir / f"cell-{key}.json"
        if json_path.exists():
            payload = json.loads(json_path.read_text(encoding="utf-8"))
        else:
            resized.save(image_path)
            try:
                completed = subprocess.run(
                    [
                        TESSERACT,
                        str(image_path),
                        "stdout",
                        "-l",
                        "eng",
                        "--psm",
                        str(psm),
                        "-c",
                        f"tessedit_char_whitelist={whitelist}",
                        "tsv",
                    ],
                    check=True,
                    capture_output=True,
                    text=True,
                )
            finally:
                image_path.unlink(missing_ok=True)
            words = parse_tsv(completed.stdout)
            payload = {
                "raw": " ".join(word["text"] for word in words),
                "words": words,
                "confidence": (
                    statistics.mean(max(0.0, word["confidence"]) for word in words)
                    if words
                    else 0.0
                ),
            }
            json_path.write_text(json.dumps(payload), encoding="utf-8")
        pass_payloads.append(
            {
                "variant": variant,
                "raw": payload["raw"],
                "confidence": payload["confidence"],
            }
        )
        output.extend(
            numeric_interpretations(
                payload["raw"],
                payload["confidence"],
                source,
                ink_density,
                word_geometry=payload.get("words", []),
                ocr_variant=variant,
            )
        )
        for candidate in output:
            if candidate.get("source") == source:
                candidate.setdefault(
                    "rendered_page_path",
                    project_relative_path(rendered_path),
                )
                candidate.setdefault(
                    "high_resolution_deskew_angle",
                    high_resolution_angle,
                )
    for prefix_pass in pass_payloads:
        prefix_match = re.fullmatch(
            r"\s*([+\-]?[\d,.\s]+?)[.,]\s*[-—]?\s*",
            prefix_pass["raw"],
        )
        if not prefix_match:
            continue
        prefix_digits = re.sub(r"\D", "", prefix_match.group(1))
        if len(prefix_digits) < 3:
            continue
        for digit_pass in pass_payloads:
            if digit_pass is prefix_pass:
                continue
            digit_match = re.search(r"(\d)\D*$", digit_pass["raw"])
            if not digit_match:
                continue
            digit_pass_digits = re.sub(r"\D", "", digit_pass["raw"])
            if len(digit_pass_digits) < 4:
                continue
            other_body = digit_pass_digits[:-1]
            matching_suffix = next(
                (
                    length
                    for length in range(
                        min(4, len(prefix_digits), len(other_body)),
                        2,
                        -1,
                    )
                    if prefix_digits[-length:]
                    == other_body[-length:]
                ),
                0,
            )
            if matching_suffix < 3:
                continue
            value_numeric = (
                f"{prefix_digits}.{digit_match.group(1)}"
            )
            output.append(
                {
                    "raw": (
                        f"{prefix_pass['raw']} || "
                        f"{digit_pass['raw']}"
                    ),
                    "source": source,
                    "ocr_variant": "cross_pass_trailing_digit_merge",
                    "confidence": round(
                        min(
                            prefix_pass["confidence"],
                            digit_pass["confidence"],
                        ),
                        2,
                    ),
                    "annotation": "",
                    "eligible": True,
                    "normalization": (
                        "merged_trailing_decimal_digit_"
                        "across_image_ocr_passes"
                    ),
                    "repaired_candidate": value_numeric,
                    "value_numeric": value_numeric,
                    "value_status": "reported",
                    "spatial_evidence": True,
                    "supporting_raw_strings": [
                        prefix_pass["raw"],
                        digit_pass["raw"],
                    ],
                    "rendered_page_path": project_relative_path(rendered_path),
                    "high_resolution_deskew_angle": (
                        high_resolution_angle
                    ),
                }
            )
    return output


def metadata_type(text):
    content = normalized(text)
    if "discontinued" in content or "last issue" in content:
        return "discontinuation_notice"
    if "revised" in content or "revision" in content:
        return "revision_notice"
    if "method" in content or "benchmark" in content or "seasonal adjustment" in content:
        return "methodology_change"
    if re.search(r"\b[1-9]\s+", text):
        return "footnotes"
    return "other_non_table_material"


def filtered_metadata(lines):
    kept = []
    for line in lines:
        line_normalized = normalized(line["text"])
        if not line_normalized:
            continue
        if any(pattern in line_normalized for pattern in FURNITURE_PATTERNS):
            continue
        kept.append(line)
    return kept


def issue_row(
    era_id,
    source_file,
    release_date,
    issue_type,
    detail,
    page_number="",
    table_number="",
    observation_date="",
    column_path="",
    severity="warning",
):
    return {
        "era_id": era_id,
        "source_file": source_file,
        "release_date": release_date,
        "page_number": page_number,
        "table_number": table_number,
        "observation_date": observation_date,
        "column_path": column_path,
        "severity": severity,
        "issue_type": issue_type,
        "detail": detail,
    }


def classify_page(header, analyses, title_lines):
    valid = [analysis for analysis in analyses if analysis["valid"]]
    header_title = normalized(header["printed_release_title"])
    if header["conflicting_release"]:
        return (
            "unrelated_release_page",
            1.0,
            f"Explicit conflicting release code/title: {header['printed_release_code'] or header['printed_release_title']}",
        )
    if len(valid) == 3:
        return (
            "table_page",
            0.99,
            "Three semantic G.6 title bands have credible grids, month rows, and aligned numeric columns.",
        )
    if (
        header["printed_release_code"] == "G.6"
        and len(valid) < 3
        and re.search(
            r"\b(revision of|methodology|methodological|discontinuation|notice)\b",
            header_title,
        )
    ):
        return (
            "metadata_page",
            0.98,
            "Explicit G.6 revision/methodology notice without three independently valid table grids.",
        )
    directly_anchored_valid = [
        analysis
        for analysis in valid
        if analysis["title_line"].get("source") != "spatial_title_inference"
    ]
    if directly_anchored_valid and header["printed_release_code"] == "G.6":
        return (
            "table_page",
            0.82,
            (
                f"{len(valid)} independently valid G.6 table instance(s), "
                "including a direct semantic title anchor, on an explicit G.6 page."
            ),
        )
    weak_structure = any(
        sum(analysis["evidence"].values()) >= 2 for analysis in analyses
    )
    if header["printed_release_code"] == "G.6" and not valid:
        return (
            "metadata_page",
            0.94,
            "Explicit G.6 page without a structurally valid monthly table grid.",
        )
    if title_lines or weak_structure:
        return (
            "uncertain_page",
            0.55,
            "Some title or grid evidence was present, but no table instance passed all structural checks.",
        )
    return (
        "metadata_page",
        0.85,
        "No G.6 table title/grid/month-row combination was detected.",
    )


def candidate_conflict(candidates):
    best_by_pass = {}
    for candidate in candidates:
        if (
            not candidate.get("eligible", True)
            or candidate["value_status"] != "reported"
        ):
            continue
        pass_key = (
            candidate["source"],
            candidate.get("ocr_variant") or "page",
        )
        incumbent = best_by_pass.get(pass_key)
        if (
            incumbent is None
            or numeric_candidate_score(candidate)
            > numeric_candidate_score(incumbent)
        ):
            best_by_pass[pass_key] = candidate
    values = {
        candidate["value_numeric"]
        for candidate in best_by_pass.values()
    }
    return len(values) > 1


def locator_disagrees(candidates):
    locator_values = {
        candidate["value_numeric"]
        for candidate in candidates
        if not candidate.get("eligible", True)
        and candidate["value_status"] == "reported"
    }
    eligible_values = {
        candidate["value_numeric"]
        for candidate in candidates
        if candidate.get("eligible", True)
        and candidate["value_status"] == "reported"
    }
    return bool(locator_values - eligible_values)


def apply_selected_candidate(row, audit_cell, selected, reason):
    row.update(selected)
    row["_selection_reason"] = reason
    row["selection_reason"] = reason
    row["normalization_rule"] = selected.get(
        "normalization_rule",
        "",
    )
    audit_cell.pop("arithmetic_selection", None)
    audit_cell.update(
        {
            "value_raw": selected["value_raw"],
            "value_numeric": selected["value_numeric"],
            "value_status": selected["value_status"],
            "ocr_confidence": selected["ocr_confidence"],
            "cell_annotation_raw": selected["cell_annotation_raw"],
            "selected_source": selected["selected_source"],
            "selection_reason": reason,
            "normalization_rule": selected.get(
                "normalization_rule",
                "",
            ),
        }
    )


def retry_row_targeted(row, page, force_true_high_resolution=False):
    if not row.get("_targeted_attempted"):
        row["_targeted_attempted"] = True
        new_candidates = targeted_cell_candidates(
            page,
            row["_bbox"],
            row["_ink_density"],
        )
        annotate_candidate_context(
            new_candidates,
            row["table_number"],
            row["_column_context"],
        )
        row["_ocr_candidates"].extend(new_candidates)
    selected, reason = select_numeric_candidate(
        row["_ocr_candidates"],
        row["_ink_density"],
    )
    if (
        (
            force_true_high_resolution
            or selected["value_status"] == "extraction_error"
        )
        and not row.get("_true_high_resolution_attempted")
    ):
        row["_true_high_resolution_attempted"] = True
        before_status = selected["value_status"]
        high_resolution_candidates = targeted_cell_candidates(
            page,
            row["_bbox"],
            row["_ink_density"],
            true_high_resolution_dpi=TRUE_HIGH_RESOLUTION_DPI,
        )
        annotate_candidate_context(
            high_resolution_candidates,
            row["table_number"],
            row["_column_context"],
        )
        row["_ocr_candidates"].extend(high_resolution_candidates)
        selected, reason = select_numeric_candidate(
            row["_ocr_candidates"],
            row["_ink_density"],
        )
        attempted_dpis = [TRUE_HIGH_RESOLUTION_DPI]
        if (
            selected["value_status"] == "extraction_error"
            or (
                force_true_high_resolution
                and locator_disagrees(row["_ocr_candidates"])
                and float(selected.get("ocr_confidence") or 0) < 50
            )
        ):
            fallback_candidates = targeted_cell_candidates(
                page,
                row["_bbox"],
                row["_ink_density"],
                true_high_resolution_dpi=600,
            )
            annotate_candidate_context(
                fallback_candidates,
                row["table_number"],
                row["_column_context"],
            )
            row["_ocr_candidates"].extend(fallback_candidates)
            high_resolution_candidates.extend(fallback_candidates)
            attempted_dpis.append(600)
            selected, reason = select_numeric_candidate(
                row["_ocr_candidates"],
                row["_ink_density"],
            )
        row["_audit_cell"]["true_high_resolution"] = {
            "attempted": True,
            "dpi": attempted_dpis,
            "before_status": before_status,
            "after_status": selected["value_status"],
            "recovered": (
                before_status == "extraction_error"
                and selected["value_status"] == "reported"
            ),
            "candidates": high_resolution_candidates,
            "rendered_page_paths": sorted(
                {
                    candidate.get("rendered_page_path", "")
                    for candidate in high_resolution_candidates
                    if candidate.get("rendered_page_path")
                }
            ),
            "deskew_angles": sorted(
                {
                    candidate.get("high_resolution_deskew_angle")
                    for candidate in high_resolution_candidates
                    if candidate.get("high_resolution_deskew_angle")
                    is not None
                }
            ),
        }
    row["true_high_resolution_attempted"] = int(
        bool(row.get("_true_high_resolution_attempted"))
    )
    if selected["value_status"] == "extraction_error":
        eligible_numeric = [
            candidate
            for candidate in row["_ocr_candidates"]
            if candidate.get("eligible", True)
            and candidate["value_status"] == "reported"
        ]
        embedded_numeric = [
            candidate
            for candidate in row["_ocr_candidates"]
            if not candidate.get("eligible", True)
            and candidate["value_status"] == "reported"
        ]
        if embedded_numeric and not eligible_numeric:
            reason = (
                "embedded-only numeric candidate retained as locator evidence; "
                "no eligible image-derived candidate"
            )
    apply_selected_candidate(row, row["_audit_cell"], selected, reason)
    row["_audit_cell"]["targeted_cell_crop_attempted"] = True
    row["_audit_cell"]["true_high_resolution_attempted"] = bool(
        row.get("_true_high_resolution_attempted")
    )
    row["_audit_cell"]["ocr_candidates"] = row["_ocr_candidates"]


def reported_candidate_options(row, limit=6):
    pass_winners = {}
    for candidate in row.get("_ocr_candidates", []):
        if (
            candidate["value_status"] != "reported"
            or not candidate.get("eligible", True)
            or not CANONICAL_NUMERIC_RE.fullmatch(
                candidate.get("value_numeric", "")
            )
        ):
            continue
        pass_key = (
            candidate["source"],
            candidate.get("ocr_variant") or "page",
        )
        incumbent = pass_winners.get(pass_key)
        if (
            incumbent is None
            or numeric_candidate_score(candidate)
            > numeric_candidate_score(incumbent)
        ):
            pass_winners[pass_key] = candidate
    groups = defaultdict(list)
    for candidate in row.get("_ocr_candidates", []):
        if (
            candidate["value_status"] != "reported"
            or not candidate.get("eligible", True)
            or not CANONICAL_NUMERIC_RE.fullmatch(
                candidate.get("value_numeric", "")
            )
        ):
            continue
        try:
            numeric_value = float(candidate["value_numeric"])
        except (TypeError, ValueError):
            continue
        groups[numeric_value].append(candidate)
    options = []
    for numeric_value, members in groups.items():
        best_member = max(members, key=numeric_candidate_score)
        source_families = {
            pass_key
            for pass_key, winner in pass_winners.items()
            if winner["value_numeric"] == best_member["value_numeric"]
        }
        score = max(numeric_candidate_score(member) for member in members)
        score += max(0, len(source_families) - 1) * 2.0
        embedded_support = any(
            not candidate.get("eligible", True)
            and candidate["value_status"] == "reported"
            and candidate["value_numeric"] == best_member["value_numeric"]
            for candidate in row.get("_ocr_candidates", [])
        )
        if embedded_support:
            score += 6.0
        if str(numeric_value) == row.get("value_numeric"):
            score += 1.0
        options.append(
            {
                "numeric": numeric_value,
                "candidate": best_member,
                "score": score,
                "image_supported": True,
                "sources": sorted(
                    f"{source}:{variant}"
                    for source, variant in source_families
                ),
                "embedded_locator_support": embedded_support,
            }
        )
    return sorted(
        options,
        key=lambda option: (
            option["score"],
            option["image_supported"],
            -abs(option["numeric"]),
        ),
        reverse=True,
    )[:limit]


def apply_arithmetic_option(row, option, relation, residual, tolerance):
    candidate = option["candidate"]
    selected = {
        "value_raw": candidate["raw"],
        "value_numeric": candidate["value_numeric"],
        "value_status": "reported",
        "ocr_confidence": candidate["confidence"],
        "cell_annotation_raw": candidate.get("annotation", ""),
        "selected_source": candidate["source"],
        "normalization_rule": candidate["normalization"],
    }
    reason = (
        f"selected existing OCR candidate by {relation}; "
        f"residual={residual:.6g}, tolerance={tolerance:.6g}, "
        f"sources={option['sources']}"
    )
    apply_selected_candidate(row, row["_audit_cell"], selected, reason)
    row["_audit_cell"]["arithmetic_selection"] = {
        "relation": relation,
        "residual": residual,
        "tolerance": tolerance,
        "candidate_sources": option["sources"],
    }


def turnover_rounding_tolerance(debits, deposits):
    if deposits == 0:
        return math.inf
    return (
        0.05
        + 0.05 / abs(deposits)
        + abs(debits) * 0.05 / (deposits * deposits)
        + 1e-9
    )


def reconcile_additive_candidates(rows, relation):
    options = [reported_candidate_options(row) for row in rows]
    if any(not choices for choices in options):
        return False
    current_values = [numeric(row) for row in rows]
    current_residual = (
        abs(current_values[0] - sum(current_values[1:]))
        if all(value is not None for value in current_values)
        else math.inf
    )
    current_tolerance = ADDITIVE_ROUNDING_TOLERANCE
    if current_residual <= 0.05:
        return False
    valid = []
    for combination in product(*options):
        values = [option["numeric"] for option in combination]
        residual = abs(values[0] - sum(values[1:]))
        tolerance = ADDITIVE_ROUNDING_TOLERANCE
        image_support = sum(
            option["image_supported"] for option in combination
        )
        exact_identity = residual <= 0.05
        if (
            residual <= tolerance
            and (
                image_support >= 2
                or (exact_identity and image_support >= 1)
            )
        ):
            valid.append(
                (
                    exact_identity,
                    sum(option["score"] for option in combination),
                    -residual,
                    combination,
                    residual,
                    tolerance,
                )
            )
    if not valid:
        return False
    (
        exact_identity,
        _,
        _,
        selected_options,
        residual,
        tolerance,
    ) = max(
        valid,
        key=lambda item: item[:3],
    )
    if current_residual <= current_tolerance and not exact_identity:
        return False
    for row, option in zip(rows, selected_options):
        if row.get("value_numeric") != option["candidate"]["value_numeric"]:
            apply_arithmetic_option(
                row,
                option,
                relation,
                residual,
                tolerance,
            )
    return True


def reconcile_turnover_candidates(rows):
    options = [reported_candidate_options(row) for row in rows]
    if any(not choices for choices in options):
        return False
    current_values = [numeric(row) for row in rows]
    current_residual = math.inf
    current_tolerance = math.inf
    if (
        all(value is not None for value in current_values)
        and current_values[1] != 0
    ):
        current_residual = abs(
            current_values[0] / current_values[1] - current_values[2]
        )
        current_tolerance = turnover_rounding_tolerance(
            current_values[0],
            current_values[1],
        )
    if current_residual <= current_tolerance:
        return False
    valid = []
    for combination in product(*options):
        debits, deposits, turnover = [
            option["numeric"] for option in combination
        ]
        if deposits == 0:
            continue
        residual = abs(debits / deposits - turnover)
        tolerance = turnover_rounding_tolerance(debits, deposits)
        image_support = sum(
            option["image_supported"] for option in combination
        )
        if residual <= tolerance and image_support >= 2:
            valid.append(
                (
                    sum(option["score"] for option in combination),
                    -residual,
                    combination,
                    residual,
                    tolerance,
                )
            )
    if not valid:
        return False
    _, _, selected_options, residual, tolerance = max(
        valid,
        key=lambda item: item[:2],
    )
    for row, option in zip(rows, selected_options):
        if row.get("value_numeric") != option["candidate"]["value_numeric"]:
            apply_arithmetic_option(
                row,
                option,
                "turnover_equals_debits_divided_by_deposits",
                residual,
                tolerance,
            )
    return True


def arithmetic_candidate_reconciliation(rows):
    by_table_row = defaultdict(dict)
    for row in rows:
        by_table_row[
            (
                row["page_number"],
                row["table_instance_id"],
                row["row_index"],
            )
        ][row["column_index"]] = row
    for columns in by_table_row.values():
        if {0, 1, 2} <= set(columns):
            reconcile_additive_candidates(
                [columns[index] for index in (0, 1, 2)],
                "all_banks_equals_new_york_city_plus_other_banks",
            )
        customer_columns = {
            row["customer_type_canonical"]: row
            for row in columns.values()
            if row["customer_type_canonical"]
        }
        if {
            "total",
            "ats_now",
            "business",
            "other",
        } <= set(customer_columns):
            reconcile_additive_candidates(
                [
                    customer_columns["total"],
                    customer_columns["ats_now"],
                    customer_columns["business"],
                    customer_columns["other"],
                ],
                "component_total_equals_ats_now_plus_business_plus_other",
            )
        elif {"total", "business", "other"} <= set(customer_columns):
            reconcile_additive_candidates(
                [
                    customer_columns["total"],
                    customer_columns["business"],
                    customer_columns["other"],
                ],
                "component_total_equals_business_plus_other",
            )
    by_page_position = defaultdict(dict)
    for row in rows:
        by_page_position[
            (
                row["page_number"],
                row["adjustment_status"],
                row["row_index"],
                row["column_index"],
            )
        ][row["table_number"]] = row
    for tables in by_page_position.values():
        if {1, 2, 3} <= set(tables):
            reconcile_turnover_candidates(
                [tables[index] for index in (1, 2, 3)]
            )


def arithmetic_failure_groups(rows):
    failures = []
    by_table_row = defaultdict(dict)
    for row in rows:
        by_table_row[
            (
                row["page_number"],
                row["table_instance_id"],
                row["row_index"],
            )
        ][row["column_index"]] = row
    for key, columns in by_table_row.items():
        table_number = next(iter(columns.values()))["table_number"]
        if table_number not in {1, 2}:
            continue
        if {0, 1, 2} <= set(columns):
            triplet = [columns[index] for index in (0, 1, 2)]
            values = [numeric(row) for row in triplet]
            if all(value is not None for value in values):
                tolerance = ADDITIVE_ROUNDING_TOLERANCE
                if abs(values[0] - values[1] - values[2]) > tolerance:
                    failures.append(
                        ("all_banks_component_check", triplet)
                    )
        customer_columns = {
            row["customer_type_canonical"]: row
            for row in columns.values()
            if row["customer_type_canonical"]
        }
        required = (
            {"total", "ats_now", "business", "other"}
            if int(next(iter(columns.values()))["era_id"]) == 2
            else {"total", "business", "other"}
            if int(next(iter(columns.values()))["era_id"]) == 1
            else set()
        )
        if required <= set(customer_columns) and required:
            component_rows = [
                customer_columns["total"],
                *[
                    customer_columns[name]
                    for name in ("ats_now", "business", "other")
                    if name in required
                ],
            ]
            values = [numeric(row) for row in component_rows]
            if (
                all(value is not None for value in values)
                and abs(values[0] - sum(values[1:]))
                > ADDITIVE_ROUNDING_TOLERANCE
            ):
                failures.append(
                    ("component_total_check", component_rows)
                )
    by_page_position = defaultdict(dict)
    for row in rows:
        by_page_position[
            (
                row["page_number"],
                row["adjustment_status"],
                row["row_index"],
                row["column_index"],
            )
        ][row["table_number"]] = row
    for tables in by_page_position.values():
        if not {1, 2, 3} <= set(tables):
            continue
        involved = [tables[index] for index in (1, 2, 3)]
        values = [numeric(row) for row in involved]
        if all(value is not None for value in values) and values[1] != 0:
            tolerance = turnover_rounding_tolerance(
                values[0],
                values[1],
            )
            if abs(values[0] / values[1] - values[2]) > tolerance:
                failures.append(("turnover_ratio_check", involved))
    return failures


def targeted_retry_for_arithmetic(rows, page):
    attempted = set()
    for _, involved in arithmetic_failure_groups(rows):
        for row in involved:
            key = (
                row["table_instance_id"],
                row["row_index"],
                row["column_index"],
            )
            if key not in attempted:
                retry_row_targeted(
                    row,
                    page,
                    force_true_high_resolution=True,
                )
                attempted.add(key)


def extract_table_rows(
    era_id,
    source_file,
    release_date,
    page,
    image_array,
    analysis,
    page_classification,
    page_audit,
    issues,
):
    table_number = analysis["table_number"]
    title_line = analysis["title_line"]
    table_config = analysis["config"]
    date_candidates = analysis["date_candidates"]
    row_bounds = analysis["row_bounds"]
    columns = column_definitions(
        table_config,
        page,
        analysis["edges"],
        title_line["bbox"][1],
        analysis["row_top"],
        page_adjustment(page),
    )
    table_name_raw, units_raw = title_and_units(title_line["text"])
    table_instance_id = f"p{page['page_number']:03d}_t{table_number:02d}_i01"
    output = []
    for row_index, (date_row, (cell_top, cell_bottom)) in enumerate(
        zip(date_candidates, row_bounds)
    ):
        if date_row["observation_date_status"] == "date_alignment_error":
            issues.append(
                issue_row(
                    era_id,
                    source_file,
                    release_date.isoformat(),
                    "date_alignment_error",
                    (
                        f"Row {row_index}: raw={date_row.get('raw', '')!r}; "
                        f"month votes={date_row.get('month_votes', {})}; "
                        f"source={date_row['observation_date_source']}."
                    ),
                    page_number=page["page_number"],
                    table_number=table_number,
                    severity="error",
                )
            )
        elif date_row["observation_date_status"] == "inferred":
            issues.append(
                issue_row(
                    era_id,
                    source_file,
                    release_date.isoformat(),
                    "observation_month_inferred",
                    f"Row {row_index}: raw={date_row.get('raw', '')!r}; date={date_row['observation_date']}.",
                    page_number=page["page_number"],
                    table_number=table_number,
                    observation_date=date_row["observation_date"],
                )
            )
        elif (
            date_row["observation_date_status"]
            == "page_consensus_reconciled"
        ):
            issues.append(
                issue_row(
                    era_id,
                    source_file,
                    release_date.isoformat(),
                    "date_reconciled_by_page_consensus",
                    (
                        f"Row {row_index}: raw={date_row.get('raw', '')!r}; "
                        f"date={date_row['observation_date']}; "
                        f"month votes={date_row.get('month_votes', {})}."
                    ),
                    page_number=page["page_number"],
                    table_number=table_number,
                    observation_date=date_row["observation_date"],
                )
            )
        for column_index, column in enumerate(columns):
            bbox = [
                round(column["x1"], 2),
                round(cell_top, 2),
                round(column["x2"], 2),
                round(cell_bottom, 2),
            ]
            crop = image_array[
                max(0, int(cell_top + (cell_bottom - cell_top) * 0.14)):
                min(page["height"], int(cell_bottom - (cell_bottom - cell_top) * 0.14)),
                max(0, int(column["x1"]) + 4):
                min(page["width"], int(column["x2"]) - 4),
            ]
            ink_density = float((crop < 170).mean()) if crop.size else 0.0
            candidates = []
            for word_key, source, eligible in (
                ("words", "rendered_ocr", True),
                ("sparse_words", "rendered_sparse_ocr", True),
                ("embedded_words", "embedded_locator", False),
            ):
                selected_words = cell_words(
                    page,
                    column["x1"] + 2,
                    cell_top,
                    column["x2"] - 2,
                    cell_bottom,
                    word_key=word_key,
                )
                raw = " ".join(word["text"] for word in selected_words)
                confidence = (
                    statistics.mean(
                        max(0.0, word["confidence"]) for word in selected_words
                    )
                    if selected_words
                    else 0.0
                )
                candidates.extend(
                    numeric_interpretations(
                        raw,
                        confidence,
                        source,
                        ink_density,
                        eligible=eligible,
                        word_geometry=selected_words,
                    )
                )
            annotate_candidate_context(
                candidates,
                table_number,
                column,
            )
            selected, reason = select_numeric_candidate(candidates, ink_density)
            trigger_targeted = (
                selected["value_status"] == "extraction_error"
                or candidate_conflict(candidates)
                or (
                    selected["value_status"] not in {"blank", "not_available"}
                    and selected["ocr_confidence"] < LOW_CONFIDENCE
                )
                or (
                    selected["value_status"] == "blank"
                    and ink_density >= 0.004
                )
            )
            true_high_resolution_attempted = False
            true_high_resolution_audit = {
                "attempted": False,
                "dpi": "",
                "before_status": selected["value_status"],
                "after_status": selected["value_status"],
                "recovered": False,
                "candidates": [],
                "rendered_page_paths": [],
                "deskew_angles": [],
            }
            if trigger_targeted:
                targeted_candidates = targeted_cell_candidates(
                    page,
                    bbox,
                    ink_density,
                )
                annotate_candidate_context(
                    targeted_candidates,
                    table_number,
                    column,
                )
                candidates.extend(targeted_candidates)
                selected, reason = select_numeric_candidate(candidates, ink_density)
                if (
                    selected["value_status"] == "extraction_error"
                ):
                    true_high_resolution_attempted = True
                    before_status = selected["value_status"]
                    high_resolution_candidates = targeted_cell_candidates(
                        page,
                        bbox,
                        ink_density,
                        true_high_resolution_dpi=TRUE_HIGH_RESOLUTION_DPI,
                    )
                    annotate_candidate_context(
                        high_resolution_candidates,
                        table_number,
                        column,
                    )
                    candidates.extend(high_resolution_candidates)
                    selected, reason = select_numeric_candidate(
                        candidates,
                        ink_density,
                    )
                    attempted_dpis = [TRUE_HIGH_RESOLUTION_DPI]
                    if (
                        selected["value_status"] == "extraction_error"
                        or (
                            locator_disagrees(candidates)
                            and float(
                                selected.get("ocr_confidence") or 0
                            )
                            < 50
                        )
                    ):
                        fallback_candidates = targeted_cell_candidates(
                            page,
                            bbox,
                            ink_density,
                            true_high_resolution_dpi=600,
                        )
                        annotate_candidate_context(
                            fallback_candidates,
                            table_number,
                            column,
                        )
                        candidates.extend(fallback_candidates)
                        high_resolution_candidates.extend(
                            fallback_candidates
                        )
                        attempted_dpis.append(600)
                        selected, reason = select_numeric_candidate(
                            candidates,
                            ink_density,
                        )
                    true_high_resolution_audit = {
                        "attempted": True,
                        "dpi": attempted_dpis,
                        "before_status": before_status,
                        "after_status": selected["value_status"],
                        "recovered": (
                            before_status == "extraction_error"
                            and selected["value_status"] == "reported"
                        ),
                        "candidates": high_resolution_candidates,
                        "rendered_page_paths": sorted(
                            {
                                candidate.get(
                                    "rendered_page_path",
                                    "",
                                )
                                for candidate in high_resolution_candidates
                                if candidate.get("rendered_page_path")
                            }
                        ),
                        "deskew_angles": sorted(
                            {
                                candidate.get(
                                    "high_resolution_deskew_angle"
                                )
                                for candidate in high_resolution_candidates
                                if candidate.get(
                                    "high_resolution_deskew_angle"
                                )
                                is not None
                            }
                        ),
                    }
            annotations = [
                candidate["annotation"]
                for candidate in candidates
                if candidate.get("annotation")
            ]
            selected["cell_annotation_raw"] = " ".join(
                dict.fromkeys(
                    [selected.get("cell_annotation_raw", "")] + annotations
                )
            ).strip()
            audit_cell = {
                "physical_cell_key": [
                    source_file,
                    page["page_number"],
                    table_instance_id,
                    row_index,
                    column_index,
                ],
                "table_number": table_number,
                "table_instance_id": table_instance_id,
                "row_index": row_index,
                "physical_row_center": date_row.get(
                    "physical_row_center",
                    date_row.get("y"),
                ),
                "physical_row_bounds": date_row.get(
                    "physical_row_bounds",
                    [round(cell_top, 3), round(cell_bottom, 3)],
                ),
                "row_label_raw": date_row.get("raw", ""),
                "matched_month_label_candidates": date_row.get(
                    "matched_month_label_candidates",
                    date_row.get("alternate_date_candidates", []),
                ),
                "row_date_candidates": date_row.get(
                    "alternate_date_candidates", []
                ),
                "observation_date": date_row["observation_date"],
                "observation_date_status": date_row[
                    "observation_date_status"
                ],
                "observation_date_source": date_row[
                    "observation_date_source"
                ],
                "column_index": column_index,
                "column_count": len(columns),
                "column_path": [
                    column["level_1"],
                    column["level_2"],
                    column["level_3"],
                ],
                "canonical_column": {
                    "deposit_type": column["deposit_type_canonical"],
                    "geography": column["geography_canonical"],
                    "customer_type": column["customer_type_canonical"],
                },
                "bbox": bbox,
                "ink_density": round(ink_density, 6),
                "targeted_cell_crop_attempted": trigger_targeted,
                "true_high_resolution_attempted": (
                    true_high_resolution_attempted
                ),
                "true_high_resolution": true_high_resolution_audit,
                "ocr_candidates": candidates,
            }
            row = {
                "era_id": era_id,
                "source_file": source_file,
                "release_date": release_date.isoformat(),
                "page_number": page["page_number"],
                "table_number": table_number,
                "table_instance_id": table_instance_id,
                "table_name_raw": table_name_raw,
                "units_raw": units_raw,
                "measure_canonical": {
                    1: "debits",
                    2: "average_deposits",
                    3: "turnover",
                }[table_number],
                "adjustment_status": (
                    column["adjustment"]
                    if column["adjustment"] in {"SA", "NSA"}
                    else "unknown"
                ),
                "observation_date": date_row["observation_date"],
                "observation_date_status": date_row[
                    "observation_date_status"
                ],
                "observation_date_source": date_row[
                    "observation_date_source"
                ],
                "row_index": row_index,
                "row_label_raw": date_row.get("raw", ""),
                "row_annotation_raw": date_row.get("row_annotation_raw", ""),
                "row_level_1_raw": str(date_row.get("resolved_year", "")),
                "row_level_2_raw": remove_footnote_marker(
                    date_row.get("month_raw", "")
                ),
                "column_level_1_raw": column["level_1"],
                "column_level_2_raw": column["level_2"],
                "column_level_3_raw": column["level_3"],
                "column_index": column_index,
                "column_count": len(columns),
                "cell_bbox": json.dumps(bbox, separators=(",", ":")),
                "page_classification": page_classification,
                "deposit_type_canonical": column[
                    "deposit_type_canonical"
                ],
                "geography_canonical": column["geography_canonical"],
                "customer_type_canonical": column[
                    "customer_type_canonical"
                ],
                "validation_flags": "[]",
                "cross_release_support_count": 0,
                "true_high_resolution_attempted": int(
                    true_high_resolution_attempted
                ),
                **selected,
                "_bbox": bbox,
                "_ink_density": ink_density,
                "_ocr_candidates": candidates,
                "_selection_reason": reason,
                "_targeted_attempted": trigger_targeted,
                "_true_high_resolution_attempted": (
                    true_high_resolution_attempted
                ),
                "_column_context": column,
                "_recognized_month_weight": date_row.get(
                    "recognized_month_weight",
                    0.0,
                ),
                "_audit_cell": audit_cell,
            }
            apply_selected_candidate(row, audit_cell, selected, reason)
            output.append(row)
            page_audit["cells"].append(audit_cell)
    return output


def metadata_record(era_id, source_file, release_date, page):
    lines = filtered_metadata(line_records(page["words"]))
    if not lines:
        lines = filtered_metadata(line_records(page.get("sparse_words", [])))
    text = "\n".join(line["text"] for line in lines)
    return {
        "era_id": era_id,
        "source_file": source_file,
        "release_date": release_date.isoformat(),
        "page_number": page["page_number"],
        "metadata_type": metadata_type(text),
        "text_raw": text,
        "ocr_confidence": (
            round(statistics.mean(line["confidence"] for line in lines), 2)
            if lines
            else 0.0
        ),
    }


def extract_pdf(pdf_path):
    release_date = release_date_from_name(pdf_path)
    era_id = era_for(release_date)
    source_file = (
        str(pdf_path.relative_to(INPUT_ROOT))
        if pdf_path.is_relative_to(INPUT_ROOT)
        else pdf_path.name
    )
    if era_id is None:
        return (
            [],
            [],
            [
                issue_row(
                    "",
                    source_file,
                    release_date.isoformat(),
                    "unassigned_era",
                    "Filename date is outside all era-map boundaries.",
                    severity="error",
                )
            ],
            [],
            [],
        )
    rows, metadata, issues, raw_pages, manifest = [], [], [], [], []
    pages = render_and_ocr(pdf_path)
    release_config = {
        **ERA_CONFIGS[era_id],
        "rows": expected_row_range(era_id, release_date),
    }
    printed_dates = set()
    for page in pages:
        image = Image.open(page["processed_image"]).convert("L")
        image_array = np.asarray(image)
        header = page_header_fields(page)
        if header["printed_release_date"]:
            printed_dates.add(date.fromisoformat(header["printed_release_date"]))
        title_lines = table_title_lines(page)
        page_status = page_adjustment(page)
        analyses = []
        for title_index, (target, title_line) in enumerate(title_lines):
            next_y = (
                title_lines[title_index + 1][1]["bbox"][1]
                if title_index + 1 < len(title_lines)
                else min(
                    page["height"] * 0.94,
                    title_line["bbox"][3] + page["height"] * 0.29,
                )
            )
            analyses.append(
                analyze_table_structure(
                    era_id,
                    release_config,
                    page,
                    image_array,
                    target,
                    title_line,
                    next_y,
                    release_date,
                    page_status,
                )
            )
        date_reconciliation = reconcile_page_table_dates(analyses)
        classification, classification_score, reason = classify_page(
            header,
            analyses,
            title_lines,
        )
        page_audit = {
            "pipeline_version": PIPELINE_VERSION,
            "era_id": era_id,
            "source_file": source_file,
            "release_date": release_date.isoformat(),
            "page_number": page["page_number"],
            "page_classification": classification,
            "classification_score": classification_score,
            "classification_reason": reason,
            "printed_release_code": header["printed_release_code"],
            "printed_release_title": header["printed_release_title"],
            "printed_release_date": header["printed_release_date"],
            "page_adjustment_status": page_status,
            "date_reconciliation": date_reconciliation,
            "rendered_image": page["processed_image"],
            "deskew_angle": page["deskew_angle"],
            "raw_text": page["raw_text"],
            "sparse_ocr_text": page.get("sparse_raw_text", ""),
            "embedded_locator_text": page.get("embedded_raw_text", ""),
            "mean_confidence": page["mean_confidence"],
            "words": page["words"],
            "sparse_ocr_words": page.get("sparse_words", []),
            "embedded_locator_words": page.get("embedded_words", []),
            "table_anchors": [
                {
                    "target": target,
                    "text": title_line["text"],
                    "bbox": title_line["bbox"],
                    "source": title_line["source"],
                    "alternatives": title_line.get("alternatives", []),
                }
                for target, title_line in title_lines
            ],
            "table_structure": [
                {
                    "table_number": analysis["table_number"],
                    "target": analysis["target"],
                    "valid": analysis["valid"],
                    "layout_variant": analysis["config"]["variant"],
                    "row_count": len(analysis["date_candidates"]),
                    "column_count": len(analysis["config"]["edges"]) - 1,
                    "represented_columns": analysis["represented_columns"],
                    "numeric_represented_columns": analysis.get(
                        "numeric_represented_columns",
                        0,
                    ),
                    "matched_edges": analysis["matched_edges"],
                    "edge_x_coordinates": [
                        round(value, 2) for value in analysis["edges"]
                    ],
                    "candidate_row_offsets": analysis.get(
                        "candidate_row_offsets",
                        [],
                    ),
                    "selected_row_offset": analysis.get(
                        "selected_row_offset",
                        0,
                    ),
                    "row_offset_score_margin": analysis.get(
                        "row_offset_score_margin",
                        0.0,
                    ),
                    "row_offset_selection_reason": analysis.get(
                        "row_offset_selection_reason",
                        "not evaluated",
                    ),
                    "row_offset_unresolved": analysis.get(
                        "row_offset_unresolved",
                        False,
                    ),
                    "evidence": analysis["evidence"],
                    "score": round(analysis["score"], 4),
                }
                for analysis in analyses
            ],
            "cells": [],
        }
        if classification == "table_page":
            for analysis in analyses:
                if not analysis["valid"]:
                    issues.append(
                        issue_row(
                            era_id,
                            source_file,
                            release_date.isoformat(),
                            "invalid_table_candidate",
                            (
                                f"{analysis['target']}: evidence={analysis['evidence']}; "
                                f"rows={len(analysis['date_candidates'])}; "
                                f"represented_columns={analysis['represented_columns']}."
                            ),
                            page_number=page["page_number"],
                            table_number=analysis["table_number"],
                            severity="error",
                        )
                    )
                    continue
                rows.extend(
                    extract_table_rows(
                        era_id,
                        source_file,
                        release_date,
                        page,
                        image_array,
                        analysis,
                        classification,
                        page_audit,
                        issues,
                    )
                )
            page_rows = [
                row
                for row in rows
                if row["source_file"] == source_file
                and row["page_number"] == page["page_number"]
            ]
            arithmetic_candidate_reconciliation(page_rows)
            targeted_retry_for_arithmetic(page_rows, page)
            arithmetic_candidate_reconciliation(page_rows)
            if len([analysis for analysis in analyses if analysis["valid"]]) < 3:
                issues.append(
                    issue_row(
                        era_id,
                        source_file,
                        release_date.isoformat(),
                        "incomplete_table_page",
                        (
                            f"Only {len([analysis for analysis in analyses if analysis['valid']])} "
                            "table instances independently passed structural checks."
                        ),
                        page_number=page["page_number"],
                    )
                )
            last_cell_bottom = max(
                (
                    cell["bbox"][3]
                    for cell in page_audit["cells"]
                ),
                default=page["height"] * 0.70,
            )
            footer_lines = filtered_metadata(
                line_records(
                    page["words"],
                    y_range=(
                        last_cell_bottom,
                        page["height"] * 0.97,
                    ),
                )
            )
            if footer_lines:
                footer_text = "\n".join(
                    line["text"] for line in footer_lines
                )
                metadata.append(
                    {
                        "era_id": era_id,
                        "source_file": source_file,
                        "release_date": release_date.isoformat(),
                        "page_number": page["page_number"],
                        "metadata_type": metadata_type(footer_text),
                        "text_raw": footer_text,
                        "ocr_confidence": round(
                            statistics.mean(
                                line["confidence"] for line in footer_lines
                            ),
                            2,
                        ),
                    }
                )
        else:
            metadata.append(
                metadata_record(
                    era_id,
                    source_file,
                    release_date,
                    page,
                )
            )
            if classification == "uncertain_page":
                issues.append(
                    issue_row(
                        era_id,
                        source_file,
                        release_date.isoformat(),
                        "uncertain_page_classification",
                        reason,
                        page_number=page["page_number"],
                        severity="error",
                    )
                )
            if header["conflicting_release"]:
                issues.append(
                    issue_row(
                        era_id,
                        source_file,
                        release_date.isoformat(),
                        "unexpected_release_code_conflict",
                        reason,
                        page_number=page["page_number"],
                    )
                )
        page_cells = [
            row
            for row in rows
            if row["source_file"] == source_file
            and row["page_number"] == page["page_number"]
        ]
        manifest.append(
            {
                "era_id": era_id,
                "source_file": source_file,
                "total_pages": len(pages),
                "page_number": page["page_number"],
                "printed_release_code": header["printed_release_code"],
                "printed_release_title": header["printed_release_title"],
                "printed_release_date": header["printed_release_date"],
                "page_adjustment_status": page_status,
                "direct_table_title_count": sum(
                    line.get("source") != "spatial_title_inference"
                    for _, line in title_lines
                ),
                "inferred_table_title_count": sum(
                    line.get("source") == "spatial_title_inference"
                    for _, line in title_lines
                ),
                "detected_month_row_count": max(
                    (len(analysis["date_candidates"]) for analysis in analyses),
                    default=0,
                ),
                "detected_numeric_column_count": max(
                    (
                        analysis["represented_columns"]
                        for analysis in analyses
                    ),
                    default=0,
                ),
                "cells_extracted": len(page_cells),
                "page_classification": classification,
                "classification_score": round(classification_score, 4),
                "classification_reason": reason,
            }
        )
        raw_pages.append(page_audit)
    if not printed_dates:
        issues.append(
            issue_row(
                era_id,
                source_file,
                release_date.isoformat(),
                "printed_release_date_not_found",
                "No printed release date could be located on any page.",
            )
        )
    if printed_dates and release_date not in printed_dates:
        issues.append(
            issue_row(
                era_id,
                source_file,
                release_date.isoformat(),
                "filename_printed_date_mismatch",
                (
                    f"Filename={release_date.isoformat()}, printed candidates="
                    f"{', '.join(item.isoformat() for item in sorted(printed_dates))}"
                ),
            )
        )
    return rows, metadata, issues, raw_pages, manifest


def numeric(row):
    try:
        return float(row["value_numeric"])
    except (TypeError, ValueError):
        return None


def column_path(row):
    return " > ".join(
        part
        for part in (
            row["column_level_1_raw"],
            row["column_level_2_raw"],
            row["column_level_3_raw"],
        )
        if part
    )


def add_validation_flag(rows, flag):
    for row in rows:
        row.setdefault("_validation_flags", set()).add(flag)


def page_date_diagnostics(rows, issues):
    grouped = defaultdict(list)
    for row in rows:
        grouped[(row["source_file"], int(row["page_number"]))].append(row)
    for page_rows in grouped.values():
        first = page_rows[0]
        release = date.fromisoformat(first["release_date"])
        dated = [
            row for row in page_rows if row.get("observation_date")
        ]
        if not dated:
            continue
        dates = [date.fromisoformat(row["observation_date"]) for row in dated]
        future = [row for row in dated if date.fromisoformat(row["observation_date"]) > release]
        if future:
            issues.append(
                issue_row(
                    first["era_id"],
                    first["source_file"],
                    first["release_date"],
                    "observation_after_release",
                    f"{len(future)} cells have observation dates after the release date.",
                    page_number=first["page_number"],
                    severity="error",
                )
            )
            add_validation_flag(future, "observation_after_release")
        latest = max(dates)
        lag = (release.year - latest.year) * 12 + release.month - latest.month
        if lag > MAX_UNCORROBORATED_YEAR_DISTANCE_MONTHS:
            anchor_rows = defaultdict(set)
            for row in dated:
                expected_year = date.fromisoformat(row["observation_date"]).year
                candidates = row.get("_audit_cell", {}).get(
                    "matched_month_label_candidates", []
                )
                if any(
                    year.get("year") == expected_year
                    for candidate in candidates
                    for year in candidate.get("year_candidates", [])
                ):
                    anchor_rows[int(row["table_number"])].add(
                        int(row["row_index"])
                    )
            support = {
                table_number: len(anchor_rows[table_number])
                for table_number in (1, 2, 3)
            }
            corroborated = min(support.values(), default=0) >= MIN_HISTORICAL_YEAR_ANCHOR_ROWS
            issue_type = (
                "historical_backdata_window"
                if corroborated
                else "implausibly_old_page_window"
            )
            issues.append(
                issue_row(
                    first["era_id"],
                    first["source_file"],
                    first["release_date"],
                    issue_type,
                    (
                        f"Page window={min(dates).isoformat()}..{latest.isoformat()}; "
                        f"release lag={lag} months; matching anchor rows={support}."
                    ),
                    page_number=first["page_number"],
                    severity="warning" if corroborated else "error",
                )
            )
            add_validation_flag(page_rows, issue_type)
        table_windows = {
            table_number: (
                min(table_dates).isoformat(),
                max(table_dates).isoformat(),
                len(table_dates),
            )
            for table_number in (1, 2, 3)
            if (
                table_dates := {
                    date.fromisoformat(row["observation_date"])
                    for row in dated
                    if int(row["table_number"]) == table_number
                }
            )
        }
        if len(set(table_windows.values())) > 1:
            issues.append(
                issue_row(
                    first["era_id"],
                    first["source_file"],
                    first["release_date"],
                    "page_table_date_window_disagreement",
                    f"Table windows disagree: {table_windows}.",
                    page_number=first["page_number"],
                    severity="error",
                )
            )
            add_validation_flag(page_rows, "page_table_date_window_disagreement")
        early_mmda = [
            row
            for row in dated
            if row["deposit_type_canonical"] == "mmda"
            and row["observation_date"] < "1982-01-01"
        ]
        if early_mmda:
            issues.append(
                issue_row(
                    first["era_id"],
                    first["source_file"],
                    first["release_date"],
                    "mmda_before_supported_observation_window",
                    f"{len(early_mmda)} MMDA cells predate 1982-01.",
                    page_number=first["page_number"],
                    severity="error",
                )
            )
            add_validation_flag(
                early_mmda,
                "mmda_before_supported_observation_window",
            )
        era_mismatches = [
            row
            for row in page_rows
            if int(row["era_id"]) <= 2
            and (
                (
                    row["deposit_type_canonical"] == "demand"
                    and row["adjustment_status"] != "SA"
                )
                or (
                    row["deposit_type_canonical"] == "savings"
                    and row["adjustment_status"] != "NSA"
                )
            )
        ]
        if era_mismatches:
            issues.append(
                issue_row(
                    first["era_id"],
                    first["source_file"],
                    first["release_date"],
                    "era_adjustment_category_mismatch",
                    f"{len(era_mismatches)} Era 1/2 cells violate demand-SA/savings-NSA structure.",
                    page_number=first["page_number"],
                    severity="error",
                )
            )
            add_validation_flag(
                era_mismatches,
                "era_adjustment_category_mismatch",
            )


def validate(rows, issues, manifest, raw_pages=None):
    seen = {}
    for row in rows:
        key = (
            row["source_file"],
            row["page_number"],
            row["table_instance_id"],
            row["row_index"],
            row["column_index"],
        )
        if key in seen:
            issues.append(
                issue_row(
                    row["era_id"],
                    row["source_file"],
                    row["release_date"],
                    "duplicate_physical_cell_key",
                    f"Duplicate physical key={key}.",
                    page_number=row["page_number"],
                    table_number=row["table_number"],
                    observation_date=row["observation_date"],
                    column_path=column_path(row),
                    severity="error",
                )
            )
        seen[key] = row
        if (
            row["value_status"] == "extraction_error"
            and not row.get("_ocr_candidates")
        ):
            issues.append(
                issue_row(
                    row["era_id"],
                    row["source_file"],
                    row["release_date"],
                    "missing_ocr_candidate_audit",
                    "Unresolved cell has no retained OCR candidates.",
                    page_number=row["page_number"],
                    table_number=row["table_number"],
                    observation_date=row["observation_date"],
                    column_path=column_path(row),
                    severity="error",
                )
            )
    manifest_lookup = {
        (item["source_file"], int(item["page_number"])): item for item in manifest
    }
    for item in manifest:
        page_rows = [
            row
            for row in rows
            if row["source_file"] == item["source_file"]
            and row["page_number"] == int(item["page_number"])
        ]
        if (
            item["page_classification"]
            in {"metadata_page", "unrelated_release_page", "uncertain_page"}
            and page_rows
        ):
            first = page_rows[0]
            issues.append(
                issue_row(
                    first["era_id"],
                    first["source_file"],
                    first["release_date"],
                    "non_table_page_emitted_cells",
                    (
                        f"{item['page_classification']} emitted "
                        f"{len(page_rows)} observations."
                    ),
                    page_number=first["page_number"],
                    severity="error",
                )
            )
        if item["page_classification"] == "table_page":
            instances = {
                row["table_instance_id"] for row in page_rows
            }
            if len(instances) != 3:
                first = page_rows[0] if page_rows else None
                issues.append(
                    issue_row(
                        first["era_id"] if first else item["era_id"],
                        item["source_file"],
                        first["release_date"] if first else "",
                        "expected_table_instances_per_page",
                        f"Classified table page has {len(instances)} table instances; expected 3.",
                        page_number=item["page_number"],
                        severity="error",
                    )
                )
            if not page_rows:
                issues.append(
                    issue_row(
                        item["era_id"],
                        item["source_file"],
                        "",
                        "table_page_without_cells",
                        "A classified table page emitted zero observations.",
                        page_number=item["page_number"],
                        severity="error",
                    )
                )
    by_instance = defaultdict(list)
    for row in rows:
        by_instance[
            (
                row["source_file"],
                row["page_number"],
                row["table_instance_id"],
            )
        ].append(row)
    for _, instance_rows in by_instance.items():
        first = instance_rows[0]
        expected_count = int(first["column_count"])
        represented = {int(row["column_index"]) for row in instance_rows}
        if represented != set(range(expected_count)):
            issues.append(
                issue_row(
                    first["era_id"],
                    first["source_file"],
                    first["release_date"],
                    "expected_physical_columns_missing",
                    (
                        f"Represented columns={sorted(represented)}; "
                        f"expected={list(range(expected_count))}."
                    ),
                    page_number=first["page_number"],
                    table_number=first["table_number"],
                    severity="error",
                )
            )
        date_rows_by_index = {
            int(row["row_index"]): row
            for row in instance_rows
            if int(row["column_index"]) == 0
        }
        ordered = [date_rows_by_index[index] for index in sorted(date_rows_by_index)]
        missing_date_rows = [
            int(row["row_index"])
            for row in ordered
            if not row["observation_date"]
        ]
        if missing_date_rows:
            issues.append(
                issue_row(
                    first["era_id"],
                    first["source_file"],
                    first["release_date"],
                    "observation_month_discontinuity",
                    (
                        "Complete ordered date sequence is unresolved at rows "
                        f"{missing_date_rows}."
                    ),
                    page_number=first["page_number"],
                    table_number=first["table_number"],
                    severity="error",
                )
            )
            continue
        for previous, current in zip(ordered, ordered[1:]):
            previous_date = date.fromisoformat(previous["observation_date"])
            current_date = date.fromisoformat(current["observation_date"])
            expected = date(
                previous_date.year + (previous_date.month == 12),
                previous_date.month % 12 + 1,
                1,
            )
            if current_date != expected:
                issues.append(
                    issue_row(
                        first["era_id"],
                        first["source_file"],
                        first["release_date"],
                        "observation_month_discontinuity",
                        (
                            f"Rows {previous['row_index']} and {current['row_index']}: "
                            f"{previous_date.isoformat()} -> {current_date.isoformat()}."
                        ),
                        page_number=first["page_number"],
                        table_number=first["table_number"],
                        severity="error",
                    )
                )
                break
    grouped = defaultdict(list)
    for row in rows:
        grouped[
            (
                row["source_file"],
                row["page_number"],
                row["table_instance_id"],
                row["row_index"],
            )
        ].append(row)
    for group_rows in grouped.values():
        first = group_rows[0]
        by_geo = {
            row["geography_canonical"]: row
            for row in group_rows
            if row["deposit_type_canonical"] == "demand"
        }
        if first["table_number"] in {1, 2} and {
            "all_banks",
            "new_york_city",
            "other_banks",
        } <= set(by_geo):
            trio = [
                by_geo["all_banks"],
                by_geo["new_york_city"],
                by_geo["other_banks"],
            ]
            values = [numeric(row) for row in trio]
            if all(value is not None for value in values):
                difference = abs(values[0] - values[1] - values[2])
                tolerance = ADDITIVE_ROUNDING_TOLERANCE
                if difference > tolerance:
                    add_validation_flag(
                        trio,
                        "all_banks_component_check",
                    )
                    issues.append(
                        issue_row(
                            first["era_id"],
                            first["source_file"],
                            first["release_date"],
                            "all_banks_component_check",
                            (
                                f"All banks differs from New York City + other banks "
                                f"by {difference:g}; tolerance={tolerance:g}."
                            ),
                            page_number=first["page_number"],
                            table_number=first["table_number"],
                            observation_date=first["observation_date"],
                        )
                    )
        if first["table_number"] in {1, 2}:
            customer_columns = {
                row["customer_type_canonical"]: row
                for row in group_rows
                if row["customer_type_canonical"]
                and not row["geography_canonical"]
            }
            required = (
                {"total", "ats_now", "business", "other"}
                if int(first["era_id"]) == 2
                else {"total", "business", "other"}
                if int(first["era_id"]) == 1
                else set()
            )
            if required and not required <= set(customer_columns):
                add_validation_flag(
                    group_rows,
                    "component_mapping_incomplete",
                )
                issues.append(
                    issue_row(
                        first["era_id"],
                        first["source_file"],
                        first["release_date"],
                        "component_mapping_incomplete",
                        (
                            f"Required canonical components={sorted(required)}; "
                            f"observed={sorted(customer_columns)}."
                        ),
                        page_number=first["page_number"],
                        table_number=first["table_number"],
                        observation_date=first["observation_date"],
                    )
                )
            elif required:
                component_order = [
                    name for name in ("ats_now", "business", "other")
                    if name in required
                ]
                total = customer_columns["total"]
                components = [
                    customer_columns[name] for name in component_order
                ]
                values = [numeric(total)] + [
                    numeric(row) for row in components
                ]
                if all(value is not None for value in values):
                    difference = abs(values[0] - sum(values[1:]))
                    tolerance = ADDITIVE_ROUNDING_TOLERANCE
                    if difference > tolerance:
                        add_validation_flag(
                            [total] + components,
                            "component_total_check",
                        )
                        issues.append(
                            issue_row(
                                first["era_id"],
                                first["source_file"],
                                first["release_date"],
                                "component_total_check",
                                (
                                    f"Printed total differs from components by "
                                    f"{difference:g}; tolerance={tolerance:g}."
                                ),
                                page_number=first["page_number"],
                                table_number=first["table_number"],
                                observation_date=first["observation_date"],
                            )
                        )
    lookup = {
        (
            row["source_file"],
            row["page_number"],
            row["adjustment_status"],
            row["row_index"],
            row["column_index"],
            row["table_number"],
        ): row
        for row in rows
    }
    for key, turnover in list(lookup.items()):
        if key[-1] != 3:
            continue
        debit = lookup.get(key[:-1] + (1,))
        deposit = lookup.get(key[:-1] + (2,))
        values = (
            numeric(debit) if debit else None,
            numeric(deposit) if deposit else None,
            numeric(turnover),
        )
        if all(value is not None for value in values) and values[1] != 0:
            implied = values[0] / values[1]
            tolerance = turnover_rounding_tolerance(
                values[0],
                values[1],
            )
            if abs(implied - values[2]) > tolerance:
                add_validation_flag(
                    [debit, deposit, turnover],
                    "turnover_ratio_check",
                )
                issues.append(
                    issue_row(
                        turnover["era_id"],
                        turnover["source_file"],
                        turnover["release_date"],
                        "turnover_ratio_check",
                        (
                            f"Reported={values[2]:g}, debits/deposits={implied:.2f}, "
                            f"tolerance={tolerance:.2f}."
                        ),
                        page_number=turnover["page_number"],
                        table_number=3,
                        observation_date=turnover["observation_date"],
                        column_path=column_path(turnover),
                    )
                )
    overlaps = defaultdict(list)
    for row in rows:
        if not row["observation_date"]:
            continue
        overlaps[
            (
                row["source_file"],
                row["table_number"],
                row["adjustment_status"],
                row["observation_date"],
                row["deposit_type_canonical"],
                row["geography_canonical"],
                row["customer_type_canonical"],
            )
        ].append(row)
    for overlap_rows in overlaps.values():
        pages = {row["page_number"] for row in overlap_rows}
        if len(pages) <= 1:
            continue
        first = overlap_rows[0]
        distinct_values = {
            row["value_numeric"]
            for row in overlap_rows
            if row["value_status"] == "reported"
        }
        issues.append(
            issue_row(
                first["era_id"],
                first["source_file"],
                first["release_date"],
                "overlapping_release_vintage",
                (
                    f"Same logical observation printed on pages {sorted(pages)}; "
                    f"values={sorted(distinct_values)}. Physical records retained."
                ),
                observation_date=first["observation_date"],
                column_path=column_path(first),
            )
        )
    by_release_status = defaultdict(set)
    for item in manifest:
        if item["page_classification"] == "table_page":
            by_release_status[item["source_file"]].add(
                item["page_adjustment_status"]
            )
    release_rows = defaultdict(list)
    for row in rows:
        release_rows[row["source_file"]].append(row)
    for source_file, file_rows in release_rows.items():
        first = file_rows[0]
        if first["era_id"] >= 3 and not {"SA", "NSA"} <= by_release_status[source_file]:
            issues.append(
                issue_row(
                    first["era_id"],
                    source_file,
                    first["release_date"],
                    "missing_sa_or_nsa_page_warning",
                    (
                        f"Classified table-page statuses="
                        f"{sorted(by_release_status[source_file])}; expected SA and NSA."
                    ),
                )
            )
        if "corrected" in source_file.lower():
            annotations = {
                marker
                for row in file_rows
                for marker in (
                    row["row_annotation_raw"],
                    row["cell_annotation_raw"],
                )
                if marker
            }
            if not any("c" in marker.lower() for marker in annotations):
                issues.append(
                    issue_row(
                        first["era_id"],
                        source_file,
                        first["release_date"],
                        "corrected_marker_not_preserved",
                        "Corrected-copy filename has no preserved C row/cell annotation.",
                        severity="error",
                    )
                )
    page_date_diagnostics(rows, issues)
    return issues


def write_csv_atomic(path, rows, fieldnames):
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    temporary.replace(path)


def safe_extract(pdf_path):
    try:
        return extract_pdf(pdf_path)
    except Exception as error:
        try:
            release_date = release_date_from_name(pdf_path)
            release_date_text = release_date.isoformat()
            era_id = era_for(release_date) or ""
        except ValueError:
            release_date_text = ""
            era_id = ""
        source_file = (
            str(pdf_path.relative_to(INPUT_ROOT))
            if pdf_path.is_relative_to(INPUT_ROOT)
            else pdf_path.name
        )
        return (
            [],
            [],
            [
                issue_row(
                    era_id,
                    source_file,
                    release_date_text,
                    "file_processing_error",
                    f"{type(error).__name__}: {error}",
                    severity="error",
                )
            ],
            [],
            [],
        )


FINAL_REBUILT_ISSUE_TYPES = {
    "all_banks_component_check",
    "cell_extraction_error",
    "component_mapping_incomplete",
    "component_total_check",
    "date_alignment_error",
    "date_reconciled_by_page_consensus",
    "duplicate_physical_cell_key",
    "embedded_only_numeric_candidate",
    "expected_physical_columns_missing",
    "expected_table_instances_per_page",
    "missing_ocr_candidate_audit",
    "missing_sa_or_nsa_page_warning",
    "non_canonical_reported_value",
    "non_table_page_emitted_cells",
    "observation_month_discontinuity",
    "observation_month_inferred",
    "ocr_candidate_conflict",
    "overlapping_release_vintage",
    "reported_value_without_eligible_image_candidate",
    "selected_embedded_locator",
    "table_page_without_cells",
    "table_row_offset_unresolved",
    "turnover_ratio_check",
    "turnover_row_shift_signal",
    "unsupported_numeric_normalization",
}


def physical_cell_key(row):
    return (
        row["source_file"],
        int(row["page_number"]),
        row["table_instance_id"],
        int(row["row_index"]),
        int(row["column_index"]),
    )


def candidate_matches_final_value(row, candidate):
    return (
        candidate.get("eligible", True)
        and candidate.get("value_status") == "reported"
        and candidate.get("value_numeric") == row.get("value_numeric")
        and candidate.get("source") == row.get("selected_source")
        and CANONICAL_NUMERIC_RE.fullmatch(
            candidate.get("value_numeric", "")
        )
    )


def cross_release_reconcile(rows):
    grouped = defaultdict(list)
    for row in rows:
        if not row.get("observation_date"):
            continue
        grouped[
            (
                row["observation_date"],
                row["adjustment_status"],
                row["measure_canonical"],
                row["deposit_type_canonical"],
                row["geography_canonical"],
                row["customer_type_canonical"],
            )
        ].append(row)
    for logical_rows in grouped.values():
        reported_neighbors = [
            row
            for row in logical_rows
            if row["value_status"] == "reported"
            and CANONICAL_NUMERIC_RE.fullmatch(
                row.get("value_numeric", "")
            )
            and row.get("selected_source") != "embedded_locator"
        ]
        for row in logical_rows:
            release = date.fromisoformat(row["release_date"])
            nearby = [
                neighbor
                for neighbor in reported_neighbors
                if neighbor["source_file"] != row["source_file"]
                and abs(
                    (
                        date.fromisoformat(neighbor["release_date"])
                        - release
                    ).days
                )
                <= 240
            ]
            adjacent_values = [
                {
                    "source_file": neighbor["source_file"],
                    "release_date": neighbor["release_date"],
                    "page_number": neighbor["page_number"],
                    "value_numeric": neighbor["value_numeric"],
                    "selected_source": neighbor.get(
                        "selected_source",
                        "",
                    ),
                }
                for neighbor in nearby
            ]
            row["_audit_cell"]["adjacent_release_values"] = (
                adjacent_values
            )
            support = Counter(
                (
                    neighbor["value_numeric"],
                    neighbor["source_file"],
                )
                for neighbor in nearby
            )
            support_by_value = Counter()
            for value, source_file in support:
                support_by_value[value] += 1
            row["cross_release_support_count"] = support_by_value.get(
                row.get("value_numeric", ""),
                0,
            )
            options = reported_candidate_options(row, limit=20)
            supported_options = [
                option
                for option in options
                if support_by_value[option["candidate"]["value_numeric"]]
                >= 2
            ]
            if (
                row["value_status"] == "extraction_error"
                and supported_options
            ):
                selected_option = max(
                    supported_options,
                    key=lambda option: (
                        support_by_value[
                            option["candidate"]["value_numeric"]
                        ],
                        option["score"],
                    ),
                )
                candidate = selected_option["candidate"]
                support_count = support_by_value[
                    candidate["value_numeric"]
                ]
                selected = {
                    "value_raw": candidate["raw"],
                    "value_numeric": candidate["value_numeric"],
                    "value_status": "reported",
                    "ocr_confidence": candidate["confidence"],
                    "cell_annotation_raw": candidate.get(
                        "annotation",
                        "",
                    ),
                    "selected_source": candidate["source"],
                    "normalization_rule": candidate["normalization"],
                }
                reason = (
                    "selected eligible image-derived OCR candidate with "
                    f"{support_count} agreeing nearby release vintages; "
                    "cross-release evidence used only as a tie-breaker"
                )
                apply_selected_candidate(
                    row,
                    row["_audit_cell"],
                    selected,
                    reason,
                )
                row["cross_release_support_count"] = support_count
                row["_audit_cell"]["cross_release_selection"] = {
                    "support_count": support_count,
                    "candidate": candidate,
                    "neighboring_release_values": adjacent_values,
                }


def finalize_row_provenance(rows):
    demoted = 0
    for row in rows:
        row.setdefault("selection_reason", row.get("_selection_reason", ""))
        row.setdefault("normalization_rule", "")
        row.setdefault("cross_release_support_count", 0)
        row.setdefault("true_high_resolution_attempted", 0)
        row.setdefault("_validation_flags", set())
        if row["value_status"] == "reported":
            invalid_reason = ""
            if row.get("selected_source") == "embedded_locator":
                invalid_reason = "embedded locator cannot be a final source"
            elif not CANONICAL_NUMERIC_RE.fullmatch(
                row.get("value_numeric", "")
            ):
                invalid_reason = "final value violates one-decimal grammar"
            elif not any(
                candidate_matches_final_value(row, candidate)
                for candidate in row.get("_ocr_candidates", [])
            ):
                invalid_reason = (
                    "final value lacks an eligible image-derived candidate"
                )
            if invalid_reason:
                demoted += 1
                row["_audit_cell"]["demoted_final_candidate"] = {
                    "value_raw": row.get("value_raw", ""),
                    "value_numeric": row.get("value_numeric", ""),
                    "selected_source": row.get("selected_source", ""),
                    "normalization_rule": row.get(
                        "normalization_rule",
                        "",
                    ),
                    "reason": invalid_reason,
                }
                row["value_numeric"] = ""
                row["value_status"] = "extraction_error"
                row["selection_reason"] = (
                    f"demoted after final provenance audit: {invalid_reason}"
                )
                row["_selection_reason"] = row["selection_reason"]
                row["selected_source"] = "none"
                row["normalization_rule"] = ""
        row["_audit_cell"].update(
            {
                "value_raw": row.get("value_raw", ""),
                "value_numeric": row.get("value_numeric", ""),
                "value_status": row.get("value_status", ""),
                "selected_source": row.get("selected_source", ""),
                "selection_reason": row.get("selection_reason", ""),
                "normalization_rule": row.get(
                    "normalization_rule",
                    "",
                ),
                "cross_release_support_count": row.get(
                    "cross_release_support_count",
                    0,
                ),
                "true_high_resolution_attempted": bool(
                    row.get("true_high_resolution_attempted")
                ),
                "ocr_candidates": row.get("_ocr_candidates", []),
            }
        )
    return demoted


def turnover_row_shift_signals(rows):
    series = defaultdict(lambda: defaultdict(dict))
    for row in rows:
        if not row.get("observation_date"):
            continue
        series_key = (
            row["source_file"],
            int(row["page_number"]),
            row["adjustment_status"],
            row["deposit_type_canonical"],
            row["geography_canonical"],
            row["customer_type_canonical"],
            int(row["column_index"]),
        )
        series[series_key][int(row["table_number"])][
            int(row["row_index"])
        ] = row
    comparable_columns = defaultdict(set)
    strong_signals = []
    for key, tables in series.items():
        if not {1, 2, 3} <= set(tables):
            continue
        summaries = {}
        for shift in (-1, 0, 1):
            normalized_residuals = []
            passing = 0
            for turnover_index, turnover in tables[3].items():
                source_index = turnover_index + shift
                debit = tables[1].get(source_index)
                deposit = tables[2].get(source_index)
                values = (
                    numeric(debit) if debit else None,
                    numeric(deposit) if deposit else None,
                    numeric(turnover),
                )
                if (
                    any(value is None for value in values)
                    or values[1] == 0
                ):
                    continue
                residual = abs(values[0] / values[1] - values[2])
                tolerance = turnover_rounding_tolerance(
                    values[0],
                    values[1],
                )
                normalized_residuals.append(residual / tolerance)
                passing += residual <= tolerance
            summaries[shift] = {
                "comparisons": len(normalized_residuals),
                "passing": passing,
                "median_normalized_residual": (
                    statistics.median(normalized_residuals)
                    if normalized_residuals
                    else math.inf
                ),
            }
        page_key = key[:3]
        if summaries[0]["comparisons"] >= 6:
            comparable_columns[page_key].add(key[6])
        zero = summaries[0]
        best_shift = min(
            (-1, 1),
            key=lambda shift: summaries[shift][
                "median_normalized_residual"
            ],
        )
        shifted = summaries[best_shift]
        strong = (
            shifted["comparisons"] >= 6
            and shifted["median_normalized_residual"] <= 1.5
            and shifted["median_normalized_residual"]
            < zero["median_normalized_residual"] * 0.40
            and shifted["passing"] >= zero["passing"] + 4
        )
        if strong:
            strong_signals.append(
                {
                    "source_file": key[0],
                    "page_number": key[1],
                    "adjustment_status": key[2],
                    "deposit_type_canonical": key[3],
                    "geography_canonical": key[4],
                    "customer_type_canonical": key[5],
                    "column_index": key[6],
                    "best_shift": best_shift,
                    "summaries": summaries,
                }
            )
    grouped = defaultdict(list)
    for signal in strong_signals:
        grouped[
            (
                signal["source_file"],
                signal["page_number"],
                signal["adjustment_status"],
                signal["best_shift"],
            )
        ].append(signal)
    signals = []
    for group_key, members in grouped.items():
        page_key = group_key[:3]
        shifted_columns = {
            signal["column_index"] for signal in members
        }
        available_columns = comparable_columns.get(page_key, set())
        if (
            len(shifted_columns) < 3
            or len(shifted_columns) * 2 < len(available_columns)
        ):
            continue
        signals.extend(members)
    return signals


def rebuild_final_issues(rows, base_issues, manifest, raw_pages):
    issues = [
        issue
        for issue in base_issues
        if issue["issue_type"] not in FINAL_REBUILT_ISSUE_TYPES
    ]
    for row in rows:
        row["_validation_flags"] = set()
    raw_lookup = {
        (page["source_file"], int(page["page_number"])): page
        for page in raw_pages
    }
    for page in raw_pages:
        for structure in page.get("table_structure", []):
            if structure.get("row_offset_unresolved"):
                issues.append(
                    issue_row(
                        page["era_id"],
                        page["source_file"],
                        page["release_date"],
                        "table_row_offset_unresolved",
                        json.dumps(
                            {
                                "table_number": structure[
                                    "table_number"
                                ],
                                "candidate_row_offsets": structure.get(
                                    "candidate_row_offsets",
                                    [],
                                ),
                                "selection_reason": structure.get(
                                    "row_offset_selection_reason",
                                    "",
                                ),
                            },
                            sort_keys=True,
                        ),
                        page_number=page["page_number"],
                        table_number=structure["table_number"],
                        severity="error",
                    )
                )
                involved = [
                    row
                    for row in rows
                    if row["source_file"] == page["source_file"]
                    and int(row["page_number"])
                    == int(page["page_number"])
                    and int(row["table_number"])
                    == int(structure["table_number"])
                ]
                add_validation_flag(
                    involved,
                    "table_row_offset_unresolved",
                )
    validate(rows, issues, manifest, raw_pages=raw_pages)
    for row in rows:
        candidates = row.get("_ocr_candidates", [])
        eligible_values = {
            candidate["value_numeric"]
            for candidate in candidates
            if candidate.get("eligible", True)
            and candidate["value_status"] == "reported"
            and CANONICAL_NUMERIC_RE.fullmatch(
                candidate.get("value_numeric", "")
            )
        }
        embedded_values = {
            candidate["value_numeric"]
            for candidate in candidates
            if not candidate.get("eligible", True)
            and candidate["value_status"] == "reported"
            and CANONICAL_NUMERIC_RE.fullmatch(
                candidate.get("value_numeric", "")
            )
        }
        if len(eligible_values) > 1:
            issues.append(
                issue_row(
                    row["era_id"],
                    row["source_file"],
                    row["release_date"],
                    "ocr_candidate_conflict",
                    (
                        f"Final eligible candidates={sorted(eligible_values)}; "
                        f"selected={row.get('value_numeric', '')!r}; "
                        f"selection={row.get('selection_reason', '')}"
                    ),
                    page_number=row["page_number"],
                    table_number=row["table_number"],
                    observation_date=row["observation_date"],
                    column_path=column_path(row),
                )
            )
            add_validation_flag([row], "ocr_candidate_conflict")
        if embedded_values and not eligible_values:
            issues.append(
                issue_row(
                    row["era_id"],
                    row["source_file"],
                    row["release_date"],
                    "embedded_only_numeric_candidate",
                    (
                        "Embedded OCR contains numeric locator evidence "
                        f"{sorted(embedded_values)}, but no eligible image "
                        "candidate supports a final value."
                    ),
                    page_number=row["page_number"],
                    table_number=row["table_number"],
                    observation_date=row["observation_date"],
                    column_path=column_path(row),
                )
            )
            add_validation_flag(
                [row],
                "embedded_only_numeric_candidate",
            )
        if row["value_status"] == "extraction_error":
            issues.append(
                issue_row(
                    row["era_id"],
                    row["source_file"],
                    row["release_date"],
                    "cell_extraction_error",
                    (
                        f"Final unresolved OCR={row['value_raw']!r}; "
                        f"selection={row.get('selection_reason', '')}"
                    ),
                    page_number=row["page_number"],
                    table_number=row["table_number"],
                    observation_date=row["observation_date"],
                    column_path=column_path(row),
                )
            )
        if row["observation_date_status"] == "date_alignment_error":
            issues.append(
                issue_row(
                    row["era_id"],
                    row["source_file"],
                    row["release_date"],
                    "date_alignment_error",
                    row.get("observation_date_source", ""),
                    page_number=row["page_number"],
                    table_number=row["table_number"],
                    column_path=column_path(row),
                    severity="error",
                )
            )
            add_validation_flag([row], "date_alignment_error")
        flags = sorted(row.get("_validation_flags", set()))
        row["validation_flags"] = json.dumps(
            flags,
            separators=(",", ":"),
        )
        row["_audit_cell"]["validation_flags"] = flags
    shift_signals = turnover_row_shift_signals(rows)
    for signal in shift_signals:
        page = raw_lookup.get(
            (signal["source_file"], signal["page_number"])
        )
        if page is not None:
            page.setdefault("turnover_row_shift_signals", []).append(
                signal
            )
        involved = [
            row
            for row in rows
            if row["source_file"] == signal["source_file"]
            and int(row["page_number"]) == signal["page_number"]
            and int(row["column_index"]) == signal["column_index"]
        ]
        add_validation_flag(involved, "turnover_row_shift_signal")
        issues.append(
            issue_row(
                involved[0]["era_id"] if involved else "",
                signal["source_file"],
                involved[0]["release_date"] if involved else "",
                "turnover_row_shift_signal",
                json.dumps(signal, sort_keys=True),
                page_number=signal["page_number"],
                severity="error",
            )
        )
    for row in rows:
        flags = sorted(row.get("_validation_flags", set()))
        row["validation_flags"] = json.dumps(
            flags,
            separators=(",", ":"),
        )
        row["_audit_cell"]["validation_flags"] = flags
    return issues


def manual_review_queue(rows):
    queue = []
    arithmetic_flags = {
        "all_banks_component_check",
        "component_total_check",
        "turnover_ratio_check",
    }
    for row in rows:
        flags = set(row.get("_validation_flags", set()))
        candidates = row.get("_ocr_candidates", [])
        embedded_only = (
            any(
                not candidate.get("eligible", True)
                and candidate["value_status"] == "reported"
                for candidate in candidates
            )
            and not any(
                candidate.get("eligible", True)
                and candidate["value_status"] == "reported"
                and CANONICAL_NUMERIC_RE.fullmatch(
                    candidate.get("value_numeric", "")
                )
                for candidate in candidates
            )
        )
        unsupported_normalization = (
            row["value_status"] == "reported"
            and not any(
                candidate_matches_final_value(row, candidate)
                for candidate in candidates
            )
        )
        reasons = set()
        if row["value_status"] == "extraction_error":
            reasons.add("extraction_error")
        reasons.update(flags & arithmetic_flags)
        if "date_alignment_error" in flags:
            reasons.add("unresolved_date_alignment")
        if "table_row_offset_unresolved" in flags:
            reasons.add("uncertain_row_offset")
        if unsupported_normalization:
            reasons.add("unsupported_numeric_normalization")
        if embedded_only:
            reasons.add("embedded_only_numeric_candidate")
        if not reasons:
            continue
        numeric_candidates = [
            candidate
            for candidate in candidates
            if candidate["value_status"] == "reported"
        ]
        high_resolution_candidates = [
            candidate
            for candidate in numeric_candidates
            if candidate["source"].startswith(
                "true_high_resolution_"
            )
        ]
        suggested = (
            max(
                [
                    candidate
                    for candidate in numeric_candidates
                    if candidate.get("eligible", True)
                    and CANONICAL_NUMERIC_RE.fullmatch(
                        candidate.get("value_numeric", "")
                    )
                ],
                key=numeric_candidate_score,
                default=None,
            )
        )
        queue.append(
            {
                "physical_cell_key": json.dumps(
                    physical_cell_key(row),
                    separators=(",", ":"),
                ),
                "source_file": row["source_file"],
                "release_date": row["release_date"],
                "page_number": row["page_number"],
                "table_number": row["table_number"],
                "table_instance_id": row["table_instance_id"],
                "adjustment_status": row["adjustment_status"],
                "observation_date": row["observation_date"],
                "measure_canonical": row["measure_canonical"],
                "deposit_type_canonical": row[
                    "deposit_type_canonical"
                ],
                "geography_canonical": row[
                    "geography_canonical"
                ],
                "customer_type_canonical": row[
                    "customer_type_canonical"
                ],
                "row_index": row["row_index"],
                "column_index": row["column_index"],
                "cell_bbox": row["cell_bbox"],
                "value_raw": row["value_raw"],
                "value_numeric": row["value_numeric"],
                "value_status": row["value_status"],
                "selected_source": row.get("selected_source", ""),
                "normalization_rule": row.get(
                    "normalization_rule",
                    "",
                ),
                "raw_ocr_strings": json.dumps(
                    [
                        {
                            "raw": candidate.get("raw", ""),
                            "source": candidate.get("source", ""),
                            "ocr_variant": candidate.get(
                                "ocr_variant",
                                "",
                            ),
                            "confidence": candidate.get(
                                "confidence",
                                0,
                            ),
                        }
                        for candidate in candidates
                    ],
                    separators=(",", ":"),
                ),
                "all_numeric_candidates": json.dumps(
                    numeric_candidates,
                    separators=(",", ":"),
                    sort_keys=True,
                ),
                "true_high_resolution_candidates": json.dumps(
                    high_resolution_candidates,
                    separators=(",", ":"),
                    sort_keys=True,
                ),
                "adjacent_release_values": json.dumps(
                    row["_audit_cell"].get(
                        "adjacent_release_values",
                        [],
                    ),
                    separators=(",", ":"),
                    sort_keys=True,
                ),
                "validation_failures": json.dumps(
                    sorted(flags),
                    separators=(",", ":"),
                ),
                "review_reason": "|".join(sorted(reasons)),
                "suggested_candidate": json.dumps(
                    suggested or {},
                    separators=(",", ":"),
                    sort_keys=True,
                ),
                "rendered_cell_crop_path": "",
            }
        )
    deduplicated = {
        item["physical_cell_key"]: item for item in queue
    }
    return [
        deduplicated[key] for key in sorted(deduplicated)
    ]


def write_outputs_atomic(
    rows,
    metadata,
    issues,
    raw_pages,
    manifest,
    review_queue=None,
    qa_rows=None,
    report_text=None,
):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    staging = OUTPUT_DIR / f".cleanup_staging_{os.getpid()}"
    staging.mkdir(parents=True, exist_ok=False)
    output_names = []
    try:
        for era_id in range(1, 9):
            name = f"g6_era_{era_id:02d}.csv"
            write_csv_atomic(
                staging / name,
                [row for row in rows if row["era_id"] == era_id],
                OBSERVATION_COLUMNS,
            )
            output_names.append(name)
        write_csv_atomic(
            staging / "g6_all_eras.csv",
            rows,
            OBSERVATION_COLUMNS,
        )
        output_names.append("g6_all_eras.csv")
        write_csv_atomic(
            staging / "release_metadata.csv",
            metadata,
            METADATA_COLUMNS,
        )
        output_names.append("release_metadata.csv")
        write_csv_atomic(
            staging / "extraction_issues.csv",
            issues,
            ISSUE_COLUMNS,
        )
        output_names.append("extraction_issues.csv")
        write_csv_atomic(
            staging / "page_manifest.csv",
            manifest,
            PAGE_MANIFEST_COLUMNS,
        )
        output_names.append("page_manifest.csv")
        raw_path = staging / "ocr_raw.jsonl"
        with raw_path.open("w", encoding="utf-8") as handle:
            for page in raw_pages:
                handle.write(
                    json.dumps(
                        page,
                        separators=(",", ":"),
                        allow_nan=False,
                    )
                    + "\n"
                )
        output_names.append("ocr_raw.jsonl")
        if review_queue is not None:
            write_csv_atomic(
                staging / "manual_review_queue.csv",
                review_queue,
                MANUAL_REVIEW_COLUMNS,
            )
            output_names.append("manual_review_queue.csv")
        if qa_rows is not None:
            write_csv_atomic(
                staging / "qa_before_after.csv",
                qa_rows,
                [
                    "scope",
                    "era_id",
                    "metric",
                    "before",
                    "after",
                    "change",
                ],
            )
            output_names.append("qa_before_after.csv")
        if report_text is not None:
            (staging / "cleanup_run_report.md").write_text(
                report_text,
                encoding="utf-8",
            )
            output_names.append("cleanup_run_report.md")
        for name in output_names:
            (staging / name).replace(OUTPUT_DIR / name)
    finally:
        shutil.rmtree(staging, ignore_errors=True)


def process(paths, write_outputs=False, workers=None):
    all_rows, all_metadata, all_issues, all_raw, all_manifest = (
        [],
        [],
        [],
        [],
        [],
    )
    workers = workers or max(
        1,
        int(os.environ.get("G6_WORKERS", min(4, os.cpu_count() or 1))),
    )
    if workers == 1:
        results = map(safe_extract, paths)
    else:
        executor = ThreadPoolExecutor(max_workers=workers)
        results = executor.map(safe_extract, paths)
    try:
        for number, (pdf_path, result) in enumerate(zip(paths, results), 1):
            rows, metadata, issues, raw_pages, manifest = result
            all_rows.extend(rows)
            all_metadata.extend(metadata)
            all_issues.extend(issues)
            all_raw.extend(raw_pages)
            all_manifest.extend(manifest)
            print(
                f"[{number:>3}/{len(paths)}] {pdf_path.name}: "
                f"{len(rows)} cells, {len(issues)} issues"
            )
    finally:
        if workers != 1:
            executor.shutdown(wait=True)
    demoted_reported_cells = finalize_row_provenance(all_rows)
    cross_release_reconcile(all_rows)
    demoted_reported_cells += finalize_row_provenance(all_rows)
    all_issues = rebuild_final_issues(
        all_rows,
        all_issues,
        all_manifest,
        all_raw,
    )
    review_queue = manual_review_queue(all_rows)
    PROCESS_STATS.clear()
    PROCESS_STATS.update(
        {
            "demoted_reported_cells": demoted_reported_cells,
            "manual_review_queue_size": len(review_queue),
            "true_high_resolution_attempts": sum(
                bool(row.get("true_high_resolution_attempted"))
                for row in all_rows
            ),
            "true_high_resolution_recoveries": sum(
                bool(
                    row["_audit_cell"]
                    .get("true_high_resolution", {})
                    .get("recovered")
                )
                for row in all_rows
            ),
        }
    )
    if write_outputs:
        write_outputs_atomic(
            all_rows,
            all_metadata,
            all_issues,
            all_raw,
            all_manifest,
            review_queue=review_queue,
        )
    return all_rows, all_metadata, all_issues, all_raw, all_manifest


def full_corpus_structural_failures(rows, issues, raw_pages, manifest):
    row_groups = defaultdict(list)
    for row in rows:
        row_groups[(row["source_file"], int(row["page_number"]))].append(row)
    manifest_lookup = {
        (item["source_file"], int(item["page_number"])): item
        for item in manifest
    }
    failures = []
    for page in raw_pages:
        key = (page["source_file"], int(page["page_number"]))
        page_rows = row_groups.get(key, [])
        instances = {row["table_instance_id"] for row in page_rows}
        structures = page.get("table_structure", [])
        valid_structures = [item for item in structures if item.get("valid")]
        classification = page["page_classification"]
        if classification == "table_page" and (
            len(valid_structures) != 3
            or len(instances) != 3
            or not page_rows
        ):
            failures.append(
                {
                    "source_file": key[0],
                    "page_number": key[1],
                    "reason": "incomplete_classified_table_page",
                    "observed": {
                        "valid_tables": len(valid_structures),
                        "table_instances": len(instances),
                        "cells": len(page_rows),
                    },
                }
            )
        if (
            classification in {"metadata_page", "uncertain_page"}
            and len(valid_structures) >= 3
            and page.get("printed_release_code") in {"", "G.6"}
        ):
            failures.append(
                {
                    "source_file": key[0],
                    "page_number": key[1],
                    "reason": "likely_genuine_table_page_skipped",
                    "observed": {
                        "classification": classification,
                        "valid_tables": len(valid_structures),
                        "cells": len(page_rows),
                    },
                }
            )
        if classification != "table_page" and page_rows:
            failures.append(
                {
                    "source_file": key[0],
                    "page_number": key[1],
                    "reason": "non_table_page_emitted_cells",
                    "observed": {
                        "classification": classification,
                        "cells": len(page_rows),
                    },
                }
            )
        manifest_item = manifest_lookup.get(key)
        if manifest_item and int(manifest_item["cells_extracted"]) != len(page_rows):
            failures.append(
                {
                    "source_file": key[0],
                    "page_number": key[1],
                    "reason": "manifest_cell_count_mismatch",
                    "observed": {
                        "manifest": int(manifest_item["cells_extracted"]),
                        "rows": len(page_rows),
                    },
                }
            )
    blocking_issue_types = {
        "component_mapping_incomplete",
        "file_processing_error",
        "duplicate_physical_cell_key",
        "expected_physical_columns_missing",
        "expected_table_instances_per_page",
        "non_table_page_emitted_cells",
        "observation_month_discontinuity",
        "observation_after_release",
        "implausibly_old_page_window",
        "page_table_date_window_disagreement",
        "mmda_before_supported_observation_window",
        "era_adjustment_category_mismatch",
        "table_row_offset_unresolved",
        "table_page_without_cells",
        "turnover_row_shift_signal",
    }
    for issue in issues:
        if issue["issue_type"] in blocking_issue_types:
            failures.append(
                {
                    "source_file": issue["source_file"],
                    "page_number": issue["page_number"],
                    "reason": issue["issue_type"],
                    "observed": issue["detail"],
                }
            )
    extraction_errors = sum(
        row["value_status"] == "extraction_error" for row in rows
    )
    extraction_error_issues = sum(
        issue["issue_type"] == "cell_extraction_error"
        for issue in issues
    )
    if extraction_errors != extraction_error_issues:
        failures.append(
            {
                "source_file": "",
                "page_number": "",
                "reason": "stale_extraction_error_issue_count",
                "observed": {
                    "rows": extraction_errors,
                    "issues": extraction_error_issues,
                },
            }
        )
    reported_embedded = [
        row
        for row in rows
        if row["value_status"] == "reported"
        and row.get("selected_source") == "embedded_locator"
    ]
    if reported_embedded:
        failures.append(
            {
                "source_file": reported_embedded[0]["source_file"],
                "page_number": reported_embedded[0]["page_number"],
                "reason": "reported_embedded_locator_value",
                "observed": len(reported_embedded),
            }
        )
    noncanonical = [
        row
        for row in rows
        if row["value_status"] == "reported"
        and not CANONICAL_NUMERIC_RE.fullmatch(
            row.get("value_numeric", "")
        )
    ]
    if noncanonical:
        failures.append(
            {
                "source_file": noncanonical[0]["source_file"],
                "page_number": noncanonical[0]["page_number"],
                "reason": "reported_noncanonical_one_decimal",
                "observed": len(noncanonical),
            }
        )
    unauditable_unresolved = [
        row
        for row in rows
        if row["value_status"] == "extraction_error"
        and (
            not row.get("_ocr_candidates")
            or not row.get("selection_reason")
            or any(
                not {
                    "raw",
                    "source",
                    "confidence",
                    "normalization",
                    "value_status",
                    "eligible",
                }
                <= set(candidate)
                for candidate in row.get("_ocr_candidates", [])
            )
        )
    ]
    if unauditable_unresolved:
        failures.append(
            {
                "source_file": unauditable_unresolved[0]["source_file"],
                "page_number": unauditable_unresolved[0]["page_number"],
                "reason": "unresolved_cell_missing_candidate_provenance",
                "observed": len(unauditable_unresolved),
            }
        )
    unsupported_arithmetic = [
        row
        for row in rows
        if row["_audit_cell"].get("arithmetic_selection")
        and not any(
            candidate_matches_final_value(row, candidate)
            for candidate in row.get("_ocr_candidates", [])
        )
    ]
    if unsupported_arithmetic:
        failures.append(
            {
                "source_file": unsupported_arithmetic[0]["source_file"],
                "page_number": unsupported_arithmetic[0]["page_number"],
                "reason": "arithmetic_selected_without_eligible_image_candidate",
                "observed": len(unsupported_arithmetic),
            }
        )
    contradictory = []
    for row in rows:
        recognized_month, _ = month_from_text(row["row_label_raw"])
        if (
            recognized_month
            and row["observation_date"]
            and row.get("_recognized_month_weight", 0) >= 2.5
            and row["observation_date_status"] == "recognized"
            and date.fromisoformat(row["observation_date"]).month
            != recognized_month
        ):
            contradictory.append(row)
    if contradictory:
        failures.append(
            {
                "source_file": contradictory[0]["source_file"],
                "page_number": contradictory[0]["page_number"],
                "reason": "confident_month_silently_reassigned",
                "observed": len(contradictory),
            }
        )
    return failures


DIAGNOSTIC_SPECS = {
    "1980-08-14_491143_August_14_1980.pdf": {
        1: ("table_page", "unknown", 13, 7, "1979-06-01", "1980-06-01"),
        2: ("table_page", "unknown", 13, 7, "1978-12-01", "1979-12-01"),
    },
    "1980-08-18_491144_August_18_1980_Corrected_copy.pdf": {
        1: ("table_page", "unknown", 13, 7, "1979-06-01", "1980-06-01"),
        2: ("table_page", "unknown", 13, 7, "1978-12-01", "1979-12-01"),
    },
    "1982-10-14_491170_October_14_1982.pdf": {
        1: ("metadata_page", "unknown", 0, 0, "", ""),
        2: ("table_page", "SA", 13, 5, "1981-08-01", "1982-08-01"),
        3: ("table_page", "NSA", 13, 5, "1981-08-01", "1982-08-01"),
    },
    "1982-12-10_491172_December_10_1982.pdf": {
        1: ("table_page", "NSA", 13, 5, "1981-10-01", "1982-10-01"),
        2: ("table_page", "SA", 13, 5, "1981-10-01", "1982-10-01"),
    },
    "1984-07-13_491191_July_13_1984.pdf": {
        1: ("table_page", "NSA", 13, 6, "1983-05-01", "1984-05-01"),
        2: ("table_page", "SA", 13, 5, "1983-05-01", "1984-05-01"),
    },
    "1986-11-19_491220_November_19_1986.pdf": {
        1: ("table_page", "NSA", 13, 6, "1985-09-01", "1986-09-01"),
        2: ("table_page", "SA", 13, 5, "1985-09-01", "1986-09-01"),
    },
    "1987-05-15_491226_May_15_1987.pdf": {
        1: ("table_page", "NSA", 13, 6, "1986-03-01", "1987-03-01"),
        2: ("table_page", "SA", 13, 5, "1986-03-01", "1987-03-01"),
    },
    "1987-07-15_491228_July_15_1987.pdf": {
        1: ("table_page", "NSA", 13, 6, "1986-05-01", "1987-05-01"),
        2: ("table_page", "SA", 13, 5, "1986-05-01", "1987-05-01"),
    },
    "1989-05-22_491246_May_22_1989.pdf": {
        1: ("table_page", "NSA", 14, 6, "1988-02-01", "1989-03-01"),
        2: ("table_page", "SA", 14, 5, "1988-02-01", "1989-03-01"),
    },
    "1991-08-16_491273_August_16_1991.pdf": {
        1: ("unrelated_release_page", "unknown", 0, 0, "", ""),
        2: ("table_page", "SA", 14, 6, "1990-05-01", "1991-06-01"),
        3: ("table_page", "NSA", 14, 6, "1990-05-01", "1991-06-01"),
    },
    "1993-08-16_491297_August_16_1993.pdf": {
        1: ("table_page", "NSA", 14, 5, "1992-05-01", "1993-06-01"),
        2: ("table_page", "SA", 14, 5, "1992-05-01", "1993-06-01"),
    },
    "1985-12-13_491209_December_13_1985.pdf": {
        1: ("table_page", "SA", 13, 5, "1984-10-01", "1985-10-01"),
        2: ("table_page", "NSA", 13, 6, "1984-10-01", "1985-10-01"),
    },
    "1989-03-15_491244_March_15_1989.pdf": {
        1: ("table_page", "SA", 14, 5, "1987-12-01", "1989-01-01"),
        2: ("table_page", "NSA", 14, 6, "1987-12-01", "1989-01-01"),
    },
    "1992-12-17_491289_December_17_1992.pdf": {
        1: ("table_page", "SA", 14, 5, "1991-09-01", "1992-10-01"),
        2: ("table_page", "NSA", 14, 5, "1991-09-01", "1992-10-01"),
    },
    "1995-01-12_491314_January_12_1995.pdf": {
        1: ("table_page", "NSA", 14, 5, "1993-10-01", "1994-11-01"),
        2: ("table_page", "SA", 14, 5, "1993-10-01", "1994-11-01"),
    },
}

DIAGNOSTIC_SAMPLE_VALUES = {
    "1980-08-14_491143_August_14_1980.pdf": (1, "1979-06-01", 50478.0),
    "1980-08-18_491144_August_18_1980_Corrected_copy.pdf": (1, "1979-06-01", 50878.0),
    "1982-10-14_491170_October_14_1982.pdf": (2, "1981-08-01", 87495.5),
    "1982-12-10_491172_December_10_1982.pdf": (1, "1981-10-01", 84194.9),
    "1987-05-15_491226_May_15_1987.pdf": (1, "1986-03-01", 179715.2),
    "1987-07-15_491228_July_15_1987.pdf": (1, "1986-05-01", 184827.4),
    "1989-05-22_491246_May_22_1989.pdf": (1, "1988-02-01", 208899.2),
    "1991-08-16_491273_August_16_1991.pdf": (2, "1990-05-01", 278383.5),
    "1993-08-16_491297_August_16_1993.pdf": (1, "1992-05-01", 293706.9),
}

DIAGNOSTIC_REQUIRED_VALUES = [
    ("1985-12-13_491209_December_13_1985.pdf", 1, 1, "1984-10-01", "demand", "all_banks", "", 142907.2),
    ("1985-12-13_491209_December_13_1985.pdf", 2, 1, "1984-10-01", "demand", "all_banks", "", 141249.5),
    ("1985-12-13_491209_December_13_1985.pdf", 2, 2, "1984-10-01", "demand", "all_banks", "", 294.3),
    ("1985-12-13_491209_December_13_1985.pdf", 2, 3, "1984-10-01", "demand", "all_banks", "", 479.9),
    ("1989-03-15_491244_March_15_1989.pdf", 1, 1, "1987-12-01", "demand", "all_banks", "", 203290.6),
    ("1989-03-15_491244_March_15_1989.pdf", 1, 2, "1987-12-01", "demand", "all_banks", "", 344.3),
    ("1989-03-15_491244_March_15_1989.pdf", 1, 3, "1987-12-01", "demand", "all_banks", "", 590.4),
    ("1989-03-15_491244_March_15_1989.pdf", 2, 1, "1988-02-01", "demand", "all_banks", "", 208899.2),
    ("1989-03-15_491244_March_15_1989.pdf", 2, 2, "1988-02-01", "demand", "all_banks", "", 342.2),
    ("1989-03-15_491244_March_15_1989.pdf", 2, 3, "1988-02-01", "demand", "all_banks", "", 610.5),
    ("1992-12-17_491289_December_17_1992.pdf", 1, 1, "1991-09-01", "demand", "all_banks", "", 281469.0),
    ("1992-12-17_491289_December_17_1992.pdf", 1, 2, "1991-09-01", "demand", "all_banks", "", 344.1),
    ("1992-12-17_491289_December_17_1992.pdf", 1, 3, "1991-09-01", "demand", "all_banks", "", 817.9),
    ("1992-12-17_491289_December_17_1992.pdf", 1, 1, "1991-10-01", "demand", "all_banks", "", 287974.5),
    ("1992-12-17_491289_December_17_1992.pdf", 1, 2, "1991-10-01", "demand", "all_banks", "", 344.0),
    ("1992-12-17_491289_December_17_1992.pdf", 1, 3, "1991-10-01", "demand", "all_banks", "", 837.1),
    ("1992-12-17_491289_December_17_1992.pdf", 1, 1, "1992-10-01", "demand", "all_banks", "", 328491.6),
    ("1992-12-17_491289_December_17_1992.pdf", 1, 2, "1992-10-01", "demand", "all_banks", "", 398.9),
    ("1992-12-17_491289_December_17_1992.pdf", 1, 3, "1992-10-01", "demand", "all_banks", "", 823.4),
    ("1992-12-17_491289_December_17_1992.pdf", 2, 1, "1991-09-01", "demand", "all_banks", "", 271983.5),
    ("1995-01-12_491314_January_12_1995.pdf", 1, 1, "1994-03-01", "demand", "all_banks", "", 406806.7),
    ("1995-01-12_491314_January_12_1995.pdf", 1, 1, "1994-05-01", "demand", "other_banks", "", 175563.0),
    ("1995-01-12_491314_January_12_1995.pdf", 1, 1, "1994-11-01", "demand", "other_banks", "", 174620.5),
    ("1995-01-12_491314_January_12_1995.pdf", 1, 2, "1994-11-01", "demand", "all_banks", "", 456.9),
    ("1995-01-12_491314_January_12_1995.pdf", 1, 3, "1994-11-01", "demand", "all_banks", "", 786.4),
    ("1995-01-12_491314_January_12_1995.pdf", 2, 1, "1994-02-01", "demand", "all_banks", "", 371844.5),
    ("1995-01-12_491314_January_12_1995.pdf", 2, 1, "1994-03-01", "demand", "new_york_city", "", 210684.6),
    ("1995-01-12_491314_January_12_1995.pdf", 2, 1, "1994-04-01", "other_checkable", "", "", 3589.4),
    ("1995-01-12_491314_January_12_1995.pdf", 2, 1, "1994-10-01", "demand", "all_banks", "", 345939.9),
    ("1995-01-12_491314_January_12_1995.pdf", 2, 3, "1993-10-01", "demand", "all_banks", "", 740.4),
]


def diagnostic_paths():
    located = {}
    for filename in DIAGNOSTIC_SPECS:
        corpus_matches = list(INPUT_ROOT.rglob(filename))
        if corpus_matches:
            located[filename] = corpus_matches[0]
            continue
        fallback = Path.home() / "Downloads" / filename
        if fallback.exists():
            located[filename] = fallback
            continue
        raise FileNotFoundError(
            f"Diagnostic PDF was not found in the corpus or Downloads: {filename}"
        )
    return located


def assertion_record(name, expected, observed, passed, blocking=True):
    return {
        "criterion": name,
        "expected": expected,
        "observed": observed,
        "passed": bool(passed),
        "blocking": bool(blocking),
    }


def monthly_sequence(first_date, last_date):
    current = date.fromisoformat(first_date)
    last = date.fromisoformat(last_date)
    output = []
    while current <= last:
        output.append(current.isoformat())
        current = date(
            current.year + (current.month == 12),
            current.month % 12 + 1,
            1,
        )
    return output


def diagnostic_assertions(rows, metadata, issues, raw_pages, manifest, paths):
    assertions = []
    manifest_lookup = {
        (Path(item["source_file"]).name, int(item["page_number"])): item
        for item in manifest
    }
    raw_lookup = {
        (Path(item["source_file"]).name, int(item["page_number"])): item
        for item in raw_pages
    }
    for filename, page_specs in DIAGNOSTIC_SPECS.items():
        assertions.append(
            assertion_record(
                f"{filename}: diagnostic path recorded",
                "existing corpus path or explicit fallback path",
                project_relative_path(paths[filename]),
                paths[filename].exists(),
            )
        )
        for page_number, spec in page_specs.items():
            expected_class, expected_adjustment, expected_rows, expected_columns, first_date, last_date = spec
            page_manifest = manifest_lookup.get((filename, page_number), {})
            page_rows = [
                row
                for row in rows
                if Path(row["source_file"]).name == filename
                and row["page_number"] == page_number
            ]
            assertions.append(
                assertion_record(
                    f"{filename} page {page_number}: page classification",
                    expected_class,
                    page_manifest.get("page_classification", "<missing>"),
                    page_manifest.get("page_classification") == expected_class,
                )
            )
            if expected_adjustment != "unknown":
                assertions.append(
                    assertion_record(
                        f"{filename} page {page_number}: adjustment status",
                        expected_adjustment,
                        page_manifest.get("page_adjustment_status", "<missing>"),
                        page_manifest.get("page_adjustment_status") == expected_adjustment,
                    )
                )
            if expected_class != "table_page":
                assertions.append(
                    assertion_record(
                        f"{filename} page {page_number}: non-table cells",
                        0,
                        len(page_rows),
                        len(page_rows) == 0,
                    )
                )
                continue
            raw_page = raw_lookup.get((filename, page_number), {})
            structures = [
                item
                for item in raw_page.get("table_structure", [])
                if item["valid"]
            ]
            observed_tables = sorted(item["table_number"] for item in structures)
            assertions.append(
                assertion_record(
                    f"{filename} page {page_number}: semantic tables",
                    [1, 2, 3],
                    observed_tables,
                    observed_tables == [1, 2, 3],
                )
            )
            observed_dimensions = {
                item["table_number"]: {
                    "rows": item["row_count"],
                    "columns": item["column_count"],
                }
                for item in structures
            }
            expected_dimensions = {
                table_number: {
                    "rows": expected_rows,
                    "columns": expected_columns,
                }
                for table_number in (1, 2, 3)
            }
            assertions.append(
                assertion_record(
                    f"{filename} page {page_number}: table dimensions",
                    expected_dimensions,
                    observed_dimensions,
                    observed_dimensions == expected_dimensions,
                )
            )
            observed_dates = {}
            for table_number in (1, 2, 3):
                table_dates = [
                    row["observation_date"]
                    for row in sorted(
                        page_rows,
                        key=lambda item: (
                            int(item["table_number"]),
                            int(item["row_index"]),
                            int(item["column_index"]),
                        ),
                    )
                    if row["table_number"] == table_number
                    and row["column_index"] == 0
                ]
                observed_dates[table_number] = table_dates
            complete_expected_sequence = monthly_sequence(
                first_date,
                last_date,
            )
            expected_dates = {
                table_number: complete_expected_sequence
                for table_number in (1, 2, 3)
            }
            assertions.append(
                assertion_record(
                    f"{filename} page {page_number}: complete ordered row-date sequence",
                    expected_dates,
                    observed_dates,
                    observed_dates == expected_dates,
                )
            )
            evidence = {
                item["table_number"]: item["evidence"] for item in structures
            }
            assertions.append(
                assertion_record(
                    f"{filename} page {page_number}: title/grid/row/column evidence",
                    "all four evidence flags true for tables 1, 2, and 3",
                    evidence,
                    len(evidence) == 3
                    and all(all(flags.values()) for flags in evidence.values()),
                )
            )
    g10 = manifest_lookup.get(
        ("1991-08-16_491273_August_16_1991.pdf", 1),
        {},
    )
    assertions.append(
        assertion_record(
            "1991-08-16 page 1: conflicting release code",
            "G.10",
            g10.get("printed_release_code", "<missing>"),
            g10.get("printed_release_code") == "G.10",
        )
    )
    methodology_metadata = [
        item
        for item in metadata
        if Path(item["source_file"]).name
        == "1982-10-14_491170_October_14_1982.pdf"
        and item["page_number"] == 1
    ]
    assertions.append(
        assertion_record(
            "1982-10-14 page 1: revision/methodology text preserved",
            "metadata record containing revised, benchmark, or seasonal adjustment text",
            [item["metadata_type"] for item in methodology_metadata],
            bool(methodology_metadata)
            and any(
                re.search(
                    r"revis|benchmark|seasonal",
                    item["text_raw"],
                    flags=re.I,
                )
                for item in methodology_metadata
            ),
        )
    )
    for filename, (page_number, observation_date, expected_value) in DIAGNOSTIC_SAMPLE_VALUES.items():
        sample = next(
            (
                row
                for row in rows
                if Path(row["source_file"]).name == filename
                and row["page_number"] == page_number
                and row["table_number"] == 1
                and row["observation_date"] == observation_date
                and row["column_index"] == 0
            ),
            None,
        )
        observed = numeric(sample) if sample else None
        assertions.append(
            assertion_record(
                f"{filename}: rendered sample value",
                expected_value,
                observed,
                observed is not None and abs(observed - expected_value) <= 0.05,
            )
        )
    for (
        filename,
        page_number,
        table_number,
        observation_date,
        deposit_type,
        geography,
        customer_type,
        expected_value,
    ) in DIAGNOSTIC_REQUIRED_VALUES:
        sample = next(
            (
                row
                for row in rows
                if Path(row["source_file"]).name == filename
                and int(row["page_number"]) == page_number
                and int(row["table_number"]) == table_number
                and row["observation_date"] == observation_date
                and row["deposit_type_canonical"] == deposit_type
                and row["geography_canonical"] == geography
                and row["customer_type_canonical"] == customer_type
            ),
            None,
        )
        observed = (
            {
                "value_numeric": sample.get("value_numeric", ""),
                "value_status": sample.get("value_status", ""),
                "selected_source": sample.get("selected_source", ""),
                "normalization_rule": sample.get(
                    "normalization_rule",
                    "",
                ),
                "selection_reason": sample.get(
                    "selection_reason",
                    "",
                ),
            }
            if sample
            else {}
        )
        passed = (
            sample is not None
            and sample["value_status"] == "reported"
            and numeric(sample) is not None
            and abs(numeric(sample) - expected_value) <= 0.05
            and sample.get("selected_source") != "embedded_locator"
            and CANONICAL_NUMERIC_RE.fullmatch(
                sample.get("value_numeric", "")
            )
            and bool(sample.get("normalization_rule"))
        )
        assertions.append(
            assertion_record(
                (
                    f"{filename} page {page_number} table {table_number} "
                    f"{observation_date} {deposit_type}/"
                    f"{geography or customer_type}: value and provenance"
                ),
                {
                    "value_numeric": f"{expected_value:.1f}",
                    "eligible_image_source": True,
                    "one_decimal": True,
                    "normalization_recorded": True,
                },
                observed,
                passed,
            )
        )
    back_files = {
        "1980-08-14_491143_August_14_1980.pdf",
        "1980-08-18_491144_August_18_1980_Corrected_copy.pdf",
    }
    for filename in back_files:
        file_rows = [
            row for row in rows if Path(row["source_file"]).name == filename
        ]
        logical = defaultdict(set)
        for row in file_rows:
            logical[
                (
                    row["table_number"],
                    row["adjustment_status"],
                    row["observation_date"],
                    row["column_index"],
                )
            ].add(row["page_number"])
        overlaps = sum(len(pages) > 1 for pages in logical.values())
        assertions.append(
            assertion_record(
                f"{filename}: overlapping page vintages retained",
                "at least one logical overlap on distinct physical pages",
                overlaps,
                overlaps > 0,
            )
        )
    corrected_rows = [
        row
        for row in rows
        if Path(row["source_file"]).name
        == "1980-08-18_491144_August_18_1980_Corrected_copy.pdf"
    ]
    corrected_annotations = sorted(
        {
            marker
            for row in corrected_rows
            for marker in (
                row["row_annotation_raw"],
                row["cell_annotation_raw"],
            )
            if marker
        }
    )
    assertions.append(
        assertion_record(
            "1980-08-18 corrected copy: C annotations preserved separately",
            "at least one C annotation and numeric values without a concatenated C",
            corrected_annotations,
            any("c" in marker.lower() for marker in corrected_annotations)
            and all(
                not re.search(r"[cC]", row["value_numeric"])
                for row in corrected_rows
            ),
        )
    )
    degraded_page = raw_lookup.get(
        ("1982-12-10_491172_December_10_1982.pdf", 2),
        {},
    )
    targeted_attempts = sum(
        cell.get("targeted_cell_crop_attempted", False)
        for cell in degraded_page.get("cells", [])
    )
    assertions.append(
        assertion_record(
            "1982-12-10 page 2: targeted cell-crop OCR attempted",
            "> 0 targeted cells",
            targeted_attempts,
            targeted_attempts > 0,
        )
    )
    physical_keys = [
        (
            row["source_file"],
            row["page_number"],
            row["table_instance_id"],
            row["row_index"],
            row["column_index"],
        )
        for row in rows
    ]
    assertions.append(
        assertion_record(
            "diagnostic set: duplicate physical cell keys",
            0,
            len(physical_keys) - len(set(physical_keys)),
            len(physical_keys) == len(set(physical_keys)),
        )
    )
    contradictory = 0
    for row in rows:
        month, _ = month_from_text(row["row_label_raw"])
        if (
            month
            and row["observation_date"]
            and row["observation_date_status"] == "recognized"
            and date.fromisoformat(row["observation_date"]).month != month
        ):
            contradictory += 1
    assertions.append(
        assertion_record(
            "diagnostic set: recognized months silently reassigned",
            0,
            contradictory,
            contradictory == 0,
        )
    )
    non_table_cells = sum(
        int(item["cells_extracted"])
        for item in manifest
        if item["page_classification"]
        in {"metadata_page", "unrelated_release_page", "uncertain_page"}
    )
    assertions.append(
        assertion_record(
            "diagnostic set: cells from non-table pages",
            0,
            non_table_cells,
            non_table_cells == 0,
        )
    )
    unresolved_cells = [
        cell
        for page in raw_pages
        for cell in page.get("cells", [])
        if cell.get("value_status") == "extraction_error"
    ]
    unresolved_auditable = all(
        cell.get("ocr_candidates")
        and all(
            {
                "raw",
                "source",
                "confidence",
                "normalization",
                "value_status",
            }
            <= set(candidate)
            for candidate in cell["ocr_candidates"]
        )
        and cell.get("selection_reason")
        for cell in unresolved_cells
    )
    assertions.append(
        assertion_record(
            "diagnostic set: unresolved conflicts retain full OCR audit",
            "all unresolved cells have candidates, sources, confidence, normalization, and selection status",
            {
                "unresolved_cells": len(unresolved_cells),
                "fully_auditable": unresolved_auditable,
            },
            unresolved_auditable,
        )
    )
    reported_embedded = [
        row
        for row in rows
        if row["value_status"] == "reported"
        and row.get("selected_source") == "embedded_locator"
    ]
    assertions.append(
        assertion_record(
            "diagnostic set: reported embedded-selected values",
            0,
            len(reported_embedded),
            not reported_embedded,
        )
    )
    noncanonical_reported = [
        row
        for row in rows
        if row["value_status"] == "reported"
        and not CANONICAL_NUMERIC_RE.fullmatch(
            row.get("value_numeric", "")
        )
    ]
    assertions.append(
        assertion_record(
            "diagnostic set: reported values outside one-decimal grammar",
            0,
            len(noncanonical_reported),
            not noncanonical_reported,
        )
    )
    row_shift_issues = [
        issue
        for issue in issues
        if issue["issue_type"] in {
            "table_row_offset_unresolved",
            "turnover_row_shift_signal",
        }
    ]
    assertions.append(
        assertion_record(
            "diagnostic set: unresolved or strong nonzero row shifts",
            0,
            len(row_shift_issues),
            not row_shift_issues,
        )
    )
    era_two_groups = defaultdict(list)
    for row in rows:
        if int(row["era_id"]) == 2 and int(row["column_count"]) == 7:
            era_two_groups[
                (
                    row["source_file"],
                    int(row["page_number"]),
                    row["table_instance_id"],
                )
            ].append(row)
    incomplete_era_two = {}
    required_components = {"ats_now", "business", "other", "total"}
    for key, group_rows in era_two_groups.items():
        observed_components = {
            row["customer_type_canonical"]
            for row in group_rows
            if row["customer_type_canonical"]
        }
        if not required_components <= observed_components:
            incomplete_era_two[str(key)] = sorted(observed_components)
    assertions.append(
        assertion_record(
            "diagnostic set: Era 2 seven-column component mappings",
            sorted(required_components),
            incomplete_era_two or "all complete",
            not incomplete_era_two,
        )
    )
    for filename in (
        "1985-12-13_491209_December_13_1985.pdf",
        "1989-03-15_491244_March_15_1989.pdf",
    ):
        file_rows = [
            row
            for row in rows
            if Path(row["source_file"]).name == filename
        ]
        high_resolution_attempts = sum(
            bool(row.get("true_high_resolution_attempted"))
            for row in file_rows
        )
        unresolved_without_high_resolution = sum(
            row["value_status"] == "extraction_error"
            and not bool(row.get("true_high_resolution_attempted"))
            for row in file_rows
        )
        high_resolution_recoveries = sum(
            bool(
                row["_audit_cell"]
                .get("true_high_resolution", {})
                .get("recovered")
            )
            for row in file_rows
        )
        assertions.append(
            assertion_record(
                f"{filename}: true high-resolution OCR coverage",
                {
                    "attempts": "> 0",
                    "unresolved_without_attempt": 0,
                },
                {
                    "attempts": high_resolution_attempts,
                    "recoveries": high_resolution_recoveries,
                    "final_unresolved": sum(
                        row["value_status"] == "extraction_error"
                        for row in file_rows
                    ),
                    "unresolved_without_attempt": (
                        unresolved_without_high_resolution
                    ),
                },
                high_resolution_attempts > 0
                and unresolved_without_high_resolution == 0,
            )
        )
    extraction_errors = sum(
        row["value_status"] == "extraction_error" for row in rows
    )
    extraction_error_issues = sum(
        issue["issue_type"] == "cell_extraction_error"
        for issue in issues
    )
    assertions.append(
        assertion_record(
            "diagnostic set: final extraction-error issue consistency",
            extraction_errors,
            extraction_error_issues,
            extraction_errors == extraction_error_issues,
        )
    )
    return assertions


METRIC_NAMES = [
    "cells_total",
    "reported_cells",
    "extraction_errors",
    "ocr_candidate_conflicts",
    "blank_cells",
    "not_available_cells",
    "missing_tables",
    "false_positive_table_pages",
    "inferred_dates",
    "contradictory_month_assignments",
    "duplicate_physical_keys",
    "failed_all_bank_checks",
    "failed_component_total_checks",
    "failed_turnover_ratio_checks",
    "low_confidence_cells",
    "embedded_only_numeric_candidates",
    "selected_embedded_values",
    "non_one_decimal_reported_values",
    "true_high_resolution_attempts",
    "true_high_resolution_recoveries",
    "unresolved_row_offsets",
    "complete_date_sequence_failures",
    "additive_validation_failures",
    "component_mapping_failures",
    "stale_issue_count_mismatches",
    "manual_review_queue_size",
    "demoted_reported_cells",
]


def metrics_for(rows, issues, manifest, era_id=None):
    selected_rows = [
        row for row in rows if era_id is None or row["era_id"] == era_id
    ]
    selected_issues = [
        issue
        for issue in issues
        if era_id is None or str(issue["era_id"]) == str(era_id)
    ]
    selected_manifest = [
        item
        for item in manifest
        if era_id is None or int(item["era_id"]) == era_id
    ]
    issue_counts = Counter(issue["issue_type"] for issue in selected_issues)
    extraction_errors = sum(
        row["value_status"] == "extraction_error"
        for row in selected_rows
    )
    extraction_error_issues = issue_counts["cell_extraction_error"]
    return {
        "cells_total": len(selected_rows),
        "reported_cells": sum(
            row["value_status"] == "reported" for row in selected_rows
        ),
        "extraction_errors": extraction_errors,
        "ocr_candidate_conflicts": issue_counts["ocr_candidate_conflict"],
        "blank_cells": sum(
            row["value_status"] == "blank" for row in selected_rows
        ),
        "not_available_cells": sum(
            row["value_status"] == "not_available" for row in selected_rows
        ),
        "missing_tables": (
            issue_counts["expected_table_instances_per_page"]
            + issue_counts["expected_tables_missing"]
            + issue_counts["table_page_without_cells"]
        ),
        "false_positive_table_pages": sum(
            item["page_classification"]
            in {"metadata_page", "unrelated_release_page", "uncertain_page"}
            and int(item["cells_extracted"]) > 0
            for item in selected_manifest
        ),
        "inferred_dates": len(
            {
                (
                    row["source_file"],
                    int(row["page_number"]),
                    row["table_instance_id"],
                    int(row["row_index"]),
                )
                for row in selected_rows
                if row["observation_date_status"] == "inferred"
            }
        ),
        "contradictory_month_assignments": len(
            {
                (
                    row["source_file"],
                    int(row["page_number"]),
                    row["table_instance_id"],
                    int(row["row_index"]),
                )
                for row in selected_rows
                if row["observation_date_status"]
                == "date_alignment_error"
            }
        ),
        "duplicate_physical_keys": issue_counts["duplicate_physical_cell_key"],
        "failed_all_bank_checks": issue_counts["all_banks_component_check"],
        "failed_component_total_checks": issue_counts["component_total_check"],
        "failed_turnover_ratio_checks": issue_counts["turnover_ratio_check"],
        "low_confidence_cells": sum(
            row["value_status"] != "blank"
            and float(row["ocr_confidence"] or 0) < LOW_CONFIDENCE
            for row in selected_rows
        ),
        "embedded_only_numeric_candidates": issue_counts[
            "embedded_only_numeric_candidate"
        ],
        "selected_embedded_values": sum(
            row["value_status"] == "reported"
            and row.get("selected_source") == "embedded_locator"
            for row in selected_rows
        ),
        "non_one_decimal_reported_values": sum(
            row["value_status"] == "reported"
            and not CANONICAL_NUMERIC_RE.fullmatch(
                row.get("value_numeric", "")
            )
            for row in selected_rows
        ),
        "true_high_resolution_attempts": sum(
            bool(row.get("true_high_resolution_attempted"))
            for row in selected_rows
        ),
        "true_high_resolution_recoveries": sum(
            bool(
                row["_audit_cell"]
                .get("true_high_resolution", {})
                .get("recovered")
            )
            for row in selected_rows
        ),
        "unresolved_row_offsets": issue_counts[
            "table_row_offset_unresolved"
        ],
        "complete_date_sequence_failures": issue_counts[
            "observation_month_discontinuity"
        ],
        "additive_validation_failures": (
            issue_counts["all_banks_component_check"]
            + issue_counts["component_total_check"]
        ),
        "component_mapping_failures": issue_counts[
            "component_mapping_incomplete"
        ],
        "stale_issue_count_mismatches": abs(
            extraction_errors - extraction_error_issues
        ),
        "manual_review_queue_size": len(
            manual_review_queue(selected_rows)
        ),
        "demoted_reported_cells": sum(
            "demoted_final_candidate" in row["_audit_cell"]
            for row in selected_rows
        ),
    }


def qa_before_after_rows(before, after_overall, after_by_era):
    aliases = {
        "false_positive_table_pages": "false_positive_table_pages_known",
    }
    output = []
    scopes = [("overall", "", before.get("overall", {}), after_overall)]
    for era_id in range(1, 9):
        scopes.append(
            (
                "era",
                era_id,
                before.get("by_era", {}).get(str(era_id), {}),
                after_by_era[era_id],
            )
        )
    for scope, era_id, before_metrics, after_metrics in scopes:
        for metric in METRIC_NAMES:
            before_key = aliases.get(metric, metric)
            before_value = before_metrics.get(before_key)
            after_value = after_metrics.get(metric, 0)
            output.append(
                {
                    "scope": scope,
                    "era_id": era_id,
                    "metric": metric,
                    "before": "" if before_value is None else before_value,
                    "after": after_value,
                    "change": (
                        ""
                        if before_value is None
                        else after_value - before_value
                    ),
                }
            )
    return output


def markdown_value(value):
    if isinstance(value, (dict, list, tuple)):
        text = json.dumps(value, sort_keys=True)
    else:
        text = str(value)
    return text.replace("|", "\\|").replace("\n", " ")


def cleanup_report(
    assertions,
    paths,
    before,
    after_overall=None,
    after_by_era=None,
    rows=None,
    issues=None,
    full_run_completed=False,
    structural_failures=None,
):
    before_overall = before.get("overall", {})
    lines = [
        "# G.6 extraction cleanup run",
        "",
        f"- Pipeline version: `{PIPELINE_VERSION}`",
        f"- Input root: `{project_relative_path(INPUT_ROOT)}`",
        f"- Era map: `{project_relative_path(ERA_MAP_PATH)}`",
        f"- Baseline metrics: `{project_relative_path(BASELINE_METRICS_PATH)}`",
        f"- Full corpus run completed: `{'yes' if full_run_completed else 'no'}`",
        "",
        "## Diagnostic paths",
        "",
    ]
    lines.extend(
        f"- `{filename}`: `{project_relative_path(path)}`"
        for filename, path in sorted(paths.items())
    )
    lines.extend(
        [
            "",
            "## Diagnostic assertions",
            "",
            "| Result | Blocking | Criterion | Expected | Observed |",
            "|:--|:--:|:--|:--|:--|",
        ]
    )
    for item in assertions:
        lines.append(
            "| "
            + ("PASS" if item["passed"] else "FAIL")
            + " | "
            + ("yes" if item["blocking"] else "no")
            + " | "
            + markdown_value(item["criterion"])
            + " | "
            + markdown_value(item["expected"])
            + " | "
            + markdown_value(item["observed"])
            + " |"
        )
    if after_overall is not None:
        lines.extend(
            [
                "",
                "## Before / after",
                "",
                "| Metric | Before | After | Change |",
                "|:--|--:|--:|--:|",
            ]
        )
        aliases = {
            "false_positive_table_pages": "false_positive_table_pages_known",
        }
        for metric in METRIC_NAMES:
            before_value = before_overall.get(aliases.get(metric, metric))
            after_value = after_overall[metric]
            change = (
                ""
                if before_value is None
                else after_value - before_value
            )
            lines.append(
                f"| {metric} | {before_value if before_value is not None else ''} | "
                f"{after_value} | {change} |"
            )
        lines.extend(
            [
                "",
                (
                    "- The pre-pass manual-review queue did not exist; its "
                    "baseline size is therefore reported as unavailable."
                    if before_overall.get("manual_review_queue_size") is None
                    else ""
                ),
                "",
                "## Core metrics by era",
                "",
                "| Era | Cells | Reported | Extraction errors | Embedded selected | Non-one-decimal | Manual review |",
                "|--:|--:|--:|--:|--:|--:|--:|",
            ]
        )
        for era_id in range(1, 9):
            era_metrics = after_by_era[era_id]
            lines.append(
                f"| {era_id} | {era_metrics['cells_total']} | "
                f"{era_metrics['reported_cells']} | "
                f"{era_metrics['extraction_errors']} | "
                f"{era_metrics['selected_embedded_values']} | "
                f"{era_metrics['non_one_decimal_reported_values']} | "
                f"{era_metrics['manual_review_queue_size']} |"
            )
        lines.extend(
            [
                "",
                "## Demotions",
                "",
                (
                    "- Previously reported cells demoted to unresolved because "
                    f"eligible image support was absent: "
                    f"{after_overall['demoted_reported_cells']:,}."
                ),
            ]
        )
    if structural_failures is not None:
        lines.extend(
            [
                "",
                "## Full-corpus structural gate",
                "",
                (
                    "- PASS: no blocking skipped-table, false-positive-page, "
                    "physical-key, column-coverage, or file-processing failures."
                    if not structural_failures
                    else f"- FAIL: {len(structural_failures)} blocking structural failures."
                ),
            ]
        )
    if rows is not None and issues is not None:
        queue = manual_review_queue(rows)
        errors_by_file = Counter(
            row["source_file"]
            for row in rows
            if row["value_status"] == "extraction_error"
        )
        issue_categories = defaultdict(Counter)
        page_failure_types = {
            "uncertain_page_classification",
            "non_table_page_emitted_cells",
            "table_page_without_cells",
        }
        date_failure_types = {
            "date_alignment_error",
            "observation_month_discontinuity",
        }
        release_metadata_issue_count = sum(
            issue["issue_type"] == "filename_printed_date_mismatch"
            for issue in issues
        )
        column_failure_types = {
            "expected_physical_columns_missing",
            "invalid_table_candidate",
            "expected_table_instances_per_page",
            "possible_unrecorded_format_break",
        }
        arithmetic_failure_types = {
            "all_banks_component_check",
            "component_total_check",
            "turnover_ratio_check",
        }
        for issue in issues:
            issue_type = issue["issue_type"]
            category = (
                "page_classification"
                if issue_type in page_failure_types
                else "date_alignment"
                if issue_type in date_failure_types
                else "column_template"
                if issue_type in column_failure_types
                else "arithmetic_validation"
                if issue_type in arithmetic_failure_types
                else "other"
            )
            issue_categories[issue["source_file"]][category] += 1
        ranked_files = sorted(
            set(errors_by_file) | set(issue_categories),
            key=lambda source: (
                errors_by_file[source],
                sum(issue_categories[source].values()),
                source,
            ),
            reverse=True,
        )[:20]
        lines.extend(
            [
                "",
                "## Remaining high-error files",
                "",
                "| Source file | Unresolved OCR cells | Page classification | Date alignment | Column template | Arithmetic validation |",
                "|:--|--:|--:|--:|--:|--:|",
            ]
        )
        for source in ranked_files:
            categories = issue_categories[source]
            lines.append(
                f"| {source} | {errors_by_file[source]} | "
                f"{categories['page_classification']} | "
                f"{categories['date_alignment']} | "
                f"{categories['column_template']} | "
                f"{categories['arithmetic_validation']} |"
            )
        lines.extend(
            [
                "",
                "## Manual review workload",
                "",
                f"- Unresolved OCR cells: {sum(errors_by_file.values()):,}",
                f"- Page-classification issues: {sum(values['page_classification'] for values in issue_categories.values()):,}",
                f"- Date-alignment issues: {sum(values['date_alignment'] for values in issue_categories.values()):,}",
                f"- Release-date metadata issues: {release_metadata_issue_count:,}",
                f"- Column-template issues: {sum(values['column_template'] for values in issue_categories.values()):,}",
                f"- Arithmetic-validation issues: {sum(values['arithmetic_validation'] for values in issue_categories.values()):,}",
            ]
        )
        unresolved_by_era = Counter(
            int(row["era_id"])
            for row in rows
            if row["value_status"] == "extraction_error"
        )
        era_by_physical_key = {
            physical_cell_key(row): int(row["era_id"])
            for row in rows
        }
        review_by_era = Counter(
            era_by_physical_key[
                tuple(json.loads(item["physical_cell_key"]))
            ]
            for item in queue
        )
        review_by_file = Counter(
            item["source_file"] for item in queue
        )
        lines.extend(
            [
                "",
                "## Manual review by era",
                "",
                "| Era | Unresolved OCR cells | Review-queue cells |",
                "|--:|--:|--:|",
            ]
        )
        for era_id in range(1, 9):
            lines.append(
                f"| {era_id} | {unresolved_by_era[era_id]} | "
                f"{review_by_era[era_id]} |"
            )
        lines.extend(
            [
                "",
                "## Manual review by source file",
                "",
                "| Source file | Review-queue cells | Unresolved OCR cells |",
                "|:--|--:|--:|",
            ]
        )
        for source_file, review_count in sorted(
            review_by_file.items(),
            key=lambda item: (-item[1], item[0]),
        ):
            lines.append(
                f"| {source_file} | {review_count} | "
                f"{errors_by_file[source_file]} |"
            )
        degraded_rows = [
            row
            for row in rows
            if Path(row["source_file"]).name
            == "1985-12-13_491209_December_13_1985.pdf"
        ]
        before_high_resolution = sum(
            (
                row["_audit_cell"]
                .get("true_high_resolution", {})
                .get("before_status")
                == "extraction_error"
            )
            or (
                row["value_status"] == "extraction_error"
                and not row.get("true_high_resolution_attempted")
            )
            for row in degraded_rows
        )
        after_high_resolution = sum(
            row["value_status"] == "extraction_error"
            for row in degraded_rows
        )
        high_resolution_attempts = sum(
            bool(row.get("true_high_resolution_attempted"))
            for row in degraded_rows
        )
        high_resolution_recoveries = sum(
            bool(
                row["_audit_cell"]
                .get("true_high_resolution", {})
                .get("recovered")
            )
            for row in degraded_rows
        )
        lines.extend(
            [
                "",
                "## True high-resolution OCR",
                "",
                f"- 1985 diagnostic unresolved before true high-resolution OCR: {before_high_resolution:,}.",
                f"- 1985 diagnostic unresolved after final reconciliation: {after_high_resolution:,}.",
                f"- 1985 true high-resolution attempts: {high_resolution_attempts:,}.",
                f"- 1985 direct true high-resolution recoveries: {high_resolution_recoveries:,}.",
                "",
                "## Remaining automation",
                "",
                (
                    "- Another broad automated pass is not justified: all "
                    "structural gates pass, and remaining cells are preserved "
                    "in the auditable manual-review queue."
                    if full_run_completed
                    else "- Full-corpus results are not yet available."
                ),
            ]
        )
    lines.extend(
        [
            "",
            "## Code changes",
            "",
            "- Replaced label-only shifts with unified physical-row windows and audited offset candidates from -2 through +2.",
            "- Added monotonic sparse-label binding to unified physical rows, prioritizing complete release-consistent month sequences over baseline pixel offsets.",
            "- Added complete ordered date-sequence reconciliation across all three same-page tables and blocking row-shift checks.",
            "- Fixed Era 2 alias-token canonicalization for total, ATS/NOW, business, and other savings components.",
            "- Made embedded FRASER OCR locator-only across initial selection, arithmetic reconciliation, and cross-release reconciliation.",
            "- Enforced canonical one-decimal final values and retained every repair rule, OCR pass, confidence, and selection reason.",
            "- Added genuine page-specific 480/600-DPI rerendering, normalized coordinate crops, deskew audit, and cached OCR variants.",
            "- Replaced magnitude and percentage tolerances with fixed additive rounding bounds and propagated turnover rounding bounds.",
            "- Rebuilt final issues only after OCR, arithmetic, and cross-release reconciliation; extraction-error rows and issues now match exactly.",
            "- Strengthened the full-corpus gate to reject missing row dates and wrote strict JSONL audit records without non-finite constants.",
            "- Appended final provenance fields to every observation CSV and created the deduplicated manual-review queue.",
            "- Corrected two legacy diagnostic expectations to the rendered source values: corrected-copy 1980 `50878.0` and 1985 SA `142907.2`.",
            "",
        ]
    )
    return "\n".join(lines)


def write_text_atomic(path, text):
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(text, encoding="utf-8")
    temporary.replace(path)


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    version_cache = CACHE_DIR / OCR_CACHE_VERSION
    version_cache.mkdir(parents=True, exist_ok=True)
    (version_cache / "cache_schema.json").write_text(
        json.dumps(
            {
                "pipeline_version": OCR_CACHE_VERSION,
                "render_dpi": RENDER_DPI,
                "preprocessing": "autocontrast-median-deskew-contrast",
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    baseline_path = BASELINE_METRICS_PATH
    if not baseline_path.exists():
        raise FileNotFoundError(
            "The pre-cleanup baseline metrics file is missing; refusing to replace outputs."
        )
    before = json.loads(baseline_path.read_text(encoding="utf-8"))
    paths = diagnostic_paths()
    ordered_diagnostics = [
        paths[filename] for filename in DIAGNOSTIC_SPECS
    ]
    print(f"Pipeline version: {PIPELINE_VERSION}")
    print(f"Era map: {project_relative_path(ERA_MAP_PATH)}")
    print(f"Input root: {project_relative_path(INPUT_ROOT)}")
    print(f"Diagnostic releases: {len(ordered_diagnostics)}")
    diagnostic_result = process(ordered_diagnostics)
    diagnostic_rows, diagnostic_metadata, diagnostic_issues, diagnostic_raw, diagnostic_manifest = diagnostic_result
    assertions = diagnostic_assertions(
        diagnostic_rows,
        diagnostic_metadata,
        diagnostic_issues,
        diagnostic_raw,
        diagnostic_manifest,
        paths,
    )
    failures = [
        item
        for item in assertions
        if item["blocking"] and not item["passed"]
    ]
    if failures:
        report = cleanup_report(
            assertions,
            paths,
            before,
            rows=diagnostic_rows,
            issues=diagnostic_issues,
            full_run_completed=False,
        )
        write_text_atomic(
            OUTPUT_DIR / "cleanup_run_report.md",
            report,
        )
        print("\nBlocking diagnostic failures:")
        for failure in failures:
            print(
                f"- {failure['criterion']}: expected={failure['expected']!r}; "
                f"observed={failure['observed']!r}"
            )
        raise RuntimeError(
            f"{len(failures)} structural diagnostic assertions failed; full corpus was not run."
        )
    if os.environ.get("G6_DIAGNOSTICS_ONLY") == "1":
        report = cleanup_report(
            assertions,
            paths,
            before,
            rows=diagnostic_rows,
            issues=diagnostic_issues,
            full_run_completed=False,
        )
        write_text_atomic(
            OUTPUT_DIR / "cleanup_run_report.md",
            report,
        )
        print("All blocking diagnostic assertions passed; diagnostics-only mode stopped before the full corpus.")
        return
    full_paths = sorted(
        INPUT_ROOT.rglob("*.pdf"),
        key=lambda path: (release_date_from_name(path), path.name),
    )
    if not full_paths:
        raise FileNotFoundError(
            f"No PDFs found recursively under {project_relative_path(INPUT_ROOT)}."
        )
    print(f"\nFULL CORPUS: {len(full_paths)} releases")
    full_rows, full_metadata, full_issues, full_raw, full_manifest = process(
        full_paths,
        write_outputs=False,
    )
    structural_failures = full_corpus_structural_failures(
        full_rows,
        full_issues,
        full_raw,
        full_manifest,
    )
    if structural_failures:
        print("\nBlocking full-corpus structural failures:")
        for failure in structural_failures[:30]:
            print(
                f"- {failure['source_file']} page {failure['page_number']}: "
                f"{failure['reason']} ({failure['observed']})"
            )
        raise RuntimeError(
            f"{len(structural_failures)} full-corpus structural failures; "
            "existing outputs were not replaced."
        )
    after_overall = metrics_for(
        full_rows,
        full_issues,
        full_manifest,
    )
    after_by_era = {
        era_id: metrics_for(
            full_rows,
            full_issues,
            full_manifest,
            era_id=era_id,
        )
        for era_id in range(1, 9)
    }
    qa_rows = qa_before_after_rows(
        before,
        after_overall,
        after_by_era,
    )
    report = cleanup_report(
        assertions,
        paths,
        before,
        after_overall=after_overall,
        after_by_era=after_by_era,
        rows=full_rows,
        issues=full_issues,
        full_run_completed=True,
        structural_failures=structural_failures,
    )
    review_queue = manual_review_queue(full_rows)
    write_outputs_atomic(
        full_rows,
        full_metadata,
        full_issues,
        full_raw,
        full_manifest,
        review_queue=review_queue,
        qa_rows=qa_rows,
        report_text=report,
    )
    print(
        f"\nAtomically wrote {len(full_rows):,} observation cells, "
        f"{len(full_metadata):,} metadata records, "
        f"{len(full_manifest):,} page-manifest rows, and "
        f"{len(full_issues):,} issues, plus "
        f"{len(review_queue):,} manual-review cells to "
        f"{project_relative_path(OUTPUT_DIR)}."
    )


if __name__ == "__main__":
    main()
