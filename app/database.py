from __future__ import annotations

import json
import sqlite3
from contextlib import closing
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from .archive import ArchiveRow
from .history import normalise_history_results
from .schemas import CatalogueEntry, PageResult
from .utils import slug


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
