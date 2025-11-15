from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import shutil
import sqlite3
import sys
import time
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

DEFAULT_DB_PATH = (
    r"C:\\Users\\aatiya\\IdeaProjects\\Hypertrophy-Toolbox-v3\\data\\database.db"
)
DEFAULT_LOG_PATH = (
    r"C:\\Users\\aatiya\\IdeaProjects\\Hypertrophy-Toolbox-v3\\logs\\merge_progress.md"
)
DEFAULT_EXCLUDE_LIKE = "glossary,index,table of contents"
MUSCLE_SINGLE_COLUMNS: Tuple[str, ...] = (
    "primary_muscle_group",
    "secondary_muscle_group",
    "tertiary_muscle_group",
)
MUSCLE_MULTI_COLUMN = "advanced_isolated_muscles"
MUSCLE_COLUMNS: Tuple[str, ...] = MUSCLE_SINGLE_COLUMNS + (MUSCLE_MULTI_COLUMN,)
TEXT_PLACEHOLDER_COLUMNS: Tuple[str, ...] = (
    "primary_muscle_group",
    "secondary_muscle_group",
    "tertiary_muscle_group",
    "advanced_isolated_muscles",
    "utility",
    "grips",
    "stabilizers",
    "synergists",
    "force",
    "equipment",
    "mechanic",
    "difficulty",
)
METADATA_COLUMNS: Tuple[str, ...] = (
    "utility",
    "grips",
    "stabilizers",
    "synergists",
    "force",
    "equipment",
    "mechanic",
    "difficulty",
)
VERIFICATION_QUERIES: Sequence[Tuple[str, str]] = (
    (
        "Case-insensitive duplicate check",
        "SELECT LOWER(TRIM(exercise_name)) AS name_key, COUNT(*) AS count\n"
        "FROM exercises\n"
        "WHERE exercise_name IS NOT NULL AND TRIM(exercise_name) <> ''\n"
        "GROUP BY name_key\n"
        "HAVING count > 1\n"
        "ORDER BY count DESC, name_key ASC;",
    ),
    (
        "Primary muscle distinct count",
        "SELECT COUNT(DISTINCT primary_muscle_group) AS distinct_primary FROM exercises;",
    ),
    (
        "Secondary muscle distinct count",
        "SELECT COUNT(DISTINCT secondary_muscle_group) AS distinct_secondary FROM exercises;",
    ),
    (
        "Tertiary muscle distinct count",
        "SELECT COUNT(DISTINCT tertiary_muscle_group) AS distinct_tertiary FROM exercises;",
    ),
    (
        "Advanced isolated muscles spot check",
        "SELECT exercise_name, advanced_isolated_muscles\n"
        "FROM exercises\n"
        "WHERE advanced_isolated_muscles LIKE '%;%' OR advanced_isolated_muscles LIKE '%,%'\n"
        "LIMIT 25;",
    ),
)
TOKEN_SPLIT_PATTERN = re.compile(r"[,;/]")
SPACE_RE = re.compile(r"\s+")

BASE_CANONICAL_MAP: Dict[str, str] = {
    "lats": "Latissimus Dorsi",
    "latissimus dorsi": "Latissimus Dorsi",
    "traps": "Trapezius",
    "trapezius": "Trapezius",
    "glutes": "Gluteus Maximus",
    "gluteus maximus": "Gluteus Maximus",
    "rear delts": "Posterior Deltoid",
    "rear delt": "Posterior Deltoid",
    "posterior delts": "Posterior Deltoid",
    "posterior deltoid": "Posterior Deltoid",
    "anterior delts": "Anterior Deltoid",
    "anterior deltoid": "Anterior Deltoid",
    "medial delts": "Lateral Deltoid",
    "side delts": "Lateral Deltoid",
    "lateral deltoid": "Lateral Deltoid",
    "hams": "Hamstrings",
    "hamstring": "Hamstrings",
    "hamstrings": "Hamstrings",
    "quads": "Quadriceps",
    "quadricep": "Quadriceps",
    "quadriceps": "Quadriceps",
    "abs": "Rectus Abdominis",
    "rectus abdominis": "Rectus Abdominis",
    "obliques": "External Obliques",
    "external obliques": "External Obliques",
    "lowerback": "Lower Back",
    "lower back": "Lower Back",
    "triceps brachi": "Triceps Brachii",
    "triceps brachii": "Triceps Brachii",
}


