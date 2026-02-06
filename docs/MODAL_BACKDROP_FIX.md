# Modal Backdrop Fix for UI Scale Issues

## Problem Description
When the UI scale level is set to any value other than "6" (100%), two issues occur:
1. **Shadows/dark backgrounds** appear on dialogs and popup menus
2. **Modals not centered** - dialogs appear off-center at different zoom levels

This affects:
- Generate Starter Plan modal
- Program Library modal
- Save Program modal
- Progression Plan modals (e.g., "Increase Weight" goal setting)
- Any other Bootstrap modals in the application

## Root Cause
CSS `zoom` is applied to the `<html>` element for UI scaling (levels 1-8 map to 75%-120% zoom). Elements with `position: fixed` using viewport units (`100vw`/`100vh`) - like Bootstrap's `.modal` and `.modal-backdrop` - don't render correctly when zoom ≠ 1, causing:
- Visual artifacts with backdrop
- Incorrect centering of modal dialogs

## Solution Implemented
**Approach:** Two-part fix:
1. Remove modal backdrops completely to eliminate rendering inconsistency
2. Apply counter-zoom to modals (same technique used for navbar) to fix centering

### Files Modified

#### 1. `static/css/styles_modals.css`
Added at the top of the file (after the existing comment block):
```css
/* ============================================
   BACKDROP REMOVAL - Fix for UI Scale Issue
   When CSS zoom != 1, position:fixed backdrops
   with viewport units render incorrectly.
   Removing backdrop eliminates visual artifacts.
   ============================================ */
.modal-backdrop {
    display: none !important;
}

/* ============================================
   MODAL COUNTER-ZOOM - Fix for Centering
   When CSS zoom is applied to <html>, position:fixed
   elements like .modal don't center correctly.
   Counter-zoom modal to ensure proper centering.
   Uses same CSS variables as navbar counter-zoom.
   ============================================ */
@supports (zoom: 1) {
    .modal {
        zoom: var(--ui-scale-inverse, 1);
    }
}

/* Add subtle shadow to modal content to maintain visual separation */
.modal-content {
    box-shadow: 0 0 40px rgba(0, 0, 0, 0.3), 0 0 100px rgba(0, 0, 0, 0.15) !important;
}
```

#### 2. `templates/workout_plan.html`
Added `modal-dialog-centered` class to modals that were missing it:

**Save Program Modal:**
```html
<div class="modal-dialog modal-dialog-centered">
```

**Program Library Modal:**
```html
<div class="modal-dialog modal-dialog-centered modal-lg">
```

#### 3. `static/css/styles_progression.css`
Removed the custom `::before` backdrop that was specific to the progression page goal setting modal.

**Before:**
```css
/* Modal Styles - Progression Page Specific */
/* Custom backdrop for goal setting modal */
#goalSettingModal.show::before {
    content: '';
    position: fixed;
    top: 0;
    left: 0;
    width: 100vw;
    height: 100vh;
    background-color: rgba(0, 0, 0, 0.5);
    z-index: -1;
}
```

**After:**
```css
/* Modal Styles - Progression Page Specific */
/* Custom backdrop REMOVED - causes visual artifacts with CSS zoom scaling */
/* The modal shadow from styles_modals.css provides visual separation */
```

## How the Counter-Zoom Fix Works
The `--ui-scale-inverse` CSS variable is already defined in `base.html`:
```css
html[data-scale="1"] { --ui-scale-inverse: 1.333; }  /* 75% zoom → 133.3% counter */
html[data-scale="2"] { --ui-scale-inverse: 1.25; }
html[data-scale="3"] { --ui-scale-inverse: 1.176; }
html[data-scale="4"] { --ui-scale-inverse: 1.111; }
html[data-scale="5"] { --ui-scale-inverse: 1.053; }
html[data-scale="6"] { --ui-scale-inverse: 1; }      /* 100% zoom → no counter */
html[data-scale="7"] { --ui-scale-inverse: 0.909; }
html[data-scale="8"] { --ui-scale-inverse: 0.833; }
```

When `zoom: 1.1` is applied to `<html>` (scale 7), the modal gets `zoom: 0.909`, which cancels out to effectively `zoom: 1` for the modal, keeping it properly positioned and sized.

## What Was NOT Changed
- Bootstrap's modal functionality remains intact
- Modal open/close behavior unchanged
- Clicking outside modal area behavior may need testing (backdrop usually handles this)

## Testing Checklist
- [ ] Test modals at scale level 1 (75%) - verify centered
- [ ] Test modals at scale level 3 (85%) - verify centered
- [ ] Test modals at scale level 5 (95%) - verify centered
- [ ] Test modals at scale level 6 (100% - default) - verify centered
- [ ] Test modals at scale level 7 (110%) - verify centered
- [ ] Test modals at scale level 8 (120%) - verify centered
- [ ] Verify Generate Starter Plan modal works and is centered
- [ ] Verify Save Program modal works and is centered
- [ ] Verify Program Library modal works and is centered
- [ ] Verify Progression Plan "Increase Weight" modal works and is centered
- [ ] Verify modal close on X button works
- [ ] Verify modal close on Cancel button works
- [ ] Test dark mode appearance

## Potential Follow-up Tasks
1. **Click-outside-to-close behavior:** With backdrop removed, clicking outside the modal may not close it. If this behavior is desired, it may need JavaScript handling.

2. **Other custom backdrops:** Search for any other custom backdrop implementations in CSS files:
   ```
   grep -r "::before" static/css/ | grep -i "backdrop\|fixed\|100vw"
   ```

3. **Consider alternative approaches if backdrop is needed:**
   - Counter-zoom the backdrop (like navbar)
   - Use JavaScript to dynamically size backdrop based on actual viewport
   - Use `transform: scale()` instead of `zoom` for UI scaling

## Related Files
- `templates/base.html` - Contains the zoom implementation on `<html>` element
- `static/js/accessibility.js` - Contains scale level management
- `static/css/styles_accessibility.css` - Contains scale CSS variables
- `app.py` - `inject_scale_level()` function provides zoom values to templates

## Session End Point
All identified backdrop issues have been addressed. Ready for testing.
