from flask import Blueprint, jsonify, request
from utils.exercise_manager import get_exercises
from utils.database import DatabaseHandler

filters_bp = Blueprint('filters', __name__)

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

@filters_bp.route("/filter_exercises", methods=["POST"])
def filter_exercises():
    try:
        filters = request.get_json()
        print(f"DEBUG: Received filters: {filters}")

        # Convert frontend names to database column names
        sanitized_filters = {}
        for key, value in filters.items():
            db_field = FILTER_MAPPING.get(key)
            if db_field and value:
                sanitized_filters[db_field] = value

        print(f"DEBUG: Sanitized filters: {sanitized_filters}")
        exercise_names = get_exercises(filters=sanitized_filters)
        print(f"DEBUG: Found {len(exercise_names)} matching exercises")

        return jsonify(exercise_names)
    except Exception as e:
        print(f"Error in filter_exercises: {e}")
        return jsonify({"error": str(e)}), 500

@filters_bp.route("/get_all_exercises")
def get_all_exercises():
    """Get all exercises without any filters."""
    try:
        exercise_names = get_exercises()
        return jsonify(exercise_names)
    except Exception as e:
        return jsonify({"error": str(e)}), 500 

@filters_bp.route("/get_unique_values/<table>/<column>")
def get_unique_values(table, column):
    """Get unique values for a given column in a table."""
    try:
        query = f"SELECT DISTINCT {column} FROM {table} WHERE {column} IS NOT NULL ORDER BY {column} ASC"
        with DatabaseHandler() as db:
            results = db.fetch_all(query)
            values = [row[column] for row in results if row[column]]
            return jsonify(values)
    except Exception as e:
        print(f"Error fetching unique values: {e}")
        return jsonify({"error": str(e)}), 500 

@filters_bp.route("/get_filtered_exercises", methods=["POST"])
def get_filtered_exercises():
    """Get exercises based on multiple filter criteria."""
    try:
        filters = request.get_json()
        query = """
        SELECT exercise_name
        FROM exercises
        WHERE 1=1
        """
        params = []
        
        for field, value in filters.items():
            if value:
                query += f" AND {field} LIKE ?"
                params.append(f"%{value}%")
                
        query += " ORDER BY exercise_name ASC"
        
        with DatabaseHandler() as db:
            results = db.fetch_all(query, params)
            exercises = [row['exercise_name'] for row in results]
            return jsonify(exercises)
    except Exception as e:
        print(f"Error filtering exercises: {e}")
        return jsonify({"error": str(e)}), 500 