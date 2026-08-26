# SISSO Symbolic Regression and Post-processing

A comprehensive workflow repository for material property prediction using SISSO (Sure Independence Screening and Sparsifying Operator) with post-processing tools for analysis and visualization.

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![SISSO](https://img.shields.io/badge/SISSO-symbolic_regression-green.svg)](https://github.com/rouyang2017/SISSO)

## Overview

This repository contains:
- **SISSO input files** for various material properties
- **SISSO output** files with model predictions and performance metrics
- **Post-processing tools** for evaluating and visualizing SISSO results
- **Prediction results** for reproducing the results

> **Note:** This is a sub-repository of the main project:  
> **[pisr-phonon-genesis](https://github.com/Shaswat-qm-researcher/pisr-phonon-genesis/)**

---
## Properties Analyzed

| Property | Symbol | Name in data file| Condition |
|---|---|---|---|
| Debye Temperature | $\Theta_D$ | DT | — |
| Specific Heat (constant pressure) | $C_p\ (300\ K)$ | Cp_300 | 300 K |
| Lattice Thermal Conductivity | $\kappa\ (300\ K)$ | TC | 300 K |

---
## Repository Structure


```
sisso_symbolic_regression/
├── config and data - SISSO INPUT/
│   ├── Debye_temperature/          # SISSO.in, train.dat
│   ├── Specific_heat.../           # SISSO.in, train.dat
│   └── Thermal_conductivity/       # SISSO.in, train.dat
├── model and equation - SISSO OUTPUT/
│   └── <property>/
│       ├── SIS_subspaces/          # Uspace.dat, Uspace.expressions
│       └── Models/data_top1/       # Predictions + coefficients
├── SISSO_post_processing_code/
│   ├── SISSO_postprocessing.ipynb
│   ├── SISSO_post_processing_input_data.xlsx
│   ├── requirements.txt
|   ├── README.md
│   └── symbol_conversion.txt
└── postprocessing results/
    └── <property>/                 # Parity plots (.pdf) + results (.xlsx)
```

---

## Getting Started


### 1. Prerequisites

- **SISSO**: Fortran compiler (gfortran/ifort), LAPACK, OpenMP (optional, for parallel execution)
- **Post-processing**: Python 3.12+, packages in `requirements.txt`, `symbol_conversion.txt` for LaTeX labels

### 2. Installation

```bash
# 1. Clone this repo
git clone https://github.com/yourusername/sisso_symbolic_regression.git

# 2. Install SISSO (see https://github.com/rouyang2017/SISSO)
git clone https://github.com/rouyang2017/SISSO.git && cd SISSO/src && make

# 3. Install Python dependencies for post-processing
pip install -r requirements.txt
```

## 3. Usage

#### Running SISSO
1. Navigate to the input directory for your target property:
```bash
cd "config and data - SISSO INPUT/Debye_temperature"
```

2. Copy or link the SISSO executable:
```bash
cp /path/to/SISSO/SISSO .
```

3. Run SISSO:
```bash
./SISSO > SISSO.in
```

4. Check the output files for results.

**For detailed SISSO usage, parameters, and methodology, refer to:**
- Official repository: https://github.com/rouyang2017/SISSO
- Original paper: Ouyang, R. et al. (2018). *Physical Review Materials*, 2(8), 083802.
#### Post-Processing

```bash
cd SISSO_post_processing_code
jupyter notebook SISSO_postprocessing.ipynb
```

The notebook guides you through loading data, inputting the SISSO equation and coefficients, generating parity plots, and exporting results to Excel.

---
## Input File Format

#### SISSO
1. `train.dat` --- Space-separated, no header, no missing values. Each row is one material sample.

```
sample_id/material_name  target_property  feature1  feature2  feature3  ...
1/Al2O3                      523.45         2.99      400.5     8.21
2/SiO2                       645.12         2.65      450.2     7.85
```
2. `SISSO.in` --- Configuration file controlaling SISSO execution parameters:

| Key Parameter | Description |
|---|---|
| `ptype=1` | Property type (1 $\rightarrow$ Regression,  2 $\rightarrow$ Classification) |
| `ntask=int` | Number of tasks (typically 1 for single property prediction) |
|`desc_dim=int` | Descriptor dimension (1  $\rightarrow$ scalar, 2  $\rightarrow$ vector, 3  $\rightarrow$ matrix) |
| `nsample=int` | Number of rows in `train.dat` |
| `nfeat=int` | Number of input feature columns in `train.dat`, do not count **sample_id** and **target_property** |
| `rung=int` | Feature space depth [1–3 typical] (complexity of symbolic expressions) |
| `maxcomplexity=int` | Max operators per feature [1–7 typical] |
| `subs_sis=int` | SIS-selected subspace size [100–200 typical] |
| `ops='(+)(-)...'` | Operators: `(+)(-)(*)(/)(^2)(sqrt)(cbrt)(log)...` |
| `method='L0'` | Sparse regression method---LASSO |
| `nm_output=int` | Number of top models to save |
|`metric=char`| Model selection metric (RMSE, MaxAE, or combinations) |

#### Post-Processing

1. `data_file.xlsx/ data_file.csv` --- Must contain ID/formula coloum, target property, PLS slected input descriptors.
2. `symbol_conversion.txt` --- LaTeX symbol mapping info for plot labels.
3. `SISSO.out` -- Get SISSO equation with fitted coefficiect from the file and enter them when asked while running the code.

**Supported Equation Syntax**
```python
Enter value of c0
Enter value of c1
Enter value of c2 etc. 

**Enter equation:**
c0 + c1*Parameter1**2
c0 + c1*exp(Parameter1) + c2*sqrt(Parameter2)
c0 + c1*log(Parameter1) + c2*(Parameter1/Parameter2)**2
```
Supported functions: `exp`, `sqrt`, `cbrt`, `log`, `log10`, `abs`, `sin`, `cos`, `tan`.


---

## Output Files

#### SISSO

| File | Contents |
|---|---|
| `SISSO.out` | Best descriptor equation, RMSE, MaxAE |
| `SIS_subspaces/Uspace.expressions` | Top SIS-selected symbolic features |
| `SIS_subspaces/Uspace.dat` | Numerical feature values matrix |
| `Models/data_top1/top0100_D001` | Actual vs. predicted for all samples |
| `Models/data_top1/top0100_D001_coeff` | Coefficients for top 100 models |

**Example descriptor** from `SISSO.out`:
```
y = c0 + c1 × (((SM + YM) / cbrt(VPA)) / sqrt(YM × D))
    c1 = 150.08,  c0 = −0.757,  RMSE = 1.72
```
#### Post-Processing

For each property:
- **Parity plot** (.pdf): actual vs. predicted with R², RMSE, MAE, and max-error annotation
- **Results spreadsheet** (.xlsx): full predictions, errors, and summary statistics

---
## Example Workflow

1. **Prepare training data** with material properties and descriptors
2. **Configure SISSO.in** with desired complexity and validation settings
3. **Run SISSO** to identify optimal symbolic equations
4. **Extract coefficients** from SISSO output
5. **Use post-processing tool** to:
   - Validate equations on test data
   - Generate publication plots
   - Export comprehensive results
---
## Troubleshooting

#### SISSO Execution Issues
- Ensure LAPACK is properly linked
- Check input file format (no extra spaces, correct data types)
- Verify feature count matches between SISSO.in and train.dat

#### Post-Processing Issues
- Verify Python package versions match requirements
- Check Excel file format and column names
- Ensure parameter names match exactly between equation and Excel columns

For more detailed troubleshooting, see the post-processing README or open an issue on GitHub.

---
## Citation

If you use this repository, for the post-processing tools in your research, please cite:

**This Work:**
```bibtex
@article{
}
```
---
## Authors and Contact

**Shaswat Pathak**, **Vardhman Dwivedi**, **Albert Linda**, and  **Somnath Bhowmick**

For questions, issues, or collaboration:
- **Email**: shaswatpathak.qm.researcher@gmail.com, bsomnath@iitk.ac.in
- **Institution:** Indian Institute of Technology Kanpur, Uttar Pradesh, 208016, India

---
## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## Acknowledgments

**[SISSO Method](https://github.com/rouyang2017/SISSO)**: Ouyang, R. et al. (2018). SISSO: a compressed-sensing method for identifying the best low-dimensional descriptor in an immensity of offered candidates. Physical Review Materials, 2(8), 083802.  
**Note: Cite this paper if usign SISSO model in your research.**

---
