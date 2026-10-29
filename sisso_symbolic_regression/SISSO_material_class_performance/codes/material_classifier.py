"""
╔══════════════════════════════════════════════════════════════════════════════╗
║          MATERIAL COMPOUND CLASSIFIER  v2.1                                 ║
║          Compatible with: PC · HPC (SLURM/PBS) · Jupyter Notebook           ║
╚══════════════════════════════════════════════════════════════════════════════╝

Usage
─────
  Interactive (terminal / HPC login node):
      python material_classifier.py

  Non-interactive (HPC batch / scripted):
      python material_classifier.py \\
          --input  /path/to/data.xlsx \\
          --output /path/to/results   \\
          --column formula            \\
          --sheet  "Sheet1"           \\
          --prefix my_run

  Jupyter Notebook:
      from material_classifier import run_notebook
      df_out = run_notebook(
          input_path  = "data/my_data.xlsx",
          output_dir  = "results",
          formula_col = "formula",   # or None → auto-detect
          prefix      = "run1",
      )
"""

# ── Standard library ──────────────────────────────────────────────────────────
import os
import re
import sys
import argparse
import warnings
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

# ── Environment detection ─────────────────────────────────────────────────────
def _in_jupyter() -> bool:
    try:
        shell = get_ipython().__class__.__name__          # type: ignore[name-defined]
        return shell in ("ZMQInteractiveShell", "TerminalInteractiveShell")
    except NameError:
        return False

def _interactive() -> bool:
    """True when running in a terminal that accepts user input."""
    return sys.stdin.isatty() and not _in_jupyter()


# ============================================================================
# TERMINAL COLOR CODES
# ============================================================================
class Colors:
    BOLD       = "\033[1m"
    ENDC       = "\033[0m"
    RED        = "\033[91m"
    ORANGE     = "\033[38;5;214m"
    YELLOW     = "\033[93m"
    PINK       = "\033[38;5;213m"
    LIME       = "\033[38;5;154m"
    CYAN       = "\033[96m"
    DARK_BLUE  = "\033[34m"
    WHITE      = "\033[97m"
    GREY       = "\033[90m"
    HEADER     = "\033[95m"
    BLUE       = "\033[94m"
    GREEN      = "\033[92m"

    # Gracefully fall back to ASCII on narrow / non-UTF-8 terminals
    try:
        "█".encode(sys.stdout.encoding or "utf-8")
        BAR_CHAR = "█"
    except (UnicodeEncodeError, LookupError):
        BAR_CHAR = "#"

    # Disable colors when output is redirected (HPC log files, etc.)
    _USE_COLOR: bool = sys.stdout.isatty()

    @classmethod
    def _c(cls, code: str, text: str) -> str:
        return f"{code}{text}{cls.ENDC}" if cls._USE_COLOR else text

    @classmethod
    def header(cls, text: str) -> None:
        border = "=" * 80
        print(f"\n{cls._c(cls.HEADER + cls.BOLD, border)}")
        print(cls._c(cls.HEADER + cls.BOLD, text.center(80)))
        print(f"{cls._c(cls.HEADER + cls.BOLD, border)}\n")

    @classmethod
    def step(cls, num: int, text: str) -> None:
        print(f"\n{cls._c(cls.BLUE + cls.BOLD, f'[STEP {num}] {text}')}")
        print("-" * 80)

    @classmethod
    def success(cls, text: str) -> None:
        print(cls._c(cls.GREEN,  f"  ✓  {text}"))

    @classmethod
    def warning(cls, text: str) -> None:
        print(cls._c(cls.YELLOW, f"  ⚠  {text}"))

    @classmethod
    def error(cls, text: str) -> None:
        print(cls._c(cls.RED,    f"  ✗  {text}"))

    @classmethod
    def info(cls, text: str) -> None:
        print(cls._c(cls.CYAN,   f"  ℹ  {text}"))

    @classmethod
    def bold(cls, text: str) -> None:
        print(cls._c(cls.BOLD, text))


