# DATA_DETAILS.md

Detailed documentation for all files in the `data/` folder.

---

## Raw Files (`data/raw/`)

### `aflow_data.csv`
- **Source**: AFLOW REST API
- **Size**: ~4,079 KB
- **Format**: Tab-separated, one compound per row
- **Key raw columns**:

| Column | Description |
|--------|-------------|
| `compound` | Chemical formula |
| `auid` | AFLOW unique ID |
| `aurl` | AFLOW database URL |
| `nspecies` | Number of element species |
| `natoms` | Number of atoms in unit cell |
| `density` | Mass density (g/cm³) |
| `Egap` | Band gap (eV) |
| `energy_atom` | Total energy per atom (eV/atom) |
| `enthalpy_formation_cell` | Formation enthalpy (eV/cell) |
| `ael_bulk_modulus_vrh` | Bulk modulus VRH (GPa) |
| `ael_shear_modulus_vrh` | Shear modulus VRH (GPa) |
| `ael_youngs_modulus_vrh` | Young's modulus (GPa) |
| `ael_poisson_ratio` | Poisson's ratio |
| `ael_debye_temperature` | Debye temperature AEL (K) |
| `agl_debye` | Debye temperature AGL (K) |
| `agl_thermal_conductivity_300K` | Thermal conductivity at 300K (W/m·K) |
| `agl_thermal_expansion_300K` | Thermal expansion coefficient at 300K (1/K) |
| `agl_heat_capacity_Cp_300K` | Heat capacity Cp at 300K |
| `agl_heat_capacity_Cv_300K` | Heat capacity Cv at 300K |
| `ael_speed_sound_transverse` | Transverse speed of sound (m/s) |
| `ael_speed_sound_longitudinal` | Longitudinal speed of sound (m/s) |
| `ael_speed_sound_average` | Mean speed of sound (m/s) |
| `spin_atom` | Atomic spin |
| `bader_net_charges` | Bader net charges (list) |
| `volume_atom` | Atomic Volume (Å³/atom) |

---

### `mp_data.xlsx`
- **Source**: Materials Project API (v2025.04.10)
- **Size**: ~16,000 KB
- **Format**: Tab-separated, one compound per row
- **Key raw columns**:

| Column | Description |
|--------|-------------|
| `material_id` | MP unique ID (e.g. mp-24390) |
| `formula_pretty` | Chemical formula |
| `nelements` | Number of element species |
| `nsites` | Number of atoms in unit cell |
| `band_gap` | Band gap (eV) |
| `energy_per_atom` | Total energy per atom (eV/atom) |
| `formation_energy_per_atom` | Formation energy per atom (eV/atom) |
| `efermi` | Fermi energy (eV) |
| `total_magnetization` | Total magnetization (μB) |
| `volume` | Unit cell volume (Å³) |
| `density` | Mass density (g/cm³) |
| `bulk_modulus` (vrh) | Bulk modulus VRH (GPa) |
| `shear_modulus` (vrh) | Shear modulus VRH (GPa) |
| `youngs_modulus` | Young's modulus (GPa) |
| `homogeneous_poisson` | Poisson's ratio |
| `debye_temperature` | Debye temperature (K) |
| `sound_velocity` (transverse/longitudinal) | Speed of sound (m/s) |
| `is_metal` | Boolean |
| `is_stable` | Boolean (energy above hull = 0) |
| `ordering` | Magnetic ordering (NM/FM/AFM) |
| `symmetry` | Crystal system, space group, number |

### `mp_data_phonon_and_elastic.xlsx`
- **Source**: Materials Project API and https://doi.org/10.26434/chemrxiv.15004632/v1
- **Size**: ~16,000 KB
- **Format**: Tab-separated, one compound per row
- **Key raw columns**:

| Column | Description |
|--------|-------------|
| `material_id` | MP unique ID (e.g. mp-24390) |
| `formula_pretty` | Chemical formula |
| `nelements` | Number of element species |
| `nsites` | Number of atoms in unit cell |
| `band_gap` | Band gap (eV) |
| `energy_per_atom` | Total energy per atom (eV/atom) |
| `formation_energy_per_atom` | Formation energy per atom (eV/atom) |
| `efermi` | Fermi energy (eV) |
| `total_magnetization` | Total magnetization (μB) |
| `volume` | Unit cell volume (Å³) |
| `density` | Mass density (g/cm³) |
| `bulk_modulus` (vrh) | Bulk modulus VRH (GPa) |
| `shear_modulus` (vrh) | Shear modulus VRH (GPa) |
| `youngs_modulus` | Young's modulus (GPa) |
| `homogeneous_poisson` | Poisson's ratio |
| `debye_temperature` | Debye temperature (K) |
| `debye_temperature_source` | Label source for Debye temperature (PDOS_phonopy vs sound_velocity_elastic) |
| `sound_velocity` (transverse/longitudinal) | Speed of sound (m/s) |
| `is_metal` | Boolean |
| `is_stable` | Boolean (energy above hull = 0) |
| `ordering` | Magnetic ordering (NM/FM/AFM) |
| `symmetry` | Crystal system, space group, number |

