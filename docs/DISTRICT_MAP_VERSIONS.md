# District-map versions and municipality reconstruction

## Principle

Electoral law and electoral geography are versioned separately. A voting
system may remain in force while the territorial composition of one or more
districts changes. Municipality reconstruction therefore uses a
`district_map_version` selected by chamber and election year, together with
every amendment and official correction applicable to that version.

The source links below point to Gazzetta Ufficiale. They are also returned by
`GET /api/v1/legal/district-maps` in `source_urls`.

## Version table

| Election years | Chamber | `district_map_version` | Geographic unit | Official sources |
|---|---|---|---|---|
| 1948-1953 | Chamber | `camera-1948-table-a` | Constituency | [DPR 26/1948](https://www.gazzettaufficiale.it/eli/id/1948/02/06/048U0026/sg); [Law 148/1953](https://www.gazzettaufficiale.it/eli/id/1953/03/31/053U0148/sg) |
| 1958-1992 | Chamber | `camera-1958-table-a-trieste` | Constituency | [Law 493/1956](https://www.gazzettaufficiale.it/eli/id/1956/06/12/056U0493/sg); [DPR 361/1957](https://www.gazzettaufficiale.it/eli/id/1957/06/03/057U0361/sg) |
| 1948-1958 | Senate | `senato-1948-corrected` | Single-member college | [DPR 30/1948](https://www.gazzettaufficiale.it/eli/id/1948/02/07/048U0030/sg); [DPR 84/1948](https://www.gazzettaufficiale.it/eli/id/1948/03/01/048U0084/sg) |
| 1963-1987 | Senate | `senato-1963-friuli` | Single-member college | [DPR 30/1948](https://www.gazzettaufficiale.it/eli/id/1948/02/07/048U0030/sg); [DPR 84/1948](https://www.gazzettaufficiale.it/eli/id/1948/03/01/048U0084/sg); [Law 55/1963](https://www.gazzettaufficiale.it/eli/id/1963/02/15/063U0055/sg) |
| 1992 | Senate | `senato-1992-trentino` | Single-member college | [DPR 30/1948](https://www.gazzettaufficiale.it/eli/id/1948/02/07/048U0030/sg); [DPR 84/1948](https://www.gazzettaufficiale.it/eli/id/1948/03/01/048U0084/sg); [Law 55/1963](https://www.gazzettaufficiale.it/eli/id/1963/02/15/063U0055/sg); [Law 422/1991](https://www.gazzettaufficiale.it/eli/id/1992/01/04/092G0002/sg) |
| 1994-2001 | Chamber | `camera-mattarellum-1993-corrected` | Single-member college | [Legislative Decree 536/1993](https://www.gazzettaufficiale.it/eli/gu/1993/12/27/302/so/120/sg/pdf); [errata corrige](https://www.gazzettaufficiale.it/eli/id/1994/01/13/094A0228/sg) |
| 1994-2001 | Senate | `senato-mattarellum-1993-corrected` | Single-member college | [Legislative Decree 535/1993](https://www.gazzettaufficiale.it/eli/gu/1993/12/27/302/so/120/sg/pdf); [errata corrige](https://www.gazzettaufficiale.it/eli/id/1993/12/31/093A7407/sg); [Law 422/1991](https://www.gazzettaufficiale.it/eli/id/1992/01/04/092G0002/sg) |
| 2006-2013 | Chamber | `camera-porcellum-table-a` | Constituency | [DPR 361/1957](https://www.gazzettaufficiale.it/eli/id/1957/06/03/057U0361/sg); [Law 270/2005](https://www.gazzettaufficiale.it/eli/id/2005/12/30/005G0284/sg) |
| 2006-2013 | Senate | `senato-porcellum-regions` | Region, with the Trentino-Alto Adige exception | [Law 270/2005](https://www.gazzettaufficiale.it/eli/id/2005/12/30/005G0284/sg); [Law 422/1991](https://www.gazzettaufficiale.it/eli/id/1992/01/04/092G0002/sg) |
| 2018 | Chamber | `parliament-rosatellum-2017-corrected` | Single- and multi-member colleges | [Legislative Decree 189/2017](https://www.gazzettaufficiale.it/eli/gu/2017/12/19/295/so/58/sg/pdf); [20 December correction](https://www.gazzettaufficiale.it/eli/id/2017/12/20/17A08633/sg); [12 January correction](https://www.gazzettaufficiale.it/eli/id/2018/01/12/18A00307/sg) |
| 2018 | Senate | `parliament-rosatellum-2017-corrected` | Single- and multi-member colleges | [Legislative Decree 189/2017](https://www.gazzettaufficiale.it/eli/gu/2017/12/19/295/so/58/sg/pdf); [20 December correction](https://www.gazzettaufficiale.it/eli/id/2017/12/20/17A08633/sg); [12 January correction](https://www.gazzettaufficiale.it/eli/id/2018/01/12/18A00307/sg) |
| 2022 onwards | Chamber | `parliament-rosatellum-2020` | Single- and multi-member colleges | [Legislative Decree 177/2020](https://www.gazzettaufficiale.it/eli/gu/2020/12/29/321/so/45/sg/pdf) |
| 2022 onwards | Senate | `parliament-rosatellum-2020` | Single- and multi-member colleges | [Legislative Decree 177/2020](https://www.gazzettaufficiale.it/eli/gu/2020/12/29/321/so/45/sg/pdf) |

## Evaluation of the new sources

- Law 148/1953 changes the Chamber seat-allocation rules and does not create a
  new general territorial map. The 1948 map therefore remains the appropriate
  version for the 1953 election.
- Law 493/1956 explicitly adds Trieste, Duino-Aurisina, Monrupino, Muggia, San
  Dorligo della Valle and Sgonico as the thirty-second Chamber constituency.
- Law 55/1963 contains a replacement Senate table for Friuli-Venezia Giulia.
  It explicitly divides Trieste into `Trieste I` and `Trieste II`, including
  submunicipal zones. These labels are now canonicalised to municipality
  `TRIESTE` while the original college remains available.
- Law 422/1991 contains the municipality lists for the six Trentino-Alto Adige
  Senate colleges and confirms that DPR 30/1948 must be read with DPR 84/1948.
- The Senate 1993 correction changes an erroneous heading from Valle d'Aosta
  to Molise. The Chamber correction assigns the affected Piemonte 2 entries to
  college 2. Both corrections are part of the Mattarellum map versions.
- The 20 December 2017 notice restores the decree's entry-into-force article;
  it does not change a boundary. The 12 January 2018 notice is territorial: it
  adds Villetta Barrea after Villavallelonga in the relevant table. Both notices
  remain linked for complete provenance.
- The 2017 and 2020 tables describe large-city fragments using labels such as
  `Roma: Municipio XIV`, `Genova: Municipio VII - Ponente`, and
  `Napoli: Quartiere 19 - Fuorigrotta`. These official forms are now recognised
  as parts of the parent municipality.

## Reconstruction and temporal validation

For each source layer, electors and voters are taken once per distinct college
or constituency fragment. Result votes are summed across subjects, and the
fragments are then summed to municipality level. The original college labels
are preserved.

The reconstructed voter total is compared with the closest available election
before it and the closest available election after it, within the same chamber.
The default tolerance is 35 per cent, expressed as a permitted ratio of
0.65-1.35. It can be changed with `tolleranza_votanti`:

```text
GET /api/v1/history/audit/municipality?comune=ROMA&tolleranza_votanti=0.35
```

An election receives a warning when the same-date other-chamber voter ratio,
or either fallback adjacent same-chamber ratio, falls outside the tolerance.
Arithmetic contradictions, such as result votes above voters or electors,
remain invalid regardless of the temporal comparison.

## College composition registry (1994-2001)

`app/district_maps/<district_map_version>.csv` lists, for one map version,
every college and the municipalities, city zones, or described parts of a city
that compose it. It is the legal reference for how many college pieces a
municipality should have. Tables exist for
`camera-mattarellum-1993-corrected` (475 colleges, 8,650 entries) and
`senato-mattarellum-1993-corrected` (232 colleges, 8,480 entries).

| Column | Definition |
|---|---|
| `geography` | Chamber constituency or Senate region, with the Open Data label |
| `college` | College number, the same numbering as the website's `lev2` code |
| `municipality` | Canonical municipality; empty when the OCR'd name could not be resolved safely |
| `entry_type` | `whole` (a municipality), `zone` (a zone of a split city, e.g. `RM-MONTI`), or `described_part` (part of a city defined by street boundaries or prose) |
| `entry_text` | Zone name, or the boundary description |
| `source_page` | Printed page of the Gazzetta supplement |
| `ocr_text`, `match_score` | Original OCR text and the name-match confidence, for review |

The decrees were published as a scanned supplement without a text layer
(S.O. 120, GU 302, 27 December 1993). `scripts/extract_district_maps_1993.py`
rebuilds the tables with Tesseract: it reads the college-number column
separately, uses the table layout (number column, vertical gaps, page-top
number repeats) to find colleges, assigns each section to a constituency or
region by the municipalities it lists, and resolves OCR'd names against the
1994 Open Data names, leaving ambiguous matches empty. Re-run it with:

```powershell
python scripts/extract_district_maps_1993.py ocr --pdf gu1993.pdf --work work
python scripts/extract_district_maps_1993.py build --work work --database $env:LOCALAPPDATA\Eligendo\eligendo.sqlite3
```

Validation against the 1994 Chamber website pages (constituency, `lev2`,
municipality for 8,191 pages):

- every constituency has the same number of colleges as Open Data;
- 28 of 30 municipalities with several colleges have exactly the website's
  college set, including Rome (1-24), Naples (1-9), Milan (1-11) and Turin
  (1-8); the exceptions are an OCR tie for TAINO and Palermo, below;
- about 1% of municipality-college pairs still differ, mostly short names the
  OCR garbled. For the Senate, 153 of 232 colleges match Open Data membership
  exactly and 65 more differ by at most two unresolved names; no municipality
  is assigned to a wrong college there.

The printed supplement contains defects that the extractor handles explicitly:

- Chamber PIEMONTE 2: the page after college 2 restarts with "1" and prints
  "2" again; the January 1994 errata assigns these entries to college 2;
- Chamber CALABRIA: a stray "SENATO DELLA REPUBBLICA - Regione VALLE D'AOSTA"
  heading appears mid-table (printed page 310), the same misprint the Senate
  errata corrects for Molise;
- Chamber SICILIA 2: college 4 begins at the top of printed page 320 without
  its number (`FORCED_STARTS` in the extractor);
- Chamber CAMPANIA 2: the Salerno colleges (printed page 296) are set in a
  different typeface and described in prose.

## Major-city sense check

The 35 per cent check was run on the complete imported history for ten major
municipalities. There were 378 Chamber/Senate municipality-election rows: 364
passed, two were invalid, two produced voter-comparison warnings, and ten
city-election combinations lacked the required metadata. The missing-metadata
case is Senate 2006 and occurs for every tested city, so it is a source-layer
limitation rather than a city-specific reconstruction failure.

| Municipality | Checks | Pass | Warning | Invalid | Insufficient |
|---|---:|---:|---:|---:|---:|
| Roma | 38 | 34 | 1 | 2 | 1 |
| Milano | 38 | 37 | 0 | 0 | 1 |
| Napoli | 38 | 37 | 0 | 0 | 1 |
| Torino | 38 | 37 | 0 | 0 | 1 |
| Palermo | 37 | 35 | 1 | 0 | 1 |
| Genova | 38 | 37 | 0 | 0 | 1 |
| Bologna | 38 | 37 | 0 | 0 | 1 |
| Firenze | 38 | 37 | 0 | 0 | 1 |
| Bari | 38 | 37 | 0 | 0 | 1 |
| Catania | 37 | 36 | 0 | 0 | 1 |

Rome's Senate 1948 and 1953 rows remain invalid because published result votes
exceed voters. Senate 1958 is a warning because its reconstructed 1,069,618
voters are 38.7 per cent above 1953; the 1958 map contains eight Rome fragments,
whereas the earlier archive exposes only seven. Palermo Senate 1958 is just
outside the threshold at 35.8 per cent above its nearest earlier available
comparison. These records are retained for review and are never silently
corrected.
