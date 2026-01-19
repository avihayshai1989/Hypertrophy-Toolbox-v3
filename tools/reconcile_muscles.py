#!/usr/bin/env python3
"""Reconcile muscle group assignments in the exercises catalogue."""
from __future__ import annotations

import argparse
import logging
import os
import re
import shutil
import sqlite3
import sys
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from utils.constants import (  # noqa: E402
    ADVANCED_SET,
    ADV_SYNONYMS,
    GROUP_LABELS_FORBIDDEN_IN_ADV,
    NULL_TOKENS,
    PRIMARY_SET,
    PST_SYNONYMS,
)

PRIMARY_LOOKUP = {label.lower(): label for label in PRIMARY_SET}
PST_SYNONYMS_LOOKUP = {alias.lower(): target for alias, target in PST_SYNONYMS.items()}
ADVANCED_LOOKUP = set(ADVANCED_SET)
ADV_SYNONYMS_LOOKUP = {alias.lower(): target for alias, target in ADV_SYNONYMS.items()}
FORBIDDEN_ADV = {token.lower() for token in GROUP_LABELS_FORBIDDEN_IN_ADV}
NULL_TOKENS_LOWER = {token.lower() for token in NULL_TOKENS}

TARGET_FIELDS = (
    "primary_muscle_group",
    "secondary_muscle_group",
    "tertiary_muscle_group",
    "advanced_isolated_muscles",
)

COLUMN_SYNONYMS = {
    "exercise_name": {"exercise_name", "exercise", "exercise name"},
    "primary_muscle_group": {
        "primary_muscle_group",
        "primary muscle group",
        "primary",
        "primary muscle",
    },
    "secondary_muscle_group": {
        "secondary_muscle_group",
        "secondary muscle group",
        "secondary",
        "secondary muscle",
    },
    "tertiary_muscle_group": {
        "tertiary_muscle_group",
        "tertiary muscle group",
        "tertiary",
        "tertiary muscle",
    },
    "advanced_isolated_muscles": {
        "advanced_isolated_muscles",
        "advanced isolated muscles",
        "advanced isolated muscle groups",
        "advanced_isolated",
    },
}

DISPLAY_ROWS = 20
_WHITESPACE_RE = re.compile(r"\s+")
_SANITIZE_RE = re.compile(r"[^a-z0-9]")


@dataclass
class PreviewResult:
    diffs_df: pd.DataFrame
    total_exercises: int
    changed_rows: int
    field_change_counts: Dict[str, int]
    missing_in_db: List[str]
    ambiguous_rows: int
    skipped_rows: int
    curation_records: List[Dict[str, Any]]


def str_to_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    if text in {"y", "yes", "true", "1"}:
        return True
    if text in {"n", "no", "false", "0"}:
        return False
    raise argparse.ArgumentTypeError(f"Expected a boolean value, got '{value}'")


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Reconcile muscle group fields from CSV sources.")
    parser.add_argument("--apply", action="store_true", help="Apply changes to the database")
    parser.add_argument("--db", dest="db_path", help="Path to the SQLite database to use")
    parser.add_argument(
        "--csv1",
        dest="musclewiki_csv",
        help="Path to musclewiki_exercises_csv.csv (defaults to data/Database_backup/...)\n",
    )
    parser.add_argument(
        "--csv2",
        dest="merge_preview_csv",
        help="Path to merge_preview.csv (defaults to data/Database_backup/...)\n",
    )
    parser.add_argument("--limit", type=int, default=DISPLAY_ROWS, help="Number of diff rows to print in preview")
    parser.add_argument(
        "--skip-ambiguous",
        type=str_to_bool,
        default=True,
        help="Skip ambiguous rows (default: true)",
    )
    return parser.parse_args(argv)


def setup_logging() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")


def _clean_str(value: Any) -> str:
    if value is None:
        return ""
    token = str(value).strip()
    if not token:
        return ""
    token = _WHITESPACE_RE.sub(" ", token)
    if token.lower() in NULL_TOKENS_LOWER:
        return ""
    return token


