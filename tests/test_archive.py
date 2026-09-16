import io
import zipfile

from app.archive import parse_zip_archive


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
