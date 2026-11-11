"""
Ontario's Pavement Condition Index, taken apart.

PCI isn't measured. It's a weighted sum of two things that are:
a distress score (DMI) and a roughness reading (IRI). Pull those
apart and you can say which of the two is costing a road its score.
"""

# Ontario publishes the asphalt and composite equations. I fitted the
# other two from the open data because I couldn't find them published,
# so treat ST and PC as approximate (see README).
PCI_COEFFS = {
    "AC": (13.75, 9.00, 7.50),    # asphalt concrete
    "CO": (20.50, 8.50, 11.00),   # composite, asphalt over concrete
    "ST": (13.14, 8.90, 5.42),    # surface treatment, fitted
    "PC": (31.14, 6.94, 8.36),    # portland cement concrete, fitted
}

PCI_MIN, PCI_MAX = 0.0, 100.0


def pci(dmi, iri, pave_type):
    """
    Rebuild the published score from its two parts.

    >>> round(pci(7.31, 1.34, "AC"), 2)
    69.49
    >>> round(pci(7.80, 1.34, "CO"), 2)
    72.06
    """
    a, b, c = PCI_COEFFS[pave_type]
    return max(PCI_MIN, min(PCI_MAX, a + b * dmi - c * iri))


def split_loss(dmi, iri, pave_type):
    """
    How far short of a perfect road each half falls, in PCI points.

    A perfect road would score 10 on distress and 0 on roughness.
    Everything below that is either cracking or ride quality, and
    this says how much of each.

    >>> d = split_loss(8.46, 1.28, "AC")
    >>> round(d["cracking"], 2), round(d["roughness"], 2)
    (13.86, 9.6)
    """
    a, b, c = PCI_COEFFS[pave_type]
    return {"cracking": b * (10.0 - dmi), "roughness": c * iri}


def gap_attribution(dmi_a, iri_a, dmi_b, iri_b, pave_type):
    """
    Two groups of roads differ by some number of PCI points. This
    says how many of those points came from cracking and how many
    from roughness.

    Northern asphalt freeways against southern ones:

    >>> g = gap_attribution(8.17, 1.36, 9.11, 1.04, "AC")
    >>> round(g["cracking"], 1), round(g["roughness"], 1), round(g["total"], 1)
    (-8.5, -2.4, -10.9)
    """
    a, b, c = PCI_COEFFS[pave_type]
    cracking = b * (dmi_a - dmi_b)
    roughness = -c * (iri_a - iri_b)
    return {"cracking": cracking, "roughness": roughness,
            "total": cracking + roughness}


if __name__ == "__main__":
    import doctest
    fails, total = doctest.testmod()
    print(f"doctests: {total - fails} passed, {fails} failed")
