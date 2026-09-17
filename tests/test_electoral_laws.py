from pathlib import Path

from fastapi.testclient import TestClient

from app import main
from app.config import Settings
from app.database import Database
from app.electoral_laws import (
    DISTRICT_MAP_VERSIONS,
    ELECTORAL_LAWS,
    district_map_for,
)
from app.http_client import Download, validate_url
from app.service import EligendoService


def settings(tmp_path: Path) -> Settings:
    return Settings(
        data_dir=tmp_path,
        database_path=tmp_path / "test.sqlite3",
        request_interval_seconds=0,
        request_timeout_seconds=1,
        catalogue_ttl_seconds=60,
        max_archive_bytes=1_000_000,
        max_uncompressed_bytes=1_000_000,
    )


def test_electoral_law_registry_covers_every_national_regime() -> None:
    assert len(ELECTORAL_LAWS) == 27
    assert {category for law in ELECTORAL_LAWS for category in law.applies_to} == {
        "assemblea_costituente",
        "camera",
        "senato",
        "europee",
        "referendum",
    }
    assert sum(law.kind == "boundary_decree" for law in ELECTORAL_LAWS) == 5
    assert sum(law.kind == "boundary_correction" for law in ELECTORAL_LAWS) == 8
    assert validate_url(ELECTORAL_LAWS[-1].download_url)


def test_electoral_law_catalogue_api(tmp_path, monkeypatch) -> None:
    service = EligendoService(settings(tmp_path), Database(tmp_path / "test.sqlite3"))
    monkeypatch.setattr(main, "service", service)
    try:
        response = TestClient(main.app).get("/api/v1/legal/electoral-laws")
    finally:
        service.close()

    assert response.status_code == 200
    assert len(response.json()) == 27
    assert response.json()[-1]["id"] == "parliament-boundaries-2020-177"


def test_district_map_versions_include_intermediate_changes_and_sources(
    tmp_path, monkeypatch
) -> None:
    assert len(DISTRICT_MAP_VERSIONS) == 13
    assert district_map_for("senato", 1958).id == "senato-1948-corrected"
    assert district_map_for("senato", 1963).id == "senato-1963-friuli"
    assert district_map_for("senato", 1992).id == "senato-1992-trentino"
    assert district_map_for("camera", 1994).source_ids == (
        "camera-boundaries-1993-536",
        "camera-boundaries-1993-536-correction",
    )

    service = EligendoService(settings(tmp_path), Database(tmp_path / "maps.sqlite3"))
    monkeypatch.setattr(main, "service", service)
    try:
        response = TestClient(main.app).get(
            "/api/v1/legal/district-maps",
            params={"year": 2018},
        )
    finally:
        service.close()

    assert response.status_code == 200
    assert len(response.json()) == 2
    assert all(len(row["source_urls"]) == 3 for row in response.json())


def test_electoral_law_download_is_hashed_and_resumable(tmp_path) -> None:
    service = EligendoService(settings(tmp_path), Database(tmp_path / "test.sqlite3"))
    menu_url = "https://www.gazzettaufficiale.it/atto/vediMenuHTML?law=1"
    article_url = "https://www.gazzettaufficiale.it/atto/caricaArticolo?law=1&art=1"
    payload = f'<a href="{article_url}">Article 1</a>'.encode()
    article = b"<html><body>official legal source</body></html>"
    calls = []

    def fake_get(url: str, *, max_bytes: int | None = None) -> Download:
        calls.append((url, max_bytes))
        if "caricaArticolo" in url:
            return Download(article, url, "text/html")
        return Download(payload, menu_url, "text/html")

    service.http.get = fake_get
    law_id = "assembly-1946-74"
    try:
        first = service.download_electoral_laws(ids=[law_id], overwrite=False)
        second = service.download_electoral_laws(ids=[law_id], overwrite=False)
    finally:
        service.close()

    assert first["downloaded"] == 1
    assert second["reused"] == 1
    assert len(calls) == 2
    saved = Path(first["files"][0]["local_path"]).read_bytes()
    assert payload in saved
    assert article in saved
    assert article_url.encode() in saved
    assert len(first["files"][0]["sha256"]) == 64
