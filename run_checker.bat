@echo off
echo Yosemite Availability Checker
echo ===========================

:: Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Python is not installed or not in PATH.
    echo Please install Python from https://www.python.org/downloads/
    pause
    exit /b 1
)

:: Check if virtual environment exists, create if not
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo Error: Failed to create virtual environment.
        pause
        exit /b 1
    )
)

:: Activate virtual environment and install requirements
echo Activating virtual environment...
call venv\Scripts\activate.bat

echo Installing required packages...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo Error: Failed to install required packages.
    pause
    exit /b 1
)

:: Run the script
echo Starting Yosemite Availability Checker...
echo Press Ctrl+C to stop
echo Logs will be saved to availability_checker.log
echo ----------------------------------------

:: Loop to restart if script exits with error
:loop
python yosemite_availability_checker.py
if %errorlevel% neq 0 (
    echo Script exited with an error. Restarting in 30 seconds...
    timeout /t 30
    goto loop
)

:: Deactivate virtual environment
call venv\Scripts\deactivate.bat

echo Yosemite Availability Checker stopped.
pause 