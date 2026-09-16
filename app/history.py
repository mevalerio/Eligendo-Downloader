from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Any, Iterable

from .archive import ArchiveRow
from .utils import canonical_municipality, clean_text, slug


ELECTION_CATEGORIES = frozenset(
    {
        "assemblea_costituente",
        "camera",
        "senato",
        "europee",
        "referendum",
        "regionali",
        "provinciali",
        "comunali",
    }
)

PARTY_FIELDS = (
    "lista",
    "descrlista",
    "descr_lista",
    "denominazione_lista",
    "descrizione_lista",
    "partito",
    "gruppo",
    "contrassegno",
    "desclista",
)
PARTY_VOTE_FIELDS = ("voti_lista", "votilista", "totvoti", "numvoti", "voti")
CANDIDATE_VOTE_FIELDS = (
    "voticandidato",
    "voticand",
    "voti_candidato",
    "voti_candiddato",
    "totvoti",
)
SEAT_FIELDS = ("seggi_lista", "seggilista", "seggi")

ELECTOR_FIELDS = (
    "elettoritot",
    "elettoritotali",
    "elettori_totali",
    "elettori",
    "numelettori",
)
MALE_ELECTOR_FIELDS = (
    "elettorim",
    "elettorimaschi",
    "elettori_maschi",
    "elettori_uomini",
    "elettori_m",
    "numelettorimaschi",
)
VOTER_FIELDS = (
    "votantitot",
    "votantitotali",
    "votanti_totali",
    "numvotantitotali",
    "votanti",
)
MALE_VOTER_FIELDS = (
    "votantim",
    "votantimaschi",
    "votanti_maschi",
    "votanti_uomini",
    "votanti_m",
    "numvotantimaschi",
)
VALID_VOTE_FIELDS = ("votivalidi", "voti_validi")
VALID_LIST_VOTE_FIELDS = ("votivalidiliste", "voti_validi_liste")
VALID_CANDIDATE_VOTE_FIELDS = (
    "votivalidicandidsindaco",
    "voti_validi_candidato",
)
BLANK_BALLOT_FIELDS = ("skbianche", "schede_bianche", "numschedebianche")
INVALID_BALLOT_FIELDS = (
    "sknonvalide",
    "sknulle",
    "schede_nulle",
    "schede_non_valide",
)
CONTESTED_BALLOT_FIELDS = (
    "skcontestate",
    "schede_contestate",
    "numschedecontestat",
)

YES_VOTE_FIELDS = (
    "voti_si",
    "votisi",
    "numvotisi",
    "votivalidisi",
    "votivalidi_si",
)
NO_VOTE_FIELDS = (
    "voti_no",
    "votino",
    "numvotino",
    "votivalidino",
)

ITALIAN_REGIONS = (
    "TRENTINO-ALTO ADIGE",
    "FRIULI-VENEZIA GIULIA",
    "EMILIA-ROMAGNA",
    "VALLE D'AOSTA",
    "PIEMONTE",
    "LOMBARDIA",
    "VENETO",
    "LIGURIA",
    "TOSCANA",
    "UMBRIA",
    "MARCHE",
    "LAZIO",
    "ABRUZZO",
    "MOLISE",
    "CAMPANIA",
    "PUGLIA",
    "BASILICATA",
    "CALABRIA",
    "SICILIA",
    "SARDEGNA",
)


@dataclass(frozen=True)
class HistoricalResult:
    election_date: date
    category: str
    round: int | None
    region: str | None
    constituency: str | None
    province: str | None
    municipality: str | None
    municipality_key: str | None
    country: str | None
    college: str | None
    question_number: str | None
    question: str | None
    result_type: str
    subject: str
    subject_key: str
    party: str | None
    candidate: str | None
    option: str | None
    votes: int
    percentage: float | None
    seats: int | None
    electors: int | None
    male_electors: int | None
    voters: int | None
    male_voters: int | None
    turnout_percentage: float | None
    valid_votes: int | None
    valid_list_votes: int | None
    valid_candidate_votes: int | None
    blank_ballots: int | None
    invalid_ballots: int | None
    contested_ballots: int | None
    source_file: str
    source_row: int


