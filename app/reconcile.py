from __future__ import annotations

import argparse
import re
import sys
import time
from collections import defaultdict, deque
from datetime import date, datetime
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from bs4 import BeautifulSoup

from .config import Settings
from .database import Database
from .http_client import Download, SafeHttpClient, UpstreamError
from .schemas import PageResult
from .scraper import parse_page_html
from .service import EligendoService
from .utils import canonical_municipality, slug


CATEGORY_CODES = {
    "camera": "C",
    "senato": "S",
    "europee": "E",
    "regionali": "R",
    "comunali": "G",
}
CATEGORY_HEADINGS = {
    "camera": "camera",
    "senato": "senato",
    "europee": "europee",
    "regionali": "regionali",
    "comunali": "comunali",
}
SELECTOR_TYPES = {
    "circoscrizione": "C",
    "regione": "R",
    "provincia": "P",
    "comune": "C",
}
OPTION_PATTERN = re.compile(r"^(?P<ne>.+?)-lev(?P<level>\d)(?P<value>.+)$")
HEADING_DATE_PATTERN = re.compile(r"(?P<date>\d{2}/\d{2}/\d{4})")
TRANSIENT_UPSTREAM_MARKERS = (
    "Error connecting to ",
    "HTTP 429",
    "HTTP 500",
    "HTTP 502",
    "HTTP 503",
    "HTTP 504",
)


def root_url(category: str, election_date: date) -> str:
    query = urlencode(
        {
            "tpel": CATEGORY_CODES[category],
            "dtel": election_date.strftime("%d/%m/%Y"),
            "tpa": "I",
            "tpe": "A",
            "lev0": "0",
            "levsut0": "0",
            "es0": "S",
            "ms": "S",
        }
    )
    return f"https://elezionistorico.interno.gov.it/index.php?{query}"


def heading_election(html: bytes) -> tuple[str | None, date | None]:
    """Read the election label and date rendered by the official website."""
    soup = BeautifulSoup(html, "html.parser")
    heading = soup.select_one("#headEnti h3")
    if heading is None:
        return None, None
    text = heading.get_text(" ", strip=True)
    match = HEADING_DATE_PATTERN.search(text)
    if match is None:
        return text or None, None
    label = text[: match.start()].strip(" |-:") or None
    return label, datetime.strptime(match.group("date"), "%d/%m/%Y").date()


def download_with_backoff(
    client: SafeHttpClient,
    url: str,
    *,
    max_bytes: int,
    max_attempts: int | None = None,
) -> tuple[Download, int]:
    """Wait through transient DNS, connection, rate-limit, and server failures."""
    attempt = 0
    while True:
        attempt += 1
        try:
            return client.get(url, max_bytes=max_bytes), attempt
        except UpstreamError as exc:
            transient = any(marker in str(exc) for marker in TRANSIENT_UPSTREAM_MARKERS)
            if not transient or (
                max_attempts is not None and attempt >= max_attempts
            ):
                raise
            delay = min(60, 2 ** min(attempt, 6))
            print(
                f"RETRY {datetime.now().isoformat(timespec='seconds')} "
                f"attempt={attempt} wait={delay}s url={url} error={exc}",
                flush=True,
            )
            time.sleep(delay)


def selector_children(html: bytes, source_url: str) -> list[str]:
    """Return the next geographical level without guessing Ministry codes."""
    soup = BeautifulSoup(html, "html.parser")
    parsed = urlparse(source_url)
    query = dict(parse_qsl(parsed.query, keep_blank_values=True))
    existing_levels = {
        int(key[3:])
        for key in query
        if key.startswith("lev") and key[3:].isdigit()
    }
    candidates: list[tuple[int, str, list[tuple[str, str, str]]]] = []
    for selector in soup.select("select[name^='sel_sezione']"):
        prompt = selector.find("option", value="0")
        prompt_text = prompt.get_text(" ", strip=True).casefold() if prompt else ""
        page_type = next(
            (value for label, value in SELECTOR_TYPES.items() if label in prompt_text),
            "C",
        )
        options: list[tuple[str, str, str]] = []
        level: int | None = None
        for option in selector.find_all("option"):
            match = OPTION_PATTERN.match(str(option.get("value", "")))
            if not match:
                continue
            option_level = int(match.group("level"))
            if option_level in existing_levels:
                continue
            level = option_level
            options.append((match.group("ne"), match.group("value"), page_type))
        if level is not None and options:
            candidates.append((level, page_type, options))
    if not candidates:
        return []
    level, _, options = min(candidates, key=lambda item: item[0])
    children = []
    for ne_value, level_value, page_type in options:
        child_query = dict(query)
        child_query.update(
            {
                "tpe": page_type,
                f"lev{level}": level_value,
                f"levsut{level}": str(level),
                f"ne{level}": ne_value,
                f"es{level}": "S",
            }
        )
        children.append(
            urlunparse(parsed._replace(query=urlencode(child_query)))
        )
    return children


