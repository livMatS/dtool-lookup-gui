"""Remove any existing dtool_cli/cli.py before pip install.

Prevents a stale or corrupted toolcache copy from being served.
Run as: python pyinstaller/vendored/preremove_dtool_cli.py
"""
import pathlib
import shutil
import site
import sys

for base in sys.path + site.getsitepackages():
    cli = pathlib.Path(base) / "dtool_cli" / "cli.py"
    if cli.is_file():
        cli.unlink()
        print(f"Pre-removed {cli}")
    pycache = pathlib.Path(base) / "dtool_cli" / "__pycache__"
    if pycache.is_dir():
        shutil.rmtree(pycache, ignore_errors=True)
        print(f"Pre-removed {pycache}")
