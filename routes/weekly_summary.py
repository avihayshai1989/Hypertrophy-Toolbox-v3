from flask import Blueprint, render_template, request, jsonify
from utils.weekly_summary import (
    calculate_exercise_categories,
    calculate_isolated_muscles_stats,
    calculate_weekly_summary,
)
from utils.business_logic import BusinessLogic
from utils.volume_classifier import (
    get_volume_class,
    get_volume_label,
    get_volume_tooltip,
    get_category_tooltip,
    get_subcategory_tooltip
)
from utils.effective_sets import CountingMode, ContributionMode

weekly_summary_bp = Blueprint('weekly_summary', __name__)


def _parse_counting_mode(value: str) -> CountingMode:
    """Parse counting mode from request parameter."""
    if value and value.lower() == 'raw':
        return CountingMode.RAW
    return CountingMode.EFFECTIVE  # Default to effective


def _parse_contribution_mode(value: str) -> ContributionMode:
    """Parse contribution mode from request parameter."""
    if value and value.lower() == 'direct':
        return ContributionMode.DIRECT_ONLY
    return ContributionMode.TOTAL  # Default to total


@weekly_summary_bp.route("/weekly_summary")
def weekly_summary():
    try:
        method = request.args.get("method", "Total")
        counting_mode_str = request.args.get("counting_mode", "effective")
        contribution_mode_str = request.args.get("contribution_mode", "total")
        
        counting_mode = _parse_counting_mode(counting_mode_str)
        contribution_mode = _parse_contribution_mode(contribution_mode_str)
        
        # Use new effective sets-based calculation
        summary_data = calculate_weekly_summary(
            method=method,
            counting_mode=counting_mode,
            contribution_mode=contribution_mode,
        )
        
        # Format for backward-compatible API response
        results = [
            {
                'muscle_group': muscle,
                'total_sets': data['weekly_sets'],
                'effective_sets': data.get('effective_weekly_sets', data['weekly_sets']),
                'raw_sets': data.get('raw_weekly_sets', data['weekly_sets']),
                'total_reps': data['total_reps'],
                'total_volume': data['total_volume'],
                'total_weight': data['total_volume'],  # Legacy alias
                'frequency': data.get('frequency', 0),
                'sets_per_session': data['sets_per_session'],
                'avg_sets_per_session': data.get('avg_sets_per_session', data['sets_per_session']),
                'max_sets_per_session': data.get('max_sets_per_session', data['sets_per_session']),
                'status': data['status'],
                'volume_class': data['volume_class'],
                'counting_mode': counting_mode.value,
                'contribution_mode': contribution_mode.value,
            }
            for muscle, data in summary_data.items()
        ]
        
        category_results = calculate_exercise_categories()
        isolated_muscles_stats = calculate_isolated_muscles_stats()
        
        if request.headers.get("Accept") == "application/json":
            return jsonify({
                "weekly_summary": results,
                "categories": category_results,
                "isolated_muscles": isolated_muscles_stats,
                "modes": {
                    "counting_mode": counting_mode.value,
                    "contribution_mode": contribution_mode.value,
                }
            })
        
        return render_template(
            "weekly_summary.html",
            weekly_summary=results,
            categories=category_results,
            isolated_muscles=isolated_muscles_stats,
            counting_mode=counting_mode.value,
            contribution_mode=contribution_mode.value,
            get_volume_class=get_volume_class,
            get_volume_label=get_volume_label,
            get_volume_tooltip=get_volume_tooltip,
            get_category_tooltip=get_category_tooltip,
            get_subcategory_tooltip=get_subcategory_tooltip
        )
    except Exception as e:
        print(f"Error in weekly_summary: {e}")
        if request.headers.get("Accept") == "application/json":
            return jsonify({"error": "Unable to fetch weekly summary"}), 500
        return render_template("error.html", message="Unable to load weekly summary."), 500 