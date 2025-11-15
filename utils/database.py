"""Database connection helpers and lightweight data-access abstraction."""
from __future__ import annotations

import sqlite3
from collections.abc import Iterable, Mapping, Sequence
from datetime import date as _date, datetime as _datetime
from typing import Any, Optional, Union

from utils.config import DB_FILE
from utils.logger import get_logger

logger = get_logger()


_SQLITE_CONVERTERS_REGISTERED = False


def _register_sqlite_converters() -> None:
    """Register custom adapters/converters to silence deprecated defaults."""
    global _SQLITE_CONVERTERS_REGISTERED
    if _SQLITE_CONVERTERS_REGISTERED:
        return

    def _adapt_datetime(value: _datetime) -> str:
        return value.isoformat(sep=" ")

    def _adapt_date(value: _date) -> str:
        return value.isoformat()

    def _parse_timestamp(raw: bytes) -> Union[_datetime, str]:
        text = raw.decode("utf-8") if raw is not None else ""
        if not text:
            return text
        for fmt in (
            "%Y-%m-%d %H:%M:%S.%f",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%dT%H:%M:%S.%f",
            "%Y-%m-%dT%H:%M:%S",
        ):
            try:
                return _datetime.strptime(text, fmt)
            except ValueError:
                continue
        return text

    def _parse_date(raw: bytes) -> Union[_date, str]:
        text = raw.decode("utf-8") if raw is not None else ""
        if not text:
            return text
        try:
            return _date.fromisoformat(text)
        except ValueError:
            return text

    sqlite3.register_adapter(_datetime, _adapt_datetime)
    sqlite3.register_adapter(_date, _adapt_date)
    sqlite3.register_converter("timestamp", _parse_timestamp)
    sqlite3.register_converter("datetime", _parse_timestamp)
    sqlite3.register_converter("date", _parse_date)
    _SQLITE_CONVERTERS_REGISTERED = True


_register_sqlite_converters()


def _configure_connection(connection: sqlite3.Connection) -> sqlite3.Connection:
    """Apply the required PRAGMAs for every new connection."""
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON;")
    connection.execute("PRAGMA busy_timeout = 5000;")
    connection.execute("PRAGMA journal_mode = WAL;")
    connection.execute("PRAGMA synchronous = NORMAL;")
    return connection


def get_db_connection(database_path: Optional[str] = None) -> sqlite3.Connection:
    """Create a new SQLite connection with the canonical configuration."""
    db_path = database_path or DB_FILE
    connection = sqlite3.connect(
        db_path,
        detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES,
        check_same_thread=False,
    )
    return _configure_connection(connection)


