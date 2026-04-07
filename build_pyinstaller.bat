@echo off
echo Building with PyInstaller (fallback)...
pip install pyinstaller qt-material
pyinstaller --onefile --windowed ^
    --name "SRK Boost" ^
    --add-data "assets;assets" ^
    --hidden-import qt_material ^
    --hidden-import PyQt6 ^
    --hidden-import psutil ^
    main.py
echo Done! Check dist folder.
pause
