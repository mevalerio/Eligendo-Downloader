from __future__ import annotations

import csv
import io
from contextlib import asynccontextmanager
from datetime import date
from typing import Annotated

from fastapi import FastAPI, Query, Request
from fastapi.responses import JSONResponse, StreamingResponse

from . import __version__
from .config import settings
from .database import Database
from .http_client import UnsafeUrlError, UpstreamError
from .schemas import (
    ArchiveImportRequest,
    ArchiveImportResult,
    ArchiveRowsResponse,
    CatalogueEntry,
    ElectionResultsResponse,
    DistrictMapVersionEntry,
    ElectoralLawDownloadRequest,
    ElectoralLawDownloadResult,
    ElectoralLawEntry,
    HistoryImportRequest,
    HistoryImportResult,
    MunicipalYearImportRequest,
    MunicipalYearImportResult,
    MunicipalitiesResponse,
    MunicipalityCoverageResponse,
    MunicipalityAuditResponse,
    NationalGeographyResponse,
    OfficialMunicipalityPagesVerificationRequest,
    OfficialMunicipalityVerificationRequest,
    OfficialMunicipalityVerificationResponse,
    OfficialVerificationQueueResponse,
    OfficialVerificationQueueSeedRequest,
    PageRequest,
    PageResult,
    PartyResultsResponse,
)
from .service import EligendoService


database = Database(settings.database_path)
service = EligendoService(settings, database)


@asynccontextmanager
async def lifespan(_: FastAPI):
    yield
    service.close()


app = FastAPI(
    title="Eligendo API",
    version=__version__,
    description=(
        "Local API for querying and normalising the Italian Ministry of the "
        "Interior's historical election archive."
    ),
    lifespan=lifespan,
)


@app.exception_handler(UnsafeUrlError)
async def unsafe_url_handler(_: Request, exc: UnsafeUrlError) -> JSONResponse:
    return JSONResponse(status_code=400, content={"detail": str(exc)})


@app.exception_handler(UpstreamError)
async def upstream_error_handler(_: Request, exc: UpstreamError) -> JSONResponse:
    return JSONResponse(status_code=502, content={"detail": str(exc)})


@app.exception_handler(ValueError)
async def value_error_handler(_: Request, exc: ValueError) -> JSONResponse:
    return JSONResponse(status_code=422, content={"detail": str(exc)})


@app.get("/", tags=["system"])
def root() -> dict[str, str]:
    return {
        "name": "Eligendo API",
        "version": __version__,
        "documentation": "/docs",
        "source": "https://elezionistorico.interno.gov.it/",
    }


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    return {"status": "ok", "database": str(settings.database_path)}


@app.get("/api/v1/catalogue", response_model=list[CatalogueEntry], tags=["catalogue"])
def get_catalogue(
    category: str | None = None,
    year: Annotated[int | None, Query(ge=1946, le=2100)] = None,
) -> list[CatalogueEntry]:
    """List files published in the official Open Data catalogue."""
    return service.filtered_catalogue(category=category, year=year)


@app.post("/api/v1/pages/parse", response_model=PageResult, tags=["pages"])
def parse_page(request: PageRequest) -> PageResult:
    """Download and normalise one page from the historical archive."""
    return service.fetch_page(str(request.url), store=request.store)


@app.post(
    "/api/v1/history/audit/official-municipality-page",
    response_model=OfficialMunicipalityVerificationResponse,
    tags=["history"],
)
def verify_official_municipality_page(
    request: OfficialMunicipalityVerificationRequest,
) -> dict[str, object]:
    """Compare reconstructed totals with an official municipality page."""
    return service.verify_official_municipality_page(
        str(request.url),
        store=request.store,
        relative_tolerance=request.relative_tolerance,
        complete_set=request.complete_set,
    )


@app.post(
    "/api/v1/history/audit/official-municipality-pages",
    response_model=OfficialMunicipalityVerificationResponse,
    tags=["history"],
)
def verify_official_municipality_pages(
    request: OfficialMunicipalityPagesVerificationRequest,
) -> dict[str, object]:
    """Aggregate split official pages and compare them with local totals."""
    return service.verify_official_municipality_pages(
        [str(url) for url in request.urls],
        store=request.store,
        relative_tolerance=request.relative_tolerance,
        complete_set=request.complete_set,
    )


