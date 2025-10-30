from flask import Blueprint, render_template, request, jsonify, Response, send_file
from utils.database import DatabaseHandler
from utils.workout_log import get_workout_logs, check_progression
from utils.volume_classifier import (
    get_volume_class,
    get_volume_label,
    get_volume_tooltip
)
import pandas as pd
from io import BytesIO
from datetime import datetime

workout_log_bp = Blueprint('workout_log', __name__)

@workout_log_bp.route("/workout_log")
def workout_log():
    """Render the workout log page."""
    try:
        workout_logs = get_workout_logs()
        return render_template(
            "workout_log.html",
            page_title="Workout Log",
            workout_logs=workout_logs,
            enumerate=enumerate,
        )
    except Exception as e:
        print(f"Error in workout_log: {e}")
        return render_template("error.html", message="Unable to load workout log."), 500

@workout_log_bp.route("/update_workout_log", methods=["POST"])
def update_workout_log():
    """Update workout log entry."""
    try:
        data = request.get_json()
        log_id = data.get("id")
        updates = data.get("updates", {})

        valid_fields = {
            "scored_weight", "scored_min_reps", "scored_max_reps", 
            "scored_rir", "scored_rpe", "last_progression_date"
        }

        valid_updates = {k: v for k, v in updates.items() if k in valid_fields}

        if not valid_updates:
            return jsonify({"message": "No valid fields to update"}), 400

        set_clause = ", ".join(f"{k} = ?" for k in valid_updates.keys())
        query = f"UPDATE workout_log SET {set_clause} WHERE id = ?"
        params = list(valid_updates.values()) + [log_id]

        with DatabaseHandler() as db:
            db.execute_query(query, params)

        return jsonify({"message": "Workout log updated successfully"}), 200
    except Exception as e:
        print(f"Error updating workout log: {e}")
        return jsonify({"error": "Failed to update workout log"}), 500

@workout_log_bp.route('/delete_workout_log', methods=['POST'])
def delete_workout_log():
    try:
        data = request.get_json()
        log_id = data.get('id')
        
        if not log_id:
            return jsonify({"error": "No log ID provided"}), 400
        
        with DatabaseHandler() as db:
            query = "DELETE FROM workout_log WHERE id = ?"
            db.execute_query(query, (log_id,))
            
        return jsonify({"message": "Log entry deleted successfully"}), 200
        
    except Exception as e:
        print(f"Error deleting workout log: {str(e)}")
        return jsonify({"error": str(e)}), 500 

@workout_log_bp.route("/update_progression_date", methods=["POST"])
def update_progression_date():
    """Update the last progression date for a workout log entry."""
    try:
        data = request.get_json()
        log_id = data.get("id")
        new_date = data.get("date")

        query = "UPDATE workout_log SET last_progression_date = ? WHERE id = ?"
        with DatabaseHandler() as db:
            db.execute_query(query, (new_date, log_id))

        return jsonify({"message": "Progression date updated successfully"}), 200
    except Exception as e:
        print(f"Error updating progression date: {e}")
        return jsonify({"error": "Failed to update progression date"}), 500 

@workout_log_bp.route("/check_progression/<int:log_id>")
def check_progression(log_id):
    """Check if progressive overload was achieved for a specific log entry."""
    try:
        query = """
        SELECT 
            planned_min_reps, planned_max_reps, planned_weight,
            scored_min_reps, scored_max_reps, scored_weight,
            planned_rir, scored_rir,
            planned_rpe, scored_rpe
        FROM workout_log 
        WHERE id = ?
        """
        with DatabaseHandler() as db:
            log = db.fetch_one(query, (log_id,))
            if not log:
                return jsonify({"error": "Log entry not found"}), 404

            is_progressive = (
                (log['scored_rir'] is not None and 
                 log['planned_rir'] is not None and 
                 log['scored_rir'] < log['planned_rir']) or
                
                (log['scored_rpe'] is not None and 
                 log['planned_rpe'] is not None and 
                 log['scored_rpe'] > log['planned_rpe']) or
                
                (log['scored_min_reps'] is not None and 
                 log['planned_min_reps'] is not None and 
                 log['scored_min_reps'] > log['planned_min_reps']) or
                
                (log['scored_max_reps'] is not None and 
                 log['planned_max_reps'] is not None and 
                 log['scored_max_reps'] > log['planned_max_reps']) or
                
                (log['scored_weight'] is not None and 
                 log['planned_weight'] is not None and 
                 log['scored_weight'] > log['planned_weight'])
            )

            return jsonify({
                "is_progressive": is_progressive,
                "status": "Achieved" if is_progressive else "Pending"
            })

    except Exception as e:
        print(f"Error checking progression: {e}")
        return jsonify({"error": str(e)}), 500 

