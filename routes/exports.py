from flask import Blueprint, Response, jsonify, request
from utils.database import DatabaseHandler
import pandas as pd
from io import BytesIO
from utils.weekly_summary import (
    calculate_exercise_categories,
    calculate_isolated_muscles_stats,
    calculate_weekly_summary
)

exports_bp = Blueprint('exports', __name__)

def calculate_volume_for_category(category, muscle_group):
    """Calculate total volume for a muscle group category."""
    try:
        with DatabaseHandler() as db:
            query = """
            SELECT SUM(scored_weight * scored_max_reps * planned_sets) as total_volume
            FROM workout_log wl
            JOIN exercises e ON wl.exercise = e.exercise_name
            WHERE (
                e.primary_muscle_group = ? 
                OR e.secondary_muscle_group = ?
                OR e.tertiary_muscle_group = ?
                OR e.advanced_isolated_muscles LIKE ?
            )
            AND scored_weight IS NOT NULL
            AND scored_max_reps IS NOT NULL
            AND planned_sets IS NOT NULL
            """
            result = db.fetch_one(query, (muscle_group, muscle_group, muscle_group, f"%{muscle_group}%"))
            return result['total_volume'] if result and result['total_volume'] else 0
    except Exception as e:
        print(f"Error calculating volume: {e}")
        return 0

def calculate_frequency_for_category(category, muscle_group):
    """Calculate training frequency for a muscle group category."""
    try:
        with DatabaseHandler() as db:
            query = """
            SELECT COUNT(DISTINCT date(created_at)) as frequency
            FROM workout_log wl
            JOIN exercises e ON wl.exercise = e.exercise_name
            WHERE (
                e.primary_muscle_group = ? 
                OR e.secondary_muscle_group = ?
                OR e.tertiary_muscle_group = ?
                OR e.advanced_isolated_muscles LIKE ?
            )
            AND created_at >= date('now', '-7 days')
            """
            result = db.fetch_one(query, (muscle_group, muscle_group, muscle_group, f"%{muscle_group}%"))
            return result['frequency'] if result and result['frequency'] else 0
    except Exception as e:
        print(f"Error calculating frequency: {e}")
        return 0