def _first(payload: dict[str, Any], names: Iterable[str]) -> str | None:
    for name in names:
        value = payload.get(name)
        if value not in (None, ""):
            return clean_text(str(value))
    return None


def _as_int(value: Any) -> int | None:
    if value in (None, ""):
        return None
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value) if value.is_integer() else None
    text = clean_text(str(value)).replace(" ", "")
    if "," in text:
        try:
            number = Decimal(text.replace(".", "").replace(",", "."))
        except InvalidOperation:
            return None
        return int(number) if number == number.to_integral_value() else None
    text = text.replace(".", "")
    return int(text) if text.lstrip("+-").isdigit() else None


def _first_int(payload: dict[str, Any], names: Iterable[str]) -> int | None:
    for name in names:
        if name in payload:
            value = _as_int(payload[name])
            if value is not None:
                return value
    return None


def _candidate(payload: dict[str, Any]) -> str | None:
    surname = _first(payload, ("cognome", "cognome_candidato"))
    name = _first(payload, ("nome", "nome_candidato"))
    return clean_text(" ".join(part for part in (surname, name) if part)) or None


def _region(row: ArchiveRow) -> str | None:
    direct = row.region or _first(row.payload, ("regione", "reg"))
    if direct:
        return direct
    circumscription = _first(row.payload, ("circ_reg",))
    if circumscription:
        folded = circumscription.casefold()
        for region in ITALIAN_REGIONS:
            if folded.startswith(region.casefold()):
                return region
    return None


def _context(row: ArchiveRow, *, category: str) -> dict[str, Any]:
    municipality = canonical_municipality(
        row.municipality
        or _first(
            row.payload,
            ("comune", "com", "desccomune", "denominazione"),
        )
    )
    question_number = _first(
        row.payload,
        ("num_referendum", "numero_referendum", "numreferendum", "numquesito"),
    )
    if category == "referendum" and not question_number:
        question_number = "1"
    return {
        "round": _first_int(row.payload, ("turno",)),
        "region": _region(row)
        or _first(row.payload, ("descregione",)),
        "constituency": row.circoscrizione
        or _first(
            row.payload,
            ("circoscrizione", "circoscr", "circ_reg", "desccirceuropea", "circ"),
        ),
        "province": row.province
        or _first(row.payload, ("provincia", "prov", "descprovincia")),
        "municipality": municipality,
        "municipality_key": row.municipality_key
        or (slug(municipality) if municipality else None),
        "country": _first(row.payload, ("nazione", "paese", "naz")),
        "college": _first(
            row.payload,
            ("collegio", "colluninom", "collpluri", "collplurinom"),
        ),
        "question_number": question_number,
        "question": _first(
            row.payload,
            ("quesito", "domanda", "quesitoreferendum"),
        ),
    }


def _summary(payload: dict[str, Any]) -> dict[str, int | float | None]:
    electors = _first_int(payload, ELECTOR_FIELDS)
    voters = _first_int(payload, VOTER_FIELDS)
    turnout = (
        round(100.0 * voters / electors, 6)
        if electors not in (None, 0) and voters is not None
        else None
    )
    return {
        "electors": electors,
        "male_electors": _first_int(payload, MALE_ELECTOR_FIELDS),
        "voters": voters,
        "male_voters": _first_int(payload, MALE_VOTER_FIELDS),
        "turnout_percentage": turnout,
        "valid_votes": _first_int(payload, VALID_VOTE_FIELDS),
        "valid_list_votes": _first_int(payload, VALID_LIST_VOTE_FIELDS),
        "valid_candidate_votes": _first_int(payload, VALID_CANDIDATE_VOTE_FIELDS),
        "blank_ballots": _first_int(payload, BLANK_BALLOT_FIELDS),
        "invalid_ballots": _first_int(payload, INVALID_BALLOT_FIELDS),
        "contested_ballots": _first_int(payload, CONTESTED_BALLOT_FIELDS),
    }


