from flask import Blueprint, render_template, request, jsonify
from utils.database import DatabaseHandler
from utils.exercise_manager import (
    add_exercise as add_exercise_to_db,
    get_exercises,
)
from utils.errors import success_response, error_response
from utils.logger import get_logger
from routes.filters import ALLOWED_COLUMNS, validate_column_name
from utils.constants import DIFFICULTY, FORCE, MECHANIC, UTILITY
from utils.plan_generator import generate_starter_plan

workout_plan_bp = Blueprint('workout_plan', __name__)
logger = get_logger()

def fetch_unique_values(column):
    """Fetch unique values for a specified column from the exercises table."""
    # Validate column name is whitelisted
    if not validate_column_name(column):
        logger.warning(f"Invalid column name in fetch_unique_values: {column}")
        return []
    
    # Get safe column name from whitelist
    safe_column = ALLOWED_COLUMNS.get(column.lower())
    if not safe_column:
        logger.warning(f"Column not found in whitelist: {column}")
        return []
    
    enum_map = {
        'force': sorted(set(FORCE.values())),
        'mechanic': sorted(set(MECHANIC.values())),
        'utility': sorted(set(UTILITY.values())),
        'difficulty': sorted(set(DIFFICULTY.values())),
    }

    try:
        with DatabaseHandler() as db:
            if safe_column in enum_map:
                return enum_map[safe_column]

            if safe_column == 'advanced_isolated_muscles':
                rows = db.fetch_all(
                    "SELECT DISTINCT muscle FROM exercise_isolated_muscles ORDER BY muscle"
                )
                return [row['muscle'] for row in rows]

            if safe_column in {
                'primary_muscle_group',
                'secondary_muscle_group',
                'tertiary_muscle_group',
            }:
                query = (
                    f"SELECT DISTINCT {safe_column} AS value FROM exercises "
                    f"WHERE {safe_column} IS NOT NULL AND TRIM({safe_column}) <> '' "
                    f"ORDER BY {safe_column}"
                )
                rows = db.fetch_all(query)
                return [row['value'] for row in rows]

            if safe_column == 'equipment':
                query = (
                    f"SELECT DISTINCT TRIM({safe_column}) AS value FROM exercises "
                    f"WHERE {safe_column} IS NOT NULL AND TRIM({safe_column}) <> '' "
                    f"ORDER BY value"
                )
                rows = db.fetch_all(query)
                return [row['value'] for row in rows if row.get('value')]

            query = (
                f"SELECT DISTINCT {safe_column} AS value FROM exercises "
                f"WHERE {safe_column} IS NOT NULL AND TRIM({safe_column}) <> '' "
                f"ORDER BY {safe_column}"
            )
            rows = db.fetch_all(query)
            return [row['value'] for row in rows if row.get('value')]
    except Exception as e:
        logger.error(f"Error fetching unique values for {column}: {e}", exc_info=True)
        return []

@workout_plan_bp.route("/workout_plan")
def workout_plan():
    """Render the workout plan page with filters."""
    filters = {
        "Primary Muscle Group": fetch_unique_values("primary_muscle_group"),
        "Secondary Muscle Group": fetch_unique_values("secondary_muscle_group"),
        "Tertiary Muscle Group": fetch_unique_values("tertiary_muscle_group"),
        "Advanced Isolated Muscles": fetch_unique_values("advanced_isolated_muscles"),
        "Force": fetch_unique_values("force"),
        "Equipment": fetch_unique_values("equipment"),
        "Mechanic": fetch_unique_values("mechanic"),
        "Utility": fetch_unique_values("utility"),
        "Grips": fetch_unique_values("grips"),
        "Stabilizers": fetch_unique_values("stabilizers"),
        "Synergists": fetch_unique_values("synergists"),
        "Difficulty": fetch_unique_values("difficulty")
    }
    
    # Fetch initial exercises for the dropdown
    exercises = get_exercises()
    
    return render_template("workout_plan.html", filters=filters, exercises=exercises)

