import json
import sqlite3

from app.data_portability import checkpoint_database, checkout_database, store_status


def test_checkpoint_and_checkout_round_trip(tmp_path) -> None:
    source = tmp_path / "source.sqlite3"
    with sqlite3.connect(source) as connection:
        connection.execute("CREATE TABLE values_table(value TEXT)")
        connection.execute("INSERT INTO values_table VALUES ('verified')")
        connection.commit()

    shared = tmp_path / "shared"
    manifest = checkpoint_database(source, shared)
    assert manifest["format"] == "eligendo-sqlite-checkpoint-v1"
    assert manifest["bytes"] > 0
    assert store_status(shared)["sha256"] == manifest["sha256"]
    assert json.loads(
        (shared / "database" / "manifest.json").read_text(encoding="utf-8")
    )["sha256"] == manifest["sha256"]

    restored = tmp_path / "working" / "eligendo.sqlite3"
    checkout_database(shared, restored)
    with sqlite3.connect(restored) as connection:
        assert connection.execute("SELECT value FROM values_table").fetchone()[0] == "verified"
