from datetime import date

from app.archive import ArchiveRow, normalise_party_result
from app.database import Database
from app.schemas import CatalogueEntry


def source_row(payload: dict, row_number: int = 2) -> ArchiveRow:
    return ArchiveRow(
        file_name="comunali.txt",
        row_number=row_number,
        region="CAMPANIA",
        circoscrizione=None,
        province="NAPOLI",
        municipality="NAPOLI",
        municipality_key="napoli",
        payload=payload,
    )


def test_normalises_legacy_and_recent_party_fields() -> None:
    election_date = date(2021, 10, 3)
    legacy = normalise_party_result(
        source_row({"lista": "PARTITO A", "voti_lista": "1.234", "turno": "1"}),
        election_date=election_date,
    )
    recent = normalise_party_result(
        source_row(
            {
                "descrlista": "LISTA B",
                "votilista": 567,
                "seggilista": 3,
                "cognome": "ROSSI",
                "nome": "ANNA",
            },
            row_number=3,
        ),
        election_date=election_date,
    )

    assert legacy is not None and legacy.votes == 1234 and legacy.round == 1
    assert recent is not None and recent.party == "LISTA B"
    assert recent.votes == 567 and recent.seats == 3
    assert recent.candidate == "ROSSI ANNA"


def test_database_defaults_to_first_round_and_exports_all_on_request(tmp_path) -> None:
    database = Database(tmp_path / "test.sqlite3")
    election_date = date(2001, 5, 13)
    entry = CatalogueEntry(
        category="comunali",
        year=2001,
        relative_path="comunali/example.zip",
        filename="example.zip",
        election_date=election_date,
        identifier="20010513",
        download_url="https://dait.interno.gov.it/documenti/opendata/comunali/example.zip",
    )
    rows = [
        source_row(
            {"lista": "PARTITO A", "voti_lista": "100", "turno": "1"},
            row_number=2,
        ),
        source_row(
            {"lista": "PARTITO A", "voti_lista": "100", "turno": "2"},
            row_number=3,
        ),
        source_row(
            {"lista": "LISTA SENZA TURNO", "voti_lista": "25"},
            row_number=4,
        ),
    ]
    catalogue_id = database.replace_archive(entry, sha256="abc", rows=rows)

    assert database.party_result_count(catalogue_id) == 3
    count_first, first_round = database.query_party_results(
        year=2001,
        election_date=None,
        municipality="Napoli",
        province=None,
        party=None,
        round_number=1,
        limit=100,
        offset=0,
    )
    count_all, all_rounds = database.query_party_results(
        year=2001,
        election_date=None,
        municipality="Napoli",
        province=None,
        party=None,
        round_number=None,
        limit=100,
        offset=0,
    )

    assert count_first == len(first_round) == 2
    assert count_all == len(all_rounds) == 3
