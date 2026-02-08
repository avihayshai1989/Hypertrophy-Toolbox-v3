"""
Tests for utils/filter_cache.py - In-memory caching for filter options.
"""

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
import threading
import time

from utils.filter_cache import (
    FilterCache,
    get_cached_unique_values,
    invalidate_cache,
    get_cache_stats,
    clear_cache,
    warm_cache,
)


class TestFilterCacheInit:
    """Tests for FilterCache initialization."""

    def test_default_ttl(self):
        """Default TTL should be 3600 seconds."""
        cache = FilterCache()
        assert cache._ttl_seconds == 3600

    def test_custom_ttl(self):
        """Custom TTL should be set."""
        cache = FilterCache(ttl_seconds=600)
        assert cache._ttl_seconds == 600

    def test_cache_starts_empty(self):
        """Cache should start empty."""
        cache = FilterCache()
        assert len(cache._cache) == 0

    def test_cache_enabled_by_default(self):
        """Cache should be enabled by default."""
        cache = FilterCache()
        assert cache._enabled is True


class TestFilterCacheGet:
    """Tests for FilterCache.get method."""

    def test_get_cache_miss(self):
        """Cache miss should return None."""
        cache = FilterCache()
        result = cache.get("exercises", "equipment")
        assert result is None

    def test_get_cache_hit(self):
        """Cache hit should return cached values."""
        cache = FilterCache()
        cache.set("exercises", "equipment", ["Barbell", "Dumbbell"])
        
        result = cache.get("exercises", "equipment")
        
        assert result == ["Barbell", "Dumbbell"]

    def test_get_from_disabled_cache_returns_none(self):
        """Disabled cache should always return None."""
        cache = FilterCache()
        cache.set("exercises", "equipment", ["Barbell"])
        cache._enabled = False
        
        result = cache.get("exercises", "equipment")
        
        assert result is None

    def test_get_expired_entry_returns_none(self):
        """Expired entry should return None and be deleted."""
        cache = FilterCache(ttl_seconds=0)  # Immediate expiry
        cache.set("exercises", "equipment", ["Barbell"])
        time.sleep(0.01)  # Ensure expiry
        
        result = cache.get("exercises", "equipment")
        
        assert result is None
        assert "exercises.equipment" not in cache._cache

    def test_get_uses_table_column_key(self):
        """Cache key should be table.column format."""
        cache = FilterCache()
        cache.set("exercises", "equipment", ["Barbell"])
        cache.set("exercises", "mechanic", ["Compound"])
        
        assert cache.get("exercises", "equipment") == ["Barbell"]
        assert cache.get("exercises", "mechanic") == ["Compound"]


class TestFilterCacheSet:
    """Tests for FilterCache.set method."""

    def test_set_stores_values(self):
        """Set should store values in cache."""
        cache = FilterCache()
        cache.set("exercises", "equipment", ["Barbell", "Dumbbell"])
        
        assert "exercises.equipment" in cache._cache
        assert cache._cache["exercises.equipment"]["values"] == ["Barbell", "Dumbbell"]

    def test_set_stores_timestamp(self):
        """Set should store timestamp with entry."""
        cache = FilterCache()
        before = datetime.now()
        cache.set("exercises", "equipment", ["Barbell"])
        after = datetime.now()
        
        timestamp = cache._cache["exercises.equipment"]["timestamp"]
        assert before <= timestamp <= after

    def test_set_when_disabled_does_nothing(self):
        """Set should do nothing when cache disabled."""
        cache = FilterCache()
        cache._enabled = False
        cache.set("exercises", "equipment", ["Barbell"])
        
        assert len(cache._cache) == 0

    def test_set_overwrites_existing(self):
        """Set should overwrite existing entry."""
        cache = FilterCache()
        cache.set("exercises", "equipment", ["Barbell"])
        cache.set("exercises", "equipment", ["Dumbbell"])
        
        assert cache.get("exercises", "equipment") == ["Dumbbell"]


