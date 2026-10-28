# Supporting Information

This folder contains the supporting data files and interactive figure referenced in the manuscript.

## Contents

| File | Description |
|---|---|
| `Experimental_Data_Figure_4.xlsx` | Experimental data used to generate Figure 4. |
| `Interactive_PCA_Scatter_Figure_6c.html` | Interactive PCA scatter plot corresponding to Figure 6c. |
| `New_Material_Properties_Table_2.xlsx` | Material properties data underlying Table 2 (see details below). |

## Viewing the interactive figure (`Interactive_PCA_Scatter_Figure_6c.html`)

The PCA scatter plot in Figure 6c is provided as a standalone interactive HTML file so that readers can explore the data directly (zoom, pan, hover for point-level details, toggle legend entries, etc.).

To view it:

1. **Download** `Interactive_PCA_Scatter_Figure_6c.html` to your computer.
2. **Open the file with a web browser** (e.g., Chrome, Firefox, Edge, or Safari) — either double-click the file, or right-click and choose "Open with" → your browser of choice.
3. The interactive plot will load directly in the browser tab. No internet connection or additional software is required.

## `New_Material_Properties_Table_2.xlsx`

This spreadsheet contains OQMD reference data together with DFT- and SISSO-computed properties for a set of candidate structures, organized into five grouped sections:

- **OQMD Reference**: entry identifiers (formula, OQMD Entry ID, Structure ID), space group (symbol and number), number of atoms, total energy (eV/atom), net magnetic moment (μB/atom), static band gap (eV), atomic volume (Å³/atom), molar mass (g/mol), unit cell mass (kg), energy above hull (eV/atom), and formation energy (eV/atom).
- **DFT Elastic Constant Calculations**:
  - *Structure*: crystal system, space group and number, initial and relaxed lattice angles (α, β, γ) and lattice parameters (a, b, c), cell volume, atomic volume, and mass density.
  - *Elastic tensor*: the full 6×6 stiffness matrix (C11–C66, all 36 components).
  - *Averaged moduli*: Voigt/Reuss/Hill bulk (B), Young's (E), and shear (G) moduli, and Poisson's ratio.
  - *Ratios*: Pugh's ratio (G/B) and its inverse (B/G), each in Voigt/Reuss/Hill form.
  - *Hardness and stiffness*: Vickers hardness estimates from two models (labelled 6 and 7), and the pressure-wave (longitudinal) modulus, all in Voigt/Reuss/Hill form.
  - *Wave speeds*: longitudinal, transverse, and average sound velocities (m/s).
  - *Debye temperature (Anderson)*: derived from the elastic constants.
- **DFT Phonopy Calculations**:
  - *Temperature-dependent properties*: heat capacity (Cv, J/K·mol), entropy (J/K·mol), internal energy (kJ/mol), and free energy (kJ/mol), each given as a temperature → value mapping.
  - *Debye temperature (Phonopy)*.
  - *300 K properties*: Cv (J/kg·K), Grüneisen parameter (γ), isothermal bulk modulus (GPa), volumetric thermal expansion (×10⁻⁶ /K), Cp (J/kg·K), and thermal conductivity (W/m·K).
- **SISSO**: the SISSO-predicted Debye temperature (K), thermal conductivity at 300 K (W/m·K), and heat capacity at 300 K (in k_B/cell and J/kg·K).
- **DFT + SISSO**: thermal diffusivity at 300 K (m²/s), combining the DFT and SISSO results. Candidates that have a DFT thermal conductivity use that value; all remaining candidates use the SISSO thermal conductivity. Every candidate uses the DFT Cp at 300 K.

## `Experimental_Data_Figure_4.xlsx`

Contains the experimental and computed data used to build Figure 4, comparing predicted and measured Debye temperatures across a set of elemental/simple materials. Columns include:

- **Identifiers**: Materials Project ID (`material_id`), chemical formula, crystal system, space group (symbol and number), composition, number of atoms, and number of elements.
- **Structural/mechanical properties**: volume per atom, mass density, Voigt-Reuss-Hill bulk modulus, shear modulus, and Young's modulus.
- **Debye temperature comparison**: Materials Project–derived, SISSO-predicted, and experimentally measured Debye temperatures, enabling direct model-vs-experiment comparison.
- **Provenance**: the literature source of the experimental value, publication year, and DOI.

---

*If you have trouble opening any file, please contact the corresponding author. *bsomnath@iitk.ac.in

---
**Last Updated**: 28-10-2026