@dataclass
class ExclusionStats:
    patterns: List[str]
    candidates: List[Tuple[int, str]]
    deleted: int


@dataclass
class PlaceholderStats:
    counts: Dict[str, int]
    rows_updated: int


@dataclass
class MuscleNormalizationStats:
    distinct_before: Dict[str, int]
    distinct_after: Dict[str, int]
    top_before: Dict[str, List[Tuple[Optional[str], int]]]
    top_after: Dict[str, List[Tuple[Optional[str], int]]]
    examples: Dict[str, List[Tuple[Optional[str], Optional[str]]]]
    rows_updated: int


@dataclass
class DuplicateResolution:
    groups_found: int
    resolved_groups: int
    rows_deleted: int
    merge_examples: List[Dict[str, object]]


@dataclass
class VerificationResult:
    title: str
    query: str
    columns: Sequence[str]
    rows: List[Tuple[object, ...]]


class CleanupError(RuntimeError):
    pass


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Post-merge cleanup utility for exercises table")
    parser.add_argument("--db", dest="db_path", default=DEFAULT_DB_PATH, help="SQLite database path")
    parser.add_argument("--log", dest="log_path", default=DEFAULT_LOG_PATH, help="Markdown log file path")
    parser.add_argument(
        "--dryrun",
        dest="dryrun",
        action="store_true",
        help="Run all steps without applying changes (default mode)",
    )
    parser.add_argument(
        "--apply",
        dest="apply",
        action="store_true",
        help="Apply changes (creates backup and commits)",
    )
    parser.add_argument(
        "--exclude-like",
        dest="exclude_like",
        default=DEFAULT_EXCLUDE_LIKE,
        help="Comma-separated substrings identifying non-exercise rows",
    )
    parser.add_argument(
        "--canon-file",
        dest="canon_file",
        default=None,
        help="Optional YAML/JSON mapping of muscle synonyms",
    )
    args = parser.parse_args(argv)
    if args.dryrun and args.apply:
        parser.error("--dryrun and --apply are mutually exclusive")
    if not args.dryrun and not args.apply:
        args.dryrun = True
    return args


def ensure_path(path: str) -> Path:
    return Path(path).expanduser().resolve()


def parse_patterns(raw: str) -> List[str]:
    if not raw:
        return []
    return [part.strip().lower() for part in raw.split(",") if part.strip()]


def load_canon_map(path: Optional[str]) -> Dict[str, str]:
    canon_map = dict(BASE_CANONICAL_MAP)
    if path:
        path_obj = Path(path)
        if not path_obj.exists():
            raise FileNotFoundError(f"Canonical map file not found: {path}")
        ext = path_obj.suffix.lower()
        if ext in {".yml", ".yaml"}:
            try:
                import yaml  # type: ignore
            except ImportError as exc:  # pragma: no cover - optional dependency
                raise CleanupError("PyYAML is required to load YAML canonical maps") from exc
            with path_obj.open("r", encoding="utf-8") as handle:
                content = yaml.safe_load(handle)
        else:
            with path_obj.open("r", encoding="utf-8") as handle:
                content = json.load(handle)
        if isinstance(content, dict):
            for key, value in content.items():
                normalized_key = str(key).strip().lower()
                normalized_value = str(value).strip()
                if normalized_key and normalized_value:
                    canon_map[normalized_key] = normalized_value
        else:
            raise CleanupError("Canonical map file must contain a mapping")
    for canonical in list(canon_map.values()):
        canon_map.setdefault(canonical.strip().lower(), canonical)
    return canon_map