@workout_plan_bp.route("/add_exercise", methods=["POST"])
def add_exercise():
    """Add a new exercise to the workout plan."""
    try:
        data = request.get_json()
        if not data:
            return error_response("VALIDATION_ERROR", "No data provided", 400)
        
        # Log request with context
        logger.info(
            "Adding exercise to workout plan",
            extra={
                'routine': data.get('routine'),
                'exercise': data.get('exercise'),
                'sets': data.get('sets'),
                'min_rep': data.get('min_rep_range'),
                'max_rep': data.get('max_rep_range'),
                'weight': data.get('weight')
            }
        )
        
        result = add_exercise_to_db(
            routine=data.get('routine'),
            exercise=data.get('exercise'),
            sets=data.get('sets'),
            min_rep_range=data.get('min_rep_range'),
            max_rep_range=data.get('max_rep_range'),
            rir=data.get('rir'),
            weight=data.get('weight'),
            rpe=data.get('rpe')
        )
        
        if result and "Error" in result:
            logger.warning(
                "Failed to add exercise",
                extra={
                    'routine': data.get('routine'),
                    'exercise': data.get('exercise'),
                    'error': result
                }
            )
            return error_response("VALIDATION_ERROR", result, 400)
        
        logger.info(
            "Exercise added successfully",
            extra={
                'routine': data.get('routine'),
                'exercise': data.get('exercise')
            }
        )
        return jsonify(success_response(message="Exercise added successfully"))
    except Exception as e:
        logger.exception(
            "Error adding exercise",
            extra={
                'routine': data.get('routine', 'unknown'),
                'exercise': data.get('exercise', 'unknown')
            }
        )
        return error_response("INTERNAL_ERROR", "Failed to add exercise", 500)

@workout_plan_bp.route("/get_exercise_details/<int:exercise_id>")
def get_exercise_details(exercise_id):
    """Get details for a specific exercise."""
    query = """
    SELECT
        us.id, us.routine, us.exercise, us.sets,
        us.min_rep_range, us.max_rep_range, us.rir, us.weight,
        e.primary_muscle_group, e.secondary_muscle_group,
        e.tertiary_muscle_group, e.advanced_isolated_muscles, e.utility,
        e.grips, e.stabilizers, e.synergists
    FROM user_selection us
    JOIN exercises e ON us.exercise = e.exercise_name
    WHERE us.id = ?
    """
    try:
        with DatabaseHandler() as db:
            result = db.fetch_one(query, (exercise_id,))
            if result:
                return jsonify(success_response(data=result))
            return error_response("NOT_FOUND", "Exercise not found", 404)
    except Exception as e:
        logger.exception(f"Error fetching exercise details for id {exercise_id}")
        return error_response("INTERNAL_ERROR", "Failed to fetch exercise details", 500) 

@workout_plan_bp.route("/get_workout_plan")
def get_workout_plan():
    """Fetch the current workout plan."""
    try:
        logger.debug("Fetching workout plan")
        
        # First check if exercise_order column exists
        with DatabaseHandler() as db:
            # Check if column exists using PRAGMA
            if column_exists(db, 'user_selection', 'exercise_order'):
                order_by_clause = "ORDER BY us.exercise_order, us.routine, us.exercise"
                include_order = ", us.exercise_order"
            else:
                order_by_clause = "ORDER BY us.routine, us.exercise"
                include_order = ""

            query = f"""
            SELECT 
                us.id, 
                us.routine, 
                us.exercise, 
                us.sets, 
                us.min_rep_range, 
                us.max_rep_range, 
                us.rir, 
                us.rpe,
                us.weight{include_order},
                e.primary_muscle_group, 
                e.secondary_muscle_group, 
                e.tertiary_muscle_group, 
                e.advanced_isolated_muscles,
                e.utility, 
                e.grips, 
                e.stabilizers, 
                e.synergists
            FROM user_selection us
            LEFT JOIN exercises e ON us.exercise = e.exercise_name
            {order_by_clause}
            """
            
            results = db.fetch_all(query)
            
            logger.info(
                "Workout plan fetched",
                extra={
                    'exercise_count': len(results),
                    'has_exercise_order': bool(include_order)
                }
            )
            
            return jsonify(success_response(data=results))
            
    except Exception as e:
        logger.exception("Error fetching workout plan")
        return error_response("INTERNAL_ERROR", "Failed to fetch workout plan", 500)

