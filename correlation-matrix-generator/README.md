# Correlation Matrix Generator

A Python tool for generating Pearson correlation matrices from materials science datasets with customizable visualization and LaTeX-compatible labels.

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## Overview

This tool provides an interactive command-line interface for analyzing Pearson correlations between materials properties and visualizing them as heatmaps with LaTeX-formatted labels. It automates the workflow from data loading to high-resolution figure export, supporting both Excel and CSV formats.

**Pearson Correlation Coefficient:**

$$r_{xy} = \frac{\sum_{i=1}^{n}(x_i - \bar{x})(y_i - \bar{y})}{\sqrt{\sum_{i=1}^{n}(x_i - \bar{x})^2}\sqrt{\sum_{i=1}^{n}(y_i - \bar{y})^2}}$$

where $r_{xy} \in [-1, 1]$:
- $r = +1$: Perfect positive correlation
- $r =  0$: No linear correlation  
- $r = -1$: Perfect negative correlation

📖 [Pearson, K. (1895) Philosophical Transactions of the Royal Society of London. ](https://royalsocietypublishing.org/rsta/article/doi/10.1098/rsta.1896.0007)

> **Note:** This is a sub-repository of the main project:  
> **[pisr-phonon-genesis](https://github.com/Shaswat-qm-researcher/pisr-phonon-genesis/)**
---

## Features

- **Interactive CLI**: User-friendly command-line interface with colored prompts and validation
- **Flexible Input**: Supports Excel (.xlsx, .xls) and CSV file formats
- **Column Management**: Drop unwanted columns (e.g., material IDs, formulas) before correlation analysis
- **Custom Labels**: Map column names to LaTeX symbols via `symbol_conversion.txt` for professional figures
- **Dynamic Sizing**: Automatic figure dimension adjustment based on number of parameters
- **Custom Colormap**: Beautiful gradient from dark red (negative) through white (zero) to dark blue (positive)
- **Dual Export**: Saves both visualization (with LaTeX labels) and data table (with original column names in CSV format)

---

## Repository Structure

```
correlation-matrix-generator/
├── correlation_matrix_generator.ipynb # Jupyter notebook
├── AFLOW_cleaned_dataset.csv          # AFLOW database training data
├── MP_cleaned_dataset.csv             # Materials Project training data
├── symbol_conversion.txt             # Feature name to LaTeX symbol mapping
├── requirements.txt                  # Python dependencies
├── results/                          
│   ├── heatmaps/                     # Correlation heatmaps
│   │   ├── Aflow_CM_matrix.pdf             
│   │   └── MP_CM_matrix.pdf                
│   └── matrices/                     # Correlation matrices (tabular)
│       ├── Aflow_CM_matrix.csv            
│       └── MP_CM_matrix.csv               
└── README.md                         # This file
```

---

## Requirements

### Python Version
- Python 3.12 or higher

### Dependencies
```
pandas==2.2.3
seaborn==0.13.2
matplotlib==3.9.2
openpyxl==3.1.2
```

Install all dependencies:
```bash
pip install -r requirements.txt
```

---

## Installation

1. Clone the main repository:
```bash
git clone https://github.com/Shaswat-qm-researcher/pisr-phonon-genesis.git
cd pisr-phonon-genesis
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

---

## Usage

### Quick Start

**Jupyter Notebook:**
```bash
jupyter notebook correlation_matrix_generator.ipynb
```

### Important: Data Preparation

**Before running correlation analysis, drop the following identifier columns:**
- `auid` (AFLOW Unique ID)
- `MP_ID` (Materials Project ID)  
- `formula` (Chemical formula)

The notebook will prompt you to drop columns in **Step 2**. These non-numeric identifiers should not be included in Pearson correlation calculations.

### Workflow

The tool guides you through 7 interactive steps:

1. **Load Data File** - Select Excel/CSV file from directory
2. **Column Selection** - Drop identifier columns (`auid`, `MP_ID`, `formula`)
3. **Label Configuration** - Use column headings or load LaTeX symbols from `symbol_conversion.txt`
4. **Calculate Correlation** - Pearson correlation coefficients computed automatically
5. **Dynamic Sizing** - Figure dimensions calculated based on parameter count
6. **Generate Visualization** - Custom colormap heatmap with correlation values
7. **Save Results** - Export PDF (visualization) and CSV (data table)

### Output Files

The tool generates two files per run:
1. **`prefix_matrix.pdf`**: Heatmap with LaTeX labels
2. **`prefix_matrix.csv`**: Correlation matrix with original column names

---

## Using LaTeX Symbols

The `symbol_conversion.txt` file maps dataset column names to publication-ready LaTeX symbols. 

**Format:**
```text
COLUMN_NAME = $LaTeX_Symbol$
```

**Example:**
```text
BGAP = $E_g$
BM = $B_{vrh}$
DT_AGL = $\Theta_D$
```

To use symbols in your figures, select the "file" option in Step 3. Include the location where the file is stored. 

For the complete list of feature definitions and symbols, refer to `symbol_conversion.txt`.

---

## Example Results

The `results/` folder contains pre-generated outputs:

- **`heatmaps/`**: PDF files with correlation visualizations
  - `Aflow_CM_matrix.pdf` - AFLOW dataset correlations
  - `MP_CM_matrix.pdf` - Materials Project dataset correlations

- **`matrices/`**: Excel files with correlation data
  - `Aflow_CM_matrix.csv` - AFLOW correlation matrix
  - `MP_CM_matrix.csv` - Materials Project correlation matrix

---

## Tips for Best Results

1. **Always drop ID columns** (`auid`, `MP_ID`, `formula`) before correlation analysis.
2. **Remove non-numeric columns** to avoid calculation errors
3. **Font size**: Start with 36 and adjust if labels overlap (decrease) or appear small (increase).
4. **Symbol file**: Keep `symbol_conversion.txt` in the same directory as your data for easy loading.
5. **Output organization**: Use descriptive file prefixes (e.g., "AFLOW_elastic", "MP_thermal").

---

## Troubleshooting

### Common Issues

**Issue**: "No files found in directory"
- **Solution**: Ensure data files have .xlsx, .xls, or .csv extensions

**Issue**: Error during correlation calculation
- **Solution**: Check that all remaining columns contain numeric data (drop ID and formula columns)

**Issue**: Labels overlapping in visualization
- **Solution**: Decrease font size or let dynamic sizing handle larger datasets

**Issue**: Column names not found when dropping columns
- **Solution**: Copy-paste column names exactly as displayed (case-sensitive)

**Issue**: Symbol conversion not loading
- **Solution**: Verify `symbol_conversion.txt` format: `COLUMN = $symbol$` (one per line)

---

## Citation

If you use this code in your research, please cite:

```bibtex
@article{
}
```

---

## Authors

- **Shaswat Pathak**, **Vardhman Dwivedi**, **Albert Linda**, and **Somnath Bhowmick**  
---

## Contact & Support

For questions, issues, or collaboration:
- **Email**: shaswatpathak.qm.researcher@gmail.com and bsomnath@iitk.ac.in 
- **Institution**: Indian Institute of Technology Kanpur, Kanpur, Uttar Pradesh, 208016, India
---

## License

MIT License - See LICENSE file for details

---

## Acknowledgments

- **[Materials Project](https://materialsproject.org)** for DFT-computed materials database
- **[AFLOW Consortium](https://aflow.org)** for high-throughput materials data
- The open-source Python community for excellent scientific computing libraries

---
**Last Updated**: 07-04-2026