# ============================================================================
# ELEMENT DATABASE
# ============================================================================
class ElementDatabase:
    ALKALI:         Set[str] = {"Li", "Na", "K", "Rb", "Cs", "Fr"}
    ALKALINE_EARTH: Set[str] = {"Be", "Mg", "Ca", "Sr", "Ba", "Ra"}

    LANTHANOIDS: Set[str] = {
        "La", "Ce", "Pr", "Nd", "Pm", "Sm", "Eu", "Gd",
        "Tb", "Dy", "Ho", "Er", "Tm", "Yb", "Lu",
    }
    ACTINOIDS: Set[str] = {
        "Ac", "Th", "Pa", "U", "Np", "Pu", "Am", "Cm",
        "Bk", "Cf", "Es", "Fm", "Md", "No", "Lr",
    }
    LANTHANOIDS_ACTINOIDS: Set[str] = LANTHANOIDS | ACTINOIDS

    TRANSITION: Set[str] = {
        "Sc", "Ti", "V",  "Cr", "Mn", "Fe", "Co", "Ni", "Cu", "Zn",
        "Y",  "Zr", "Nb", "Mo", "Tc", "Ru", "Rh", "Pd", "Ag", "Cd",
        "Hf", "Ta", "W",  "Re", "Os", "Ir", "Pt", "Au", "Hg",
        "Rf", "Db", "Sg", "Bh", "Hs", "Mt", "Ds", "Rg", "Cn",
    }
    POST_TRANSITION: Set[str] = {
        "Al", "Ga", "In", "Sn", "Tl", "Pb", "Bi",
        "Nh", "Fl", "Mc", "Lv",
    }
    METALLOIDS: Set[str] = {"Si", "Ge", "As", "Sb", "Te", "Po"}

    ALL_METALS: Set[str] = (
        ALKALI | ALKALINE_EARTH | TRANSITION | POST_TRANSITION | LANTHANOIDS_ACTINOIDS
    )
    METALS_AND_METALLOIDS: Set[str] = ALL_METALS | METALLOIDS
    HALOGENS: Set[str] = {"F", "Cl", "Br", "I", "At", "Ts"}

    ALL_ELEMENTS: Set[str] = METALS_AND_METALLOIDS | HALOGENS | {
        "H", "He", "B", "C", "N", "O", "P", "S", "Se",
        "Ne", "Ar", "Kr", "Xe", "Rn", "Og",
    }

    METAL_GROUP_PRIORITY: List[Tuple[str, Set[str]]] = [
        ("Lanthanoid/Actinoid", LANTHANOIDS_ACTINOIDS),
        ("Transition Metal",    TRANSITION),
        ("Post-Transition",     POST_TRANSITION),
        ("Alkaline Earth",      ALKALINE_EARTH),
        ("Alkali",              ALKALI),
    ]


# ============================================================================
# FORMULA PARSER
# ============================================================================
class FormulaParser:
    """
    Extracts the set of element symbols from a chemical formula string.

    Handles: Fe2O3, NaCl, Ca3(PO4)2, 'Fe 2 O 3', ['Fe', 'C'].
    Returns an empty set on parse failure.
    """
    _TOKEN_RE = re.compile(r"([A-Z][a-z]?)(\d*\.?\d*)")

    def __init__(self) -> None:
        self._db = ElementDatabase()

    def parse(self, formula) -> Set[str]:
        if pd.isna(formula):
            return set()

        raw = str(formula).strip()

        # Path 1 – species list  ['Fe', 'C']  or  Fe, C
        if "," in raw or raw.startswith("["):
            cleaned = raw.strip("[]")
            tokens = {x.strip().strip("'\"") for x in cleaned.split(",") if x.strip()}
            if tokens and all(re.fullmatch(r"[A-Z][a-z]?", t) for t in tokens):
                return tokens

        # Path 2 – chemical formula string
        elements: Set[str] = set()
        for match in self._TOKEN_RE.finditer(raw):
            sym = match.group(1)
            if sym in self._db.ALL_ELEMENTS:
                elements.add(sym)
            elif sym[0] in self._db.ALL_ELEMENTS:
                elements.add(sym[0])
            else:
                Colors.warning(f"Unrecognised token '{sym}' in formula: {raw!r}")

        return elements


