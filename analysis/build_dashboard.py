"""Build the standalone HTML dashboard and the Tableau-ready data file.

Usage:  python analysis/build_dashboard.py [path/to/csv]

Outputs
  dashboard/index.html              self-contained dashboard (data embedded; Chart.js from jsDelivr)
  tableau/market_share_tableau.csv  the same data with helper columns for Tableau Public
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
CSV = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "data" / "market_share_synthetic.csv"
MFRS = ["Valley Central", "Neptune", "Cornfield", "Barefoot"]
TIERS = ["Rail", "Call", "Premium", "Top Shelf"]
REGION = {
    "Northeast": "CT ME MA NH RI VT NJ NY PA",
    "Midwest": "IL IN MI OH WI IA KS MN MO NE ND SD",
    "South": "DE FL GA MD NC SC VA DC WV AL KY MS TN AR LA OK TX",
    "West": "AZ CO ID MT NV NM UT WY AK CA HI OR WA",
}
REGION_OF = {s: r for r, states in REGION.items() for s in states.split()}

df = pd.read_csv(CSV)
months = sorted(df.Interval.unique())
states = df.groupby("State").Units.sum().sort_values(ascending=False).index.tolist()
assert set(df.Manufacturer) == set(MFRS) and set(df.Product) == set(TIERS), "unexpected brands or tiers"
assert len(df) == len(months) * len(MFRS) * len(TIERS) * len(states), "data is not a complete grid"
assert not df.duplicated(["Interval", "Manufacturer", "Product", "State"]).any(), "duplicate keys"
assert set(states) <= set(REGION_OF), "state missing from region map"

# ---- dashboard -----------------------------------------------------------------
cube = (df.assign(Interval=pd.Categorical(df.Interval, months), Manufacturer=pd.Categorical(df.Manufacturer, MFRS),
                  Product=pd.Categorical(df.Product, TIERS), State=pd.Categorical(df.State, states))
        .sort_values(["Interval", "Manufacturer", "Product", "State"]))
payload = {"months": months, "mfrs": MFRS, "tiers": TIERS, "states": states,
           "units": cube.Units.astype(int).tolist()}
data_json = json.dumps(payload, separators=(",", ":")).replace("</", "<\\/")
template = (ROOT / "dashboard" / "template.html").read_text(encoding="utf-8")
assert template.count("__DASH_DATA__") == 1
out = ROOT / "dashboard" / "index.html"
out.write_text(template.replace("__DASH_DATA__", data_json), encoding="utf-8")
print(f"wrote {out.relative_to(ROOT)} ({out.stat().st_size / 1024:,.0f} KB)")

# ---- Tableau --------------------------------------------------------------------
tab = df.copy()
tab["Month Date"] = pd.to_datetime(tab.Interval, format="%Y-%m").dt.strftime("%Y-%m-%d")
tab["Year"] = tab.Interval.str[:4].astype(int)
tab["Month Num"] = tab.Interval.str[5:].astype(int)
tab["Half"] = (tab["Month Num"] <= 6).map({True: "H1", False: "H2"})
tab["Region"] = tab.State.map(REGION_OF)
tab["Tier Order"] = tab.Product.map({t: i + 1 for i, t in enumerate(TIERS)})
tab["Brand Order"] = tab.Manufacturer.map({m: i + 1 for i, m in enumerate(MFRS)})
last = tab.Interval.max()
tab["Partial Year"] = tab.Year.eq(int(last[:4])) & (last[5:] != "12")
key = ["Manufacturer", "Product", "State"]
prior = tab[key + ["Interval", "Units"]].copy()
prior["Interval"] = (pd.to_datetime(prior.Interval, format="%Y-%m") + pd.DateOffset(months=12)).dt.strftime("%Y-%m")
tab = tab.merge(prior.rename(columns={"Units": "Units Year Earlier"}), on=key + ["Interval"], how="left")
tab["Units Year Earlier"] = tab["Units Year Earlier"].astype("Int64")
cols = ["Month Date", "Interval", "Year", "Month Num", "Half", "Partial Year", "Manufacturer", "Brand Order",
        "Product", "Tier Order", "State", "Region", "Units", "Units Year Earlier"]
tdir = ROOT / "tableau"
tdir.mkdir(exist_ok=True)
tout = tdir / "market_share_tableau.csv"
tab[cols].sort_values(["Month Date", "Brand Order", "Tier Order", "State"]).to_csv(tout, index=False)
print(f"wrote {tout.relative_to(ROOT)} ({len(tab):,} rows, {tout.stat().st_size / 1024 / 1024:.1f} MB)")
