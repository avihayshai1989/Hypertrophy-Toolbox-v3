# Backend Refactor Roadmap

This document tracks the remaining backend work for the security/export stabilization effort and the muscle-normalization rollout. Items are grouped by theme and should stay in sync with the ongoing merge-progress notes.

## ✅ Recent Wins
- Restored XHR-aware error handling (`utils/errors.py`, `app.py`) with HTML fallback for browsers.
- Export summary endpoint now returns empty workbooks instead of 400s.
- Test database fixtures reset `exercises` data and enforce foreign keys on every run.
- Priority 0 suites and full pytest run are passing on main as of 2025-11-15.

## 🔁 In Flight
- **Regression guardrails**
  - [x] Add regression tests covering HTML error templates (404, 500) after the new helper.
  - [x] Reduce sqlite3 deprecation warnings by registering explicit timestamp/date converters.
- **Export polish**
  - [x] Document the empty-workbook behavior in API docs / README.
  - [ ] Confirm streaming export still behaves with zero rows and large datasets post-change.
    - Run `pytest tests/test_exports.py::TestExportMemorySafety::test_streaming_export_memory_usage` to catch regressions on memory usage.
    - Smoke-test `/export_large_dataset` via the Postman collection using the `large_workout_log` fixture dump and an empty database snapshot.

## 🧠 Muscle Normalization Initiative
- **Data Modeling**
  - [ ] Finalize canonical muscle mapping in `utils/normalization.py`.
    - Consolidate duplicates from `data/muscle_normalization.md` into a single source map and add TODO markers for any ambiguous groups.
    - Pair with `tests/test_normalize_muscles.py::test_canonical_primary_mapping` to lock in expected canonical names before refactoring helper logic.
  - [ ] Backfill normalized muscles for existing exercises (idempotent script).
    - Dry run `python normalize_muscles.py --db data/database.db --log logs/muscle_normalization.md --dryrun` and audit the diff-heavy sections of the report.
    - Capture a pre-migration snapshot via `scripts/migrate_isolated_muscles.py --database data/database.db` once ready to apply, ensuring the backup path is recorded in the merge notes.
    - Re-run the command without `--dryrun`, then validate spot-check rows with `tests/test_normalize_muscles.py::test_normalize_database_idempotent` to confirm no drift.
  - [ ] Audit downstream consumers (weekly/session summaries) for new fields.
    - Trace `normalized_primary_muscle` usage through `routes/session_summary.py`, `routes/weekly_summary.py`, and `routes/workout_plan.py` to confirm the canonical names propagate into the rendered templates.
    - Add instrumentation to `tests/test_session_summary.py` (or equivalent) capturing both pre- and post-normalization expectations; file a follow-up TODO if fixture coverage is missing.
    - Verify the exports stay aligned by cross-referencing `routes/exports.py` and the Excel sheet headers.
- **Testing**
  - [ ] Expand `tests/test_merge_muscle_normalization.py` with edge-case fixtures.
  - [ ] Add contract tests ensuring normalized fields appear in API responses.

## 🧾 Merge / Deployment Prep
- [ ] Refresh `merge_progress.md` with latest state once normalization scripts land.
- [ ] Update `README.md` quick-start or runbook to note the new migration sequence.
- [ ] Capture rollback plan for normalization (snapshot DB before script, restore path).

## 🔍 Observability & Logging
- [ ] Replace Windows-incompatible log emojis with ASCII across the codebase.
- [ ] Ensure export & normalization scripts emit structured INFO logs for monitoring.

## 📋 Post-Launch Follow-Up
- [ ] Re-run full regression suite on production dataset after migration.
- [ ] Gather user feedback on export changes (empty workbook) and adjust messaging.
- [ ] Schedule cleanup milestone to remove any temporary compatibility shims.

> Keep this checklist updated after each work session. If parallel tracks emerge (e.g., UI adjustments), split into separate docs to avoid drift.
