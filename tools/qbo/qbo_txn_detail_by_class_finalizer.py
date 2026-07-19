#!/usr/bin/env python3
"""Finalize the Upload worksheet for the PFL transaction import.

This module is intended to run after:

    qbo_txn_detail_by_class_transformer.py
    qbo_txn_detail_by_class_dimensioner.py

It modifies the workbook in place by:

1. Keeping only rows whose QBO_Project is an approved Version 0.1 project.
2. Rebuilding the Upload worksheet with exactly these columns:

       PFL_Transaction_Key
       Organization
       Funding_Source
       Transaction_Date
       Transaction_Type
       Counter_Party
       Distribution_Account
       Memo_Description
       Amount

PFL_Trasaction_Key is intentionally duplicated from Funding_Source, following
Version 0.1 requirements.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from openpyxl import load_workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.worksheet.worksheet import Worksheet

UPLOAD_SHEET = "Upload"

FINAL_HEADERS = [
    "PFL_Transaction_Key",
    "Organization",
    "Funding_Source",
    "Transaction_Date",
    "Transaction_Type",
    "Counter_Party",
    "Distribution_Account",
    "Memo_Description",
    "Amount",
]

APPROVED_ORGANIZATIONS = {
    "ArviZ",
    "Astropy",
    "Bactopia",
    "biocommons",
    "Bioconductor",
    "Blosc",
    "Bokeh",
    "Cantera",
    "conda",
    "conda-forge",
    "CuPy",
    "Dask",
    "data.table",
    "Dynare",
    "Econ-ARK",
    "FEniCS",
    "Fortran-lang",
    "Gammapy",
    "GDAL",
    "GeoPandas",
    "GNU Octave",
    "Grant Witness",
    "GRASS",
    "HoloViz",
    "ITK",
    "Julia",
    "JuMP",
    "LFortran",
    "matplotlib",
    "MDAnalysis",
    "Micro-manager",
    "mlpack",
    "napari",
    "NetworkX",
    "nibabel",
    "nteract",
    "NumPy",
    "Open Journals",
    "OpenFHE",
    "OpenMBEE",
    "OpenProblems.bio",
    "pandas",
    "Pangeo",
    "Parsl",
    "PETSc",
    "PyBaMM",
    "PyMC",
    "PyTables",
    "QuantEcon",
    "rOpenSci",
    "Scientific Python",
    "scikit-image",
    "scikit-learn",
    "SciML",
    "SciPy",
    "scverse",
    "sgkit",
    "Spyder",
    "Stan",
    "SunPy",
    "SymPy",
    "TARDIS",
    "Vega",
    "VisPy",
    "WWT",
    "xarray",
    "yt",
    "Zarr",
}

APPROVED_ORGANIZATIONS_CASEFOLD = {
    organization.casefold(): organization for organization in APPROVED_ORGANIZATIONS
}

REQUIRED_SOURCE_HEADERS = {
    "Transaction_Date",
    "Transaction_Type",
    "Counter_Party",
    "Memo_Description",
    "Amount",
    "Distribution_Account",
    "QBO_Project",
    "QBO_Funding_Source",
}

HEADER_FILL = PatternFill("solid", fgColor="1F4E78")
HEADER_FONT = Font(color="FFFFFF", bold=True)


def text(value: Any) -> str:
    return "" if value is None else str(value).strip()


def header_map(ws: Worksheet) -> dict[str, int]:
    """Return a mapping of header name to one-based column number."""
    result: dict[str, int] = {}
    for cell in ws[1]:
        name = text(cell.value)
        if name:
            result[name] = cell.column
    return result


def validate_upload_sheet(ws: Worksheet) -> dict[str, int]:
    """Validate the source Upload worksheet and return its header map."""
    headers = header_map(ws)
    missing = sorted(REQUIRED_SOURCE_HEADERS - headers.keys())
    if missing:
        raise ValueError(
            "Upload worksheet is missing required column(s): " + ", ".join(missing)
        )
    return headers


def approved_organization(value: Any) -> bool:
    """Use case-insensitive exact matching against the Version 0.1 project list."""
    return text(value).casefold() in APPROVED_ORGANIZATIONS_CASEFOLD


def collect_final_rows(ws: Worksheet, headers: dict[str, int]) -> tuple[list[list[Any]], dict[str, int]]:
    """Filter project rows and construct the final nine-column row set."""
    final_rows: list[list[Any]] = []
    kept = 0
    removed = 0
    skipped_blank = 0

    for row_number in range(2, ws.max_row + 1):
        organization = ws.cell(row_number, headers["QBO_Project"]).value

        if text(organization) == "":
            skipped_blank += 1
            continue

        if not approved_organization(organization):
            removed += 1
            continue

        funding_source = ws.cell(row_number, headers["QBO_Funding_Source"]).value

        final_rows.append(
            [
                funding_source,  # PFL_Trasaction_Key duplicates Funding_Source
                organization,    # QBO_Project renamed to Organization
                funding_source,
                ws.cell(row_number, headers["Transaction_Date"]).value,
                ws.cell(row_number, headers["Transaction_Type"]).value,
                ws.cell(row_number, headers["Counter_Party"]).value,
                ws.cell(row_number, headers["Distribution_Account"]).value,
                ws.cell(row_number, headers["Memo_Description"]).value,
                ws.cell(row_number, headers["Amount"]).value,
            ]
        )
        kept += 1

    return final_rows, {
        "rows_kept": kept,
        "rows_removed": removed,
        "rows_skipped_blank_organization": skipped_blank,
    }


def rebuild_upload_sheet(ws: Worksheet, final_rows: list[list[Any]]) -> None:
    """Replace the worksheet contents with the final PFL import layout."""
    if ws.max_row > 0:
        ws.delete_rows(1, ws.max_row)

    ws.append(FINAL_HEADERS)
    for row in final_rows:
        ws.append(row)

    for cell in ws[1]:
        cell.fill = HEADER_FILL
        cell.font = HEADER_FONT
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

    ws.freeze_panes = "A2"
    ws.auto_filter.ref = f"A1:I{ws.max_row}"
    ws.row_dimensions[1].height = 32

    widths = {
        "A": 45,
        "B": 28,
        "C": 45,
        "D": 15,
        "E": 20,
        "F": 32,
        "G": 38,
        "H": 70,
        "I": 16,
    }
    for column, width in widths.items():
        ws.column_dimensions[column].width = width

    for row_number in range(2, ws.max_row + 1):
        ws.cell(row_number, 4).number_format = "mm/dd/yyyy"
        ws.cell(row_number, 9).number_format = "#,##0.00;[Red]-#,##0.00"


def finalize_upload(workbook_path: Path) -> dict[str, int]:
    """Finalize the Upload worksheet in place and return processing counts."""
    workbook_path = Path(workbook_path).expanduser().resolve()

    if workbook_path.suffix.lower() != ".xlsx":
        raise ValueError("Finalizer input must be an .xlsx workbook.")
    if not workbook_path.exists():
        raise FileNotFoundError(f"Workbook does not exist: {workbook_path}")
    if not workbook_path.is_file():
        raise ValueError(f"Workbook path is not a file: {workbook_path}")

    workbook = load_workbook(workbook_path)
    try:
        if workbook.sheetnames != [UPLOAD_SHEET]:
            raise ValueError(
                'Workbook must contain exactly one worksheet named "Upload"; '
                f"found: {', '.join(workbook.sheetnames) or '(none)'}"
            )

        ws = workbook[UPLOAD_SHEET]
        headers = validate_upload_sheet(ws)
        final_rows, counts = collect_final_rows(ws, headers)
        rebuild_upload_sheet(ws, final_rows)
        workbook.save(workbook_path)
    finally:
        workbook.close()

    return counts


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        print(
            "Usage: python3 qbo_txn_detail_by_class_finalizer.py <workbook.xlsx>",
            file=sys.stderr,
        )
        return 2

    workbook_path = Path(argv[0])

    try:
        counts = finalize_upload(workbook_path)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print(f"Finalized: {workbook_path.expanduser().resolve()}")
    print(f"Rows kept: {counts['rows_kept']}")
    print(f"Rows removed: {counts['rows_removed']}")
    print(
        "Rows skipped for blank Organization: "
        f"{counts['rows_skipped_blank_organization']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