def _usable_aggregate_row(row: ArchiveRow) -> bool:
    file_key = slug(row.file_name)
    excluded_markers = (
        "livsez",
        "liv_sez",
        "preferenze",
        "prefeuropee",
        "votanti_varie_ore",
        "votantivarieore",
        "candidatilista",
        "candlista",
        "candidcollegio",
    )
    if any(marker in file_key for marker in excluded_markers):
        return False
    if any(row.payload.get(field) not in (None, "") for field in ("sezione", "sez")):
        return False
    return True


def _irrelevant_result_row(row: ArchiveRow) -> bool:
    file_key = slug(row.file_name)
    return any(
        marker in file_key
        for marker in (
            "preferenze",
            "prefeuropee",
            "votanti_varie_ore",
            "votantivarieore",
            "candidatilista",
            "candlista",
            "candidcollegio",
        )
    )


def _summary_key(context: dict[str, Any]) -> tuple[Any, ...]:
    return (
        context["region"],
        context["constituency"],
        context["province"],
        context["municipality_key"],
        context["country"],
        context["college"],
        context["round"],
        context["question_number"],
    )


def _merge_summary(
    current: dict[str, int | float | None],
    incoming: dict[str, int | float | None],
) -> None:
    for name, value in incoming.items():
        if current.get(name) is None and value is not None:
            current[name] = value


def _result(
    *,
    row: ArchiveRow,
    election_date: date,
    category: str,
    context: dict[str, Any],
    summary: dict[str, int | float | None],
    result_type: str,
    subject: str,
    votes: int,
    party: str | None = None,
    candidate: str | None = None,
    option: str | None = None,
) -> HistoricalResult:
    valid_denominator = summary["valid_list_votes"] or summary["valid_votes"]
    percentage = (
        round(100.0 * votes / valid_denominator, 6)
        if valid_denominator not in (None, 0)
        else None
    )
    return HistoricalResult(
        election_date=election_date,
        category=category,
        result_type=result_type,
        subject=subject,
        subject_key=slug(subject),
        party=party,
        candidate=candidate,
        option=option,
        votes=votes,
        percentage=percentage,
        seats=_first_int(row.payload, SEAT_FIELDS),
        source_file=row.file_name,
        source_row=row.row_number,
        **context,
        **summary,
    )


def _result_specs(
    row: ArchiveRow,
    *,
    category: str,
    summary: dict[str, int | float | None],
) -> list[dict[str, Any]]:
    if category == "referendum":
        yes_votes = _first_int(row.payload, YES_VOTE_FIELDS)
        no_votes = _first_int(row.payload, NO_VOTE_FIELDS)
        if no_votes is None and yes_votes is not None:
            valid_votes = summary["valid_votes"]
            if valid_votes is not None and valid_votes >= yes_votes:
                no_votes = int(valid_votes) - yes_votes
        if summary["valid_votes"] is None and yes_votes is not None and no_votes is not None:
            summary["valid_votes"] = yes_votes + no_votes
        return [
            {
                "result_type": "option",
                "subject": option,
                "option": option,
                "votes": votes,
            }
            for option, votes in (("SI", yes_votes), ("NO", no_votes))
            if votes is not None
        ]

    party = _first(row.payload, PARTY_FIELDS)
    party_votes = _first_int(row.payload, PARTY_VOTE_FIELDS)
    candidate = _candidate(row.payload)
    if party and party_votes is not None:
        return [
            {
                "result_type": "list",
                "subject": party,
                "party": party,
                "candidate": candidate,
                "votes": party_votes,
            }
        ]

    candidate_votes = _first_int(row.payload, CANDIDATE_VOTE_FIELDS)
    if candidate and candidate_votes is not None:
        return [
            {
                "result_type": "candidate",
                "subject": candidate,
                "candidate": candidate,
                "votes": candidate_votes,
            }
        ]
    return []


