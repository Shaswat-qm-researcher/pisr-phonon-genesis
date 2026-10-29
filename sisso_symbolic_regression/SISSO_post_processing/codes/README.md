# SISSO Post-Processing Tool

A Jupyter notebook for evaluating SISSO prediction equations on material property datasets, generating publication-quality parity plots, and exporting comprehensive results with conformal prediction intervals.

---

## Overview

This tool provides an interactive, step-by-step workflow to:
- Load material property data from Excel or CSV files
- Input a SISSO-derived equation with its fitted coefficients (copied from `SISSO.out`)
- Compute predictions and standard regression metrics (R², RMSE, MAE, MaxError)
- Compute **conformal prediction intervals** (distribution-free, guaranteed coverage)
- Generate a parity plot (PDF) with metric annotations and conformal bands
- Export a two-sheet Excel workbook: full predictions + summary statistics

---

## Requirements

### Python version
Python 3.12 or higher

### Dependencies

```bash
pip install -r requirements.txt
```

```
pandas==2.2.3
numpy==1.26.4
matplotlib==3.9.2
scikit-learn==1.5.2
colorama==0.4.6
openpyxl            # latest
scipy>=1.11.0
jupyter>=1.0.0
```

---

## Input Files

### Required: `SISSO_postprocessing_input_data.xlsx`

One sheet per property. Each sheet must contain a formula/ID column, the target property column, and the descriptor columns used in the SISSO equation.

**Available sheets:**

| Sheet name | Target column | Descriptor columns | DT source (MP only) |
|---|---|---|---|
| `Debye_temperature` | `DT` | `SM`, `YM`, `D`, `VPA` | Mixed: phonopy (1,394) + elastic (4,882) |
| `Cp (300 K)` | `Cp_300` | `NA`, `PR`, `PUGR`, `SM`, `VPA` | — |
| `thermal_conductivity (300 K)` | `TC_300` | `SM`, `YM`, `NA`, `NE`, `D` | — |

> The `Debye_temperature` sheet corresponds to the **manuscript run** (`Debye_temperature_phonopy` SISSO input folder), which uses a mixed Debye temperature dataset combining PDOS phonon calculations and elastic-constant-derived values from the Materials Project.

### Optional: `symbol_conversion.txt`

Maps column header names to LaTeX symbols for axis labels. If not provided, raw column names are used on plots.

### Required for equation: `SISSO.out`

Copy the best equation and its coefficients from the appropriate `SISSO.out` file in `SISSO_model_config/model and equation - SISSO OUTPUT/<property>/`.

---

## Usage

```bash
cd SISSO_post_processing/codes
jupyter notebook SISSO_postprocessing.ipynb
```

### Interactive workflow

#### Step 1 — Data loading
- Enter the directory containing the Excel file
- Select the file from the auto-detected list
- Choose the target property sheet

#### Step 2 — Column selection
- Select the formula/ID column
- Select the target property column
- Select descriptor columns (comma-separated indices from the displayed list)

#### Step 3 — Symbol file (optional)
- Enter the path to `symbol_conversion.txt`, or press Enter to skip

#### Step 4 — SISSO equation input

Enter coefficient values when prompted (`c0`, `c1`, ...), then type the equation:

