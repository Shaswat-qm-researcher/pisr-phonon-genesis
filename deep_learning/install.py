"""
install.py — Install all dependencies for the DNN benchmark.

Tested on:
  Python  : 3.12.12 (Anaconda)
  Platform: Windows

Usage:
  python install.py

Optionally, create a dedicated conda environment first:
  conda create -n dnn_env python=3.12 -y
  conda activate dnn_env
  python install.py
"""

import subprocess
import sys


PACKAGES = [
    "numpy==2.4.4",
    "pandas==2.2.3",
    "matplotlib==3.9.2",
    "seaborn==0.13.2",
    "joblib==1.5.2",
    "tensorflow==2.20.0",
    "keras==3.12.0",
    "scikit-learn==1.5.2",
    "scikeras==0.13.0",
    "openpyxl>=3.1.0",
]


def install(packages: list[str]) -> None:
    pip = [sys.executable, "-m", "pip", "install", "--upgrade"]
    for pkg in packages:
        print(f"\nInstalling: {pkg}")
        result = subprocess.run(pip + [pkg], capture_output=False)
        if result.returncode != 0:
            print(f"  WARNING: installation of '{pkg}' may have failed "
                  f"(exit code {result.returncode}). Check output above.")


if __name__ == "__main__":
    print(f"Python: {sys.version}")
    print("=" * 60)
    install(PACKAGES)
    print("\n" + "=" * 60)
    print("Installation complete. Verify with:")
    print("  python -c \"import tensorflow as tf; print(tf.__version__)\"")