# ============================================================================
# FILE MANAGER
# ============================================================================
class FileManager:
    SUPPORTED_EXT = [".xlsx", ".xls", ".csv"]

    # ── static helpers ────────────────────────────────────────────────────
    @staticmethod
    def list_files(folder: str) -> List[Tuple[int, str, str]]:
        files = sorted(
            [f for f in Path(folder).iterdir()
             if f.suffix.lower() in FileManager.SUPPORTED_EXT
             and not f.name.startswith("~$")],
            key=lambda f: f.name,
        )
        return [(i, f.name, str(f)) for i, f in enumerate(files, 1)]

    # ── interactive (terminal) ────────────────────────────────────────────
    @staticmethod
    def select_input_file() -> Tuple[str, Optional[str]]:
        """
        Returns (file_path, sheet_name).
        sheet_name is None for CSV files or when the workbook has only one sheet
        and the user accepts it with ENTER.
        """
        Colors.step(1, "SELECT INPUT FILE")
        while True:
            folder = input(
                f"\n{Colors.CYAN}  Enter folder path containing your data file: {Colors.ENDC}"
            ).strip().strip("\"'")
            if os.path.isdir(folder):
                break
            Colors.error("Path not found — please try again.")

        files = FileManager.list_files(folder)
        if not files:
            Colors.error(f"No supported files found in: {folder}")
            sys.exit(1)

        print(f"\n{Colors.BOLD}  Available files:{Colors.ENDC}")
        for num, name, _ in files:
            print(f"    {Colors.GREEN}[{num}]{Colors.ENDC}  {name}")

        while True:
            try:
                sel = int(input(f"\n{Colors.CYAN}  Select file number: {Colors.ENDC}"))
                if 1 <= sel <= len(files):
                    chosen_path = files[sel - 1][2]
                    Colors.success(f"Selected: {files[sel-1][1]}")
                    break
                Colors.error(f"Enter a number between 1 and {len(files)}")
            except ValueError:
                Colors.error("Please enter a valid integer.")

        # ── Sheet selection for Excel files ───────────────────────────────
        chosen_sheet: Optional[str] = None
        ext = Path(chosen_path).suffix.lower()
        if ext in [".xlsx", ".xls"]:
            try:
                xls = pd.ExcelFile(chosen_path)
                sheet_names = xls.sheet_names
            except Exception as e:
                Colors.warning(f"Could not read sheet list: {e}")
                sheet_names = []

            if sheet_names:
                print(f"\n{Colors.BOLD}  Available sheets:{Colors.ENDC}")
                for i, s in enumerate(sheet_names, 1):
                    print(f"    {Colors.GREEN}[{i}]{Colors.ENDC}  {s}")

                if len(sheet_names) == 1:
                    chosen_sheet = sheet_names[0]
                    Colors.info(f"Single sheet found — using '{chosen_sheet}'.")
                else:
                    while True:
                        raw = input(
                            f"\n{Colors.CYAN}  Select sheet number "
                            f"(ENTER for sheet 1 — '{sheet_names[0]}'): {Colors.ENDC}"
                        ).strip()
                        if raw == "":
                            chosen_sheet = sheet_names[0]
                            Colors.success(f"Using sheet: '{chosen_sheet}'")
                            break
                        try:
                            idx = int(raw)
                            if 1 <= idx <= len(sheet_names):
                                chosen_sheet = sheet_names[idx - 1]
                                Colors.success(f"Using sheet: '{chosen_sheet}'")
                                break
                            Colors.error(f"Enter a number between 1 and {len(sheet_names)}")
                        except ValueError:
                            Colors.error("Please enter a valid integer or press ENTER.")

        return chosen_path, chosen_sheet

    @staticmethod
    def select_output_folder() -> str:
        Colors.step(2, "SELECT OUTPUT FOLDER")
        while True:
            folder = input(
                f"\n{Colors.CYAN}  Enter output folder path "
                f"(created automatically if absent): {Colors.ENDC}"
            ).strip().strip("\"'")
            if folder:
                os.makedirs(folder, exist_ok=True)
                Colors.success(f"Output folder ready: {folder}")
                return folder
            Colors.error("Output path cannot be empty.")

    # ── loader (shared) ───────────────────────────────────────────────────
    @staticmethod
    def load_file(file_path: str, sheet: Optional[str] = None) -> pd.DataFrame:
        """
        Load a spreadsheet file.

        For Excel files the caller should pass the desired sheet name (resolved
        by select_input_file or --sheet CLI flag).  If sheet is None the first
        sheet is used without prompting, keeping this method safe for batch /
        Jupyter use.
        """
        ext = Path(file_path).suffix.lower()
        try:
            if ext in [".xlsx", ".xls"]:
                if sheet:
                    df = pd.read_excel(file_path, sheet_name=sheet)
                    Colors.success(f"Loaded sheet: '{sheet}'  ←  {Path(file_path).name}")
                else:
                    # No sheet specified: fall back to the first sheet silently
                    xls = pd.ExcelFile(file_path)
                    first = xls.sheet_names[0]
                    df = pd.read_excel(file_path, sheet_name=first)
                    Colors.success(f"Loaded sheet: '{first}'  ←  {Path(file_path).name}")
            elif ext == ".csv":
                df = pd.read_csv(file_path)
                Colors.success(f"Loaded: {Path(file_path).name}")
            else:
                Colors.error(f"Unsupported format: {ext}")
                sys.exit(1)

        except Exception as e:
            Colors.error(f"Could not read file: {e}")
            sys.exit(1)

        Colors.info(f"Rows: {len(df):,}  |  Columns: {df.shape[1]}")
        return df


