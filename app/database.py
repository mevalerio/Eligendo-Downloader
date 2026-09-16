from __future__ import annotations

import json
import sqlite3
from contextlib import closing
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from .archive import ArchiveRow
from .electoral_laws import LAW_BY_ID, boundary_source, district_map_for
from .history import normalise_history_results
from .schemas import CatalogueEntry, PageResult
from .utils import canonical_municipality, slug


NATIONAL_ELECTION_CATEGORIES = (
    "assemblea_costituente",
    "camera",
    "senato",
    "europee",
    "referendum",
)


SCHEMA = """
PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;

CREATE TABLE IF NOT EXISTS catalogues (
    id INTEGER PRIMARY KEY,
    category TEXT NOT NULL,
    election_date TEXT NOT NULL,
    filename TEXT NOT NULL,
    download_url TEXT NOT NULL,
    sha256 TEXT NOT NULL,
    downloaded_at TEXT NOT NULL,
    file_count INTEGER NOT NULL,
    row_count INTEGER NOT NULL,
    UNIQUE(category, election_date, filename)
);

CREATE TABLE IF NOT EXISTS archive_rows (
    id INTEGER PRIMARY KEY,
    catalogue_id INTEGER NOT NULL REFERENCES catalogues(id) ON DELETE CASCADE,
    file_name TEXT NOT NULL,
    row_number INTEGER NOT NULL,
    region TEXT,
    circoscrizione TEXT,
    province TEXT,
    municipality TEXT,
    municipality_key TEXT,
    payload_json TEXT NOT NULL,
    UNIQUE(catalogue_id, file_name, row_number)
);

CREATE INDEX IF NOT EXISTS idx_archive_lookup
ON archive_rows(catalogue_id, municipality_key, province);

CREATE TABLE IF NOT EXISTS party_results (
    id INTEGER PRIMARY KEY,
    catalogue_id INTEGER NOT NULL REFERENCES catalogues(id) ON DELETE CASCADE,
    election_date TEXT NOT NULL,
    region TEXT,
    province TEXT,
    municipality TEXT NOT NULL,
    municipality_key TEXT NOT NULL,
    party TEXT NOT NULL,
    party_key TEXT NOT NULL,
    votes INTEGER NOT NULL,
    round INTEGER,
    candidate TEXT,
    seats INTEGER,
    source_file TEXT NOT NULL,
    source_row INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_party_results_year
ON party_results(election_date, municipality_key, party_key, round);

CREATE INDEX IF NOT EXISTS idx_party_results_catalogue
ON party_results(catalogue_id);

CREATE TABLE IF NOT EXISTS election_results (
    id INTEGER PRIMARY KEY,
    catalogue_id INTEGER NOT NULL REFERENCES catalogues(id) ON DELETE CASCADE,
    election_date TEXT NOT NULL,
    category TEXT NOT NULL,
    round INTEGER,
    region TEXT,
    constituency TEXT,
    province TEXT,
    municipality TEXT,
    municipality_key TEXT,
    country TEXT,
    college TEXT,
    question_number TEXT,
    question TEXT,
    result_type TEXT NOT NULL,
    subject TEXT NOT NULL,
    subject_key TEXT NOT NULL,
    party TEXT,
    candidate TEXT,
    option TEXT,
    votes INTEGER NOT NULL,
    percentage REAL,
    seats INTEGER,
    electors INTEGER,
    male_electors INTEGER,
    voters INTEGER,
    male_voters INTEGER,
    turnout_percentage REAL,
    valid_votes INTEGER,
    valid_list_votes INTEGER,
    valid_candidate_votes INTEGER,
    blank_ballots INTEGER,
    invalid_ballots INTEGER,
    contested_ballots INTEGER,
    source_file TEXT NOT NULL,
    source_row INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_election_results_lookup
ON election_results(
    category, election_date, region, province, municipality_key,
    result_type, subject_key, round
);

CREATE INDEX IF NOT EXISTS idx_election_results_catalogue
ON election_results(catalogue_id);

CREATE TABLE IF NOT EXISTS page_snapshots (
    id INTEGER PRIMARY KEY,
    source_url TEXT NOT NULL,
    election_code TEXT,
    election_date TEXT NOT NULL,
    municipality TEXT,
    retrieved_at TEXT NOT NULL,
    payload_json TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_snapshot_lookup
ON page_snapshots(election_code, election_date, municipality);
"""


