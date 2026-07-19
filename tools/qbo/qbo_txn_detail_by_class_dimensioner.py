#!/usr/bin/env python3
"""Populate QBO dimension fields on the Upload worksheet.

This module is called after qbo_txn_detail_by_class_transformer.py creates the
output workbook. It modifies that workbook in place and populates:

    QBO_Project
    QBO_Class
    QBO_Location
    QBO_Funding_Source
    QBO_Service_Agreement
    QBO_Program_Initiative
    QBO_Account

Rows that cannot be mapped are marked in Review_Flag.
"""
from __future__ import annotations

import sys
from datetime import datetime, date
from pathlib import Path
from typing import Any, Optional

from openpyxl import load_workbook
from openpyxl.worksheet.worksheet import Worksheet

COL = {
    "Transaction_Date": "B",
    "Counter_Party": "E",
    "Memo_Description": "G",
    "Class_Full_Name": "L",
    "Distribution_Account": "O",
    "Backup_Class_2": "R",
    "Data_Row_1": "S",
    "SDG_Round": "X",
    "Derived_Class": "Y",
    "QBO_Project": "Z",
    "QBO_Class": "AA",
    "QBO_Location": "AB",
    "QBO_Funding_Source": "AC",
    "QBO_Service_Agreement": "AD",
    "QBO_Program_Initiative": "AE",
    "QBO_Account": "AF",
    "Deleted_Class": "AG",
    "Review_Flag": "AH",
}

DEFAULT_CLASS = "Program Services"
DEFAULT_LOCATION = "Fiscal Sponsorship"
DEFAULT_FUNDING = "General - Unrestricted"


def is_blank(value: Any) -> bool:
    return value is None or str(value).strip() == ""


def text(value: Any) -> str:
    return "" if value is None else str(value).strip()


def norm(value: Any) -> str:
    return text(value).casefold()


def starts(value: str, prefix: str) -> bool:
    return norm(value).startswith(prefix.casefold())


def contains(value: str, needle: str) -> bool:
    return needle.casefold() in norm(value)


def clean_deleted_marker(value: str) -> str:
    """Remove legacy QBO '(deleted)' marker from new dimension fields."""
    cleaned = text(value).replace("(deleted)", "")
    return " ".join(cleaned.split())


def is_number(value: Any) -> bool:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return True
    try:
        float(str(value).strip())
        return True
    except Exception:
        return False


def as_date(value: Any) -> Optional[date]:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if is_blank(value):
        return None
    for fmt in ("%m/%d/%Y", "%Y-%m-%d", "%m-%d-%Y", "%m/%d/%y"):
        try:
            return datetime.strptime(str(value).strip(), fmt).date()
        except ValueError:
            pass
    return None


def on_or_after(value: Any, year: int, month: int, day: int) -> bool:
    parsed = as_date(value)
    return parsed is not None and parsed >= date(year, month, day)


def fiscal_year_by_cutoff(value: Any, cutoffs: list[tuple[date, int]], fallback: int) -> int:
    parsed = as_date(value)
    if parsed is None:
        return fallback
    for cutoff, year in sorted(cutoffs, reverse=True):
        if parsed >= cutoff:
            return year
    return fallback


def year_from_text(value: str, fallback: Optional[int] = None) -> Optional[int]:
    for year in (2027, 2026, 2025, 2024, 2023):
        if str(year) in value:
            return year
    return fallback


def set_qbo(ws: Worksheet, row: int, project: str, qbo_class: str, location: str,
            funding_source: str, service_agreement: str = "", program_initiative: str = "") -> None:
    ws[f"{COL['QBO_Project']}{row}"] = clean_deleted_marker(project)
    ws[f"{COL['QBO_Class']}{row}"] = qbo_class
    ws[f"{COL['QBO_Location']}{row}"] = location
    ws[f"{COL['QBO_Funding_Source']}{row}"] = clean_deleted_marker(funding_source)
    ws[f"{COL['QBO_Service_Agreement']}{row}"] = clean_deleted_marker(service_agreement)
    ws[f"{COL['QBO_Program_Initiative']}{row}"] = clean_deleted_marker(program_initiative)


def append_memo(ws: Worksheet, row: int, addition: str) -> None:
    cell = ws[f"{COL['Memo_Description']}{row}"]
    current = text(cell.value)
    if not addition:
        return
    if addition in current:
        return
    cell.value = addition if current == "" else f"{current} | {addition}"


