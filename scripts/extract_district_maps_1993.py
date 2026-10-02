"""Extract the 1993 college tables (Legislative Decrees 535 and 536/1993).

The Gazzetta Ufficiale supplement (S.O. 120, GU 302 of 27 December 1993) is a
scanned PDF without a text layer. This script rebuilds the college composition
tables in two steps:

``ocr``
    Render every table page at 300 dpi and run Tesseract twice: the full page
    with word positions, and the college-number column alone, digits only.
    Needs PyMuPDF and Tesseract with Italian data; neither is a project
    dependency.

``build``
    Parse the OCR output into constituencies (Chamber) or regions (Senate),
    colleges and entries, resolve OCR'd names against the municipality names
    of the 1994 Open Data archive (read from the working database, read-only),
    and write ``app/district_maps/<map version>.csv``.

Parsing relies on the table layout rather than on the OCR'd college numbers
alone: numbers sit in their own column, colleges are separated by extra
vertical space, a college continuing on a new page repeats its number at the
top, and a section heading counts only if its page restarts at college 1. The
printed supplement contains defects the layout cannot reveal; they are listed
in ``FORCED_STARTS`` with their evidence.

Usage::

    python scripts/extract_district_maps_1993.py ocr --pdf gu1993.pdf --work work/
    python scripts/extract_district_maps_1993.py build --work work/ \
        --database %LOCALAPPDATA%/Eligendo/eligendo.sqlite3
"""
from __future__ import annotations

import argparse
import csv
import re
import sqlite3
import statistics
import subprocess
import sys
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from difflib import get_close_matches
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.district_registry import REGISTRY_DIR, REGISTRY_FIELDS  # noqa: E402
from app.utils import canonical_municipality  # noqa: E402

# PDF page n carries printed page n - 1. Senate table: printed 5-156; Chamber: 161-330.
CHAMBERS = {
    "senato": {
        "pages": range(6, 158),
        "map_version": "senato-mattarellum-1993-corrected",
        "geography": "region",
    },
    "camera": {
        "pages": range(162, 332),
        "map_version": "camera-mattarellum-1993-corrected",
        "geography": "constituency",
    },
}
PRINTED_PAGE_OFFSET = 1
NUMBER_COLUMN = (380, 780)  # x range of the college-number column at 300 dpi
FOOTER_Y = 3330
# Printing defects the layout cannot reveal: (chamber, PDF page, first entry) starts a college.
FORCED_STARTS = {
    # Chamber SICILIA 2, printed page 320: college 4 begins at the top of the page
    # without its number. Website and Open Data both start college 4 at CASTROREALE.
    ("camera", 321, "CASTROREALE"),
}
# Province codes that prefix the zones of a split city, e.g. "( RM-MONTI )".
CITY_CODES = {
    "RM": "ROMA", "GE": "GENOVA", "NA": "NAPOLI", "PG": "PERUGIA", "PA": "PALERMO",
    "PD": "PADOVA", "CT": "CATANIA", "BS": "BRESCIA", "ME": "MESSINA", "BO": "BOLOGNA",
    "TA": "TARANTO", "BA": "BARI", "RC": "REGGIO CALABRIA", "PO": "PRATO", "RA": "RAVENNA",
    "CA": "CAGLIARI", "FG": "FOGGIA", "FE": "FERRARA", "VE": "VENEZIA", "FI": "FIRENZE",
    "TS": "TRIESTE", "LI": "LIVORNO", "MO": "MODENA", "PR": "PARMA", "RN": "RIMINI",
    "SA": "SALERNO", "TO": "TORINO", "MI": "MILANO", "VR": "VERONA",
}


# --------------------------------------------------------------------------- OCR


def run_ocr(pdf: Path, work: Path, tesseract: str, workers: int) -> None:
    import pymupdf  # optional tool dependency

    images, tsv = work / "img", work / "tsv"
    images.mkdir(parents=True, exist_ok=True)
    tsv.mkdir(parents=True, exist_ok=True)
    pages = [page for spec in CHAMBERS.values() for page in spec["pages"]]
    document = pymupdf.open(pdf)
    for page in pages:
        full = images / f"p{page:03d}.png"
        if not full.exists():
            document[page - 1].get_pixmap(dpi=300, colorspace=pymupdf.csGRAY).save(full)
        column = images / f"n{page:03d}.png"
        if not column.exists():
            pixmap = pymupdf.Pixmap(str(full))
            clip = pymupdf.IRect(NUMBER_COLUMN[0], 0, NUMBER_COLUMN[1], pixmap.height)
            pymupdf.Pixmap(pixmap, pixmap.width, pixmap.height, clip).save(column)

    def ocr(page: int) -> None:
        jobs = (
            (images / f"p{page:03d}.png", tsv / f"p{page:03d}", ["-l", "ita", "--psm", "6"]),
            (images / f"n{page:03d}.png", tsv / f"n{page:03d}",
             ["--psm", "6", "-c", "tessedit_char_whitelist=0123456789"]),
        )
        for image, output, options in jobs:
            if not output.with_suffix(".tsv").exists():
                subprocess.run([tesseract, str(image), str(output), *options, "tsv"],
                               capture_output=True, check=True)

    with ThreadPoolExecutor(max_workers=workers) as pool:
        list(pool.map(ocr, pages))


