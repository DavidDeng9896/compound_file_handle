# -*- mode: python ; coding: utf-8 -*-
# PyInstaller：cdxml.text_ai_bridge（无 RDKit）
# 在仓库根目录执行: pyinstaller packaging/text-ai-bridge.spec --noconfirm --distpath dist --workpath build/pyi-text-ai

import os

from PyInstaller.utils.hooks import collect_all

block_cipher = None

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(SPEC)))

datas_httpx, binaries_httpx, hiddenimports_httpx = collect_all('httpx')
datas_jsonschema, binaries_jsonschema, hiddenimports_jsonschema = collect_all('jsonschema')

a = Analysis(
    [os.path.join(ROOT, 'cdxml', 'text_ai_bridge.py')],
    pathex=[ROOT],
    binaries=binaries_httpx + binaries_jsonschema,
    datas=datas_httpx + datas_jsonschema,
    hiddenimports=list(hiddenimports_httpx)
    + list(hiddenimports_jsonschema)
    + ['cdxml', 'cdxml.text_ai', 'cdxml.text_ai.batch', 'cdxml.text_ai.client'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['rdkit'],
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='text-ai-bridge',
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
    name='text-ai-bridge',
)