> Note: Many columns contain nested JSON objects (e.g. `structure`, `bandstructure`, `dos`, `fitting_data`). These are present in raw files but are not carried into cleaned files.

---

## Processed Files (`data/processed/`)

### `AFLOW_cleaned_dataset.csv`
- **Size**: ~1,300 KB
- **Compounds**: 5,077 rows × 28 columns
- **Format**: Tab-separated

| Abbreviation | Original AFLOW column | Unit |
|---|---|---|
| `auid` | `auid` | — |
| `formula` | `compound` | — |
| `NE` | `nspecies` | — |
| `NA` | `natoms` | — |
| `BGAP` | `Egap` | eV |
| `EPA` | `energy_atom` | eV/atom |
| `ASPIN` | `spin_atom` | — |
| `ENPA` | `enthalpy_atom` | eV/atom |
| `VPA` | `Atomic_volume` | Å³/atom |
| `D` | `mass_density` | g/cm³ |
| `BM` | `ael_bulk_modulus_vrh` | GPa |
| `SM` | `ael_shear_modulus_vrh` | GPa |
| `YM` | `ael_youngs_modulus_vrh` | GPa |
| `ANI` | `ael_elastic_anisotropy` | — |
| `PR` | `ael_poisson_ratio` | — |
| `PUGR` | `ael_pughs_modulus_ratio` | — |
| `IPUGR` | Computed: B/G | — |
| `DT_AGL` | `agl_debye` | K |
| `DT_A_AGL` | `agl_acoustic_debye` | K |
| `vs` | `ael_speed_sound_transverse` | m/s |
| `vl` | `ael_speed_sound_longitudinal` | m/s |
| `vm` | `ael_speed_sound_average` | m/s |
| `gruneisen` | `agl_gruneisen` | — |
| `Cv_300` | `agl_heat_capacity_Cv_300K` | J/K.cell |
| `Cp_300` | `agl_heat_capacity_Cp_300K` | J/K.cell |
| `TEX_300` | `agl_thermal_expansion_300K` | 1/K |
| `TC_300` | `agl_thermal_conductivity_300K` | W/m·K |
| `VIB_EN_300` | `agl_vibrational_entropy_300K_atom` | eV/K·atom |
| `VIB_FE_300` | `agl_vibrational_free_energy_300K_atom` | eV/atom |

---

### `AFLOW_only_dataset.csv`
- **Size**: ~1,100 KB
- **Compounds**: 4,206 rows × 28 columns
- **Format**: Tab-separated

| Abbreviation | Original AFLOW column | Unit |
|---|---|---|
| `auid` | `auid` | — |
| `formula` | `compound` | — |
| `NE` | `nspecies` | — |
| `NA` | `natoms` | — |
| `BGAP` | `Egap` | eV |
| `EPA` | `energy_atom` | eV/atom |
| `ASPIN` | `spin_atom` | — |
| `ENPA` | `enthalpy_atom` | eV/atom |
| `VPA` | `Atomic_volume` | Å³/atom |
| `D` | `mass_density` | g/cm³ |
| `BM` | `ael_bulk_modulus_vrh` | GPa |
| `SM` | `ael_shear_modulus_vrh` | GPa |
| `YM` | `ael_youngs_modulus_vrh` | GPa |
| `ANI` | `ael_elastic_anisotropy` | — |
| `PR` | `ael_poisson_ratio` | — |
| `PUGR` | `ael_pughs_modulus_ratio` | — |
| `IPUGR` | Computed: B/G | — |
| `DT_AGL` | `agl_debye` | K |
| `DT_A_AGL` | `agl_acoustic_debye` | K |
| `vs` | `ael_speed_sound_transverse` | m/s |
| `vl` | `ael_speed_sound_longitudinal` | m/s |
| `vm` | `ael_speed_sound_average` | m/s |
| `gruneisen` | `agl_gruneisen` | — |
| `Cv_300` | `agl_heat_capacity_Cv_300K` | J/K.cell |
| `Cp_300` | `agl_heat_capacity_Cp_300K` | J/K.cell |
| `TEX_300` | `agl_thermal_expansion_300K` | 1/K |
| `TC_300` | `agl_thermal_conductivity_300K` | W/m·K |
| `VIB_EN_300` | `agl_vibrational_entropy_300K_atom` | eV/K·atom |
| `VIB_FE_300` | `agl_vibrational_free_energy_300K_atom` | eV/atom |

