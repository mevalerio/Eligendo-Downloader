import io
import zipfile

from app.archive import parse_zip_archive
from app.utils import canonical_municipality, slug


def test_archive_parser() -> None:
    csv_content = (
        '"CIRCOSCRIZIONE";"PROVINCIA";"COMUNE";"ELETTORI";"LISTA";"VOTI_LISTA"\n'
        '"ROMA";"FROSINONE";"CASSINO";7697;"DC";"1578"\n'
    ).encode("cp1252")
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w") as archive:
        archive.writestr("assemblea.txt", csv_content)

    rows = parse_zip_archive(stream.getvalue(), max_uncompressed_bytes=100_000)
    assert len(rows) == 1
    assert rows[0].municipality == "CASSINO"
    assert rows[0].municipality_key == "cassino"
    assert rows[0].payload["voti_lista"] == "1578"


def test_archive_rejects_path_traversal() -> None:
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w") as archive:
        archive.writestr("../escape.txt", "A;B\n1;2\n")

    try:
        parse_zip_archive(stream.getvalue(), max_uncompressed_bytes=100_000)
    except ValueError as exc:
        assert "unsafe" in str(exc).casefold()
    else:
        raise AssertionError("Expected unsafe ZIP path to be rejected")


def test_archive_can_retain_only_municipality_level_members() -> None:
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w") as archive:
        archive.writestr(
            "results_LivComune.csv",
            "COMUNE;LISTA;VOTI\nROMA;A;10\n",
        )
        archive.writestr(
            "results_LivSez.csv",
            "COMUNE;SEZIONE;LISTA;VOTI\nROMA;1;A;5\n",
        )
        archive.writestr(
            "Preferenze_LivComune.csv",
            "COMUNE;CANDIDATO;PREFERENZE\nROMA;ROSSI;3\n",
        )

    rows = parse_zip_archive(
        stream.getvalue(),
        max_uncompressed_bytes=100_000,
        municipality_level_only=True,
    )

    assert len(rows) == 1
    assert rows[0].file_name == "results_LivComune.csv"


def test_archive_infers_known_headerless_layouts() -> None:
    referendum = io.BytesIO()
    with zipfile.ZipFile(referendum, "w") as archive:
        archive.writestr(
            "referendum-19850609.txt",
            '"LAZIO";"ROMA";"ROMA";1;"QUESITO";"100";"0";80;0;45;30;5\n',
        )
    municipal = io.BytesIO()
    with zipfile.ZipFile(municipal, "w") as archive:
        archive.writestr(
            "comunali-20171105.txt",
            (
                '"LAZIO";"ROMA";"ROMA";100;80;5;"LISTA";"60";4;'
                '"ROSSI";"ANNA";"1/1/1970";"ROMA";"F";"S";"60"\n'
            ),
        )

    referendum_rows = parse_zip_archive(
        referendum.getvalue(),
        max_uncompressed_bytes=100_000,
    )
    municipal_rows = parse_zip_archive(
        municipal.getvalue(),
        max_uncompressed_bytes=100_000,
    )

    assert referendum_rows[0].payload["numvotisi"] == "45"
    assert municipal_rows[0].payload["descrlista"] == "LISTA"
    assert municipal_rows[0].payload["votilista"] == "60"


def test_historical_rome_constituency_is_canonicalised_as_municipality() -> None:
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w") as archive:
        archive.writestr(
            "camera.txt",
            (
                "circoscrizione;collegio;comune;lista;voti_lista\n"
                "LAZIO 1;Roma - Appio Latino;Roma - Appio Latino;LISTA A;100\n"
            ),
        )

    rows = parse_zip_archive(stream.getvalue(), max_uncompressed_bytes=100_000)

    assert len(rows) == 1
    assert rows[0].municipality == "ROMA"
    assert rows[0].municipality_key == "roma"
    assert rows[0].payload["collegio"] == "Roma - Appio Latino"


def test_official_submunicipal_labels_are_canonicalised() -> None:
    for label, expected in (
        ("TRIESTE II", "TRIESTE"),
        ("Roma: Municipio XIV", "ROMA"),
        ("Napoli: Quartiere 19 - Fuorigrotta", "NAPOLI"),
        ("Genova: Municipio VII - Ponente", "GENOVA"),
    ):
        municipality = canonical_municipality(label)
        assert municipality == expected
        assert slug(municipality) == expected.casefold()


def test_other_historical_split_cities_are_canonicalised() -> None:
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w") as archive:
        archive.writestr(
            "camera.txt",
            (
                "comune;lista;voti_lista\n"
                "Milano 10;LISTA A;100\n"
                "Napoli - Vomero;LISTA A;200\n"
                "Reggio Calabria - Sbarre;LISTA A;300\n"
                "Parma centro;LISTA A;400\n"
                "Messina centro storico;LISTA A;500\n"
                "Firenze Nord;LISTA A;600\n"
                "Palermo Sud;LISTA A;700\n"
                "Parte di Comune TARANTO;LISTA A;800\n"
                "parte del comune di Trieste;LISTA A;900\n"
                "Parte di Comune REGGIO DI CALABRIA;LISTA A;1000\n"
            ),
        )

    rows = parse_zip_archive(stream.getvalue(), max_uncompressed_bytes=100_000)

    assert [row.municipality for row in rows] == [
        "MILANO",
        "NAPOLI",
        "REGGIO CALABRIA",
        "PARMA",
        "MESSINA",
        "FIRENZE",
        "PALERMO",
        "TARANTO",
        "TRIESTE",
        "REGGIO CALABRIA",
    ]
