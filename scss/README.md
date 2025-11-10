# Custom Bootstrap Build

This directory contains the custom Bootstrap SCSS configuration for the Hypertrophy Toolbox.

## Purpose

Instead of loading the full Bootstrap 5.1.3 (~150KB), we create a minimal build with only the components we actually use (~60-80KB), reducing the CSS bundle size by approximately 50-70%.

## Setup

1. **Install dependencies**:
   ```bash
   npm install
   ```

2. **Build the custom CSS**:
   ```bash
   npm run build:css
   ```

3. **Watch for changes during development**:
   ```bash
   npm run watch:css
   ```

## What's Included

### Core
- Functions, Variables, Mixins, Root, Reboot

### Layout
- Containers
- Grid System

### Components (Only What We Use)
- Buttons & Button Groups
- Navigation & Navbar
- Cards
- Alerts
- Badges
- Forms
- Tables
- Modals
- Dropdowns
- Toasts
- Close Button

### Utilities
- Helpers
- Utility API

## What's Excluded (Unused)

The following Bootstrap components are NOT included, saving ~50KB:
- Accordion
- Breadcrumb
- Carousel
- List Group
- Pagination
- Placeholders
- Popovers
- Progress Bars
- Scrollspy
- Spinners
- Offcanvas

## Customization

You can customize Bootstrap variables in `custom-bootstrap.scss`. Current customizations:
- Primary color: `#007bff`
- Dark color: `#212529`
- Font family: System fonts

## Output

The compiled CSS is output to: `static/css/bootstrap.custom.min.css`

This file should be used instead of the Bootstrap CDN link in `templates/base.html`.

## Migration

To switch from CDN to custom build:

**Before**:
```html
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
```

**After**:
```html
<link rel="stylesheet" href="{{ url_for('static', filename='css/bootstrap.custom.min.css') }}">
```

## Benefits

1. **Smaller Bundle Size**: ~50-70% reduction in CSS size
2. **Faster Loading**: Less data to download and parse
3. **Self-Hosted**: Better caching control, works offline
4. **Customizable**: Easy to adjust colors, spacing, etc.
5. **Version Control**: Lock Bootstrap version explicitly
6. **No Unused Code**: Only ship what you actually use

