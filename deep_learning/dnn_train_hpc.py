"""
================================================================================
DEEP NEURAL NETWORK TRAINING SYSTEM — HPC VERSION
================================================================================
Usage:
    python dnn_train_hpc.py                   # uses config.py in same folder
    python dnn_train_hpc.py --gpu             # enable GPU
    python dnn_train_hpc.py --no-cv           # skip 5-fold cross-validation
================================================================================
"""

import os
import sys
import time
import json
import argparse
import warnings
import logging
from pathlib import Path
from typing import Tuple, Dict, List, Optional

# ---------------------------------------------------------------------------
# Matplotlib MUST use non-interactive backend before any other import of it
# ---------------------------------------------------------------------------
import matplotlib
matplotlib.use("Agg")   # <-- critical for HPC (no display)
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from matplotlib.ticker import MaxNLocator, AutoMinorLocator

import numpy as np
import pandas as pd
import seaborn as sns
import joblib

import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers, models, regularizers, callbacks, optimizers

from sklearn.model_selection import train_test_split, GridSearchCV, KFold
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (r2_score, root_mean_squared_error,
                              mean_absolute_error, max_error, make_scorer)
from scikeras.wrappers import KerasRegressor

warnings.filterwarnings("ignore")
sns.set_style("ticks")
plt.rcParams["font.family"] = "sans-serif"

# ============================================================================
# LOGGING  (replaces colored terminal prints — works cleanly in job logs)
# ============================================================================
def setup_logging(log_path: str) -> logging.Logger:
    logger = logging.getLogger("DNN_HPC")
    logger.setLevel(logging.DEBUG)
    fmt = logging.Formatter("%(asctime)s  %(levelname)-8s  %(message)s",
                             datefmt="%Y-%m-%d %H:%M:%S")
    # File handler — always written
    fh = logging.FileHandler(log_path)
    fh.setFormatter(fmt)
    logger.addHandler(fh)
    # Console handler — visible in SLURM .out file
    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(fmt)
    logger.addHandler(ch)
    return logger

log: logging.Logger = None   # set in main()

# ============================================================================
# CONFIG LOADER  — reads config.txt from the same folder as this script
# ============================================================================
def load_config() -> dict:
    """
    Parse config.txt (key = value format) located next to this script.
    Returns the cfg dict used throughout the training pipeline.
    """
    folder   = os.path.dirname(os.path.abspath(__file__)) if "__file__" in dir() else os.getcwd()
    cfg_path = os.path.join(folder, "config_DNN.txt")

    if not os.path.isfile(cfg_path):
        raise FileNotFoundError(f"config_DNN.txt not found in: {folder}")

    raw          = {}
    current_key  = None

    with open(cfg_path, "r", encoding="utf-8") as f:
        for line in f:
            stripped = line.rstrip()
            # Skip blank lines and comments
            if not stripped or stripped.lstrip().startswith("#"):
                current_key = None
                continue
            # Indented continuation line -> append to current key's list
            if stripped[0] in (" ", "\t") and current_key is not None:
                raw[current_key].append(stripped.strip())
                continue
            # Normal  key = value  line
            if "=" in stripped:
                key, _, value = stripped.partition("=")
                key  = key.strip()
                value = value.strip()
                raw[key]    = [value] if value else []
                current_key = key
            else:
                current_key = None

    # -- helpers --
    def _str(k, default=None):
        v = raw.get(k, [])
        return v[0] if v else default

    def _int(k, default=None):
        v = _str(k)
        return int(v) if v is not None else default

    def _float(k, default=None):
        v = _str(k)
        return float(v) if v is not None else default

    def _list_str(k):
        v = _str(k, "")
        return [x.strip() for x in v.split(",") if x.strip()]

    def _tuple_int(k):
        return tuple(int(x) for x in _list_str(k))

    def _multi_tuple(k):
        return [tuple(int(x.strip()) for x in ln.split(",") if x.strip())
                for ln in raw.get(k, []) if ln]

    sheet = _str("sheet_name") or None   # blank value becomes None

    return {
        "data": {
            "file_path":     _str("file_path"),
            "sheet_name":    sheet,
            "drop_columns":  _list_str("drop_columns"),
            "input_columns": _list_str("input_columns"),
            "output_column": _str("output_column"),
            "output_latex":  _str("output_latex"),
        },
        "output": {
            "save_dir":  _str("save_dir"),
            "save_name": _str("save_name"),
        },
        "mode": _str("mode", "manual").lower(),
        "manual_params": {
            "hidden_layers": _tuple_int("hidden_layers"),
            "learning_rate": _float("learning_rate", 0.001),
            "epochs":        _int("epochs",        1000),
            "batch_size":    _int("batch_size",     256),
            "random_state":  _int("random_state",    42),
        },
        "auto_params": {
            "n_jobs":       _int("auto_n_jobs", -1),
            "random_state": _int("auto_random_state", 42),
            "param_grid": {
                "hidden_layers": _multi_tuple("auto_hidden_layers"),
                "learning_rate": [float(x) for x in _list_str("auto_learning_rate")],
                "batch_size":    [int(x)   for x in _list_str("auto_batch_size")],
                "epochs":        [int(x)   for x in _list_str("auto_epochs")],
            },
        },
    }