def _normalise_section_results(
    rows: list[ArchiveRow],
    *,
    category: str,
    election_date: date,
) -> list[HistoricalResult]:
    section_summaries: dict[
        tuple[Any, ...], dict[str, int | float | None]
    ] = {}
    grouped: dict[tuple[Any, ...], dict[str, Any]] = {}

    for row in rows:
        if _irrelevant_result_row(row):
            continue
        section = _first(row.payload, ("sezione", "sez"))
        if not section:
            continue
        context = _context(row, category=category)
        base_key = _summary_key(context)
        section_key = (*base_key, section)
        current = section_summaries.setdefault(section_key, _summary(row.payload))
        _merge_summary(current, _summary(row.payload))

        row_summary = _summary(row.payload)
        for spec in _result_specs(row, category=category, summary=row_summary):
            group_key = (
                *base_key,
                spec["result_type"],
                slug(spec["subject"]),
                spec.get("candidate"),
                spec.get("option"),
            )
            if group_key not in grouped:
                grouped[group_key] = {
                    "row": row,
                    "context": context,
                    "spec": dict(spec),
                }
            else:
                grouped[group_key]["spec"]["votes"] += spec["votes"]

    summaries: dict[tuple[Any, ...], dict[str, int | float | None]] = {}
    for section_key, section_summary in section_summaries.items():
        base_key = section_key[:-1]
        target = summaries.setdefault(
            base_key,
            {name: None for name in section_summary},
        )
        for name, value in section_summary.items():
            if name == "turnout_percentage" or value is None:
                continue
            target[name] = (target[name] or 0) + value
    for summary in summaries.values():
        electors = summary["electors"]
        voters = summary["voters"]
        summary["turnout_percentage"] = (
            round(100.0 * int(voters) / int(electors), 6)
            if electors not in (None, 0) and voters is not None
            else None
        )

    list_totals: dict[tuple[Any, ...], int] = {}
    for group_key, group in grouped.items():
        if group["spec"]["result_type"] == "list":
            base_key = group_key[:8]
            list_totals[base_key] = (
                list_totals.get(base_key, 0) + group["spec"]["votes"]
            )

    results: list[HistoricalResult] = []
    for group_key, group in grouped.items():
        context = group["context"]
        base_key = _summary_key(context)
        summary = dict(summaries.get(base_key, _summary(group["row"].payload)))
        if summary["valid_list_votes"] is None and base_key in list_totals:
            summary["valid_list_votes"] = list_totals[base_key]
        source = group["row"]
        aggregate_row = ArchiveRow(
            file_name=f"{source.file_name}#municipality-aggregate",
            row_number=0,
            region=source.region,
            circoscrizione=source.circoscrizione,
            province=source.province,
            municipality=source.municipality,
            municipality_key=source.municipality_key,
            payload=source.payload,
        )
        results.append(
            _result(
                row=aggregate_row,
                election_date=election_date,
                category=category,
                context=context,
                summary=summary,
                **group["spec"],
            )
        )
    return results


def normalise_history_results(
    rows: Iterable[ArchiveRow],
    *,
    category: str,
    election_date: date,
) -> list[HistoricalResult]:
    all_rows = list(rows)
    usable_rows = [row for row in all_rows if _usable_aggregate_row(row)]
    summaries: dict[tuple[Any, ...], dict[str, int | float | None]] = {}
    contexts: dict[int, dict[str, Any]] = {}

    for row in usable_rows:
        context = _context(row, category=category)
        contexts[id(row)] = context
        key = _summary_key(context)
        current = summaries.setdefault(key, _summary(row.payload))
        _merge_summary(current, _summary(row.payload))

    results: list[HistoricalResult] = []
    for row in usable_rows:
        context = contexts[id(row)]
        summary = dict(summaries[_summary_key(context)])
        _merge_summary(summary, _summary(row.payload))

        for spec in _result_specs(row, category=category, summary=summary):
            results.append(
                _result(
                    row=row,
                    election_date=election_date,
                    category=category,
                    context=context,
                    summary=summary,
                    **spec,
                )
            )
    if results:
        return results
    return _normalise_section_results(
        all_rows,
        category=category,
        election_date=election_date,
    )
