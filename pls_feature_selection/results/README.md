# Results - PLS Feature Selection Output

This folder contains all output files from PLS regression feature selection analyses, including Excel reports and figures.

---

## Folder Structure

```
results/
│
├── excel_data_files/
│   ├── Cp_300K_AFLOW_results.xlsx
│   ├── Debye_temperature_MP_results.xlsx
│   └── thermal_conductivity_300K_AFLOW_results.xlsx
│
└── figures/
    ├── Debye_temperature/
    │   ├── Debye_temperature_MP_1_pls_component_analysis.pdf
    │   ├── Debye_temperature_MP_2_loading_heatmap.pdf
    │   ├── Debye_temperature_MP_3_feature_contributions.pdf
    │   ├── Debye_temperature_MP_4_nlr_relative_gain.pdf
    │   └── Debye_temperature_MP_5_foldwise_selection_frequency.pdf
    ├── Specific_heat_at_constant_pressure/
    └── Thermal_conductivity/
```

---

## Analysis Summary

| Property | File | Dataset | CV R² | CV RMSE | PLS-screened | NLR-retained | Stability (50 runs) |
|----------|------|---------|-------|---------|--------------|--------------|---------------------|
| Θ_D | `Debye_temperature_MP_results.xlsx` | MP | 0.8241 | 77.68 K | 14 | 4 (SM, YM, VPA, D) | 50/50 (100%) |
| C_p | `Cp_300K_AFLOW_results.xlsx` | AFLOW | 0.9828 | 3.05 J/K·cell | 15 | 5 (NA, PR, PUGR, VPA, SM) | 30/50 (60%) |
| κ | `thermal_conductivity_300K_AFLOW_results.xlsx` | AFLOW | 0.6920 | 5.60 W/m·K | 13 | 3 (SM, YM, NA) | 45/50 (90%) |

---

## Excel File Structure

Each Excel file contains **8 sheets** with comprehensive analysis results:

---

### Sheet 1: Metadata_and_Grid_Search

Two sections in one sheet: analysis configuration at the top, followed by the full grid search cross-validation results table below.

**Metadata section:**

| Parameter | Description |
|-----------|-------------|
| `Output Variable` | Target property name |
| `Num Components` | Number of PLS components used |
| `Components tuned by CV` | Whether n_components was optimised by CV |
| `Loading Threshold` | Min \|loading\| for feature retention |
| `Delta R2 Threshold` | Min ΔR² for component significance |
| `NLR Relative-gain Threshold` | Min fraction of remaining unexplained variance a feature must remove to be retained |
| `NLR Absolute Delta R2 Floor` | Noise guard: gains smaller than this are ignored regardless of relative gain |
| `Num Selected Features` | Count of PLS-screened features |
| `Num NLR-retained Features` | Count of features surviving nested linear regression |
| `Best CV R2 Score` | Cross-validated R² |
| `Best CV RMSE (orig units)` | Cross-validated RMSE in original units |
| `In-sample RMSE (orig units)` | Training RMSE in original units |
| `Fold-wise check: folds` | K-fold splits per repeat |
| `Fold-wise check: repeats` | Number of full K-fold repetitions |
| `GridSearch max_iter` | Optimal max iterations from grid search |
| `GridSearch tol` | Optimal convergence tolerance from grid search |

**Grid Search CV Results table** (appended below metadata):

Includes all parameter combinations tested, with columns for `rank_test_RMSE`, `mean_test_RMSE`, `std_test_RMSE`, `mean_test_R2`, `std_test_R2`, `mean_train_RMSE`, `mean_train_R2`, overfitting gap metrics (`overfit_gap_R2`, `overfit_gap_RMSE`), and fit/score timing. The best-performing row is highlighted in green.

---

### Sheet 2: PLS Component Summary

Component-wise performance and selection status.

| Column | Description |
|--------|-------------|
| `PLS Component` | Component identifier (PLS1, PLS2, ...) |
| `Incremental R2` | ΔR² contribution of each component |
| `Normalized Covariance` | Normalised \|covariance\| with target property |
| `Selected Component` | Whether this component passed the ΔR² threshold (Yes/No) |

**Example (Θ_D — MP):**
```
PLS Component | Incremental R2 | Normalized Covariance | Selected Component
PLS1          | 0.7265         | 1.0000                | Yes
PLS2          | 0.0732         | 0.1928                | Yes
PLS3          | 0.0596         | 0.1517                | Yes
PLS4          | 0.0066         | 0.0244                | No
PLS5          | 0.0015         | 0.0000                | No
```

---

### Sheet 3: PLS Loadings (All)

