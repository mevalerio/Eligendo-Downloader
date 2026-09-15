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
