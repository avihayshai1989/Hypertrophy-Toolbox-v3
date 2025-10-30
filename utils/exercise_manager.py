from utils.database import DatabaseHandler
import sqlite3

class ExerciseManager:
    """
    Handles operations for fetching and managing exercises.
    """

    @staticmethod
    def get_exercises(filters=None):
        """
        Fetch exercises from the database, optionally filtered.
        :param filters: Dictionary containing filter criteria.
        :return: List of exercise names.
        """
        base_query = """
        SELECT exercise_name 
        FROM exercises 
        WHERE exercise_name IS NOT NULL
        """
        
        params = []
        if filters:
            conditions = []
            for field, value in filters.items():
                if field in [
                    "primary_muscle_group", 
                    "secondary_muscle_group",
                    "tertiary_muscle_group",
                    "advanced_isolated_muscles",
                    "grips",
                    "stabilizers",
                    "synergists"
                ]:
                    conditions.append(f"{field} LIKE ?")
                    params.append(f"%{value}%")
                else:
                    conditions.append(f"LOWER({field}) = LOWER(?)")
                    params.append(value)
            
            if conditions:
                base_query += " AND " + " AND ".join(conditions)

        base_query += " ORDER BY exercise_name ASC"
        print(f"DEBUG: Final query: {base_query} with params: {params}")

        with DatabaseHandler() as db:
            try:
                results = db.fetch_all(base_query, params if params else None)
                return [row["exercise_name"] for row in results if row["exercise_name"]]
            except Exception as e:
                print(f"Error fetching exercises: {e}")
                return []

    @staticmethod
    def add_exercise(routine, exercise, sets, min_rep_range, max_rep_range, rir, weight, rpe=None):
        """
        Add a new exercise entry to the user_selection table.
        Ensures duplicate entries are not allowed.
        """
        if not all([routine, exercise, sets, min_rep_range, max_rep_range, weight]):
            print("Error: Missing required fields for adding an exercise.")
            return "Error: Missing required fields."

        duplicate_check_query = """
        SELECT COUNT(*) AS count FROM user_selection
        WHERE routine = ? 
        AND exercise = ?
        """

        insert_query = """
        INSERT INTO user_selection 
        (routine, exercise, sets, min_rep_range, max_rep_range, rir, weight, rpe)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """

        try:
            with DatabaseHandler() as db:
                # Check for duplicates only by routine and exercise
                params = (routine, exercise)
                existing_count = db.fetch_one(duplicate_check_query, params)
                
                if existing_count and existing_count["count"] > 0:
                    print(f"Duplicate exercise found: {routine}, {exercise}")
                    return "Exercise already exists in this routine."

                # Insert new exercise
                insert_params = (routine, exercise, sets, min_rep_range, max_rep_range, rir, weight, rpe)
                db.execute_query(insert_query, insert_params)
                print(f"DEBUG: Exercise added - {exercise} in routine {routine}")
                return "Exercise added successfully."

        except Exception as e:
            print(f"Database error in add_exercise: {e}")
            return f"Database error: {e}"

    @staticmethod
    def delete_exercise(exercise_id):
        """
        Delete an exercise from the user_selection table using its unique ID.
        """
        query = "DELETE FROM user_selection WHERE id = ?"
        with DatabaseHandler() as db:
            try:
                db.execute_query(query, (exercise_id,))
                print(f"DEBUG: Exercise with ID {exercise_id} deleted.")
            except sqlite3.Error as e:
                print(f"Error deleting exercise: {e}")

    @staticmethod
    def fetch_unique_values(table, column):
        """
        Fetch unique values from a specific column in a table.
        """
        query = f"SELECT DISTINCT {column} FROM {table} WHERE {column} IS NOT NULL ORDER BY {column} ASC"
        with DatabaseHandler() as db:
            try:
                results = db.fetch_all(query)
                print(f"DEBUG: Unique values fetched for {column} in {table}")
                return [row[column] for row in results]
            except Exception as e:
                print(f"Error fetching unique values: {e}")
                return []

    @staticmethod
    def build_query(base_query, filters, valid_fields):
        """
        Dynamically build a SQL query with conditions based on filters.
        """
        query_conditions = []
        params = []
        for field, value in (filters or {}).items():
            if field in valid_fields and value:
                query_conditions.append(f"LOWER({field}) LIKE ?")
                params.append(f"%{value.lower()}%")
        if query_conditions:
            base_query += " AND " + " AND ".join(query_conditions)
        base_query += " ORDER BY exercise_name ASC"
        print(f"DEBUG: Built query - {base_query} with params {params}")
        return base_query, params

# Publicly expose key functions
get_exercises = ExerciseManager.get_exercises
add_exercise = ExerciseManager.add_exercise
delete_exercise = ExerciseManager.delete_exercise
fetch_unique_values = ExerciseManager.fetch_unique_values
