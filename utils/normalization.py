"""Utilities for canonicalising exercise data before it is persisted."""
from __future__ import annotations

import re
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence

from utils.constants import (
    DIFFICULTY,
    EQUIPMENT_SYNONYMS,
    FORCE,
    MECHANIC,
    MUSCLE_ALIAS,
    MUSCLE_GROUPS,
    UTILITY,
)

_WHITESPACE_RE = re.compile(r"\s+")


def clean_token(value: Optional[str]) -> str:
    """Trim the value and collapse internal whitespace without altering case."""
    if value is None:
        return ""
    token = str(value).strip()
    return _WHITESPACE_RE.sub(" ", token)


def to_title(value: Optional[str]) -> str:
    """Return a Title-Case representation of the token while normalising spacing."""
    token = clean_token(value)
    if not token:
        return ""
    pieces = _WHITESPACE_RE.sub(" ", token.replace("_", " ")).strip()
    # string.title() lowercases everything after the first char, which is fine here
    titled = pieces.title()
    return _WHITESPACE_RE.sub(" ", titled)


def _canonical_key(value: str) -> str:
    """Collapse a string to a case-insensitive alphanumeric key."""
    return re.sub(r"[^a-z0-9]", "", value.lower())


def _build_lookup(mapping: Mapping[str, str]) -> Dict[str, str]:
    return {_canonical_key(clean_token(key)): value for key, value in mapping.items()}


_FORCE_LOOKUP = _build_lookup(FORCE)
_MECHANIC_LOOKUP = _build_lookup(MECHANIC)
_UTILITY_LOOKUP = _build_lookup(UTILITY)
_DIFFICULTY_LOOKUP = _build_lookup(DIFFICULTY)

_CANONICAL_MUSCLES = {_canonical_key(name): name for name in MUSCLE_GROUPS}
_MUSCLE_ALIAS_LOOKUP: Dict[str, str] = {}
for alias, canonical in MUSCLE_ALIAS.items():
    canonical_target = _CANONICAL_MUSCLES.get(_canonical_key(canonical), canonical)
    _MUSCLE_ALIAS_LOOKUP[_canonical_key(clean_token(alias))] = canonical_target


def _normalise_equipment_key(value: str) -> str:
    token = clean_token(value)
    token = token.replace("-", "_")
    token = _WHITESPACE_RE.sub("_", token)
    return token.lower()


_EQUIPMENT_LOOKUP = {
    _normalise_equipment_key(key): value for key, value in EQUIPMENT_SYNONYMS.items()
}


def _resolve_from_lookup(value: Optional[str], lookup: Mapping[str, str]) -> Optional[str]:
    token = clean_token(value)
    if not token:
        return None
    key = _canonical_key(token)
    return lookup.get(key, token)


def normalize_force(value: Optional[str]) -> Optional[str]:
    """Normalise force classifications using the canonical set."""
    return _resolve_from_lookup(value, _FORCE_LOOKUP)


def normalize_mechanic(value: Optional[str]) -> Optional[str]:
    """Normalise mechanic classifications using canonical descriptors."""
    return _resolve_from_lookup(value, _MECHANIC_LOOKUP)


def normalize_utility(value: Optional[str]) -> Optional[str]:
    """Normalise utility classifications."""
    return _resolve_from_lookup(value, _UTILITY_LOOKUP)


def normalize_difficulty(value: Optional[str]) -> Optional[str]:
    """Normalise difficulty classifications."""
    return _resolve_from_lookup(value, _DIFFICULTY_LOOKUP)


def normalize_equipment(value: Optional[str]) -> Optional[str]:
    """Normalise equipment names, applying known synonyms and TitleCasing others."""
    token = clean_token(value)
    if not token:
        return None

    key = _normalise_equipment_key(token)
    synonym = _EQUIPMENT_LOOKUP.get(key)
    if synonym:
        return synonym

    parts = [part for part in key.split("_") if part]
    if not parts:
        return None

    titled_parts = [part[:1].upper() + part[1:].lower() for part in parts]
    if len(titled_parts) == 1:
        return titled_parts[0]
    return "_".join(titled_parts)


def normalize_muscle(value: Optional[str]) -> Optional[str]:
    """Map aliases to canonical muscle groups."""
    token = clean_token(value)
    if not token:
        return None

    key = _canonical_key(token)
    if key in _MUSCLE_ALIAS_LOOKUP:
        return _MUSCLE_ALIAS_LOOKUP[key]
    if key in _CANONICAL_MUSCLES:
        return _CANONICAL_MUSCLES[key]

    fallback = token.replace("_", " ")
    return to_title(fallback)


def split_csv(text: Optional[str]) -> List[str]:
    """Split a comma-separated string into clean tokens."""
    if not text:
        return []
    parts = [clean_token(part) for part in text.split(",")]
    return [part for part in parts if part]


def _dedupe_preserving_order(items: Iterable[str]) -> List[str]:
    seen = set()
    ordered: List[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            ordered.append(item)
    return ordered


def normalize_exercise_row(row: Mapping[str, Any]) -> Dict[str, Any]:
    """Normalise the relevant exercise fields in-place before persistence."""
    normalised: Dict[str, Any] = dict(row)

    # Exercise name and grips are stored TitleCase/trimmed for consistency
    exercise_name = clean_token(row.get("exercise_name"))
    normalised["exercise_name"] = exercise_name or None

    for field in ("primary_muscle_group", "secondary_muscle_group", "tertiary_muscle_group"):
        normalised[field] = normalize_muscle(row.get(field))

    iso_values = _dedupe_preserving_order(
        filter(None, (normalize_muscle(token) for token in split_csv(row.get("advanced_isolated_muscles"))))
    )
    normalised["advanced_isolated_muscles"] = ", ".join(iso_values) if iso_values else None

    normalised["force"] = normalize_force(row.get("force"))
    normalised["mechanic"] = normalize_mechanic(row.get("mechanic"))
    normalised["utility"] = normalize_utility(row.get("utility"))
    normalised["difficulty"] = normalize_difficulty(row.get("difficulty"))
    normalised["equipment"] = normalize_equipment(row.get("equipment"))

    grips_values = _dedupe_preserving_order(
        filter(None, (to_title(token) for token in split_csv(row.get("grips"))))
    )
    normalised["grips"] = ", ".join(grips_values) if grips_values else None

    return normalised
