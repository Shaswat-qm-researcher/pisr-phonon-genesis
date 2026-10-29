# Materials Property Dataset: AFLOW & Materials Project

Comparative dataset of thermoelastic and electronic properties for inorganic compounds, sourced from the AFLOW and Materials Project (MP) databases.

---
> **Note:** This is a sub-repository of the main project:  
> **[pisr-phonon-genesis](https://github.com/Shaswat-qm-researcher/pisr-phonon-genesis/)**
---

## Folder Structure

```
Physics-Informed-Symbolic-Regression-for-Phonon-Related-Property-Prediction-and-Materials-Discovery/
├── codes/
│   ├── Aflow_data_downloader.py            # Downloads raw AFLOW data via AFLUX API
│   ├── MP_data_downloader.py               # Downloads stable MP materials + elastic data
│   ├── MP_vs_AFLOW_dataset_comparison.py   # Compares MP and AFLOW datasets
│   ├── zendo_phonopy_data_downloader.py    # Downloads MP Phonon DB v1.1 from Zenodo
│   └── requirements.txt
├── data/
│   ├── raw/
│   │   ├── aflow_data.csv                  # Raw AFLOW database export
│   │   ├── mp_data.xlsx                    # Raw Materials Project database export
│   │   └── mp_data_phonon_and_elastic.xlsx # MP data with phonon (Zenodo) + elastic properties
│   └── processed/
│       ├── AFLOW_cleaned_dataset.csv       # Cleaned & renamed AFLOW features
│       ├── AFLOW_only_dataset.csv          # AFLOW compounds not found in MP
│       ├── MP_cleaned_dataset.csv          # Cleaned & renamed MP features
│       ├── MP_cleaned_dataset_stable.csv   # MP features filtered to stable compounds only
│       ├── common_compounds.csv            # Compounds matched across both databases
│       ├── feature_descriptions.json       # Feature description for processed data coloums
│       └── symbol_conversion.txt           # Feature abbreviations, LaTeX symbols & definitions
├── figures/
│   ├── data_comparison.pdf                 # Bar chart: MP vs AFLOW compound counts
│   └── venn_diagram.pdf                    # Venn diagram: shared vs unique compounds
├── DATA_DETAILS.md
└── README.md
```

> For detailed column definitions, data formats, and file sizes see [`DATA_DETAILS.md`](https://github.com/Shaswat-qm-researcher/pisr-phonon-genesis/blob/main/data/DATA_DETAILS.md).

---

## Dataset Summary

| File | Source | Compounds | Properties |
|------|--------|-----------|------------|
| `AFLOW_cleaned_dataset.csv` | AFLOW | 5,077 | 28 |
| `AFLOW_only_dataset.csv` | AFLOW | 4,206 | 28 |
| `MP_cleaned_dataset.csv` | Materials Project | 6,432 | 24 |
| `MP_cleaned_dataset_stable.csv` | Materials Project | 6,276 | 24 |
| `common_compounds.csv` | Both | 871 | 10 (ID + metadata) |

**Total unique compounds: 10,412** (9,315 database-exclusive + 1,097 shared)

---

## Feature Abbreviations

All cleaned files use short abbreviations defined in `symbol_conversion.txt` and detailed in `feature_descriptions.json`. Key ones:

| Abbreviation | Property | Unit |
|---|---|---|
| `BGAP` | Band Gap | eV |
| `EPA` | Energy per Atom | eV/atom |
| `FEPA` | Formation Energy per Atom | eV/atom |
| `BM` | Bulk Modulus (VRH) | GPa |
| `SM` | Shear Modulus (VRH) | GPa |
| `YM` | Young's Modulus (VRH) | GPa |
| `DT` / `DT_AGL` | Debye Temperature | K |
| `TC_300` | Thermal Conductivity at 300K | W/m·K |
| `D` | Mass Density | g/cm³ |
| `VPA` | Atomic Volume | Å³/atom |

Full list with LaTeX symbols: [`data/processed/symbol_conversion.txt`](https://github.com/Shaswat-qm-researcher/pisr-phonon-genesis/blob/main/data/processed/symbol_conversion.txt)

---

## Symbol Conversion Format

Each entry in `symbol_conversion.txt` follows this format:

```
ABBREVIATION = $LaTeX_symbol$
```

Example:
```
BGAP = $E_g$
BM   = $B_{VRH}$
DT   = $\Theta_D$
```

Comments begin with `#`.

---

## Data Sources

- **AFLOW**: [aflow.org](https://aflow.org) — AGL/AEL-based thermoelastic properties
- **Materials Project**: [materialsproject.org](https://materialsproject.org) — DFPT-based dielectric and elastic properties
- **Zenodo Phonon DB**: [doi.org/10.26434/chemrxiv.15004632/v1](https://doi.org/10.26434/chemrxiv.15004632/v1) — MP Phonon Database v1.1 (harmonic phonon properties)

---

## Requirements to Obtain Data from Databases

### Common
```
pandas
numpy
matplotlib
ast
json
requests
tqdm
```

### Materials Project
```
mp-api>=0.46.5
emmet-core>=0.87.2
```

Install with:
```bash
pip install -r codes/requirements.txt
```

### AFLOW
No API key required. The AFLUX API is accessed directly via HTTP — the compute node must be able to reach `https://aflow.org`.

### Zenodo Phonon Database
```
requests
```
Downloads MP Phonon DB v1.1 (Zenodo record 20196565). Supports parallel downloads, mid-tar resume, and SLURM/PBS batch jobs. The full dataset is >100 GB; run on a login/transfer node or a compute node with outbound internet access.

---
**Last Updated**: 28-10-2026
