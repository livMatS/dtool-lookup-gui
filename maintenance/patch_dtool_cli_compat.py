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

OLD_IMPORT = "from pkg_resources import iter_entry_points"

NEW_IMPORT = textwrap.dedent("""\
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

# pretty_version_text() is called at module import time as a default argument
# to @click.version_option. It calls iter_entry_points() and __import__() for
# each storage broker plugin, which can raise exceptions in PyInstaller's
# isolated analysis subprocess (no entry points registered there). When the
# import raises, PyInstaller marks dtool_cli.cli as broken and excludes it.
#
# Fix: wrap the call in a lambda / deferred callable so it is only evaluated
# when the CLI is actually invoked, not at import time.
OLD_VERSION_OPTION = "@click.version_option(message=pretty_version_text())"
NEW_VERSION_OPTION = "@click.version_option(message=pretty_version_text() if not getattr(__import__('sys'), '_MEIPASS', None) else 'dtool (bundled)')"


def patch_one(p: pathlib.Path) -> bool:
    """Patch a single dtool_cli/cli.py file. Returns True if changed."""
    src = p.read_text()
    changed = False

    if OLD_IMPORT in src:
        src = src.replace(OLD_IMPORT, NEW_IMPORT)
        print(f"Patched pkg_resources import in {p}")
        changed = True

    if OLD_VERSION_OPTION in src:
        src = src.replace(OLD_VERSION_OPTION, NEW_VERSION_OPTION)
        print(f"Patched version_option call in {p}")
        changed = True

    if changed:
        p.write_text(src)
        # Remove stale .pyc so Python recompiles from patched source
        pyc_dir = p.parent / "__pycache__"
        for pyc in pyc_dir.glob(f"{p.stem}.cpython-*.pyc"):
            pyc.unlink()
            print(f"Removed {pyc}")

    return changed


def main():
    # Find ALL copies of dtool_cli/cli.py on sys.path and in common toolcache
    # locations. PyInstaller uses its own subprocess that may pick up a
    # different (toolcache) copy of the module if multiple installs exist.
    candidates = set()

    # Primary location via importlib
    spec = importlib.util.find_spec("dtool_cli.cli")
    if spec and spec.origin:
        candidates.add(pathlib.Path(spec.origin))

    # Also search sys.path entries for any additional copies
    import site
    for base in sys.path + site.getsitepackages():
        candidate = pathlib.Path(base) / "dtool_cli" / "cli.py"
        if candidate.is_file():
            candidates.add(candidate)

    if not candidates:
        print("dtool_cli not found anywhere on sys.path, skipping patch", file=sys.stderr)
        return

    for p in sorted(candidates):
        patch_one(p)


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
