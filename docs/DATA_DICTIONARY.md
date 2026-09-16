# Data dictionary

## Compact municipal result

| CSV field | JSON field | Type | Definition |
|---|---|---|---|
| `DATA` | `data` | ISO date | Election date published in the catalogue |
| `COMUNE` | `comune` | text | Municipality label published in the source |
| `PARTITO` | `partito` | text | Party or civic-list label published in the source |
| `VOTI` | `voti` | integer | Valid list votes in that source row |

The compact table's observational unit is an election-date, municipality, and
source-list row. A party label alone is not a stable identifier across years.
Two distinct civic lists may share a label and remain separate observations.

## Detailed municipal result

| CSV field | JSON field | Type | Definition |
|---|---|---|---|
| `DATA` | `data` | ISO date | Election date |
| `REGIONE` | `regione` | text or null | Region |
| `PROVINCIA` | `provincia` | text or null | Province |
| `COMUNE` | `comune` | text | Municipality |
| `PARTITO` | `partito` | text | Party or civic-list label |
| `VOTI` | `voti` | integer | List votes |
| `TURNO` | `turno` | integer or null | Ballot round, when supplied |
| `CANDIDATO` | `candidato` | text or null | Associated mayoral candidate |
| `SEGGI` | `seggi` | integer or null | Seats, when supplied |
| `FONTE_FILE` | `fonte_file` | text | Member file within the archive |
| `FONTE_RIGA` | `fonte_riga` | integer | One-based source row number |

## Query semantics

- Text filters use normalised search keys while responses preserve source
  labels.
- The default `turno=1` also includes rows with a null round because many
  historical files do not record it.
- Setting `tutti_turni=true` removes the round filter.
- `year` uses the election date rather than the download or import date.
- Pagination applies to JSON results. CSV export streams every matching row.

## Provenance

Each imported archive stores its official URL, catalogue metadata, and SHA-256
digest. Raw archive rows store the member filename and source row. These fields
allow an exported observation to be traced back to the exact imported archive.

## Longitudinal analysis

Labels may differ because of spelling, abbreviations, coalitions, civic lists,
or organisational change. A longitudinal analysis should define a separate
concordance with at least:

- the original label;
- a harmonised identifier and label;
- the election-date range;
- a documented coding rule;
- the concordance version.

Keeping this crosswalk separate preserves the distinction between published
data and analytical decisions.
