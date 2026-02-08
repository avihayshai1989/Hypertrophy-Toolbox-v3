"""
Tests for utils/data_handler.py

Covers the DataHandler class which wraps database operations:
- fetch_user_selection with JOIN on exercises
- add_exercise delegation to ExerciseManager
- remove_exercise delegation
- save_exercise delegation
- fetch_unique_values delegation
"""
import pytest
from utils.data_handler import DataHandler


class TestFetchUserSelection:
    """Tests for DataHandler.fetch_user_selection method."""

    def test_fetch_user_selection_empty(self, clean_db):
        """Should return empty list when no selections exist."""
        result = DataHandler.fetch_user_selection()
        assert result == []

    def test_fetch_user_selection_returns_list(self, clean_db):
        """Should always return a list."""
        result = DataHandler.fetch_user_selection()
        assert isinstance(result, list)

    def test_fetch_user_selection_with_entries(self, clean_db, user_selection_fixture):
        """Should return user selections when they exist."""
        result = DataHandler.fetch_user_selection()
        assert len(result) >= 1

    def test_fetch_user_selection_includes_exercise_metadata(
        self, clean_db, user_selection_with_exercise
    ):
        """Should include exercise metadata from JOIN."""
        result = DataHandler.fetch_user_selection()
        assert len(result) >= 1
        
        # Check that exercise fields are included
        first_row = result[0]
        # These fields come from the exercises table JOIN
        assert "primary_muscle_group" in first_row.keys() or hasattr(first_row, "primary_muscle_group")

    def test_fetch_user_selection_handles_missing_exercise(self, clean_db):
        """DB enforces FK constraint - orphaned user_selection cannot be created."""
        import sqlite3
        from utils.database import DatabaseHandler
        
        # The database enforces FK constraints, so this should fail
        with pytest.raises(sqlite3.IntegrityError):
            with DatabaseHandler() as db:
                db.execute_query("""
                    INSERT INTO user_selection (
                        routine, exercise, sets, min_rep_range, max_rep_range, rir, weight
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, ("Push", "NonExistentExercise", 3, 8, 12, 2, 80.0))


class TestAddExercise:
    """Tests for DataHandler.add_exercise method."""

    def test_add_exercise_delegates_to_manager(self, clean_db, exercise_factory):
        """Should delegate to ExerciseManager.add_exercise."""
        exercise_factory("Test Add Exercise")
        
        result = DataHandler.add_exercise(
            routine="Push",
            exercise="Test Add Exercise",
            sets=3,
            min_rep_range=8,
            max_rep_range=12,
            rir=2,
            weight=80.0
        )
        
        # ExerciseManager.add_exercise returns "Success" or error string
        assert result == "Success" or "Error" not in result

    def test_add_exercise_with_rpe(self, clean_db, exercise_factory):
        """Should pass RPE parameter through to ExerciseManager."""
        exercise_factory("RPE Exercise")
        
        result = DataHandler.add_exercise(
            routine="Pull",
            exercise="RPE Exercise",
            sets=4,
            min_rep_range=6,
            max_rep_range=8,
            rir=None,
            weight=100.0,
            rpe=8.5
        )
        
        assert result == "Success" or "Error" not in result


class TestRemoveExercise:
    """Tests for DataHandler.remove_exercise method."""

    def test_remove_exercise_delegates(self, clean_db, user_selection_fixture):
        """Should delegate to ExerciseManager.delete_exercise."""
        exercise_id = user_selection_fixture["id"]
        
        # Should not raise
        DataHandler.remove_exercise(exercise_id)
        
        # Verify deletion
        from utils.database import DatabaseHandler
        with DatabaseHandler() as db:
            result = db.fetch_one(
                "SELECT * FROM user_selection WHERE id = ?",
                (exercise_id,)
            )
            assert result is None


class TestFetchUniqueValues:
    """Tests for DataHandler.fetch_unique_values method."""

    def test_fetch_unique_values_delegates(self, clean_db, exercise_factory):
        """Should delegate to ExerciseManager.fetch_unique_values."""
        exercise_factory("Test Unique")
        
        # This should work - delegates to ExerciseManager
        result = DataHandler.fetch_unique_values("exercises", "primary_muscle_group")
        
        # Should return a list
        assert isinstance(result, list)


class TestSaveExercise:
    """Tests for DataHandler.save_exercise method."""

    def test_save_exercise_delegates(self, clean_db):
        """Should delegate to ExerciseManager.save_exercise."""
        exercise_data = {
            "exercise_name": "New Test Exercise",
            "primary_muscle_group": "Chest",
            "secondary_muscle_group": "Triceps",
            "tertiary_muscle_group": None,
            "advanced_isolated_muscles": None,
            "force": "Push",
            "mechanic": "Compound",
            "utility": "Basic",
            "equipment": "Barbell",
            "grips": None,
            "stabilizers": None,
            "synergists": None,
            "difficulty": "Beginner",
            "movement_pattern": None,
            "movement_subpattern": None,
        }
        
        # Should not raise
        result = DataHandler.save_exercise(exercise_data)
        
        # ExerciseManager.save_exercise returns the saved data
        assert isinstance(result, dict)


# Fixtures for data_handler tests
@pytest.fixture
def user_selection_fixture(clean_db, exercise_factory):
    """Create a user_selection entry for testing."""
    from utils.database import DatabaseHandler
    
    # First create the exercise (FK requirement)
    exercise_factory("Basic Exercise")
    
    with DatabaseHandler() as db:
        db.execute_query("""
            INSERT INTO user_selection (
                routine, exercise, sets, min_rep_range, max_rep_range, rir, weight
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, ("Push", "Basic Exercise", 3, 8, 12, 2, 80.0))
        
        result = db.fetch_one(
            "SELECT id FROM user_selection ORDER BY id DESC LIMIT 1"
        )
        assert result is not None
        
        return {"id": result["id"], "exercise": "Basic Exercise"}


@pytest.fixture
def user_selection_with_exercise(clean_db, exercise_factory):
    """Create user_selection with matching exercise for JOIN tests."""
    from utils.database import DatabaseHandler
    
    # Create exercise first
    exercise_factory("Joined Exercise")
    
    with DatabaseHandler() as db:
        db.execute_query("""
            INSERT INTO user_selection (
                routine, exercise, sets, min_rep_range, max_rep_range, rir, weight
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, ("Push", "Joined Exercise", 3, 8, 12, 2, 80.0))
        
        result = db.fetch_one(
            "SELECT id FROM user_selection ORDER BY id DESC LIMIT 1"
        )
        assert result is not None
        
        return {"id": result["id"], "exercise": "Joined Exercise"}
