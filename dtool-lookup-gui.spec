# -*- mode: python ; coding: utf-8 -*-


block_cipher = None


a = Analysis(['dtool_lookup_gui/launcher.py'],
             pathex=[
                '/home/jotelha/venv/20220120-dtool-lookup-gui/lib/python3.8/site-packages',
                '/home/jotelha/venv/20220120-dtool-lookup-gui/lib64/python3.8/site-packages'
             ],
             binaries=[],
             datas=[],
             hiddenimports=[],
             hookspath=[],
             hooksconfig={},
             runtime_hooks=[],
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
