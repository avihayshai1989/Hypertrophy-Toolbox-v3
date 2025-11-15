"""Session-level analytics mirroring the weekly summary weighting."""
from __future__ import annotations

from collections import defaultdict
from typing import Any, Dict, Optional, Tuple

from utils.database import DatabaseHandler
from utils.volume_classifier import get_volume_class
from utils.weekly_summary import STATUS_MAP


def calculate_session_summary(
    routine: Optional[str] = None,
    time_window: Optional[Tuple[str, str]] = None,
) -> Dict[str, Dict[str, Dict[str, Any]]]:
    """Aggregate weighted sets per muscle, grouped by routine and optional date window."""
    start_date, end_date = (time_window if time_window else (None, None))

    query = """
        SELECT
            us.id AS selection_id,
            us.routine,
            us.sets,
            us.min_rep_range,
            us.max_rep_range,
            us.weight,
            e.primary_muscle_group,
            e.secondary_muscle_group,
            e.tertiary_muscle_group,
            wl.id AS log_id,
            wl.created_at
        FROM user_selection us
        JOIN exercises e ON us.exercise = e.exercise_name
        LEFT JOIN workout_log wl ON wl.workout_plan_id = us.id
        WHERE 1=1
    """
    params: list[Any] = []

    if routine:
        query += " AND us.routine = ?"
        params.append(routine)

    if start_date:
        query += " AND wl.created_at IS NOT NULL AND DATE(wl.created_at) >= DATE(?)"
        params.append(start_date)
    if end_date:
        query += " AND wl.created_at IS NOT NULL AND DATE(wl.created_at) <= DATE(?)"
        params.append(end_date)

    query += " ORDER BY us.routine, wl.created_at"

    with DatabaseHandler() as db:
        rows = db.fetch_all(query, params if params else None)

    totals: Dict[str, Dict[str, Dict[str, float]]] = defaultdict(lambda: defaultdict(lambda: {'sets': 0.0, 'reps': 0.0, 'volume': 0.0}))
    occurrences: Dict[str, Dict[str, set]] = defaultdict(lambda: defaultdict(set))

    for row in rows:
        routine_name = row.get('routine') or 'Unassigned'
        sets = row.get('sets') or 0
        avg_reps = 0.0
        min_rep = row.get('min_rep_range')
        max_rep = row.get('max_rep_range')
        if min_rep is not None and max_rep is not None:
            avg_reps = (min_rep + max_rep) / 2.0
        load = row.get('weight') or 0
        log_id = row.get('log_id')
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
                bucket = totals[routine_name][muscle]
                bucket['sets'] += weighted_sets
                bucket['reps'] += weighted_reps
                bucket['volume'] += weighted_volume
                if log_id:
                    occurrences[routine_name][muscle].add(log_id)

    summary: Dict[str, Dict[str, Dict[str, Any]]] = {}
    for routine_name, muscle_map in totals.items():
        summary[routine_name] = {}
        for muscle, aggregates in sorted(muscle_map.items()):
            weekly_sets = aggregates['sets']
            session_ids = occurrences[routine_name].get(muscle, set())
            session_count = len(session_ids) or 1
            sets_per_session = weekly_sets / session_count if session_count else weekly_sets
            volume_class = get_volume_class(weekly_sets)
            summary[routine_name][muscle] = {
                'weekly_sets': round(weekly_sets, 2),
                'sets_per_session': round(sets_per_session, 2),
                'status': STATUS_MAP.get(volume_class, 'low'),
                'volume_class': volume_class,
                'total_reps': round(aggregates['reps'], 2),
                'total_volume': round(aggregates['volume'], 2),
            }

    return summary
