# Home Chef Produce Scorecard — Full Session Handoff

## What This Is

An internal analytics dashboard for Home Chef's produce operations team. It tracks produce waste costs, cost-per-meal (CPM), ingredient shorts, purchase order waste rates, and corrective action records (CARs). Built in Python / Streamlit against a Google Sheets backend. All source data lives in a single Google Sheet; the app reads it on load and caches it.

---

## Current Stack

| Layer | Tool |
|---|---|
| Language | Python 3.11+ |
| UI framework | Streamlit ≥ 1.37.0 |
| Data | Google Sheets via `gspread` + `google-auth` |
| Charts | Plotly Express + Plotly Graph Objects |
| Data wrangling | pandas, numpy |
| Auth | Service account JSON (local) or `st.secrets["gcp_service_account"]` (Streamlit Cloud) |

**Google Sheet ID**: `1srGhRlY2Zk6r7fCnOcFsrCVfermL_gN5J47nqQEFhjg`
**Scopes**: `["https://www.googleapis.com/auth/spreadsheets.readonly"]`
**GitHub repo**: `https://github.com/joaquinsubi/produce-scorecard` (branch: `main`)
**Deployed on**: Streamlit Community Cloud — auto-deploys on push to `main`

---

## Design System

### Colors
```
HC_GREEN       = "#008600"   # Primary — good / low waste
HC_GREEN_DARK  = "#006D00"
HC_BLUEBERRY   = "#0B355A"   # Sidebar, secondary navy
HC_CREAM       = "#FEF9F5"   # Page background
HC_MELON       = "#F27045"   # Alert — high waste / bad
HC_WATER       = "#9CD9DB"
HC_ORANGE      = "#FFB046"
HC_LEMON       = "#FFDE6F"   # Mid-range / caution
HC_GRAPE       = "#9F5E87"
HC_GRAY        = "#4A4A4A"   # Body text
HC_BORDER      = "#E6E0D8"   # Card / chart borders
HC_MUTED       = "#7A7A7A"   # Secondary text, axis labels

HC_PALETTE = [HC_GREEN, HC_MELON, HC_BLUEBERRY, "#00809C",
              HC_ORANGE, HC_GRAPE, HC_LEMON, HC_WATER]
```

### Fonts
- **Headings / KPI values**: Bree Serif (Google Fonts) — Georgia fallback
- **Body / labels / axes**: Karla (Google Fonts) — Work Sans / system-ui fallback
- Import URL: `https://fonts.googleapis.com/css2?family=Bree+Serif&family=Karla:wght@400;600;700;800&family=Work+Sans:wght@400;600;700&display=swap`

### Streamlit Theme (`.streamlit/config.toml`)
```toml
[theme]
base = "dark"
primaryColor = "#008600"
backgroundColor = "#FEF9F5"
secondaryBackgroundColor = "#FFFFFF"
textColor = "#4A4A4A"
```
`base = "dark"` forces consistent rendering for all users; CSS injection overrides it toward the cream aesthetic.

### Page Config
```python
st.set_page_config(
    page_title="Produce Scorecard — Home Chef",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded",
)
```

### Visual Treatment
- All Plotly charts: white background, `#E6E0D8` 1px border, 16px border-radius, subtle box-shadow
- KPI cards: white background, `#E6E0D8` 1px border, 16px border-radius, min-height 140px, padding 22px 24px 20px
- Sidebar: `#0B355A` background
- Page max-width: 1480px

---

## Constants

```python
FULL_WASTE_THRESHOLD = 0.95   # PO lines >= 95% wasted are flagged "fully wasted"

FACILITY_MAP = {              # Applied only in Shorts Log parsing
    "chicago midway": "Chicago",
    "chicago":        "Chicago",
    "skyview":        "Skyview",
    "san bernardino": "San Bernardino",
    "baltimore":      "Baltimore",
}
```

---

## Data Sources — Full Column Mappings

All sheets: header at row 0, data from row 1+. Column indices are **0-based**.

---

### Sheet 1: `WMS-Logged YTD`
The Waste Management System log. **Contains only waste events** — rows exist only when produce was logged as wasted. This is the critical architectural constraint: ingredients that were received but NOT wasted have zero rows here.

