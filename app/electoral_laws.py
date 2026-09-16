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


@dataclass(frozen=True)
class DistrictMapVersion:
    id: str
    category: str
    start_year: int
    end_year: int
    geography_level: str
    source_ids: tuple[str, ...]
    notes: str


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
        "camera-1953-148",
        "1953-03-31",
        "Law 31 March 1953, no. 148",
        "Amendments to the Chamber electoral law without general redistricting",
        "electoral_law",
        ("camera",),
        "1953",
        _gazette("053U0148", 1953, 3, 31),
        _gazette("053U0148", 1953, 3, 31),
        "html",
    ),
    ElectoralLaw(
        "camera-boundaries-1956-493",
        "1956-05-16",
        "Law 16 May 1956, no. 493",
        "Chamber territorial amendment adding the Trieste constituency",
        "boundary_correction",
        ("camera",),
        "1958-1992",
        _gazette("056U0493", 1956, 6, 12),
        _gazette("056U0493", 1956, 6, 12),
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
        "senato-boundaries-1963-55",
        "1963-02-14",
        "Law 14 February 1963, no. 55",
        "Revision of Senate colleges in Friuli-Venezia Giulia",
        "boundary_correction",
        ("senato",),
        "1963-1987",
        _gazette("063U0055", 1963, 2, 15),
        _gazette("063U0055", 1963, 2, 15),
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
        "senato-boundaries-1991-422",
        "1991-12-30",
        "Law 30 December 1991, no. 422",
        "Revision of the six Senate colleges in Trentino-Alto Adige",
        "boundary_correction",
        ("senato",),
        "1992-2013 special regional regime",
        _gazette("092G0002", 1992, 1, 4),
        _gazette("092G0002", 1992, 1, 4),
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
        "senato-boundaries-1993-535-correction",
        "1993-12-31",
        "Errata corrige to Legislative Decree 20 December 1993, no. 535",
        "Corrections to the Senate single-member college table",
        "boundary_correction",
        ("senato",),
        "1994-2001",
        _gazette("093A7407", 1993, 12, 31),
        _gazette("093A7407", 1993, 12, 31),
        "html",
    ),
    ElectoralLaw(
        "camera-boundaries-1993-536-correction",
        "1994-01-13",
        "Errata corrige to Legislative Decree 20 December 1993, no. 536",
        "Corrections to the Chamber single-member college table",
        "boundary_correction",
        ("camera",),
        "1994-2001",
        _gazette("094A0228", 1994, 1, 13),
        _gazette("094A0228", 1994, 1, 13),
        "html",
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
        "parliament-boundaries-2017-189-correction-1",
        "2017-12-20",
        "Correction notice 20 December 2017 to Legislative Decree no. 189",
        "First official correction to the 2018 college instrument",
        "boundary_correction",
        ("camera", "senato"),
        "2018",
        _gazette("17A08633", 2017, 12, 20),
        _gazette("17A08633", 2017, 12, 20),
        "html",
    ),
    ElectoralLaw(
        "parliament-boundaries-2017-189-correction-2",
        "2018-01-12",
        "Correction notice 12 January 2018 to Legislative Decree no. 189",
        "Territorial correction adding Villetta Barrea to the published table",
        "boundary_correction",
        ("camera", "senato"),
        "2018",
        _gazette("18A00307", 2018, 1, 12),
        _gazette("18A00307", 2018, 1, 12),
        "html",
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


DISTRICT_MAP_VERSIONS = (
    DistrictMapVersion(
        "camera-1948-table-a",
        "camera",
        1948,
        1953,
        "circoscrizione",
        ("camera-1948-26", "camera-1953-148"),
        "The 1953 law changed seat allocation, not the general territorial map.",
    ),
    DistrictMapVersion(
        "camera-1958-table-a-trieste",
        "camera",
        1958,
        1992,
        "circoscrizione",
        ("camera-boundaries-1956-493", "camera-1957-361"),
        "The consolidated Table A includes the Trieste territorial amendment.",
    ),
    DistrictMapVersion(
        "senato-1948-corrected",
        "senato",
        1948,
        1958,
        "collegio_uninominale",
        ("senato-boundaries-1948-30", "senato-boundaries-1948-84"),
        "The original municipality-to-college table must be read with DPR 84/1948.",
    ),
    DistrictMapVersion(
        "senato-1963-friuli",
        "senato",
        1963,
        1987,
        "collegio_uninominale",
        (
            "senato-boundaries-1948-30",
            "senato-boundaries-1948-84",
            "senato-boundaries-1963-55",
        ),
        "The 1963 law replaces the Friuli-Venezia Giulia portion of the map.",
    ),
    DistrictMapVersion(
        "senato-1992-trentino",
        "senato",
        1992,
        1992,
        "collegio_uninominale",
        (
            "senato-boundaries-1948-30",
            "senato-boundaries-1948-84",
            "senato-boundaries-1963-55",
            "senato-boundaries-1991-422",
        ),
        "The 1991 law replaces the six Trentino-Alto Adige colleges.",
    ),
    DistrictMapVersion(
        "camera-mattarellum-1993-corrected",
        "camera",
        1994,
        2001,
        "collegio_uninominale",
        (
            "camera-boundaries-1993-536",
            "camera-boundaries-1993-536-correction",
        ),
        "The 1993 decree is applied together with its January 1994 errata corrige.",
    ),
    DistrictMapVersion(
        "senato-mattarellum-1993-corrected",
        "senato",
        1994,
        2001,
        "collegio_uninominale",
        (
            "senato-boundaries-1993-535",
            "senato-boundaries-1993-535-correction",
            "senato-boundaries-1991-422",
        ),
        "The corrected decree applies nationally; the 1991 Trentino map remains relevant.",
    ),
    DistrictMapVersion(
        "camera-porcellum-table-a",
        "camera",
        2006,
        2013,
        "circoscrizione",
        ("camera-1957-361", "parliament-2005-270"),
        "The system uses the Chamber constituencies in Table A, without Mattarellum colleges.",
    ),
    DistrictMapVersion(
        "senato-porcellum-regions",
        "senato",
        2006,
        2013,
        "regione",
        ("parliament-2005-270", "senato-boundaries-1991-422"),
        "Regions are the general unit; the six Trentino-Alto Adige colleges persist.",
    ),
    DistrictMapVersion(
        "parliament-rosatellum-2017-corrected",
        "camera",
        2018,
        2018,
        "collegio_uninominale_e_plurinominale",
        (
            "parliament-boundaries-2017-189",
            "parliament-boundaries-2017-189-correction-1",
            "parliament-boundaries-2017-189-correction-2",
        ),
        "Tables A.1/A.2 are applied with both official correction notices.",
    ),
    DistrictMapVersion(
        "parliament-rosatellum-2017-corrected",
        "senato",
        2018,
        2018,
        "collegio_uninominale_e_plurinominale",
        (
            "parliament-boundaries-2017-189",
            "parliament-boundaries-2017-189-correction-1",
            "parliament-boundaries-2017-189-correction-2",
        ),
        "Tables B.1/B.2 are applied with both official correction notices.",
    ),
    DistrictMapVersion(
        "parliament-rosatellum-2020",
        "camera",
        2022,
        2100,
        "collegio_uninominale_e_plurinominale",
        ("parliament-boundaries-2020-177",),
        "The 2020 decree supplies the post-reduction Chamber map.",
    ),
    DistrictMapVersion(
        "parliament-rosatellum-2020",
        "senato",
        2022,
        2100,
        "collegio_uninominale_e_plurinominale",
        ("parliament-boundaries-2020-177",),
        "The 2020 decree supplies the post-reduction Senate map.",
    ),
)


def district_map_for(category: str, year: int) -> DistrictMapVersion | None:
    return next(
        (
            version
            for version in DISTRICT_MAP_VERSIONS
            if version.category == category
            and version.start_year <= year <= version.end_year
        ),
        None,
    )


def boundary_source(category: str, year: int) -> str | None:
    version = district_map_for(category, year)
    return version.source_ids[0] if version else None
