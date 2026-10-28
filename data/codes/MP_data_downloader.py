#!/usr/bin/env python3
"""
Materials Project Data Downloader (Stable Materials + Elastic Properties)
=========================================================================

Downloads all thermodynamically stable materials from the Materials Project,
merges the summary and elasticity datasets, extracts derived columns
(bulk/shear moduli, symmetry, sound velocities, C11/C12/C44), applies quality
filters, and saves ONE CSV file inside a NEW folder at a location you choose.

Works on PCs (Windows / macOS / Linux) and HPC clusters (SLURM / PBS / LSF / SGE).

Usage
-----
    pip install -r requirements.txt
    python MP_data_downloader.py

You will be asked for your API key (hidden input) and the output location.
For non-interactive / batch (HPC) runs, set environment variables instead:
    MP_API_KEY      Materials Project API key
    MP_OUTPUT_DIR   directory in which the output folder is created
    MP_FOLDER_NAME  (optional) name of the output folder

Get an API key at: https://next-gen.materialsproject.org/api
Never hard-code or commit your API key.
"""

import ast
import getpass
import os
import sys
import time
import warnings
from datetime import datetime
from enum import Enum
from pathlib import Path

import numpy as np
import pandas as pd

try:
    from mp_api.client import MPRester
except ImportError:
    sys.exit("Missing dependencies. Install them first with:  pip install -r requirements.txt")

try:
    from tqdm.auto import tqdm
except ImportError:  # tqdm is optional
    def tqdm(iterable, **kwargs):
        return iterable

warnings.filterwarnings("ignore", category=UserWarning)

# ----------------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------------
BATCH_SIZE = 100      # material IDs per elasticity request
MAX_RETRIES = 4       # attempts (with exponential back-off) per request

# Quality filters: lower bound is EXCLUSIVE, upper bound is INCLUSIVE.
FILTERS = {
    "debye_temperature":    (0.0, 10000.0),
    "shear_vrh":            (0.0, 5000.0),
    "bulk_vrh":             (0.0, 5000.0),
    "homogeneous_poisson":  (-10, 10),
    "universal_anisotropy": (-6.0, 1000.0),
}

SUMMARY_FIELDS = [
    'builder_meta', 'nsites', 'elements', 'nelements', 'composition', 'composition_reduced',
    'formula_pretty', 'formula_anonymous', 'chemsys', 'volume', 'density', 'density_atomic',
    'symmetry', 'property_name', 'material_id', 'deprecated', 'deprecation_reasons', 'last_updated',
    'origins', 'warnings', 'structure', 'task_ids', 'uncorrected_energy_per_atom', 'energy_per_atom',
    'formation_energy_per_atom', 'energy_above_hull', 'is_stable', 'equilibrium_reaction_energy_per_atom',
    'decomposes_to', 'xas', 'grain_boundaries', 'band_gap', 'cbm', 'vbm', 'efermi', 'is_gap_direct',
    'is_metal', 'es_source_calc_id', 'bandstructure', 'dos', 'dos_energy_up', 'dos_energy_down',
    'is_magnetic', 'ordering', 'total_magnetization', 'total_magnetization_normalized_vol',
    'total_magnetization_normalized_formula_units', 'num_magnetic_sites', 'num_unique_magnetic_sites',
    'types_of_magnetic_species', 'bulk_modulus', 'shear_modulus', 'universal_anisotropy',
    'homogeneous_poisson', 'e_total', 'e_ionic', 'e_electronic', 'n', 'e_ij_max',
    'weighted_surface_energy_EV_PER_ANG2', 'weighted_surface_energy', 'weighted_work_function',
    'surface_anisotropy', 'shape_factor', 'has_reconstructed', 'possible_species', 'has_props',
    'theoretical', 'database_IDs',
]

# Very large nested objects that bloat the output file.
# Set to [] to request them anyway (they will be written as long text strings).
EXCLUDE_LARGE_FIELDS = ['structure', 'bandstructure', 'dos', 'xas', 'grain_boundaries']


# ----------------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------------
def detect_environment():
    hpc_vars = ("SLURM_JOB_ID", "PBS_JOBID", "LSB_JOBID", "SGE_TASK_ID")
    is_hpc = any(v in os.environ for v in hpc_vars)
    print(f"Python {sys.version.split()[0]} | pandas {pd.__version__} | "
          f"environment: {'HPC job' if is_hpc else 'PC / interactive'}")