def split_tokens(value: Optional[str]) -> List[str]:
    if value is None:
        return []
    tokens = [token.strip() for token in TOKEN_SPLIT_PATTERN.split(str(value))]
    return [token for token in tokens if token]


def titlecase_hyphen_aware(token: str) -> str:
    words = SPACE_RE.split(token.strip())
    normalized_words: List[str] = []
    for word in words:
        parts = word.split("-")
        normalized_parts = [part[:1].upper() + part[1:].lower() if part else "" for part in parts]
        normalized_words.append("-".join(normalized_parts))
    return " ".join(normalized_words)


def canonize(token: str, canon_map: Dict[str, str]) -> str:
    lowered = token.strip().lower()
    if not lowered:
        return ""
    mapped = canon_map.get(lowered)
    if mapped:
        return mapped
    return titlecase_hyphen_aware(token)


def ensure_backup(db_path: Path) -> Path:
    timestamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = db_path.with_name(f"{db_path.stem}.backup_{timestamp}{db_path.suffix}")
    shutil.copy2(db_path, backup_path)
    return backup_path


def fetch_top_values(conn: sqlite3.Connection, column: str, limit: int = 20) -> List[Tuple[Optional[str], int]]:
    query = (
        f"SELECT {column} AS value, COUNT(*) AS cnt "
        "FROM exercises "
        f"GROUP BY {column} "
        "ORDER BY (value IS NULL) ASC, cnt DESC, value ASC "
        "LIMIT ?"
    )
    cursor = conn.execute(query, (limit,))
    return [(row["value"], row["cnt"]) for row in cursor.fetchall()]


def fetch_distinct_count(conn: sqlite3.Connection, column: str) -> int:
    cursor = conn.execute(f"SELECT COUNT(DISTINCT {column}) FROM exercises")
    result = cursor.fetchone()
    return int(result[0] if result and result[0] is not None else 0)


def has_value(value: Optional[str]) -> bool:
    if value is None:
        return False
    return bool(str(value).strip())


def handle_exclusions(
    conn: sqlite3.Connection,
    patterns: Sequence[str],
    apply_mode: bool,
) -> ExclusionStats:
    if not patterns:
        return ExclusionStats(patterns=list(patterns), candidates=[], deleted=0)
    conditions = ["LOWER(exercise_name) LIKE ?" for _ in patterns]
    params = [f"%{pattern}%" for pattern in patterns]
    query = (
        "SELECT rowid AS row_id, exercise_name FROM exercises WHERE exercise_name IS NOT NULL AND ("
        + " OR ".join(conditions)
        + ")"
    )
    cursor = conn.execute(query, params)
    rows = [(int(row["row_id"]), str(row["exercise_name"])) for row in cursor.fetchall()]
    deleted = 0
    if apply_mode and rows:
        rowids = [row_id for row_id, _ in rows]
        placeholders = ",".join(["?"] * len(rowids))
        delete_sql = f"DELETE FROM exercises WHERE rowid IN ({placeholders})"
        conn.execute(delete_sql, rowids)
        deleted = len(rowids)
    return ExclusionStats(patterns=list(patterns), candidates=rows, deleted=deleted)


def convert_placeholders(conn: sqlite3.Connection) -> PlaceholderStats:
    placeholder_counts: Dict[str, int] = {}
    conditions: List[str] = []
    for column in TEXT_PLACEHOLDER_COLUMNS:
        cursor = conn.execute(
            f"SELECT COUNT(*) FROM exercises WHERE {column} IS NOT NULL AND TRIM({column}) IN ('', '-')"
        )
        count = int(cursor.fetchone()[0])
        placeholder_counts[column] = count
        if count:
            conditions.append(
                f"({column} IS NOT NULL AND TRIM({column}) IN ('', '-'))"
            )
    if not conditions:
        return PlaceholderStats(counts=placeholder_counts, rows_updated=0)
    assignments = []
    for column in TEXT_PLACEHOLDER_COLUMNS:
        assignments.append(
            f"{column} = CASE WHEN {column} IS NOT NULL AND TRIM({column}) IN ('', '-') THEN NULL ELSE {column} END"
        )
    update_sql = "UPDATE exercises SET " + ", ".join(assignments) + " WHERE " + " OR ".join(conditions)
    cursor = conn.execute(update_sql)
    rows_updated = cursor.rowcount if cursor.rowcount is not None else 0
    return PlaceholderStats(counts=placeholder_counts, rows_updated=rows_updated)


