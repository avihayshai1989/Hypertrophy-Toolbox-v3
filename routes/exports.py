from flask import Blueprint, Response, jsonify, request, make_response
from utils.database import DatabaseHandler
from utils.export_utils import (
    create_excel_workbook,
    sanitize_filename,
    create_content_disposition_header,
    generate_timestamped_filename,
    stream_excel_response,
    should_use_streaming,
    MAX_EXPORT_ROWS
)
from utils.weekly_summary import (
    calculate_exercise_categories,
    calculate_isolated_muscles_stats,
    calculate_weekly_summary
)
from utils.errors import error_response, success_response
from utils.logger import get_logger
import logging

exports_bp = Blueprint('exports', __name__)
logger = get_logger()

# Removed verbose before_request logging - using logger only

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

# Test route to verify blueprint is working
# Test route removed - no longer needed

@exports_bp.route("/export_to_excel", methods=['GET'])
def export_to_excel():
    """
    Export all data to Excel using memory-efficient approach.
    
    This replaces pandas with direct XlsxWriter usage for better
    memory efficiency and performance on large datasets.
    """
    try:
        logger.info("Starting Excel export")
        sheets_data = {}
        
        with DatabaseHandler() as db:
            # Export User Selection (Workout Plan)
            logger.info("Fetching workout plan data")
            
            # Check if exercise_order column exists and initialize if needed
            from routes.workout_plan import column_exists
            
            # Initialize/Recalculate exercise_order if column exists
            if column_exists(db, 'user_selection', 'exercise_order'):
                # Check current state of exercise_order
                total_check = db.fetch_one("SELECT COUNT(*) as count FROM user_selection")
                order_check = db.fetch_one("SELECT COUNT(DISTINCT exercise_order) as distinct_count, COUNT(*) as total_count FROM user_selection WHERE exercise_order IS NOT NULL")
                
                # Recalculate if all values are the same (like all "1") or NULL
                needs_recalc = False
                if total_check and total_check['count'] > 0:
                    if order_check and order_check['distinct_count'] == 1:
                        # All non-NULL values are the same - need to recalculate
                        logger.info(f"All exercise_order values are the same ({order_check['distinct_count']} distinct). Recalculating...")
                        needs_recalc = True
                    elif order_check and order_check['total_count'] < total_check['count']:
                        # Some values are NULL
                        logger.info(f"Some exercise_order values are NULL. Initializing...")
                        needs_recalc = True
                
                if needs_recalc:
                    logger.info(f"Recalculating exercise_order for {total_check['count']} rows")
                    
                    # Get all rows ordered by routine and exercise (don't use existing exercise_order)
                    ordered_rows = db.fetch_all("""
                        SELECT id FROM user_selection 
                        ORDER BY routine, exercise, id
                    """)
                    
                    logger.info(f"Found {len(ordered_rows)} rows to update")
                    
                    # Update each row with its sequential order
                    updated_count = 0
                    for index, row in enumerate(ordered_rows, start=1):
                        try:
                            db.execute_query(
                                "UPDATE user_selection SET exercise_order = ? WHERE id = ?",
                                (index, row['id'])
                            )
                            updated_count += 1
                            if index <= 3:  # Log first 3 for debugging
                                logger.debug(f"Updated row id={row['id']} to exercise_order={index}")
                        except Exception as e:
                            logger.error(f"Error updating row id={row['id']}: {e}")
                    
                    # Verify the updates
                    verify = db.fetch_one("SELECT COUNT(DISTINCT exercise_order) as distinct_count FROM user_selection WHERE exercise_order IS NOT NULL")
                    logger.info(f"exercise_order recalculated: {updated_count} rows updated, {verify['distinct_count'] if verify else 0} distinct values")
                
                order_by_clause = "ORDER BY us.exercise_order, us.routine, us.exercise"
            else:
                order_by_clause = "ORDER BY us.routine, us.exercise"
            
            user_selection_query = f"""
            SELECT us.*, e.primary_muscle_group, e.secondary_muscle_group
            FROM user_selection us
            LEFT JOIN exercises e ON us.exercise = e.exercise_name
            {order_by_clause}
            """
            user_selection = db.fetch_all(user_selection_query)
            if user_selection:
                sheets_data['Workout Plan'] = user_selection
                logger.info(f"Fetched {len(user_selection)} workout plan rows")

            # Export Workout Log
            logger.info("Fetching workout log data")
            workout_log_query = f"""
            SELECT * FROM workout_log 
            ORDER BY created_at DESC
            LIMIT {MAX_EXPORT_ROWS}
            """
            workout_log = db.fetch_all(workout_log_query)
            if workout_log:
                sheets_data['Workout Log'] = workout_log
                logger.info(f"Fetched {len(workout_log)} workout log rows")

            # Export Weekly Summary
            logger.info("Calculating weekly summary")
            weekly_summary = calculate_weekly_summary('Total')
            if weekly_summary:
                sheets_data['Weekly Summary'] = weekly_summary
                logger.info(f"Generated {len(weekly_summary)} weekly summary rows")

            # Export Session Summary with exercise categories
            logger.info("Fetching session summary data")
            session_summary_query = f"""
            SELECT 
                date(wl.created_at) as session_date,
                wl.routine,
                wl.exercise,
                e.primary_muscle_group,
                e.secondary_muscle_group,
                e.tertiary_muscle_group,
                e.advanced_isolated_muscles,
                wl.planned_sets,
                wl.planned_min_reps,
                wl.planned_max_reps,
                wl.planned_weight,
                wl.planned_rir,
                wl.planned_rpe,
                wl.scored_weight,
                wl.scored_max_reps,
                wl.scored_rir,
                wl.scored_rpe
            FROM workout_log wl
            LEFT JOIN exercises e ON wl.exercise = e.exercise_name
            WHERE (
                wl.scored_weight IS NOT NULL
                OR wl.scored_max_reps IS NOT NULL
                OR wl.planned_weight IS NOT NULL
                OR wl.planned_sets IS NOT NULL
            )
            AND wl.routine IS NOT NULL
            ORDER BY wl.created_at DESC
            LIMIT {MAX_EXPORT_ROWS}
            """
            session_summary = db.fetch_all(session_summary_query)
            if session_summary:
                sheets_data['Session Summary'] = session_summary
                logger.info(f"Fetched {len(session_summary)} session summary rows")

            # Export Progression Goals
            logger.info("Fetching progression goals")
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
            progression_goals = db.fetch_all(progression_query)
            if progression_goals:
                sheets_data['Progression Goals'] = progression_goals
                logger.info(f"Fetched {len(progression_goals)} progression goals")

            # Export Categories Summary
            logger.info("Calculating exercise categories")
            categories = calculate_exercise_categories()
            if categories:
                sheets_data['Categories'] = categories
                logger.info(f"Generated {len(categories)} category rows")

            # Export Isolated Muscles Stats
            logger.info("Calculating isolated muscles stats")
            isolated_muscles = calculate_isolated_muscles_stats()
            if isolated_muscles:
                sheets_data['Isolated Muscles'] = isolated_muscles
                logger.info(f"Generated {len(isolated_muscles)} isolated muscle rows")

        # Generate filename with timestamp
        filename = generate_timestamped_filename('workout_tracker_summary')
        
        logger.info(f"Creating Excel workbook with {len(sheets_data)} sheets: {list(sheets_data.keys())}")
        
        try:
            response = create_excel_workbook(sheets_data, filename)
            
            # Ensure response has data
            if hasattr(response, 'data') and (not response.data or len(response.data) == 0):
                logger.error("Response data is empty!")
                raise ValueError("Generated Excel file is empty")
            
            logger.info(f"Excel export completed successfully: {filename}")
            return response
        except Exception as create_error:
            logger.exception(f"Error in create_excel_workbook: {create_error}")
            raise
        
    except Exception as e:
        logger.exception(f"Error exporting to Excel: {e}")
        # Return JSON error response properly
        # The frontend should handle this and show an error message
        error = error_response(
            "EXPORT_FAILED",
            "Failed to export data to Excel. Please try again.",
            500
        )
        # error_response returns a tuple (response, status_code)
        # For export endpoint, we need to return it properly
        return error

