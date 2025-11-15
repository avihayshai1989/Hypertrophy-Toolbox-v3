import argparse
import datetime as dt
import os
import re
import shutil
import sqlite3
import sys
import traceback
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional, Sequence, Set, Tuple

try:
    import pandas as pd
except ImportError as exc:  # pragma: no cover - environment guard
    raise SystemExit("pandas is required to run merge_progress.py") from exc

DEFAULT_CSV_PATH = r"C:\\vscondim_code\\exrx\\progress.csv"
DEFAULT_DB_PATH = r"C:\\Users\\aatiya\\IdeaProjects\\Hypertrophy-Toolbox-v3\\data\\database.db"
DEFAULT_LOG_PATH = r"C:\\Users\\aatiya\\IdeaProjects\\Hypertrophy-Toolbox-v3\\data\\merge_progress.md"

DB_COLUMNS: List[str] = [
    "exercise_name",
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
]

LIST_COLUMNS: Tuple[str, ...] = (
    "advanced_isolated_muscles",
    "stabilizers",
    "synergists",
)
MUSCLE_COLUMNS: Tuple[str, ...] = (
    "primary_muscle_group",
    "secondary_muscle_group",
    "tertiary_muscle_group",
)
SCALAR_COLUMNS: Tuple[str, ...] = tuple(
    column for column in DB_COLUMNS if column not in LIST_COLUMNS and column != "exercise_name"
)
CSV_COLUMN_MAP: Sequence[Tuple[str, str]] = (
    ("target", "primary_muscle_group"),
    ("primary target", "primary_muscle_group"),
    ("secondary target", "secondary_muscle_group"),
    ("secondary", "secondary_muscle_group"),
    ("tertiary target", "tertiary_muscle_group"),
    ("tertiary", "tertiary_muscle_group"),
    ("advanced isolated muscles", "advanced_isolated_muscles"),
    ("advanced_isolated_muscles", "advanced_isolated_muscles"),
    ("utility", "utility"),
    ("mechanic", "mechanic"),
    ("difficulty", "difficulty"),
    ("equipment", "equipment"),
    ("force", "force"),
    ("grips", "grips"),
    ("stabilizers", "stabilizers"),
    ("synergists", "synergists"),
    ("dynamic stabilizers", "dynamic_stabilizers"),
)

CANON: Dict[str, str] = {
    "quads": "Quadriceps",
    "quadricep": "Quadriceps",
    "quadriceps": "Quadriceps",
    "hams": "Hamstrings",
    "hamstring": "Hamstrings",
    "rear delts": "Posterior Deltoid",
    "rear delt": "Posterior Deltoid",
    "posterior delts": "Posterior Deltoid",
    "anterior delts": "Anterior Deltoid",
    "medial delts": "Lateral Deltoid",
    "side delts": "Lateral Deltoid",
    "traps": "Trapezius",
    "lats": "Latissimus Dorsi",
    "glutes": "Gluteus Maximus",
    "calves": "Gastrocnemius",
    "abs": "Rectus Abdominis",
    "obliques": "Obliques",
}

