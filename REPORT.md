# Market Share Data (synthetic): EDA, traps, and next questions

Source file: `data/market_share_synthetic.csv` (63,648 rows; columns `Interval, Manufacturer, Product, State, Units`).
All numbers below come from `python analysis/eda.py`. The full console output is in `reports/eda_output.txt`.

## TL;DR

- **The file is clean, but it is built from a simple formula.** National total × manufacturer share × product mix × a fixed state weight, rounded to whole units. Once you see that, most of the 63k rows are redundant. Only **two series carry independent information: manufacturer share over time and product-tier mix over time.**
- **The biggest traps are time-based.** 2026 holds only six months, so a naive full-year comparison reads −46.7% when H1 vs H1 is −1.3%. June is 4× January every year, so month-over-month changes are meaningless.
- **State and cross-dimension cuts are traps.** Every brand has the same product mix, and every state gets the same fixed slice of every brand, tier and month. Any "Brand X over-indexes in Top Shelf" or "Brand X is growing in Texas" story is noise.
- **Small cells are rounding artifacts.** The data has 1,935 zeros (80% of them Barefoot). Blocks under ~100 units lose 3–17% of their volume to rounding. Cell-level growth rates of +500% or infinity are mechanical.
- **The real story:** Valley Central (+5.5 pts) and Neptune (+5.0 pts) took share from Barefoot (−7.5 pts) and Cornfield (−3.0 pts) in a market that shrank 7.2% (H1 2020 → H1 2026). Over the same period the Call tier collapsed from ~21% to ~6% of units and Top Shelf rose from ~19% to ~37%.

---

## 1. Integrity checks

| Check | Result |
|---|---|
| Rows | 63,648 = 78 months × 4 manufacturers × 4 products × 51 states. A **complete grid**, every combination present |
| Period | 2020-01 → 2026-06, no gaps |
| States | 50 states + DC (no territories) |
| Blanks / duplicate keys / negatives / non-integers | 0 / 0 / 0 / 0 |
| Zeros | 1,935 (3.0%). These are rounding outcomes, not "no data" (see trap 7) |
| Units distribution | median 10, mean 24.5, p99 197, max 1,019 (heavy right tail) |
| Row order | Sorted by Units descending within each month × manufacturer × product block. The order carries no meaning |

## 2. How the data was generated (reverse-engineered)

This is the most useful thing to say in an interview. The dataset decomposes exactly into four layers:

1. **National total = 10,000 × year factor × month factor.**
   - Month factors (Jan → Dec): `1, 1.25, 2, 2.75, 2.5, 4, 3.25, 3, 2, 1.5, 1, 0.75`. They sum to 25, so a factor-1.00 year is about 250k units.
   - Year factors: 2020 1.00, 2021 1.04, 2022 0.96, 2023 0.92, 2024 0.88, 2025 0.94, 2026 0.928.
   - The seasonal index is identical to three decimals in every year. The total has no noise at all.
2. **Manufacturer shares follow whole-point random walks.**
   - Valley Central, Neptune and Cornfield move exactly −1, 0 or +1 share point each month.
   - **Barefoot is the plug** (100 minus the others). Its monthly change correlates −0.56 to −0.62 with each of the others, while the other three are mutually uncorrelated (|r| ≤ 0.05). It is the only brand that moves ±2 or ±3 points.
3. **One product mix per month, applied to every manufacturer.**
   - Each tier's share differs across brands in the same month by a median of 0.1–0.2 pts (max 1.4 pts, in tiny cells).
   - Units(month, brand, tier) ≈ brand total × tier total ÷ market total, with a median error of 0.11%.
   - Top Shelf looks like the tier plug: it is the only tier whose monthly change correlates (−0.40 to −0.61) with the others, and it is the most volatile (σ 2.6 pts).
4. **Fixed state weights, then rounding:** cell = round(block total × state weight).
   - Across 389 large blocks, each state's share varies by only ±0.01–0.02 pts.
   - Across all 63,648 cells, the maximum gap between actual units and block × weight is **1.3 units**.

<img src="reports/figures/04_share_steps.png" width="900">
<img src="reports/figures/06_mix_identical.png" width="900">
<img src="reports/figures/07_state_share_constant.png" width="900">

## 3. What the data actually says

### Market: shrinking slowly, highly seasonal

<img src="reports/figures/01_market_total_monthly.png" width="900">
<img src="reports/figures/02_annual_vs_h1.png" width="900">

| | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 |
|---|---|---|---|---|---|---|---|
| Full-year units | 250,014 | 259,996 | 239,993 | 229,968 | 219,947 | 234,966 | *(H1 only)* |
| H1 units | 135,005 | 140,411 | 129,607 | 124,205 | 118,754 | 126,870 | 125,278 |
| H1 YoY | | +4.0% | −7.7% | −4.2% | −4.4% | +6.8% | **−1.3%** |

The market peaked in 2021, troughed in 2024, rebounded in 2025, and is slightly down in 2026 YTD. H1 is always 54% of the year, which implies a 2026 full year of about **232,000 units**.

### Manufacturers: consolidation toward the top two

<img src="reports/figures/03_manufacturer_share.png" width="900">

Unit change split into a market-size effect and a share effect:

| H1 2020 → H1 2026 (market −7.2%) | Units change | Market effect | Share effect | Share pts |
|---|---:|---:|---:|---:|
| Valley Central | +3,129 | −3,725 | +6,854 | **+5.5** (38.3 → 43.8%) |
| Neptune | +3,489 | −2,784 | +6,273 | **+5.0** (28.6 → 33.6%) |
| Cornfield | −5,884 | −2,097 | −3,787 | **−3.0** (21.6 → 18.5%) |
| Barefoot | −10,461 | −1,122 | −9,339 | **−7.5** (11.5 → 4.1%) |

Last 12 months (H1 2025 → H1 2026, market −1.3%):
- **Neptune is the only brand gaining:** +5,009 units, +4.4 pts.
- Valley Central is flat in units (−74).
- Barefoot halved (−52%).

### Product tiers: Call is disappearing

<img src="reports/figures/05_product_share.png" width="900">

| Annual unit share | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 H1 |
|---|---|---|---|---|---|---|---|
| Rail | 29.1% | 35.5% | 26.9% | 21.4% | 21.8% | 27.8% | 29.3% |
| Call | 17.3% | 14.7% | 19.7% | 16.7% | 10.5% | **4.0%** | 5.8% |
| Premium | 29.8% | 33.2% | 33.4% | 31.7% | 38.7% | 31.9% | 30.0% |
| Top Shelf | 23.8% | 16.5% | 20.1% | 30.1% | 29.1% | **36.4%** | 34.9% |

The tier names follow bar vocabulary (rail < call < premium < top shelf), which suggests price tiers. If so, the second tier is hollowing out. Top Shelf took most of that volume, and Rail recovered from its 2023–24 low (~21%) back to ~29%.

## 4. Traps and outliers

| # | Trap | Naive read | What is actually true | How to handle |
|---|---|---|---|---|
| 1 | **Partial final year** | 2026 down 46.7% | 2026 is Jan–Jun only. H1 vs H1 is −1.3% | Compare YTD with LYTD, or use rolling 12 months |
| 2 | **Seasonality** | "June +60% vs May", "December collapse", "May slump" | Fixed seasonal curve. June is 4× January. **May dips below April every year** (2.5 vs 2.75), a built-in feature, not an event | Compare with the same month last year, or seasonally adjust. Ask whether the May dip is a calendar or reporting artifact in real data |
| 3 | **Share ≠ volume** | "Valley Central is growing" | VC share +5.5 pts, but units only +6% because the market fell 7%. Last 12 months VC units are flat | Always show units, share, and the market vs share split together |
| 4 | **Small-base growth (Barefoot)** | Barefoot H1 2025 **+234%**, then H1 2026 −52% | Barefoot is the plug and absorbs the other three brands' moves. Its 8 biggest swings (±3 pts) happen exactly when all three others move together | Report changes in share points, not % growth, for small brands. Ask whether Barefoot is a real brand or "All Other" |
| 5 | **Brand × tier cuts** | "VC dominates Top Shelf" / "Cornfield is weak in Call" | Every brand has the same tier mix, so a brand's share in every tier equals its overall share | Mix and Simpson's-paradox analyses show nothing here. Value share = unit share if tier prices are common across brands |
| 6 | **State cuts** | "Florida is our growth market", "CA under-penetrated" | Every state's share is a constant, the same for every brand, tier and month. FL alone is 16.2%, more than TX+MI+MN combined (14.9%). The weights do not track population (CA 3.4%; AK 1.4% > AZ 0.7%) | No geographic insight exists in this file. Per-capita normalisation will produce artifacts. Ask for real geographic variation |
| 7 | **Rounding in small cells** | Zeros = "no sales"; summing states gives the true total | 1,935 zeros (Barefoot 1,542; Call tier 1,190; mostly NM, DC, WY, VT, NV). Blocks under 100 units lose 3–17% on average to rounding. Worst: Barefoot × Call, Jan 2026, sums to 11 where ~16 is implied (−31%) | Suppress or aggregate cells below a volume threshold. Don't take logs or % changes on cells with 0 or 1 unit |
| 8 | **Cell-level growth rankings** | "Barefoot Rail in AZ/ID/ND grew 500%" | 1 → 6 units. In Jun-25 vs Jun-24, 11 cells have infinite growth and 5 have 0/0. The top 10 growth cells are all Barefoot | Rank by absolute change, or use shrinkage or minimum-volume rules |
| 9 | **Raw-value "outliers"** | IQR rule flags 5,594 cells (8.8%); max 1,019 = VC × Premium × FL × Jun-2024 | All structural: big brand × FL × June. 64% of flagged cells are in the top-8 states | Detect outliers on normalised series (share, index vs expected), not raw units. In this file the genuine anomalies are the Barefoot ±3-pt months (Apr-20, Jan-21, Feb-21, Jul-21, Dec-21, Nov-23, Dec-24, Jan-26) |
| 10 | **Realism gaps** | Treat as a real market | No COVID shock in Mar–Apr 2020 (index exactly 1.00). No noise in the total. "Market" means these four brands only | State the assumptions explicitly. Share is share of a 4-brand universe, not the true market |
| 11 | **Undefined measures** | Units = sales | Units could be shipments, retail sales, or registrations. Tier order is inferred from the names | Ask (see below) |

