-- One-shot SQL for data merge + normalization
-- Run this in SQLite GUI/CLI or via sqlite3 command-line tool
-- Adjust paths as needed. On Windows GUIs, forward slashes help with spaces in paths.

-- Attach both DB files (use forward slashes to avoid space issues)
ATTACH DATABASE 'C:/Users/aatiya/IdeaProjects/Hypertrophy-Toolbox-v3/data/database.db' AS live;
ATTACH DATABASE 'C:/Users/aatiya/IdeaProjects/Hypertrophy-Toolbox-v3/data/Database_backup/work with/database_backup.db' AS backup;

-- Ensure target tables exist
CREATE TABLE IF NOT EXISTS live.exercises (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  exercise_name TEXT NOT NULL,
  primary_muscle_group   TEXT,
  secondary_muscle_group TEXT,
  tertiary_muscle_group  TEXT,
  advanced_isolated_muscles TEXT,
  utility TEXT, grips TEXT, stabilizers TEXT, synergists TEXT,
  force TEXT, equipment TEXT, mechanic TEXT, difficulty TEXT
);

CREATE TABLE IF NOT EXISTS live.user_selection (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  routine TEXT NOT NULL,
  exercise TEXT NOT NULL,
  sets INTEGER NOT NULL,
  min_rep_range INTEGER NOT NULL,
  max_rep_range INTEGER NOT NULL,
  rir INTEGER DEFAULT 0,
  rpe REAL,
  weight REAL NOT NULL,
  FOREIGN KEY (exercise) REFERENCES exercises(exercise_name)
);

-- Merge exercises (skip duplicates by name)
INSERT INTO live.exercises (
  exercise_name, primary_muscle_group, secondary_muscle_group, tertiary_muscle_group,
  advanced_isolated_muscles, utility, grips, stabilizers, synergists,
  force, equipment, mechanic, difficulty
)
SELECT
  b.exercise_name, b.primary_muscle_group, b.secondary_muscle_group, b.tertiary_muscle_group,
  b.advanced_isolated_muscles, b.utility, b.grips, b.stabilizers, b.synergists,
  b.force, b.equipment, b.mechanic, b.difficulty
FROM backup.exercises b
WHERE NOT EXISTS (
  SELECT 1 FROM live.exercises l WHERE l.exercise_name = b.exercise_name
);

-- Normalize delimiter for isolated muscles (semicolons → commas)
UPDATE live.exercises
SET advanced_isolated_muscles = REPLACE(advanced_isolated_muscles, ';', ',')
WHERE advanced_isolated_muscles LIKE '%;%';

-- Minimal taxonomy lifts for common tokens (expand later as needed)
UPDATE live.exercises
SET advanced_isolated_muscles = REPLACE(advanced_isolated_muscles, 'Anterior Deltoid', 'anterior-deltoid')
WHERE advanced_isolated_muscles LIKE '%Anterior Deltoid%';

UPDATE live.exercises
SET advanced_isolated_muscles = REPLACE(advanced_isolated_muscles, 'Lateral Head Triceps', 'lateral-head-triceps')
WHERE advanced_isolated_muscles LIKE '%Lateral Head Triceps%';

UPDATE live.exercises
SET advanced_isolated_muscles = REPLACE(advanced_isolated_muscles, 'Medial Head Triceps', 'medial-head-triceps')
WHERE advanced_isolated_muscles LIKE '%Medial Head Triceps%';

UPDATE live.exercises
SET advanced_isolated_muscles = REPLACE(advanced_isolated_muscles, 'Long Head Triceps', 'long-head-triceps')
WHERE advanced_isolated_muscles LIKE '%Long Head Triceps%';

-- Angle-based chest mapping (quick win)
UPDATE live.exercises
SET advanced_isolated_muscles = REPLACE(advanced_isolated_muscles, 'Chest', 'upper-pectoralis')
WHERE exercise_name LIKE '%Incline%' AND advanced_isolated_muscles LIKE '%Chest%';