@workout_plan_bp.route("/remove_exercise", methods=["POST"])
def remove_exercise():
    try:
        data = request.get_json()
        if not data:
            return error_response("VALIDATION_ERROR", "No data provided", 400)
        
        logger.debug(f"Received data for remove_exercise: {data}")

        exercise_id = data.get("id")
        if not exercise_id or not str(exercise_id).isdigit():
            return error_response("VALIDATION_ERROR", "Invalid exercise ID", 400)

        with DatabaseHandler() as db_handler:
            # First get exercise details for logging
            exercise_info = db_handler.fetch_one(
                "SELECT routine, exercise FROM user_selection WHERE id = ?",
                (int(exercise_id),)
            )
            
            # First delete related workout logs to avoid foreign key constraint error
            delete_logs_query = "DELETE FROM workout_log WHERE workout_plan_id = ?"
            db_handler.execute_query(delete_logs_query, (int(exercise_id),))
            
            # Then delete the exercise from user_selection
            delete_exercise_query = "DELETE FROM user_selection WHERE id = ?"
            db_handler.execute_query(delete_exercise_query, (int(exercise_id),))

        logger.info(
            "Exercise removed from workout plan",
            extra={
                'exercise_id': exercise_id,
                'routine': exercise_info.get('routine') if exercise_info else 'unknown',
                'exercise': exercise_info.get('exercise') if exercise_info else 'unknown'
            }
        )
        return jsonify(success_response(message="Exercise removed successfully"))
    except Exception as e:
        logger.exception(
            "Error removing exercise",
            extra={'exercise_id': data.get("id", 'unknown')}
        )
        return error_response("INTERNAL_ERROR", "Unable to remove exercise", 500)


@workout_plan_bp.route("/clear_workout_plan", methods=["POST"])
def clear_workout_plan():
    """Clear all exercises from the workout plan."""
    try:
        with DatabaseHandler() as db_handler:
            # First delete all related workout logs to avoid foreign key constraint errors
            db_handler.execute_query("DELETE FROM workout_log WHERE workout_plan_id IN (SELECT id FROM user_selection)")
            
            # Then delete all exercises from user_selection
            db_handler.execute_query("DELETE FROM user_selection")

        logger.info("Workout plan cleared - all exercises removed")
        return jsonify(success_response(message="Workout plan cleared successfully"))
    except Exception as e:
        logger.exception("Error clearing workout plan")
        return error_response("INTERNAL_ERROR", "Unable to clear workout plan", 500)


@workout_plan_bp.route("/get_routine_options")
def get_routine_options():
    """Return the structured routine options with clear hierarchy."""
    return {
        "Gym": {
            "Full Body": {
                "name": "Full Body",
                "description": "Train all major muscle groups in each session",
                "routines": ["Fullbody1", "Fullbody2", "Fullbody3"]
            },
            "Split Programs": {
                "4 Week Split": {
                    "name": "4 Week Split",
                    "description": "Rotating 4-week program for maximum variety",
                    "routines": ["A1", "B1", "A2", "B2"]
                },
                "Push Pull Legs": {
                    "name": "Push, Pull, Legs",
                    "description": "Classic 6-day split focusing on movement patterns",
                    "routines": ["Push1", "Pull1", "Legs1", "Push2", "Pull2", "Legs2"]
                },
                "Upper Lower": {
                    "name": "Upper Lower",
                    "description": "4-day split targeting upper and lower body",
                    "routines": ["Upper1", "Lower1", "Upper2", "Lower2"]
                }
            },
            "Basic Splits": {
                "2 Days Split": {
                    "name": "2 Days Split",
                    "description": "Simple alternating workout pattern",
                    "routines": ["A", "B"]
                },
                "3 Days Split": {
                    "name": "3 Days Split",
                    "description": "Three-way split for balanced training",
                    "routines": ["A", "B", "C"]
                }
            }
        },
        "Home Workout": {
            "Full Body": {
                "name": "Full Body",
                "description": "Complete body workout with minimal equipment",
                "routines": ["Fullbody1", "Fullbody2", "Fullbody3"]
            },
            "Split Programs": {
                "4 Week Split": {
                    "name": "4 Week Split",
                    "description": "Home-adapted 4-week rotation",
                    "routines": ["A1", "B1", "A2", "B2"]
                },
                "Push Pull Legs": {
                    "name": "Push, Pull, Legs",
                    "description": "Bodyweight and minimal equipment PPL",
                    "routines": ["Push1", "Pull1", "Legs1", "Push2", "Pull2", "Legs2"]
                },
                "Upper Lower": {
                    "name": "Upper Lower",
                    "description": "Home-based upper/lower split",
                    "routines": ["Upper1", "Lower1", "Upper2", "Lower2"]
                }
            },
            "Basic Splits": {
                "2 Days Split": {
                    "name": "2 Days Split",
                    "description": "Simple home workout alternation",
                    "routines": ["A", "B"]
                },
                "3 Days Split": {
                    "name": "3 Days Split",
                    "description": "Three-way home training split",
                    "routines": ["A", "B", "C"]
                }
            }
        }
    } 

