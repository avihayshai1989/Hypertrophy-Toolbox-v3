from __future__ import annotations

import argparse
import datetime as dt
import os
import sqlite3
from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple

from muscle_norm import (
    DEFAULT_ACRONYMS,
    get_alias_acronyms,
    load_alias_map,
    normalize_list,
    normalize_single,
    split_list,
)

SCRIPT_ROOT = os.path.dirname(os.path.abspath(__file__))
DEFAULT_DB_PATH = os.path.join(SCRIPT_ROOT, "data", "database.db")
DEFAULT_LOG_PATH = os.path.join(SCRIPT_ROOT, "logs", "muscle_normalization.md")
MUSCLE_SCALAR_FIELDS: Sequence[str] = (
    "primary_muscle_group",
    "secondary_muscle_group",
    "tertiary_muscle_group",
)
MUSCLE_LIST_FIELD = "advanced_isolated_muscles"
MUSCLE_FIELDS: Sequence[str] = (*MUSCLE_SCALAR_FIELDS, MUSCLE_LIST_FIELD)


@dataclass
class NormalizationResult:
    updated: int
    no_op: int
    errors: int
    total_rows: int
    dryrun: bool
    backup_path: Optional[str]
    log_path: str
    timestamp: dt.datetime


def _format_value(value: Optional[str]) -> str:
    if value is None:
        return "NULL"
    return f'"{value}"'


def _display_value(value: Optional[str]) -> str:
    return value if value is not None else "<NULL>"


def _create_backup(db_path: str) -> str:
    timestamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{db_path}.backup_{timestamp}"
    source = sqlite3.connect(db_path)
    target = sqlite3.connect(backup_path)
    try:
        source.backup(target)
    finally:
        target.close()
        source.close()
    return backup_path


def _collect_distinct(values: Dict[str, Set[str]], field: str, value: Optional[str]) -> None:
    if value is None:
        return
    values[field].add(value)


def _values_equal(original: Optional[str], normalized: Optional[str]) -> bool:
    return original == normalized


def _normalize_row(
    row: sqlite3.Row,
    alias_map: Dict[str, str],
    acronyms: Set[str],
) -> Tuple[Dict[str, Optional[str]], List[str], Dict[str, Tuple[Optional[str], Optional[str]]]]:
    updates: Dict[str, Optional[str]] = {}
    change_lines: List[str] = []
    per_field_changes: Dict[str, Tuple[Optional[str], Optional[str]]] = {}

    for field in MUSCLE_SCALAR_FIELDS:
        original = row[field]
        normalized = normalize_single(original, alias_map, acronyms)
        if not _values_equal(original, normalized):
            updates[field] = normalized
            change_lines.append(
                f"{field}: {_format_value(original)} → {_format_value(normalized)}"
            )
            per_field_changes[field] = (original, normalized)

    original_list = row[MUSCLE_LIST_FIELD]
    normalized_list = normalize_list(original_list, alias_map, acronyms)
    if not _values_equal(original_list, normalized_list):
        updates[MUSCLE_LIST_FIELD] = normalized_list
        change_lines.append(
            f"{MUSCLE_LIST_FIELD}: {_format_value(original_list)} → {_format_value(normalized_list)}"
        )
        per_field_changes[MUSCLE_LIST_FIELD] = (original_list, normalized_list)

    return updates, change_lines, per_field_changes


def _ensure_log_directory(log_path: str) -> None:
    directory = os.path.dirname(log_path) or "."
    os.makedirs(directory, exist_ok=True)


def _write_report(
    log_path: str,
    timestamp: dt.datetime,
    dryrun: bool,
    alias_file: Optional[str],
    acronyms: Set[str],
    distinct_before: Dict[str, Set[str]],
    distinct_after: Dict[str, Set[str]],
    change_counter: Counter,
    row_change_lines: List[str],
    updated: int,
    no_op: int,
    errors: List[str],
) -> None:
    _ensure_log_directory(log_path)
    lines: List[str] = []
    lines.append(f"## Run: {timestamp.strftime('%Y-%m-%d %H:%M:%S')} | dryrun={'true' if dryrun else 'false'}")
    lines.append(f"- Alias file: {alias_file or 'default aliases'}")
    lines.append(f"- Acronyms: {', '.join(sorted(acronyms)) or 'none'}")
    lines.append("- Distinct values:")
    for field in MUSCLE_FIELDS:
        before_count = len(distinct_before[field])
        after_count = len(distinct_after[field])
        lines.append(f"  - {field}: before={before_count} after={after_count}")
    lines.append("")
    lines.append("### Top Changes (limit 50)")
    lines.append("| Field | Before | After | Count |")
    lines.append("| --- | --- | --- | --- |")
    if change_counter:
        for (field, before, after), count in change_counter.most_common(50):
            lines.append(f"| {field} | {before} | {after} | {count} |")
    else:
        lines.append("| - | - | - | 0 |")
    lines.append("")
    lines.append("### Row Changes")
    if row_change_lines:
        for entry in row_change_lines:
            lines.append(f"- {entry}")
    else:
        lines.append("- None.")
    lines.append("")
    lines.append(f"Totals: Updated={updated}, No-op={no_op}, Errors={len(errors)}")
    if errors:
        lines.append("")
        lines.append("### Errors")
        for err in errors:
            lines.append(f"- {err}")
    with open(log_path, "a", encoding="utf-8") as handle:
        if handle.tell() > 0:
            handle.write("\n\n")
        handle.write("\n".join(lines))


