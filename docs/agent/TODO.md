# TODO (Responsive Tables)

## Infrastructure & Core Files
- [x] A-0 Create /docs/agent/ directory and checkpoint files
- [x] A-1 Create static/css/responsive.css with base tokens, sticky elements, priority classes
- [x] A-2 Create static/js/table-responsiveness.js with ResizeObserver and column toggles
- [x] A-3 Integrate responsive.css and table-responsiveness.js into base.html

## Template Updates
- [x] B-1 Update workout_plan.html: Add .tbl-wrap, priority classes, data-labels
- [ ] B-2 Update workout_log.html: Add .tbl-wrap, priority classes, data-labels
- [ ] B-3 Update weekly_summary.html: Add responsive wrappers and priority classes
- [ ] B-4 Update session_summary.html: Add responsive wrappers and priority classes
- [ ] B-5 Update volume_splitter.html: Add responsive wrappers (if has tables)

## Testing & Documentation
- [ ] C-1 Add viewport/zoom test notes to README
- [ ] C-2 Manual test: 1920×1080 @ 100% zoom - no horizontal scroll for key columns
- [ ] C-3 Manual test: ≤1366px width - compact/card mode activates
- [ ] C-4 Manual test: Zoom 90-125% - no layout breakage
- [ ] C-5 Test: Column visibility persistence via localStorage
- [ ] C-6 Test: Dark mode contrast passes WCAG AA

## Documentation
- [x] D-1 Add "Responsive Behavior & Adding New Columns" section to README

## Status Summary

### ✅ Completed
- Core CSS and JavaScript infrastructure
- Base template integration
- Workout Plan page fully responsive
- Comprehensive README documentation
- Checkpoint/resume system operational

### 🔄 In Progress
- Workout Log template (structure defined, needs final template update)

### ⏳ Pending
- Weekly Summary, Session Summary, Volume Splitter templates
- Manual cross-browser/zoom testing
- Visual regression testing (optional)

## Notes
- Prioritize workout_plan and workout_log (most used pages)
- Keep all changes scoped to table components
- No backend/database modifications
- Maintain accessibility throughout
- All infrastructure in place - remaining work is template updates only

