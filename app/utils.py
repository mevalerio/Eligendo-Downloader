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
