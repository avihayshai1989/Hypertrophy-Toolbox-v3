"""Session-level analytics mirroring the weekly summary weighting."""
from __future__ import annotations

from collections import defaultdict
from typing import Any, Dict, Optional, Tuple

from utils.database import DatabaseHandler
from utils.volume_classifier import get_volume_class
from utils.weekly_summary import STATUS_MAP, EFFECTIVE_STATUS_MAP
from utils.effective_sets import (
    CountingMode,
    ContributionMode,
    VolumeWarningLevel,
    calculate_effective_sets,
    get_session_volume_warning,
    get_weekly_volume_class,
    MUSCLE_CONTRIBUTION_WEIGHTS,
)


def calculate_session_summary(
    routine: Optional[str] = None,
    time_window: Optional[Tuple[str, str]] = None,
    counting_mode: CountingMode = CountingMode.EFFECTIVE,
    contribution_mode: ContributionMode = ContributionMode.TOTAL,
) -> Dict[str, Dict[str, Dict[str, Any]]]:
    """Aggregate weighted sets per muscle, grouped by routine and optional date window.
    
    Applies effective set calculation at the per-exercise level, including:
    - Effort factor (RIR/RPE based)
    - Rep range factor
    - Muscle contribution weighting
    
    Args:
        routine: Optional filter for specific routine.
        time_window: Optional (start_date, end_date) tuple for filtering.
        counting_mode: RAW or EFFECTIVE set counting mode.
        contribution_mode: DIRECT_ONLY or TOTAL muscle contribution mode.
        
    Returns:
        Nested dict: {routine: {muscle: {volume_stats}}} with:
        - weekly_sets: Session sets (effective or raw based on mode)
        - effective_sets: Always the effective set count
        - raw_sets: Always the raw set count
        - sets_per_session: Average per session occurrence
        - status: Volume classification
        - volume_class: CSS class for styling
        - warning_level: Session volume warning (ok/borderline/excessive)
        - total_reps: Rep total for session
        - total_volume: Volume total (sets * reps * weight)
    """
    start_date, end_date = (time_window if time_window else (None, None))

    query = """
        SELECT
            us.id AS selection_id,
            us.routine,
            us.sets,
            us.min_rep_range,
            us.max_rep_range,
            us.weight,
            us.rir,
            us.rpe,
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

    # Track both effective and raw totals per routine per muscle
    effective_totals: Dict[str, Dict[str, Dict[str, float]]] = defaultdict(
        lambda: defaultdict(lambda: {'sets': 0.0, 'reps': 0.0, 'volume': 0.0})
    )
    raw_totals: Dict[str, Dict[str, Dict[str, float]]] = defaultdict(
        lambda: defaultdict(lambda: {'sets': 0.0, 'reps': 0.0, 'volume': 0.0})
    )
    occurrences: Dict[str, Dict[str, set]] = defaultdict(lambda: defaultdict(set))

    for row in rows:
        routine_name = row.get('routine') or 'Unassigned'
        sets = row.get('sets') or 0
        min_rep = row.get('min_rep_range')
        max_rep = row.get('max_rep_range')
        rir = row.get('rir')
        rpe = row.get('rpe')
        load = row.get('weight') or 0
        log_id = row.get('log_id')
        
        avg_reps = 0.0
        if min_rep is not None and max_rep is not None:
            avg_reps = (min_rep + max_rep) / 2.0
        
        # Calculate effective sets using the new module
        eff_result = calculate_effective_sets(
            sets=sets,
            rir=rir,
            rpe=rpe,
            min_rep_range=min_rep,
            max_rep_range=max_rep,
            primary_muscle=row.get('primary_muscle_group'),
            secondary_muscle=row.get('secondary_muscle_group'),
            tertiary_muscle=row.get('tertiary_muscle_group'),
            counting_mode=counting_mode,
            contribution_mode=contribution_mode,
        )
        
        contributions = [
            (row.get('primary_muscle_group'), MUSCLE_CONTRIBUTION_WEIGHTS['primary']),
            (row.get('secondary_muscle_group'), MUSCLE_CONTRIBUTION_WEIGHTS['secondary']),
            (row.get('tertiary_muscle_group'), MUSCLE_CONTRIBUTION_WEIGHTS['tertiary']),
        ]
        
        for muscle, weight_factor in contributions:
            if not muscle:
                continue
            
            # Skip secondary/tertiary in direct-only mode
            if contribution_mode == ContributionMode.DIRECT_ONLY:
                if weight_factor != MUSCLE_CONTRIBUTION_WEIGHTS['primary']:
                    continue
                weight_factor = 1.0
            
            # Get effective contribution for this muscle
            eff_contribution = eff_result.muscle_contributions.get(muscle, 0.0)
            
            # Raw calculations
            raw_weighted_sets = sets * weight_factor
            raw_weighted_reps = raw_weighted_sets * avg_reps
            raw_weighted_volume = raw_weighted_reps * load
            
            # Effective calculations
            eff_weighted_reps = eff_contribution * avg_reps
            eff_weighted_volume = eff_weighted_reps * load
            
            # Update effective totals
            eff_bucket = effective_totals[routine_name][muscle]
            eff_bucket['sets'] += eff_contribution
            eff_bucket['reps'] += eff_weighted_reps
            eff_bucket['volume'] += eff_weighted_volume
            
            # Update raw totals
            raw_bucket = raw_totals[routine_name][muscle]
            raw_bucket['sets'] += raw_weighted_sets
            raw_bucket['reps'] += raw_weighted_reps
            raw_bucket['volume'] += raw_weighted_volume
            
            if log_id:
                occurrences[routine_name][muscle].add(log_id)

    summary: Dict[str, Dict[str, Dict[str, Any]]] = {}
    
    for routine_name in set(effective_totals.keys()) | set(raw_totals.keys()):
        summary[routine_name] = {}
        all_muscles = set(effective_totals[routine_name].keys()) | set(raw_totals[routine_name].keys())
        
        for muscle in sorted(all_muscles):
            eff_aggregates = effective_totals[routine_name][muscle]
            raw_aggregates = raw_totals[routine_name][muscle]
            
            weekly_eff_sets = eff_aggregates['sets']
            weekly_raw_sets = raw_aggregates['sets']
            
            # Use effective or raw based on counting mode
            if counting_mode == CountingMode.RAW:
                weekly_sets = weekly_raw_sets
            else:
                weekly_sets = weekly_eff_sets
            
            session_ids = occurrences[routine_name].get(muscle, set())
            session_count = len(session_ids) or 1
            sets_per_session = weekly_sets / session_count if session_count else weekly_sets
            
            # Volume classification
            volume_class_str = get_weekly_volume_class(weekly_eff_sets)
            legacy_volume_class = get_volume_class(weekly_sets)
            
            # Session volume warning (based on effective sets per session)
            eff_per_session = weekly_eff_sets / session_count if session_count else weekly_eff_sets
            warning_level = get_session_volume_warning(eff_per_session)
            
            summary[routine_name][muscle] = {
                # Primary metrics (mode-dependent)
                'weekly_sets': round(weekly_sets, 2),
                'sets_per_session': round(sets_per_session, 2),
                'status': EFFECTIVE_STATUS_MAP.get(volume_class_str, 'low'),
                'volume_class': legacy_volume_class,
                
                # Always-available metrics
                'raw_sets': round(weekly_raw_sets, 2),
                'effective_sets': round(weekly_eff_sets, 2),
                'effective_per_session': round(eff_per_session, 2),
                
                # Volume warnings
                'warning_level': warning_level.value,
                'is_borderline': warning_level == VolumeWarningLevel.BORDERLINE,
                'is_excessive': warning_level == VolumeWarningLevel.EXCESSIVE,
                
                # Volume totals
                'total_reps': round(eff_aggregates['reps'], 2),
                'total_volume': round(eff_aggregates['volume'], 2),
                'raw_total_reps': round(raw_aggregates['reps'], 2),
                'raw_total_volume': round(raw_aggregates['volume'], 2),
                
                # Mode indicators
                'counting_mode': counting_mode.value,
                'contribution_mode': contribution_mode.value,
            }

    return summary
