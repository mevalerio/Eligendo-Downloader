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
    round: int | None = None
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


class OfficialMunicipalityVerificationRequest(BaseModel):
    url: HttpUrl
    store: bool = True
    relative_tolerance: float = Field(default=0.0, ge=0.0, le=0.10)
    complete_set: bool = False


class OfficialMunicipalityPagesVerificationRequest(BaseModel):
    urls: list[HttpUrl] = Field(min_length=1)
    store: bool = True
    relative_tolerance: float = Field(default=0.0, ge=0.0, le=0.10)
    complete_set: bool = False


class OfficialValueComparison(BaseModel):
    campo: Literal["aventi_diritto", "votanti", "voti_validi"]
    ufficiale: int | None = None
    ricostruito: int | None = None
    scarto: int | None = None
    scarto_relativo: float | None = None
    coincide: bool | None = None


class OfficialPartyComparison(BaseModel):
    partito_ufficiale: str | None = None
    partito_ricostruito: str | None = None
    voti_ufficiali: int | None = None
    voti_ricostruiti: int | None = None
    scarto: int | None = None
    scarto_relativo: float | None = None
    stato: Literal[
        "match",
        "within_tolerance",
        "mismatch",
        "missing_local",
        "missing_official",
    ]


class OfficialMunicipalityVerificationResponse(BaseModel):
    source_url: str
    source_urls: list[str]
    pagine_ufficiali: int
    insieme_completo: bool
    tipo_elezione: Literal["camera", "senato", "europee", "regionali", "comunali"]
    data: date
    regione: str | None = None
    circoscrizione: str | None = None
    provincia: str | None = None
    comune: str
    tolleranza_relativa: float
    stato: Literal[
        "exact_match",
        "within_tolerance",
        "mismatch",
        "local_data_missing",
    ]
    riepilogo: list[OfficialValueComparison]
    partiti_confrontati: int
    partiti_coincidenti: int
    partiti_non_coincidenti: int
    partiti: list[OfficialPartyComparison]
    risultati_ufficiali: list[dict[str, Any]] = Field(default_factory=list)


class OfficialVerificationQueueSeedRequest(BaseModel):
    tipo_elezione: Literal["camera", "senato", "europee", "regionali", "comunali"]
    data: date


class OfficialVerificationQueueRow(BaseModel):
    id: int
    tipo_elezione: str
    data: date
    turno: int | None = None
    regione: str | None = None
    provincia: str | None = None
    comune: str
    priorita: int
    stato: Literal["pending", "partial", "verified", "failed"]
    tentativi: int
    fonti: list[str]
    ultimo_errore: str | None = None
    aggiornato_il: datetime


class OfficialVerificationQueueResponse(BaseModel):
    count: int
    limit: int
    offset: int
    rows: list[OfficialVerificationQueueRow]


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
    chiave_comune_tornata: str | None = None
    stato_localizzazione: Literal[
        "non_municipal",
        "region_province_municipality",
        "province_municipality",
        "region_municipality_incomplete",
        "municipality_incomplete",
    ]
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


class NationalGeographyRow(BaseModel):
    tipo_elezione: str
    data: date
    livello: Literal["comune", "provincia", "regione", "nazione", "nazionale"]
    regione: str | None = None
    circoscrizione: str | None = None
    provincia: str | None = None
    comune: str | None = None
    nazione: str | None = None
    collegio: str | None = None
    turno: int | None = None
    numero_quesito: str | None = None
    righe: int
    soggetti: int
    elettori: int | None = None
    votanti: int | None = None
    voti_validi: int | None = None
    fonte_file: str
    file_count: int
    fonte_url: str
    sha256: str


class NationalGeographyResponse(BaseModel):
    count: int
    limit: int
    offset: int
    rows: list[NationalGeographyRow]


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


class ElectoralLawEntry(BaseModel):
    id: str
    date: date
    citation: str
    title: str
    kind: Literal["electoral_law", "boundary_decree", "boundary_correction"]
    applies_to: list[str]
    election_years: str
    source_url: str
    download_url: str
    file_format: Literal["html", "pdf"]
    downloaded: bool = False
    local_path: str | None = None


class DistrictMapVersionEntry(BaseModel):
    id: str
    category: Literal["camera", "senato"]
    start_year: int
    end_year: int
    geography_level: str
    source_ids: list[str]
    source_citations: list[str]
    source_urls: list[str]
    notes: str


class ElectoralLawDownloadRequest(BaseModel):
    ids: list[str] | None = None
    overwrite: bool = False


class DownloadedElectoralLaw(BaseModel):
    id: str
    local_path: str
    sha256: str
    bytes: int
    content_type: str | None = None
    downloaded: bool


class ElectoralLawDownloadResult(BaseModel):
    requested: int
    downloaded: int
    reused: int
    files: list[DownloadedElectoralLaw]


class MunicipalityAuditRow(BaseModel):
    tipo_elezione: str
    data: date
    comune: str
    fonte_file: str
    tipo_risultato: str
    parti_rilevate: int
    aventi_diritto: int | None = None
    votanti: int | None = None
    voti_risultato: int
    fonte_aggregazione: Literal["open_data", "official_municipality_pages"]
    aventi_diritto_open_data: int | None = None
    votanti_open_data: int | None = None
    voti_risultato_open_data: int | None = None
    verifica_ufficiale_stato: str | None = None
    verifica_ufficiale_pagine: int = 0
    verifica_ufficiale_fonti: list[str]
    verifica_ufficiale_data: datetime | None = None
    rapporto_voti_aventi_diritto: float | None = None
    data_riferimento: date | None = None
    tipo_elezione_riferimento: str | None = None
    metodo_riferimento: Literal[
        "same_date_other_chamber", "adjacent_same_chamber"
    ] | None = None
    aventi_diritto_riferimento: int | None = None
    rapporto_aventi_diritto_riferimento: float | None = None
    metodo_confronto_votanti: Literal[
        "same_date_other_chamber", "adjacent_same_chamber"
    ] | None = None
    tipo_elezione_stessa_data: str | None = None
    votanti_stessa_data: int | None = None
    rapporto_votanti_stessa_data: float | None = None
    data_precedente: date | None = None
    votanti_precedenti: int | None = None
    rapporto_votanti_precedenti: float | None = None
    data_successiva: date | None = None
    votanti_successivi: int | None = None
    rapporto_votanti_successivi: float | None = None
    tolleranza_votanti: float
    votanti_comparabili: bool | None = None
    mappa_collegi_versione: str | None = None
    fonti_confini_ids: list[str]
    fonti_confini_urls: list[str]
    fonte_confini_id: str | None = None
    stato: Literal["pass", "warning", "invalid", "insufficient_data"]


class MunicipalityAuditResponse(BaseModel):
    comune: str
    provincia: str | None = None
    regione: str | None = None
    categories: list[str]
    voter_tolerance: float
    elections_checked: int
    passed: int
    warnings: int
    invalid: int
    insufficient_data: int
    rows: list[MunicipalityAuditRow]
