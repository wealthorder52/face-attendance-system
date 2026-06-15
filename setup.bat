@echo off
setlocal enabledelayedexpansion
cd /d %~dp0
echo ================================
echo Face Attendance System Setup
echo ================================

echo Checking for Python 3.10+...
py -3.10 --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo Python 3.10+ not found via the py launcher.
    echo Please install Python 3.10 or later from https://www.python.org/downloads/ and make sure "py" is available.
    pause
    exit /b 1
)

echo Creating virtual environment in %cd%\venv ...
if not exist venv (
    py -3.10 -m venv venv
    if errorlevel 1 (
        echo Failed to create virtual environment.
        pause
        exit /b 1
    )
) else (
    echo Virtual environment already exists.
)

call venv\Scripts\activate.bat
if errorlevel 1 (
    echo Failed to activate the virtual environment.
    pause
    exit /b 1
)

echo Upgrading pip, setuptools, and wheel...
python -m pip install --upgrade pip setuptools wheel
if errorlevel 1 (
    echo Failed to upgrade pip setuptools wheel.
    pause
    exit /b 1
)

echo Installing required Python packages...
python -m pip install -r requirements.txt
if errorlevel 1 (
    echo.
    echo Initial dependency install failed. Trying alternate install for dlib and face_recognition...
    python -m pip install --prefer-binary dlib
    python -m pip install --only-binary :all: face_recognition
    python -m pip install pymysql pillow opencv-python numpy
    if errorlevel 1 (
        echo.
        echo One or more packages failed to install.
        echo Please review the output above and install missing dependencies manually.
        pause
        exit /b 1
    )
)

echo.
echo Setup complete.
echo To run the app:
echo    call venv\Scripts\activate.bat
echo    python main.py
echo.
echo Reminder: edit db_config.py with your MySQL credentials before running the app.
pause