@workout_plan_bp.route("/get_user_selection")
def get_user_selection():
    """Get the current user selection data."""
    try:
        query = """
        SELECT 
            us.*, 
            e.primary_muscle_group,
            e.secondary_muscle_group,
            e.tertiary_muscle_group,
            e.advanced_isolated_muscles,
            e.utility,
            e.grips,
            e.stabilizers,
            e.synergists
        FROM user_selection us
        LEFT JOIN exercises e ON us.exercise = e.exercise_name
        ORDER BY us.routine, us.exercise
        """
        with DatabaseHandler() as db:
            results = db.fetch_all(query)
            return jsonify(success_response(data=results))
    except Exception as e:
        logger.exception("Error fetching user selection")
        return error_response("INTERNAL_ERROR", "Failed to fetch user selection", 500) 

@workout_plan_bp.route("/get_exercise_info/<exercise_name>")
def get_exercise_info(exercise_name):
    """Get detailed information about a specific exercise."""
    try:
        query = """
        SELECT *
        FROM exercises
        WHERE exercise_name = ?
        """
        with DatabaseHandler() as db:
            result = db.fetch_one(query, (exercise_name,))
            if result:
                return jsonify(success_response(data=result))
            return error_response("NOT_FOUND", "Exercise not found", 404)
    except Exception as e:
        logger.exception(f"Error fetching exercise info for {exercise_name}")
        return error_response("INTERNAL_ERROR", "Failed to fetch exercise info", 500) 

@workout_plan_bp.route("/get_routine_exercises/<routine>")
def get_routine_exercises(routine):
    """Get exercises for a specific routine."""
    try:
        # First try to get exercises already in the routine
        query = """
        SELECT DISTINCT e.exercise_name
        FROM exercises e
        LEFT JOIN user_selection us ON e.exercise_name = us.exercise
        WHERE us.routine = ? OR us.routine IS NULL
        ORDER BY e.exercise_name ASC
        """
        
        with DatabaseHandler() as db:
            results = db.fetch_all(query, (routine,))
            exercises = [row['exercise_name'] for row in results if row['exercise_name']]
            
            if not exercises:
                # If no exercises found, get all available exercises
                exercises = get_exercises()
            
            logger.debug(f"Found {len(exercises)} exercises for routine {routine}")
            return jsonify(success_response(data=exercises))
            
    except Exception as e:
        logger.exception(f"Error fetching exercises for routine {routine}")
        return error_response("INTERNAL_ERROR", "Failed to fetch exercises for routine", 500) 

@workout_plan_bp.route("/update_exercise", methods=["POST"])
def update_exercise():
    """Update exercise details in the workout plan."""
    try:
        data = request.get_json()
        exercise_id = data.get('id')
        updates = data.get('updates', {})
        
        # Validate the input data
        if not exercise_id or not updates:
            return error_response("VALIDATION_ERROR", "Missing required data", 400)
        
        logger.debug(
            "Updating exercise",
            extra={
                'exercise_id': exercise_id,
                'fields_to_update': list(updates.keys())
            }
        )
            
        # Build the update query dynamically based on provided fields
        update_fields = []
        params = []
        valid_fields = {'sets', 'min_rep_range', 'max_rep_range', 'rir', 'rpe', 'weight'}
        
        for field, value in updates.items():
            if field in valid_fields:
                update_fields.append(f"{field} = ?")
                params.append(value)
        
        if not update_fields:
            return error_response("VALIDATION_ERROR", "No valid fields to update", 400)
            
        query = f"""
            UPDATE user_selection 
            SET {', '.join(update_fields)}
            WHERE id = ?
        """
        params.append(exercise_id)
        
        with DatabaseHandler() as db:
            db.execute_query(query, tuple(params))
        
        logger.info(
            "Exercise updated successfully",
            extra={
                'exercise_id': exercise_id,
                'fields_updated': list(updates.keys())
            }
        )
            
        return jsonify(success_response(message="Exercise updated successfully"))
        
    except Exception as e:
        logger.exception(
            "Error updating exercise",
            extra={'exercise_id': exercise_id if 'exercise_id' in locals() else 'unknown'}
        )
        return error_response("INTERNAL_ERROR", "Failed to update exercise", 500)

def column_exists(db, table_name, column_name):
    """Check if a column exists in a table using PRAGMA."""
    query = f"PRAGMA table_info({table_name})"
    columns = db.fetch_all(query)
    return any(col['name'] == column_name for col in columns)

