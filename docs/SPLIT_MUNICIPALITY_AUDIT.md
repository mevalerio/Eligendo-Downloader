# Split-municipality audit

## Scope

This audit covers municipality records in every imported Chamber and Senate
election. It links each applicable election to the official college-boundary
instrument and evaluates whether electoral-college fragments reconstruct a
plausible municipality total.

The legal corpus contains 27 principal post-war national electoral acts,
boundary instruments, territorial amendments, and official corrections. It
includes the 1948 Senate boundary table and correction, the 1956 Chamber and
1963/1991 Senate changes, the corrected 1993 Chamber and Senate college
decrees, and the 2017 and 2020 boundary decrees. The API downloads the official
Gazzetta Ufficiale sources and records a SHA-256 digest for every file.

Territorial versions are separate from electoral-law versions. The complete
period table and clickable official sources are in
[District-map versions](DISTRICT_MAP_VERSIONS.md) and are returned by
`/api/v1/legal/district-maps`.

## Municipality and college normalisation

The importer recognises:

- named fragments such as `Roma - Appio Latino`;
- centre and directional labels such as `Messina centro storico`,
  `Firenze Nord`, and `Palermo Sud`;
- Arabic- or Roman-numbered and zonal labels;
- official `Municipio` and `Quartiere` labels; and
- explicit archive markers such as `Parte di Comune TARANTO`,
  `PARTE DI COMUNE DI ROMA`, and `parte del comune di Trieste`.

The canonical municipality is stored in `COMUNE`. The electoral subdivision
is retained in `COLLEGIO`. Historical aliases for `collegio`, `coll`, and the
full uninominal and plurinominal field names are supported.

## Validation method

For each municipality, election, source file, result type and college, the
audit takes electors and voters once and sums result votes across parties or
candidates. It then sums the college fragments to municipality level. The best
complete result layer is selected for each election.

The selected row is compared with the closest earlier and later elections of
the same chamber that have voter data. The default tolerance is 35 per cent,
so each reconstructed voter ratio must lie within 0.65-1.35. The response also
retains the nearest-election electorate comparison for continuity. An election
is:

- `invalid` when votes exceed electors by more than 2%, voters exceed electors
  by more than 1%, or votes exceed voters by more than 2%;
- `warning` when votes/electors fall outside 0.20-1.02, the electorate is
  outside 0.65-1.35 of the nearest same-category election, or either adjacent
  voter ratio falls outside the configured tolerance;
- `insufficient_data` when the source omits the required electorate/voter data
  or no adjacent voter reference is available; and
- `pass` otherwise.

The comparison is a sense check. It does not replace legal-boundary research
or silently alter an anomalous official source row.

For uncertain historical names or administrative changes, the audit may also
be cross-checked against the [Elesh municipal-history database](http://www.elesh.it/storiacomuni/cercacomuni.asp),
which describes its records as derived from ISTAT and Agenzia delle Entrate
data. This is a secondary identification aid; Gazzetta Ufficiale and Ministry
election files remain the authoritative electoral sources.

## Full-history result

The validated run covered 28 historically split municipalities and 1,020
Chamber/Senate municipality-election rows. It reconstructed 277 elections from
more than one college fragment.

| Status | Rows |
|---|---:|
| Pass | 982 |
| Warning | 8 |
| Invalid | 3 |
| Insufficient data | 27 |

The warnings were Reggio Calabria (Chamber 2001), Cagliari (Senate 1948 and
1958), Palermo (Senate 1958), Padova (Chamber 1992, 1994 and 1996), and Rome
(Senate 1958). These rows are arithmetically coherent but their electorate or
voter totals differ substantially from an adjacent comparison election.

The invalid rows were:

| Municipality | Election | Parts | Electors | Voters | Result votes | Finding |
|---|---|---:|---:|---:|---:|---|
| Cagliari | Senate 1953 | 1 | 18,929 | 17,143 | 62,099 | Published result votes exceed both electorate and voters |
| Roma | Senate 1948 | 7 | 794,455 | 690,554 | 775,402 | Votes exceed voters; source reports seven Rome labels |
| Roma | Senate 1953 | 7 | 832,259 | 771,077 | 889,712 | Votes exceed voters and electors; source reports seven Rome labels |

The 1948 Senate boundary decree defines `ROMA I` through `ROMA VIII`. The 1948
source rows contain I, II, III, V, VI, VII and VIII, with two incompatible
blocks under `ROMA V`; `ROMA IV` is absent. This supports retaining the two
elections as invalid source anomalies rather than inventing a correction.

The 27 insufficient-data rows arise where the selected source layer does not
publish municipality-level electors or voters, notably the 2006 Senate files.

## Rome result

Rome appears in 38 Chamber/Senate election checks: 34 pass, the 1948 and 1953
Senate rows are invalid for the reasons above, the 1958 Senate row is a voter
comparison warning, and the 2006 Senate row has insufficient electorate and
voter metadata. The 2018 and 2022 rows reconstruct 11 and 7 Chamber parts, and
5 and 3 Senate parts, respectively; all four pass the arithmetic and adjacent-
election voter checks.

## Reproduction

After importing the national history, request:

```text
GET /api/v1/history/audit/municipality?comune=ROMA
```

Use `category=camera` or `category=senato` for a single chamber. Set
`tolleranza_votanti` to change the default 0.35 threshold. The response includes
the previous and following voter references, every component total, ratio and
status, `mappa_collegi_versione`, and all `fonti_confini_urls` needed to review
the result against the downloaded legal corpus.
