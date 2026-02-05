"""
Pytest configuration and fixtures for Priority 0 security tests.
"""
import pytest
import sqlite3
import tempfile
import os
from pathlib import Path
from flask import Flask
from utils.database import DatabaseHandler, add_progression_goals_table, add_volume_tracking_tables
from utils.db_initializer import initialize_database
from routes.workout_plan import workout_plan_bp, initialize_exercise_order
from routes.filters import filters_bp
from routes.workout_log import workout_log_bp
from routes.weekly_summary import weekly_summary_bp
from routes.session_summary import session_summary_bp
from routes.exports import exports_bp
from routes.main import main_bp
from routes.progression_plan import progression_plan_bp
from routes.volume_splitter import volume_splitter_bp
from routes.program_backup import program_backup_bp
from utils.program_backup import initialize_backup_tables
import sys


# Override config before importing app
os.environ['TESTING'] = '1'
TEST_DB_PATH = os.path.join(tempfile.gettempdir(), 'test_hypertrophy_toolbox.db')


@pytest.fixture(scope='session')
def test_db_path():
    """Create a temporary database file for testing."""
    # Remove test DB if it exists
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)
    
    yield TEST_DB_PATH
    
    # Cleanup
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)


@pytest.fixture(scope='session')
def app(test_db_path):
    """Create Flask app with test configuration."""
    # Override DB_FILE in config
    import utils.config
    original_db_file = utils.config.DB_FILE
    utils.config.DB_FILE = test_db_path
    
    # Create test app
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    app.url_map.strict_slashes = False
    
    # Register blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(workout_log_bp)
    app.register_blueprint(weekly_summary_bp)
    app.register_blueprint(session_summary_bp)
    app.register_blueprint(exports_bp)
    app.register_blueprint(filters_bp)
    app.register_blueprint(workout_plan_bp)
    app.register_blueprint(progression_plan_bp)
    app.register_blueprint(volume_splitter_bp)
    app.register_blueprint(program_backup_bp)
    
    # Add erase-data endpoint (defined in app.py, not a blueprint)
    from flask import jsonify
    from utils.errors import success_response, error_response
    
    @app.route('/erase-data', methods=['POST'])
    def erase_data():
        try:
            # Drop ALL tables including backup tables (full reset)
            with DatabaseHandler() as db:
                tables = [
                    'program_backup_items',  # Drop child table first (FK constraint)
                    'program_backups',        # Then parent backup table
                    'user_selection',
                    'progression_goals',
                    'muscle_volumes',
                    'volume_plans',
                    'workout_log'
                ]
                for table in tables:
                    db.execute_query(f"DROP TABLE IF EXISTS {table}")
            
            # Reinitialize database
            initialize_database(force=True)
            add_progression_goals_table()
            add_volume_tracking_tables()
            initialize_exercise_order()
            initialize_backup_tables()
            
            return jsonify(success_response(
                data=None,
                message='All data has been erased and tables reinitialized successfully.'
            ))
        except Exception as e:
            return error_response("INTERNAL_ERROR", "Failed to erase data", 500)
    
    # Initialize test database
    with app.app_context():
        initialize_database()
        add_progression_goals_table()
        add_volume_tracking_tables()
        initialize_exercise_order()
        initialize_backup_tables()
    
    # Restore original DB_FILE
    utils.config.DB_FILE = original_db_file
    
    yield app
    
    # Cleanup
    if os.path.exists(test_db_path):
        os.remove(test_db_path)


@pytest.fixture(scope='function')
def client(app, test_db_path):
    """Flask test client."""
    # Override DB_FILE for each test
    import utils.config
    original_db_file = utils.config.DB_FILE
    utils.config.DB_FILE = test_db_path
    
    with app.test_client() as client:
        yield client
    
    # Restore original DB_FILE
    utils.config.DB_FILE = original_db_file


@pytest.fixture(scope='function')
def db_handler(app, test_db_path):
    """Database handler with test DB and foreign keys enabled."""
    import utils.config
    original_db_file = utils.config.DB_FILE
    utils.config.DB_FILE = test_db_path
    
    # Pass explicit path to ensure we use test database
    handler = DatabaseHandler(test_db_path)
    
    # Verify foreign keys are enabled
    with handler.connection:
        result = handler.fetch_one("PRAGMA foreign_keys;")
        assert result['foreign_keys'] == 1, "Foreign keys must be enabled"
    
    yield handler
    
    handler.close()
    utils.config.DB_FILE = original_db_file


