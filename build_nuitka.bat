@echo off
echo ========================================
echo   SRK Boost - Professional Build
echo   Using Nuitka (Best Quality)
echo ========================================
echo.

echo [1/4] Installing dependencies...
pip install -r requirements.txt
pip install nuitka ordered-set zstandard qt-material

echo.
echo [2/4] Building with Nuitka...
python -m nuitka ^
    --standalone ^
    --onefile ^
    --windows-console-mode=disable ^
    --windows-icon-from-ico=assets/icon.ico ^
    --output-filename="SRK Boost" ^
    --output-dir=dist ^
    --enable-plugin=pyqt6 ^
    --include-data-dir=assets=assets ^
    --company-name="SRK Software" ^
    --product-name="SRK Boost" ^
    --file-version=1.0.0.0 ^
    --product-version=1.0.0 ^
    --file-description="PC Performance Optimizer" ^
    --copyright="Copyright 2025 SRK Software" ^
    main.py

echo.
echo [3/4] Build complete!
echo Output: dist\SRK Boost.exe
echo.
pause
