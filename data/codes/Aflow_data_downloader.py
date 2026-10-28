#!/usr/bin/env python3
"""
AFLOW Data Downloader (AFLUX API)
=================================

Downloads the requested properties for every entry returned by the AFLOW
AFLUX API (https://aflow.org), page by page, and saves them to ONE CSV file
inside a folder you choose (created if it does not exist).
No filters are applied: everything the query returns is saved.

Works on PCs (Windows / macOS / Linux) and HPC clusters (SLURM / PBS / LSF / SGE).
The AFLOW public API needs no API key, but the compute node must be able to
reach https://aflow.org.

Usage
-----
    pip install -r requirements_aflow.txt
    python AFLOW_data_downloader.py

You will be asked where to save the data and what to call the folder.
For non-interactive / batch (HPC) runs, set environment variables instead:
    AFLOW_OUTPUT_DIR   directory in which the output folder is created
    AFLOW_FOLDER_NAME  (optional) name of the output folder
"""

import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request, urlopen

import pandas as pd

try:
    from tqdm.auto import tqdm
except ImportError:  # tqdm is optional
    tqdm = None

# ----------------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------------
SERVER = "https://aflow.org"
API = "/API/aflux/?"

MAX_RETRIES = 4          # attempts (with exponential back-off) per page
TIMEOUT_SECONDS = 120    # network timeout per request
PAUSE_BETWEEN_PAGES = 0  # seconds to wait between pages (raise if AFLOW throttles you)
PAGE_SIZE = None         # None = AFLOW default page size; or an int to request that many
                         # entries per page via $paging(page,size)
OUTPUT_FILE_NAME = "AFLOW_data.csv"

FIELDS = [
    "auid",
    "nspecies(*)",
    "compound",
    "crystal_family(*)",
    "density(*)",
    "bader_net_charges",
    "bader_atomic_volumes",
    "spin_atom",
    "natoms(*)",
    "nbondxx",
    "Egap(*)",
    "energy_atom(*)",
    "energy_cell",
    "enthalpy_atom(*)",
    "enthalpy_cell",
    "enthalpy_formation_cell",
    "entropic_temperature",
    "ael_bulk_modulus_reuss(*)",
    "ael_bulk_modulus_voigt(*)",
    "ael_bulk_modulus_vrh(*)",
    "ael_debye_temperature(*)",
    "ael_elastic_anisotropy(*)",
    "ael_poisson_ratio(*)",
    "ael_pughs_modulus_ratio(*)",
    "ael_shear_modulus_reuss(*)",
    "ael_shear_modulus_voigt(*)",
    "ael_shear_modulus_vrh(*)",
    "ael_speed_sound_average",
    "ael_speed_sound_longitudinal",
    "ael_speed_sound_transverse",
    "ael_stiffness_tensor",
    "ael_youngs_modulus_vrh(*)",
    "agl_acoustic_debye",
    "agl_debye(*)",
    "agl_heat_capacity_Cp_300K(*)",
    "agl_heat_capacity_Cv_300K(*)",
    "agl_thermal_conductivity_300K(*)",
    "agl_thermal_expansion_300K",
    "agl_vibrational_entropy_300K_atom",
    "agl_vibrational_entropy_300K_cell",
    "agl_vibrational_free_energy_300K_atom",
    "agl_vibrational_free_energy_300K_cell",
    "Pearson_symbol_orig",
    "point_group_Schoenflies_orig",
    "point_group_structure_orig",
    "point_group_type_orig",
    "spacegroup_orig",
    "species",
    "volume_atom(*)",
    "volume_cell(*)",
]


# ----------------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------------
def detect_environment():
    hpc_vars = ("SLURM_JOB_ID", "PBS_JOBID", "LSB_JOBID", "SGE_TASK_ID")
    is_hpc = any(v in os.environ for v in hpc_vars)
    print(f"Python {sys.version.split()[0]} | pandas {pd.__version__} | "
          f"environment: {'HPC job' if is_hpc else 'PC / interactive'}")


