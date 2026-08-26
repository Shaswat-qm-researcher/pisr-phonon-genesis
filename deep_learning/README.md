# Deep Learning — DNN Benchmark

Feed-forward deep neural networks (DNNs) trained on PLS-reduced AFLOW features to benchmark SISSO descriptors for three phonon-related properties: Debye temperature $\Theta_D$, specific heat $C_p$ (300 K), and lattice thermal conductivity $\kappa$ (300 K). Implements exhaustive grid search, 5-fold cross-validation, and full convergence diagnostics.

---
> **Note:** This is a sub-repository of the main project:  
> **[pisr-phonon-genesis](https://github.com/Shaswat-qm-researcher/pisr-phonon-genesis/)**

---

## Table of Contents
1. [Repository Structure](#repository-structure)
2. [Workflow](#workflow)
3. [Files](#files)
4. [Outputs](#outputs)
5. [Performance](#performance)
6. [Requirements](#requirements)
7. [Citation](#citation)

---

## Repository Structure

```
📁 deep_learning/
├── 📓 DNN_interactive.ipynb       # Interactive notebook (local use)
├── 🐍 dnn_train_hpc.py            # Non-interactive script (HPC/batch use)
├── ⚙️  config.txt                 # Hyperparameter and I/O configuration (HPC/batch use)
├── 📋 requirements.txt            # Library requirements to run DNN code
├── 🔧 install.py                  # Python script to install libraries
└── 📁 Results/
    ├── 📁 Debye_temp/
    │   ├── 📁 Debye_temp_optimized_model/     # .keras, scalers, metadata
    │   ├── 📄 Debye_temp_Actual_vs_Predicted.pdf
    │   ├── 📄 Debye_temp_Loss_vs_Epoch.pdf
    │   ├── 📄 Debye_temp_5_Fold_CV_Plot.pdf
    │   └── 📊 Debye_temp_optimized_results.xlsx
    ├── 📁 Specific_heat/          # Same structure
    └── 📁 Lattice_therm_cond/     # Same structure
```
 
---

## Workflow

**Architecture:** Pyramidal fully-connected layers → PReLU activations → scalar linear output. Glorot uniform initialization, L2 regularization ($\lambda = 10^{-4}$), AdamW optimizer with adaptive LR scheduling (halved on 20-epoch validation stagnation, min $10^{-6}$). Inputs and outputs independently standardized (zero mean, unit variance); scalers fit on training data only.

**Data split:** 70:30 train/test, `random_state=42`.

**Grid search space** (396 configurations, 5-fold CV, scored by $R^2$):

| Hyperparameter | Values |
|---|---|
| Hidden layers | 11 configs: single layers 8–256; multi-layer up to 1024–512–256 |
| Learning rate | $10^{-4}$, $10^{-3}$, $10^{-2}$ |
| Batch size | 32, 64, 128, 256 |
| Epochs | 1000, 1500, 2000 |

Post-selection: best config retrained on full training set; post-hoc 5-fold CV on complete dataset.

---

## Files

| File | Purpose |
|---|---|
| `DNN_interactive.ipynb` | Step-by-step interactive session with prompted I/O — suitable for local Jupyter |
| `dnn_train_hpc.py` | Reads `config.txt`; no user prompts — suitable for HPC job submission |
| `config.txt` | Set `mode = manual` or `mode = auto` (grid search); configure data paths, columns, and hyperparameters |

**`config.txt` key options:**
```ini
mode = manual        # manual | auto
hidden_layers = 512, 256, 128
learning_rate = 0.001
epochs        = 1000
batch_size    = 256
```

---

## Outputs

Each property folder contains:

| File | Description |
|---|---|
| `*_best_model.keras` | Saved Keras model for feature predictions |
| `*_scaler_X.joblib` / `*_scaler_y.joblib` | Fitted StandardScalers for inference |
| `*_metadata.json` | Architecture, hyperparameters, training config |
| `*_Actual_vs_Predicted.pdf` | Parity plot (train + test) |
| `*_Loss_vs_Epoch.pdf` | Training/validation MSE convergence |
| `*_5_Fold_CV_Plot.pdf` | Cross-validation $R^2$ per fold |
| `*_optimized_results.xlsx` | Full metrics: $R^2$, MAE, RMSE, max error |

---

## Performance

Optimized architectures (5077 samples, 3553 train / 1524 test):

| Property | Architecture | Parameters | LR / Epochs / Batch | Test $R^2$ |
|---|---|---|---|---|
| $\Theta_D$ | 512–256–128 | $1.7 \times 10^5$ | $10^{-3}$, 1000, 256 | > 0.99 |
| $C_p$ | 256–128 | $3.5 \times 10^4$ | $10^{-4}$, 1000, 128 | > 0.99 |
| $\kappa$ | 128–64 | $0.9 \times 10^4$ | $10^{-2}$, 1000, 128 | ~0.96 |

### **Indicative runtimes for $\Theta_D$** (hardware-dependent)
#### **Tested on:**
- **CPU:** AMD Ryzen 7 7735HS with Radeon Graphics with Base speed: 3.20 GHz, Cores: 8, Logical processors: 16.
- **Memory:** 16.0 GB DDR5, Speed: 4800 MT/s.

| Stage | Time |
|---|---|
| Model training | ~335 s |
| 5-fold CV | ~1,554 s |
| Grid search (396 configs) | ~280,843 s (~78 h) |

> Grid search is computationally expensive. Use `auto_n_jobs = -1` and allocate sufficient CPUs on HPC.

---

## Requirements

See [`requirements.txt`](requirements.txt) and [`install.py`](install.py).

**Core stack:** Python 3.12, TensorFlow 2.20, Keras 3.12, Scikit-learn 1.5, SciKeras 0.13.

---
## Citation

>If you use this data, please cite:

---