UPDATE live.exercises
SET advanced_isolated_muscles = REPLACE(advanced_isolated_muscles, 'Chest', 'mid-lower-pectoralis')
WHERE exercise_name LIKE '%Decline%' AND advanced_isolated_muscles LIKE '%Chest%';

UPDATE live.exercises
SET advanced_isolated_muscles = REPLACE(advanced_isolated_muscles, 'Chest', 'mid-lower-pectoralis')
WHERE advanced_isolated_muscles LIKE '%Chest%'
  AND ( (exercise_name LIKE '%Bench Press%' OR exercise_name LIKE '%Chest Fly%' OR
         exercise_name LIKE '%Pec Fly%'    OR exercise_name LIKE '%Chest Press%')
        AND exercise_name NOT LIKE '%Incline%' AND exercise_name NOT LIKE '%Decline%' );

-- Optional: workout_log (skip if table doesn't exist)
CREATE TABLE IF NOT EXISTS live.workout_log (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  routine TEXT, exercise TEXT,
  planned_sets INTEGER, planned_min_reps INTEGER, planned_max_reps INTEGER,
  planned_rir INTEGER, planned_rpe REAL, planned_weight REAL,
  scored_min_reps INTEGER, scored_max_reps INTEGER, scored_rir INTEGER, scored_rpe REAL, scored_weight REAL,
  last_progression_date DATE, created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  workout_plan_id INTEGER,
  FOREIGN KEY (workout_plan_id) REFERENCES user_selection(id)
);

-- Merge workout_log if the table exists in backup
INSERT OR IGNORE INTO live.workout_log (
  routine, exercise, 
  planned_sets, planned_min_reps, planned_max_reps, planned_rir, planned_rpe, planned_weight,
  scored_min_reps, scored_max_reps, scored_rir, scored_rpe, scored_weight,
  last_progression_date, created_at, workout_plan_id
)
SELECT 
  b.routine, b.exercise,
  b.planned_sets, b.planned_min_reps, b.planned_max_reps, b.planned_rir, b.planned_rpe, b.planned_weight,
  b.scored_min_reps, b.scored_max_reps, b.scored_rir, b.scored_rpe, b.scored_weight,
  b.last_progression_date, b.created_at, b.workout_plan_id
FROM backup.workout_log b
WHERE EXISTS (SELECT 1 FROM backup.sqlite_master WHERE type='table' AND name='workout_log');

-- Merge user_selection (avoid dupes via composite)
INSERT INTO live.user_selection (
  routine, exercise, sets, min_rep_range, max_rep_range, rir, rpe, weight
)
SELECT
  b.routine, b.exercise, b.sets, b.min_rep_range, b.max_rep_range,
  COALESCE(b.rir,0), b.rpe, b.weight
FROM backup.user_selection b
WHERE NOT EXISTS (
  SELECT 1 FROM live.user_selection l
  WHERE l.routine = b.routine
    AND l.exercise = b.exercise
    AND l.sets = b.sets
    AND l.min_rep_range = b.min_rep_range
    AND l.max_rep_range = b.max_rep_range
    AND COALESCE(l.rir,0) = COALESCE(b.rir,0)
    AND l.weight = b.weight
);

-- Sanity checks
SELECT COUNT(*) AS exercises_rows      FROM live.exercises;
SELECT COUNT(*) AS user_selection_rows FROM live.user_selection;
SELECT COUNT(*) AS has_isolated_values FROM live.exercises
 WHERE advanced_isolated_muscles IS NOT NULL AND TRIM(advanced_isolated_muscles) <> '';

-- Display sample of normalized values
SELECT exercise_name, advanced_isolated_muscles 
FROM live.exercises 
WHERE advanced_isolated_muscles IS NOT NULL 
  AND TRIM(advanced_isolated_muscles) <> ''
LIMIT 10;