def _is_null(value: Any) -> bool:
    return _clean_str(value) == ""


def display_value(value: Any) -> Optional[str]:
    cleaned = _clean_str(value)
    return cleaned or None


def values_equal(old: Any, new: Any) -> bool:
    return _clean_str(old).lower() == _clean_str(new).lower()


def sanitize_key(value: Any) -> str:
    token = _clean_str(value)
    if not token:
        return ""
    return _SANITIZE_RE.sub("", token.lower())


def parse_diff_value(value: Any) -> Optional[str]:
    if _is_null(value):
        return None
    text = str(value)
    if "->" not in text:
        cleaned = _clean_str(text)
        return cleaned or None
    _, right = text.split("->", 1)
    cleaned = _clean_str(right)
    return cleaned or None


def normalize_pst(value: Any) -> Tuple[str, bool, str]:
    token = _clean_str(value)
    if not token:
        return "", False, ""
    low = token.lower()
    if low == "shoulders":
        return "Shoulders", True, "generic_shoulders"
    if low in PST_SYNONYMS_LOOKUP:
        mapped = PST_SYNONYMS_LOOKUP[low]
        if mapped in PRIMARY_SET:
            return mapped, False, ""
        return mapped, True, "mapped_not_canonical"
    if low in PRIMARY_LOOKUP:
        return PRIMARY_LOOKUP[low], False, ""
    return token, True, "unmapped"


def refine_shoulders_with_advanced(pst_value: str, advanced_tokens: Sequence[str]) -> Tuple[str, bool, str]:
    token = _clean_str(pst_value)
    if not token:
        return "", False, ""
    if token.lower() != "shoulders":
        return pst_value, False, ""
    has_front = "anterior-deltoid" in advanced_tokens
    has_middle = "lateral-deltoid" in advanced_tokens
    has_rear = "posterior-deltoid" in advanced_tokens
    picks = sum([has_front, has_middle, has_rear])
    if picks == 1:
        if has_front:
            return "Front-Shoulder", False, ""
        if has_middle:
            return "Middle-Shoulder", False, ""
        return "Rear-Shoulder", False, ""
    return pst_value, True, "ambiguous_shoulders"


def normalize_advanced(csv_str: Any) -> List[str]:
    if _is_null(csv_str):
        return []
    raw = _clean_str(csv_str).replace(";", ",")
    tokens: List[str] = []
    seen: set[str] = set()
    for part in raw.split(","):
        token = _clean_str(part)
        if not token:
            continue
        low = token.lower()
        low = ADV_SYNONYMS_LOOKUP.get(low, low)
        if low in FORBIDDEN_ADV:
            continue
        if low in ADVANCED_LOOKUP and low not in seen:
            seen.add(low)
            tokens.append(low)
    tokens.sort()
    return tokens


def format_advanced(tokens: Sequence[str]) -> str:
    return ", ".join(tokens) if tokens else ""


def resolve_advanced(
    merge_value: Any,
    wiki_value: Any,
    db_value: Any,
) -> Dict[str, Any]:
    candidate_sequence = [
        ("merge_preview", merge_value),
        ("musclewiki", wiki_value),
        ("database", db_value),
    ]
    candidate_source = "database"
    candidate_raw: Any = db_value
    for source, raw in candidate_sequence:
        if not _is_null(raw):
            candidate_source = source
            candidate_raw = raw
            break
    candidate_tokens = normalize_advanced(candidate_raw)
    db_tokens = normalize_advanced(db_value)
    ambiguous = False
    reason = ""
    used_source = candidate_source
    source_value = candidate_raw
    if used_source != "database" and not candidate_tokens and db_tokens:
        candidate_tokens = db_tokens
        used_source = "database"
        source_value = db_value
    elif not candidate_tokens and candidate_raw and not _is_null(candidate_raw):
        if db_tokens:
            candidate_tokens = db_tokens
            used_source = "database"
            source_value = db_value
        else:
            ambiguous = True
            reason = "advanced_unmapped"
    formatted = format_advanced(candidate_tokens)
    return {
        "tokens": candidate_tokens,
        "formatted": formatted,
        "ambiguous": ambiguous,
        "reason": reason,
        "source": used_source,
        "source_value": source_value,
        "candidate_source": candidate_source,
    }


