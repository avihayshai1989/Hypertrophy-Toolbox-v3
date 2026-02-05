"""
Tests for Program Backup / Program Library functionality.

Tests cover:
1. Creating backups saves active program data
2. Restoring backups (replace mode)
3. Restoring skips missing exercises
4. Deleting backups removes them
5. Erase/reset integration with auto-backup
"""
import pytest
import sqlite3
from datetime import datetime
from utils.program_backup import (
    initialize_backup_tables,
    create_backup,
    list_backups,
    get_backup_details,
    restore_backup,
    delete_backup,
    create_auto_backup_before_erase,
    get_latest_auto_backup,
    get_active_program_count,
    BACKUP_SCHEMA_VERSION,
)
from utils.database import DatabaseHandler


class TestProgramBackup:
    """Test suite for program backup functionality."""
    
    # -------------------------------------------------------------------------
    # Test 1: Create backup saves active program data
    # -------------------------------------------------------------------------
    
    def test_create_backup_saves_active_program_data(self, clean_db, exercise_factory, workout_plan_factory):
        """Test that creating a backup correctly captures active program data."""
        # Seed exercises
        ex1 = exercise_factory("Bench Press", primary_muscle_group="Chest")
        ex2 = exercise_factory("Squat", primary_muscle_group="Quadriceps")
        ex3 = exercise_factory("Deadlift", primary_muscle_group="Back")
        
        # Seed active program selections
        workout_plan_factory(exercise_name=ex1, routine="Workout A", sets=3, min_rep_range=6, max_rep_range=8, weight=100.0)
        workout_plan_factory(exercise_name=ex2, routine="Workout A", sets=4, min_rep_range=8, max_rep_range=10, weight=120.0)
        workout_plan_factory(exercise_name=ex3, routine="Workout B", sets=3, min_rep_range=5, max_rep_range=5, weight=150.0)
        
        # Create backup
        backup = create_backup(name="Test Backup", note="Test note")
        
        # Assert backup exists
        assert backup is not None
        assert backup['id'] is not None
        assert backup['name'] == "Test Backup"
        assert backup['note'] == "Test note"
        assert backup['backup_type'] == "manual"
        assert backup['schema_version'] == BACKUP_SCHEMA_VERSION
        assert backup['item_count'] == 3  # Three exercises
        
        # Verify backup items match expected fields
        details = get_backup_details(backup['id'])
        assert details is not None
        assert len(details['items']) == 3
        
        # Check specific item fields
        item_exercises = {item['exercise'] for item in details['items']}
        assert item_exercises == {"Bench Press", "Squat", "Deadlift"}
        
        # Verify all fields are captured
        bench_item = next(item for item in details['items'] if item['exercise'] == "Bench Press")
        assert bench_item['routine'] == "Workout A"
        assert bench_item['sets'] == 3
        assert bench_item['min_rep_range'] == 6
        assert bench_item['max_rep_range'] == 8
        assert bench_item['weight'] == 100.0
    
    def test_create_backup_with_empty_program(self, clean_db):
        """Test that creating a backup with empty program creates empty backup."""
        backup = create_backup(name="Empty Backup")
        
        assert backup is not None
        assert backup['item_count'] == 0
        
        details = get_backup_details(backup['id'])
        assert details is not None
        assert len(details['items']) == 0
    
    def test_create_backup_requires_name(self, clean_db):
        """Test that backup name is required."""
        with pytest.raises(ValueError, match="Backup name is required"):
            create_backup(name="")
        
        with pytest.raises(ValueError, match="Backup name is required"):
            create_backup(name="   ")
    
    def test_list_backups_returns_all_backups(self, clean_db, exercise_factory, workout_plan_factory):
        """Test that list_backups returns all created backups."""
        exercise_factory("Test Exercise")
        workout_plan_factory(exercise_name="Test Exercise")
        
        # Create multiple backups
        create_backup(name="Backup 1")
        create_backup(name="Backup 2")
        create_backup(name="Backup 3")
        
        backups = list_backups()
        
        assert len(backups) == 3
        names = {b['name'] for b in backups}
        assert names == {"Backup 1", "Backup 2", "Backup 3"}
    
    # -------------------------------------------------------------------------
    # Test 2: Restore backup (replace mode)
    # -------------------------------------------------------------------------
    
    def test_restore_backup_replaces_active_program(self, clean_db, exercise_factory, workout_plan_factory):
        """Test that restoring a backup replaces the current active program."""
        # Create initial exercises and program
        ex1 = exercise_factory("Bench Press", primary_muscle_group="Chest")
        ex2 = exercise_factory("Squat", primary_muscle_group="Quadriceps")
        
        workout_plan_factory(exercise_name=ex1, routine="Workout A", sets=3, weight=100.0)
        workout_plan_factory(exercise_name=ex2, routine="Workout A", sets=4, weight=120.0)
        
        # Create backup
        backup = create_backup(name="Original Program")
        
        # Mutate active program
        with DatabaseHandler() as db:
            db.execute_query("DELETE FROM user_selection")
            # Add different exercises
            ex3 = exercise_factory("Deadlift", primary_muscle_group="Back")
            workout_plan_factory(exercise_name=ex3, routine="Workout B", sets=5, weight=180.0)
        
        # Verify mutation
        assert get_active_program_count() == 1
        
        # Restore backup
        result = restore_backup(backup['id'])
        
        assert result['restored_count'] == 2
        assert result['backup_name'] == "Original Program"
        assert len(result['skipped']) == 0
        
        # Verify active program equals backup snapshot
        with DatabaseHandler() as db:
            rows = db.fetch_all("SELECT exercise, sets, weight FROM user_selection ORDER BY exercise")
            assert len(rows) == 2
            
            exercises = {row['exercise']: row for row in rows}
            assert "Bench Press" in exercises
            assert "Squat" in exercises
            assert exercises["Bench Press"]['sets'] == 3
            assert exercises["Bench Press"]['weight'] == 100.0
            assert exercises["Squat"]['sets'] == 4
            assert exercises["Squat"]['weight'] == 120.0
    
    # -------------------------------------------------------------------------
    # Test 3: Restore skips missing exercises
    # -------------------------------------------------------------------------
    
    def test_restore_skips_missing_exercises(self, clean_db, exercise_factory, workout_plan_factory):
        """Test that restore skips exercises that are missing from catalog."""
        # Create exercises and backup
        ex1 = exercise_factory("Bench Press", primary_muscle_group="Chest")
        ex2 = exercise_factory("Squat", primary_muscle_group="Quadriceps")
        ex3 = exercise_factory("Overhead Press", primary_muscle_group="Shoulders")
        
        workout_plan_factory(exercise_name=ex1, routine="Workout A", sets=3)
        workout_plan_factory(exercise_name=ex2, routine="Workout A", sets=4)
        workout_plan_factory(exercise_name=ex3, routine="Workout A", sets=3)
        
        backup = create_backup(name="Full Program")
        
        # Remove one exercise from catalog (simulates missing exercise)
        with DatabaseHandler() as db:
            # First clear user_selection to avoid FK constraint
            db.execute_query("DELETE FROM user_selection")
            # Delete exercise from catalog
            db.execute_query("DELETE FROM exercises WHERE exercise_name = ?", ("Overhead Press",))
        
        # Restore backup
        result = restore_backup(backup['id'])
        
        # Should not fail
        assert result['restored_count'] == 2  # Only 2 of 3 restored
        assert "Overhead Press" in result['skipped']
        
        # Verify only valid exercises were restored
        with DatabaseHandler() as db:
            rows = db.fetch_all("SELECT exercise FROM user_selection")
            exercises = {row['exercise'] for row in rows}
            assert exercises == {"Bench Press", "Squat"}
            assert "Overhead Press" not in exercises
    
    def test_restore_nonexistent_backup_raises_error(self, clean_db):
        """Test that restoring a non-existent backup raises ValueError."""
        with pytest.raises(ValueError, match="not found"):
            restore_backup(99999)
    
    # -------------------------------------------------------------------------
    # Test 4: Delete backup removes it
    # -------------------------------------------------------------------------
    
    def test_delete_backup_removes_backup_and_items(self, clean_db, exercise_factory, workout_plan_factory):
        """Test that deleting a backup removes both header and items."""
        exercise_factory("Test Exercise")
        workout_plan_factory(exercise_name="Test Exercise")
        
        backup = create_backup(name="To Delete")
        backup_id = backup['id']
        
        # Verify backup exists
        assert get_backup_details(backup_id) is not None
        
        # Delete backup
        result = delete_backup(backup_id)
        assert result is True
        
        # Verify backup and items are gone
        assert get_backup_details(backup_id) is None
        
        # Verify items are also deleted
        with DatabaseHandler() as db:
            items = db.fetch_all(
                "SELECT * FROM program_backup_items WHERE backup_id = ?",
                (backup_id,)
            )
            assert len(items) == 0
    
    def test_delete_nonexistent_backup_returns_false(self, clean_db):
        """Test that deleting a non-existent backup returns False."""
        result = delete_backup(99999)
        assert result is False
    
    # -------------------------------------------------------------------------
    # Test 5: Erase/reset integration
    # -------------------------------------------------------------------------
    
    def test_auto_backup_created_before_erase(self, clean_db, exercise_factory, workout_plan_factory):
        """Test that auto-backup is created when active program has data."""
        exercise_factory("Test Exercise")
        workout_plan_factory(exercise_name="Test Exercise", routine="Workout A")
        
        # Verify active program has data
        assert get_active_program_count() == 1
        
        # Create auto-backup
        auto_backup = create_auto_backup_before_erase()
        
        assert auto_backup is not None
        assert auto_backup['backup_type'] == "auto"
        assert auto_backup['item_count'] == 1
        assert "Pre-Erase Auto-Backup" in auto_backup['name']
    
    def test_auto_backup_skipped_when_program_empty(self, clean_db):
        """Test that auto-backup is skipped when active program is empty."""
        assert get_active_program_count() == 0
        
        auto_backup = create_auto_backup_before_erase()
        
        assert auto_backup is None
    
    def test_backups_survive_table_drop(self, clean_db, exercise_factory, workout_plan_factory):
        """Test that backups survive when user_selection is dropped."""
        exercise_factory("Test Exercise")
        workout_plan_factory(exercise_name="Test Exercise")
        
        # Create backup
        backup = create_backup(name="Survivor Backup")
        
        # Simulate erase by dropping user_selection
        with DatabaseHandler() as db:
            db.execute_query("DELETE FROM workout_log")
            db.execute_query("DELETE FROM user_selection")
        
        # Verify backup still exists
        backups = list_backups()
        assert len(backups) == 1
        assert backups[0]['name'] == "Survivor Backup"
        
        # Verify backup details are intact
        details = get_backup_details(backup['id'])
        assert details is not None
        assert len(details['items']) == 1
    
    def test_get_latest_auto_backup(self, clean_db, exercise_factory, workout_plan_factory):
        """Test that get_latest_auto_backup returns most recent auto-backup."""
        exercise_factory("Test Exercise")
        workout_plan_factory(exercise_name="Test Exercise")
        
        # Create multiple auto-backups
        create_backup(name="Auto 1", backup_type="auto")
        create_backup(name="Auto 2", backup_type="auto")
        create_backup(name="Manual", backup_type="manual")
        
        latest = get_latest_auto_backup()
        
        assert latest is not None
        assert latest['backup_type'] == "auto"
        # Should be the most recent auto-backup (Auto 2)
        assert latest['name'] == "Auto 2"


