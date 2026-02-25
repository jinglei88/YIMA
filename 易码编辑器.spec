# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['易码编辑器.py'],
    pathex=[],
    binaries=[],
    datas=[('易码打包工具.py', '.'), ('yima', 'yima'), ('yima/logo.ico', '.'), ('文档', '文档'), ('示例', '示例'), ('VERSION', '.')],
    hiddenimports=['易码打包工具'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='易码编辑器',
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
    icon=['yima\\logo.ico'],
)
