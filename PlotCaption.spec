# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['plotcaption.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('assets', 'assets'),
        ('prompts', 'prompts')
    ],
    hiddenimports=[],
    hookspath=['hooks'], # The hooks for qwen local files
    hooksconfig={},
    runtime_hooks=[],
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
    name='PlotCaption',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False, # This ensures no console window appears
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/plot_icon.ico', # <-- Here's our app icon!
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='PlotCaption',
)