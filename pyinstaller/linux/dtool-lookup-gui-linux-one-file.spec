# -*- mode: python ; coding: utf-8 -*-
from glob import glob
import os
from PyInstaller.utils.hooks import collect_entry_point, copy_metadata, collect_submodules

root_dir = os.path.abspath(os.curdir)
block_cipher = None

# storage brokers and their entrypoints need the following special treatment,
# as they won't be discovered by pyinstaller's default tracing mechanisms
dtool_hidden_imports = ['dtool_http', 'dtool_smb', 'dtool_s3', 'dtool_symlink']
dtool_hidden_imports_datas = []
for module in dtool_hidden_imports:
    dtool_hidden_imports_datas.extend(copy_metadata(module, recursive=True))

dtool_storage_brokers_datas, dtool_storage_brokers_hidden_imports = collect_entry_point("dtool.storage_brokers")

# gi.overrides contains pure-Python wrappers that add type_register, GObjectMeta,
# etc. to gi.repository.GObject (and equivalents for Gtk, Gio, GLib, Gdk, ...).
# When PyInstaller's GI hook subprocess fails (GIRepository namespace unavailable
# in the headless build environment), these overrides are not auto-collected.
# Explicitly collect them so GObject.type_register and similar APIs work at runtime.
gi_overrides_hidden_imports = collect_submodules('gi.overrides')

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
    'GLibUnix-2.0',
    'GModule-2.0',
    'GObject-2.0',
    'Gio-2.0',
    'GioUnix-2.0',
    'Gdk-3.0',
    'GdkX11-3.0',
    'GdkPixbuf-2.0',
    'GdkPixdata-2.0',
    'Pango-1.0',
    'PangoCairo-1.0',
    'PangoFT2-1.0',
    'PangoFc-1.0',
    'PangoOT-1.0',
    'PangoXft-1.0',
    'cairo-1.0',
    'GtkSource-4',
    'freetype2-2.0',
    'HarfBuzz-0.0',
    'Atk-1.0',
    'fontconfig-2.0',
    'xlib-2.0',
    'xfixes-4.0',
    'xrandr-1.3',
    'GL-1.0',
    'DBus-1.0',
    'DBusGLib-1.0',
]

# Search standard typelib locations — order matters: Ubuntu 24.04 x86_64 first
TYPELIB_SEARCH_DIRS = [
    '/usr/lib/x86_64-linux-gnu/girepository-1.0',
    '/usr/lib/girepository-1.0',
    '/usr/lib64/girepository-1.0',
    '/usr/local/lib/girepository-1.0',
]

gi_typelib_datas = []
for typelib_name in REQUIRED_TYPELIBS:
    filename = f'{typelib_name}.typelib'
    for search_dir in TYPELIB_SEARCH_DIRS:
        full_path = os.path.join(search_dir, filename)
        if os.path.isfile(full_path):
            gi_typelib_datas.append((full_path, 'gi_typelibs'))
            break

# Icon theme bundling. The crash this fixes: the build-on-ubuntu smoke test aborted
# (SIGABRT, gtkiconhelper.c:495) when GTK could not resolve a themed icon and tried
# to render its built-in image-missing.png fallback. The root cause is NOT a broken
# PNG/libpng stack — a scriptable CI diagnostic (system Python + the bundled libs on
# LD_LIBRARY_PATH) confirmed GdkPixbuf reports png in get_formats() and decodes PNG
# correctly even in the bundle-mix. The real problem is that no icon theme is bundled
# (PyInstaller's GI hook, which would collect the Adwaita theme requested in
# hooksconfig below, is skipped because GIRepository introspection is unavailable in
# the headless build env). With no icon theme on disk, every themed-icon lookup fails
# and GTK falls into the image-missing fallback path, which asserts and aborts in the
# headless/no-theme environment.
#
# Fix: explicitly bundle the Adwaita + hicolor icon themes into share/icons/. The
# runtime hook pyi_rth_glib.py already prepends {_MEIPASS}/share to XDG_DATA_DIRS, so
# GTK finds them at $XDG_DATA_DIRS/icons and resolves icons normally — the
# image-missing fallback is never triggered.
#
# We do NOT bundle libgdk-pixbuf-2.0.so or libpng16/libjpeg: the system
# libgdk-pixbuf runs fine against the bundled GLib stack (verified by the diagnostic
# above), and its built-in PNG/JPEG loaders suffice on Ubuntu 24.04.
_pixbuf_loaders_datas = []
_pixbuf_binaries = []

_icon_theme_datas = []
for _theme in ('Adwaita', 'hicolor'):
    _theme_dir = os.path.join('/usr/share/icons', _theme)
    if os.path.isdir(_theme_dir):
        _icon_theme_datas += Tree(_theme_dir, prefix=os.path.join('share', 'icons', _theme))
print(f'[spec] bundling icon themes: {sorted({d.split(os.sep)[2] for d, _s, _t in _icon_theme_datas})}'
      if _icon_theme_datas else '[spec] WARNING: no icon themes found to bundle')

hooks_path = [os.path.join(root_dir, 'pyinstaller/hooks')]

runtime_hooks = [
    os.path.join(root_dir, 'pyinstaller/rthooks/pyi_rth_jinja2.py'),
    os.path.join(root_dir, 'pyinstaller/rthooks/pyi_rth_glib.py'),
    # NOTE: do NOT add pyi_rth_gdkpixbuf here. PyInstaller ships its own hook
    # that sets GDK_PIXBUF_MODULE_FILE. When no loaders.cache is bundled, it
    # points to a nonexistent path → GdkPixbuf falls back to built-in PNG/JPEG.
    # Adding our own hook that creates the file breaks this fallback.
]

a = Analysis(
    [os.path.join(root_dir, 'dtool_lookup_gui', 'launcher.py')],
    pathex=[],
    binaries=[*_pixbuf_binaries],
    datas=[
        *additional_datas,
        *dtool_storage_brokers_datas,
        *dtool_hidden_imports_datas,
        *gi_typelib_datas,
        *_pixbuf_loaders_datas,
    ],
    hiddenimports=[
        *dtool_hidden_imports,
        *dtool_storage_brokers_hidden_imports,
        *other_hidden_imports,
        *gi_overrides_hidden_imports,
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
# Tree() yields 3-tuple TOC entries (dest, src, typecode); append to a.datas
# directly rather than passing through Analysis(datas=...), which expects 2-tuples.
a.datas += _icon_theme_datas

# TEMP EXPERIMENT (revert if it doesn't help): drop the bundled GLib + libpng stack
# so the frozen app loads the *system* ones, matching the working system-Python case.
_EXCLUDE_PREFIXES = ('libglib-2.0', 'libgobject-2.0', 'libgio-2.0',
                     'libgmodule-2.0', 'libpng16')
_before = len(a.binaries)
a.binaries = [b for b in a.binaries
              if not os.path.basename(b[0]).startswith(_EXCLUDE_PREFIXES)]
print(f'[spec] excluded {_before - len(a.binaries)} glib/png binaries from bundle')

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