@app.post(
    "/api/v1/history/reconciliation/queue",
    tags=["history"],
)
def seed_official_verification_queue(
    request: OfficialVerificationQueueSeedRequest,
) -> dict[str, int]:
    """Seed resumable municipality checks from imported ZIP results."""
    changed = database.seed_official_verification_queue(
        category=request.tipo_elezione,
        election_date=request.data,
    )
    return {"inserted_or_updated": changed}


@app.get(
    "/api/v1/history/reconciliation/queue",
    response_model=OfficialVerificationQueueResponse,
    tags=["history"],
)
def get_official_verification_queue(
    tipo_elezione: str | None = None,
    data: date | None = None,
    stato: str | None = None,
    limit: Annotated[int, Query(ge=1, le=5000)] = 1000,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> dict[str, object]:
    """List pending, partial, verified, or failed municipality checks."""
    allowed_categories = {"camera", "senato", "europee", "regionali", "comunali"}
    allowed_statuses = {"pending", "partial", "verified", "failed"}
    if tipo_elezione is not None and tipo_elezione not in allowed_categories:
        raise ValueError("Unsupported election category.")
    if stato is not None and stato not in allowed_statuses:
        raise ValueError("Unsupported queue status.")
    count, rows = database.official_verification_queue(
        category=tipo_elezione,
        election_date=data,
        status=stato,
        limit=limit,
        offset=offset,
    )
    return {"count": count, "limit": limit, "offset": offset, "rows": rows}


@app.post(
    "/api/v1/archives/import",
    response_model=ArchiveImportResult,
    tags=["archives"],
)
def import_archive(request: ArchiveImportRequest) -> ArchiveImportResult:
    """Download an official Open Data ZIP archive and import it into SQLite."""
    return service.import_archive(
        category=request.category,
        election_date=request.election_date,
    )


@app.get(
    "/api/v1/archives/results",
    response_model=ArchiveRowsResponse,
    tags=["archives"],
)
def archive_results(
    category: str,
    election_date: date,
    comune: str | None = None,
    provincia: str | None = None,
    limit: Annotated[int, Query(ge=1, le=5000)] = 1000,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> ArchiveRowsResponse:
    """Query imported rows, including municipality-level filtering."""
    count, rows = database.query_archive(
        category=category,
        election_date=election_date,
        municipality=comune,
        province=provincia,
        limit=limit,
        offset=offset,
    )
    return ArchiveRowsResponse(count=count, limit=limit, offset=offset, rows=rows)


@app.get(
    "/api/v1/archives/municipalities",
    response_model=MunicipalitiesResponse,
    tags=["archives"],
)
def archive_municipalities(
    category: str,
    election_date: date,
) -> MunicipalitiesResponse:
    """List municipalities found in an imported election."""
    municipalities = database.list_municipalities(
        category=category,
        election_date=election_date,
    )
    return MunicipalitiesResponse(
        count=len(municipalities),
        municipalities=municipalities,
    )


@app.post(
    "/api/v1/history/import",
    response_model=HistoryImportResult,
    tags=["history"],
)
def import_history(request: HistoryImportRequest) -> HistoryImportResult:
    """Import every matching election archive with resumable skipping."""
    return service.import_history(
        categories=list(request.categories),
        start_year=request.start_year,
        end_year=request.end_year,
        skip_existing=request.skip_existing,
        continue_on_error=request.continue_on_error,
    )


@app.get(
    "/api/v1/history/results",
    response_model=ElectionResultsResponse,
    tags=["history"],
)
def historical_results(
    category: str | None = None,
    year: Annotated[int | None, Query(ge=1946, le=2100)] = None,
    election_date: date | None = None,
    regione: str | None = None,
    provincia: str | None = None,
    comune: str | None = None,
    tipo_risultato: str | None = None,
    soggetto: str | None = None,
    turno: Annotated[int | None, Query(ge=1)] = None,
    limit: Annotated[int, Query(ge=1, le=5000)] = 1000,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> ElectionResultsResponse:
    """Return paginated normalised results for every election category."""
    count, rows = database.query_election_results(
        category=category,
        year=year,
        election_date=election_date,
        region=regione,
        province=provincia,
        municipality=comune,
        result_type=tipo_risultato,
        subject=soggetto,
        round_number=turno,
        limit=limit,
        offset=offset,
    )
    return ElectionResultsResponse(count=count, limit=limit, offset=offset, rows=rows)


HISTORY_CSV_FIELDS = [
    "TIPO_ELEZIONE",
    "DATA",
    "TURNO",
    "REGIONE",
    "CIRCOSCRIZIONE",
    "PROVINCIA",
    "COMUNE",
    "CHIAVE_COMUNE_TORNATA",
    "STATO_LOCALIZZAZIONE",
    "NAZIONE",
    "COLLEGIO",
    "NUMERO_QUESITO",
    "QUESITO",
    "TIPO_RISULTATO",
    "SOGGETTO",
    "PARTITO",
    "CANDIDATO",
    "OPZIONE_REFERENDUM",
    "VOTI",
    "PERCENTUALE",
    "SEGGI",
    "ELETTORI",
    "ELETTORI_MASCHI",
    "VOTANTI",
    "VOTANTI_MASCHI",
    "AFFLUENZA_PCT",
    "VOTI_VALIDI",
    "VOTI_VALIDI_LISTE",
    "VOTI_VALIDI_CANDIDATO",
    "SCHEDE_BIANCHE",
    "SCHEDE_NON_VALIDE",
    "SCHEDE_CONTESTATE",
    "FONTE_URL",
    "FONTE_FILE",
    "FONTE_RIGA",
    "SHA256",
]


@app.get("/api/v1/history/results.csv", tags=["history"])
def historical_results_csv(
    category: str | None = None,
    year: Annotated[int | None, Query(ge=1946, le=2100)] = None,
    election_date: date | None = None,
    regione: str | None = None,
    provincia: str | None = None,
    comune: str | None = None,
    tipo_risultato: str | None = None,
    soggetto: str | None = None,
    turno: Annotated[int | None, Query(ge=1)] = None,
) -> StreamingResponse:
    """Stream a semicolon-delimited UTF-8 export of all matching elections."""

    def generate_csv():
        buffer = io.StringIO()
        writer = csv.DictWriter(
            buffer,
            fieldnames=HISTORY_CSV_FIELDS,
            delimiter=";",
            lineterminator="\n",
        )
        buffer.write("\ufeff")
        writer.writeheader()
        yield buffer.getvalue()
        buffer.seek(0)
        buffer.truncate(0)
        for row in database.iter_election_results(
            category=category,
            year=year,
            election_date=election_date,
            region=regione,
            province=provincia,
            municipality=comune,
            result_type=tipo_risultato,
            subject=soggetto,
            round_number=turno,
        ):
            writer.writerow({field: row[field.casefold()] for field in HISTORY_CSV_FIELDS})
            yield buffer.getvalue()
            buffer.seek(0)
            buffer.truncate(0)

    label = str(year) if year is not None else "all"
    return StreamingResponse(
        generate_csv(),
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": (
                f'attachment; filename="all_election_results_{label}.csv"'
            )
        },
    )


NATIONAL_GEOGRAPHY_CSV_FIELDS = [
    "TIPO_ELEZIONE",
    "DATA",
    "LIVELLO",
    "REGIONE",
    "CIRCOSCRIZIONE",
    "PROVINCIA",
    "COMUNE",
    "NAZIONE",
    "COLLEGIO",
    "TURNO",
    "NUMERO_QUESITO",
    "RIGHE",
    "SOGGETTI",
    "ELETTORI",
    "VOTANTI",
    "VOTI_VALIDI",
    "FONTE_FILE",
    "FONTE_FILE_COUNT",
    "FONTE_URL",
    "SHA256",
]


@app.get(
    "/api/v1/history/coverage/national",
    response_model=NationalGeographyResponse,
    tags=["history"],
)
def national_history_geography(
    category: str | None = None,
    year: Annotated[int | None, Query(ge=1946, le=2100)] = None,
    election_date: date | None = None,
    regione: str | None = None,
    provincia: str | None = None,
    comune: str | None = None,
    limit: Annotated[int, Query(ge=1, le=5000)] = 1000,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> NationalGeographyResponse:
    """List the geographic units present in each imported national election."""
    count, rows = database.query_national_geography(
        category=category,
        year=year,
        election_date=election_date,
        region=regione,
        province=provincia,
        municipality=comune,
        limit=limit,
        offset=offset,
    )
    return NationalGeographyResponse(count=count, limit=limit, offset=offset, rows=rows)


@app.get("/api/v1/history/coverage/national.csv", tags=["history"])
def national_history_geography_csv(
    category: str | None = None,
    year: Annotated[int | None, Query(ge=1946, le=2100)] = None,
    election_date: date | None = None,
    regione: str | None = None,
    provincia: str | None = None,
    comune: str | None = None,
) -> StreamingResponse:
    """Stream the national-election geography table as semicolon-delimited CSV."""

    def generate_csv():
        buffer = io.StringIO()
        writer = csv.DictWriter(
            buffer,
            fieldnames=NATIONAL_GEOGRAPHY_CSV_FIELDS,
            delimiter=";",
            lineterminator="\n",
        )
        buffer.write("\ufeff")
        writer.writeheader()
        yield buffer.getvalue()
        buffer.seek(0)
        buffer.truncate(0)
        for row in database.iter_national_geography(
            category=category,
            year=year,
            election_date=election_date,
            region=regione,
            province=provincia,
            municipality=comune,
        ):
            writer.writerow(
                {
                    field: row[
                        "file_count" if field == "FONTE_FILE_COUNT" else field.casefold()
                    ]
                    for field in NATIONAL_GEOGRAPHY_CSV_FIELDS
                }
            )
            yield buffer.getvalue()
            buffer.seek(0)
            buffer.truncate(0)

    label = str(year) if year is not None else "all"
    return StreamingResponse(
        generate_csv(),
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": (
                f'attachment; filename="national_geography_{label}.csv"'
            )
        },
    )