def crawl_and_reconcile(
    *,
    settings: Settings,
    category: str,
    election_date: date,
    max_requests: int | None = None,
) -> dict[str, int | bool | str | None]:
    database = Database(settings.database_path)
    database.store_reconciliation_run(
        category=category, election_date=election_date, status="running"
    )
    database.seed_official_verification_queue(
        category=category, election_date=election_date
    )
    service = EligendoService(settings, database)
    frontier = deque([root_url(category, election_date)])
    seen: set[str] = set()
    municipality_pages: dict[tuple[str, str, str], list[PageResult]] = defaultdict(list)
    network_requests = 0
    errors = 0
    complete = True
    available = True
    rendered_label: str | None = None
    root_request_url = frontier[0]
    rendered_date: date | None = None
    try:
        while frontier:
            url = frontier.popleft()
            if url in seen:
                continue
            seen.add(url)
            cached = database.latest_snapshot(url)
            if cached is not None and cached.geography.comune:
                page = cached
                html = None
            else:
                if max_requests is not None and network_requests >= max_requests:
                    complete = False
                    break
                try:
                    download, attempts = download_with_backoff(
                        service.http,
                        url,
                        max_bytes=5_000_000,
                    )
                    network_requests += attempts
                    html = download.content
                    if url == root_request_url:
                        rendered_label, rendered_date = heading_election(html)
                        expected_label = CATEGORY_HEADINGS[category]
                        label_matches = (
                            rendered_label is not None
                            and expected_label in rendered_label.casefold()
                        )
                        if rendered_date != election_date or not label_matches:
                            available = False
                            result: dict[str, int | bool | str | None] = {
                                "complete": True,
                                "available": False,
                                "rendered_election": rendered_label,
                                "rendered_date": (
                                    rendered_date.isoformat()
                                    if rendered_date is not None
                                    else None
                                ),
                                "network_requests": network_requests,
                                "pages_seen": len(seen),
                                "municipality_pages": 0,
                                "municipalities_verified": 0,
                                "errors": 0,
                            }
                            database.store_reconciliation_run(
                                category=category,
                                election_date=election_date,
                                status="unavailable",
                                result=result,
                            )
                            return result
                    try:
                        page = parse_page_html(html, download.final_url)
                    except ValueError as exc:
                        if "Results table not found" not in str(exc):
                            raise
                        page = None
                except Exception as exc:  # the queue remains resumable after an upstream error
                    errors += 1
                    complete = False
                    print(f"ERROR {url}: {exc}", file=sys.stderr, flush=True)
                    break
            if page is not None and page.geography.comune:
                if cached is None:
                    database.store_snapshot(page)
                municipality = canonical_municipality(page.geography.comune)
                if municipality:
                    key = (
                        slug(page.geography.provincia or page.geography.regione or ""),
                        slug(municipality),
                        str(page.election.date),
                    )
                    municipality_pages[key].append(page)
                continue
            if html is None:
                continue
            frontier.extend(
                selector_children(
                    html,
                    page.source_url if page is not None else download.final_url,
                )
            )

        verified = 0
        if complete:
            for pages in municipality_pages.values():
                service.verify_official_page_results(
                    pages,
                    store=True,
                    complete_set=True,
                )
                verified += 1
                if verified % 100 == 0:
                    print(f"verified {verified} municipalities", flush=True)
        result = {
            "complete": complete,
            "available": available,
            "rendered_election": rendered_label,
            "rendered_date": (
                rendered_date.isoformat() if rendered_date is not None else None
            ),
            "network_requests": network_requests,
            "pages_seen": len(seen),
            "municipality_pages": sum(len(pages) for pages in municipality_pages.values()),
            "municipalities_verified": verified,
            "errors": errors,
        }
        database.store_reconciliation_run(
            category=category,
            election_date=election_date,
            status="complete" if complete else "partial",
            result=result,
        )
        return result
    except Exception as exc:
        database.store_reconciliation_run(
            category=category,
            election_date=election_date,
            status="failed",
            error=str(exc),
        )
        raise
    finally:
        service.close()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Reconcile one imported election with official municipality pages."
    )
    parser.add_argument("--category", choices=sorted(CATEGORY_CODES), required=True)
    parser.add_argument("--date", type=date.fromisoformat, required=True)
    parser.add_argument("--database", type=Path)
    parser.add_argument("--max-requests", type=int)
    args = parser.parse_args()
    settings = Settings.from_environment()
    if args.database:
        settings = Settings(
            data_dir=settings.data_dir,
            database_path=args.database.resolve(),
            request_interval_seconds=settings.request_interval_seconds,
            request_timeout_seconds=settings.request_timeout_seconds,
            catalogue_ttl_seconds=settings.catalogue_ttl_seconds,
            max_archive_bytes=settings.max_archive_bytes,
            max_uncompressed_bytes=settings.max_uncompressed_bytes,
        )
    result = crawl_and_reconcile(
        settings=settings,
        category=args.category,
        election_date=args.date,
        max_requests=args.max_requests,
    )
    print(result)


if __name__ == "__main__":
    main()