def resolve_pst_field(
    field_name: str,
    merge_value: Any,
    wiki_value: Any,
    db_value: Any,
    advanced_tokens: Sequence[str],
) -> Dict[str, Any]:
    candidate_sequence = [
        ("merge_preview", merge_value),
        ("musclewiki", wiki_value),
        ("database", db_value),
    ]
    source = "database"
    source_value: Any = db_value
    for origin, raw in candidate_sequence:
        if not _is_null(raw):
            source = origin
            source_value = raw
            break
    normalized, ambiguous, reason = normalize_pst(source_value)
    if ambiguous:
        normalized, refined_ambiguous, refine_reason = refine_shoulders_with_advanced(normalized, advanced_tokens)
        if refined_ambiguous:
            ambiguous = True
            reason = refine_reason or reason or f"{field_name}_ambiguous"
        else:
            ambiguous = False
            reason = ""
    if normalized and normalized not in PRIMARY_SET and not ambiguous:
        ambiguous = True
        reason = reason or "not_in_primary_set"
    return {
        "value": normalized,
        "ambiguous": ambiguous,
        "reason": reason,
        "source_value": source_value,
        "source": source,
    }


def load_musclewiki_dataframe(path: Path) -> pd.DataFrame:
    if not path.exists():
        logging.warning("MuscleWiki CSV not found at %s", path)
        return pd.DataFrame(columns=["exercise_name", *TARGET_FIELDS])
    df = pd.read_csv(path)
    rename: Dict[str, str] = {}
    reversed_lookup = {sanitize_key(col): col for col in df.columns}
    for target, synonyms in COLUMN_SYNONYMS.items():
        for synonym in synonyms:
            key = sanitize_key(synonym)
            if key in reversed_lookup:
                rename[reversed_lookup[key]] = target
                break
    df = df.rename(columns=rename)
    if "exercise_name" not in df.columns:
        raise ValueError("musclewiki CSV missing 'exercise_name' column")
    relevant_cols = [col for col in ["exercise_name", *TARGET_FIELDS] if col in df.columns]
    relevant = df[relevant_cols].copy()
    relevant["exercise_name"] = relevant["exercise_name"].astype(str).str.strip()
    return relevant


def load_merge_preview_dataframe(path: Path) -> pd.DataFrame:
    if not path.exists():
        logging.warning("merge_preview CSV not found at %s", path)
        return pd.DataFrame(columns=["exercise_name", *TARGET_FIELDS])
    df = pd.read_csv(path)
    records: List[Dict[str, Any]] = []
    for _, row in df.iterrows():
        exercise_name = row.get("exercise_name") or row.get("excel_original_name")
        if _is_null(exercise_name):
            continue
        record: Dict[str, Any] = {"exercise_name": _clean_str(exercise_name)}
        for field in TARGET_FIELDS:
            direct_value = row.get(field)
            diff_value = row.get(f"{field}_diff")
            value = None
            if not _is_null(direct_value):
                value = direct_value
            elif not _is_null(diff_value):
                value = parse_diff_value(diff_value)
            record[field] = value
        records.append(record)
    if not records:
        return pd.DataFrame(columns=["exercise_name", *TARGET_FIELDS])
    return pd.DataFrame.from_records(records, columns=["exercise_name", *TARGET_FIELDS])


def load_db_snapshot(connection: sqlite3.Connection) -> pd.DataFrame:
    query = """
        SELECT
            exercise_name,
            primary_muscle_group,
            secondary_muscle_group,
            tertiary_muscle_group,
            advanced_isolated_muscles
        FROM exercises
    """
    return pd.read_sql_query(query, connection)


