@echo off
ECHO =================================================================
ECHO PLOTCaption CPU Installer
ECHO =================================================================
ECHO This will create a Python virtual environment in a 'venv' folder.
ECHO.
PAUSE

ECHO --- Step 1: Creating Python virtual environment...
python -m venv venv
IF %ERRORLEVEL% NEQ 0 (
    ECHO Error: Could not create the virtual environment. Is Python installed and in your PATH?
    PAUSE
    EXIT /B 1
)

CALL venv\Scripts\activate.bat

ECHO --- Step 2: Uninstalling any old PyTorch versions...
pip uninstall torch torchvision torchaudio -y

ECHO --- Step 3: Installing CPU-version of PyTorch...
pip install torch torchvision torchaudio

ECHO --- Step 4: Installing all other dependencies from requirements.txt...
pip install -r requirements.txt

CALL venv\Scripts\deactivate.bat

ECHO.
ECHO =================================================================
ECHO Installation Complete! To run the app, use run_app.bat
ECHO =================================================================
PAUSE