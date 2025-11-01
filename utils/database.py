from utils.config import DB_FILE
import sqlite3
from utils.logger import get_logger

logger = get_logger()

def get_db_connection():
    """Get a database connection."""
    conn = sqlite3.connect(DB_FILE)
    # Enable foreign keys
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

class DatabaseHandler:
    """
    Handles low-level database operations with context management.
    """

    def __init__(self):
        """
        Initialize the database connection and cursor.
        """
        self.connection = sqlite3.connect(DB_FILE)
        self.connection.row_factory = sqlite3.Row  # Return results as dictionaries
        self.cursor = self.connection.cursor()
        # Enable Write-Ahead Logging (WAL) mode
        self.connection.execute("PRAGMA journal_mode=WAL;")
        # Enable foreign keys (must be enabled per connection in SQLite)
        self.connection.execute("PRAGMA foreign_keys = ON;")

    def execute_query(self, query, params=None):
        """
        Executes a query with optional parameters.
        :param query: SQL query to execute.
        :param params: Optional parameters for parameterized queries.
        """
        try:
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)
            self.connection.commit()
            logger.debug(f"Query executed successfully: {query[:100]}... | Params: {params}")
        except sqlite3.Error as e:
            logger.error(f"Database error during query execution: {e} | Query: {query[:100]}... | Params: {params}", exc_info=True)
            raise e

    def fetch_all(self, query, params=None):
        """
        Fetch all rows for a query.
        :param query: SQL query to execute.
        :param params: Optional parameters for parameterized queries.
        :return: List of all rows fetched as dictionaries.
        """
        try:
            if not isinstance(params, (list, tuple)) and params is not None:
                params = [params]  # Convert single parameter to list
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)
            results = self.cursor.fetchall()
            return [dict(row) for row in results] if results else []
        except sqlite3.Error as e:
            logger.error(f"Database error: {e} | Query: {query[:100]}... | Params: {params}", exc_info=True)
            raise e

    def fetch_one(self, query, params=None):
        """
        Fetch a single row for a query.
        :param query: SQL query to execute.
        :param params: Optional parameters for parameterized queries.
        :return: Single row fetched as a dictionary.
        """
        try:
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)
            result = self.cursor.fetchone()
            logger.debug(f"Fetch one successful: {query[:100]}... | Params: {params}")
            return dict(result) if result else None
        except sqlite3.Error as e:
            logger.error(f"Database fetch error: {e} | Query: {query[:100]}... | Params: {params}", exc_info=True)
            raise e

    def close(self):
        """
        Close the database connection.
        """
        self.connection.close()
        logger.debug("Database connection closed.")

    def __enter__(self):
        """
        Context management entry.
        :return: The instance itself for use in `with` statements.
        """
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Context management exit.
        Automatically closes the database connection.
        """
        self.close()

    def get_exercise_details(self, exercise_name):
        query = """
        SELECT 
            primary_muscle_group,
            secondary_muscle_group,
            tertiary_muscle_group,
            advanced_isolated_muscles,
            utility,
            grips,
            stabilizers,
            synergists
        FROM exercises 
        WHERE exercise_name = ?
        """

    def add_progression_goals_table(self):
        """Add progression_goals table if it doesn't exist."""
        try:
            self.execute_query("""
                CREATE TABLE IF NOT EXISTS progression_goals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    exercise TEXT NOT NULL,
                    goal_type TEXT NOT NULL,
                    current_value REAL,
                    target_value REAL,
                    goal_date DATE NOT NULL,
                    created_at DATETIME NOT NULL,
                    completed BOOLEAN DEFAULT 0,
                    completed_at DATETIME
                )
            """)
            logger.info("Progression goals table created successfully")
        except sqlite3.Error as e:
            logger.error(f"Error creating progression_goals table: {e}", exc_info=True)
            raise e

def initialize_database():
    """Initialize the database with required tables."""
    with DatabaseHandler() as db:
        # Create exercises table
        db.execute_query("""
            CREATE TABLE IF NOT EXISTS exercises (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                exercise_name TEXT UNIQUE NOT NULL,
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
            )
        """)

        # Create user_selection table
        db.execute_query("""
            CREATE TABLE IF NOT EXISTS user_selection (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                routine TEXT NOT NULL,
                exercise TEXT NOT NULL,
                sets INTEGER NOT NULL,
                min_rep_range INTEGER NOT NULL,
                max_rep_range INTEGER NOT NULL,
                rir INTEGER DEFAULT 0,
                rpe REAL,
                weight REAL NOT NULL,
                FOREIGN KEY (exercise) REFERENCES exercises(exercise_name) ON DELETE CASCADE
            )
        """)

        # Create workout_log table
        db.execute_query("""
            CREATE TABLE IF NOT EXISTS workout_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                routine TEXT,
                exercise TEXT,
                planned_sets INTEGER,
                planned_min_reps INTEGER,
                planned_max_reps INTEGER,
                planned_rir INTEGER,
                planned_rpe REAL,
                planned_weight REAL,
                scored_min_reps INTEGER,
                scored_max_reps INTEGER,
                scored_rir INTEGER,
                scored_rpe REAL,
                scored_weight REAL,
                last_progression_date DATE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                workout_plan_id INTEGER,
                FOREIGN KEY (workout_plan_id) REFERENCES user_selection(id) ON DELETE CASCADE
            )
        """)
        
        # Create progression_goals table
        db.add_progression_goals_table()

def add_rpe_column():
    """Add RPE column to existing tables if it doesn't exist."""
    alter_queries = [
        """
        ALTER TABLE user_selection 
        ADD COLUMN rpe REAL;
        """,
        """
        ALTER TABLE workout_log
        ADD COLUMN planned_rpe REAL;
        """
    ]

    with DatabaseHandler() as db_handler:
        for query in alter_queries:
            try:
                db_handler.execute_query(query)
                logger.info(f"Added RPE column: {query[:100]}...")
            except sqlite3.OperationalError as e:
                if "duplicate column name" not in str(e).lower():
                    logger.error(f"Error adding RPE column: {e}", exc_info=True)
                    raise e

def add_progression_goals_table():
    """Add progression_goals table if it doesn't exist."""
    with DatabaseHandler() as db:
        db.add_progression_goals_table()

def add_volume_tracking_tables():
    """Add tables for volume tracking"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Volume Plans table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS volume_plans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            training_days INTEGER NOT NULL,
            created_at DATETIME NOT NULL
        )
    ''')
    
    # Muscle Volumes table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS muscle_volumes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plan_id INTEGER NOT NULL,
            muscle_group TEXT NOT NULL,
            weekly_sets INTEGER NOT NULL,
            sets_per_session REAL NOT NULL,
            status TEXT NOT NULL,
            FOREIGN KEY (plan_id) REFERENCES volume_plans (id) ON DELETE CASCADE
        )
    ''')
    
    conn.commit()
    conn.close()
