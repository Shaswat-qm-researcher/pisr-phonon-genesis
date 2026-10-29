"""
Environment Setup Script for PLS Feature Selection

Compatible with:
- Google Colab
- Jupyter Notebook/Lab
- Anaconda Navigator
- Visual Studio Code
- PyCharm
- Command Line/Terminal
- Any Python environment

Automatically detects platform and sets up appropriate environment
for running .ipynb files.

REQUIREMENTS:
- Python 3.12+

Any issues with code contact at:
- Lead Author: Shaswat Pathak
- Institution: Universiti Sains Malaysia, in collaboration with IIT Kanpur
- Email: shaswatpathak.qm.researcher@gmail.com

Date of last update: 08-12-2025
"""

import subprocess
import sys
import os
import platform
from pathlib import Path

# Color codes (safe for all terminals)
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
CYAN = "\033[96m"
RESET = "\033[0m"

# Detect if running in special environments
def detect_environment():
    """Detect the current Python environment"""
    env_info = {
        'is_colab': False,
        'is_jupyter': False,
        'is_conda': False,
        'is_vscode': False,
        'platform': platform.system()
    }
    
    # Check for Google Colab
    try:
        import google.colab
        env_info['is_colab'] = True
        return env_info
    except ImportError:
        pass
    
    # Check for Jupyter
    try:
        from IPython import get_ipython
        if get_ipython() is not None:
            env_info['is_jupyter'] = True
    except ImportError:
        pass
    
    # Check for Conda
    env_info['is_conda'] = os.path.exists(os.path.join(sys.prefix, 'conda-meta'))
    
    # Check for VS Code
    env_info['is_vscode'] = 'VSCODE_PID' in os.environ or 'TERM_PROGRAM' in os.environ and os.environ['TERM_PROGRAM'] == 'vscode'
    
    return env_info

def print_header():
    """Print script header"""
    print("=" * 80)
    print(f"{CYAN}Universal PLSR Environment Setup Script{RESET}")
    print("=" * 80)

def run_command(cmd, description="", silent=False):
    """Run shell command with error handling"""
    if description and not silent:
        print(f"\n{BLUE}ℹ {description}...{RESET}")
    
    try:
        result = subprocess.run(
            cmd, 
            shell=True, 
            check=True, 
            capture_output=True, 
            text=True,
            timeout=300  # 5 minute timeout
        )
        if not silent:
            print(f"{GREEN}✓ Success{RESET}")
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        if not silent:
            print(f"{RED}✗ Failed: {e.stderr[:200]}{RESET}")
        return False, e.stderr
    except subprocess.TimeoutExpired:
        if not silent:
            print(f"{RED}✗ Timeout{RESET}")
        return False, "Command timed out"

def install_in_colab():
    """Install packages in Google Colab"""
    print(f"\n{YELLOW}Detected: Google Colab{RESET}")
    print(f"{GREEN}✓ Colab comes with Jupyter pre-installed!{RESET}\n")
    
    packages = [
        "numpy==2.0.1",
        "pandas==2.2.3",
        "scipy==1.14.1",
        "scikit-learn==1.5.2",
        "matplotlib==3.9.2",
        "openpyxl==3.1.2",
    ]
    
    print(f"{CYAN}Installing required packages...{RESET}")
    for pkg in packages:
        pkg_name = pkg.split('==')[0]
        success, _ = run_command(f"pip install -q {pkg}", f"Installing {pkg_name}")
        if not success:
            print(f"{YELLOW}⚠ {pkg_name} installation failed, trying without version constraint{RESET}")
            run_command(f"pip install -q {pkg_name}", f"Installing {pkg_name}")
    
    print(f"\n{GREEN}✓ All packages installed in Colab!{RESET}")
    print(f"{CYAN}You can now run .ipynb files directly in Colab!{RESET}")

def install_in_jupyter():
    """Install packages in existing Jupyter environment"""
    print(f"\n{YELLOW}Detected: Jupyter Notebook/Lab{RESET}")
    
    packages = [
        "numpy==2.0.1",
        "pandas==2.2.3",
        "scipy==1.14.1",
        "scikit-learn==1.5.2",
        "matplotlib==3.9.2",
        "openpyxl==3.1.2",
    ]
    
    print(f"{CYAN}Installing packages in current kernel...{RESET}")
    for pkg in packages:
        pkg_name = pkg.split('==')[0]
        success, _ = run_command(
            f"{sys.executable} -m pip install {pkg}",
            f"Installing {pkg_name}"
        )
    
    print(f"\n{GREEN}✓ Packages installed! Restart kernel to use.{RESET}")

