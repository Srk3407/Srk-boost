# SRK Boost — Build Guide

## Requirements (Windows)
```
pip install pyinstaller
pip install -r requirements.txt
```
Inno Setup 6: https://jrsoftware.org/isdl.php

---

## Step 1 — Build EXE (PyInstaller)

```cmd
cd srk-boost
pyinstaller SrkBoost.spec --clean
```

Output: `dist/SRK Boost/SRK Boost.exe`

---

## Step 2 — Create Installer (Inno Setup)

1. Install Inno Setup 6
2. Open `installer/SrkBoost_Setup.iss`
3. Click **Build → Compile** (or run):
```cmd
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer\SrkBoost_Setup.iss
```

Output: `release/SrkBoost-v1.5.1-Setup.exe`

---

## Folder structure after build
```
srk-boost/
├── dist/
│   └── SRK Boost/          ← PyInstaller output (all DLLs + exe)
├── release/
│   └── SrkBoost-v1.5.1-Setup.exe   ← Final installer to share
├── installer/
│   └── SrkBoost_Setup.iss  ← Inno Setup script
├── SrkBoost.spec            ← PyInstaller spec
└── version_info.txt         ← EXE version metadata
```

---

## Notes
- PyInstaller must run on **Windows** (cannot cross-compile from Linux)
- The `.spec` requests `uac_admin=True` — setup will ask for admin on first launch
- Inno Setup adds Start Menu + optional Desktop shortcut + optional startup entry
- Uninstaller is automatically created
