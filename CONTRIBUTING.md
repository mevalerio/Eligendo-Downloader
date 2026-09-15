# Contributing

## Development setup

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
pytest -q
```

Use Python 3.11 or later. Tests must remain independent of the live Ministry
website: add the smallest representative HTML, TXT, CSV, or XLSX fixture needed
to exercise new behaviour.

## Changes to source parsing

Official files vary across election types and years. When adding a source-column
alias:

1. retain the original field in the raw payload;
2. document the mapping and its source;
3. add a fixture reproducing the relevant header;
4. test the normalised value and provenance fields; and
5. verify that existing formats still parse.

Party names must remain as published. Analytical harmonisation belongs in a
separate, versioned concordance.

## Pull requests

Keep each pull request focused. Explain which election types and source files
are affected, describe any API or schema change, and list the tests run. Do not
include downloaded archives, SQLite databases, credentials, or virtual
environments.

Before opening a pull request:

```powershell
pytest -q
git diff --check
```

Rebase the feature branch on the current target branch and avoid rewriting a
branch used by other contributors.
