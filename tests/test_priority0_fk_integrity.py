"""
Priority 0 Tests: Foreign Key Integrity (CASCADE Deletes)
"""
import pytest
import sqlite3


class TestForeignKeyEnabled:
    """Test that foreign keys are enabled in database connections."""
    
    def test_foreign_keys_enabled_in_handler(self, db_handler):
        """Test that DatabaseHandler has foreign keys enabled."""
        result = db_handler.fetch_one("PRAGMA foreign_keys;")
        assert result['foreign_keys'] == 1, "Foreign keys must be enabled"
    
    def test_foreign_keys_enabled_after_reconnect(self, db_handler):
        """Test that foreign keys are enabled after reconnection."""
        # Close and reconnect
        db_handler.close()
        new_handler = db_handler.__class__()
        
        result = new_handler.fetch_one("PRAGMA foreign_keys;")
        assert result['foreign_keys'] == 1, "Foreign keys must be enabled on new connection"
        
        new_handler.close()


class TestCascadeDelete:
    """Test CASCADE delete behavior for foreign keys."""
    
    def test_delete_exercise_cascades_to_user_selection(self, clean_db, exercise_factory, workout_plan_factory):
        """Test that deleting an exercise cascades to user_selection entries."""
        exercise_name = exercise_factory("Test Exercise")
        plan_id = workout_plan_factory(exercise_name=exercise_name)
        
        # Verify plan exists
        result = clean_db.fetch_one("SELECT COUNT(*) as count FROM user_selection WHERE exercise = ?", (exercise_name,))
        assert result['count'] == 1
        
        # Delete exercise
        clean_db.execute_query("DELETE FROM exercises WHERE exercise_name = ?", (exercise_name,))
        
        # Verify user_selection entry is deleted (CASCADE)
        result = clean_db.fetch_one("SELECT COUNT(*) as count FROM user_selection WHERE exercise = ?", (exercise_name,))
        assert result['count'] == 0, "user_selection entry should be deleted when exercise is deleted"
    
    def test_delete_workout_plan_cascades_to_logs(self, clean_db, workout_plan_factory, workout_log_factory):
        """Test that deleting a workout plan cascades to workout_log entries."""
        plan_id = workout_plan_factory()
        log_id1 = workout_log_factory(plan_id=plan_id)
        log_id2 = workout_log_factory(plan_id=plan_id)
        
        # Verify logs exist
        result = clean_db.fetch_one("SELECT COUNT(*) as count FROM workout_log WHERE workout_plan_id = ?", (plan_id,))
        assert result['count'] == 2
        
        # Delete workout plan
        clean_db.execute_query("DELETE FROM user_selection WHERE id = ?", (plan_id,))
        
        # Verify workout_log entries are deleted (CASCADE)
        result = clean_db.fetch_one("SELECT COUNT(*) as count FROM workout_log WHERE workout_plan_id = ?", (plan_id,))
        assert result['count'] == 0, "workout_log entries should be deleted when workout plan is deleted"
    
    def test_delete_volume_plan_cascades_to_muscle_volumes(self, clean_db):
        """Test that deleting a volume plan cascades to muscle_volumes."""
        # Create volume plan
        clean_db.execute_query("""
            INSERT INTO volume_plans (training_days, created_at)
            VALUES (4, datetime('now'))
        """)
        
        plan_result = clean_db.fetch_one("SELECT last_insert_rowid() as id")
        plan_id = plan_result['id']
        
        # Create muscle volumes
        clean_db.execute_query("""
            INSERT INTO muscle_volumes (plan_id, muscle_group, weekly_sets, sets_per_session, status)
            VALUES (?, 'Chest', 20, 5.0, 'Active')
        """, (plan_id,))
        
        clean_db.execute_query("""
            INSERT INTO muscle_volumes (plan_id, muscle_group, weekly_sets, sets_per_session, status)
            VALUES (?, 'Legs', 24, 6.0, 'Active')
        """, (plan_id,))
        
        # Verify muscle volumes exist
        result = clean_db.fetch_one("SELECT COUNT(*) as count FROM muscle_volumes WHERE plan_id = ?", (plan_id,))
        assert result['count'] == 2
        
        # Delete volume plan
        clean_db.execute_query("DELETE FROM volume_plans WHERE id = ?", (plan_id,))
        
        # Verify muscle_volumes entries are deleted (CASCADE)
        result = clean_db.fetch_one("SELECT COUNT(*) as count FROM muscle_volumes WHERE plan_id = ?", (plan_id,))
        assert result['count'] == 0, "muscle_volumes entries should be deleted when volume_plan is deleted"


class TestForeignKeyPreventsInvalidReferences:
    """Test that foreign keys prevent invalid references."""
    
    def test_cannot_insert_user_selection_without_exercise(self, clean_db):
        """Test that inserting user_selection with non-existent exercise fails."""
        with pytest.raises(sqlite3.IntegrityError):
            clean_db.execute_query("""
                INSERT INTO user_selection (routine, exercise, sets, min_rep_range, max_rep_range, rir, weight)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, ("Test Routine", "Non-existent Exercise", 3, 6, 8, 3, 50.0))
    
    def test_cannot_insert_workout_log_without_workout_plan(self, clean_db):
        """Test that inserting workout_log with non-existent workout_plan_id fails."""
        with pytest.raises(sqlite3.IntegrityError):
            clean_db.execute_query("""
                INSERT INTO workout_log (workout_plan_id, routine, exercise, planned_sets, planned_min_reps,
                                        planned_max_reps, planned_rir, planned_weight)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (99999, "Test Routine", "Test Exercise", 3, 6, 8, 3, 50.0))
    
    def test_cannot_insert_muscle_volumes_without_volume_plan(self, clean_db):
        """Test that inserting muscle_volumes with non-existent plan_id fails."""
        with pytest.raises(sqlite3.IntegrityError):
            clean_db.execute_query("""
                INSERT INTO muscle_volumes (plan_id, muscle_group, weekly_sets, sets_per_session, status)
                VALUES (?, ?, ?, ?, ?)
            """, (99999, "Chest", 20, 5.0, "Active"))

