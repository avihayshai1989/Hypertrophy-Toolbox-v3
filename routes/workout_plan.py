from flask import Blueprint, render_template, request, jsonify
from utils.database import DatabaseHandler
from utils.exercise_manager import (
    add_exercise as add_exercise_to_db,
    get_exercises,
)

workout_plan_bp = Blueprint('workout_plan', __name__)

def fetch_unique_values(column):
    """Fetch unique values for a specified column from the exercises table."""
    query = f"SELECT DISTINCT {column} FROM exercises WHERE {column} IS NOT NULL ORDER BY {column} ASC"
    try:
        with DatabaseHandler() as db:
            results = db.fetch_all(query)
            return [row[column] for row in results if row[column]]
    except Exception as e:
        print(f"Error fetching unique values for {column}: {e}")
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
        return jsonify({"message": "Exercise added successfully"}), 200
    except Exception as e:
        print(f"Error adding exercise: {e}")
        return jsonify({"error": str(e)}), 500

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
            return jsonify(result) if result else jsonify({"error": "Exercise not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500 

@workout_plan_bp.route("/get_workout_plan")
def get_workout_plan():
    """Fetch the current workout plan."""
    try:
        # First check if exercise_order column exists
        with DatabaseHandler() as db:
            try:
                db.fetch_one("SELECT exercise_order FROM user_selection LIMIT 1")
                order_by_clause = "ORDER BY us.exercise_order, us.routine, us.exercise"
                include_order = ", us.exercise_order"
            except:
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
            return jsonify(results)
            
    except Exception as e:
        print(f"Error fetching workout plan: {e}")
        return jsonify({"error": str(e)}), 500

@workout_plan_bp.route("/remove_exercise", methods=["POST"])
def remove_exercise():
    try:
        data = request.get_json()
        print(f"DEBUG: Received data for remove_exercise: {data}")

        exercise_id = data.get("id")
        if not exercise_id or not str(exercise_id).isdigit():
            return jsonify({"message": "Invalid exercise ID"}), 400

        query = "DELETE FROM user_selection WHERE id = ?"
        with DatabaseHandler() as db_handler:
            db_handler.execute_query(query, (int(exercise_id),))

        print(f"DEBUG: Deleted exercise with ID = {exercise_id}")
        return jsonify({"message": "Exercise removed successfully"}), 200
    except Exception as e:
        print(f"Error in remove_exercise: {e}")
        return jsonify({"error": "Unable to remove exercise"}), 500 

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
            return jsonify(results)
    except Exception as e:
        print(f"Error fetching user selection: {e}")
        return jsonify({"error": str(e)}), 500 

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
                return jsonify(result)
            return jsonify({"error": "Exercise not found"}), 404
    except Exception as e:
        print(f"Error fetching exercise info: {e}")
        return jsonify({"error": str(e)}), 500 

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
            
            print(f"DEBUG: Found {len(exercises)} exercises for routine {routine}")
            return jsonify(exercises)
            
    except Exception as e:
        print(f"Error fetching exercises for routine {routine}: {e}")
        return jsonify({"error": f"Failed to fetch exercises for routine: {str(e)}"}), 500 

@workout_plan_bp.route("/update_exercise", methods=["POST"])
def update_exercise():
    """Update exercise details in the workout plan."""
    try:
        data = request.get_json()
        exercise_id = data.get('id')
        updates = data.get('updates', {})
        
        # Validate the input data
        if not exercise_id or not updates:
            return jsonify({"error": "Missing required data"}), 400
            
        # Build the update query dynamically based on provided fields
        update_fields = []
        params = []
        valid_fields = {'sets', 'min_rep_range', 'max_rep_range', 'rir', 'rpe', 'weight'}
        
        for field, value in updates.items():
            if field in valid_fields:
                update_fields.append(f"{field} = ?")
                params.append(value)
        
        if not update_fields:
            return jsonify({"error": "No valid fields to update"}), 400
            
        query = f"""
            UPDATE user_selection 
            SET {', '.join(update_fields)}
            WHERE id = ?
        """
        params.append(exercise_id)
        
        with DatabaseHandler() as db:
            db.execute_query(query, tuple(params))
            
        return jsonify({"message": "Exercise updated successfully"}), 200
        
    except Exception as e:
        print(f"Error updating exercise: {e}")
        return jsonify({"error": str(e)}), 500

def initialize_exercise_order():
    """Initialize or update the order column in user_selection table."""
    try:
        with DatabaseHandler() as db:
            # Check if column exists
            try:
                db.fetch_one("SELECT exercise_order FROM user_selection LIMIT 1")
                print("Exercise order column already exists")
            except:
                print("Adding exercise_order column")
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
                print("Exercise order column initialized")
                
        return True
    except Exception as e:
        print(f"Error initializing exercise order: {e}")
        return False

@workout_plan_bp.route("/update_exercise_order", methods=["POST"])
def update_exercise_order():
    """Update the order of exercises in the workout plan."""
    try:
        data = request.get_json()
        
        with DatabaseHandler() as db:
            for entry in data:
                db.execute_query(
                    "UPDATE user_selection SET exercise_order = ? WHERE id = ?",
                    (entry["order"], entry["id"])
                )
                
        return jsonify({"message": "Exercise order updated successfully"}), 200
    except Exception as e:
        print(f"Error updating exercise order: {e}")
        return jsonify({"error": str(e)}), 500