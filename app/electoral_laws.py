from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ElectoralLaw:
    id: str
    date: str
    citation: str
    title: str
    kind: str
    applies_to: tuple[str, ...]
    election_years: str
    source_url: str
    download_url: str
    file_format: str


def _gazette(code: str, year: int, month: int, day: int) -> str:
    return (
        "https://www.gazzettaufficiale.it/atto/vediMenuHTML?"
        f"atto.codiceRedazionale={code}&"
        f"atto.dataPubblicazioneGazzetta={year:04d}-{month:02d}-{day:02d}&"
        "tipoSerie=serie_generale&tipoVigenza=originario"
    )


ELECTORAL_LAWS = (
    ElectoralLaw(
        "assembly-1946-74",
        "1946-03-10",
        "D.Lgs.Lgt. 10 March 1946, no. 74",
        "Rules for electing the Constituent Assembly",
        "electoral_law",
        ("assemblea_costituente",),
        "1946",
        _gazette("046U0074", 1946, 3, 12),
        _gazette("046U0074", 1946, 3, 12),
        "html",
    ),
    ElectoralLaw(
        "camera-1948-26",
        "1948-02-05",
        "D.P.R. 5 February 1948, no. 26",
        "Consolidated law for electing the Chamber of Deputies",
        "electoral_law",
        ("camera",),
        "1948-1953",
        _gazette("048U0026", 1948, 2, 6),
        _gazette("048U0026", 1948, 2, 6),
        "html",
    ),
    ElectoralLaw(
        "senato-1948-29",
        "1948-02-06",
        "Law 6 February 1948, no. 29",
        "Rules for electing the Senate of the Republic",
        "electoral_law",
        ("senato",),
        "1948-1992",
        _gazette("048U0029", 1948, 2, 7),
        _gazette("048U0029", 1948, 2, 7),
        "html",
    ),
    ElectoralLaw(
        "senato-boundaries-1948-30",
        "1948-02-06",
        "D.P.R. 6 February 1948, no. 30",
        "Table of Senate electoral-college boundaries",
        "boundary_decree",
        ("senato",),
        "1948-1992",
        _gazette("048U0030", 1948, 2, 7),
        _gazette("048U0030", 1948, 2, 7),
        "html",
    ),
    ElectoralLaw(
        "senato-boundaries-1948-84",
        "1948-02-28",
        "D.P.R. 28 February 1948, no. 84",
        "Corrections to the Senate electoral-college boundary table",
        "boundary_correction",
        ("senato",),
        "1948-1992",
        _gazette("048U0084", 1948, 3, 1),
        _gazette("048U0084", 1948, 3, 1),
        "html",
    ),
    ElectoralLaw(
        "camera-1957-361",
        "1957-03-30",
        "D.P.R. 30 March 1957, no. 361",
        "Consolidated law for electing the Chamber of Deputies",
        "electoral_law",
        ("camera",),
        "1958-present, as amended",
        _gazette("057U0361", 1957, 6, 3),
        _gazette("057U0361", 1957, 6, 3),
        "html",
    ),
    ElectoralLaw(
        "senato-1958-64",
        "1958-02-27",
        "Law 27 February 1958, no. 64",
        "Amendments to the 1948 Senate electoral law",
        "electoral_law",
        ("senato",),
        "1958-1992",
        _gazette("058U0064", 1958, 2, 28),
        _gazette("058U0064", 1958, 2, 28),
        "html",
    ),
    ElectoralLaw(
        "european-1979-18",
        "1979-01-24",
        "Law 24 January 1979, no. 18",
        "Election of Italy's members of the European Parliament",
        "electoral_law",
        ("europee",),
        "1979-present, as amended",
        _gazette("079U0018", 1979, 1, 30),
        _gazette("079U0018", 1979, 1, 30),
        "html",
    ),
    ElectoralLaw(
        "referendum-1970-352",
        "1970-05-25",
        "Law 25 May 1970, no. 352",
        "Rules for constitutional and abrogative referendums",
        "electoral_law",
        ("referendum",),
        "1970-present, as amended",
        _gazette("070U0352", 1970, 6, 15),
        _gazette("070U0352", 1970, 6, 15),
        "html",
    ),
    ElectoralLaw(
        "senato-1993-276",
        "1993-08-04",
        "Law 4 August 1993, no. 276",
        "New rules for electing the Senate of the Republic",
        "electoral_law",
        ("senato",),
        "1994-2001",
        _gazette("093G0358", 1993, 8, 6),
        _gazette("093G0358", 1993, 8, 6),
        "html",
    ),
    ElectoralLaw(
        "camera-1993-277",
        "1993-08-04",
        "Law 4 August 1993, no. 277",
        "New rules for electing the Chamber of Deputies",
        "electoral_law",
        ("camera",),
        "1994-2001",
        _gazette("093G0359", 1993, 8, 6),
        _gazette("093G0359", 1993, 8, 6),
        "html",
    ),
    ElectoralLaw(
        "senato-1993-533",
        "1993-12-20",
        "Legislative Decree 20 December 1993, no. 533",
        "Consolidated law for electing the Senate",
        "electoral_law",
        ("senato",),
        "1994-present, as amended",
        _gazette("093G0613", 1993, 12, 27),
        _gazette("093G0613", 1993, 12, 27),
        "html",
    ),
    ElectoralLaw(
        "senato-boundaries-1993-535",
        "1993-12-20",
        "Legislative Decree 20 December 1993, no. 535",
        "Senate single-member electoral-college boundaries",
        "boundary_decree",
        ("senato",),
        "1994-2001",
        _gazette("093G0615", 1993, 12, 27),
        "https://www.gazzettaufficiale.it/eli/gu/1993/12/27/302/so/120/sg/pdf",
        "pdf",
    ),
    ElectoralLaw(
        "camera-boundaries-1993-536",
        "1993-12-20",
        "Legislative Decree 20 December 1993, no. 536",
        "Chamber single-member electoral-college boundaries",
        "boundary_decree",
        ("camera",),
        "1994-2001",
        _gazette("093G0616", 1993, 12, 27),
        "https://www.gazzettaufficiale.it/eli/gu/1993/12/27/302/so/120/sg/pdf",
        "pdf",
    ),
    ElectoralLaw(
        "parliament-2005-270",
        "2005-12-21",
        "Law 21 December 2005, no. 270",
        "Amendments to the Chamber and Senate electoral systems",
        "electoral_law",
        ("camera", "senato"),
        "2006-2013",
        _gazette("005G0284", 2005, 12, 30),
        _gazette("005G0284", 2005, 12, 30),
        "html",
    ),
    ElectoralLaw(
        "parliament-2017-165",
        "2017-11-03",
        "Law 3 November 2017, no. 165",
        "Mixed electoral system and delegation to determine colleges",
        "electoral_law",
        ("camera", "senato"),
        "2018-present, as amended",
        _gazette("17G00175", 2017, 11, 11),
        _gazette("17G00175", 2017, 11, 11),
        "html",
    ),
    ElectoralLaw(
        "parliament-boundaries-2017-189",
        "2017-12-12",
        "Legislative Decree 12 December 2017, no. 189",
        "2018 Chamber and Senate electoral-college boundaries",
        "boundary_decree",
        ("camera", "senato"),
        "2018",
        _gazette("17G00210", 2017, 12, 19),
        "https://www.gazzettaufficiale.it/eli/gu/2017/12/19/295/so/58/sg/pdf",
        "pdf",
    ),
    ElectoralLaw(
        "parliament-2019-51",
        "2019-05-27",
        "Law 27 May 2019, no. 51",
        "Rules making electoral laws independent of Parliament's size",
        "electoral_law",
        ("camera", "senato"),
        "2022-present",
        _gazette("19G00060", 2019, 6, 11),
        _gazette("19G00060", 2019, 6, 11),
        "html",
    ),
    ElectoralLaw(
        "parliament-boundaries-2020-177",
        "2020-12-23",
        "Legislative Decree 23 December 2020, no. 177",
        "Current Chamber and Senate electoral-college boundaries",
        "boundary_decree",
        ("camera", "senato"),
        "2022-present",
        _gazette("20G00198", 2020, 12, 29),
        "https://www.gazzettaufficiale.it/eli/gu/2020/12/29/321/so/45/sg/pdf",
        "pdf",
    ),
)


LAW_BY_ID = {law.id: law for law in ELECTORAL_LAWS}


def boundary_source(category: str, year: int) -> str | None:
    if category == "senato" and year <= 1992:
        return "senato-boundaries-1948-30"
    if category in {"camera", "senato"} and 1994 <= year <= 2001:
        return f"{category}-boundaries-1993-{'536' if category == 'camera' else '535'}"
    if category in {"camera", "senato"} and year == 2018:
        return "parliament-boundaries-2017-189"
    if category in {"camera", "senato"} and year >= 2022:
        return "parliament-boundaries-2020-177"
    return None
