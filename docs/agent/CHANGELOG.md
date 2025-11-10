# Changelog (Responsive Tables Implementation)

Format: `YYYY-MM-DD [unit-id] short-hash: Description`

---

## 2025-11-10

- **A-0** `initial`: Created /docs/agent/ checkpoint infrastructure
  - Files: AGENT_STATE.md, TODO.md, DECISIONS.md, CHANGELOG.md
  - Established work unit tracking and resume protocol
  - Defined ADRs for table layout, container queries, column priorities

- **A-1** `css-001`: Created static/css/responsive.css
  - CSS tokens for zoom-friendly typography (rem + clamp())
  - Sticky header and first column positioning
  - Priority-based column visibility (.col--high, .col--med, .col--low)
  - Container queries with media query fallback
  - Row card mode for ≤820px containers
  - Dark mode compatibility
  - Print styles
  - Accessibility focus states

- **A-2** `js-001`: Created static/js/table-responsiveness.js
  - Column chooser with localStorage persistence
  - Density toggle (comfortable/compact)
  - ResizeObserver for dynamic rows-per-page
  - Auto-initialization via data attributes
  - Public API for manual initialization

- **A-3** `base-001`: Integrated responsive files into base.html
  - Added responsive.css after styles_tables.css
  - Added table-responsiveness.js after darkMode.js
  - Fixed merge conflicts in bootstrap imports

- **B-1** `plan-001`: Updated workout_plan.html
  - Wrapped table in .tbl-wrap container
  - Added .tbl--responsive class to table
  - Added data-table-responsive="workout_plan" attribute
  - Applied priority classes to all <th> elements
  - Added data-label attributes for card mode
  - Updated workout-plan.js to apply classes to dynamic <td> elements

- **B-2** `log-001`: Started workout_log.html update
  - In progress: Adding responsive wrappers and priority classes

