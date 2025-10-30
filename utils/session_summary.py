from utils.database import DatabaseHandler


def calculate_session_summary(method="Total"):
    """
    Calculate the per-session summary for sets and reps by muscle group.
    :param method: Calculation method - "Total", "Fractional", or "Direct".
    :return: List of session summary data.
    """
    # Scaling factors for each calculation method
    scaling_factors = {
        "Total": {"primary": 1, "secondary": 1, "tertiary": 0.33},
        "Fractional": {"primary": 1, "secondary": 0.5, "tertiary": 0.17},
        "Direct": {"primary": 1, "secondary": 0, "tertiary": 0},
    }

    # Validate method
    if method not in scaling_factors:
        print(f"ERROR: Unsupported method '{method}'. Defaulting to 'Total'.")
        method = "Total"

    factors = scaling_factors[method]

    # Query to calculate session summary
    query = """
    SELECT 
        us.routine,
        e.primary_muscle_group as muscle_group,
        SUM(us.sets) as total_sets,
        SUM(us.sets * (us.min_rep_range + us.max_rep_range) / 2) as total_reps,
        SUM(us.sets * (us.min_rep_range + us.max_rep_range) / 2 * us.weight) as total_volume
    FROM user_selection us
    JOIN exercises e ON us.exercise = e.exercise_name
    GROUP BY us.routine, e.primary_muscle_group
    ORDER BY us.routine, e.primary_muscle_group
    """

    try:
        with DatabaseHandler() as db:
            results = db.fetch_all(query)
            return results
    except Exception as e:
        print(f"Error calculating session summary: {e}")
        return []
