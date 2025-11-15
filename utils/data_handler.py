from typing import Any, Dict, List, Optional

from utils.database import DatabaseHandler
from utils.exercise_manager import ExerciseManager
from utils.logger import get_logger


logger = get_logger()


class DataHandler:
    """Application-facing data operations that back the Flask routes."""

    @staticmethod
    def fetch_user_selection() -> List[Dict[str, Any]]:
        """Return the user selection rows joined with their exercise metadata."""
        query = """
            SELECT
                us.id,
                us.routine,
                us.exercise,
                us.sets,
                us.min_rep_range,
                us.max_rep_range,
                us.rir,
                us.rpe,
                us.weight,
                e.primary_muscle_group,
                e.secondary_muscle_group,
                e.tertiary_muscle_group,
                e.advanced_isolated_muscles,
                e.utility,
                e.grips,
                e.stabilizers,
                e.synergists
            FROM user_selection us
            LEFT JOIN exercises e ON us.exercise = e.exercise_name
        """

        with DatabaseHandler() as db:
            results = db.fetch_all(query)
            if not results:
                logger.debug("No user_selection rows found")
            return results

    @staticmethod
    def add_exercise(
        routine: str,
        exercise: str,
        sets: int,
        min_rep_range: int,
        max_rep_range: int,
        rir: Optional[int],
        weight: float,
        rpe: Optional[float] = None,
    ) -> str:
        """Delegate to ExerciseManager for normalised user-selection inserts."""
        return ExerciseManager.add_exercise(
            routine,
            exercise,
            sets,
            min_rep_range,
            max_rep_range,
            rir,
            weight,
            rpe,
        )

    @staticmethod
    def remove_exercise(exercise_id: int) -> None:
        """Delete a user selection entry."""
        ExerciseManager.delete_exercise(exercise_id)

    @staticmethod
    def fetch_unique_values(table: str, column: str) -> List[Any]:
        """Fetch unique values for a given column in a table."""
        return ExerciseManager.fetch_unique_values(table, column)

    @staticmethod
    def save_exercise(exercise_data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalise and persist an exercise row through ExerciseManager."""
        return ExerciseManager.save_exercise(exercise_data)