| Col Index | Field Name | Type | Notes |
|---|---|---|---|
| 0 | `created_date` | datetime | Drop row if NaT |
| 2 | `lot_id` | string | |
| 4 | `ingredient_id` | string | |
| 5 | `ingredient_name` | string | |
| 6 | `uom` | string | Unit of measure |
| 7 | `quantity` | float | **Negate on load** — sheet stores removals as negative; flip to positive |
| 9 | `waste_reason` | string | |
| 10 | `waste_reason_detail` | string | |
| 12 | `po_number` | string | |
| 13 | `received_qty` | float | Received qty for this lot |
| 14 | `menu_ship_date` | datetime | Primary date key for all filtering |
| 15 | `waste_cost` | float | **Negate on load** — same sign convention as quantity |
| 16 | `facility` | string | Strip whitespace |
| 17 | `is_rth` | string | "RTH" or "Non-RTH" |

**Computed column**: `week = (menu_ship_date - dayofweek_offset).strftime("%Y-%m-%d")` — Monday of the week

---

### Sheet 2: `Total Meals`
Meal bag counts per facility per week. Used only for CPM calculation.

| Col Index | Field Name | Type | Notes |
|---|---|---|---|
| 0 | `menu_ship_date` | datetime | Drop row if NaT |
| 1 | `facility` | string | Strip whitespace |
| 2 | `is_rth` | string | |
| 3 | `total_meals` | float | Fill NaN → 0 |

---

### Sheet 3: `Menus`
Used only to populate the sidebar "Pick" week selector.

| Col Index | Usage |
|---|---|
| 1 | Menu ship week dates — parsed to datetime, deduplicated, sorted; filtered to only those with WMS data |

---

### Sheet 4: `Shorts Logs`
Ingredient shortage incidents. Only Produce category rows are kept.

| Col Index | Field Name | Type | Notes |
|---|---|---|---|
| 2 | `facility` | string | Normalized via FACILITY_MAP (case-insensitive) |
| 4 | `menu_ship_week` | datetime | Drop row if NaT |
| 6 | `shorted_ingredient` | string | Strip whitespace |
| 7 | `short_reason` | string | Strip whitespace |
| 11 | `brand` | string | Vendor / brand |
| 23 | `category` | string | **Filter**: keep only `category.lower() == "produce"` |

**Computed column**: `week` (same ISO week formula as WMS)

---

### Sheet 5: `Purchase Orders`
Used for total spend (case cost) to compute "% of cost wasted." Parsed via manual row iteration because rows with invalid case_cost are silently skipped.

| Col Index | Field Name | Type | Notes |
|---|---|---|---|
| 0 | `po_number` | string | |
| 1 | `facility` | string | |
| 2 | `ingredient_id` | string | |
| 10 | `menu_ship_week` | datetime | |
| 13 | `case_cost` | float | Strip "$" and commas; skip entire row if parse fails |

**Output DataFrame** `po_costs_df`: columns `[po_number, ingredient_id, menu_ship_week, facility, case_cost]`

---

### Sheet 6: `Received_vs_Wasted`
**Source of truth for waste percentages.** Has a row for every PO line received, including POs where nothing was wasted. This is what makes ingredient-level waste % trustworthy — WMS alone would always show 100% because it only contains waste events.

| Col Index | Field Name | Type | Notes |
|---|---|---|---|
| 0 | `menu_ship_week` | datetime | |
| 1 | `facility` | string | |
| 2 | `ingredient_id` | string | Strip whitespace |
| 3 | `po_number` | string | Strip whitespace; drop row if blank |
| 5 | `total_received` | float | Strip "$" and commas; fill NaN → 0 |
| 6 | `total_wasted` | float | Same cleaning |
| 7 | `pct_wasted_rvw` | float | Strip "%"; stored as 0–100 scale (e.g. "21%" → 21.0); can exceed 100 |

**Critical**: Multiple rows can exist per `po_number + ingredient_id` (e.g., one per facility). Before joining to WMS, you MUST aggregate RVW by `(po_number, ingredient_id)` summing received and wasted. Do NOT `drop_duplicates()` — that picks an arbitrary row and can inflate percentages to 100%.

---

### Sheet 7: `CARs`
Corrective Action Records — customer complaints escalated to responsible vendors. Only Produce category rows are kept.

