#!/usr/bin/env python3

import argparse
import math
from pathlib import Path


DEFAULT_CHUNK_COUNT = 5


def chunk_limit_for_count(input_path: Path, chunk_count: int) -> int:
    total_bytes = input_path.stat().st_size
    largest_line = 0

    with input_path.open("rb") as source:
        for line in source:
            largest_line = max(largest_line, len(line))

    return math.ceil(total_bytes / chunk_count) + largest_line


def split_jsonl(input_path: Path, output_dir: Path, max_bytes: int) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    prefix = f"{input_path.stem}.part_"

    for existing_chunk in output_dir.glob(f"{prefix}*.jsonl"):
        existing_chunk.unlink()

    chunk_paths = []
    chunk_handle = None
    chunk_size = 0
    chunk_number = 0

    try:
        with input_path.open("rb") as source:
            for line in source:
                if chunk_handle is None or (
                    chunk_size > 0 and chunk_size + len(line) > max_bytes
                ):
                    if chunk_handle is not None:
                        chunk_handle.close()

                    chunk_number += 1
                    chunk_path = output_dir / f"{prefix}{chunk_number:03d}.jsonl"
                    chunk_paths.append(chunk_path)
                    chunk_handle = chunk_path.open("wb")
                    chunk_size = 0

                chunk_handle.write(line)
                chunk_size += len(line)
    finally:
        if chunk_handle is not None:
            chunk_handle.close()

    return chunk_paths


def main() -> None:
    script_dir = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(
        description="Split ocr_raw.jsonl into smaller files without splitting JSONL records."
    )
    parser.add_argument(
        "input",
        nargs="?",
        type=Path,
        default=script_dir / "ocr_raw.jsonl",
        help="Input JSONL file (default: ocr_raw.jsonl beside this script).",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=script_dir / "ocr_raw_chunks",
        help="Directory for chunk files (default: ocr_raw_chunks beside this script).",
    )
    size_group = parser.add_mutually_exclusive_group()
    size_group.add_argument(
        "--chunks",
        type=int,
        help=(
            "Maximum number of chunks. The default is 5, leaving fifteen of "
            "ChatGPT's 20 upload slots available for other files."
        ),
    )
    size_group.add_argument(
        "--max-mb",
        type=float,
        help="Optional explicit maximum target chunk size in MiB.",
    )
    args = parser.parse_args()

    input_path = args.input.expanduser().resolve()
    output_dir = args.output_dir.expanduser().resolve()

    if not input_path.is_file():
        parser.error(f"Input file does not exist: {input_path}")
    if args.chunks is not None and args.chunks <= 0:
        parser.error("--chunks must be greater than zero")
    if args.max_mb is not None and args.max_mb <= 0:
        parser.error("--max-mb must be greater than zero")

    if args.max_mb is not None:
        max_bytes = int(args.max_mb * 1024 * 1024)
        sizing_description = f"targeting at most {args.max_mb:g} MiB each"
    else:
        chunk_count = args.chunks or DEFAULT_CHUNK_COUNT
        max_bytes = chunk_limit_for_count(input_path, chunk_count)
        sizing_description = f"targeting no more than {chunk_count} chunks"

    chunk_paths = split_jsonl(input_path, output_dir, max_bytes)

    print(
        f"Created {len(chunk_paths)} chunks in {output_dir}, "
        f"{sizing_description}"
    )
    for chunk_path in chunk_paths:
        size_mb = chunk_path.stat().st_size / (1024 * 1024)
        print(f"{chunk_path.name}: {size_mb:.2f} MiB")


if __name__ == "__main__":
    main()
