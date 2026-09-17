# Data dictionary

## Unified historical result

The `/api/v1/history/results.csv` export uses the following fields. Null values
mean that the source archive did not publish that item for the observation.

| CSV field | JSON field | Type | Definition |
|---|---|---|---|
| `TIPO_ELEZIONE` | `tipo_elezione` | text | Normalised election category |
| `DATA` | `data` | ISO date | Election date |
| `TURNO` | `turno` | integer or null | Ballot round |
| `REGIONE` | `regione` | text or null | Region |
| `CIRCOSCRIZIONE` | `circoscrizione` | text or null | Electoral constituency |
| `PROVINCIA` | `provincia` | text or null | Province |
| `COMUNE` | `comune` | text or null | Municipality |
| `NAZIONE` | `nazione` | text or null | Country for overseas results |
| `COLLEGIO` | `collegio` | text or null | Electoral college or retained Rome subdivision |
| `NUMERO_QUESITO` | `numero_quesito` | text or null | Referendum question number |
| `QUESITO` | `quesito` | text or null | Referendum question text |
| `TIPO_RISULTATO` | `tipo_risultato` | text | `list`, `candidate`, or `option` |
| `SOGGETTO` | `soggetto` | text | Result-bearing list, candidate, or option |
| `PARTITO` | `partito` | text or null | Party or list label |
| `CANDIDATO` | `candidato` | text or null | Candidate label |
| `OPZIONE_REFERENDUM` | `opzione_referendum` | text or null | `SI` or `NO` |
| `VOTI` | `voti` | integer | Votes for the result subject |
| `PERCENTUALE` | `percentuale` | number or null | Calculated share of the available valid-vote denominator |
| `SEGGI` | `seggi` | integer or null | Seats |
| `ELETTORI` | `elettori` | integer or null | Registered electors |
| `ELETTORI_MASCHI` | `elettori_maschi` | integer or null | Male electors |
| `VOTANTI` | `votanti` | integer or null | Voters |
| `VOTANTI_MASCHI` | `votanti_maschi` | integer or null | Male voters |
| `AFFLUENZA_PCT` | `affluenza_pct` | number or null | Voters divided by electors, as a percentage |
| `VOTI_VALIDI` | `voti_validi` | integer or null | Valid votes |
| `VOTI_VALIDI_LISTE` | `voti_validi_liste` | integer or null | Valid list votes |
| `VOTI_VALIDI_CANDIDATO` | `voti_validi_candidato` | integer or null | Valid candidate votes |
| `SCHEDE_BIANCHE` | `schede_bianche` | integer or null | Blank ballots |
| `SCHEDE_NON_VALIDE` | `schede_non_valide` | integer or null | Invalid ballots |
| `SCHEDE_CONTESTATE` | `schede_contestate` | integer or null | Contested ballots |
| `FONTE_URL` | `fonte_url` | URL | Official archive URL |
| `FONTE_FILE` | `fonte_file` | text | Member file within the ZIP archive |
| `FONTE_RIGA` | `fonte_riga` | integer | Source row; zero denotes a municipality aggregate |
| `SHA256` | `sha256` | text | Digest of the imported ZIP archive |

The eight `TIPO_ELEZIONE` values are `assemblea_costituente`, `camera`,
`senato`, `europee`, `referendum`, `regionali`, `provinciali`, and `comunali`.
The observational unit varies with the published source geography. Geography
fields should therefore be retained when aggregating rows.

## National-election geography coverage

The `/api/v1/history/coverage/national` endpoint and its `.csv` equivalent
provide a sense-check table for the five national categories. The observational
unit is an imported election, geography, college, round, and question. Several
rows for one municipality are therefore expected when a law divides it across
electoral colleges. Results from multiple source members are collapsed into one
geography row and retained in `FONTE_FILE`.

| CSV field | JSON field | Type | Definition |
|---|---|---|---|
| `TIPO_ELEZIONE` | `tipo_elezione` | text | National election category |
| `DATA` | `data` | ISO date | Election date |
| `LIVELLO` | `livello` | text | `comune`, `provincia`, `regione`, `nazione`, or `nazionale` |
| `REGIONE` | `regione` | text or null | Region published by the source |
| `CIRCOSCRIZIONE` | `circoscrizione` | text or null | Electoral constituency |
| `PROVINCIA` | `provincia` | text or null | Province |
| `COMUNE` | `comune` | text or null | Canonical municipality, where available |
| `NAZIONE` | `nazione` | text or null | Country for overseas records |
| `COLLEGIO` | `collegio` | text or null | Uninominal/plurinominal college or retained historical subdivision |
| `TURNO` | `turno` | integer or null | Ballot round |
| `NUMERO_QUESITO` | `numero_quesito` | text or null | Referendum question number |
| `RIGHE` | `righe` | integer | Normalised result rows represented by the coverage row |
| `SOGGETTI` | `soggetti` | integer | Distinct result subjects represented |
| `ELETTORI` | `elettori` | integer or null | Maximum registered-elector value in the group |
| `VOTANTI` | `votanti` | integer or null | Maximum voter value in the group |
| `VOTI_VALIDI` | `voti_validi` | integer or null | Maximum valid-vote value in the group |
| `FONTE_FILE` | `fonte_file` | text | Member file names represented by the row, comma-separated |
| `FONTE_FILE_COUNT` | `file_count` | integer | Number of distinct source members represented |
| `FONTE_URL` | `fonte_url` | URL | Official archive URL |
| `SHA256` | `sha256` | text | Digest of the imported archive |

