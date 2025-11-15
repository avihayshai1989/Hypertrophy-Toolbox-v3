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

3. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Install Node.js dependencies and build CSS:
   ```bash
   npm install
   npm run build:css
   ```
   > This compiles the custom Bootstrap CSS required by the application

5. Run the application:
   ```bash
   python app.py
   ```

6. Open your browser and navigate to `http://localhost:5000`

## 🧭 Operations Runbook

1. **Create and activate a virtual environment** (see steps above) and install dependencies with `pip install -r requirements.txt`.
2. **Point the app at the container-mounted database** by exporting `DB_FILE=/mnt/data/database.db`. On PowerShell use ` $Env:DB_FILE = "C:\\mnt\\data\\database.db" ` for the current session.
3. **Initialize the schema**:
   ```bash
   python -c "from utils.db_initializer import initialize_database; initialize_database()"
   ```
4. **Populate the isolated muscle junction table** (idempotent and safe to rerun):
   ```bash
   python scripts/migrate_isolated_muscles.py
   ```
5. **Start the Flask service** with `python app.py`.
6. **Smoke test**:
   - `/get_unique_values/exercises/advanced_isolated_muscles` returns canonical muscles from the junction table.
   - Weekly/session summary pages show weighted sets with clean volume buckets.
7. **Rollback plan**: restore the most recent `database.backup-<timestamp>.sqlite` created during migrations and rerun steps 3-5.

## 📚 Documentation

For comprehensive documentation, see the [`docs/`](docs/) folder:

- **[Project Scope](docs/scope.md)** - Architecture, tech stack, and implementation status
- **[Changelog](docs/CHANGELOG.md)** - Version history and modernization work
- **[CSS Ownership Map](docs/CSS_OWNERSHIP_MAP.md)** - CSS file organization guide
- **[Consolidation Summary](docs/PRIORITY5_CONSOLIDATION_SUMMARY.md)** - Codebase consolidation details
- **[Test Results](docs/PRIORITY5_TEST_RESULTS.md)** - Test coverage and results
- **[Dependency Optimization](docs/PRIORITY9_DEPENDENCY_OPTIMIZATION.md)** - Dependency hygiene & slimming analysis
- **[Backend Refactor Roadmap](docs/BACKEND_REFACTOR_TODO.md)** - Current security/export stabilization and normalization plan
- **Export Behavior** - Summary endpoints always return a valid Excel workbook, even when no data is available, with a "No Data" tab that explains the situation.

## ✨ Features

- **Workout Plan Builder** - Create custom workout routines with exercises filtered by muscle groups, equipment, and more
- **Exercise Database** - Comprehensive exercise library with scientific parameters (RIR, RPE, rep ranges)
- **Workout Logging** - Track actual performance vs. planned workouts
- **Analytics** - Weekly and session summaries with data visualization
- **Volume Management** - Volume splitting and distribution tools
- **Data Export** - Export to Excel and workout log (summary exports return a valid empty workbook if no data is available)
   - Summary exports always include a `No Data` worksheet when there are no results.
- **Dark Mode** - System-aware theme with smooth transitions
- **Modern UI** - 2025-refreshed design with accessibility features
- **Responsive Tables** - Zoom-friendly, adaptive tables with column prioritization

## 📱 Responsive Table Behavior

All data tables are fully responsive across screen sizes (1366px-2560px) and browser zoom levels (90%-125%).

### Key Features

- **Sticky Headers & First Column** - Header row and first column remain visible while scrolling
- **Progressive Column Disclosure** - Columns automatically hide/show based on priority:
  - **High Priority** (always visible ≥1080p): Exercise, Routine, Sets, Reps, Weight, Date, Actions
  - **Medium Priority** (hidden <1366px or >110% zoom): Primary Muscle, RIR, RPE, Notes
  - **Low Priority** (first to collapse): Secondary muscles, Grips, Stabilizers, Synergists
- **Zoom-Friendly Typography** - Uses `rem` and `clamp()` for readable text at all zoom levels
- **Card Mode** - Tables automatically switch to stacked cards on narrow screens (≤820px)
- **User Preferences** - Column visibility and density settings persist via localStorage
- **Accessibility** - WCAG AA compliant with full keyboard navigation

### Usage on 1920×1080 Display

At 100% zoom, you'll see key columns without horizontal scrolling. As you zoom in or resize the window, lower-priority columns progressively hide to maintain usability.

### Adding Responsive Behavior to New Tables

1. **Wrap your table** in a `.tbl-wrap` container:
   ```html
   <div class="tbl-wrap">
     <table class="table tbl tbl--responsive" data-table-responsive="page_key">
       <!-- table content -->
     </table>
   </div>
   ```

2. **Add priority classes** to `<th>` elements:
   ```html
   <th class="col--high" data-label="Exercise">Exercise</th>
   <th class="col--med" data-label="RIR">RIR</th>
   <th class="col--low" data-label="Grips">Grips</th>
   ```

3. **Mirror classes on `<td>` elements** (same classes + data-label):
   ```html
   <td class="col--high" data-label="Exercise">Bench Press</td>
   <td class="col--med is-num" data-label="RIR">3</td>
   <td class="col--low" data-label="Grips">Pronated</td>
   ```

4. **Use utility classes** where appropriate:
   - `.is-num` - Right-align numeric columns
   - `.el-clip` - Truncate with ellipsis
   - `.col--wrap` - Allow text wrapping

### Files

- `static/css/responsive.css` - Responsive table styles
- `static/js/table-responsiveness.js` - Column chooser, density toggle, ResizeObserver
- `docs/agent/` - Implementation checkpoints for resumable work

### Implementation Status

- ✅ Workout Plan - Fully responsive
- 🔄 Workout Log - In progress
- ⏳ Weekly Summary - Pending
- ⏳ Session Summary - Pending

For architecture decisions, see `docs/agent/DECISIONS.md`.

## 🛠️ Tech Stack

- **Backend**: Flask 3.1.0, Python 3.12, SQLite
- **Frontend**: Vanilla JavaScript (ES6+), HTML5, CSS3
- **Styling**: Custom CSS + Custom Bootstrap 5.1.3 build
- **Build Tools**: SASS (optional, for Bootstrap customization)
- **CI/CD**: GitHub Actions (security audits, linting, testing)
- **Dependencies**: See `requirements.txt` and `package.json`

## 📝 Contributing

Before making changes:
1. Review the [scope.md](docs/scope.md) for architecture overview
2. Check [CSS_OWNERSHIP_MAP.md](docs/CSS_OWNERSHIP_MAP.md) before modifying styles
3. Update [CHANGELOG.md](docs/CHANGELOG.md) after completing features

## 📄 License

All rights reserved.
