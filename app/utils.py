from __future__ import annotations

import re
import unicodedata
from datetime import date, datetime


def clean_text(value: str | None) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def slug(value: str) -> str:
    normalised = unicodedata.normalize("NFKD", clean_text(value))
    ascii_value = "".join(char for char in normalised if not unicodedata.combining(char))
    return re.sub(r"[^a-z0-9]+", "_", ascii_value.casefold()).strip("_")


HISTORICALLY_SPLIT_MUNICIPALITIES = (
    "REGGIO CALABRIA",
    "BRESCIA",
    "BOLOGNA",
    "CAGLIARI",
    "CATANIA",
    "FERRARA",
    "FIRENZE",
    "FOGGIA",
    "GENOVA",
    "LIVORNO",
    "MESSINA",
    "MILANO",
    "MODENA",
    "NAPOLI",
    "PALERMO",
    "PADOVA",
    "PARMA",
    "PERUGIA",
    "PRATO",
    "RAVENNA",
    "RIMINI",
    "SALERNO",
    "TARANTO",
    "TORINO",
    "TRIESTE",
    "VENEZIA",
    "BARI",
    "ROMA",
)


def canonical_municipality(value: str | None) -> str | None:
    cleaned = clean_text(value)
    if not cleaned:
        return None
    folded = cleaned.casefold()
    explicit_part = re.fullmatch(
        r"parte\s+(?:di|del)\s+comune(?:\s+di)?\s+(.+)",
        folded,
    )
    if explicit_part:
        municipality = clean_text(explicit_part.group(1)).upper()
        if municipality == "REGGIO DI CALABRIA":
            return "REGGIO CALABRIA"
        return municipality
    for municipality in HISTORICALLY_SPLIT_MUNICIPALITIES:
        base = municipality.casefold()
        if (
            folded.startswith(f"{base} - ")
            or folded.startswith(f"{base} centro")
            or folded.startswith(f"{base} nord")
            or folded.startswith(f"{base} sud")
            or folded.startswith(f"{base} est")
            or folded.startswith(f"{base} ovest")
            or folded.startswith(f"{base} zona ")
            or folded.startswith(f"{base}: municipio ")
            or folded.startswith(f"{base}: quartiere ")
            or folded.startswith(f"{base}: zona ")
            or re.fullmatch(rf"{re.escape(base)}\s+\d+", folded)
            or re.fullmatch(rf"{re.escape(base)}\s+[ivxlcdm]+", folded)
        ):
            return municipality
    return cleaned


def parse_italian_int(value: str | None) -> int | None:
    if value is None:
        return None
    cleaned = clean_text(value).replace(".", "").replace(" ", "")
    if not cleaned or not re.fullmatch(r"[-+]?\d+", cleaned):
        return None
    return int(cleaned)


def parse_italian_float(value: str | None) -> float | None:
    if value is None:
        return None
    cleaned = clean_text(value).replace("%", "").replace(" ", "")
    if not cleaned:
        return None
    if "," in cleaned:
        cleaned = cleaned.replace(".", "").replace(",", ".")
    try:
        return float(cleaned)
    except ValueError:
        return None


def parse_date(value: str) -> date:
    value = value.strip()
    for pattern in ("%Y-%m-%d", "%d/%m/%Y", "%Y%m%d"):
        try:
            return datetime.strptime(value, pattern).date()
        except ValueError:
            continue
    raise ValueError(f"Invalid date: {value!r}")
