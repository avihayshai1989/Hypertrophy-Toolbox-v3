# E2E Testing Documentation

## How to Run Tests

### Prerequisites
1. **Install dependencies** (one-time setup):
   ```bash
   npm install
   npx playwright install
   ```

2. **Ensure Python environment** is set up with Flask app dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Running Tests

| Command | Description |
|---------|-------------|
| `npm run test:e2e` | Run all tests headless (CI mode) |
| `npm run test:e2e:headed` | Run tests with visible browser |
| `npm run test:e2e:ui` | Open Playwright UI for interactive debugging |
| `npm run test:e2e:debug` | Run with Playwright Inspector |

**Note:** The Flask server starts automatically on port 5000 via Playwright's `webServer` configuration.

---

## Test Suite Summary

**Total: ~200+ tests** across 12 spec files

### Test Files

| File | Tests | Coverage |
|------|-------|----------|
| `smoke-navigation.spec.ts` | 14 | Homepage, navigation links, navbar elements, page titles & structure |
| `dark-mode.spec.ts` | 6 | Theme toggle, localStorage persistence, cross-page persistence, icon changes |
| `workout-plan.spec.ts` | 12 | Routine cascade, add exercise, filters, export, table structure, tabs |
| `workout-log.spec.ts` | 28 | Table structure, import, date filter, editable cells, clear log, mobile responsive |
| `summary-pages.spec.ts` | 12 | Weekly summary, session summary, method selector, muscle group selection |
| `progression.spec.ts` | 25 | Page structure, goals management, methodology display, status indicators, suggestions |
| `volume-splitter.spec.ts` | 22 | Input controls, modes, sliders, results, mobile responsive |
| `program-backup.spec.ts` | 18 | Backup creation, listing, restore, delete, API integration |
| `exercise-interactions.spec.ts` | 26 | Delete, replace, superset, inline editing, filter application, tab navigation |
| `accessibility.spec.ts` | 24 | Keyboard navigation, ARIA attributes, focus management, color contrast, screen reader |
| `api-integration.spec.ts` | 40+ | All API endpoints, error handling, response format, rate limiting |

### Key Test Scenarios

#### Navigation & Smoke Tests
- Homepage loads with welcome message
- All 7 navigation links work correctly
- Navbar has all expected elements (logo, links, dark mode toggle, zoom controls)
- Each page loads without JavaScript errors

#### Dark Mode
- Toggle changes theme from light to dark
- Preference persists in localStorage
- Dark mode survives page reloads
- Theme persists across different pages
- Icon changes (moon ↔ sun) correctly

#### Workout Plan
- Routine cascade: Environment → Program → Workout Day selection
- Hidden `#routine` field updates with composite value
- Add exercise to plan with success feedback
- Filter dropdowns populated with options
- Clear filters resets all selections
- Export buttons functional (Excel, Workout Log)
- Generate starter plan modal

#### Workout Log  
- Import exercises from workout plan
- Editable weight, reps, notes cells
- Date filter functionality
- Table structure validation
- Row data persistence
- Clear log confirmation modal
- Mobile responsive table scrolling
- Delete log entries

#### Summary Pages
- Weekly summary grid displays muscle groups
- Session summary table with date filtering
- Method selector changes calculation approach
- Muscle group selection updates display

#### Progression Plan
- Page structure and element visibility
- Goals management (add/delete forms)
- Methodology display and selection
- Status indicators (on track, behind, ahead)
- Progression suggestions display
- Mobile responsive layout

#### Volume Splitter
- Basic and advanced mode switching
- Slider controls and label validation
- Results display and calculation
- State persistence across mode changes
- Mobile responsive controls

#### Program Backup
- Program library modal opens/closes
- Create new backup with naming
- List existing backups
- Restore from backup with confirmation
- Delete backup with confirmation
- API error handling

#### Exercise Interactions
- Delete exercise from plan
- Replace exercise with alternative
- Superset checkbox linking
- Inline editing of sets/reps
- Filter application affects table
- Tab navigation between fields

