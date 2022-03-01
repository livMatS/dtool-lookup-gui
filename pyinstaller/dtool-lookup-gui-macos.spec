# -*- mode: python ; coding: utf-8 -*-

root_dir = os.path.abspath(os.curdir)
block_cipher = None

other_hidden_imports = ['cairo']

# relative to repository root
glob_patterns_to_include =  [
    'README.rst', 'LICENSE.md',
    'dtool_lookup_gui/gschemas.compiled',
    'dtool_lookup_gui/views/*.ui',
    'dtool_lookup_gui/widgets/*.ui',
]

additional_datas = [
    (os.path.join(root_dir, rel_path),
     os.path.join(os.curdir, os.path.dirname(rel_path))) for rel_path in glob_patterns_to_include
]

hooks_path = [os.path.join(root_dir, 'pyinstaller/hooks')]

runtime_hooks = [
  os.path.join(root_dir, 'pyinstaller/rthooks/pyi_rth_jinja2.py'),
  os.path.join(root_dir, 'pyinstaller/rthooks/pyi_rth_glib.py')
]

a = Analysis(
             [os.path.join(root_dir, 'dtool_lookup_gui', 'launcher.py')],
             pathex=[],
             binaries=[],
             datas=[
                 *additional_datas,
             ],
             hiddenimports=[*other_hidden_imports],
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
             runtime_hooks=[*runtime_hooks],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)

exe = EXE(pyz,
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
          target_arch=None,
          codesign_identity=None,
          entitlements_file=None )
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas, 
               strip=False,
               upx=True,
               upx_exclude=[],
               name='dtool-lookup-gui')
