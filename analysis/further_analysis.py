"""Answers to the 'further inquiry' questions that the data itself can answer.

Usage:  python analysis/further_analysis.py [path/to/csv]

1. Share-shift monitor   rolling-12-month change split into market effect and share effect
2. Source of share       who took share from whom (proportional flow allocation)
3. Tier migration        same flow method across product tiers
4. Forecast backtest     market total and brand share, rolling origin, vs naive baselines
5. H2 2026 forecast      market by month and brand shares with 80% intervals
Writes tables to reports/tables/.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
CSV = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "data" / "market_share_synthetic.csv"
TAB = ROOT / "reports" / "tables"
TAB.mkdir(parents=True, exist_ok=True)
MFRS = ["Valley Central", "Neptune", "Cornfield", "Barefoot"]
TIERS = ["Rail", "Call", "Premium", "Top Shelf"]
pd.set_option("display.width", 200)

df = pd.read_csv(CSV)
df["Date"] = pd.to_datetime(df.Interval, format="%Y-%m")
brand = df.pivot_table(index="Date", columns="Manufacturer", values="Units", aggfunc="sum")[MFRS]
tier = df.pivot_table(index="Date", columns="Product", values="Units", aggfunc="sum")[TIERS]
market = brand.sum(axis=1)


def section(t):
    print(f"\n{'=' * 78}\n{t}\n{'=' * 78}")


# ---- 1. Share-shift monitor (rolling 12 months) ----------------------------
section("1. Share-shift monitor: rolling 12 months vs the 12 months before")
r12 = brand.rolling(12).sum()
r12m = r12.sum(axis=1)
rows = []
for d in r12.index[23:]:
    p = d - pd.DateOffset(months=12)
    t0, t1 = r12m[p], r12m[d]
    for m in MFRS:
        s0, s1 = r12.at[p, m] / t0, r12.at[d, m] / t1
        rows.append({"r12_end": d.strftime("%Y-%m"), "manufacturer": m, "units": r12.at[d, m],
                     "units_prior": r12.at[p, m], "change": r12.at[d, m] - r12.at[p, m],
                     "market_effect": (t1 - t0) * s0, "share_effect": t1 * (s1 - s0),
                     "share_pct": s1 * 100, "share_pts_change": (s1 - s0) * 100,
                     "market_change_pct": (t1 / t0 - 1) * 100})
mon = pd.DataFrame(rows)
mon.round(2).to_csv(TAB / "r12_share_shift_monitor.csv", index=False)
latest = mon[mon.r12_end == mon.r12_end.max()].set_index("manufacturer")
print(f"R12 to {mon.r12_end.max()} vs prior R12 (market {latest.market_change_pct.iloc[0]:+.1f}%):")
print(latest[["units", "units_prior", "change", "market_effect", "share_effect", "share_pct", "share_pts_change"]]
      .round(1).to_string())
wide = mon.pivot(index="r12_end", columns="manufacturer", values="share_pts_change")[MFRS]
print("\nR12 share-point change vs prior R12, each June:")
print(wide[wide.index.str.endswith("-06")].round(1).to_string())


# ---- 2/3. Flow allocation ---------------------------------------------------
def flow_matrix(units: pd.DataFrame) -> pd.DataFrame:
    """Each month, allocate every gainer's share gain to the losers in proportion to their losses.
    Returns cumulative points flowing FROM row TO column."""
    sh = units.div(units.sum(axis=1), axis=0) * 100
    d = sh.diff().dropna()
    names = list(units.columns)
    f = pd.DataFrame(0.0, index=names, columns=names)
    for _, row in d.iterrows():
        gains, losses = row[row > 0], -row[row < 0]
        if losses.sum() == 0:
            continue
        for g, gv in gains.items():
            for l, lv in losses.items():
                f.at[l, g] += gv * lv / losses.sum()
    return f


section("2. Source of share: cumulative points flowing FROM (row) TO (column), Jan 2020 – Jun 2026")
fb = flow_matrix(brand)
net_b = fb - fb.T
print("Gross flows:\n", fb.round(1).to_string())
print("\nNet flows (positive = column gained from row):\n", net_b.round(1).to_string())
via_bf = fb.loc["Barefoot"].sum() + fb["Barefoot"].sum()
print(f"\nShare of all gross flow that involves Barefoot: {via_bf / fb.values.sum():.0%}")
fb.round(2).to_csv(TAB / "brand_share_flows.csv")

section("3. Tier migration: cumulative points FROM (row) TO (column)")
ft = flow_matrix(tier)
print("Gross flows:\n", ft.round(1).to_string())
print("\nNet flows (positive = column gained from row):\n", (ft - ft.T).round(1).to_string())
tsh = tier.div(tier.sum(axis=1), axis=0) * 100
call_peak = tsh.Call.loc["2022"].idxmax()
print(f"\nSince Call's 2022 peak ({call_peak:%b %Y}, {tsh.Call[call_peak]:.1f}%):")
print((tsh.iloc[-1] - tsh.loc[call_peak]).round(1).rename("pts change to Jun 2026").to_string())
print("Net flow out of Call over that window:")
print(((ft_w := flow_matrix(tier.loc[call_peak:])) - ft_w.T).loc["Call"].round(1).to_string())
ft.round(2).to_csv(TAB / "tier_share_flows.csv")

# ---- 4. Forecast backtest ---------------------------------------------------
section("4. Forecast backtest")
mt = market.to_frame("u")
mt["Y"], mt["M"] = mt.index.year, mt.index.month


def seasonal_profile(hist: pd.DataFrame) -> pd.Series:
    full = hist.groupby("Y").filter(lambda g: len(g) == 12)
    return (full.u / full.groupby("Y").u.transform("sum")).groupby(full.M).mean()


res = []
for y in range(2021, 2026):
    prof = seasonal_profile(mt[mt.Y < y])
    h1 = mt[(mt.Y == y) & (mt.M <= 6)].u.sum()
    level = h1 / prof.loc[1:6].sum()
    actual = mt[(mt.Y == y) & (mt.M > 6)].u
    seas = level * prof.loc[7:12].values
    naive = mt[(mt.Y == y - 1) & (mt.M > 6)].u.values
    res.append({"year": y, "H2_actual": actual.sum(),
                "seasonal_x_ytd_MAPE_%": np.mean(np.abs(seas - actual.values) / actual.values) * 100,
                "same_month_last_year_MAPE_%": np.mean(np.abs(naive - actual.values) / actual.values) * 100})
bt_m = pd.DataFrame(res)
print("Market total, forecast Jul–Dec from Jan–Jun:\n", bt_m.round(2).to_string(index=False))

sh = brand.div(market, axis=0) * 100
rows = []
for h in (1, 3, 6, 12):
    for o in range(24, len(sh) - h):
        hist, act = sh.iloc[: o + 1], sh.iloc[o + h]
        last = hist.iloc[-1]
        slope = (hist.iloc[-1] - hist.iloc[-13]) / 12
        preds = {"naive_last_value": last, "linear_trend_12m": last + slope * h,
                 "mean_last_12m": hist.iloc[-12:].mean()}
        for k, p in preds.items():
            for m in MFRS:
                rows.append({"h": h, "method": k, "mfr": m, "abs_err": abs(p[m] - act[m])})
bt_s = pd.DataFrame(rows)
tab = bt_s.pivot_table(index=["h", "mfr"], columns="method", values="abs_err", aggfunc="mean")
print("\nBrand share MAE (points), rolling origin from 2022:\n", tab.round(2).to_string())
print("\nAverage over brands:\n", bt_s.pivot_table(index="h", columns="method", values="abs_err").round(2).to_string())
pd.concat({"market": bt_m.set_index("year")}, axis=1).to_csv(TAB / "backtest_market.csv")
tab.round(3).to_csv(TAB / "backtest_share.csv")

# ---- 5. H2 2026 forecast ------------------------------------------------------
section("5. Forecast Jul–Dec 2026")
prof = seasonal_profile(mt)
level = mt[mt.Y == 2026].u.sum() / prof.loc[1:6].sum()
fc_dates = pd.date_range("2026-07-01", periods=6, freq="MS")
fc_market = pd.Series(level * prof.loc[7:12].values, index=fc_dates)
print(f"Implied 2026 full year: {level:,.0f} units (H1 actual {mt[mt.Y == 2026].u.sum():,} + H2 forecast {fc_market.sum():,.0f})")
steps = sh.diff().dropna()
last = sh.iloc[-1]
out = []
for i, d in enumerate(fc_dates, start=1):
    for m in MFRS:
        # empirical h-step share change distribution (overlapping windows)
        hstep = (sh[m].shift(-i) - sh[m]).dropna()
        lo, hi = np.percentile(hstep, [10, 90])
        out.append({"month": d.strftime("%Y-%m"), "manufacturer": m, "market_units": round(fc_market[d]),
                    "share_pct": last[m], "share_p10": max(0, last[m] + lo), "share_p90": last[m] + hi,
                    "units": fc_market[d] * last[m] / 100})
fc = pd.DataFrame(out)
fc.round(2).to_csv(TAB / "forecast_h2_2026.csv", index=False)
print("Market by month:", {k.strftime('%b'): round(v) for k, v in fc_market.items()})
summ = fc.groupby("manufacturer").agg(H2_units=("units", "sum"), share=("share_pct", "last"),
                                      share_p10_dec=("share_p10", "last"), share_p90_dec=("share_p90", "last"))
print("Brand H2 2026 (naive share, 80% band at Dec from empirical 6-month moves):\n",
      summ.loc[MFRS].round(1).to_string())