def preserve_legacy_detail(ws: Worksheet, row: int) -> None:
    class_full_name = text(ws[f"{COL['Class_Full_Name']}{row}"].value)
    backup_class = text(ws[f"{COL['Backup_Class_2']}{row}"].value)
    derived_class = text(ws[f"{COL['Derived_Class']}{row}"].value)
    distribution_account = text(ws[f"{COL['Distribution_Account']}{row}"].value)
    save_class = class_full_name or backup_class or derived_class
    append_memo(ws, row, f"Legacy Class: {save_class} | Legacy Distribution Account: {distribution_account}")


def sdg_initiative(ws: Worksheet, row: int, derived_class: str, distribution_account: str) -> str:
    if (
        distribution_account == "5813 Small Development Grants"
        or contains(distribution_account, "Small Development Grants")
        or contains(derived_class, "SDG")
        or contains(derived_class, "Small Development Grants")
    ):
        sdg_round = text(ws[f"{COL['SDG_Round']}{row}"].value)
        if sdg_round:
            append_memo(ws, row, f"SDG Legacy Round: {sdg_round}")
        return "SDG"
    return ""


def sdg_year(derived_class: str, transaction_date: Any) -> int:
    for year in (2026, 2025, 2024, 2023):
        if str(year) in derived_class:
            return year
    if on_or_after(transaction_date, 2025, 1, 1):
        return 2025
    if on_or_after(transaction_date, 2024, 1, 1):
        return 2024
    return 2023


def sdg_funding_base(derived_class: str, transaction_date: Any) -> str:
    return f"Small Development Grants {sdg_year(derived_class, transaction_date)}"


def sdg_program_initiative(derived_class: str, transaction_date: Any) -> str:
    return f"SDG {sdg_year(derived_class, transaction_date)}"

def handle_programs(ws: Worksheet, row: int, derived_class: str, transaction_date: Any) -> bool:
    if starts(derived_class, "GSoD -") or starts(derived_class, "GSoC -"):
        project = "NumFOCUS Core"

        for candidate in (
            "ArviZ",
            "Fortran-lang",
            "GNU Octave",
            "Julia",
            "MDAnalysis",
            "Mesa",
            "mlpack",
            "NumPy",
            "Open Astronomy",
            "rOpenSci",
            "SymPy",
            "TARDIS",
        ):
            if contains(derived_class, candidate):
                project = candidate
                break

        candidate_years = ["2023", "2024", "2025", "2026"]
        year = next((y for y in candidate_years if y in derived_class), None)

        if year is None:
            year = fiscal_year_by_cutoff(
                transaction_date,
                [(date(2026, 1, 1), 2026), (date(2025, 1, 1), 2025)],
                2024,
            )

        if starts(derived_class, "GSoD -"):
            funding_program = "Google Season of Docs"
            initiative = f"GSoD {year}"
        else:
            funding_program = "Google Summer of Code"
            initiative = f"GSoC {year}"

        set_qbo(
            ws,
            row,
            project,
            DEFAULT_CLASS,
            DEFAULT_LOCATION,
            f"{project} | {funding_program} {year}",
            "",
            initiative,
        )
        return True

    if derived_class == "Bloomberg Open Source Sustainability Series":
        year = fiscal_year_by_cutoff(transaction_date, [(date(2026, 1, 1), 2026), (date(2025, 1, 1), 2025)], 2024)
        set_qbo(ws, row, "NumFOCUS Core", DEFAULT_CLASS, DEFAULT_LOCATION,
                f"Bloomberg OS Sustainability Series {year}", "", "Bloomberg OS Sustainability Series")
        return True

    if derived_class == "OSSci":
        set_qbo(ws, row, "OSSci", DEFAULT_CLASS, DEFAULT_LOCATION, f"OSSci | {DEFAULT_FUNDING}", "", "OSSci")
        return True

    return False


