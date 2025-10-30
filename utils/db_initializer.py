import sqlite3
from utils.config import DB_FILE
from .database import DatabaseHandler

def initialize_exercises_table():
    """Create the exercises table if it doesn't exist."""
    query = """
    CREATE TABLE IF NOT EXISTS exercises (
        exercise_name TEXT PRIMARY KEY,
        primary_muscle_group TEXT,
        secondary_muscle_group TEXT,
        tertiary_muscle_group TEXT,
        advanced_isolated_muscles TEXT,
        utility TEXT,
        grips TEXT,
        stabilizers TEXT,
        synergists TEXT,
        force TEXT,
        equipment TEXT,
        mechanic TEXT,
        difficulty TEXT
    );
    """
    try:
        with DatabaseHandler() as db:
            db.execute_query(query)
            print("Exercises table initialized successfully")
    except Exception as e:
        print(f"Error initializing exercises table: {e}")

def initialize_user_selection_table():
    """Create the user_selection table if it doesn't exist."""
    query = """
    CREATE TABLE IF NOT EXISTS user_selection (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        routine TEXT NOT NULL,
        exercise TEXT NOT NULL,
        sets INTEGER NOT NULL,
        min_rep_range INTEGER NOT NULL,
        max_rep_range INTEGER NOT NULL,
        rir INTEGER,
        rpe REAL,
        weight REAL NOT NULL,
        UNIQUE (routine, exercise, sets, min_rep_range, max_rep_range, rir, rpe, weight)
    );
    """
    try:
        with DatabaseHandler() as db:
            db.execute_query(query)
            print("User selection table initialized successfully")
    except Exception as e:
        print(f"Error initializing user selection table: {e}")

def initialize_workout_log_table():
    """Create the workout_log table if it doesn't exist."""
    query = """
    CREATE TABLE IF NOT EXISTS workout_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        workout_plan_id INTEGER,
        routine TEXT NOT NULL,
        exercise TEXT NOT NULL,
        planned_sets INTEGER,
        planned_min_reps INTEGER,
        planned_max_reps INTEGER,
        planned_rir INTEGER,
        planned_rpe REAL,
        planned_weight REAL,
        scored_weight REAL,
        scored_min_reps INTEGER,
        scored_max_reps INTEGER,
        scored_rir INTEGER,
        scored_rpe REAL,
        last_progression_date TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (workout_plan_id) REFERENCES user_selection(id)
    );
    """
    try:
        with DatabaseHandler() as db:
            db.execute_query(query)
            print("Workout log table initialized successfully")
    except Exception as e:
        print(f"Error initializing workout log table: {e}")

def initialize_database():
    """Initialize all database tables."""
    try:
        initialize_exercises_table()
        initialize_user_selection_table()
        initialize_workout_log_table()
        print("All database tables initialized successfully")
    except Exception as e:
        print(f"Error during database initialization: {e}")