class Database:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.initialise()

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=30)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def initialise(self) -> None:
        with closing(self.connect()) as connection:
            connection.executescript(SCHEMA)
            connection.commit()

    def store_snapshot(self, result: PageResult) -> int:
        payload = result.model_dump_json()
        with closing(self.connect()) as connection:
            cursor = connection.execute(
                """
                INSERT INTO page_snapshots(
                    source_url, election_code, election_date, municipality,
                    retrieved_at, payload_json
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    result.source_url,
                    result.election.code,
                    result.election.date.isoformat(),
                    result.geography.comune,
                    result.retrieved_at.isoformat(),
                    payload,
                ),
            )
            connection.commit()
            return int(cursor.lastrowid)

    def replace_archive(
        self,
        entry: CatalogueEntry,
        *,
        sha256: str,
        rows: list[ArchiveRow],
    ) -> int:
        if not entry.election_date:
            raise ValueError("The catalogue entry has no election date.")
        file_count = len({row.file_name for row in rows})
        downloaded_at = datetime.now(timezone.utc).isoformat()
        with closing(self.connect()) as connection:
            connection.execute("BEGIN IMMEDIATE")
            connection.execute(
                """
                INSERT INTO catalogues(
                    category, election_date, filename, download_url, sha256,
                    downloaded_at, file_count, row_count
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(category, election_date, filename) DO UPDATE SET
                    download_url=excluded.download_url,
                    sha256=excluded.sha256,
                    downloaded_at=excluded.downloaded_at,
                    file_count=excluded.file_count,
                    row_count=excluded.row_count
                """,
                (
                    entry.category,
                    entry.election_date.isoformat(),
                    entry.filename,
                    entry.download_url,
                    sha256,
                    downloaded_at,
                    file_count,
                    len(rows),
                ),
            )
            catalogue_id = int(
                connection.execute(
                    """
                    SELECT id FROM catalogues
                    WHERE category=? AND election_date=? AND filename=?
                    """,
                    (entry.category, entry.election_date.isoformat(), entry.filename),
                ).fetchone()["id"]
            )
            connection.execute(
                "DELETE FROM archive_rows WHERE catalogue_id=?", (catalogue_id,)
            )
            connection.execute(
                "DELETE FROM party_results WHERE catalogue_id=?", (catalogue_id,)
            )
            connection.execute(
                "DELETE FROM election_results WHERE catalogue_id=?", (catalogue_id,)
            )
            connection.executemany(
                """
                INSERT INTO archive_rows(
                    catalogue_id, file_name, row_number, region, circoscrizione,
                    province, municipality, municipality_key, payload_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    (
                        catalogue_id,
                        row.file_name,
                        row.row_number,
                        row.region,
                        row.circoscrizione,
                        row.province,
                        row.municipality,
                        row.municipality_key,
                        json.dumps(row.payload, ensure_ascii=False, separators=(",", ":")),
                    )
                    for row in rows
                ),
            )
            history_results = normalise_history_results(
                rows,
                category=entry.category,
                election_date=entry.election_date,
            )
            connection.executemany(
                """
                INSERT INTO election_results(
                    catalogue_id, election_date, category, round, region,
                    constituency, province, municipality, municipality_key,
                    country, college, question_number, question, result_type,
                    subject, subject_key, party, candidate, option, votes,
                    percentage, seats, electors, male_electors, voters,
                    male_voters, turnout_percentage, valid_votes,
                    valid_list_votes, valid_candidate_votes, blank_ballots,
                    invalid_ballots, contested_ballots, source_file, source_row
                ) VALUES (
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                )
                """,
                (
                    (
                        catalogue_id,
                        result.election_date.isoformat(),
                        result.category,
                        result.round,
                        result.region,
                        result.constituency,
                        result.province,
                        result.municipality,
                        result.municipality_key,
                        result.country,
                        result.college,
                        result.question_number,
                        result.question,
                        result.result_type,
                        result.subject,
                        result.subject_key,
                        result.party,
                        result.candidate,
                        result.option,
                        result.votes,
                        result.percentage,
                        result.seats,
                        result.electors,
                        result.male_electors,
                        result.voters,
                        result.male_voters,
                        result.turnout_percentage,
                        result.valid_votes,
                        result.valid_list_votes,
                        result.valid_candidate_votes,
                        result.blank_ballots,
                        result.invalid_ballots,
                        result.contested_ballots,
                        result.source_file,
                        result.source_row,
                    )
                    for result in history_results
                ),
            )
            party_results = [
                result
                for result in history_results
                if (
                    entry.category == "comunali"
                    and result.result_type == "list"
                    and result.municipality
                    and result.party
                )
            ]
            connection.executemany(
                """
                INSERT INTO party_results(
                    catalogue_id, election_date, region, province, municipality,
                    municipality_key, party, party_key, votes, round, candidate,
                    seats, source_file, source_row
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    (
                        catalogue_id,
                        result.election_date.isoformat(),
                        result.region,
                        result.province,
                        result.municipality,
                        result.municipality_key or slug(result.municipality),
                        result.party,
                        result.subject_key,
                        result.votes,
                        result.round,
                        result.candidate,
                        result.seats,
                        result.source_file,
                        result.source_row,
                    )
                    for result in party_results
                ),
            )
            connection.commit()
        return catalogue_id

    def party_result_count(self, catalogue_id: int) -> int:
        with closing(self.connect()) as connection:
            return int(
                connection.execute(
                    "SELECT COUNT(*) AS n FROM party_results WHERE catalogue_id=?",
                    (catalogue_id,),
                ).fetchone()["n"]
            )

    def election_result_count(self, catalogue_id: int) -> int:
        with closing(self.connect()) as connection:
            return int(
                connection.execute(
                    "SELECT COUNT(*) AS n FROM election_results WHERE catalogue_id=?",
                    (catalogue_id,),
                ).fetchone()["n"]
            )

    def archive_is_normalised(self, entry: CatalogueEntry) -> bool:
        if entry.election_date is None:
            return False
        with closing(self.connect()) as connection:
            row = connection.execute(
                """
                SELECT c.id,
                       EXISTS(
                           SELECT 1 FROM election_results e
                           WHERE e.catalogue_id = c.id
                       ) AS has_results
                FROM catalogues c
                WHERE c.category=? AND c.election_date=? AND c.filename=?
                """,
                (
                    entry.category,
                    entry.election_date.isoformat(),
                    entry.filename,
                ),
            ).fetchone()
        return bool(row and row["has_results"])

    @staticmethod
    def _history_filters(
        *,
        category: str | None,
        year: int | None,
        election_date: date | None,
        region: str | None,
        province: str | None,
        municipality: str | None,
        result_type: str | None,
        subject: str | None,
        round_number: int | None,
    ) -> tuple[str, list[Any]]:
        clauses = ["1 = 1"]
        parameters: list[Any] = []
        if category:
            clauses.append("e.category = ?")
            parameters.append(category)
        if year is not None:
            clauses.append("substr(e.election_date, 1, 4) = ?")
            parameters.append(str(year))
        if election_date is not None:
            clauses.append("e.election_date = ?")
            parameters.append(election_date.isoformat())
        if region:
            clauses.append("e.region = ? COLLATE NOCASE")
            parameters.append(region)
        if province:
            clauses.append("e.province = ? COLLATE NOCASE")
            parameters.append(province)
        if municipality:
            clauses.append("e.municipality_key = ?")
            parameters.append(slug(municipality))
        if result_type:
            clauses.append("e.result_type = ?")
            parameters.append(result_type)
        if subject:
            clauses.append("e.subject_key = ?")
            parameters.append(slug(subject))
        if round_number is not None:
            clauses.append("e.round = ?")
            parameters.append(round_number)
        return " AND ".join(clauses), parameters

    @staticmethod
    def _history_row(record: sqlite3.Row) -> dict[str, Any]:
        return {
            "tipo_elezione": record["category"],
            "data": record["election_date"],
            "turno": record["round"],
            "regione": record["region"],
            "circoscrizione": record["constituency"],
            "provincia": record["province"],
            "comune": record["municipality"],
            "nazione": record["country"],
            "collegio": record["college"],
            "numero_quesito": record["question_number"],
            "quesito": record["question"],
            "tipo_risultato": record["result_type"],
            "soggetto": record["subject"],
            "partito": record["party"],
            "candidato": record["candidate"],
            "opzione_referendum": record["option"],
            "voti": record["votes"],
            "percentuale": record["percentage"],
            "seggi": record["seats"],
            "elettori": record["electors"],
            "elettori_maschi": record["male_electors"],
            "votanti": record["voters"],
            "votanti_maschi": record["male_voters"],
            "affluenza_pct": record["turnout_percentage"],
            "voti_validi": record["valid_votes"],
            "voti_validi_liste": record["valid_list_votes"],
            "voti_validi_candidato": record["valid_candidate_votes"],
            "schede_bianche": record["blank_ballots"],
            "schede_non_valide": record["invalid_ballots"],
            "schede_contestate": record["contested_ballots"],
            "fonte_url": record["download_url"],
            "fonte_file": record["source_file"],
            "fonte_riga": record["source_row"],
            "sha256": record["sha256"],
        }

    def query_election_results(
        self,
        *,
        category: str | None,
        year: int | None,
        election_date: date | None,
        region: str | None,
        province: str | None,
        municipality: str | None,
        result_type: str | None,
        subject: str | None,
        round_number: int | None,
        limit: int,
        offset: int,
    ) -> tuple[int, list[dict[str, Any]]]:
        where, parameters = self._history_filters(
            category=category,
            year=year,
            election_date=election_date,
            region=region,
            province=province,
            municipality=municipality,
            result_type=result_type,
            subject=subject,
            round_number=round_number,
        )
        with closing(self.connect()) as connection:
            count = int(
                connection.execute(
                    f"SELECT COUNT(*) AS n FROM election_results e WHERE {where}",
                    parameters,
                ).fetchone()["n"]
            )
            selected = connection.execute(
                f"""
                SELECT e.*, c.download_url, c.sha256
                FROM election_results e
                JOIN catalogues c ON c.id = e.catalogue_id
                WHERE {where}
                ORDER BY e.election_date, e.category, e.region, e.province,
                         e.municipality, e.question_number, e.result_type,
                         e.subject, e.source_file, e.source_row
                LIMIT ? OFFSET ?
                """,
                [*parameters, limit, offset],
            ).fetchall()
        return count, [self._history_row(record) for record in selected]

    def iter_election_results(
        self,
        *,
        category: str | None,
        year: int | None,
        election_date: date | None,
        region: str | None,
        province: str | None,
        municipality: str | None,
        result_type: str | None,
        subject: str | None,
        round_number: int | None,
    ):
        where, parameters = self._history_filters(
            category=category,
            year=year,
            election_date=election_date,
            region=region,
            province=province,
            municipality=municipality,
            result_type=result_type,
            subject=subject,
            round_number=round_number,
        )
        connection = self.connect()
        try:
            cursor = connection.execute(
                f"""
                SELECT e.*, c.download_url, c.sha256
                FROM election_results e
                JOIN catalogues c ON c.id = e.catalogue_id
                WHERE {where}
                ORDER BY e.election_date, e.category, e.region, e.province,
                         e.municipality, e.question_number, e.result_type,
                         e.subject, e.source_file, e.source_row
                """,
                parameters,
            )
            for record in cursor:
                yield self._history_row(record)
        finally:
            connection.close()

    @staticmethod
    def _national_coverage_filters(
        *,
        category: str | None,
        year: int | None,
        election_date: date | None,
        region: str | None,
        province: str | None,
        municipality: str | None,
    ) -> tuple[str, list[Any]]:
        if category is not None and category not in NATIONAL_ELECTION_CATEGORIES:
            raise ValueError(
                "category must be one of: "
                + ", ".join(NATIONAL_ELECTION_CATEGORIES)
            )
        placeholders = ",".join("?" for _ in NATIONAL_ELECTION_CATEGORIES)
        clauses = [f"e.category IN ({placeholders})"]
        parameters: list[Any] = list(NATIONAL_ELECTION_CATEGORIES)
        if category:
            clauses.append("e.category = ?")
            parameters.append(category)
        if year is not None:
            clauses.append("substr(e.election_date, 1, 4) = ?")
            parameters.append(str(year))
        if election_date is not None:
            clauses.append("e.election_date = ?")
            parameters.append(election_date.isoformat())
        if region:
            clauses.append("e.region = ? COLLATE NOCASE")
            parameters.append(region)
        if province:
            clauses.append("e.province = ? COLLATE NOCASE")
            parameters.append(province)
        if municipality:
            clauses.append("e.municipality_key = ?")
            parameters.append(slug(municipality))
        return " AND ".join(clauses), parameters

    @staticmethod
    def _national_coverage_row(record: sqlite3.Row) -> dict[str, Any]:
        if record["municipality"]:
            level = "comune"
        elif record["province"]:
            level = "provincia"
        elif record["region"]:
            level = "regione"
        elif record["country"]:
            level = "nazione"
        else:
            level = "nazionale"
        return {
            "tipo_elezione": record["category"],
            "data": record["election_date"],
            "livello": level,
            "regione": record["region"],
            "circoscrizione": record["constituency"],
            "provincia": record["province"],
            "comune": record["municipality"],
            "nazione": record["country"],
            "collegio": record["college"],
            "turno": record["round"],
            "numero_quesito": record["question_number"],
            "righe": int(record["rows"]),
            "soggetti": int(record["subjects"]),
            "elettori": record["electors"],
            "votanti": record["voters"],
            "voti_validi": record["valid_votes"],
            "fonte_file": record["source_file"],
            "file_count": int(record["source_files"]),
            "fonte_url": record["download_url"],
            "sha256": record["sha256"],
        }

    def query_national_geography(
        self,
        *,
        category: str | None,
        year: int | None,
        election_date: date | None,
        region: str | None,
        province: str | None,
        municipality: str | None,
        limit: int,
        offset: int,
    ) -> tuple[int, list[dict[str, Any]]]:
        where, parameters = self._national_coverage_filters(
            category=category,
            year=year,
            election_date=election_date,
            region=region,
            province=province,
            municipality=municipality,
        )
        grouped = f"""
            SELECT e.catalogue_id, e.category, e.election_date,
                   e.region, e.constituency, e.province, e.municipality,
                   e.country, e.college, e.round, e.question_number,
                   GROUP_CONCAT(DISTINCT e.source_file) AS source_file,
                   COUNT(DISTINCT e.source_file) AS source_files,
                   COUNT(*) AS rows,
                   COUNT(DISTINCT e.subject_key) AS subjects,
                   MAX(e.electors) AS electors,
                   MAX(e.voters) AS voters,
                   MAX(e.valid_votes) AS valid_votes,
                   c.download_url, c.sha256
            FROM election_results e
            JOIN catalogues c ON c.id = e.catalogue_id
            WHERE {where}
            GROUP BY e.catalogue_id, e.category, e.election_date,
                     e.region, e.constituency, e.province, e.municipality,
                     e.country, e.college, e.round, e.question_number,
                     c.download_url, c.sha256
        """
        order = """
            ORDER BY election_date, category, region, province, municipality,
                     constituency, college, source_file, round, question_number
        """
        with closing(self.connect()) as connection:
            count = int(
                connection.execute(
                    f"SELECT COUNT(*) AS n FROM ({grouped}) geography",
                    parameters,
                ).fetchone()["n"]
            )
            selected = connection.execute(
                f"SELECT * FROM ({grouped}) geography {order} LIMIT ? OFFSET ?",
                [*parameters, limit, offset],
            ).fetchall()
        return count, [self._national_coverage_row(record) for record in selected]

    def iter_national_geography(
        self,
        *,
        category: str | None,
        year: int | None,
        election_date: date | None,
        region: str | None,
        province: str | None,
        municipality: str | None,
    ):
        where, parameters = self._national_coverage_filters(
            category=category,
            year=year,
            election_date=election_date,
            region=region,
            province=province,
            municipality=municipality,
        )
        connection = self.connect()
        try:
            cursor = connection.execute(
                f"""
                SELECT e.catalogue_id, e.category, e.election_date,
                       e.region, e.constituency, e.province, e.municipality,
                       e.country, e.college, e.round, e.question_number,
                       GROUP_CONCAT(DISTINCT e.source_file) AS source_file,
                       COUNT(DISTINCT e.source_file) AS source_files,
                       COUNT(*) AS rows,
                       COUNT(DISTINCT e.subject_key) AS subjects,
                       MAX(e.electors) AS electors,
                       MAX(e.voters) AS voters,
                       MAX(e.valid_votes) AS valid_votes,
                       c.download_url, c.sha256
                FROM election_results e
                JOIN catalogues c ON c.id = e.catalogue_id
                WHERE {where}
                GROUP BY e.catalogue_id, e.category, e.election_date,
                         e.region, e.constituency, e.province, e.municipality,
                         e.country, e.college, e.round, e.question_number,
                         c.download_url, c.sha256
                ORDER BY e.election_date, e.category, e.region, e.province,
                         e.municipality, e.constituency, e.college,
                         e.source_file, e.round, e.question_number
                """,
                parameters,
            )
            for record in cursor:
                yield self._national_coverage_row(record)
        finally:
            connection.close()

    def municipality_coverage(
        self, *, region: str, municipality: str
    ) -> list[dict[str, Any]]:
        municipality_key = slug(municipality)
        national_categories = (
            "assemblea_costituente",
            "camera",
            "senato",
            "europee",
            "referendum",
        )
        placeholders = ",".join("?" for _ in national_categories)
        with closing(self.connect()) as connection:
            selected = connection.execute(
                f"""
                SELECT c.category, c.election_date, c.filename, c.download_url,
                       c.sha256,
                       SUM(CASE WHEN e.municipality IS NOT NULL THEN 1 ELSE 0 END)
                           AS municipality_rows,
                       SUM(CASE WHEN e.municipality_key = ? THEN 1 ELSE 0 END)
                           AS target_rows,
                       SUM(
                           CASE
                               WHEN e.region = ? COLLATE NOCASE
                                 OR e.municipality_key = ?
                               THEN 1 ELSE 0
                           END
                       ) AS region_rows
                FROM catalogues c
                LEFT JOIN election_results e ON e.catalogue_id = c.id
                WHERE c.category IN ({placeholders})
                   OR EXISTS(
                       SELECT 1 FROM election_results ee
                       WHERE ee.catalogue_id = c.id
                         AND (
                             ee.region = ? COLLATE NOCASE
                             OR ee.municipality_key = ?
                         )
                   )
                GROUP BY c.id
                ORDER BY c.election_date, c.category, c.filename
                """,
                (
                    municipality_key,
                    region,
                    municipality_key,
                    *national_categories,
                    region,
                    municipality_key,
                ),
            ).fetchall()

        coverage = []
        for record in selected:
            if record["target_rows"]:
                status = "present"
            elif not record["municipality_rows"]:
                status = "not_available_at_municipality_level"
            else:
                status = "missing"
            coverage.append(
                {
                    "tipo_elezione": record["category"],
                    "data": record["election_date"],
                    "filename": record["filename"],
                    "regione": region,
                    "comune": municipality,
                    "stato": status,
                    "righe_comune": int(record["target_rows"] or 0),
                    "righe_livello_comunale": int(record["municipality_rows"] or 0),
                    "fonte_url": record["download_url"],
                    "sha256": record["sha256"],
                }
            )
        return coverage

    def municipality_election_audit(
        self,
        *,
        municipality: str,
        categories: tuple[str, ...] = ("camera", "senato"),
        voter_tolerance: float = 0.35,
    ) -> list[dict[str, Any]]:
        if not 0 <= voter_tolerance < 1:
            raise ValueError(
                "voter_tolerance must be greater than or equal to 0 and below 1."
            )
        municipality_key = slug(municipality)
        placeholders = ",".join("?" for _ in categories)
        legacy_keys = (
            f"parte_di_comune_{municipality_key}",
            f"parte_di_comune_di_{municipality_key}",
            f"parte_del_comune_di_{municipality_key}",
        )
        if municipality_key == "reggio_calabria":
            legacy_keys = (
                *legacy_keys,
                "parte_di_comune_reggio_di_calabria",
                "parte_del_comune_di_reggio_di_calabria",
            )
        legacy_placeholders = ",".join("?" for _ in legacy_keys)
        with closing(self.connect()) as connection:
            units = connection.execute(
                f"""
                SELECT e.catalogue_id, e.category, e.election_date,
                       e.source_file, e.result_type, e.round,
                       e.municipality,
                       COALESCE(e.college, '') AS college,
                       COALESCE(e.constituency, '') AS constituency,
                       MAX(e.electors) AS electors,
                       MAX(e.voters) AS voters,
                       SUM(e.votes) AS result_votes
                FROM election_results e
                WHERE (
                    e.municipality_key = ?
                    OR e.municipality_key LIKE ?
                    OR e.municipality_key IN ({legacy_placeholders})
                )
                  AND e.category IN ({placeholders})
                GROUP BY e.catalogue_id, e.category, e.election_date,
                         e.source_file, e.result_type, e.round,
                         e.municipality,
                         COALESCE(e.college, ''),
                         COALESCE(e.constituency, '')
                ORDER BY e.election_date, e.category, e.source_file,
                         e.result_type, college
                """,
                (
                    municipality_key,
                    f"{municipality_key}_%",
                    *legacy_keys,
                    *categories,
                ),
            ).fetchall()

        layers: dict[tuple[Any, ...], dict[str, Any]] = {}
        for unit in units:
            canonical = canonical_municipality(unit["municipality"])
            if slug(canonical or "") != municipality_key:
                continue
            key = (
                unit["catalogue_id"],
                unit["category"],
                unit["election_date"],
                unit["source_file"],
                unit["result_type"],
                unit["round"],
            )
            layer = layers.setdefault(
                key,
                {
                    "tipo_elezione": unit["category"],
                    "data": unit["election_date"],
                    "comune": municipality,
                    "fonte_file": unit["source_file"],
                    "tipo_risultato": unit["result_type"],
                    "parti_rilevate": 0,
                    "aventi_diritto": 0,
                    "votanti": 0,
                    "voti_risultato": 0,
                    "_complete_electors": True,
                    "_complete_voters": True,
                },
            )
            layer["parti_rilevate"] += 1
            if unit["electors"] is None:
                layer["_complete_electors"] = False
            else:
                layer["aventi_diritto"] += int(unit["electors"])
            if unit["voters"] is None:
                layer["_complete_voters"] = False
            else:
                layer["votanti"] += int(unit["voters"])
            layer["voti_risultato"] += int(unit["result_votes"] or 0)

        by_election: dict[tuple[str, str], list[dict[str, Any]]] = {}
        for layer in layers.values():
            if not layer.pop("_complete_electors"):
                layer["aventi_diritto"] = None
            if not layer.pop("_complete_voters"):
                layer["votanti"] = None
            by_election.setdefault(
                (layer["tipo_elezione"], layer["data"]), []
            ).append(layer)

        selected: list[dict[str, Any]] = []
        for candidates in by_election.values():
            selected.append(
                max(
                    candidates,
                    key=lambda row: (
                        row["aventi_diritto"] is not None,
                        row["tipo_risultato"] == "list",
                        row["votanti"] is not None,
                        row["voti_risultato"],
                    ),
                )
            )

        dated = sorted(
            [(date.fromisoformat(row["data"]), row) for row in selected],
            key=lambda item: (item[0], item[1]["tipo_elezione"]),
        )
        for current_date, row in dated:
            electors = row["aventi_diritto"]
            voters = row["votanti"]
            votes = row["voti_risultato"]
            vote_ratio = (
                round(votes / electors, 6) if electors not in (None, 0) else None
            )
            references = [
                (other_date, other)
                for other_date, other in dated
                if other is not row
                and other["tipo_elezione"] == row["tipo_elezione"]
                and other["aventi_diritto"] not in (None, 0)
            ]
            reference_date = None
            reference_electors = None
            reference_ratio = None
            if references:
                reference_date, reference = min(
                    references,
                    key=lambda item: abs((item[0] - current_date).days),
                )
                reference_electors = int(reference["aventi_diritto"])
                if electors is not None:
                    reference_ratio = round(electors / reference_electors, 6)

            voter_references = [
                (other_date, other)
                for other_date, other in dated
                if other is not row
                and other["tipo_elezione"] == row["tipo_elezione"]
                and other["votanti"] not in (None, 0)
            ]
            previous = [item for item in voter_references if item[0] < current_date]
            following = [item for item in voter_references if item[0] > current_date]
            previous_date, previous_row = max(previous, default=(None, None))
            next_date, next_row = min(following, default=(None, None))
            previous_voters = (
                int(previous_row["votanti"]) if previous_row is not None else None
            )
            next_voters = int(next_row["votanti"]) if next_row is not None else None
            previous_voter_ratio = (
                round(voters / previous_voters, 6)
                if voters not in (None, 0) and previous_voters not in (None, 0)
                else None
            )
            next_voter_ratio = (
                round(voters / next_voters, 6)
                if voters not in (None, 0) and next_voters not in (None, 0)
                else None
            )
            voter_ratios = [
                ratio
                for ratio in (previous_voter_ratio, next_voter_ratio)
                if ratio is not None
            ]
            voters_comparable = (
                all(
                    1 - voter_tolerance <= ratio <= 1 + voter_tolerance
                    for ratio in voter_ratios
                )
                if voter_ratios
                else None
            )

            votes_exceed_electors = (
                electors not in (None, 0) and votes > electors * 1.02
            )
            voters_exceed_electors = (
                electors not in (None, 0)
                and voters is not None
                and voters > electors * 1.01
            )
            votes_exceed_voters = voters is not None and votes > voters * 1.02
            if (
                votes_exceed_electors
                or voters_exceed_electors
                or votes_exceed_voters
            ):
                status = "invalid"
            elif electors in (None, 0) or voters in (None, 0) or not voter_ratios:
                status = "insufficient_data"
            elif (
                vote_ratio is None
                or not 0.2 <= vote_ratio <= 1.02
                or (
                    reference_ratio is not None
                    and not 0.65 <= reference_ratio <= 1.35
                )
                or voters_comparable is False
            ):
                status = "warning"
            else:
                status = "pass"

            map_version = district_map_for(row["tipo_elezione"], current_date.year)
            source_ids = list(map_version.source_ids) if map_version else []
            row.update(
                {
                    "rapporto_voti_aventi_diritto": vote_ratio,
                    "data_riferimento": (
                        reference_date.isoformat() if reference_date else None
                    ),
                    "aventi_diritto_riferimento": reference_electors,
                    "rapporto_aventi_diritto_riferimento": reference_ratio,
                    "data_precedente": (
                        previous_date.isoformat() if previous_date else None
                    ),
                    "votanti_precedenti": previous_voters,
                    "rapporto_votanti_precedenti": previous_voter_ratio,
                    "data_successiva": next_date.isoformat() if next_date else None,
                    "votanti_successivi": next_voters,
                    "rapporto_votanti_successivi": next_voter_ratio,
                    "tolleranza_votanti": voter_tolerance,
                    "votanti_comparabili": voters_comparable,
                    "mappa_collegi_versione": map_version.id if map_version else None,
                    "fonti_confini_ids": source_ids,
                    "fonti_confini_urls": [
                        LAW_BY_ID[source_id].source_url for source_id in source_ids
                    ],
                    "fonte_confini_id": boundary_source(
                        row["tipo_elezione"], current_date.year
                    ),
                    "stato": status,
                }
            )
        return sorted(selected, key=lambda row: (row["data"], row["tipo_elezione"]))

    @staticmethod
    def _party_filters(
        *,
        year: int | None,
        election_date: date | None,
        municipality: str | None,
        province: str | None,
        party: str | None,
        round_number: int | None,
    ) -> tuple[str, list[Any]]:
        clauses = ["c.category = 'comunali'"]
        parameters: list[Any] = []
        if year is not None:
            clauses.append("substr(p.election_date, 1, 4) = ?")
            parameters.append(str(year))
        if election_date is not None:
            clauses.append("p.election_date = ?")
            parameters.append(election_date.isoformat())
        if municipality:
            clauses.append("p.municipality_key = ?")
            parameters.append(slug(municipality))
        if province:
            clauses.append("p.province = ? COLLATE NOCASE")
            parameters.append(province)
        if party:
            clauses.append("p.party_key = ?")
            parameters.append(slug(party))
        if round_number == 1:
            clauses.append("(p.round = 1 OR p.round IS NULL)")
        elif round_number is not None:
            clauses.append("p.round = ?")
            parameters.append(round_number)
        return " AND ".join(clauses), parameters

    @staticmethod
    def _party_row(record: sqlite3.Row) -> dict[str, Any]:
        return {
            "data": record["election_date"],
            "regione": record["region"],
            "provincia": record["province"],
            "comune": record["municipality"],
            "partito": record["party"],
            "voti": record["votes"],
            "turno": record["round"],
            "candidato": record["candidate"],
            "seggi": record["seats"],
            "fonte_file": record["source_file"],
            "fonte_riga": record["source_row"],
        }

    def query_party_results(
        self,
        *,
        year: int | None,
        election_date: date | None,
        municipality: str | None,
        province: str | None,
        party: str | None,
        round_number: int | None,
        limit: int,
        offset: int,
    ) -> tuple[int, list[dict[str, Any]]]:
        where, parameters = self._party_filters(
            year=year,
            election_date=election_date,
            municipality=municipality,
            province=province,
            party=party,
            round_number=round_number,
        )
        with closing(self.connect()) as connection:
            count = int(
                connection.execute(
                    f"""
                    SELECT COUNT(*) AS n FROM party_results p
                    JOIN catalogues c ON c.id = p.catalogue_id
                    WHERE {where}
                    """,
                    parameters,
                ).fetchone()["n"]
            )
            selected = connection.execute(
                f"""
                SELECT p.* FROM party_results p
                JOIN catalogues c ON c.id = p.catalogue_id
                WHERE {where}
                ORDER BY p.election_date, p.region, p.province, p.municipality,
                         p.party, p.candidate, p.source_row
                LIMIT ? OFFSET ?
                """,
                [*parameters, limit, offset],
            ).fetchall()
        return count, [self._party_row(record) for record in selected]

    def iter_party_results(
        self,
        *,
        year: int | None,
        election_date: date | None,
        municipality: str | None,
        province: str | None,
        party: str | None,
        round_number: int | None,
    ):
        where, parameters = self._party_filters(
            year=year,
            election_date=election_date,
            municipality=municipality,
            province=province,
            party=party,
            round_number=round_number,
        )
        connection = self.connect()
        try:
            cursor = connection.execute(
                f"""
                SELECT p.* FROM party_results p
                JOIN catalogues c ON c.id = p.catalogue_id
                WHERE {where}
                ORDER BY p.election_date, p.region, p.province, p.municipality,
                         p.party, p.candidate, p.source_row
                """,
                parameters,
            )
            for record in cursor:
                yield self._party_row(record)
        finally:
            connection.close()

    def query_archive(
        self,
        *,
        category: str,
        election_date: date,
        municipality: str | None,
        province: str | None,
        limit: int,
        offset: int,
    ) -> tuple[int, list[dict[str, Any]]]:
        clauses = ["c.category = ?", "c.election_date = ?"]
        parameters: list[Any] = [category, election_date.isoformat()]
        if municipality:
            clauses.append("r.municipality_key = ?")
            parameters.append(slug(municipality))
        if province:
            clauses.append("r.province = ? COLLATE NOCASE")
            parameters.append(province)
        where = " AND ".join(clauses)
        with closing(self.connect()) as connection:
            count = int(
                connection.execute(
                    f"""
                    SELECT COUNT(*) AS n FROM archive_rows r
                    JOIN catalogues c ON c.id = r.catalogue_id
                    WHERE {where}
                    """,
                    parameters,
                ).fetchone()["n"]
            )
            selected = connection.execute(
                f"""
                SELECT c.category, c.election_date, r.file_name, r.row_number,
                       r.payload_json
                FROM archive_rows r
                JOIN catalogues c ON c.id = r.catalogue_id
                WHERE {where}
                ORDER BY r.file_name, r.row_number
                LIMIT ? OFFSET ?
                """,
                [*parameters, limit, offset],
            ).fetchall()
        rows = []
        for record in selected:
            payload = json.loads(record["payload_json"])
            payload["_meta"] = {
                "category": record["category"],
                "election_date": record["election_date"],
                "file_name": record["file_name"],
                "row_number": record["row_number"],
            }
            rows.append(payload)
        return count, rows

    def list_municipalities(
        self, *, category: str, election_date: date
    ) -> list[dict[str, Any]]:
        with closing(self.connect()) as connection:
            selected = connection.execute(
                """
                SELECT r.municipality AS comune,
                       MAX(r.province) AS provincia,
                       MAX(r.region) AS regione,
                       COUNT(*) AS rows
                FROM archive_rows r
                JOIN catalogues c ON c.id = r.catalogue_id
                WHERE c.category = ? AND c.election_date = ?
                  AND r.municipality IS NOT NULL
                GROUP BY r.municipality_key, r.municipality
                ORDER BY r.municipality COLLATE NOCASE
                """,
                (category, election_date.isoformat()),
            ).fetchall()
        return [dict(row) for row in selected]
