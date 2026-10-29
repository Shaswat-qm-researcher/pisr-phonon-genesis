# Code and Configuration

This folder contains all analysis scripts, configuration files, and environment setup tools for the PLS feature selection framework.

---

## Contents

### 1. PLS_analysis.ipynb

Main analysis notebook for complete PLS feature selection workflow.

**Workflow Steps:**

1. **Data Loading**: Scan a directory and load a selected CSV/Excel file
2. **Column Selection**: Choose input features and target property interactively
3. **Symbol Configuration** *(Step 1B)*: Optionally load `symbol_conversion.txt` for LaTeX labels
4. **Parameter Setup**: Set PLS and NLR parameters interactively
5. **Results Directory**: Choose output folder and file prefix
6. **PLS Analysis**: GridSearchCV optimisation → fit best PLS model → component screening
7. **Feature Selection** *(Step 5)*: Rank features by loadings; apply nested linear regression (NLR) to identify the retained set
8. **Fold-wise Stability Check** *(Step 6B)*: Repeat the full pipeline inside each training fold (folds × repeats) to validate selection consistency
9. **Visualisation** *(Step 7)*: Generate 5 publication-quality plots
10. **Export** *(Step 8)*: Save 8-sheet Excel workbook to the results directory

**Usage:**

```bash
# Standard Jupyter
jupyter notebook PLS_analysis.ipynb

# JupyterLab
jupyter lab PLS_analysis.ipynb

# VS Code
# Open in VS Code and select kernel
```

**Interactive Prompts:**

- **Directory path**: Folder containing the input CSV/Excel file
- **File selection**: Choose from auto-detected supported files (`.csv`, `.xls`, `.xlsx`)
- **Input columns**: Features for PLS (comma-separated, copy-paste from displayed list)
- **Output column**: Target property (e.g. `DT`, `Cp_300`, `TC_300`)
- **Symbol file**: Whether to load `symbol_conversion.txt` for LaTeX axis labels
- **PLS parameters**: `loading_threshold`, `incremental_r2_threshold`, `n_components`, CV tuning toggle
- **NLR parameters**: `nlr_relative_gain_threshold`, `nlr_delta_r2_floor`
- **Fold-wise check**: Number of folds and repeats for stability validation
- **Save path**: Output directory for results
- **File prefix**: Prefix for all saved files (e.g. `Debye_temperature_MP`)

---

**Output files** (using prefix `<prefix>`):

| File | Description |
|------|-------------|
| `<prefix>_1_pls_component_analysis.pdf` | Incremental R² per PLS component |
| `<prefix>_2_loading_heatmap.pdf` | Loading heatmap (selected components only) |
| `<prefix>_3_feature_contributions.pdf` | Feature contribution bar chart |
| `<prefix>_4_nlr_relative_gain.pdf` | NLR relative-gain waterfall |
| `<prefix>_5_foldwise_selection_frequency.pdf` | Fold-wise PLS-screened and NLR-retained frequencies |
| `<prefix>_results.xlsx` | Excel workbook with 8 sheets (see below) |

**Excel sheets:**

| Sheet | Contents |
|-------|----------|
| Metadata and Grid search | Run metadata + GridSearchCV results (best row highlighted) |
| PLS Component Summary | Incremental R², normalised covariance, component selection flag |
| PLS Loadings (All) | Loadings for all `n_components` |
| PLS Loadings (Selected) | Loadings for components passing the incremental R² screen |
| NLR Feature Selection | PLS-ranked features with cumulative R², ΔR², relative gain, and retained flag |
| Foldwise Selection Freq | Per-feature PLS-screened and NLR-retained frequencies across all folds |
| Foldwise Runs | One row per fold-repeat run |
| Foldwise Summary | Aggregate stability statistics (exact-match fraction, held-out R² stats) |

---

### 2. pls_parameters.json

Configuration file containing all default parameters and property-specific configurations.

**Key Sections:**