@pytest.fixture(scope='function')
def clean_db(db_handler):
    """Clean database before each test."""
    # Delete all data but keep tables
    with db_handler.connection:
        tables = [
            'program_backup_items',
            'program_backups',
            'exercise_isolated_muscles',
            'workout_log',
            'user_selection',
            'progression_goals',
            'muscle_volumes',
            'volume_plans',
            'exercises',
        ]
        for table in tables:
            db_handler.execute_query(f"DELETE FROM {table}")
    
    yield db_handler


@pytest.fixture
def exercise_factory(clean_db):
    """Factory for creating test exercises."""
    def _create_exercise(name, **kwargs):
        """Create an exercise with optional attributes."""
        defaults = {
            'primary_muscle_group': 'Chest',
            'secondary_muscle_group': 'Triceps',
            'tertiary_muscle_group': 'Shoulders',
            'force': 'Push',
            'equipment': 'Barbell',
            'mechanic': 'Compound',
            'utility': 'Basic',
            'difficulty': 'Intermediate'
        }
        defaults.update(kwargs)
        
        query = """
        INSERT INTO exercises (exercise_name, primary_muscle_group, secondary_muscle_group,
                              tertiary_muscle_group, force, equipment, mechanic, utility, difficulty)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            name,
            defaults.get('primary_muscle_group'),
            defaults.get('secondary_muscle_group'),
            defaults.get('tertiary_muscle_group'),
            defaults.get('force'),
            defaults.get('equipment'),
            defaults.get('mechanic'),
            defaults.get('utility'),
            defaults.get('difficulty')
        )
        
        clean_db.execute_query(query, params)
        return name
    
    return _create_exercise


@pytest.fixture
def workout_plan_factory(clean_db, exercise_factory):
    """Factory for creating test workout plan entries."""
    def _create_workout_plan(exercise_name=None, routine="GYM - Full Body - Workout A", **kwargs):
        """Create a workout plan entry."""
        if exercise_name is None:
            exercise_name = exercise_factory("Test Exercise")
        
        defaults = {
            'routine': routine,
            'exercise': exercise_name,
            'sets': 3,
            'min_rep_range': 6,
            'max_rep_range': 8,
            'rir': 3,
            'rpe': 7.0,
            'weight': 50.0
        }
        defaults.update(kwargs)
        
        query = """
        INSERT INTO user_selection (routine, exercise, sets, min_rep_range, max_rep_range, rir, rpe, weight)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            defaults['routine'],
            defaults['exercise'],
            defaults['sets'],
            defaults['min_rep_range'],
            defaults['max_rep_range'],
            defaults['rir'],
            defaults.get('rpe'),
            defaults['weight']
        )
        
        clean_db.execute_query(query, params)
        
        # Get the inserted ID
        result = clean_db.fetch_one("SELECT last_insert_rowid() as id")
        return result['id']
    
    return _create_workout_plan


@pytest.fixture
def workout_log_factory(clean_db, workout_plan_factory):
    """Factory for creating test workout log entries."""
    def _create_workout_log(plan_id=None, **kwargs):
        """Create a workout log entry."""
        if plan_id is None:
            plan_id = workout_plan_factory()
        
        defaults = {
            'workout_plan_id': plan_id,
            'routine': "GYM - Full Body - Workout A",
            'exercise': "Test Exercise",
            'planned_sets': 3,
            'planned_min_reps': 6,
            'planned_max_reps': 8,
            'planned_rir': 3,
            'planned_rpe': 7.0,
            'planned_weight': 50.0,
            'scored_min_reps': 6,
            'scored_max_reps': 8,
            'scored_rir': 2,
            'scored_rpe': 8.0,
            'scored_weight': 52.5
        }
        defaults.update(kwargs)
        
        query = """
        INSERT INTO workout_log (workout_plan_id, routine, exercise, planned_sets, planned_min_reps,
                                planned_max_reps, planned_rir, planned_rpe, planned_weight,
                                scored_min_reps, scored_max_reps, scored_rir, scored_rpe, scored_weight)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            defaults['workout_plan_id'],
            defaults['routine'],
            defaults['exercise'],
            defaults['planned_sets'],
            defaults['planned_min_reps'],
            defaults['planned_max_reps'],
            defaults['planned_rir'],
            defaults.get('planned_rpe'),
            defaults['planned_weight'],
            defaults['scored_min_reps'],
            defaults['scored_max_reps'],
            defaults['scored_rir'],
            defaults.get('scored_rpe'),
            defaults['scored_weight']
        )
        
        clean_db.execute_query(query, params)
        
        # Get the inserted ID
        result = clean_db.fetch_one("SELECT last_insert_rowid() as id")
        return result['id']
    
    return _create_workout_log

