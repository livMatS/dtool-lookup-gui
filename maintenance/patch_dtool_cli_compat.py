"""Patch dtool-cli 0.7.1 for Python 3.12+ compatibility.

dtool-cli 0.7.1 uses `pkg_resources.iter_entry_points` which is not available
in Python 3.12+ (pkg_resources requires setuptools, which no longer ships it).

Additionally, click-plugins 1.1.1.x accesses `ep.module_name` on entry-point
objects, which is a pkg_resources-only attribute absent from
importlib.metadata.EntryPoint.

This script patches the installed dtool_cli/cli.py to replace the
pkg_resources import with an importlib.metadata shim whose wrapper class
exposes `.module_name` and `.attrs` for backward compatibility with
click-plugins.

Safe to run multiple times (idempotent).
"""

import importlib.util
import pathlib
import sys
import textwrap

OLD = "from pkg_resources import iter_entry_points"

NEW = textwrap.dedent("""\
    try:
        from importlib.metadata import entry_points as _eps

        class _EPCompat:
            \"\"\"importlib.metadata EntryPoint wrapper with pkg_resources compat attrs.\"\"\"
            def __init__(self, ep):
                self._ep = ep
                self.name = ep.name
                self.group = ep.group
                self.value = ep.value
                parts = ep.value.split(":")
                self.module_name = parts[0]
                self.attrs = parts[1].split(".") if len(parts) > 1 else []

            def load(self):
                return self._ep.load()

            def __repr__(self):
                return repr(self._ep)

        def iter_entry_points(group, name=None):
            eps = _eps(group=group)
            if name is not None:
                eps = [e for e in eps if e.name == name]
            return [_EPCompat(e) for e in eps]

    except ImportError:
        from pkg_resources import iter_entry_points
""")


def main():
    spec = importlib.util.find_spec("dtool_cli.cli")
    if spec is None:
        print("dtool_cli not found, skipping patch", file=sys.stderr)
        return

    p = pathlib.Path(spec.origin)
    src = p.read_text()

    if OLD not in src:
        print(f"{p}: pattern not found - already patched or different version, skipping")
        return

    p.write_text(src.replace(OLD, NEW))
    print(f"Patched {p}")


def clear_pyc(module_name):
    """Remove .pyc bytecode so patched source is used by all subprocesses."""
    spec = importlib.util.find_spec(module_name)
    if spec and spec.origin:
        pyc_dir = pathlib.Path(spec.origin).parent / "__pycache__"
        for pyc in pyc_dir.glob(f"{pathlib.Path(spec.origin).stem}.cpython-*.pyc"):
            pyc.unlink()
            print(f"Removed {pyc}")


if __name__ == "__main__":
    main()
    clear_pyc("dtool_cli.cli")