# ============================================================================
# DATA LOADER
# ============================================================================
class DataLoader:

    @staticmethod
    def load_file(file_path: str, sheet_name=None) -> pd.DataFrame:
        ext = Path(file_path).suffix.lower()
        try:
            if ext == ".csv":
                df = pd.read_csv(file_path)
            elif ext in [".xls", ".xlsx"]:
                df = pd.read_excel(file_path, sheet_name=sheet_name)
            elif ext == ".txt":
                df = pd.read_csv(file_path, delimiter="\t", engine="python")
            else:
                raise ValueError(f"Unsupported format: {ext}")
        except Exception as e:
            log.error(f"Failed to load file: {e}")
            sys.exit(1)

        if df.isnull().values.any():
            log.error("Dataset contains missing values — aborting.")
            sys.exit(1)

        log.info(f"Loaded {file_path}  ({len(df)} rows, {len(df.columns)} columns)")
        return df

    @staticmethod
    def prepare_xy(df: pd.DataFrame, cfg: dict):
        drop_cols = cfg["data"].get("drop_columns", [])
        if drop_cols:
            df = df.drop(columns=drop_cols)
            log.info(f"Dropped columns: {drop_cols}")

        input_cols  = cfg["data"]["input_columns"]
        output_col  = cfg["data"]["output_column"]
        output_latex = cfg["data"].get("output_latex", output_col)

        missing = [c for c in input_cols + [output_col] if c not in df.columns]
        if missing:
            log.error(f"Columns not found in data: {missing}")
            sys.exit(1)

        X = df[input_cols]
        y = df[output_col]
        log.info(f"Input features ({len(input_cols)}): {input_cols}")
        log.info(f"Output column: {output_col}  |  LaTeX label: {output_latex}")
        return X, y, output_latex

# ============================================================================
# DATA PROCESSOR
# ============================================================================
class DataProcessor:

    def __init__(self, test_size: float = 0.30, random_state: int = 42):
        self.test_size    = test_size
        self.random_state = random_state
        self.scaler_X     = StandardScaler()
        self.scaler_y     = StandardScaler()

    @staticmethod
    def determine_test_size(n: int) -> float:
        if n < 20:  return 0.15
        if n < 30:  return 0.20
        if n < 40:  return 0.25
        return 0.30

    def split_and_scale(self, X: np.ndarray, y: np.ndarray):
        X_tr, X_te, y_tr, y_te = train_test_split(
            X, y, test_size=self.test_size, random_state=self.random_state)

        X_tr = self.scaler_X.fit_transform(X_tr)
        X_te = self.scaler_X.transform(X_te)
        y_tr = self.scaler_y.fit_transform(y_tr.reshape(-1, 1))
        y_te = self.scaler_y.transform(y_te.reshape(-1, 1))

        # Full-dataset scaled arrays (for post-hoc CV)
        X_all = self.scaler_X.transform(X)
        y_all = self.scaler_y.transform(y.reshape(-1, 1))
        return X_tr, X_te, y_tr, y_te, X_all, y_all

# ============================================================================
# MODEL BUILDER
# ============================================================================
class DNNBuilder:

    @staticmethod
    def build_model(input_dim: int, hidden_layers: tuple,
                    learning_rate: float = 0.001) -> keras.Model:
        model = models.Sequential()
        model.add(layers.Dense(
            hidden_layers[0], input_shape=(input_dim,),
            kernel_initializer="glorot_uniform",
            kernel_regularizer=regularizers.l2(1e-4)))
        model.add(layers.PReLU())

        for n in hidden_layers[1:]:
            model.add(layers.Dense(
                n, kernel_initializer="glorot_uniform",
                kernel_regularizer=regularizers.l2(1e-4)))
            model.add(layers.PReLU())

        model.add(layers.Dense(1))
        opt = optimizers.AdamW(learning_rate=learning_rate, weight_decay=1e-5)
        model.compile(optimizer=opt, loss="mean_squared_error", metrics=["mae"])
        return model

    @staticmethod
    def count_params(model: keras.Model) -> Tuple[int, Dict]:
        total, breakdown = 0, {}
        for i, layer in enumerate(model.layers):
            if not (hasattr(layer, "trainable_weights") and layer.trainable_weights):
                continue
            lp = sum(int(tf.size(w).numpy()) for w in layer.trainable_weights)
            total += lp
            if isinstance(layer, tf.keras.layers.Dense):
                ws = layer.trainable_weights[0].shape
                wc = int(ws[0] * ws[1])
                bc = int(layer.trainable_weights[1].shape[0]) if len(layer.trainable_weights) > 1 else 0
                breakdown[f"Layer_{i}_{layer.name}"] = {"weights": wc, "biases": bc, "total": lp}
        return total, breakdown

# ============================================================================
# METRICS
# ============================================================================
class Metrics:
    @staticmethod
    def all(y_true, y_pred) -> Dict[str, float]:
        return {
            "R2":       r2_score(y_true, y_pred),
            "MAE":      mean_absolute_error(y_true, y_pred),
            "RMSE":     root_mean_squared_error(y_true, y_pred),
            "MaxError": max_error(y_true, y_pred),
        }

