# Exercise Import Decisions

This document captures the non-negotiable rules for the Excel to SQLite merge utility.

- **Normalization rules**: Trim leading/trailing whitespace, collapse internal whitespace to a single space, and normalize endash/emdash characters to the ASCII hyphen before any comparisons.
- **Exact name matching**: Import logic only merges rows whose normalized `exercise_name` strings are identical. No fuzzy, partial, or substring matching is permitted.
- **Empty cell handling**: Blank strings and missing values coming from Excel are treated as nulls and never overwrite populated database fields.
- **Case sensitivity flag**: `--nocase` enforces a `COLLATE NOCASE` uniqueness constraint; when omitted, uniqueness is strictly case-sensitive.
- **Update-only flag**: `--update-only` converts unmatched Excel rows into skipped entries instead of inserts.
- **Default paths**: Unless overridden, the tool reads from `data/exercises.xlsx`, writes to `data/database.db`, and emits Markdown artifacts in `docs/`.

## Data semantics

- Equipment semantics: The equipment field intentionally includes both gear (Barbell, Dumbbells, …) and categories (Yoga, Recovery, Stretches, Cardio). These are first-class filter values.
- Enumerations: Incoming `force`, `mechanic`, and `difficulty` values are canonicalized to `Push`/`Pull`/`Hold`, `Compound`/`Isolation`, and `Beginner`/`Intermediate`/`Advanced` respectively before merging.

