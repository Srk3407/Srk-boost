# -*- mode: python ; coding: utf-8 -*-
# SRK Boost - PyInstaller Spec (onefile mode)

import sys
from PyInstaller.utils.hooks import collect_data_files

block_cipher = None

try:
    qt_material_datas = collect_data_files('qt_material')
except Exception:
    qt_material_datas = []

hidden_imports = [
    'PyQt6.QtCore',
    'PyQt6.QtGui',
    'PyQt6.QtWidgets',
    'PyQt6.sip',
    'win32api',
    'win32con',
    'win32gui',
    'win32security',
    'pywintypes',
    'wmi',
    'psutil',
    'PIL',
    'PIL.Image',
    'qt_material',
]

a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        ('assets/styles.qss', 'assets'),
        ('assets/logo.png',   'assets'),
        ('assets/icon.ico',   'assets'),
        *qt_material_datas,
    ],
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib', 'numpy', 'pandas', 'scipy', 'PyQt6.QtCharts'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# onefile: everything bundled into single EXE
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='SRK Boost',
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
    icon='assets/icon.ico',
    uac_admin=True,
    version='version_info.txt',
)
