# ab\_initio\_calculations\_results

[← Main README](../README.md) · [python\_postprocessing\_codes →](../python_postporcessing_codes/README.md)

First-principles calculation files for all 26 predicted compounds. Each compound folder follows a consistent three-module layout: 
- OQMD source structures 
- DFT elastic data 
- Phonopy/DFPT phonon calculations.

---

## Table of Contents

1. [Folder Structure](#1-folder-structure)
2. [Compound Folders](#2-compound-folders)
3. [Internal Layout — Phonopy Compounds](#3-internal-layout--phonopy-compounds)
4. [Internal Layout — DFPT Compound](#4-internal-layout--dfpt-compound-beb12n2-triclinic)
5. [Key Files Reference](#5-key-files-reference)

---

## 1. Folder Structure

```
ab_initio_calculations_results/
│
├── 📄 psudo_potentials_details.xlsx
│
├── 📁 B13CN/
├── 📁 Be17V2/
├── 📁 Be3Cr2B/
├── 📁 Be7Cr4B/
├── 📁 BeB12N2 (Triclinic)/          ← DFPT method
├── 📁 BeB12N2 (Trigonal)/
├── 📁 BeB2/
├── 📁 BeV3N/
├── 📁 Cr2N/
├── 📁 Cr23C6/
├── 📁 CrN2/
├── 📁 Li4BeN2/
├── 📁 Li4C3/
├── 📁 LiB15/
├── 📁 LiBeB/
├── 📁 Mn2Be/
├── 📁 Mn2BeB2/
├── 📁 Mn8CN3/
├── 📁 MnBe2/
├── 📁 Si3N4/
├── 📁 Ti3C2N/
├── 📁 Ti6Be23/
├── 📁 Ti6C4N/
├── 📁 Ti6C5/
├── 📁 TiBeC/
└── 📁 V8CN3/
```

| File / Folder | Description |
|---|---|
| [`psudo_potentials_details.xlsx`](./psudo_potentials_details.xlsx) | PAW pseudopotential versions used for each element across all calculations |
| `<Formula>/` | Self-contained calculation folder for each compound (see §3–4) |

---

## 2. Compound Folders

Each compound folder contains up to three subfolders:

| Subfolder | Present in | Description |
|---|---|---|
| `oqmd_structures/` | All compounds | Original POSCAR and INCAR retrieved from OQMD |
| `DFT_elastic_data/` | All compounds | VASP inputs/output for elastic constant calculation |
| `phonopy_calculations/` | 25 compounds | Phonopy finite-displacement phonon workflow |
| `DFPT_Phonopy_calculations/` | BeB₁₂N₂ (Triclinic) only | DFPT-based phonon workflow |

---

## 3. Internal Layout — Phonopy Compounds

Applies to all compounds **except** `BeB12N2 (Triclinic)`.

```
<Formula>/
│
├── 📁 oqmd_structures/
│   ├── 📄 POSCAR              — original OQMD structure
│   └── 📄 INCAR               — VASP relaxation settings
│
├── 📁 DFT_elastic_data/
│   ├── 📄 POSCAR              — conventional cell for elastic calculation
│   ├── 📄 INCAR               — VASP elastic settings (IBRION=6, ISIF=3)
│   ├── 📄 INPUT.in            — auxiliary elastic input parameters
│   └── 📄 elastic_vasp_output — raw VASP output; contains C_ij tensor
│
└── 📁 phonopy_calculations/
    │
    ├── 📁 Step1_phonopy_input/
    │   ├── 📄 POSCAR          — primitive cell
    │   ├── 📄 SPOSCAR         — supercell for finite-displacement forces
    │   ├── 📄 INCAR           — single-point VASP settings for force runs
    │   └── 📄 SYMMETRY        — symmetry analysis output
    │
    ├── 📁 Step2_phonopy_output/
    │   ├── 📄 PRIMCELL.vasp   — primitive cell (VASP5 format; required by scripts)
    │   ├── 📄 FORCE_CONSTANTS — second-order interatomic force constants
    │   ├── 📄 FORCE_SETS      — raw displacement–force dataset
    │   ├── 📄 KPATH.phonopy   — Brillouin zone path definition
    │   ├── 📄 HIGH_SYMMETRY_POINTS
    │   ├── 📄 phonopy_disp    — Phonopy displacement configuration (YAML)
    │   ├── 📄 projected_dos.dat — atom-projected phonon DOS
    │   └── 📄 thermal_properties — C_v, S, E, F vs T from 0–1000 K (YAML)
    │
    └── 📁 Step3_postprocessing_results/
        ├── 📄 phonon_dispersion_<Formula>.pdf
        ├── 📄 Cv_comparison_<Formula>.pdf
        └── 📄 <Formula>_thermal_properties.json
```

---

## 4. Internal Layout — DFPT Compound (BeB₁₂N₂ Triclinic)

`BeB12N2 (Triclinic)` uses **Density Functional Perturbation Theory** (DFPT) because its P1 space group offers no symmetry reduction, making the finite-displacement supercell approach computationally prohibitive. DFPT computes force constants analytically via linear response without large supercells.

```
BeB12N2 (Triclinic)/
│
├── 📁 DFT_elastic_data/              — identical layout to §3
│
└── 📁 DFPT_Phonopy_calculations/
    │
    ├── 📁 Step1_DFPT_input/
    │   ├── 📄 POSCAR              — primitive cell
    │   ├── 📄 POSCAR_supercell    — supercell for DFPT
    │   ├── 📄 INCAR               — VASP DFPT settings (LEPSILON, IBRION=8)
    │   └── 📄 SYMMETRY
    │
    ├── 📁 Step2_DFPT_output/
    │   ├── 📄 DYNMAT              — dynamical matrix from VASP DFPT (~1400 KB)
    │   ├── 📄 FORCE_CONSTANTS     — force constants converted from DYNMAT
    │   ├── 📄 KPATH.phonopy
    │   ├── 📄 KPATH_supercell.phonopy
    │   ├── 📄 HIGH_SYMMETRY_POINTS
    │   ├── 📄 PRIMCELL.vasp
    │   ├── 📄 phonopy_disp
    │   ├── 📄 projected_dos.dat
    │   └── 📄 thermal_properties
    │
    └── 📁 Step3_postprocessing_results_with_phonopy/
        ├── 📄 phonon_dispersion_B12BeN2-triclinic.pdf
        ├── 📄 Cv_comparison_B12BeN2-triclinic.pdf
        └── 📄 BeB12N2_triclinic_thermal_properties.json
```

---

## 5. Key Files Reference

| File | Location | Description |
|---|---|---|
| [`PRIMCELL.vasp`](.) | `Step2_*/` | Primitive cell in VASP5 format. **Required** by both post-processing scripts to parse chemical formula and species. |
| [`FORCE_CONSTANTS`](.) | `Step2_*/` | Second-order interatomic force constants in Phonopy format; input for phonon dispersion calculation. |
| [`thermal_properties`](.) | `Step2_*/` | Phonopy YAML output: C\_v, entropy, internal energy, free energy at 10 K intervals from 0–1000 K. |
| [`projected_dos.dat`](.) | `Step2_*/` | Atom-projected phonon DOS. Column layout: frequency (THz), then one column per atom following POSCAR atom order. |
| [`KPATH.phonopy`](.) | `Step2_*/` | Defines the Brillouin zone path. Contains `DIM`, `NPOINTS`, `BAND` (fractional coordinates), and `BAND_LABELS`. |
| [`elastic_vasp_output`](.) | `DFT_elastic_data/` | Raw VASP output containing the full C\_ij elastic tensor in GPa. |
| [`DYNMAT`](.) | `Step2_DFPT_output/` | DFPT-only. Dynamical matrix written by VASP; converted to `FORCE_CONSTANTS` by Phonopy. |
| [`psudo_potentials_details.xlsx`](./psudo_potentials_details.xlsx) | Root of this folder | PAW pseudopotential version for every element used across all 26 compounds. |
