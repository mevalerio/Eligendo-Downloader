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

## Direct Ministry-page verification

The strongest operational check is the municipality result page published by
the Ministry. The API therefore provides two complementary endpoints:

- `POST /api/v1/history/audit/official-municipality-page` compares one page;
- `POST /api/v1/history/audit/official-municipality-pages` first aggregates a
  set of pages when the municipality is divided among several colleges.

Both endpoints compare electors, voters, valid votes, and party-level votes.
The multi-page endpoint requires the same chamber, election date,
municipality, province, and region on every page. Its default relative
tolerance is zero. Each page is retained as a source URL in the response, and
`store=true` saves the parsed snapshot in the local database. A page with
neither province nor region is rejected because its municipality name alone
does not establish a safe match.

Names alone do not identify a municipality. The 1958 Chamber archive has two
municipalities called BRIONE. The [Brescia page](https://elezionistorico.interno.gov.it/index.php?tpel=C&dtel=25/05/1958&tpa=I&tpe=C&lev0=0&levsut0=0&lev1=6&levsut1=1&lev2=15&levsut2=2&levsut3=3&ne1=6&ne2=15&es0=S&es1=S&es2=S&es3=N&ms=S&ne3=150270&lev3=270)
reports 334 electors, 304 voters, and 296 valid list votes. The
[Trento page](https://elezionistorico.interno.gov.it/index.php?tpel=C&dtel=25/05/1958&tpa=I&tpe=C&lev0=0&levsut0=0&lev1=8&levsut1=1&lev2=83&levsut2=2&levsut3=3&ne1=8&ne2=83&es0=S&es1=S&es2=S&es3=N&ms=S&ne3=830270&lev3=270)
reports 164, 162, and 162 respectively. The live API comparison matched all
10 Brescia party totals and all 11 Trento party totals exactly. Official checks
are keyed by province and municipality (or by
region and municipality if the page has no province), so saving one cannot
overwrite the other. Use `provincia=BRESCIA` or `provincia=TRENTO` in the
municipality audit. These 1958 Chamber pages do not publish a region, so that
field remains unknown rather than being inferred from a present-day map.

For Rome in the 1958 Chamber election, the single municipality page matches
the Open Data reconstruction exactly: 1,243,752 electors, 1,183,771 voters,
1,160,923 valid list votes, and all 13 party totals.

For Rome in the 1958 Senate election, the archive exposes eight municipality
pages under `ROMA I` to `ROMA VIII`. Their aggregate also matches exactly:
1,131,128 electors, 1,069,618 voters, 1,032,267 valid votes, and all 10 party
totals. The original temporal audit labelled this row `warning` against the
uncorrected 1953 summary. After applying the complete 1953 official page set,
the 1958 row passes the adjacent-election check as well.

Validation evidence is therefore interpreted in this order:

1. an exact match with the complete set of Ministry municipality pages;
2. consistency with the applicable legal district map; and
3. proportionality to the previous and following election as a diagnostic
   sense check.

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
| Warning | 7 |
| Invalid | 1 |
| Insufficient data | 27 |

The warnings were Reggio Calabria (Chamber 2001), Cagliari (Senate 1948 and
1958), Palermo (Senate 1958), and Padova (Chamber 1992, 1994 and 1996). These
rows are arithmetically coherent but their electorate or voter totals differ
substantially from an adjacent comparison election.

The invalid rows were:

| Municipality | Election | Parts | Electors | Voters | Result votes | Finding |
|---|---|---:|---:|---:|---:|---|
| Cagliari | Senate 1953 | 1 | 18,929 | 17,143 | 62,099 | Published result votes exceed both electorate and voters |

The raw 1948 and 1953 Senate Open Data rows contain seven Rome summary labels
and omit the `ROMA IV` electorate/voter component. The party and valid-vote
totals are complete. Aggregating the eight Ministry municipality pages restores
the missing metadata: 915,306 electors and 797,083 voters in 1948; 986,155
electors and 916,069 voters in 1953. The audit preserves the raw values in the
`*_open_data` fields and identifies the applied source as
`official_municipality_pages`.

The 27 insufficient-data rows arise where the selected source layer does not
publish municipality-level electors or voters, notably the 2006 Senate files.

## Rome result

Rome appears in 38 Chamber/Senate election checks: 37 pass after the official
page corrections and the 2006 Senate row has insufficient electorate and voter
metadata. The 2018 and 2022 rows reconstruct 11 and 7 Chamber parts, and 5 and
3 Senate parts, respectively; all four pass the arithmetic and adjacent-
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
