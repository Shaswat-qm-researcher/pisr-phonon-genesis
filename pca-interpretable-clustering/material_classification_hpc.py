"""
================================================================================
MATERIAL COMPOUND CLASSIFIER — HPC VERSION
================================================================================
Usage:
    python material_classification_hpc.py          # uses Material_classification_PCA.txt
    python material_classification_hpc.py --no-log # skip writing a .log file
================================================================================
"""

# ── Standard library ──────────────────────────────────────────────────────────
import os
import re
import sys
import argparse
import logging
import warnings
from pathlib import Path
from typing import Set, Dict, List, Tuple

import pandas as pd

warnings.filterwarnings('ignore')

# ============================================================================
# LOGGING  (replaces Colors terminal output — works cleanly in HPC job logs)
# ============================================================================
def setup_logging(log_path: str = None) -> logging.Logger:
    logger = logging.getLogger("Classifier")
    logger.handlers.clear()          # ← add this line
    logger.setLevel(logging.DEBUG)
    fmt = logging.Formatter("%(asctime)s  %(levelname)-8s  %(message)s",
                            datefmt="%Y-%m-%d %H:%M:%S")
    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(fmt)
    logger.addHandler(ch)
    if log_path:
        fh = logging.FileHandler(log_path)
        fh.setFormatter(fmt)
        logger.addHandler(fh)
    return logger

log: logging.Logger = None   # set in main()

# ============================================================================
# CONFIG LOADER  — reads Material_classification_PCA.txt from same folder
# ============================================================================
def load_config() -> dict:
    """
    Parse Material_classification_PCA.txt (key = value) from the same
    folder as this script.  Returns a plain dict.
    """
    folder   = os.path.dirname(os.path.abspath(__file__)) if "__file__" in dir() else os.getcwd()
    cfg_path = os.path.join(folder, "Material_classification_PCA.txt")

    if not os.path.isfile(cfg_path):
        raise FileNotFoundError(
            f"Material_classification_PCA.txt not found in: {folder}"
        )

    raw = {}
    with open(cfg_path, "r", encoding="utf-8") as f:
        for line in f:
            stripped = line.rstrip()
            if not stripped or stripped.lstrip().startswith("#"):
                continue
            if "=" in stripped:
                key, _, value = stripped.partition("=")
                value = value.partition("#")[0].strip()   # ← strip inline comments
                raw[key.strip()] = value

    def _str(k, default=None):
        v = raw.get(k, "").strip()
        return v if v else default

    return {
        "file_path":      _str("file_path"),
        "sheet_name":     _str("sheet_name"),       # None if blank
        "output_dir":     _str("output_dir"),
        "formula_column": _str("formula_column"),   # None triggers auto-detect
    }

# ============================================================================
# ELEMENT DATABASE
# ============================================================================
class ElementDatabase:
    ALL_METALS: Set[str] = {
        'Li','Na','K','Rb','Cs','Fr',
        'Be','Mg','Ca','Sr','Ba','Ra',
        'Sc','Ti','V','Cr','Mn','Fe','Co','Ni','Cu','Zn',
        'Y','Zr','Nb','Mo','Tc','Ru','Rh','Pd','Ag','Cd',
        'Hf','Ta','W','Re','Os','Ir','Pt','Au','Hg',
        'Al','Ga','In','Sn','Tl','Pb','Bi',
        'Rf','Db','Sg','Bh','Hs','Mt','Ds','Rg','Cn','Nh','Fl','Mc','Lv',
        'La','Ce','Pr','Nd','Pm','Sm','Eu','Gd',
        'Tb','Dy','Ho','Er','Tm','Yb','Lu',
        'Ac','Th','Pa','U','Np','Pu','Am','Cm',
        'Bk','Cf','Es','Fm','Md','No','Lr',
    }

    METALLOIDS: Set[str] = {'Si', 'Ge', 'As', 'Sb', 'Te', 'Po'}
    METALS_AND_METALLOIDS: Set[str] = ALL_METALS | METALLOIDS
    HALOGENS: Set[str] = {'F', 'Cl', 'Br', 'I', 'At', 'Ts'}

    ALL_ELEMENTS: Set[str] = METALS_AND_METALLOIDS | HALOGENS | {
        'H', 'He', 'B', 'C', 'N', 'O', 'P', 'S', 'Se',
        'Ne', 'Ar', 'Kr', 'Xe', 'Rn', 'Og',
    }

