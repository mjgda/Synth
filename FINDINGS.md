# Market Share Data: Findings

Analysis of the synthetic market-share dataset: 4 manufacturers × 4 product tiers × 50 states + DC, monthly from January 2020 to June 2026 (63,648 rows).

## TL;DR

- **The market is shrinking slowly and is highly seasonal.** Jan–Jun 2026 units are 1.3% below Jan–Jun 2025 and 7.2% below Jan–Jun 2020. June is four times January in every year.
- **The two largest brands are consolidating share.** From Jan–Jun 2020 to Jan–Jun 2026:
  - Valley Central rose from 38.3% to 43.8% (+5.5 pts).
  - Neptune rose from 28.6% to 33.6% (+5.0 pts).
  - Barefoot fell from 11.5% to 4.1% (−7.5 pts).
  - Cornfield fell from 21.6% to 18.5% (−3.0 pts).
- **Neptune has the momentum.** In the 12 months to June 2026 it added 7,922 units (+11.6%), 80% of it from share gains rather than market growth. In Jan–Jun 2026 it was the only brand to grow (+13.5% vs Jan–Jun 2025).
- **The mix is moving away from the Call tier.** Call fell from about 21% of units in early 2020 to about 6% in June 2026, while Top Shelf rose from about 19% to about 37%.
- **2026 is on track for about 232,000 units, −1.3% vs 2025.**
- **Several features of the data change how results should be read:**
  - 2026 has only six months.
  - Seasonality is strong.
  - Every brand has the same tier mix.
  - Every state gets a fixed share of every brand.
  - Small cells are heavily affected by rounding.

  Comparisons below are made like-for-like to account for these.

## 1. Market size and seasonality

| | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 |
|---|---:|---:|---:|---:|---:|---:|---:|
| Full-year units | 250,014 | 259,996 | 239,993 | 229,968 | 219,947 | 234,966 | *Jan–Jun only* |
| Jan–Jun units | 135,005 | 140,411 | 129,607 | 124,205 | 118,754 | 126,870 | 125,278 |
| Jan–Jun vs prior year | | +4.0% | −7.7% | −4.2% | −4.4% | +6.8% | −1.3% |

- **Trend:** the market peaked in 2021, declined through 2024, rebounded in 2025 and is slightly down in 2026 so far.
- **Like-for-like comparisons matter.** A full-year comparison would show 2026 down 47%, only because 2026 contains six months.
- **The seasonal curve is identical every year.** Monthly units relative to January:

| Jan | Feb | Mar | Apr | May | Jun | Jul | Aug | Sep | Oct | Nov | Dec |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1.00 | 1.25 | 2.00 | 2.75 | 2.50 | 4.00 | 3.25 | 3.00 | 2.00 | 1.50 | 1.00 | 0.75 |

  - January to June is always 54% of the year.
  - May always dips below April.
  - Month-over-month changes mostly reflect this curve, so I compare each period with the same months a year earlier.

## 2. Manufacturer share

### Long-term shift (Jan–Jun 2020 vs Jan–Jun 2026; market −7.2%)

| Brand | Share 2020 → 2026 | Unit change | From market size | From share |
|---|---|---:|---:|---:|
| Valley Central | 38.3% → 43.8% (+5.5 pts) | +3,129 | −3,725 | +6,854 |
| Neptune | 28.6% → 33.6% (+5.0 pts) | +3,489 | −2,784 | +6,273 |
| Cornfield | 21.6% → 18.5% (−3.0 pts) | −5,884 | −2,097 | −3,787 |
| Barefoot | 11.5% → 4.1% (−7.5 pts) | −10,461 | −1,122 | −9,339 |

Each brand's unit change is split into the part explained by the market shrinking and the part explained by its share moving.
- Valley Central and Neptune grew in units even though the market contracted.
- Barefoot's decline is almost entirely lost share.

