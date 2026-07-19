#!/usr/bin/env python3
"""Orchestrate the QBO transaction-detail-by-class transformation pipeline."""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path

from openpyxl import load_workbook

from qbo_txn_detail_by_class_dimensioner import dimension_upload
from qbo_txn_detail_by_class_finalizer import finalize_upload
from qbo_txn_detail_by_class_transformer import transform_report


@dataclass(frozen=True)
class PipelinePaths:
    input_path: Path
    output_directory: Path
    output_path: Path


def parse_args(argv):
    parser = argparse.ArgumentParser(
        description="Run the complete QBO transaction migration pipeline."
    )
    parser.add_argument("input_file")
    parser.add_argument("output_directory")
    parser.add_argument("output_name")
    return parser.parse_args(argv)


def validate_source_workbook(input_path: Path):
    if input_path.suffix.lower() not in {".xlsx", ".xlsm"}:
        raise ValueError("Input file must be an .xlsx or .xlsm workbook.")
    if not input_path.exists():
        raise FileNotFoundError(input_path)
    wb = load_workbook(input_path, read_only=True)
    try:
        if len(wb.sheetnames) != 1:
            raise ValueError("Input workbook must contain exactly one worksheet.")
    finally:
        wb.close()


def normalize_output_name(name: str) -> str:
    name = name.strip()
    if not name:
        raise ValueError("Output name cannot be blank.")
    if Path(name).name != name:
        raise ValueError("Output name must not contain directories.")
    if not name.lower().endswith(".xlsx"):
        name += ".xlsx"
    return name


def validate_parameters(args):
    input_path = Path(args.input_file).expanduser().resolve()
    output_dir = Path(args.output_directory).expanduser().resolve()

    validate_source_workbook(input_path)

    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / normalize_output_name(args.output_name)

    return PipelinePaths(
        input_path=input_path,
        output_directory=output_dir,
        output_path=output_path,
    )


def run_pipeline(paths):
    print("Step 1 complete: Parameters validated.")

    print("Step 2: Transforming report...")
    transform_counts = transform_report(paths.input_path, paths.output_path)

    print("Step 3: Populating QBO dimensions...")
    dimension_counts = dimension_upload(paths.output_path)

    print("Step 4: Finalizing Upload worksheet...")
    finalizer_counts = finalize_upload(paths.output_path)

    return transform_counts, dimension_counts, finalizer_counts


def main(argv):
    try:
        paths = validate_parameters(parse_args(argv))
        t, d, f = run_pipeline(paths)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print("\nPipeline completed successfully.")
    print(f"Saved: {paths.output_path}")
    print(t)
    print(d)
    print(f)

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
