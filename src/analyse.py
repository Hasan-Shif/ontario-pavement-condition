"""
Splits each PCI into its cracking and roughness halves, then compares
northern and southern asphalt within the same road class.

Run build_dataset.py first. The charts come from figures.py.
"""
import pathlib
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from pci import gap_attribution
from regions import label_text
from pci import PCI_COEFFS
from uncertainty import bootstrap_gap, LEVEL

ROOT = pathlib.Path(__file__).resolve().parent.parent

MIN_GROUP = 10      # below this a median isn't worth reporting
CLASSES = ["FWY", "ART", "COL", "LOC"]


def audit(df):
    """
    Rows where the published score doesn't match its own ingredients.

    Only asphalt and composite count here. Those two equations are
    published, so a mismatch means something is wrong with the row.
    The other two equations are my own fit, so a mismatch there is
    just as likely to be my fit.
    """
    published = df[df.Pave_Type.isin(["AC", "CO"])]
    off = published[published.rebuild_error > 0.1]
    default = df[(df.PCI.round(2) == 92.89) & (df.DMI == 9.5)]
    stale = df[df.PCI_change == 0]
    impossible = df[df.IRI <= 0]
    return off, default, stale, impossible


def compare(df, region_col="region"):
    """North against south, holding pavement type and road class fixed."""
    ac = df[(df.Pave_Type == "AC") & df[region_col].notna()]
    rows = []
    for fc in CLASSES:
        here = ac[ac.FUNC_CLASS == fc]
        north = here[here[region_col] == "North"]
        south = here[here[region_col] == "South"]
        if len(north) < MIN_GROUP or len(south) < MIN_GROUP:
            continue
        g = gap_attribution(north.DMI.median(), north.IRI.median(),
                            south.DMI.median(), south.IRI.median(), "AC")
        ci = bootstrap_gap(north[["DMI", "IRI"]].to_numpy(),
                           south[["DMI", "IRI"]].to_numpy(),
                           PCI_COEFFS["AC"])
        rows.append({"road_class": fc, "n_north": len(north),
                     "n_south": len(south), **g,
                     "share_cracking": g["cracking"] / g["total"],
                     "total_low": ci["total_low"], "total_high": ci["total_high"],
                     "share_low": ci["share_low"], "share_high": ci["share_high"],
                     "excludes_zero": ci["excludes_zero"]})
    return pd.DataFrame(rows)


def robustness(df):
    """
    The region of a highway is decided by whichever of its sections
    happen to name a town, and then applied to all of them. This checks
    that against the stricter version, where only the sections naming a
    town count, and everything else is dropped.
    """
    endpoints = (df.Pavement_Section_From.astype(str) + " | " +
                 df.Pavement_Section_To.astype(str))
    strict = pd.Series([label_text(t) for t in endpoints], index=df.index)
    overlap = df.region.notna() & strict.notna()
    agreement = (df.region[overlap] == strict[overlap]).mean()
    return strict, overlap.sum(), agreement


def main():
    df = pd.read_csv(ROOT / "data/processed/sections.csv")

    off, default, stale, impossible = audit(df)
    print("Data quality")
    n_pub = int(df.Pave_Type.isin(["AC", "CO"]).sum())
    print(f"  {len(off)} of {n_pub} asphalt and composite sections whose PCI "
          f"doesn't match their own DMI and IRI")
    print(f"  {len(default)} sitting at exactly 92.89 with a distress score of 9.5")
    print(f"  {len(stale)} with a PCI identical to last year's")
    print(f"  {len(impossible)} with a roughness of zero")

    print("\nWhere the score goes, by pavement type (median points lost)")
    halves = df.groupby("Pave_Type")[["loss_cracking", "loss_roughness"]].median()
    halves["share_cracking"] = (halves.loss_cracking /
                                (halves.loss_cracking + halves.loss_roughness))
    print(halves.round(2).to_string())

    print(f"\nNorthern asphalt against southern asphalt, same road class")
    print(f"  (square brackets are {LEVEL}% bootstrap intervals)")
    gaps = compare(df)
    for _, r in gaps.iterrows():
        sure = "" if r.excludes_zero else "   [could be chance]"
        print(f"  {r.road_class} ({r.n_north:.0f} north, {r.n_south:.0f} south): "
              f"{r.total:+.1f} PCI  [{r.total_low:+.1f} to {r.total_high:+.1f}]"
              f"{sure}")
        print(f"      cracking {r.cracking:+.1f}, roughness {r.roughness:+.1f}, "
              f"cracking is {r.share_cracking:.0%} "
              f"[{r.share_low:.0%} to {r.share_high:.0%}] of it")

    strict, n_overlap, agreement = robustness(df)
    print(f"\nSame comparison using only sections that name a town themselves")
    print(f"  the two labellings agree on {agreement:.0%} of the "
          f"{n_overlap} sections that carry both")
    strict_gaps = compare(df.assign(region_strict=strict), "region_strict")
    for _, r in strict_gaps.iterrows():
        print(f"  {r.road_class} ({r.n_north:.0f} north, {r.n_south:.0f} south): "
              f"{r.total:+.1f} PCI, {r.share_cracking:.0%} cracking")

    gaps.to_csv(ROOT / "data/processed/region_gaps.csv", index=False)
    strict_gaps.to_csv(ROOT / "data/processed/region_gaps_strict.csv", index=False)


if __name__ == "__main__":
    main()
