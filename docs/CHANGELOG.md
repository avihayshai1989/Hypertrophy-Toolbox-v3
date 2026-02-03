# Changelog

All notable changes to Hypertrophy Toolbox v3.

## v1.4.1 - November 10, 2025

### Bug Fixes
- Fixed Columns button dropdown overlap in Workout Plan table
- Fixed Compact/Comfortable density toggle not responding to clicks

### Improvements
- Added Escape key support to close column menu
- Better ARIA labels and keyboard accessibility
- Mobile-responsive menu positioning

---

## v1.4.0 - November 2, 2025

### Dependency Optimization
- Removed jQuery dependency (~85KB saved)
- Removed unused `requests` package
- Set up custom Bootstrap build infrastructure (~50% size reduction when activated)
- Pinned all package versions for reproducible builds

### New
- Native JavaScript table sorting (replaced jQuery DataTables)
- Custom Bootstrap SCSS build system (`npm run build:css`)

---

## v1.3.0 - 2025

### Workout Plan Dropdowns Refresh
- Modern dropdown UI with progressive enhancement
- Full keyboard navigation (Arrow keys, Home/End, Escape, typeahead)
- WCAG 2.2 AA+ accessibility compliance
- Mobile sheet-style dropdowns
- Search functionality for long option lists

---

## v1.2.0 - 2025

### Workout Plan Modernization
- Modern 2025 visual refresh
- CSS custom properties (`--wp-*` tokens)
- Enhanced semantic HTML and ARIA attributes
- Improved form controls and table styling
- Dark mode support
- Reduced motion support

---

## v1.1.0 - 2025

### Navbar Modernization
- Modern 2025 visual refresh with fluid typography
- Sticky header with compact mode on scroll
- Enhanced mobile menu (full-screen overlay, focus trap)
- CSS custom properties (`--nav-*` tokens)
- WCAG 2.2 AA+ accessibility compliance
- Dark mode support

---

## v1.0.0 - 2025

### Welcome Screen Refresh
- Modern 2025 visual design
- Fluid typography with `clamp()`
- CSS custom properties (`--welcome-*` tokens)
- Enhanced accessibility (ARIA labels, keyboard navigation)
- Dark mode and reduced motion support
- Container queries for responsive card layouts

