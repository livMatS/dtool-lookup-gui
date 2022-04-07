# -*- mode: python ; coding: utf-8 -*-
# see https://www.pythonguis.com/tutorials/packaging-pyqt5-applications-pyinstaller-macos-dmg/
from glob import glob

root_dir = os.path.abspath(os.curdir)
block_cipher = None

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
    os.path.join('data','icons', '*.icns'),
    *icon_glob_patterns
]

icns_file = os.path.join(root_dir, 'data', 'icons', 'dtool_logo_small.icns')

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

# see https://pyinstaller.readthedocs.io/en/stable/spec-files.html#spec-file-options-for-a-mac-os-x-bundle
app = BUNDLE(coll,
             name='dtool-lookup-gui.app',
             icon=icns_file,
             bundle_identifier='de.uni-freiburg.dtool-lookup-gui')
