from __future__ import annotations

import re
from datetime import datetime, timezone
from urllib.parse import parse_qsl, urljoin, urlparse

from bs4 import BeautifulSoup, Tag

from .schemas import ElectionInfo, Geography, PageResult, ResultRecord
from .utils import clean_text, parse_date, parse_italian_float, parse_italian_int, slug


def _header_tokens(tag: Tag) -> set[str]:
    value = tag.get("headers", [])
    if isinstance(value, str):
        return set(value.split())
    return {str(item) for item in value}


def _cell_by_header(row: Tag, header: str) -> Tag | None:
    for cell in row.find_all(["td", "th"]):
        if header in _header_tokens(cell):
            return cell
    return None


def _parse_heading(soup: BeautifulSoup, source_url: str) -> tuple[ElectionInfo, Geography]:
    heading = soup.select_one("#headEnti h3")
    if not heading:
        raise ValueError("Election heading not found.")
    parts = [clean_text(part) for part in heading.stripped_strings if clean_text(part)]
    if not parts:
        raise ValueError("Election heading is empty.")

    election_match = re.match(r"^(.*?)\s+(\d{2}/\d{2}/\d{4})$", parts[0])
    if not election_match:
        raise ValueError(f"Unexpected election title: {parts[0]!r}")
    query = dict(parse_qsl(urlparse(source_url).query, keep_blank_values=True))
    election = ElectionInfo(
        code=query.get("tpel"),
        name=election_match.group(1),
        date=parse_date(election_match.group(2)),
    )

    geography_data: dict[str, str] = {}
    labels = {
        "area": "area",
        "regione": "regione",
        "circoscrizione": "circoscrizione",
        "provincia": "provincia",
        "comune": "comune",
    }
    for part in parts[1:]:
        for prefix, field in labels.items():
            if part.casefold().startswith(prefix + " "):
                geography_data[field] = clean_text(part[len(prefix) + 1 :])
                break
    geography = Geography(**geography_data, query_codes=query)
    return election, geography


def _parse_summary(soup: BeautifulSoup) -> dict[str, int | float | str | None]:
    summary: dict[str, int | float | str | None] = {}
    for table in soup.select("table.dati_riepilogo"):
        for row in table.select("tr"):
            label_cell = row.find("th")
            value_cells = row.find_all("td")
            if not label_cell or not value_cells:
                continue
            label = clean_text(label_cell.get_text(" ", strip=True))
            key = slug(label)
            value_text = clean_text(value_cells[0].get_text(" ", strip=True))
            value = parse_italian_int(value_text)
            summary[key] = value if value is not None else value_text
            percentage_cell = next(
                (cell for cell in value_cells[1:] if "percentuale" in cell.get("class", [])),
                None,
            )
            if percentage_cell:
                summary[f"{key}_percentuale"] = parse_italian_float(
                    percentage_cell.get_text(" ", strip=True)
                )
    return summary


def _find_results_table(soup: BeautifulSoup) -> Tag:
    for table in soup.find_all("table"):
        if "risultat" in str(table.get("summary", "")).casefold():
            return table
    raise ValueError("Results table not found.")


def _parse_record(row: Tag, source_url: str) -> ResultRecord | None:
    classes = set(row.get("class", []))
    candidate_cell = row.find(id=re.compile(r"^candidato\d+$"))
    list_cell = row.select_one("th.candidato")
    first_heading = row.find("th")

    if "leader" in classes and candidate_cell:
        record_type = "candidate"
        label_cell = candidate_cell
    elif "totale_liste" in classes:
        record_type = "coalition_total"
        label_cell = row.find(id=re.compile(r"^htotalecoalizione")) or first_heading
    elif "totalecomplessivovoti" in classes:
        record_type = "total"
        label_cell = first_heading
    elif list_cell:
        record_type = "list"
        label_cell = list_cell
    elif first_heading:
        record_type = "option"
        label_cell = first_heading
    else:
        return None

    name = clean_text(label_cell.get_text(" ", strip=True)) if label_cell else ""
    if not name:
        return None
    record_id = str(label_cell.get("id")) if label_cell and label_cell.get("id") else None
    parent_id = None
    for cell in row.find_all(["td", "th"]):
        for token in _header_tokens(cell):
            if re.fullmatch(r"candidato\d+", token):
                parent_id = token
                break
        if parent_id:
            break

    votes_cell = _cell_by_header(row, "hvoti")
    percentage_cell = _cell_by_header(row, "hpercentuale")
    seats_cell = _cell_by_header(row, "hseggi")
    image = row.find("img")
    status = None
    if record_type == "candidate":
        status_cell = row.select_one("td.text-left")
        if status_cell:
            status = clean_text(status_cell.get_text(" ", strip=True)) or None

    return ResultRecord(
        record_type=record_type,
        record_id=record_id,
        parent_id=parent_id,
        name=name,
        status=status,
        votes=parse_italian_int(votes_cell.get_text(" ", strip=True)) if votes_cell else None,
        percentage=(
            parse_italian_float(percentage_cell.get_text(" ", strip=True))
            if percentage_cell
            else None
        ),
        seats=parse_italian_int(seats_cell.get_text(" ", strip=True)) if seats_cell else None,
        symbol_url=urljoin(source_url, image.get("src")) if image and image.get("src") else None,
        raw_cells=[clean_text(cell.get_text(" ", strip=True)) for cell in row.find_all(["td", "th"])],
    )


def parse_page_html(html: str | bytes, source_url: str) -> PageResult:
    soup = BeautifulSoup(html, "html.parser")
    election, geography = _parse_heading(soup, source_url)
    records = []
    for row in _find_results_table(soup).select("tbody tr"):
        record = _parse_record(row, source_url)
        if record:
            records.append(record)
    if not records:
        raise ValueError("The results table contains no recognisable rows.")
    return PageResult(
        source_url=source_url,
        retrieved_at=datetime.now(timezone.utc),
        election=election,
        geography=geography,
        summary=_parse_summary(soup),
        records=records,
    )