def handle_admin_and_fundraising(ws: Worksheet, row: int, derived_class: str) -> bool:
    if derived_class == "NUMFOCUS-CZI 2020-219367":
        project = "NumFOCUS Core"
        set_qbo(
            ws,
            row,
            project,
            "Management & General",
            "NumFOCUS Operations",
            f"{project} | CZI 2020-219367",
            "",
            "",
        )
        return True

    admin_exact = {"01 ADMIN", "Admin", "NUMFOCUS ADMIN", "Board Benefit"}
    if derived_class in admin_exact:
        set_qbo(ws, row, "NumFOCUS Core", "Management & General", "NumFOCUS Operations",
                "NumFOCUS Core | General - Unrestricted")
        return True

    if derived_class == "Sloan G-2020-13954 (NumFOCUS Academy)":
        set_qbo(
            ws,
            row,
            "NumFOCUS Core",
            DEFAULT_CLASS,
            "Grant",
            "NumFOCUS Core | Sloan G-2020-13954",
            "",
            "NumFOCUS Academy",
        )
        return True

    numfocus_programs = {
        "JHT FELLOWSHIP": ("JHT | JHT Fellowship", "JHT Fellowship"),
        "05 Special Projects T3 Training Up": ("NumFOCUS | Special Projects | T3 Training Up", "NumFOCUS Special Projects"),
        "Admin - MOORE 6207": ("NumFOCUS | Admin - MOORE 6207", "Admin - MOORE 6207"),
        "Special Projects Data Carpentry": ("NumFOCUS Core | Special Projects | Data Carpentry", "NumFOCUS Special Projects"),
        "Special Projects Women in Technology": ("NumFOCUS Core | Special Projects | Women in Technology", "NumFOCUS Special Projects"),
        "Software Carpentry": ("NumFOCUS Core | Special Projects | Software Carpentry", "NumFOCUS Special Projects"),
        "R Consortium": ("R Consortium", "R Consortium"),
        "NumFOCUS CZI 2020-219367": ("NumFOCUS | CZI 2020-219367", "NumFOCUS Special Projects"),
        "Meetup General": ("NumFOCUS | General - Unrestricted", ""),
        "PyData General": ("PyData | General - Unrestricted", "PyData"),
    }
    if derived_class in numfocus_programs:
        funding, initiative = numfocus_programs[derived_class]
        set_qbo(ws, row, "NumFOCUS Core", DEFAULT_CLASS, DEFAULT_LOCATION, funding, "", initiative)
        return True

    if derived_class in {"Fundraising General", "Fundraising Event"}:
        set_qbo(ws, row, "Fundraising", "Fundraising", "Fundraising",
                "Fundraising | General - Unrestricted")
        return True

    if derived_class == "05A Small Development Grants":
        transaction_date = ws[f"{COL['Transaction_Date']}{row}"].value
        set_qbo(
            ws,
            row,
            "NumFOCUS Core",
            DEFAULT_CLASS,
            DEFAULT_LOCATION,
            project_funding_source("NumFOCUS Core", sdg_funding_base(derived_class, transaction_date)),
            "",
            sdg_program_initiative(derived_class, transaction_date),
        )
        return True

    return False

