# -*- coding: utf-8 -*-
"""
Shared, cross-platform configuration for the Build/ and Analysis/ pipelines.

Paths and the database connection are resolved from environment variables so the
code runs on any OS and no credentials live in source control. Sensible defaults
place the ``Data/`` and ``Output/`` trees at the repository root.

Environment variables
---------------------
HOMELESSNESS_DATA_DIR    Directory for input/intermediate data   (default: <repo>/Data)
HOMELESSNESS_OUTPUT_DIR  Directory for models/figures            (default: <repo>/Output)
HOMELESSNESS_DB_CONN     pyodbc connection string for the HMIS warehouse (required
                         only by the Build/ scripts that query the database).
"""
import os
from pathlib import Path

# Repository root = parent of the Build/ directory this file lives in.
_REPO_ROOT = Path(__file__).resolve().parent.parent

DATA_DIR = Path(os.environ.get("HOMELESSNESS_DATA_DIR", _REPO_ROOT / "Data"))
OUTPUT_DIR = Path(os.environ.get("HOMELESSNESS_OUTPUT_DIR", _REPO_ROOT / "Output"))

MODELS_DIR = OUTPUT_DIR / "models"
FIGURES_DIR = OUTPUT_DIR / "figures"
COUNTERFACTUALS_DIR = FIGURES_DIR / "Counterfactuals"
COMPONENTS_DIR = DATA_DIR / "components"

# Create the directories so writes succeed on a fresh checkout.
for _d in (DATA_DIR, OUTPUT_DIR, MODELS_DIR, FIGURES_DIR, COUNTERFACTUALS_DIR,
           COMPONENTS_DIR):
    _d.mkdir(parents=True, exist_ok=True)


def get_connection():
    """Return a pyodbc connection to the HMIS warehouse.

    The connection string is read from the ``HOMELESSNESS_DB_CONN`` environment
    variable. Raises a clear error if it is not set rather than failing deep
    inside a query.
    """
    conn_str = os.environ.get("HOMELESSNESS_DB_CONN")
    if not conn_str:
        raise RuntimeError(
            "Set the HOMELESSNESS_DB_CONN environment variable to a valid pyodbc "
            "connection string for the HMIS warehouse before running the Build "
            "scripts that query the database."
        )
    import pyodbc
    return pyodbc.connect(conn_str)