# ============================================================================
# HYPERPARAMETER TUNING — AUTO (GridSearchCV)
# ============================================================================
def run_grid_search(X_train, y_train, input_dim, cfg) -> Tuple[Dict, object, pd.DataFrame]:
    ap  = cfg["auto_params"]
    pg  = ap["param_grid"]
    rs  = ap.get("random_state", 42)
    nj  = ap.get("n_jobs", -1)

    def create_model(hidden_layers=(128, 64), learning_rate=0.001, input_dim=None):
        hl = hidden_layers if isinstance(hidden_layers, tuple) else (hidden_layers,)
        return DNNBuilder.build_model(input_dim, hl, learning_rate)

    param_grid = {
        "model__hidden_layers": pg["hidden_layers"],
        "model__learning_rate": pg["learning_rate"],
        "batch_size":           pg["batch_size"],
        "epochs":               pg["epochs"],
    }
    scoring = {
        "R2":       make_scorer(r2_score,                 greater_is_better=True),
        "MAE":      make_scorer(mean_absolute_error,      greater_is_better=False),
        "RMSE":     make_scorer(root_mean_squared_error,  greater_is_better=False),
        "MaxError": make_scorer(max_error,                greater_is_better=False),
    }
    wrapper = KerasRegressor(model=create_model, model__input_dim=input_dim, verbose=0)
    grid = GridSearchCV(
        estimator=wrapper, param_grid=param_grid,
        scoring=scoring, refit="R2",
        cv=KFold(n_splits=5, shuffle=True, random_state=rs),
        n_jobs=nj, verbose=2, return_train_score=True)

    log.info("Starting GridSearchCV …")
    t0 = time.time()
    grid.fit(X_train, y_train.ravel())
    log.info(f"GridSearchCV done in {time.time()-t0:.1f}s  |  best R²={grid.best_score_:.5f}")

    cv_results = pd.DataFrame(grid.cv_results_)
    err_cols = [c for c in cv_results.columns if any(x in c for x in ["MAE","RMSE","MaxError"])]
    cv_results[err_cols] = cv_results[err_cols].abs()

    best = {
        "hidden_layers": grid.best_params_["model__hidden_layers"],
        "learning_rate": grid.best_params_["model__learning_rate"],
        "epochs":        grid.best_params_["epochs"],
        "batch_size":    grid.best_params_["batch_size"],
        "random_state":  rs,
    }
    log.info(f"Best params: {best}")
    return best, grid, cv_results

# ============================================================================
# PLOT DATA STORE
# ============================================================================
class PlotDataStore:

    @staticmethod
    def save(save_dir, save_name,
             y_train_actual, y_train_pred, y_test_actual, y_test_pred,
             train_loss, val_loss, cv_scores, model_info, output_latex,
             train_metrics, test_metrics):

        npz_path  = os.path.join(save_dir, f"{save_name}_plot_data.npz")
        json_path = os.path.join(save_dir, f"{save_name}_plot_meta.json")

        np.savez_compressed(
            npz_path,
            y_train_actual=y_train_actual.flatten(),
            y_train_pred=y_train_pred.flatten(),
            y_test_actual=y_test_actual.flatten(),
            y_test_pred=y_test_pred.flatten(),
            train_loss=np.array(train_loss),
            val_loss=np.array(val_loss),
            cv_r2=np.array(cv_scores["R2"]),
            cv_mae=np.array(cv_scores["MAE"]),
            cv_rmse=np.array(cv_scores["RMSE"]),
            cv_maxerr=np.array(cv_scores["MaxError"]),
        )

        def _to_serializable(v):
            if isinstance(v, tuple):
                return list(v)
            if isinstance(v, np.integer):
                return int(v)
            if isinstance(v, np.floating):
                return float(v)
            return v

        meta = {
            "output_latex": output_latex,
            "model_info":   {k: _to_serializable(v) for k, v in model_info.items()},
            "train_metrics": {k: float(v) for k, v in train_metrics.items()},
            "test_metrics":  {k: float(v) for k, v in test_metrics.items()},
        }
        with open(json_path, "w") as f:
            json.dump(meta, f, indent=4)

        log.info(f"Plot data saved: {npz_path}")

    @staticmethod
    def load(save_dir, save_name):
        npz_path  = os.path.join(save_dir, f"{save_name}_plot_data.npz")
        json_path = os.path.join(save_dir, f"{save_name}_plot_meta.json")

        if not os.path.exists(npz_path) or not os.path.exists(json_path):
            return None, None

        arrays = dict(np.load(npz_path, allow_pickle=False))
        with open(json_path, "r") as f:
            meta = json.load(f)

        if "hidden_layers" in meta.get("model_info", {}):
            meta["model_info"]["hidden_layers"] = tuple(meta["model_info"]["hidden_layers"])

        log.info(f"Plot data loaded from: {npz_path}")
        return arrays, meta

    @staticmethod
    def regenerate_figures(save_dir, save_name):
        """Regenerate all figures without retraining."""
        arrays, meta = PlotDataStore.load(save_dir, save_name)
        if arrays is None:
            log.error("No plot data found. Train the model first.")
            return

        output_latex  = meta["output_latex"]
        model_info    = meta["model_info"]
        train_metrics = meta["train_metrics"]
        test_metrics  = meta["test_metrics"]

        y_train_actual = arrays["y_train_actual"].reshape(-1, 1)
        y_train_pred   = arrays["y_train_pred"].reshape(-1, 1)
        y_test_actual  = arrays["y_test_actual"].reshape(-1, 1)
        y_test_pred    = arrays["y_test_pred"].reshape(-1, 1)
        cv_scores = {
            "R2":       arrays["cv_r2"].tolist(),
            "MAE":      arrays["cv_mae"].tolist(),
            "RMSE":     arrays["cv_rmse"].tolist(),
            "MaxError": arrays["cv_maxerr"].tolist(),
        }

        Visualizer.actual_vs_predicted(
            y_train_actual, y_train_pred, y_test_actual, y_test_pred,
            model_info, output_latex, save_dir, save_name,
            train_m=train_metrics, test_m=test_metrics,
        )
        Visualizer.training_history(
            arrays["train_loss"].tolist(),
            arrays["val_loss"].tolist(),
            output_latex, save_dir, save_name
        )
        Visualizer.cv_results(cv_scores, output_latex, save_dir, save_name)
        log.info("All figures regenerated.")

