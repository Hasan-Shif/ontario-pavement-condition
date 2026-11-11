"""
How much of the north-south gap could just be luck.

Thirteen northern freeway sections is not many. Resampling those
sections, with replacement, a few thousand times shows how far the
gap moves when the draw changes, which is a fairer thing to quote
than a single median difference.
"""
import numpy as np

DRAWS = 5000
SEED = 20261112      # fixed so the numbers come out the same every run
LEVEL = 95


def bootstrap_gap(north, south, coeffs, draws=DRAWS, seed=SEED):
    """
    A confidence interval for a gap in PCI points, and for the share
    of it that cracking accounts for.

    north and south are arrays of (DMI, IRI) pairs. coeffs is the
    (intercept, dmi, iri) triple for the pavement type.

    >>> rng = np.random.default_rng(0)
    >>> n = np.c_[rng.normal(8.2, .5, 40), rng.normal(1.3, .2, 40)]
    >>> s = np.c_[rng.normal(9.1, .5, 40), rng.normal(1.05, .2, 40)]
    >>> r = bootstrap_gap(n, s, (13.75, 9.0, 7.5), draws=400, seed=1)
    >>> bool(r["total_low"] < r["total"] < r["total_high"])
    True
    """
    _, b, c = coeffs
    rng = np.random.default_rng(seed)

    def gap(n, s):
        cracking = b * (np.median(n[:, 0]) - np.median(s[:, 0]))
        roughness = -c * (np.median(n[:, 1]) - np.median(s[:, 1]))
        return cracking, roughness

    crack_0, rough_0 = gap(north, south)
    totals = np.empty(draws)
    shares = np.empty(draws)
    for i in range(draws):
        n = north[rng.integers(0, len(north), len(north))]
        s = south[rng.integers(0, len(south), len(south))]
        cr, ro = gap(n, s)
        totals[i] = cr + ro
        shares[i] = cr / (cr + ro) if (cr + ro) != 0 else np.nan

    lo, hi = (100 - LEVEL) / 2, 100 - (100 - LEVEL) / 2
    return {
        "total": crack_0 + rough_0,
        "total_low": np.percentile(totals, lo),
        "total_high": np.percentile(totals, hi),
        "share_cracking": crack_0 / (crack_0 + rough_0),
        "share_low": np.nanpercentile(shares, lo),
        "share_high": np.nanpercentile(shares, hi),
        "excludes_zero": np.percentile(totals, hi) < 0 or np.percentile(totals, lo) > 0,
    }


if __name__ == "__main__":
    import doctest
    fails, total = doctest.testmod()
    print(f"doctests: {total - fails} passed, {fails} failed")
