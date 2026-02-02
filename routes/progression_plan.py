from flask import Blueprint, render_template, request, jsonify, redirect
from utils.database import DatabaseHandler
from utils.progression_plan import (
    get_exercise_history,
    generate_progression_suggestions,
    save_progression_goal
)
from datetime import datetime
import traceback

progression_plan_bp = Blueprint('progression_plan', __name__)

@progression_plan_bp.route("/progression")
def progression_plan():
    """Render the progression plan page."""
    try:
        with DatabaseHandler() as db:
            # Get unique exercises from workout log
            query = """
            SELECT DISTINCT exercise, routine
            FROM workout_log
            ORDER BY routine, exercise
            """
            exercises = db.fetch_all(query)
            print(f"Found exercises: {exercises}")
            
            # Get existing progression goals
            goals_query = """
            SELECT * FROM progression_goals
            WHERE completed = 0
            ORDER BY goal_date
            """
            goals = db.fetch_all(goals_query)
            print(f"Found goals: {goals}")
            
        return render_template(
            "progression_plan.html",
            exercises=exercises,
            goals=goals
        )
    except Exception as e:
        print(f"Error in progression_plan: {str(e)}")
        print(traceback.format_exc())
        return render_template("error.html", message="Unable to load progression plan."), 500

@progression_plan_bp.route("/get_exercise_suggestions", methods=["POST"])
def get_suggestions():
    """Get progression suggestions for a specific exercise."""
    try:
        print("\n=== Starting get_suggestions ===")
        data = request.get_json()
        exercise = data.get('exercise')
        print(f"Received request for exercise: {exercise}")
        
        history = get_exercise_history(exercise)
        print(f"Exercise history found: {len(history) if history else 0} records")
        
        if not history:
            print(f"No history found for exercise: {exercise}")
            return jsonify([{
                "type": "technique",
                "title": "Start Training",
                "description": f"Begin training {exercise} to generate progression suggestions.",
                "action": "Set initial goals"
            }])
        
        # Get the latest workout data
        latest = history[0]
        print(f"Latest workout data: {latest}")
        suggestions = []
        
        # Add each suggestion with debug logging
        print("Generating suggestions...")
        
        # 1. Technique suggestion (always available)
        suggestions.append({
            "type": "technique",
            "title": "Perfect Your Form",
            "description": f"Focus on mastering {exercise} technique for better results.",
            "action": "Set technique goal"
        })
        print("Added technique suggestion")
        
        # 2. Weight progression suggestion
        if latest.get('scored_weight') is not None or latest.get('planned_weight') is not None:
            # Use scored weight if available, otherwise use planned weight
            weight = float(latest.get('scored_weight') or latest.get('planned_weight'))
            weight_increment = 2.5 if weight < 20 else 5
            print(f"Found weight: {weight}, suggesting increment: {weight_increment}")
            suggestions.append({
                "type": "weight",
                "title": "Increase Weight",
                "description": f"Current weight: {weight}kg. Try adding {weight_increment}kg.",
                "action": "Set weight goal"
            })
            print("Added weight suggestion")
        
        # 3. Reps progression suggestion
        if latest.get('scored_max_reps') is not None or latest.get('planned_max_reps') is not None:
            # Use scored reps if available, otherwise use planned reps
            reps = int(latest.get('scored_max_reps') or latest.get('planned_max_reps'))
            print(f"Found reps: {reps}")
            suggestions.append({
                "type": "reps",
                "title": "Increase Repetitions",
                "description": f"Current max reps: {reps}. Try adding 1-2 reps per set.",
                "action": "Set rep goal"
            })
            print("Added reps suggestion")
        
        # 4. Volume progression suggestion
        if latest.get('planned_sets') is not None:
            sets = int(latest['planned_sets'])
            print(f"Found sets: {sets}")
            suggestions.append({
                "type": "sets",
                "title": "Add Another Set",
                "description": f"Current sets: {sets}. Add one more set for increased volume.",
                "action": "Set volume goal"
            })
            print("Added sets suggestion")
        
        print(f"Generated {len(suggestions)} suggestions")
        return jsonify(suggestions)
    except Exception as e:
        print(f"Error in get_suggestions: {str(e)}")
        print(traceback.format_exc())
        return jsonify({"error": str(e)}), 500

@progression_plan_bp.route("/save_progression_goal", methods=["POST"])
def save_goal():
    """Save a new progression goal."""
    try:
        data = request.get_json()
        save_progression_goal(data)
        return redirect('/progression')
    except Exception as e:
        return jsonify({"error": str(e)}), 500 

@progression_plan_bp.route("/delete_progression_goal/<int:goal_id>", methods=["DELETE"])
def delete_goal(goal_id):
    try:
        with DatabaseHandler() as db:
            # Check if goal exists
            query = "SELECT * FROM progression_goals WHERE id = ?"
            goal = db.fetch_one(query, (goal_id,))
            
            if not goal:
                return jsonify({"error": "Goal not found"}), 404
            
            # Delete the goal
            query = "DELETE FROM progression_goals WHERE id = ?"
            db.execute_query(query, (goal_id,))
            
            return jsonify({"message": "Goal deleted successfully"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500 

@progression_plan_bp.route("/get_current_value", methods=["POST"])
def get_current_value():
    """Get the current value for an exercise based on recent workout history."""
    try:
        data = request.get_json()
        exercise = data.get('exercise')
        goal_type = data.get('goal_type')
        
        print(f"Fetching current value for exercise: {exercise}, goal type: {goal_type}")
        
        with DatabaseHandler() as db:
            if goal_type == 'weight':
                # Get maximum weight ever achieved for this exercise
                # Use scored_weight if available, otherwise fall back to planned_weight
                query = """
                    SELECT MAX(COALESCE(scored_weight, planned_weight)) as current_value 
                    FROM workout_log 
                    WHERE exercise = ?
                """
            elif goal_type == 'reps':
                # Get maximum reps ever achieved for this exercise
                # Use scored_max_reps if available, otherwise fall back to planned_max_reps
                query = """
                    SELECT MAX(COALESCE(scored_max_reps, planned_max_reps)) as current_value 
                    FROM workout_log 
                    WHERE exercise = ?
                """
            elif goal_type == 'sets':
                # Get most recent sets count for this exercise
                query = """
                    SELECT planned_sets as current_value 
                    FROM workout_log 
                    WHERE exercise = ?
                    ORDER BY created_at DESC
                    LIMIT 1
                """
            else:
                return jsonify({"current_value": "N/A"})
            
            print(f"Executing query: {query} with exercise: {exercise}")
            result = db.fetch_one(query, (exercise,))
            print(f"Query result: {result}")
            
            current_value = result['current_value'] if result and result['current_value'] else 0
            print(f"Returning current_value: {current_value}")
            
            return jsonify({"current_value": current_value})
            
    except Exception as e:
        print(f"Error in get_current_value: {str(e)}")
        return jsonify({"error": str(e)}), 500 