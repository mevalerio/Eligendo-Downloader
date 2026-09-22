from datetime import date

from app.database import Database
from app.reconcile_all import pending_elections


def test_pending_elections_skips_terminal_runs(tmp_path) -> None:
    database = Database(tmp_path / "test.sqlite3")
    database.imported_elections = lambda categories: [  # type: ignore[method-assign]
        ("camera", date(1948, 4, 18)),
        ("senato", date(1948, 4, 18)),
        ("europee", date(1979, 6, 10)),
    ]
    database.store_reconciliation_run(
        category="camera",
        election_date=date(1948, 4, 18),
        status="complete",
    )
    database.store_reconciliation_run(
        category="senato",
        election_date=date(1948, 4, 18),
        status="unavailable",
    )

    assert pending_elections(database, ("camera", "senato", "europee")) == [
        ("europee", date(1979, 6, 10))
    ]
