from datetime import date, datetime, timezone
from pathlib import Path

from fastapi.testclient import TestClient

from app import main
from app.archive import ArchiveRow
from app.config import Settings
from app.database import Database
from app.history import normalise_history_results
from app.schemas import CatalogueEntry, ElectionInfo, Geography, PageResult, ResultRecord
from app.service import EligendoService


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


def test_history_normaliser_preserves_full_college_field_names() -> None:
    results = normalise_history_results(
        [
            source_row(
                {
                    "collegioplurinominale": "LAZIO 1 - 01",
                    "collegiouninominale": "01 - ROMA - TRIONFALE",
                    "lista": "LISTA A",
                    "voti_lista": "60",
                    "elettori": "100",
                    "votanti": "80",
                }
            )
        ],
        category="camera",
        election_date=date(2018, 3, 4),
    )

    assert results[0].college == "01 - ROMA - TRIONFALE"


def test_history_normaliser_preserves_short_college_field() -> None:
    results = normalise_history_results(
        [
            source_row(
                {
                    "coll": "Brescia - Flero",
                    "lista": "LISTA A",
                    "voti_lista": "60",
                    "elettori": "100",
                    "votanti": "80",
                }
            )
        ],
        category="camera",
        election_date=date(2001, 5, 13),
    )

    assert results[0].college == "Brescia - Flero"


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


def test_main_results_disambiguate_homonymous_municipalities(
    tmp_path, monkeypatch
) -> None:
    database = Database(tmp_path / "homonyms.sqlite3")
    database.replace_archive(
        entry("camera", date(1958, 5, 25), "camera-19580525.zip"),
        sha256="homonyms",
        rows=[
            source_row(
                {"lista": "DC", "voti_lista": "100"},
                municipality="BRIONE",
                province="BRESCIA",
                region="LOMBARDIA",
                row_number=2,
            ),
            source_row(
                {"lista": "DC", "voti_lista": "200"},
                municipality="BRIONE",
                province="TRENTO",
                region="TRENTINO-ALTO ADIGE",
                row_number=3,
            ),
            source_row(
                {"lista": "DC", "voti_lista": "300"},
                municipality="CALLIANO",
                province=None,
                region="TRENTINO-ALTO ADIGE",
                row_number=4,
            ),
        ],
    )
    monkeypatch.setattr(main, "database", database)
    client = TestClient(main.app)

    response = client.get(
        "/api/v1/history/results",
        params={"category": "camera", "comune": "BRIONE"},
    )
    assert response.status_code == 200
    rows = response.json()["rows"]
    assert response.json()["count"] == 2
    assert {row["provincia"] for row in rows} == {"BRESCIA", "TRENTO"}
    assert {row["chiave_comune_tornata"] for row in rows} == {
        "1958-05-25|brescia|brione",
        "1958-05-25|trento|brione",
    }
    assert {row["stato_localizzazione"] for row in rows} == {
        "region_province_municipality"
    }

    csv_response = client.get(
        "/api/v1/history/results.csv",
        params={"category": "camera", "comune": "BRIONE"},
    )
    assert csv_response.status_code == 200
    assert "REGIONE;CIRCOSCRIZIONE;PROVINCIA;COMUNE;CHIAVE_COMUNE_TORNATA;STATO_LOCALIZZAZIONE" in csv_response.text
    assert "1958-05-25|brescia|brione" in csv_response.text
    assert "1958-05-25|trento|brione" in csv_response.text

    incomplete = client.get(
        "/api/v1/history/results",
        params={"category": "camera", "comune": "CALLIANO"},
    ).json()["rows"][0]
    assert incomplete["chiave_comune_tornata"] is None
    assert incomplete["stato_localizzazione"] == "region_municipality_incomplete"