@exports_bp.route("/export_to_workout_log", methods=["POST"])
def export_to_workout_log():
    """Export current workout plan to workout log."""
    try:
        logger.info("Starting workout plan export to workout log")
        
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
                logger.warning("No exercises found in workout plan to export")
                return error_response(
                    "NO_DATA",
                    "No exercises to export",
                    400
                )
            
            exported_count = 0
            for exercise in workout_plan:
                params = (
                    exercise["id"], exercise["routine"], exercise["exercise"],
                    exercise["sets"], exercise["min_rep_range"], exercise["max_rep_range"],
                    exercise["rir"], exercise["rpe"], exercise["weight"]
                )
                db.execute_query(insert_query, params)
                exported_count += 1
            
            logger.info(f"Successfully exported {exported_count} exercises to workout log")
        
        return success_response(
            message=f"Workout plan exported successfully ({exported_count} exercises)"
        )
            
    except Exception as e:
        logger.exception(f"Error exporting workout plan: {e}")
        return error_response(
            "EXPORT_FAILED",
            "Failed to export workout plan",
            500
        ) 

@exports_bp.route("/export_summary", methods=["POST"])
def export_summary():
    """
    Export summary data based on specified parameters.
    
    Memory-efficient implementation without pandas.
    """
    try:
        params = request.get_json() or {}
        method = params.get('method', 'Total')
        
        logger.info(f"Starting summary export with method: {method}")
        sheets_data = {}
        
        # Export Weekly Summary
        logger.info("Calculating weekly summary")
        weekly_data = calculate_weekly_summary(method)
        if weekly_data:
            sheets_data['Weekly Summary'] = weekly_data
            logger.info(f"Generated {len(weekly_data)} weekly summary rows")
        
        # Export Categories
        logger.info("Calculating exercise categories")
        categories = calculate_exercise_categories()
        if categories:
            sheets_data['Categories'] = categories
            logger.info(f"Generated {len(categories)} category rows")
        
        if not sheets_data:
            logger.warning("No data available for export")
            return error_response(
                "NO_DATA",
                "No data available to export",
                400
            )
        
        # Generate filename with method and timestamp
        base_name = f'workout_summary_{method}'
        filename = generate_timestamped_filename(base_name)
        
        logger.info(f"Creating Excel workbook with {len(sheets_data)} sheets")
        response = create_excel_workbook(sheets_data, filename)
        logger.info("Summary export completed successfully")
        
        return response
        
    except Exception as e:
        logger.exception(f"Error exporting summary: {e}")
        return error_response(
            "EXPORT_FAILED",
            "Failed to export summary data",
            500
        )


