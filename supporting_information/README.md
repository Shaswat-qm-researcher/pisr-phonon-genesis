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

This spreadsheet contains DFT- and SISSO-computed properties for a set of candidate structures, organized into four grouped sections:

- **OQMD Reference**: entry identifiers (S.No., formula, OQMD Entry ID, Structure ID), space group (symbol and number), number of atoms, total energy, net magnetic moment, static band gap, atomic volume, molar mass, unit cell mass, energy above hull, and formation energy.
- **DFT Elastic Constant Calculations**: crystal system and space group, cell volume and density, the full elastic stiffness tensor (C11–C66), Voigt/Reuss/Hill-averaged bulk (B), Young's (E), and shear (G) moduli, Poisson's ratio, Pugh's ratio (G/B) and its inverse, Vickers hardness estimates (two models), longitudinal/transverse/average sound velocities, and the Debye temperature from the Anderson approximation.
- **DFT Phonopy/DFPT Calculations**: temperature-dependent heat capacity (Cv), entropy, internal energy, and free energy (each given as a temperature → value mapping from 0–1000 K), together with the Debye temperature computed from Phonopy.
- **SISSO**: the SISSO-predicted Debye temperature, thermal conductivity at 300 K, heat capacity at 300 K (in kB/cell and J/kg·K), and thermal diffusivity at 300 K.

Some entries include multiple rows per formula (e.g., an original relaxed structure and a DFPT-distorted variant), reflecting different structural inputs used in the calculations.

## `Experimental_Data_Figure_4.xlsx`

Contains the experimental and computed data used to build Figure 4, comparing predicted and measured Debye temperatures across a set of elemental/simple materials. Columns include:

- **Identifiers**: Materials Project ID (`material_id`), chemical formula, crystal system, space group (symbol and number), composition, number of atoms, and number of elements.
- **Structural/mechanical properties**: volume per atom, mass density, Voigt-Reuss-Hill bulk modulus, shear modulus, and Young's modulus.
- **Debye temperature comparison**: Materials Project–derived, SISSO-predicted, and experimentally measured Debye temperatures, enabling direct model-vs-experiment comparison.
- **Provenance**: the literature source of the experimental value, publication year, and DOI.

---

*If you have trouble opening any file, please contact the corresponding author. *bsomnath@iitk.ac.in
