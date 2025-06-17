import subprocess
import sys

def check_and_install_dependencies():
    required_packages = [
        "PyQt6",
        "winshell",
        "pypiwin32",
        "mojang"
    ]

    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])

if __name__ == "__main__":
    check_and_install_dependencies()