# ============================================================================
# CLASSIFIER
# ============================================================================
class MaterialClassifier:
    """
    Appends a single 'Class' column to the dataframe.

    Class values
    ─────────────────────────────────────────────────────────────────────────
    Carbide | Boride | Nitride | Oxide | Halide | Element | Other | Unknown
    Alkali | Alkaline Earth | Transition Metal | Post-Transition |
    Lanthanoid/Actinoid
    """

    CLASS_COL       = "Class"
    _CANDIDATE_COLS = ["species", "formula", "composition"]

    def __init__(self) -> None:
        self.db     = ElementDatabase()
        self.parser = FormulaParser()

    # ── column detection ──────────────────────────────────────────────────
    def _detect_column(self, df: pd.DataFrame,
                       hint: Optional[str] = None) -> str:
        if hint:
            if hint in df.columns:
                Colors.info(f"Using column '{hint}' for element extraction.")
                return hint
            Colors.warning(f"Specified column '{hint}' not found — falling back to auto-detect.")

        col_lower = {c.lower(): c for c in df.columns}
        for candidate in self._CANDIDATE_COLS:
            if candidate in col_lower:
                found = col_lower[candidate]
                Colors.info(f"Using column '{found}' for element extraction.")
                return found

        Colors.warning("Could not auto-detect a species/formula column.")
        Colors.info(f"Available columns: {', '.join(map(str, df.columns))}")

        if not _interactive():
            raise ValueError(
                "Cannot auto-detect formula column and no interactive terminal "
                "available. Re-run with --column <name>."
            )

        while True:
            col = input(
                f"\n{Colors.CYAN}  Enter the column name to use: {Colors.ENDC}"
            ).strip()
            if col in df.columns:
                return col
            Colors.error(f"Column '{col}' not found. Please try again.")

    # ── classification logic ──────────────────────────────────────────────
    def classify(self, elements: Set[str]) -> str:
        if not elements:
            return "Unknown"
        metallic = elements & self.db.METALS_AND_METALLOIDS
        if len(elements) == 1:
            return "Element"
        if "C" in elements and metallic:
            return "Carbide"
        if "B" in elements and metallic:
            return "Boride"
        if "N" in elements and metallic:
            return "Nitride"
        if "O" in elements:
            return "Oxide"
        if elements & self.db.HALOGENS:
            return "Halide"
        if elements.issubset(self.db.METALS_AND_METALLOIDS):
            return self.metal_group(elements)
        return "Other"

    def metal_group(self, elements: Set[str]) -> str:
        for name, members in self.db.METAL_GROUP_PRIORITY:
            if elements & members:
                return name
        return "Other"

    # ── main entry point ──────────────────────────────────────────────────
    def run(self, df: pd.DataFrame,
            formula_col: Optional[str] = None) -> pd.DataFrame:
        col = self._detect_column(df, formula_col)
        df  = df.copy()
        elements         = df[col].apply(self.parser.parse)
        df[self.CLASS_COL] = elements.apply(self.classify)
        return df