@app.get(
    "/api/v1/history/coverage/municipality",
    response_model=MunicipalityCoverageResponse,
    tags=["history"],
)
def municipality_history_coverage(
    regione: str,
    comune: str,
) -> MunicipalityCoverageResponse:
    """Check municipality availability across relevant imported elections."""
    rows = database.municipality_coverage(region=regione, municipality=comune)
    counts = {
        status: sum(row["stato"] == status for row in rows)
        for status in (
            "present",
            "missing",
            "not_available_at_municipality_level",
        )
    }
    return MunicipalityCoverageResponse(
        regione=regione,
        comune=comune,
        elections_checked=len(rows),
        present=counts["present"],
        missing=counts["missing"],
        not_available_at_municipality_level=counts[
            "not_available_at_municipality_level"
        ],
        rows=rows,
    )


@app.get(
    "/api/v1/legal/electoral-laws",
    response_model=list[ElectoralLawEntry],
    tags=["legal"],
)
def electoral_law_catalogue() -> list[dict[str, object]]:
    """List the official electoral laws and college-boundary decrees."""
    return service.electoral_laws()


@app.get(
    "/api/v1/legal/district-maps",
    response_model=list[DistrictMapVersionEntry],
    tags=["legal"],
)
def district_map_catalogue(
    category: str | None = None,
    year: Annotated[int | None, Query(ge=1948, le=2100)] = None,
) -> list[dict[str, object]]:
    """List district-map versions and every official source applied to them."""
    if category not in (None, "camera", "senato"):
        raise ValueError("category must be 'camera' or 'senato'.")
    return service.district_maps(category=category, year=year)


