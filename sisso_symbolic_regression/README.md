# SISSO Symbolic Regression and Post-processing

A comprehensive workflow repository for material property prediction using SISSO (Sure Independence Screening and Sparsifying Operator) with post-processing and material classification tools.

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![SISSO](https://img.shields.io/badge/SISSO-v3.5-green.svg)](https://github.com/rouyang2017/SISSO)

> **Note:** This is a sub-repository of the main project:  
> **[pisr-phonon-genesis](https://github.com/Shaswat-qm-researcher/pisr-phonon-genesis/)**

---

## Overview

This repository contains:
- **SISSO input files** (`train.dat`, `SISSO.in`) for four property runs
- **SISSO output files** with best equations, SIS subspaces, and top-ranked models
- **Post-processing notebook** for evaluating SISSO equations, generating parity plots, and exporting results with conformal prediction intervals
- **Material classifier** for per-class and per-crystal-system performance breakdown

---

## Properties Analyzed

| Property | Symbol | Column | Dataset | Samples | Folder | In manuscript |
|---|---|---|---|---|---|---|
| Debye Temperature (phonopy + elastic) | $\Theta_D$ | `DT` | MP | 6,275 | `Debye_temperature_phonopy` | ✅ Yes |
| Debye Temperature (elastic only) | $\Theta_D$ | `DT` | MP | 6,275 | `Debye_temperature` | Reference run |
| Specific Heat (const. pressure, 300 K) | $C_p$ | `Cp_300` | AFLOW | 5,077 | `Specific_heat_at_constant_pressure` | ✅ Yes |
| Lattice Thermal Conductivity (300 K) | $\kappa$ | `TC_300` | AFLOW | 5,077 | `Thermal_conductivity` | ✅ Yes |

> **Important — two Θ_D runs for MP:**  
> `Debye_temperature_phonopy` is the **primary manuscript run**. Its training data (`train.dat`) uses a mixed Debye temperature dataset: 4,882 compounds from elastic (`sound_velocity_elastic`) and 1,394 from harmonic phonon calculations (`PDOS_phonopy`), and uses `material_id` (mp-xxxx) as the sample identifier. `Debye_temperature` is a reference run that used elastic-derived DT only and chemical formulae as sample identifiers. All post-processing results and classifier outputs for the MP Θ_D dataset correspond to the `Debye_temperature_phonopy` run.

---

## Repository Structure

```
sisso_symbolic_regression/
│
├── SISSO_model_config/
│   ├── config and data - SISSO INPUT/
│   │   ├── Debye_temperature_phonopy/         ★ MANUSCRIPT — MP, mixed DT source
│   │   │   ├── SISSO.in    # 6,275 samples, 4 features: SM, YM, D, VPA
│   │   │   └── train.dat   # material_id | DT | SM | YM | D | VPA
│   │   ├── Debye_temperature/                 # Reference run — elastic DT only
│   │   │   ├── SISSO.in    # 6,275 samples, 4 features: SM, YM, VPA, D
│   │   │   └── train.dat   # formula | DT | SM | YM | VPA | D
│   │   ├── Specific_heat_at_constant_pressure/
│   │   │   ├── SISSO.in    # 5,077 samples, 5 features: NA, PR, PUGR, SM, VPA
│   │   │   └── train.dat   # formula | Cp_300 | NA | PR | PUGR | SM | VPA
│   │   └── Thermal_conductivity/
│   │       ├── SISSO.in    # 5,077 samples, 5 features: SM, YM, NA, NE, D
│   │       └── train.dat   # formula | TC_300 | SM | YM | NA | NE | D
│   │
│   └── model and equation - SISSO OUTPUT/
│       ├── Debye_temperature_phonopy/         ★ MANUSCRIPT
│       │   ├── SISSO.out                      # Best eq., RMSE = 22.44 K, MaxAE = 100.77 K
│       │   ├── SIS_subspaces/
│       │   │   ├── Uspace.expressions         # Top 200 SIS features (to be added)
│       │   │   └── Uspace.dat                 # Numerical feature matrix (to be added)
│       │   └── Models/
│       │       ├── top0100_D001               # Actual vs. predicted (to be added)
│       │       ├── top0100_D001_coeff         # Coefficients for top 100 models (to be added)
│       │       └── data_top1/
│       │           └── desc_D001.dat          # Descriptor values, best model (to be added)
│       ├── Debye_temperature/                 # Reference run
│       │   ├── SISSO.out
│       │   ├── SIS_subspaces/
│       │   └── Models/
│       ├── Specific_heat_at_constant_pressure/
│       │   ├── SISSO.out
│       │   ├── SIS_subspaces/
│       │   └── Models/
│       └── Thermal_conductivity/
│           ├── SISSO.out
│           ├── SIS_subspaces/
│           └── Models/
│
├── SISSO_post_processing/
│   ├── codes/
│   │   ├── SISSO_postprocessing.ipynb
│   │   ├── SISSO_postprocessing_input_data.xlsx  # 3 property sheets
│   │   ├── symbol_conversion.txt
│   │   ├── requirements.txt
│   │   └── README.md
│   └── results/
│       ├── Debye_temp_MP/                    # From Debye_temperature_phonopy run
│       │   ├── Debye_temp_MP_prediction.pdf
│       │   └── Debye_temp_MP_results.xlsx
│       ├── Debye_temp_AFLOW/
│       │   ├── Debye_temp_AFLOW_predictions.pdf
│       │   └── Debye_temp_AFLOW_results.xlsx
│       ├── Specific_heat/
│       │   ├── Cp_300K_AFLOW_prediction_plot.pdf
│       │   └── Cp_300K_AFLOW_results.xlsx
│       └── Lattice_therm_cond/
│           ├── Lattice_therm_cod_300K_AFLOW_predictions.pdf
│           └── Lattice_therm_cond_300K_AFLOW_results.xlsx
│
└── SISSO_material_class_performance/
    ├── codes/
    │   ├── material_classifier.py
    │   ├── example_notebook.ipynb
    │   ├── SISSO_material_classifier_input.xlsx
    │   ├── requirements.txt
    │   ├── environment.yml
    │   ├── run_hpc.sh
    │   └── README.md
    └── results/
        ├── Debye_temp_MP_classified_materials.xlsx     # Mixed DT source (phonopy + elastic)
        ├── Debye_temp_AFLOW_classified_materials.xlsx
        ├── Cp_300K_AFLOW_classified_materials.xlsx
        └── Lattice_thermal_conductivity_300K_AFLOW_classified_materials.xlsx
```

---

## SISSO Results Summary

### Best Equations (from `SISSO.out`)

| Property | Folder | Descriptor | c₁ | c₀ | RMSE† | MaxAE† |
|---|---|---|---|---|---|---|
| Θ_D (MP, phonopy+elastic) ★ | `Debye_temperature_phonopy` | `((SM+YM)/cbrt(VPA))/sqrt(YM×D)` | 149.743 | −6.478 | 22.44 | 100.77 |
| Θ_D (MP, elastic only) | `Debye_temperature` | `((SM+YM)/cbrt(VPA))/sqrt(YM×D)` | 150.081 | −0.762 | 1.72‡ | 23.19‡ |
| C_p (AFLOW) | `Specific_heat_at_constant_pressure` | `(NA×PR×exp(PUGR))×cbrt(sqrt(VPA))` | 3.761 | 0.143 | 2.37‡ | 36.67‡ |
| κ (AFLOW) | `Thermal_conductivity` | `cbrt(SM×NA)/((NA/SM)×sqrt(D))` | 0.279 | −0.344 | 2.36‡ | 41.31‡ |

> †RMSE and MaxAE from `SISSO.out` are in standardised training-space units for all runs except Θ_D phonopy, which uses original units (K).  
> ‡Standardised units — see post-processing results below for original-unit metrics.

### Post-Processing Results (original units, with conformal prediction)

| Property | Dataset | N | R² | RMSE | MAE | Max Error | Coverage |
|---|---|---|---|---|---|---|---|
| Θ_D ★ | MP (phonopy+elastic) | 6,276 | 0.9825 | 23.12 K | 10.04 K | 97.20 K (Al₂O₃) | 95.0% |
| Θ_D | AFLOW | 5,077 | 0.9938 | 14.00 K | 10.21 K | 49.86 K (Eu₂F₈Mg₂) | 95.1% |
| C_p | AFLOW | 5,077 | 0.9902 | 2.37 J/K·cell | 1.10 J/K·cell | 36.70 J/K·cell (Li₄₀Pb₁₂) | 95.1% |
| κ | AFLOW | 5,077 | 0.9456 | 2.36 W/m·K | 1.27 W/m·K | 41.35 W/m·K (N₄) | 95.1% |

★ = manuscript result

### Material Class Distribution — MP Θ_D (6,276 compounds, phonopy + elastic DT)

| Class | Count | Share |
|---|---|---|
| Transition Metal | 2,020 | 32.2% |
| Lanthanoid/Actinoid | 1,304 | 20.8% |
| Other | 771 | 12.3% |
| Oxide | 665 | 10.6% |
| Halide | 462 | 7.4% |
| Nitride | 294 | 4.7% |
| Boride | 234 | 3.7% |
| Carbide | 214 | 3.4% |

---

## Getting Started

### Prerequisites

- **SISSO v3.5**: Fortran compiler (gfortran ≥ 9 or ifort), LAPACK, OpenMP (optional)
- **Post-processing**: Python 3.12+, packages in `SISSO_post_processing/codes/requirements.txt`
- **Classifier**: Python 3.9+, packages in `SISSO_material_class_performance/codes/requirements.txt`

### Installation

```bash
# 1. Clone this repo
git clone https://github.com/Shaswat-qm-researcher/pisr-phonon-genesis.git

# 2. Build SISSO v3.5
git clone https://github.com/rouyang2017/SISSO.git
cd SISSO/src && make
cd ../..

# 3. Install post-processing dependencies
pip install -r SISSO_post_processing/codes/requirements.txt

# 4. Install classifier dependencies
pip install -r SISSO_material_class_performance/codes/requirements.txt
# or via conda:
conda env create -f SISSO_material_class_performance/codes/environment.yml
conda activate sisso_classifier
```

---

## Usage

### 1. Running SISSO

```bash
# Navigate to the target property input directory
# For the manuscript MP Θ_D run:
cd "SISSO_model_config/config and data - SISSO INPUT/Debye_temperature_phonopy"

# Copy or symlink the SISSO executable
cp /path/to/SISSO/SISSO .

# Run — SISSO writes output to SISSO.out automatically
./SISSO
```

**Key `SISSO.in` parameters (shared across all runs):**

| Parameter | Value | Meaning |
|---|---|---|
| `ptype` | 1 | Regression |
| `desc_dim` | 1 | 1-D descriptor |
| `rung` | 3 | Feature-space tier (depth of expression tree) |
| `fcomplexity` | 7 | Max operators per feature |
| `nf_sis` | 200 | SIS-selected subspace size |
| `ops` | `(+)(-)(*)(/)(exp)(exp-)(^-1)(^2)(^3)(sqrt)(cbrt)(\|-\|)(^6)(sin)(cos)` | Operator set |
| `method_so` | `L0` | Sparse regression method |
| `metric` | `RMSE` | Model selection metric |
| `nmodels` | 200 | Top models saved |

For the full parameter reference see the [SISSO guide](https://github.com/rouyang2017/SISSO).

### 2. Post-Processing

```bash
cd SISSO_post_processing/codes
jupyter notebook SISSO_postprocessing.ipynb
```

The notebook guides you through selecting the input data, entering the SISSO equation and coefficients from `SISSO.out`, validating on sample rows, and generating a parity plot (PDF) and results workbook (Excel).

### 3. Material Classifier

```bash
# Interactive
cd SISSO_material_class_performance/codes
python material_classifier.py

# Non-interactive / HPC batch
python material_classifier.py \
    --input  SISSO_material_classifier_input.xlsx \
    --output ../results \
    --column formula \
    --actual DT --predicted DT_SISSO \
    --prefix Debye_temp_MP

# HPC (SLURM)
sbatch run_hpc.sh
```

---

## Input File Formats

### `train.dat`

Space-separated, no header line, no missing values. First column: sample identifier. Second column: target property. Remaining columns: input descriptors.

| Property | Folder | Sample ID | Features (`nsf`) | Feature columns |
|---|---|---|---|---|
| Θ_D — MP ★ | `Debye_temperature_phonopy` | `material_id` (mp-xxxx) | 4 | `SM`, `YM`, `D`, `VPA` |
| Θ_D — MP (ref.) | `Debye_temperature` | formula | 4 | `SM`, `YM`, `VPA`, `D` |
| C_p — AFLOW | `Specific_heat_at_constant_pressure` | formula | 5 | `NA`, `PR`, `PUGR`, `SM`, `VPA` |
| κ — AFLOW | `Thermal_conductivity` | formula | 5 | `SM`, `YM`, `NA`, `NE`, `D` |

> **Note on column order:** SISSO assigns units by column position via `funit`. The two Θ_D runs have the same four features but in different orders (`SM YM D VPA` vs `SM YM VPA D`), resulting in different unit groupings. Always verify `funit` against the column order in `train.dat` before running.

### Post-processing input (`SISSO_postprocessing_input_data.xlsx`)

One sheet per property. Must contain a formula/ID column, the target property column, and the descriptor columns used in the SISSO equation. Available sheets:

| Sheet name | Target | Descriptor columns | DT source |
|---|---|---|---|
| `Debye_temperature` | `DT` | `SM`, `YM`, `D`, `VPA` | Mixed (phonopy + elastic) |
| `Cp (300 K)` | `Cp_300` | `NA`, `PR`, `PUGR`, `SM`, `VPA` | — |
| `thermal_conductivity (300 K)` | `TC_300` | `SM`, `YM`, `NA`, `NE`, `D` | — |

### Equation syntax (post-processing notebook)

```python
# Θ_D — MP (phonopy + elastic):
c0 + c1*((SM+YM)/VPA**(1/3)/((YM*D)**0.5))
# c0 = -6.478,  c1 = 149.743

# Θ_D — AFLOW:
c0 + c1*((SM+YM)/VPA**(1/3)/((YM*D)**0.5))
# c0 = -0.762,  c1 = 150.081

# C_p — AFLOW:
c0 + c1*(NA*PR*exp(PUGR)*VPA**(1/6))
# c0 = 0.143,   c1 = 3.761

# κ — AFLOW:
c0 + c1*(SM**(4/3)*NA**(-2/3)*D**(-0.5))
# c0 = -0.344,  c1 = 0.279
```

Supported functions: `exp`, `sqrt`, `cbrt`, `log`, `log10`, `abs`, `sin`, `cos`, `tan`. Use `**` for exponentiation — `^` is **not** supported.

---

## Output Files

### SISSO outputs (`model and equation - SISSO OUTPUT/<property>/`)

| File | Contents |
|---|---|
| `SISSO.out` | Best descriptor expression, c₀, c₁, RMSE, MaxAE |
| `SIS_subspaces/Uspace.expressions` | Top 200 SIS-selected features with SIS scores |
| `SIS_subspaces/Uspace.dat` | Numerical values of those 200 features |
| `Models/top0100_D001` | Actual vs. predicted for top 100 1-D models |
| `Models/top0100_D001_coeff` | Coefficients for those 100 models |
| `Models/data_top1/desc_D001.dat` | Descriptor values for the best model |

> For `Debye_temperature_phonopy`, only `SISSO.out`, `SISSO.in`, and `train.dat` are currently committed. The `SIS_subspaces/` and `Models/` files will be added once available.

### Post-processing outputs (`SISSO_post_processing/results/<property>/`)

| File | Contents |
|---|---|
| `*_prediction.pdf` | Parity plot with R², RMSE, MAE, MaxError, and conformal bands |
| `*_results.xlsx` — Predictions sheet | All input columns + `SISSO_Prediction`, `Absolute_Error`, `Relative_Error_%`, `Conformal_Lower_Bound`, `Conformal_Upper_Bound`, `Inside_Conformal_Interval` |
| `*_results.xlsx` — Summary sheet | Property, equation, N, R², RMSE, MAE, MaxError (with formula), conformal q, coverage |

### Classifier outputs (`SISSO_material_class_performance/results/`)

Each `*_classified_materials.xlsx` contains four sheets:

| Sheet | Contents |
|---|---|
| `Classified_Data` | All original columns + `Class` column |
| `Summary_Class` | Count and percentage share per material class |
| `Perf_by_Class` | MAE, RMSE, MaxError, R² per class |
| `Perf_by_CrystalSystem` | Same metrics per crystal system |

---

## Troubleshooting

### SISSO

| Symptom | Fix |
|---|---|
| Linker error (LAPACK not found) | `export LDFLAGS="-llapack -lblas"` before `make` |
| Feature count mismatch | Verify `nsf` in `SISSO.in` equals the descriptor column count in `train.dat` (exclude sample ID and target) |
| Wrong `funit` grouping | `funit=(1:2)(3:3)(4:4)` means features 1–2 share units, feature 3 has its own, feature 4 has its own. Verify this matches your column order |
| `SISSO.out` is empty | Check the executable has run permission: `chmod +x SISSO` |
| `restart=1` hangs | Delete the `CONTINUE` file and set `restart=0` to start fresh |

### Post-processing notebook

| Symptom | Fix |
|---|---|
| Equation validation fails | Column names in the equation must match Excel column headers exactly (case-sensitive) |
| `KeyError` on column selection | Confirm the correct sheet is active; column names differ across property sheets |
| `Division by zero` or `NaN` | Check for zero or negative values in denominator / log / sqrt arguments |
| Plot labels show raw column names | Verify column names are listed in `symbol_conversion.txt` |

### Material classifier

| Symptom | Fix |
|---|---|
| `ModuleNotFoundError: openpyxl` | `pip install openpyxl` |
| `Cannot auto-detect formula column` | Add `--column <name>` flag or enter the column name at the interactive prompt |
| Unknown element warnings | Non-standard symbol in formula; token is skipped and compound may be classed `Unknown` |

---

## Citation

**This work:**
```bibtex
@article{
}
```

**SISSO method** (cite if using SISSO):
```bibtex
@article{ouyang2018sisso,
  title   = {SISSO: A compressed-sensing method for identifying the best
             low-dimensional descriptor in an immensity of offered candidates},
  author  = {Ouyang, Runhai and Curtarolo, Stefano and Ahmetcik, Emre and
             Scheffler, Matthias and Ghiringhelli, Luca M.},
  journal = {Physical Review Materials},
  volume  = {2},
  number  = {8},
  pages   = {083802},
  year    = {2018}
}
```

---

## Authors and Contact

**Shaswat Pathak**, **Vardhman Dwivedi**, **Albert Linda**, and **Somnath Bhowmick**

- **Email**: shaswatpathak.qm.researcher@gmail.com, bsomnath@iitk.ac.in
- **Institution**: Indian Institute of Technology Kanpur, Uttar Pradesh, 208016, India

---

## License

MIT License — see LICENSE file for details.

---

## Acknowledgments

- **[SISSO](https://github.com/rouyang2017/SISSO)**: Ouyang, R. et al. (2018). Physical Review Materials, 2(8), 083802.
- **[Materials Project](https://materialsproject.org)**: DFT-computed materials database.
- **[AFLOW Consortium](https://aflow.org)**: High-throughput materials data.

**Last Updated**: 29-10-2026
