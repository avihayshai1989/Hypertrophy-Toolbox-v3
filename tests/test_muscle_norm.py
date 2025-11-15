import json
from typing import Set

from muscle_norm import (
    DEFAULT_ACRONYMS,
    get_alias_acronyms,
    load_alias_map,
    normalize_list,
    normalize_single,
    split_list,
)


def _acronyms_copy() -> Set[str]:
    return set(DEFAULT_ACRONYMS)


def test_normalize_single_title_case_and_alias():
    alias_map = load_alias_map(None)
    acronyms = _acronyms_copy()

    assert normalize_single(" upper back ", alias_map, acronyms) == "Upper Back"
    assert normalize_single("lats", alias_map, acronyms) == "Latissimus Dorsi"
    assert normalize_single("tfl", alias_map, acronyms) == "TFL"


def test_normalize_list_deduplicates_and_sorts():
    alias_map = load_alias_map(None)
    acronyms = _acronyms_copy()

    value = "lats; tfl , latissimus dorsi;;"
    normalized = normalize_list(value, alias_map, acronyms)
    assert normalized == "Latissimus Dorsi, TFL"
    assert split_list(normalized) == ["Latissimus Dorsi", "TFL"]


def test_load_alias_map_with_custom_acronyms(tmp_path):
    alias_file = tmp_path / "aliases.json"
    alias_file.write_text(
        json.dumps(
            {
                "aliases": {"rear delts": "Posterior Deltoid", "pns": "PNS"},
                "acronyms": ["PNS"],
            }
        ),
        encoding="utf-8",
    )

    alias_map = load_alias_map(str(alias_file))
    acronyms = _acronyms_copy()
    acronyms.update(get_alias_acronyms())

    assert normalize_single("rear delts", alias_map, acronyms) == "Posterior Deltoid"
    assert normalize_single("pns", alias_map, acronyms) == "PNS"
    assert split_list(normalize_list("rear delts, pns", alias_map, acronyms)) == [
        "PNS",
        "Posterior Deltoid",
    ]
