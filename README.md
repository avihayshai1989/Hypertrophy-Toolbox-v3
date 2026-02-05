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

### Option 2: Standalone Executable (No Python Required)

If you received a pre-built executable:

1. Extract the zip file to any folder
2. Double-click `Hypertrophy-Toolbox.exe`
3. Browser opens automatically!

**To build the executable yourself:**
```bash
# Double-click build_exe.bat, or run:
python -m pip install pyinstaller
build_exe.bat
```
The executable will be in `dist/Hypertrophy-Toolbox/`

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
