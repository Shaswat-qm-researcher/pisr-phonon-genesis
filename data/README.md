# Materials Property Dataset: AFLOW & Materials Project

Comparative dataset of thermoelastic and electronic properties for inorganic compounds, sourced from the AFLOW and Materials Project (MP) databases.

---
> **Note:** This is a sub-repository of the main project:  
> **[pisr-phonon-genesis](https://github.com/Shaswat-qm-researcher/pisr-phonon-genesis/)**
---

## Folder Structure

```
Physics-Informed-Symbolic-Regression-for-Phonon-Related-Property-Prediction-and-Materials-Discovery/
├── data/
│   ├── raw/
│   │   ├── aflow_data.csv          # Raw AFLOW database export
│   │   └── mp_data.xlsx             # Raw Materials Project database export
│   └── processed/
│       ├── AFLOW_cleaned_dataset.csv   # Cleaned & renamed AFLOW features
│       ├── MP_cleaned_dataset.csv      # Cleaned & renamed MP features
│       ├── common_compounds.csv        # Compounds matched across both databases
│       └── symbol_conversion.txt       # Feature abbreviations, LaTeX symbols & definitions
├── figures/
│   ├── data_comparison.pdf         # Bar chart: MP vs AFLOW compound counts
│   └── venn_diagram.pdf            # Venn diagram: shared vs unique compounds
├──
├── DATA_DETAILS.md
└── README.md
```

> For detailed column definitions, data formats, and file sizes see [`DATA_DETAILS.md`](https://github.com/Shaswat-qm-researcher/pisr-phonon-genesis/data/DATA_DETAILS.md).

---

## Dataset Summary

| File | Source | Compounds | Properties |
|------|--------|-----------|------------|
| `AFLOW_cleaned_dataset.csv` | AFLOW | 5,077 | 28 |
| `MP_cleaned_dataset.csv` | Materials Project | 6,432 | 23 |
| `common_compounds.csv` | Both | 1,097 | 8 (ID + metadata) |

**Total unique compounds: 10,412** (9,315 database-exclusive + 1,097 shared)

---

## Feature Abbreviations

All cleaned files use short abbreviations defined in `symbol_conversion.txt`. Key ones:

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
| `VPA` | Atomic volume | Å³/atom |

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

---

## Requirements to obtain data from databases

### Common
```
pandas
numpy
matplotlib
ast
json
```
### Material Project
```
from emmet.core.summary import HasProps
from mp_api.client import MPRester
```
### AFLOW
```
pymatgen
from emmet.core.summary import HasProps
from pymatgen.ext.matproj import MPRester
```
