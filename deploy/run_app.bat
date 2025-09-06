@echo off
ECHO --- Starting PLOT Captioning ---

:: Check if the virtual environment exists
IF NOT EXIST venv\Scripts\activate.bat (
    ECHO Error: Virtual environment not found!
    ECHO Please run either install_cpu.bat or install_gpu.bat first.
    PAUSE
    EXIT /B 1
)

:: Activate the virtual environment and run the app
CALL venv\Scripts\activate.bat
ECHO Virtual environment activated. Launching application...
python plotcaption.py

ECHO.
ECHO --- Application has been closed. ---

CALL venv\Scripts\deactivate.bat

PAUSE