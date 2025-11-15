import csv
import sqlite3
from typing import Dict, Set, Tuple

from merge_progress_into_db import MUSCLE_LIST_COLUMNS, MUSCLE_SCALAR_COLUMNS, ensure_exercises_table, run_merge
from muscle_norm import DEFAULT_ACRONYMS, get_alias_acronyms, load_alias_map


def _load_default_aliases() -> Tuple[Dict[str, str], Set[str]]:
    alias_map = load_alias_map(None)
    acronyms = set(DEFAULT_ACRONYMS)
    acronyms.update(get_alias_acronyms())
    return alias_map, acronyms


def _fetch_muscles(conn: sqlite3.Connection, name: str) -> Dict[str, str]:
    columns = [*MUSCLE_SCALAR_COLUMNS, *MUSCLE_LIST_COLUMNS]
    cursor = conn.execute(
        f"SELECT {', '.join(columns)} FROM exercises WHERE exercise_name = ?",
        (name,),
    )
    row = cursor.fetchone()
    if row is None:
        raise AssertionError(f"Exercise {name} not found")
    return {column: row[index] for index, column in enumerate(columns)}


def test_run_merge_normalizes_muscle_fields(tmp_path):
    db_path = tmp_path / "database.db"
    log_path = tmp_path / "merge.md"
    csv_path = tmp_path / "import.csv"

    conn = sqlite3.connect(db_path)
    ensure_exercises_table(conn)
    conn.execute(
        "INSERT INTO exercises (exercise_name, primary_muscle_group, advanced_isolated_muscles) VALUES (?, ?, ?)",
        ("Existing", "upper back", "lats; tfl"),
    )
    conn.commit()
    conn.close()

    with open(csv_path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow([
            "exercise_name",
            "primary_muscle_group",
            "secondary_muscle_group",
            "tertiary_muscle_group",
            "advanced_isolated_muscles",
        ])
        writer.writerow(["New", "lats", "glutes", "hamstrings", "lats; tfl"])
        writer.writerow(["Existing", "", "", "", ""])

    alias_map, acronyms = _load_default_aliases()

    summary = run_merge(
        str(csv_path),
        str(db_path),
        str(log_path),
        dryrun=False,
        fix_names=False,
        scalar_policy="db",
        scalar_overrides={},
        list_policy="union",
        list_overrides={},
        export_diff_path=None,
        diff_format="csv",
        diff_top_k=5,
        alias_map=alias_map,
        acronyms=acronyms,
        alias_file=None,
    )

    assert summary.inserted == 1
    assert summary.updated == 1
    assert summary.no_ops == 0

    conn = sqlite3.connect(db_path)
    muscles_new = _fetch_muscles(conn, "New")
    muscles_existing = _fetch_muscles(conn, "Existing")
    conn.close()

    assert muscles_new["primary_muscle_group"] == "Latissimus Dorsi"
    assert muscles_new["secondary_muscle_group"] == "Gluteus Maximus"
    assert muscles_new["tertiary_muscle_group"] == "Hamstrings"
    assert muscles_new["advanced_isolated_muscles"] == "Latissimus Dorsi, TFL"

    assert muscles_existing["primary_muscle_group"] == "Upper Back"
    assert muscles_existing["advanced_isolated_muscles"] == "Latissimus Dorsi, TFL"