### Last 12 months (Jul 2025–Jun 2026 vs the 12 months before; market +2.3%)

| Brand | Units | Unit change | From market size | From share | Share | Share change |
|---|---:|---:|---:|---:|---:|---:|
| Valley Central | 102,681 | +4,854 | +2,278 | +2,576 | 44.0% | +1.1 pts |
| Neptune | 76,060 | +7,922 | +1,587 | +6,335 | 32.6% | +2.7 pts |
| Cornfield | 41,349 | −2,528 | +1,022 | −3,550 | 17.7% | −1.5 pts |
| Barefoot | 13,284 | −4,937 | +424 | −5,361 | 5.7% | −2.3 pts |

- **Neptune is the clear gainer.** In Jan–Jun 2026 alone it added 5,009 units (+13.5%) and 4.4 share points versus Jan–Jun 2025.
- **Valley Central is flat in units** over the same period (−74).
- **Barefoot halved** (−52%).

### Barefoot behaves like the remainder

- **Barefoot is mechanically tied to the other three.** Valley Central, Neptune and Cornfield move by exactly −1, 0 or +1 share point each month. Barefoot takes whatever is left. Its monthly change correlates −0.56 to −0.62 with each of the others, while the other three are uncorrelated with one another.
- **Its largest swings are mechanical.** It moved ±3 points in Apr 2020, Jan 2021, Feb 2021, Jul 2021, Dec 2021, Nov 2023, Dec 2024 and Jan 2026, which are exactly the months when all three larger brands moved together.
- **Percentage growth exaggerates its moves.** It shows +234% in Jan–Jun 2025 and −52% a year later. Share points are the more reliable way to describe it.
- **Most share movement involves Barefoot.** About 70% of all month-to-month share movement involves it. Total movement over the period adds up to about 126 points, yet the largest net transfer between any two brands is only about 4 points. Brands trade share back and forth far more than the end-to-end change suggests.

## 3. Product tiers

| Share of units | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 (Jan–Jun) |
|---|---:|---:|---:|---:|---:|---:|---:|
| Rail | 29.1% | 35.5% | 26.9% | 21.4% | 21.8% | 27.8% | 29.3% |
| Call | 17.3% | 14.7% | 19.7% | 16.7% | 10.5% | 4.0% | 5.8% |
| Premium | 29.8% | 33.2% | 33.4% | 31.7% | 38.7% | 31.9% | 30.0% |
| Top Shelf | 23.8% | 16.5% | 20.1% | 30.1% | 29.1% | 36.4% | 34.9% |

- **Call has steadily declined since its May 2022 peak** (21.9%). Since then it is down 16.1 points.
- **Top Shelf took that volume.** It gained 17.0 points over the same period, while Rail (+1.1) and Premium (−2.0) were roughly flat.
- **The mix is trading up.** Assuming the tiers are price bands, buyers are moving to the top tier rather than down to the entry tier.
- **The tier mix is identical for every brand** in each month (within 0.1–0.2 points). Each brand's share is therefore the same in every tier, and tier-level differences between brands don't exist in this data.

## 4. Outlook for 2026

- **Market:**
  - **Method:** forecast the rest of the year as the January–June level times the seasonal curve. Tested on 2021–2025, this predicted July–December within 0.1% each year. The simpler "same month last year" approach missed by 3.8–8.4%.
  - **Forecast:** about **106,700 units** for July–December 2026, bringing the full year to **about 232,000 (−1.3% vs 2025)**. By month: Jul 30,167 · Aug 27,839 · Sep 18,557 · Oct 13,920 · Nov 9,276 · Dec 6,956.
- **Brand share:** carrying the latest share forward is the most accurate simple forecast.
  - **The trend line loses everywhere.** In backtests from 2022, a 12-month trend line was less accurate at every horizon: average error 0.72 vs 0.80 points one month ahead, 1.58 vs 2.02 at six months, and 2.22 vs 3.35 at twelve.
  - **The trend line also loses at a year out:** a 12-month average roughly ties the latest share there (2.17 vs 2.22).
  - **No momentum to extrapolate:** share changes from one month carry no information about the next, so recent trends should not be extended.

