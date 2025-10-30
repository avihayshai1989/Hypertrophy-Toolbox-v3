from utils.database import DatabaseHandler


class ExerciseFilter:
    """
    Handles filtering of exercises based on provided criteria.
    """

    def __init__(self):
        pass  # Remove persistent database instance to avoid reuse issues

    def filter_exercises(self, filters):
        """
        Filter exercises based on the provided filters.

        :param filters: Dictionary containing filter criteria.
        :return: List of exercise names matching the criteria.
        """
        valid_fields = [
            "primary_muscle_group", "secondary_muscle_group", 
            "tertiary_muscle_group", "force", 
            "equipment", "mechanic", "difficulty",
            "target_muscles", "utility", "grips", 
            "stabilizers", "synergists"
        ]
        base_query = "SELECT exercise_name FROM exercises WHERE 1=1"
        query_conditions = []
        params = []

        # Dynamically build query based on provided filters
        for field, value in filters.items():
            if field in valid_fields and value:  # Ensure field is valid and value is not empty
                query_conditions.append(f"{field} = ?")
                params.append(value)

        if query_conditions:
            base_query += " AND " + " AND ".join(query_conditions)

        try:
            with DatabaseHandler() as db:
                results = db.fetch_all(base_query, params)
                print(f"DEBUG: Filter query executed: {base_query} with params {params}")
                return [row[0] for row in results if isinstance(row, tuple)]  # Extract exercise names from results
        except Exception as e:
            print(f"Error filtering exercises with filters {filters}: {e}")
            return []

