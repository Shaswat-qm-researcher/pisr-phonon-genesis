# Material Compound Classifier

> **Version 2.1** — Compatible with PC · HPC (SLURM/PBS) · Jupyter Notebook

A tool that reads a spreadsheet of chemical formulae and SISSO predictions, appends a `Class` column identifying each compound's material family, and outputs per-class and per-crystal-system performance metrics.

Output is one Excel workbook with four sheets: classified data, class summary, performance by class, and performance by crystal system.

---

## Table of Contents

1. [Material classes](#material-classes)
2. [Quick start](#quick-start)
3. [Installation](#installation)
4. [Usage](#usage)
5. [Output structure](#output-structure)
6. [Results summary](#results-summary)
7. [Supported input formats](#supported-input-formats)
8. [Troubleshooting](#troubleshooting)

---

## Material Classes

| Class | Rule |
|---|---|
| `Carbide` | Compound of a metal/metalloid + carbon |
| `Boride` | Compound of a metal/metalloid + boron |
| `Nitride` | Compound of a metal/metalloid + nitrogen |
| `Oxide` | Any compound containing oxygen |
| `Halide` | Any compound containing a halogen (F, Cl, Br, I, At, Ts) |
| `Transition Metal` | All elements are transition metals (or metalloids) |
| `Alkaline Earth` | All elements are alkaline-earth metals (or metalloids) |
| `Alkali` | All elements are alkali metals (or metalloids) |
| `Post-Transition` | All elements are post-transition metals (or metalloids) |
| `Lanthanoid/Actinoid` | All elements are lanthanoids/actinoids (or metalloids) |
| `Element` | Pure single-element entry |
| `Other` | Does not fit any category above |
| `Unknown` | Formula could not be parsed |

When a compound contains metals from several sub-groups, the **first** group in the priority list (Lanthanoid/Actinoid → Transition → Post-Transition → Alkaline Earth → Alkali) wins.

---

## Quick Start

```bash
pip install -r requirements.txt

# Interactive
python material_classifier.py

# Non-interactive / HPC
python material_classifier.py \
    --input  SISSO_material_classifier_input.xlsx \
    --output ../results \
    --column formula \
    --actual DT --predicted DT_SISSO \
    --prefix Debye_temp_MP
```

---

## Installation

### pip

```bash
pip install -r requirements.txt
```

### conda

```bash
conda env create -f environment.yml
conda activate sisso_classifier
```

### HPC modules

```bash
module load python/3.11
python -m venv ~/.venvs/sisso_classifier
source ~/.venvs/sisso_classifier/bin/activate
pip install -r requirements.txt
```

---

## Usage

### Interactive terminal

```bash
python material_classifier.py
```

Steps:
1. Enter the folder containing the data file.
2. Select the file by number.
3. **Select the sheet** — all available sheets are listed for Excel files. Press Enter to accept sheet 1, or type the sheet number.
4. Enter the output folder (created automatically if it does not exist).
5. Optionally enter the actual and predicted column names for per-class performance metrics.
6. Optionally enter a filename prefix.

### Non-interactive / HPC batch

```bash
python material_classifier.py \
    --input     /scratch/user/data.xlsx \
    --output    /scratch/user/results   \
    --column    formula                 \
    --sheet     "Sheet1"                \
    --prefix    hpc_run                 \
    --actual    DT                      \
    --predicted DT_SISSO
```

| Flag | Description |
|---|---|
| `--input` | Path to the input file |
| `--output` | Output root directory |
| `--column` | Formula/species column name (auto-detected if omitted) |
| `--sheet` | Excel sheet name (first sheet if omitted) |
| `--prefix` | Prefix for the output filename |
| `--actual` | Column with true target values (enables performance analysis) |
| `--predicted` | Column with SISSO-predicted values (enables performance analysis) |

A ready-to-submit SLURM script is at `run_hpc.sh` — edit the paths at the top and submit with `sbatch run_hpc.sh`.

### Jupyter Notebook

```python
from material_classifier import run_notebook

df = run_notebook(
    input_path  = "SISSO_material_classifier_input.xlsx",
    output_dir  = "../results",
    formula_col = "formula",
    sheet       = "Sheet1",
    actual_col  = "DT",
    pred_col    = "DT_SISSO",
    prefix      = "Debye_temp_MP",
)
df.head()
```

A worked example is in `example_notebook.ipynb`.

---

## Output Structure

```
<output_dir>/
└── SISSO_material_classification/
    └── [prefix_]classified_materials.xlsx
        ├── Classified_Data        ← all original columns + 'Class'
        ├── Summary_Class          ← count and share (%) per class
        ├── Perf_by_Class          ← MAE / RMSE / MaxError / R² per class
        └── Perf_by_CrystalSystem  ← same metrics per crystal system
```

`Perf_by_Class` and `Perf_by_CrystalSystem` are written only when both `--actual` and `--predicted` are provided. A `Low_N_Flag` warning marks classes with fewer than 10 samples.

---

## Results Summary

> The MP Θ_D classifier results (`Debye_temp_MP_classified_materials.xlsx`) use the **manuscript dataset**: 6,276 compounds with Debye temperatures from a mix of PDOS phonon calculations (1,394 compounds, `PDOS_phonopy`) and elastic-constant-derived values (4,882 compounds, `sound_velocity_elastic`). This corresponds to the `Debye_temperature_phonopy` SISSO run.

### Θ_D — MP dataset (6,276 compounds, phonopy + elastic)

**Class distribution:**

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

**Performance by class:**

| Class | N | MAE (K) | RMSE (K) | R² |
|---|---|---|---|---|
| ALL | 6,276 | 10.34 | 23.36 | 0.9821 |
| Transition Metal | 2,020 | 10.24 | 22.67 | 0.9716 |
| Lanthanoid/Actinoid | 1,304 | 8.70 | 21.37 | 0.9425 |
| Oxide | 665 | 11.42 | 24.68 | 0.9771 |
| Boride | 234 | 5.10 | 15.40 | 0.9965 |
| Carbide | 214 | 3.19 | 8.85 | 0.9987 |
| Halide | 462 | 10.69 | 23.74 | 0.9510 |

**Performance by crystal system:**

| Crystal System | N | MAE (K) | RMSE (K) | R² |
|---|---|---|---|---|
| ALL | 6,276 | 10.34 | 23.36 | 0.9821 |
| Cubic | 2,333 | 10.95 | 23.82 | 0.9761 |
| Tetragonal | 1,247 | 9.08 | 21.88 | 0.9780 |
| Orthorhombic | 966 | 7.34 | 18.37 | 0.9922 |
| Hexagonal | 884 | 12.34 | 26.68 | 0.9809 |

### Θ_D — AFLOW dataset (4,206 compounds, AFLOW-only subset)

**Performance by class:**

| Class | N | MAE (K) | RMSE (K) | R² |
|---|---|---|---|---|
| ALL | 4,206 | 10.11 | 14.09 | 0.9939 |
| Transition Metal | 1,294 | 8.51 | 11.36 | 0.9913 |
| Lanthanoid/Actinoid | 917 | 6.17 | 8.67 | 0.9925 |
| Oxide | 431 | 13.97 | 18.28 | 0.9855 |
| Halide | 176 | 16.39 | 20.86 | 0.9729 |

### C_p — AFLOW dataset (5,077 compounds)

**Performance by class:**

| Class | N | MAE (J/K·cell) | RMSE (J/K·cell) | R² |
|---|---|---|---|---|
| ALL | 5,077 | 8.21 | 12.29 | 0.7351 |
| Transition Metal | 1,654 | 7.19 | 10.65 | 0.8034 |
| Halide | 221 | 4.69 | 6.72 | 0.8688 |
| Post-Transition | 139 | 5.22 | 7.82 | 0.9261 |
| Oxide | 463 | 12.66 | 15.47 | 0.4992 |

### κ — AFLOW dataset (5,077 compounds)

**Performance by class:**

| Class | N | MAE (W/m·K) | RMSE (W/m·K) | R² |
|---|---|---|---|---|
| ALL | 5,077 | 1.27 | 2.36 | 0.9456 |
| Lanthanoid/Actinoid | 1,085 | 0.69 | 1.06 | 0.8894 |
| Halide | 221 | 0.60 | 0.93 | 0.7391 |
| Carbide | 248 | 2.99 | 4.12 | 0.9474 |
| Element | 75 | 3.99 | 7.17 | 0.8962 |

---

## Supported Input Formats

| Extension | Notes |
|---|---|
| `.xlsx` | Sheet selector shown after file selection |
| `.xls` | Legacy format; requires `xlrd` |
| `.csv` | UTF-8 encoding assumed |

The formula column is auto-detected when its name is `species`, `formula`, or `composition` (case-insensitive). Any other name must be passed via `--column` or the interactive prompt.

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| `ModuleNotFoundError: openpyxl` | `pip install openpyxl` |
| `ModuleNotFoundError: xlrd` | `pip install xlrd` (needed for `.xls` only) |
| `Cannot auto-detect formula column` | Add `--column <name>` to the command |
| `Perf_by_Class` sheet missing | Both `--actual` and `--predicted` must be provided and present in the sheet |
| Unknown element warnings | Non-standard symbol in formula; token is skipped; compound may be classed `Unknown` |
| Colors not showing in HPC log | Colors are disabled automatically when output is redirected to a file |

---

## Authors and Contact

**Shaswat Pathak**, **Vardhman Dwivedi**, **Albert Linda**, and **Somnath Bhowmick**

- **Email**: shaswatpathak.qm.researcher@gmail.com, bsomnath@iitk.ac.in
- **Institution**: Indian Institute of Technology Kanpur, Uttar Pradesh, 208016, India

---

## License

MIT License — see LICENSE file for details.
