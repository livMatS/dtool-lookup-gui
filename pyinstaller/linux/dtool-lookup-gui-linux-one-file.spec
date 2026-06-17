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

# GdkPixbuf loaders: do NOT bundle a loaders.cache or external loader .so files.
# On Ubuntu 24.04 the PNG and JPEG loaders are compiled directly into
# libgdk-pixbuf-2.0.so (there is no libpixbufloader-png.so on disk). A
# loaders.cache generated from the system loaders directory therefore lists only
# the *external* formats (svg, tiff, bmp, …) and contains NO png/jpeg entry.
# Bundling such a cache and pointing GDK_PIXBUF_MODULE_FILE at it disables the
# built-in loaders, so the app aborts with SIGABRT the moment GTK loads any PNG
# (e.g. its image-missing.png icon fallback) — which is exactly what broke the
# build-on-ubuntu smoke test.
#
# With no cache bundled, PyInstaller's built-in gdk-pixbuf hook points
# GDK_PIXBUF_MODULE_FILE at a nonexistent path and GdkPixbuf falls back to its
# built-in PNG/JPEG loaders, which is all the GUI needs.
_pixbuf_loaders_datas = []
_pixbuf_binaries = []

# Do NOT explicitly bundle libpng16/libjpeg: they are system libs already linked into
# the system libgdk_pixbuf-2.0.so.0. Bundling them in _MEIPASS causes two copies of
# libpng16 to be loaded (one from _MEIPASS via LD_LIBRARY_PATH, one pulled by
# system libgdk_pixbuf via its RPATH), corrupting libpng's global state and making
# all PNG decoding fail with "Unrecognized image file format".

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