def normalize_muscles(
    conn: sqlite3.Connection,
    canon_map: Dict[str, str],
) -> MuscleNormalizationStats:
    distinct_before = {column: fetch_distinct_count(conn, column) for column in MUSCLE_COLUMNS}
    top_before = {column: fetch_top_values(conn, column) for column in MUSCLE_COLUMNS}
    examples: Dict[str, List[Tuple[Optional[str], Optional[str]]]] = {
        column: [] for column in MUSCLE_COLUMNS
    }
    updates: List[Tuple[Optional[str], Optional[str], Optional[str], Optional[str], int]] = []
    rows_updated = 0
    cursor = conn.execute(
        "SELECT rowid AS row_id, primary_muscle_group, secondary_muscle_group, tertiary_muscle_group, "
        "advanced_isolated_muscles FROM exercises"
    )
    seen_examples: Dict[str, set[Tuple[str, str]]] = {column: set() for column in MUSCLE_COLUMNS}
    for row in cursor.fetchall():
        row_id = int(row["row_id"])
        current_primary = row["primary_muscle_group"]
        current_secondary = row["secondary_muscle_group"]
        current_tertiary = row["tertiary_muscle_group"]
        current_advanced = row["advanced_isolated_muscles"]

        normalized_primary = normalize_single_value(current_primary, canon_map)
        normalized_secondary = normalize_single_value(current_secondary, canon_map)
        normalized_tertiary = normalize_single_value(current_tertiary, canon_map)
        normalized_advanced = normalize_multi_value(current_advanced, canon_map)

        if (
            normalized_primary == current_primary
            and normalized_secondary == current_secondary
            and normalized_tertiary == current_tertiary
            and normalized_advanced == current_advanced
        ):
            continue
        updates.append(
            (
                normalized_primary,
                normalized_secondary,
                normalized_tertiary,
                normalized_advanced,
                row_id,
            )
        )
        rows_updated += 1
        append_example(examples, seen_examples, "primary_muscle_group", current_primary, normalized_primary)
        append_example(
            examples,
            seen_examples,
            "secondary_muscle_group",
            current_secondary,
            normalized_secondary,
        )
        append_example(
            examples,
            seen_examples,
            "tertiary_muscle_group",
            current_tertiary,
            normalized_tertiary,
        )
        append_example(
            examples,
            seen_examples,
            "advanced_isolated_muscles",
            current_advanced,
            normalized_advanced,
        )
    if updates:
        update_sql = (
            "UPDATE exercises SET primary_muscle_group = ?, secondary_muscle_group = ?, "
            "tertiary_muscle_group = ?, advanced_isolated_muscles = ? WHERE rowid = ?"
        )
        payload = [
            (primary, secondary, tertiary, advanced, row_id)
            for primary, secondary, tertiary, advanced, row_id in updates
        ]
        conn.executemany(update_sql, payload)
    distinct_after = {column: fetch_distinct_count(conn, column) for column in MUSCLE_COLUMNS}
    top_after = {column: fetch_top_values(conn, column) for column in MUSCLE_COLUMNS}
    return MuscleNormalizationStats(
        distinct_before=distinct_before,
        distinct_after=distinct_after,
        top_before=top_before,
        top_after=top_after,
        examples=examples,
        rows_updated=rows_updated,
    )


def append_example(
    examples: Dict[str, List[Tuple[Optional[str], Optional[str]]]],
    seen_examples: Dict[str, set[Tuple[str, str]]],
    column: str,
    before: Optional[str],
    after: Optional[str],
    limit: int = 20,
) -> None:
    if before == after or len(examples[column]) >= limit:
        return
    key = (before or "", after or "")
    if key in seen_examples[column]:
        return
    seen_examples[column].add(key)
    examples[column].append((before, after))