def setup_jupyter_kernel(env_name, env_path, env_type="conda"):
    """Setup Jupyter kernel for the environment"""
    print(f"\n{CYAN}Setting up Jupyter kernel...{RESET}")
    
    if env_type == "conda":
        cmd = f"conda run -n {env_name} python -m ipykernel install --user --name {env_name} --display-name 'Python ({env_name})'"
    else:
        # Use the actual python path from the environment
        if sys.platform == "win32":
            python_path = os.path.join(env_path, "Scripts", "python.exe")
        else:
            python_path = os.path.join(env_path, "bin", "python")
        
        # Convert to absolute path
        python_path = os.path.abspath(python_path)
        cmd = f'"{python_path}" -m ipykernel install --user --name {env_name} --display-name "Python ({env_name})"'
    
    success, _ = run_command(cmd, "Registering Jupyter kernel")
    
    if success:
        print(f"\n{GREEN}✓ Jupyter kernel '{env_name}' installed!{RESET}")
        print(f"{CYAN}You can now select this kernel in Jupyter/VS Code{RESET}")
    else:
        print(f"\n{YELLOW}⚠ Kernel registration failed, but environment is ready{RESET}")
        print(f"{YELLOW}You can manually register it later if needed{RESET}")
    
    return success

def setup_conda_environment():
    """Create conda environment with Jupyter support"""
    print(f"\n{YELLOW}Setting up Conda Environment{RESET}")
    
    env_name = input(f"{CYAN}Enter environment name [default: plsr_env]: {RESET}").strip()
    if not env_name:
        env_name = "plsr_env"
    
    python_version = input(f"{CYAN}Python version [default: 3.12]: {RESET}").strip()
    if not python_version:
        python_version = "3.12"
    
    # Create environment
    success, _ = run_command(
        f"conda create -n {env_name} python={python_version} -y",
        f"Creating conda environment '{env_name}'"
    )
    
    if not success:
        return None
    
    # Install packages
    packages = [
        "numpy=2.0.1",
        "pandas=2.2.3",
        "scipy=1.14.1",
        "scikit-learn=1.5.2",
        "matplotlib=3.9.2",
        "openpyxl=3.1.2",
        "jupyter",
        "ipykernel",
        "notebook",
        "jupyterlab"
    ]
    
    print(f"\n{CYAN}Installing packages...{RESET}")
    for pkg in packages:
        pkg_name = pkg.split('=')[0]
        run_command(
            f"conda install -n {env_name} {pkg} -y",
            f"Installing {pkg_name}"
        )
    
    # Setup Jupyter kernel
    setup_jupyter_kernel(env_name, None, "conda")
    
    print(f"\n{GREEN}✓ Conda environment '{env_name}' ready!{RESET}")
    print(f"\n{CYAN}To activate and use:{RESET}")
    print(f"  conda activate {env_name}")
    print(f"  jupyter notebook  # or jupyter lab")
    print(f"\n{CYAN}In Jupyter/VS Code:{RESET}")
    print(f"  Select kernel: 'Python ({env_name})'")
    
    return env_name

def setup_venv_environment():
    """Create venv with Jupyter support"""
    print(f"\n{YELLOW}Setting up Virtual Environment{RESET}")
    
    env_name = input(f"{CYAN}Enter environment name [default: plsr_venv]: {RESET}").strip()
    if not env_name:
        env_name = "plsr_venv"
    
    # Get absolute path for the environment
    env_path = os.path.abspath(env_name)
    
    # Create venv
    success, _ = run_command(
        f'"{sys.executable}" -m venv "{env_path}"',
        f"Creating virtual environment '{env_name}'"
    )
    
    if not success:
        print(f"{RED}✗ Failed to create virtual environment{RESET}")
        return None
    
    # Determine paths based on the actual environment name/path
    if sys.platform == "win32":
        pip_path = os.path.join(env_path, "Scripts", "pip.exe")
        python_path = os.path.join(env_path, "Scripts", "python.exe")
        activate_cmd = os.path.join(env_path, "Scripts", "activate")
    else:
        pip_path = os.path.join(env_path, "bin", "pip")
        python_path = os.path.join(env_path, "bin", "python")
        activate_cmd = f"source {os.path.join(env_path, 'bin', 'activate')}"
    
    # Verify paths exist
    if not os.path.exists(python_path):
        print(f"{RED}✗ Python executable not found at {python_path}{RESET}")
        return None
    
    print(f"{GREEN}✓ Environment created at: {env_path}{RESET}")
    
    # Upgrade pip
    run_command(f'"{pip_path}" install --upgrade pip', "Upgrading pip")
    
    # Install packages
    packages = [
        "numpy==2.0.1",
        "pandas==2.2.3",
        "scipy==1.14.1",
        "scikit-learn==1.5.2",
        "matplotlib==3.9.2",
        "openpyxl==3.1.2",
        "jupyter",
        "jupyterlab",
        "notebook",
        "ipykernel"
    ]
    
    print(f"\n{CYAN}Installing packages...{RESET}")
    for pkg in packages:
        pkg_name = pkg.split('==')[0]
        run_command(f'"{pip_path}" install {pkg}', f"Installing {pkg_name}")
    
    # Setup Jupyter kernel with correct paths
    setup_jupyter_kernel(env_name, env_path, "venv")
    
    print(f"\n{GREEN}✓ Virtual environment '{env_name}' ready!{RESET}")
    print(f"\n{CYAN}To activate and use:{RESET}")
    if sys.platform == "win32":
        print(f"  {activate_cmd}")
    else:
        print(f"  {activate_cmd}")
    print(f"  jupyter notebook  # or jupyter lab")
    print(f"\n{CYAN}In VS Code:{RESET}")
    print(f"  1. Open Command Palette (Ctrl+Shift+P)")
    print(f"  2. Select 'Python: Select Interpreter'")
    print(f"  3. Choose the interpreter from: {env_path}")
    
    return env_name

