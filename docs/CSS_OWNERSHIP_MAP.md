# CSS Ownership Map

This document maps CSS files to their responsible UI areas and components. Use this as a reference to know where to make styling changes.

## Architecture Overview

**Main Entry Point:** `styles.css` (73 lines) - Imports all other stylesheets in dependency order

```
styles.css
├── Base & Utilities (foundational)
├── Layout & Structure (page-level)
├── Core Components (reusable elements)
├── UI Components (complex widgets)
└── Page-Specific (single-page styles)
```

---

## 🔵 Base & Utilities (Foundational)

### `bootstrap.custom.min.css` (compiled)
**Owner:** Bootstrap framework
**Scope:**
- Custom Bootstrap 5.1.3 build
- Grid, buttons, forms, modals, cards, alerts, badges, tables
- Generated via `npm run build:css` from `scss/custom-bootstrap.scss`
**Note:** Optional - CDN version can be used instead

### `styles_tokens.css` (372 lines)
**Owner:** Design tokens / Responsive scaling system
**Scope:**
- CSS custom properties for responsive spacing and sizing
- Viewport-based scaling (720p to 4K)
- Spacing scale, typography sizes, layout tokens

### `styles_general.css` (23 lines)
**Owner:** Global base styles
**Scope:**
- Body defaults
- Text rendering
- Font smoothing
- Global resets

### `styles_utilities.css` (60 lines)
**Owner:** Utility classes
**Scope:**
- Spacing utilities (.mt-*, .mb-*, .p-*)
- Text utilities (.text-center, .text-muted)
- Display utilities (.d-none, .d-flex)
- Helper classes

---

## 🟢 Layout & Structure

### `styles_layout.css` (97 lines)
**Owner:** Page layout structure
**Scope:**
- Container styles
- Grid layouts
- Flexbox containers
- Section spacing
- Page wrappers

### `styles_responsive.css` (233 lines)
**Owner:** Responsive behavior
**Scope:**
- Media queries
- Mobile adaptations
- Tablet breakpoints
- Desktop optimizations
- Responsive utilities

### `responsive.css` (714 lines)
**Owner:** Responsive tables
**Scope:**
- Sticky headers and first column
- Priority-based column visibility (`.col--high`, `.col--med`, `.col--low`)
- Column chooser and density toggle
- Card mode for narrow screens
- Zoom-friendly typography
**Pages:** Workout Plan, Workout Log

---

## 🟡 Core Components (Reusable Elements)

### `styles_buttons.css` (191 lines)
**Owner:** Button components
**Scope:**
- Primary/secondary buttons
- Button sizes and states
- Button groups
- Icon buttons
**Note:** Some overlap with `styles_action_buttons.css` - consider consolidation

### `styles_action_buttons.css` (156 lines)
**Owner:** Action-specific buttons
**Scope:**
- Add/remove buttons
- Save/cancel buttons
- Action button groups
- Contextual action buttons
**Note:** ⚠️ Potential duplication with `styles_buttons.css`

### `styles_forms.css` (417 lines)
**Owner:** Form elements
**Scope:**
- Input fields
- Select dropdowns
- Textareas
- Form groups
- Form validation styles
- Labels and hints

### `styles_tables.css` (507 lines)
**Owner:** Table components
**Scope:**
- Table layouts
- Table headers/rows/cells
- Sortable tables
- Responsive tables
- Table actions

### `styles_cards.css` (41 lines)
**Owner:** Card components
**Scope:**
- Card containers
- Card headers/body/footer
- Card shadows and borders

### `styles_dropdowns.css` (131 lines)
**Owner:** Dropdown menus
**Scope:**
- Dropdown containers
- Dropdown items
- Dropdown animations
- Custom select styles

---

## 🟣 UI Components (Complex Widgets)

### `styles_navbar.css` (701 lines)
**Owner:** Navigation bar
**Scope:**
- Navbar structure
- Nav links
- Mobile navigation
- Navbar branding
- Navigation icons
- Mega menus
**Pages:** All pages (global header)