# ============================================================================
# FORMULA PARSER
# ============================================================================
class FormulaParser:
    """
    Extracts the set of element symbols from a chemical formula string.

    Handles:
      - Standard formulas:  Fe2O3, NaCl, MoSi2, Al2O3
      - Hill-order:         C2H6O
      - Parentheses:        Ca3(PO4)2
      - Whitespace/spaces:  Fe 2 O 3  (Materials Project style)
      - Species-list:       ['Fe', 'C']  or  Fe, C
    """

    _TOKEN_RE = re.compile(r'([A-Z][a-z]?)(\d*\.?\d*)')

    def __init__(self):
        self._db = ElementDatabase()

    def parse(self, formula) -> Set[str]:
        if pd.isna(formula):
            return set()

        raw = str(formula).strip()

        # ── Path 1: species-list format  ['Fe', 'C']  or  Fe, C ──────
        if ',' in raw or raw.startswith('['):
            cleaned = raw.strip("[]")
            tokens = {x.strip().strip("'\"") for x in cleaned.split(",") if x.strip()}
            if all(re.fullmatch(r'[A-Z][a-z]?', t) for t in tokens):
                return tokens

        # ── Path 2: chemical formula string ───────────────────────────
        elements: Set[str] = set()
        for match in self._TOKEN_RE.finditer(raw):
            sym = match.group(1)
            if sym in self._db.ALL_ELEMENTS:
                elements.add(sym)
            elif sym[0] in self._db.ALL_ELEMENTS:
                elements.add(sym[0])
            else:
                log.warning(f"Unrecognised token '{sym}' in formula: {raw!r}")

        return elements

# ============================================================================
# FILE MANAGER  — no interactive prompts; reads from config
# ============================================================================
class FileManager:

    @staticmethod
    def load_file(file_path: str, sheet_name: str = None) -> pd.DataFrame:
        ext = Path(file_path).suffix.lower()
        try:
            if ext in ['.xlsx', '.xls']:
                if sheet_name:
                    df = pd.read_excel(file_path, sheet_name=sheet_name)
                    log.info(f"Loaded sheet '{sheet_name}' from {Path(file_path).name}")
                else:
                    # Use first sheet if sheet_name not specified
                    xls = pd.ExcelFile(file_path)
                    df = pd.read_excel(file_path, sheet_name=xls.sheet_names[0])
                    log.info(f"Loaded sheet '{xls.sheet_names[0]}' from {Path(file_path).name}")
            elif ext == '.csv':
                df = pd.read_csv(file_path)
                log.info(f"Loaded: {Path(file_path).name}")
            else:
                log.error(f"Unsupported format: {ext}")
                sys.exit(1)
        except Exception as e:
            log.error(f"Could not read file: {e}")
            sys.exit(1)

        log.info(f"Rows: {len(df):,}  |  Columns: {df.shape[1]}")
        return df

# ============================================================================
# CLASSIFIER
# ============================================================================
class MaterialClassifier:
    """Parses species/formula strings and assigns compound categories."""

    _CANDIDATE_COLS = ['species', 'formula', 'FORMULA', 'composition']

    def __init__(self):
        self.db     = ElementDatabase()
        self.parser = FormulaParser()

    # ------------------------------------------------------------------
    def _detect_column(self, df: pd.DataFrame, override: str = None) -> str:
        """
        Return the formula column to use.
        Priority: config override -> auto-detect -> error (no interactive fallback).
        """
        # 1. Config-specified column
        if override:
            if override in df.columns:
                log.info(f"Using config-specified column '{override}' for element extraction.")
                return override
            log.error(
                f"Column '{override}' (from config formula_column) not found. "
                f"Available: {', '.join(df.columns.tolist())}"
            )
            sys.exit(1)

        # 2. Auto-detect from candidate list
        col_lower = {c.lower(): c for c in df.columns}
        for candidate in self._CANDIDATE_COLS:
            if candidate.lower() in col_lower:
                found = col_lower[candidate.lower()]
                log.info(f"Auto-detected column '{found}' for element extraction.")
                return found

        # 3. Fail clearly — no interactive input on HPC
        log.error(
            "Could not auto-detect a formula/species column. "
            f"Available columns: {', '.join(df.columns.tolist())}. "
            "Set 'formula_column' in Material_classification_PCA.txt."
        )
        sys.exit(1)

    # ------------------------------------------------------------------
    def classify(self, elements: Set[str]) -> str:
        if not elements:
            return 'Unknown'

        metallic = elements & self.db.METALS_AND_METALLOIDS

        if len(elements) == 1:
            return 'Element'
        if 'C' in elements and metallic:
            return 'Carbide'
        if 'B' in elements and metallic:
            return 'Boride'
        if 'N' in elements and metallic:
            return 'Nitride'
        if 'O' in elements:
            return 'Oxide'
        if elements & self.db.HALOGENS:
            return 'Halide'
        if elements.issubset(self.db.METALS_AND_METALLOIDS):
            return 'Metal-Metalloid'
        return 'Other'

    # ------------------------------------------------------------------
    def run(self, df: pd.DataFrame, formula_column: str = None) -> pd.DataFrame:
        col = self._detect_column(df, override=formula_column)
        df = df.copy()
        df['Elements'] = df[col].apply(self.parser.parse)
        df['Category'] = df['Elements'].apply(self.classify)
        return df

