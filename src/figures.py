"""
Makes the four charts used in the README.
Run build_dataset.py and analyse.py first.
"""
import pathlib

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parent.parent
FIG = ROOT / "figures"

# same palette as the signal timing project, it passed a colour-blind check
BLUE, RED, GREY = "#2E6FD9", "#E04B4B", "#9a9a97"
SURFACE = "#fcfcfb"
INK, MUTED = "#23231f", "#6b6b66"

plt.rcParams.update({
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE,
    "text.color": INK, "axes.labelcolor": MUTED, "axes.edgecolor": "#d8d8d4",
    "xtick.color": MUTED, "ytick.color": MUTED,
    "font.size": 10, "axes.titlesize": 11,
})


def style(ax):
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", color="#e8e8e4", linewidth=0.8)
    ax.set_axisbelow(True)


def fig1_pci_is_a_formula(df):
    """Published score against the one rebuilt from its parts."""
    d = df[df.Pave_Type.isin(["AC", "CO"])]
    good = d[d.rebuild_error <= 0.1]
    off = d[d.rebuild_error > 0.1]

    fig, ax = plt.subplots(figsize=(6.6, 6.0))
    ax.plot([0, 100], [0, 100], color=GREY, linewidth=1.2,
            linestyle=(0, (5, 3)), zorder=1)
    ax.scatter(good.PCI, good.pci_rebuilt, s=9, c=BLUE, alpha=0.45,
               linewidths=0, label=f"matches ({len(good)})")
    ax.scatter(off.PCI, off.pci_rebuilt, s=26, c=RED, linewidths=0.5,
               edgecolors=SURFACE, label=f"doesn't match ({len(off)})")
    ax.set_xlabel("PCI as published")
    ax.set_ylabel("PCI rebuilt from DMI and IRI")
    ax.set_title("The score is arithmetic, not a measurement",
                 loc="left", fontweight="bold")
    ax.legend(frameon=False, loc="upper left", fontsize=9)
    style(ax); ax.grid(axis="x", color="#e8e8e4", linewidth=0.8)
    fig.tight_layout(); fig.savefig(FIG / "1_pci_is_a_formula.png", dpi=170)
    return len(good), len(off)


def fig2_where_the_score_goes(df):
    """Points lost to cracking and to roughness, per pavement type."""
    names = {"AC": "Asphalt", "CO": "Composite", "PC": "Concrete",
             "ST": "Surface treated"}
    d = (df.groupby("Pave_Type")[["loss_cracking", "loss_roughness"]]
           .median().reindex(["PC", "CO", "ST", "AC"]))

    fig, ax = plt.subplots(figsize=(7.6, 3.8))
    y = range(len(d))
    ax.barh(y, d.loss_cracking, color=BLUE, label="cracking and surface damage")
    ax.barh(y, d.loss_roughness, left=d.loss_cracking, color=RED,
            label="roughness")
    ax.set_yticks(list(y)); ax.set_yticklabels([names[i] for i in d.index])
    ax.set_xlabel("PCI points below a perfect road, at the median section")
    ax.set_title("Concrete roads lose their score to roughness, "
                 "asphalt to cracking", loc="left", fontweight="bold")
    ax.legend(frameon=False, loc="lower right", fontsize=9)
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="x", color="#e8e8e4", linewidth=0.8); ax.set_axisbelow(True)
    fig.tight_layout(); fig.savefig(FIG / "2_where_the_score_goes.png", dpi=170)


def fig3_north_south_gap(gaps):
    """The north-south gap, split into its two causes."""
    names = {"FWY": "Freeways", "ART": "Arterials", "COL": "Collectors"}
    g = gaps.set_index("road_class")

    fig, ax = plt.subplots(figsize=(7.8, 4.0))
    y = range(len(g))
    ax.barh(y, g.cracking, color=BLUE, label="cracking and surface damage")
    ax.barh(y, g.roughness, left=g.cracking, color=RED, label="roughness")
    ax.set_xlim(g.total.min() * 1.28, 0)
    for i, (_, r) in enumerate(g.iterrows()):
        ax.annotate(f"{r.total:+.1f} PCI", xy=(r.total - 0.35, i),
                    ha="right", va="center", fontsize=9.5, color=INK,
                    fontweight="bold")
    ax.set_yticks(list(y))
    ax.set_yticklabels([f"{names[i]}\n{int(r.n_north)} vs {int(r.n_south)}"
                        for i, r in g.iterrows()])
    ax.axvline(0, color=INK, linewidth=0.9)
    ax.set_xlabel("how far northern asphalt sits below southern asphalt, "
                  "in PCI points")
    ax.set_title("The north's roads are more cracked, not much rougher",
                 loc="left", fontweight="bold")
    ax.legend(frameon=False, fontsize=9, ncol=2,
              loc="upper center", bbox_to_anchor=(0.5, -0.24))
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="x", color="#e8e8e4", linewidth=0.8); ax.set_axisbelow(True)
    fig.tight_layout(); fig.savefig(FIG / "3_north_south_gap.png", dpi=170)


def fig4_two_axes(df):
    """Every asphalt section on its distress and roughness axes."""
    ac = df[(df.Pave_Type == "AC") & df.region.notna()]
    fig, ax = plt.subplots(figsize=(7.2, 5.4))
    for label, colour, size in (("South", GREY, 12), ("North", RED, 26)):
        d = ac[ac.region == label]
        ax.scatter(d.DMI, d.IRI, s=size, c=colour,
                   alpha=0.5 if label == "South" else 0.95,
                   linewidths=0.4, edgecolors=SURFACE,
                   label=f"{label} ({len(d)})")
    for label, colour in (("South", INK), ("North", RED)):
        d = ac[ac.region == label]
        ax.plot(d.DMI.median(), d.IRI.median(), marker="X", markersize=13,
                color=colour, markeredgecolor=SURFACE, markeredgewidth=1.4,
                linestyle="none", zorder=5)
    ax.annotate("  medians", xy=(ac[ac.region == "North"].DMI.median(),
                                 ac[ac.region == "North"].IRI.median()),
                fontsize=8.5, color=MUTED, va="center")
    ax.set_xlabel("distress score (10 is a new road, low means cracked)")
    ax.set_ylabel("roughness, IRI in m/km (low is smooth)")
    ax.set_title("Northern asphalt sits to the left, not far above",
                 loc="left", fontweight="bold")
    ax.legend(frameon=False, loc="upper right", fontsize=9)
    ax.invert_xaxis()
    style(ax); ax.grid(axis="x", color="#e8e8e4", linewidth=0.8)
    fig.tight_layout(); fig.savefig(FIG / "4_two_axes.png", dpi=170)


if __name__ == "__main__":
    df = pd.read_csv(ROOT / "data/processed/sections.csv")
    gaps = pd.read_csv(ROOT / "data/processed/region_gaps.csv")
    FIG.mkdir(parents=True, exist_ok=True)
    good, off = fig1_pci_is_a_formula(df)
    fig2_where_the_score_goes(df)
    fig3_north_south_gap(gaps)
    fig4_two_axes(df)
    print(f"wrote 4 figures to {FIG}")
    print(f"  PCI rebuilt exactly for {good} of {good + off} sections")