class TestFilterCacheInvalidate:
    """Tests for FilterCache.invalidate method."""

    def test_invalidate_entire_cache(self):
        """Invalidate with no args should clear entire cache."""
        cache = FilterCache()
        cache.set("exercises", "equipment", ["Barbell"])
        cache.set("exercises", "mechanic", ["Compound"])
        cache.set("workout_plan", "routine", ["Push", "Pull"])
        
        cache.invalidate()
        
        assert len(cache._cache) == 0

    def test_invalidate_specific_table(self):
        """Invalidate with table should clear only that table."""
        cache = FilterCache()
        cache.set("exercises", "equipment", ["Barbell"])
        cache.set("exercises", "mechanic", ["Compound"])
        cache.set("workout_plan", "routine", ["Push", "Pull"])
        
        cache.invalidate(table="exercises")
        
        assert "exercises.equipment" not in cache._cache
        assert "exercises.mechanic" not in cache._cache
        assert "workout_plan.routine" in cache._cache

    def test_invalidate_specific_column(self):
        """Invalidate with table and column should clear only that entry."""
        cache = FilterCache()
        cache.set("exercises", "equipment", ["Barbell"])
        cache.set("exercises", "mechanic", ["Compound"])
        
        cache.invalidate(table="exercises", column="equipment")
        
        assert "exercises.equipment" not in cache._cache
        assert "exercises.mechanic" in cache._cache

    def test_invalidate_nonexistent_entry(self):
        """Invalidate nonexistent entry should not raise."""
        cache = FilterCache()
        cache.invalidate(table="nonexistent", column="column")
        # Should not raise


class TestFilterCacheGetStats:
    """Tests for FilterCache.get_stats method."""

    def test_get_stats_empty_cache(self):
        """Stats for empty cache."""
        cache = FilterCache(ttl_seconds=3600)
        
        stats = cache.get_stats()
        
        assert stats['enabled'] is True
        assert stats['total_entries'] == 0
        assert stats['expired_entries'] == 0
        assert stats['active_entries'] == 0
        assert stats['ttl_seconds'] == 3600
        assert stats['keys'] == []

    def test_get_stats_with_entries(self):
        """Stats with cached entries."""
        cache = FilterCache()
        cache.set("exercises", "equipment", ["Barbell"])
        cache.set("exercises", "mechanic", ["Compound"])
        
        stats = cache.get_stats()
        
        assert stats['total_entries'] == 2
        assert stats['active_entries'] == 2
        assert "exercises.equipment" in stats['keys']
        assert "exercises.mechanic" in stats['keys']

    def test_get_stats_counts_expired(self):
        """Stats should count expired entries."""
        cache = FilterCache(ttl_seconds=0)  # Immediate expiry
        cache.set("exercises", "equipment", ["Barbell"])
        time.sleep(0.01)  # Ensure expiry
        
        stats = cache.get_stats()
        
        assert stats['total_entries'] == 1
        assert stats['expired_entries'] == 1
        assert stats['active_entries'] == 0


class TestFilterCacheIsExpired:
    """Tests for FilterCache._is_expired method."""

    def test_missing_timestamp_is_expired(self):
        """Entry without timestamp should be considered expired."""
        cache = FilterCache()
        entry = {'values': ['test']}  # No timestamp
        
        assert cache._is_expired(entry) is True

    def test_fresh_entry_not_expired(self):
        """Fresh entry should not be expired."""
        cache = FilterCache(ttl_seconds=3600)
        entry = {'values': ['test'], 'timestamp': datetime.now()}
        
        assert cache._is_expired(entry) is False

    def test_old_entry_is_expired(self):
        """Entry older than TTL should be expired."""
        cache = FilterCache(ttl_seconds=60)
        old_time = datetime.now() - timedelta(seconds=120)
        entry = {'values': ['test'], 'timestamp': old_time}
        
        assert cache._is_expired(entry) is True


class TestFilterCacheThreadSafety:
    """Tests for thread safety of FilterCache."""

    def test_concurrent_reads_and_writes(self):
        """Cache should handle concurrent reads and writes safely."""
        cache = FilterCache()
        errors = []
        
        def writer():
            try:
                for i in range(100):
                    cache.set("table", f"column_{i % 10}", [f"value_{i}"])
            except Exception as e:
                errors.append(e)
        
        def reader():
            try:
                for i in range(100):
                    cache.get("table", f"column_{i % 10}")
            except Exception as e:
                errors.append(e)
        
        threads = [
            threading.Thread(target=writer) for _ in range(3)
        ] + [
            threading.Thread(target=reader) for _ in range(3)
        ]
        
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        assert len(errors) == 0

    def test_concurrent_invalidation(self):
        """Cache should handle concurrent invalidation safely."""
        cache = FilterCache()
        errors = []
        
        def populate_and_invalidate():
            try:
                for i in range(50):
                    cache.set("table", f"col_{i}", [f"val_{i}"])
                    if i % 10 == 0:
                        cache.invalidate()
            except Exception as e:
                errors.append(e)
        
        threads = [threading.Thread(target=populate_and_invalidate) for _ in range(5)]
        
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        assert len(errors) == 0


