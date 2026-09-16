from datetime import date

from fastapi.testclient import TestClient

from app import main
from app.archive import ArchiveRow
from app.database import Database
from app.history import normalise_history_results
from app.schemas import CatalogueEntry


def source_row(
    payload: dict,
    *,
    file_name: str = "results.csv",
    row_number: int = 2,
    region: str | None = "LAZIO",
    province: str | None = "ROMA",
    municipality: str | None = "ROMA",
) -> ArchiveRow:
    return ArchiveRow(
        file_name=file_name,
        row_number=row_number,
        region=region,
        circoscrizione=None,
        province=province,
        municipality=municipality,
        municipality_key=municipality.casefold() if municipality else None,
        payload=payload,
    )


def entry(category: str, election_date: date, filename: str) -> CatalogueEntry:
    return CatalogueEntry(
        category=category,
        year=election_date.year,
        relative_path=f"{category}/{filename}",
        filename=filename,
        election_date=election_date,
        identifier=election_date.strftime("%Y%m%d"),
        download_url=(
            f"https://dait.interno.gov.it/documenti/opendata/"
            f"{category}/{filename}"
        ),
    )


def test_history_normaliser_joins_summary_and_excludes_sections() -> None:
    election_date = date(2026, 6, 7)
    rows = [
        source_row(
            {
                "turno": "1",
                "elettoritot": "1000",
                "numvotantitotali": "600",
                "skbianche": "10",
            },
            file_name="_OPENDATA_Scrutini_LivComune.txt",
        ),
        source_row(
            {
                "turno": "1",
                "descrlista": "LISTA ROMA",
                "votilista": "450",
                "seggilista": "5",
                "cognome": "ROSSI",
                "nome": "ANNA",
            },
            file_name="_OPENDATA_Liste&Cand_LivComune.txt",
            row_number=3,
        ),
        source_row(
            {
                "sezione": "SEZIONE 1",
                "turno": "1",
                "descrlista": "LISTA ROMA",
                "votilista": "120",
            },
            file_name="_OPENDATA_Liste&Cand_LivSezione.txt",
            row_number=4,
        ),
    ]

    results = normalise_history_results(
        rows,
        category="comunali",
        election_date=election_date,
    )

    assert len(results) == 1
    result = results[0]
    assert result.party == "LISTA ROMA"
    assert result.votes == 450
    assert result.candidate == "ROSSI ANNA"
    assert result.electors == 1000
    assert result.voters == 600
    assert result.turnout_percentage == 60.0
    assert result.blank_ballots == 10


def test_history_normaliser_expands_referendum_options() -> None:
    results = normalise_history_results(
        [
            source_row(
                {
                    "num_referendum": "2",
                    "quesito": "Example question",
                    "elettori": "100",
                    "votanti": "80",
                    "voti_si": "45",
                    "voti_no": "30",
                    "schede_bianche": "5",
                }
            )
        ],
        category="referendum",
        election_date=date(2022, 6, 12),
    )

    assert [(result.option, result.votes) for result in results] == [
        ("SI", 45),
        ("NO", 30),
    ]
    assert all(result.question_number == "2" for result in results)
    assert all(result.valid_votes == 75 for result in results)


def test_history_normaliser_accepts_italian_decimal_integers() -> None:
    results = normalise_history_results(
        [
            source_row(
                {
                    "lista": "LISTA REGIONALE",
                    "voti_lista": "1.234,00",
                    "elettori": "2.000,00",
                    "votanti": "1.500,00",
                }
            )
        ],
        category="regionali",
        election_date=date(2018, 3, 4),
    )

    assert len(results) == 1
    assert results[0].votes == 1234
    assert results[0].electors == 2000
    assert results[0].voters == 1500


def test_history_normaliser_accepts_2024_european_columns() -> None:
    row = source_row(
        {
            "desclista": "PARTITO EUROPEO",
            "numvoti": "321",
            "elettori": "1000",
            "votanti": "600",
            "numschedebianche": "5",
            "numschedecontestat": "2",
        }
    )
    results = normalise_history_results(
        [row],
        category="europee",
        election_date=date(2024, 6, 9),
    )

    assert len(results) == 1
    assert results[0].party == "PARTITO EUROPEO"
    assert results[0].votes == 321
    assert results[0].blank_ballots == 5
    assert results[0].contested_ballots == 2


