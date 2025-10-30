from flask import Blueprint, render_template, request, jsonify
from utils.session_summary import calculate_session_summary
from utils.weekly_summary import (
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

session_summary_bp = Blueprint('session_summary', __name__)

@session_summary_bp.route("/session_summary", methods=["GET"])
def session_summary():
    method = request.args.get("method", "Total")
    try:
        results = calculate_session_summary(method)
        category_results = calculate_exercise_categories()
        isolated_muscles_stats = calculate_isolated_muscles_stats()
        
        if request.headers.get("Accept") == "application/json":
            return jsonify({
                "session_summary": results,
                "categories": category_results,
                "isolated_muscles": isolated_muscles_stats
            })
        
        return render_template(
            "session_summary.html",
            session_summary=results,
            categories=category_results,
            isolated_muscles=isolated_muscles_stats,
            get_volume_class=get_volume_class,
            get_volume_label=get_volume_label,
            get_volume_tooltip=get_volume_tooltip,
            get_category_tooltip=get_category_tooltip,
            get_subcategory_tooltip=get_subcategory_tooltip
        )
    except Exception as e:
        print(f"Error in session_summary: {e}")
        if request.headers.get("Accept") == "application/json":
            return jsonify({"error": "Unable to fetch session summary"}), 500
        return render_template("error.html", message="Unable to load session summary."), 500 