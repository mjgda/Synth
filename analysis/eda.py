"""Exploratory data analysis of the synthetic market-share dataset.

Usage:  python analysis/eda.py [path/to/csv]

Writes figures to reports/figures/ and summary tables to reports/tables/.
Every number quoted in REPORT.md is produced by this script.
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
CSV = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "data" / "market_share_synthetic.csv"
FIG = ROOT / "reports" / "figures"
TAB = ROOT / "reports" / "tables"
FIG.mkdir(parents=True, exist_ok=True)
TAB.mkdir(parents=True, exist_ok=True)

KEY = ["Interval", "Manufacturer", "Product", "State"]
MFRS = ["Valley Central", "Neptune", "Cornfield", "Barefoot"]
TIERS = ["Rail", "Call", "Premium", "Top Shelf"]  # assumed low -> high price tier

# ---- chart styling (light-mode reference palette) --------------------------
SURFACE, INK, INK2, MUTED, GRID, AXIS = "#fcfcfb", "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7"
MFR_COLOR = dict(zip(MFRS, ["#2a78d6", "#eb6834", "#1baf7a", "#eda100"]))
plt.rcParams.update({
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
    "font.family": "DejaVu Sans", "font.size": 10, "text.color": INK,
    "axes.edgecolor": AXIS, "axes.labelcolor": INK2, "axes.titlesize": 12, "axes.titleweight": "bold",
    "axes.titlelocation": "left", "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "axes.axisbelow": True, "grid.color": GRID, "grid.linewidth": 0.6,
    "xtick.color": MUTED, "ytick.color": MUTED, "xtick.labelcolor": INK2, "ytick.labelcolor": INK2,
    "lines.linewidth": 2, "legend.frameon": False, "legend.fontsize": 9,
})


def save(fig, name):
    fig.tight_layout()
    fig.savefig(FIG / name, dpi=160)
    plt.close(fig)


def label_ends(ax, x, items, min_gap):
    """Direct-label line ends at x, nudging labels apart so none collide. items: [(y, text)]."""
    items = sorted(items)
    ys = [y for y, _ in items]
    for i in range(1, len(ys)):
        ys[i] = max(ys[i], ys[i - 1] + min_gap)
    for (y0, text), y in zip(items, ys):
        ax.annotate(text, (x, y0), xytext=(x + pd.Timedelta(days=25), y), textcoords="data",
                    va="center", fontsize=9, color=INK2)


def year_ticks(ax, first=2020, last=2026):
    ax.set_xticks([pd.Timestamp(f"{y}-01-01") for y in range(first, last + 1)])
    ax.xaxis.set_major_formatter(matplotlib.dates.DateFormatter("%Y"))


def section(title):
    print(f"\n{'=' * 78}\n{title}\n{'=' * 78}")


# ---- 1. Load & integrity ---------------------------------------------------
raw = pd.read_csv(CSV, dtype=str, keep_default_na=False)
df = raw.copy()
df["Units"] = pd.to_numeric(df["Units"], errors="raise").astype(int)
df["Date"] = pd.to_datetime(df["Interval"], format="%Y-%m")
df["Year"], df["Month"] = df.Date.dt.year, df.Date.dt.month

section("1. Integrity")
dims = {c: df[c].nunique() for c in KEY}
print("rows:", len(df), "| distinct:", dims, "| full grid size:", int(np.prod(list(dims.values()))))
print("duplicate keys:", df.duplicated(KEY).sum(), "| blanks:", int((raw == "").sum().sum()),
      "| negatives:", (df.Units < 0).sum(), "| zeros:", (df.Units == 0).sum())
months = pd.period_range(df.Date.min(), df.Date.max(), freq="M")
print("months:", months[0], "->", months[-1], "| gaps:", len(set(months) - set(df.Date.dt.to_period("M"))))
print(df.Units.describe(percentiles=[.5, .9, .99]).round(1).to_string())

# ---- 2. Market total: deterministic seasonality ---------------------------
section("2. Market total")
tot = df.groupby(["Year", "Month"]).Units.sum().unstack()
season = tot.div(tot[1], axis=0)
year_idx = tot / tot.loc[2020]
print("Seasonal index (month / January):\n", season.round(3).to_string())
print("\nIndex vs same month of 2020:\n", year_idx.round(3).to_string())
annual = df.groupby("Year").Units.sum()
h1 = df[df.Month <= 6].groupby("Year").Units.sum()
ytd = pd.DataFrame({"full_year": annual, "H1": h1, "H1_share_of_year": (h1 / annual).round(3),
                    "naive_FY_yoy_%": (annual.pct_change() * 100).round(1),
                    "H1_yoy_%": (h1.pct_change() * 100).round(1)})
print("\n", ytd.to_string())
ytd.to_csv(TAB / "annual_vs_h1.csv")

monthly_total = df.groupby("Date").Units.sum()
fig, ax = plt.subplots(figsize=(10, 3.6))
ax.plot(monthly_total.index, monthly_total.values, color=MFR_COLOR["Valley Central"])
ax.set_title("Total units by month: the same seasonal curve every year")
ax.set_ylabel("Units")
ax.yaxis.set_major_formatter(matplotlib.ticker.StrMethodFormatter("{x:,.0f}"))
for y in range(2020, 2027):
    d = pd.Timestamp(f"{y}-06-01")
    ax.annotate(f"Jun {y}\n{monthly_total[d]:,}", (d, monthly_total[d]), xytext=(0, 6),
                textcoords="offset points", ha="center", fontsize=8, color=INK2)
ax.set_ylim(0, monthly_total.max() * 1.18)
save(fig, "01_market_total_monthly.png")

fig, ax = plt.subplots(figsize=(10, 3.6))
yrs = annual.index.astype(str)
ax.bar(yrs, annual.values, color="#cde2fb", width=0.6, label="Full year")
ax.bar(yrs, h1.values, color=MFR_COLOR["Valley Central"], width=0.6, label="Jan–Jun (H1)")
for x, (a, b) in enumerate(zip(annual.values, h1.values)):
    ax.text(x, a + 3000, f"{a:,}", ha="center", fontsize=8, color=INK2)
ax.text(len(yrs) - 1, annual.iloc[-1] * 0.5, "2026 is\nH1 only", ha="center", va="center",
        color="white", fontsize=8, fontweight="bold")
ax.set_title("Annual units: 2026 holds six months, so the full-year bar is not comparable")
ax.yaxis.set_major_formatter(matplotlib.ticker.StrMethodFormatter("{x:,.0f}"))
ax.legend(loc="upper right", ncols=2)
ax.set_ylim(0, annual.max() * 1.15)
ax.grid(axis="x", visible=False)
save(fig, "02_annual_vs_h1.png")

# ---- 3. Manufacturer share ------------------------------------------------
section("3. Manufacturer share")
mm = df.pivot_table(index="Date", columns="Manufacturer", values="Units", aggfunc="sum")[MFRS]
msh = mm.div(mm.sum(axis=1), axis=0) * 100
ann_m = df.pivot_table(index="Year", columns="Manufacturer", values="Units", aggfunc="sum")[MFRS]
h1_m = df[df.Month <= 6].pivot_table(index="Year", columns="Manufacturer", values="Units", aggfunc="sum")[MFRS]
print("Annual share %:\n", (ann_m.div(ann_m.sum(axis=1), axis=0) * 100).round(2).to_string())
print("\nH1 units:\n", h1_m.to_string())
print("\nH1 YoY %:\n", (h1_m.pct_change() * 100).round(1).to_string())
steps = msh.diff().round(0)
print("\nMoM share change (pp, rounded) counts:\n",
      steps.apply(lambda s: s.value_counts()).fillna(0).astype(int).sort_index().to_string())
print("\nFractional part of share (whole-point lattice check):\n",
      (msh - msh.round(0)).describe().loc[["mean", "std"]].round(3).to_string())
msh.round(3).to_csv(TAB / "manufacturer_share_monthly.csv")
pd.concat({"annual_units": ann_m, "h1_units": h1_m}, axis=1).to_csv(TAB / "manufacturer_annual_h1.csv")

fig, ax = plt.subplots(figsize=(10, 4.2))
for m in MFRS:
    ax.plot(msh.index, msh[m], color=MFR_COLOR[m], label=m)
label_ends(ax, msh.index[-1], [(msh[m].iloc[-1], f"{m} {msh[m].iloc[-1]:.1f}%") for m in MFRS], 2.5)
year_ticks(ax)
ax.set_title("Unit share by manufacturer (share of these four brands)")
ax.set_ylabel("Share of units (%)")
ax.set_ylim(0, 50)
ax.set_xlim(msh.index[0], msh.index[-1] + pd.Timedelta(days=420))
ax.legend(loc="upper left", ncols=4)
save(fig, "03_manufacturer_share.png")

fig, axes = plt.subplots(1, 4, figsize=(11, 2.8), sharey=True)
bins = np.arange(-3.5, 4.5, 1)
for ax, m in zip(axes, MFRS):
    v = steps[m].dropna()
    ax.hist(v, bins=bins, color=MFR_COLOR[m], rwidth=0.8)
    ax.set_title(m, fontsize=10)
    ax.set_xticks(range(-3, 4))
    ax.grid(axis="x", visible=False)
axes[0].set_ylabel("Months")
fig.suptitle("Month-over-month share change, in whole points: the big three only ever move −1, 0 or +1",
             x=0.01, ha="left", fontsize=11, fontweight="bold")
save(fig, "04_share_steps.png")

print("\nBarefoot moves of 3 points (all three big brands moved the same way):\n",
      steps.loc[steps.Barefoot.abs() >= 3].to_string())
print("\nCorrelation of MoM share changes (the plug is the only one correlated with the others):\n",
      msh.diff().corr().round(2).to_string())
print("Lag-1 autocorrelation of MoM share changes (≈0 means random walk, no momentum):",
      {m: round(float(msh[m].diff().autocorr(1)), 2) for m in MFRS})


def decompose(a, b):
    """Split each brand's H1 unit change into market-size effect and share effect."""
    t0, t1 = h1_m.loc[a].sum(), h1_m.loc[b].sum()
    s0, s1 = h1_m.loc[a] / t0, h1_m.loc[b] / t1
    out = pd.DataFrame({f"H1 {a}": h1_m.loc[a], f"H1 {b}": h1_m.loc[b], "change": h1_m.loc[b] - h1_m.loc[a],
                        "market_effect": (t1 - t0) * s0, "share_effect": t1 * (s1 - s0),
                        "share_pts": (s1 - s0) * 100})
    print(f"\nH1 {a} -> H1 {b}: market {t0:,} -> {t1:,} ({t1 / t0 - 1:+.1%})\n", out.round(1).to_string())
    return out