def ask(prompt, default=None, env=None):
    """Ask the user; fall back to an environment variable or default when non-interactive."""
    if env and os.environ.get(env):
        print(f"{prompt}: using environment variable {env}")
        return os.environ[env].strip()
    label = prompt + (f" [default: {default}]" if default else "") + ": "
    try:
        answer = input(label).strip()
    except (EOFError, RuntimeError):  # no stdin (batch mode)
        if default is not None:
            print(f"{prompt}: non-interactive session, using default '{default}'")
            return default
        raise RuntimeError(
            f"No interactive input available for '{prompt}'. Set the environment variable {env}."
        )
    return answer or (default if default is not None else "")


def prompt_user():
    base_dir = Path(ask("Directory where the output folder will be created",
                        default=os.getcwd(), env="AFLOW_OUTPUT_DIR")).expanduser().resolve()
    base_dir.mkdir(parents=True, exist_ok=True)

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    folder_name = ask("Name of the output folder",
                      default=f"AFLOW_data_{stamp}", env="AFLOW_FOLDER_NAME")
    output_dir = base_dir / folder_name
    if output_dir.exists():
        print(f"Folder already exists, saving into it: {output_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)  # reuse the folder if it already exists

    output_file = output_dir / OUTPUT_FILE_NAME
    if output_file.exists():
        print("Note: a CSV file with this name already exists and will be replaced.")
    print(f"Output will be saved to: {output_file}")
    return output_file


def build_url(matchbook, page):
    paging = f"$paging({page})" if PAGE_SIZE is None else f"$paging({page},{PAGE_SIZE})"
    query = f"{matchbook},{paging},format(json)"
    return f"{SERVER}{API}{quote(query, safe='(),$')}"


def fetch_page(url):
    """Download one page and return a list of records (empty list = no more data)."""
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urlopen(req, timeout=TIMEOUT_SECONDS) as response:
                data = json.loads(response.read().decode("utf-8"))
            if not data:
                return []
            if isinstance(data, dict):  # AFLUX may return {index: record}
                data = list(data.values())
            return data
        except Exception as exc:
            if attempt == MAX_RETRIES:
                raise
            wait = 2 ** attempt
            print(f"  Request failed ({exc}); retry {attempt}/{MAX_RETRIES - 1} in {wait}s")
            time.sleep(wait)


# ----------------------------------------------------------------------------
# Download
# ----------------------------------------------------------------------------
def download_and_save(output_file):
    matchbook = ",".join(FIELDS)
    page, total_rows = 1, 0
    columns = None          # CSV header, fixed by the first page
    extra_columns = set()   # columns that appeared later but are not in the header
    bar = tqdm(desc="AFLOW pages", unit="page") if tqdm else None

    try:
        while True:
            try:
                records = fetch_page(build_url(matchbook, page))
            except Exception as exc:
                print(f"\nERROR: page {page} failed permanently: {exc}")
                print(f"The file is incomplete ({total_rows} rows saved from pages 1-{page - 1}). "
                      "Re-run the script to download again.")
                break

            if not records:
                print("\nNo more data.")
                break

            df_page = pd.DataFrame(records)
            if columns is None:
                columns = list(df_page.columns)
            else:
                extra_columns.update(set(df_page.columns) - set(columns))
                df_page = df_page.reindex(columns=columns)  # keep every page aligned

            df_page.to_csv(output_file, mode="w" if page == 1 else "a",
                           index=False, header=(page == 1), encoding="utf-8")
            total_rows += len(df_page)

            if bar is not None:
                bar.update(1)
                bar.set_postfix(rows=total_rows)
            else:
                print(f"Page {page} saved. Total rows so far: {total_rows}")

            page += 1
            if PAUSE_BETWEEN_PAGES:
                time.sleep(PAUSE_BETWEEN_PAGES)
    finally:
        if bar is not None:
            bar.close()
            
    if extra_columns:
        print(f"Note: these columns appeared after page 1 and were not saved: {sorted(extra_columns)}")
    return total_rows


def main():
    detect_environment()
    output_file = prompt_user()
    total_rows = download_and_save(output_file)
    if total_rows:
        print(f"DATA SAVED: {output_file}")
        print(f"Total rows: {total_rows}")
    else:
        print("No data was saved.")


if __name__ == "__main__":
    main()