def test_national_geography_table_groups_units_and_streams_csv(
    tmp_path, monkeypatch
) -> None:
    database = Database(tmp_path / "geography.sqlite3")
    database.replace_archive(
        entry("camera", date(1994, 3, 27), "camera-19940327.zip"),
        sha256="camera",
        rows=[
            source_row(
                {
                    "lista": "LISTA A",
                    "voti_lista": "40",
                    "elettori": "100",
                    "votanti": "80",
                    "voti_validi": "50",
                    "collegio": "ROMA 1",
                },
                row_number=2,
            ),
            source_row(
                {
                    "lista": "LISTA B",
                    "voti_lista": "10",
                    "elettori": "100",
                    "votanti": "80",
                    "voti_validi": "50",
                    "collegio": "ROMA 1",
                },
                file_name="candidate-results.csv",
                row_number=3,
            ),
            source_row(
                {
                    "lista": "LISTA A",
                    "voti_lista": "30",
                    "elettori": "70",
                    "votanti": "55",
                    "voti_validi": "60",
                },
                row_number=4,
                province="VITERBO",
                municipality="VITERBO",
            ),
            source_row(
                {
                    "lista": "LISTA A",
                    "voti_lista": "25",
                    "elettori": "60",
                    "votanti": "45",
                    "voti_validi": "50",
                },
                row_number=5,
                region="LOMBARDIA",
                province="MILANO",
                municipality="MILANO",
            ),
        ],
    )
    monkeypatch.setattr(main, "database", database)
    client = TestClient(main.app)

    response = client.get(
        "/api/v1/history/coverage/national",
        params={"category": "camera", "year": 1994},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["count"] == 3
    assert {row["comune"] for row in payload["rows"]} == {
        "ROMA",
        "VITERBO",
        "MILANO",
    }
    roma = next(row for row in payload["rows"] if row["comune"] == "ROMA")
    assert roma["regione"] == "LAZIO"
    assert roma["collegio"] == "ROMA 1"
    assert roma["righe"] == 2
    assert roma["soggetti"] == 2
    assert roma["file_count"] == 2

    csv_response = client.get(
        "/api/v1/history/coverage/national.csv",
        params={"category": "camera", "comune": "ROMA"},
    )
    assert csv_response.status_code == 200
    assert "TIPO_ELEZIONE;DATA;LIVELLO;REGIONE" in csv_response.text
    assert ";LAZIO;;ROMA;" in csv_response.text


def test_municipality_audit_reconstructs_split_colleges(
    tmp_path, monkeypatch
) -> None:
    database = Database(tmp_path / "audit.sqlite3")
    database.replace_archive(
        entry("camera", date(1992, 4, 5), "camera-19920405.zip"),
        sha256="reference",
        rows=[
            source_row(
                {
                    "lista": "LISTA A",
                    "voti_lista": "500",
                    "elettori": "1000",
                    "votanti": "800",
                }
            )
        ],
    )
    database.replace_archive(
        entry("camera", date(1994, 3, 27), "camera-19940327.zip"),
        sha256="split",
        rows=[
            source_row(
                {
                    "collegio": college,
                    "lista": "LISTA A",
                    "voti_lista": "250",
                    "elettori": "500",
                    "votanti": "400",
                },
                file_name="camera_proporzionale.txt",
                row_number=row_number,
            )
            for college, row_number in (("ROMA 1", 2), ("ROMA 2", 3))
        ],
    )

    rows = database.municipality_election_audit(
        municipality="ROMA",
        categories=("camera",),
    )

    assert len(rows) == 2
    split = next(row for row in rows if row["data"] == "1994-03-27")
    assert split["parti_rilevate"] == 2
    assert split["aventi_diritto"] == 1000
    assert split["voti_risultato"] == 500
    assert split["data_riferimento"] == "1992-04-05"
    assert split["rapporto_aventi_diritto_riferimento"] == 1.0
    assert split["data_precedente"] == "1992-04-05"
    assert split["votanti_precedenti"] == 800
    assert split["rapporto_votanti_precedenti"] == 1.0
    assert split["votanti_comparabili"] is True
    assert split["mappa_collegi_versione"] == "camera-mattarellum-1993-corrected"
    assert split["fonti_confini_ids"] == [
        "camera-boundaries-1993-536",
        "camera-boundaries-1993-536-correction",
    ]
    assert split["fonte_confini_id"] == "camera-boundaries-1993-536"
    assert split["stato"] == "pass"

    monkeypatch.setattr(main, "database", database)
    response = TestClient(main.app).get(
        "/api/v1/history/audit/municipality",
        params={"comune": "ROMA", "category": "camera"},
    )
    assert response.status_code == 200
    assert response.json()["elections_checked"] == 2
    assert response.json()["voter_tolerance"] == 0.35
    assert response.json()["passed"] == 2


def test_municipality_audit_uses_nearest_complete_split_election(tmp_path) -> None:
    database = Database(tmp_path / "nearest.sqlite3")
    for election_date, electors in (
        (date(1992, 4, 5), 800),
        (date(1994, 3, 27), 1000),
        (date(1996, 4, 21), 1020),
    ):
        database.replace_archive(
            entry("camera", election_date, f"camera-{election_date:%Y%m%d}.zip"),
            sha256=str(election_date),
            rows=[
                source_row(
                    {
                        "collegio": college,
                        "lista": "LISTA A",
                        "voti_lista": str(electors // 4),
                        "elettori": str(electors // 2),
                        "votanti": str(electors // 3),
                    },
                    row_number=row_number,
                )
                for row_number, college in enumerate(("ROMA 1", "ROMA 2"), start=2)
            ],
        )

    rows = database.municipality_election_audit(
        municipality="ROMA",
        categories=("camera",),
    )
    current = next(row for row in rows if row["data"] == "1996-04-21")
    assert current["data_riferimento"] == "1994-03-27"
    assert current["aventi_diritto_riferimento"] == 1000
    assert current["rapporto_aventi_diritto_riferimento"] == 1.02


def test_municipality_audit_flags_adjacent_voter_outlier_and_accepts_tolerance(
    tmp_path,
) -> None:
    database = Database(tmp_path / "voter-comparison.sqlite3")
    elections = (
        (date(1992, 4, 5), 800),
        (date(1994, 3, 27), 400),
        (date(1996, 4, 21), 820),
    )
    for election_date, voters in elections:
        database.replace_archive(
            entry("camera", election_date, f"camera-{election_date:%Y%m%d}.zip"),
            sha256=str(election_date),
            rows=[
                source_row(
                    {
                        "collegio": "ROMA 1",
                        "lista": "LISTA A",
                        "voti_lista": "300",
                        "elettori": "1000",
                        "votanti": str(voters),
                    }
                )
            ],
        )

    strict = database.municipality_election_audit(
        municipality="ROMA",
        categories=("camera",),
        voter_tolerance=0.35,
    )
    middle = next(row for row in strict if row["data"] == "1994-03-27")
    assert middle["data_precedente"] == "1992-04-05"
    assert middle["data_successiva"] == "1996-04-21"
    assert middle["rapporto_votanti_precedenti"] == 0.5
    assert middle["rapporto_votanti_successivi"] == 0.487805
    assert middle["votanti_comparabili"] is False
    assert middle["stato"] == "warning"

    tolerant = database.municipality_election_audit(
        municipality="ROMA",
        categories=("camera",),
        voter_tolerance=0.55,
    )
    middle = next(row for row in tolerant if row["data"] == "1994-03-27")
    assert middle["votanti_comparabili"] is True
    assert middle["stato"] == "pass"


def test_municipality_audit_reads_legacy_fragments_without_mutating_them(tmp_path) -> None:
    database = Database(tmp_path / "legacy.sqlite3")
    database.replace_archive(
        entry("senato", date(2001, 5, 13), "senato-20010513.zip"),
        sha256="legacy",
        rows=[
            source_row(
                {
                    "collegio": "Firenze Nord",
                    "lista": "LISTA A",
                    "voti_lista": "60",
                    "elettori": "100",
                    "votanti": "80",
                },
                municipality="Firenze Nord",
            )
        ],
    )
    with database.connect() as connection:
        connection.execute(
            "UPDATE election_results SET municipality='Firenze Nord', "
            "municipality_key='firenze_nord'"
        )
        connection.commit()

    rows = database.municipality_election_audit(
        municipality="FIRENZE",
        categories=("senato",),
    )

    assert len(rows) == 1
    with database.connect() as connection:
        stored = connection.execute(
            "SELECT municipality FROM election_results"
        ).fetchone()["municipality"]
    assert stored == "Firenze Nord"


def test_municipality_audit_reads_legacy_reggio_di_calabria_label(tmp_path) -> None:
    database = Database(tmp_path / "reggio.sqlite3")
    database.replace_archive(
        entry("camera", date(2001, 5, 13), "camera-20010513.zip"),
        sha256="reggio",
        rows=[
            source_row(
                {
                    "coll": "Reggio Calabria - Sud",
                    "lista": "LISTA A",
                    "voti_lista": "60",
                    "elettori": "100",
                    "votanti": "80",
                },
                municipality="Parte di Comune REGGIO DI CALABRIA",
            )
        ],
    )
    with database.connect() as connection:
        connection.execute(
            "UPDATE election_results SET municipality="
            "'Parte di Comune REGGIO DI CALABRIA', "
            "municipality_key='parte_di_comune_reggio_di_calabria'"
        )
        connection.commit()

    rows = database.municipality_election_audit(
        municipality="REGGIO CALABRIA",
        categories=("camera",),
    )

    assert len(rows) == 1


def test_official_municipality_page_verifies_split_party_totals(
    tmp_path, monkeypatch
) -> None:
    database = Database(tmp_path / "official-page.sqlite3")
    rows = []
    for municipality, electors, voters, party_a, party_b, row_number in (
        ("ROMA I", 500, 450, 100, 200, 2),
        ("ROMA II", 600, 500, 150, 250, 4),
    ):
        rows.extend(
            [
                source_row(
                    {
                        "collegio": municipality,
                        "lista": party,
                        "voti_lista": str(votes),
                        "elettori": str(electors),
                        "votanti": str(voters),
                    },
                    row_number=row_number + offset,
                    municipality=municipality,
                )
                for offset, (party, votes) in enumerate(
                    (("LISTA A", party_a), ("LISTA B", party_b))
                )
            ]
        )
    database.replace_archive(
        entry("camera", date(1958, 5, 25), "camera-19580525.zip"),
        sha256="official-page",
        rows=rows,
    )

    settings = Settings(
        data_dir=Path(tmp_path),
        database_path=tmp_path / "official-page.sqlite3",
        request_interval_seconds=0,
        request_timeout_seconds=1,
        catalogue_ttl_seconds=60,
        max_archive_bytes=1024,
        max_uncompressed_bytes=1024,
    )
    service = EligendoService(settings, database)
    official_page = PageResult(
        source_url="https://elezionistorico.interno.gov.it/index.php?tpel=C",
        retrieved_at=datetime.now(timezone.utc),
        election=ElectionInfo(code="C", name="Camera", date=date(1958, 5, 25)),
        geography=Geography(
            regione="LAZIO",
            provincia="ROMA",
            comune="ROMA",
        ),
        summary={"elettori": 1100, "votanti": 950},
        records=[
            ResultRecord(record_type="list", name="LISTA A", votes=250),
            ResultRecord(record_type="list", name="LISTA B", votes=450),
            ResultRecord(record_type="total", name="TOTALI", votes=700),
        ],
    )
    monkeypatch.setattr(service, "fetch_page", lambda url, store: official_page)
    monkeypatch.setattr(main, "service", service)

    response = TestClient(main.app).post(
        "/api/v1/history/audit/official-municipality-page",
        json={
            "url": official_page.source_url,
            "store": False,
            "relative_tolerance": 0,
        },
    )

    assert response.status_code == 200
    result = response.json()
    assert result["stato"] == "exact_match"
    assert result["partiti_confrontati"] == 2
    assert result["partiti_coincidenti"] == 2
    assert result["partiti_non_coincidenti"] == 0
    assert result["pagine_ufficiali"] == 1
    assert result["riepilogo"] == [
        {
            "campo": "aventi_diritto",
            "ufficiale": 1100,
            "ricostruito": 1100,
            "scarto": 0,
            "scarto_relativo": 0.0,
            "coincide": True,
        },
        {
            "campo": "votanti",
            "ufficiale": 950,
            "ricostruito": 950,
            "scarto": 0,
            "scarto_relativo": 0.0,
            "coincide": True,
        },
        {
            "campo": "voti_validi",
            "ufficiale": 700,
            "ricostruito": 700,
            "scarto": 0,
            "scarto_relativo": 0.0,
            "coincide": True,
        },
    ]

    component_urls = [
        "https://elezionistorico.interno.gov.it/index.php?tpel=C&part=1",
        "https://elezionistorico.interno.gov.it/index.php?tpel=C&part=2",
    ]
    components = {
        component_urls[0]: official_page.model_copy(
            update={
                "source_url": component_urls[0],
                "summary": {"elettori": 500, "votanti": 450},
                "records": [
                    ResultRecord(record_type="list", name="LISTA A", votes=100),
                    ResultRecord(record_type="list", name="LISTA B", votes=200),
                    ResultRecord(record_type="total", name="TOTALI", votes=300),
                ],
            }
        ),
        component_urls[1]: official_page.model_copy(
            update={
                "source_url": component_urls[1],
                "summary": {"elettori": 600, "votanti": 500},
                "records": [
                    ResultRecord(record_type="list", name="LISTA A", votes=150),
                    ResultRecord(record_type="list", name="LISTA B", votes=250),
                    ResultRecord(record_type="total", name="TOTALI", votes=400),
                ],
            }
        ),
    }
    monkeypatch.setattr(
        service,
        "fetch_page",
        lambda url, store: components[url],
    )
    batch_response = TestClient(main.app).post(
        "/api/v1/history/audit/official-municipality-pages",
        json={"urls": component_urls, "store": False},
    )
    assert batch_response.status_code == 200
    batch = batch_response.json()
    assert batch["stato"] == "exact_match"
    assert batch["pagine_ufficiali"] == 2
    assert batch["insieme_completo"] is False
    assert batch["source_urls"] == component_urls
    assert batch["partiti_coincidenti"] == 2

    corrected_components = dict(components)
    corrected_components[component_urls[1]] = components[
        component_urls[1]
    ].model_copy(update={"summary": {"elettori": 700, "votanti": 550}})
    monkeypatch.setattr(
        service,
        "fetch_page",
        lambda url, store: corrected_components[url],
    )
    service.verify_official_municipality_pages(
        component_urls,
        store=True,
        complete_set=True,
    )
    corrected = database.municipality_election_audit(
        municipality="ROMA",
        categories=("camera",),
    )[0]
    assert corrected["fonte_aggregazione"] == "official_municipality_pages"
    assert corrected["aventi_diritto"] == 1200
    assert corrected["votanti"] == 1000
    assert corrected["aventi_diritto_open_data"] == 1100
    assert corrected["votanti_open_data"] == 950
    assert corrected["verifica_ufficiale_pagine"] == 2
    service.close()