def handle_events(ws: Worksheet, row: int, derived_class: str, transaction_date: Any) -> bool:
    event = None
    initiative = ""
    service = ""
    funding_suffix = "General - Unrestricted"

    if derived_class == "BioCon 2026":
        year = "2026"
        event = f"BioConductor Conference {year}"

    elif derived_class == "BioCon":
        year = fiscal_year_by_cutoff(transaction_date, [(date(2026, 2, 1), 2026), (date(2025, 2, 1), 2025)], 2024)
        event = f"BioConductor Conference {year}"
    
    elif derived_class == "Dask Summit":
        event = "DASK Summit Conference 2024"
    
    elif derived_class in {"DISC Unconference", "Disc Unconf CZI 2024-345566", "DISC Unconf Sloan G-2024-22663", "Moore 9113 DISC", "DISC Unconference - CZI 2020-219367", "DISC"}:
        event = "DISC Unconference 2025" if on_or_after(transaction_date, 2024, 7, 1) else "DISC Unconference 2023"
        initiative = "DISC"
        special = {
            "Disc Unconf CZI 2024-345566": "CZI 2024-345566",
            "DISC Unconf Sloan G-2024-22663": "Sloan G-2024-22663",
            "Moore 9113 DISC": "Moore 9113",
            "DISC Unconference - CZI 2020-219367": "CZI 2020-219367",
        }
        funding_suffix = special.get(derived_class, "General - Unrestricted")
    
   
    elif starts(derived_class, "GRASS Developer Summit"):
        year = 2026 if on_or_after(transaction_date, 2026, 5, 1) else 2025
        event = f"GRASS Developer Summit {year}"
    
    elif derived_class == "JuliaCon Global 2026":
        year = 2026
        event = f"Julia Global Conference {year}"

    elif derived_class == "JuliaCon":
        year = fiscal_year_by_cutoff(transaction_date, [(date(2026, 3, 1), 2026), (date(2025, 3, 1), 2025)], 2024)
        event = f"Julia Conference {year}"
    
    elif starts(derived_class, "JuliaCon Paris"):
        year = 2025 if derived_class == "JuliaCon Paris 2025" else fiscal_year_by_cutoff(transaction_date, [(date(2026, 4, 1), 2026), (date(2025, 4, 1), 2025)], 2024)
        event = f"Julia Paris Conference {year}"
    
    elif derived_class == "JuMP-dev 2024":
        event = "JuMP Developers Conference 2024"
    
    elif derived_class == "JupyterCon":
        event = "Jupiter Conference 2024"
    
    elif derived_class == "Meetup Leadership Summit":
        event = "Meetup Leadership Summit 2024"

    elif derived_class == "Ohio State/GOOD Conference 2026":
        year = "2026"
        event = f"GOOD Conference {year}"
        service = "GOOD Conference"

    elif derived_class == "Ohio State/GOOD Conference":
        year = fiscal_year_by_cutoff(transaction_date, [(date(2025, 10, 1), 2026), (date(2024, 10, 1), 2025)], 2024)
        event = f"GOOD Conference {year}"
        service = "GOOD Conference"
    
    elif starts(derived_class, "Open Problems Hackathon"):
        year = 2026 if on_or_after(transaction_date, 2026, 1, 1) else 2024
        event = f"Open Problems Hackaton {year}"

    elif derived_class == "ParslFest":
        event = "ParslFest Conference 2025"
    
    elif starts(derived_class, "PETSc User Group"):
        year = year_from_text(derived_class, 2025)
        event = f"PETSc User Group Conference {year}"

    elif derived_class == "PyCon DE":
        year = fiscal_year_by_cutoff(transaction_date, [(date(2025, 10, 1), 2026), (date(2024, 10, 1), 2025)], 2024)
        event = f"PyCon DE Conference {year}"
    
    elif derived_class == "PackagingCon":
        event = "PyCon Packaging Conference 2024"
    
    elif derived_class == "Project Summit":
        event = "NumFOCUS Project Summit 2024"

    elif derived_class == "PyCon US/EU":
        year = fiscal_year_by_cutoff(transaction_date, [(date(2025, 11, 1), 2026), (date(2024, 11, 1), 2025)], 2024)
        event = f"PyCon US-EU Conference {year}"

    elif derived_class == "AI Chicago":
        year = fiscal_year_by_cutoff(transaction_date, [(date(2026, 6, 1), 2026), (date(2025, 6, 1), 2025)], 2024)
        event = f"PyData AI Chicago Conference {year}"

    elif derived_class == "PyData Amsterdam 2026":
        year = "2026"
        event = f"PyData Amsterdam Conference {year}"

    elif derived_class == "PyData Amsterdam":
        year = fiscal_year_by_cutoff(transaction_date, [(date(2026, 3, 1), 2026), (date(2025, 3, 1), 2025)], 2024)
        event = f"PyData Amsterdam Conference {year}"

    elif derived_class == "PyData Berlin":
        year = fiscal_year_by_cutoff(transaction_date, [(date(2026, 3, 1), 2026), (date(2025, 3, 1), 2025)], 2024)
        event = f"PyData Berlin Conference {year}"

    elif derived_class == "PyData Boston":
        year = fiscal_year_by_cutoff(transaction_date, [(date(2026, 6, 1), 2026), (date(2025, 6, 1), 2025)], 2024)
        event = f"PyData Boston Conference {year}"
    
    elif derived_class == "PyData Burlington VT":
        year = fiscal_year_by_cutoff(transaction_date, [(date(2026, 4, 1), 2026), (date(2025, 4, 1), 2025)], 2024)
        event = f"PyData Burlington VT Conference {year}"
    
    elif derived_class == "PyData Chicago":
        year = fiscal_year_by_cutoff(transaction_date, [(date(2026, 1, 1), 2026), (date(2025, 1, 1), 2025)], 2024)
        event = f"PyData Chicago Conference {year}"
   
    elif derived_class == "PyData Eindhoven 2025":
        year = "2025"
        event = f"PyData Eindhoven Conference {year}"

    elif derived_class == "PyData Eindhoven 2026":
        year = "2026"
        event = f"PyData Eindhoven Conference {year}"

    elif starts(derived_class, "PyData Eindhoven"):
        year = fiscal_year_by_cutoff(transaction_date, [(date(2026, 7, 1), 2026), (date(2025, 7, 1), 2025)], 2024)
        event = f"PyData Eindhoven Conference {year}"
   
    elif derived_class == "PyData Global 2026":
        year = "2026"
        event = f"PyData Global Conference {year}"   

    elif derived_class == "PyData Global 2025":
        year = "2026"
        event = f"PyData Global Conference {year}"   

    elif starts(derived_class, "PyData Global"):
        year = fiscal_year_by_cutoff(transaction_date, [(date(2026, 6, 1), 2026), (date(2025, 6, 1), 2025)], 2024)
        event = f"PyData Global Conference {year}"

    elif derived_class == "PyData London 2026":
        year = "2026"
        event = f"PyData London Conference {year}"   

    elif derived_class == "PyData London":
        year = fiscal_year_by_cutoff(transaction_date, [(date(2025, 12, 1), 2026), (date(2024, 12, 1), 2025)], 2024)
        event = f"PyData London Conference {year}"
    
    elif derived_class == "NumHack":
        event = "PyData NumHack Hackathon 2024"
    
    elif derived_class == "PyData NYC":
        year = 2024 if on_or_after(transaction_date, 2024, 4, 1) else 2023
        event = f"PyData NYC Conference {year}"
    
    elif derived_class == "PyData Pittsburgh":
        year = 2024 if on_or_after(transaction_date, 2023, 10, 1) else 2023
        event = f"PyData Pittsburgh Conference {year}"

    elif derived_class == "PyData Seattle":
        year = fiscal_year_by_cutoff(transaction_date, [(date(2026, 6, 1), 2026), (date(2025, 6, 1), 2025)], 2024)
        event = f"PyData Seattle Conference {year}"

    elif derived_class == "PyData Tel Aviv 2026":
        year = "2026"
        event = f"PyData Tel Aviv Conference {year}"  

    elif derived_class == "PyData Tel Aviv":
        year = 2025 if on_or_after(transaction_date, 2025, 3, 1) else 2024
        event = f"PyData Tel Aviv Conference {year}"
    
    elif derived_class == "PyData Virginia":
        year = 2026 if on_or_after(transaction_date, 2026, 1, 1) else 2025
        event = f"PyData Virginia Conference {year}"

    elif derived_class == "SciPy 2025":
        year = "2026"
        event = f"SciPy Conference {year}"   

    elif derived_class == "SciPy 2026":
        year = "2026"
        event = f"SciPy Conference {year}"   

    elif starts(derived_class, "SciPy Conference"):
        year = fiscal_year_by_cutoff(transaction_date, [(date(2026, 1, 1), 2026), (date(2025, 1, 1), 2025)], 2024)
        event = f"SciPy Conference {year}"
    
    elif starts(derived_class, "scverse 2024 Conference"):
        year = "2024"
        event = f"scverse Conference {year}"
   
    elif starts(derived_class, "scverse 2025 Conference"):
        year = "2025"
        event = f"scverse Conference {year}"

    elif starts(derived_class, "scverse 2026 Conference"):
        year = "2026"
        event = f"scverse Conference {year}"

    elif derived_class == "StanCon":
        year = 2026 if on_or_after(transaction_date, 2026, 1, 1) else 2024
        event = f"Stan Conference {year}"
 
    if event is None:
        return False

    set_qbo(ws, row, event, DEFAULT_CLASS, "Event", f"{event} | {funding_suffix}", service, initiative)
    return True


