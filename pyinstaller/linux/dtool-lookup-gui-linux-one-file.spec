# -*- mode: python ; coding: utf-8 -*-
from glob import glob
import os
import pathlib
import textwrap
from PyInstaller.utils.hooks import collect_entry_point, copy_metadata

root_dir = os.path.abspath(os.curdir)
block_cipher = None

# ---------------------------------------------------------------------------
# Patch dtool_cli/cli.py for Python 3.12+ compatibility.
#
# dtool-cli 0.7.1 uses `pkg_resources.iter_entry_points` (unavailable in
# Python 3.12+) and calls `pretty_version_text()` eagerly as a default
# argument, which invokes __import__() on storage broker packages. In
# PyInstaller's analysis environment that causes ImportError, making
# PyInstaller silently exclude dtool_cli.cli from the bundle.
#
# We patch the file HERE inside the spec, in the same Python process that
# drives PyInstaller's analysis, so there are no caching or subprocess
# timing issues.
# ---------------------------------------------------------------------------
_OLD_IMPORT = "from pkg_resources import iter_entry_points"
_NEW_IMPORT = textwrap.dedent("""\
    try:
        from importlib.metadata import entry_points as _eps

        class _EPCompat:
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

        def iter_entry_points(group, name=None):
            eps = _eps(group=group)
            if name is not None:
                eps = [e for e in eps if e.name == name]
            return [_EPCompat(e) for e in eps]

    except ImportError:
        from pkg_resources import iter_entry_points
""")
_OLD_VERSION_OPT = "@click.version_option(message=pretty_version_text())"
_NEW_VERSION_OPT = "@click.version_option(message=pretty_version_text() if not getattr(__import__('sys'), '_MEIPASS', None) else 'dtool')"

import importlib.util as _ilu
import site as _site
_cli_candidates = set()
_spec = _ilu.find_spec("dtool_cli.cli")
if _spec and _spec.origin:
    _cli_candidates.add(pathlib.Path(_spec.origin))
for _base in __import__('sys').path + _site.getsitepackages():
    _c = pathlib.Path(_base) / "dtool_cli" / "cli.py"
    if _c.is_file():
        _cli_candidates.add(_c)

for _p in sorted(_cli_candidates):
    _src = _p.read_text()
    _changed = False
    if _OLD_IMPORT in _src:
        _src = _src.replace(_OLD_IMPORT, _NEW_IMPORT)
        _changed = True
        print(f"[spec] Patched pkg_resources import in {_p}")
    if _OLD_VERSION_OPT in _src:
        _src = _src.replace(_OLD_VERSION_OPT, _NEW_VERSION_OPT)
        _changed = True
        print(f"[spec] Patched version_option in {_p}")
    if _changed:
        _p.write_text(_src)
        for _pyc in (_p.parent / "__pycache__").glob(f"{_p.stem}.cpython-*.pyc"):
            _pyc.unlink()
            print(f"[spec] Removed stale {_pyc}")
        # Force Python to re-import from the patched source
        import sys as _sys
        for _mod in list(_sys.modules.keys()):
            if _mod.startswith("dtool_cli"):
                del _sys.modules[_mod]
# ---------------------------------------------------------------------------

# storage brokers and their entrypoints need the following special treatment,
# as they won't be discovered by pyinstaller's default tracing mechanisms
dtool_hidden_imports = ['dtool_http', 'dtool_smb', 'dtool_s3', 'dtool_symlink']
dtool_hidden_imports_datas = []
for module in dtool_hidden_imports:
    dtool_hidden_imports_datas.extend(copy_metadata(module, recursive=True))

dtool_storage_brokers_datas, dtool_storage_brokers_hidden_imports = collect_entry_point("dtool.storage_brokers")

other_hidden_imports = ['cairo', 'dtool_cli', 'dtool_cli.cli', 'dtool_create', 'click_plugins']