@workout_log_bp.route("/get_workout_logs")
def get_logs():
    """Get all workout logs."""
    try:
        query = """
        SELECT 
            wl.*,
            us.routine as plan_routine,
            us.exercise as plan_exercise
        FROM workout_log wl
        LEFT JOIN user_selection us ON wl.workout_plan_id = us.id
        ORDER BY wl.created_at DESC
        """
        with DatabaseHandler() as db:
            results = db.fetch_all(query)
            return jsonify(results)
    except Exception as e:
        print(f"Error fetching workout logs: {e}")
        return jsonify({"error": str(e)}), 500 

@workout_log_bp.route('/export_workout_log')
def export_workout_log():
    try:
        # Get workout log data
        logs = get_workout_logs()  # Your existing function to get workout logs
        
        # Convert to DataFrame
        df = pd.DataFrame(logs)
        
        # Create Excel file in memory
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, sheet_name='Workout Log', index=False)
            
            # Get the workbook and worksheet objects
            workbook = writer.book
            worksheet = writer.sheets['Workout Log']
            
            # Add some formatting
            header_format = workbook.add_format({
                'bold': True,
                'bg_color': '#f8f9fa',
                'border': 1
            })
            
            # Format the header row
            for col_num, value in enumerate(df.columns.values):
                worksheet.write(0, col_num, value, header_format)
                
            # Adjust column widths
            for idx, col in enumerate(df.columns):
                worksheet.set_column(idx, idx, max(len(str(col)), df[col].astype(str).str.len().max()) + 2)
        
        # Seek to the beginning of the stream
        output.seek(0)
        
        # Generate filename with timestamp
        filename = f'workout_log_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
        
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        print(f"Export error: {e}")
        return {'error': 'Failed to export workout log'}, 500 

@workout_log_bp.route('/export_to_workout_log', methods=['POST'])
def export_to_workout_log():
    print("Export to workout log endpoint hit")
    try:
        with DatabaseHandler() as db:
            print("Getting workout plans from database")
            query = """
            SELECT 
                us.routine,
                us.exercise,
                us.sets,
                us.min_rep_range,
                us.max_rep_range,
                us.rir,
                us.rpe,
                us.weight
            FROM user_selection us
            """
            workout_plans = db.fetch_all(query)
            
            print(f"Found {len(workout_plans)} workout plans to export")
            
            if not workout_plans:
                return jsonify({"error": "No workout plans found to export"}), 404
            
            # Insert each entry into workout_log
            for plan in workout_plans:
                print(f"Exporting plan: {plan}")
                insert_query = """
                INSERT INTO workout_log (
                    routine,
                    exercise,
                    planned_sets,
                    planned_min_reps,
                    planned_max_reps,
                    planned_rir,
                    planned_rpe,
                    planned_weight,
                    created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """
                
                params = (
                    plan['routine'],
                    plan['exercise'],
                    plan['sets'],
                    plan['min_rep_range'],
                    plan['max_rep_range'],
                    plan['rir'],
                    plan['rpe'],
                    plan['weight'],
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                )
                
                db.execute_query(insert_query, params)
            
            print("Export completed successfully")
            return jsonify({
                "message": f"Successfully exported {len(workout_plans)} exercises to workout log"
            }), 200
            
    except Exception as e:
        print(f"Error during export: {e}")
        return jsonify({"error": str(e)}), 500 