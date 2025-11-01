from flask import Blueprint, jsonify, request
from utils.filter_predicates import FilterPredicates
from utils.database import DatabaseHandler
from utils.errors import success_response, error_response
from utils.logger import get_logger

filters_bp = Blueprint('filters', __name__)
logger = get_logger()

# Define standard filter mapping
FILTER_MAPPING = {
    "Primary Muscle Group": "primary_muscle_group",
    "Secondary Muscle Group": "secondary_muscle_group",
    "Tertiary Muscle Group": "tertiary_muscle_group",
    "Advanced Isolated Muscles": "advanced_isolated_muscles",
    "Force": "force",
    "Equipment": "equipment",
    "Mechanic": "mechanic",
    "Utility": "utility",
    "Grips": "grips",
    "Stabilizers": "stabilizers",
    "Synergists": "synergists",
    "Difficulty": "difficulty"
}

# Whitelist for safe table and column names (prevents SQL injection)
ALLOWED_TABLES = {
    'exercises': 'exercises',
    'user_selection': 'user_selection',
    'workout_log': 'workout_log',
    'progression_goals': 'progression_goals',
}

ALLOWED_COLUMNS = {
    # Exercises table columns
    'primary_muscle_group': 'primary_muscle_group',
    'secondary_muscle_group': 'secondary_muscle_group',
    'tertiary_muscle_group': 'tertiary_muscle_group',
    'advanced_isolated_muscles': 'advanced_isolated_muscles',
    'force': 'force',
    'equipment': 'equipment',
    'mechanic': 'mechanic',
    'utility': 'utility',
    'grips': 'grips',
    'stabilizers': 'stabilizers',
    'synergists': 'synergists',
    'difficulty': 'difficulty',
    'exercise_name': 'exercise_name',
    # User selection columns
    'routine': 'routine',
    'exercise': 'exercise',
    'sets': 'sets',
    'min_rep_range': 'min_rep_range',
    'max_rep_range': 'max_rep_range',
    'rir': 'rir',
    'rpe': 'rpe',
    'weight': 'weight',
}


def validate_table_name(table: str) -> bool:
    """Validate that table name is in whitelist."""
    return table.lower() in {k.lower(): v for k, v in ALLOWED_TABLES.items()}


def validate_column_name(column: str) -> bool:
    """Validate that column name is in whitelist."""
    return column.lower() in {k.lower(): v for k, v in ALLOWED_COLUMNS.items()}

@filters_bp.route("/filter_exercises", methods=["POST"])
def filter_exercises():
    try:
        filters = request.get_json()
        if not filters:
            return error_response("VALIDATION_ERROR", "No filters provided", 400)

        logger.debug(f"Received filters: {filters}")

        # Convert frontend names to database column names
        sanitized_filters = {}
        for key, value in filters.items():
            db_field = FILTER_MAPPING.get(key)
            
            #  NEW CODE VERIFICATION: Check if field is in mapping
            if db_field is None:
                logger.warning(f"🔴 NEW CODE: Unknown filter field rejected: {key}")
                return error_response("VALIDATION_ERROR", f"Invalid filter column: {key}", 400)
            
            if value:  # Only include non-empty values
                # Validate column is whitelisted
                if validate_column_name(db_field):
                    sanitized_filters[db_field] = value
                else:
                    logger.warning(f"Invalid column in filter: {db_field}")
                    return error_response("VALIDATION_ERROR", f"Invalid filter column: {key}", 400)

        logger.debug(f"Sanitized filters: {sanitized_filters}")
        exercise_names = FilterPredicates.get_exercises(filters=sanitized_filters)
        logger.debug(f"Found {len(exercise_names)} matching exercises")

        return jsonify(success_response(data=exercise_names))
    except Exception as e:
        logger.exception("Error in filter_exercises")
        return error_response("INTERNAL_ERROR", "Failed to filter exercises", 500)

@filters_bp.route("/get_all_exercises")
def get_all_exercises():
    """Get all exercises without any filters."""
    try:
        exercise_names = FilterPredicates.get_exercises()
        return jsonify(success_response(data=exercise_names))
    except Exception as e:
        logger.exception("Error in get_all_exercises")
        return error_response("INTERNAL_ERROR", "Failed to fetch exercises", 500) 

@filters_bp.route("/get_unique_values/<table>/<column>")
def get_unique_values(table, column):
    """Get unique values for a given column in a table."""
    try:
        # Validate table and column names against whitelist
        if not validate_table_name(table):
            logger.warning(f"Invalid table name: {table}")
            return error_response("VALIDATION_ERROR", f"Invalid table: {table}", 400)
        
        if not validate_column_name(column):
            logger.warning(f"Invalid column name: {column}")
            return error_response("VALIDATION_ERROR", f"Invalid column: {column}", 400)
        
        # Get safe table and column names from whitelist
        safe_table = ALLOWED_TABLES.get(table.lower())
        safe_column = ALLOWED_COLUMNS.get(column.lower())
        
        if not safe_table or not safe_column:
            return error_response("VALIDATION_ERROR", "Invalid table or column", 400)
        
        # Use parameterized query with safe names
        query = f"SELECT DISTINCT {safe_column} FROM {safe_table} WHERE {safe_column} IS NOT NULL ORDER BY {safe_column} ASC"
        with DatabaseHandler() as db:
            results = db.fetch_all(query)
            values = [row[safe_column] for row in results if row.get(safe_column)]
            return jsonify(success_response(data=values))
    except Exception as e:
        logger.exception(f"Error fetching unique values for {table}.{column}")
        return error_response("INTERNAL_ERROR", "Failed to fetch unique values", 500) 

@filters_bp.route("/get_filtered_exercises", methods=["POST"])
def get_filtered_exercises():
    """Get exercises based on multiple filter criteria."""
    try:
        filters = request.get_json()
        if not filters:
            return error_response("VALIDATION_ERROR", "No filters provided", 400)
        
        query = """
        SELECT exercise_name
        FROM exercises
        WHERE 1=1
        """
        params = []
        
        for field, value in filters.items():
            # Validate column name is whitelisted
            if not validate_column_name(field):
                logger.warning(f"Invalid column in filter: {field}")
                return error_response("VALIDATION_ERROR", f"Invalid filter column: {field}", 400)
            
            if value:
                safe_column = ALLOWED_COLUMNS.get(field.lower())
                query += f" AND {safe_column} LIKE ?"
                params.append(f"%{value}%")
                
        query += " ORDER BY exercise_name ASC"
        
        with DatabaseHandler() as db:
            results = db.fetch_all(query, params)
            exercises = [row['exercise_name'] for row in results]
            return jsonify(success_response(data=exercises))
    except Exception as e:
        logger.exception("Error filtering exercises")
        return error_response("INTERNAL_ERROR", "Failed to filter exercises", 500) 