# ------------------------------------------------------------------- page layout


def read_tsv(path: Path) -> list[dict[str, str]]:
    words = []
    with path.open(encoding="utf-8", errors="replace") as handle:
        header = handle.readline().rstrip("\n").split("\t")
        for line in handle:
            values = line.rstrip("\n").split("\t")
            if len(values) == len(header):
                row = dict(zip(header, values))
                if row["level"] == "5" and row["text"].strip():
                    words.append(row)
    return words


def page_lines(tsv: Path, page: int) -> list[dict]:
    """Group OCR words into lines, splitting the number column from the names."""
    lines: dict[tuple[str, str, str], dict] = {}
    for word in read_tsv(tsv / f"p{page:03d}.tsv"):
        key = (word["block_num"], word["par_num"], word["line_num"])
        x, y, height = int(word["left"]), int(word["top"]), int(word["height"])
        line = lines.setdefault(key, {"words": [], "top": y, "bottom": y + height})
        line["words"].append((x, word["text"]))
        line["top"] = min(line["top"], y)
        line["bottom"] = max(line["bottom"], y + height)
    out = []
    for line in lines.values():
        words = sorted(line["words"])
        out.append({
            "top": line["top"],
            "bottom": line["bottom"],
            "number_text": " ".join(t for x, t in words if x < NUMBER_COLUMN[1]),
            "text": " ".join(t for x, t in words if x >= NUMBER_COLUMN[1]),
            "full": " ".join(t for _, t in words),
        })
    return sorted(out, key=lambda line: line["top"])


def column_numbers(tsv: Path, page: int) -> list[tuple[int, int]]:
    return [
        (int(word["top"]), int(word["text"]))
        for word in read_tsv(tsv / f"n{page:03d}.tsv")
        if word["text"].isdigit() and float(word["conf"]) > 20
    ]


def mostly_upper(text: str) -> bool:
    letters = [ch for ch in text if ch.isalpha()]
    return bool(letters) and sum(ch.isupper() for ch in letters) / len(letters) > 0.8


def clean_name(text: str) -> str:
    text = re.sub(r"[\(\)\{\}\[\]€<>|*\"“”]", " ", text)
    text = text.replace("’", "'").replace("‘", "'").replace("`", "'")
    text = re.sub(r"\s+[23Iìèî?>.,;:]+\s*$", "", text)
    return re.sub(r"\s+", " ", text).strip(" .,-;:")


def is_heading(text: str) -> bool:
    upper = text.upper()
    return (
        ("DEPUTATI" in upper or "REPUBBLICA" in upper)
        and "GAZZETTA" not in upper
        # Headings are capitals; a street name such as "p.zza Della Repubblica" is not.
        and mostly_upper(re.sub(r"\b\w*(?:rizion|egion)\w*", "", text, flags=re.I))
    )


