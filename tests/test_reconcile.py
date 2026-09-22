from datetime import date
from urllib.parse import parse_qs, urlparse

from app.http_client import Download, UpstreamError
from app.reconcile import (
    download_with_backoff,
    heading_election,
    root_url,
    selector_children,
)


def test_root_url_uses_official_category_and_date() -> None:
    query = parse_qs(urlparse(root_url("europee", date(1994, 6, 12))).query)
    assert query["tpel"] == ["E"]
    assert query["dtel"] == ["12/06/1994"]
    assert query["tpe"] == ["A"]

    municipal = parse_qs(
        urlparse(root_url("comunali", date(2018, 6, 10))).query
    )
    assert municipal["tpel"] == ["G"]


def test_selector_children_follow_encoded_levels_without_guessing_codes() -> None:
    root = root_url("camera", date(1958, 5, 25))
    html = b"""
    <select name="sel_sezione2">
      <option value="0">Scegli Circoscrizione</option>
      <option value="20-lev120">ROMA</option>
      <option value="21-lev121">ALTRO</option>
    </select>
    """
    children = selector_children(html, root)
    assert len(children) == 2
    first = parse_qs(urlparse(children[0]).query)
    assert first["ne1"] == ["20"]
    assert first["lev1"] == ["20"]
    assert first["levsut1"] == ["1"]
    assert first["tpe"] == ["C"]

    region_html = b"""
    <select name="sel_sezione2">
      <option value="0">Scegli Circoscrizione</option>
      <option value="20-lev120">ROMA</option>
    </select>
    <select name="sel_sezione3">
      <option value="0">Scegli Regione</option>
      <option value="7-lev27">LAZIO</option>
    </select>
    """
    grandchildren = selector_children(region_html, children[0])
    assert len(grandchildren) == 1
    query = parse_qs(urlparse(grandchildren[0]).query)
    assert query["ne1"] == ["20"]
    assert query["ne2"] == ["7"]
    assert query["lev2"] == ["7"]
    assert query["tpe"] == ["R"]


def test_heading_election_reads_the_election_actually_rendered() -> None:
    html = b"""
    <div id="headEnti"><h3>Comunali 10/06/2018 | Area ITALIA</h3></div>
    """
    assert heading_election(html) == ("Comunali", date(2018, 6, 10))


def test_heading_election_fails_closed_when_heading_is_missing() -> None:
    assert heading_election(b"<html></html>") == (None, None)


def test_download_with_backoff_recovers_transient_dns_failure(monkeypatch) -> None:
    class Client:
        attempts = 0

        def get(self, url, *, max_bytes):
            self.attempts += 1
            if self.attempts < 3:
                raise UpstreamError(f"Error connecting to {url}: DNS unavailable")
            return Download(b"ok", url, "text/html")

    client = Client()
    waits = []
    monkeypatch.setattr("app.reconcile.time.sleep", waits.append)
    result, attempts = download_with_backoff(  # type: ignore[arg-type]
        client,
        "https://elezionistorico.interno.gov.it/",
        max_bytes=100,
        max_attempts=3,
    )
    assert result.content == b"ok"
    assert attempts == 3
    assert waits == [2, 4]


def test_download_with_backoff_does_not_retry_permanent_error(monkeypatch) -> None:
    class Client:
        def get(self, url, *, max_bytes):
            raise UpstreamError("The portal returned HTTP 404.")

    monkeypatch.setattr(
        "app.reconcile.time.sleep",
        lambda _seconds: (_ for _ in ()).throw(AssertionError("unexpected wait")),
    )
    import pytest

    with pytest.raises(UpstreamError, match="404"):
        download_with_backoff(  # type: ignore[arg-type]
            Client(),
            "https://elezionistorico.interno.gov.it/missing",
            max_bytes=100,
            max_attempts=3,
        )