| Col Index | Field Name | Type | Notes |
|---|---|---|---|
| 0 | `investigation_number` | string | CAR identifier |
| 4 | `report_date` | datetime | Date customer reported the incident |
| 5 | `meal` | string | Meal ID and name |
| 6 | `ingredient_name_raw` | string | "Ingredient ID – Name" combined; fallback only |
| 14 | `po_numbers` | string | One or multiple PO numbers (free text) |
| 15 | `supplier` | string | Vendor / supplier name |
| 16 | `ship_week` | datetime | Drop row if NaT |
| 25 | `ingredient_id` | string | Clean numeric ingredient ID — use this for joins, not col 6 |
| 26 | `category` | string | **Filter**: keep only `category == "Produce"` (exact, case-sensitive) |
| 27 | `facility` | string | Cleaned facility name — use this, not col 8 (col I, uncleaned) |

**Post-parse**: left-join `ingredient_id → ingredient_name` from WMS lookup. Fall back to `ingredient_name_raw` (col 6) if no WMS match.

---

## Data Transformation Logic

### Week Normalization (applies to all sheets)
```python
week = (date_col - pd.to_timedelta(date_col.dt.dayofweek, unit="D")
       ).dt.normalize().dt.strftime("%Y-%m-%d")
```
Gives the Monday of any date's week as a sortable `"YYYY-MM-DD"` string.

For display, reformat to `"Mmm D"` stripping leading zeros:
```python
pd.to_datetime(week_col).dt.strftime("%b %d").str.replace(r" 0(\d)$", r" \1", regex=True)
# "May 01" → "May 1"
```

### CPM (`build_cpm`)
```
1. Group WMS by (facility, menu_ship_date) → sum waste_cost
2. Group Meals by (facility, menu_ship_date) → sum total_meals
3. Left-join waste onto meals on (facility, menu_ship_date)
4. cpm = waste_cost / total_meals  (replace 0 with NaN to avoid ÷0)
```
Always divide summed totals — do not average per-week CPM ratios.

### PO Analysis (`build_po_analysis`)
```
Input: date-filtered WMS (f) + full unfiltered RVW (rvw_df)

Step 1 — Aggregate WMS by (po_number, ingredient_id, ingredient_name):
  facility         → first value
  menu_ship_date   → first value
  waste_cost       → sum
  waste_reason     → mode (most frequent; "" if no mode)
  n_lots           → count of unique lot_id
  wms_waste_qty    → sum(quantity)
  wms_recv_qty     → sum(received_qty)

Step 2 — Aggregate RVW by (po_number, ingredient_id):
  total_received   → sum
  total_wasted     → sum
  pct_wasted_rvw   → total_wasted / total_received * 100, clipped 0–100

Step 3 — Left-join Step 2 into Step 1 on (po_number, ingredient_id)
  received_qty  = total_received from RVW  (fallback: wms_recv_qty)
  waste_qty     = total_wasted from RVW    (fallback: wms_waste_qty)
  pct_wasted    = pct_wasted_rvw from RVW  (fallback: wms_waste_qty/wms_recv_qty*100)

Step 4 — clip pct_wasted to max 100
Step 5 — full_po_wasted = (pct_wasted >= 95)
```

### Ingredient-Level % Wasted (PO tab bar chart)
Different from per-PO pct_wasted. For the ingredient bar chart:
```
1. Filter RVW to the same date range AND facility as the sidebar → rvw_win
2. Normalize ingredient_id: str(int(float(id))) when numeric (handles "17407.0" → "17407")
3. Group rvw_win by normalized ingredient_id
4. For each row: cap pct_wasted_rvw at 100
5. overall_pct_wasted = mean(capped values) per ingredient
```
This correctly includes POs where 0% was wasted, which WMS-only data never contains.

### Prior-Period Delta (Summary tab Total Waste Cost)
```python
span       = date_range[1] - date_range[0]
prior_start = date_range[0] - span
prior_end   = date_range[0] - timedelta(days=1)
prior_cost  = wms_df filtered to (prior_start, prior_end)["waste_cost"].sum()
delta_pct   = (current_cost - prior_cost) / prior_cost * 100
```

---

## Sidebar Filters

No form wrapper — every widget change immediately reruns the app (no "Apply" button).

### Date Range
```python
# Fiscal year: Feb 1 start; rolls back to prior year if current month < 2
fiscal_start = date(today.year, 2, 1) if today.month >= 2 else date(today.year - 1, 2, 1)
data_min = wms_df["menu_ship_date"].min().date()
data_max = wms_df["menu_ship_date"].max().date()
```