def table_exists(db, table_name):
    """Check if a table exists in the database."""
    result = db.fetch_one(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table_name,)
    )
    return result is not None

def initialize_exercise_order():
    """Initialize or update the order column in user_selection table."""
    try:
        with DatabaseHandler() as db:
            # First check if the table exists
            if not table_exists(db, 'user_selection'):
                logger.debug("user_selection table does not exist yet, skipping exercise order initialization")
                return True
            
            # Check if column exists using PRAGMA
            if column_exists(db, 'user_selection', 'exercise_order'):
                logger.debug("Exercise order column already exists")
                # Check for any NULL exercise_order values and initialize them
                null_count = db.fetch_one(
                    "SELECT COUNT(*) as count FROM user_selection WHERE exercise_order IS NULL"
                )
                if null_count and null_count.get('count', 0) > 0:
                    logger.info(f"Found {null_count['count']} rows with NULL exercise_order, initializing...")
                    # Get max existing order
                    max_order = db.fetch_one(
                        "SELECT COALESCE(MAX(exercise_order), 0) as max_order FROM user_selection"
                    )
                    current_order = (max_order.get('max_order', 0) or 0)
                    
                    # Get rows with NULL order, sorted by id (oldest first)
                    null_rows = db.fetch_all(
                        "SELECT id FROM user_selection WHERE exercise_order IS NULL ORDER BY id"
                    )
                    for row in null_rows:
                        current_order += 1
                        db.execute_query(
                            "UPDATE user_selection SET exercise_order = ? WHERE id = ?",
                            (current_order, row['id'])
                        )
                    logger.info(f"Initialized exercise_order for {len(null_rows)} rows")
            else:
                logger.info("Adding exercise_order column")
                # Add the column
                db.execute_query("ALTER TABLE user_selection ADD COLUMN exercise_order INTEGER")
                
                # Initialize with sequential order
                db.execute_query("""
                    UPDATE user_selection 
                    SET exercise_order = (
                        SELECT ROW_NUMBER() OVER (ORDER BY routine, exercise) 
                        FROM user_selection AS t2 
                        WHERE t2.id = user_selection.id
                    )
                """)
                logger.info("Exercise order column initialized")
                
        return True
    except Exception as e:
        logger.exception("Error initializing exercise order")
        return False

@workout_plan_bp.route("/update_exercise_order", methods=["POST"])
def update_exercise_order():
    """Update the order of exercises in the workout plan."""
    try:
        data = request.get_json()
        
        if not data:
            return error_response("VALIDATION_ERROR", "No data provided", 400)
        
        with DatabaseHandler() as db:
            for entry in data:
                if not entry.get("id") or not entry.get("order"):
                    return error_response("VALIDATION_ERROR", "Invalid entry data", 400)
                db.execute_query(
                    "UPDATE user_selection SET exercise_order = ? WHERE id = ?",
                    (entry["order"], entry["id"])
                )
                
        return jsonify(success_response(message="Exercise order updated successfully"))
    except Exception as e:
        logger.exception("Error updating exercise order")
        return error_response("INTERNAL_ERROR", "Failed to update exercise order", 500)