### `styles_notifications.css` (87 lines)
**Owner:** Toast notifications
**Scope:**
- Toast containers
- Toast animations
- Success/error/warning styles
- Notification positioning

### `styles_modals.css` (47 lines)
**Owner:** Modal dialogs
**Scope:**
- Modal overlays
- Modal content
- Modal headers/footers
- Modal animations

### `styles_tooltips.css` (49 lines)
**Owner:** Tooltip components
**Scope:**
- Tooltip containers
- Tooltip arrows
- Tooltip positioning
- Tooltip animations

### `styles_filters.css` (106 lines)
**Owner:** Filter UI components
**Scope:**
- Filter panels
- Filter chips
- Advanced filter UI
- Filter buttons and controls
**Pages:** Workout Plan, Exercise selection

### `styles_muscle_groups.css` (41 lines)
**Owner:** Muscle group displays
**Scope:**
- Muscle badges
- Muscle group pills
- Muscle category styles

### `styles_volume.css` (41 lines)
**Owner:** Volume indicators
**Scope:**
- Volume badges
- Volume status indicators
- Volume thresholds

### `volume_indicators.css` (23 lines)
**Owner:** Volume indicator specifics
**Scope:**
- Volume progress bars
- Volume status colors
**Note:** ⚠️ Potential consolidation with `styles_volume.css`

### `styles_frames.css` (586 lines)
**Owner:** Content frames/panels
**Scope:**
- Panel containers
- Frame layouts
- Sectioned content areas
- Bordered containers

### `styles_chat.css` (34 lines)
**Owner:** Chat/messaging UI (if applicable)
**Scope:**
- Chat bubbles
- Message containers
**Note:** ⚠️ Review if chat feature exists

### `styles_muscle_selector.css` (581 lines)
**Owner:** Muscle selector component
**Scope:**
- SVG body diagram styling
- Muscle region hover/selection states
- Simple/Advanced view modes
- Front/Back tab navigation
- Tooltip and debug UI
**Pages:** `/workout_plan` (Generate Plan modal)

### `styles_routine_cascade.css` (342 lines)
**Owner:** Routine cascade selector
**Scope:**
- 3-step cascading dropdown for routine selection
- Split type, days, routine name dropdowns
- Connector arrows between steps
**Pages:** `/workout_plan`

---

## 🔴 Page-Specific Styles

### `styles_welcome.css` (760 lines)
**Owner:** Welcome/Home page
**Scope:**
- Welcome hero section
- Getting started cards
- Onboarding UI
- Feature highlights
**Pages:** `/` (home/welcome)

### `styles_workout_plan.css` (1,285 lines)
**Owner:** Workout Plan page
**Scope:**
- Exercise selection UI
- Routine builder
- Exercise details panel
- Workout plan table
- Filter integration
**Pages:** `/workout_plan`

### `styles_workout_dropdowns.css` (328 lines)
**Owner:** Workout-specific dropdowns
**Scope:**
- Exercise dropdowns
- Routine selection
- Set/rep dropdowns
**Pages:** `/workout_plan`, `/workout_log`
**Note:** ⚠️ Consider merging with `styles_dropdowns.css`

### `workout_log.css` (151 lines)
**Owner:** Workout Log page
**Scope:**
- Log entry forms
- Date pickers
- Set tracking UI
- Log history display
**Pages:** `/workout_log`

### `styles_progression.css` (174 lines)
**Owner:** Progression Plan page
**Scope:**
- Progression tracking UI
- Progress indicators
- Goal setting forms
- Achievement displays
**Pages:** `/progression`

### `styles_volume_splitter.css` (333 lines)
**Owner:** Volume Splitter page
**Scope:**
- Volume splitting UI
- Muscle volume allocation
- Volume distribution charts
- Split recommendations
**Pages:** `/volume_splitter`

### `session_summary.css` (23 lines)
**Owner:** Session Summary page
**Scope:**
- Session overview
- Summary cards
- Session metrics
**Pages:** `/session_summary`

### `styles_science.css` (74 lines)
**Owner:** Science/educational content
**Scope:**
- Scientific notation
- Research citations
- Educational panels
**Pages:** Scattered across pages

