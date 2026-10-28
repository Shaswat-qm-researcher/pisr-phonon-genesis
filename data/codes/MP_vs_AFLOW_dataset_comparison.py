"""
MP vs AFLOW dataset comparison (interactive + automation friendly)

Works on: Windows/Linux/macOS PC, Jupyter (notebook / Lab / VS Code), HPC (interactive or batch).

Usage
-----
Interactive (PC / Jupyter / HPC login or srun session):
    python compare_mp_aflow.py
    -> prompts for MP csv, AFLOW csv, column names, and the save location

Non-interactive (HPC batch / SLURM / PBS):
    python compare_mp_aflow.py --mp /path/MP.csv --aflow /path/AFLOW.csv --out /path/results

Jupyter:
    %run compare_mp_aflow.py
    (or paste into a cell; input() prompts appear inline)
"""
import argparse
import os
import re
import sys

import matplotlib
matplotlib.use("Agg")  # headless-safe: figures are saved to file, never need a display
import matplotlib.pyplot as plt
import pandas as pd

# ── Default column names (press Enter at the prompt to accept) ────────────────
DEFAULT_MP_COLS    = {'id': 'material_id', 'formula': 'formula', 'sg': 'spacegroup',
                      'species': 'species', 'NA': 'NA'}
DEFAULT_AFLOW_COLS = {'id': 'auid', 'formula': 'formula', 'sg': 'spacegroup',
                      'species': 'species', 'NA': 'NA'}


# ── Input helpers ─────────────────────────────────────────────────────────────
def clean_path(p):
    """Strip quotes/whitespace, expand ~ and env vars, make absolute."""
    p = str(p).strip().strip('"').strip("'")
    return os.path.abspath(os.path.expandvars(os.path.expanduser(p)))


def ask(prompt, default=None):
    """input() with an optional default; raises a clear error if no stdin (batch jobs)."""
    suffix = f" [{default}]" if default else ""
    try:
        ans = input(f"{prompt}{suffix}: ").strip()
    except EOFError:
        if default is not None:
            return default
        sys.exit(f"ERROR: no interactive input available for '{prompt}'. "
                 f"Run with --mp, --aflow and --out arguments instead.")
    return ans or default


def ask_file(label, preset=None):
    if preset:
        path = clean_path(preset)
        if not os.path.isfile(path):
            sys.exit(f"ERROR: {label} file not found: {path}")
        return path
    while True:
        path = clean_path(ask(f"Enter full path to the {label} CSV file"))
        if os.path.isfile(path):
            return path
        print(f"  File not found: {path}\n  Please try again.")


def ask_columns(label, defaults, interactive):
    cols = dict(defaults)
    if interactive and (ask(f"Use default {label} column names {defaults}? (y/n)", "y") or "y").lower().startswith("n"):
        for k, v in defaults.items():
            cols[k] = ask(f"  {label} column for '{k}'", v)
    return cols


def get_output_folder(preset=None):
    base = clean_path(preset or ask("Enter the save location (a folder will be created inside it)"))
    folder = os.path.join(base, "MP_vs_AFLOW_comparison")
    os.makedirs(folder, exist_ok=True)  # creates it (and parents) only if missing
    return folder


# ── Core helpers ──────────────────────────────────────────────────────────────
def parse_formula(formula):
    pattern = r'([A-Z][a-z]?)(\d*\.?\d*)'
    counts = {}
    for element, num in re.findall(pattern, str(formula)):
        counts[element] = float(num) if num else 1.0
    return counts


def make_key(df, cols):
    """Key = (sorted element counts, space group number)."""
    missing = [c for c in (cols['formula'], cols['sg']) if c not in df.columns]
    if missing:
        sys.exit(f"ERROR: column(s) {missing} not found. Available columns: {list(df.columns)}")
    formula_key = df[cols['formula']].apply(
        lambda f: tuple(sorted(parse_formula(f).items())))
    sg_key = pd.to_numeric(df[cols['sg']], errors='coerce')
    return pd.Series(list(zip(formula_key, sg_key)), index=df.index)