def test_history_normaliser_aggregates_section_only_archives() -> None:
    rows = [
        source_row(
            {
                "sezione": section,
                "elettori_totali": electors,
                "votanti_totali": voters,
                "schede_bianche": blank,
                "lista": party,
                "voti_lista": votes,
            },
            file_name="risultati_regionali.csv",
            row_number=row_number,
        )
        for section, electors, voters, blank, party, votes, row_number in (
            ("1", "100", "70", "2", "LISTA A", "40", 2),
            ("2", "120", "80", "1", "LISTA A", "50", 3),
            ("1", "100", "70", "2", "LISTA B", "20", 4),
            ("2", "120", "80", "1", "LISTA B", "20", 5),
        )
    ]
    results = normalise_history_results(
        rows,
        category="regionali",
        election_date=date(2024, 11, 17),
    )

    assert [(result.party, result.votes) for result in results] == [
        ("LISTA A", 90),
        ("LISTA B", 40),
    ]
    assert all(result.electors == 220 for result in results)
    assert all(result.voters == 150 for result in results)
    assert all(result.blank_ballots == 3 for result in results)
    assert all(result.source_row == 0 for result in results)


def test_history_normaliser_derives_2025_referendum_no_votes() -> None:
    results = normalise_history_results(
        [
            source_row(
                {
                    "numquesito": "1",
                    "quesitoreferendum": "Example question",
                    "elettoritot": "100",
                    "votantitot": "80",
                    "votivalidi": "75",
                    "votivalidi_si": "45",
                }
            )
        ],
        category="referendum",
        election_date=date(2025, 6, 8),
    )

    assert [(result.option, result.votes) for result in results] == [
        ("SI", 45),
        ("NO", 30),
    ]
    assert all(result.question == "Example question" for result in results)


def test_history_api_and_rome_lazio_coverage(tmp_path, monkeypatch) -> None:
    database = Database(tmp_path / "history.sqlite3")
    assembly_date = date(1946, 6, 2)
    referendum_date = date(1995, 6, 11)
    municipal_date = date(2024, 6, 9)

    database.replace_archive(
        entry(
            "assemblea_costituente",
            assembly_date,
            "assemblea_costituente-19460602.zip",
        ),
        sha256="assembly",
        rows=[
            source_row(
                {
                    "lista": "DC",
                    "voti_lista": "218383",
                    "elettori": "970156",
                    "votanti": "783865",
                },
                region=None,
            )
        ],
    )
    database.replace_archive(
        entry("referendum", referendum_date, "referendum-19950611.zip"),
        sha256="referendum",
        rows=[
            source_row(
                {
                    "num_referendum": "1",
                    "numvotisi": "10",
                    "numvotino": "20",
                },
                municipality=None,
            )
        ],
    )
    database.replace_archive(
        entry("comunali", municipal_date, "comunali-20240609.zip"),
        sha256="municipal",
        rows=[
            source_row(
                {"lista": "LISTA CIVICA", "voti": "100"},
                province="VITERBO",
                municipality="VITERBO",
            )
        ],
    )

    monkeypatch.setattr(main, "database", database)
    client = TestClient(main.app)

    response = client.get(
        "/api/v1/history/results",
        params={"comune": "ROMA", "category": "assemblea_costituente"},
    )
    assert response.status_code == 200
    assert response.json()["count"] == 1
    assert response.json()["rows"][0]["partito"] == "DC"

    csv_response = client.get(
        "/api/v1/history/results.csv",
        params={"comune": "ROMA"},
    )
    assert csv_response.status_code == 200
    assert "TIPO_ELEZIONE;DATA;TURNO;REGIONE" in csv_response.text
    assert ";ROMA;" in csv_response.text

    coverage_response = client.get(
        "/api/v1/history/coverage/municipality",
        params={"regione": "LAZIO", "comune": "ROMA"},
    )
    assert coverage_response.status_code == 200
    coverage = coverage_response.json()
    assert coverage["elections_checked"] == 3
    assert coverage["present"] == 1
    assert coverage["missing"] == 1
    assert coverage["not_available_at_municipality_level"] == 1
