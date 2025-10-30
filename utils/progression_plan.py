from .database import DatabaseHandler
from datetime import datetime, timedelta

def get_exercise_history(exercise):
    """Get the exercise history from workout log."""
    query = """
    SELECT *
    FROM workout_log
    WHERE exercise = ?
    ORDER BY created_at DESC
    LIMIT 10
    """
    
    with DatabaseHandler() as db:
        return db.fetch_all(query, (exercise,))

def generate_progression_suggestions(history):
    """Generate progression suggestions based on exercise history."""
    if not history:
        return []
    
    latest = history[0]
    suggestions = []
    
    # Technique improvement suggestion
    suggestions.append({
        "type": "technique",
        "title": "Technique Improvement",
        "description": f"Focus on improving your {latest['exercise']} form and mobility.",
        "action": "Set a goal date for mastering proper technique"
    })
    
    # Repetition increase suggestion
    if latest['scored_max_reps']:
        suggestions.append({
            "type": "reps",
            "title": "Increase Repetitions",
            "description": f"Add 1 rep to your {latest['exercise']} sets (current max: {latest['scored_max_reps']})",
            "action": "Set a goal date for achieving this increment"
        })
    
    # Weight increase suggestion
    if latest['scored_weight']:
        weight_increment = 2.5 if latest['scored_weight'] < 20 else 5
        suggestions.append({
            "type": "weight",
            "title": "Increase Working Weight",
            "description": f"Increase your {latest['exercise']} weight by {weight_increment}kg (current: {latest['scored_weight']}kg)",
            "action": "Set a goal date and target weight increment"
        })
    
    # Additional set suggestion
    if latest['planned_sets']:
        suggestions.append({
            "type": "sets",
            "title": "Add Another Set",
            "description": f"Add one more set to your {latest['exercise']} (current: {latest['planned_sets']} sets)",
            "action": "Set a goal date for adapting to increased volume"
        })
    
    return suggestions

def save_progression_goal(data):
    """Save a new progression goal to the database."""
    query = """
    INSERT INTO progression_goals (
        exercise,
        goal_type,
        current_value,
        target_value,
        goal_date,
        created_at
    ) VALUES (?, ?, ?, ?, ?, ?)
    """
    
    params = (
        data['exercise'],
        data['goal_type'],
        data['current_value'],
        data['target_value'],
        data['goal_date'],
        datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    )
    
    with DatabaseHandler() as db:
        db.execute_query(query, params) 