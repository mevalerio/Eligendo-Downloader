# Split-municipality audit

## Scope

This audit covers municipality records in every imported Chamber and Senate
election. It links each applicable election to the official college-boundary
instrument and evaluates whether electoral-college fragments reconstruct a
plausible municipality total.

The legal corpus contains 19 principal post-war national electoral acts and
boundary instruments. It includes the 1948 Senate boundary table, the 1993
Chamber and Senate college decrees, and the 2017 and 2020 boundary decrees. The
API downloads the official Gazzetta Ufficiale sources and records a SHA-256
digest for every file.

## Municipality and college normalisation

The importer recognises:

- named fragments such as `Roma - Appio Latino`;
- centre and directional labels such as `Messina centro storico`,
  `Firenze Nord`, and `Palermo Sud`;
- numbered or zonal labels; and
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

The selected row is compared with the nearest same-category election that has
electorate data. An election is:

- `invalid` when votes exceed electors by more than 2%, voters exceed electors
  by more than 1%, or votes exceed voters by more than 2%;
- `warning` when votes/electors fall outside 0.20–1.02 or the electorate is
  outside 0.65–1.35 of the nearest same-category election;
- `insufficient_data` when the source omits an electorate or reference; and
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
| Pass | 985 |
| Warning | 5 |
| Invalid | 3 |
| Insufficient data | 27 |

The warnings were Reggio Calabria (Chamber 2001), Cagliari (Senate 1948), and
Padova (Chamber 1992, 1994 and 1996). These rows are arithmetically coherent but
their electorate differs substantially from the nearest comparison election.

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

Rome appears in 38 Chamber/Senate election checks: 35 pass, the 1948 and 1953
Senate rows are invalid for the reasons above, and the 2006 Senate row has
insufficient electorate metadata. The 2018 and 2022 rows reconstruct 11 and 7
Chamber parts, and 5 and 3 Senate parts, respectively; all four pass the vote
and nearest-electorate checks.

## Reproduction

After importing the national history, request:

```text
GET /api/v1/history/audit/municipality?comune=ROMA
```

Use `category=camera` or `category=senato` for a single chamber. The response
includes every component total, ratio, status, and `fonte_confini_id` needed to
review the result against the downloaded legal corpus.
