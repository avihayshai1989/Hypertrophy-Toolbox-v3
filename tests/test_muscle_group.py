"""
Tests for utils/muscle_group.py - Muscle group queries for exercises.
"""

import pytest
from unittest.mock import patch, MagicMock
from utils.muscle_group import MuscleGroupHandler


@pytest.fixture
def handler():
    """Create a MuscleGroupHandler instance."""
    return MuscleGroupHandler()


class TestMuscleGroupHandlerInit:
    """Tests for MuscleGroupHandler initialization."""

    def test_init_creates_instance(self):
        """Should create handler instance."""
        handler = MuscleGroupHandler()
        assert handler is not None

    def test_muscle_groups_constant_exists(self):
        """MUSCLE_GROUPS constant should be defined."""
        assert hasattr(MuscleGroupHandler, 'MUSCLE_GROUPS')
        assert 'primary' in MuscleGroupHandler.MUSCLE_GROUPS
        assert 'secondary' in MuscleGroupHandler.MUSCLE_GROUPS
        assert 'tertiary' in MuscleGroupHandler.MUSCLE_GROUPS
        assert 'isolated' in MuscleGroupHandler.MUSCLE_GROUPS


class TestGetExerciseNames:
    """Tests for MuscleGroupHandler.get_exercise_names method."""

    @patch('utils.muscle_group.DatabaseHandler')
    def test_returns_exercise_names(self, mock_db_class, handler):
        """Should return list of exercise names."""
        mock_db = MagicMock()
        mock_db.__enter__ = MagicMock(return_value=mock_db)
        mock_db.__exit__ = MagicMock(return_value=False)
        mock_db.fetch_all.return_value = [
            {"exercise_name": "Bench Press"},
            {"exercise_name": "Squat"},
            {"exercise_name": "Deadlift"}
        ]
        mock_db_class.return_value = mock_db

        result = handler.get_exercise_names()

        assert result == ["Bench Press", "Squat", "Deadlift"]

    @patch('utils.muscle_group.DatabaseHandler')
    def test_returns_empty_list_on_empty_db(self, mock_db_class, handler):
        """Should return empty list when database is empty."""
        mock_db = MagicMock()
        mock_db.__enter__ = MagicMock(return_value=mock_db)
        mock_db.__exit__ = MagicMock(return_value=False)
        mock_db.fetch_all.return_value = []
        mock_db_class.return_value = mock_db

        result = handler.get_exercise_names()

        assert result == []

    @patch('utils.muscle_group.DatabaseHandler')
    def test_handles_database_error(self, mock_db_class, handler):
        """Should return empty list on database error."""
        mock_db = MagicMock()
        mock_db.__enter__ = MagicMock(return_value=mock_db)
        mock_db.__exit__ = MagicMock(return_value=False)
        mock_db.fetch_all.side_effect = Exception("DB error")
        mock_db_class.return_value = mock_db

        result = handler.get_exercise_names()

        assert result == []

    @patch('utils.muscle_group.DatabaseHandler')
    def test_filters_invalid_rows(self, mock_db_class, handler):
        """Should filter out rows without exercise_name key."""
        mock_db = MagicMock()
        mock_db.__enter__ = MagicMock(return_value=mock_db)
        mock_db.__exit__ = MagicMock(return_value=False)
        mock_db.fetch_all.return_value = [
            {"exercise_name": "Bench Press"},
            {"other_field": "value"},  # Missing exercise_name
            {"exercise_name": "Squat"}
        ]
        mock_db_class.return_value = mock_db

        result = handler.get_exercise_names()

        assert result == ["Bench Press", "Squat"]