@exports_bp.route("/export_to_excel")
def export_to_excel():
    """Export all data to Excel."""
    try:
        # Create a single database connection for all operations
        db = DatabaseHandler()
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            # Export User Selection (Workout Plan)
            user_selection_query = """
            SELECT us.*, e.primary_muscle_group, e.secondary_muscle_group
            FROM user_selection us
            LEFT JOIN exercises e ON us.exercise = e.exercise_name
            """
            user_selection = pd.DataFrame(db.fetch_all(user_selection_query))
            if not user_selection.empty:
                user_selection.to_excel(writer, sheet_name='Workout Plan', index=False)

            # Export Workout Log
            workout_log_query = """
            SELECT * FROM workout_log 
            ORDER BY routine, exercise
            """
            workout_log = pd.DataFrame(db.fetch_all(workout_log_query))
            if not workout_log.empty:
                workout_log.to_excel(writer, sheet_name='Workout Log', index=False)

            # Export Weekly Summary
            weekly_summary = calculate_weekly_summary('Total')
            if weekly_summary:
                pd.DataFrame(weekly_summary).to_excel(writer, sheet_name='Weekly Summary', index=False)

            # Export Session Summary
            session_summary_query = """
            SELECT 
                date(created_at) as session_date,
                routine,
                exercise,
                planned_sets,
                planned_min_reps,
                planned_max_reps,
                planned_weight,
                planned_rir,
                planned_rpe,
                scored_weight,
                scored_max_reps,
                scored_rir,
                scored_rpe
            FROM workout_log
            WHERE (
                scored_weight IS NOT NULL
                OR scored_max_reps IS NOT NULL
                OR planned_weight IS NOT NULL
                OR planned_sets IS NOT NULL
            )
            AND routine IS NOT NULL
            ORDER BY created_at DESC
            """
            session_summary = pd.DataFrame(db.fetch_all(session_summary_query))
            if not session_summary.empty:
                # Add exercise categories for each exercise
                exercise_categories_query = """
                SELECT 
                    exercise_name,
                    primary_muscle_group,
                    secondary_muscle_group,
                    tertiary_muscle_group,
                    advanced_isolated_muscles
                FROM exercises
                """
                exercise_categories = pd.DataFrame(db.fetch_all(exercise_categories_query))
                
                # Merge with session summary
                session_summary = session_summary.merge(
                    exercise_categories,
                    left_on='exercise',
                    right_on='exercise_name',
                    how='left'
                )
                
                # Reorder columns
                columns_order = [
                    'session_date', 'routine', 'exercise',
                    'primary_muscle_group', 'secondary_muscle_group', 
                    'tertiary_muscle_group', 'advanced_isolated_muscles',
                    'planned_sets', 'planned_min_reps', 'planned_max_reps',
                    'planned_weight', 'planned_rir', 'planned_rpe',
                    'scored_weight', 'scored_max_reps', 'scored_rir', 'scored_rpe'
                ]
                session_summary = session_summary[columns_order]
                session_summary.to_excel(writer, sheet_name='Session Summary', index=False)

            # Export Progression Goals
            progression_query = """
            SELECT 
                exercise,
                goal_type,
                current_value,
                target_value,
                goal_date,
                completed,
                created_at
            FROM progression_goals
            ORDER BY created_at DESC
            """
            progression_goals = pd.DataFrame(db.fetch_all(progression_query))
            if not progression_goals.empty:
                progression_goals.to_excel(writer, sheet_name='Progression Goals', index=False)

            # Export Categories Summary
            categories = pd.DataFrame(calculate_exercise_categories())
            if not categories.empty:
                categories.to_excel(writer, sheet_name='Categories', index=False)

            # Export Isolated Muscles Stats
            isolated_muscles = pd.DataFrame(calculate_isolated_muscles_stats())
            if not isolated_muscles.empty:
                isolated_muscles.to_excel(writer, sheet_name='Isolated Muscles', index=False)

        output.seek(0)
        # Close the database connection after all operations are complete
        db.close()
        
        return Response(
            output,
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment;filename=workout_tracker_summary.xlsx"},
        )
    except Exception as e:
        print(f"Error exporting to Excel: {e}")
        # Ensure database connection is closed in case of error
        if 'db' in locals():
            db.close()
        return jsonify({"error": "Failed to export to Excel"}), 500

@exports_bp.route("/export_to_workout_log", methods=["POST"])
def export_to_workout_log():
    """Export current workout plan to workout log."""
    try:
        query = """
        SELECT id, routine, exercise, sets, min_rep_range, max_rep_range, 
               rir, rpe, weight
        FROM user_selection
        """
        
        insert_query = """
        INSERT INTO workout_log (
            workout_plan_id, routine, exercise, planned_sets, planned_min_reps,
            planned_max_reps, planned_rir, planned_rpe, planned_weight, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """
        
        with DatabaseHandler() as db:
            workout_plan = db.fetch_all(query)
            
            if not workout_plan:
                return jsonify({"message": "No exercises to export"}), 400
                
            for exercise in workout_plan:
                params = (
                    exercise["id"], exercise["routine"], exercise["exercise"],
                    exercise["sets"], exercise["min_rep_range"], exercise["max_rep_range"],
                    exercise["rir"], exercise["rpe"], exercise["weight"]
                )
                db.execute_query(insert_query, params)
            
        return jsonify({"message": "Workout plan exported successfully"}), 200
            
    except Exception as e:
        print(f"Error exporting workout plan: {e}")
        return jsonify({"error": "Failed to export workout plan"}), 500 

@exports_bp.route("/export_summary", methods=["POST"])
def export_summary():
    """Export summary data based on specified parameters."""
    try:
        params = request.get_json()
        method = params.get('method', 'Total')
        
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            # Export Weekly Summary
            weekly_data = calculate_weekly_summary(method)
            if weekly_data:
                pd.DataFrame(weekly_data).to_excel(
                    writer, 
                    sheet_name='Weekly Summary',
                    index=False
                )
            
            # Export Categories
            categories = calculate_exercise_categories()
            if categories:
                pd.DataFrame(categories).to_excel(
                    writer,
                    sheet_name='Categories',
                    index=False
                )
                
        output.seek(0)
        return Response(
            output,
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment;filename=workout_summary.xlsx"}
        )
    except Exception as e:
        print(f"Error exporting summary: {e}")
        return jsonify({"error": "Failed to export summary"}), 500 