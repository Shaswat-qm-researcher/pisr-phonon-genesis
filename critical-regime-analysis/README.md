# Critical Regime Analysis (CRA)

A physics-informed post-processing tool that evaluates SISSO-derived symbolic descriptors by partitioning materials into physico-chemical regimes and quantifying how each descriptor controls the target property within each regime. It also tests how robust the regime conclusions are to the choice of regime width (α) and to finite sample size.

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
- [Tunability and Dominance Definitions](#tunability-and-dominance-definitions)
- [Symbol Conversion](#symbol-conversion)
- [Citation](#citation)

---
> **Note:** This is a sub-repository of the main project:  
> **[pisr-phonon-genesis](https://github.com/Shaswat-qm-researcher/pisr-phonon-genesis/)**

---

## Overview

Critical Regime Analysis (CRA) builds on SISSO (Sure Independence Screening and Sparsifying Operator) symbolic regression by:

1. Screening the primitive descriptors for correlation and **collinearity (VIF)**.
2. Partitioning the materials dataset into three regimes (**LOW**, **MID**, **HIGH**) based on the percentile distribution of each descriptor, with a user-adjustable regime width α.
3. Computing **Dominance Analysis** metrics (standardised regression coefficients × incremental R²) to identify which SISSO term exerts the strongest control over the target property in each regime.
4. Computing a **Tunability Index** (normalised descriptor-to-response coupling) and plotting it against the target CV% to map which regimes allow meaningful property tuning.
5. Testing the **robustness** of every regime through an α sweep and a within-regime bootstrap.
6. Exporting all results to a structured 15-sheet Excel workbook and saving publication-quality plots (PNG at 600 dpi and PDF).

The analysis is applied here to predict and interpret the **Debye temperature** ($\Theta_D$), a key phonon-related quantity governing heat capacity and thermal transport, using elastic and volumetric descriptors derived from DFT calculations.

---

## Repository Structure

```
critical-regime-analysis/
│
├── critical_regime_analysis.ipynb   # Main interactive analysis notebook
├── CRA_data.csv                     # Input dataset (Materials Project + AFLOW)
├── symbol_conversion.txt            # Column-name → LaTeX label mapping
│
├── requirements.txt                 # Pinned Python dependencies
├── setup_env.py                     # One-command environment installer
│
├── results/                         # Output root (chosen at the prompt)
│   └── CRA/                         # Created automatically on run
│       ├── Plots/                   # Each figure saved as .png (600 dpi) and .pdf
│       │   ├── Debye_Temperature_Plot_Correlation_Heatmap
│       │   ├── Debye_Temperature_Plot_Distribution_D
│       │   ├── Debye_Temperature_Plot_Distribution_SM
│       │   ├── Debye_Temperature_Plot_Distribution_VPA
│       │   ├── Debye_Temperature_Plot_Distribution_YM
│       │   ├── Debye_Temperature_Plot_ParallelCoordinates
│       │   ├── Debye_Temperature_Plot_Dominance_Map
│       │   └── Debye_Temperature_Plot_Tunability_vs_CV
│       └── Debye_Temperature_SISSO_Regime_Analysis.xlsx   # 15-sheet results workbook
│
└── README.md (This file)
```

---

## Input Files

### `CRA_data.csv`

The primary dataset containing DFT-computed material properties sourced from the Materials Project and AFLOW databases. Each row represents one material entry. Excel files (`.xlsx`, `.xls`, `.xlsm`) are also supported, and the sheet is chosen at the prompt. Columns include:

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

If your file has no pre-computed SISSO-term columns, leave that prompt blank and define the terms interactively from formulas over the existing columns (see [Usage](#usage)).

### `symbol_conversion.txt`

A plain-text mapping file that converts raw column names to LaTeX symbols used in all figures. Format is one `column = label` assignment per line:

```
SM = $G_{\mathrm{VRH}}$
D  = $\rho$
# Lines starting with # are ignored
```

You can give either the path to the file itself or the folder that contains it. If no file is provided, the raw column headers are used as labels.

---

## Analyses Performed

### 1. Pearson Correlation Screening
Computes the Pearson correlation matrix of the primitive input descriptors and shows it as a lower-triangular heatmap to identify correlated or redundant features before regime analysis.

### 2. Collinearity Check (VIF)
Computes the variance inflation factor of each primitive descriptor (VIF = diagonal of the inverse correlation matrix) for two descriptor sets: **all primitive descriptors**, and **coupled groups collapsed** to their leader (the set actually used by CRA). VIF > 5 is flagged as moderate and VIF > 10 as severe.

### 3. Regime Partitioning and Distribution Plots
Materials are assigned to LOW, MID, or HIGH windows based on quantile thresholds applied independently to each descriptor (default α = 0.15, user-adjustable). All regime combinations are enumerated, with coupled descriptors sharing the leader's level. A box plot per descriptor, overlaid with the LOW / MID / HIGH bands, shows where each window sits in the distribution.

### 4. Parallel Coordinates Map
Draws one line per regime across the descriptor axes and the mean target value. Line colour encodes the target band (LOW / MID / HIGH) and line thickness is proportional to the number of materials in the regime.

### 5. Dominance Analysis
For each regime, computes standardised OLS coefficients (β*) and the incremental R² (ΔR²) lost when each SISSO term is dropped. Their product, normalised to 100 %, is the dominance 𝔇 and identifies the controlling SISSO term per regime. Per-term VIF warnings are reported. The polygon dominance map needs at least 3 SISSO terms, and its vertices are assigned automatically by mean dominance.

### 6. Tunability Analysis
Calculates a normalised descriptor-to-response coupling index T for each descriptor in each regime and plots T_max against the coefficient of variation (CV%) of the target. Each regime falls in one of four quadrants (see [definitions](#tunability-and-dominance-definitions)).

### 7. Sensitivity to Regime Width (α Sweep)
Repeats the full CRA at α = 0.10, 0.15, 0.20, 0.25 (plus the chosen α) and reports, for each regime, how much its size, mean target and CV vary, and whether its dominant term, most-tunable descriptor and tunability quadrant change.

### 8. Within-Regime Bootstrap
Resamples the materials inside each regime (B = 1000, windows held fixed, since threshold effects are covered by the α sweep) to obtain 95 % confidence intervals for the mean target, CV, T_max, T_j and dominance %, together with the fraction of resamples that reproduce the reference dominant term, most-tunable descriptor and quadrant. A regime is labelled **robust** if it has n ≥ 20 and at least 90 % agreement on both the dominant term and the quadrant, and **indicative only** otherwise.

---

## Results

All outputs are saved to `<output root>/CRA/`, which is created automatically on first run.

### `CRA/Plots/`
Publication-quality figures, each exported as both **PNG** (600 dpi) and **PDF** (vector):

| File | Description |
|---|---|
| `Debye_Temperature_Plot_Correlation_Heatmap` | Lower-triangular Pearson correlation heatmap of the primitive descriptors |
| `Debye_Temperature_Plot_Distribution_D` | Box plot of mass density $\rho$ with LOW / MID / HIGH bands |
| `Debye_Temperature_Plot_Distribution_SM` | Box plot of shear modulus $G_{VRH}$ with LOW / MID / HIGH bands |
| `Debye_Temperature_Plot_Distribution_VPA` | Box plot of volume per atom $V_\mathrm{atom}$ with LOW / MID / HIGH bands |
| `Debye_Temperature_Plot_Distribution_YM` | Box plot of Young's modulus $E$ with LOW / MID / HIGH bands |
| `Debye_Temperature_Plot_ParallelCoordinates` | Regime lines across descriptors and mean target, coloured by target band |
| `Debye_Temperature_Plot_Dominance_Map` | Polygon dominance map across all regimes (requires ≥ 3 SISSO terms) |
| `Debye_Temperature_Plot_Tunability_vs_CV` | T_max vs target CV% scatter with the four-quadrant classification |

### `CRA/Debye_Temperature_SISSO_Regime_Analysis.xlsx`
A 15-sheet Excel workbook containing all numerical results:

| # | Sheet | Content |
|---|---|---|
| 1 | `Regime_Summary` | Headline metrics per regime |
| 2 | `Descriptor_Stats` | Min / max / mean / std / range of each descriptor per regime |
| 3 | `SISSO_Stats` | Same statistics for each SISSO term |
| 4 | `Target_Stats` | Target statistics and CV% per regime |
| 5 | `Dominance_Analysis` | β*, ΔR², VIF and 𝔇% per SISSO term per regime |
| 6 | `Tunability_Analysis` | All intermediate tunability quantities per descriptor per regime |
| 7 | `Regime_Windows` | LOW / MID / HIGH thresholds for each descriptor |
| 8 | `Skipped_Combinations` | Combinations with fewer than 5 materials |
| 9 | `Global_Statistics` | Dataset-wide descriptive statistics |
| 10 | `Full_Dataset` | Data for all columns used |
| 11 | `Collinearity_VIF` | VIF for all descriptors and for coupled groups collapsed |
| 12 | `Pearson_Matrix` | Pearson correlation matrix of the primitive descriptors |
| 13 | `Alpha_Stability_Summary` | Per-regime stability across the α sweep |
| 14 | `Alpha_Sweep_All` | Full results of every regime at every α |
| 15 | `Bootstrap_CI` | Bootstrap confidence intervals and robustness status |

---

## Requirements

| Package | Version |
|---|---|
| Python | 3.12+ (tested with 3.12.12, Anaconda) |
| numpy | 1.26.4 |
| pandas | 2.2.3 |
| matplotlib | 3.9.2 |
| scipy | 1.14.1 |
| scikit-learn | 1.5.2 |
| seaborn | 0.13.2 |
| openpyxl | 3.1.2 |
| XlsxWriter | 3.2.9 |
| Jupyter (Notebook or JupyterLab) | to run `critical_regime_analysis.ipynb` |

---

## Installation

**Step 1 — Clone the repository**

```bash
git clone https://github.com/Shaswat-qm-researcher/pisr-phonon-genesis/critical-regime-analysis.git
cd pisr-phonon-genesis
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

1. Launch Jupyter and open the notebook:
   ```bash
   jupyter notebook critical_regime_analysis.ipynb
   ```
   (or `jupyter lab critical_regime_analysis.ipynb`; the notebook also opens in VS Code.)
2. Run the cells from top to bottom (**Run → Run All Cells**). Enter your answers in the interactive prompts that appear below the cells:
   - Enter the data folder path and pick the file (`.xlsx` / `.xls` / `.xlsm` / `.csv`); for Excel, pick the sheet
   - Optionally provide `symbol_conversion.txt` (the file path, or the folder containing it) for LaTeX labels
   - Select the primitive descriptors, the pre-computed SISSO-term columns (or press Enter to define the terms from formulas), and the target column
   - Define any coupled descriptor groups, one group per line (the first descriptor in each group is the leader)
   - Set the regime width α (press Enter for the default 0.15; valid range 0 < α < 0.5)
   - Enter the output root folder and a file prefix (e.g. `Debye_Temperature`)
   - Set the target-band thresholds (or accept the defaults)
3. All plots and the Excel workbook are saved to `<output root>/CRA/` automatically.

### Defining SISSO terms interactively

If no SISSO columns are supplied, you are asked for the number of terms and, for each, a name and a formula over the existing columns.

- Operators: `+  -  *  /  **`
- Functions: `exp`, `sqrt`, `cbrt`, `log`, `log10`, `abs`, `sin`, `cos`, `tan`
- `|expr|` is converted automatically to `abs(expr)`

---

## Regime Partitioning Logic

Regimes are defined by quantile windows applied independently to each descriptor, using a bandwidth parameter α (default 0.15, adjustable):

| Regime | Percentile Range | Description |
|---|---|---|
| **LOW** | [min … Q(α)] | Bottom α of materials by descriptor value |
| **MID** | [Q(0.5 − α/2) … Q(0.5 + α/2)] | Central α of materials |
| **HIGH** | [Q(1 − α) … max] | Top α of materials |

For α = 0.15 these are [min … Q(0.15)], [Q(0.425) … Q(0.575)] and [Q(0.85) … max].

- Smaller α gives more extreme regimes with fewer materials; larger α gives more data but weaker regime distinction.
- All LOW / MID / HIGH combinations are enumerated over the independent descriptors. Coupled descriptors always take the level of their group leader.
- Regimes with fewer than 5 materials are skipped and listed in the `Skipped_Combinations` sheet.

### Target bands (plot colouring only)

The target bands used to colour the parallel coordinates and the dominance map are based on the **value range** of the target, not on its quantiles:

- **LOW band:** target < min + 0.15 × (max − min)
- **HIGH band:** target ≥ min + 0.85 × (max − min)

Custom absolute thresholds can be entered at the prompt.

---

## Dominance and Tunability Definitions

**Dominance.** 𝔇_j = |β*_j| × ΔR²_norm_j, normalised so the terms sum to 100 % within a regime. VIF > 5 is flagged as a multicollinearity warning.

**Tunability.** For descriptor *j* in a regime:

$$T_j = \frac{\Delta D_j / G_j}{p_\mathrm{eff}}, \qquad p_\mathrm{eff} = \underset{k \neq j}{\mathrm{mean}}\left(\frac{\Delta D_k}{G_k}\right)$$

where ΔD is the descriptor range within the regime and G is its global range. T > 1 means tunable, T < 1 limited, and T ≈ 0 frozen.

**Quadrants** (T_max vs target CV%, thresholds T = 1 and CV = 25 %):

| Quadrant | Meaning |
|---|---|
| I | Tunable but high variability |
| II | Uncontrollable |
| III | Frozen and stable |
| IV | Tunable and stable (ideal for engineering) |

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


---
**Last Updated**: 28-10-2026