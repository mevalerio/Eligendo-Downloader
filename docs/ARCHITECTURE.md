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
  aggregate section-only local archives to municipalities.
- `app/scraper.py` parses election metadata, geography, summaries,
  candidates, lists, totals, votes, percentages, and seats from HTML pages.
- `app/database.py` owns the SQLite schema, transactional replacement, and
  filtered queries.
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
or referendum option. Where a source exposes Rome through historical electoral
subdivisions, the municipality is canonicalised to `ROMA` and the original
subdivision is retained as the college. Section-only archives are grouped by
municipality and result subject before insertion; their provenance uses a
`#municipality-aggregate` source marker.

The compact municipal export is a projection:

```text
DATA, COMUNE, PARTITO, VOTI
```

It does not harmonise party identities across elections. By default, queries
select round one together with records whose source provides no round, avoiding
the repeated list values that may accompany run-off records.

## Trust boundaries

External content is treated as untrusted. Network requests are restricted to
the two configured Ministry hosts, redirect targets are revalidated, compressed
and extracted size limits are applied, and archive paths are checked before
reading members. The service should still be deployed with ordinary operating
system and network isolation when exposed beyond a research workstation.

## Extension points

- Add source-column aliases in `app/archive.py` with a fixture-based test.
- Add a new election-source parser as a separate module and retain provenance.
- Introduce a versioned party concordance as a new layer; do not overwrite
  published labels in the raw or compact tables.
- Replace SQLite only behind the database interface so the HTTP contract remains
  stable.
