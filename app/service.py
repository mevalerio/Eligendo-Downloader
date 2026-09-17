from __future__ import annotations

import hashlib
import html
import threading
import time
from datetime import date
from pathlib import Path
from urllib.parse import urldefrag, urljoin

from bs4 import BeautifulSoup

from .archive import parse_zip_archive
from .catalogue import CATALOGUE_URL, catalogue_matches, parse_catalogue_html
from .config import Settings
from .database import Database
from .electoral_laws import DISTRICT_MAP_VERSIONS, ELECTORAL_LAWS, LAW_BY_ID
from .history import ELECTION_CATEGORIES
from .http_client import Download, SafeHttpClient
from .schemas import (
    ArchiveImportResult,
    CatalogueEntry,
    HistoryImportResult,
    MunicipalYearImportResult,
    PageResult,
)
from .scraper import parse_page_html
from .utils import slug


OFFICIAL_PAGE_CATEGORIES = {"C": "camera", "S": "senato"}


class EligendoService:
    def __init__(self, settings: Settings, database: Database) -> None:
        self.settings = settings
        self.database = database
        self.http = SafeHttpClient(
            timeout=settings.request_timeout_seconds,
            interval=settings.request_interval_seconds,
        )
        self._catalogue: list[CatalogueEntry] | None = None
        self._catalogue_loaded_at = 0.0
        self._catalogue_lock = threading.Lock()

    def close(self) -> None:
        self.http.close()

    def catalogue(self, *, force: bool = False) -> list[CatalogueEntry]:
        with self._catalogue_lock:
            fresh = (
                self._catalogue is not None
                and time.monotonic() - self._catalogue_loaded_at
                < self.settings.catalogue_ttl_seconds
            )
            if fresh and not force:
                return list(self._catalogue or [])
            download = self.http.get(CATALOGUE_URL)
            self._catalogue = parse_catalogue_html(
                download.content.decode("utf-8", errors="replace")
            )
            self._catalogue_loaded_at = time.monotonic()
            return list(self._catalogue)

    def filtered_catalogue(
        self, *, category: str | None = None, year: int | None = None
    ) -> list[CatalogueEntry]:
        return catalogue_matches(self.catalogue(), category=category, year=year)

    def fetch_page(self, url: str, *, store: bool = False) -> PageResult:
        download = self.http.get(url)
        result = parse_page_html(download.content, download.final_url)
        if store:
            self.database.store_snapshot(result)
        return result

    @staticmethod
    def _value_comparison(
        field: str,
        official: int | None,
        reconstructed: int | None,
        tolerance: float,
    ) -> dict[str, object]:
        if official is None or reconstructed is None:
            return {
                "campo": field,
                "ufficiale": official,
                "ricostruito": reconstructed,
                "scarto": None,
                "scarto_relativo": None,
                "coincide": None,
            }
        difference = reconstructed - official
        relative = abs(difference) / official if official else float(bool(difference))
        return {
            "campo": field,
            "ufficiale": official,
            "ricostruito": reconstructed,
            "scarto": difference,
            "scarto_relativo": round(relative, 8),
            "coincide": relative <= tolerance,
        }

    def verify_official_municipality_page(
        self,
        url: str,
        *,
        store: bool = True,
        relative_tolerance: float = 0.0,
        complete_set: bool = False,
    ) -> dict[str, object]:
        """Compare reconstructed totals with an authoritative municipality page."""
        return self.verify_official_municipality_pages(
            [url],
            store=store,
            relative_tolerance=relative_tolerance,
            complete_set=complete_set,
        )

    def verify_official_municipality_pages(
        self,
        urls: list[str],
        *,
        store: bool = True,
        relative_tolerance: float = 0.0,
        complete_set: bool = False,
    ) -> dict[str, object]:
        """Aggregate official split pages and compare them with local totals."""
        unique_urls = list(dict.fromkeys(urls))
        if not unique_urls:
            raise ValueError("At least one official municipality URL is required.")
        pages = [self.fetch_page(url, store=store) for url in unique_urls]
        page = pages[0]
        category = OFFICIAL_PAGE_CATEGORIES.get((page.election.code or "").upper())
        if category is None:
            raise ValueError(
                "Official municipality verification currently supports Camera "
                "and Senato pages."
            )
        municipality = page.geography.comune
        if not municipality:
            raise ValueError("The official URL must identify one municipality.")
        for component in pages[1:]:
            component_category = OFFICIAL_PAGE_CATEGORIES.get(
                (component.election.code or "").upper()
            )
            if component_category != category:
                raise ValueError("All official pages must use the same chamber.")
            if component.election.date != page.election.date:
                raise ValueError("All official pages must use the same election date.")
            if slug(component.geography.comune or "") != slug(municipality):
                raise ValueError("All official pages must identify the same municipality.")

        audit_rows = self.database.municipality_election_audit(
            municipality=municipality,
            categories=(category,),
        )
        audit = next(
            (
                row
                for row in audit_rows
                if row["data"] == page.election.date.isoformat()
            ),
            None,
        )

        official_lists: dict[str, dict[str, object]] = {}
        for component in pages:
            for record in component.records:
                if record.record_type != "list" or record.votes is None:
                    continue
                key = slug(record.name)
                current = official_lists.setdefault(
                    key,
                    {"name": record.name, "votes": 0},
                )
                current["votes"] = int(current["votes"]) + record.votes

        total_records = [
            record.votes
            for component in pages
            for record in component.records
            if record.record_type == "total" and record.votes is not None
        ]
        official_valid_votes = (
            sum(total_records)
            if total_records
            else sum(int(row["votes"]) for row in official_lists.values())
        )

        def aggregate_summary(field: str) -> int | None:
            values = [component.summary.get(field) for component in pages]
            if not all(isinstance(value, (int, float)) for value in values):
                return None
            return sum(int(value) for value in values)

        official_electors = aggregate_summary("elettori")
        official_voters = aggregate_summary("votanti")

        local_lists: dict[str, dict[str, object]] = {}
        if audit is not None:
            local_lists = {
                row["subject_key"]: row
                for row in self.database.municipality_party_totals(
                    municipality=municipality,
                    category=category,
                    election_date=page.election.date,
                    source_file=str(audit["fonte_file"]),
                    result_type=str(audit["tipo_risultato"]),
                )
            }

        comparisons = [
            self._value_comparison(
                "aventi_diritto",
                official_electors,
                int(audit["aventi_diritto"])
                if audit is not None and audit["aventi_diritto"] is not None
                else None,
                relative_tolerance,
            ),
            self._value_comparison(
                "votanti",
                official_voters,
                int(audit["votanti"])
                if audit is not None and audit["votanti"] is not None
                else None,
                relative_tolerance,
            ),
            self._value_comparison(
                "voti_validi",
                official_valid_votes,
                int(audit["voti_risultato"]) if audit is not None else None,
                relative_tolerance,
            ),
        ]

        parties: list[dict[str, object]] = []
        for key in sorted(official_lists.keys() | local_lists.keys()):
            official = official_lists.get(key)
            local = local_lists.get(key)
            official_votes = int(official["votes"]) if official else None
            local_votes = int(local["votes"]) if local else None
            if official is None:
                party_status = "missing_official"
                difference = None
                relative = None
            elif local is None:
                party_status = "missing_local"
                difference = None
                relative = None
            else:
                difference = local_votes - official_votes
                relative = (
                    abs(difference) / official_votes
                    if official_votes
                    else float(bool(difference))
                )
                if difference == 0:
                    party_status = "match"
                elif relative <= relative_tolerance:
                    party_status = "within_tolerance"
                else:
                    party_status = "mismatch"
            parties.append(
                {
                    "partito_ufficiale": official["name"] if official else None,
                    "partito_ricostruito": local["subject"] if local else None,
                    "voti_ufficiali": official_votes,
                    "voti_ricostruiti": local_votes,
                    "scarto": difference,
                    "scarto_relativo": round(relative, 8) if relative is not None else None,
                    "stato": party_status,
                }
            )

        party_matches = sum(
            row["stato"] in ("match", "within_tolerance") for row in parties
        )
        party_mismatches = len(parties) - party_matches
        if audit is None:
            status = "local_data_missing"
        elif party_mismatches or any(row["coincide"] is False for row in comparisons):
            status = "mismatch"
        elif any(row["stato"] == "within_tolerance" for row in parties) or any(
            row["scarto"] not in (None, 0) for row in comparisons
        ):
            status = "within_tolerance"
        else:
            status = "exact_match"

        verification = {
            "source_url": page.source_url,
            "source_urls": [component.source_url for component in pages],
            "pagine_ufficiali": len(pages),
            "insieme_completo": complete_set,
            "tipo_elezione": category,
            "data": page.election.date,
            "regione": next(
                (component.geography.regione for component in pages if component.geography.regione),
                None,
            ),
            "circoscrizione": next(
                (
                    component.geography.circoscrizione
                    for component in pages
                    if component.geography.circoscrizione
                ),
                None,
            ),
            "provincia": next(
                (
                    component.geography.provincia
                    for component in pages
                    if component.geography.provincia
                ),
                None,
            ),
            "comune": municipality,
            "tolleranza_relativa": relative_tolerance,
            "stato": status,
            "riepilogo": comparisons,
            "partiti_confrontati": len(parties),
            "partiti_coincidenti": party_matches,
            "partiti_non_coincidenti": party_mismatches,
            "partiti": parties,
        }
        if store:
            self.database.store_official_municipality_verification(verification)
        return verification

    def electoral_laws(self) -> list[dict[str, object]]:
        law_dir = self.settings.data_dir / "electoral_laws"
        rows: list[dict[str, object]] = []
        for law in ELECTORAL_LAWS:
            path = law_dir / f"{law.id}.{law.file_format}"
            rows.append(
                {
                    "id": law.id,
                    "date": law.date,
                    "citation": law.citation,
                    "title": law.title,
                    "kind": law.kind,
                    "applies_to": list(law.applies_to),
                    "election_years": law.election_years,
                    "source_url": law.source_url,
                    "download_url": law.download_url,
                    "file_format": law.file_format,
                    "downloaded": path.exists(),
                    "local_path": str(path) if path.exists() else None,
                }
            )
        return rows

    def district_maps(
        self, *, category: str | None = None, year: int | None = None
    ) -> list[dict[str, object]]:
        rows: list[dict[str, object]] = []
        for version in DISTRICT_MAP_VERSIONS:
            if category is not None and version.category != category:
                continue
            if year is not None and not version.start_year <= year <= version.end_year:
                continue
            sources = [LAW_BY_ID[source_id] for source_id in version.source_ids]
            rows.append(
                {
                    "id": version.id,
                    "category": version.category,
                    "start_year": version.start_year,
                    "end_year": version.end_year,
                    "geography_level": version.geography_level,
                    "source_ids": list(version.source_ids),
                    "source_citations": [source.citation for source in sources],
                    "source_urls": [source.source_url for source in sources],
                    "notes": version.notes,
                }
            )
        return rows

    def download_electoral_laws(
        self, *, ids: list[str] | None, overwrite: bool
    ) -> dict[str, object]:
        requested_ids = list(dict.fromkeys(ids or [law.id for law in ELECTORAL_LAWS]))
        unknown = sorted(set(requested_ids) - LAW_BY_ID.keys())
        if unknown:
            raise ValueError(f"Unknown electoral-law ids: {', '.join(unknown)}")

        law_dir = self.settings.data_dir / "electoral_laws"
        law_dir.mkdir(parents=True, exist_ok=True)
        files = []
        downloaded = 0
        reused = 0
        for law_id in requested_ids:
            law = LAW_BY_ID[law_id]
            path = law_dir / f"{law.id}.{law.file_format}"
            content_type = None
            was_downloaded = overwrite or not path.exists()
            if was_downloaded:
                response = self.http.get(
                    law.download_url,
                    max_bytes=self.settings.max_archive_bytes,
                )
                content = response.content
                if law.file_format == "html":
                    content = self._complete_gazette_html(response)
                temporary = Path(f"{path}.part")
                temporary.write_bytes(content)
                temporary.replace(path)
                content_type = response.content_type
                downloaded += 1
            else:
                reused += 1
            content = path.read_bytes()
            files.append(
                {
                    "id": law.id,
                    "local_path": str(path),
                    "sha256": hashlib.sha256(content).hexdigest(),
                    "bytes": len(content),
                    "content_type": content_type,
                    "downloaded": was_downloaded,
                }
            )
        return {
            "requested": len(requested_ids),
            "downloaded": downloaded,
            "reused": reused,
            "files": files,
        }

    def _complete_gazette_html(self, menu: Download) -> bytes:
        """Combine a Gazzetta act menu and all linked articles into one HTML file."""
        text = menu.content.decode("utf-8", errors="replace")
        soup = BeautifulSoup(text, "html.parser")
        article_urls: list[str] = []
        seen: set[str] = set()
        for link in soup.select('a[href*="caricaArticolo"]'):
            href = link.get("href")
            if not isinstance(href, str):
                continue
            url = urldefrag(urljoin(menu.final_url, href))[0]
            if url not in seen:
                seen.add(url)
                article_urls.append(url)

        sections = [
            '<section data-source-role="act-menu">',
            text,
            "</section>",
        ]
        for index, url in enumerate(article_urls, start=1):
            article = self.http.get(
                url,
                max_bytes=self.settings.max_archive_bytes,
            )
            article_text = article.content.decode("utf-8", errors="replace")
            sections.extend(
                [
                    (
                        f'<section data-source-role="article" '
                        f'data-source-index="{index}" '
                        f'data-source-url="{html.escape(article.final_url, quote=True)}">'
                    ),
                    article_text,
                    "</section>",
                ]
            )
        return (
            "<!doctype html>\n<html><head><meta charset=\"utf-8\">"
            "<title>Official Gazzetta Ufficiale act bundle</title></head><body>\n"
            + "\n".join(sections)
            + "\n</body></html>\n"
        ).encode("utf-8")

    def import_archive(self, *, category: str, election_date: date) -> ArchiveImportResult:
        candidates = [
            entry
            for entry in self.catalogue()
            if entry.category == category and entry.election_date == election_date
        ]
        if not candidates:
            raise ValueError(
                f"Archive not found for category={category!r}, "
                f"election_date={election_date.isoformat()!r}."
            )
        if len(candidates) > 1:
            raise ValueError(
                "More than one archive matches the request; use the catalogue "
                "to identify the required file."
            )
        return self._import_entry(candidates[0])

    def _import_entry(
        self,
        entry: CatalogueEntry,
        *,
        municipality_level_only: bool = False,
    ) -> ArchiveImportResult:
        if entry.election_date is None:
            raise ValueError(f"File {entry.filename!r} has no election date.")
        download = self.http.get(
            entry.download_url, max_bytes=self.settings.max_archive_bytes
        )
        rows = parse_zip_archive(
            download.content,
            max_uncompressed_bytes=self.settings.max_uncompressed_bytes,
            municipality_level_only=municipality_level_only,
        )
        digest = hashlib.sha256(download.content).hexdigest()
        catalogue_id = self.database.replace_archive(entry, sha256=digest, rows=rows)
        party_rows = self.database.party_result_count(catalogue_id)
        result_rows = self.database.election_result_count(catalogue_id)
        return ArchiveImportResult(
            catalogue_id=catalogue_id,
            category=entry.category,
            election_date=entry.election_date,
            filename=entry.filename,
            sha256=digest,
            files=len({row.file_name for row in rows}),
            rows=len(rows),
            party_rows=party_rows,
            result_rows=result_rows,
        )

    def import_history(
        self,
        *,
        categories: list[str],
        start_year: int | None = None,
        end_year: int | None = None,
        skip_existing: bool = True,
        continue_on_error: bool = True,
    ) -> HistoryImportResult:
        requested = list(dict.fromkeys(categories))
        invalid = sorted(set(requested) - ELECTION_CATEGORIES)
        if invalid:
            raise ValueError(f"Unsupported election categories: {', '.join(invalid)}")
        if start_year is not None and end_year is not None and start_year > end_year:
            raise ValueError("start_year must be less than or equal to end_year.")

        entries = [
            entry
            for entry in self.catalogue()
            if (
                entry.category in requested
                and entry.election_date is not None
                and (start_year is None or entry.election_date.year >= start_year)
                and (end_year is None or entry.election_date.year <= end_year)
            )
        ]
        entries.sort(
            key=lambda entry: (
                entry.election_date or date.min,
                entry.category,
                entry.filename,
            )
        )

        imports: list[ArchiveImportResult] = []
        errors: list[dict[str, str]] = []
        skipped = 0
        for entry in entries:
            if skip_existing and self.database.archive_is_normalised(entry):
                skipped += 1
                continue
            try:
                imports.append(
                    self._import_entry(entry, municipality_level_only=True)
                )
            except Exception as exc:
                errors.append(
                    {
                        "category": entry.category,
                        "filename": entry.filename,
                        "election_date": (
                            entry.election_date.isoformat() if entry.election_date else ""
                        ),
                        "error": str(exc),
                    }
                )
                if not continue_on_error:
                    raise

        return HistoryImportResult(
            categories=requested,
            start_year=start_year,
            end_year=end_year,
            archives_found=len(entries),
            archives_imported=len(imports),
            archives_skipped=skipped,
            result_rows=sum(result.result_rows for result in imports),
            imports=imports,
            errors=errors,
        )

    def import_municipal_year(
        self, *, year: int, continue_on_error: bool = True
    ) -> MunicipalYearImportResult:
        entries = self.filtered_catalogue(category="comunali", year=year)
        imports: list[ArchiveImportResult] = []
        errors: list[dict[str, str]] = []
        for entry in entries:
            try:
                imports.append(
                    self._import_entry(entry, municipality_level_only=True)
                )
            except Exception as exc:
                errors.append(
                    {
                        "filename": entry.filename,
                        "election_date": (
                            entry.election_date.isoformat() if entry.election_date else ""
                        ),
                        "error": str(exc),
                    }
                )
                if not continue_on_error:
                    raise
        return MunicipalYearImportResult(
            year=year,
            archives_found=len(entries),
            archives_imported=len(imports),
            party_rows=sum(result.party_rows for result in imports),
            imports=imports,
            errors=errors,
        )