def normalize_database(
    db_path: str,
    log_path: str,
    *,
    alias_file: Optional[str] = None,
    dryrun: bool = False,
) -> NormalizationResult:
    if not os.path.exists(db_path):
        raise FileNotFoundError(f"SQLite database not found: {db_path}")

    alias_map = load_alias_map(alias_file)
    acronyms = set(DEFAULT_ACRONYMS)
    acronyms.update(get_alias_acronyms())

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    timestamp = dt.datetime.now()

    distinct_before: Dict[str, Set[str]] = defaultdict(set)
    distinct_after: Dict[str, Set[str]] = defaultdict(set)
    change_counter: Counter = Counter()
    row_change_lines: List[str] = []
    errors: List[str] = []
    updates: List[Tuple[int, Dict[str, Optional[str]]]] = []
    updated_rows = 0
    no_op_rows = 0

    total_rows = 0
    backup_path: Optional[str] = None

    try:
        try:
            query = "SELECT rowid, " + ", ".join(MUSCLE_FIELDS) + " FROM exercises"
            rows = conn.execute(query).fetchall()
        except sqlite3.OperationalError as exc:
            raise RuntimeError("Table 'exercises' not found or schema mismatch") from exc

        total_rows = len(rows)

        for row in rows:
            rowid = row["rowid"]
            try:
                row_updates, change_lines, per_field_changes = _normalize_row(row, alias_map, acronyms)
            except Exception as exc:  # pragma: no cover - defensive
                errors.append(f"rowid={rowid}: {exc}")
                continue

            for field in MUSCLE_FIELDS:
                original = row[field]
                if original is not None and str(original).strip() != "":
                    distinct_before[field].add(str(original).strip())
                if field in MUSCLE_SCALAR_FIELDS:
                    normalized = normalize_single(original, alias_map, acronyms)
                else:
                    normalized = normalize_list(original, alias_map, acronyms)
                if normalized:
                    distinct_after[field].add(normalized)

            if row_updates:
                updates.append((rowid, row_updates))
                updated_rows += 1
                for line in change_lines:
                    row_change_lines.append(f"[rowid={rowid}] {line}")
                for field, (before, after) in per_field_changes.items():
                    change_counter[(field, _display_value(before), _display_value(after))] += 1
            else:
                no_op_rows += 1

        if updates and not dryrun and not errors:
            backup_path = _create_backup(db_path)
            conn.execute("BEGIN")
            try:
                for rowid, payload in updates:
                    columns = list(payload.keys())
                    assignments = ", ".join(f"{column} = ?" for column in columns)
                    params: List[Any] = [payload[column] for column in columns]
                    params.append(rowid)
                    conn.execute(
                        f"UPDATE exercises SET {assignments} WHERE rowid = ?",
                        params,
                    )
                conn.commit()
            except Exception:
                conn.rollback()
                raise
    finally:
        conn.close()

    _write_report(
        log_path,
        timestamp,
        dryrun,
        alias_file,
        acronyms,
        distinct_before,
        distinct_after,
        change_counter,
        row_change_lines,
        updated_rows,
        no_op_rows,
        errors,
    )

    print(
        f"Run {timestamp.strftime('%Y-%m-%d %H:%M:%S')} | dryrun={dryrun} | "
        f"rows={total_rows} updated={updated_rows} no_ops={no_op_rows} errors={len(errors)}"
    )
    for field in MUSCLE_FIELDS:
        print(
            f"  {field}: distinct_before={len(distinct_before[field])} → distinct_after={len(distinct_after[field])}"
        )
    if backup_path:
        print(f"Backup created: {backup_path}")
    print(f"Report appended to: {log_path}")

    return NormalizationResult(
        updated=updated_rows,
        no_op=no_op_rows,
        errors=len(errors),
        total_rows=total_rows,
        dryrun=dryrun,
        backup_path=backup_path,
        log_path=os.path.abspath(log_path),
        timestamp=timestamp,
    )


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Normalize muscle fields in the exercises table.")
    parser.add_argument("--db", default=DEFAULT_DB_PATH, help="Path to the SQLite database")
    parser.add_argument("--log", default=DEFAULT_LOG_PATH, help="Path to the Markdown report file")
    parser.add_argument("--alias-file", help="Optional YAML/JSON alias map for muscle names")
    parser.add_argument("--dryrun", action="store_true", help="Run without writing changes")
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> None:
    args = parse_args(argv)
    normalize_database(
        os.path.abspath(args.db),
        os.path.abspath(args.log),
        alias_file=os.path.abspath(args.alias_file) if args.alias_file else None,
        dryrun=args.dryrun,
    )


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    main()
