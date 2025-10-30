from flask import Flask, render_template, url_for, jsonify
from utils import initialize_database
from utils.database import DatabaseHandler, add_progression_goals_table, add_volume_tracking_tables
from routes.workout_log import workout_log_bp
from routes.weekly_summary import weekly_summary_bp
from routes.session_summary import session_summary_bp
from routes.exports import exports_bp
from routes.filters import filters_bp
from routes.workout_plan import workout_plan_bp, initialize_exercise_order
from routes.main import main_bp
from routes.progression_plan import progression_plan_bp
from routes.volume_splitter import volume_splitter_bp
from datetime import datetime
from werkzeug.middleware.proxy_fix import ProxyFix

app = Flask(__name__)
app.url_map.strict_slashes = False  # This makes Flask handle URLs with or without trailing slashes
app.wsgi_app = ProxyFix(app.wsgi_app)

# Initialize the database
print("Initializing database...")
initialize_database()
print("Adding progression goals table...")
add_progression_goals_table()
print("Adding volume tracking tables...")
add_volume_tracking_tables()
print("Initializing exercise order...")
initialize_exercise_order()
print("Database initialization complete")

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

# Print registered routes
print("\nRegistered routes:")
for rule in app.url_map.iter_rules():
    print(f"{rule.endpoint}: {rule.rule} [{', '.join(rule.methods)}]")

@app.template_filter('datetime')
def format_datetime(value, format='%d-%m-%Y'):
    if value and value != 'None':
        try:
            if isinstance(value, str):
                # Parse the date string (assuming it's in ISO format)
                date_obj = datetime.strptime(value, '%Y-%m-%d')
            else:
                date_obj = value
            return date_obj.strftime(format)
        except (ValueError, TypeError):
            return value
    return ''

@app.before_request
def clear_trailing():
    from flask import redirect, request
    rp = request.path 
    if rp != '/' and rp.endswith('/'):
        return redirect(rp[:-1])

@app.route('/erase-data', methods=['POST'])
def erase_data():
    try:
        # Drop all tables
        with DatabaseHandler() as db:
            tables = [
                'user_selection',
                'progression_goals',
                'muscle_volumes',
                'volume_plans',
                'workout_log'
            ]
            
            for table in tables:
                db.execute_query(f"DROP TABLE IF EXISTS {table}")
        
        # Reinitialize database
        print("Reinitializing database...")
        initialize_database()
        print("Adding progression goals table...")
        add_progression_goals_table()
        print("Adding volume tracking tables...")
        add_volume_tracking_tables()
        print("Initializing exercise order...")
        initialize_exercise_order()
        
        return jsonify({
            "success": True, 
            "message": "All data has been erased and tables reinitialized successfully."
        })
    except Exception as e:
        print(f"Error erasing data: {e}")
        return jsonify({
            "success": False, 
            "message": str(e)
        }), 500

if __name__ == "__main__":
    app.run(debug=True)
