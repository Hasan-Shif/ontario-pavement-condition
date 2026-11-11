"""
Working out which highways are in Northern Ontario.

The condition file has no coordinates. What it does have is the names
of the places each section runs between, so a section that mentions
Kapuskasing is in the north and one that mentions Burlington isn't.

Most rows name a road, not a town, so the names are used to label the
highway and the label is then carried to every section on it. Highways
whose names point both ways, or neither, are left out. Highway 11 runs
1,885 km and crosses the boundary, so it is one of the ones left out.
"""

NORTHERN_PLACES = [
    "THUNDER BAY", "KENORA", "TIMMINS", "SUDBURY", "SAULT", "DRYDEN",
    "FORT FRANCES", "KAPUSKASING", "HEARST", "COCHRANE", "PICKLE LAKE",
    "RED LAKE", "ATIKOKAN", "MARATHON", "WAWA", "CHAPLEAU", "NIPIGON",
    "GERALDTON", "LONGLAC", "ESPANOLA", "NORTH BAY", "SIOUX", "IGNACE",
    "TERRACE BAY", "SCHREIBER", "MANITOUWADGE", "ELLIOT LAKE",
    "BLIND RIVER", "MATTAWA", "KIRKLAND", "NEW LISKEARD", "ENGLEHART",
    "IROQUOIS FALLS", "MANITOULIN", "GORE BAY", "HORNEPAYNE",
    "DUBREUILVILLE", "MOONBEAM", "SMOOTH ROCK",
]

SOUTHERN_PLACES = [
    "TORONTO", "OTTAWA", "HAMILTON", "LONDON", "WINDSOR", "KINGSTON",
    "NIAG", "FORT ERIE", "BARRIE", "GUELPH", "KITCHENER", "WATERLOO",
    "BRANTFORD", "OSHAWA", "PETERBOROUGH", "BELLEVILLE", "CORNWALL",
    "SARNIA", "CHATHAM", "ST CATHARINES", "BURLINGTON", "MISSISSAUGA",
    "BRAMPTON", "PICKERING", "WHITBY", "AJAX", "MILTON", "ORILLIA",
    "COLLINGWOOD", "OWEN SOUND", "STRATFORD", "WOODSTOCK", "SIMCOE",
    "TILLSONBURG", "GODERICH", "WALKERTON", "ORANGEVILLE", "NEWMARKET",
    "BRADFORD", "CAMBRIDGE", "THOROLD",
]


def label_text(text):
    """
    Which region, if any, a pair of section endpoints points to.

    >>> label_text("KAPUSKASING - BROADWAY AV")
    'North'
    >>> label_text("BURLOAK DR IC-109 | THIRD LINE IC-113")
    >>> label_text("HAMILTON - CENTENNIAL PKWY IC-88")
    'South'
    """
    t = text.upper()
    north = any(p in t for p in NORTHERN_PLACES)
    south = any(p in t for p in SOUTHERN_PLACES)
    if north == south:          # both or neither tells us nothing
        return None
    return "North" if north else "South"


def label_highways(df):
    """
    One label per highway, from whatever its sections happen to name.
    A highway with evidence pointing both ways is left unlabelled.
    """
    votes = {}
    for hwy, section in zip(df.Highway, df.endpoints):
        seen = votes.setdefault(hwy, set())
        found = label_text(section)
        if found:
            seen.add(found)
    return {h: v.pop() for h, v in votes.items() if len(v) == 1}


if __name__ == "__main__":
    import doctest
    fails, total = doctest.testmod()
    print(f"doctests: {total - fails} passed, {fails} failed")