@workout_plan_bp.route("/generate_starter_plan", methods=["POST"])
def generate_starter_plan_route():
    """
    Generate a starter workout plan based on movement patterns.
    
    Request body (JSON):
        training_days: int (1-5, default 3)
        environment: "gym" | "home" (default "gym")
        experience_level: "novice" | "intermediate" | "advanced" (default "novice")
        goal: "hypertrophy" | "strength" | "general" (default "hypertrophy")
        volume_scale: float (default 1.0, use 0.8 for heavy lifters)
        equipment_whitelist: list[str] (optional, filter available equipment)
        exclude_exercises: list[str] (optional, exercises to exclude)
        preferred_exercises: dict (optional, pattern -> list of exercise names)
        movement_restrictions: dict (optional, e.g. {"no_overhead_press": true})
        target_muscle_groups: list[str] (optional, filter to specific muscles)
        beginner_consistency_mode: bool (default true for novices)
        persist: bool (default true, save to database)
        overwrite: bool (default true, replace existing routines)
    
    Returns:
        JSON with generated plan structure and metadata
    """
    try:
        data = request.get_json() or {}
        
        logger.info(
            "Generating starter plan",
            extra={
                'training_days': data.get('training_days', 3),
                'environment': data.get('environment', 'gym'),
                'experience_level': data.get('experience_level', 'novice'),
                'goal': data.get('goal', 'hypertrophy'),
            }
        )
        
        # Extract and validate parameters
        training_days = data.get('training_days', 3)
        if not isinstance(training_days, int) or training_days < 1 or training_days > 5:
            return error_response(
                "VALIDATION_ERROR",
                "training_days must be an integer between 1 and 5",
                400
            )
        
        environment = data.get('environment', 'gym')
        if environment not in ('gym', 'home'):
            return error_response(
                "VALIDATION_ERROR",
                "environment must be 'gym' or 'home'",
                400
            )
        
        experience_level = data.get('experience_level', 'novice')
        if experience_level not in ('novice', 'intermediate', 'advanced'):
            return error_response(
                "VALIDATION_ERROR",
                "experience_level must be 'novice', 'intermediate', or 'advanced'",
                400
            )
        
        goal = data.get('goal', 'hypertrophy')
        if goal not in ('hypertrophy', 'strength', 'general'):
            return error_response(
                "VALIDATION_ERROR",
                "goal must be 'hypertrophy', 'strength', or 'general'",
                400
            )
        
        volume_scale = data.get('volume_scale', 1.0)
        if not isinstance(volume_scale, (int, float)) or volume_scale <= 0 or volume_scale > 2:
            return error_response(
                "VALIDATION_ERROR",
                "volume_scale must be a number between 0 and 2",
                400
            )
        
        # Generate the plan
        result = generate_starter_plan(
            training_days=training_days,
            environment=environment,
            experience_level=experience_level,
            goal=goal,
            volume_scale=float(volume_scale),
            equipment_whitelist=data.get('equipment_whitelist'),
            exclude_exercises=data.get('exclude_exercises'),
            preferred_exercises=data.get('preferred_exercises'),
            movement_restrictions=data.get('movement_restrictions'),
            target_muscle_groups=data.get('target_muscle_groups'),
            beginner_consistency_mode=data.get('beginner_consistency_mode', True),
            persist=data.get('persist', True),
            overwrite=data.get('overwrite', True),
        )
        
        logger.info(
            "Starter plan generated successfully",
            extra={
                'total_exercises': result.get('total_exercises'),
                'routines': list(result.get('routines', {}).keys()),
                'persisted': result.get('persisted'),
            }
        )
        
        return jsonify(success_response(data=result))
        
    except ValueError as e:
        logger.warning(f"Validation error in generate_starter_plan: {e}")
        return error_response("VALIDATION_ERROR", str(e), 400)
    except Exception as e:
        logger.exception("Error generating starter plan")
        return error_response("INTERNAL_ERROR", "Failed to generate starter plan", 500)


@workout_plan_bp.route("/get_generator_options")
def get_generator_options():
    """
    Get available options for the plan generator.
    
    Returns configuration options including environments, goals,
    experience levels, and available equipment.
    """
    try:
        # Get available equipment from database
        with DatabaseHandler() as db:
            equipment_rows = db.fetch_all(
                "SELECT DISTINCT equipment FROM exercises WHERE equipment IS NOT NULL ORDER BY equipment"
            )
            available_equipment = [row['equipment'] for row in equipment_rows if row.get('equipment')]
        
        options = {
            "training_days": {
                "min": 1,
                "max": 3,
                "default": 2,
                "descriptions": {
                    1: "Single full-body session per week",
                    2: "A/B split (2 sessions per week)",
                    3: "A/B/C rotation (3 sessions per week)",
                }
            },
            "environments": ["gym", "home"],
            "experience_levels": ["novice", "intermediate", "advanced"],
            "goals": ["hypertrophy", "strength", "general"],
            "available_equipment": available_equipment,
            "home_equipment": ["Bodyweight", "Dumbbells", "Band", "Kettlebells", "Trx"],
            "gym_equipment": available_equipment,
            "volume_scale": {
                "min": 0.5,
                "max": 1.5,
                "default": 1.0,
                "description": "Use lower values (e.g., 0.8) for advanced/heavy lifters"
            },
            "movement_restrictions": [
                "no_overhead_press",
                "no_deadlift",
            ],
        }
        
        return jsonify(success_response(data=options))
        
    except Exception as e:
        logger.exception("Error fetching generator options")
        return error_response("INTERNAL_ERROR", "Failed to fetch generator options", 500)