def normalize_single_value(value: Optional[str], canon_map: Dict[str, str]) -> Optional[str]:
    if value is None:
        return None
    token = SPACE_RE.sub(" ", str(value).strip())
    if not token:
        return None
    normalized = canonize(token, canon_map)
    return normalized if normalized else None


def normalize_multi_value(value: Optional[str], canon_map: Dict[str, str]) -> Optional[str]:
    tokens = split_tokens(value)
    if not tokens:
        return None
    seen: Dict[str, str] = {}
    for token in tokens:
        normalized = canonize(token, canon_map)
        if not normalized:
            continue
        key = normalized.lower()
        seen[key] = normalized
    if not seen:
        return None
    ordered = sorted(seen.values(), key=lambda item: item.lower())
    return ", ".join(ordered)


def resolve_duplicates(
    conn: sqlite3.Connection,
    canon_map: Dict[str, str],
) -> DuplicateResolution:
    key_query = (
        "SELECT LOWER(TRIM(exercise_name)) AS name_key, COUNT(*) AS cnt "
        "FROM exercises WHERE exercise_name IS NOT NULL AND TRIM(exercise_name) <> '' "
        "GROUP BY name_key HAVING cnt > 1"
    )
    groups = conn.execute(key_query).fetchall()
    groups_found = len(groups)
    if not groups_found:
        return DuplicateResolution(groups_found=0, resolved_groups=0, rows_deleted=0, merge_examples=[])

    merge_examples: List[Dict[str, object]] = []
    resolved_groups = 0
    rows_deleted = 0
    for group in groups:
        name_key = group["name_key"]
        members = conn.execute(
            "SELECT rowid AS row_id, exercise_name, primary_muscle_group, secondary_muscle_group, "
            "tertiary_muscle_group, advanced_isolated_muscles, utility, grips, stabilizers, "
            "synergists, force, equipment, mechanic, difficulty "
            "FROM exercises WHERE LOWER(TRIM(exercise_name)) = ?",
            (name_key,),
        ).fetchall()
        if len(members) <= 1:
            continue
        keeper = choose_keeper(members)
        if keeper is None:
            continue
        keeper_id = keeper["row_id"]
        keeper_name = keeper["exercise_name"]
        updates, deleted_ids, filled_columns = merge_group(keeper, members, canon_map)
        if updates:
            update_sql = (
                "UPDATE exercises SET primary_muscle_group = ?, secondary_muscle_group = ?, "
                "tertiary_muscle_group = ?, advanced_isolated_muscles = ?, utility = ?, grips = ?, "
                "stabilizers = ?, synergists = ?, force = ?, equipment = ?, mechanic = ?, difficulty = ? "
                "WHERE rowid = ?"
            )
            conn.execute(update_sql, (*updates, keeper_id))
        if deleted_ids:
            placeholders = ",".join(["?"] * len(deleted_ids))
            delete_sql = f"DELETE FROM exercises WHERE rowid IN ({placeholders})"
            conn.execute(delete_sql, deleted_ids)
            rows_deleted += len(deleted_ids)
        if updates or deleted_ids:
            resolved_groups += 1
            merge_examples.append(
                {
                    "keeper_id": keeper_id,
                    "keeper_name": keeper_name,
                    "merged_ids": deleted_ids,
                    "filled_columns": sorted(set(filled_columns)),
                }
            )
    return DuplicateResolution(
        groups_found=groups_found,
        resolved_groups=resolved_groups,
        rows_deleted=rows_deleted,
        merge_examples=merge_examples,
    )


def choose_keeper(rows: Sequence[sqlite3.Row]) -> Optional[sqlite3.Row]:
    if not rows:
        return None
    best_row = None
    best_score = -1
    for row in rows:
        score = 0
        for column in MUSCLE_COLUMNS + METADATA_COLUMNS:
            if has_value(row[column]):
                score += 1
        if score > best_score or (score == best_score and (best_row is None or row["row_id"] < best_row["row_id"])):
            best_row = row
            best_score = score
    return best_row