# ============================================================================
# VISUALIZER  (all plt.show() removed; saves PNG + PDF only)
# ============================================================================
class Visualizer:

    @staticmethod
    def actual_vs_predicted(y_train_act, y_train_pred,
                             y_test_act,  y_test_pred,
                             model_info, output_latex,
                             save_dir, save_name,
                             train_m, test_m):
        fig, ax = plt.subplots(figsize=(8, 5))

        ax.scatter(y_train_act.flatten(), y_train_pred.flatten(),
                   s=80, alpha=0.6, c="red", marker="s",
                   edgecolors="none", label="Training", zorder=2)
        ax.scatter(y_test_act.flatten(), y_test_pred.flatten(),
                   s=80, alpha=0.7, c="#00008B", marker="s",
                   edgecolors="none", label="Test", zorder=3)

        mn = min(y_train_act.min(), y_test_act.min(),
                 y_train_pred.min(), y_test_pred.min())
        mx = max(y_train_act.max(), y_test_act.max(),
                 y_train_pred.max(), y_test_pred.max())
        pad = 0.05 * (mx - mn)
        ax.plot([mn-pad, mx+pad], [mn-pad, mx+pad],
                "k--", lw=2, alpha=0.8, label="Ideal Fit", zorder=1)

        all_act  = np.concatenate([y_train_act.flatten(), y_test_act.flatten()])
        all_pred = np.concatenate([y_train_pred.flatten(), y_test_pred.flatten()])
        max_idx  = np.argmax(np.abs(all_act - all_pred))
        ax.scatter(all_act[max_idx], all_pred[max_idx],
                   s=200, c="blue", marker="x", linewidths=3,
                   edgecolors="black", label="Max Error", zorder=5)

        ax.set_xlim(mn-pad, mx+pad); ax.set_ylim(mn-pad, mx+pad)
        ax.xaxis.set_major_locator(MaxNLocator(nbins=5))
        ax.yaxis.set_major_locator(MaxNLocator(nbins=5))
        ax.tick_params(axis="both", which="major", direction="in",
                       length=8, labelsize=20, top=True, right=True)
        ax.tick_params(axis="both", which="minor", direction="in",
                       length=3, top=True, right=True)
        ax.minorticks_on()
        ax.xaxis.set_minor_locator(AutoMinorLocator(13))
        ax.yaxis.set_minor_locator(AutoMinorLocator(10))

        ax.set_xlabel(fr"Actual {output_latex}", fontsize=24)
        ax.set_ylabel(fr"Predicted {output_latex}", fontsize=24)

        ax.annotate(
            f"$R^2$ (Train): {train_m['R2']:.4f}\n"
            f"$R^2$ (Test):  {test_m['R2']:.4f}\n"
            f"MAE (Train): {train_m['MAE']:.3f}\n"
            f"MAE (Test):  {test_m['MAE']:.3f}\n"
            f"RMSE (Train): {train_m['RMSE']:.3f}\n"
            f"RMSE (Test):  {test_m['RMSE']:.3f}",
            xy=(0.57, 0.37), xycoords="axes fraction",
            fontsize=12.5, ha="left", va="top",
            bbox=dict(boxstyle="round,pad=0.3", facecolor="white",
                      edgecolor="black", alpha=0.8))

        ax.annotate(
            f"Max Error (Train): {train_m['MaxError']:.3f}\n"
            f"Max Error (Test):  {test_m['MaxError']:.3f}",
            xy=(0.053, 0.938), xycoords="axes fraction",
            fontsize=12.5, ha="left", va="top",
            bbox=dict(boxstyle="round,pad=0.3", facecolor="white",
                      edgecolor="black", alpha=0.8))

        box_text = "\n".join([
            "DNN Model Information", "",
            f"Input Dim: {model_info['input_dim']}",
            f"Total samples: {model_info['n_total']}",
            f"Train: {model_info['n_train']}",
            f"Test: {model_info['n_test']}",
            f"Total layers: {model_info['n_layers']}",
            f"Neurons: {model_info['n_neurons']}",
            f"Parameters: {model_info['params']:,}",
            f"Hidden layers: {model_info['hidden_layers']}",
            f"LR: {model_info['lr']}",
            f"Epochs: {model_info['epochs']}",
            f"Batch: {model_info['batch']}",
        ])
        ax.annotate(box_text, xy=(1.05, 0.5), xycoords="axes fraction",
                    fontsize=12, verticalalignment="center",
                    bbox=dict(boxstyle="round,pad=0.4", edgecolor="black",
                              facecolor="white", alpha=1))

        ax.legend(fontsize=13, frameon=False, loc="upper center",
                  bbox_to_anchor=(0.5, 1.12), ncol=4)
        plt.grid(False)
        plt.tight_layout()
        for fmt in ["png", "pdf"]:
            fig.savefig(os.path.join(save_dir, f"{save_name}_Actual_vs_Predicted.{fmt}"),
                        dpi=600, bbox_inches="tight")
        plt.close(fig)

    @staticmethod
    def training_history(train_loss, val_loss, output_latex, save_dir, save_name):
        fig, ax = plt.subplots(figsize=(14, 5))
        ax.plot(train_loss, "-", color="darkblue", lw=1.5, label="Training")
        if val_loss:
            ax.plot(val_loss, "-", color="black",   lw=1.5, label="Validation")
        ax.set_ylim(-0.01, 0.3)
        ax.set_xlabel("Epoch", fontsize=20, fontweight="bold")
        ax.set_ylabel(fr"Loss {output_latex}", fontsize=20, fontweight="bold")
        for sp in ax.spines.values():
            sp.set_linewidth(1.5); sp.set_color("black")
        ax.minorticks_on()
        ax.tick_params(axis="both", which="major", labelsize=20, direction="in",
                       length=10, width=1.5, top=True, right=True)
        ax.tick_params(axis="both", which="minor", direction="in",
                       length=5, width=1, top=True, right=True)
        ax.xaxis.set_minor_locator(AutoMinorLocator(15))
        ax.yaxis.set_minor_locator(AutoMinorLocator(5))
        ax.legend(fontsize=20, frameon=False)
        plt.grid(False); plt.tight_layout()
        for fmt in ["png", "pdf"]:
            fig.savefig(os.path.join(save_dir, f"{save_name}_Loss_vs_Epoch.{fmt}"),
                        dpi=600, bbox_inches="tight")
        plt.close(fig)

    @staticmethod
    def cv_results(cv_scores, output_latex, save_dir, save_name):
        folds = np.arange(1, 6)
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        configs = [
            (axes[0,0], cv_scores["R2"],       fr"R² Score {output_latex}", "#0343DF"),
            (axes[0,1], cv_scores["MAE"],       fr"MAE {output_latex}",      "#2ca02c"),
            (axes[1,0], cv_scores["RMSE"],      fr"RMSE {output_latex}",     "red"),
            (axes[1,1], cv_scores["MaxError"],  fr"Max Error {output_latex}","mediumslateblue"),
        ]
        for ax, scores, ylabel, color in configs:
            ax.bar(folds, scores, width=0.5, color=color,
                   edgecolor="black", linewidth=1.5, alpha=0.85)
            mean_val = np.mean(scores)
            ax.axhline(mean_val, color="darkred", linestyle="--",
                       linewidth=3, label=f"Mean: {mean_val:.4f}", zorder=10)
            ax.set_xlabel("Fold Number", fontsize=20, fontweight="bold")
            ax.set_ylabel(ylabel, fontsize=20, fontweight="bold")
            mn, mx = np.min(scores), np.max(scores)
            rng = mx - mn
            ax.set_ylim(mn - 0.05*rng, mx + 0.5*rng)
            leg = ax.legend(fontsize=20, frameon=True, loc="best")
            leg.get_frame().set_edgecolor("black")
            leg.get_frame().set_linewidth(1.5)
            ax.set_xticks(folds); ax.set_xticklabels(folds, fontsize=13)
            ax.tick_params(axis="y", labelsize=13)
            for sp in ax.spines.values():
                sp.set_linewidth(1.5); sp.set_color("black")
            ax.minorticks_on()
            ax.tick_params(axis="both", which="major", direction="in",
                           length=8, width=1.5, right=True, labelsize=20)
            ax.tick_params(axis="both", which="minor", direction="in",
                           length=4, width=1.5, right=True)
        plt.tight_layout(); plt.grid(False)
        for fmt in ["png", "pdf"]:
            fig.savefig(os.path.join(save_dir, f"{save_name}_5_Fold_CV_Plot.{fmt}"),
                        dpi=600, bbox_inches="tight")
        plt.close(fig)

    @staticmethod
    def grid_search_plots(cv_results, save_dir, save_name):
        metrics_cfg = [
            ("mean_test_R2",       "R² Score",  True),
            ("mean_test_MAE",      "MAE",        False),
            ("mean_test_RMSE",     "RMSE",       False),
            ("mean_test_MaxError", "Max Error",  False),
        ]
        for col, label, higher in metrics_cfg:
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.plot(cv_results.index + 1, cv_results[col],
                    marker="o", linestyle="-", linewidth=2,
                    markersize=8, markeredgecolor="black", markeredgewidth=1.5,
                    markerfacecolor="royalblue", color="black")
            best_val = cv_results[col].max() if higher else cv_results[col].min()
            best_idx = cv_results[col].idxmax() if higher else cv_results[col].idxmin()
            ax.axhline(best_val, color="red", linestyle="--", linewidth=2,
                       label=f"Best {label}: {best_val:.4f}")
            ax.axvline(best_idx + 1, color="red", linestyle="--", linewidth=2)
            ax.set_xlabel("Grid Search Iteration", fontsize=14)
            ax.set_ylabel(label, fontsize=14)
            ax.legend(fontsize=12)
            plt.grid(False); plt.tight_layout()
            for fmt in ["png", "pdf"]:
                fig.savefig(os.path.join(save_dir,
                    f"{save_name}_{label.replace(' ','_')}.{fmt}"),
                    dpi=600, bbox_inches="tight")
            plt.close(fig)