Complete loading matrix for **all** PLS components.

- Rows: Input features
- Columns: `Feature` + all PLS components (PLS1, PLS2, ...)
- Values: Loading weights (approximately −1 to +1)

---

### Sheet 4: PLS Loadings (Selected)

Loading matrix restricted to **selected components only** (those passing the ΔR² threshold). This matches exactly what is shown in Plot 2.

- Rows: Input features
- Columns: `Feature` + selected PLS components only
- Values: Loading weights (approximately −1 to +1)

---

### Sheet 5: NLR Feature Selection

PLS-ranked features with cumulative performance from the nested linear regression (NLR) step.

| Column | Description |
|--------|-------------|
| `PLS Rank` | Feature importance ranking by PLS loading magnitude (1 = most important) |
| `Feature Name` | Descriptor name |
| `NLR Cumulative R2` | R² with features 1 through current rank |
| `NLR Delta R2` | Incremental R² contribution of this feature |
| `NLR Relative Gain` | ΔR² / (1 − R²_previous): fraction of remaining error removed |
| `Retained` | Yes if relative gain ≥ threshold and ΔR² ≥ floor; No otherwise |

**Example (Θ_D — MP):**
```
PLS Rank | Feature | NLR Cum. R² | NLR ΔR²  | Rel. Gain | Retained
1        | SM      | 0.6325      | 0.6325   | 0.633     | Yes
2        | YM      | 0.6769      | 0.0444   | 0.121     | Yes
3        | BM      | 0.6781      | 0.0012   | 0.004     | No
4        | VPA     | 0.7433      | 0.0652   | 0.202     | Yes
5        | PR      | 0.7495      | 0.0063   | 0.024     | No
...
8        | D       | 0.8769      | 0.1267   | 0.507     | Yes
```

---

### Sheet 6: Foldwise Selection Freq

Per-feature selection frequencies across all fold-wise runs.

| Column | Description |
|--------|-------------|
| `Feature` | Descriptor name |
| `PLS-screened frequency` | Fraction of runs in which this feature passed the loading screen |
| `NLR-retained frequency` | Fraction of runs in which this feature was NLR-retained |
| `PLS-screened (n of runs)` | Absolute count (out of 50) |
| `NLR-retained (n of runs)` | Absolute count (out of 50) |
| `Mean PLS rank (when screened)` | Average PLS rank across runs where the feature appeared |
| `In full-data retained set` | Whether this feature is in the full-data NLR-retained set |

---

### Sheet 7: Foldwise Runs

One row per fold-repeat run, recording the complete selection outcome for that training fold.

| Column | Description |
|--------|-------------|
| `Repeat` | Repeat index (1 to n_repeats) |
| `Fold` | Fold index within that repeat |
| `N train` / `N test` | Training and test set sizes |
| `Selected PLS components` | Components passing ΔR² screen in this fold |
| `PLS-screened features` | Features passing the loading threshold |
| `NLR-retained features` | Features surviving NLR in this fold |
| `N retained` | Count of NLR-retained features |
| `Held-out R2 (retained set)` | R² on the held-out fold using only the retained features |
| `Held-out RMSE (retained set)` | RMSE on the held-out fold |

---

### Sheet 8: Foldwise Summary

Aggregate stability statistics across all fold-wise runs.

| Quantity | Θ_D (MP) | C_p (AFLOW) | κ (AFLOW) |
|----------|-----------|-------------|-----------|
| Total fold-wise runs | 50 | 50 | 50 |
| Full-data NLR-retained set | SM, YM, VPA, D | NA, PR, PUGR, VPA, SM | SM, YM, NA |
| Runs retaining exactly that set | 50 | 30 | 45 |
| Exact-match fraction | 1.00 (100%) | 0.60 (60%) | 0.90 (90%) |
| Held-out R² — mean | 0.8678 | 0.9834 | 0.7011 |
| Held-out R² — std | 0.0137 | 0.0033 | 0.0308 |
| Held-out R² — min | 0.8407 | 0.9757 | 0.6494 |
| Held-out R² — max | 0.9061 | 0.9902 | 0.7756 |

---

## Figure Files

Each property folder contains **5 high-resolution PDF plots** (600 DPI). `*` = user-defined file prefix.

---

### Plot 1: PLS Component Analysis
`*_1_pls_component_analysis.pdf`

**Shows:**
- Bar chart of incremental R² per component (left y-axis, red)
- Bar chart of normalised |covariance| with the target (right y-axis, blue)
- Components selected by the ΔR² threshold are marked with ★ and bolded on the x-axis