def merge_group(
    keeper: sqlite3.Row,
    rows: Sequence[sqlite3.Row],
    canon_map: Dict[str, str],
) -> Tuple[Tuple[Optional[str], ...], List[int], List[str]]:
    keeper_id = keeper["row_id"]
    muscle_values = {
        column: keeper[column]
        for column in MUSCLE_COLUMNS
    }
    metadata_values = {
        column: keeper[column]
        for column in METADATA_COLUMNS
    }
    filled_columns: List[str] = []
    delete_ids: List[int] = []
    for row in rows:
        row_id = row["row_id"]
        if row_id == keeper_id:
            continue
        delete_ids.append(row_id)
        for column in MUSCLE_SINGLE_COLUMNS:
            if not has_value(muscle_values[column]) and has_value(row[column]):
                normalized = normalize_single_value(row[column], canon_map)
                if normalized:
                    muscle_values[column] = normalized
                    filled_columns.append(column)
        if has_value(row[MUSCLE_MULTI_COLUMN]):
            keeper_tokens = split_tokens(muscle_values[MUSCLE_MULTI_COLUMN])
            row_tokens = split_tokens(row[MUSCLE_MULTI_COLUMN])
            combined_tokens = set()
            for token in keeper_tokens + row_tokens:
                normalized = canonize(token, canon_map)
                if normalized:
                    combined_tokens.add(normalized)
            if combined_tokens:
                merged_value = ", ".join(sorted(combined_tokens, key=lambda item: item.lower()))
                if merged_value != muscle_values[MUSCLE_MULTI_COLUMN]:
                    muscle_values[MUSCLE_MULTI_COLUMN] = merged_value
                    filled_columns.append(MUSCLE_MULTI_COLUMN)
        for column in METADATA_COLUMNS:
            if not has_value(metadata_values[column]) and has_value(row[column]):
                metadata_values[column] = str(row[column]).strip()
                filled_columns.append(column)
    updates = (
        muscle_values["primary_muscle_group"],
        muscle_values["secondary_muscle_group"],
        muscle_values["tertiary_muscle_group"],
        muscle_values[MUSCLE_MULTI_COLUMN],
        metadata_values["utility"],
        metadata_values["grips"],
        metadata_values["stabilizers"],
        metadata_values["synergists"],
        metadata_values["force"],
        metadata_values["equipment"],
        metadata_values["mechanic"],
        metadata_values["difficulty"],
    )
    unique_filled: List[str] = []
    seen: set[str] = set()
    for column_name in filled_columns:
        lowered = column_name.lower()
        if lowered in seen:
            continue
        seen.add(lowered)
        unique_filled.append(column_name)
    return updates, delete_ids, unique_filled


def ensure_unique_index(conn: sqlite3.Connection) -> None:
    conn.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS ux_exercises_name_norm "
        "ON exercises (LOWER(TRIM(exercise_name)))"
    )


def run_verification_queries(conn: sqlite3.Connection) -> List[VerificationResult]:
    results: List[VerificationResult] = []
    for title, query in VERIFICATION_QUERIES:
        cursor = conn.execute(query)
        rows = cursor.fetchall()
        columns = [description[0] for description in cursor.description] if cursor.description else []
        results.append(VerificationResult(title=title, query=query, columns=columns, rows=[tuple(row) for row in rows]))
    return results


