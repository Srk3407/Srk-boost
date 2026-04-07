@echo off
echo ========================================
echo   SRK Boost - Build Script
echo ========================================
echo.

echo Installing dependencies...
pip install -r requirements.txt
pip install pyinstaller

echo.
echo Building executable...
pyinstaller --onefile --windowed ^
    --name "SRK Boost" ^
    --add-data "assets;assets" ^
    --add-data "ui;ui" ^
    --add-data "core;core" ^
    --hidden-import PyQt6 ^
    --hidden-import psutil ^
    main.py

echo.
echo Build complete! Check the 'dist' folder.
echo Run: dist\SRK Boost.exe
pause