decomp = pd.concat({"2020_to_2026": decompose(2020, 2026), "2025_to_2026": decompose(2025, 2026)})
decomp.round(1).to_csv(TAB / "h1_change_decomposition.csv")

# ---- 4. Product (tier) mix ------------------------------------------------
section("4. Product mix")
pm = df.pivot_table(index="Date", columns="Product", values="Units", aggfunc="sum")[TIERS]
psh = pm.div(pm.sum(axis=1), axis=0) * 100
ann_p = df.pivot_table(index="Year", columns="Product", values="Units", aggfunc="sum")[TIERS]
print("Annual product share %:\n", (ann_p.div(ann_p.sum(axis=1), axis=0) * 100).round(2).to_string())
psh.round(3).to_csv(TAB / "product_share_monthly.csv")

mp = df.pivot_table(index=["Date", "Manufacturer"], columns="Product", values="Units", aggfunc="sum")[TIERS]
mix = mp.div(mp.sum(axis=1), axis=0) * 100
spread = mix.groupby(level=0).agg(lambda s: s.max() - s.min())
print("\nSpread of each tier's share across the 4 manufacturers in the same month (pp):\n",
      spread.describe().loc[["mean", "50%", "max"]].round(2).to_string())
# separability: units(t,m,p) == M(t,m) * P(t,p) / T(t)
g = df.groupby(["Interval", "Manufacturer", "Product"]).Units.sum().reset_index()
expected = (g.groupby(["Interval", "Manufacturer"]).Units.transform("sum")
            * g.groupby(["Interval", "Product"]).Units.transform("sum")
            / g.groupby("Interval").Units.transform("sum"))
