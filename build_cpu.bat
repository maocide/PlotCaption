@echo off
echo ===================================
echo   Starting PlotCaption CPU Build
echo ===================================

REM --- Clean up old build files ---
echo.
echo [1/6] Cleaning up old build directories...
if exist build rd /s /q build
if exist dist rd /s /q dist

REM --- Create a fresh virtual environment ---
echo.
echo [2/6] Creating CPU virtual environment...
python -m venv venv-build-cpu

REM --- Activate, Upgrade Pip, and Install Dependencies ---
echo.
echo [3/6] Activating environment and installing CPU dependencies...
call .\\venv-build-cpu\\Scripts\\activate.bat
python.exe -m pip install --upgrade pip
pip install -r requirements-cpu.txt --no-cache-dir
pip install pyinstaller

REM --- Run PyInstaller ---
echo.
echo [4/6] Running PyInstaller to build the application...
python -m PyInstaller PlotCaption.spec

REM --- copy in the install script and launcher ---
echo.
echo Copying batch files
copy /Y .\\deploy\\requirements.txt .\\dist\\PlotCaption\\requirements.txt
copy /Y .\\deploy\\install.bat .\\dist\\PlotCaption\\install.bat
copy /Y .\\deploy\\run_plotcaption.bat .\\dist\\PlotCaption\\run_plotcaption.bat


REM --- Rename the Output Folder ---
echo.
echo [5/6] Renaming output folder...
ren .\\dist\\PlotCaption PlotCaption-Windows-CPU

REM --- Deactivate and Finish ---
echo.
echo [6/6] Cleaning up and deactivating...
call deactivate
echo.
echo ===================================
echo   CPU Build Complete!
echo   Find the package in the 'dist' folder.
echo ===================================
pause