# ============================================================================
# RESULTS EXPORTER  (identical logic, HPC-safe paths)
# ============================================================================
class ResultsExporter:

    def __init__(self, save_dir, save_name):
        self.save_dir    = save_dir
        self.save_name   = save_name
        self.model_dir   = os.path.join(save_dir, save_name)
        os.makedirs(self.model_dir, exist_ok=True)
        self._xlsx       = os.path.join(save_dir, f"{save_name}_Optimized_DNN_Results.xlsx")

    def _write_sheet(self, df, sheet):
        mode = "a" if os.path.exists(self._xlsx) else "w"
        kw   = {"if_sheet_exists": "replace"} if mode == "a" else {}
        with pd.ExcelWriter(self._xlsx, engine="openpyxl", mode=mode, **kw) as w:
            df.to_excel(w, sheet_name=sheet, index=False)
        log.info(f"Sheet written: {sheet}")

    def save_model_and_scalers(self, model, scaler_X, scaler_y):
        path = os.path.join(self.model_dir, f"{self.save_name}_best_model.keras")
        m = model.model_ if hasattr(model, "model_") else model
        m.save(path)
        joblib.dump(scaler_X, os.path.join(self.model_dir, f"{self.save_name}_scaler_X.joblib"))
        joblib.dump(scaler_y, os.path.join(self.model_dir, f"{self.save_name}_scaler_y.joblib"))
        log.info(f"Model + scalers saved to {self.model_dir}")

    def save_metadata(self, X, y, scaler_X, scaler_y,
                      n_params, best_params, train_m, test_m):
        meta = {
            "input_features":     list(X.columns),
            "output_feature":     y.name,
            "trainable_params":   int(n_params),
            "best_params":        {k: (str(v) if isinstance(v, tuple) else v)
                                   for k, v in best_params.items()},
            "scaler_X_mean":      scaler_X.mean_.tolist(),
            "scaler_X_scale":     scaler_X.scale_.tolist(),
            "scaler_y_mean":      scaler_y.mean_.tolist(),
            "scaler_y_scale":     scaler_y.scale_.tolist(),
            "scaler_X_min":       X.min(axis=0).tolist(),
            "scaler_X_max":       X.max(axis=0).tolist(),
            "scaler_y_min":       float(y.min()),
            "scaler_y_max":       float(y.max()),
            "train_metrics":      {k: float(v) for k, v in train_m.items()},
            "test_metrics":       {k: float(v) for k, v in test_m.items()},
        }
        path = os.path.join(self.model_dir, f"{self.save_name}_metadata.json")
        with open(path, "w") as f:
            json.dump(meta, f, indent=4)
        log.info(f"Metadata saved: {path}")

    def save_predictions(self, y_tr_act, y_tr_pred, y_te_act, y_te_pred):
        self._write_sheet(pd.DataFrame({"Actual_Train":    y_tr_act.flatten(),
                                         "Predicted_Train": y_tr_pred.flatten()}),
                          "Predictions_Train")
        self._write_sheet(pd.DataFrame({"Actual_Test":     y_te_act.flatten(),
                                         "Predicted_Test":  y_te_pred.flatten()}),
                          "Predictions_Test")

    def save_model_details(self, config, arch, param_bd, hp, perf):
        for df, sheet in [(pd.DataFrame(config), "Model_Configuration"),
                          (pd.DataFrame(arch),   "Architecture"),
                          (pd.DataFrame(param_bd),"Parameter_Breakdown"),
                          (pd.DataFrame(hp),      "Hyperparameters"),
                          (pd.DataFrame(perf),    "Performance_Metrics")]:
            self._write_sheet(df, sheet)

    def save_cv_results(self, cv_df):
        self._write_sheet(cv_df, "5_Fold_CV_Results")

    def save_training_history(self, history):
        loss = history.history["loss"]
        vl   = history.history.get("val_loss", [None]*len(loss))
        self._write_sheet(
            pd.DataFrame({"Epoch": range(1, len(loss)+1),
                          "Training_Loss": loss, "Validation_Loss": vl}),
            "Loss_vs_Epoch")

    def save_timing_data(self, timing):
        self._write_sheet(pd.DataFrame(timing), "Timing_Summary")

    def save_grid_search_results(self, cv_results, best_params, best_score):
        path = os.path.join(self.save_dir, f"{self.save_name}_GridSearch.xlsx")
        with pd.ExcelWriter(path, engine="openpyxl", mode="w") as w:
            cv_results.to_excel(w, sheet_name="CV_Results", index=True)
            pd.DataFrame({
                "Parameter": list(best_params.keys()) + ["Best_CV_R2"],
                "Value":     [str(v) for v in best_params.values()] + [f"{best_score:.6f}"]
            }).to_excel(w, sheet_name="Best_Params", index=False)
        log.info(f"GridSearch workbook: {path}")