# ============================================================================
# PERFORMANCE ANALYZER
# ============================================================================
class PerformanceAnalyzer:
    MIN_N = 10  # classes with fewer samples are flagged

    @staticmethod
    def ask_columns(df: pd.DataFrame) -> Optional[Tuple[str, str]]:
        Colors.step(5, "OPTIONAL: PER-CLASS MODEL PERFORMANCE")
        Colors.info(
            "Provide actual and predicted columns to compute MAE / RMSE / "
            "Max Error / R² per chemical class (and per crystal_system if present)."
        )
        Colors.info("Press ENTER to skip.")
        Colors.info(f"Columns: {', '.join(map(str, df.columns))}")

        actual = input(
            f"\n{Colors.CYAN}  Actual / true value column: {Colors.ENDC}"
        ).strip()
        if not actual:
            return None
        if actual not in df.columns:
            Colors.error(f"'{actual}' not found — skipping.")
            return None
        pred = input(
            f"{Colors.CYAN}  Predicted value column: {Colors.ENDC}"
        ).strip()
        if pred not in df.columns:
            Colors.error(f"'{pred}' not found — skipping.")
            return None
        return actual, pred

    @staticmethod
    def _metrics(y: np.ndarray, p: np.ndarray) -> Dict[str, float]:
        err  = p - y
        n    = len(y)
        mae  = float(np.mean(np.abs(err)))
        rmse = float(np.sqrt(np.mean(err ** 2)))
        max_e = float(np.max(np.abs(err)))
        ss_res = float(np.sum(err ** 2))
        ss_tot = float(np.sum((y - y.mean()) ** 2))
        r2   = 1 - ss_res / ss_tot if (n >= 2 and ss_tot > 0) else np.nan
        return {"N": n, "MAE": mae, "RMSE": rmse, "MaxError": max_e, "R2": r2}

    @classmethod
    def by_group(cls, df: pd.DataFrame, group_col: str,
                 actual: str, pred: str) -> pd.DataFrame:
        data = df[[group_col, actual, pred]].copy()
        data[actual] = pd.to_numeric(data[actual], errors="coerce")
        data[pred]   = pd.to_numeric(data[pred],   errors="coerce")
        data = data.dropna()

        rows = []
        for g, sub in data.groupby(group_col):
            m = cls._metrics(sub[actual].to_numpy(), sub[pred].to_numpy())
            m[group_col]  = g
            m["Low_N_Flag"] = f"n < {cls.MIN_N}" if m["N"] < cls.MIN_N else ""
            rows.append(m)

        m = cls._metrics(data[actual].to_numpy(), data[pred].to_numpy())
        m[group_col]  = "ALL"
        m["Low_N_Flag"] = ""
        rows.append(m)

        out = pd.DataFrame(rows)[
            [group_col, "N", "MAE", "RMSE", "MaxError", "R2", "Low_N_Flag"]
        ]
        return out.sort_values("N", ascending=False).reset_index(drop=True)