def append_report(
    log_path: Path,
    db_path: Path,
    mode: str,
    duration: float,
    exclusion_stats: ExclusionStats,
    placeholder_stats: PlaceholderStats,
    muscle_stats: MuscleNormalizationStats,
    duplicate_stats: DuplicateResolution,
    verification_results: List[VerificationResult],
) -> None:
    timestamp = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines: List[str] = []
    lines.append(f"## Post-Merge Cleanup: {timestamp}")
    lines.append(f"DB: `{db_path}`")
    lines.append(f"Mode: {mode}")
    lines.append("")
    lines.append("Exclusions:")
    lines.append(f"- patterns: {', '.join(exclusion_stats.patterns) if exclusion_stats.patterns else 'none'}")
    lines.append(f"- candidates: {len(exclusion_stats.candidates)}")
    if exclusion_stats.candidates:
        preview = ", ".join(
            f"{row_id}:{name}" for row_id, name in exclusion_stats.candidates[:20]
        )
        lines.append(f"- sample: {preview}")
    if mode == "apply":
        lines.append(f"- deleted: {exclusion_stats.deleted}")
    lines.append("")
    lines.append("Placeholders -> NULL:")
    lines.append(format_counts_table(placeholder_stats.counts))
    lines.append(f"Rows updated: {placeholder_stats.rows_updated}")
    lines.append("")
    lines.append("Muscle normalization:")
    lines.append(format_distinct_table(muscle_stats))
    lines.append(f"Rows normalized: {muscle_stats.rows_updated}")
    lines.append("")
    for column in MUSCLE_COLUMNS:
        lines.append(f"{column} top values (before):")
        lines.append(format_value_count_table(muscle_stats.top_before[column]))
        lines.append(f"{column} top values (after):")
        lines.append(format_value_count_table(muscle_stats.top_after[column]))
        if muscle_stats.examples[column]:
            example_strings = [
                f"`{format_optional(before)}` -> `{format_optional(after)}`"
                for before, after in muscle_stats.examples[column]
            ]
            lines.append(
                "Examples: " + ", ".join(example_strings)
            )
        lines.append("")
    lines.append("Duplicates resolution:")
    lines.append(
        f"- groups found: {duplicate_stats.groups_found}, merged: {duplicate_stats.resolved_groups}, "
        f"deleted: {duplicate_stats.rows_deleted}"
    )
    if duplicate_stats.merge_examples:
        example_lines = []
        for example in duplicate_stats.merge_examples[:10]:
            merged_ids_raw = example.get("merged_ids", [])
            if isinstance(merged_ids_raw, (list, tuple)):
                merged_ids_values = [str(value) for value in merged_ids_raw]
            elif merged_ids_raw is None:
                merged_ids_values = []
            else:
                merged_ids_values = [str(merged_ids_raw)]
            merged_ids = ", ".join(merged_ids_values)

            filled_cols_raw = example.get("filled_columns", [])
            if isinstance(filled_cols_raw, (list, tuple, set)):
                filled_cols_values = [str(value) for value in filled_cols_raw]
            elif filled_cols_raw is None:
                filled_cols_values = []
            else:
                filled_cols_values = [str(filled_cols_raw)]
            filled_cols = ", ".join(filled_cols_values) if filled_cols_values else "none"

            example_lines.append(
                f"`{example['keeper_name']}` kept (id {example['keeper_id']}), merged ids: [{merged_ids}], "
                f"columns filled: {filled_cols}"
            )
        lines.append("- examples: " + " | ".join(example_lines))
    lines.append("")
    lines.append("Verification:")
    for result in verification_results:
        lines.append(f"### {result.title}")
        lines.append("```")
        lines.append(result.query.strip())
        lines.append("```")
        if result.columns:
            lines.append(format_query_table(result.columns, result.rows))
        else:
            lines.append("(no rows)")
        lines.append("")
    lines.append(f"Timing: {duration:.2f} seconds")
    lines.append("")
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write("\n".join(lines) + "\n")


def format_counts_table(counts: Dict[str, int]) -> str:
    headers = "| Column | Placeholders |"
    separator = "| --- | --- |"
    rows = [
        f"| {column} | {counts.get(column, 0)} |"
        for column in TEXT_PLACEHOLDER_COLUMNS
    ]
    return "\n".join([headers, separator, *rows])


def format_distinct_table(stats: MuscleNormalizationStats) -> str:
    headers = "| Column | Before | After |"
    separator = "| --- | --- | --- |"
    rows = []
    for column in MUSCLE_COLUMNS:
        before = stats.distinct_before.get(column, 0)
        after = stats.distinct_after.get(column, 0)
        rows.append(f"| {column} | {before} | {after} |")
    return "\n".join([headers, separator, *rows])


