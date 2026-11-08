# Building the dashboard in Tableau Public

This folder holds the data and the recipe for rebuilding the HTML dashboard (`dashboard/index.html`) in Tableau Public. Budget about an hour.

**Why there's no ready-made `.twbx` here.** Tableau's packaged workbook (`.twbx`) is a zip of workbook XML plus data. It is normally produced by Tableau itself. Tableau isn't available in the environment that built this repo, so a hand-written workbook couldn't be opened and tested, and untested workbook XML often fails to load. Building it yourself from the steps below also gives you a workbook you can explain in an interview. Once you publish, your Tableau Public profile can give you the `.twbx` (see step 7).

## 1. The data file

`market_share_tableau.csv`: 63,648 rows, one per month × brand × tier × state. It holds the same numbers as `data/market_share_synthetic.csv`, plus helper columns:

| Column | Type | What it's for |
|---|---|---|
| Month Date | Date | First day of the month. Use this for every time axis |
| Interval | String | Original `YYYY-MM` label |
| Year, Month Num | Number | Grouping and seasonality |
| Half | String | `H1`/`H2`, for like-for-like comparisons with 2026 |
| Partial Year | Boolean | True for 2026 (Jan–Jun only) |
| Manufacturer, Brand Order | String, Number | Brand, and a sort key (Valley Central 1 … Barefoot 4) |
| Product, Tier Order | String, Number | Tier, and a sort key (Rail 1, Call 2, Premium 3, Top Shelf 4) |
| State, Region | String | State code and US Census region |
| Units | Number | Units |
| **Units Year Earlier** | Number | Units for the same brand × tier × state 12 months earlier. Blank in 2020 |

`Units Year Earlier` does the heavy lifting. Filter Month Date to any period, and `SUM([Units Year Earlier])` is automatically the same months a year before. Year-on-year comparisons need no table calculations.

## 2. Connect

