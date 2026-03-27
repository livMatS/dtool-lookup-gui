"""Overwrite all installed copies of dtool_cli/cli.py with the vendored fix.

Run as: python pyinstaller/vendored/override_dtool_cli.py
"""
import pathlib
import shutil
import site
import sys

src = pathlib.Path(__file__).parent / "dtool_cli_cli.py"
assert src.is_file(), f"Vendored source not found: {src}"

candidates = set()
for base in sys.path + site.getsitepackages():
    c = pathlib.Path(base) / "dtool_cli" / "cli.py"
    if c.is_file():
        candidates.add(c)

if not candidates:
    print("ERROR: dtool_cli/cli.py not found on sys.path", file=sys.stderr)
    sys.exit(1)

for dst in sorted(candidates):
    shutil.copy2(src, dst)
    print(f"Overwrote {dst}")
    pycache = dst.parent / "__pycache__"
    for pyc in pycache.glob(f"{dst.stem}.cpython-*.pyc"):
        pyc.unlink()
        print(f"Removed {pyc}")