**Interpretation:**
- High incremental R²: Component captures significant variance in the target
- High covariance: Strong linear relationship with the target
- ★ markers indicate which components were used for feature selection

**Example (Θ_D — MP):** PLS1★, PLS2★, PLS3★ pass the 0.05 threshold (ΔR² = 0.73, 0.07, 0.06); PLS4 and PLS5 do not.

---

### Plot 2: Loading Heatmap
`*_2_loading_heatmap.pdf`

**Shows:**
- Heatmap of PLS loadings for **selected components only**
- Features (rows) × selected components (columns)
- Colour scale: Red (positive) → White (zero) → Blue (negative), seismic colormap
- Numerical loading values overlaid on each cell
- Subtitle states how many components are shown vs. total

**Interpretation:**
- |Loading| > threshold: Feature significantly contributes to that component
- Sign indicates the direction of the relationship with the target
- Full loadings for all components are available in Sheet 3

**Example (Θ_D — MP):** 3 of 5 components shown. G_VRH (0.52), E (0.52), B_VRH (0.43) have the largest PLS1 loadings; ρ (0.72) dominates PLS2.

---

### Plot 3: Feature Contributions (NLR)
`*_3_feature_contributions.pdf`

**Shows:**
- Line plot: Cumulative R² vs. number of features added in PLS rank order (left y-axis)
- Scatter points: Colour-coded by cumulative R² value (jet colormap)
- Bar chart: ΔR² for each feature addition (right y-axis, grey)
- Legend (left of plot): Sequential feature addition order with LaTeX symbols

**Interpretation:**
- Steep initial rise: First few features capture most variance
- Plateau: Additional features contribute marginally
- Large ΔR² bars highlight the most informative features

---

### Plot 4: NLR Relative-Gain Waterfall
`*_4_nlr_relative_gain.pdf`

**Shows:**
- Horizontal bar for each feature (in PLS rank order) showing its NLR relative gain: ΔR² / (1 − R²_previous)
- A vertical dashed line at the retention threshold (default 0.05)
- Features to the right of the line are retained; features to the left are not

**Interpretation:**
- Relative gain works uniformly regardless of how much variance is already explained: a gain of 0.20 means "this feature removes 20% of the remaining prediction error"
- The threshold line makes the retain/drop decision visually transparent

---

### Plot 5: Fold-wise Selection Frequency
`*_5_foldwise_selection_frequency.pdf`

**Shows:**
- Grouped bar chart: one pair of bars per descriptor, sorted by PLS-screened frequency
- Red bars: fraction of runs in which the feature passed the loading screen (PLS-screened)
- Blue bars: fraction of runs in which the feature was NLR-retained
- Title states total runs (folds × repeats)

**Interpretation:**
- A feature with both bars at 1.0 is consistently selected across all data splits — high-confidence indicator
- A gap between red and blue bars means the feature clears the loading screen but rarely survives NLR — low marginal gain
- Features with low red-bar frequency are sensitive to the specific data split

**Example (Θ_D — MP):** V_atom, ρ, G_VRH, E are all PLS-screened and NLR-retained at frequency 1.0 across all 50 runs, confirming these four descriptors as the stable, parsimonious predictor set for Θ_D.

---

## Reproducing Results

### Step 1: Verify Input Data
```bash
ls ../data/processed/*_cleaned_dataset.csv
# Expected: AFLOW_cleaned_dataset.csv, MP_cleaned_dataset.csv
```

### Step 2: Run Analysis
```bash
jupyter notebook ../code_and_config/PLS_analysis.ipynb

# Follow prompts:
# - Enter directory path containing the input CSV/Excel file
# - Select file from auto-detected list
# - Paste input column names and output column name
# - Confirm symbol_conversion.txt usage
# - Set parameters (defaults match values reported here)
# - Enter results directory and file prefix
```

### Step 3: Compare Outputs
```bash
# Excel files should match:
# - Same CV R² and RMSE values (within 0.001)
# - Same NLR-retained feature set
# - Same or very similar fold-wise stability fraction
```

---

## Notes

1. **Reproducibility**: Minor variations (<0.001 in R²) may occur due to random state in cross-validation. The fold-wise stability fraction can vary slightly across runs.
2. **Units**: All RMSE values are in the original physical units of the target property (K for Θ_D, J/K·cell for C_p, W/m·K for κ).
3. **LaTeX Symbols**: Feature names in figures use LaTeX formatting as defined in `symbol_conversion.txt`. See `pls_parameters.json` for the full symbol mapping.
4. **NLR retention**: A feature is retained if its relative gain ≥ 0.05 AND its absolute ΔR² ≥ 0.001. Both criteria must be satisfied.
