"""Populate the exercise_isolated_muscles junction table from denormalised data."""
from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path
import shutil

from utils.config import DB_FILE
from utils.database import DatabaseHandler
from utils.normalization import normalize_exercise_row, split_csv
from utils.logger import get_logger


logger = get_logger()


def create_backup(db_path: Path) -> Path:
    timestamp = datetime.utcnow().strftime("%Y%m%d-%H%M")
    backup_path = db_path.with_name(f"{db_path.stem}.backup-{timestamp}{db_path.suffix}")
    shutil.copy2(db_path, backup_path)
    logger.info("Database backup created at %s", backup_path)
    return backup_path


def migrate_isolated_muscles(db_path: Path) -> None:
    with DatabaseHandler(str(db_path)) as db:
        exercises = db.fetch_all(
            "SELECT exercise_name, primary_muscle_group, secondary_muscle_group, "
            "tertiary_muscle_group, advanced_isolated_muscles, utility, grips, "
            "stabilizers, synergists, force, equipment, mechanic, difficulty "
            "FROM exercises"
        )

        for row in exercises:
            name = row['exercise_name']
            normalised = normalize_exercise_row(row)
            canonical_text = normalised.get('advanced_isolated_muscles')

            update_params = {
                'exercise_name': name,
                'primary_muscle_group': normalised.get('primary_muscle_group'),
                'secondary_muscle_group': normalised.get('secondary_muscle_group'),
                'tertiary_muscle_group': normalised.get('tertiary_muscle_group'),
                'advanced_isolated_muscles': canonical_text,
                'utility': normalised.get('utility'),
                'grips': normalised.get('grips'),
                'stabilizers': normalised.get('stabilizers'),
                'synergists': normalised.get('synergists'),
                'force': normalised.get('force'),
                'equipment': normalised.get('equipment'),
                'mechanic': normalised.get('mechanic'),
                'difficulty': normalised.get('difficulty'),
            }

            db.execute_query(
                """
                UPDATE exercises
                SET primary_muscle_group = :primary_muscle_group,
                    secondary_muscle_group = :secondary_muscle_group,
                    tertiary_muscle_group = :tertiary_muscle_group,
                    advanced_isolated_muscles = :advanced_isolated_muscles,
                    utility = :utility,
                    grips = :grips,
                    stabilizers = :stabilizers,
                    synergists = :synergists,
                    force = :force,
                    equipment = :equipment,
                    mechanic = :mechanic,
                    difficulty = :difficulty
                WHERE exercise_name = :exercise_name
                """,
                update_params,
            )
            db.execute_query(
                "DELETE FROM exercise_isolated_muscles WHERE exercise_name = ?",
                (name,),
            )
            muscles = [token for token in split_csv(canonical_text)]
            if muscles:
                db.executemany(
                    "INSERT OR IGNORE INTO exercise_isolated_muscles (exercise_name, muscle) VALUES (?, ?)",
                    [(name, muscle) for muscle in muscles],
                )

    logger.info("Migrated %s exercises into exercise_isolated_muscles", len(exercises))


def main() -> None:
    parser = argparse.ArgumentParser(description="Backfill the exercise_isolated_muscles junction table")
    parser.add_argument(
        "--database",
        dest="database",
        default=DB_FILE,
        help="Path to the SQLite database file (defaults to utils.config.DB_FILE)",
    )
    args = parser.parse_args()

    db_path = Path(args.database).expanduser().resolve()
    if not db_path.exists():
        raise FileNotFoundError(f"Database file not found at {db_path}")

    create_backup(db_path)
    migrate_isolated_muscles(db_path)
    logger.info("Migration completed successfully")


if __name__ == "__main__":
    main()