class TestGetMuscleGroups:
    """Tests for MuscleGroupHandler.get_muscle_groups method."""

    @patch('utils.muscle_group.DatabaseHandler')
    def test_returns_muscle_groups_tuple(self, mock_db_class, handler):
        """Should return tuple of (primary, secondary, tertiary)."""
        mock_db = MagicMock()
        mock_db.__enter__ = MagicMock(return_value=mock_db)
        mock_db.__exit__ = MagicMock(return_value=False)
        mock_db.fetch_one.return_value = {
            "primary_muscle_group": "Chest",
            "secondary_muscle_group": "Triceps",
            "tertiary_muscle_group": "Shoulders"
        }
        mock_db_class.return_value = mock_db

        result = handler.get_muscle_groups("Bench Press")

        assert result == ("Chest", "Triceps", "Shoulders")

    @patch('utils.muscle_group.DatabaseHandler')
    def test_returns_none_tuple_for_unknown_exercise(self, mock_db_class, handler):
        """Should return (None, None, None) for unknown exercise."""
        mock_db = MagicMock()
        mock_db.__enter__ = MagicMock(return_value=mock_db)
        mock_db.__exit__ = MagicMock(return_value=False)
        mock_db.fetch_one.return_value = None
        mock_db_class.return_value = mock_db

        result = handler.get_muscle_groups("Unknown Exercise")

        assert result == (None, None, None)

    @patch('utils.muscle_group.DatabaseHandler')
    def test_handles_database_error(self, mock_db_class, handler):
        """Should return (None, None, None) on database error."""
        mock_db = MagicMock()
        mock_db.__enter__ = MagicMock(return_value=mock_db)
        mock_db.__exit__ = MagicMock(return_value=False)
        mock_db.fetch_one.side_effect = Exception("DB error")
        mock_db_class.return_value = mock_db

        result = handler.get_muscle_groups("Bench Press")

        assert result == (None, None, None)

    @patch('utils.muscle_group.DatabaseHandler')
    def test_passes_exercise_name_parameter(self, mock_db_class, handler):
        """Should pass exercise name as query parameter."""
        mock_db = MagicMock()
        mock_db.__enter__ = MagicMock(return_value=mock_db)
        mock_db.__exit__ = MagicMock(return_value=False)
        mock_db.fetch_one.return_value = {
            "primary_muscle_group": "Chest",
            "secondary_muscle_group": "Triceps",
            "tertiary_muscle_group": None
        }
        mock_db_class.return_value = mock_db

        handler.get_muscle_groups("Bench Press")

        call_args = mock_db.fetch_one.call_args
        assert call_args[0][1] == ("Bench Press",)


class TestFetchMuscleGroupsSummary:
    """Tests for MuscleGroupHandler.fetch_muscle_groups_summary method."""

    @patch('utils.muscle_group.DatabaseHandler')
    def test_returns_summary_list(self, mock_db_class, handler):
        """Should return list of muscle group summaries."""
        mock_db = MagicMock()
        mock_db.__enter__ = MagicMock(return_value=mock_db)
        mock_db.__exit__ = MagicMock(return_value=False)
        mock_db.fetch_all.return_value = [
            {"primary_muscle_group": "Chest", "exercise_count": 15},
            {"primary_muscle_group": "Back", "exercise_count": 12},
            {"primary_muscle_group": "Legs", "exercise_count": 10}
        ]
        mock_db_class.return_value = mock_db

        result = handler.fetch_muscle_groups_summary()

        assert len(result) == 3
        assert result[0] == {"muscle_group": "Chest", "exercise_count": 15}
        assert result[1] == {"muscle_group": "Back", "exercise_count": 12}
        assert result[2] == {"muscle_group": "Legs", "exercise_count": 10}

    @patch('utils.muscle_group.DatabaseHandler')
    def test_returns_empty_list_on_empty_db(self, mock_db_class, handler):
        """Should return empty list when database is empty."""
        mock_db = MagicMock()
        mock_db.__enter__ = MagicMock(return_value=mock_db)
        mock_db.__exit__ = MagicMock(return_value=False)
        mock_db.fetch_all.return_value = []
        mock_db_class.return_value = mock_db

        result = handler.fetch_muscle_groups_summary()

        assert result == []

    @patch('utils.muscle_group.DatabaseHandler')
    def test_handles_database_error(self, mock_db_class, handler):
        """Should return empty list on database error."""
        mock_db = MagicMock()
        mock_db.__enter__ = MagicMock(return_value=mock_db)
        mock_db.__exit__ = MagicMock(return_value=False)
        mock_db.fetch_all.side_effect = Exception("DB error")
        mock_db_class.return_value = mock_db

        result = handler.fetch_muscle_groups_summary()

        assert result == []


