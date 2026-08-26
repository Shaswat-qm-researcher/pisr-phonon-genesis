# Critical Regime Analysis (CRA)

A physics-informed post-processing tool that evaluates SISSO-derived symbolic descriptors by partitioning materials into physico-chemical regimes and quantifying how each descriptor controls the target property within each regime.

This sub-repository contains the full analysis pipeline applied to the **Debye temperature** ($\Theta_D$), using data sourced from the [Materials Project](https://materialsproject.org/) and the [AFLOW](http://aflow.org/) database.

---

## Table of Contents

- [Overview](#overview)
- [Repository Structure](#repository-structure)
- [Input Files](#input-files)
- [Analyses Performed](#analyses-performed)
- [Results](#results)
- [Requirements](#requirements)
- [Installation](#installation)
- [Usage](#usage)
- [Regime Partitioning Logic](#regime-partitioning-logic)
- [Symbol Conversion](#symbol-conversion)
- [Citation](#citation)

---
> **Note:** This is a sub-repository of the main project:  
> **[pisr-phonon-genesis](https://github.com/Shaswat-qm-researcher/pisr-phonon-genesis/)**

---

## Overview

Critical Regime Analysis (CRA) builds on SISSO (Sure Independence Screening and Sparsifying Operator) symbolic regression by:

1. Partitioning the materials dataset into three regimes — **LOW**, **MID**, and **HIGH** — based on the percentile distribution of selected descriptors.
2. Computing **Dominance Analysis** metrics (standardised regression coefficients × incremental R²) to identify which descriptor exerts the strongest control over the target property in each regime.
3. Computing a **Tunability Index** (normalised descriptor-to-response coupling) to map which regimes allow meaningful property tuning and which are inert or unstable.
4. Exporting all results to a structured multi-sheet Excel workbook and saving publication-quality PDF plots.

The analysis is applied here to predict and interpret the **Debye temperature** ($\Theta_D$) — a key phonon-related quantity governing heat capacity and thermal transport — using elastic and volumetric descriptors derived from DFT calculations.

---

## Repository Structure

```
critical-regime-analysis/
│
├── critical_regime_analysis.ipynb   # Main analysis notebook
├── CRA_data.csv                     # Input dataset (Materials Project + AFLOW)
├── symbol_conversion.txt            # Column-name → LaTeX label mapping
│
├── requirements.txt                 # Pinned Python dependencies
├── setup_env.py                     # One-command environment installer
│
├── results/                         # All generated outputs (auto-created on run)
│   ├── Plots/                       # Publication-quality PDF figures
│   │   ├── Debye_Temperature_Plot_Correlation_Heatmap.pdf
│   │   ├── Debye_Temperature_Plot_Distribution_D.pdf
│   │   ├── Debye_Temperature_Plot_Distribution_SM.pdf
│   │   ├── Debye_Temperature_Plot_Distribution_VPA.pdf
│   │   ├── Debye_Temperature_Plot_Distribution_YM.pdf
│   │   ├── Debye_Temperature_Plot_Dominance_Map.pdf
│   │   ├── Debye_Temperature_Plot_ParallelCoordinates.pdf
│   │   └── Debye_Temperature_Plot_Tunability_vs_CV.pdf
│   └── Debye_Temperature_SISSO_Regime_Analysis.xlsx   # Multi-sheet results workbook
│
└── README.md
```

---

## Input Files

### `CRA_data.csv`

The primary dataset containing DFT-computed material properties sourced from the Materials Project and AFLOW databases. Each row represents one material entry. Columns include:

| Column | Symbol | Description |
|---|---|---|
| `Material_ID` | — | Unique material identifier |
| `formula` | — | Chemical formula |
| `SM` | $G_{VRH}$ | Shear Modulus (Voigt–Reuss–Hill) |
| `YM` | $E$ | Young's Modulus (Voigt–Reuss–Hill) |
| `VPA` | $V_\mathrm{atom}$ | Volume Per Atom |
| `D` | $\rho$ | Mass Density |
| `Term_Moduli` | $(G_{VRH}+E)/E^{1/2}$ | SISSO-derived composite elastic descriptor |
| `Term_Interatomic_spacing` | $V_\mathrm{atom}^{-1/3}$ | SISSO-derived interatomic spacing descriptor |
| `Term_Mass_density` | $\rho^{-1/2}$ | SISSO-derived density descriptor |
| `DT` | $\Theta_D$ | Debye Temperature (target property) |

### `symbol_conversion.txt`

A plain-text mapping file that converts raw column names to LaTeX symbols used in all figures and tables. Format is one assignment per line:

```
SM = $G_{\mathrm{VRH}}$
D  = $\rho$
# Lines starting with # are ignored
```

The full list of supported symbols is documented inside the file.

---

## Analyses Performed

### 1. Pearson Correlation Screening
Computes a full correlation matrix across all input descriptors and the target property. Visualised as a heatmap to identify collinear or redundant features before regime analysis.

### 2. Property Distribution Plots
Histograms and KDE plots for each descriptor and the target, segmented by LOW / MID / HIGH regime membership, to inspect distributional overlap and separation.

### 3. Regime Partitioning
Materials are assigned to LOW, MID, or HIGH regimes based on quantile thresholds (α = 0.15) applied independently to each descriptor. All regime combinations are enumerated.

### 4. Parallel Coordinates Map
Traces each material's descriptor values across axes coloured by its target-property band (LOW / MID / HIGH), revealing cross-descriptor patterns and regime interactions.

### 5. Dominance Analysis
Computes standardised OLS regression coefficients and incremental R² contributions for each descriptor within each regime combination. The dominance score identifies the controlling descriptor per regime.

### 6. Tunability Analysis
Calculates a normalised descriptor-to-response coupling index and plots it against the coefficient of variation (CV%) of the target within each regime, classifying regimes as *Tunable*, *Inert*, *Unstable*, or *Undefined*.

---

## Results

All outputs are saved to the `results/` directory, which is created automatically on first run.

### `results/Plots/`
Eight publication-quality figures exported as both **PDF** (vector) and **PNG** (600 dpi):

| File | Description |
|---|---|
| `Debye_Temperature_Plot_Correlation_Heatmap.pdf` | Pearson correlation heatmap of all descriptors and target |
| `Debye_Temperature_Plot_Distribution_D.pdf` | Regime-segmented distribution of mass density $\rho$ |
| `Debye_Temperature_Plot_Distribution_SM.pdf` | Regime-segmented distribution of shear modulus $G_{VRH}$ |
| `Debye_Temperature_Plot_Distribution_VPA.pdf` | Regime-segmented distribution of volume per atom $V_\mathrm{atom}$ |
| `Debye_Temperature_Plot_Distribution_YM.pdf` | Regime-segmented distribution of Young's modulus $E$ |
| `Debye_Temperature_Plot_Dominance_Map.pdf` | Dominance Analysis map across all regime combinations |
| `Debye_Temperature_Plot_ParallelCoordinates.pdf` | Parallel coordinates coloured by target property ranges |
| `Debye_Temperature_Plot_Tunability_vs_CV.pdf` | Tunability index vs. target CV% scatter by regime |

### `results/Debye_Temperature_SISSO_Regime_Analysis.xlsx`
A multi-sheet Excel workbook containing all numerical results:
- Per-regime descriptor statistics
- Dominance scores and incremental R² values
- Tunability indices
- Full regime combination table

---

## Requirements

| Package | Version |
|---|---|
| Python | 3.12.12 (Anaconda) |
| numpy | 1.26.4 |
| pandas | 2.2.3 |
| matplotlib | 3.9.2 |
| scipy | 1.14.1 |
| scikit-learn | 1.5.2 |
| seaborn | 0.13.2 |
| openpyxl | 3.1.2 |
| XlsxWriter | 3.2.9 |

---

## Installation

**Step 1 — Clone the repository**

```bash
git clone https://github.com/Shaswat-qm-researcher/pisr-phonon-genesis/critical-regime-analysis.git
cd critical-regime-analysis
```

**Step 2 — Create a conda environment (recommended)**

```bash
conda create -n cra_env python=3.12 anaconda
conda activate cra_env
```

**Step 3 — Install dependencies**

Run the provided setup script:

```bash
python setup_env.py
```

Or install directly from `requirements.txt`:

```bash
pip install -r requirements.txt
```

---

## Usage

1. Ensure both `CRA_data.csv` and `symbol_conversion.txt` are in the same directory as the notebook. Or enter the manual path for both seperatly.
2. Launch Jupyter:
   ```bash
   jupyter notebook critical_regime_analysis.ipynb
   ```
3. Run all cells. The notebook will interactively prompt you to:
   - Select the data file and sheet (if Excel)
   - Optionally load `symbol_conversion.txt` for LaTeX axis labels
   - Select descriptor, SISSO-term, and target columns
   - Define coupled descriptor groups (if any)
   - Choose the output folder name
   - Set target-band thresholds (or accept the quantile-based defaults)

4. All plots and the Excel results workbook are saved to `results/` automatically.

---

## Regime Partitioning Logic

Regimes are defined by quantile windows applied independently to each descriptor, using a bandwidth parameter α = 0.15:

| Regime | Percentile Range | Description |
|---|---|---|
| **LOW** | [min … Q(0.15)] | Bottom 15% of materials by descriptor value |
| **MID** | [Q(0.425) … Q(0.575)] | Central 15% of materials |
| **HIGH** | [Q(0.85) … max] | Top 15% of materials |

All combinations of LOW / MID / HIGH across the selected descriptors are evaluated. Target-band thresholds (for plot colouring) use the same Q(0.15) and Q(0.85) quantiles of the target distribution by default, and can be overridden interactively.

---

## Symbol Conversion

The `symbol_conversion.txt` file maps raw column names (as they appear in the CSV/Excel) to LaTeX mathematical symbols used in all figures. A full list of supported features and their symbols is provided in the file header. Example entries:

```
SM     = $G_{\mathrm{VRH}}$       # Shear Modulus
YM     = $E$                       # Young's Modulus
VPA    = $V_{\mathrm{atom}}$       # Volume Per Atom
D      = $\rho$                    # Mass Density
DT     = $\Theta_D$                # Debye Temperature
```

Lines beginning with `#` are treated as comments and ignored.

---

## Citation

If you use this code or dataset in your work, please cite the main repository:

```bibtex
@article{
}
```

Data sourced from:
- [Materials Project](https://materialsproject.org/) — A. Jain *et al.*, APL Materials 1, 011002 (2013).
- [AFLOW](http://aflow.org/) — S. Curtarolo *et al.*, Computational Materials Science 58, 218 (2012).
