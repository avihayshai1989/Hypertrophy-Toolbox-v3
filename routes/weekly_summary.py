from flask import Blueprint, render_template, request, jsonify
from utils.weekly_summary import (
    calculate_weekly_summary,
    calculate_exercise_categories,
    calculate_isolated_muscles_stats
)
from utils.volume_classifier import (
    get_volume_class,
    get_volume_label,
    get_volume_tooltip,
    get_category_tooltip,
    get_subcategory_tooltip
)

weekly_summary_bp = Blueprint('weekly_summary', __name__)

@weekly_summary_bp.route("/weekly_summary")
def weekly_summary():
    try:
        summary_map = calculate_weekly_summary()
        results = [
            {
                'muscle_group': muscle,
                'weekly_sets': data['weekly_sets'],
                'sets_per_session': data['sets_per_session'],
                'status': data['status'],
                'volume_class': data['volume_class'],
                'total_sets': data['weekly_sets'],
                'total_reps': data['total_reps'],
                'total_volume': data['total_volume'],
                'total_weight': data['total_volume'],
            }
            for muscle, data in summary_map.items()
        ]
        category_results = calculate_exercise_categories()
        isolated_muscles_stats = calculate_isolated_muscles_stats()
        
        if request.headers.get("Accept") == "application/json":
            return jsonify({
                "weekly_summary": results,
                "categories": category_results,
                "isolated_muscles": isolated_muscles_stats
            })
        
        return render_template(
            "weekly_summary.html",
            weekly_summary=results,
            categories=category_results,
            isolated_muscles=isolated_muscles_stats,
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