@echo off
setlocal enabledelayedexpansion
title Hypertrophy Toolbox
color 0A

echo.
echo  ========================================
echo     HYPERTROPHY TOOLBOX - LAUNCHER
echo  ========================================
echo.

:: Change to the script's directory
cd /d "%~dp0"
echo [INFO] Working directory: %cd%
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

for /f "tokens=*" %%i in ('python --version 2^>^&1') do set PYVER=%%i
echo [OK] %PYVER% found
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
if errorlevel 1 (
    echo [ERROR] Failed to activate virtual environment!
    pause
    exit /b 1
)
echo [OK] Virtual environment activated
echo.

:: Check if dependencies are installed (check for Flask)
echo [INFO] Checking dependencies...
venv\Scripts\python.exe -c "import flask" >nul 2>&1
if errorlevel 1 (
    echo [SETUP] Installing dependencies - this may take 1-2 minutes...
    echo.
    venv\Scripts\pip.exe install -r requirements.txt
    if errorlevel 1 (
        echo.
        echo [ERROR] Failed to install dependencies!
        pause
        exit /b 1
    )
    echo.
    echo [OK] Dependencies installed
    echo.
) else (
    echo [OK] Dependencies already installed
    echo.
)

:: Set port
set PORT=5000

echo  ========================================
echo    Starting Hypertrophy Toolbox...
echo  ========================================
echo.
echo    URL: http://127.0.0.1:%PORT%
echo.
echo    The browser will open automatically.
echo    If not, manually open the URL above.
echo.
echo    Press Ctrl+C to stop the server.
echo  ========================================
echo.

:: Open browser after delay (use start command directly)
start "" cmd /c "ping -n 4 127.0.0.1 >nul && start http://127.0.0.1:%PORT%"

:: Run the Flask app using the venv python explicitly
echo [INFO] Starting Flask server...
echo.
venv\Scripts\python.exe app.py

:: If we get here, server stopped
echo.
echo [INFO] Server stopped.
pause
pause
