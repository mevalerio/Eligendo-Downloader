from app.catalogue import catalogue_matches, parse_catalogue_html


HTML = """
<script>
var aliasFile = '/daithome/documenti/opendata';
var dataSet = [["assemblea_costituente", "1946",
"assemblea_costituente/assemblea_costituente-19460602.zip",
"assemblea_costituente-19460602.zip", "02/06/1946", "", "19460602"],
["camera", "1948", "camera/camera-19480418.zip",
"camera-19480418.zip", "18/04/1948", "", "19480418"],];
</script>
"""


def test_catalogue_parser_and_filter() -> None:
    entries = parse_catalogue_html(HTML)
    assert len(entries) == 2
    assert entries[0].election_date.isoformat() == "1946-06-02"
    assert entries[0].download_url.startswith("https://dait.interno.gov.it/")
    assert catalogue_matches(entries, category="camera", year=1948) == [entries[1]]
