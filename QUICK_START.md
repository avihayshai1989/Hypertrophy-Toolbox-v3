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

## ✨ Key Features

### 🎯 Auto Starter Plan Generator
Generate evidence-based workout plans with one click:
1. Go to **Workout Plan** page
2. Click the green **Generate Plan** button
3. Configure your preferences:
   - **Training Days**: 1-3 days per week
   - **Environment**: Gym (full equipment) or Home (bodyweight/minimal)
   - **Experience Level**: Novice, Intermediate, or Advanced
   - **Goal**: Hypertrophy, Strength, or General fitness
   - **Priority Muscles**: Select up to 2 muscles to get extra volume
4. Click **Generate Plan** to create your personalized routine

### 📈 Double Progression System
The progression tracker automatically suggests when to increase weight:
- **Hit top of rep range** (e.g., 3×10 when range is 6-10) → Increase weight
- **Below minimum reps** → Focus on adding reps first
- **In range but not at top** → Continue current load

View suggestions on the **Progression Plan** page.

### 🔍 Pattern Coverage Analysis
Monitor your program balance on the **Weekly Summary** page:
- See total sets per movement pattern (squat, hinge, push, pull)
- Get warnings for missing patterns or volume imbalances
- Track sets per routine (target: 15-24 sets per session)

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
