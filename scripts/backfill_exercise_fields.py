#!/usr/bin/env python3
"""Rule-based backfill utility for exercise metadata columns."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import re
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple, cast

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = REPO_ROOT / "data" / "database.db"
DOCS_DIR = REPO_ROOT / "docs"
TARGET_COLUMNS = [
    "primary_muscle_group",
    "secondary_muscle_group",
    "tertiary_muscle_group",
    "advanced_isolated_muscles",
    "utility",
    "grips",
    "mechanic",
]


@dataclass
class BackfillOptions:
    db_path: Path
    dry_run: bool
    apply: bool
    preview_csv: Optional[Path]
    limit: Optional[int]


@dataclass
class RowChange:
    exercise_name: str
    changes: Dict[str, Any]
    fill_source: Optional[str]

SQUAT_TOKENS = {"squat", "split squat", "front squat", "hack squat", "leg press", "lunge"}
HINGE_TOKENS = {"deadlift", "rdl", "romanian", "good morning", "hip thrust", "hip hinge"}
HORIZONTAL_PRESS_QUALIFIERS = {"bench", "incline", "decline", "floor"}
VERTICAL_PRESS_TOKENS = {"overhead press", "military press", "shoulder press", "ohp"}
HORIZONTAL_ROW_TOKENS = {"row", "t bar", "seal row", "pendlay"}
VERTICAL_PULL_TOKENS = {"pull up", "chin up", "pulldown", "lat pulldown"}
CURL_TOKENS = {"curl", "preacher", "spider"}
TRICEPS_TOKENS = {
    "skullcrusher",
    "skull crusher",
    "pushdown",
    "tricep pushdown",
    "overhead triceps",
    "triceps extension",
    "tricep extension",
}
CHEST_FLY_TOKENS = {"fly", "pec deck"}
LATERAL_RAISE_TOKENS = {"lateral raise", "side raise"}
REAR_DELT_TOKENS = {"rear delt", "face pull", "reverse fly"}
CALF_TOKENS = {"calf", "calves", "heel raise"}
CORE_TOKENS = {"plank", "crunch", "sit up", "leg raise", "knee raise", "ab rollout", "pallof"}
CARRY_TOKENS = {"carry", "farmer", "yoke"}
LEG_CURL_TOKENS = {"leg curl", "hamstring curl"}
FRONT_RAISE_TOKENS = {"front raise"}
LANDMINE_PRESS_TOKENS = {"landmine press"}
HOLD_DEFAULT_TOKENS = {"hold", "iso", "plank"}
GRIP_SUPINATED_TOKENS = {"underhand", "supinated", "reverse"}
GRIP_PRONATED_TOKENS = {"overhand", "pronated"}
GRIP_NEUTRAL_TOKENS = {"neutral", "hammer", "rope"}
MOBILITY_EQUIPMENT = {"Yoga", "Stretches", "Recovery"}
VALID_MECHANIC_VALUES = {"Compound", "Isolation", "Hold"}


def _norm_name(value: Optional[str]) -> str:
    text = "" if value is None else str(value)
    text = text.lower()
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def near(word_a: str, word_b: str, text: str, max_gap: int = 2) -> bool:
    tokens = re.findall(r"[a-z']+", text)
    positions_a = [idx for idx, token in enumerate(tokens) if token == word_a]
    positions_b = [idx for idx, token in enumerate(tokens) if token == word_b]
    for i in positions_a:
        for j in positions_b:
            if abs(i - j) <= max_gap:
                return True
    return False


def normalize_phrase(value: str) -> str:
    text = _norm_name(value)
    text = text.replace("-", " ").replace("_", " ")
    return " ".join(text.split())


def has_any(text: str, tokens: Iterable[str]) -> bool:
    return any(token in text for token in tokens)


def ensure_directory(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def append_apply_log(
    db_path: Path,
    scanned: int,
    rows_changed: int,
    per_column: Dict[str, int],
    tier2_rows: int,
) -> None:
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    log_path = DOCS_DIR / "IMPORT_RUNS.md"
    timestamp = dt.datetime.now().isoformat(timespec="seconds")
    db_display = str(db_path.resolve())
    filled_counts = {
        "primary": per_column.get("primary_muscle_group", 0),
        "secondary": per_column.get("secondary_muscle_group", 0),
        "tertiary": per_column.get("tertiary_muscle_group", 0),
        "mechanic": per_column.get("mechanic", 0),
        "grips": per_column.get("grips", 0),
        "adv_iso": per_column.get("advanced_isolated_muscles", 0),
        "utility": per_column.get("utility", 0),
    }
    column_summary = ", ".join(f"{key}={value}" for key, value in filled_counts.items())
    lines = [
        f"### Backfill run: {timestamp}",
        "",
        "- Command: backfill_exercise_fields.py --apply",
        f"- DB: {db_display}",
        f"- Rows scanned: {scanned}; Rows changed: {rows_changed}",
        f"- Filled counts: {column_summary}",
        f"- Tier-2 rows: {tier2_rows}",
        "- Notes: NULL-only, idempotent",
        "",
    ]
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write("\n".join(lines) + "\n")


def parse_args(argv: Optional[Sequence[str]] = None) -> BackfillOptions:
    parser = argparse.ArgumentParser(description="Backfill NULL exercise fields with deterministic rules")
    parser.add_argument(
        "--db",
        type=Path,
        default=DEFAULT_DB,
        help="Path to the SQLite database (default: data/database.db)",
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true", help="Preview changes without writing")
    mode.add_argument("--apply", action="store_true", help="Apply updates to the database")
    parser.add_argument(
        "--preview-csv",
        type=Path,
        help="Optional path to write a CSV of proposed changes (only populated keys per row)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Process at most this many NULL-containing rows (for quick tests)",
    )
    args = parser.parse_args(argv)
    return BackfillOptions(
        db_path=args.db,
        dry_run=args.dry_run,
        apply=args.apply,
        preview_csv=args.preview_csv,
        limit=args.limit,
    )


def fetch_rows(conn: sqlite3.Connection, limit: Optional[int]) -> List[sqlite3.Row]:
    columns = ["exercise_name", "equipment", "force"] + TARGET_COLUMNS
    select_clause = ", ".join(columns)
    where_clause = " OR ".join([f"{col} IS NULL" for col in TARGET_COLUMNS])
    sql = f"SELECT {select_clause} FROM exercises WHERE {where_clause} ORDER BY exercise_name"
    if limit is not None and limit > 0:
        sql += " LIMIT ?"
        cursor = conn.execute(sql, (limit,))
    else:
        cursor = conn.execute(sql)
    return cursor.fetchall()


def clean_value(value: Any) -> Optional[Any]:
    if value is None:
        return None
    if isinstance(value, str):
        stripped = value.strip()
        return stripped if stripped else None
    if pd.isna(value):
        return None
    return value


def infer_tier1(row_data: Dict[str, Any]) -> Dict[str, Any]:
    raw_name = row_data.get("exercise_name", "")
    name = normalize_phrase(str(raw_name))
    tokens = name.split()
    equipment = (row_data.get("equipment") or "").strip()
    changes: Dict[str, Any] = {}

    def set_if_null(column: str, value: Optional[str]) -> None:
        if value is None:
            return
        if column == "mechanic" and value not in VALID_MECHANIC_VALUES:
            return
        current = row_data.get(column)
        if current is None or (isinstance(current, str) and not current.strip()):
            changes[column] = value
            row_data[column] = value

    def has_leg_extension(tokens_list: List[str]) -> bool:
        for idx, token in enumerate(tokens_list):
            if token in {"leg", "legs"}:
                for offset in (1, 2):
                    j = idx + offset
                    if j < len(tokens_list) and tokens_list[j] == "extension":
                        return True
        return False

    family = None
    if has_any(name, LANDMINE_PRESS_TOKENS):
        family = "vertical_press"
        set_if_null("primary_muscle_group", "Delts")
        set_if_null("secondary_muscle_group", "Triceps")
        set_if_null("tertiary_muscle_group", "Upper Chest")
        set_if_null("mechanic", "Compound")
    elif has_leg_extension(tokens):
        family = "leg_extension"
        set_if_null("primary_muscle_group", "Quads")
        set_if_null("mechanic", "Isolation")
    elif has_any(name, LEG_CURL_TOKENS):
        family = "leg_curl"
        set_if_null("primary_muscle_group", "Hamstrings")
        set_if_null("mechanic", "Isolation")
    elif has_any(name, FRONT_RAISE_TOKENS):
        family = "front_raise"
        set_if_null("primary_muscle_group", "Anterior Delts")
        set_if_null("mechanic", "Isolation")
    elif has_any(name, SQUAT_TOKENS):
        family = "squat"
        set_if_null("primary_muscle_group", "Quads")
        set_if_null("secondary_muscle_group", "Glutes")
        set_if_null("tertiary_muscle_group", "Hamstrings")
        set_if_null("mechanic", "Compound")
    elif has_any(name, HINGE_TOKENS):
        family = "hinge"
        set_if_null("primary_muscle_group", "Glutes")
        set_if_null("secondary_muscle_group", "Hamstrings")
        set_if_null("tertiary_muscle_group", "Erectors")
        set_if_null("mechanic", "Compound")
    elif ("press" in name or "bench" in name) and has_any(name, HORIZONTAL_PRESS_QUALIFIERS):
        family = "horizontal_press"
        set_if_null("primary_muscle_group", "Chest")
        set_if_null("secondary_muscle_group", "Triceps")
        set_if_null("tertiary_muscle_group", "Anterior Delts")
        set_if_null("mechanic", "Compound")
    elif has_any(name, VERTICAL_PRESS_TOKENS):
        family = "vertical_press"
        set_if_null("primary_muscle_group", "Delts")
        set_if_null("secondary_muscle_group", "Triceps")
        set_if_null("tertiary_muscle_group", "Upper Chest")
        set_if_null("mechanic", "Compound")
    elif has_any(name, HORIZONTAL_ROW_TOKENS):
        family = "horizontal_row"
        set_if_null("primary_muscle_group", "Mid/Upper Back")
        set_if_null("secondary_muscle_group", "Lats")
        set_if_null("tertiary_muscle_group", "Biceps")
        set_if_null("mechanic", "Compound")
    elif has_any(name, VERTICAL_PULL_TOKENS):
        family = "vertical_pull"
        set_if_null("primary_muscle_group", "Lats")
        set_if_null("secondary_muscle_group", "Biceps")
        set_if_null("tertiary_muscle_group", "Mid/Upper Back")
        set_if_null("mechanic", "Compound")
    elif "curl" in name and not has_any(name, LEG_CURL_TOKENS):
        family = "curl"
        set_if_null("primary_muscle_group", "Biceps")
        set_if_null("secondary_muscle_group", "Forearms")
        set_if_null("mechanic", "Isolation")
    elif has_any(name, TRICEPS_TOKENS):
        family = "triceps_iso"
        set_if_null("primary_muscle_group", "Triceps")
        set_if_null("secondary_muscle_group", "Forearms")
        set_if_null("mechanic", "Isolation")
    elif has_any(name, LATERAL_RAISE_TOKENS):
        family = "lateral_raise"
        set_if_null("primary_muscle_group", "Medial Delts")
        set_if_null("secondary_muscle_group", "Upper Traps")
        set_if_null("mechanic", "Isolation")
    elif has_any(name, REAR_DELT_TOKENS):
        family = "rear_delt"
        set_if_null("primary_muscle_group", "Rear Delts")
        set_if_null("secondary_muscle_group", "Rotator Cuff")
        set_if_null("mechanic", "Isolation")
    elif has_any(name, CHEST_FLY_TOKENS):
        family = "chest_fly"
        set_if_null("primary_muscle_group", "Chest")
        set_if_null("secondary_muscle_group", "Anterior Delts")
        set_if_null("mechanic", "Isolation")
    elif "shrug" in name:
        family = "shrug"
        set_if_null("primary_muscle_group", "Upper Traps")
        set_if_null("secondary_muscle_group", "Forearms")
        set_if_null("mechanic", "Isolation")
    elif has_any(name, CALF_TOKENS):
        family = "calf"
        set_if_null("primary_muscle_group", "Calves")
        set_if_null("mechanic", "Isolation")
    elif has_any(name, CORE_TOKENS):
        family = "core"
        set_if_null("primary_muscle_group", "Abs/Core")
        set_if_null("secondary_muscle_group", "Obliques")
        if has_any(name, HOLD_DEFAULT_TOKENS | {"hollow"}):
            set_if_null("mechanic", "Hold")
        else:
            set_if_null("mechanic", "Isolation")
    elif has_any(name, CARRY_TOKENS):
        family = "carry"
        set_if_null("primary_muscle_group", "Traps")
        set_if_null("secondary_muscle_group", "Forearms")
        set_if_null("tertiary_muscle_group", "Core")
        set_if_null("mechanic", "Compound")

    if equipment in MOBILITY_EQUIPMENT:
        set_if_null("utility", "Mobility/Recovery")
        set_if_null("mechanic", "Hold")
    elif equipment == "Cardio":
        set_if_null("utility", "Conditioning")
    else:
        set_if_null("utility", "Strength")

    grips_value = row_data.get("grips")
    if grips_value is None or (isinstance(grips_value, str) and not grips_value.strip()):
        grip_tokens: List[str] = []
        if has_any(name, GRIP_SUPINATED_TOKENS):
            grip_tokens.append("Supinated")
        if has_any(name, GRIP_PRONATED_TOKENS):
            grip_tokens.append("Pronated")
        if has_any(name, GRIP_NEUTRAL_TOKENS):
            grip_tokens.append("Neutral")
        if "wide" in name:
            grip_tokens.append("Wide")
        if "close" in name:
            grip_tokens.append("Close")
        if grip_tokens:
            preferred_order = ["Supinated", "Pronated", "Neutral", "Wide", "Close"]
            ordered = [token for token in preferred_order if token in grip_tokens]
            set_if_null("grips", " / ".join(ordered))

    advanced_value = row_data.get("advanced_isolated_muscles")
    if advanced_value is None or (isinstance(advanced_value, str) and not advanced_value.strip()):
        extras: List[str] = []
        if family in {"horizontal_row", "vertical_pull"}:
            extras.append("Rear Delts")
        if "face pull" in name:
            extras.extend(["Rear Delts", "Rotator Cuff"])
        if family == "lateral_raise":
            extras.append("Supraspinatus")
        if family in {"squat", "hinge"}:
            extras.append("Adductors")
        if family in {"horizontal_press", "vertical_press"}:
            extras.append("Serratus Anterior")
        if extras:
            deduped: List[str] = []
            for item in extras:
                if item not in deduped:
                    deduped.append(item)
            set_if_null("advanced_isolated_muscles", ", ".join(deduped))

    mechanic_value = row_data.get("mechanic")
    if (mechanic_value is None or (isinstance(mechanic_value, str) and not mechanic_value.strip())) and has_any(
        name, HOLD_DEFAULT_TOKENS
    ) and "mechanic" not in changes:
        set_if_null("mechanic", "Hold")

    return changes


def apply_tier2_fallback(df: pd.DataFrame) -> pd.DataFrame:
    candidate_columns = {
        "primary_muscle_group",
        "secondary_muscle_group",
        "tertiary_muscle_group",
        "mechanic",
        "utility",
    }
    if not candidate_columns.intersection(df.columns):
        return df

    if "fill_source" not in df.columns:
        df["fill_source"] = None

    for idx, row in df.iterrows():
        name = _norm_name(row.get("exercise_name"))
        if not name:
            continue

        def set_if_null(column: str, value: Optional[str]) -> None:
            if value is None or column not in df.columns:
                return
            current = row.get(column)
            if pd.isna(current) or (isinstance(current, str) and not current.strip()):
                if column == "mechanic" and value not in VALID_MECHANIC_VALUES:
                    return
                index_key = cast(Any, idx)
                df.at[index_key, column] = value
                df.at[index_key, "fill_source"] = "Tier-2"

        squat_toks = {"squat", "split squat", "front squat", "hack squat", "leg press", "lunge"}
        hinge_toks = {"deadlift", "rdl", "romanian", "good morning", "hip thrust", "hinge"}
        horiz_press_toks = {"bench", "incline", "decline", "floor press"}
        vert_press_toks = {"overhead press", "ohp", "military press", "shoulder press"}
        row_toks = {" row", "t-bar", "seal row", "pendlay"}
        vpull_toks = {"pull-up", "chin-up", "pulldown", "lat pulldown"}
        calf_toks = {"calf", "calves", "heel raise"}
        core_toks = {"plank", "crunch", "sit-up", "sit up", "leg raise", "knee raise", "rollout", "pallof"}

        is_leg_extension = near("leg", "extension", name) or "leg extension" in name
        is_leg_curl = "leg curl" in name or "hamstring curl" in name
        is_triceps_extension = "triceps" in name and "extension" in name
        is_biceps_curl = "curl" in name and not is_leg_curl

        if has_any(name, squat_toks):
            set_if_null("primary_muscle_group", "Quads")
            set_if_null("secondary_muscle_group", "Glutes")
            set_if_null("tertiary_muscle_group", "Hamstrings")
        elif has_any(name, hinge_toks):
            set_if_null("primary_muscle_group", "Glutes")
            set_if_null("secondary_muscle_group", "Hamstrings")
            set_if_null("tertiary_muscle_group", "Erectors")
        elif has_any(name, row_toks) or has_any(name, vpull_toks):
            set_if_null("primary_muscle_group", "Lats")
            set_if_null("secondary_muscle_group", "Biceps")
            set_if_null("tertiary_muscle_group", "Mid/Upper Back")
        elif has_any(name, horiz_press_toks):
            set_if_null("primary_muscle_group", "Chest")
            set_if_null("secondary_muscle_group", "Triceps")
            set_if_null("tertiary_muscle_group", "Anterior Delts")
        elif has_any(name, vert_press_toks):
            set_if_null("primary_muscle_group", "Delts")
            set_if_null("secondary_muscle_group", "Triceps")
            set_if_null("tertiary_muscle_group", "Upper Chest")
        elif is_biceps_curl:
            set_if_null("primary_muscle_group", "Biceps")
            set_if_null("secondary_muscle_group", "Forearms")
        elif is_triceps_extension:
            set_if_null("primary_muscle_group", "Triceps")
            set_if_null("secondary_muscle_group", "Forearms")
        elif is_leg_extension:
            set_if_null("primary_muscle_group", "Quads")
        elif is_leg_curl:
            set_if_null("primary_muscle_group", "Hamstrings")
        elif has_any(name, calf_toks):
            set_if_null("primary_muscle_group", "Calves")
        elif has_any(name, core_toks):
            set_if_null("primary_muscle_group", "Abs/Core")
            set_if_null("secondary_muscle_group", "Obliques")

        if "mechanic" in df.columns:
            current_mech = row.get("mechanic")
            if pd.isna(current_mech) or (isinstance(current_mech, str) and not current_mech.strip()):
                mech_value = None
                if any(t in name for t in ["plank", "hold", "iso"]):
                    mech_value = "Hold"
                elif any(t in name for t in ["curl", "extension", "raise", "fly", "shrug"]):
                    mech_value = "Isolation"
                elif any(t in name for t in ["press", "row", "pull", "squat", "deadlift", "carry", "lunge", "hinge"]):
                    mech_value = "Compound"
                if mech_value in VALID_MECHANIC_VALUES:
                    set_if_null("mechanic", mech_value)

        if "utility" in df.columns:
            current_util = row.get("utility")
            if pd.isna(current_util) or (isinstance(current_util, str) and not current_util.strip()):
                equipment_value = row.get("equipment") or ""
                if equipment_value in {"Yoga", "Stretches", "Recovery"}:
                    set_if_null("utility", "Mobility/Recovery")
                elif equipment_value == "Cardio":
                    set_if_null("utility", "Conditioning")
                else:
                    set_if_null("utility", "Strength")

    return df


def compute_updates(rows: List[sqlite3.Row]) -> Tuple[List[RowChange], Dict[str, int]]:
    if not rows:
        return [], {column: 0 for column in TARGET_COLUMNS}

    originals: List[Dict[str, Any]] = []
    working_records: List[Dict[str, Any]] = []
    tier1_flags: List[bool] = []

    for row in rows:
        base: Dict[str, Any] = {}
        for key in row.keys():
            value = row[key]
            if key in TARGET_COLUMNS:
                base[key] = clean_value(value)
            elif key == "equipment" and isinstance(value, str):
                base[key] = value.strip()
            else:
                base[key] = value
        base["fill_source"] = None
        originals.append(dict(base))
        tier1_changes = infer_tier1(base)
        tier1_flags.append(bool(tier1_changes))
        working_records.append(base)

    df = pd.DataFrame(working_records)
    if df.empty:
        return [], {column: 0 for column in TARGET_COLUMNS}
    if "fill_source" not in df.columns:
        df["fill_source"] = None
    df = apply_tier2_fallback(df)
    final_records = df.to_dict(orient="records")

    processed_rows: List[RowChange] = []
    per_column: Dict[str, int] = {column: 0 for column in TARGET_COLUMNS}

    for original, final, tier1_flag in zip(originals, final_records, tier1_flags):
        updates: Dict[str, Any] = {}
        for column in TARGET_COLUMNS:
            final_value = clean_value(final.get(column))
            original_value = original.get(column)
            if original_value is None and final_value is not None:
                updates[column] = final_value
                per_column[column] += 1
        if updates:
            fill_source = final.get("fill_source")
            if isinstance(fill_source, float) and pd.isna(fill_source):
                fill_source = None
            if fill_source == "Tier-2":
                source_label = "Tier-2"
            else:
                source_label = "Tier-1" if tier1_flag else None
            processed_rows.append(
                RowChange(
                    exercise_name=str(final.get("exercise_name") or original.get("exercise_name")),
                    changes=updates,
                    fill_source=source_label,
                )
            )

    return processed_rows, per_column


def write_preview_csv(path: Path, changes: List[RowChange]) -> None:
    if not changes:
        return
    all_columns = {column for change in changes for column in change.changes}
    ordered_columns = ["exercise_name", "fill_source"] + sorted(all_columns)
    ensure_directory(path)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=ordered_columns)
        writer.writeheader()
        for change in changes:
            row = {
                "exercise_name": change.exercise_name,
                "fill_source": change.fill_source or "",
            }
            for column, value in change.changes.items():
                row[column] = f"NULL -> {value}"
            writer.writerow(row)


def apply_updates(conn: sqlite3.Connection, updates: List[RowChange]) -> None:
    if not updates:
        return
    conn.execute("BEGIN")
    try:
        for change in updates:
            set_clause = ", ".join(f"{column} = ?" for column in change.changes)
            params = list(change.changes.values()) + [change.exercise_name]
            conn.execute(
                f"UPDATE exercises SET {set_clause} WHERE exercise_name = ?",
                params,
            )
        conn.commit()
    except Exception:
        conn.rollback()
        raise


def main(argv: Optional[Sequence[str]] = None) -> int:
    options = parse_args(argv)
    if not options.db_path.exists():
        print(f"Database not found: {options.db_path}")
        return 1

    conn = sqlite3.connect(str(options.db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        rows = fetch_rows(conn, options.limit)
        scanned = len(rows)
        print(f"Scanned rows with NULL targets: {scanned}")
        changes, per_column = compute_updates(rows)
        updated_rows = len(changes)
        tier2_rows = sum(1 for change in changes if change.fill_source == "Tier-2")
        tier1_rows = sum(1 for change in changes if change.fill_source in (None, "Tier-1"))

        if options.dry_run:
            if updated_rows == 0:
                print("No NULL rows matched the Tier-1/Tier-2 rules.")
                if options.preview_csv:
                    print("Preview skipped; no changes to write.")
            else:
                print(f"Rows with inferred updates: {updated_rows}")
                if tier1_rows:
                    print(f"  Tier-1 rows: {tier1_rows}")
                if tier2_rows:
                    print(f"  Tier-2 rows: {tier2_rows}")
                for column, count in per_column.items():
                    if count:
                        print(f"  {column}: {count}")
                if options.preview_csv:
                    write_preview_csv(options.preview_csv, changes)
                    print(f"Preview written to {options.preview_csv}")
            if options.limit is None:
                print(
                    "[INFO] Dry-run executed without --limit; rerunning immediately should report the same counts."
                )
            return 0

        if updated_rows == 0:
            print("No updates identified; database left unchanged.")
            return 0

        apply_updates(conn, changes)
        print(f"Rows updated: {updated_rows}")
        if tier1_rows:
            print(f"  Tier-1 rows: {tier1_rows}")
        if tier2_rows:
            print(f"  Tier-2 rows: {tier2_rows}")
        for column, count in per_column.items():
            if count:
                print(f"  {column}: {count}")
        append_apply_log(options.db_path, scanned, updated_rows, per_column, tier2_rows)
        return 0
    finally:
        conn.close()


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