def build_source_map(df: pd.DataFrame) -> Dict[str, Dict[str, Any]]:
    mapping: Dict[str, Dict[str, Any]] = {}
    if df.empty:
        return mapping
    for _, row in df.iterrows():
        exercise_name = row.get("exercise_name")
        if _is_null(exercise_name):
            continue
        key = sanitize_key(exercise_name)
        if not key or key in mapping:
            continue
        entry = {"exercise_name": _clean_str(exercise_name)}
        for field in TARGET_FIELDS:
            if field in row:
                entry[field] = row[field]
        mapping[key] = entry
    return mapping


def build_proposed_updates(
    db_df: pd.DataFrame,
    merge_map: Dict[str, Dict[str, Any]],
    wiki_map: Dict[str, Dict[str, Any]],
    *,
    skip_ambiguous: bool,
) -> Tuple[pd.DataFrame, Dict[str, int], List[str], List[Dict[str, Any]], int, int]:
    field_change_counts = {field: 0 for field in TARGET_FIELDS}
    rows: List[Dict[str, Any]] = []
    curation_records: List[Dict[str, Any]] = []
    ambiguous_rows = 0
    skipped_rows = 0

    db_df = db_df.copy()
    db_df["exercise_name"] = db_df["exercise_name"].astype(str)
    db_keys = {sanitize_key(name): name for name in db_df["exercise_name"]}
    extra_keys = (set(merge_map) | set(wiki_map)) - set(db_keys)
    missing_in_db = sorted(
        {
            (merge_map.get(key) or wiki_map.get(key) or {}).get("exercise_name")
            for key in extra_keys
            if key
        }
    )

    for _, db_row in db_df.iterrows():
        exercise_name = db_row["exercise_name"]
        key = sanitize_key(exercise_name)
        merge_row = merge_map.get(key, {})
        wiki_row = wiki_map.get(key, {})

        advanced_result = resolve_advanced(
            merge_row.get("advanced_isolated_muscles"),
            wiki_row.get("advanced_isolated_muscles"),
            db_row.get("advanced_isolated_muscles"),
        )
        advanced_tokens = advanced_result["tokens"]

        ambiguous_fields: List[Tuple[str, Dict[str, Any]]] = []
        if advanced_result["ambiguous"]:
            ambiguous_fields.append(("advanced_isolated_muscles", advanced_result))

        pst_results: Dict[str, Dict[str, Any]] = {}
        for field in ("primary_muscle_group", "secondary_muscle_group", "tertiary_muscle_group"):
            result = resolve_pst_field(
                field,
                merge_row.get(field),
                wiki_row.get(field),
                db_row.get(field),
                advanced_tokens,
            )
            pst_results[field] = result
            if result["ambiguous"]:
                ambiguous_fields.append((field, result))

        if ambiguous_fields:
            ambiguous_rows += 1
            for field, info in ambiguous_fields:
                mapped_value = (
                    info.get("formatted")
                    if field == "advanced_isolated_muscles"
                    else info.get("value")
                )
                curation_records.append(
                    {
                        "exercise_name": exercise_name,
                        "field": field,
                        "source_value": display_value(info.get("source_value")),
                        "mapped_value": display_value(mapped_value),
                        "reason": info.get("reason") or "ambiguous",
                    }
                )
            if skip_ambiguous:
                skipped_rows += 1
                continue

        record: Dict[str, Any] = {"exercise_name": exercise_name}
        changed = False

        for field in ("primary_muscle_group", "secondary_muscle_group", "tertiary_muscle_group"):
            old_value = display_value(db_row.get(field))
            new_label = pst_results[field]["value"]
            new_value = new_label if new_label else None
            record[f"{field}_old"] = old_value
            record[f"{field}_new"] = new_value
            if not values_equal(old_value, new_value):
                field_change_counts[field] += 1
                changed = True

        old_adv_value = display_value(db_row.get("advanced_isolated_muscles"))
        new_adv_string = advanced_result["formatted"]
        new_adv_value = new_adv_string if new_adv_string else None
        record["advanced_isolated_muscles_old"] = old_adv_value
        record["advanced_isolated_muscles_new"] = new_adv_value
        if not values_equal(old_adv_value, new_adv_value):
            field_change_counts["advanced_isolated_muscles"] += 1
            changed = True

        if changed:
            rows.append(record)

    diffs_df = pd.DataFrame(rows)
    return diffs_df, field_change_counts, missing_in_db, curation_records, ambiguous_rows, skipped_rows