def suggest_replacement_exercise(current_exercise, muscle, equipment, candidates, strategy="fallback"):
    """
    Suggest a replacement exercise from the candidate pool.
    
    Args:
        current_exercise: The exercise being replaced
        muscle: Primary muscle group to match
        equipment: Equipment type to match
        candidates: List of valid candidate exercise names
        strategy: "ai" for AI-based suggestion, "fallback" for deterministic
    
    Returns:
        str: Selected exercise name from candidates, or None if no valid candidate
    """
    import random
    
    if not candidates:
        return None
    
    # AI strategy placeholder - for now, use heuristic ranking
    # In the future, this could call an LLM or ML model to rank candidates
    if strategy == "ai":
        # Simple heuristic: prefer exercises with similar name patterns
        # (e.g., "Barbell Bench Press" -> prefer other "Bench" or "Press" exercises)
        current_words = set(current_exercise.lower().split())
        
        def score_candidate(candidate):
            candidate_words = set(candidate.lower().split())
            # Count overlapping words (excluding common words like "the", "with")
            common_words = {'the', 'with', 'a', 'an', 'and', 'or', 'for', 'to'}
            meaningful_current = current_words - common_words
            meaningful_candidate = candidate_words - common_words
            overlap = len(meaningful_current & meaningful_candidate)
            # Add some randomness to avoid always picking same exercise
            return (overlap, random.random())
        
        # Sort by score (higher is better) but with randomness for ties
        scored = [(score_candidate(c), c) for c in candidates]
        scored.sort(reverse=True)
        return scored[0][1]
    
    # Fallback: random selection
    return random.choice(candidates)