- **In the browser (no install):** sign in at [public.tableau.com](https://public.tableau.com), start a new viz from the Create menu, and upload the CSV when it asks for data.
- **Tableau Public desktop (free download):** Connect → *To a File* → *Text file* → pick the CSV.

Then check data types in the data pane:
- Month Date should show the date icon.
- State: right-click → *Geographic Role* → *State/Province*.
- Units and Units Year Earlier should be measures.

## 3. Parameter and calculated fields

**Parameter:** create `Min Units` (Integer, current value 50, range 0–500, step 10). Right-click it → *Show Parameter*.

**Calculated fields** (*Analysis → Create Calculated Field*). Paste each one exactly:

```
// Share of Units  — table calc: Compute Using → Manufacturer (brand share) or Product (tier mix)
SUM([Units]) / TOTAL(SUM([Units]))

// Units Change %  — same months a year earlier; blank for 2020
IF SUM([Units Year Earlier]) > 0 THEN SUM([Units]) / SUM([Units Year Earlier]) - 1 END

// Low Volume
SUM([Units]) < [Min Units] OR SUM([Units Year Earlier]) < [Min Units]

// Units Change % (safe)  — hides rounding noise in tiny cells
IF NOT [Low Volume] THEN [Units Change %] END

// Share Change (pts)  — table calc, Compute Using → Manufacturer
SUM([Units]) / TOTAL(SUM([Units]))
  - SUM([Units Year Earlier]) / TOTAL(SUM([Units Year Earlier]))

// Market Effect  — table calc, Compute Using → Manufacturer
(TOTAL(SUM([Units])) - TOTAL(SUM([Units Year Earlier])))
  * SUM([Units Year Earlier]) / TOTAL(SUM([Units Year Earlier]))

// Share Effect  — table calc, Compute Using → Manufacturer
TOTAL(SUM([Units])) * ( SUM([Units]) / TOTAL(SUM([Units]))
  - SUM([Units Year Earlier]) / TOTAL(SUM([Units Year Earlier])) )

// Rolling 12 Units  — table calc along Month Date
WINDOW_SUM(SUM([Units]), -11, 0)

// Brand Filter  — use as a table-calc filter so hiding a brand doesn't change other brands' shares
LOOKUP(ATTR([Manufacturer]), 0)
```

Market Effect + Share Effect = each brand's unit change. The split is the same one used in `REPORT.md` and the HTML dashboard.

**Colours** (to match the HTML dashboard): on any sheet, click *Color* → *Edit Colors* and assign these. In Tableau Public desktop you can type the hex values.

| Brand | Hex | Tier | Hex |
|---|---|---|---|
| Valley Central | `#2a78d6` | Rail | `#e87ba4` |
| Neptune | `#eb6834` | Call | `#008300` |
| Cornfield | `#1baf7a` | Premium | `#6250d6` |
| Barefoot | `#eda100` | Top Shelf | `#e34948` |

Sort Manufacturer by *Brand Order* (right-click → *Sort* → *Field* → Brand Order) and Product by *Tier Order*.

## 4. Sheets

1. **KPI: Units.** Text mark with `SUM(Units)` and `Units Change %`. Format the change as a percentage. Add `Month Date` as a range filter.
2. **Brand share over time.**
   - Columns: `MONTH(Month Date)` (the green, continuous one).
   - Rows: `Share of Units`, Compute Using → Manufacturer.
   - Color: Manufacturer. Mark type Line. Label: line ends only.
3. **Tier mix over time.** Same as sheet 2, with Product on Color and Compute Using → Product.
4. **Seasonal curve by year.**
   - Columns: `MONTH(Month Date)` as a discrete month name.
   - Rows: `SUM(Units)`.
   - Color: `YEAR(Month Date)`, grey shades with 2026 in black.
5. **What drove the change.**
   - Rows: Manufacturer. Columns: Measure Values with only *Market Effect* and *Share Effect*.
   - Mark type Bar. Colour the two measures grey and dark grey.
   - Filter Month Date to a period in 2021 or later, e.g. Jan–Jun 2026. The bars then show that period against Jan–Jun 2025.
6. **Brand × tier table.**
   - Rows: Manufacturer, Product.
   - Measure Values: `SUM(Units)`, `Share of Units` (Compute Using → Manufacturer), `Units Change % (safe)`.
7. **State map.** Double-click State, put `SUM(Units)` on Color with a single-hue sequential palette, and Region on Detail. Caption it: *"Each state's slice is fixed in this data, so the map looks the same for every brand and tier."*

## 5. Dashboard

1. New Dashboard, fixed size 1200 × 1000 (Tableau Public works best with a fixed size).
2. Layout:
   - Title and the KPI sheet across the top.
   - Brand share | Tier mix.
   - What drove the change | Seasonal curve | State map.
   - Brand × tier table across the bottom.
3. Filters: show Month Date (range), Product, Region and State. On each one choose *Apply to Worksheets → All Using This Data Source*. Show the `Min Units` parameter.
4. Brands: add a highlight action (*Dashboard → Actions → Add Action → Highlight*, run on Select, target field Manufacturer). Clicking a brand anywhere then highlights it everywhere without changing shares.
5. Add a caption under the title with the traps:
   - 2026 is Jan–Jun only.
   - Compare with the same months a year earlier.
   - Barefoot is the remainder brand.

## 6. Checks that show you built it right

| View | Expected value |
|---|---|
| Month Date = Jan–Jun 2026, all brands: Units Change % | −1.3% |
| Same filter, Neptune: Market Effect / Share Effect | −466 / +5,475 (net +5,009) |
| Same filter, Barefoot: Units Change % | −52.2% |
| All months: Valley Central share | 40.8% |
| Jun 2026 only: Valley Central share | 44.7% |
| Year view of total units | 2026 bar (125,278) about half of 2025 (234,966). The partial-year trap, so label it |

## 7. Publish and get the `.twbx`

- **Desktop:** *File → Save to Tableau Public As…*, sign in, name it.
- **Browser:** use the publish button in the editor.
- Everything on Tableau Public is public. That's fine here because the data is synthetic.
- To get a `.twbx` file afterwards, open the viz on your profile and use the download button → *Tableau Workbook*. Allow downloads in the viz settings if you want others to have it too.