1. Default Parameters
2. GridSearch Parameters
3. Property-Specific Configs
4. Feature Symbols Mapping (LaTeX)

---

### 3. setup_environment.py

Universal environment setup script that automatically configures a Python environment for Jupyter notebook execution across all platforms.

**Supported Platforms:**

- Google Colab
- Jupyter Notebook/Lab
- Anaconda Navigator
- Visual Studio Code
- PyCharm
- Command Line/Terminal

**Features:**

- Auto-detects current environment
- Installs required packages
- Sets up Jupyter kernels
- Provides platform-specific instructions

**Usage:**

```bash
python setup_environment.py
```

**Setup Options:**

1. Create Conda environment (recommended for Anaconda users)
2. Create Virtual environment (venv)
3. Install in current environment
4. Show VS Code setup instructions

**Example Output:**

```bash
Choose setup option:
  1. Create Conda environment
  2. Create Virtual environment (venv)
  3. Install in current environment
  4. Show VS Code setup instructions
  5. Exit

Enter choice (1-5): 1

Creating conda environment 'plsr_env'...
✓ Success

Installing packages...
✓ numpy==2.0.1
✓ pandas==2.2.3
...
✓ All packages installed!

To activate:
  conda activate plsr_env
  jupyter notebook
```

---

## Configuration Guide

### PLS Parameters

| Parameter | Default | Range | Effect |
|-----------|---------|-------|--------|
| `n_components` | 5 | 2–20 | Number of PLS components to extract |
| `loading_threshold` | 0.10 | 0.05–0.30 | Min \|L\| for feature retention |
| `incremental_r2_threshold` | 0.05 | 0.01–0.15 | Min ΔR² for component significance |

### NLR Parameters

| Parameter | Default | Range | Effect |
|-----------|---------|-------|--------|
| `nlr_relative_gain_threshold` | 0.05 | 0.10–0.50 | Feature retained if it removes ≥ this fraction of remaining unexplained variance — works uniformly whether R² is 0.5 or 0.99 |
| `nlr_delta_r2_floor` | 0.001 | 0.0005–0.005 | Noise guard: gains smaller than this are ignored regardless of relative gain |

### GridSearch Parameters

| Parameter | Values | Description |
|-----------|--------|-------------|
| `max_iter` | [500, 800, 1000, 2000] | NIPALS algorithm iterations |
| `tol` | [1e-8, 1e-6, 1e-4] | Convergence tolerance |
| `cv_folds` | 5 | Cross-validation folds |

### Fold-wise Stability Check

| Parameter | Default | Description |
|-----------|---------|-------------|
| `folds` | 5 | K-fold splits per repeat |
| `repeats` | 10 | Number of full K-fold repetitions (total runs = folds × repeats) |

---

## Workflow Integration

<p align="center">
  <img src="https://raw.githubusercontent.com/Shaswat-qm-researcher/pisr-phonon-genesis/main/pls_feature_selection/code_and_config/pls_setup.png"
       alt="PLS Setup"
       width="95%">
</p>

---

## Required Packages

```txt
numpy==2.0.1
pandas==2.2.3
scipy==1.14.1
scikit-learn==1.5.2
matplotlib==3.9.2
openpyxl==3.1.2
jupyter
jupyterlab
notebook
ipykernel
```

---

## Troubleshooting

### Issue: Jupyter kernel not found

**Solution:**
```bash
python -m ipykernel install --user --name plsr_env
```

### Issue: Import errors in notebook

**Solution:**
```bash
# Restart kernel after installing packages
# Kernel → Restart
```

### Issue: Convergence warnings during GridSearch

**Solution:** Increase `max_iter` in `pls_parameters.json`:
```json
"max_iter": { "values": [2000, 5000] }
```

### Issue: VS Code cannot find environment

**Solution:**
1. Open Command Palette (`Ctrl+Shift+P`)
2. Select "Python: Select Interpreter"
3. Choose the `plsr_env` interpreter

---
