# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['d:\\易码\\示例\\打包缓存文件夹\\_启动器_易码生成软件.py'],
    pathex=[],
    binaries=[],
    datas=[('C:\\Users\\llvk\\AppData\\Local\\Temp\\_易码源码编译缓冲.ym', '.'), ('d:\\易码\\示例\\yima', 'yima')],
    hiddenimports=['turtle', 'tkinter', 'tkinter.messagebox'],
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
    name='_启动器_易码生成软件',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