class TestModuleFunctions:
    """Tests for module-level convenience functions."""

    @patch('utils.filter_cache._filter_cache')
    def test_invalidate_cache_delegates(self, mock_cache):
        """invalidate_cache should delegate to module cache."""
        invalidate_cache("exercises", "equipment")
        mock_cache.invalidate.assert_called_once_with("exercises", "equipment")

    @patch('utils.filter_cache._filter_cache')
    def test_get_cache_stats_delegates(self, mock_cache):
        """get_cache_stats should delegate to module cache."""
        mock_cache.get_stats.return_value = {'total': 5}
        
        result = get_cache_stats()
        
        mock_cache.get_stats.assert_called_once()
        assert result == {'total': 5}

    @patch('utils.filter_cache._filter_cache')
    def test_clear_cache_delegates(self, mock_cache):
        """clear_cache should delegate to module cache invalidate."""
        clear_cache()
        mock_cache.invalidate.assert_called_once()


class TestGetCachedUniqueValues:
    """Tests for get_cached_unique_values function."""

    @patch('utils.filter_cache._filter_cache')
    def test_returns_cached_value_on_hit(self, mock_cache):
        """Should return cached value on cache hit."""
        mock_cache.get.return_value = ["Barbell", "Dumbbell"]
        
        result = get_cached_unique_values("exercises", "equipment")
        
        assert result == ["Barbell", "Dumbbell"]
        mock_cache.get.assert_called_once_with("exercises", "equipment")

    @patch('utils.filter_cache.DatabaseHandler')
    @patch('utils.filter_cache._filter_cache')
    def test_queries_database_on_miss(self, mock_cache, mock_db_class):
        """Should query database on cache miss."""
        mock_cache.get.return_value = None
        
        mock_db = MagicMock()
        mock_db.__enter__ = MagicMock(return_value=mock_db)
        mock_db.__exit__ = MagicMock(return_value=False)
        mock_db.fetch_all.return_value = [
            {"equipment": "Barbell"},
            {"equipment": "Dumbbell"}
        ]
        mock_db_class.return_value = mock_db
        
        result = get_cached_unique_values("exercises", "equipment")
        
        assert result == ["Barbell", "Dumbbell"]
        mock_cache.set.assert_called_once_with("exercises", "equipment", ["Barbell", "Dumbbell"])

    @patch('utils.filter_cache.DatabaseHandler')
    @patch('utils.filter_cache._filter_cache')
    def test_filters_null_values(self, mock_cache, mock_db_class):
        """Should filter out null/empty values from results."""
        mock_cache.get.return_value = None
        
        mock_db = MagicMock()
        mock_db.__enter__ = MagicMock(return_value=mock_db)
        mock_db.__exit__ = MagicMock(return_value=False)
        mock_db.fetch_all.return_value = [
            {"equipment": "Barbell"},
            {"equipment": None},
            {"equipment": ""},
        ]
        mock_db_class.return_value = mock_db
        
        result = get_cached_unique_values("exercises", "equipment")
        
        assert result == ["Barbell"]


class TestWarmCache:
    """Tests for warm_cache function."""

    @patch('utils.filter_cache.get_cached_unique_values')
    def test_warm_cache_loads_common_filters(self, mock_get_cached):
        """warm_cache should load common filter columns."""
        warm_cache()
        
        # Should have called for common filters
        expected_calls = [
            ("exercises", "primary_muscle_group"),
            ("exercises", "equipment"),
            ("exercises", "mechanic"),
            ("exercises", "force"),
            ("exercises", "difficulty"),
            ("exercises", "utility"),
        ]
        
        for table, column in expected_calls:
            mock_get_cached.assert_any_call(table, column)

    @patch('utils.filter_cache.get_cached_unique_values')
    def test_warm_cache_continues_on_error(self, mock_get_cached):
        """warm_cache should continue even if one column fails."""
        mock_get_cached.side_effect = [
            Exception("DB error"),
            ["Barbell"],
            ["Compound"],
            ["Push"],
            ["Beginner"],
            ["Basic"],
        ]
        
        # Should not raise
        warm_cache()
        
        # Should have attempted all columns
        assert mock_get_cached.call_count == 6
