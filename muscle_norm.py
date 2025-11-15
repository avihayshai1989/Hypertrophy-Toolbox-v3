from __future__ import annotations

import json
import os
import re
from typing import Dict, List, Optional, Set

DEFAULT_ALIAS_MAP: Dict[str, str] = {
    "lats": "Latissimus Dorsi",
    "lat": "Latissimus Dorsi",
    "latissimus": "Latissimus Dorsi",
    "traps": "Trapezius",
    "trap": "Trapezius",
    "abs": "Rectus Abdominis",
    "abdominals": "Rectus Abdominis",
    "glutes": "Gluteus Maximus",
    "glute": "Gluteus Maximus",
    "gluteals": "Gluteus Maximus",
    "hams": "Hamstrings",
    "hamstring": "Hamstrings",
    "hamstrings": "Hamstrings",
    "obliques": "External Obliques",
    "oblique": "External Obliques",
}
DEFAULT_ACRONYMS: Set[str] = {"TFL", "IT Band", "SCM"}

_WORD_PATTERN = re.compile(r"[A-Za-z0-9]+(?:'[A-Za-z0-9]+)?")
_EXTRA_ACRONYMS: Set[str] = set()


def _collapse_spaces(text: str) -> str:
    return " ".join(text.split())


def _load_json(path: str) -> object:
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def _load_yaml(path: str) -> object:
    try:
        import yaml  # type: ignore
    except ImportError as exc:  # pragma: no cover - optional dependency
        raise RuntimeError("PyYAML is required to load YAML alias files") from exc

    with open(path, "r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def _normalize_alias_key(key: str) -> str:
    return _collapse_spaces(key.strip().lower())


def load_alias_map(path: Optional[str]) -> Dict[str, str]:
    alias_map = dict(DEFAULT_ALIAS_MAP)
    global _EXTRA_ACRONYMS
    _EXTRA_ACRONYMS = set()

    if not path:
        return alias_map

    if not os.path.exists(path):
        raise FileNotFoundError(f"Alias file not found: {path}")

    ext = os.path.splitext(path)[1].lower()
    if ext in {".yml", ".yaml"}:
        data = _load_yaml(path)
    else:
        data = _load_json(path)

    if data is None:
        return alias_map

    if isinstance(data, dict):
        aliases = data.get("aliases") if "aliases" in data else data
        if not isinstance(aliases, dict):
            raise ValueError("Alias file 'aliases' entry must be a mapping")
        for raw_key, raw_value in aliases.items():
            key = _normalize_alias_key(str(raw_key))
            if not key:
                continue
            value = _collapse_spaces(str(raw_value).strip())
            if not value:
                continue
            alias_map[key] = value
        raw_acronyms = data.get("acronyms") if isinstance(data, dict) else None
        if raw_acronyms:
            if not isinstance(raw_acronyms, (list, tuple, set)):
                raise ValueError("Alias file 'acronyms' entry must be a sequence")
            _EXTRA_ACRONYMS = {str(item).strip() for item in raw_acronyms if str(item).strip()}
    else:
        raise ValueError("Alias file must contain a mapping or an object with an 'aliases' mapping")

    return alias_map


def get_alias_acronyms() -> Set[str]:
    return set(_EXTRA_ACRONYMS)


def is_acronym(token: str, acronyms: Set[str]) -> bool:
    token_normalized = _collapse_spaces(token.strip())
    if not token_normalized:
        return False
    lowered = token_normalized.lower()
    return any(lowered == entry.lower() for entry in acronyms)


def _acronym_lookup(acronyms: Set[str]) -> Dict[str, str]:
    return {entry.lower(): entry for entry in acronyms}


def titlecase_token(token: str, acronyms: Set[str]) -> str:
    stripped = token.strip()
    if not stripped:
        return ""

    lookup = _acronym_lookup(acronyms)
    if stripped.lower() in lookup:
        return lookup[stripped.lower()]

    result_parts: List[str] = []
    last_index = 0
    for match in _WORD_PATTERN.finditer(stripped):
        start, end = match.span()
        result_parts.append(stripped[last_index:start])
        word = match.group(0)
        lowered = word.lower()
        if lowered in lookup:
            replacement = lookup[lowered]
        elif word.isupper() and len(word) <= 4:
            replacement = word
        elif word.isdigit():
            replacement = word
        else:
            replacement = lowered.capitalize()
        result_parts.append(replacement)
        last_index = end
    result_parts.append(stripped[last_index:])
    return "".join(result_parts)


def normalize_single(
    value: Optional[str],
    alias_map: Dict[str, str],
    acronyms: Set[str],
) -> Optional[str]:
    if value is None:
        return None
    collapsed = _collapse_spaces(str(value).strip())
    if not collapsed:
        return None

    alias_value = alias_map.get(collapsed.lower())
    if alias_value:
        collapsed = _collapse_spaces(alias_value.strip())

    if is_acronym(collapsed, acronyms):
        lookup = _acronym_lookup(acronyms)
        return lookup[collapsed.lower()]

    normalized = titlecase_token(collapsed, acronyms)
    return normalized if normalized else None


def split_list(value: Optional[str]) -> List[str]:
    if value is None:
        return []
    raw = str(value).replace(";", ",")
    parts = [part.strip() for part in raw.split(",")]
    return [part for part in parts if part]


def normalize_list(
    value: Optional[str],
    alias_map: Dict[str, str],
    acronyms: Set[str],
) -> Optional[str]:
    tokens = split_list(value)
    seen: Set[str] = set()
    normalized: List[str] = []
    for token in tokens:
        normalized_token = normalize_single(token, alias_map, acronyms)
        if not normalized_token:
            continue
        key = normalized_token.lower()
        if key in seen:
            continue
        seen.add(key)
        normalized.append(normalized_token)
    if not normalized:
        return None
    normalized.sort(key=lambda item: item.lower())
    return ", ".join(normalized)
