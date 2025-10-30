from utils.database import DatabaseHandler


def calculate_weekly_summary(method="Total"):
    """
    Calculate the weekly summary based on the selected method.
    Consolidates results across primary, secondary, and tertiary muscle groups.
    """
    # Scaling factors for each method
    scaling_factors = {
        "Total": {"primary": 1, "secondary": 1, "tertiary": 0.33},
        "Fractional": {"primary": 1, "secondary": 0.5, "tertiary": 0.17},
        "Direct": {"primary": 1, "secondary": 0, "tertiary": 0},
    }

    # Validate the method
    if method not in scaling_factors:
        print(f"ERROR: Unsupported method '{method}'. Defaulting to 'Total'.")
        method = "Total"

    factors = scaling_factors[method]

    # Unified query to consolidate data
    query = f"""
        SELECT muscle_group,
               ROUND(SUM(total_sets), 1) AS total_sets,
               ROUND(SUM(total_reps), 1) AS total_reps,
               ROUND(SUM(total_weight), 1) AS total_weight
        FROM (
            SELECT e.primary_muscle_group AS muscle_group,
                   SUM(us.sets * {factors['primary']}) AS total_sets,
                   SUM(us.sets * us.max_rep_range * {factors['primary']}) AS total_reps,
                   SUM(us.sets * us.weight * {factors['primary']}) AS total_weight
            FROM user_selection us
            JOIN exercises e ON us.exercise = e.exercise_name
            WHERE e.primary_muscle_group IS NOT NULL
            GROUP BY e.primary_muscle_group

            UNION ALL

            SELECT e.secondary_muscle_group AS muscle_group,
                   SUM(us.sets * {factors['secondary']}) AS total_sets,
                   SUM(us.sets * us.max_rep_range * {factors['secondary']}) AS total_reps,
                   SUM(us.sets * us.weight * {factors['secondary']}) AS total_weight
            FROM user_selection us
            JOIN exercises e ON us.exercise = e.exercise_name
            WHERE e.secondary_muscle_group IS NOT NULL
            GROUP BY e.secondary_muscle_group

            UNION ALL

            SELECT e.tertiary_muscle_group AS muscle_group,
                   SUM(us.sets * {factors['tertiary']}) AS total_sets,
                   SUM(us.sets * us.max_rep_range * {factors['tertiary']}) AS total_reps,
                   SUM(us.sets * us.weight * {factors['tertiary']}) AS total_weight
            FROM user_selection us
            JOIN exercises e ON us.exercise = e.exercise_name
            WHERE e.tertiary_muscle_group IS NOT NULL
            GROUP BY e.tertiary_muscle_group
        ) AS combined
        WHERE muscle_group IS NOT NULL
        GROUP BY muscle_group;
    """

    try:
        with DatabaseHandler() as db_handler:
            # Execute the query and fetch results
            db_handler.cursor.execute(query)
            results = db_handler.cursor.fetchall()

            print(f"DEBUG: Weekly summary query executed successfully. Results: {results}")

            # Format results for output
            summary = [
                {
                    "muscle_group": row["muscle_group"],
                    "total_sets": row["total_sets"],
                    "total_reps": row["total_reps"],
                    "total_weight": row["total_weight"],
                }
                for row in results
            ]
            return summary

    except Exception as e:
        print(f"Error calculating weekly summary for method '{method}': {e}")
        return []


def get_weekly_summary():
    """
    Fetch weekly summary from the database.
    """
    query = """
        SELECT muscle_group, total_sets, total_reps, total_weight
        FROM weekly_summary
    """
    try:
        with DatabaseHandler() as db_handler:
            results = db_handler.fetch_all(query)
            print(f"DEBUG: Weekly summary fetched successfully. Results: {results}")
            return results
    except Exception as e:
        print(f"Error fetching weekly summary: {e}")
        return []


def calculate_total_sets(muscle_group):
    """
    Calculate total sets for a specific muscle group.
    """
    query = """
        SELECT SUM(us.sets) AS total_sets
        FROM user_selection us
        JOIN exercises e ON us.exercise = e.exercise_name
        WHERE e.primary_muscle_group = ?
    """
    try:
        with DatabaseHandler() as db_handler:
            result = db_handler.fetch_one(query, (muscle_group,))
            total_sets = result["total_sets"] if result and "total_sets" in result else 0
            print(f"DEBUG: Total sets for '{muscle_group}' -> {total_sets}")
            return total_sets
    except Exception as e:
        print(f"Error calculating total sets for muscle group '{muscle_group}': {e}")
        return 0


def calculate_exercise_categories():
    """Calculate the totals for each exercise category."""
    query = """
    WITH CategoryCounts AS (
        SELECT 
            'Mechanic' as category,
            COALESCE(e.mechanic, 'Unspecified') as subcategory,
            COUNT(DISTINCT us.exercise) as total_exercises
        FROM user_selection us
        JOIN exercises e ON us.exercise = e.exercise_name
        GROUP BY e.mechanic
        
        UNION ALL
        
        SELECT 
            'Utility' as category,
            COALESCE(e.utility, 'Unspecified') as subcategory,
            COUNT(DISTINCT us.exercise) as total_exercises
        FROM user_selection us
        JOIN exercises e ON us.exercise = e.exercise_name
        GROUP BY e.utility
        
        UNION ALL
        
        SELECT 
            'Force' as category,
            COALESCE(e.force, 'Unspecified') as subcategory,
            COUNT(DISTINCT us.exercise) as total_exercises
        FROM user_selection us
        JOIN exercises e ON us.exercise = e.exercise_name
        GROUP BY e.force
    )
    SELECT *
    FROM CategoryCounts
    ORDER BY 
        CASE category 
            WHEN 'Mechanic' THEN 1 
            WHEN 'Utility' THEN 2 
            WHEN 'Force' THEN 3 
            ELSE 4 
        END,
        subcategory
    """
    
    try:
        with DatabaseHandler() as db:
            results = db.fetch_all(query)
            print(f"DEBUG: Category query results: {results}")
            return results
    except Exception as e:
        print(f"Error calculating exercise categories: {e}")
        return []


def calculate_isolated_muscles_stats():
    """Calculate statistics for advanced isolated muscles."""
    query = """
    WITH RECURSIVE split(muscle, rest) AS (
        SELECT '', e.advanced_isolated_muscles || ','
        FROM user_selection us
        JOIN exercises e ON us.exercise = e.exercise_name
        WHERE e.advanced_isolated_muscles IS NOT NULL
        
        UNION ALL
        
        SELECT
            substr(rest, 0, instr(rest, ',')),
            substr(rest, instr(rest, ',') + 1)
        FROM split
        WHERE rest <> ''
    )
    SELECT 
        TRIM(muscle) as isolated_muscle,
        COUNT(DISTINCT us.exercise) as exercise_count,
        SUM(us.sets) as total_sets,
        SUM(us.sets * (us.min_rep_range + us.max_rep_range) / 2) as total_reps,
        SUM(us.sets * (us.min_rep_range + us.max_rep_range) / 2 * us.weight) as total_volume
    FROM user_selection us
    JOIN exercises e ON us.exercise = e.exercise_name
    JOIN split ON e.advanced_isolated_muscles LIKE '%' || muscle || '%'
    WHERE muscle <> ''
    GROUP BY muscle
    ORDER BY muscle ASC
    """
    
    try:
        with DatabaseHandler() as db:
            results = db.fetch_all(query)
            print(f"DEBUG: Isolated muscles stats: {results}")
            return results
    except Exception as e:
        print(f"Error calculating isolated muscles stats: {e}")
        return []