def parse_sections(chamber: str, tsv: Path) -> list[dict]:
    """Split the table pages into sections and colleges of raw text lines."""
    sections: list[dict] = []
    for page in CHAMBERS[chamber]["pages"]:
        lines = page_lines(tsv, page)
        numbers = column_numbers(tsv, page)
        header_bottom = 0
        pending_heading = None
        for line in lines[:12]:
            if is_heading(line["full"]):
                found = re.search(r"(?:Circoscrizion|Regione)\w*\s+(.+)", line["full"])
                pending_heading = found.group(1) if found else line["full"]
                if not sections:
                    sections.append({"heading": pending_heading, "page": page, "colleges": [], "stray": []})
                    pending_heading = None
            if re.search(r"Comuni e/o|grandi citt", line["full"], re.I) or re.fullmatch(
                r"\W*(Numero|.?.ordine|col\S{0,3}gio)\W*", line["number_text"], re.I
            ):
                header_bottom = max(header_bottom, line["bottom"])
        if not sections:
            continue
        body = [
            line for line in lines
            if header_bottom + 5 < line["top"] < FOOTER_Y
            and not re.match(r"^\(?\s*provincia", line["full"], re.I)
            and not re.fullmatch(r"[-—_=. ]*", line["full"])
        ]
        spacing = statistics.median([b["top"] - a["top"] for a, b in zip(body, body[1:])] or [38])
        first = True
        previous_top = None
        for line in body:
            colleges = sections[-1]["colleges"]
            number = next((value for y, value in numbers if abs(y - line["top"]) < 25), None)
            mark = bool(re.search(r"\w", line["number_text"]))
            gap = previous_top is None or line["top"] - previous_top > 1.6 * spacing
            wide_gap = previous_top is not None and line["top"] - previous_top > 2.4 * spacing
            previous_top = line["top"]
            readings = {number} if number is not None else set()
            digits = re.sub(r"\D", "", line["number_text"])
            if digits and len(digits) <= 3:
                readings.add(int(digits))
            if pending_heading is not None and (readings or mark):
                # A heading opens a section only if its page restarts at college 1;
                # otherwise it is a stray (the Chamber Calabria table repeats one).
                if 1 in readings or not readings or not colleges:
                    sections.append({"heading": pending_heading, "page": page, "colleges": [], "stray": []})
                    colleges = sections[-1]["colleges"]
                else:
                    sections[-1]["stray"].append((page, pending_heading))
                pending_heading = None
            current = colleges[-1]["number"] if colleges else 0
            start = None
            if not colleges and (readings or mark):
                start = 1
            elif current + 1 in readings:
                start = current + 1
            elif readings and all(value == current for value in readings):
                start = None  # the current number printed again
            elif first and (readings or mark):
                start = None  # a misread page-top number continues the college
            elif gap and (readings or mark):
                start = current + 1
            elif wide_gap and colleges and mostly_upper(line["text"]):
                start = current + 1  # number lost by OCR; the layout gap marks it
            if colleges and any(
                chamber == forced[0] and page == forced[1] and line["text"].startswith(forced[2])
                for forced in FORCED_STARTS
            ):
                start = current + 1
            if readings or mark:
                first = False
            if start is not None:
                colleges.append({"number": start, "page": page, "lines": []})
            if colleges and line["text"].strip():
                colleges[-1]["lines"].append((page, line["text"]))
    for section in sections:
        move_prose_lists(section["colleges"])
    return sections


def move_prose_lists(colleges: list[dict]) -> None:
    """A prose list can begin a line above its college number (Salerno, college 15)."""
    for college, following in zip(colleges, colleges[1:]):
        starts = [
            index for index, (_, text) in enumerate(college["lines"])
            if index > 0 and re.match(r"^C[oc]{1,2}mprende\s+i\s+seguenti", text, re.I)
        ]
        if starts and following["lines"] and not mostly_upper(following["lines"][0][1]):
            following["lines"][:0] = college["lines"][starts[-1]:]
            del college["lines"][starts[-1]:]


# ----------------------------------------------------------------------- entries

PROSE_LIST = re.compile(r"seguenti\s+comuni\s*:\s*(.+?)(?:\s+nonch|\.\s|\.$|$)", re.I | re.S)
PARTIAL_PATTERNS = (
    r"Comprende\s+[i1l][l1]\s+comune\s+di\s+([A-Z][\w' ]+?)[,.]",
    r"parte\s+del\s+territori\w*\s+del\s+c\w{4,5}\s+(?:di\s+)?([A-Z][\w']+)",
)