Pills widget — options: `["YTD", "4W", "8W", "12W", "Pick"]`, default: `"YTD"`

| Preset | date_range |
|---|---|
| YTD | `(fiscal_start, data_max)` |
| 4W | `(data_max − 4 weeks, data_max)` |
| 8W | `(data_max − 8 weeks, data_max)` |
| 12W | `(data_max − 12 weeks, data_max)` |
| Pick | Opens multiselect of individual menu weeks; `selected_weeks` = list of date objects |

Filter application for WMS:
```python
if selected_weeks is not None:    # Pick mode
    f = f[f["menu_ship_date"].dt.date.isin(selected_weeks)]
else:
    f = f[(f["menu_ship_date"].dt.date >= date_range[0]) &
          (f["menu_ship_date"].dt.date <= date_range[1])]
```

Same pattern applied to `meals_df`, `shorts_df`, `rvw_df`, and `cars_df` in each tab.

### Other Filters
| Widget | Options | Applied to |
|---|---|---|
| Facility | `["All"] + sorted(wms_df["facility"].unique())` | `f`, `meals_f`, `cars_f`, `rvw_win` |
| Waste Reason | `["All"] + sorted(wms_df["waste_reason"].unique())` | `f` only |
| RTH / Non-RTH | `["All"] + sorted(wms_df["is_rth"].unique())` | `f` only |

### Outside Filters
- **Refresh Data** button: `st.cache_data.clear()` + `st.rerun()` — forces a fresh pull from Sheets
- Shows: "Last pull: MMM DD · HH:MM AM/PM"

---

## Helper Functions

### `chart_base(fig, height=None) → Figure`
Applies Home Chef brand styling to any Plotly figure.
- Font: Karla 12px, `#4A4A4A`
- Backgrounds: `#FFFFFF` for both plot and paper
- Grid lines: `#EEE8DD`; axis lines: `#E6E0D8`; zeroline: False
- Title: Bree Serif 15px, left-aligned
- Legend: horizontal, below chart, no background
- Hover: unified mode, white background, Karla 12px
- Margins: `t=48, b=28, l=52, r=24`

### `kpi_card(label, value, delta=None, delta_positive=None, help_text=None) → str`
Returns an HTML string. Render with `st.markdown(kpi_card(...), unsafe_allow_html=True)` inside a column.
- Card: white bg, `#E6E0D8` 1px border, 16px radius, min-height 140px
- Label: Karla 10.5px bold uppercase, `#7A7A7A`
- Value: Bree Serif 32px, `#1A1A1A`
- Delta badge colors:
  - `delta_positive=True` → `rgba(0,134,0,0.12)` bg, `#008600` text (good)
  - `delta_positive=False` → `rgba(242,112,69,0.12)` bg, `#F27045` text (bad)
  - `delta_positive=None` → `rgba(74,74,74,0.08)` bg, `#7A7A7A` text (neutral)

### `section_head(eyebrow, title) → None`
Renders a ruled section divider via `st.markdown`. The `eyebrow` parameter is accepted for call-site compatibility but not rendered.
- 1px `#E6E0D8` top border, 28px padding-top, 36px margin-top, 16px margin-bottom
- Title: Bree Serif 22px, `#1A1A1A`

### `fmt_weeks(df, col="week") → pd.DataFrame`
Sorts df by the given column (expects `"YYYY-MM-DD"` strings), then reformats values to `"Mmm D"` display format, stripping leading zeros. **Overwrites the column in-place.**

When you need both sortable and display values, create the label separately before calling:
```python
df["week_label"] = (pd.to_datetime(df["week"])
    .dt.strftime("%b %d")
    .str.replace(r" 0(\d)$", r" \1", regex=True))
```

### `_nid(s) → str`
Normalizes ingredient_id for reliable joins between sheets (Google Sheets may return numbers as `"17407.0"` in one sheet and `"17407"` in another):
```python
try:
    return str(int(float(str(s).strip())))
except (ValueError, TypeError):
    return str(s).strip()
```

---

## Tab Structure

### Tab 0 — Summary

**KPI Row (4 chips)**

