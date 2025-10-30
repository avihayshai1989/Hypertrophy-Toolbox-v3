import sqlite3
from utils.database import DatabaseHandler


class DataHandler:
    """
    Application-facing data operations using the DatabaseHandler.
    """

    @staticmethod
    def fetch_user_selection():
        """
        Fetch user selection data joined with muscle group info.
        """
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
            e.target_muscles,
            e.utility,
            e.grips,
            e.stabilizers,
            e.synergists
        FROM user_selection us
        JOIN exercises e ON us.exercise = e.exercise_name;
        """
        try:
            with DatabaseHandler() as db:
                results = db.fetch_all(query)
                if not results:
                    print("DEBUG: No user selection data found.")
                return [
                    {
                        "id": row["id"],
                        "routine": row["routine"],
                        "exercise": row["exercise"],
                        "sets": row["sets"],
                        "min_rep_range": row["min_rep_range"],
                        "max_rep_range": row["max_rep_range"],
                        "rir": row["rir"],
                        "rpe": row["rpe"],
                        "weight": row["weight"],
                        "primary_muscle_group": row["primary_muscle_group"],
                        "secondary_muscle_group": row["secondary_muscle_group"],
                        "tertiary_muscle_group": row["tertiary_muscle_group"],
                        "target_muscles": row["target_muscles"],
                        "utility": row["utility"],
                        "grips": row["grips"],
                        "stabilizers": row["stabilizers"],
                        "synergists": row["synergists"],
                    }
                    for row in results
                ]
        except Exception as e:
            print(f"Error fetching user selection: {e}")
            return []

    @staticmethod
    def add_exercise(routine, exercise, sets, min_rep_range, max_rep_range, rir, weight):
        """
        Add a new exercise entry to the user_selection table and return the new exercise ID.
        Checks for duplicates before insertion.
        """
        duplicate_check_query = """
        SELECT COUNT(*) AS count FROM user_selection
        WHERE routine = ? AND exercise = ? AND sets = ? AND min_rep_range = ?
        AND max_rep_range = ? AND rir = ? AND weight = ?
        """
        insert_query = """
        INSERT INTO user_selection 
        (routine, exercise, sets, min_rep_range, max_rep_range, rir, weight)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        try:
            with DatabaseHandler() as db:
                # Check for duplicates
                duplicate_count = db.fetch_one(
                    duplicate_check_query,
                    (routine, exercise, sets, min_rep_range, max_rep_range, rir, weight),
                )
                if duplicate_count and duplicate_count["count"] > 0:
                    print("DEBUG: Duplicate entry detected.")
                    return None

                # Insert new exercise
                db.cursor.execute(
                    insert_query,
                    (routine, exercise, sets, min_rep_range, max_rep_range, rir, weight),
                )
                db.connection.commit()
                new_id = db.cursor.lastrowid
                print(f"DEBUG: New exercise added with ID: {new_id}")
                return new_id
        except sqlite3.OperationalError as oe:
            print(f"Operational error adding exercise: {oe}")
            return None
        except Exception as e:
            print(f"Error adding exercise: {e}")
            return None

    @staticmethod
    def remove_exercise(exercise_id):
        """
        Remove an exercise from the user_selection table.
        """
        query = "DELETE FROM user_selection WHERE id = ?"
        try:
            with DatabaseHandler() as db:
                db.execute_query(query, (exercise_id,))
                print(f"DEBUG: Exercise with ID {exercise_id} removed.")
        except Exception as e:
            print(f"Error removing exercise: {e}")

    @staticmethod
    def fetch_unique_values(table, column):
        """
        Fetch unique values for a given column in a table.
        """
        query = f"SELECT DISTINCT {column} FROM {table} WHERE {column} IS NOT NULL ORDER BY {column} ASC"
        try:
            with DatabaseHandler() as db:
                results = db.fetch_all(query)
                if not results:
                    print(f"DEBUG: No unique values found for {column} in {table}.")
                return [row[column] for row in results if column in row]
        except Exception as e:
            print(f"Error fetching unique values for column '{column}' in table '{table}': {e}")
            return []