def college_entries(lines: list[tuple[int, str]], page: int) -> list[dict]:
    """Classify a college's lines as whole municipalities, city zones, or described parts."""
    out: list[dict] = []
    prose = " ".join(text for _, text in lines)
    for found in PROSE_LIST.finditer(prose):
        for name in re.split(r",|\s+e\s+", found.group(1)):
            if name.strip(" .;:"):
                out.append({"kind": "whole", "name": name.strip(" .;:").upper(), "raw": name, "page": page})
    described: dict[str, str] = {}
    for pattern in PARTIAL_PATTERNS:
        for found in re.finditer(pattern, prose, re.I):
            described.setdefault(found.group(1).upper(), found.group(0))
    for city, raw in described.items():
        out.append({"kind": "described_part", "name": city, "raw": raw, "page": page, "description": prose})
    describing = False
    for line_page, line in lines:
        if re.match(r"^C[oc]{1,2}mprende\b", line, re.I):
            describing = True
        continues = any(ch.islower() for ch in line) or " - " in line or line.rstrip().endswith((",", ")", "-", "—"))
        if describing and continues:
            continue
        describing = False
        name = clean_name(line)
        if len(name) < 2 or not mostly_upper(name):
            continue
        entry = {"kind": "whole", "name": name, "raw": line, "page": line_page}
        # "PARMA-CIRC.1": a one-word city name joined to the zone without spaces.
        named = re.match(r"^(?:\S{1,3}\s+)?([A-Z]{4,})-(\S.*)$", name)
        # "FI EX-QUART.1": Florence's former quarters.
        coded = re.match(r"^([A-Z0-9]{2})\s+(EX-.+)$", name) or re.match(
            r"^(?:\S{1,3}\s+)?([A-Z0-9]{2})(?:\s*-\s*|\s+[^\w\s]\s+|\s+)([A-Z0-9'].+)$",
            re.sub(r"\bR[HN]-", "RM-", name),
        )
        # The decree brackets every zone of a large city: "( RM-MONTI )".
        bracketed = bool(re.match(r"^\s*[\(\{\[€<]", line)) or line.rstrip().endswith((")", "}", ">"))
        if named:
            entry.update(kind="zone", prefix=named.group(1), zone=named.group(2))
        elif coded and (
            bracketed
            or re.match(r"^[A-Z0-9]{2}\s*(?:-|\W\s)", name)
            or re.match(r"^\S{1,3}\s+[A-Z0-9]{2}-", name)  # "C RM-...": an OCR'd bracket
        ):
            entry.update(kind="zone", code=coded.group(1), zone=coded.group(2))
        elif bracketed:
            entry.update(kind="zone", zone=name)
        out.append(entry)
    return out


# ------------------------------------------------------------------ name matching


def normal(text: str) -> str:
    """Collapse letters the scan confuses (H/M, 1/I, 0/O, 5/S, 8/B) on both sides."""
    text = text.upper().translate(str.maketrans({"0": "O", "1": "I", "5": "S", "8": "B", "H": "M", "$": "S"}))
    return re.sub(r"[^A-Z]", "", text)


def edit_similarity(a: str, b: str) -> float:
    """1 - Levenshtein distance / longer length; suits one-letter OCR slips."""
    previous = list(range(len(b) + 1))
    for i, char_a in enumerate(a, start=1):
        current = [i]
        for j, char_b in enumerate(b, start=1):
            current.append(min(previous[j] + 1, current[j - 1] + 1, previous[j - 1] + (char_a != char_b)))
        previous = current
    return 1 - previous[-1] / max(len(a), len(b), 1)


def match_name(text: str, names: dict[str, str]) -> tuple[str | None, float]:
    """Match an OCR'd name to ``names`` (normalised -> official); ties stay unresolved."""
    target = normal(text)
    if not target:
        return None, 0.0
    if target in names:
        return names[target], 1.0
    scored = sorted(
        ((edit_similarity(target, key), key) for key in get_close_matches(target, list(names), n=6, cutoff=0.5)),
        reverse=True,
    )
    if not scored:
        return None, 0.0
    if len(scored) > 1 and scored[0][0] - scored[1][0] < 0.05:
        return None, scored[0][0]
    return names[scored[0][1]], scored[0][0]


# -------------------------------------------------------------------- reference


def load_reference(database: Path, category: str) -> dict[str, dict[str, set[str]]]:
    """geography -> canonical municipality -> Open Data college labels (1994)."""
    field = "constituency" if category == "camera" else "region"
    connection = sqlite3.connect(f"file:{database}?mode=ro", uri=True)
    try:
        rows = connection.execute(
            f"""SELECT DISTINCT {field}, municipality, college FROM election_results
                 WHERE category=? AND election_date='1994-03-27' AND municipality IS NOT NULL""",
            (category,),
        ).fetchall()
    finally:
        connection.close()
    reference: dict[str, dict[str, set[str]]] = defaultdict(lambda: defaultdict(set))
    for geography, municipality, college in rows:
        name = canonical_municipality(municipality)
        if geography and name:
            reference[geography][name.upper()].add(college or "")
    return reference


# ------------------------------------------------------------------------ build


