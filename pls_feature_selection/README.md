# PLS Regression Based Feature Selection for Thermodynamic and Transport Property Prediction

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## Overview

This repository provides a complete Partial Least Squares Regression (PLS) framework (a Physics-Informed Machine Learning Framework) for identifying the most influential physical descriptors for predicting thermodynamic and transport properties of crystalline materials from latent machine learned space, including:

- **Debye Temperature ($Θ_D$)**: Maximum phonon frequency cutoff
- **Heat Capacity ($C_p$)**: Thermal energy storage at 300K
- **Thermal Conductivity ($\kappa$)**: Phonon-mediated heat transport at 300K

---

> **Note:** This is a sub-repository of the main project:  
> **[pisr-phonon-genesis](https://github.com/Shaswat-qm-researcher/pisr-phonon-genesis/)**

---

## Project Workflow

<p align="center">
  <img src="https://github.com/Shaswat-qm-researcher/pisr-phonon-genesis/blob/main/pls_feature_selection/pls_worflow.png"
       alt="PLS Workflow"
       width="95%">
</p>

## Repository Structure

```
plsr_feature_selection/
│
├── data/                                   # Input datasets
│   ├── MP_cleaned_dataset.csv              # Materials Project: 6,433 compounds, 22 features
│   ├── AFLOW_cleaned_dataset.csv           # AFLOW: 5,154 compounds, 29 features
│   ├── feature_descriptions.json           # Feature metadata & descriptions
│   └── README.md                           # Data documentation
│
├── code_and_config/                        # Analysis scripts & configuration
│   ├── PLS_analysis.ipynb                  # Main Jupyter notebook
│   ├── pls_parameters.json                 # Configuration parameters
│   ├── setup_environment.py                # Environment setup script
│   ├── requirements.txt                    # Python dependencies
│   └── README.md                           # Code documentation
│
├── results/                                # Output results
│   ├── excel_data_files/                   # 8-sheet Excel reports per property
│   ├── figures/                            # 5 PDF plots per property
│   └── README.md                           # Results documentation
│
└── README.md                               # This file
```

---

## Quick Start

### Setup

```bash
# Install dependencies
pip install -r code_and_config/requirements.txt

# Setup environment (for Jupyter support)
python code_and_config/setup_environment.py

# Run analysis
jupyter notebook code_and_config/PLS_analysis.ipynb
```

---

## Input Datasets

| Dataset | Source | Compounds | Features | Primary Targets |
|---------|--------|-----------|----------|-----------------|
| `MP_cleaned_dataset.csv` | Materials Project | 6,433 | 22 | `DT` |
| `AFLOW_cleaned_dataset.csv` | AFLOW Consortium | 5,154 | 29 | `DT_AGL`, `Cp_300`, `TC_300` |

> ⚠️ Always drop `MP_ID` / `auid`, `formula`, and `debye_temperature_source` before training — these are string identifiers with no numerical meaning and will cause errors in scikit-learn.

### Key Database Differences

| Feature | Materials Project | AFLOW | Notes |
|---------|-------------------|-------|-------|
| ID Column | `MP_ID` | `auid` | Both must be dropped |
| Formula | `formula` | `formula` | Both must be dropped |
| Debye Temp. | `DT` | `DT_AGL` | Primary target |
| Fermi Energy | `EFMR` | ❌ | MP-only |
| Magnetization | `TM` | `ASPIN` | Different conventions |
| Magnetic Sites | `MSITE` | ❌ | MP-only |
| Cell Volume | `V` | ❌ | MP-only (derivable as VPA × NA) |
| Anisotropy | ❌ | `ANI` | AFLOW-only |
| Grüneisen γ | ❌ | `gruneisen` | AFLOW-only; critical for κ and α |
| Heat Cap. (C_v) | ❌ | `Cv_300` | AFLOW-only |
| Heat Cap. (C_p) | ❌ | `Cp_300` | Secondary target — AFLOW-only |
| Thermal Exp. | ❌ | `TEX_300` | AFLOW-only |
| Thermal Cond. | ❌ | `TC_300` | Secondary target — AFLOW-only |
| Vib. Free Energy | ❌ | `VIB_FE_300` | AFLOW-only |
| Vib. Entropy | ❌ | `VIB_EN_300` | AFLOW-only |

---

## Key Features

### 1. Feature Selection Algorithm
- PLSR-based dimensionality reduction with component screening (ΔR² > 0.05)
- Automatic loading threshold filtering (|L| > 0.10)
- Nested linear regression (NLR) to identify the minimal retained feature set: a feature is kept only if it removes ≥ 5% of the remaining unexplained variance (relative gain ≥ 0.05) **and** contributes an absolute ΔR² ≥ 0.001

### 2. Hyperparameter Optimisation
- GridSearchCV with 5-fold cross-validation
- Optimises: `max_iter` [500, 800, 1000, 2000], `tol` [1e-8, 1e-6, 1e-4]
- Primary scoring metric: RMSE; secondary: R²

### 3. Fold-wise Selection Stability Check
- The full selection pipeline (scaling → PLS → component screening → loading screening → NLR) is repeated inside each training fold
- Default: 5-fold × 10 repeats = 50 runs
- Reports per-feature PLS-screened and NLR-retained frequencies and the fraction of runs that recover exactly the full-data retained set

### 4. Multi-Property Support
Can be configured for any numerical target variable in the input dataset, not only the properties demonstrated in this work.

---

## Configuration

### Default Parameters

Configuration file: `code_and_config/pls_parameters.json`

```json
{
  "n_components": 5,
  "loading_threshold": 0.10,
  "incremental_r2_threshold": 0.05,
  "nlr_relative_gain_threshold": 0.05,
  "nlr_delta_r2_floor": 0.001,
  "cv_folds": 5,
  "folds": 5,
  "repeats": 10,
  "max_iter": [500, 800, 1000, 2000],
  "tol": [1e-8, 1e-6, 1e-4]
}
```

### Parameter Reference

| Parameter | Default | Range | Effect |
|-----------|---------|-------|--------|
| `n_components` | 5 | 2–20 | Higher = more variance captured, risk of overfitting |
| `loading_threshold` | 0.10 | 0.05–0.30 | Higher = fewer, more important features after PLS screen |
| `incremental_r2_threshold` | 0.05 | 0.01–0.15 | Higher = fewer PLS components retained |
| `nlr_relative_gain_threshold` | 0.05 | 0.02–0.50 | Fraction of remaining error a feature must remove to be retained by NLR |
| `nlr_delta_r2_floor` | 0.001 | 0.0005–0.005 | Noise guard: absolute ΔR² gains below this are ignored |
| `folds` | 5 | 3–10 | K-fold splits per repeat in the stability check |
| `repeats` | 10 | 5–20 | Repetitions of K-fold (total runs = folds × repeats) |

---

## Results Summary

| Property | Dataset | CV R² | CV RMSE | NLR-retained Features | Stability |
|----------|---------|-------|---------|----------------------|-----------|
| Θ_D | MP | 0.8241 | 77.68 K | SM, YM, VPA, D | 50/50 (100%) |
| C_p | AFLOW | 0.9828 | 3.05 J/K·cell | NA, PR, PUGR, VPA, SM | 30/50 (60%) |
| κ | AFLOW | 0.6920 | 5.60 W/m·K | SM, YM, NA | 45/50 (90%) |

---

## Documentation

- **[data/README.md](data/README.md)**: Dataset descriptions, feature definitions, database comparison
- **[code_and_config/README.md](code_and_config/README.md)**: Notebook workflow, parameters, output files
- **[results/README.md](results/README.md)**: Excel sheet structure, plot descriptions, per-property results

---

## Citation

If you use this code in your research, please cite:

```bibtex
@article{
}
```

---



## Contact & Support

For questions, issues, or collaboration:
- **Email**: shaswatpathak.qm.researcher@gmail.com and bsomnath@iitk.ac.in
- **Institution**: Indian Institute of Technology Kanpur, Kanpur, Uttar Pradesh, 208016, India

---

## License

MIT License — see LICENSE file for details.

---

## Acknowledgments

- **[Materials Project](https://materialsproject.org)** for DFT-computed materials database
- **[AFLOW Consortium](https://aflow.org)** for high-throughput materials data
- **[scikit-learn](https://scikit-learn.org/stable/modules/generated/sklearn.cross_decomposition.PLSRegression.html)** team for PLS implementation

**Last Updated**: 29-10-2026