@exports_bp.route("/export_large_dataset", methods=["POST"])
def export_large_dataset():
    """
    Stream export for large datasets to prevent memory issues.
    
    This endpoint uses a generator to stream data directly to the client,
    preventing the entire dataset from being loaded into memory at once.
    """
    try:
        params = request.get_json() or {}
        export_type = params.get('type', 'all')  # 'all', 'workout_log', 'session_summary'
        
        logger.info(f"Starting streaming export for type: {export_type}")
        
        def data_generator():
            """Generator that yields (sheet_name, data) tuples for streaming."""
            with DatabaseHandler() as db:
                if export_type in ['all', 'workout_log']:
                    # Stream workout log in batches
                    logger.info("Streaming workout log data")
                    query = f"""
                    SELECT * FROM workout_log 
                    ORDER BY created_at DESC
                    LIMIT {MAX_EXPORT_ROWS}
                    """
                    workout_log = db.fetch_all(query)
                    if workout_log:
                        yield ('Workout Log', workout_log)
                
                if export_type in ['all', 'session_summary']:
                    # Stream session summary
                    logger.info("Streaming session summary data")
                    query = f"""
                    SELECT 
                        date(wl.created_at) as session_date,
                        wl.routine,
                        wl.exercise,
                        e.primary_muscle_group,
                        e.secondary_muscle_group,
                        wl.planned_sets,
                        wl.planned_min_reps,
                        wl.planned_max_reps,
                        wl.planned_weight,
                        wl.scored_weight,
                        wl.scored_max_reps
                    FROM workout_log wl
                    LEFT JOIN exercises e ON wl.exercise = e.exercise_name
                    WHERE wl.scored_weight IS NOT NULL
                       OR wl.scored_max_reps IS NOT NULL
                    ORDER BY wl.created_at DESC
                    LIMIT {MAX_EXPORT_ROWS}
                    """
                    session_data = db.fetch_all(query)
                    if session_data:
                        yield ('Session Summary', session_data)
                
                if export_type == 'all':
                    # Add summary sheets
                    logger.info("Generating summary sheets")
                    weekly = calculate_weekly_summary('Total')
                    if weekly:
                        yield ('Weekly Summary', weekly)
                    
                    categories = calculate_exercise_categories()
                    if categories:
                        yield ('Categories', categories)
        
        filename = generate_timestamped_filename(f'workout_export_{export_type}')
        logger.info(f"Starting streaming response for {filename}")
        
        return stream_excel_response(data_generator(), filename)
        
    except Exception as e:
        logger.exception(f"Error in streaming export: {e}")
        return error_response(
            "EXPORT_FAILED",
            "Failed to stream export data",
            500
        )
 