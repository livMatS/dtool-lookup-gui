"""Patch dtool_cli/cli.py for Python 3.12+ compatibility.

dtool-cli 0.7.1 uses pkg_resources.iter_entry_points which was removed
from the standard library in Python 3.12 (requires setuptools installed
separately). This script replaces the import with an importlib.metadata
shim so dtool-cli works on Python 3.12+.

Run after: pip install dtool-cli==0.7.1
"""
import importlib
import inspect
import sys

SHIM = (
    "try:\n"
    "    from importlib.metadata import entry_points as _entry_points\n"
    "    def iter_entry_points(group, name=None):\n"
    "        eps = _entry_points(group=group)\n"
    "        if name is not None:\n"
    "            eps = [ep for ep in eps if ep.name == name]\n"
    "        return eps\n"
    "except ImportError:\n"
    "    from pkg_resources import iter_entry_points"
)


def patch():
    try:
        import dtool_cli.cli as cli_mod
        cli_path = inspect.getfile(cli_mod)
    except Exception as e:
        print(f"Could not locate dtool_cli.cli: {e}", file=sys.stderr)
        sys.exit(1)

    with open(cli_path, 'r') as f:
        source = f.read()

    old = 'from pkg_resources import iter_entry_points'
    if old not in source:
        print(f"dtool_cli/cli.py already patched or unexpected content: {cli_path}")
        return

    patched = source.replace(old, SHIM)
    # Sanity-check before writing: catch indentation / syntax errors immediately
    try:
        compile(patched, cli_path, 'exec')
    except SyntaxError as e:
        print(f"BUG: patched source has a syntax error: {e}", file=sys.stderr)
        print("Patched content:\n" + patched, file=sys.stderr)
        sys.exit(1)

    with open(cli_path, 'w') as f:
        f.write(patched)

    # Remove cached .pyc so Python picks up the new source
    import py_compile, os
    pyc = cli_path + 'c'
    if os.path.exists(pyc):
        os.remove(pyc)
    # Also remove __pycache__ entry
    import importlib.util
    cache = importlib.util.cache_from_source(cli_path)
    if os.path.exists(cache):
        os.remove(cache)

    print(f"Patched: {cli_path}")


if __name__ == '__main__':
    patch()
