from flask import Blueprint, jsonify, request
from utils.filter_predicates import FilterPredicates
from utils.database import DatabaseHandler
from utils.errors import success_response, error_response
from utils.logger import get_logger
from utils.constants import DIFFICULTY, MECHANIC, UTILITY

filters_bp = Blueprint('filters', __name__)
logger = get_logger()

# Define standard filter mapping - supports both display names and snake_case keys
FILTER_MAPPING = {
    # Display names (from data-filter-key attribute)
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
    "Difficulty": "difficulty",
    # Snake_case keys (from select element id fallback)
    "primary_muscle_group": "primary_muscle_group",
    "secondary_muscle_group": "secondary_muscle_group",
    "tertiary_muscle_group": "tertiary_muscle_group",
    "advanced_isolated_muscles": "advanced_isolated_muscles",
    "equipment": "equipment",
    "mechanic": "mechanic",
    "utility": "utility",
    "grips": "grips",
    "stabilizers": "stabilizers",
    "synergists": "synergists",
    "difficulty": "difficulty",
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


ENUM_VALUE_MAP = {
    'mechanic': sorted(set(MECHANIC.values())),
    'utility': sorted(set(UTILITY.values())),
    'difficulty': sorted(set(DIFFICULTY.values())),
}

@filters_bp.route("/filter_exercises", methods=["POST"])
def filter_exercises():
    filters = None
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
                logger.warning(f"New code guard: unknown filter field rejected: {key}")
                return error_response("VALIDATION_ERROR", f"Invalid filter column: {key}", 400)
            
            if value:  # Only include non-empty values
                # Validate column is whitelisted
                if validate_column_name(db_field):
                    sanitized_filters[db_field] = value
                else:
                    logger.warning(f"Invalid column in filter: {db_field}")
                    return error_response("VALIDATION_ERROR", f"Invalid filter column: {key}", 400)

        logger.debug(f"Sanitized filters: {sanitized_filters}")
        
        # Apply filters and get results
        exercise_names = FilterPredicates.get_exercises(filters=sanitized_filters)
        
        logger.info(
            "Exercises filtered",
            extra={
                'filter_count': len(sanitized_filters),
                'filter_fields': list(sanitized_filters.keys()),
                'result_count': len(exercise_names)
            }
        )

        return jsonify(success_response(data=exercise_names))
    except Exception as e:
        logger.exception(
            "Error filtering exercises",
            extra={'filter_count': len(filters) if filters else 0}
        )
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
        with DatabaseHandler() as db:
            if safe_table == 'exercises' and safe_column == 'advanced_isolated_muscles':
                records = db.fetch_all(
                    "SELECT DISTINCT muscle FROM exercise_isolated_muscles ORDER BY muscle"
                )
                values = [row['muscle'] for row in records]
                return jsonify(success_response(data=values))

            if safe_column in ENUM_VALUE_MAP:
                return jsonify(success_response(data=ENUM_VALUE_MAP[safe_column]))

            # Force column: query DB and normalize to title case to merge variants
            if safe_column == 'force':
                query = (
                    f"SELECT DISTINCT {safe_column} AS value FROM {safe_table} "
                    f"WHERE {safe_column} IS NOT NULL AND TRIM({safe_column}) <> '' "
                    f"ORDER BY {safe_column}"
                )
                rows = db.fetch_all(query)
                # Normalize to title case and dedupe (merges 'push'/'Push', 'pull'/'Pull')
                seen = set()
                values = []
                for row in rows:
                    val = row['value']
                    if val:
                        normalized = val.strip().title()
                        if normalized not in seen:
                            seen.add(normalized)
                            values.append(normalized)
                return jsonify(success_response(data=sorted(values)))

            if safe_column in {
                'primary_muscle_group',
                'secondary_muscle_group',
                'tertiary_muscle_group',
            }:
                query = (
                    f"SELECT DISTINCT {safe_column} AS value FROM {safe_table} "
                    f"WHERE {safe_column} IS NOT NULL AND TRIM({safe_column}) <> '' "
                    f"ORDER BY {safe_column}"
                )
                rows = db.fetch_all(query)
                values = [row['value'] for row in rows]
                return jsonify(success_response(data=values))

            if safe_column == 'equipment':
                query = (
                    f"SELECT DISTINCT TRIM({safe_column}) AS value FROM {safe_table} "
                    f"WHERE {safe_column} IS NOT NULL AND TRIM({safe_column}) <> '' "
                    f"ORDER BY value"
                )
                rows = db.fetch_all(query)
                values = [row['value'] for row in rows if row.get('value')]
                return jsonify(success_response(data=values))

            query = (
                f"SELECT DISTINCT {safe_column} AS value FROM {safe_table} "
                f"WHERE {safe_column} IS NOT NULL AND TRIM({safe_column}) <> '' "
                f"ORDER BY {safe_column}"
            )
            results = db.fetch_all(query)
            values = [row['value'] for row in results if row.get('value')]
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
                # Special handling for advanced_isolated_muscles - use mapping table
                if safe_column == "advanced_isolated_muscles":
                    query += """
                        AND EXISTS (
                            SELECT 1
                            FROM exercise_isolated_muscles m
                            WHERE m.exercise_name = exercises.exercise_name
                              AND m.muscle LIKE ?
                        )
                    """
                    params.append(f"%{value}%")
                else:
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