def export_preview(diffs_df: pd.DataFrame, logs_dir: Path) -> Path:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = logs_dir / f"muscle_reconciliation_preview_{timestamp}.xlsx"
    ensure_parent_dir(output_path)
    diffs_df.to_excel(output_path, index=False)
    return output_path


def export_curation(curation_records: List[Dict[str, Any]], logs_dir: Path) -> Optional[Path]:
    if not curation_records:
        return None
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = logs_dir / f"muscle_reconciliation_curation_{timestamp}.csv"
    ensure_parent_dir(output_path)
    pd.DataFrame(curation_records).to_csv(output_path, index=False)
    return output_path


def generate_alias_candidate_report(
    db_df: pd.DataFrame,
    merge_df: pd.DataFrame,
    wiki_df: pd.DataFrame,
    logs_dir: Path,
) -> Optional[Path]:
    counts: Counter[str] = Counter()

    def accumulate(values: Iterable[Any]) -> None:
        for value in values:
            token = _clean_str(value)
            if not token:
                continue
            low = token.lower()
            if low in NULL_TOKENS_LOWER or low in PRIMARY_LOOKUP or low in PST_SYNONYMS_LOOKUP:
                continue
            if any(canonical.lower() == low for canonical in PRIMARY_SET):
                continue
            counts[token] += 1

    for df in (db_df, merge_df, wiki_df):
        for field in ("primary_muscle_group", "secondary_muscle_group", "tertiary_muscle_group"):
            if field in df.columns:
                accumulate(df[field].tolist())

    if not counts:
        return None

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = logs_dir / f"muscle_alias_candidates_{timestamp}.csv"
    ensure_parent_dir(output_path)
    pd.DataFrame(
        [{"label": label, "count": count} for label, count in counts.most_common()]
    ).to_csv(output_path, index=False)
    return output_path


def print_preview(diffs_df: pd.DataFrame, limit: int) -> None:
    if diffs_df.empty:
        logging.info("No differences detected.")
        return
    display_df = diffs_df.head(limit).fillna("")
    with pd.option_context("display.max_columns", None, "display.width", 160):
        logging.info("Top %s differences:\n%s", limit, display_df.to_string(index=False))