def format_value_count_table(entries: List[Tuple[Optional[str], int]]) -> str:
    if not entries:
        return "(no data)"
    headers = "| Value | Count |"
    separator = "| --- | --- |"
    rows = [
        f"| {format_optional(value)} | {count} |"
        for value, count in entries
    ]
    return "\n".join([headers, separator, *rows])


def format_optional(value: object) -> str:
    if value is None:
        return "NULL"
    text = str(value)
    return text if text else '""'


def format_query_table(columns: Sequence[str], rows: Sequence[Tuple[object, ...]]) -> str:
    if not rows:
        return "(no rows)"
    headers = "| " + " | ".join(columns) + " |"
    separator = "| " + " | ".join(["---"] * len(columns)) + " |"
    formatted_rows = []
    for row in rows:
        formatted_rows.append(
            "| " + " | ".join(format_optional(value) for value in row) + " |"
        )
    return "\n".join([headers, separator, *formatted_rows])


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    db_path = ensure_path(args.db_path)
    log_path = ensure_path(args.log_path)
    patterns = parse_patterns(args.exclude_like)
    try:
        canon_map = load_canon_map(args.canon_file)
    except (CleanupError, FileNotFoundError) as exc:
        print(f"Error loading canonical map: {exc}", file=sys.stderr)
        return 1
    if not db_path.exists():
        print(f"Database not found: {db_path}", file=sys.stderr)
        return 1
    backup_path: Optional[Path] = None
    start_time = time.perf_counter()
    mode = "apply" if args.apply else "dryrun"
    exclusion_stats: ExclusionStats = ExclusionStats(patterns=list(patterns), candidates=[], deleted=0)
    placeholder_stats: PlaceholderStats = PlaceholderStats(
        counts={column: 0 for column in TEXT_PLACEHOLDER_COLUMNS},
        rows_updated=0,
    )
    muscle_stats: MuscleNormalizationStats = MuscleNormalizationStats(
        distinct_before={column: 0 for column in MUSCLE_COLUMNS},
        distinct_after={column: 0 for column in MUSCLE_COLUMNS},
        top_before={column: [] for column in MUSCLE_COLUMNS},
        top_after={column: [] for column in MUSCLE_COLUMNS},
        examples={column: [] for column in MUSCLE_COLUMNS},
        rows_updated=0,
    )
    duplicate_stats: DuplicateResolution = DuplicateResolution(
        groups_found=0,
        resolved_groups=0,
        rows_deleted=0,
        merge_examples=[],
    )
    verification_results: List[VerificationResult] = []
    conn: Optional[sqlite3.Connection] = None
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        if args.apply:
            backup_path = ensure_backup(db_path)
        conn.execute("BEGIN")
        exclusion_stats = handle_exclusions(conn, patterns, args.apply)
        placeholder_stats = convert_placeholders(conn)
        muscle_stats = normalize_muscles(conn, canon_map)
        duplicate_stats = resolve_duplicates(conn, canon_map)
        ensure_unique_index(conn)
        verification_results = run_verification_queries(conn)
        if args.apply:
            conn.commit()
        else:
            conn.rollback()
    except Exception as exc:
        if conn is not None:
            try:
                conn.rollback()
            except sqlite3.Error:
                pass
        print(f"Cleanup failed: {exc}", file=sys.stderr)
        return 1
    finally:
        if conn is not None:
            conn.close()
    duration = time.perf_counter() - start_time
    append_report(
        log_path=log_path,
        db_path=db_path,
        mode=mode,
        duration=duration,
        exclusion_stats=exclusion_stats,
        placeholder_stats=placeholder_stats,
        muscle_stats=muscle_stats,
        duplicate_stats=duplicate_stats,
        verification_results=verification_results,
    )
    if backup_path:
        print(f"Backup created at {backup_path}")
    print(f"Cleanup completed in {duration:.2f}s ({mode})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