# ============================================================================
# EXPORTER
# ============================================================================
class Exporter:
    _CAT_COLOR: Dict[str, str] = {
        "Carbide":              Colors.RED,
        "Boride":               Colors.CYAN,
        "Nitride":              Colors.PINK,
        "Oxide":                Colors.YELLOW,
        "Halide":               Colors.LIME,
        "Alkali":               Colors.ORANGE,
        "Alkaline Earth":       Colors.ORANGE,
        "Transition Metal":     Colors.ORANGE,
        "Post-Transition":      Colors.ORANGE,
        "Lanthanoid/Actinoid":  Colors.ORANGE,
        "Element":              Colors.WHITE,
        "Other":                Colors.DARK_BLUE,
        "Unknown":              Colors.GREY,
    }

    @staticmethod
    def build_summary(df: pd.DataFrame, col: str) -> pd.DataFrame:
        s = df[col].value_counts().rename_axis(col).reset_index(name="Count")
        s["Share_%"] = (s["Count"] / len(df) * 100).round(2)
        return s

    @staticmethod
    def save_workbook(df: pd.DataFrame, output_dir: str,
                      perf: Dict[str, pd.DataFrame],
                      prefix: str = "") -> str:
        fname = (
            f"{prefix}_classified_materials.xlsx"
            if prefix else "classified_materials.xlsx"
        )
        out_path = os.path.join(output_dir, fname)

        with pd.ExcelWriter(out_path, engine="openpyxl") as writer:
            df.to_excel(writer, sheet_name="Classified_Data", index=False)
            Exporter.build_summary(df, MaterialClassifier.CLASS_COL).to_excel(
                writer, sheet_name="Summary_Class", index=False
            )
            for name, tbl in perf.items():
                tbl.round(4).to_excel(writer, sheet_name=name, index=False)
            for ws in writer.book.worksheets:
                ws.freeze_panes = "A2"

        Colors.success(f"Saved: {out_path}")
        return out_path

    @staticmethod
    def print_summary(df: pd.DataFrame) -> None:
        Colors.header("CLASSIFICATION SUMMARY")
        total   = len(df)
        summary = df[MaterialClassifier.CLASS_COL].value_counts()
        col_w   = max(len(k) for k in summary.index) + 2

        print(f"{Colors.BOLD}  {'Class':<{col_w}}  {'Count':>8}  {'Share':>7}   Distribution{Colors.ENDC}")
        print(f"  {'-'*col_w}  {'-'*8}  {'-'*7}   {'-'*42}")

        for cls, count in summary.items():
            pct = count / total * 100
            bar = Colors.BAR_CHAR * max(1, int(pct / 2.5))
            col = Exporter._CAT_COLOR.get(str(cls), Colors.CYAN)
            if Colors._USE_COLOR:
                print(f"  {col}{str(cls):<{col_w}}{Colors.ENDC}  {count:>8,}  {pct:>6.1f}%   {col}{bar}{Colors.ENDC}")
            else:
                print(f"  {str(cls):<{col_w}}  {count:>8,}  {pct:>6.1f}%   {bar}")

        print(f"\n  {'─'*70}")
        Colors.bold(f"  Total materials classified: {total:,}")


# ============================================================================
# JUPYTER / PROGRAMMATIC ENTRY POINT
# ============================================================================
def run_notebook(
    input_path:  str,
    output_dir:  str,
    formula_col: Optional[str] = None,
    actual_col:  Optional[str] = None,
    pred_col:    Optional[str] = None,
    sheet:       Optional[str] = None,
    prefix:      str           = "",
    display_summary: bool      = True,
) -> pd.DataFrame:
    """
    Call this from a Jupyter notebook or any Python script.

    Parameters
    ----------
    input_path   : Path to the input file (.xlsx/.xls/.csv).
    output_dir   : Directory where the workbook is saved
                   (a 'SISSO_material_classification' subfolder is created).
    formula_col  : Name of the formula/species column. Auto-detected if None.
    actual_col   : Column with true target values (for performance analysis).
    pred_col     : Column with predicted values (for performance analysis).
    sheet        : Excel sheet name or None (first sheet used if omitted).
    prefix       : Optional prefix for the output filename.
    display_summary : If True and in Jupyter, display a styled summary table.

    Returns
    -------
    pd.DataFrame with all original columns + 'Class'.
    """
    Colors.header("MATERIAL COMPOUND CLASSIFIER  v2.1")

    final_dir = os.path.join(output_dir, "SISSO_material_classification")
    os.makedirs(final_dir, exist_ok=True)

    Colors.step(3, "LOADING DATA")
    df = FileManager.load_file(input_path, sheet=sheet)

    Colors.step(4, "CLASSIFYING MATERIALS")
    df_classified = MaterialClassifier().run(df, formula_col=formula_col)

    perf: Dict[str, pd.DataFrame] = {}
    if actual_col and pred_col:
        Colors.step(5, "COMPUTING PERFORMANCE METRICS")
        perf["Perf_by_Class"] = PerformanceAnalyzer.by_group(
            df_classified, MaterialClassifier.CLASS_COL, actual_col, pred_col
        )
        Colors.success("Per-class performance table computed.")

        cs_col = next(
            (c for c in df_classified.columns
             if str(c).strip().lower() == "crystal_system"), None
        )
        if cs_col:
            perf["Perf_by_CrystalSystem"] = PerformanceAnalyzer.by_group(
                df_classified, cs_col, actual_col, pred_col
            )
            Colors.success(f"Crystal-system performance computed ('{cs_col}').")
        else:
            Colors.warning("No 'crystal_system' column found — skipping that analysis.")

    Colors.step(6, "EXPORTING WORKBOOK")
    prefix_clean = re.sub(r'[\\/:*?"<>|\s]+', "_", prefix).strip("_")
    Exporter.save_workbook(df_classified, final_dir, perf, prefix_clean)
    Exporter.print_summary(df_classified)

    # Pretty display inside Jupyter
    if display_summary and _in_jupyter():
        try:
            from IPython.display import display
            summary = Exporter.build_summary(df_classified, MaterialClassifier.CLASS_COL)
            display(summary.style.bar(subset=["Count"], color="#5fba7d").format({"Share_%": "{:.2f}%"}))
        except Exception:
            pass

    Colors.header("CLASSIFICATION COMPLETE")
    return df_classified