@app.post(
    "/api/v1/legal/electoral-laws/download",
    response_model=ElectoralLawDownloadResult,
    tags=["legal"],
)
def download_electoral_laws(
    request: ElectoralLawDownloadRequest,
) -> dict[str, object]:
    """Download and hash the selected official legal sources."""
    return service.download_electoral_laws(
        ids=request.ids,
        overwrite=request.overwrite,
    )


@app.get(
    "/api/v1/history/audit/municipality",
    response_model=MunicipalityAuditResponse,
    tags=["history"],
)
def audit_municipality_history(
    comune: str,
    category: str | None = None,
    tolleranza_votanti: Annotated[float, Query(ge=0.05, le=0.80)] = 0.35,
    provincia: str | None = None,
    regione: str | None = None,
) -> MunicipalityAuditResponse:
    """Sense-check reconstructed national-election municipality totals."""
    if category not in (None, "camera", "senato"):
        raise ValueError("category must be 'camera' or 'senato'.")
    categories = (category,) if category else ("camera", "senato")
    rows = database.municipality_election_audit(
        municipality=comune,
        categories=categories,
        voter_tolerance=tolleranza_votanti,
        province=provincia,
        region=regione,
    )
    counts = {
        status: sum(row["stato"] == status for row in rows)
        for status in ("pass", "warning", "invalid", "insufficient_data")
    }
    return MunicipalityAuditResponse(
        comune=comune,
        provincia=provincia,
        regione=regione,
        categories=list(categories),
        voter_tolerance=tolleranza_votanti,
        elections_checked=len(rows),
        passed=counts["pass"],
        warnings=counts["warning"],
        invalid=counts["invalid"],
        insufficient_data=counts["insufficient_data"],
        rows=rows,
    )


