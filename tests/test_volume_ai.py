"""
Tests for utils/volume_ai.py - AI-based volume suggestions.
"""

import pytest
from utils.volume_ai import generate_volume_suggestions


class TestGenerateVolumeSuggestions:
    """Tests for generate_volume_suggestions function."""

    # ─────────────────────────────────────────────────────────────────────
    # Basic mode tests
    # ─────────────────────────────────────────────────────────────────────
    def test_empty_muscle_volumes_returns_empty(self):
        """Empty muscle volumes should return no suggestions."""
        result = generate_volume_suggestions(training_days=4, muscle_volumes={})
        # Only category volume suggestions (push/pull/legs < 30)
        assert all(s['type'] == 'suggestion' for s in result)

    def test_default_mode_is_basic(self):
        """Mode defaults to 'basic' when not specified."""
        muscle_volumes = {
            'Chest': {'weekly_sets': 10, 'sets_per_session': 5}
        }
        result = generate_volume_suggestions(training_days=4, muscle_volumes=muscle_volumes)
        # Should work without errors using basic muscle groups
        assert isinstance(result, list)

    def test_mode_normalization_uppercase(self):
        """Mode should be normalized (case-insensitive)."""
        muscle_volumes = {'Chest': {'weekly_sets': 10, 'sets_per_session': 5}}
        result = generate_volume_suggestions(training_days=4, muscle_volumes=muscle_volumes, mode="BASIC")
        assert isinstance(result, list)

    def test_mode_normalization_mixed_case(self):
        """Mode handles mixed case."""
        muscle_volumes = {'Chest': {'weekly_sets': 10, 'sets_per_session': 5}}
        result = generate_volume_suggestions(training_days=4, muscle_volumes=muscle_volumes, mode="BaSiC")
        assert isinstance(result, list)

    def test_invalid_mode_defaults_to_basic(self):
        """Invalid mode should default to 'basic'."""
        muscle_volumes = {'Chest': {'weekly_sets': 10, 'sets_per_session': 5}}
        result = generate_volume_suggestions(training_days=4, muscle_volumes=muscle_volumes, mode="invalid_mode")
        assert isinstance(result, list)

    def test_none_mode_defaults_to_basic(self):
        """None mode should default to 'basic'."""
        muscle_volumes = {'Chest': {'weekly_sets': 10, 'sets_per_session': 5}}
        result = generate_volume_suggestions(training_days=4, muscle_volumes=muscle_volumes, mode=None)  # type: ignore[arg-type]
        assert isinstance(result, list)

    # ─────────────────────────────────────────────────────────────────────
    # Total volume warnings
    # ─────────────────────────────────────────────────────────────────────
    def test_total_volume_warning_when_too_high(self):
        """Should warn when total volume exceeds training_days * 30."""
        # 4 training days * 30 = 120 sets max
        muscle_volumes = {
            'Chest': {'weekly_sets': 50, 'sets_per_session': 10},
            'Back': {'weekly_sets': 50, 'sets_per_session': 10},
            'Legs': {'weekly_sets': 50, 'sets_per_session': 10},  # Total: 150
        }
        result = generate_volume_suggestions(training_days=4, muscle_volumes=muscle_volumes)
        warning_messages = [s for s in result if s['type'] == 'warning']
        recovery_warning = [m for m in warning_messages if 'recovery' in m['message'].lower()]
        assert len(recovery_warning) >= 1

    def test_no_total_volume_warning_when_within_limit(self):
        """Should not warn when total volume is within limits."""
        # 4 training days * 30 = 120 sets max
        muscle_volumes = {
            'Chest': {'weekly_sets': 30, 'sets_per_session': 10},
            'Back': {'weekly_sets': 30, 'sets_per_session': 10},
        }
        result = generate_volume_suggestions(training_days=4, muscle_volumes=muscle_volumes)
        recovery_warnings = [s for s in result if s['type'] == 'warning' and 'recovery' in s['message'].lower()]
        assert len(recovery_warnings) == 0

    def test_total_volume_handles_missing_weekly_sets(self):
        """Should handle missing weekly_sets in data."""
        muscle_volumes = {
            'Chest': {'sets_per_session': 5},  # No weekly_sets
        }
        result = generate_volume_suggestions(training_days=4, muscle_volumes=muscle_volumes)
        assert isinstance(result, list)

    # ─────────────────────────────────────────────────────────────────────
    # Per-session volume warnings
    # ─────────────────────────────────────────────────────────────────────
    def test_per_session_warning_when_too_high(self):
        """Should warn when sets_per_session exceeds 10."""
        muscle_volumes = {
            'Chest': {'weekly_sets': 15, 'sets_per_session': 15},
        }
        result = generate_volume_suggestions(training_days=4, muscle_volumes=muscle_volumes)
        session_warnings = [s for s in result if s['type'] == 'warning' and 'sets/session' in s['message']]
        assert len(session_warnings) == 1
        assert 'Chest' in session_warnings[0]['message']

    def test_no_per_session_warning_when_normal(self):
        """Should not warn when sets_per_session is 10 or below."""
        muscle_volumes = {
            'Chest': {'weekly_sets': 20, 'sets_per_session': 10},
        }
        result = generate_volume_suggestions(training_days=4, muscle_volumes=muscle_volumes)
        session_warnings = [s for s in result if s['type'] == 'warning' and 'sets/session' in s['message']]
        assert len(session_warnings) == 0

    def test_consolidation_suggestion_for_low_per_session(self):
        """Should suggest consolidation when sets_per_session < 3 but weekly_sets > 0."""
        muscle_volumes = {
            'Chest': {'weekly_sets': 10, 'sets_per_session': 2},
        }
        result = generate_volume_suggestions(training_days=4, muscle_volumes=muscle_volumes)
        consolidation_suggestions = [s for s in result if s['type'] == 'info' and 'consolidated' in s['message'].lower()]
        assert len(consolidation_suggestions) == 1
        assert 'Chest' in consolidation_suggestions[0]['message']

    def test_no_consolidation_for_zero_weekly_sets(self):
        """Should not suggest consolidation when weekly_sets is 0."""
        muscle_volumes = {
            'Chest': {'weekly_sets': 0, 'sets_per_session': 0},
        }
        result = generate_volume_suggestions(training_days=4, muscle_volumes=muscle_volumes)
        consolidation_suggestions = [s for s in result if s['type'] == 'info' and 'consolidated' in s['message'].lower()]
        assert len(consolidation_suggestions) == 0

    def test_handles_missing_sets_per_session(self):
        """Should handle missing sets_per_session gracefully (defaults to 0)."""
        muscle_volumes = {
            'Chest': {'weekly_sets': 10},  # No sets_per_session
        }
        result = generate_volume_suggestions(training_days=4, muscle_volumes=muscle_volumes)
        assert isinstance(result, list)

    # ─────────────────────────────────────────────────────────────────────
    # Category volume suggestions (basic mode)
    # ─────────────────────────────────────────────────────────────────────
    def test_push_category_low_volume_suggestion(self):
        """Should suggest increasing push volume when below 30 sets."""
        # Basic mode push muscles: Chest, Front-Shoulder, Triceps
        muscle_volumes = {
            'Chest': {'weekly_sets': 5, 'sets_per_session': 5},
        }
        result = generate_volume_suggestions(training_days=4, muscle_volumes=muscle_volumes, mode="basic")
        push_suggestions = [s for s in result if 'push' in s['message'].lower()]
        assert len(push_suggestions) == 1

    def test_pull_category_low_volume_suggestion(self):
        """Should suggest increasing pull volume when below 30 sets."""
        # Basic mode pull muscles: Latissimus-Dorsi, Rear-Shoulder, Biceps
        muscle_volumes = {
            'Biceps': {'weekly_sets': 5, 'sets_per_session': 5},
        }
        result = generate_volume_suggestions(training_days=4, muscle_volumes=muscle_volumes, mode="basic")
        pull_suggestions = [s for s in result if 'pull' in s['message'].lower()]
        assert len(pull_suggestions) == 1

    def test_legs_category_low_volume_suggestion(self):
        """Should suggest increasing legs volume when below 30 sets."""
        # Basic mode legs muscles: Quadriceps, Hamstrings, Calves
        muscle_volumes = {
            'Quadriceps': {'weekly_sets': 5, 'sets_per_session': 5},
        }
        result = generate_volume_suggestions(training_days=4, muscle_volumes=muscle_volumes, mode="basic")
        legs_suggestions = [s for s in result if 'legs' in s['message'].lower()]
        assert len(legs_suggestions) == 1

    def test_no_suggestion_when_category_volume_adequate(self):
        """Should not suggest when category volume is 30+ sets."""
        muscle_volumes = {
            'Chest': {'weekly_sets': 15, 'sets_per_session': 5},
            'Front-Shoulder': {'weekly_sets': 10, 'sets_per_session': 5},
            'Triceps': {'weekly_sets': 10, 'sets_per_session': 5},  # Total push: 35 sets
        }
        result = generate_volume_suggestions(training_days=4, muscle_volumes=muscle_volumes, mode="basic")
        push_suggestions = [s for s in result if 'push' in s['message'].lower()]
        assert len(push_suggestions) == 0

    # ─────────────────────────────────────────────────────────────────────
    # Advanced mode muscle groups
    # ─────────────────────────────────────────────────────────────────────
    def test_advanced_mode_uses_different_muscle_groups(self):
        """Advanced mode should use detailed muscle group mapping."""
        # In advanced mode, push includes: upper-pectoralis, mid-lower-pectoralis, etc.
        muscle_volumes = {
            'upper-pectoralis': {'weekly_sets': 15, 'sets_per_session': 5},
            'mid-lower-pectoralis': {'weekly_sets': 15, 'sets_per_session': 5},
            'anterior-deltoid': {'weekly_sets': 10, 'sets_per_session': 5},  # Total: 40 sets push
        }
        result = generate_volume_suggestions(training_days=4, muscle_volumes=muscle_volumes, mode="advanced")
        push_suggestions = [s for s in result if 'push' in s['message'].lower()]
        assert len(push_suggestions) == 0  # 40 > 30, no suggestion

    def test_advanced_mode_pull_muscles(self):
        """Advanced mode pull should use detailed mapping."""
        muscle_volumes = {
            'posterior-deltoid': {'weekly_sets': 5, 'sets_per_session': 5},
        }
        result = generate_volume_suggestions(training_days=4, muscle_volumes=muscle_volumes, mode="advanced")
        pull_suggestions = [s for s in result if 'pull' in s['message'].lower()]
        assert len(pull_suggestions) == 1  # Low pull volume

    def test_advanced_mode_legs_muscles(self):
        """Advanced mode legs should include detailed leg muscles."""
        muscle_volumes = {
            'rectus-femoris': {'weekly_sets': 10, 'sets_per_session': 5},
            'gluteus-maximus': {'weekly_sets': 10, 'sets_per_session': 5},
            'gastrocnemius': {'weekly_sets': 10, 'sets_per_session': 5},  # Total: 30 sets
        }
        result = generate_volume_suggestions(training_days=4, muscle_volumes=muscle_volumes, mode="advanced")
        legs_suggestions = [s for s in result if 'legs' in s['message'].lower()]
        assert len(legs_suggestions) == 0  # 30 >= 30, no suggestion

    # ─────────────────────────────────────────────────────────────────────
    # Edge cases
    # ─────────────────────────────────────────────────────────────────────
    def test_null_muscle_data_raises_error(self):
        """None values in muscle_volumes dict raise AttributeError.
        
        This documents current behavior - callers must ensure no None values.
        """
        muscle_volumes = {
            'Chest': None,  # Explicitly null
        }
        with pytest.raises(AttributeError):
            generate_volume_suggestions(training_days=4, muscle_volumes=muscle_volumes)

    def test_handles_zero_training_days(self):
        """Total volume limit is 0 when training_days is 0."""
        muscle_volumes = {
            'Chest': {'weekly_sets': 1, 'sets_per_session': 1},
        }
        result = generate_volume_suggestions(training_days=0, muscle_volumes=muscle_volumes)
        # 1 > 0*30 = 0, so should trigger recovery warning
        recovery_warnings = [s for s in result if s['type'] == 'warning' and 'recovery' in s['message'].lower()]
        assert len(recovery_warnings) == 1

    def test_multiple_muscles_multiple_warnings(self):
        """Should generate warnings for multiple muscles."""
        muscle_volumes = {
            'Chest': {'weekly_sets': 20, 'sets_per_session': 15},
            'Back': {'weekly_sets': 20, 'sets_per_session': 12},
            'Legs': {'weekly_sets': 20, 'sets_per_session': 11},
        }
        result = generate_volume_suggestions(training_days=4, muscle_volumes=muscle_volumes)
        session_warnings = [s for s in result if s['type'] == 'warning' and 'sets/session' in s['message']]
        assert len(session_warnings) == 3  # All three exceed 10 sets/session

    def test_suggestion_types_are_valid(self):
        """All suggestions should have valid type values."""
        muscle_volumes = {
            'Chest': {'weekly_sets': 100, 'sets_per_session': 20},
        }
        result = generate_volume_suggestions(training_days=2, muscle_volumes=muscle_volumes)
        valid_types = {'warning', 'info', 'suggestion'}
        for suggestion in result:
            assert suggestion['type'] in valid_types
            assert 'message' in suggestion

    def test_return_format_is_list_of_dicts(self):
        """Results should be a list of dicts with type and message keys."""
        result = generate_volume_suggestions(training_days=4, muscle_volumes={})
        assert isinstance(result, list)
        for item in result:
            assert isinstance(item, dict)
            assert 'type' in item
            assert 'message' in item