#### Accessibility
- Keyboard navigation (Tab, Escape, Enter, Arrow keys)
- ARIA attributes on interactive elements
- Focus management in modals
- Skip links functionality
- Color contrast compliance
- Screen reader compatible elements
- Touch target sizes on mobile

#### API Integration
- Workout Plan API (/api/workout-plan)
- Superset API (/api/superset)
- Workout Log API (/api/workout-log)
- Export API (/api/export)
- Progression API (/api/progression-plan)
- Summary APIs (/api/weekly-summary, /api/session-summary)
- Volume Splitter API (/api/volume-splitter)
- Filters API (/api/filters)
- Error response format consistency
- Rate limiting behavior

---

## Bugfix Summary

The E2E tests detected and helped fix the following bug:

### Bug: `handleApiResponse is not defined` in filters.js

**Location:** [static/js/modules/filters.js](../static/js/modules/filters.js#L218)

**Symptom:** Console error when clicking "Clear Filters" button:
```
ReferenceError: handleApiResponse is not defined
    at HTMLButtonElement.clearFilters (filters.js:218:31)
```

**Cause:** The `clearFilters` function called `handleApiResponse(response)` which was never defined or imported in this module.

**Fix:** Changed line 218 from:
```javascript
const exercises = await handleApiResponse(response);
```
To:
```javascript
const exercises = await response.json();
```

This works correctly because `response.ok` is already checked on the previous line.

---

## Architecture

### Files Created

```
├── playwright.config.ts      # Playwright configuration (baseURL, webServer, reporters)
├── tsconfig.json             # TypeScript configuration for test files
├── package.json              # Updated with test scripts and Playwright dependencies
└── e2e/
    ├── fixtures.ts           # Shared test utilities, SELECTORS, helper functions
    ├── smoke-navigation.spec.ts   # Navigation and smoke tests
    ├── dark-mode.spec.ts          # Theme toggle and persistence
    ├── workout-plan.spec.ts       # Workout plan CRUD operations
    ├── workout-log.spec.ts        # Workout log and editing
    ├── summary-pages.spec.ts      # Weekly/session summaries
    ├── progression.spec.ts        # Progression tracking and goals
    ├── volume-splitter.spec.ts    # Volume calculation tool
    ├── program-backup.spec.ts     # Backup/restore functionality
    ├── exercise-interactions.spec.ts  # Delete, replace, superset operations
    ├── accessibility.spec.ts      # A11y, keyboard nav, ARIA, focus
    └── api-integration.spec.ts    # Direct API endpoint testing
```

### Templates Modified

Added `data-testid` attributes to:
- `templates/base.html` - Navbar elements, dark mode toggle, toast container
- `templates/workout_plan.html` - Routine selectors, exercise search, buttons, table

### Selector Strategy

Tests use CSS fallback selectors for resilience:
```typescript
ROUTINE_ENV: '[data-testid="routine-env"], #routine-env'
```
This allows tests to work whether `data-testid` attributes are present or not.

---

## Fixture Utilities

### `fixtures.ts` Exports

| Export | Description |
|--------|-------------|
| `ROUTES` | Route constants: `HOME`, `WORKOUT_PLAN`, `WORKOUT_LOG`, etc. |
| `SELECTORS` | Element selectors with fallbacks |
| `waitForPageReady()` | Waits for DOM + network idle |
| `getDarkModeState()` | Returns current theme ('light' or 'dark') |
| `getStoredDarkMode()` | Returns localStorage 'darkMode' value |
| `ConsoleErrorCollector` | Fixture that collects and asserts no console errors |

### Console Error Detection

All tests use a custom fixture that:
1. Collects all `console.error` messages during test execution
2. Asserts no errors occurred in `afterEach`
3. This caught the `handleApiResponse` bug automatically

---

## CI Integration

The tests are designed for CI pipelines:
- Headless execution by default
- Auto-starting Flask server via `webServer`
- Multiple reporters: list (console) + HTML (artifacts)
- 30-second test timeout
- Automatic retry on server start failure