# ============================================================================
# MAIN
# ============================================================================
def main():
    parser = argparse.ArgumentParser(description="DNN Training — HPC Mode")
    parser.add_argument("--gpu",   action="store_true",
                        help="Allow GPU (default: CPU-only for reproducibility)")
    parser.add_argument("--no-cv", dest="no_cv", action="store_true",
                        help="Skip 5-fold cross-validation")
    args, _ = parser.parse_known_args()  # parse_known_args ignores Jupyter's -f kernel-xxx.json

    # ----- GPU / CPU pinning ------------------------------------------------
    if not args.gpu:
        os.environ["CUDA_VISIBLE_DEVICES"] = ""
        tf.config.set_visible_devices([], "GPU")

    # ----- Load config -------------------------------------------------------
    cfg      = load_config()
    save_dir = cfg["output"]["save_dir"]
    save_name = cfg["output"]["save_name"]
    os.makedirs(save_dir, exist_ok=True)

    # ----- Logging -----------------------------------------------------------
    global log
    log = setup_logging(os.path.join(save_dir, f"{save_name}_training.log"))
    log.info("=" * 70)
    log.info("DNN TRAINING SYSTEM — HPC VERSION")
    log.info(f"Config module: config.py")
    log.info(f"TF version: {tf.__version__}  |  GPU enabled: {args.gpu}")
    log.info("=" * 70)

    timing = {"Operation": [], "Time (seconds)": []}
    t_total = time.time()

    # ----- Load & prepare data -----------------------------------------------
    df = DataLoader.load_file(cfg["data"]["file_path"],
                               cfg["data"].get("sheet_name"))
    X, y, output_latex = DataLoader.prepare_xy(df, cfg)

    n_samples, n_features = X.shape
    if n_features > n_samples:
        log.error(f"More features ({n_features}) than samples ({n_samples}) — aborting.")
        sys.exit(1)

    exporter  = ResultsExporter(save_dir, save_name)
    test_size = DataProcessor.determine_test_size(n_samples)
    log.info(f"Samples: {n_samples}  |  Features: {n_features}  |  Test split: {test_size*100:.0f}%")

    rs = cfg.get("manual_params", {}).get("random_state", 42)
    processor = DataProcessor(test_size=test_size, random_state=rs)
    X_tr, X_te, y_tr, y_te, X_all, y_all = processor.split_and_scale(
        X.values, y.values)

    # ----- Hyperparameters ---------------------------------------------------
    mode = cfg.get("mode", "manual").lower()

    if mode == "manual":
        mp = cfg["manual_params"]
        best_params = {
            "hidden_layers": mp["hidden_layers"],
            "learning_rate": mp["learning_rate"],
            "epochs":        mp["epochs"],
            "batch_size":    mp["batch_size"],
            "random_state":  mp.get("random_state", 42),
        }
        log.info(f"Manual params: {best_params}")

    elif mode == "auto":
        best_params, grid, cv_results = run_grid_search(
            X_tr, y_tr, X_tr.shape[1], cfg)
        exporter.save_grid_search_results(cv_results, best_params, grid.best_score_)
        Visualizer.grid_search_plots(cv_results, save_dir, save_name)
    else:
        log.error(f"Unknown mode '{mode}'. Use 'manual' or 'auto'.")
        sys.exit(1)

    # ----- Train model -------------------------------------------------------
    log.info("Training DNN …")
    t0 = time.time()
    model = DNNBuilder.build_model(X_tr.shape[1],
                                   best_params["hidden_layers"],
                                   best_params["learning_rate"])
    reduce_lr = callbacks.ReduceLROnPlateau(
        monitor="val_loss", factor=0.5, patience=20, min_lr=1e-6)

    history = model.fit(
        X_tr, y_tr,
        validation_data=(X_te, y_te),
        epochs=best_params["epochs"],
        batch_size=best_params["batch_size"],
        callbacks=[reduce_lr],
        verbose=2   # one line per epoch — clean in SLURM logs
    )
    elapsed_train = time.time() - t0
    timing["Operation"].append("Model Training")
    timing["Time (seconds)"].append(elapsed_train)
    log.info(f"Training done in {elapsed_train:.1f}s")

    # ----- Evaluate ----------------------------------------------------------
    t0 = time.time()
    y_tr_pred = model.predict(X_tr, verbose=0)
    timing["Operation"].append("Train Prediction")
    timing["Time (seconds)"].append(time.time()-t0)

    t0 = time.time()
    y_te_pred = model.predict(X_te, verbose=0)
    timing["Operation"].append("Test Prediction")
    timing["Time (seconds)"].append(time.time()-t0)

    y_tr_act  = processor.scaler_y.inverse_transform(y_tr)
    y_tr_pred = processor.scaler_y.inverse_transform(y_tr_pred.reshape(-1,1))
    y_te_act  = processor.scaler_y.inverse_transform(y_te)
    y_te_pred = processor.scaler_y.inverse_transform(y_te_pred.reshape(-1,1))

    train_m = Metrics.all(y_tr_act, y_tr_pred)
    test_m  = Metrics.all(y_te_act,  y_te_pred)

    log.info("=== TRAIN METRICS ===")
    for k, v in train_m.items(): log.info(f"  {k}: {v:.6f}")
    log.info("=== TEST  METRICS ===")
    for k, v in test_m.items():  log.info(f"  {k}: {v:.6f}")

    # ----- Model metadata ----------------------------------------------------
    n_params, param_bd = DNNBuilder.count_params(model)
    log.info(f"Trainable parameters: {n_params:,}")

    n_tr = X_tr.shape[0]; n_te = X_te.shape[0]
    total_layers  = 1 + len(best_params["hidden_layers"]) + 1
    total_neurons = sum(best_params["hidden_layers"])

    model_info = dict(input_dim=n_features, n_total=n_samples,
                      n_train=n_tr, n_test=n_te,
                      n_layers=total_layers, n_neurons=total_neurons,
                      params=n_params, hidden_layers=best_params["hidden_layers"],
                      lr=best_params["learning_rate"],
                      epochs=best_params["epochs"], batch=best_params["batch_size"])

    # ----- Save model & Excel ------------------------------------------------
    exporter.save_model_and_scalers(model, processor.scaler_X, processor.scaler_y)
    exporter.save_metadata(X, y, processor.scaler_X, processor.scaler_y,
                            n_params, best_params, train_m, test_m)
    exporter.save_predictions(y_tr_act, y_tr_pred, y_te_act, y_te_pred)

    config_data = {"Configuration": ["Model Type","Input Dim","Output Dim",
                                      "Total Samples","Train Samples","Test Samples",
                                      "Test Ratio","Random State"],
                   "Values":        ["DNN", n_features, 1, n_samples,
                                     n_tr, n_te, test_size, rs]}
    arch_data   = {"Architecture":  ["Total Layers","Total Neurons","Hidden Config",
                                      "Trainable Params","Activation","Initializer","Regularizer"],
                   "Values":        [total_layers, total_neurons,
                                     str(best_params["hidden_layers"]),
                                     n_params,"PReLU","glorot_uniform","L2(0.0001)"]}
    pbd = {"Layer":[], "Weights":[], "Biases":[], "Total":[]}
    for lname, lp in param_bd.items():
        pbd["Layer"].append(lname); pbd["Weights"].append(lp["weights"])
        pbd["Biases"].append(lp["biases"]); pbd["Total"].append(lp["total"])
    pbd["Layer"].append("TOTAL")
    pbd["Weights"].append(sum(p["weights"] for p in param_bd.values()))
    pbd["Biases"].append(sum(p["biases"]  for p in param_bd.values()))
    pbd["Total"].append(n_params)

    hp_data   = {"Hyperparameter": ["Learning Rate","Optimizer","Weight Decay",
                                     "Epochs","Batch Size","Loss"],
                 "Values":         [best_params["learning_rate"],"AdamW","1e-5",
                                    best_params["epochs"],best_params["batch_size"],"MSE"]}
    perf_data = {"Metric":  ["R²","MAE","RMSE","Max Error","Infer Time (s)"],
                 "Training":[f"{train_m['R2']:.6f}", f"{train_m['MAE']:.6f}",
                              f"{train_m['RMSE']:.6f}", f"{train_m['MaxError']:.6f}",
                              f"{timing['Time (seconds)'][timing['Operation'].index('Train Prediction')]:.6f}"],
                 "Test":    [f"{test_m['R2']:.6f}",  f"{test_m['MAE']:.6f}",
                              f"{test_m['RMSE']:.6f}",  f"{test_m['MaxError']:.6f}",
                              f"{timing['Time (seconds)'][timing['Operation'].index('Test Prediction')]:.6f}"]}

    exporter.save_model_details(config_data, arch_data, pbd, hp_data, perf_data)
    exporter.save_training_history(history)

    # ----- Visualizations ----------------------------------------------------
    log.info("Generating plots …")
    Visualizer.actual_vs_predicted(y_tr_act, y_tr_pred, y_te_act, y_te_pred,
                                    model_info, output_latex,
                                    save_dir, save_name, train_m, test_m)
    Visualizer.training_history(history.history["loss"],
                                 history.history.get("val_loss",[]),
                                 output_latex, save_dir, save_name)

    # ----- 5-Fold CV ---------------------------------------------------------
    if not args.no_cv:
        log.info("Starting 5-fold cross-validation …")
        t0 = time.time()
        kf = KFold(n_splits=5, shuffle=True, random_state=42)
        cv_scores = {"R2":[],"MAE":[],"RMSE":[],"MaxError":[]}

        for fold, (tr_idx, te_idx) in enumerate(kf.split(X_all), 1):
            fm = DNNBuilder.build_model(X_all.shape[1],
                                        best_params["hidden_layers"],
                                        best_params["learning_rate"])
            rlr = callbacks.ReduceLROnPlateau(
                monitor="val_loss", factor=0.5, patience=20, min_lr=1e-6)
            fm.fit(X_all[tr_idx], y_all[tr_idx],
                   validation_data=(X_all[te_idx], y_all[te_idx]),
                   epochs=best_params["epochs"],
                   batch_size=best_params["batch_size"],
                   callbacks=[rlr], verbose=0)
            yp = fm.predict(X_all[te_idx], verbose=0)
            yt_orig = processor.scaler_y.inverse_transform(y_all[te_idx])
            yp_orig = processor.scaler_y.inverse_transform(yp.reshape(-1,1))
            m = Metrics.all(yt_orig, yp_orig)
            for k in cv_scores: cv_scores[k].append(m[k])
            log.info(f"  Fold {fold}: R²={m['R2']:.4f}  MAE={m['MAE']:.4f}  "
                     f"RMSE={m['RMSE']:.4f}  MaxErr={m['MaxError']:.4f}")

        t_cv = time.time() - t0
        timing["Operation"].append("5-Fold CV")
        timing["Time (seconds)"].append(t_cv)
        log.info(f"CV done in {t_cv:.1f}s")
        log.info("=== CV SUMMARY ===")
        for k in cv_scores:
            log.info(f"  {k}: {np.mean(cv_scores[k]):.5f} ± {np.std(cv_scores[k]):.5f}")

        cv_df = pd.DataFrame({"Fold": np.arange(1,6), **cv_scores})
        cv_df.loc["Mean"] = ["Mean"] + [np.mean(cv_scores[k]) for k in ["R2","MAE","RMSE","MaxError"]]
        cv_df.loc["Std"]  = ["Std"]  + [np.std(cv_scores[k])  for k in ["R2","MAE","RMSE","MaxError"]]
        exporter.save_cv_results(cv_df)
        PlotDataStore.save(
            save_dir, save_name,
            y_tr_act, y_tr_pred,
            y_te_act, y_te_pred,
            train_loss=history.history["loss"],
            val_loss=history.history.get("val_loss", []),
            cv_scores=cv_scores,
            model_info=model_info,
            output_latex=output_latex,
            train_metrics=train_m,
            test_metrics=test_m,
        )
        Visualizer.cv_results(cv_scores, output_latex, save_dir, save_name)
    else:
        log.info("CV skipped (--no-cv flag)")

    # ----- Timing & wrap-up --------------------------------------------------
    timing["Operation"].append("Total Runtime")
    timing["Time (seconds)"].append(time.time() - t_total)
    exporter.save_timing_data(timing)

    log.info("=" * 70)
    log.info("ALL DONE")
    log.info(f"Results in: {save_dir}")
    for op, t in zip(timing["Operation"], timing["Time (seconds)"]):
        log.info(f"  {op}: {t:.1f}s")
    log.info("=" * 70)


if __name__ == "__main__":
    main()