PROJECT_RULES: list[tuple[str, str, str]] = [
    ("ArviZ", "ArviZ", "prefix"),
    ("Astropy", "Astropy", "prefix"),
    ("Bactopia", "Bactopia", "prefix"),
    ("Bioconductor", "Bioconductor", "prefix"),
    ("Blosc", "Blosc", "prefix"),
    ("Bokeh", "Bokeh", "prefix"),
    ("Cantera", "Cantera", "prefix"),
    ("Colour", "Colour Science", "prefix"),
    ("Conda General", "conda", "exact"),
    ("conda-forge", "conda-forge", "prefix"),
    ("CuPy", "CuPy", "prefix"),
    ("CVXPY", "CVXPY", "prefix"),
    ("Cython", "Cython", "prefix"),
    ("Dask General", "Dask", "exact"),
    ("data.table General", "data.table", "exact"),
    ("Dynare General", "Dynare", "exact"),
    ("Econ-ARK", "Econ-ARK", "prefix"),
    ("equadratures", "Effective Quadratures", "prefix"),
    ("FEniCS", "FEniCS", "prefix"),
    ("FluxML", "FluxML", "prefix"),
    ("Freemocap", "FreeMoCap Foundation", "prefix"),
    ("GDAL", "GDAL", "prefix"),
    ("GeomScale", "GeomScale", "prefix"),
    ("GeoPandas", "GeoPandas", "prefix"),
    ("GNU Octave", "GNU Octave", "prefix"),
    ("Grant Witness", "Grant Witness", "prefix"),
    ("GRASS General", "GRASS", "exact"),
    ("HoloViz", "HoloViz", "prefix"),
    ("HPX", "HPX", "prefix"),
    ("ITK", "ITK", "prefix"),
    ("Julia", "Julia", "prefix"),
    ("JuMP", "JuMP", "prefix"),
    ("Jupyter", "Jupyter", "prefix"),
    ("LFortran", "LFortran", "prefix"),
    ("Magpylib", "Magpylib", "prefix"),
    ("MathJax", "MathJax", "prefix"),
    ("matplotlib", "matplotlib", "prefix"),
    ("MDAnalysis", "MDAnalysis", "prefix"),
    ("Mesa", "Mesa", "prefix"),
    ("Micro-Manager", "Micro-Manager", "prefix"),
    ("mlpack", "mlpack", "prefix"),
    ("napari", "napari", "prefix"),
    ("NetworkX", "NetworkX", "prefix"),
    ("nibabel", "nibabel", "prefix"),
    ("NiBabel", "nibabel", "prefix"),
    ("nteract", "nteract", "prefix"),
    ("NumPy", "NumPy", "prefix"),
    ("Open Astronomy", "Open Astronomy", "prefix"),
    ("Open Journals", "Open Journals", "prefix"),
    ("OpenFHE", "OpenFHE", "prefix"),
    ("OpenMBEE", "OpenMBEE", "prefix"),
    ("Optimagic", "Optimagic", "prefix"),
    ("Orange", "Orange", "prefix"),
    ("pandas", "pandas", "prefix"),
    ("poliastro", "poliastro", "prefix"),
    ("PyBaMM", "PyBaMM", "prefix"),
    ("PyDMD", "PyDMD", "prefix"),
    ("pyhf", "pyhf", "prefix"),
    ("PyMC", "PyMC", "prefix"),
    ("PyTables", "PyTables", "prefix"),
    ("python-graphblas", "python-graphblas", "prefix"),
    ("PyTorch-Ignite", "PyTorch-Ignite", "prefix"),
    ("PyVista", "PyVista", "prefix"),
    ("QuantEcon", "QuantEcon", "prefix"),
    ("QuTip", "QuTip", "prefix"),
    ("R Consortium", "R Consortium", "prefix"),
    ("rOpenSci", "rOpenSci", "prefix"),
    ("Scientific Python", "Scientific Python", "prefix"),
    ("scikit-image", "scikit-image", "prefix"),
    ("scikit-learn", "scikit-learn", "prefix"),
    ("SciML", "SciML", "prefix"),
    ("SciPy", "SciPy", "prefix"),
    ("scverse", "scverse", "prefix"),
    ("sgkit", "sgkit", "prefix"),
    ("Shogun", "Shogun", "prefix"),
    ("sktime", "sktime", "prefix"), 
    ("Software Carpentry", "Software Carpentry", "prefix"),
    ("Spyder", "Spyder", "prefix"),
    ("Stan", "Stan", "prefix"),
    ("SunPy", "SunPy", "prefix"),
    ("SymPy", "SymPy", "prefix"),
    ("TARDIS", "TARDIS", "prefix"),
    ("Taskflow", "Taskflow", "prefix"),
    ("Vega", "Vega", "prefix"),
    ("VisPy", "VisPy", "prefix"),
    ("WorldWide Telescope", "WorldWide Telescope", "prefix"),
    ("WWT", "WorldWide Telescope", "prefix"),
    ("xarray", "xarray", "prefix"),
    ("yt General", "yt", "exact"),
    ("Zarr", "Zarr", "prefix"),
]

