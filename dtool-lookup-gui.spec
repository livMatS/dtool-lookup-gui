# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_entry_point

# datafiles_toc = Tree('dtool_lookup_gui', prefix='dtool_lookup_gui', excludes=['.gitignore', '*.py','*.pyc', '*.pyo'])
block_cipher = None

dtool_hidden_imports = ['dtool_smb', 'dtool_s3', 'pysmb']
dtool_storage_brokers_datas, dtool_storage_brokers_hidden_imports = collect_entry_point("dtool.storage_brokers")

additional_datas = [
      ('README.rst', '.'),
      ('LICENSE.md', '.'),
      ('dtool_lookup_gui/gschemas.compiled', 'dtool_lookup_gui'),
      ('dtool_lookup_gui/views/*.ui', 'dtool_lookup_gui/views'),
      ('dtool_lookup_gui/widgets/*.ui', 'dtool_lookup_gui/widgets'),
]

a = Analysis(
    ['dtool_lookup_gui/launcher.py'],
    pathex=['/home/jotelha/venv/20220120-dtool-lookup-gui/lib/python3.8/site-packages'],
    binaries=[],
    datas=[*additional_datas, *dtool_storage_brokers_datas],
    hiddenimports=[*dtool_hidden_imports, *dtool_storage_brokers_hidden_imports],
    hookspath=[],
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
    runtime_hooks=['./pyinstaller/rthooks/pyi_rth_jinja2.py'],
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
