# Hypertrophy Toolbox - Quick Start Guide

## 🚀 For Users (Running the App)

### Option 1: Easy Start (Requires Python)
1. **Double-click `START.bat`**
2. Wait for setup to complete (first time only)
3. Browser opens automatically to the app!

### Option 2: Standalone Executable (No Python Needed)
If you received a zip file with the executable:
1. Extract the zip to any folder
2. Double-click `Hypertrophy-Toolbox.exe`
3. Browser opens automatically!

---

## 🔧 For Developers (Building the Executable)

### Prerequisites
- Python 3.10+ installed
- All dependencies installed (`pip install -r requirements.txt`)

### Building the Standalone Executable

1. **Run the build script:**
   ```
   build_exe.bat
   ```

2. **Wait for build to complete** (3-5 minutes)

3. **Find your executable in:**
   ```
   dist/Hypertrophy-Toolbox/
   ```

### Distributing to Users

1. Zip the entire `dist/Hypertrophy-Toolbox/` folder
2. Share the zip file
3. Users extract and run `Hypertrophy-Toolbox.exe`

---

## ❓ Troubleshooting

### "Python is not installed" Error
- Download Python from https://www.python.org/downloads/
- **IMPORTANT:** Check "Add Python to PATH" during installation

### App Won't Start
- Make sure no other app is using port 5000
- Try running as Administrator

### Browser Doesn't Open
- Manually open: http://localhost:5000

### Executable Build Fails
- Make sure all dependencies are installed
- Run: `pip install -r requirements.txt`
- Run: `pip install pyinstaller`

---

## 📁 File Overview

| File | Purpose |
|------|---------|
| `START.bat` | Quick launcher for users with Python |
| `build_exe.bat` | Creates standalone .exe (for developers) |
| `app_launcher.py` | Wrapper for executable build |
| `RUN_APP.bat` | Helper script included in executable |