class TestProgramBackupAPI:
    """Test suite for program backup API endpoints."""
    
    def test_api_list_backups(self, client, clean_db, exercise_factory, workout_plan_factory):
        """Test GET /api/backups returns list of backups."""
        exercise_factory("Test Exercise")
        workout_plan_factory(exercise_name="Test Exercise")
        
        create_backup(name="API Test Backup")
        
        response = client.get('/api/backups')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['ok'] is True
        assert len(data['data']) == 1
        assert data['data'][0]['name'] == "API Test Backup"
    
    def test_api_create_backup(self, client, clean_db, exercise_factory, workout_plan_factory):
        """Test POST /api/backups creates a backup."""
        exercise_factory("Test Exercise")
        workout_plan_factory(exercise_name="Test Exercise")
        
        response = client.post('/api/backups', 
            json={'name': 'New Backup', 'note': 'Test note'},
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['ok'] is True
        assert data['data']['name'] == "New Backup"
        assert data['data']['item_count'] == 1
    
    def test_api_create_backup_requires_name(self, client, clean_db):
        """Test POST /api/backups requires name."""
        response = client.post('/api/backups',
            json={'note': 'No name'},
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['ok'] is False
        assert 'name' in data['error']['message'].lower()
    
    def test_api_get_backup_details(self, client, clean_db, exercise_factory, workout_plan_factory):
        """Test GET /api/backups/<id> returns backup details."""
        exercise_factory("Test Exercise")
        workout_plan_factory(exercise_name="Test Exercise")
        
        backup = create_backup(name="Detail Test")
        
        response = client.get(f'/api/backups/{backup["id"]}')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['ok'] is True
        assert data['data']['name'] == "Detail Test"
        assert 'items' in data['data']
        assert len(data['data']['items']) == 1
    
    def test_api_get_backup_not_found(self, client, clean_db):
        """Test GET /api/backups/<id> returns 404 for missing backup."""
        response = client.get('/api/backups/99999')
        
        assert response.status_code == 404
        data = response.get_json()
        assert data['ok'] is False
    
    def test_api_restore_backup(self, client, clean_db, exercise_factory, workout_plan_factory):
        """Test POST /api/backups/<id>/restore restores backup."""
        ex1 = exercise_factory("Original Exercise")
        workout_plan_factory(exercise_name=ex1)
        
        backup = create_backup(name="Restore Test")
        
        # Clear and add new data
        with DatabaseHandler() as db:
            db.execute_query("DELETE FROM user_selection")
        
        response = client.post(f'/api/backups/{backup["id"]}/restore',
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['ok'] is True
        assert data['data']['restored_count'] == 1
    
    def test_api_delete_backup(self, client, clean_db, exercise_factory, workout_plan_factory):
        """Test DELETE /api/backups/<id> deletes backup."""
        exercise_factory("Test Exercise")
        workout_plan_factory(exercise_name="Test Exercise")
        
        backup = create_backup(name="To Delete")
        
        response = client.delete(f'/api/backups/{backup["id"]}')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['ok'] is True
        
        # Verify backup is gone
        assert get_backup_details(backup['id']) is None


class TestEraseDataDeletesBackups:
    """Test the erase-data endpoint deletes all data including backups."""
    
    def test_erase_data_deletes_backups(self, client, clean_db, exercise_factory, workout_plan_factory):
        """Test that /erase-data deletes all backups (full reset)."""
        # Setup: Create exercise and add to workout plan
        exercise_factory("Test Exercise")
        workout_plan_factory(exercise_name="Test Exercise")
        
        # Create some backups
        create_backup(name="Manual Backup 1")
        create_backup(name="Manual Backup 2")
        
        # Verify backups exist
        backups_before = list_backups()
        assert len(backups_before) == 2
        
        # Call erase-data
        response = client.post('/erase-data')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['ok'] is True
        
        # Verify all backups are deleted
        backups_after = list_backups()
        assert len(backups_after) == 0
    
    def test_erase_data_on_empty_database(self, client, clean_db):
        """Test that /erase-data works on empty database."""
        # Ensure program is empty
        assert get_active_program_count() == 0
        
        # Call erase-data
        response = client.post('/erase-data')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['ok'] is True
        assert data.get('data') is None
    
    def test_erase_data_reinitializes_tables(self, client, clean_db, exercise_factory, workout_plan_factory):
        """Test that /erase-data properly reinitializes all tables."""
        # Setup: Create exercise and workout plan
        exercise_factory("Test Exercise")
        workout_plan_factory(exercise_name="Test Exercise")
        
        # Create a backup
        create_backup(name="Test Backup")
        
        # Call erase-data
        response = client.post('/erase-data')
        assert response.status_code == 200
        
        # Verify workout plan is cleared
        assert get_active_program_count() == 0
        
        # Verify backups are cleared
        backups = list_backups()
        assert len(backups) == 0
        
        # Verify we can create new backups (tables were reinitialized)
        exercise_factory("New Exercise")
        workout_plan_factory(exercise_name="New Exercise")
        new_backup = create_backup(name="New Backup After Erase")
        assert new_backup is not None
        assert new_backup['item_count'] == 1