class DatabaseHandler:
    """Context-friendly helper around SQLite connections."""

    def __init__(self, database_path: Optional[str] = None) -> None:
        self.database_path = database_path or DB_FILE
        self.connection: sqlite3.Connection = get_db_connection(self.database_path)
        self.cursor: sqlite3.Cursor = self.connection.cursor()

    # -- Core query helpers -------------------------------------------------
    def execute_query(
        self,
        query: str,
        params: Optional[Union[Sequence[Any], Mapping[str, Any], Any]] = None,
        *,
        commit: bool = True,
    ) -> int:
        """Execute a single statement and optionally commit."""
        prepared = self._prepare_params(params)
        try:
            if prepared is None:
                self.cursor.execute(query)
            else:
                self.cursor.execute(query, prepared)
            if commit:
                self.connection.commit()
            logger.debug("SQL exec: %s | params=%s", query[:120], prepared)
            return self.cursor.rowcount
        except sqlite3.Error as exc:  # pragma: no cover - logged for observability
            if commit:
                self.connection.rollback()
            logger.error("SQL error: %s | params=%s", query[:120], prepared, exc_info=True)
            raise

    def executemany(
        self,
        query: str,
        param_sets: Iterable[Union[Sequence[Any], Mapping[str, Any], Any]],
        *,
        commit: bool = True,
    ) -> int:
        """Execute the same statement for multiple parameter sets."""
        prepared_sets = (self._prepare_params(params, for_many=True) for params in param_sets)
        try:
            self.cursor.executemany(query, prepared_sets)
            if commit:
                self.connection.commit()
            logger.debug("SQL executemany: %s", query[:120])
            return self.cursor.rowcount
        except sqlite3.Error as exc:  # pragma: no cover - logged for observability
            if commit:
                self.connection.rollback()
            logger.error("SQL executemany error: %s", query[:120], exc_info=True)
            raise

    def fetch_one(
        self,
        query: str,
        params: Optional[Union[Sequence[Any], Mapping[str, Any], Any]] = None,
    ) -> Optional[dict[str, Any]]:
        prepared = self._prepare_params(params)
        if prepared is None:
            self.cursor.execute(query)
        else:
            self.cursor.execute(query, prepared)
        row = self.cursor.fetchone()
        return dict(row) if row is not None else None

    def fetch_all(
        self,
        query: str,
        params: Optional[Union[Sequence[Any], Mapping[str, Any], Any]] = None,
    ) -> list[dict[str, Any]]:
        prepared = self._prepare_params(params)
        if prepared is None:
            self.cursor.execute(query)
        else:
            self.cursor.execute(query, prepared)
        rows = self.cursor.fetchall()
        return [dict(row) for row in rows]

    # -- Lifetime management -------------------------------------------------
    def close(self) -> None:
        if getattr(self, "connection", None):
            self.connection.close()
            logger.debug("SQLite connection closed")
            self.connection = None  # type: ignore[assignment]
            self.cursor = None  # type: ignore[assignment]

    def __enter__(self) -> "DatabaseHandler":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        try:
            if getattr(self, "connection", None):
                if exc_type:
                    self.connection.rollback()
                else:
                    self.connection.commit()
        finally:
            self.close()

    # -- Internal helpers ---------------------------------------------------
    @staticmethod
    def _prepare_params(
        params: Optional[Union[Sequence[Any], Mapping[str, Any], Any]],
        *,
        for_many: bool = False,
    ) -> Optional[Union[Sequence[Any], Mapping[str, Any]]]:
        if params is None:
            return () if for_many else None
        if isinstance(params, Mapping):
            return params
        if isinstance(params, Sequence) and not isinstance(params, (str, bytes, bytearray)):
            return tuple(params)
        return (params,)

    # -- Convenience DDL helpers --------------------------------------------
    def add_progression_goals_table(self) -> None:
        """Ensure the progression_goals table exists."""
        ddl = """
            CREATE TABLE IF NOT EXISTS progression_goals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                exercise TEXT NOT NULL,
                goal_type TEXT NOT NULL,
                current_value REAL,
                target_value REAL,
                goal_date DATE NOT NULL,
                created_at DATETIME NOT NULL,
                completed BOOLEAN DEFAULT 0,
                completed_at DATETIME
            )
        """
        self.execute_query(ddl)


def add_progression_goals_table() -> None:
    """Module-level helper to create the progression goals table."""
    with DatabaseHandler() as db:
        db.add_progression_goals_table()


def add_volume_tracking_tables() -> None:
    """Ensure the volume tracking supporting tables exist."""
    ddl_volume_plans = """
        CREATE TABLE IF NOT EXISTS volume_plans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            training_days INTEGER NOT NULL,
            created_at DATETIME NOT NULL
        )
    """
    ddl_muscle_volumes = """
        CREATE TABLE IF NOT EXISTS muscle_volumes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plan_id INTEGER NOT NULL,
            muscle_group TEXT NOT NULL,
            weekly_sets INTEGER NOT NULL,
            sets_per_session REAL NOT NULL,
            status TEXT NOT NULL,
            FOREIGN KEY (plan_id) REFERENCES volume_plans (id) ON DELETE CASCADE
        )
    """
    with DatabaseHandler() as db:
        db.execute_query(ddl_volume_plans)
        db.execute_query(ddl_muscle_volumes)
