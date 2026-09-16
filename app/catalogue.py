from __future__ import annotations

import json
import re
from datetime import datetime
from urllib.parse import urljoin

from .schemas import CatalogueEntry
from .utils import parse_date


CATALOGUE_URL = "https://elezionistorico.interno.gov.it/eligendo/opendata.php"
DOWNLOAD_BASE = "https://dait.interno.gov.it/documenti/opendata/"


def parse_catalogue_html(html: str) -> list[CatalogueEntry]:
    match = re.search(
        r"var\s+dataSet\s*=\s*(\[\[.*?\]\s*,?\s*\])\s*;",
        html,
        re.DOTALL,
    )
    if not match:
        raise ValueError("Open Data catalogue not found on the official page.")
    # The portal's JavaScript sometimes uses a trailing comma. It is valid in
    # JavaScript, but not in JSON.
    json_text = re.sub(r",\s*]", "]", match.group(1))
    raw_entries = json.loads(json_text)
    entries: list[CatalogueEntry] = []
    for raw in raw_entries:
        if len(raw) < 4:
            continue
        category = str(raw[0]).strip()
        year_text = str(raw[1]).strip() if len(raw) > 1 else ""
        relative_path = str(raw[2]).strip()
        filename = str(raw[3]).strip()
        date_text = str(raw[4]).strip() if len(raw) > 4 else ""
        identifier = str(raw[6]).strip() if len(raw) > 6 else None
        election_date = None
        if re.fullmatch(r"\d{2}/\d{2}/\d{4}", date_text):
            election_date = parse_date(date_text)
        year = int(year_text) if re.fullmatch(r"\d{4}", year_text) else None
        entries.append(
            CatalogueEntry(
                category=category,
                year=year,
                relative_path=relative_path,
                filename=filename,
                election_date=election_date,
                identifier=identifier or None,
                download_url=urljoin(DOWNLOAD_BASE, relative_path),
            )
        )
    return entries


def catalogue_matches(
    entries: list[CatalogueEntry],
    *,
    category: str | None = None,
    year: int | None = None,
) -> list[CatalogueEntry]:
    filtered = entries
    if category:
        filtered = [entry for entry in filtered if entry.category == category]
    if year:
        filtered = [entry for entry in filtered if entry.year == year]
    return sorted(
        filtered,
        key=lambda entry: (
            entry.category,
            entry.election_date or datetime.min.date(),
            entry.filename,
        ),
    )
