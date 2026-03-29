"""Patch dtool_cli/cli.py for Python 3.12+ compatibility.

dtool-cli 0.7.1 uses pkg_resources.iter_entry_points which was removed
from the standard library in Python 3.12 (requires setuptools installed
separately). This script replaces the import with an importlib.metadata
shim so dtool-cli works on Python 3.12+.

Also wraps returned EntryPoints in an _EPCompat class that exposes
.module_name and .attrs, which click-plugins 1.1.1.x accesses via the
old pkg_resources API.

Idempotent: safe to run multiple times even on a cached/pre-patched file.
If the file is found in a broken/partial-patch state (e.g. stale toolcache),
it is reinstated from pip before patching.

Run after: pip install dtool-cli==0.7.1
"""
import importlib.util
import os
import sys

OLD = 'from pkg_resources import iter_entry_points'

SHIM = '''\
try:
    from importlib.metadata import entry_points as _eps

    class _EPCompat:
        """Wrap importlib.metadata EntryPoint to add pkg_resources-style attrs."""
        def __init__(self, ep):
            self._ep = ep
            self.name = ep.name
            self.group = ep.group
            self.value = ep.value
            # pkg_resources compat: module_name / attrs used by click-plugins
            parts = ep.value.split(":")
            self.module_name = parts[0]
            self.attrs = parts[1].split(".") if len(parts) > 1 else []

        def load(self):
            return self._ep.load()

        def __repr__(self):
            return f"_EPCompat({self._ep!r})"

    def iter_entry_points(group, name=None):
        eps = _eps(group=group)
        if name is not None:
            eps = [e for e in eps if e.name == name]
        return [_EPCompat(e) for e in eps]

except ImportError:
    from pkg_resources import iter_entry_points\
'''


def _reinstall_dtool_cli():
    """Force-reinstall dtool-cli to restore a broken cli.py."""
    import subprocess
    print("Reinstalling dtool-cli to restore broken cli.py ...", file=sys.stderr)
    subprocess.check_call([
        sys.executable, '-m', 'pip', 'install', '--force-reinstall',
        '--no-deps', '-q', 'dtool-cli==0.7.1'
    ])


def patch():
    spec = importlib.util.find_spec('dtool_cli.cli')
    if spec is None or not spec.origin:
        print("Could not locate dtool_cli.cli: not found in sys.path", file=sys.stderr)
        sys.exit(1)
    cli_path = spec.origin

    with open(cli_path, 'r') as f:
        source = f.read()

    # Detect broken/partial-patch state: shim start present but OLD absent
    # and the file doesn't compile cleanly — reinstall and re-read.
    try:
        compile(source, cli_path, 'exec')
    except SyntaxError as e:
        print(f"dtool_cli/cli.py has a syntax error ({e}); reinstalling ...", file=sys.stderr)
        _reinstall_dtool_cli()
        # Re-resolve path after reinstall (may have moved in toolcache)
        importlib.invalidate_caches()
        spec = importlib.util.find_spec('dtool_cli.cli')
        cli_path = spec.origin
        with open(cli_path, 'r') as f:
            source = f.read()

    # Already fully patched — nothing to do
    if OLD not in source:
        print(f"dtool_cli/cli.py already patched: {cli_path}")
        return

    # Replace only the first occurrence to stay idempotent
    patched = source.replace(OLD, SHIM, 1)

    with open(cli_path, 'w') as f:
        f.write(patched)

    # Remove stale .pyc caches so Python picks up the new source
    try:
        cache = importlib.util.cache_from_source(cli_path)
        if os.path.exists(cache):
            os.remove(cache)
    except Exception:
        pass

    print(f"Patched: {cli_path}")


if __name__ == '__main__':
    patch()