### `styles_error.css` (32 lines)
**Owner:** Error pages
**Scope:**
- 404 pages
- Error messages
- Error layouts
**Pages:** Error pages

---

## 🌓 Theming

### `styles_dark_mode.css` (297 lines)
**Owner:** Dark mode theme
**Scope:**
- Dark mode color overrides
- Dark mode component adjustments
- Theme toggle integration
**Pages:** All pages (global theme)

---

## 🔍 Consolidation Opportunities

### High Priority

1. **Button Duplication**
   - Merge `styles_action_buttons.css` (156 lines) into `styles_buttons.css` (191 lines)
   - Create clear button hierarchy (primary, secondary, action, danger)

2. **Volume Styles**
   - Consolidate `volume_indicators.css` (23 lines) into `styles_volume.css` (41 lines)
   - Single source for all volume-related styling

3. **Dropdown Duplication**
   - Review `styles_workout_dropdowns.css` (328 lines) vs `styles_dropdowns.css` (131 lines)
   - Extract common dropdown patterns into base, keep workout-specific in page file

### Medium Priority

4. **Design Tokens Enhancement**
   - `styles_tokens.css` now contains responsive scaling system
   - Consider adding color palette tokens
   - Reference tokens throughout other files

5. **Chat Styles Review**
   - Verify if `styles_chat.css` is actually used
   - Remove if chat feature doesn't exist

### Low Priority

6. **General/Utilities Split**
   - Review overlap between `styles_general.css` and `styles_utilities.css`
   - Ensure clear separation of concerns

---

## 📋 Page-to-CSS Mapping

| Page | Primary CSS | Secondary CSS |
|------|-------------|---------------|
| `/` (Home) | `styles_welcome.css` | - |
| `/workout_plan` | `styles_workout_plan.css` | `styles_filters.css`, `styles_workout_dropdowns.css` |
| `/workout_log` | `workout_log.css` | `styles_workout_dropdowns.css` |
| `/progression` | `styles_progression.css` | - |
| `/volume_splitter` | `styles_volume_splitter.css` | `styles_volume.css` |
| `/session_summary` | `session_summary.css` | - |
| `/weekly_summary` | *(inherits from base)* | `styles_tables.css`, `styles_cards.css` |
| Error pages | `styles_error.css` | - |

---

## 🎯 Per-Page Loading Strategy

Currently, all CSS is loaded globally via `styles.css`. To implement per-page loading:

### Core (Always Load)
```html
<link rel="stylesheet" href="styles_general.css">
<link rel="stylesheet" href="styles_utilities.css">
<link rel="stylesheet" href="styles_layout.css">
<link rel="stylesheet" href="styles_buttons.css">
<link rel="stylesheet" href="styles_forms.css">
<link rel="stylesheet" href="styles_navbar.css">
<link rel="stylesheet" href="styles_notifications.css">
<link rel="stylesheet" href="styles_dark_mode.css">
```

### Page-Specific (Conditional)
```python
# In base.html template
{% block page_css %}
    <!-- Override in child templates -->
{% endblock %}

# In workout_plan.html
{% block page_css %}
    <link rel="stylesheet" href="styles_workout_plan.css">
    <link rel="stylesheet" href="styles_filters.css">
    <link rel="stylesheet" href="styles_workout_dropdowns.css">
{% endblock %}
```

---

## 📝 Maintenance Guidelines

1. **Before adding styles:** Check this map to find the correct file
2. **Before creating a new file:** Justify why existing files don't fit
3. **When duplicating:** Mark with `⚠️` in this document and plan consolidation
4. **Page-specific rule:** Styles used by 2+ pages → move to component file
5. **Update this map:** When adding/removing/refactoring CSS files

---

## 🚀 Implementation Status

- ✅ **Map Created:** CSS ownership documented
- ⏳ **Pending:** Consolidate button styles
- ⏳ **Pending:** Consolidate volume indicators
- ⏳ **Pending:** Implement per-page CSS loading
- ⏳ **Pending:** Populate design tokens

**Last Updated:** 2026-02-03