```python
# Θ_D — MP (Debye_temperature_phonopy, MANUSCRIPT):
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

**Supported operators and functions:**

| Category | Syntax |
|---|---|
| Arithmetic | `+`, `-`, `*`, `/` |
| Powers | `**` (not `^`) |
| Functions | `exp()`, `sqrt()`, `cbrt()`, `log()`, `log10()`, `abs()`, `sin()`, `cos()`, `tan()` |
| Grouping | `()` |

#### Step 5 — Equation validation
The notebook tests the equation on 3 representative rows. Review the computed values and confirm before the full run.

#### Step 6 — Output configuration
- Enter the output directory (created automatically if absent)
- Enter a filename prefix (e.g. `Debye_temp_MP`)

---

## Output Files

### 1. Parity plot — `<prefix>_prediction.pdf`

Publication-ready scatter plot (600 DPI) showing:
- Actual vs. predicted values (crimson circles, black edges)
- Perfect prediction line (black dashed)
- Conformal prediction band (shaded at chosen coverage level)
- Maximum-error point highlighted (blue ✕ marker)
- Annotation box with R², RMSE, MAE, MaxError, and conformal coverage

### 2. Results workbook — `<prefix>_results.xlsx`

**Sheet 1: Predictions**

| Column | Description |
|---|---|
| *(all input columns)* | Preserved as-is |
| `SISSO_Prediction` | Model-predicted value |
| `Absolute_Error` | \|Actual − Predicted\| |
| `Relative_Error_%` | 100 × \|Actual − Predicted\| / \|Actual\| |
| `Conformal_Lower_Bound` | Lower bound of prediction interval |
| `Conformal_Upper_Bound` | Upper bound of prediction interval |
| `Inside_Conformal_Interval` | True / False |

**Sheet 2: Summary**

| Row | Content |
|---|---|
| Property | Target column name |
| Equation | Full SISSO expression as entered |
| N | Number of data points |
| R² | Coefficient of determination |
| RMSE | Root mean square error (original units) |
| MAE | Mean absolute error (original units) |
| Max Error | Largest absolute error |
| Max Error Formula | Chemical formula of the worst-predicted compound |
| Conformal q | Quantile used for the prediction intervals |
| Coverage | Empirical fraction of samples inside the conformal interval |

---

## Results Summary

| Property | Dataset | N | R² | RMSE | MAE | Max Error | Coverage |
|---|---|---|---|---|---|---|---|
| Θ_D ★ | MP (phonopy + elastic) | 6,276 | 0.9825 | 23.12 K | 10.04 K | 97.20 K (Al₂O₃) | 95.0% |
| Θ_D | AFLOW | 5,077 | 0.9938 | 14.00 K | 10.21 K | 49.86 K (Eu₂F₈Mg₂) | 95.1% |
| C_p | AFLOW | 5,077 | 0.9902 | 2.37 J/K·cell | 1.10 J/K·cell | 36.70 J/K·cell (Li₄₀Pb₁₂) | 95.1% |
| κ | AFLOW | 5,077 | 0.9456 | 2.36 W/m·K | 1.27 W/m·K | 41.35 W/m·K (N₄) | 95.1% |

★ = manuscript result

---

## Best Practices

**Data preparation:**
- Ensure consistent units across all descriptor columns
- Verify descriptor column names match the column headers in the Excel sheet exactly (case-sensitive)
- For the Debye temperature sheet, the column order is `SM, YM, D, VPA` — this differs from the AFLOW Θ_D run

**Equation input:**
- Always use `**` for exponentiation, not `^`
- Include explicit `*` for multiplication (`c1*SM`, not `c1 SM`)
- Use the 3-row validation step to catch typos before the full run

---

## Troubleshooting

| Issue | Solution |
|---|---|
| Equation validation fails | Column names must match Excel headers exactly (case-sensitive) |
| `KeyError` on column selection | Confirm the correct sheet is active; names differ across sheets |
| `File not found` | Verify file path and extension (`.xlsx`, `.xls`, or `.csv`) |
| `Division by zero` or `NaN` | Check for zero or negative values in denominator / log / sqrt arguments |
| Plot labels show raw column names | Verify column names are listed in `symbol_conversion.txt` |
| Conformal interval is very wide | Reflects genuine prediction uncertainty; check for outliers or data-quality issues |

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

**[SISSO Method](https://github.com/rouyang2017/SISSO)**: Ouyang, R. et al. (2018). SISSO: a compressed-sensing method for identifying the best low-dimensional descriptor in an immensity of offered candidates. *Physical Review Materials*, 2(8), 083802.
