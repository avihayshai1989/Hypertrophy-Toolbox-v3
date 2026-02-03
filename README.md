# Hypertrophy Toolbox v3

Design your workout plan using science - all the tools you need to design, track, and monitor your workouts.

## 🚀 Quick Start

1. **Create and activate virtual environment:**
   ```bash
   python -m venv .venv
   # Windows
   .venv\Scripts\activate
   # Linux/Mac
   source .venv/bin/activate
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
