import sys
import os
import subprocess
import venv
from pathlib import Path

# Configuration
VENV_DIR_NAME = ".venv"
REQUIREMENTS_FILE = "requirements.txt"
MAIN_MODULE = "Wingman.main"
SRC_DIR = "src"


def get_venv_python_executable(venv_path: Path):
    """Returns the path to the python executable within the venv."""
    if sys.platform == "win32":
        return venv_path / "Scripts" / "python.exe"
    else:
        return venv_path / "bin" / "python"


def is_running_in_venv():
    """Checks if the script is currently running inside a virtual environment."""
    return sys.prefix != sys.base_prefix


def bootstrap():
    """Handles venv creation and dependency installation."""
    root_dir = Path(__file__).parent.resolve()
    venv_path = root_dir / VENV_DIR_NAME
    venv_python = get_venv_python_executable(venv_path)
    req_file = root_dir / REQUIREMENTS_FILE

    # 1. Create venv if it doesn't exist
    if not venv_path.exists():
        print(f"[Wingman] Creating virtual environment in {VENV_DIR_NAME}...")
        venv.create(venv_path, with_pip=True)

    # 2. Check if we are running IN that venv. If not, relaunch.
    # Note: We relaunch even if the venv existed, to ensure we use IT and not system python.
    if not is_running_in_venv():
        print("[Wingman] Switching to virtual environment...")

        # Ensure dependencies are installed before launching
        if req_file.exists():
            print("[Wingman] Checking dependencies...")
            try:
                subprocess.check_call(
                    [str(venv_python), "-m", "pip", "install", "-r", str(req_file)],
                    stdout=subprocess.DEVNULL,  # Hide spam unless it fails
                    stderr=subprocess.STDOUT
                )
            except subprocess.CalledProcessError:
                print("Error installing requirements. Attempting to run anyway...")

        # Relaunch this script using the venv python
        try:
            subprocess.call([str(venv_python), str(root_dir / "run.py")] + sys.argv[1:])
        except KeyboardInterrupt:
            pass
        sys.exit()


def main():
    """The actual application logic."""
    print("[Wingman] Starting application...")

    # Add 'src' to python path so we can find the Wingman package
    root_dir = Path(__file__).parent.resolve()
    src_path = root_dir / SRC_DIR
    sys.path.insert(0, str(src_path))

    # Launch the app
    import runpy
    try:
        runpy.run_module(MAIN_MODULE, run_name="__main__", alter_sys=True)
    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
        input("Press Enter to close...")


if __name__ == "__main__":
    if not is_running_in_venv():
        bootstrap()
    else:
        main()