# Architecture

## Purpose

Eligendo API turns heterogeneous election files and municipality-level web
pages into queryable, provenance-preserving records. The application keeps raw
source fields available, maintains a compact table for municipal party results,
and builds a unified result table spanning all eight election categories.

## Data flow

```text
Official Open Data catalogue
          |
          v
  allow-listed HTTP client
          |
          v
 ZIP validation and parsing -----> raw archive rows
          |                              |
          v                              v
 all-election normalisation -------> SQLite
                                         |
                                         v
                            JSON and CSV API endpoints

Exact archive page -> HTML parser -> optional SQLite snapshot

Official legal catalogue -> article/PDF downloader -> hashed local corpus
```

## Components

- `app/http_client.py` validates schemes, hosts, ports, and redirect targets;
  applies the request interval; and enforces download-size limits.
- `app/catalogue.py` extracts and filters the official Open Data catalogue.
- `app/archive.py` validates ZIP paths, reads TXT/CSV/XLSX files, preserves
  source rows, filters preference and polling-station files where aggregate
  files exist, and derives municipal party-result records.
- `app/history.py` maps heterogeneous result, geography, electorate, turnout,
  ballot, and referendum fields to the unified historical result model. It can
  aggregate section-only local archives to municipalities and canonicalises
  historical college-part labels.
- `app/electoral_laws.py` records the applicable national electoral laws and
  official college-boundary instruments. District-map versions are selected
  independently by chamber and year and compose base instruments, territorial
  amendments, and errata corrige.
- `app/scraper.py` parses election metadata, geography, summaries,
  candidates, lists, totals, votes, percentages, and seats from HTML pages.
- `app/database.py` owns the SQLite schema, transactional replacement, and
  filtered queries, including the grouped national-election geography
  coverage table used to expose municipality and college splits.
- `app/reconcile.py` follows the website's encoded geography selectors for one
  election, validates the rendered election heading, and stores municipality
  comparisons and normalised official rows.
- `app/reconcile_all.py` runs that process sequentially for every imported
  Camera, Senato, European, regional, and municipal election, using the
  election-level restart ledger to resume safely.
- `app/data_portability.py` creates SHA-256-manifested SQLite backups for a
  synchronised data store and restores verified local working copies.
- `app/service.py` coordinates catalogue caching, downloads, parsing, hashes,
  and database writes.
- `app/main.py` exposes the FastAPI application, JSON endpoints, and streaming
  CSV export.

## Storage model

The SQLite database contains:

- catalogue metadata and archive digests;
- normalised raw rows with their original payload;
- unified historical result rows for every election category;
- municipal party-result rows;
- optional snapshots of parsed HTML pages.

An archive replacement is performed in a transaction. A failed import therefore
does not leave an election in a partially updated state.

## Normalisation boundary

The importer normalises column names to `snake_case` and recognises a controlled
set of aliases for geography, parties, candidates, referendum options, votes,
seats, electorate, turnout, ballots, and rounds. Unrecognised columns remain in
the raw payload. This design permits future alias additions without discarding
source information.

The unified table uses one row per published result subject: list, candidate,
or referendum option. Where a source exposes a municipality through named
districts or an explicit `Parte di Comune` label, the municipality is
canonicalised and the original subdivision is retained as the college.
Section-only archives are grouped by
municipality and result subject before insertion; their provenance uses a
`#municipality-aggregate` source marker.

Municipality reconstruction is a separate projection. It takes electors and
voters once per distinct college fragment, sums the fragments to the canonical
municipality, and retains the original college labels. The audit compares the
reconstructed voters with the other chamber on the same election date when
available. The closest earlier and later elections of the same chamber are the
fallback under a configurable tolerance. Every output row carries the selected
district-map version and links to all applicable official sources.

The compact municipal export is a projection:

```text
DATA, COMUNE, PARTITO, VOTI
```

It does not harmonise party identities across elections. By default, queries
select round one together with records whose source provides no round, avoiding
the repeated list values that may accompany run-off records.

The national geography coverage projection groups normalised result rows by
election, geography, college, round, and question, and collapses duplicate
source members into one row with a source-file list and count. It keeps
region-level and nation-level records when municipality data are absent, so a
coverage check does not mistake a broader source table for a missing town.

## Trust boundaries

External content is treated as untrusted. Network requests are restricted to
configured Ministry and official legal-publication hosts. Redirect targets are
revalidated, compressed and extracted size limits are applied, and archive
paths are checked before
reading members. The service should still be deployed with ordinary operating
system and network isolation when exposed beyond a research workstation.

## Extension points

- Add source-column aliases in `app/archive.py` with a fixture-based test.
- Add a new election-source parser as a separate module and retain provenance.
- Introduce a versioned party concordance as a new layer; do not overwrite
  published labels in the raw or compact tables.
- Replace SQLite only behind the database interface so the HTTP contract remains
  stable.
