"""
Builds the dataset for the Ontario pavement project.

Reads   data/raw/pci_2022.csv, data/raw/pci_2023.csv
Writes  data/processed/sections.csv

Each row is one highway section in 2023, with its region, the two
halves of its PCI, and its 2022 condition where the same section can
be found in the earlier file.
"""
import pathlib
import sys

import pandas as pd

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from pci import pci, split_loss
from regions import label_highways

ROOT = pathlib.Path(__file__).resolve().parent.parent
RAW = ROOT / "data/raw"
OUT = ROOT / "data/processed"

# a section is the same section in both years if it sits on the same
# highway, same direction, between the same two chainages
KEY = ["Highway", "DIR", "FROM_Distance", "TO_Distance"]


def load(year):
    df = pd.read_csv(RAW / f"pci_{year}.csv")
    df.columns = [c.strip() for c in df.columns]
    df["Highway"] = df.Highway.astype(str)
    df["endpoints"] = (df.Pavement_Section_From.astype(str) + " | " +
                       df.Pavement_Section_To.astype(str))
    # the same stretch is listed twice in a handful of cases
    return df.drop_duplicates(KEY)


def main():
    now = load(2023)
    before = load(2022)
    print(f"  {len(now)} sections in 2023, {len(before)} in 2022")

    regions = label_highways(now)
    now["region"] = now.Highway.map(regions)
    print(f"  {len(regions)} of {now.Highway.nunique()} highways placed, "
          f"covering {now.region.notna().mean():.0%} of sections")

    # rebuild the published score from its parts. Anything that doesn't
    # land back on the published number is worth looking at.
    now["pci_rebuilt"] = [pci(d, i, t) for d, i, t
                          in zip(now.DMI, now.IRI, now.Pave_Type)]
    now["rebuild_error"] = (now.pci_rebuilt - now.PCI).abs()

    halves = [split_loss(d, i, t) for d, i, t
              in zip(now.DMI, now.IRI, now.Pave_Type)]
    now["loss_cracking"] = [h["cracking"] for h in halves]
    now["loss_roughness"] = [h["roughness"] for h in halves]

    prev = before[KEY + ["PCI", "DMI", "IRI"]].rename(
        columns={"PCI": "PCI_2022", "DMI": "DMI_2022", "IRI": "IRI_2022"})
    out = now.merge(prev, on=KEY, how="left")
    out["PCI_change"] = out.PCI - out.PCI_2022
    print(f"  {out.PCI_2022.notna().sum()} sections found in both years")

    cols = (KEY + ["PCI", "DMI", "IRI", "Pave_Type", "FUNC_CLASS", "region",
                   "Pavement_Section_From", "Pavement_Section_To",
                   "pci_rebuilt", "rebuild_error",
                   "loss_cracking", "loss_roughness",
                   "PCI_2022", "DMI_2022", "IRI_2022", "PCI_change"])
    OUT.mkdir(parents=True, exist_ok=True)
    out[cols].to_csv(OUT / "sections.csv", index=False)
    print(f"\nWrote {OUT / 'sections.csv'} ({len(out)} rows)")


if __name__ == "__main__":
    print("Building:")
    main()
