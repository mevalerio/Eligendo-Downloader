from __future__ import annotations

import json
import sqlite3
from contextlib import closing
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from .archive import ArchiveRow, normalise_party_result
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
            party_results = [
                result
                for row in rows
                if (
                    result := normalise_party_result(
                        row,
                        election_date=entry.election_date,
                    )
                )
                is not None
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
                        result.municipality_key,
                        result.party,
                        result.party_key,
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