def ensure_parent_dir(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def copy_database_backup(db_path: Path, logs_dir: Path) -> Path:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = logs_dir / f"database_backup_{timestamp}.db"
    ensure_parent_dir(backup_path)
    shutil.copy2(db_path, backup_path)
    logging.info("Backup created at %s", backup_path)
    return backup_path


def configure_sqlite_connection(db_path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(str(db_path))
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON;")
    connection.execute("PRAGMA busy_timeout = 5000;")
    connection.execute("PRAGMA journal_mode = WAL;")
    connection.execute("PRAGMA synchronous = NORMAL;")
    return connection


def fetch_current_row(connection: sqlite3.Connection, exercise_name: str) -> Optional[Dict[str, Any]]:
    cursor = connection.execute(
        "SELECT * FROM exercises WHERE exercise_name = ? COLLATE NOCASE",
        (exercise_name,),
    )
    row = cursor.fetchone()
    return dict(row) if row else None


def build_shared_handler(connection: sqlite3.Connection):
    from utils.database import DatabaseHandler  # type: ignore

    class SharedDatabaseHandler(DatabaseHandler):
        # Reuse project normalisation while keeping writes within this script's transaction.
        def __init__(self):
            self.database_path = "shared"
            self.connection = connection
            self.cursor = self.connection.cursor()

        def execute_query(self, query: str, params: Any = None, *, commit: bool = True) -> int:  # type: ignore[override]
            prepared = self._prepare_params(params)
            if prepared is None:
                self.cursor.execute(query)
            else:
                self.cursor.execute(query, prepared)
            return self.cursor.rowcount

        def executemany(self, query: str, param_sets: Iterable[Any], *, commit: bool = True) -> int:  # type: ignore[override]
            prepared_sets = [self._prepare_params(params, for_many=True) or tuple() for params in param_sets]
            self.cursor.executemany(query, prepared_sets)
            return self.cursor.rowcount

        def __exit__(self, exc_type, exc_val, exc_tb):
            try:
                if exc_type:
                    connection.rollback()
            finally:
                self.cursor.close()

        def close(self) -> None:  # type: ignore[override]
            if getattr(self, "cursor", None):
                self.cursor.close()
                self.cursor = None  # type: ignore[assignment]

    return SharedDatabaseHandler


def apply_updates(
    diffs_df: pd.DataFrame,
    db_path: Path,
    exercise_manager_module,
    connection: sqlite3.Connection,
) -> List[str]:
    if diffs_df.empty:
        logging.info("No updates to apply.")
        return []

    SharedHandler = build_shared_handler(connection)
    original_handler = exercise_manager_module.DatabaseHandler
    exercise_manager_module.DatabaseHandler = SharedHandler
    changed: List[str] = []

    try:
        connection.execute("BEGIN")
        clean_df = diffs_df.copy()
        clean_df = clean_df.where(pd.notna(clean_df), None)
        for record in clean_df.to_dict(orient="records"):
            exercise_name = record["exercise_name"]
            current_row = fetch_current_row(connection, exercise_name)
            if not current_row:
                logging.warning("Exercise '%s' not found during apply; skipping.", exercise_name)
                continue
            update_payload = dict(current_row)
            for field in TARGET_FIELDS:
                new_value = record.get(f"{field}_new")
                update_payload[field] = new_value if new_value else None
            exercise_manager_module.ExerciseManager.save_exercise(update_payload)
            changed.append(exercise_name)
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        exercise_manager_module.DatabaseHandler = original_handler
    return changed


def post_apply_checks(connection: sqlite3.Connection, sample_names: List[str]) -> None:
    if not sample_names:
        logging.info("No sample rows available for post-apply checks.")
        return

    from utils.normalization import split_csv

    limited = sample_names[:5]
    for name in limited:
        row = connection.execute(
            "SELECT advanced_isolated_muscles FROM exercises WHERE exercise_name = ? COLLATE NOCASE",
            (name,),
        ).fetchone()
        iso_rows = connection.execute(
            "SELECT muscle FROM exercise_isolated_muscles WHERE exercise_name = ? COLLATE NOCASE ORDER BY muscle",
            (name,),
        ).fetchall()
        advanced_tokens = split_csv(row["advanced_isolated_muscles"] if row else None)
        mapped_tokens = [entry["muscle"] for entry in iso_rows]
        logging.info(
            "Post-check '%s': advanced=%s | mapped=%s",
            name,
            advanced_tokens,
            mapped_tokens,
        )

    null_counts = connection.execute(
        """
        SELECT
            SUM(CASE WHEN primary_muscle_group IS NULL THEN 1 ELSE 0 END) AS primary_nulls,
            SUM(CASE WHEN secondary_muscle_group IS NULL THEN 1 ELSE 0 END) AS secondary_nulls,
            SUM(CASE WHEN tertiary_muscle_group IS NULL THEN 1 ELSE 0 END) AS tertiary_nulls,
            SUM(CASE WHEN advanced_isolated_muscles IS NULL THEN 1 ELSE 0 END) AS advanced_nulls
        FROM exercises
        """
    ).fetchone()
    logging.info(
        "Null checks -> primary=%s secondary=%s tertiary=%s advanced=%s",
        null_counts["primary_nulls"],
        null_counts["secondary_nulls"],
        null_counts["tertiary_nulls"],
        null_counts["advanced_nulls"],
    )


def build_preview(
    db_df: pd.DataFrame,
    merge_df: pd.DataFrame,
    wiki_df: pd.DataFrame,
    *,
    skip_ambiguous: bool,
) -> PreviewResult:
    merge_map = build_source_map(merge_df)
    wiki_map = build_source_map(wiki_df)

    diffs_df, field_change_counts, missing_in_db, curation_records, ambiguous_rows, skipped_rows = build_proposed_updates(
        db_df,
        merge_map,
        wiki_map,
        skip_ambiguous=skip_ambiguous,
    )

    return PreviewResult(
        diffs_df=diffs_df,
        total_exercises=len(db_df),
        changed_rows=len(diffs_df),
        field_change_counts=field_change_counts,
        missing_in_db=[name for name in missing_in_db if name],
        ambiguous_rows=ambiguous_rows,
        skipped_rows=skipped_rows,
        curation_records=curation_records,
    )


def main(argv: Optional[Sequence[str]] = None) -> None:
    args = parse_args(argv)
    setup_logging()

    if args.db_path:
        os.environ["DB_FILE"] = str(Path(args.db_path).resolve())

    from utils import config as project_config
    import utils.exercise_manager as exercise_manager_module

    db_path = Path(project_config.DB_FILE).resolve()
    logs_dir = Path(project_config.LOGS_DIR)
    musclewiki_path = (
        Path(args.musclewiki_csv)
        if args.musclewiki_csv
        else Path(project_config.DATA_DIR) / "Database_backup" / "musclewiki_exercises_csv.csv"
    )
    merge_preview_path = (
        Path(args.merge_preview_csv)
        if args.merge_preview_csv
        else Path(project_config.DATA_DIR) / "Database_backup" / "merge_preview.csv"
    )

    merge_df = load_merge_preview_dataframe(merge_preview_path)
    musclewiki_df = load_musclewiki_dataframe(musclewiki_path)

    connection = configure_sqlite_connection(db_path)
    try:
        db_df = load_db_snapshot(connection)
    finally:
        connection.close()

    preview = build_preview(db_df, merge_df, musclewiki_df, skip_ambiguous=args.skip_ambiguous)
    alias_path = generate_alias_candidate_report(db_df, merge_df, musclewiki_df, logs_dir)

    logging.info("Exercises scanned: %s", preview.total_exercises)
    logging.info("Exercises with changes: %s", preview.changed_rows)
    for field, count in preview.field_change_counts.items():
        logging.info("%s changes: %s", field, count)

    if preview.ambiguous_rows:
        logging.info(
            "Ambiguous rows detected: %s (skipped=%s)",
            preview.ambiguous_rows,
            preview.skipped_rows,
        )

    if preview.missing_in_db:
        logging.info("CSV entries missing in DB (showing up to 10): %s", preview.missing_in_db[:10])

    if alias_path:
        logging.info("Alias candidate suggestions exported to %s", alias_path)

    if not preview.diffs_df.empty:
        preview_path = export_preview(preview.diffs_df, logs_dir)
        logging.info("Preview exported to %s", preview_path)
        print_preview(preview.diffs_df, limit=args.limit)
    else:
        logging.info("No differences detected; nothing to preview.")

    curation_path = export_curation(preview.curation_records, logs_dir)
    if curation_path:
        logging.info("Curation issues logged to %s", curation_path)

    if not args.apply:
        logging.info("Dry run complete. Re-run with --apply to persist changes.")
        return

    if preview.diffs_df.empty:
        logging.info("No updates to apply.")
        return

    backup_path = copy_database_backup(db_path, logs_dir)
    connection = configure_sqlite_connection(db_path)
    try:
        changed_names = apply_updates(preview.diffs_df, db_path, exercise_manager_module, connection)
        post_apply_checks(connection, changed_names)
    finally:
        connection.close()

    logging.info(
        "Applied updates for %s exercises. Backup stored at %s",
        len(changed_names),
        backup_path,
    )


if __name__ == "__main__":
    main()