| Brand | Jul–Dec 2026 units | Share held at | Likely December share (80% range) |
|---|---:|---:|---|
| Valley Central | 47,700 | 44.7% | 42.7–47.8% |
| Neptune | 35,200 | 33.0% | 31.0–36.0% |
| Cornfield | 19,200 | 18.0% | 15.0–20.0% |
| Barefoot | 4,500 | 4.2% | 0.2–9.2% |

## 5. How the data is structured, and what that means for the analysis

The dataset decomposes almost exactly into four layers. Knowing this tells you which questions the data can answer:

| Feature | What I found | Implication |
|---|---|---|
| Market total | 10,000 × a yearly level × a fixed monthly curve, with no month-to-month noise. There is no dip in spring 2020. | Forecasting the total is straightforward. Real-world shocks are not represented. |
| Brand shares | Three brands move in whole-point steps; Barefoot is the remainder. | Barefoot's swings reflect the other brands, not its own performance. |
| Tier mix | One mix per month, applied to every brand. | Brand-by-tier comparisons add no information beyond brand and tier separately. |
| States | Each state gets a fixed slice of every brand, tier and month (Florida 16.2%, top four states 31.1%). | State results are national results scaled down. The slices don't follow population (California 3.4%; Alaska 1.4% vs Arizona 0.7%), so per-capita comparisons would mislead. |
| Rounding | State cells are rounded to whole units. That leaves 1,935 zero cells (3%, 80% of them Barefoot), and small brand-tier-month totals lose 3–17% of their volume. | Growth rates on small cells are unreliable. One cell grows 1 → 6 units (+500%). I aggregated before calculating rates. |
| Latest period | Data ends June 2026. | 2026 is compared with January–June of earlier years. |

**Outlier screen:** a standard outlier rule on raw units flags 8.8% of cells. All of them are expected combinations (the largest brand, Florida, June) rather than anomalies. Outliers are better judged on shares or on deviations from the expected allocation. On that basis, the only unusual events are Barefoot's 3-point monthly swings listed above.

**Data quality:**
- **Structure is clean:** the file is a complete grid (every month, brand, tier and state present), with no blanks, duplicates, negative values or gaps in the months.
- **Things to watch:** the partial final year, the zero cells, 14 brand-tier-month totals under 50 units, and the fixed state allocation.
- **"Market share" covers these four brands only.** It is share of the four-brand total, not of a wider market.

## 6. Questions and next steps

**Questions about the data:**
1. What does a unit represent: shipments, retail sales or registrations? If registrations, is there a reporting lag that revises recent months?
2. Is Barefoot a single brand, or an "all other" group?
3. Are the four tiers price bands, and do prices differ by brand? That determines whether value share would differ from unit share.
4. Would real data vary by state? If so, what is the right baseline for state comparisons: population, dealer count, or the category's installed base?
5. Is the data modelled on a real category? The state ranking (Florida far ahead, then Texas, Michigan, Minnesota, North Carolina and Wisconsin), the June peak and roughly 250,000 units a year resemble US recreational-boat sales.

**With real data, I would next:**
- **Track share monthly.** Report rolling-12-month and year-to-date figures, each split into market-size and share effects.
- **Measure switching directly.** Use switching or trade-in data to see which brands gain from which, rather than inferring it from share movements.
- **Check what replaced Call.** Look at whether Call buyers moved to Top Shelf or left the category, and whether a tier was redefined.
- **Benchmark states properly.** Compare each state's share with the national share and with an appropriate baseline, to find under-served markets.
- **Automate quality checks.** Run them on each data refresh: completeness, totals that reconcile, small-cell suppression, a flag for partial periods, and alerts for unusually large monthly share moves.