class TestFetchFullMuscleData:
    """Tests for MuscleGroupHandler.fetch_full_muscle_data method."""

    @patch('utils.muscle_group.DatabaseHandler')
    def test_returns_full_muscle_data(self, mock_db_class, handler):
        """Should return complete muscle data dict."""
        mock_db = MagicMock()
        mock_db.__enter__ = MagicMock(return_value=mock_db)
        mock_db.__exit__ = MagicMock(return_value=False)
        mock_db.fetch_one.return_value = {
            "primary_muscle_group": "Chest",
            "secondary_muscle_group": "Triceps",
            "tertiary_muscle_group": "Shoulders",
            "target_muscles": "Pectoralis Major",
            "stabilizers": "Core",
            "synergists": "Anterior Deltoid"
        }
        mock_db_class.return_value = mock_db

        result = handler.fetch_full_muscle_data("Bench Press")

        assert result["primary_muscle_group"] == "Chest"
        assert result["secondary_muscle_group"] == "Triceps"
        assert result["tertiary_muscle_group"] == "Shoulders"
        assert result["target_muscles"] == "Pectoralis Major"
        assert result["stabilizers"] == "Core"
        assert result["synergists"] == "Anterior Deltoid"

    @patch('utils.muscle_group.DatabaseHandler')
    def test_returns_empty_dict_for_unknown_exercise(self, mock_db_class, handler):
        """Should return empty dict for unknown exercise."""
        mock_db = MagicMock()
        mock_db.__enter__ = MagicMock(return_value=mock_db)
        mock_db.__exit__ = MagicMock(return_value=False)
        mock_db.fetch_one.return_value = None
        mock_db_class.return_value = mock_db

        result = handler.fetch_full_muscle_data("Unknown Exercise")

        assert result == {}

    @patch('utils.muscle_group.DatabaseHandler')
    def test_handles_database_error(self, mock_db_class, handler):
        """Should return empty dict on database error."""
        mock_db = MagicMock()
        mock_db.__enter__ = MagicMock(return_value=mock_db)
        mock_db.__exit__ = MagicMock(return_value=False)
        mock_db.fetch_one.side_effect = Exception("DB error")
        mock_db_class.return_value = mock_db

        result = handler.fetch_full_muscle_data("Bench Press")

        assert result == {}

    @patch('utils.muscle_group.DatabaseHandler')
    def test_passes_exercise_name_parameter(self, mock_db_class, handler):
        """Should pass exercise name as query parameter."""
        mock_db = MagicMock()
        mock_db.__enter__ = MagicMock(return_value=mock_db)
        mock_db.__exit__ = MagicMock(return_value=False)
        mock_db.fetch_one.return_value = {
            "primary_muscle_group": "Chest",
            "secondary_muscle_group": None,
            "tertiary_muscle_group": None,
            "target_muscles": None,
            "stabilizers": None,
            "synergists": None
        }
        mock_db_class.return_value = mock_db

        handler.fetch_full_muscle_data("Incline Press")

        call_args = mock_db.fetch_one.call_args
        assert call_args[0][1] == ("Incline Press",)


class TestMuscleGroupsConstant:
    """Tests for MUSCLE_GROUPS class constant."""

    def test_primary_muscles_defined(self):
        """Primary muscles should be defined."""
        assert MuscleGroupHandler.MUSCLE_GROUPS["primary"] == ["Chest", "Back", "Legs"]

    def test_secondary_muscles_defined(self):
        """Secondary muscles should be defined."""
        assert "Upper Chest" in MuscleGroupHandler.MUSCLE_GROUPS["secondary"]
        assert "Lower Back" in MuscleGroupHandler.MUSCLE_GROUPS["secondary"]

    def test_tertiary_muscles_defined(self):
        """Tertiary muscles should be defined."""
        assert "Upper Traps" in MuscleGroupHandler.MUSCLE_GROUPS["tertiary"]
        assert "Lower Abs" in MuscleGroupHandler.MUSCLE_GROUPS["tertiary"]

    def test_isolated_muscles_defined(self):
        """Isolated muscles should be defined."""
        assert "Pectoralis Major" in MuscleGroupHandler.MUSCLE_GROUPS["isolated"]
        assert "Latissimus Dorsi" in MuscleGroupHandler.MUSCLE_GROUPS["isolated"]

    def test_all_categories_are_lists(self):
        """All muscle group categories should be lists."""
        for category, muscles in MuscleGroupHandler.MUSCLE_GROUPS.items():
            assert isinstance(muscles, list), f"{category} should be a list"
