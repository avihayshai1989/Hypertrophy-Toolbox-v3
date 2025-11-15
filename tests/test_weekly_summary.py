import pytest

from utils.exercise_manager import save_exercise, add_exercise
from utils.weekly_summary import (
    calculate_exercise_categories,
    calculate_isolated_muscles_stats,
    calculate_weekly_summary,
)


@pytest.mark.usefixtures('clean_db')
def test_weighted_weekly_summary(db_handler):
    save_exercise(
        {
            'exercise_name': 'Bench Press',
            'primary_muscle_group': 'Chest',
            'secondary_muscle_group': 'Triceps',
            'tertiary_muscle_group': 'Front Shoulder',
            'advanced_isolated_muscles': 'Deltoid; Anterior, Delts',
            'utility': 'basic',
            'grips': 'overhand',
            'stabilizers': None,
            'synergists': None,
            'force': 'push',
            'equipment': 'barbell',
            'mechanic': 'compound',
            'difficulty': 'intermediate',
        }
    )

    response = add_exercise(
        routine='Push Day',
        exercise='Bench Press',
        sets=4,
        min_rep_range=6,
        max_rep_range=8,
        rir=2,
        weight=80.0,
        rpe=8.0,
    )
    assert 'successfully' in response.lower()

    summary = calculate_weekly_summary()
    assert 'Chest' in summary
    chest = summary['Chest']
    assert chest['weekly_sets'] == pytest.approx(4.0)
    assert chest['sets_per_session'] == pytest.approx(4.0)
    assert chest['status'] == 'low'
    assert chest['total_reps'] == pytest.approx(28.0)
    assert chest['total_volume'] == pytest.approx(2240.0)

    triceps = summary['Triceps']
    assert triceps['weekly_sets'] == pytest.approx(2.0)
    assert summary['Front-Shoulder']['weekly_sets'] == pytest.approx(1.0)

    categories = calculate_exercise_categories()
    category_map = {(row['category'], row['subcategory']): row['total_exercises'] for row in categories}
    assert category_map[('Mechanic', 'Compound')] == 1
    assert category_map[('Utility', 'Basic')] == 1
    assert category_map[('Force', 'Push')] == 1

    isolated = calculate_isolated_muscles_stats()
    iso_map = {row['isolated_muscle']: row for row in isolated}
    assert iso_map['Front-Shoulder']['exercise_count'] == 1
    assert iso_map['Front-Shoulder']['total_sets'] == pytest.approx(4.0)