| Chip | Formula |
|---|---|
| Total Waste Cost | `f["waste_cost"].sum()` with prior-period % delta |
| Overall CPM | `total_waste_cost / total_matched_meals` |
| Avg Shorts / Week | `len(shorts_f) / shorts_f["week"].nunique()` |
| % of Cost Wasted | `total_waste_cost / po_costs_df_filtered["case_cost"].sum() * 100` |

**Charts (top to bottom)**:
1. Top 10 shorted ingredients (horizontal bar, HC_CREAM→HC_MELON) + Shorts by site (horizontal bar, HC_CREAM→HC_BLUEBERRY) — 2 col, 360px
2. Waste cost by facility (horizontal bar) + CPM by facility (horizontal bar) — 2 col, 360px, HC_GREEN→HC_LEMON→HC_MELON gradient
3. Top 10 ingredients by waste cost (horizontal bar, full width, HC_CREAM→HC_MELON) — 360px

---

### Tab 1 — Shorts Log

**KPI Row (4 chips)**: Total Produce Shorts · Most Shorted Ingredient · Top Short Reason · Top Vendor

**Charts**:
1. Top N shorted ingredients (horizontal bar, slider 10–50 default 20)
2. Short count by reason (vertical bar, HC_PALETTE discrete) — 2 col layout
3. Weekly produce shorts (line chart, HC_MELON, xaxis_type="category")
4. Short reason breakdown per site (heatmap, facility × reason, white→HC_LEMON→HC_MELON)
5. **Ingredient deep dive** (collapsed expander):
   - Selectbox: pick an ingredient
   - 4 mini-KPIs: Total Shorts, Facilities Affected, Top Reason, Weeks Affected
   - Weekly bar + by-facility bar + by-reason bar
   - Grouped detail table (week, facility, reason, brand, count)

---

### Tab 2 — Waste Trends

**General** (expanded expander):
1. Waste cost by facility (horizontal bar) + Waste cost by reason (vertical bar, note: negative = correction) — 2 col
2. Weekly waste cost by facility (stacked bar, barmode="stack", xaxis_type="category", HC_PALETTE)
3. Weekly CPM line (all facilities combined, HC_MELON, markers w/ white fill)
4. CPM by facility (horizontal bar) + CPM summary table — 2 col
5. CPM heatmap (facility × week, HC_GREEN→HC_LEMON→HC_MELON)

**By Ingredient** (collapsed expander):
1. Top N by waste cost (stacked horizontal bar, facility breakdown, HC_PALETTE, slider 10–50)
2. Top N by total spend from PO sheet (stacked horizontal bar, same ingredient order + color map)

---

### Tab 3 — Purchase Orders

**KPI Row (4 chips)**

| Chip | Source | Formula |
|---|---|---|
| Total PO Lines | `rvw_win` | Count unique (po_number, ingredient_id) combos |
| Avg % of Line Wasted | `rvw_win` | `mean(clip(pct_wasted_rvw, 0, 100))` |
| Fully Wasted Lines | `po_df` | Count where `pct_wasted >= 95%` |
| Cost of Fully Wasted Lines | `po_df` | Sum of waste_cost where fully wasted |

**Alert section** (shown only when n_fully_wasted > 0):
- 3 dropdowns: Facility, Ingredient, Reason
- Table: po_number, facility, ingredient_name, menu_ship_date, waste_qty, received_qty, pct_wasted (progress bar), waste_cost, n_lots, waste_reason

**Charts**:
1. Distribution of PO lines by % wasted (histogram, 20 bins, HC_GREEN; shaded zone 95–100% in HC_MELON 15% opacity labelled "Fully wasted zone")
2. Top 15 PO lines by waste cost (horizontal bar; color: full_po_wasted=True → HC_MELON, False → HC_GREEN)

**Ingredient section**:
- Slider: Top N (10–50, default 20)
- % of PO wasted bar (horizontal, HC_GREEN→HC_LEMON→HC_MELON gradient)
- Waste cost by week heatmap (ingredient × week, white→HC_LEMON→HC_MELON)
  - Row order: **descending** by overall_pct_wasted so highest-% ingredient is at top of both charts

---

### Tab 4 — Detail Table

Full-text search across ingredient_name, facility, waste_reason, waste_reason_detail.
3 dropdown filters: Facility, Reason, UOM.

Columns: created_date, facility, ingredient_name, uom, quantity, waste_reason, waste_reason_detail, menu_ship_date, waste_cost, is_rth
Sorted by created_date descending. Height 560px. CSV download button.

---

