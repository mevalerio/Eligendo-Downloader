# Portable data workflow

## Separation of code and data

The Git repository is the reproducible software layer. It contains source
code, database migrations, tests, documentation, and portable launch commands.
It deliberately excludes SQLite files, downloaded archives, cached pages, and
runtime logs.

The shared `ElectionData` directory is the canonical data layer:

```text
ElectionData/
├── database/
│   ├── eligendo.sqlite3
│   └── manifest.json
├── logs/
└── artifacts/
```

`manifest.json` records the checkpoint timestamp, byte size, SHA-256 digest,
table counts, and reconciliation-run statuses. A checkpoint is created through
SQLite's online backup API, checked with `PRAGMA quick_check`, hashed, and only
then atomically promoted to `database/eligendo.sqlite3`.

## Why the live database is local

OneDrive is appropriate for transferring closed, verified checkpoints. It is
not a database filesystem. SQLite's main file, write-ahead log, and shared-memory
file must remain mutually consistent while writes are occurring. A sync client
may upload those files at different times or create conflict copies.

The portable launcher therefore restores the shared checkpoint to:

```text
%LOCALAPPDATA%\Eligendo\eligendo.sqlite3
```

The crawler writes only to this local copy. It periodically publishes a new
verified checkpoint to OneDrive. Only one machine may run the writer at a time.

## Starting on another machine

1. Wait until OneDrive reports that `ElectionData/database` is fully synced.
2. Ensure the crawler is stopped on every other machine.
3. Clone the Git repository and check out the published branch.
4. Create a Python 3.11 or newer virtual environment.
5. Install the package with `python -m pip install -e ".[dev]"`.
6. Set `ELIGENDO_SHARED_DATA_DIR` to that machine's synced `ElectionData` path.
7. Run `scripts/run_portable.ps1`.

The queue, cached pages, verified results, and election-level run ledger are
inside the checkpoint. The launcher resumes incomplete work and skips complete
or unavailable elections.

## Recovery

If a machine loses power, its most recent local changes may not yet have reached
the shared checkpoint. Start that machine again and run `eligendo-data
checkpoint`, or deliberately resume from the latest shared checkpoint on a new
machine. Previously published checkpoints remain internally consistent; at
worst, work performed since the last checkpoint is repeated.

Never merge two independently advanced SQLite files. Choose the newest trusted
working copy and publish it as the next canonical checkpoint.

## Analytical access

SQLite remains the operational source for the single-writer crawler, cached
pages, provenance, and restart state. The final publication layer should expose
a best-available results view and partitioned Parquet exports. Official website
rows take precedence after a complete verification; immutable ZIP rows remain
available for provenance and cases where the website has no municipality data.