rel = ((g.Units - expected) / expected).abs()
print(f"Separability: median |rel. dev| = {rel.median():.2%}, 99th pct = {rel.quantile(.99):.2%} "
      f"(large deviations only in tiny cells)")
print("Correlation of MoM tier share changes (Top Shelf behaves as the tier plug):\n",
      psh.diff().corr().round(2).to_string())
print("MoM sd of tier share (pp):", psh.diff().std().round(2).to_dict())

fig, axes = plt.subplots(1, 4, figsize=(11, 3.0), sharey=True)
for ax, p in zip(axes, TIERS):
    for q in TIERS:
        if q != p:
            ax.plot(psh.index, psh[q], color=GRID, linewidth=1.2)
    ax.plot(psh.index, psh[p], color=MFR_COLOR["Valley Central"], linewidth=2)
    ax.set_title(f"{p}  ({psh[p].iloc[0]:.0f}% → {psh[p].iloc[-1]:.0f}%)", fontsize=10)
    ax.xaxis.set_major_locator(matplotlib.dates.YearLocator(2))
    ax.xaxis.set_major_formatter(matplotlib.dates.DateFormatter("%Y"))
axes[0].set_ylabel("Share of units (%)")
axes[0].set_ylim(0, 45)
fig.suptitle("Unit share by product tier (other tiers in grey): Call collapses, Top Shelf rises",
             x=0.01, ha="left", fontsize=11, fontweight="bold")
