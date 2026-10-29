#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# SLURM batch script — Material Compound Classifier
# Usage:  sbatch run_hpc.sh
# ─────────────────────────────────────────────────────────────────────────────
#SBATCH --job-name=mat_classify
#SBATCH --output=logs/%x_%j.out
#SBATCH --error=logs/%x_%j.err
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=01:00:00
# Uncomment and adjust the partition/account lines for your cluster:
##SBATCH --partition=standard
##SBATCH --account=your_project

# ── Environment ───────────────────────────────────────────────────────────────
# Option A: activate a conda environment
# module load anaconda3
# conda activate sisso_classifier

# Option B: activate a virtualenv
# source /path/to/venv/bin/activate

# ── Paths — edit these ────────────────────────────────────────────────────────
INPUT="/path/to/your/data.xlsx"
OUTPUT="/path/to/results"
COLUMN="formula"          # column that contains chemical formulae

# Excel sheet name to load.
# Leave empty ("") → first sheet is used automatically.
# Set to the exact sheet name (e.g. "Sheet1" or "Training_Data") to pick one.
SHEET=""

PREFIX="hpc_run"          # prefix for the output filename

# Optional: set both to enable per-class performance metrics.
# Leave empty to skip performance analysis.
ACTUAL=""                 # e.g. "band_gap"
PREDICTED=""              # e.g. "band_gap_pred"

# ── Run ───────────────────────────────────────────────────────────────────────
mkdir -p logs

python material_classifier.py \
    --input   "$INPUT"   \
    --output  "$OUTPUT"  \
    --column  "$COLUMN"  \
    ${SHEET:+--sheet "$SHEET"}         \
    ${ACTUAL:+--actual "$ACTUAL"}      \
    ${PREDICTED:+--predicted "$PREDICTED"} \
    --prefix  "$PREFIX"

echo "Done — exit code $?"
