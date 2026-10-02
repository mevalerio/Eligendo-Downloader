"""College composition tables extracted from the district-map decrees.

Each table lists, for one district-map version, the municipalities and city
zones that make up every college. It answers how many college pieces a
municipality should have, which the official-page verification compares with
the pieces found on the website and in Open Data.
"""
from __future__ import annotations

import csv
from functools import lru_cache
from pathlib import Path
from typing import Any

from .electoral_laws import district_map_for
from .utils import slug

REGISTRY_DIR = Path(__file__).with_name("district_maps")
REGISTRY_FIELDS = (
    "map_version",
    "geography",
    "college",
    "municipality",
    "entry_type",
    "entry_text",
    "source_page",
    "ocr_text",
    "match_score",
)


@lru_cache(maxsize=None)
def registry_rows(map_version: str) -> tuple[dict[str, str], ...]:
    path = REGISTRY_DIR / f"{map_version}.csv"
    if not path.exists():
        return ()
    with path.open(encoding="utf-8", newline="") as handle:
        return tuple(csv.DictReader(handle))


def _registry_index(map_version: str) -> dict[tuple[str, str], set[int]]:
    """(geography key, municipality key) -> colleges, built once per loaded table."""
    rows = registry_rows(map_version)
    cached = _INDEX.get(map_version)
    if cached is not None and cached[0] is rows:
        return cached[1]
    index: dict[tuple[str, str], set[int]] = {}
    for row in rows:
        if row["municipality"]:
            key = (slug(row["geography"]), slug(row["municipality"]))
            index.setdefault(key, set()).add(int(row["college"]))
    _INDEX[map_version] = (rows, index)
    return index


_INDEX: dict[str, tuple[tuple[dict[str, str], ...], dict[tuple[str, str], set[int]]]] = {}


def legal_colleges(
    *,
    category: str,
    year: int,
    municipality: str,
    geography: str | None,
) -> dict[str, Any] | None:
    """Return the colleges the decree assigns to a municipality.

    ``geography`` is the constituency for the Chamber and the region for the
    Senate. ``None`` is returned when no extracted table covers the election,
    so callers can report the check as not available.
    """
    version = district_map_for(category, year)
    if version is None:
        return None
    if not registry_rows(version.id):
        return None
    municipality_key = slug(municipality)
    geography_key = slug(geography or "")
    colleges = sorted(
        {
            college
            for (row_geography, row_municipality), numbers in _registry_index(version.id).items()
            if row_municipality == municipality_key
            and (not geography_key or row_geography == geography_key)
            for college in numbers
        }
    )
    return {
        "mappa_collegi_versione": version.id,
        "collegi": colleges,
        "fonti_ids": list(version.source_ids),
    }
