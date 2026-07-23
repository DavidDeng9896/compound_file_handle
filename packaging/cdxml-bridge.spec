# -*- mode: python ; coding: utf-8 -*-
# PyInstaller：将 cdxml.bridge + cdxml.parser + RDKit 打成 onedir 可执行文件。
# 在仓库根目录执行: pyinstaller packaging/cdxml-bridge.spec --noconfirm --distpath dist --workpath build/pyi

import os

from PyInstaller.utils.hooks import collect_all

block_cipher = None

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(SPEC)))

datas_rdkit, binaries_rdkit, hiddenimports_rdkit = collect_all('rdkit')

a = Analysis(
    [os.path.join(ROOT, 'cdxml', 'bridge.py')],
    pathex=[ROOT],
    binaries=binaries_rdkit,
    datas=datas_rdkit,
    hiddenimports=list(hiddenimports_rdkit) + ['rdkit', 'rdkit.Chem', 'cdxml', 'cdxml.parser'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='cdxml-bridge',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
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
    upx=False,
    upx_exclude=[],
    name='cdxml-bridge',
)