save(fig, "05_product_share.png")

fig, axes = plt.subplots(1, 4, figsize=(11, 3.0), sharey=True)
for ax, p in zip(axes, TIERS):
    for m in MFRS:
        s = mix.xs(m, level=1)[p]
        ax.plot(s.index, s, color=MFR_COLOR[m], label=m, linewidth=1.5)
    ax.set_title(p, fontsize=10)
    ax.xaxis.set_major_locator(matplotlib.dates.YearLocator(2))
    ax.xaxis.set_major_formatter(matplotlib.dates.DateFormatter("%y"))
axes[0].set_ylabel("% of manufacturer's units")
handles, labels = axes[0].get_legend_handles_labels()
fig.legend(handles, labels, loc="lower center", ncols=4, bbox_to_anchor=(0.5, -0.01))
fig.suptitle("Each manufacturer's product mix: four lines per panel, drawn on top of each other",
             x=0.01, ha="left", fontsize=11, fontweight="bold")
fig.tight_layout(rect=(0, 0.08, 1, 1))
fig.savefig(FIG / "06_mix_identical.png", dpi=160)
plt.close(fig)

# ---- 5. State allocation ---------------------------------------------------
section("5. State allocation")
df["block"] = df.groupby(["Interval", "Manufacturer", "Product"]).Units.transform("sum")
big = df[df.block >= 1500]
w = (big.groupby("State").Units.sum() / big.Units.sum()).sort_values(ascending=False)
df["state_share"] = df.Units / df.block
stab = df[df.block >= 1500].groupby("State").state_share.agg(["mean", "std"]) * 100
print("State weights (blocks >= 1,500 units) — mean and std of share across",
      df[df.block >= 1500][["Interval", "Manufacturer", "Product"]].drop_duplicates().shape[0], "blocks:")
print(stab.loc[w.index].round(3).to_string())
print(f"Top 4 states = {w.head(4).sum():.1%} of units; bottom 25 = {w.tail(25).sum():.1%}")
w.rename("weight").to_csv(TAB / "state_weights.csv")

# residual vs fixed allocation
df["expected"] = df.block * df.State.map(w)
resid = df.Units - df.expected
print(f"Max |actual - block x weight| over all {len(df):,} cells: {resid.abs().max():.2f} units")

