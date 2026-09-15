# Eligendo API

Eligendo API is an independent local service for downloading, normalising, and
querying data from the Italian Ministry of the Interior's
[historical election archive](https://elezionistorico.interno.gov.it/).

The service combines two sources from the same official portal:

1. **Open Data archives**, intended for bulk downloads by election; and
2. **municipality-level HTML pages**, which reproduce the summaries shown on
   the website, including turnout, ballots, candidates, lists, votes,
   percentages, and seats.

Imported records are stored in SQLite. Municipal party results are also exposed
in the uniform format:

```text
DATA;COMUNE;PARTITO;VOTI
```

The field names in that compact export remain in Italian to match the requested
research format and the terminology used by the source. API documentation is
generated automatically with Swagger UI.

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

- Only HTTPS URLs on the Ministry's two allow-listed domains are accepted.
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
