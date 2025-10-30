from utils.database import get_db_connection
import sqlite3

def export_volume_plan(volume_data):
    """
    Export volume data to the workout plan database
    """
    conn = get_db_connection()
    try:
        # Create a new volume plan entry
        cursor = conn.cursor()
        
        # Store the volume plan
        cursor.execute('''
            INSERT INTO volume_plans (training_days, created_at)
            VALUES (?, datetime('now'))
        ''', (volume_data['training_days'],))
        
        plan_id = cursor.lastrowid
        
        # Store individual muscle group volumes
        for muscle, data in volume_data['volumes'].items():
            cursor.execute('''
                INSERT INTO muscle_volumes 
                (plan_id, muscle_group, weekly_sets, sets_per_session, status)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                plan_id,
                muscle,
                data,  # This is the weekly_sets value
                round(data / volume_data['training_days'], 1),  # Calculate sets_per_session
                'optimal'  # Default status
            ))
        
        conn.commit()
        return plan_id
        
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        conn.rollback()
        return None
    finally:
        conn.close() 