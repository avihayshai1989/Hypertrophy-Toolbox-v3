import sqlite3
import utils.config  # Dynamic import for test support


def get_user_selection():
    """
    Fetches user selection data along with muscle group information
    from the exercises table.
    :return: List of dictionaries containing user selection and muscle groups.
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
        us.weight,
        us.superset_group,
        e.primary_muscle_group,
        e.secondary_muscle_group,
        e.tertiary_muscle_group,
        e.advanced_isolated_muscles,
        e.utility,
        e.grips,
        e.stabilizers,
        e.synergists
    FROM user_selection us
    JOIN exercises e ON us.exercise = e.exercise_name;
    """
    try:
        connection = sqlite3.connect(utils.config.DB_FILE)
        connection.row_factory = sqlite3.Row
        cursor = connection.cursor()
        cursor.execute(query)
        results = cursor.fetchall()
        connection.close()

        if not results:
            print("DEBUG: No user selection data found.")  # Debugging log

        # Format results into a list of dictionaries for easier handling
        user_selection = [
            {
                "id": row["id"],
                "routine": row["routine"],
                "exercise": row["exercise"],
                "sets": row["sets"],
                "min_rep_range": row["min_rep_range"],
                "max_rep_range": row["max_rep_range"],
                "rir": row["rir"],
                "weight": row["weight"],
                "superset_group": row["superset_group"],
                "primary_muscle_group": row["primary_muscle_group"],
                "secondary_muscle_group": row["secondary_muscle_group"],
                "tertiary_muscle_group": row["tertiary_muscle_group"],
                "advanced_isolated_muscles": row["advanced_isolated_muscles"],
                "utility": row["utility"],
                "grips": row["grips"],
                "stabilizers": row["stabilizers"],
                "synergists": row["synergists"],
            }
            for row in results
        ]
        print("DEBUG: User selection data retrieved successfully.")  # Debugging log
        return user_selection

    except sqlite3.OperationalError as oe:
        print(f"Operational error in database: {oe}")
        return []
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return []
    except Exception as ex:
        print(f"Unexpected error: {ex}")
        return []
