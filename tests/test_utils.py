from app.utils import canonical_municipality


def test_canonical_municipality_reunites_split_city_labels() -> None:
    # Labels seen for the same cities in the 1994-1996 Chamber archive and pages.
    assert canonical_municipality("Roma centro") == "ROMA"
    assert canonical_municipality("Parte di Comune ROMA") == "ROMA"
    assert canonical_municipality("parte del comune di Roma") == "ROMA"
    assert canonical_municipality("Verona Est") == "VERONA"
    assert canonical_municipality("Verona Ovest") == "VERONA"
    assert canonical_municipality("REGGIO DI CALABRIA") == "REGGIO CALABRIA"
    assert canonical_municipality("Reggio Calabria - Sbarre") == "REGGIO CALABRIA"


def test_canonical_municipality_keeps_similar_names_apart() -> None:
    assert canonical_municipality("VERONELLA") == "VERONELLA"
    assert canonical_municipality("ROMANO CANAVESE") == "ROMANO CANAVESE"
