from __future__ import annotations

import argparse
import hashlib
import json
import os
import sqlite3
import tempfile
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DATABASE_NAME = "eligendo.sqlite3"
MANIFEST_NAME = "manifest.json"


def file_sha256(path: Path, chunk_size: int = 8 * 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def _quick_check(path: Path) -> None:
    with closing(sqlite3.connect(path, timeout=60)) as connection:
        result = connection.execute("PRAGMA quick_check").fetchone()
    if result is None or result[0] != "ok":
        raise RuntimeError(f"SQLite quick_check failed for {path}: {result}")


def _database_counts(path: Path) -> dict[str, Any]:
    with closing(sqlite3.connect(path, timeout=60)) as connection:
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }
        counts: dict[str, Any] = {}
        for table in (
            "catalogues",
            "election_results",
            "page_snapshots",
            "official_municipality_verifications",
            "official_municipality_results",
            "official_verification_queue",
        ):
            if table in tables:
                counts[table] = connection.execute(
                    f'SELECT COUNT(*) FROM "{table}"'
                ).fetchone()[0]
        if "official_reconciliation_runs" in tables:
            counts["run_statuses"] = dict(
                connection.execute(
                    """SELECT status, COUNT(*)
                         FROM official_reconciliation_runs GROUP BY status"""
                ).fetchall()
            )
    return counts


def _sqlite_backup(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(source, timeout=60)) as source_connection:
        source_connection.execute("PRAGMA busy_timeout = 60000")
        with closing(sqlite3.connect(destination, timeout=60)) as destination_connection:
            source_connection.backup(destination_connection, pages=8192, sleep=0.1)


def checkpoint_database(database: Path, store: Path) -> dict[str, Any]:
    """Publish a verified, atomically replaceable database checkpoint."""
    database = database.resolve()
    store = store.resolve()
    if not database.is_file():
        raise FileNotFoundError(f"Working database not found: {database}")
    database_store = store / "database"
    database_store.mkdir(parents=True, exist_ok=True)
    target = database_store / DATABASE_NAME
    handle, temporary_name = tempfile.mkstemp(
        prefix=f".{DATABASE_NAME}.", suffix=".partial", dir=database_store
    )
    os.close(handle)
    temporary = Path(temporary_name)
    temporary.unlink()
    try:
        _sqlite_backup(database, temporary)
        _quick_check(temporary)
        digest = file_sha256(temporary)
        manifest = {
            "format": "eligendo-sqlite-checkpoint-v1",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "database": f"database/{DATABASE_NAME}",
            "bytes": temporary.stat().st_size,
            "sha256": digest,
            "counts": _database_counts(temporary),
        }
        os.replace(temporary, target)
        manifest_path = database_store / MANIFEST_NAME
        manifest_temporary = manifest_path.with_suffix(".json.partial")
        manifest_temporary.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        os.replace(manifest_temporary, manifest_path)
        return manifest
    finally:
        temporary.unlink(missing_ok=True)


def checkout_database(store: Path, database: Path) -> dict[str, Any]:
    """Restore and verify a local working copy from the shared checkpoint."""
    store = store.resolve()
    database = database.resolve()
    source = store / "database" / DATABASE_NAME
    manifest_path = store / "database" / MANIFEST_NAME
    if not source.is_file() or not manifest_path.is_file():
        raise FileNotFoundError(
            f"No portable checkpoint found below {store / 'database'}"
        )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    source_digest = file_sha256(source)
    if source_digest != manifest.get("sha256"):
        raise RuntimeError("Shared database checksum does not match manifest.json")
    database.parent.mkdir(parents=True, exist_ok=True)
    handle, temporary_name = tempfile.mkstemp(
        prefix=f".{database.name}.", suffix=".partial", dir=database.parent
    )
    os.close(handle)
    temporary = Path(temporary_name)
    temporary.unlink()
    try:
        _sqlite_backup(source, temporary)
        _quick_check(temporary)
        if file_sha256(temporary) != source_digest:
            raise RuntimeError("Restored working database checksum differs from checkpoint")
        os.replace(temporary, database)
        return manifest
    finally:
        temporary.unlink(missing_ok=True)


def store_status(store: Path) -> dict[str, Any]:
    manifest_path = store.resolve() / "database" / MANIFEST_NAME
    if not manifest_path.is_file():
        raise FileNotFoundError(f"Checkpoint manifest not found: {manifest_path}")
    return json.loads(manifest_path.read_text(encoding="utf-8"))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Create and restore portable Eligendo SQLite checkpoints."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    checkpoint = subparsers.add_parser("checkpoint")
    checkpoint.add_argument("--database", type=Path, required=True)
    checkpoint.add_argument("--store", type=Path, required=True)
    checkout = subparsers.add_parser("checkout")
    checkout.add_argument("--store", type=Path, required=True)
    checkout.add_argument("--database", type=Path, required=True)
    status = subparsers.add_parser("status")
    status.add_argument("--store", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "checkpoint":
        result = checkpoint_database(args.database, args.store)
    elif args.command == "checkout":
        result = checkout_database(args.store, args.database)
    else:
        result = store_status(args.store)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
