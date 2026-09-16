# Changelog

All notable project changes are documented in this file.

## Unreleased

## 2.0.0

- Replaced the TypeScript demonstration application with a Python FastAPI
  service backed by official Ministry archives.
- Added official Open Data catalogue parsing and archive import.
- Added annual import of all municipal elections in the official catalogue.
- Added normalised municipal party results in JSON and CSV.
- Added first-round defaults to prevent repeated run-off list votes.
- Added detailed provenance fields for municipality-level results.
- Added TXT, CSV, and XLSX ingestion from official ZIP archives.
- Added municipality-level queries over imported rows.
- Added parsing and optional storage of exact historical archive pages.
- Added host allow-listing, redirect validation, rate limiting, archive limits,
  SHA-256 digests, and transactional imports.
- Rewrote project, API, architecture, and data documentation in English.
- Added Python 3.11–3.13 testing through GitHub Actions.

## 1.0.0

- Published the original TypeScript demonstration and municipality-query tools.
- Preserved this release in Git history under the `v1.0.0` tag.
