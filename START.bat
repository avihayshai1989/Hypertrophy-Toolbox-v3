@echo off
title Hypertrophy Toolbox
color 0A

echo.
echo  ========================================
echo     HYPERTROPHY TOOLBOX - LAUNCHER
echo  ========================================
echo.

:: Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH!
    echo.
    echo Please install Python from: https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation.
    echo.
    pause
    exit /b 1
)

echo [OK] Python found
echo.

:: Check if virtual environment exists
if not exist "venv" (
    echo [SETUP] Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment!
        pause
        exit /b 1
    )
    echo [OK] Virtual environment created
    echo.
)

:: Activate virtual environment
echo [INFO] Activating virtual environment...
call venv\Scripts\activate.bat

:: Check if dependencies are installed (check for Flask)
python -c "import flask" >nul 2>&1
if errorlevel 1 (
    echo [SETUP] Installing dependencies (this may take a minute)...
    pip install -r requirements.txt --quiet
    if errorlevel 1 (
        echo [ERROR] Failed to install dependencies!
        pause
        exit /b 1
    )
    echo [OK] Dependencies installed
    echo.
)

echo [OK] All dependencies ready
echo.

:: Find available port (default 5000)
set PORT=5000

echo  ========================================
echo    Starting Hypertrophy Toolbox...
echo    
echo    Opening browser in 3 seconds...
echo    URL: http://localhost:%PORT%
echo  ========================================
echo.
echo  Press Ctrl+C to stop the server
echo.

:: Start browser after a delay (in background)
start /b cmd /c "timeout /t 3 /nobreak >nul && start http://localhost:%PORT%"

:: Run the Flask app
python app.py

:: Deactivate when done
call venv\Scripts\deactivate.bat
pause