def ask(prompt, default=None, secret=False, env=None):
    """Ask the user; fall back to an environment variable or default when non-interactive."""
    if env and os.environ.get(env):
        print(f"{prompt}: using environment variable {env}")
        return os.environ[env].strip()
    label = prompt + (f" [default: {default}]" if default else "") + ": "
    try:
        answer = (getpass.getpass(label) if secret else input(label)).strip()
    except (EOFError, RuntimeError):  # no stdin (batch mode)
        if default is not None:
            print(f"{prompt}: non-interactive session, using default '{default}'")
            return default
        raise RuntimeError(
            f"No interactive input available for '{prompt}'. Set the environment variable {env}."
        )
    return answer or (default if default is not None else "")


def to_dict(doc):
    return doc.model_dump() if hasattr(doc, "model_dump") else doc.dict()


def with_retries(func, *args, **kwargs):
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            return func(*args, **kwargs)
        except Exception as exc:
            # Retrying cannot fix a bad request, so fail immediately in that case.
            if attempt == MAX_RETRIES or "invalid fields" in str(exc):
                raise
            wait = 2 ** attempt
            print(f"  Request failed ({exc}); retry {attempt}/{MAX_RETRIES - 1} in {wait}s")
            time.sleep(wait)


def plain(v):
    return v.value if isinstance(v, Enum) else v


def as_dict(x):
    """Return a plain dict from a dict, a pydantic model, or its string representation."""
    if isinstance(x, dict):
        return {k: plain(v) for k, v in x.items()}
    if hasattr(x, "model_dump"):
        return as_dict(x.model_dump())
    if isinstance(x, str):
        try:
            parsed = ast.literal_eval(x)
            return parsed if isinstance(parsed, dict) else {}
        except (ValueError, SyntaxError):
            return {}
    return {}


def tensor_entry(tensor, i, j):
    try:
        return as_dict(tensor).get("raw")[i][j]
    except (TypeError, IndexError, KeyError):
        return np.nan


def csv_safe(value):
    """Convert enums, timezone-aware datetimes and nested objects to CSV-friendly values."""
    value = plain(value)
    if isinstance(value, datetime):
        return value.replace(tzinfo=None)
    if isinstance(value, (dict, list, tuple, set, np.ndarray)) or hasattr(value, "model_dump"):
        return str(value)
    return value


