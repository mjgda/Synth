"""Data-quality guards for a monthly market-share extract.

Usage:  python analysis/dq_checks.py [path/to/csv] [--min-units 50] [--share-jump 2]

Prints PASS / WARN / FAIL per check and exits non-zero on any FAIL, so it can gate a pipeline.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
ap = argparse.ArgumentParser()
ap.add_argument("csv", nargs="?", default=ROOT / "data" / "market_share_synthetic.csv")
ap.add_argument("--min-units", type=int, default=50, help="block size below which growth rates are unreliable")
ap.add_argument("--share-jump", type=float, default=2.0, help="month-over-month share move (points) that triggers a WARN")
args = ap.parse_args()

KEY = ["Interval", "Manufacturer", "Product", "State"]
results: list[tuple[str, str, str]] = []


def check(name: str, status: str, detail: str) -> None:
    results.append((status, name, detail))


raw = pd.read_csv(args.csv, dtype=str, keep_default_na=False)
check("Expected columns", "PASS" if list(raw.columns) == KEY + ["Units"] else "FAIL", ", ".join(raw.columns))
blanks = int((raw.apply(lambda c: c.str.strip()) == "").sum().sum())
check("No blank values", "PASS" if blanks == 0 else "FAIL", f"{blanks} blank cells")

units = pd.to_numeric(raw.Units, errors="coerce")
bad = int(units.isna().sum() + (units < 0).sum() + (units.dropna() % 1 != 0).sum())
check("Units are non-negative integers", "PASS" if bad == 0 else "FAIL", f"{bad} bad values")
df = raw.assign(Units=units.fillna(0).astype(int))

dups = int(df.duplicated(KEY).sum())
check("Unique keys", "PASS" if dups == 0 else "FAIL", f"{dups} duplicate key rows")

bad_month = int((~df.Interval.str.fullmatch(r"\d{4}-(0[1-9]|1[0-2])")).sum())
check("Interval format YYYY-MM", "PASS" if bad_month == 0 else "FAIL", f"{bad_month} malformed")
months = pd.period_range(df.Interval.min(), df.Interval.max(), freq="M").strftime("%Y-%m")
gaps = sorted(set(months) - set(df.Interval))
check("No missing months", "PASS" if not gaps else "FAIL", f"{df.Interval.min()} to {df.Interval.max()}, gaps: {gaps[:5] or 'none'}")

dims = {c: df[c].nunique() for c in KEY}
grid = 1
for v in dims.values():
    grid *= v
check("Complete grid (every combination present)", "PASS" if grid == len(df) else "WARN",
      f"{len(df):,} rows vs {grid:,} combinations {dims}")

last = df.Interval.max()
check("Latest year complete", "PASS" if last.endswith("-12") else "WARN",
      f"data ends {last}: compare the latest year to date with the same months a year earlier")

zeros = int((df.Units == 0).sum())
check("Zero cells", "PASS" if zeros == 0 else "WARN",
      f"{zeros:,} cells are 0 ({zeros / len(df):.1%}); confirm 0 means none sold, not missing")

blk = df.groupby(["Interval", "Manufacturer", "Product"]).Units.sum()
small = blk[blk < args.min_units]
check(f"Blocks under {args.min_units} units", "PASS" if small.empty else "WARN",
      f"{len(small)} brand × tier × month blocks; suppress or pool them before quoting growth"
      + (f" (e.g. {', '.join(' / '.join(i) for i in small.nsmallest(3).index)})" if len(small) else ""))

share = df.pivot_table(index="Interval", columns="Manufacturer", values="Units", aggfunc="sum")
share = share.div(share.sum(axis=1), axis=0) * 100
jumps = share.diff().abs().stack()
jumps = jumps[jumps >= args.share_jump]
check(f"Brand share moves of {args.share_jump:g}+ points in a month", "PASS" if jumps.empty else "WARN",
      f"{len(jumps)} moves" + (": " + ", ".join(f"{m} {i} ({share.diff().at[i, m]:+.1f})" for i, m in jumps.index[:6]) if len(jumps) else ""))

state_share = df.groupby(["Interval", "State"]).Units.sum() / df.groupby("Interval").Units.sum()
spread = state_share.groupby(level="State").std() * 100
check("State shares vary over time", "WARN" if spread.max() < 0.1 else "PASS",
      f"largest monthly std of a state's share: {spread.max():.3f} pts"
      + (" (states are a fixed allocation; no geographic signal)" if spread.max() < 0.1 else ""))

width = max(len(n) for _, n, _ in results)
for status, name, detail in results:
    print(f"[{status:4}] {name:<{width}}  {detail}")
fails = sum(s == "FAIL" for s, _, _ in results)
warns = sum(s == "WARN" for s, _, _ in results)
print(f"\n{len(results)} checks: {len(results) - fails - warns} pass, {warns} warn, {fails} fail")
sys.exit(1 if fails else 0)