## 5. Directions for further inquiry

**Questions to ask the data owner**
1. What is a "unit": shipment, retail sale, or registration? Is there a reporting lag, and do recent months get revised upward?
2. Is this the whole market, or four tracked brands? Is Barefoot a real competitor or an "All Other" bucket?
3. Are the four products price tiers, and do prices differ by brand? That decides whether dollar share would differ from unit share.
4. Is the state split real in the production data? If yes, what is the right baseline: population, dealer count, or the category's installed base?
5. Domain hunch, offered as a guess only: the state ranking (FL far ahead, then TX, MI, MN, NC, WI), the June peak, and roughly 250k units a year look a lot like US recreational-boat retail registration data. If that is the domain, registration lag and state reporting gaps are the first data-quality issues to ask about.

**Analyses worth building next**
1. **Share-shift monitor:** monthly decomposition of each brand's unit change into market effect + share effect (started in `reports/tables/h1_change_decomposition.csv`). Report rolling-12-month and YTD vs LYTD views, never raw month-over-month.
2. **Source of share:** who gains from whom. In this synthetic file the answer is "everyone from Barefoot", because it is the plug. In real data, a switching or correlation matrix of monthly share changes is a cheap first pass.
3. **Tier migration:** is Call volume trading up to Top Shelf or down to Rail? In this file Top Shelf's monthly changes mirror Rail's (r = −0.61) and Premium's (−0.57) more than Call's (−0.40). Call's decline is a slow drift, not a step change, so ask whether a tier was redefined.
4. **Forecasting:** the total is a deterministic seasonal curve times an annual level (2026 FY ≈ 232k). Share changes show no momentum (lag-1 autocorrelation of monthly changes is −0.06 to 0.18, none significant over 77 months), so a last-value forecast for share is the honest baseline. Any trend model should beat it in a backtest before anyone trusts it.
5. **Geographic white space (real data only):** state share vs the national share (location quotient), and penetration vs a population or installed-base denominator.
6. **Automated data-quality guards** for a production pipeline:
   - grid completeness;
   - totals reconcile across levels;
   - small-cell suppression;
   - zero vs missing;
   - partial-period flag on the latest year;
   - alerts when a share moves more than N points in a month.
7. **Dashboard design:** KPI tiles for YTD units, YoY %, share, and share change in points. Show rolling-12 trend lines for share and tier mix, a seasonality-aware month-vs-same-month-last-year chart, and suppression notes on any cut below the volume threshold.

## 6. Reproduce

```bash
pip install pandas numpy matplotlib
python analysis/eda.py                # writes reports/figures/*.png and reports/tables/*.csv
```

| Output | Contents |
|---|---|
| `reports/tables/annual_vs_h1.csv` | Full-year vs H1 totals and the naive vs correct YoY |
| `reports/tables/manufacturer_share_monthly.csv` | Monthly share by brand |
| `reports/tables/manufacturer_annual_h1.csv` | Annual and H1 units by brand |
| `reports/tables/h1_change_decomposition.csv` | Market vs share effect |
| `reports/tables/product_share_monthly.csv` | Monthly tier mix |
| `reports/tables/state_weights.csv` | Fixed state allocation |
| `reports/tables/block_rounding.csv` | Observed vs implied block totals (rounding loss) |
