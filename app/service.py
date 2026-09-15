from __future__ import annotations

import hashlib
import threading
import time
from datetime import date

from .archive import parse_zip_archive
from .catalogue import CATALOGUE_URL, catalogue_matches, parse_catalogue_html
from .config import Settings
from .database import Database
from .http_client import SafeHttpClient
from .schemas import (
    ArchiveImportResult,
    CatalogueEntry,
    MunicipalYearImportResult,
    PageResult,
)
from .scraper import parse_page_html


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

    def _import_entry(self, entry: CatalogueEntry) -> ArchiveImportResult:
        if entry.election_date is None:
            raise ValueError(f"File {entry.filename!r} has no election date.")
        download = self.http.get(
            entry.download_url, max_bytes=self.settings.max_archive_bytes
        )
        rows = parse_zip_archive(
            download.content,
            max_uncompressed_bytes=self.settings.max_uncompressed_bytes,
        )
        digest = hashlib.sha256(download.content).hexdigest()
        catalogue_id = self.database.replace_archive(entry, sha256=digest, rows=rows)
        party_rows = self.database.party_result_count(catalogue_id)
        return ArchiveImportResult(
            catalogue_id=catalogue_id,
            category=entry.category,
            election_date=entry.election_date,
            filename=entry.filename,
            sha256=digest,
            files=len({row.file_name for row in rows}),
            rows=len(rows),
            party_rows=party_rows,
        )

    def import_municipal_year(
        self, *, year: int, continue_on_error: bool = True
    ) -> MunicipalYearImportResult:
        entries = self.filtered_catalogue(category="comunali", year=year)
        imports: list[ArchiveImportResult] = []
        errors: list[dict[str, str]] = []
        for entry in entries:
            try:
                imports.append(self._import_entry(entry))
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
