# Hypertrophy Toolbox v3

Design your workout plan using science, all the toolbox you need in order to design, track and monitor your workouts.

## 🚀 Quick Start

### How To Run the Application?

1. Create `.venv` virtual environment under the project:
   ```bash
   python -m venv .venv
   ```

2. Activate the `.venv`:
   - **Windows**: `.venv\Scripts\activate`
   - **Linux/Mac**: `source .venv/bin/activate`

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Run the application:
   ```bash
   python app.py
   ```

5. Open your browser and navigate to `http://localhost:5000`

## 📚 Documentation

For comprehensive documentation, see the [`docs/`](docs/) folder:

- **[Project Scope](docs/scope.md)** - Architecture, tech stack, and implementation status
- **[Changelog](docs/CHANGELOG.md)** - Version history and modernization work
- **[CSS Ownership Map](docs/CSS_OWNERSHIP_MAP.md)** - CSS file organization guide
- **[Consolidation Summary](docs/PRIORITY5_CONSOLIDATION_SUMMARY.md)** - Codebase consolidation details
- **[Test Results](docs/PRIORITY5_TEST_RESULTS.md)** - Test coverage and results

## ✨ Features

- **Workout Plan Builder** - Create custom workout routines with exercises filtered by muscle groups, equipment, and more
- **Exercise Database** - Comprehensive exercise library with scientific parameters (RIR, RPE, rep ranges)
- **Workout Logging** - Track actual performance vs. planned workouts
- **Analytics** - Weekly and session summaries with data visualization
- **Volume Management** - Volume splitting and distribution tools
- **Data Export** - Export to Excel and workout log
- **Dark Mode** - System-aware theme with smooth transitions
- **Modern UI** - 2025-refreshed design with accessibility features

## 🛠️ Tech Stack

- **Backend**: Flask 3.1.0, Python 3.12, SQLite
- **Frontend**: Vanilla JavaScript (ES6+), HTML5, CSS3
- **Styling**: Custom CSS with Bootstrap 5.1.3
- **Dependencies**: See `requirements.txt`

## 📝 Contributing

Before making changes:
1. Review the [scope.md](docs/scope.md) for architecture overview
2. Check [CSS_OWNERSHIP_MAP.md](docs/CSS_OWNERSHIP_MAP.md) before modifying styles
3. Update [CHANGELOG.md](docs/CHANGELOG.md) after completing features

## 📄 License

All rights reserved.
