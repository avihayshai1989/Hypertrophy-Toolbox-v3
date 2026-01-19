import sqlite3
from pathlib import Path

from scripts.migrate_isolated_muscles import create_backup, migrate_isolated_muscles


def _make_db(db_path: Path) -> None:
    conn = sqlite3.connect(db_path)
    try:
        conn.execute("PRAGMA foreign_keys = ON;")
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
            """
            CREATE TABLE exercise_isolated_muscles (
                exercise_name TEXT NOT NULL,
                muscle TEXT NOT NULL,
                PRIMARY KEY (exercise_name, muscle)
            )
            """
        )
        conn.executemany(
            "INSERT INTO exercises VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [
                (
                    'Hip Thrust',
                    'Glutes',
                    None,
                    None,
                    'Gluteus Maximus, glutes ',
                    'basic',
                    None,
                    None,
                    None,
                    'push & pull',
                    'smith machine',
                    'isolation',
                    'intermediate',
                ),
                (
                    'Face Pull',
                    'Rear-Shoulder',
                    None,
                    None,
                    None,
                    'auxiliary',
                    None,
                    None,
                    None,
                    'pull',
                    'cable machine',
                    'compound',
                    'beginner',
                ),
            ],
        )
        conn.commit()
    finally:
        conn.close()


def test_migration_backfills_junction_table(tmp_path):
    db_path = tmp_path / 'test.db'
    _make_db(db_path)

    backup_path = create_backup(db_path)
    assert backup_path.exists()

    migrate_isolated_muscles(db_path)

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        cur = conn.execute("SELECT muscle FROM exercise_isolated_muscles WHERE exercise_name = ? ORDER BY muscle", ('Hip Thrust',))
        muscles = [row['muscle'] for row in cur.fetchall()]
        assert muscles == ['gluteus-maximus']

        row = conn.execute(
            "SELECT advanced_isolated_muscles, force, equipment FROM exercises WHERE exercise_name = ?",
            ('Hip Thrust',),
        ).fetchone()
        assert row['advanced_isolated_muscles'] == 'gluteus-maximus'
        assert row['force'] == 'Push/Pull'
        assert row['equipment'] == 'Smith_Machine'

        cur = conn.execute(
            "SELECT muscle FROM exercise_isolated_muscles WHERE exercise_name = ?",
            ('Face Pull',),
        )
        assert cur.fetchall() == []
    finally:
        conn.close()