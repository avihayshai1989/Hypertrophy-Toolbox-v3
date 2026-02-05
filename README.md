# Hypertrophy Toolbox v3

Design your workout plan using science - all the tools you need to design, track, and monitor your workouts.

## 🚀 Running the Application

### Option 1: One-Click Start (Recommended for Windows Users)

**Double-click `START.bat`** - That's it!

This will automatically:
- Check for Python installation
- Create a virtual environment
- Install all dependencies
- Start the Flask server
- Open your browser to `http://127.0.0.1:5000`

> **Note:** If the browser doesn't open automatically, manually navigate to `http://127.0.0.1:5000`

### Option 2: Standalone Executable (No Installation Required)

**This option is for users who received a pre-packaged zip file.**

**Requirements:** None! No Python, no installation, no setup needed.

**Steps:**
1. Extract the zip file to any folder on your computer
2. Open the extracted folder
3. Double-click `Hypertrophy-Toolbox.exe`
4. Your browser will open automatically to the app

> **Troubleshooting:** 
> - If Windows shows a security warning, click "More info" → "Run anyway"
> - If browser doesn't open, manually go to `http://127.0.0.1:5000`

---

### Option 3: Manual Setup (For Developers)

1. **Create and activate virtual environment:**
   ```bash
   python -m venv venv
   # Windows
   venv\Scripts\activate
   # Linux/Mac
   source venv/bin/activate
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   npm install
   npm run build:css
   ```

3. **Run the application:**
   ```bash
   python app.py
   ```

4. **Open** `http://localhost:5000`

---

## 📁 Launcher Files

| File | Description |
|------|-------------|
| `START.bat` | 1-click launcher (requires Python installed) |
| `build_exe.bat` | Builds standalone .exe for distribution |
| `app_launcher.py` | Wrapper script for executable build |
| `QUICK_START.md` | Detailed setup instructions |

## 📦 Building the Standalone Executable (For Developers)

To create the standalone `.exe` package for distribution to end users:

1. **Run the build script:**
   ```bash
   build_exe.bat
   ```
   (PyInstaller will be installed automatically if needed)

2. **Find the output in the `dist` folder:**
   ```
   dist/
   └── Hypertrophy-Toolbox/
       ├── Hypertrophy-Toolbox.exe   ← Main executable
       ├── RUN_APP.bat
       └── _internal/                 ← Required support files
   ```

3. **Distribute:** Zip the entire `dist/Hypertrophy-Toolbox/` folder and share with users

## ✨ Features

- **Workout Plan Builder** - Create custom routines with exercises filtered by muscle groups, equipment, and more
- **Exercise Database** - Comprehensive library with scientific parameters (RIR, RPE, rep ranges)
- **Workout Logging** - Track actual performance vs. planned workouts
- **Weekly & Session Summaries** - Analytics with volume tracking and data visualization
- **Volume Splitter** - Volume distribution and muscle group allocation tools
- **Program Backups** - Save and restore workout programs
- **Data Export** - Export to Excel with proper formatting
- **Dark Mode** - System-aware theme
- **Responsive Tables** - Adaptive tables with sticky headers and column prioritization

## 📚 Documentation

See the [`docs/`](docs/) folder:

- [scope.md](docs/scope.md) - Architecture and tech stack
- [CHANGELOG.md](docs/CHANGELOG.md) - Version history
- [CSS_OWNERSHIP_MAP.md](docs/CSS_OWNERSHIP_MAP.md) - CSS file organization
- [muscle_selector.md](docs/muscle_selector.md) - Muscle selector component
- [program_backups.md](docs/program_backups.md) - Backup/restore feature

## 🛠️ Tech Stack

- **Backend**: Flask 3.1+, Python 3.12, SQLite
- **Frontend**: Vanilla JavaScript (ES6+), HTML5, CSS3
- **Styling**: Custom Bootstrap 5.1.3 build + custom CSS
- **Testing**: pytest (240 tests)

## 🧪 Running Tests

```bash
pytest tests/ -v
```

## 📄 License

All rights reserved.