def make_chart(values, labels, graph_files):
    total_mat = values[0]
    bar_colors = ['#E63946', '#F4A261', '#2A9D8F', '#457B9D', '#6A4C93', '#F4D35E', '#06D6A0']

    plt.rcParams.update({'font.family': 'sans-serif',
                         'font.sans-serif': ['Arial', 'DejaVu Sans'],  # fallback for HPC
                         'font.size': 12})
    fig, ax = plt.subplots(figsize=(9, 5.5))
    bars = ax.barh(labels[::-1], values[::-1], color=bar_colors[::-1],
                   edgecolor='black', linewidth=0.9, height=0.62)

    for bar, val in zip(bars, values[::-1]):
        pct = val / total_mat * 100 if total_mat else 0
        ax.text(bar.get_width() + max(values) * 0.008,
                bar.get_y() + bar.get_height() / 2,
                f'{val:,}  ({pct:.1f}%)',
                va='center', ha='left', fontsize=11, fontweight='bold', color='#111111')

    ax.set_xlim(0, max(values) * 1.30)
    ax.set_xlabel('Number of Compounds', fontsize=13, labelpad=6)
    ax.set_title('Dataset Comparison: MP vs AFLOW', fontsize=15, fontweight='bold', pad=12)
    fig.patch.set_facecolor('#F8F9FA')
    ax.set_facecolor('#F0F2F5')
    for spine in ax.spines.values():
        spine.set_visible(True)
        spine.set_linewidth(1.1)
        spine.set_color('#555555')
    ax.tick_params(axis='both', direction='in', length=4, width=1.0, top=True, right=True)
    ax.xaxis.grid(True, linestyle='--', linewidth=0.6, color='#CCCCCC', alpha=0.8)
    ax.set_axisbelow(True)
    plt.tight_layout()

    for path in graph_files:
        plt.savefig(path, dpi=600, bbox_inches='tight', facecolor=fig.get_facecolor())
    plt.close(fig)


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Compare MP and AFLOW datasets")
    parser.add_argument('--mp', help="path to MP cleaned CSV")
    parser.add_argument('--aflow', help="path to AFLOW cleaned CSV")
    parser.add_argument('--out', help="base save location (a subfolder is created)")
    args, _ = parser.parse_known_args()  # ignores Jupyter's extra argv

    interactive = not (args.mp and args.aflow and args.out)

    mp_path    = ask_file("Materials Project (MP)", args.mp)
    aflow_path = ask_file("AFLOW", args.aflow)
    MP_COLS    = ask_columns("MP", DEFAULT_MP_COLS, interactive)
    AFLOW_COLS = ask_columns("AFLOW", DEFAULT_AFLOW_COLS, interactive)
    out_folder = get_output_folder(args.out)

    common_csv     = os.path.join(out_folder, 'common_compounds.csv')
    aflow_only_csv = os.path.join(out_folder, 'aflow_only_compounds.csv')
    graph_pdf      = os.path.join(out_folder, 'data_comparison.pdf')
    graph_png      = os.path.join(out_folder, 'data_comparison.png')

    # Load
    print("\nLoading data ...")
    mp_df    = pd.read_csv(mp_path)
    aflow_df = pd.read_csv(aflow_path)

    mp_df['key']    = make_key(mp_df, MP_COLS)
    aflow_df['key'] = make_key(aflow_df, AFLOW_COLS)

    # Matching
    mp_keys     = set(mp_df['key'])
    aflow_keys  = set(aflow_df['key'])
    common_keys = mp_keys & aflow_keys

    mp_sub = mp_df[mp_df['key'].isin(common_keys)].rename(
        columns={MP_COLS[k]: f'MP_{k}' for k in MP_COLS})
    af_sub = aflow_df[aflow_df['key'].isin(common_keys)].rename(
        columns={AFLOW_COLS[k]: f'AFLOW_{k}' for k in AFLOW_COLS})

    keep_mp = ['key'] + [f'MP_{k}' for k in MP_COLS]
    keep_af = ['key'] + [f'AFLOW_{k}' for k in AFLOW_COLS]
    matches_df = mp_sub[keep_mp].merge(af_sub[keep_af], on='key').drop(columns='key')

    aflow_only_df = aflow_df[~aflow_df['key'].isin(mp_keys)].drop(columns='key')

    # Save CSVs
    matches_df.to_csv(common_csv, index=False)
    aflow_only_df.to_csv(aflow_only_csv, index=False)

    # Counts (unique formula + space group combinations)
    num_matches = len(common_keys)
    mp_total    = len(mp_keys)
    aflow_total = len(aflow_keys)
    mp_only     = mp_total - num_matches
    aflow_only  = aflow_total - num_matches
    total_sep   = mp_only + aflow_only
    total_mat   = mp_only + aflow_only + num_matches

    labels = ['Total Unique Materials', 'MP Total', 'MP Only', 'AFLOW Total',
              'AFLOW Only', 'Total Separate', 'Matched (Both)']
    values = [total_mat, mp_total, mp_only, aflow_total, aflow_only, total_sep, num_matches]
    make_chart(values, labels, [graph_pdf, graph_png])

    # Summary (also saved to a text log)
    summary = (
        f"Output folder           : {out_folder}\n"
        f"Common compounds (CSV)  : {common_csv}\n"
        f"AFLOW-only (CSV)        : {aflow_only_csv}\n"
        f"Comparison chart        : {graph_pdf} (+ .png)\n\n"
        f"Summary (unique formula + space group)\n"
        f"  Total unique materials : {total_mat:,}\n"
        f"  MP total               : {mp_total:,}\n"
        f"  AFLOW total            : {aflow_total:,}\n"
        f"  Matched (both DBs)     : {num_matches:,}\n"
        f"  MP only                : {mp_only:,}\n"
        f"  AFLOW only             : {aflow_only:,}  -> {len(aflow_only_df):,} rows in CSV\n"
    )
    with open(os.path.join(out_folder, 'summary.txt'), 'w', encoding='utf-8') as f:
        f.write(f"MP file    : {mp_path}\nAFLOW file : {aflow_path}\n\n{summary}")
    print("\n" + summary)


if __name__ == "__main__":
    main()