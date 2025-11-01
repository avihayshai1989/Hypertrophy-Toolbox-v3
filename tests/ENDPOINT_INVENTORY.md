# Endpoint Inventory

**Generated:** 2025-01-27  
**Source:** Auto-discovered from Flask app routes

## Endpoint Map

| Method | Path | Blueprint | Handler | Source File |
|---|---|---|---|---|
| GET | `/` | `main_bp` | `index()` | `routes/main.py:5` |
| GET | `/workout_log` | `workout_log_bp` | `workout_log()` | `routes/workout_log.py:15` |
| POST | `/update_workout_log` | `workout_log_bp` | `update_workout_log()` | `routes/workout_log.py:30` |
| POST | `/delete_workout_log` | `workout_log_bp` | `delete_workout_log()` | `routes/workout_log.py:60` |
| POST | `/update_progression_date` | `workout_log_bp` | `update_progression_date()` | `routes/workout_log.py:79` |
| GET | `/check_progression/<int:log_id>` | `workout_log_bp` | `check_progression()` | `routes/workout_log.py:96` |
| GET | `/get_workout_logs` | `workout_log_bp` | `get_logs()` | `routes/workout_log.py:145` |
| GET | `/export_workout_log` | `workout_log_bp` | `export_workout_log()` | `routes/workout_log.py:165` |
| POST | `/export_to_workout_log` | `workout_log_bp` | `export_to_workout_log()` | `routes/workout_log.py:215` |
| GET | `/weekly_summary` | `weekly_summary_bp` | `weekly_summary()` | `routes/weekly_summary.py:17` |
| GET | `/session_summary` | `session_summary_bp` | `session_summary()` | `routes/session_summary.py:17` |
| GET | `/export_to_excel` | `exports_bp` | `export_to_excel()` | `routes/exports.py:59` |
| POST | `/export_to_workout_log` | `exports_bp` | `export_to_workout_log()` | `routes/exports.py:194` |
| POST | `/export_summary` | `exports_bp` | `export_summary()` | `routes/exports.py:231` |
| **POST** | **`/filter_exercises`** | **`filters_bp`** | **`filter_exercises()`** | **`routes/filters.py:70`** — **PRIORITY 0** |
| **GET** | **`/get_all_exercises`** | **`filters_bp`** | **`get_all_exercises()`** | **`routes/filters.py:100`** — **PRIORITY 0** |
| **GET** | **`/get_unique_values/<table>/<column>`** | **`filters_bp`** | **`get_unique_values()`** | **`routes/filters.py:110`** — **PRIORITY 0** |
| POST | `/get_filtered_exercises` | `filters_bp` | `get_filtered_exercises()` | `routes/filters.py:140` |
| GET | `/workout_plan` | `workout_plan_bp` | `workout_plan()` | `routes/workout_plan.py:36` |
| **POST** | **`/add_exercise`** | **`workout_plan_bp`** | **`add_exercise()`** | **`routes/workout_plan.py:59`** — **PRIORITY 0** |
| **GET** | **`/get_exercise_details/<int:exercise_id>`** | **`workout_plan_bp`** | **`get_exercise_details()`** | **`routes/workout_plan.py:86`** — **PRIORITY 0** |
| **GET** | **`/get_workout_plan`** | **`workout_plan_bp`** | **`get_workout_plan()`** | **`routes/workout_plan.py:110`** — **PRIORITY 0** |
| **POST** | **`/remove_exercise`** | **`workout_plan_bp`** | **`remove_exercise()`** | **`routes/workout_plan.py:155`** — **PRIORITY 0** |
| GET | `/get_routine_options` | `workout_plan_bp` | `get_routine_options()` | `routes/workout_plan.py:178` |
| GET | `/get_user_selection` | `workout_plan_bp` | `get_user_selection()` | `routes/workout_plan.py:256` |
| **GET** | **`/get_exercise_info/<exercise_name>`** | **`workout_plan_bp`** | **`get_exercise_info()`** | **`routes/workout_plan.py:282`** — **PRIORITY 0** |
| **GET** | **`/get_routine_exercises/<routine>`** | **`workout_plan_bp`** | **`get_routine_exercises()`** | **`routes/workout_plan.py:300`** — **PRIORITY 0** |
| **POST** | **`/update_exercise`** | **`workout_plan_bp`** | **`update_exercise()`** | **`routes/workout_plan.py:328`** — **PRIORITY 0** |
| **POST** | **`/update_exercise_order`** | **`workout_plan_bp`** | **`update_exercise_order()`** | **`routes/workout_plan.py:398`** — **PRIORITY 0** |
| GET | `/progression` | `progression_plan_bp` | `progression_plan()` | `routes/progression_plan.py:13` |
| POST | `/get_exercise_suggestions` | `progression_plan_bp` | `get_suggestions()` | `routes/progression_plan.py:46` |
| POST | `/save_progression_goal` | `progression_plan_bp` | `save_goal()` | `routes/progression_plan.py:130` |
| DELETE | `/delete_progression_goal/<int:goal_id>` | `progression_plan_bp` | `delete_goal()` | `routes/progression_plan.py:140` |
| POST | `/get_current_value` | `progression_plan_bp` | `get_current_value()` | `routes/progression_plan.py:159` |
| GET | `/volume_splitter` | `volume_splitter_bp` | `volume_splitter()` | `routes/volume_splitter.py:23` |
| POST | `/api/calculate_volume` | `volume_splitter_bp` | `calculate_volume()` | `routes/volume_splitter.py:29` |
| GET | `/api/volume_history` | `volume_splitter_bp` | `get_volume_history()` | `routes/volume_splitter.py:62` |
| POST | `/api/save_volume_plan` | `volume_splitter_bp` | `save_volume_plan()` | `routes/volume_splitter.py:98` |
| GET | `/api/volume_plan/<int:plan_id>` | `volume_splitter_bp` | `get_volume_plan()` | `routes/volume_splitter.py:107` |
| POST | `/api/export_volume_excel` | `volume_splitter_bp` | `export_volume_excel()` | `routes/volume_splitter.py:142` |
| POST | `/erase-data` | — | `erase_data()` | `app.py:74` |

## Priority 0 Endpoints (Standardized Errors + Security)

Endpoints marked **PRIORITY 0** have been updated with:
- ✅ Whitelist validation (where applicable)
- ✅ Standardized error responses `{"ok": false, "error": {...}}`
- ✅ Standardized success responses `{"ok": true, "data": ...}`
- ✅ Structured logging

**Total Endpoints:** 38 routes  
**Priority 0 Endpoints:** 10 routes

