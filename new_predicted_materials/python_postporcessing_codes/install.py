#!/usr/bin/env python3
"""
install.py  –  Set up all dependencies for:
    • cv_comparison_pub.py
    • plot_phonon_publication.py

Usage:
    python install.py

What it does:
    1. Checks the Python version (3.9+ required).
    2. Upgrades pip to the latest version.
    3. Installs every package in requirements.txt.
    4. Verifies each import works after installation.
    5. Prints a clear pass / fail summary.
"""

import sys
import subprocess
import importlib
from pathlib import Path

# ── Minimum Python version ────────────────────────────────────────────────────
MIN_PYTHON = (3, 9)

# ── Package list: (pip_name, import_name, human_label) ───────────────────────
PACKAGES = [
    ("numpy",    "numpy",      "NumPy"),
    ("scipy",    "scipy",      "SciPy"),
    ("matplotlib", "matplotlib", "Matplotlib"),
    ("PyYAML",   "yaml",       "PyYAML"),
    ("openpyxl", "openpyxl",   "openpyxl"),
    ("Pillow",   "PIL",        "Pillow (TIFF support)"),
    ("phonopy",  "phonopy",    "Phonopy"),
]

REQ_FILE = Path(__file__).parent / "requirements.txt"

# ─────────────────────────────────────────────────────────────────────────────

def banner(text: str, char: str = "─") -> None:
    width = 62
    print(f"\n{char * width}")
    print(f"  {text}")
    print(f"{char * width}")


def run(cmd: list[str]) -> int:
    """Run a subprocess command, streaming output live."""
    proc = subprocess.run(cmd)
    return proc.returncode


def check_python() -> None:
    ver = sys.version_info[:2]
    if ver < MIN_PYTHON:
        print(
            f"\n  ✗  Python {'.'.join(map(str, MIN_PYTHON))}+ is required.\n"
            f"     You are running Python {'.'.join(map(str, ver))}.\n"
            "     Please upgrade Python and try again."
        )
        sys.exit(1)
    print(f"  ✓  Python {sys.version.split()[0]}  (≥ {'.'.join(map(str, MIN_PYTHON))} required)")


def upgrade_pip() -> None:
    print("\n  Upgrading pip …")
    run([sys.executable, "-m", "pip", "install", "--upgrade", "pip", "-q"])
    print("  ✓  pip up to date")


def install_requirements() -> None:
    if REQ_FILE.exists():
        print(f"\n  Installing from {REQ_FILE.name} …\n")
        rc = run([
            sys.executable, "-m", "pip", "install",
            "-r", str(REQ_FILE),
        ])
    else:
        # Fallback: install individual packages
        print(f"\n  {REQ_FILE.name} not found — installing packages individually …\n")
        pip_names = [p[0] for p in PACKAGES]
        rc = run([sys.executable, "-m", "pip", "install"] + pip_names)

    if rc != 0:
        print("\n  ✗  pip exited with an error (see output above).")
        sys.exit(rc)


def verify_imports() -> None:
    banner("Import verification")
    passed, failed = [], []

    for pip_name, import_name, label in PACKAGES:
        try:
            mod = importlib.import_module(import_name)
            ver = getattr(mod, "__version__", "unknown")
            print(f"  ✓  {label:<30}  {ver}")
            passed.append(label)
        except ImportError as exc:
            print(f"  ✗  {label:<30}  FAILED  ({exc})")
            failed.append(label)

    banner("Summary", char="═")
    print(f"  Passed : {len(passed)} / {len(PACKAGES)}")
    if failed:
        print(f"  Failed : {', '.join(failed)}")
        print("\n  Some packages did not import correctly.")
        print("  Try running:  pip install <package_name>  manually.")
        sys.exit(1)
    else:
        print("\n  All dependencies installed and verified.")
        print("  You are ready to run:")
        print("      python cv_comparison_pub.py")
        print("      python plot_phonon_publication.py")


# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    banner("Dependency installer", char="═")
    check_python()
    upgrade_pip()
    install_requirements()
    verify_imports()
    print()


if __name__ == "__main__":
    main()