# ============================================================================
# EXPORTER
# ============================================================================
class Exporter:

    @staticmethod
    def save_categories(df: pd.DataFrame, output_dir: str) -> Dict[str, int]:
        summary: Dict[str, int] = {}
        export_df = df.drop(columns=['Elements', 'Category'])

        for cat in sorted(df['Category'].unique()):
            subset    = export_df[df['Category'] == cat]
            out_path  = os.path.join(output_dir, f"{cat}.xlsx")
            subset.to_excel(out_path, index=False)
            summary[cat] = len(subset)
            log.info(f"Saved '{cat}.xlsx'  ({len(subset):,} rows)")

        return summary

    @staticmethod
    def print_summary(summary: Dict[str, int], total: int) -> None:
        log.info("=" * 60)
        log.info("CLASSIFICATION SUMMARY")
        log.info("=" * 60)
        log.info(f"  {'Category':<20}  {'Count':>8}  {'Share':>7}")
        log.info(f"  {'-'*20}  {'-'*8}  {'-'*7}")
        for cat, count in sorted(summary.items(), key=lambda x: -x[1]):
            pct = count / total * 100
            log.info(f"  {cat:<20}  {count:>8,}  {pct:>6.1f}%")
        log.info(f"  {'-'*40}")          # ← was '─'*40
        log.info(f"  {'Total':<20}  {total:>8,}")
        log.info("=" * 60)

    @staticmethod
    def print_file_list(output_dir: str, summary: Dict[str, int]) -> None:
        log.info("Output files:")
        for cat in sorted(summary):
            log.info(f"  -> {os.path.join(output_dir, cat + '.xlsx')}")

# ============================================================================
# MAIN
# ============================================================================
def main():
    parser = argparse.ArgumentParser(description="Material Classifier — HPC Mode")
    parser.add_argument("--no-log", dest="no_log", action="store_true",
                        help="Skip writing a .log file (print to stdout only)")
    args, _ = parser.parse_known_args()   # parse_known_args ignores Jupyter's -f kernel-xxx.json

    # ----- Load config -------------------------------------------------------
    cfg = load_config()

    if not cfg["file_path"]:
        print("ERROR: file_path is not set in Material_classification_PCA.txt")
        sys.exit(1)
    if not cfg["output_dir"]:
        print("ERROR: output_dir is not set in Material_classification_PCA.txt")
        sys.exit(1)

    # ----- Setup output & logging -------------------------------------------
    output_dir = os.path.join(cfg["output_dir"], "classified_data")
    os.makedirs(output_dir, exist_ok=True)

    log_path = None if args.no_log else os.path.join(cfg["output_dir"], "classification.log")

    global log
    log = setup_logging(log_path)

    log.info("=" * 60)
    log.info("MATERIAL COMPOUND CLASSIFIER — HPC VERSION")
    log.info(f"Config  : Material_classification_PCA.txt")
    log.info(f"Input   : {cfg['file_path']}")
    log.info(f"Output  : {output_dir}")
    log.info("=" * 60)

    # ----- Load data ---------------------------------------------------------
    log.info("Loading data ...")
    df = FileManager.load_file(cfg["file_path"], cfg["sheet_name"])

    # ----- Classify ----------------------------------------------------------
    log.info("Classifying materials ...")
    classifier    = MaterialClassifier()
    df_classified = classifier.run(df, formula_column=cfg["formula_column"])

    cat_counts = df_classified['Category'].value_counts()
    log.info(
        f"Categories found ({len(cat_counts)}): "
        f"{', '.join(sorted(cat_counts.index.tolist()))}"
    )

    # ----- Export ------------------------------------------------------------
    log.info("Exporting category files ...")
    summary = Exporter.save_categories(df_classified, output_dir)

    Exporter.print_summary(summary, total=len(df_classified))
    Exporter.print_file_list(output_dir, summary)

    log.info("CLASSIFICATION COMPLETE")


if __name__ == "__main__":
    main()
