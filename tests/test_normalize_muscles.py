import json
import os
import sqlite3

from normalize_muscles import NormalizationResult, normalize_database
from utils.constants import MUSCLE_GROUPS
from utils.normalization import normalize_muscle


def _fetch_row(db_path: str, name: str) -> sqlite3.Row:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        cursor = conn.execute(
            "SELECT exercise_name, primary_muscle_group, secondary_muscle_group, "
            "tertiary_muscle_group, advanced_isolated_muscles FROM exercises WHERE exercise_name = ?",
            (name,),
        )
        row = cursor.fetchone()
        if row is None:
            raise AssertionError(f"Row {name} not found")
        return row
    finally:
        conn.close()


def test_normalize_database_idempotent(tmp_path):
    db_path = tmp_path / "database.db"
    log_path = tmp_path / "report.md"
    alias_path = tmp_path / "aliases.json"

    alias_path.write_text(
        json.dumps(
            {
                "aliases": {"rear delts": "Posterior Deltoid", "pns": "PNS"},
                "acronyms": ["PNS"],
            }
        ),
        encoding="utf-8",
    )

    conn = sqlite3.connect(db_path)
    conn.execute(
        """
        CREATE TABLE exercises (
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
        )
        """
    )
    conn.execute(
        "INSERT INTO exercises VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            "New Exercise",
            "lats",
            "rear delts",
            " ",
            "lats; tfl , latissimus dorsi",
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
        ),
    )
    conn.execute(
        "INSERT INTO exercises VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            "Existing Exercise",
            "upper back",
            None,
            None,
            "pns; glutes",
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
        ),
    )
    conn.commit()
    conn.close()

    result_dry = normalize_database(
        str(db_path),
        str(log_path),
        alias_file=str(alias_path),
        dryrun=True,
    )
    assert isinstance(result_dry, NormalizationResult)
    assert result_dry.updated == 2
    assert result_dry.backup_path is None

    row_after_dry = _fetch_row(str(db_path), "Existing Exercise")
    assert row_after_dry["primary_muscle_group"] == "upper back"
    assert row_after_dry["advanced_isolated_muscles"] == "pns; glutes"

    result_apply = normalize_database(
        str(db_path),
        str(log_path),
        alias_file=str(alias_path),
        dryrun=False,
    )
    assert result_apply.updated == 2
    assert result_apply.backup_path is not None
    assert os.path.exists(result_apply.backup_path)

    row_new = _fetch_row(str(db_path), "New Exercise")
    assert row_new["primary_muscle_group"] == "Latissimus Dorsi"
    assert row_new["secondary_muscle_group"] == "Posterior Deltoid"
    assert row_new["tertiary_muscle_group"] is None
    assert row_new["advanced_isolated_muscles"] == "Latissimus Dorsi, TFL"

    row_existing = _fetch_row(str(db_path), "Existing Exercise")
    assert row_existing["primary_muscle_group"] == "Upper Back"
    assert row_existing["advanced_isolated_muscles"] == "Gluteus Maximus, PNS"

    result_again = normalize_database(
        str(db_path),
        str(log_path),
        alias_file=str(alias_path),
        dryrun=False,
    )
    assert result_again.updated == 0
    assert result_again.no_op == 2


def test_canonical_primary_mapping():
    aliases = {
        "latissimus-dorsi": "Latissimus Dorsi",
        "lowerback": "Lower Back",
        "front shoulders": "Front-Shoulder",
        "rear delts": "Rear-Shoulder",
        "mid traps": "Middle-Traps",
        "gluteals": "Gluteus Maximus",
        "hip adductors": "Hip-Adductors",
    }

    for alias, expected in aliases.items():
        assert normalize_muscle(alias) == expected
        assert expected in MUSCLE_GROUPS