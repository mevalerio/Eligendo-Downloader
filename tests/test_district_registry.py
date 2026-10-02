import csv
import importlib.util
from collections import defaultdict
from pathlib import Path

from app import district_registry
from app.district_registry import REGISTRY_FIELDS, legal_colleges, registry_rows

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "extract_district_maps_1993", ROOT / "scripts" / "extract_district_maps_1993.py"
)
extractor = importlib.util.module_from_spec(spec)
spec.loader.exec_module(extractor)


def _colleges(map_version: str) -> dict[tuple[str, str], set[int]]:
    colleges: dict[tuple[str, str], set[int]] = defaultdict(set)
    for row in registry_rows(map_version):
        if row["municipality"]:
            colleges[(row["geography"], row["municipality"])].add(int(row["college"]))
    return colleges


def test_shipped_1993_registry_has_every_college() -> None:
    camera = {(row["geography"], row["college"]) for row in registry_rows("camera-mattarellum-1993-corrected")}
    senate = {(row["geography"], row["college"]) for row in registry_rows("senato-mattarellum-1993-corrected")}
    assert len(camera) == 475
    assert len(senate) == 232


def test_shipped_1993_registry_splits_large_cities() -> None:
    colleges = _colleges("camera-mattarellum-1993-corrected")
    assert colleges[("LAZIO 1", "ROMA")] == set(range(1, 25))
    assert colleges[("CAMPANIA 1", "NAPOLI")] == set(range(1, 10))
    assert colleges[("LOMBARDIA 1", "MILANO")] == set(range(1, 12))
    assert colleges[("PIEMONTE 1", "TORINO")] == set(range(1, 9))
    # Ciampino shares college 12 with a piece of Rome.
    assert colleges[("LAZIO 1", "CIAMPINO")] == {12}


def test_legal_colleges_reads_the_applicable_map(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(district_registry, "REGISTRY_DIR", tmp_path)
    registry_rows.cache_clear()
    with (tmp_path / "camera-mattarellum-1993-corrected.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=REGISTRY_FIELDS)
        writer.writeheader()
        for college, municipality in ((1, "ROMA"), (2, "ROMA"), (12, "ROMA"), (12, "CIAMPINO"), (3, "CASTRO")):
            writer.writerow({"map_version": "camera-mattarellum-1993-corrected", "geography": "LAZIO 1",
                             "college": college, "municipality": municipality, "entry_type": "zone"})
    try:
        roma = legal_colleges(category="camera", year=1996, municipality="Roma", geography="LAZIO 1")
        assert roma["collegi"] == [1, 2, 12]
        assert roma["mappa_collegi_versione"] == "camera-mattarellum-1993-corrected"
        assert legal_colleges(category="camera", year=1996, municipality="CASTRO", geography="PUGLIA")["collegi"] == []
        assert legal_colleges(category="camera", year=1958, municipality="ROMA", geography="LAZIO 1") is None
    finally:
        registry_rows.cache_clear()


def test_extractor_classifies_decree_entries() -> None:
    lines = [
        (271, "( RM-MONTI )"),
        (271, "C RM-PRENESTINO-LABICANO"),
        (256, "{ FI EX-QUART.1 })"),
        (249, "{ PARMA-CIRC.1 )"),
        (170, "PONT-CANAVESE"),
        (170, "SAINT-MARCEL"),
        (170, "BORGARO TORINESE"),
    ]
    entries = extractor.college_entries(lines, 170)
    kinds = [(entry["kind"], entry.get("code"), entry.get("prefix")) for entry in entries]
    assert kinds == [
        ("zone", "RM", None),
        ("zone", "RM", None),
        ("zone", "FI", None),
        ("zone", None, "PARMA"),
        ("zone", None, "PONT"),  # resolved later: PONT is not a split city
        ("zone", None, "SAINT"),
        ("whole", None, None),
    ]


def test_extractor_reads_prose_colleges() -> None:
    salerno = [
        (296, "Comprende i seguenti comuni: Baronissi, Bracigliano,"),
        (296, "Calvanico, Pellezzano e San Mango Piemonte nonchè parte del"),
        (296, "territorio del comune di Salerno, delimitata come segue: confine"),
    ]
    entries = extractor.college_entries(salerno, 296)
    assert [e["name"] for e in entries if e["kind"] == "whole"] == [
        "BARONISSI", "BRACIGLIANO", "CALVANICO", "PELLEZZANO", "SAN MANGO PIEMONTE",
    ]
    assert [e["name"] for e in entries if e["kind"] == "described_part"] == ["SALERNO"]
    turin = [(10, "Comprende parte del territoric del comune di Terine"),
             (10, "delimitata come segue: asse corse Regina Margherita (dal")]
    assert [e["name"] for e in extractor.college_entries(turin, 10)] == ["TERINE"]


def test_extractor_name_matching_prefers_edits_and_refuses_ties() -> None:
    names = {extractor.normal(name): name for name in ("DUNO", "MADONE", "BARIANO", "BARZANO'")}
    assert extractor.match_name("DUNE", names) == ("DUNO", 0.75)
    assert extractor.match_name("BARANO", names)[0] is None
    assert extractor.match_name("MADONE", names) == ("MADONE", 1.0)
