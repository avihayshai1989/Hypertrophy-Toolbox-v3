@echo off
setlocal enabledelayedexpansion
title Building Hypertrophy Toolbox Executable
color 0E

echo.
echo  ========================================
echo    BUILDING STANDALONE EXECUTABLE
echo  ========================================
echo.

:: Change to script directory
cd /d "%~dp0"
echo [INFO] Working directory: %cd%
echo.

:: Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH!
    pause
    exit /b 1
)

for /f "tokens=*" %%i in ('python --version 2^>^&1') do set PYVER=%%i
echo [OK] %PYVER% found
echo.

:: Check if virtual environment exists, create if not
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

:: Install dependencies if needed
echo [INFO] Checking Flask...
venv\Scripts\python.exe -c "import flask" >nul 2>&1
if errorlevel 1 (
    echo [SETUP] Installing dependencies...
    venv\Scripts\pip.exe install -r requirements.txt
    if errorlevel 1 (
        echo [ERROR] Failed to install dependencies!
        pause
        exit /b 1
    )
    echo [OK] Dependencies installed
    echo.
)

:: Install PyInstaller if not present
echo [INFO] Checking PyInstaller...
venv\Scripts\python.exe -c "import PyInstaller" >nul 2>&1
if errorlevel 1 (
    echo [SETUP] Installing PyInstaller...
    venv\Scripts\pip.exe install pyinstaller
    if errorlevel 1 (
        echo [ERROR] Failed to install PyInstaller!
        pause
        exit /b 1
    )
    echo [OK] PyInstaller installed
    echo.
)

:: Clean previous builds
echo [INFO] Cleaning previous builds...
if exist "dist" rmdir /s /q dist
if exist "build" rmdir /s /q build
if exist "Hypertrophy-Toolbox.spec" del /q "Hypertrophy-Toolbox.spec"

:: Check if favicon exists, adjust command accordingly
set ICON_ARG=
if exist "static\images\favicon.ico" (
    set ICON_ARG=--icon=static/images/favicon.ico
)

:: Build the executable
echo.
echo [BUILD] Creating executable (this may take several minutes)...
echo.

venv\Scripts\pyinstaller.exe --name "Hypertrophy-Toolbox" ^
    --onedir ^
    --console ^
    %ICON_ARG% ^
    --add-data "templates;templates" ^
    --add-data "static;static" ^
    --add-data "data;data" ^
    --hidden-import=flask ^
    --hidden-import=jinja2 ^
    --hidden-import=werkzeug ^
    --hidden-import=pandas ^
    --hidden-import=numpy ^
    --hidden-import=openpyxl ^
    --hidden-import=xlsxwriter ^
    --collect-submodules=werkzeug ^
    --collect-submodules=jinja2 ^
    app_launcher.py

if errorlevel 1 (
    echo.
    echo [ERROR] Build failed!
    pause
    exit /b 1
)

:: Copy the run script to dist folder
copy "RUN_APP.bat" "dist\Hypertrophy-Toolbox\" >nul

echo.
echo  ========================================
echo    BUILD COMPLETE!
echo  ========================================
echo.
echo  Your executable is in: dist\Hypertrophy-Toolbox\
echo.
echo  To distribute:
echo    1. Zip the entire "dist\Hypertrophy-Toolbox" folder
echo    2. Share the zip file with users
echo    3. Users extract and double-click "Hypertrophy-Toolbox.exe"
echo.
pause