SPECIAL_FUNDING = {
    "ArviZ CZI 2021-237551": "CZI 2021-237551",
    "Astropy NASA ROSES20 80NSSC22K0347": "NASA ROSES20 80NSSC22K0347",
    "Astropy NNASA ROSES24 80NSSC25M7029": "NASA ROSES24 80NSSC25M7029",
    "Astropy Moore 8435": "Moore 8435",
    "Bactopia CZI 2024-344595": "CZI 2024-344595",
    "Bioconductor Scholarship Fund": "Bioconductor Scholarship Fund",
    "Bokeh CZI 2020-225259": "CZI 2020-225259",
    "Bokeh CZI 2022-309815": "CZI 2022-309815",
    "conda-forge CZI 2021-237432": "CZI 2021-237432",
    "conda-forge CZI 2022-309814": "CZI 2022-309814",
    "CuPy CZI 2022-309812": "CZI 2022-309812",
    "CVXYP NASA": "NASA",
    "Econ-ARK Sloan 9832": "loan 9832",
    "Econ-ARK Sloan G-2025-79177": "Sloan G-2025-79177",
    "Sloan G-2025-25312": "Sloan G-2025-25312",
    "ITK Wellcome 313320/Z/24/Z": "Wellcome 313320/Z/24/Z",
    "Julia 2024 NSF Center for Quantum Networks": "2024 NSF Center for Quantum Networks",
    "JuMP - Breakthrough Energy": "Breakthrough Energy",
    "JuMP - Breakthrough Energy GRIDS":"Breakthrough Energy GRIDS",
    "Jupyter (JupyterHub) CZI 2021-237021": "CZI 2021-237021 (JupyterHub)",
    "Jupyter (Pipyri) CZI 2021-237462": "CZI 2021-237462 (Pipyri)",
    "Jupyter Community Building": "Jupyter Community Building",
    "LFortran STF Grant 1": "STF Grant 1",
    "LFortran STF Grant 2": "STF Grant 2",
    "matplotlib CZI 2021-237562": "CZI 2021-237562",
    "NASA 80NSSC22K0348": "NASA 80NSSC22K0348",
    "MDAnalysis ASU NSF Subaward": "ASU NSF Subaward",
    "MDAnalysis ASU Subaward UGM 2025": "ASU Subaward UGM 2025",
    "CZI 2021-237663": "CZI 2021-237663",
    "MDAnalysis CZI 2022-309811": "CZI 2022-309811",
    "MDAnalysis CZI 2022 UGM 2025": "CZI 2022 UGM 2025",
    "Micro-Manager CZI 2024-344596": "CZI 2024-344596",
    "mlpack NASA 80NSSC24K1524": "NASA 80NSSC24K1524",
    "napari CZI 2022-316432": "CZI 2022-316432",
    "napari CZI 2024-355351": "CZI 2024-355351",
    "NetworkX Wellcome 313293/Z/24/Z": "Wellcome 313293/Z/24/Z",
    "Open Journals (JOSS) Sloan G-2020-13945": "Sloan G-2020-13945",
    "NumPy Fellowship Program": "Fellowship Program",
    "QuantEcon Schwab Charitable": "Schwab Charitable QuantEcon 2024",
    "Spyder CZI 2022-316698": "CZI 2022-316698",
    "scverse gget": "gget",
    "mlpack Sovereign Tech Fund": "Sovereign Tech Fund",
}