The JSON endpoint accepts `category`, `year`, `election_date`, `regione`,
`provincia`, and `comune` filters, together with `limit` and `offset`. The CSV
endpoint accepts the same filters except pagination and streams every matching
row with a UTF-8 byte-order mark and semicolon delimiter.

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
- Unified-history filters can be combined across election type, year, exact
  date, geography, result type, subject, and round.
- A `FONTE_FILE` ending in `#municipality-aggregate` indicates that the source
  supplied polling-station rows and the importer summed them by municipality.

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

## Split-municipality audit

`/api/v1/history/audit/municipality` returns one selected aggregation layer per
Chamber or Senate election.

| JSON field | Type | Definition |
|---|---|---|
| `tipo_elezione` | text | `camera` or `senato` |
| `data` | ISO date | Election date |
| `comune` | text | Requested canonical municipality |
| `fonte_file` | text | Source member selected for the check |
| `tipo_risultato` | text | Result layer used for vote totals |
| `parti_rilevate` | integer | Distinct college or constituency fragments reconstructed |
| `aventi_diritto` | integer or null | Electors summed once per fragment |
| `votanti` | integer or null | Voters summed once per fragment |
| `voti_risultato` | integer | Result votes summed across subjects and fragments |
| `fonte_aggregazione` | text | `open_data` or `official_municipality_pages` when a complete page set supplies authoritative summary metadata |
| `aventi_diritto_open_data` | integer or null | Original Open Data electors retained when an official-page correction is applied |
| `votanti_open_data` | integer or null | Original Open Data voters retained when an official-page correction is applied |
| `voti_risultato_open_data` | integer or null | Original Open Data valid/result votes retained when an official-page correction is applied |
| `verifica_ufficiale_stato` | text or null | Comparison outcome recorded before applying the official summary |
| `verifica_ufficiale_pagine` | integer | Number of official pages used by the stored verification |
| `verifica_ufficiale_fonti` | array | Exact Ministry municipality page URLs used |
| `verifica_ufficiale_data` | timestamp or null | Time at which the official-page verification was stored |
| `rapporto_voti_aventi_diritto` | number or null | Result votes divided by electors |
| `data_riferimento` | ISO date or null | Nearest same-category election with electorate data |
| `aventi_diritto_riferimento` | integer or null | Electors in the reference election |
| `rapporto_aventi_diritto_riferimento` | number or null | Current electors divided by reference electors |
| `data_precedente` | ISO date or null | Closest earlier same-chamber election with voter data |
| `votanti_precedenti` | integer or null | Reconstructed voters in the earlier comparison election |
| `rapporto_votanti_precedenti` | number or null | Current voters divided by earlier-election voters |
| `data_successiva` | ISO date or null | Closest later same-chamber election with voter data |
| `votanti_successivi` | integer or null | Reconstructed voters in the later comparison election |
| `rapporto_votanti_successivi` | number or null | Current voters divided by later-election voters |
| `tolleranza_votanti` | number | Symmetric tolerance applied around ratio 1.0; default 0.35 |
| `votanti_comparabili` | boolean or null | Whether every available adjacent voter ratio is within tolerance |
| `mappa_collegi_versione` | text or null | Time-versioned district-map identifier |
| `fonti_confini_ids` | array | Every base instrument, amendment, and correction applied |
| `fonti_confini_urls` | array | Clickable official URLs corresponding to `fonti_confini_ids` |
| `fonte_confini_id` | text or null | Applicable item in the electoral-law catalogue |
| `stato` | text | `pass`, `warning`, `invalid`, or `insufficient_data` |

`invalid` indicates an arithmetic contradiction such as votes exceeding
voters or electors. `warning` identifies an unusually large voter/elector
change or vote/elector ratio. `insufficient_data` means the source does not
publish the required fields or no adjacent comparison exists. The check
preserves rather than silently rewrites anomalous official records.

## Official municipality-page verification

The single-page and multi-page verification endpoints return the same response
shape. The multi-page form sums every supplied Ministry page before comparing
it with the selected local aggregation layer.

| JSON field | Type | Definition |
|---|---|---|
| `source_url` | URL | First official municipality page, retained for single-page compatibility |
| `source_urls` | array | Complete set of official municipality pages used |
| `pagine_ufficiali` | integer | Number of distinct official pages aggregated |
| `insieme_completo` | boolean | Whether the caller declared that every municipality component page is present |
| `tipo_elezione` | text | `camera` or `senato` |
| `data` | ISO date | Election date shared by every page |
| `comune` | text | Municipality shared by every page |
| `tolleranza_relativa` | number | Allowed relative difference; default `0` |
| `stato` | text | `exact_match`, `within_tolerance`, `mismatch`, or `local_data_missing` |
| `riepilogo` | array | Official and reconstructed electors, voters, and valid votes, with differences |
| `partiti_confrontati` | integer | Union of official and reconstructed party identifiers |
| `partiti_coincidenti` | integer | Parties matching exactly or within the requested tolerance |
| `partiti_non_coincidenti` | integer | Mismatched or missing parties |
| `partiti` | array | Party-level official votes, reconstructed votes, differences, and status |

Only a stored verification with `complete_set=true` may supply authoritative
summary metadata to the municipality audit. This explicit declaration prevents
an incomplete subset of college pages from replacing a full municipal total.
