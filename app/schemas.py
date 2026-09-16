from __future__ import annotations

from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, HttpUrl


class ElectionInfo(BaseModel):
    code: str | None = None
    name: str
    date: date


class Geography(BaseModel):
    area: str | None = None
    regione: str | None = None
    circoscrizione: str | None = None
    provincia: str | None = None
    comune: str | None = None
    query_codes: dict[str, str] = Field(default_factory=dict)


class ResultRecord(BaseModel):
    record_type: Literal["candidate", "list", "coalition_total", "total", "option"]
    record_id: str | None = None
    parent_id: str | None = None
    name: str
    status: str | None = None
    votes: int | None = None
    percentage: float | None = None
    seats: int | None = None
    symbol_url: str | None = None
    raw_cells: list[str] = Field(default_factory=list)


class PageResult(BaseModel):
    source_url: str
    retrieved_at: datetime
    election: ElectionInfo
    geography: Geography
    summary: dict[str, int | float | str | None]
    records: list[ResultRecord]


class PageRequest(BaseModel):
    url: HttpUrl
    store: bool = False


class CatalogueEntry(BaseModel):
    category: str
    year: int | None = None
    relative_path: str
    filename: str
    election_date: date | None = None
    identifier: str | None = None
    download_url: str


class ArchiveImportRequest(BaseModel):
    category: str
    election_date: date


class ArchiveImportResult(BaseModel):
    catalogue_id: int
    category: str
    election_date: date
    filename: str
    sha256: str
    files: int
    rows: int
    party_rows: int = 0
    result_rows: int = 0


class ArchiveRowsResponse(BaseModel):
    count: int
    limit: int
    offset: int
    rows: list[dict[str, Any]]


class MunicipalityEntry(BaseModel):
    comune: str
    provincia: str | None = None
    regione: str | None = None
    rows: int


class MunicipalitiesResponse(BaseModel):
    count: int
    municipalities: list[MunicipalityEntry]


class PartyResultRow(BaseModel):
    data: date
    regione: str | None = None
    provincia: str | None = None
    comune: str
    partito: str
    voti: int
    turno: int | None = None
    candidato: str | None = None
    seggi: int | None = None
    fonte_file: str
    fonte_riga: int


class PartyResultsResponse(BaseModel):
    count: int
    limit: int
    offset: int
    rows: list[PartyResultRow]


class MunicipalYearImportRequest(BaseModel):
    year: int = Field(ge=1946, le=2100)
    continue_on_error: bool = True


class MunicipalYearImportResult(BaseModel):
    year: int
    archives_found: int
    archives_imported: int
    party_rows: int
    imports: list[ArchiveImportResult]
    errors: list[dict[str, str]]


ElectionCategory = Literal[
    "assemblea_costituente",
    "camera",
    "senato",
    "europee",
    "referendum",
    "regionali",
    "provinciali",
    "comunali",
]


class HistoryImportRequest(BaseModel):
    categories: list[ElectionCategory] = Field(
        default_factory=lambda: [
            "assemblea_costituente",
            "camera",
            "senato",
            "europee",
            "referendum",
            "regionali",
            "provinciali",
            "comunali",
        ]
    )
    start_year: int | None = Field(default=None, ge=1946, le=2100)
    end_year: int | None = Field(default=None, ge=1946, le=2100)
    skip_existing: bool = True
    continue_on_error: bool = True


class HistoryImportResult(BaseModel):
    categories: list[str]
    start_year: int | None
    end_year: int | None
    archives_found: int
    archives_imported: int
    archives_skipped: int
    result_rows: int
    imports: list[ArchiveImportResult]
    errors: list[dict[str, str]]


class ElectionResultRow(BaseModel):
    tipo_elezione: str
    data: date
    turno: int | None = None
    regione: str | None = None
    circoscrizione: str | None = None
    provincia: str | None = None
    comune: str | None = None
    nazione: str | None = None
    collegio: str | None = None
    numero_quesito: str | None = None
    quesito: str | None = None
    tipo_risultato: str
    soggetto: str
    partito: str | None = None
    candidato: str | None = None
    opzione_referendum: str | None = None
    voti: int
    percentuale: float | None = None
    seggi: int | None = None
    elettori: int | None = None
    elettori_maschi: int | None = None
    votanti: int | None = None
    votanti_maschi: int | None = None
    affluenza_pct: float | None = None
    voti_validi: int | None = None
    voti_validi_liste: int | None = None
    voti_validi_candidato: int | None = None
    schede_bianche: int | None = None
    schede_non_valide: int | None = None
    schede_contestate: int | None = None
    fonte_url: str
    fonte_file: str
    fonte_riga: int
    sha256: str


class ElectionResultsResponse(BaseModel):
    count: int
    limit: int
    offset: int
    rows: list[ElectionResultRow]


class MunicipalityCoverageRow(BaseModel):
    tipo_elezione: str
    data: date
    filename: str
    regione: str
    comune: str
    stato: Literal[
        "present",
        "missing",
        "not_available_at_municipality_level",
    ]
    righe_comune: int
    righe_livello_comunale: int
    fonte_url: str
    sha256: str


class MunicipalityCoverageResponse(BaseModel):
    regione: str
    comune: str
    elections_checked: int
    present: int
    missing: int
    not_available_at_municipality_level: int
    rows: list[MunicipalityCoverageRow]