icon_parent_folder_glob_pattern = os.path.join('data', 'icons', '*x*')
icon_parent_folders = list(glob(icon_parent_folder_glob_pattern))
icon_glob_patterns = [os.path.join(icon_parent_folder, '*.xpm') for icon_parent_folder in icon_parent_folders]

# relative to repository root
glob_patterns_to_include = [
    'README.rst', 'LICENSE.md',
    os.path.join('dtool_lookup_gui', 'gschemas.compiled'),
    os.path.join('dtool_lookup_gui', 'views', '*.ui'),
    os.path.join('dtool_lookup_gui', 'widgets', '*.ui'),
    *icon_glob_patterns
]

additional_datas = [
    (os.path.join(root_dir, rel_path),
     os.path.join(os.curdir, os.path.dirname(rel_path))) for rel_path in glob_patterns_to_include
]

# Explicitly bundle GObject Introspection typelib files.
# PyInstaller's GI hook attempts to introspect modules at build time via a
# child process. If the build environment has no display or the GI typelib path
# is not set, the hook emits "Failed to query GI module X" warnings and skips
# bundling the typelibs — producing a defunct bundle that crashes with
# "gi.RepositoryError: Typelib file for namespace 'Gtk' version '3.0' not found".
#
# We explicitly collect the required typelibs here as a reliable fallback.
# The runtime hook (pyi_rth_glib.py) sets GI_TYPELIB_PATH to the bundle's
# gi_typelibs/ directory so gi.repository can find them at startup.
REQUIRED_TYPELIBS = [
    'Gtk-3.0',
    'GLib-2.0',
    'GObject-2.0',
    'Gio-2.0',
    'Gdk-3.0',
    'GdkX11-3.0',
    'GdkPixbuf-2.0',
    'Pango-1.0',
    'PangoCairo-1.0',
    'cairo-1.0',
    'GtkSource-4',
    'freetype2-2.0',
    'HarfBuzz-0.0',
    'GdkPixdata-2.0',
    'Graphene-1.0',
    'xlib-2.0',
    'xfixes-4.0',
]

# Search standard typelib locations used by Ubuntu 24.04
TYPELIB_SEARCH_DIRS = [
    '/usr/lib/x86_64-linux-gnu/girepository-1.0',
    '/usr/lib/girepository-1.0',
    '/usr/lib64/girepository-1.0',
]

gi_typelib_datas = []
for typelib_name in REQUIRED_TYPELIBS:
    filename = f'{typelib_name}.typelib'
    for search_dir in TYPELIB_SEARCH_DIRS:
        full_path = os.path.join(search_dir, filename)
        if os.path.isfile(full_path):
            gi_typelib_datas.append((full_path, 'gi_typelibs'))
            break

hooks_path = [os.path.join(root_dir, 'pyinstaller/hooks')]

runtime_hooks = [
    os.path.join(root_dir, 'pyinstaller/rthooks/pyi_rth_jinja2.py'),
    os.path.join(root_dir, 'pyinstaller/rthooks/pyi_rth_glib.py'),
]

a = Analysis(
    [os.path.join(root_dir, 'dtool_lookup_gui', 'launcher.py')],
    pathex=[],
    binaries=[],
    datas=[
        *additional_datas,
        *dtool_storage_brokers_datas,
        *dtool_hidden_imports_datas,
        *gi_typelib_datas,
    ],
    hiddenimports=[
        *dtool_hidden_imports,
        *dtool_storage_brokers_hidden_imports,
        *other_hidden_imports,
    ],
    hookspath=[*hooks_path],
    hooksconfig={
        "gi": {
            "icons": ["Adwaita"],
            "themes": ["Adwaita"],
            "languages": ["en_US"],
            "module-versions": {
                "Gtk": "3.0",
                "GtkSource": "4"
            }
        }
    },
    runtime_hooks=runtime_hooks,
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='dtool-lookup-gui',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
