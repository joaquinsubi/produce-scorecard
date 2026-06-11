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
**Local run**: `cd /Users/joaquinsubijana/produce-scorecard && streamlit run app.py`

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
- KPI cards: white background, `#E6E0D8` 1px border, 16px border-radius, **fixed `height: 160px`** (this ensures all chips in a row are the same height — do NOT change to `min-height` or `height:100%` as that requires a fragile flex chain through Streamlit's DOM and breaks chart containers)
- Sidebar: `#0B355A` background
- Page max-width: 1480px
- Section heads (`section_head()`): top border only — **do NOT add `st.divider()` before a `section_head()` call** as the combined spacing looks like a double break

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

**Important**: The CARs sheet has TWO header rows before actual data (row 0 = Google Sheets import metadata, row 1 = column letter labels). The parser uses `raw[1:]` which makes that label row the first DataFrame row — it gets filtered out by the category check and NaT drop, so actual data still parses correctly from row 2+.

---

### Sheet 1: `WMS-Logged YTD`
The Waste Management System log. **Contains only waste events** — rows exist only when produce was logged as wasted.

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
**Source of truth for waste percentages.** Has a row for every PO line received, including POs where nothing was wasted.

| Col Index | Field Name | Type | Notes |
|---|---|---|---|
| 0 | `menu_ship_week` | datetime | |
| 1 | `facility` | string | |
| 2 | `ingredient_id` | string | Strip whitespace |
| 3 | `po_number` | string | Strip whitespace; drop row if blank |
| 5 | `total_received` | float | Strip "$" and commas; fill NaN → 0 |
| 6 | `total_wasted` | float | Same cleaning |
| 7 | `pct_wasted_rvw` | float | Strip "%"; stored as 0–100 scale (e.g. "21%" → 21.0); can exceed 100 |

**Critical**: Multiple rows can exist per `po_number + ingredient_id` (e.g., one per facility). Before joining to WMS, you MUST aggregate RVW by `(po_number, ingredient_id)` summing received and wasted. Do NOT `drop_duplicates()`.

---

### Sheet 7: `CARs`
Corrective Action Records. Only Produce category rows are kept. **Note: this sheet has TWO header rows before data.**

| Col Index | Col Letter | Field Name | Type | Notes |
|---|---|---|---|---|
| 2 | C | `report_date` | datetime | Date customer reported the incident |
| 3 | D | `meal` | string | Meal ID and name |
| 6 | G | `ingredient_name_raw` | string | Fallback ingredient name only |
| 13 | N | `po_numbers` | string | One or multiple PO numbers (free text) |
| 14 | O | `supplier` | string | Vendor / supplier name |
| 15 | P | `ship_week` | datetime | **Drop row if NaT** — this is the primary date key |
| 24 | Y | `investigation_number` | string | CAR identifier |
| 25 | Z | `ingredient_id` | string | Clean numeric ingredient ID — use for joins |
| 26 | AA | `category` | string | **Filter**: keep only `category.lower() == "produce"` (case-insensitive) |
| 27 | AB | `facility` | string | Cleaned facility name |

**Post-parse**: left-join `ingredient_id → ingredient_name` from WMS lookup. Fall back to `ingredient_name_raw` (col G) if no WMS match.

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
```
1. Filter RVW to the same date range AND facility as the sidebar → rvw_win
2. Normalize ingredient_id via _nid() (handles "17407.0" → "17407")
3. Group rvw_win by normalized ingredient_id
4. Cap pct_wasted_rvw at 100 per row
5. overall_pct_wasted = mean(capped values) per ingredient
```

### Prior-Period Delta (Summary tab Total Waste Cost)
```python
span        = date_range[1] - date_range[0]
prior_start = date_range[0] - span
prior_end   = date_range[0] - timedelta(days=1)
prior_cost  = wms_df filtered to (prior_start, prior_end)["waste_cost"].sum()
delta_pct   = (current_cost - prior_cost) / prior_cost * 100
```

---

## Sidebar Filters

No form wrapper — every widget change immediately reruns the app.

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

### Other Filters
| Widget | Options | Applied to |
|---|---|---|
| Facility | `["All"] + sorted(wms_df["facility"].unique())` | `f`, `meals_f`, `cars_f`, `rvw_win` |
| Waste Reason | `["All"] + sorted(wms_df["waste_reason"].unique())` | `f` only |
| RTH / Non-RTH | `["All"] + sorted(wms_df["is_rth"].unique())` | `f` only |

**Ingredient Lookup tab uses `ing_base`** — a separate filtered copy of WMS that applies only the date and facility filters (not reason or RTH), so all waste reasons are visible when looking up a specific ingredient.

### Refresh Button
`st.cache_data.clear()` + `st.rerun()` — forces a fresh pull from Sheets.

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
- Card: white bg, `#E6E0D8` 1px border, 16px radius, **`height: 160px`** (fixed — not min-height), `display:flex; flex-direction:column`
- Label: Karla 10.5px bold uppercase, `#7A7A7A`
- Value: Bree Serif 32px, `#1A1A1A`
- Delta badge colors:
  - `delta_positive=True` → `rgba(0,134,0,0.12)` bg, `#008600` text (good)
  - `delta_positive=False` → `rgba(242,112,69,0.12)` bg, `#F27045` text (bad)
  - `delta_positive=None` → `rgba(74,74,74,0.08)` bg, `#7A7A7A` text (neutral)

### `section_head(eyebrow, title) → None`
Renders a ruled section divider via `st.markdown`. The `eyebrow` parameter is accepted but not rendered.
- 1px `#E6E0D8` top border, 20px padding-top, 20px margin-top, 12px margin-bottom
- Title: Bree Serif 22px, `#1A1A1A`
- **Do not call `st.divider()` immediately before `section_head()`** — the combined spacing reads as a double break.

### `fmt_weeks(df, col="week") → pd.DataFrame`
Sorts df by the given column (expects `"YYYY-MM-DD"` strings), then reformats values to `"Mmm D"` display format, stripping leading zeros. **Overwrites the column in-place.**

### `_nid(s) → str`
Normalizes ingredient_id for reliable joins (defined at module level, available to all tabs):
```python
try:
    return str(int(float(str(s).strip())))
except (ValueError, TypeError):
    return str(s).strip()
```

---

## Tab Structure

Tab order: **Summary → Ingredient Lookup → Shorts Log → Waste Trends → Purchase Orders → Detail Table → CARs**

```python
tab_summary, tab_ingredient, tab_shorts, tab_trends, tab_po, tab_table, tab_cars = st.tabs([...])
```

---

### Tab 0 — Summary

**KPI Row (4 chips)** — no `st.divider()` after this row

| Chip | Formula |
|---|---|
| Total Waste Cost | `f["waste_cost"].sum()` with prior-period % delta |
| Overall CPM | `total_waste_cost / total_matched_meals` |
| Avg Shorts / Week | `len(shorts_f) / shorts_f["week"].nunique()` |
| % of Cost Wasted | `total_waste_cost / po_costs_df_filtered["case_cost"].sum() * 100` |

**Charts**: Top 10 shorted ingredients + Shorts by site (2 col) → Waste cost by facility + CPM by facility (2 col) → Top 10 ingredients by waste cost (full width)

---

### Tab 1 — Ingredient Lookup

A per-ingredient deep-dive. Uses `ing_base` (date + facility filtered, NOT reason/RTH filtered).

**Search**: Single `st.selectbox` with `index=None, placeholder="Type an ingredient name or ID…"`. Each option is formatted as `"Ingredient Name  ·  ID: 12345"` so Streamlit's native type-to-filter works on both name and ID. Nothing renders until a selection is made.

**KPI Row (5 chips)** — no `st.divider()` after this row

| Chip | Source |
|---|---|
| Total Waste Cost | `ing_wms["waste_cost"].sum()` |
| Total Spend (POs) | `po_costs_df` filtered by date + facility + ingredient_id |
| % of Spend Wasted | `waste_cost / spend * 100` |
| Avg PO Waste % | `mean(ing_po["pct_wasted"])` with fully-wasted count as delta |
| Total Shorts | `len(ing_shorts)` with facilities-affected count as delta |

**Sections** (each introduced by `section_head()`):
1. Waste by facility — waste cost ($) + waste quantity (UOM) side by side
2. Trends & breakdown — weekly waste cost line + waste cost by reason
3. Purchase order lines — full PO table with received, wasted, % wasted (progress bar), fully-wasted checkbox
4. Shorts — only rendered if `not ing_shorts.empty`: weekly bar + reason bar + detail table
5. CARs — only rendered if `not ing_cars.empty`: detail table

---

### Tab 2 — Shorts Log

**KPI Row (4 chips)** — no `st.divider()` after this row: Total Produce Shorts · Most Shorted Ingredient · Top Short Reason · Top Vendor

**Charts**: Top N shorted ingredients + Short count by reason (2 col) → Weekly produce shorts (line) → Reason breakdown per site (heatmap) → **Ingredient deep dive** (collapsed expander with 4 mini-KPIs, charts, and grouped table)

---

### Tab 3 — Waste Trends

**General** (expanded expander): facility cost bar + reason bar → weekly stacked bar by facility → weekly CPM line → CPM by facility bar + CPM table → CPM heatmap

**By Ingredient** (collapsed expander): Top N by waste cost (stacked bar, facility breakdown) + Total spend from PO sheet (same ingredient order)

---

### Tab 4 — Purchase Orders

**KPI Row (4 chips)** — no `st.divider()` after this row

| Chip | Source | Formula |
|---|---|---|
| Total PO Lines | `rvw_win` | Count unique (po_number, ingredient_id) |
| Avg % of Line Wasted | `rvw_win` | `mean(clip(pct_wasted_rvw, 0, 100))` |
| Fully Wasted Lines | `po_df` | Count where `pct_wasted >= 95%` |
| Cost of Fully Wasted Lines | `po_df` | Sum waste_cost where fully wasted |

**Alert section** (only when n_fully_wasted > 0): 3 dropdowns + table

**Charts**: % wasted histogram + Top 15 PO lines by cost (2 col) → ingredient % wasted bar + waste cost heatmap

---

### Tab 5 — Detail Table

Full-text search + 3 dropdown filters (Facility, Reason, UOM). All WMS columns. CSV export.

---

### Tab 6 — CARs

**KPI Row (4 chips)** — no `st.divider()` after this row: Total CARs · CARs/Week · Most Affected Ingredient · Most Affected Vendor

**Charts**: Weekly stacked bar by facility → Top 15 ingredients + Top 15 vendors (2 col) → Detail table with 3 dropdowns

---

## Critical Data Architecture Notes

1. **WMS = waste events only.** Using WMS alone to compute "% wasted" always gives 100% — every row is a waste event by definition. Always use RVW for received quantities.

2. **RVW is the source of truth.** `Received_vs_Wasted` has a row for every PO received, including 0%-wasted POs.

3. **Multiple RVW rows per PO + ingredient.** Aggregate by `(po_number, ingredient_id)` before joining. Never `drop_duplicates()`.

4. **Percentage wasted always clipped to 100.** Data entry errors can produce wasted > received. Cap at 100% before any averaging or display.

5. **WMS quantity and waste_cost are stored negative.** Negate both on parse. Corrections (positive in sheet) become negative after negation, correctly reducing waste totals.

6. **CARs category filter is case-insensitive.** The sheet stores "Produce" but use `.str.lower() == "produce"` to be resilient.

7. **CARs ship_week is column P (index 15).** The sheet has two header rows before data. If ship_week parses to all NaT, the `dropna` will empty the entire DataFrame — this is the failure mode if the column index is wrong.

8. **Fiscal year starts Feb 1.** If current month is January, roll back to Feb 1 of prior year.

9. **Week normalization is Monday-anchored.** Subtract `dayofweek` (0=Mon) to get Monday of the week. Store as `"YYYY-MM-DD"`; format as `"Mmm D"` for display.

10. **Facility names normalized only in Shorts.** All other sheets use canonical names: Chicago, Skyview, San Bernardino, Baltimore.

11. **Ingredient IDs may be stored as floats.** Google Sheets can return `"17407.0"` instead of `"17407"`. Always normalize with `_nid()` before joining across sheets.

12. **KPI card height must stay fixed at 160px.** Do not change to `min-height` or `height:100%` — those approaches require propagating flex through Streamlit's internal DOM wrappers, which also affects chart containers and causes charts to grow unboundedly on tab interaction.

13. **Never put `st.divider()` immediately before `section_head()`.** The section head already draws a 1px top border. The combination creates a visually jarring double-line break.

---

## Credentials & Deployment

- **Local dev**: reads credentials from `/Users/joaquinsubijana/Downloads/produce-scorecard-36234099db1a.json`
- **Streamlit Cloud**: reads from `st.secrets["gcp_service_account"]` (service account dict)
- **Password gate**: `check_password()` — password stored in `st.secrets["app_password"]`; empty password = open
- **Cache**: `@st.cache_data` on `load_raw()` with TTL 300s — "Refresh Data" button calls `st.cache_data.clear()` + `st.rerun()`
- **Deploy**: `git add app.py && git commit -m "..." && git push` — Streamlit Cloud auto-deploys from `main`