SPECIAL_SERVICE = {
    "Astropy STScI Glue": "Astropy STScI Glue",
    "Astropy - STSCI Kepler": "Astropy STSCI Kepler",
    "JuMP LANL": "JuMP LANL",
    "JuMP PSR": "JuMP PSR",
    "JuMP MIT": "JuMP MIT",
    "Jupyter Tidelift": "Jupyter Tidelift",
    "rOpenSci EpiVerse": "rOpenSci EpiVerse",
    "Spyder Tidelift": "Spyder Tidelift",
}

SPECIAL_INITIATIVE = {
    "Julia pluto.jl": "Julia: pluto.jl",
}


def match_project(derived_class: str) -> Optional[str]:
    for pattern, project, mode in PROJECT_RULES:
        if mode == "exact" and derived_class == pattern:
            return project
        if mode == "prefix" and starts(derived_class, pattern):
            if pattern == "JuMP" and derived_class == "JuMP-dev 2024":
                continue
            return project
    return None


def default_project_funding(derived_class: str, project: str = "") -> str:
    if derived_class in SPECIAL_FUNDING:
        return SPECIAL_FUNDING[derived_class]
    if derived_class.endswith(" General") or derived_class.endswith("General"):
        return DEFAULT_FUNDING

    # Carefully extract funding from project rows only when the remaining text
    # starts with a known funder/grant pattern. This avoids misclassifying
    # service-agreement rows like "JuMP LANL" as funding sources.
    if project and starts(derived_class, project):
        remainder = derived_class[len(project):].strip()
        if remainder.startswith("-"):
            remainder = remainder[1:].strip()

        known_funding_starts = (
            "CZI ",
            "Sloan ",
            "Moore ",
            "NASA ",
            "NSF ",
            "Wellcome ",
            "STF ",
            "Gordon and Betty Moore ",
            "Breakthrough Energy",
        )

        if remainder.startswith(known_funding_starts):
            return remainder

    return DEFAULT_FUNDING


def project_funding_source(project: str, funding_source: str) -> str:
    """Normal project rule: QBO_Funding_Source = QBO_Project + " | " + funding source.

    This helper is intentionally not used for the explicit exceptions:
    Bloomberg, the special NumFOCUS program block, and SDG rows.
    """
    funding_source = text(funding_source)
    if funding_source == "":
        funding_source = DEFAULT_FUNDING
    return f"{project} | {funding_source}"