---

### `MP_cleaned_dataset.csv`
- **Size**: ~1,512 KB
- **Compounds**: 6,432 rows × 24 columns
- **Format**: Tab-separated

| Abbreviation | Original MP column | Unit |
|---|---|---|
| `material_id` | `material_id` | — |
| `formula` | `formula_pretty` | — |
| `NE` | `nelements` | — |
| `NA` | `nsites` | — |
| `BGAP` | `band_gap` | eV |
| `EPA` | `energy_per_atom` | eV/atom |
| `FEPA` | `formation_energy_per_atom` | eV/atom |
| `EFMR` | `efermi` | eV |
| `TM` | `total_magnetization` | μB |
| `MSITE` | `num_unique_magnetic_sites` | — |
| `V` | `volume` | Å³ |
| `VPA` | Computed: V/NA | Å³ |
| `D` | `density` | g/cm³ |
| `BM` | `bulk_modulus.vrh` | GPa |
| `SM` | `shear_modulus.vrh` | GPa |
| `YM` | `youngs_modulus` | GPa |
| `PR` | `homogeneous_poisson` | — |
| `PUGR` | Computed: SM/BM | — |
| `IPUGR` | Computed: BM/SM | — |
| `DT` | `debye_temperature` | K |
| `debye_temperature_source` | Label source for Debye temperature | —  |
| `vs` | `sound_velocity.transverse` | m/s |
| `vl` | `sound_velocity.longitudinal` | m/s |
| `vm` | `sound_velocity.snyder_acoustic` (approx.) | m/s |

---

### `MP_cleaned_dataset_stable.csv`
- **Size**: ~1,444 KB
- **Compounds**: 6,276 rows × 24 columns
- **Format**: Tab-separated

| Abbreviation | Original MP column | Unit |
|---|---|---|
| `material_id` | `material_id` | — |
| `formula` | `formula_pretty` | — |
| `NE` | `nelements` | — |
| `NA` | `nsites` | — |
| `BGAP` | `band_gap` | eV |
| `EPA` | `energy_per_atom` | eV/atom |
| `FEPA` | `formation_energy_per_atom` | eV/atom |
| `EFMR` | `efermi` | eV |
| `TM` | `total_magnetization` | μB |
| `MSITE` | `num_unique_magnetic_sites` | — |
| `V` | `volume` | Å³ |
| `VPA` | Computed: V/NA | Å³ |
| `D` | `density` | g/cm³ |
| `BM` | `bulk_modulus.vrh` | GPa |
| `SM` | `shear_modulus.vrh` | GPa |
| `YM` | `youngs_modulus` | GPa |
| `PR` | `homogeneous_poisson` | — |
| `PUGR` | Computed: SM/BM | — |
| `IPUGR` | Computed: BM/SM | — |
| `DT` | `debye_temperature` | K |
| `debye_temperature_source` | Label source for Debye temperature | —  |
| `vs` | `sound_velocity.transverse` | m/s |
| `vl` | `sound_velocity.longitudinal` | m/s |
| `vm` | `sound_velocity.snyder_acoustic` (approx.) | m/s |

---

### `common_compounds.csv`
- **Size**: ~78 KB
- **Compounds**: 871 rows × 10 columns
- **Description**: Compounds present in both AFLOW and MP, matched by chemical formula and element species

| Column | Description |
|--------|-------------|
| `MP_ID` | Materials Project ID |
| `MP_formula` | Formula from MP |
| `MP_sg` | Space group number from MP |
| `MP_species` | Element list from MP |
| `MP_NA` | Number of atoms (MP) |
| `AFLOW_ID` | AFLOW unique ID |
| `AFLOW_formula` | Formula from AFLOW |
| `AFLOW_sg` | Space group number from AFLOW |
| `AFLOW_species` | Element list from AFLOW |
| `AFLOW_NA` | Number of atoms (AFLOW) |

---

### `symbol_conversion.txt`
- **Size**: ~3 KB
- **Format**: Plain text, `ABBREVIATION = $LaTeX_symbol$`, comments start with `#`
- **Contents**: Maps all feature abbreviations used in cleaned files to their LaTeX mathematical symbols and plain-English definitions
- **Usage**: Reference when labelling plots, writing equations, or building tables in papers

---

## Figures (`figures/`)

| File | Description |
|------|-------------|
| `data_comparison.pdf` | Horizontal bar chart comparing compound counts: MP Total, MP Only, AFLOW Total, AFLOW Only, Shared, Total Unique |
| `venn_diagram.pdf` | Venn diagram showing overlap between Material project and AFLOW |