@app.post(
    "/api/v1/municipal/import-year",
    response_model=MunicipalYearImportResult,
    tags=["municipal"],
)
def import_municipal_year(
    request: MunicipalYearImportRequest,
) -> MunicipalYearImportResult:
    """Import all municipal elections published for a year."""
    return service.import_municipal_year(
        year=request.year,
        continue_on_error=request.continue_on_error,
    )


@app.get(
    "/api/v1/municipal/party-results",
    response_model=PartyResultsResponse,
    tags=["municipal"],
)
def municipal_party_results(
    year: Annotated[int | None, Query(ge=1946, le=2100)] = None,
    election_date: date | None = None,
    comune: str | None = None,
    provincia: str | None = None,
    partito: str | None = None,
    turno: Annotated[int, Query(ge=1)] = 1,
    tutti_turni: bool = False,
    limit: Annotated[int, Query(ge=1, le=5000)] = 1000,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> PartyResultsResponse:
    """Return normalised, paginated municipal party results."""
    count, rows = database.query_party_results(
        year=year,
        election_date=election_date,
        municipality=comune,
        province=provincia,
        party=partito,
        round_number=None if tutti_turni else turno,
        limit=limit,
        offset=offset,
    )
    return PartyResultsResponse(count=count, limit=limit, offset=offset, rows=rows)


@app.get("/api/v1/municipal/party-results.csv", tags=["municipal"])
def municipal_party_results_csv(
    year: Annotated[int | None, Query(ge=1946, le=2100)] = None,
    election_date: date | None = None,
    comune: str | None = None,
    provincia: str | None = None,
    partito: str | None = None,
    turno: Annotated[int, Query(ge=1)] = 1,
    tutti_turni: bool = False,
    dettagliato: bool = False,
) -> StreamingResponse:
    """Export all matching rows as semicolon-delimited UTF-8 CSV."""
    compact_fields = ["DATA", "COMUNE", "PARTITO", "VOTI"]
    detailed_fields = [
        "DATA",
        "REGIONE",
        "PROVINCIA",
        "COMUNE",
        "PARTITO",
        "VOTI",
        "TURNO",
        "CANDIDATO",
        "SEGGI",
        "FONTE_FILE",
        "FONTE_RIGA",
    ]
    fields = detailed_fields if dettagliato else compact_fields

    def generate_csv():
        buffer = io.StringIO()
        writer = csv.DictWriter(
            buffer,
            fieldnames=fields,
            delimiter=";",
            lineterminator="\n",
            extrasaction="ignore",
        )
        buffer.write("\ufeff")
        writer.writeheader()
        yield buffer.getvalue()
        buffer.seek(0)
        buffer.truncate(0)
        for row in database.iter_party_results(
            year=year,
            election_date=election_date,
            municipality=comune,
            province=provincia,
            party=partito,
            round_number=None if tutti_turni else turno,
        ):
            export_row = {
                "DATA": row["data"],
                "REGIONE": row["regione"],
                "PROVINCIA": row["provincia"],
                "COMUNE": row["comune"],
                "PARTITO": row["partito"],
                "VOTI": row["voti"],
                "TURNO": row["turno"],
                "CANDIDATO": row["candidato"],
                "SEGGI": row["seggi"],
                "FONTE_FILE": row["fonte_file"],
                "FONTE_RIGA": row["fonte_riga"],
            }
            writer.writerow(export_row)
            yield buffer.getvalue()
            buffer.seek(0)
            buffer.truncate(0)

    label = str(year) if year is not None else "all"
    filename = f"municipal_party_results_{label}.csv"
    return StreamingResponse(
        generate_csv(),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