def handle_projects(ws: Worksheet, row: int, derived_class: str, transaction_date: Any, distribution_account: str) -> bool:
    project = match_project(derived_class)
    if project is None:
        return False

    initiative = sdg_initiative(ws, row, derived_class, distribution_account)
    service = SPECIAL_SERVICE.get(derived_class, "")
    if derived_class in SPECIAL_INITIATIVE and initiative == "":
        initiative = SPECIAL_INITIATIVE[derived_class]

    if initiative == "SDG":
        # SDG funding is project-specific, and the initiative carries the SDG year.
        funding = project_funding_source(project, sdg_funding_base(derived_class, transaction_date))
        initiative = sdg_program_initiative(derived_class, transaction_date)
    elif derived_class == "scverse Weizmann":
        if on_or_after(transaction_date, 2026, 1, 1):
            base_funding = "Weizmann Institute of Science 2026"
        elif on_or_after(transaction_date, 2025, 1, 1):
            base_funding = "Weizmann Institute of Science 2025"
        else:
            base_funding = "Weizmann Institute of Science 2024"
        funding = project_funding_source(project, base_funding)
    else:
        # Normal project rule: QBO_Funding_Source = QBO_Project + " | " + base funding source.
        base_funding = default_project_funding(derived_class, project)
        funding = project_funding_source(project, base_funding)

    set_qbo(ws, row, project, DEFAULT_CLASS, DEFAULT_LOCATION, funding, service, initiative)
    return True


def process_row(ws: Worksheet, row: int) -> str:
    #data_row = ws[f"{COL['Data_Row_1']}{row}"].value

    derived_class = text(ws[f"{COL['Derived_Class']}{row}"].value)
    
    # print(f"Processing: {derived_class}" )

    #if not is_number(data_row) or derived_class == "":
    if derived_class == "":
        return "skipped"

    transaction_date = ws[f"{COL['Transaction_Date']}{row}"].value
    distribution_account = text(ws[f"{COL['Distribution_Account']}{row}"].value)

    # The legacy mapping rules did not explicitly populate QBO_Account.
    # Carry the source distribution account into the new QBO account field.
    ws[f"{COL['QBO_Account']}{row}"] = clean_deleted_marker(distribution_account)

    preserve_legacy_detail(ws, row)

    if handle_programs(ws, row, derived_class, transaction_date):
        return "mapped"
    if handle_admin_and_fundraising(ws, row, derived_class):
        return "mapped"
    if handle_events(ws, row, derived_class, transaction_date):
        return "mapped"
    if handle_projects(ws, row, derived_class, transaction_date, distribution_account):
        return "mapped"

    ws[f"{COL['Review_Flag']}{row}"] = f"REVIEW: {derived_class}"
    print(f"UNMAPPED: {derived_class}")
    return "unmapped"


def dimension_upload(workbook_path: Path) -> dict[str, int]:
    """Populate QBO dimensions on the existing Upload worksheet in place."""
    workbook_path = Path(workbook_path)

    if workbook_path.suffix.lower() != ".xlsx":
        raise ValueError("Dimensioner input must be an .xlsx workbook.")
    if not workbook_path.exists():
        raise FileNotFoundError(workbook_path)
    if not workbook_path.is_file():
        raise ValueError(f"Dimensioner input is not a file: {workbook_path}")

    workbook = load_workbook(workbook_path)
    try:
        if workbook.sheetnames != ["Upload"]:
            raise ValueError(
                'Dimensioner input must contain exactly one worksheet named "Upload"; '
                f"found: {', '.join(workbook.sheetnames) or '(none)'}"
            )

        worksheet = workbook["Upload"]

        required_headers = {name: column for name, column in COL.items()}
        missing_headers = [
            name
            for name, column in required_headers.items()
            if text(worksheet[f"{column}1"].value) != name
        ]
        if missing_headers:
            raise ValueError(
                "Upload worksheet is missing or has misplaced required columns: "
                + ", ".join(missing_headers)
            )

        counts = {"mapped": 0, "unmapped": 0, "skipped": 0}
        for row in range(2, worksheet.max_row + 1):
            result = process_row(worksheet, row)
            counts[result] += 1

        workbook.save(workbook_path)
        return counts
    finally:
        workbook.close()


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        print(
            "ERROR: Expected one argument: path to the transformed Upload workbook.",
            file=sys.stderr,
        )
        return 2

    workbook_path = Path(argv[0]).expanduser().resolve()
    try:
        counts = dimension_upload(workbook_path)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print(f"Updated: {workbook_path}")
    print(f"Rows mapped: {counts['mapped']}")
    print(f"Rows unmapped: {counts['unmapped']}")
    print(f"Rows skipped: {counts['skipped']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