# ============================================================================
# CLI ENTRY POINT
# ============================================================================
def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="material_classifier",
        description="Classify materials from chemical formulae into compound families.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument("--input",   metavar="FILE",   help="Input .xlsx/.xls/.csv file")
    p.add_argument("--output",  metavar="DIR",    help="Output root directory")
    p.add_argument("--column",  metavar="COL",    help="Formula/species column name")
    p.add_argument("--sheet",   metavar="SHEET",  help="Excel sheet name (optional)")
    p.add_argument("--prefix",  metavar="PREFIX", default="",
                   help="Output filename prefix (optional)")
    p.add_argument("--actual",  metavar="COL",    help="True-value column for performance analysis")
    p.add_argument("--predicted", metavar="COL",  help="Predicted-value column for performance analysis")
    return p.parse_args()


def main() -> None:
    args = _parse_args()

    # ── Non-interactive (HPC / batch / scripted) ──────────────────────────
    if args.input and args.output:
        run_notebook(
            input_path  = args.input,
            output_dir  = args.output,
            formula_col = args.column,
            actual_col  = args.actual,
            pred_col    = args.predicted,
            sheet       = args.sheet,
            prefix      = args.prefix,
        )
        return

    # ── Interactive (terminal) ────────────────────────────────────────────
    Colors.header("MATERIAL COMPOUND CLASSIFIER  v2.1")

    input_path, chosen_sheet = FileManager.select_input_file()
    base_output_dir = FileManager.select_output_folder()
    output_dir = os.path.join(base_output_dir, "SISSO_material_classification")
    os.makedirs(output_dir, exist_ok=True)

    Colors.step(3, "LOADING DATA")
    df = FileManager.load_file(input_path, sheet=chosen_sheet)

    Colors.step(4, "CLASSIFYING MATERIALS")
    df_classified = MaterialClassifier().run(df, formula_col=args.column)

    perf: Dict[str, pd.DataFrame] = {}
    if _interactive():
        cols = PerformanceAnalyzer.ask_columns(df_classified)
        if cols:
            actual, pred = cols
            perf["Perf_by_Class"] = PerformanceAnalyzer.by_group(
                df_classified, MaterialClassifier.CLASS_COL, actual, pred
            )
            Colors.success("Per-class performance table computed.")

            cs_col = next(
                (c for c in df_classified.columns
                 if str(c).strip().lower() == "crystal_system"), None
            )
            if cs_col:
                perf["Perf_by_CrystalSystem"] = PerformanceAnalyzer.by_group(
                    df_classified, cs_col, actual, pred
                )
                Colors.success(f"Crystal-system performance computed ('{cs_col}').")
            else:
                Colors.warning("No 'crystal_system' column found — skipping.")

    Colors.step(6, "EXPORTING WORKBOOK")
    prefix = input(
        f"\n{Colors.CYAN}  Optional prefix for the output file name "
        f"(ENTER for none): {Colors.ENDC}"
    ).strip()
    prefix_clean = re.sub(r'[\\/:*?"<>|\s]+', "_", prefix).strip("_")
    Exporter.save_workbook(df_classified, output_dir, perf, prefix_clean)
    Exporter.print_summary(df_classified)

    Colors.header("CLASSIFICATION COMPLETE")


if __name__ == "__main__":
    main()