def install_current_environment():
    """Install packages in current Python environment"""
    print(f"\n{YELLOW}Installing in current environment...{RESET}")
    print(f"{CYAN}Current Python: {sys.executable}{RESET}")
    
    packages = [
        "numpy==2.0.1",
        "pandas==2.2.3",
        "scipy==1.14.1",
        "scikit-learn==1.5.2",
        "matplotlib==3.9.2",
        "openpyxl==3.1.2",
        "jupyter",
        "jupyterlab",
        "notebook",
        "ipykernel"
    ]
    
    for pkg in packages:
        pkg_name = pkg.split('==')[0]
        run_command(
            f'"{sys.executable}" -m pip install {pkg}',
            f"Installing {pkg_name}"
        )
    
    print(f"\n{GREEN}✓ All packages installed!{RESET}")
    print(f"\n{CYAN}To run Jupyter notebooks:{RESET}")
    print(f"  jupyter notebook")
    print(f"  # or")
    print(f"  jupyter lab")

def show_vscode_instructions():
    """Show VS Code specific instructions"""
    print(f"\n{CYAN}VS Code Instructions:{RESET}")
    print("1. Install Python extension (if not installed)")
    print("2. Install Jupyter extension (if not installed)")
    print("3. Open .ipynb file")
    print("4. Click 'Select Kernel' in top-right")
    print("5. Choose your environment")
    print(f"\n{CYAN}Documentation:{RESET}")
    print("   https://code.visualstudio.com/docs/datascience/jupyter-notebooks")

def main():
    print_header()
    
    # Detect environment
    env_info = detect_environment()
    
    print(f"\n{CYAN}Environment Detection:{RESET}")
    print(f"  Platform: {env_info['platform']}")
    print(f"  Google Colab: {'Yes' if env_info['is_colab'] else 'No'}")
    print(f"  Jupyter: {'Yes' if env_info['is_jupyter'] else 'No'}")
    print(f"  Conda: {'Yes' if env_info['is_conda'] else 'No'}")
    print(f"  VS Code: {'Yes' if env_info['is_vscode'] else 'No'}")
    
    # Auto-install for Colab
    if env_info['is_colab']:
        install_in_colab()
        return
    
    # Auto-install for Jupyter
    if env_info['is_jupyter']:
        response = input(f"\n{CYAN}Install in current Jupyter kernel? (y/n): {RESET}").strip().lower()
        if response == 'y':
            install_in_jupyter()
            return
    
    # Manual selection
    print(f"\n{CYAN}Choose setup option:{RESET}")
    print("  1. Create Conda environment (recommended for Anaconda users)")
    print("  2. Create Virtual environment (venv)")
    print("  3. Install in current environment")
    print("  4. Show VS Code setup instructions")
    print("  5. Exit")
    
    choice = input(f"\n{CYAN}Enter choice (1-5): {RESET}").strip()
    
    if choice == "1":
        try:
            subprocess.run(["conda", "--version"], capture_output=True, check=True)
            setup_conda_environment()
        except (subprocess.CalledProcessError, FileNotFoundError):
            print(f"{RED}✗ Conda not found. Install Anaconda/Miniconda first{RESET}")
            print(f"{CYAN}Download: https://www.anaconda.com/download{RESET}")
    
    elif choice == "2":
        setup_venv_environment()
    
    elif choice == "3":
        install_current_environment()
    
    elif choice == "4":
        show_vscode_instructions()
    
    elif choice == "5":
        print("Exiting...")
        sys.exit(0)
    
    else:
        print(f"{RED}Invalid choice{RESET}")
        sys.exit(1)
    
    # Final instructions
    print(f"\n{GREEN}{'=' * 80}{RESET}")
    print(f"{GREEN}✓ Setup Complete!{RESET}")
    print(f"{GREEN}{'=' * 80}{RESET}")
    print(f"\n{CYAN}Quick Reference:{RESET}")
    print(f"  • To run notebooks: jupyter notebook or jupyter lab")
    print(f"  • In VS Code: Install Python + Jupyter extensions")
    print(f"  • In PyCharm: File → Settings → Project Interpreter")
    print(f"  • In Anaconda Navigator: Select your environment")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{YELLOW}⚠ Setup interrupted. Exiting...{RESET}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{RED}✗ Error: {str(e)}{RESET}")
        print(f"{YELLOW}Please report this error with details of your setup.{RESET}")
        sys.exit(1)