### Tab 5 — CARs

Filtered by sidebar date range + facility. Produce-only filter applied at parse time (col AA = "Produce").

**KPI Row (4 chips)**

| Chip | Formula |
|---|---|
| Total CARs | `len(cars_f)` |
| CARs / Week | `total_cars / cars_f["ship_week"].nunique()` |
| Most Affected Ingredient | `mode(ingredient_name)` — drops blanks/NaN before mode |
| Most Affected Vendor | `mode(supplier)` — drops blanks/NaN before mode |

**Charts**:
1. CARs by facility — weekly (stacked bar, barmode="stack", xaxis_tickangle=-35, HC_PALETTE)
2. Top 15 ingredients by CAR count (stacked horizontal bar, facility breakdown, HC_PALETTE) + Top 15 vendors by CAR count (same) — 2 col
3. CAR detail table — 3 labeled dropdowns (Facility, Ingredient, Supplier); columns: CAR #, Ship Week, Report Date, Facility, Ingredient, Vendor, PO Numbers, Meal; sorted by ship_week descending; height 500px

---

## Critical Data Architecture Notes

1. **WMS = waste events only.** If an ingredient was received but not wasted, it has zero WMS rows. Using WMS alone to compute "% wasted" always gives 100% for any ingredient that appears — because by definition every row is a waste event.

2. **RVW is the source of truth for received vs. wasted quantities.** `Received_vs_Wasted` has a row for every PO received, including 0%-wasted POs. Always pull received/wasted quantities from RVW, not WMS.

3. **Ingredient-level % = mean of capped per-PO percentages — not summed quantities.** A PO with wasted > received (data entry error, UOM mismatch) can show > 100% in the raw sheet. Cap each row at 100% before averaging. Do not sum raw received/wasted across all POs for an ingredient and then divide — this produces a global ratio that misrepresents the distribution.
   - Correct: `mean(clip(pct_wasted_rvw[i], 0, 100) for i in all POs for ingredient)`
   - Incorrect: `sum(total_wasted) / sum(total_received)` across POs

4. **Multiple RVW rows per PO + ingredient.** The same PO can ship to multiple facilities, producing one RVW row per facility. Aggregate by `(po_number, ingredient_id)` before joining to WMS. Using `drop_duplicates()` picks an arbitrary row and breaks percentages.

5. **WMS quantity and waste_cost are stored negative.** Negate both on parse. This means corrections (positive in the sheet) become negative after negation, which correctly reduces waste totals when summed.

6. **Fiscal year starts Feb 1.** YTD = Feb 1 of current year to today. If current month is January, roll back to Feb 1 of the prior calendar year.

7. **Week normalization is Monday-anchored.** Subtract `dayofweek` (0=Mon…6=Sun) to get the Monday of any week. Store as `"YYYY-MM-DD"` for sorting/grouping; format as `"Mmm D"` for chart axes.

8. **Facility names normalized only in Shorts.** The Shorts sheet has inconsistent names ("chicago midway", "chicago", etc.) — apply `FACILITY_MAP` case-insensitively. All other sheets are expected to already have canonical names: Chicago, Skyview, San Bernardino, Baltimore.

9. **Ingredient IDs may be stored as floats in some sheets.** Google Sheets can return `"17407.0"` instead of `"17407"`. Normalize before joining: `str(int(float(id)))`.

10. **CARs ingredient name lookup:** CARs col 6 (G) has combined "ID – Name" text; col 25 (Z) has the clean numeric ingredient ID. Always use col 25 for the join key; fall back to col 6 text only if the WMS lookup fails.

11. **`fmt_weeks()` overwrites the column.** If you need both a sort key and a display label, create the label column first, then sort on the original.

---

## Credentials & Deployment

- **Local dev**: reads credentials from `/Users/joaquinsubijana/Downloads/produce-scorecard-36234099db1a.json`
- **Streamlit Cloud**: reads from `st.secrets["gcp_service_account"]` (service account dict)
- **Password gate**: `check_password()` function; password stored in `st.secrets["app_password"]`; empty password allowed by default (effectively open when no secret is set)
- **Cache**: `@st.cache_data` on `load_raw()` — "Refresh Data" button calls `st.cache_data.clear()` + `st.rerun()`
- **Deploy**: `git add app.py && git commit -m "..." && git push` — Streamlit Cloud auto-deploys from `main`
