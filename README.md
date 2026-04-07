# SRK Boost - PC Performance Optimizer

Professional Windows PC optimization tool with a premium dark purple UI.

## Features

- Real-time CPU/RAM/GPU monitoring
- FPS Boost with selectable tweaks
- System Scanner
- Junk Cleaner
- Game Mode
- Driver Manager
- Startup Manager
- Internet Speed Test
- TR/EN language support
- Restore points before changes

## Build

### Generate Icon (first time only)

```
pip install Pillow
python generate_icon.py
```

### Option 1: Nuitka (Recommended - Best Performance)

Produces a single, fast native executable. Slower build but best quality output.

```
pip install nuitka
build_nuitka.bat
```

Output: `dist\SRK Boost.exe`

### Option 2: PyInstaller (Faster build)

Faster to build, slightly larger output.

```
build_pyinstaller.bat
```

Output: `dist\SRK Boost.exe`

### Option 3: Installer Package (Inno Setup)

After building the exe with either method above, compile `setup.iss` with [Inno Setup](https://jrsoftware.org/isinfo.php) to create a proper installer.

Output: `Output\SRK_Boost_Setup.exe`

## Requirements

- Windows 10/11
- Python 3.10+
- Run as Administrator for full features (registry, service management)

## Dependencies

| Package | Purpose |
|---------|---------|
| PyQt6 | GUI framework |
| qt-material | Premium dark theme |
| psutil | System monitoring |
| pywin32 | Windows API |
| wmi | Hardware info |
| speedtest-cli | Internet speed test |
| Pillow | Icon generation |

## Theme

Uses **qt-material** `dark_purple.xml` as the base theme, with custom QSS overrides for:
- Sidebar gradient
- Nav button active/hover states
- Card backgrounds
- Custom button variants (primary, cyan, boost, danger, success)

## License

Copyright 2025 SRK Software
