from __future__ import annotations

import argparse
import sys
import time
from datetime import date
from pathlib import Path

from .config import Settings
from .database import Database
from .data_portability import checkpoint_database
from .reconcile import CATEGORY_CODES, crawl_and_reconcile


TERMINAL_RUN_STATUSES = {"complete", "unavailable"}


def pending_elections(
    database: Database,
    categories: tuple[str, ...],
    *,
    retry_complete: bool = False,
) -> list[tuple[str, date]]:
    statuses = database.reconciliation_run_statuses()
    return [
        (category, election_date)
        for category, election_date in database.imported_elections(categories)
        if retry_complete
        or statuses.get((category, election_date.isoformat()))
        not in TERMINAL_RUN_STATUSES
    ]


def run_all(
    *,
    settings: Settings,
    categories: tuple[str, ...],
    max_elections: int | None = None,
    retry_complete: bool = False,
    checkpoint_store: Path | None = None,
    checkpoint_hours: float = 6.0,
) -> dict[str, int]:
    database = Database(settings.database_path)
    targets = pending_elections(
        database, categories, retry_complete=retry_complete
    )
    if max_elections is not None:
        targets = targets[:max_elections]
    totals = {
        "selected": len(targets),
        "processed": 0,
        "complete": 0,
        "unavailable": 0,
        "partial": 0,
        "failed": 0,
    }
    last_checkpoint = time.monotonic()
    try:
        for index, (category, election_date) in enumerate(targets, start=1):
            totals["processed"] += 1
            print(
                f"[{index}/{len(targets)}] {category} {election_date.isoformat()}",
                flush=True,
            )
            try:
                result = crawl_and_reconcile(
                    settings=settings,
                    category=category,
                    election_date=election_date,
                )
                if not result["available"]:
                    outcome = "unavailable"
                elif result["complete"]:
                    outcome = "complete"
                else:
                    outcome = "partial"
                totals[outcome] += 1
                print(f"{outcome}: {result}", flush=True)
                if outcome == "partial":
                    print(
                        "stopping: the current election is incomplete; rerun to resume",
                        file=sys.stderr,
                        flush=True,
                    )
                    break
                if (
                    checkpoint_store is not None
                    and time.monotonic() - last_checkpoint
                    >= checkpoint_hours * 3600
                ):
                    print("publishing periodic shared-data checkpoint", flush=True)
                    checkpoint_database(settings.database_path, checkpoint_store)
                    last_checkpoint = time.monotonic()
            except Exception as exc:
                totals["failed"] += 1
                print(
                    f"failed: {category} {election_date}: {exc}",
                    file=sys.stderr,
                    flush=True,
                )
                break
    finally:
        if checkpoint_store is not None:
            print("publishing final shared-data checkpoint", flush=True)
            checkpoint_database(settings.database_path, checkpoint_store)
    print(f"totals: {totals}", flush=True)
    return totals


def _settings_with_database(settings: Settings, database_path: Path) -> Settings:
    return Settings(
        data_dir=settings.data_dir,
        database_path=database_path.resolve(),
        request_interval_seconds=settings.request_interval_seconds,
        request_timeout_seconds=settings.request_timeout_seconds,
        catalogue_ttl_seconds=settings.catalogue_ttl_seconds,
        max_archive_bytes=settings.max_archive_bytes,
        max_uncompressed_bytes=settings.max_uncompressed_bytes,
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Reconcile every imported election with official municipality pages."
    )
    parser.add_argument("--database", type=Path)
    parser.add_argument(
        "--categories",
        nargs="+",
        choices=sorted(CATEGORY_CODES),
        default=sorted(CATEGORY_CODES),
    )
    parser.add_argument("--max-elections", type=int)
    parser.add_argument("--retry-complete", action="store_true")
    parser.add_argument("--checkpoint-store", type=Path)
    parser.add_argument("--checkpoint-hours", type=float, default=6.0)
    args = parser.parse_args()
    settings = Settings.from_environment()
    if args.database:
        settings = _settings_with_database(settings, args.database)
    run_all(
        settings=settings,
        categories=tuple(args.categories),
        max_elections=args.max_elections,
        retry_complete=args.retry_complete,
        checkpoint_store=args.checkpoint_store,
        checkpoint_hours=args.checkpoint_hours,
    )


if __name__ == "__main__":
    main()
