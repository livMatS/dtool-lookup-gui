# -*- mode: python ; coding: utf-8 -*-
from glob import glob
from PyInstaller.utils.hooks import collect_entry_point, copy_metadata
import subprocess, glob as _glob

root_dir = os.path.abspath(os.curdir)
block_cipher = None

# --- gdk-pixbuf loaders ---
# Find the loaders directory
_pixbuf_loaders_dir = None
for _candidate in [
    "/usr/lib/x86_64-linux-gnu/gdk-pixbuf-2.0/2.10.0/loaders",
    "/usr/lib/gdk-pixbuf-2.0/2.10.0/loaders",
]:
    if os.path.isdir(_candidate):
        _pixbuf_loaders_dir = _candidate
        break

# Fall back to pkg-config / environment query
if _pixbuf_loaders_dir is None:
    try:
        _pixbuf_loaders_dir = subprocess.check_output(
            ["pkg-config", "--variable=gdk_pixbuf_moduledir", "gdk-pixbuf-2.0"],
            text=True
        ).strip()
    except Exception:
        pass

pixbuf_loaders_datas = []
pixbuf_loaders_cache = []
if _pixbuf_loaders_dir and os.path.isdir(_pixbuf_loaders_dir):
    # Include all .so loader files
    pixbuf_loaders_datas = [
        (so, "gdk_pixbuf_loaders")
        for so in _glob.glob(os.path.join(_pixbuf_loaders_dir, "*.so"))
    ]
    # Generate loaders.cache pointing to bundled paths
    _cache_content_lines = []
    try:
        raw = subprocess.check_output(
            ["gdk-pixbuf-query-loaders"] + [so for so, _ in pixbuf_loaders_datas],
            text=True
        )
        # Rewrite absolute paths to relative bundle paths
        for line in raw.splitlines():
            if line.startswith('"') and _pixbuf_loaders_dir in line:
                so_file = os.path.basename(line.strip().strip('"'))
                line = f'"gdk_pixbuf_loaders/{so_file}"'
            _cache_content_lines.append(line)
    except Exception:
        pass
    if _cache_content_lines:
        import tempfile
        _cache_tmp = tempfile.NamedTemporaryFile(
            mode="w", suffix="loaders.cache", delete=False
        )
        _cache_tmp.write("\n".join(_cache_content_lines) + "\n")
        _cache_tmp.close()
        pixbuf_loaders_cache = [(_cache_tmp.name, "gdk_pixbuf_loaders")]

# storage brokers and their entrypoints need the following special treatment,
# as they won't be discovered by pyinstaller's default tracing mechanisms
dtool_hidden_imports = ['dtool_http', 'dtool_smb', 'dtool_s3', 'dtool_symlink']
dtool_hidden_imports_datas = []
for module in dtool_hidden_imports:
    dtool_hidden_imports_datas.extend(copy_metadata(module, recursive=True))

dtool_storage_brokers_datas, dtool_storage_brokers_hidden_imports = collect_entry_point("dtool.storage_brokers")

other_hidden_imports = ['cairo']

icon_parent_folder_glob_pattern = os.path.join('data', 'icons', '*x*')
icon_parent_folders = list(glob(icon_parent_folder_glob_pattern))
icon_glob_patterns = [os.path.join(icon_parent_folder, '*.xpm') for icon_parent_folder in icon_parent_folders]

# relative to repository root
glob_patterns_to_include =  [
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

hooks_path = [os.path.join(root_dir, 'pyinstaller/hooks')]

runtime_hooks = [
  os.path.join(root_dir, 'pyinstaller/rthooks/pyi_rth_jinja2.py'),
  os.path.join(root_dir, 'pyinstaller/rthooks/pyi_rth_glib.py'),
  os.path.join(root_dir, 'pyinstaller/rthooks/pyi_rth_gdk_pixbuf.py'),
]

a = Analysis(
    [os.path.join(root_dir, 'dtool_lookup_gui', 'launcher.py')],
    pathex=[],
    binaries=[],
    datas=[
        *additional_datas,
        *dtool_storage_brokers_datas,
        *dtool_hidden_imports_datas,
        *pixbuf_loaders_datas,
        *pixbuf_loaders_cache,
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
    [],
    exclude_binaries=True,
    name='dtool-lookup-gui',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='dtool-lookup-gui',
)
