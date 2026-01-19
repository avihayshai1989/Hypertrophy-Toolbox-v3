"""Aggregations for weekly volume and supporting analytics."""
from __future__ import annotations

from collections import defaultdict
from typing import Any, Dict, List, Optional

from utils.database import DatabaseHandler
from utils.volume_classifier import get_volume_class


STATUS_MAP = {
    'low-volume': 'low',
    'medium-volume': 'medium',
    'high-volume': 'high',
    'ultra-volume': 'excessive',
}


def calculate_weekly_summary(method: Optional[str] = None) -> Dict[str, Dict[str, Any]]:
    """Aggregate weighted weekly set counts per muscle group.

    Args:
        method: Optional summary mode retained for backwards compatibility. Current
            implementation ignores the value but accepts inputs like "Total" so
            existing callers do not raise ``TypeError``.
    """
    _ = method  # Method handled implicitly; provided for API compatibility.
    query = """
        SELECT
            us.routine,
            us.sets,
            us.min_rep_range,
            us.max_rep_range,
            us.weight,
            e.primary_muscle_group,
            e.secondary_muscle_group,
            e.tertiary_muscle_group
        FROM user_selection us
        JOIN exercises e ON us.exercise = e.exercise_name
    """

    with DatabaseHandler() as db:
        rows = db.fetch_all(query)

    totals = defaultdict(lambda: {'sets': 0.0, 'reps': 0.0, 'volume': 0.0})
    sessions_by_muscle: Dict[str, set[str]] = defaultdict(set)

    for row in rows:
        sets = row.get('sets') or 0
        routine = row.get('routine')
        avg_reps = 0.0
        min_rep = row.get('min_rep_range')
        max_rep = row.get('max_rep_range')
        if min_rep is not None and max_rep is not None:
            avg_reps = (min_rep + max_rep) / 2.0
        load = row.get('weight') or 0
        contributions = (
            (row.get('primary_muscle_group'), 1.0),
            (row.get('secondary_muscle_group'), 0.5),
            (row.get('tertiary_muscle_group'), 0.25),
        )
        for muscle, weight_factor in contributions:
            if muscle and weight_factor:
                weighted_sets = sets * weight_factor
                weighted_reps = weighted_sets * avg_reps
                weighted_volume = weighted_reps * load
                bucket = totals[muscle]
                bucket['sets'] += weighted_sets
                bucket['reps'] += weighted_reps
                bucket['volume'] += weighted_volume
                if routine:
                    sessions_by_muscle[muscle].add(routine)

    global_sessions = {row.get('routine') for row in rows if row.get('routine')}
    summary: Dict[str, Dict[str, Any]] = {}
    for muscle, aggregates in totals.items():
        weekly_sets = aggregates['sets']
        muscle_sessions = sessions_by_muscle.get(muscle)
        session_count = len(muscle_sessions) if muscle_sessions else len(global_sessions) or 1
        sets_per_session = weekly_sets / session_count if session_count else weekly_sets
        volume_class = get_volume_class(weekly_sets)
        summary[muscle] = {
            'weekly_sets': round(weekly_sets, 2),
            'sets_per_session': round(sets_per_session, 2),
            'status': STATUS_MAP.get(volume_class, 'low'),
            'volume_class': volume_class,
            'total_reps': round(aggregates['reps'], 2),
            'total_volume': round(aggregates['volume'], 2),
        }

    return dict(sorted(summary.items()))


def calculate_exercise_categories() -> List[Dict[str, Any]]:
    """Count distinct exercises per canonical classification bucket."""
    query = """
        SELECT
            us.exercise,
            e.mechanic,
            e.utility,
            e.force,
            e.difficulty
        FROM user_selection us
        JOIN exercises e ON us.exercise = e.exercise_name
    """

    with DatabaseHandler() as db:
        rows = db.fetch_all(query)

    categories = {
        'Mechanic': defaultdict(set),
        'Utility': defaultdict(set),
        'Force': defaultdict(set),
        'Difficulty': defaultdict(set),
    }

    for row in rows:
        exercise = row.get('exercise')
        if not exercise:
            continue
        if row.get('mechanic'):
            categories['Mechanic'][row['mechanic'].title()].add(exercise)
        if row.get('utility'):
            categories['Utility'][row['utility'].title()].add(exercise)
        if row.get('force'):
            categories['Force'][row['force'].title()].add(exercise)
        if row.get('difficulty'):
            categories['Difficulty'][row['difficulty'].title()].add(exercise)

    results: List[Dict[str, Any]] = []
    for category, sub_map in categories.items():
        for subcategory in sorted(sub_map.keys()):
            results.append(
                {
                    'category': category,
                    'subcategory': subcategory,
                    'total_exercises': len(sub_map[subcategory]),
                }
            )
    return results


def calculate_isolated_muscles_stats() -> List[Dict[str, Any]]:
    """
    Calculate statistics for advanced isolated muscles using the mapping table.
    Assumes tables: user_selection us, exercises e, exercise_isolated_muscles eim.
    """
    query = """
    SELECT 
        eim.muscle                          AS isolated_muscle,
        COUNT(DISTINCT us.exercise)         AS exercise_count,
        SUM(us.sets)                        AS total_sets,
        SUM(us.sets * (us.min_rep_range + us.max_rep_range) / 2.0) AS total_reps,
        SUM(us.sets * (us.min_rep_range + us.max_rep_range) / 2.0 * us.weight) AS total_volume
    FROM user_selection us
    JOIN exercises e ON us.exercise = e.exercise_name
    JOIN exercise_isolated_muscles eim ON eim.exercise_name = e.exercise_name
    GROUP BY eim.muscle
    ORDER BY eim.muscle ASC
    """
    try:
        with DatabaseHandler() as db:
            return db.fetch_all(query)
    except Exception as e:
        print(f"Error calculating isolated muscles stats: {e}")
        return []