# ----------------------------------------------------------------------------
# Pipeline steps
# ----------------------------------------------------------------------------
def prompt_user():
    api_key = ask("Enter your Materials Project API key", secret=True, env="MP_API_KEY")
    if not api_key:
        raise ValueError("An API key is required.")

    base_dir = Path(ask("Directory where the output folder will be created",
                        default=os.getcwd(), env="MP_OUTPUT_DIR")).expanduser().resolve()
    base_dir.mkdir(parents=True, exist_ok=True)

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    folder_name = ask("Name of the new output folder",
                      default=f"MP_stable_materials_{stamp}", env="MP_FOLDER_NAME")
    output_dir = base_dir / folder_name
    if output_dir.exists():
        print(f"Folder already exists, saving into it: {output_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)  # reuse the folder if it already exists
    output_file = output_dir / "MP_stable_materials_filtered.csv"
    if output_file.exists():
        print("Note: a CSV file with this name already exists and will be replaced.")
    print(f"Output will be saved to: {output_file}")
    return api_key, output_file


def download(api_key):
    requested = [f for f in SUMMARY_FIELDS if f not in EXCLUDE_LARGE_FIELDS]
    failed_chunks = []

    with MPRester(api_key) as mpr:
        # The set of available fields changes between mp-api versions, so keep only
        # the fields this installed version actually supports.
        available = set(mpr.materials.summary.available_fields)
        fields = [f for f in requested if f in available]
        skipped = [f for f in requested if f not in available]
        if skipped:
            print(f"Note: skipping fields not available in this mp-api version: {skipped}")

        print("Fetching stable materials (summary)...")
        summary_docs = with_retries(mpr.materials.summary.search, is_stable=True, fields=fields)
        summary_data = [to_dict(d) for d in summary_docs]
        material_ids = [str(d["material_id"]) for d in summary_data]
        print(f"  {len(material_ids)} stable materials found")

        print("Fetching elastic data in chunks...")
        elastic_data = []
        for i in tqdm(range(0, len(material_ids), BATCH_SIZE), desc="elasticity"):
            chunk = material_ids[i:i + BATCH_SIZE]
            try:
                docs = with_retries(mpr.materials.elasticity.search, material_ids=chunk)
                elastic_data.extend(to_dict(d) for d in docs)
            except Exception as exc:
                failed_chunks.append((i, i + BATCH_SIZE))
                print(f"  Chunk {i}-{i + BATCH_SIZE} failed permanently: {exc}")

    if failed_chunks:
        print(f"WARNING: {len(failed_chunks)} chunk(s) failed; re-run the script to retry.")
    print(f"Summary rows: {len(summary_data)} | Elastic rows: {len(elastic_data)}")
    return summary_data, elastic_data


def process(summary_data, elastic_data):
    df_summary = pd.DataFrame(summary_data)
    df_elastic = pd.DataFrame(elastic_data)
    if df_elastic.empty:
        raise RuntimeError("No elasticity data was retrieved; nothing to merge.")
    df_elastic = df_elastic.drop_duplicates(subset="material_id")
    df_summary["material_id"] = df_summary["material_id"].astype(str)
    df_elastic["material_id"] = df_elastic["material_id"].astype(str)

    # Left-merge: keep every stable material; overlapping elasticity columns get '_elastic'
    df = df_summary.merge(df_elastic, on="material_id", how="left", suffixes=("", "_elastic"))
    print("Merged shape:", df.shape)

    def pick(base):
        """Prefer the elasticity-dataset column when both datasets provide it."""
        return f"{base}_elastic" if f"{base}_elastic" in df.columns else base

    # Bulk and shear moduli (Voigt / Reuss / VRH)
    bulk = df[pick("bulk_modulus")].apply(as_dict)
    shear = df[pick("shear_modulus")].apply(as_dict)
    for name, src in (("bulk", bulk), ("shear", shear)):
        for kind in ("voigt", "reuss", "vrh"):
            df[f"{name}_{kind}"] = src.apply(lambda d, k=kind: d.get(k))

    # Symmetry
    sym = df["symmetry"].apply(as_dict)
    for col, key in (("crystal_system", "crystal_system"), ("crystal_symbol", "symbol"),
                     ("space_group_number", "number"), ("crystal_point_group", "point_group"),
                     ("crystal_symprec", "symprec"), ("crystal_angle_tolerance", "angle_tolerance"),
                     ("crystal_version", "version")):
        df[col] = sym.apply(lambda d, k=key: d.get(k))

    # Sound velocities
    if "sound_velocity" in df.columns:
        sv = df["sound_velocity"].apply(as_dict)
        for key in ("transverse", "longitudinal", "snyder_acoustic", "snyder_optical", "snyder_total"):
            df[f"sound_velocity_{key}"] = sv.apply(lambda d, k=key: d.get(k))

    # Elastic tensor components (GPa)
    if "elastic_tensor" in df.columns:
        df["C11"] = df["elastic_tensor"].apply(lambda t: tensor_entry(t, 0, 0))
        df["C12"] = df["elastic_tensor"].apply(lambda t: tensor_entry(t, 0, 1))
        df["C44"] = df["elastic_tensor"].apply(lambda t: tensor_entry(t, 3, 3))

    # Columns used in the filters (elasticity dataset preferred)
    df["debye_temperature"] = pd.to_numeric(df[pick("debye_temperature")], errors="coerce")
    df["homogeneous_poisson"] = pd.to_numeric(df[pick("homogeneous_poisson")], errors="coerce")
    df["universal_anisotropy"] = pd.to_numeric(df[pick("universal_anisotropy")], errors="coerce")
    for col in ("bulk_vrh", "shear_vrh"):
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Drop the raw dictionary columns that were expanded above
    drop_cols = [c for c in ("bulk_modulus", "bulk_modulus_elastic", "shear_modulus",
                             "shear_modulus_elastic", "symmetry", "sound_velocity",
                             "elastic_tensor") if c in df.columns]
    df = df.drop(columns=drop_cols)

    # Apply all filters (lower bound exclusive, upper bound inclusive)
    mask = pd.Series(True, index=df.index)
    print(f"Rows before filtering: {len(df)}")
    for col, (lo, hi) in FILTERS.items():
        cond = df[col].between(lo, hi, inclusive="right")
        print(f"  {col:<22} in ({lo}, {hi}] -> {int(cond.sum())} pass")
        mask &= cond
    df_filtered = df[mask].reset_index(drop=True)
    print(f"Rows after all filters: {len(df_filtered)}")
    return df_filtered


def save_csv(df_filtered, output_file):
    out = df_filtered.copy()
    for col in out.columns:
        if isinstance(out[col].dtype, pd.DatetimeTZDtype):
            out[col] = out[col].dt.tz_localize(None)
        elif out[col].dtype == object:
            out[col] = out[col].map(csv_safe)

    # utf-8-sig adds a BOM so Excel opens the file with correct characters;
    # other tools (pandas, R, etc.) read it normally.
    out.to_csv(output_file, index=False, encoding="utf-8-sig")
    print(f"DATA SAVED: {output_file}")
    print(f"Final shape: {out.shape}")


def main():
    detect_environment()
    api_key, output_file = prompt_user()
    summary_data, elastic_data = download(api_key)
    df_filtered = process(summary_data, elastic_data)
    save_csv(df_filtered, output_file)


if __name__ == "__main__":
    main()