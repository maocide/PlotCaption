@echo off
echo ===================================
echo   Starting PlotCaption GPU Build
echo ===================================

REM --- Clean up old build files ---
echo.
echo [1/6] Cleaning up old build directories...
if exist build rd /s /q build
if exist dist rd /s /q dist

REM --- Create a fresh virtual environment ---
echo.
echo [2/6] Creating GPU virtual environment...
python -m venv venv-build-gpu

REM --- Activate, Upgrade Pip, and Install Dependencies ---
echo.
echo [3/6] Activating environment and installing GPU dependencies...
call .\\venv-build-gpu\\Scripts\\activate.bat
python.exe -m pip install --upgrade pip
pip install -r requirements-gpu.txt --no-cache-dir

REM --- Run PyInstaller ---
echo.
echo [4/6] Running PyInstaller to build the application...
python -m PyInstaller PlotCaption.spec

REM --- Rename the Output Folder ---
echo.
echo [5/6] Renaming output folder...
ren .\\dist\\PlotCaption PlotCaption-Windows-GPU

REM --- Deactivate and Finish ---
echo.
echo [6/6] Cleaning up and deactivating...
call deactivate
echo.
echo ===================================
echo   GPU Build Complete!
echo   Find the package in the 'dist' folder.
echo ===================================
pause