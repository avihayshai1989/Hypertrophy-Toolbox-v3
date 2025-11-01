"""
DEPRECATED: This module is superseded by utils/filter_predicates.py
Kept for backward compatibility only.
"""

from utils.filter_predicates import FilterPredicates


class ExerciseFilter:
    """
    DEPRECATED: Use FilterPredicates instead.
    Handles filtering of exercises based on provided criteria.
    """

    def __init__(self):
        pass

    def filter_exercises(self, filters):
        """
        Filter exercises based on the provided filters.
        Delegates to FilterPredicates.

        :param filters: Dictionary containing filter criteria.
        :return: List of exercise names matching the criteria.
        """
        return FilterPredicates.filter_exercises(filters)