# reconstruct intended block totals assuming cell = round(B * w)
W = w.values
blocks = df.pivot_table(index=["Interval", "Manufacturer", "Product"], columns="State", values="Units")[w.index]
rows = []
for idx, obs in zip(blocks.index, blocks.values):
    s = obs.sum()
    cands = np.arange(max(1, s // 2), 2 * s + 30)
    err = np.abs(np.floor(np.outer(cands, W) + 0.5) - obs).sum(axis=1)
    rows.append((*idx, s, cands[err.argmin()], err.min()))
rb = pd.DataFrame(rows, columns=["Interval", "Manufacturer", "Product", "observed", "implied", "fit_err"])
rb["gap_pct"] = (rb.observed - rb.implied) / rb.implied * 100
print(f"round(B x w) reproduces {np.mean(rb.fit_err == 0):.0%} of blocks exactly; "
      f"mean abs cell error {rb.fit_err.mean() / 51:.3f} units")
by = rb.groupby(pd.cut(rb.implied, [0, 25, 50, 100, 200, 500, 20000]), observed=True).agg(
    blocks=("gap_pct", "size"), mean_gap_pct=("gap_pct", "mean"), worst_gap_pct=("gap_pct", "min"))
print("Observed block total vs implied (rounding loss):\n", by.round(1).to_string())
rb.to_csv(TAB / "block_rounding.csv", index=False)

fl = df[df.State == "FL"]
fig, ax = plt.subplots(figsize=(10, 3.6))
ax.scatter(fl.block, fl.state_share * 100, s=10, color=MFR_COLOR["Valley Central"], alpha=0.5, linewidths=0)
ax.axhline(w["FL"] * 100, color=INK2, linewidth=1)
ax.annotate(f"FL weight {w['FL']:.1%}", (fl.block.max(), w["FL"] * 100), xytext=(0, 6),
            textcoords="offset points", ha="right", fontsize=9, color=INK2)
ax.set_xscale("log")
ax.set_xlabel("Units in the manufacturer × product × month block (log scale)")
ax.set_ylabel("FL share of block (%)")
ax.set_title("Florida's share is a constant; spread appears only when blocks are small (rounding)")
save(fig, "07_state_share_constant.png")

top = w.head(15)[::-1] * 100
fig, ax = plt.subplots(figsize=(10, 4.2))
ax.barh(top.index, top.values, color=MFR_COLOR["Valley Central"], height=0.6)
for y, v in enumerate(top.values):
    ax.text(v + 0.15, y, f"{v:.1f}%", va="center", fontsize=8, color=INK2)
ax.set_title("Top 15 states by fixed allocation weight (identical for every brand, tier and month)")
ax.set_xlabel("Share of units (%)")
ax.grid(axis="y", visible=False)
save(fig, "08_state_weights.png")

# ---- 6. Raw-value outliers and naive-metric traps --------------------------
section("6. Outliers & traps")
q1, q3 = df.Units.quantile([.25, .75])
fence = q3 + 1.5 * (q3 - q1)
flag = df[df.Units > fence]
print(f"IQR fence {fence:.0f}: {len(flag):,} cells flagged ({len(flag) / len(df):.1%}); "
      f"{flag.State.isin(w.head(8).index).mean():.0%} are top-8 states")
print("Largest cells:\n", df.nlargest(5, "Units")[KEY + ["Units"]].to_string(index=False))
z = df[df.Units == 0]
print("Zeros by manufacturer:", z.Manufacturer.value_counts().to_dict())
print("Zeros by product:", z.Product.value_counts().to_dict())
print("Smallest blocks:\n", rb.nsmallest(5, "observed")[["Interval", "Manufacturer", "Product", "observed", "implied"]]
      .to_string(index=False))
c = df[df.Interval.isin(["2024-06", "2025-06"])].pivot_table(
    index=["Manufacturer", "Product", "State"], columns="Interval", values="Units")
yoy = c["2025-06"] / c["2024-06"] - 1
top_growth = yoy.replace(np.inf, np.nan).nlargest(10)
print(f"Cell-level Jun-25 vs Jun-24 growth: {np.isinf(yoy).sum()} infinite, {yoy.isna().sum()} undefined (0/0); "
      f"top 10 finite growth cells all Barefoot: {(top_growth.index.get_level_values(0) == 'Barefoot').all()}")
print(top_growth.mul(100).round(0).to_string())
print("\nDone. Figures ->", FIG.relative_to(ROOT), "| tables ->", TAB.relative_to(ROOT))
