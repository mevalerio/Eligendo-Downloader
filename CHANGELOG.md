# Changelog

All notable project changes are documented in this file.

## Unreleased

- Added municipality election keys and geographic completeness status to the
  main JSON and CSV results, so same-name municipalities can be distinguished
  when province is available and incomplete source geography is visible.
- Added JSON and streaming CSV national-election geography coverage tables,
  grouped by election, region, municipality, college, and source file for
  sense-checking historical geographic coverage.
- Added explicit district-map versioning separate from electoral-law versions,
  with eight additional official territorial amendments and corrections.
- Extended split-municipality validation to compare reconstructed voters with
  both adjacent elections under a configurable tolerance and return all
  applicable official source links.
- Canonicalised Roman-numeral, municipio, and quartiere fragment labels found
  in the official boundary tables.
- Added exact verification against Ministry municipality result pages,
  including party-level vote comparisons.
- Added multi-page verification for municipalities divided among several
  colleges, validated against all eight Rome components in the 1958 Senate
  election.
- Added persistent, explicitly complete official-page summaries that correct
  audit metadata while retaining the original Open Data values and exact page
  provenance.

## 2.2.0

- Added a downloadable, hashed catalogue of 19 principal national electoral
  laws and official college-boundary instruments from Gazzetta Ufficiale.
- Added complete offline HTML bundling of every article and annex linked by a
  Gazzetta act, plus bounded retries for transient network failures.
- Added a Chamber/Senate split-municipality audit with reconstructed college
  totals, nearest-election electorate comparisons, and boundary-source IDs.
- Canonicalised historical named districts and explicit `Parte di Comune`
  records for 28 split municipalities while preserving college labels.
- Added full and abbreviated historical college-field aliases used by the 1994
  to 2018 national archives.
- Documented the 1,020-row audit run and the remaining source anomalies.

## 2.1.0

- Added resumable bulk import for all eight election categories.
- Added a unified JSON and streaming CSV history export with election,
  geography, result, turnout, ballot, seat, and provenance fields.
- Added municipality coverage auditing across national and relevant local
  elections.
- Added referendum option normalisation and municipality aggregation for
  section-only local archives.
- Added support for recent European, regional, municipal, and referendum
  archive schemas and historical headerless files.
- Canonicalised historical Rome electoral subdivisions to municipality `ROMA`
  while preserving their college labels.
- Validated all 288 archives in the live catalogue available during the 2.1.0
  audit; every archive produced normalised result rows.

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
