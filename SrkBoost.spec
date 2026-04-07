# -*- mode: python ; coding: utf-8 -*-
# SRK Boost - PyInstaller Spec File
# Build: pyinstaller SrkBoost.spec

import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# Collect qt-material theme files
qt_material_datas = collect_data_files('qt_material')

# Hidden imports (runtime-discovered modules)
hidden_imports = [
    'PyQt6.QtCore',
    'PyQt6.QtGui',
    'PyQt6.QtWidgets',
    'PyQt6.QtCharts',
    'PyQt6.sip',
    'win32api',
    'win32con',
    'win32gui',
    'win32security',
    'pywintypes',
    'wmi',
    'psutil',
    'speedtest',
    'PIL',
    'PIL.Image',
    'qt_material',
]

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('assets/styles.qss', 'assets'),
        ('assets/icon.ico',   'assets'),
        *qt_material_datas,
    ],
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib', 'numpy', 'pandas', 'scipy'],
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
    name='SRK Boost',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,          # No console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/icon.ico',
    uac_admin=True,         # Request admin on launch
    version='version_info.txt',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='SRK Boost',
)
