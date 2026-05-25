# python\_postprocessing\_codes

[← Main README](../README.md) · [ab\_initio\_calculations\_results →](../ab_initio_calculations_results/README.md)

Python scripts for reproducing all post-processing figures from the ab initio data.

---

## Table of Contents

1. [Scripts Overview](#1-scripts-overview)
2. [Installation](#2-installation)
3. [Script 1 — Phonon Dispersion Plot](#3-phonon-dispersion-plot)
4. [Script 2 — Cv Comparison](#4-cv-comparison)
5. [Workflow Summary](#5-workflow-summary)
6. [Troubleshooting](#7-troubleshooting)

---

## 1. Scripts Overview

| File | Purpose | Outputs |
|---|---|---|
| [`install.py`](./install.py) | Installs and verifies all Python dependencies | Console pass/fail summary |
| [`FORCE_CONT_PHONON_DISPERSION.py`](./FORCE_CONT_PHONON_DISPERSION.py) | Phonon band structure + atom-projected DOS | `.pdf`, `.png` |
| [`cv_comparison_plot_phonopy_vs_SISSO.py`](./cv_comparison_plot_phonopy_vs_SISSO.py) | $C_v$ vs $T$: Phonopy data vs SISSO Debye vs Fitted Debye Integral | `.pdf`, `.tiff`, `.xlsx` |
| [`requirements.txt`](./requirements.txt) | Pinned dependency list for `install.py` | — |

---

## 2. Installation

```bash
python install.py
```

Upgrades pip, installs all packages from `requirements.txt`, imports each package, and prints a pass/fail summary. Requires **Python 3.9+**.

## 3. Phonon Dispersion Plot

**File:** [`FORCE_CONT_PHONON_DISPERSION.py`](./FORCE_CONT_PHONON_DISPERSION.py)

Reads force constants and a k-path definition, computes phonon frequencies along the Brillouin zone path using Phonopy, and plot phonon band structure with an optional atom-projected DOS panel.

#### Required Input Files

All files must be in the **same directory**.

| File | Required | Description |
|---|---|---|
| [`POSCAR`](.) | Yes | Unit cell used for Phonopy dynamics |
| [`PRIMCELL.vasp`](.) | Yes | Primitive cell; chemical formula and species extracted from here |
| [`FORCE_CONSTANTS`](.) | Yes | Interatomic force constants in Phonopy format |
| [`KPATH.phonopy`](.) | Yes | Brillouin zone path definition (see §3.2) |
| [`projected_dos.dat`](.) | Optional | Atom-projected DOS; DOS panel is omitted if absent |

#### Usage

```bash
python FORCE_CONT_PHONON_DISPERSION.py
# Prompts:
#   Input directory  [cwd]:    <path/to/Step2_phonopy_output>
#   Output directory [input]:  <path/to/Step3_postprocessing_results>
```

#### Outputs
 `phonon_dispersion_<Formula>.pdf/png` - Resulting phonon dispersion curves and projected density of states.

---

## 4. Cv Comparison

**File:** [`cv_comparison_plot_phonopy_vs_SISSO.py`](./cv_comparison_plot_phonopy_vs_SISSO.py)

Loads Phonopy/DFPT $C_v(T)$ data, fits a Debye model via non-linear least squares, and overlays the SISSO-predicted Debye model and the classical Dulong–Petit limit.

**Debye model fitted:**

$$C_v = 9N_AR\left(\frac{T}{\theta_D}\right)^3 \int_0^{\theta_D/T} \frac{x^4 e^x}{(e^x-1)^2}\,dx$$

where *$N_A$* = atoms per formula unit (read from `thermal_properties.yaml`) and *$R$* = 8.314 J mol⁻¹ K⁻¹.

#### Required Input Files

| File | Required | Description |
|---|---|---|
| [`PRIMCELL.vasp`](.) | Yes | Primitive cell; chemical formula extracted from here |
| [`thermal_properties`](.) | Yes | Phonopy YAML output containing $C_v$, $S$, $E$, $F$ vs $T$ |

#### Usage

```bash
python cv_comparison_plot_phonopy_vs_SISSO.py
# Prompts:
#   SISSO Debye temperature θ_D [K]:           <value from predicted_structures_material_properties.xlsx>
#   Figure width — 1 = single-col (89 mm) [default], 2 = double-col (183 mm):
#   Input directory  [cwd]:
#   Output directory [input]:
```

The SISSO $\Theta_D$ value for each compound is in column **"Debye temperature SISSO (K)"** of [`predicted_structures_material_properties.xlsx`](../predicted_structures_material_properties.xlsx).

#### Computed and Reported Values

| Quantity | Description |
|---|---|
| $\Theta_D$ (fitted) $\pm \sigma$ | Debye temperature from curve fit with standard error |
| R² | Goodness of fit over the 5–1000 K range |
| Δ$\Theta_D$ | Difference between fitted and SISSO Debye temperatures |
| 3nR | Dulong–Petit limit (classical high-temperature asymptote) |

#### Outputs

`Cv_comparison_<Formula>.pdf/tiff`

`Cv_comparison_<Formula>_source_data.xlsx`

**Source data workbook sheets:**

| Sheet | Contents |
|---|---|
| `Phonopy_Data` | Raw $C_v(T)$ from Phonopy YAML |
| `Model_Curves` | Smooth Debye model curves (600 points, 1–1000 K) |
| `Fit_Summary` | $\Theta_D$ fitted, $\Theta_D$ SISSO, $\Delta \Theta_D$, $R^2$, Dulong–Petit limit |

---

## 5. Workflow Summary

Both scripts are run from a compound's `Step2` output directory. Figures and data are written to `Step3`.

```
Step2_phonopy_output/             ← run scripts from here
├── POSCAR
├── PRIMCELL.vasp
├── FORCE_CONSTANTS
├── KPATH.phonopy
├── projected_dos.dat
└── thermal_properties

        ↓   python FORCE_CONT_PHONON_DISPERSION.py
        ↓   python cv_comparison_plot_phonopy_vs_SISSO.py

Step3_postprocessing_results/     ← outputs written here
├── phonon_dispersion_<Formula>.pdf
├── Cv_comparison_<Formula>.pdf
└── Cv_comparison_<Formula>_source_data.xlsx
```
---
## 6. Troubleshooting

| Error / Warning | Cause | Fix |
|---|---|---|
| `VASP4 format` error | `PRIMCELL.vasp` lacks species names on line 6 | Re-export from VESTA or Phonopy using `--pa AUTO` to produce VASP5 format |
| `natom` missing in YAML | Older Phonopy versions omit this field | Script falls back to atom count from `PRIMCELL.vasp`; verify the primitive cell matches the supercell |
| Imaginary modes warning | Frequencies below −0.5 THz detected | May indicate structural instability or insufficient VASP k-point / energy cutoff convergence |
| TIFF export fails | Pillow not installed | Run `pip install Pillow` |
| Curve fit does not converge | Initial guess `p0 = [500]` too far from true θ\_D | Edit `p0` in the script to a value closer to the expected Debye temperature |