TABLE_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS exercises (
    exercise_name TEXT PRIMARY KEY,
    primary_muscle_group TEXT,
    secondary_muscle_group TEXT,
    tertiary_muscle_group TEXT,
    advanced_isolated_muscles TEXT,
    utility TEXT,
    grips TEXT,
    stabilizers TEXT,
    synergists TEXT,
    force TEXT,
    equipment TEXT,
    mechanic TEXT,
    difficulty TEXT
);
"""

LIST_SPLIT_PATTERN = re.compile(r"[;,]")


def collapse_spaces(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip())


def normalized_key(name: str) -> str:
    return collapse_spaces(name).lower()


def title_case(text: str) -> str:
    def repl(match: re.Match[str]) -> str:
        word = match.group(0)
        return word[0].upper() + word[1:].lower()

    return re.sub(r"[A-Za-z]+", repl, text)


def normalize_scalar_value(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    text = collapse_spaces(str(value))
    return text if text else None


def normalize_list_field(value: Optional[str]) -> List[str]:
    if value is None:
        return []
    text = str(value)
    text = text.replace("\r\n", "\n").replace("\r", "\n").replace("\n", ";")
    tokens: List[str] = []
    seen: Set[str] = set()
    for chunk in LIST_SPLIT_PATTERN.split(text):
        token = collapse_spaces(chunk)
        if not token:
            continue
        lowered = token.lower()
        if lowered in {"", "none", "n/a", "na"}:
            continue
        prefix = ""
        core = token
        if lowered.startswith("dynamic:"):
            _, rest = token.split(":", 1)
            core = collapse_spaces(rest)
            prefix = "Dynamic: "
        elif lowered.startswith("dynamic "):
            core = collapse_spaces(token[len("dynamic "):])
            prefix = "Dynamic: "
        normalized_core = title_case(core) if core else ""
        normalized = f"{prefix}{normalized_core}".strip()
        if not normalized:
            continue
        key = normalized.lower()
        if key not in seen:
            seen.add(key)
            tokens.append(normalized)
    return tokens


def format_token_list(tokens: Iterable[str]) -> Optional[str]:
    cleaned: List[str] = []
    seen: Set[str] = set()
    for token in tokens:
        if not token:
            continue
        normalized = collapse_spaces(token)
        if not normalized:
            continue
        key = normalized.lower()
        if key not in seen:
            seen.add(key)
            cleaned.append(normalized)
    if not cleaned:
        return None
    cleaned.sort(key=lambda item: item.lower())
    return "; ".join(cleaned)


def canonicalize_muscles(raw: Optional[str]) -> Optional[str]:
    if raw is None:
        return None
    text = str(raw).strip()
    if not text:
        return None
    text = text.replace("\r\n", "\n").replace("\r", "\n").replace("\n", ";")
    tokens: List[str] = []
    seen: Set[str] = set()
    for chunk in re.split(r"[;,/]", text):
        token = collapse_spaces(chunk)
        if not token:
            continue
        lowered = token.lower()
        mapped = CANON.get(lowered, lowered)
        normalized = title_case(mapped)
        key = normalized.lower()
        if key not in seen:
            seen.add(key)
            tokens.append(normalized)
    return "; ".join(tokens) if tokens else None


def parse_list_from_db(value: Optional[str]) -> List[str]:
    return normalize_list_field(value)


@dataclass
class StageRecord:
    norm_key: str
    exercise_name: str
    scalars: Dict[str, str] = field(default_factory=dict)
    lists: Dict[str, Set[str]] = field(default_factory=dict)
    source_names: List[str] = field(default_factory=list)

    def record_source_name(self, name: str) -> None:
        if name not in self.source_names:
            self.source_names.append(name)

    def add_scalar(self, column: str, value: Optional[str]) -> None:
        if not value:
            return
        if column not in self.scalars or not self.scalars[column]:
            self.scalars[column] = value

    def add_list(self, column: str, tokens: Sequence[str]) -> None:
        if not tokens:
            return
        bucket = self.lists.setdefault(column, set())
        for token in tokens:
            normalized = collapse_spaces(token)
            if not normalized:
                continue
            bucket.add(normalized)

    def get_list_tokens(self, column: str) -> List[str]:
        tokens = sorted(self.lists.get(column, set()), key=lambda item: item.lower())
        return tokens

    def to_db_dict(self) -> Dict[str, Optional[str]]:
        data: Dict[str, Optional[str]] = {column: None for column in DB_COLUMNS}
        data["exercise_name"] = self.exercise_name
        for column, value in self.scalars.items():
            data[column] = value
        for column in LIST_COLUMNS:
            data[column] = format_token_list(self.get_list_tokens(column))
        return data


@dataclass
class StageResult:
    records: List[StageRecord]
    csv_rows: int
    staged_rows: int
    skipped: List[str]
    collisions: List[Tuple[str, List[str]]]


@dataclass
class MergeDecision:
    action: str
    final: Dict[str, Optional[str]]
    assignments: List[Tuple[str, Optional[str]]]
    conflicts: List[Tuple[str, str, Optional[str], Optional[str]]]
    notes: List[str]
    columns_filled: int
    columns_already: int


@dataclass
class RunSummary:
    timestamp: dt.datetime
    csv_path: str
    db_path: str
    log_path: str
    dryrun: bool
    csv_rows: int = 0
    staged_rows: int = 0
    stage_skips: List[str] = field(default_factory=list)
    collisions: List[Tuple[str, List[str]]] = field(default_factory=list)
    matched_updates: int = 0
    new_inserts: int = 0
    unchanged: int = 0
    columns_filled: int = 0
    columns_already: int = 0
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    conflicts: List[Tuple[str, str, Optional[str], Optional[str]]] = field(default_factory=list)
    change_samples: List[Tuple[str, Dict[str, Optional[str]]]] = field(default_factory=list)
    recent_changes: List[Tuple[str, str]] = field(default_factory=list)
    backup_path: Optional[str] = None
    normalized_rows: int = 0
    post_count: Optional[int] = None
    spot_check_rows: List[Dict[str, Optional[str]]] = field(default_factory=list)

    @property
    def skipped_count(self) -> int:
        return len(self.stage_skips) + self.unchanged

    @property
    def conflict_count(self) -> int:
        return len(self.conflicts)


def ensure_table(conn: sqlite3.Connection) -> None:
    conn.execute(TABLE_SCHEMA_SQL)


def create_backup(db_path: str) -> str:
    if not os.path.exists(db_path):
        raise FileNotFoundError(f"Database file not found for backup: {db_path}")
    directory = os.path.dirname(db_path)
    os.makedirs(directory or ".", exist_ok=True)
    timestamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    base = os.path.basename(db_path)
    backup_name = f"{base}.backup_{timestamp}"
    backup_path = os.path.join(directory, backup_name)
    shutil.copy2(db_path, backup_path)
    return backup_path


def row_to_dict(row: sqlite3.Row) -> Dict[str, Optional[str]]:
    return {column: row[column] for column in DB_COLUMNS}


def stage_csv(csv_path: str) -> StageResult:
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"CSV file not found: {csv_path}")
    frame = pd.read_csv(csv_path, dtype=str, keep_default_na=False).fillna("")
    column_lookup = {column.lower(): column for column in frame.columns}
    if "exercise_name" not in column_lookup:
        raise ValueError("CSV must include an exercise_name column")

    records_by_key: Dict[str, StageRecord] = {}
    skipped: List[str] = []

    for row_number, (_, row) in enumerate(frame.iterrows(), start=2):
        raw_name = str(row[column_lookup["exercise_name"]])
        clean_name = collapse_spaces(raw_name)
        if not clean_name:
            skipped.append(f"Row {row_number}: missing exercise_name")
            continue
        key = normalized_key(clean_name)
        record = records_by_key.get(key)
        if record is None:
            record = StageRecord(norm_key=key, exercise_name=clean_name)
            records_by_key[key] = record
        record.record_source_name(raw_name)

        for source_key, target_column in CSV_COLUMN_MAP:
            column_name = column_lookup.get(source_key)
            if column_name is None:
                continue
            raw_value = row[column_name]
            text_value = str(raw_value) if raw_value is not None else ""
            if target_column == "dynamic_stabilizers":
                dynamic_tokens = [f"Dynamic: {token}" for token in normalize_list_field(text_value)]
                record.add_list("stabilizers", dynamic_tokens)
            elif target_column in LIST_COLUMNS:
                record.add_list(target_column, normalize_list_field(text_value))
            else:
                record.add_scalar(target_column, normalize_scalar_value(text_value))

    records = list(records_by_key.values())
    for record in records:
        for column in MUSCLE_COLUMNS:
            original = record.scalars.get(column)
            normalized = canonicalize_muscles(original)
            if normalized:
                record.scalars[column] = normalized
            elif column in record.scalars:
                del record.scalars[column]

    collisions = [
        (record.norm_key, record.source_names)
        for record in records
        if len(record.source_names) > 1
    ]

    return StageResult(
        records=sorted(records, key=lambda item: item.exercise_name.lower()),
        csv_rows=len(frame.index),
        staged_rows=len(records),
        skipped=skipped,
        collisions=collisions,
    )


def plan_update(existing: Dict[str, Optional[str]], record: StageRecord) -> MergeDecision:
    final: Dict[str, Optional[str]] = {column: existing.get(column) for column in DB_COLUMNS}
    final["exercise_name"] = existing["exercise_name"]
    assignments: List[Tuple[str, Optional[str]]] = []
    conflicts: List[Tuple[str, str, Optional[str], Optional[str]]] = []
    notes: List[str] = []
    columns_filled = 0
    columns_already = 0

    staged = record.to_db_dict()
    existing_name = str(existing.get("exercise_name") or "")

    for column in SCALAR_COLUMNS:
        stage_value = staged.get(column)
        existing_raw = existing.get(column)
        existing_clean = normalize_scalar_value(existing_raw)
        if stage_value:
            if existing_clean:
                columns_already += 1
                if stage_value != existing_clean:
                    conflicts.append(
                        (existing_name, column, existing_raw, stage_value)
                    )
            else:
                final[column] = stage_value
                assignments.append((column, stage_value))
                columns_filled += 1
                notes.append(f"{column} <- {stage_value}")
        else:
            final[column] = existing_raw

    for column in LIST_COLUMNS:
        stage_tokens = record.get_list_tokens(column)
        existing_raw = existing.get(column)
        existing_tokens = parse_list_from_db(existing_raw)
        stage_lower = {token.lower() for token in stage_tokens}
        existing_lower = {token.lower() for token in existing_tokens}
        union_needed = bool(stage_lower - existing_lower)
        if stage_tokens:
            if union_needed or not existing_tokens:
                union_tokens = existing_tokens + [token for token in stage_tokens if token.lower() not in existing_lower]
                formatted = format_token_list(union_tokens)
                if formatted != normalize_scalar_value(existing_raw):
                    assignments.append((column, formatted))
                    final[column] = formatted
                    columns_filled += 1
                    added_tokens = [token for token in stage_tokens if token.lower() not in existing_lower]
                    if added_tokens:
                        notes.append(f"{column} extended with {', '.join(added_tokens)}")
                else:
                    final[column] = existing_raw
            else:
                columns_already += 1
                final[column] = existing_raw
        else:
            final[column] = existing_raw

    action = "update" if assignments else "noop"
    return MergeDecision(
        action=action,
        final=final,
        assignments=assignments,
        conflicts=conflicts,
        notes=notes,
        columns_filled=columns_filled,
        columns_already=columns_already,
    )


def plan_insert(record: StageRecord) -> MergeDecision:
    final = record.to_db_dict()
    assignments = [
        (column, final.get(column))
        for column in DB_COLUMNS
        if column != "exercise_name" and final.get(column) is not None
    ]
    notes = [f"{column} <- {final[column]}" for column, _ in assignments]
    return MergeDecision(
        action="insert",
        final=final,
        assignments=assignments,
        conflicts=[],
        notes=notes,
        columns_filled=len(assignments),
        columns_already=0,
    )


def apply_update(conn: sqlite3.Connection, decision: MergeDecision) -> None:
    if not decision.assignments:
        return
    assignments_sql = ", ".join(f"{column} = ?" for column, _ in decision.assignments)
    params = [value for _, value in decision.assignments]
    params.append(decision.final["exercise_name"])
    conn.execute(
        f"UPDATE exercises SET {assignments_sql} WHERE exercise_name = ?",
        params,
    )


def apply_insert(conn: sqlite3.Connection, record: Dict[str, Optional[str]]) -> None:
    columns_sql = ", ".join(DB_COLUMNS)
    placeholders = ", ".join("?" for _ in DB_COLUMNS)
    values = [record.get(column) for column in DB_COLUMNS]
    conn.execute(
        f"INSERT INTO exercises ({columns_sql}) VALUES ({placeholders})",
        values,
    )


def merge_records(
    conn: sqlite3.Connection,
    stage_result: StageResult,
    summary: RunSummary,
) -> None:
    conn.row_factory = sqlite3.Row
    existing_rows = conn.execute("SELECT * FROM exercises").fetchall()
    duplicates_map: Dict[str, List[Dict[str, Optional[str]]]] = {}
    for row in existing_rows:
        row_dict = row_to_dict(row)
        raw_name = row_dict.get("exercise_name")
        if not isinstance(raw_name, str):
            continue
        duplicates_map.setdefault(normalized_key(raw_name), []).append(row_dict)

    existing_by_key: Dict[str, Dict[str, Optional[str]]] = {
        key: rows[0] for key, rows in duplicates_map.items()
    }

    for record in stage_result.records:
        existing = existing_by_key.get(record.norm_key)
        if existing:
            decision = plan_update(existing, record)
            summary.columns_filled += decision.columns_filled
            summary.columns_already += decision.columns_already
            summary.conflicts.extend(decision.conflicts)
            if decision.action == "update":
                summary.matched_updates += 1
                if not summary.dryrun:
                    apply_update(conn, decision)
                existing_by_key[record.norm_key] = decision.final
                updated_name = str(existing.get("exercise_name") or "")
                summary.recent_changes.append(("update", updated_name))
                if len(summary.change_samples) < 10:
                    summary.change_samples.append(("update", decision.final.copy()))
            else:
                summary.unchanged += 1
        else:
            decision = plan_insert(record)
            summary.new_inserts += 1
            summary.columns_filled += decision.columns_filled
            if not summary.dryrun:
                apply_insert(conn, decision.final)
            existing_by_key[record.norm_key] = decision.final
            summary.recent_changes.append(("insert", record.exercise_name))
            if len(summary.change_samples) < 10:
                summary.change_samples.append(("insert", decision.final.copy()))


def normalize_database(conn: sqlite3.Connection, summary: RunSummary) -> None:
    rows = conn.execute(
        "SELECT exercise_name, primary_muscle_group, secondary_muscle_group, tertiary_muscle_group, "
        "advanced_isolated_muscles, stabilizers, synergists FROM exercises"
    ).fetchall()
    for row in rows:
        row_dict = dict(row)
        assignments: Dict[str, Optional[str]] = {}
        for column in MUSCLE_COLUMNS:
            normalized = canonicalize_muscles(row_dict.get(column))
            if normalized != normalize_scalar_value(row_dict.get(column)):
                assignments[column] = normalized
        for column in LIST_COLUMNS:
            formatted = format_token_list(parse_list_from_db(row_dict.get(column)))
            if formatted != normalize_scalar_value(row_dict.get(column)):
                assignments[column] = formatted
        if assignments:
            cols_sql = ", ".join(f"{col} = ?" for col in assignments.keys())
            params = [assignments[col] for col in assignments.keys()]
            params.append(row_dict["exercise_name"])
            conn.execute(
                f"UPDATE exercises SET {cols_sql} WHERE exercise_name = ?",
                params,
            )
            summary.normalized_rows += 1


def run_post_checks(conn: sqlite3.Connection, summary: RunSummary) -> None:
    summary.post_count = conn.execute("SELECT COUNT(*) FROM exercises").fetchone()[0]
    spot_rows = conn.execute(
        "SELECT exercise_name, primary_muscle_group, secondary_muscle_group, equipment, mechanic, difficulty "
        "FROM exercises WHERE exercise_name LIKE ? ORDER BY exercise_name LIMIT 10",
        ("%Neck Flexion%",),
    ).fetchall()
    for row in spot_rows:
        summary.spot_check_rows.append(dict(row))


def format_change_samples(samples: List[Tuple[str, Dict[str, Optional[str]]]]) -> str:
    if not samples:
        return "No inserts or updates applied."
    headers = [
        "Action",
        "exercise_name",
        "primary_muscle_group",
        "secondary_muscle_group",
        "equipment",
        "mechanic",
        "difficulty",
    ]
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for action, row in samples[:10]:
        values = [
            action,
            row.get("exercise_name"),
            row.get("primary_muscle_group"),
            row.get("secondary_muscle_group"),
            row.get("equipment"),
            row.get("mechanic"),
            row.get("difficulty"),
        ]
        lines.append("| " + " | ".join(value or "" for value in values) + " |")
    return "\n".join(lines)


def format_conflicts(conflicts: List[Tuple[str, str, Optional[str], Optional[str]]]) -> str:
    if not conflicts:
        return "No conflicts detected."
    headers = ["exercise_name", "column", "kept_db_value", "csv_value"]
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for exercise_name, column, db_value, csv_value in conflicts[:20]:
        values = [exercise_name or "", column, db_value or "", csv_value or ""]
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines)


def format_spot_check(rows: List[Dict[str, Optional[str]]]) -> str:
    if not rows:
        return "No rows matched the Neck Flexion spot check."
    headers = [
        "exercise_name",
        "primary_muscle_group",
        "secondary_muscle_group",
        "equipment",
        "mechanic",
        "difficulty",
    ]
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for row in rows:
        values = [row.get(column) or "" for column in headers]
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines)


def format_markdown(summary: RunSummary) -> str:
    mode = "dry-run" if summary.dryrun else "real-run"
    lines: List[str] = []
    lines.append(f"## {summary.timestamp.isoformat(timespec='seconds')} ({mode})")
    lines.append(f"- CSV path: {summary.csv_path}")
    lines.append(f"- DB path: {summary.db_path}")
    if summary.backup_path:
        lines.append(f"- Backup: {summary.backup_path}")
    lines.append(f"- Total={summary.csv_rows}")
    lines.append(f"- Consolidated={summary.staged_rows}")
    lines.append(f"- Inserts={summary.new_inserts}")
    lines.append(f"- Updates={summary.matched_updates}")
    lines.append(f"- Conflicts={summary.conflict_count}")
    lines.append(f"- Skipped={summary.skipped_count}")
    if summary.columns_filled:
        lines.append(f"- Columns filled={summary.columns_filled}")
    if summary.columns_already:
        lines.append(f"- Columns kept={summary.columns_already}")
    if summary.normalized_rows:
        lines.append(f"- Rows normalized post-merge={summary.normalized_rows}")
    if summary.post_count is not None:
        lines.append(f"- Exercises table count={summary.post_count}")
    if summary.warnings:
        lines.append(f"- Warnings={len(summary.warnings)}")
    if summary.errors:
        lines.append(f"- Errors={len(summary.errors)}")

    lines.append("\n### Change Samples")
    lines.append(format_change_samples(summary.change_samples))

    lines.append("\n### Conflict Summary")
    lines.append(format_conflicts(summary.conflicts))

    lines.append("\n### Post-merge Quick Checks")
    recent = ", ".join(name for _, name in summary.recent_changes[:10]) if summary.recent_changes else "None"
    lines.append(f"- Top recent changes (<=10): {recent}")
    lines.append("\n" + format_spot_check(summary.spot_check_rows))

    if summary.stage_skips:
        lines.append("\n### Staging Skips")
        for item in summary.stage_skips[:20]:
            lines.append(f"- {item}")

    if summary.collisions:
        lines.append("\n### CSV Name Collisions")
        for key, names in summary.collisions[:20]:
            lines.append(f"- `{key}` => {' | '.join(names)}")

    if summary.warnings:
        lines.append("\n### Warnings")
        for warning in summary.warnings:
            lines.append(f"- {warning}")

    if summary.errors:
        lines.append("\n### Errors")
        for error in summary.errors:
            lines.append(f"- {error}")

    return "\n".join(lines) + "\n"


def append_log(summary: RunSummary) -> None:
    os.makedirs(os.path.dirname(summary.log_path) or ".", exist_ok=True)
    content = format_markdown(summary)
    with open(summary.log_path, "a", encoding="utf-8") as handle:
        handle.write(content)


def print_summary(summary: RunSummary) -> None:
    mode = "DRY-RUN" if summary.dryrun else "REAL-RUN"
    print(
        f"[{mode}] total={summary.csv_rows} consolidated={summary.staged_rows} "
        f"inserts={summary.new_inserts} updates={summary.matched_updates} conflicts={summary.conflict_count} "
        f"skipped={summary.skipped_count}"
    )
    if summary.backup_path:
        print(f"Backup created at: {summary.backup_path}")
    if summary.post_count is not None:
        print(f"Exercises count after merge: {summary.post_count}")
    if summary.conflicts:
        print(f"Conflicts kept in DB: {summary.conflict_count}")
    print(f"Log appended to: {summary.log_path}")


def run_merge(args: argparse.Namespace) -> RunSummary:
    summary = RunSummary(
        timestamp=dt.datetime.now(),
        csv_path=os.path.abspath(args.csv),
        db_path=os.path.abspath(args.db),
        log_path=os.path.abspath(args.log),
        dryrun=args.dry_run,
    )

    try:
        stage_result = stage_csv(summary.csv_path)
        summary.csv_rows = stage_result.csv_rows
        summary.staged_rows = stage_result.staged_rows
        summary.stage_skips.extend(stage_result.skipped)
        summary.collisions.extend(stage_result.collisions)

        conn = sqlite3.connect(
            summary.db_path,
            detect_types=sqlite3.PARSE_DECLTYPES,
        )
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        ensure_table(conn)

        try:
            if not summary.dryrun and os.path.exists(summary.db_path):
                summary.backup_path = create_backup(summary.db_path)
        except FileNotFoundError:
            summary.backup_path = None

        try:
            if not summary.dryrun:
                conn.execute("BEGIN")
            merge_records(conn, stage_result, summary)
            if summary.dryrun:
                summary.warnings.append(
                    "Dry-run: no database changes were written."
                )
            else:
                normalize_database(conn, summary)
                conn.commit()
                conn.execute("VACUUM")
            run_post_checks(conn, summary)
        except Exception:
            if not summary.dryrun:
                conn.rollback()
            raise
        finally:
            conn.close()
    except Exception as exc:  # pragma: no cover - defensive logging
        summary.errors.append(f"{exc.__class__.__name__}: {exc}")
        summary.errors.append(traceback.format_exc())
    finally:
        append_log(summary)
        print_summary(summary)
    return summary


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Merge progress.csv into database.db with dedupe, normalization, and logging."
    )
    parser.add_argument("--csv", default=DEFAULT_CSV_PATH, help="Path to the source CSV file.")
    parser.add_argument("--db", default=DEFAULT_DB_PATH, help="Path to the target SQLite database.")
    parser.add_argument("--log", default=DEFAULT_LOG_PATH, help="Path to the Markdown log file.")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="Preview changes without writing to the database (log still appended).",
    )
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    summary = run_merge(args)
    return 0 if not summary.errors else 1


if __name__ == "__main__":
    sys.exit(main())
