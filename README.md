# Eligendo API

Eligendo API is an independent local service for downloading, normalising, and
querying data from the Italian Ministry of the Interior's
[historical election archive](https://elezionistorico.interno.gov.it/).

The service combines two sources from the same official portal:

1. **Open Data archives**, intended for bulk downloads by election; and
2. **municipality-level HTML pages**, which reproduce the summaries shown on
   the website, including turnout, ballots, candidates, lists, votes,
   percentages, and seats.

Imported records are stored in SQLite. The unified history API covers every
election category published in the Open Data catalogue and exposes results in
the core format:

```text
DATA;COMUNE;PARTITO;VOTI
```

The full export adds all metadata available in each source, including election
type, round, region, constituency, province, country, college, referendum
question, candidate, seats, electorate, voters, turnout, valid votes, ballots,
and provenance. Field names remain in Italian to match the requested research
format and the terminology used by the source. API documentation is generated
automatically with Swagger UI.

## Requirements

- Python 3.11 or later
- Network access to the two allow-listed Ministry domains
- Sufficient local storage for downloaded archives and the SQLite database

## Quick start

```powershell
cd outputs\eligendo-api
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
uvicorn app.main:app --reload
```

Open <http://127.0.0.1:8000/docs> to explore and run the API.

## Complete election history

### Import every published election

```powershell
$body = @{
  categories = @(
    "assemblea_costituente", "camera", "senato", "europee",
    "referendum", "regionali", "provinciali", "comunali"
  )
  skip_existing = $true
  continue_on_error = $true
} | ConvertTo-Json

Invoke-RestMethod `
  -Method Post `
  -Uri http://127.0.0.1:8000/api/v1/history/import `
  -ContentType application/json `
  -Body $body
```

The default request includes all eight categories. `start_year` and `end_year`
can restrict the period. Imports are resumable: with `skip_existing=true`, an
archive that already has normalised results is not downloaded again. A complete
history requires several gigabytes of local storage and may take substantial
time, depending on the catalogue and connection.

The importer handles aggregate municipality files and, where recent local
archives publish only polling-station results, aggregates those rows to the
municipality level. Source file and row references remain attached to every
observation.

### Query and export the unified dataset

Paginated JSON for Rome across all categories:

```text
GET /api/v1/history/results?comune=ROMA&limit=1000&offset=0
```

Complete semicolon-delimited CSV:

```text
GET /api/v1/history/results.csv
```

The CSV can be filtered with `category`, `year`, `election_date`, `regione`,
`provincia`, `comune`, `tipo_risultato`, `soggetto`, and `turno`. For example:

```text
GET /api/v1/history/results.csv?category=camera&year=2022&comune=ROMA
```

`tipo_risultato` is `list`, `candidate`, or `option`. Referendum `SI` and `NO`
votes are separate option rows. The complete column definition is in the
[data dictionary](docs/DATA_DICTIONARY.md).

### Sense-check election geography

```text
GET /api/v1/history/coverage/national?category=camera&year=1994
GET /api/v1/history/coverage/national.csv?comune=ROMA
```

These endpoints list the geographic units represented in each imported
national election (`assemblea_costituente`, `camera`, `senato`, `europee`, and
`referendum`). A row is an election, geography, college, round, and question;
multiple source members are collapsed and listed in the provenance fields. It preserves region, province, municipality,
constituency, country, electorate, voters, valid votes, row and subject
counts, and archive provenance. This makes municipality splits visible while
retaining broader region- or nation-level records where the source does not
publish municipality data. JSON is paginated; the CSV streams all matches and
uses semicolons.

### Check Rome across elections involving Lazio

```text
GET /api/v1/history/coverage/municipality?regione=LAZIO&comune=ROMA
```

The check includes every national election and each local election whose
imported results contain Lazio. Status values mean:

- `present`: the archive contains result rows indexed to Rome;
- `missing`: municipality-level data exist, but Rome did not appear among the
  municipalities voting in that particular local election; and
- `not_available_at_municipality_level`: the archive publishes results only at
  a broader geography, so Rome cannot be tested from that file.

Historical Chamber and Senate archives that label a city by electoral
subdivision (for example, `Roma - Appio Latino`, `Firenze Nord`, or
`Parte di Comune TARANTO`) are indexed under the canonical municipality; the
original electoral subdivision remains available in `COLLEGIO`.

### Download the electoral-law corpus

The legal catalogue covers the principal post-war national electoral regimes
represented in the archive. Its 27 sources include the 1946 Constituent
Assembly rules, Chamber, Senate, European and referendum laws, intermediate
territorial revisions from 1948, 1956, 1963 and 1991, the 1993, 2017 and 2020
boundary instruments, and their official corrections.

```text
GET /api/v1/legal/electoral-laws
```

The district-map table separates territorial versions from electoral-law
versions and includes clickable source URLs:

```text
GET /api/v1/legal/district-maps
GET /api/v1/legal/district-maps?category=senato&year=1992
```

Download and SHA-256 hash every source:

```powershell
$body = @{ overwrite = $false } | ConvertTo-Json
Invoke-RestMethod `
  -Method Post `
  -Uri http://127.0.0.1:8000/api/v1/legal/electoral-laws/download `
  -ContentType application/json `
  -Body $body
```

Gazzetta Ufficiale HTML acts are saved as self-contained bundles containing
the act menu and every linked article or annex. Large boundary supplements are
retained as the official PDFs. Existing files are reused unless
`overwrite=true`; every result reports its path, byte size and digest.

### Audit a split municipality

```text
GET /api/v1/history/audit/municipality?comune=ROMA
```

The audit reconstructs municipality totals across every reported college,
checks votes against voters and electors, and compares voters with both the
previous and following election of the same chamber. The default tolerance is
35 per cent and can be changed with `tolleranza_votanti=0.25`, for example.
`parti_rilevate` records the number of college fragments found,
`mappa_collegi_versione` identifies the applicable territorial version, and
`fonti_confini_urls` links every base instrument and correction. Use
`category=camera` or `category=senato` to restrict the check. The validation
method is documented in [Split-municipality audit](docs/SPLIT_MUNICIPALITY_AUDIT.md)
and the territorial sources are evaluated in
[District-map versions](docs/DISTRICT_MAP_VERSIONS.md).

### Verify against official municipality pages

Use an exact municipality result page as the authoritative counter-check:

```powershell
$body = @{
  url = "https://elezionistorico.interno.gov.it/index.php?tpel=C&dtel=25/05/1958&..."
  store = $true
  relative_tolerance = 0
  complete_set = $true
} | ConvertTo-Json

Invoke-RestMethod `
  -Method Post `
  -Uri http://127.0.0.1:8000/api/v1/history/audit/official-municipality-page `
  -ContentType application/json `
  -Body $body
```

For a municipality divided among several colleges, submit every official
municipality page in `urls` to
`POST /api/v1/history/audit/official-municipality-pages`. The endpoint sums
electors, voters, valid votes, and each party's votes before comparing the
result with the locally reconstructed municipality. It rejects pages from
different chambers, election dates, or municipalities. The default tolerance
is zero, so `exact_match` means equality down to the individual vote.
Set `complete_set=true` only after supplying every component page. The stored
verification then becomes the audit's authoritative summary source; the raw
Open Data electors, voters, and valid votes remain available in the
`*_open_data` fields.

The live 1958 Rome checks are exact:

| Election | Official pages | Electors | Voters | Valid votes | Parties | Result |
|---|---:|---:|---:|---:|---:|---|
| Chamber, 25 May 1958 | 1 | 1,243,752 | 1,183,771 | 1,160,923 | 13/13 | `exact_match` |
| Senate, 25 May 1958 | 8 | 1,131,128 | 1,069,618 | 1,032,267 | 10/10 | `exact_match` |

The same eight-page procedure identified missing Open Data summary components
for Rome in the 1948 and 1953 Senate elections. Official electors/voters are
915,306/797,083 and 986,155/916,069 respectively. All party votes and total
valid votes already matched. Applying these provenance-preserving corrections
makes 37 of Rome's 38 Chamber/Senate audit rows pass; the 2006 Senate row
retains `insufficient_data` because its source omits the required metadata.

This gives official municipality pages priority as a direct validation source.
The adjacent-election test remains a diagnostic fallback for cases where a
complete set of municipality pages has not yet been collected.

## Municipal results by year

### Import every municipal election held in a year

```powershell
$body = @{
  year = 2021
  continue_on_error = $true
} | ConvertTo-Json

Invoke-RestMethod `
  -Method Post `
  -Uri http://127.0.0.1:8000/api/v1/municipal/import-year `
  -ContentType application/json `
  -Body $body
```

The official catalogue may contain several municipal elections for the same
year. The endpoint finds and imports every matching archive. TXT, CSV, and XLSX
files contained in the official ZIP archives are supported.

### Query the compact party-result format

Paginated JSON:

```text
GET /api/v1/municipal/party-results?year=2021&limit=1000&offset=0
```

Complete CSV for the year:

```text
GET /api/v1/municipal/party-results.csv?year=2021
```

The CSV is encoded as UTF-8 with a byte-order mark and uses semicolons, which
makes it suitable for common continental European spreadsheet settings. Its
columns are:

```text
DATA;COMUNE;PARTITO;VOTI
```

To include region, province, ballot round, candidate, seats, and source
references:

```text
GET /api/v1/municipal/party-results.csv?year=2021&dettagliato=true
```

The filters `year`, `election_date`, `comune`, `provincia`, and
`partito` may be combined. By default, results include the first round and
historical records without a round field. This avoids counting list votes again
when the same values appear in run-off rows. To retrieve every original round:

```text
GET /api/v1/municipal/party-results?year=2021&tutti_turni=true
```

Distinct civic lists that share a name remain separate source rows. The detailed
export identifies them through the candidate and source-row fields.

## General archive access

### Browse the official catalogue

```text
GET /api/v1/catalogue?category=assemblea_costituente&year=1946
```

| Page code | Open Data category | Election type |
|---|---|---|
| `A` | `assemblea_costituente` | Constituent Assembly |
| `C` | `camera` | Chamber of Deputies |
| `S` | `senato` | Senate of the Republic |
| `E` | `europee` | European Parliament |
| `F` | `referendum` | Referendum |
| `R` | `regionali` | Regional elections |
| `P` | `provinciali` | Provincial elections |
| `G` | `comunali` | Municipal elections |

### Import one election

```powershell
$body = @{
  category = "assemblea_costituente"
  election_date = "1946-06-02"
} | ConvertTo-Json

Invoke-RestMethod `
  -Method Post `
  -Uri http://127.0.0.1:8000/api/v1/archives/import `
  -ContentType application/json `
  -Body $body
```

The service downloads the corresponding official ZIP archive, calculates its
SHA-256 digest, normalises column names, and atomically replaces any previous
import of the same election.

### Query one municipality

```text
GET /api/v1/archives/results?category=assemblea_costituente&election_date=1946-06-02&comune=CASSINO
```

The response retains the original columns with normalised `snake_case` names.
Each row also contains `_meta`, which records the source file and row number.
To list all municipalities found in an imported election:

```text
GET /api/v1/archives/municipalities?category=assemblea_costituente&election_date=1946-06-02
```

### Parse an exact archive page

```powershell
$body = @{
  url = "https://elezionistorico.interno.gov.it/index.php?tpel=A&dtel=02/06/1946&tpa=I&tpe=C&lev0=0&levsut0=0&lev1=20&levsut1=1&lev2=33&levsut2=2&levsut3=3&ne1=20&ne2=33&es0=S&es1=S&es2=S&es3=N&ms=S&ne3=330190&lev3=190"
  store = $true
} | ConvertTo-Json

Invoke-RestMethod `
  -Method Post `
  -Uri http://127.0.0.1:8000/api/v1/pages/parse `
  -ContentType application/json `
  -Body $body
```

The response distinguishes `candidate`, `list`, `coalition_total`,
`total`, and `option` records. Municipal lists contain a `parent_id`
linking them to their candidate.

## Endpoint summary

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/health` | Report service status |
| `GET` | `/api/v1/catalogue` | List and filter official archives |
| `POST` | `/api/v1/archives/import` | Download and import one election |
| `GET` | `/api/v1/archives/results` | Search by election, municipality, and province |
| `GET` | `/api/v1/archives/municipalities` | List municipalities in an imported election |
| `POST` | `/api/v1/pages/parse` | Parse one exact archive URL |
| `POST` | `/api/v1/history/import` | Resumably import all selected election categories |
| `GET` | `/api/v1/history/results` | Query unified all-election results as JSON |
| `GET` | `/api/v1/history/results.csv` | Stream the complete or filtered history as CSV |
| `GET` | `/api/v1/history/coverage/national` | List regions, municipalities, and colleges by national election |
| `GET` | `/api/v1/history/coverage/national.csv` | Stream the national geography table as CSV |
| `GET` | `/api/v1/history/coverage/municipality` | Audit a municipality across relevant elections |
| `GET` | `/api/v1/history/audit/municipality` | Reconstruct and sense-check a split municipality |
| `POST` | `/api/v1/history/audit/official-municipality-page` | Compare one official municipality page with reconstructed totals |
| `POST` | `/api/v1/history/audit/official-municipality-pages` | Aggregate split official pages and compare them with reconstructed totals |
| `GET` | `/api/v1/legal/electoral-laws` | List official electoral laws and boundary instruments |
| `GET` | `/api/v1/legal/district-maps` | List time-versioned district maps and official source links |
| `POST` | `/api/v1/legal/electoral-laws/download` | Download, bundle, and hash legal sources |
| `POST` | `/api/v1/municipal/import-year` | Import all municipal elections for a year |
| `GET` | `/api/v1/municipal/party-results` | Return normalised party results as JSON |
| `GET` | `/api/v1/municipal/party-results.csv` | Export filtered results as CSV |

## Docker

```powershell
docker build -t eligendo-api .
docker run --rm -p 8000:8000 -v eligendo-data:/service/data eligendo-api
```

## Configuration

| Environment variable | Default | Meaning |
|---|---:|---|
| `ELIGENDO_DATA_DIR` | `./data` | Local data directory |
| `ELIGENDO_DATABASE_PATH` | `./data/eligendo.sqlite3` | SQLite database path |
| `ELIGENDO_REQUEST_INTERVAL_SECONDS` | `0.8` | Minimum delay between requests |
| `ELIGENDO_REQUEST_TIMEOUT_SECONDS` | `30` | HTTP timeout |
| `ELIGENDO_CATALOGUE_TTL_SECONDS` | `3600` | Catalogue cache lifetime |
| `ELIGENDO_MAX_ARCHIVE_BYTES` | `262144000` | Compressed ZIP size limit |
| `ELIGENDO_MAX_UNCOMPRESSED_BYTES` | `2147483648` | Extracted ZIP size limit |

## Data integrity and safety

- Only HTTPS URLs on the configured Ministry, Gazzetta Ufficiale, and
  Normattiva domains are accepted.
- Every redirect target is validated before it is followed.
- Requests are rate-limited and the official catalogue is cached.
- ZIP archives are checked for configured size limits and unsafe paths.
- TXT, CSV, and XLSX values are read without forcing dates and numbers to text.
- Each imported archive is identified by a SHA-256 digest.
- SQLite transactions prevent partially imported elections.

Party and list labels are preserved as published. They are not harmonised
across years, spelling variants, coalitions, or successor organisations.
Researchers requiring longitudinal party series should add a separate,
versioned concordance rather than altering the source label.

See [Data dictionary](docs/DATA_DICTIONARY.md),
[Architecture](docs/ARCHITECTURE.md), and
[Git workflow](docs/GIT_WORKFLOW.md) for further details.

## Tests

```powershell
pytest -q
```

The test suite uses local fixtures and does not require the live Ministry
website.

## Project status and attribution

This project is an independent client and is not an official API of the Italian
Ministry of the Interior. Bulk collections should use the official Open Data
archives. HTML parsing is intended for validation, supplementation, or fallback
use, subject to the source website's terms and a prudent request interval.

## Licence

Eligendo API is distributed under the [MIT Licence](LICENSE).