@workout_plan_bp.route("/replace_exercise", methods=["POST"])
def replace_exercise():
    """
    Replace an exercise in the workout plan with another matching the same
    primary muscle group and equipment.
    
    Request body (JSON):
        id: int - user_selection.id of the exercise to replace
        strategy: "ai"|"fallback" (optional, default "fallback")
    
    Returns:
        On success: { "ok": true, "data": { "updated_row": {...} } }
        On failure: { "ok": false, "error": { "code": "...", "reason": "..." } }
    """
    try:
        data = request.get_json()
        if not data:
            return error_response("VALIDATION_ERROR", "No data provided", 400)
        
        exercise_id = data.get("id")
        strategy = data.get("strategy", "fallback")
        
        if not exercise_id or not str(exercise_id).isdigit():
            return error_response("VALIDATION_ERROR", "Invalid exercise ID", 400)
        
        exercise_id = int(exercise_id)
        
        with DatabaseHandler() as db:
            # a) Fetch the current user_selection row with exercise metadata
            current_row = db.fetch_one("""
                SELECT 
                    us.id, us.routine, us.exercise, us.sets,
                    us.min_rep_range, us.max_rep_range, us.rir, us.rpe, us.weight,
                    e.primary_muscle_group, e.equipment
                FROM user_selection us
                LEFT JOIN exercises e ON us.exercise = e.exercise_name
                WHERE us.id = ?
            """, (exercise_id,))
            
            if not current_row:
                return error_response(
                    "NOT_FOUND", 
                    "Exercise not found in workout plan",
                    404,
                    reason="not_found"
                )
            
            current_exercise = current_row['exercise']
            routine = current_row['routine']
            muscle = current_row['primary_muscle_group']
            equipment = current_row['equipment']
            
            # b) Validate we have the necessary metadata
            if not muscle or not equipment:
                logger.warning(
                    "Cannot replace exercise - missing metadata",
                    extra={
                        'exercise_id': exercise_id,
                        'exercise': current_exercise,
                        'muscle': muscle,
                        'equipment': equipment
                    }
                )
                return error_response(
                    "VALIDATION_ERROR",
                    "Exercise is missing muscle group or equipment metadata",
                    400,
                    reason="missing_metadata"
                )
            
            # c) Build candidate pool from exercises table
            # Match same primary muscle group and equipment (case-insensitive)
            candidates_query = """
                SELECT exercise_name
                FROM exercises
                WHERE LOWER(primary_muscle_group) = LOWER(?)
                  AND LOWER(equipment) = LOWER(?)
                  AND exercise_name != ?
            """
            candidate_rows = db.fetch_all(candidates_query, (muscle, equipment, current_exercise))
            candidate_names = [row['exercise_name'] for row in candidate_rows]
            
            # d) Exclude exercises already used in the same routine
            routine_exercises_query = """
                SELECT exercise FROM user_selection WHERE routine = ?
            """
            routine_exercises = db.fetch_all(routine_exercises_query, (routine,))
            routine_exercise_names = {row['exercise'] for row in routine_exercises}
            
            # Filter out exercises already in the routine
            valid_candidates = [c for c in candidate_names if c not in routine_exercise_names]
            
            logger.debug(
                "Replacement candidates",
                extra={
                    'exercise_id': exercise_id,
                    'current_exercise': current_exercise,
                    'routine': routine,
                    'muscle': muscle,
                    'equipment': equipment,
                    'total_candidates': len(candidate_names),
                    'valid_candidates': len(valid_candidates)
                }
            )
            
            # e) If no valid candidates, return failure
            if not valid_candidates:
                return jsonify({
                    "ok": False,
                    "status": "error",
                    "message": f"No alternative exercises found for {muscle} with {equipment}",
                    "error": {
                        "code": "NO_CANDIDATES",
                        "reason": "no_candidates",
                        "message": f"No alternative exercises found for {muscle} with {equipment}"
                    }
                }), 200  # Return 200 so frontend can handle gracefully
            
            # f) Choose replacement using AI or fallback
            new_exercise = suggest_replacement_exercise(
                current_exercise, muscle, equipment, valid_candidates, strategy
            )
            
            if not new_exercise:
                return jsonify({
                    "ok": False,
                    "status": "error",
                    "message": "Failed to select replacement exercise",
                    "error": {
                        "code": "SELECTION_FAILED",
                        "reason": "selection_failed",
                        "message": "Failed to select replacement exercise"
                    }
                }), 200
            
            # g) Double-check duplicate constraint before updating
            duplicate_check = db.fetch_one(
                "SELECT id FROM user_selection WHERE routine = ? AND exercise = ?",
                (routine, new_exercise)
            )
            
            if duplicate_check:
                # Try to find another candidate
                remaining_candidates = [c for c in valid_candidates if c != new_exercise]
                if remaining_candidates:
                    new_exercise = suggest_replacement_exercise(
                        current_exercise, muscle, equipment, remaining_candidates, "fallback"
                    )
                else:
                    return jsonify({
                        "ok": False,
                        "status": "error",
                        "message": "All candidate exercises are already in this routine",
                        "error": {
                            "code": "DUPLICATE",
                            "reason": "duplicate",
                            "message": "All candidate exercises are already in this routine"
                        }
                    }), 200
            
            # Update the exercise in user_selection
            db.execute_query(
                "UPDATE user_selection SET exercise = ? WHERE id = ?",
                (new_exercise, exercise_id)
            )
            
            # h) Fetch the updated row with full metadata for response
            updated_row = db.fetch_one("""
                SELECT 
                    us.id, us.routine, us.exercise, us.sets,
                    us.min_rep_range, us.max_rep_range, us.rir, us.rpe, us.weight,
                    e.primary_muscle_group, e.secondary_muscle_group,
                    e.tertiary_muscle_group, e.advanced_isolated_muscles,
                    e.utility, e.grips, e.stabilizers, e.synergists, e.equipment
                FROM user_selection us
                LEFT JOIN exercises e ON us.exercise = e.exercise_name
                WHERE us.id = ?
            """, (exercise_id,))
            
            # Check if exercise_order column exists and include it
            if column_exists(db, 'user_selection', 'exercise_order'):
                order_row = db.fetch_one(
                    "SELECT exercise_order FROM user_selection WHERE id = ?",
                    (exercise_id,)
                )
                if order_row and order_row.get('exercise_order'):
                    updated_row = dict(updated_row)
                    updated_row['exercise_order'] = order_row['exercise_order']
            
            logger.info(
                "Exercise replaced successfully",
                extra={
                    'exercise_id': exercise_id,
                    'routine': routine,
                    'old_exercise': current_exercise,
                    'new_exercise': new_exercise,
                    'muscle': muscle,
                    'equipment': equipment,
                    'candidates_available': len(valid_candidates)
                }
            )
            
            return jsonify(success_response(
                data={
                    "updated_row": dict(updated_row),
                    "old_exercise": current_exercise,
                    "new_exercise": new_exercise
                },
                message=f"Replaced {current_exercise} with {new_exercise}"
            ))
            
    except Exception as e:
        logger.exception(
            "Error replacing exercise",
            extra={'exercise_id': data.get('id') if data else 'unknown'}
        )
        return error_response("INTERNAL_ERROR", "Failed to replace exercise", 500)