def build(chamber: str, tsv: Path, reference: dict[str, dict[str, set[str]]]) -> list[dict]:
    owners: dict[str, set[str]] = defaultdict(set)
    for geography, names in reference.items():
        for name in names:
            owners[name].add(geography)
    sections = parse_sections(chamber, tsv)
    merged: list[dict] = []
    for section in sections:
        votes = Counter(
            geography
            for college in section["colleges"]
            for entry in college_entries(college["lines"], college["page"])
            for geography in owners.get(entry["name"], ())
        )
        section["geography"] = votes.most_common(1)[0][0] if votes else None
        if section["geography"] is None or not section["colleges"]:
            continue  # the decree's article pages
        if merged and merged[-1]["geography"] == section["geography"]:
            offset = merged[-1]["colleges"][-1]["number"]
            for college in section["colleges"]:
                college["number"] += offset
            merged[-1]["colleges"].extend(section["colleges"])
        else:
            merged.append(section)

    rows = []
    for section in merged:
        geography = section["geography"]
        names = {normal(name): name for name in reference[geography]}
        split_cities = [name for name, colleges in reference[geography].items() if len(colleges) > 1]
        split_names = {normal(name): name for name in split_cities}
        for college in section["colleges"]:
            college_city = None
            for entry in college_entries(college["lines"], college["page"]):
                kind, municipality, score = entry["kind"], None, 0.0
                if kind == "zone":
                    city = None
                    zone_cities = list(split_cities)
                    if entry.get("prefix"):
                        city, prefix_score = match_name(entry["prefix"], split_names)
                        city = city if prefix_score >= 0.95 else None
                        # Zones of a city that Open Data shows in one piece
                        # (Senate 1994: "VERONA-ZONA AMM.1"); exact names only.
                        exact = names.get(normal(entry["prefix"]))
                        if city is None and exact:
                            city = exact
                            zone_cities.append(exact)
                    if city is None and entry.get("code"):
                        code = entry["code"].translate(str.maketrans({"8": "B", "0": "O", "1": "I", "5": "S"}))
                        city = CITY_CODES.get(code)
                        if code == "PO" and "PRATO" not in split_cities:
                            city = "PADOVA"  # PD is often read as PO
                    # A hyphenated name such as PONT-CANAVESE is not a zone; only
                    # bracketed or coded lines may inherit the college's city.
                    if city not in split_cities and not entry.get("prefix"):
                        city = college_city
                        if city not in split_cities:
                            coded_cities = [name for name in split_cities if name in CITY_CODES.values()]
                            city = coded_cities[0] if len(coded_cities) == 1 else None
                    if city in zone_cities:
                        college_city, municipality, score = city, city, 1.0
                    else:
                        kind = "whole"
                elif kind == "described_part":
                    # Only a split city can be described in part; OCR slips such
                    # as "Terine" for Torino are resolved within that short list.
                    municipality, score = match_name(entry["name"], split_names)
                    score = 1.0 if municipality and score >= 0.6 else 0.0
                if municipality is None:
                    municipality, score = match_name(entry["name"], names)
                rows.append({
                    "map_version": CHAMBERS[chamber]["map_version"],
                    "geography": geography,
                    "college": college["number"],
                    "municipality": municipality if municipality and score >= 0.75 else "",
                    "entry_type": kind,
                    "entry_text": entry.get("zone", "") if kind == "zone" else entry.get("description", ""),
                    "source_page": entry["page"] - PRINTED_PAGE_OFFSET,
                    "ocr_text": entry["raw"].strip(),
                    "match_score": round(score, 3),
                })
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    commands = parser.add_subparsers(dest="command", required=True)
    ocr = commands.add_parser("ocr", help="render and OCR the table pages")
    ocr.add_argument("--pdf", type=Path, required=True)
    ocr.add_argument("--work", type=Path, required=True)
    ocr.add_argument("--tesseract", default="tesseract")
    ocr.add_argument("--workers", type=int, default=6)
    make = commands.add_parser("build", help="parse OCR output into registry CSVs")
    make.add_argument("--work", type=Path, required=True)
    make.add_argument("--database", type=Path, required=True, help="opened read-only")
    make.add_argument("--out", type=Path, default=REGISTRY_DIR)
    args = parser.parse_args()
    if args.command == "ocr":
        run_ocr(args.pdf, args.work, args.tesseract, args.workers)
        return
    args.out.mkdir(parents=True, exist_ok=True)
    for chamber in CHAMBERS:
        rows = build(chamber, args.work / "tsv", load_reference(args.database, chamber))
        target = args.out / f"{CHAMBERS[chamber]['map_version']}.csv"
        with target.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=REGISTRY_FIELDS)
            writer.writeheader()
            writer.writerows(rows)
        colleges = {(row["geography"], row["college"]) for row in rows}
        unresolved = sum(not row["municipality"] for row in rows)
        print(f"{chamber}: {len(colleges)} colleges, {len(rows)} entries, {unresolved} unresolved -> {target}")


if __name__ == "__main__":
    main()
