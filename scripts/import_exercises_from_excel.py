#!/usr/bin/env python3
"""Excel to SQLite merge utility for Hypertrophy-Toolbox exercises."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import platform
import re
import shutil
import sqlite3
import sys
from dataclasses import dataclass
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple, Union

import pandas as pd

# Repository-relative defaults
REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_EXCEL = str((REPO_ROOT / "data" / "musclewiki_exercises.xlsx").resolve())
DEFAULT_DB = str((REPO_ROOT / "data" / "database.db").resolve())
DEFAULT_MAX_PREVIEW = 20
DOCS_DIR = REPO_ROOT / "docs"

SheetArg = Union[int, str]


# Exceptions
class MergeError(Exception):
    """Base class for merge related errors."""


class DuplicateNameError(MergeError):
    """Raised when duplicates prevent index creation."""

    def __init__(self, message: str, duplicates: Sequence["DuplicateGroup"]):
        super().__init__(message)
        self.duplicates = duplicates


@dataclass
class DuplicateGroup:
    normalized_name: str
    raw_names: List[str]
    rowids: List[int]


@dataclass
class MergeOptions:
    excel_path: Path
    db_path: Path
    sheet: Optional[SheetArg]
    nocase: bool
    update_only: bool
    dry_run: bool
    preview_csv: Optional[Path]
    backup_path: Optional[Path]
    max_preview: int
    raw_args: List[str]


@dataclass
class RowResult:
    normalized_name: str
    original_name: str
    intended_action: str  # insert, update, skip, noop
    changes: Dict[str, Tuple[Any, Any]]
    values_for_sql: Dict[str, Any]


@dataclass
class RunSummary:
    dry_run: bool
    intended_inserts: int
    intended_updates: int
    intended_skips: int
    intended_noops: int
    applied_inserts: int
    applied_updates: int
    conflicts: int


@dataclass
class RunArtifacts:
    preview_md: Optional[Path]
    preview_csv: Optional[Path]
    conflicts_md: Optional[Path]


@dataclass
class MergeContext:
    options: MergeOptions
    repo_root: Path = REPO_ROOT
    docs_dir: Path = DOCS_DIR


def _titlecase_preserve(value: Any) -> str:
    return " ".join(str(value).split()).title()


def canon_map(val: Any, mapping: Dict[str, str]) -> Optional[str]:
    if val is None:
        return None
    if isinstance(val, float) and pd.isna(val):
        return None
    key = str(val).strip().lower()
    if not key:
        return None
    return mapping.get(key, _titlecase_preserve(val))


def _equip_preclean(value: str) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    text = text.replace("—", "-").replace("–", "-")
    text = text.replace("_", " ")
    text = text.lower()
    text = text.replace("medicineball", "medicine ball")
    text = text.replace("bosuball", "bosu ball")
    text = text.replace("smithmachine", "smith machine")
    text = " ".join(text.split())
    return text


_SMITH_PAT = re.compile(r"\bsmith\b")
_MACHINE_PAT = re.compile(r"\bmachine\b")


def classify_equipment(raw: Any) -> Optional[str]:
    """Return canonical categories for equipment with precedence for Smith machines."""
    if raw is None or (isinstance(raw, str) and not raw.strip()):
        return None
    cleaned = _equip_preclean(raw)
    if cleaned is None:
        return None
    if _SMITH_PAT.search(cleaned):
        return "Smith_Machine"
    if _MACHINE_PAT.search(cleaned):
        return "Machine"
    return raw


CANON = globals().get("CANON", {})
CANON.setdefault("force", {}).update({
    "push": "Push",
    "pull": "Pull",
    "static": "Hold",
    "hold": "Hold",
    "isometric": "Hold",
})
CANON.setdefault("mechanic", {}).update({
    "compound": "Compound",
    "multi-joint": "Compound",
    "isolation": "Isolation",
    "single-joint": "Isolation",
})
CANON.setdefault("difficulty", {}).update({
    "novice": "Beginner",
    "beginner": "Beginner",
    "intermediate": "Intermediate",
    "advanced": "Advanced",
    "expert": "Advanced",
})
CANON.setdefault("equipment", {})
CANON["equipment"].update({
    # Gear
    "barbell": "Barbell",
    "ez bar": "Barbell",
    "trap bar": "Barbell",
    "dumbbell": "Dumbbells",
    "dumbbells": "Dumbbells",
    "db": "Dumbbells",
    "kettlebell": "Kettlebells",
    "kettlebells": "Kettlebells",
    "kb": "Kettlebells",
    "cable": "Cables",
    "cables": "Cables",
    "pulley": "Cables",
    "machine": "Machine",
    "leg press": "Machine",
    "band": "Band",
    "resistance band": "Band",
    "bands": "Band",
    "bodyweight": "Bodyweight",
    "no equipment": "Bodyweight",
    "plate": "Plate",
    "weight plate": "Plate",
    "bosu": "Bosu Ball",
    "bosu ball": "Bosu Ball",
    "bosu-ball": "Bosu Ball",
    "medicine ball": "Medicine_Ball",
    "med ball": "Medicine_Ball",
    "medicine-ball": "Medicine_Ball",
    "medicineball": "Medicine_Ball",
    "pole": "Pole",
    "stick": "Pole",
    "smith machine": "Smith_Machine",
    "smith-machine": "Smith_Machine",
    "smith_machine": "Smith_Machine",
    "trx": "TRX",
    "vitruvian": "Vitruvian",
    "bosu ball": "Bosu_Ball",
    "bosu-ball": "Bosu_Ball",
    "bosu_ball": "Bosu_Ball",
    # Categories retained as Equipment
    "yoga": "Yoga",
    "recovery": "Recovery",
    "stretches": "Stretches",
    "cardio": "Cardio",
})


def canonicalize_enums(df: pd.DataFrame) -> pd.DataFrame:
    for column, mapping in CANON.items():
        if column not in df.columns:
            continue

        def _convert(value: Any) -> Optional[str]:
            if value is None:
                return None
            if isinstance(value, float) and pd.isna(value):
                return None
            if isinstance(value, str) and not value.strip():
                return None
            return canon_map(value, mapping)

        df[column] = df[column].map(_convert)
    return df


def report_unknowns(df: pd.DataFrame, column: str, mapping: Dict[str, str]) -> None:
    if column not in df.columns:
        return
    series = df[column].dropna()
    if series.empty:
        return
    observed = set(str(value).strip().lower() for value in series if str(value).strip())
    known = set(mapping.keys()) | {str(val).strip().lower() for val in mapping.values()}
    unknown = sorted(value for value in observed if value not in known)
    if unknown:
        excerpt = unknown[:10]
        suffix = " ..." if len(unknown) > 10 else ""
        print(
            f"[WARN] {column}: {len(unknown)} unrecognized values -> {excerpt}{suffix}"
        )


def normalize_name(value: Any) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    text = " ".join(text.split())
    text = text.replace("–", "-").replace("—", "-")
    return text


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_sheet_arg(raw: Optional[str]) -> Optional[SheetArg]:
    if raw is None:
        return None
    try:
        return int(raw)
    except (TypeError, ValueError):
        return raw


def ensure_docs_basics(docs_dir: Path) -> None:
    docs_dir.mkdir(parents=True, exist_ok=True)
    decisions_path = docs_dir / "DECISIONS.md"
    if not decisions_path.exists():
        decisions_path.write_text(
            "# Exercise Import Decisions\n\n"
            "This document captures the non-negotiable rules for the Excel to SQLite merge utility.\n\n"
            "- **Normalization rules**: Trim leading/trailing whitespace, collapse internal whitespace to a single space, and normalize endash/emdash characters to the ASCII hyphen before any comparisons.\n"
            "- **Exact name matching**: Import logic only merges rows whose normalized `exercise_name` strings are identical. No fuzzy, partial, or substring matching is permitted.\n"
            "- **Empty cell handling**: Blank strings and missing values coming from Excel are treated as nulls and never overwrite populated database fields.\n"
            "- **Case sensitivity flag**: `--nocase` enforces a `COLLATE NOCASE` uniqueness constraint; when omitted, uniqueness is strictly case-sensitive.\n"
            "- **Update-only flag**: `--update-only` converts unmatched Excel rows into skipped entries instead of inserts.\n"
            "- **Default paths**: Unless overridden, the tool reads from `data/musclewiki_exercises.xlsx`, writes to `data/database.db`, and emits Markdown artifacts in `docs/`.\n",
            encoding="utf-8",
        )
    import_runs_path = docs_dir / "IMPORT_RUNS.md"
    if not import_runs_path.exists():
        import_runs_path.write_text(
            "# Exercise Import Run Log\n\n"
            "This file is append-only. Each run of `scripts/import_exercises_from_excel.py` should add a new section with timestamped metadata, summary counts, file hashes, and artifact paths.\n",
            encoding="utf-8",
        )


def load_excel_dataframe(excel_path: Path, sheet: Optional[SheetArg]) -> pd.DataFrame:
    try:
        df = pd.read_excel(excel_path, sheet_name=sheet if sheet is not None else 0, engine="openpyxl")
    except FileNotFoundError as exc:
        raise MergeError(f"Excel file not found: {excel_path}") from exc
    except ValueError as exc:
        raise MergeError(f"Failed to open Excel sheet '{sheet}': {exc}") from exc

    if "exercise_name" not in df.columns:
        available = ", ".join(str(col) for col in df.columns)
        raise MergeError(
            "Excel file must contain an 'exercise_name' column. Available columns: "
            f"{available}"
        )

    df = df.copy()
    df["exercise_name_original"] = df["exercise_name"]
    df["_normalized_name"] = df["exercise_name"].apply(normalize_name)
    df = df[df["_normalized_name"].notna()]
    df = df.drop_duplicates(subset=["_normalized_name"], keep="last")
    df["exercise_name"] = df["_normalized_name"].astype(str)
    df = df.drop(columns=["_normalized_name"])
    if "equipment" in df.columns:
        df["equipment"] = df["equipment"].map(classify_equipment)
    df = canonicalize_enums(df)
    if {"exercise_name", "equipment"}.issubset(df.columns):
        smith_name_mask = (
            df["exercise_name"].astype(str).str.contains("smith", case=False, na=False)
            & df["exercise_name"].astype(str).str.contains("machine", case=False, na=False)
        )
        smith_fix_mask = smith_name_mask & (df["equipment"] != "Smith_Machine")
        if smith_fix_mask.any():
            df.loc[smith_fix_mask, "equipment"] = "Smith_Machine"
    for column in ("force", "mechanic", "difficulty", "equipment"):
        report_unknowns(df, column, CANON.get(column, {}))
    df = df.reset_index(drop=True)
    return df


def clean_cell(value: Any) -> Optional[Any]:
    if value is None:
        return None
    if isinstance(value, float) and pd.isna(value):
        return None
    if isinstance(value, (pd.Series, pd.DataFrame)):
        return None
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return None
        return stripped
    if pd.isna(value):
        return None
    return value


def get_table_columns(conn: sqlite3.Connection, table: str) -> List[str]:
    cursor = conn.execute(f"PRAGMA table_info({table})")
    columns = [row[1] for row in cursor.fetchall()]
    if not columns:
        raise MergeError(f"Table '{table}' does not exist in the database")
    return columns


def fetch_existing_rows(conn: sqlite3.Connection, columns: Sequence[str]) -> List[Dict[str, Any]]:
    cols_sql = ", ".join(["rowid"] + list(columns))
    cursor = conn.execute(f"SELECT {cols_sql} FROM exercises")
    rows = []
    for record in cursor.fetchall():
        row = {column: record[idx + 1] for idx, column in enumerate(columns)}
        row["rowid"] = record[0]
        rows.append(row)
    return rows


def detect_duplicate_groups(rows: Sequence[Dict[str, Any]], nocase: bool) -> List[DuplicateGroup]:
    groups: Dict[str, List[Dict[str, Any]]] = {}
    for row in rows:
        name = row.get("exercise_name")
        if name is None:
            continue
        key = name.casefold() if nocase and isinstance(name, str) else name
        groups.setdefault(key, []).append(row)
    duplicates: List[DuplicateGroup] = []
    for candidates in groups.values():
        if len(candidates) <= 1:
            continue
        normalized = normalize_name(candidates[0].get("exercise_name")) or ""
        duplicates.append(
            DuplicateGroup(
                normalized_name=normalized,
                raw_names=[str(item.get("exercise_name")) for item in candidates],
                rowids=[int(item.get("rowid", 0)) for item in candidates],
            )
        )
    return duplicates


def ensure_unique_index(conn: sqlite3.Connection, nocase: bool, dry_run: bool) -> None:
    index_name = "idx_exercises_name_nocase" if nocase else "idx_exercises_name"
    collate_sql = " COLLATE NOCASE" if nocase else ""
    if dry_run:
        return
    conn.execute(
        f"CREATE UNIQUE INDEX IF NOT EXISTS {index_name} ON exercises(exercise_name{collate_sql})"
    )


def build_upsert_sql(data_columns: Sequence[str]) -> str:
    non_key_cols = [col for col in data_columns if col != "exercise_name"]
    placeholders = ", ".join(["?"] * len(data_columns))
    columns_sql = ", ".join(data_columns)
    if non_key_cols:
        update_fragments = []
        for column in non_key_cols:
            update_fragments.append(
                f"{column} = COALESCE(excluded.{column}, exercises.{column})"
            )
        update_sql = ", ".join(update_fragments)
        return (
            f"INSERT INTO exercises ({columns_sql}) VALUES ({placeholders}) "
            f"ON CONFLICT(exercise_name) DO UPDATE SET {update_sql}"
        )
    return (
        f"INSERT INTO exercises ({columns_sql}) VALUES ({placeholders}) "
        f"ON CONFLICT(exercise_name) DO NOTHING"
    )


def classify_rows(
    dataframe: pd.DataFrame,
    existing_rows: Sequence[Dict[str, Any]],
    data_columns: Sequence[str],
    options: MergeOptions,
) -> Tuple[List[RowResult], Dict[str, Dict[str, Any]]]:
    existing_map: Dict[str, Dict[str, Any]] = {}
    normalized_to_row: Dict[str, Dict[str, Any]] = {}
    for row in existing_rows:
        existing_name = normalize_name(row.get("exercise_name"))
        if existing_name is None:
            continue
        key = existing_name.casefold() if options.nocase else existing_name
        existing_map[key] = row
        normalized_to_row[existing_name] = row

    results: List[RowResult] = []
    for _, frame_row in dataframe.iterrows():
        normalized_name = frame_row["exercise_name"]
        original_name = frame_row.get("exercise_name_original", normalized_name)
        key = normalized_name.casefold() if options.nocase else normalized_name
        existing = existing_map.get(key)
        changes: Dict[str, Tuple[Any, Any]] = {}
        values_for_sql: Dict[str, Any] = {"exercise_name": normalized_name}

        if existing is not None:
            existing_name = existing.get("exercise_name")
            if existing_name != normalized_name:
                changes["exercise_name"] = (existing_name, normalized_name)

        for column in data_columns:
            if column == "exercise_name":
                continue
            new_value = clean_cell(frame_row.get(column))
            values_for_sql[column] = new_value
            if existing is None:
                if new_value is not None:
                    changes[column] = (None, new_value)
            else:
                old_value = existing.get(column)
                if new_value is None:
                    continue
                if old_value != new_value:
                    changes[column] = (old_value, new_value)

        if existing is None and options.update_only:
            results.append(
                RowResult(
                    normalized_name=normalized_name,
                    original_name=original_name,
                    intended_action="skip",
                    changes={},
                    values_for_sql=values_for_sql,
                )
            )
            continue

        if existing is None:
            results.append(
                RowResult(
                    normalized_name=normalized_name,
                    original_name=original_name,
                    intended_action="insert",
                    changes=changes,
                    values_for_sql=values_for_sql,
                )
            )
            continue

        if not changes:
            results.append(
                RowResult(
                    normalized_name=normalized_name,
                    original_name=original_name,
                    intended_action="noop",
                    changes={},
                    values_for_sql=values_for_sql,
                )
            )
            continue

        results.append(
            RowResult(
                normalized_name=normalized_name,
                original_name=original_name,
                intended_action="update",
                changes=changes,
                values_for_sql=values_for_sql,
            )
        )

    return results, normalized_to_row


def summarize_results(results: Sequence[RowResult], dry_run: bool) -> RunSummary:
    inserts = sum(1 for row in results if row.intended_action == "insert")
    updates = sum(1 for row in results if row.intended_action == "update")
    skips = sum(1 for row in results if row.intended_action == "skip")
    noops = sum(1 for row in results if row.intended_action == "noop")
    applied_inserts = 0 if dry_run else inserts
    applied_updates = 0 if dry_run else updates
    return RunSummary(
        dry_run=dry_run,
        intended_inserts=inserts,
        intended_updates=updates,
        intended_skips=skips,
        intended_noops=noops,
        applied_inserts=applied_inserts,
        applied_updates=applied_updates,
        conflicts=0,
    )


def ensure_directory(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def write_preview_csv(csv_path: Path, results: Sequence[RowResult], data_columns: Sequence[str]) -> None:
    ensure_directory(csv_path)
    headers = ["exercise_name", "action", "excel_original_name"]
    tracked_columns = ["exercise_name"] + [col for col in data_columns if col != "exercise_name"]
    diff_headers = [f"{column}_diff" for column in tracked_columns]
    headers.extend(diff_headers)
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers)
        writer.writeheader()
        for row in results:
            if row.intended_action == "noop":
                continue
            record: Dict[str, Any] = {
                "exercise_name": row.normalized_name,
                "action": row.intended_action,
                "excel_original_name": row.original_name,
            }
            for column, header in zip(tracked_columns, diff_headers):
                change = row.changes.get(column)
                record[header] = "" if change is None else f"{change[0]} -> {change[1]}"
            writer.writerow(record)


def write_preview_md(
    path: Path,
    summary: RunSummary,
    results: Sequence[RowResult],
    max_preview: int,
    preview_csv: Optional[Path],
    near_duplicates: Sequence[Tuple[str, str, float]],
) -> None:
    ensure_directory(path)
    timestamp = dt.datetime.now().isoformat(timespec="seconds")
    lines: List[str] = []
    lines.append(f"# Excel Merge Preview ({timestamp})")
    lines.append("")
    lines.append("- would_insert: {0}".format(summary.intended_inserts))
    lines.append("- would_update: {0}".format(summary.intended_updates))
    lines.append("- skipped: {0}".format(summary.intended_skips))
    lines.append("- unchanged: {0}".format(summary.intended_noops))
    if preview_csv is not None:
        lines.append(f"- preview_csv: `{preview_csv}`")
    lines.append("")
    lines.append(f"Showing up to {max_preview} rows:")
    lines.append("")
    table_rows: List[RowResult] = [row for row in results if row.intended_action != "noop"]
    table_rows = table_rows[:max_preview]
    if table_rows:
        lines.append("| exercise_name | action | changes |")
        lines.append("| --- | --- | --- |")
        for row in table_rows:
            change_summary = "; ".join(
                f"{column}: {old} -> {new}" for column, (old, new) in row.changes.items()
            ) or "-"
            lines.append(
                f"| {row.normalized_name} | {row.intended_action} | {change_summary} |"
            )
    else:
        lines.append("No rows require inserts or updates.")
    if near_duplicates:
        lines.append("")
        lines.append("## Near-duplicate suspects")
        for source, target, ratio in near_duplicates[:25]:
            lines.append(f"- `{source}` vs `{target}` (similarity {ratio:.2f})")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_conflicts_md(path: Path, duplicates: Sequence[DuplicateGroup], nocase: bool) -> None:
    ensure_directory(path)
    timestamp = dt.datetime.now().isoformat(timespec="seconds")
    mode = "NOCASE" if nocase else "CASE"
    lines: List[str] = []
    lines.append(f"# Exercise Name Conflicts ({timestamp})")
    lines.append("")
    lines.append(f"Detected duplicates under {mode} uniqueness constraint.")
    lines.append("")
    for dup in duplicates:
        lines.append(f"## `{dup.normalized_name}`")
        lines.append("- rowids: {0}".format(", ".join(str(rid) for rid in dup.rowids)))
        lines.append("- names: {0}".format(", ".join(f"`{name}`" for name in dup.raw_names)))
        lines.append("")
    lines.append("## Suggested fixes")
    lines.append("- Review the listed rows and consolidate duplicates manually.")
    lines.append("- Ensure the intended canonical `exercise_name` remains unique.")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def clear_conflicts_md(path: Path) -> None:
    if path.exists():
        path.unlink()


def append_import_run(
    path: Path,
    summary: RunSummary,
    options: MergeOptions,
    excel_hash: str,
    db_hash_before: str,
    db_hash_after: Optional[str],
    artifacts: RunArtifacts,
) -> None:
    ensure_directory(path)
    timestamp = dt.datetime.now().isoformat(timespec="seconds")
    args_line = " ".join(options.raw_args) if options.raw_args else "<no-args>"
    python_version = platform.python_version()
    pandas_version = pd.__version__
    summary_line = (
        f"would_insert={summary.intended_inserts}, would_update={summary.intended_updates}, "
        f"skipped={summary.intended_skips}, conflicts={summary.conflicts}"
    )
    applied_line = (
        f"applied_insert={summary.applied_inserts}, applied_update={summary.applied_updates}"
    )
    suggested_commit = (
        "chore: import exercises from Excel (dry-run)"
        if summary.dry_run
        else "chore: import exercises from Excel"
    )
    lines = [
        f"## {timestamp}",
        "",
        f"- **Args:** `{args_line}`",
        f"- **excel_sha256:** `{excel_hash}`",
        f"- **db_sha256_before:** `{db_hash_before}`",
    ]
    if db_hash_after is not None:
        lines.append(f"- **db_sha256_after:** `{db_hash_after}`")
    lines.extend(
        [
            f"- **Python:** {python_version}",
            f"- **pandas:** {pandas_version}",
            f"- **Summary:** {summary_line}",
            f"- **Applied:** {applied_line}",
            f"- **Artifacts:** preview_csv={(artifacts.preview_csv or 'None')}, "
            f"preview_md={(artifacts.preview_md or 'None')}, conflicts_md={(artifacts.conflicts_md or 'None')}",
            f"- **Suggested commit:** {suggested_commit}",
            "",
        ]
    )
    with path.open("a", encoding="utf-8") as handle:
        handle.write("\n".join(lines) + "\n")


def find_near_duplicates(
    incoming_names: Iterable[str], existing_names: Iterable[str]
) -> List[Tuple[str, str, float]]:
    existing_list = list(dict.fromkeys(existing_names))
    incoming_list = list(dict.fromkeys(incoming_names))
    if not incoming_list or not existing_list:
        return []
    if len(incoming_list) * len(existing_list) > 50_000:
        return []
    suspects: List[Tuple[str, str, float]] = []
    for source in incoming_list:
        for target in existing_list:
            if source == target:
                continue
            ratio = SequenceMatcher(a=source, b=target).ratio()
            if ratio >= 0.9:
                suspects.append((source, target, ratio))
    suspects.sort(key=lambda item: (-item[2], item[0], item[1]))
    return suspects[:50]


def run_merge(context: MergeContext) -> Tuple[RunSummary, RunArtifacts]:
    options = context.options
    docs_dir = context.docs_dir
    ensure_docs_basics(docs_dir)

    if not options.excel_path.exists():
        raise MergeError(f"Excel file not found: {options.excel_path}")
    if not options.db_path.exists():
        raise MergeError(f"SQLite DB not found: {options.db_path}")

    dataframe = load_excel_dataframe(options.excel_path, options.sheet)

    conn = sqlite3.connect(str(options.db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        columns = get_table_columns(conn, "exercises")
        if "exercise_name" not in columns:
            raise MergeError("exercises table must include an exercise_name column")
        shared_columns = [col for col in dataframe.columns if col in columns]
        if "exercise_name" not in shared_columns:
            shared_columns.insert(0, "exercise_name")
        else:
            shared_columns = ["exercise_name"] + [col for col in shared_columns if col != "exercise_name"]

        existing_rows = fetch_existing_rows(conn, columns)
        duplicates = detect_duplicate_groups(existing_rows, options.nocase)
        conflicts_path = docs_dir / "CONFLICTS.md"
        if duplicates:
            write_conflicts_md(conflicts_path, duplicates, options.nocase)
            summary = summarize_results([], options.dry_run)
            summary.conflicts = len(duplicates)
            raise DuplicateNameError("Duplicate exercise_name values detected", duplicates)
        clear_conflicts_md(conflicts_path)

        ensure_unique_index(conn, options.nocase, options.dry_run)

        row_results, existing_normalized = classify_rows(
            dataframe, existing_rows, shared_columns, options
        )

        summary = summarize_results(row_results, options.dry_run)
        artifacts = RunArtifacts(preview_md=None, preview_csv=None, conflicts_md=None)

        if options.dry_run and {"exercise_name", "equipment"}.issubset(dataframe.columns):
            smith_name_mask = (
                dataframe["exercise_name"].astype(str).str.contains("smith", case=False, na=False)
                & dataframe["exercise_name"].astype(str).str.contains("machine", case=False, na=False)
            )
            remaining = dataframe.loc[
                smith_name_mask & (dataframe["equipment"] != "Smith_Machine"),
                ["exercise_name", "equipment"],
            ]
            if not remaining.empty:
                print(
                    f"[WARN] {len(remaining)} Smith-named exercises are not 'Smith_Machine'. Top examples:"
                )
                print(remaining.head(10).to_string(index=False))

        if options.dry_run:
            preview_csv_path = options.preview_csv
            if preview_csv_path is not None:
                write_preview_csv(preview_csv_path, row_results, shared_columns)
                artifacts.preview_csv = preview_csv_path
            preview_md_path = docs_dir / "PREVIEW.md"
            near_duplicates = find_near_duplicates(
                incoming_names=[row.normalized_name for row in row_results],
                existing_names=existing_normalized.keys(),
            )
            write_preview_md(
                preview_md_path,
                summary,
                row_results,
                options.max_preview,
                preview_csv_path,
                near_duplicates,
            )
            artifacts.preview_md = preview_md_path
            artifacts.conflicts_md = None
            return summary, artifacts

        if options.backup_path is not None:
            ensure_directory(options.backup_path)
            shutil.copy2(options.db_path, options.backup_path)

        upsert_columns = [col for col in shared_columns if col in dataframe.columns or col == "exercise_name"]
        sql = build_upsert_sql(upsert_columns)
        params: List[Tuple[Any, ...]] = []
        for row in row_results:
            if row.intended_action not in {"insert", "update"}:
                continue
            ordered = [row.values_for_sql.get(column) for column in upsert_columns]
            params.append(tuple(ordered))
        if params:
            conn.execute("BEGIN")
            conn.executemany(sql, params)
            conn.commit()
        artifacts.preview_md = None
        artifacts.preview_csv = None
        artifacts.conflicts_md = None
        return summary, artifacts
    finally:
        conn.close()


def perform_run(options: MergeOptions) -> int:
    context = MergeContext(options=options)
    excel_hash = sha256_of(options.excel_path)
    db_hash_before = sha256_of(options.db_path)
    try:
        summary, artifacts = run_merge(context)
        db_hash_after = None
        if not summary.dry_run:
            db_hash_after = sha256_of(options.db_path)
        import_runs_path = context.docs_dir / "IMPORT_RUNS.md"
        append_import_run(
            import_runs_path,
            summary,
            options,
            excel_hash,
            db_hash_before,
            db_hash_after,
            artifacts,
        )
        return 0
    except DuplicateNameError as exc:
        conflicts_path = context.docs_dir / "CONFLICTS.md"
        append_import_run(
            context.docs_dir / "IMPORT_RUNS.md",
            RunSummary(
                dry_run=options.dry_run,
                intended_inserts=0,
                intended_updates=0,
                intended_skips=0,
                intended_noops=0,
                applied_inserts=0,
                applied_updates=0,
                conflicts=len(exc.duplicates),
            ),
            options,
            excel_hash,
            db_hash_before,
            None,
            RunArtifacts(preview_md=None, preview_csv=None, conflicts_md=conflicts_path),
        )
        print(exc, file=sys.stderr)
        print(f"See {conflicts_path} for conflict details.", file=sys.stderr)
        return 1
    except MergeError as exc:
        print(exc, file=sys.stderr)
        return 1


def run_self_test() -> int:
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        db_path = tmp_path / "test.db"
        conn = sqlite3.connect(db_path)
        conn.execute(
            "CREATE TABLE exercises (exercise_name TEXT PRIMARY KEY, equipment TEXT, difficulty TEXT)"
        )
        conn.execute(
            "INSERT INTO exercises (exercise_name, equipment, difficulty) VALUES (?, ?, ?)",
            ("squat", "barbell", "medium"),
        )
        conn.commit()
        conn.close()

        excel_path = tmp_path / "input.xlsx"
        df = pd.DataFrame(
            [
                {"exercise_name": "squat", "equipment": "", "difficulty": "hard"},
                {"exercise_name": "band squat", "equipment": "bands", "difficulty": "easy"},
                {"exercise_name": " squat ", "equipment": None, "difficulty": None},
            ]
        )
        df.to_excel(excel_path, index=False)

        preview_csv = tmp_path / "preview.csv"
        options = MergeOptions(
            excel_path=excel_path,
            db_path=db_path,
            sheet=None,
            nocase=False,
            update_only=False,
            dry_run=True,
            preview_csv=preview_csv,
            backup_path=None,
            max_preview=10,
            raw_args=["--dry-run"],
        )
        exit_code = perform_run(options)
        if exit_code != 0:
            raise RuntimeError("Dry-run self-test failed")
        if not preview_csv.exists():
            raise RuntimeError("Preview CSV was not generated during dry-run")

        options = MergeOptions(
            excel_path=excel_path,
            db_path=db_path,
            sheet=None,
            nocase=False,
            update_only=False,
            dry_run=False,
            preview_csv=None,
            backup_path=None,
            max_preview=10,
            raw_args=[],
        )
        exit_code = perform_run(options)
        if exit_code != 0:
            raise RuntimeError("Real-run self-test failed")
        conn = sqlite3.connect(db_path)
        cursor = conn.execute("SELECT exercise_name, equipment, difficulty FROM exercises ORDER BY exercise_name")
        rows = cursor.fetchall()
        conn.close()
        if len(rows) != 2:
            raise RuntimeError("Expected exactly 2 rows after merge")
        equipment_lookup = {name: equipment for name, equipment, _ in rows}
        if equipment_lookup.get("squat") != "barbell":
            raise RuntimeError("Existing equipment value should remain 'barbell'")
    print("Self-test passed")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Merge exercises from Excel into SQLite")
    parser.add_argument("--excel", default=DEFAULT_EXCEL, help="Path to the Excel (.xlsx) file")
    parser.add_argument("--db", default=DEFAULT_DB, help="Path to the SQLite database")
    parser.add_argument("--sheet", help="Excel sheet name or index", default=None)
    parser.add_argument("--nocase", action="store_true", help="Use case-insensitive uniqueness")
    parser.add_argument(
        "--update-only",
        action="store_true",
        help="Only update existing exercises; skip new names",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Analyze and report without writing to the database",
    )
    parser.add_argument(
        "--preview-csv",
        help="Optional path for a CSV preview report (dry-run)",
    )
    parser.add_argument(
        "--backup",
        help="Optional path for a SQLite backup copy (real run)",
    )
    parser.add_argument(
        "--max-preview",
        type=int,
        default=DEFAULT_MAX_PREVIEW,
        help="Number of rows to show in PREVIEW.md (dry-run)",
    )
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="Run built-in acceptance checks and exit",
    )
    return parser


def parse_options(args: argparse.Namespace) -> MergeOptions:
    excel_path = Path(args.excel)
    db_path = Path(args.db)
    sheet = parse_sheet_arg(args.sheet)
    preview_csv = Path(args.preview_csv) if args.preview_csv else None
    backup_path = Path(args.backup) if args.backup else None
    if args.max_preview <= 0:
        raise MergeError("--max-preview must be positive")
    return MergeOptions(
        excel_path=excel_path,
        db_path=db_path,
        sheet=sheet,
        nocase=args.nocase,
        update_only=args.update_only,
        dry_run=args.dry_run,
        preview_csv=preview_csv,
        backup_path=backup_path,
        max_preview=args.max_preview,
        raw_args=sys.argv[1:],
    )


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    parsed = parser.parse_args(argv)
    if parsed.self_test:
        return run_self_test()
    try:
        options = parse_options(parsed)
    except MergeError as exc:
        print(exc, file=sys.stderr)
        return 1
    return perform_run(options)


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
