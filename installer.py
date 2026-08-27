# installer.py
import subprocess
import sys
import importlib.util
import os

def install(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

def check_and_install():
    required = ["Pillow", "pygame", "pyyaml", "lupa"]
    for pkg in required:
        try:
            if importlib.util.find_spec(pkg.lower()) is None:
                print(f"Instalowanie {pkg}...")
                install(pkg)
            else:
                print(f"{pkg} już zainstalowane.")
        except Exception as e:
            print(f"Błąd przy sprawdzaniu {pkg}: {e}")

if __name__ == "__main__":
    check_and_install()
    input("Naciśnij Enter, aby zakończyć...")