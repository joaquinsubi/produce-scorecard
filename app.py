import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date, timedelta
import numpy as np

# ── CONFIG ────────────────────────────────────────────────────────────────────
CREDENTIALS_PATH = "/Users/joaquinsubijana/Downloads/produce-scorecard-36234099db1a.json"
SHEET_ID         = "1srGhRlY2Zk6r7fCnOcFsrCVfermL_gN5J47nqQEFhjg"
SCOPES           = ["https://www.googleapis.com/auth/spreadsheets.readonly"]

st.set_page_config(
    page_title="Produce Scorecard — Home Chef",
    page_icon="https://i.imgur.com/placeholder.png",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── PASSWORD GATE ─────────────────────────────────────────────────────────────
def check_password():
    if st.session_state.get("authenticated"):
        return True
    st.markdown('<p class="hc-title" style="margin-bottom:8px">Produce Scorecard</p>', unsafe_allow_html=True)
    pw = st.text_input("Password", type="password", placeholder="Enter team password")
    if pw:
        correct = st.secrets.get("app_password", "")
        if pw == correct:
            st.session_state["authenticated"] = True
            st.rerun()
        else:
            st.error("Incorrect password.")
    return False

if not check_password():
    st.stop()

# ── HOME CHEF DESIGN TOKENS ───────────────────────────────────────────────────
HC_GREEN      = "#008600"
HC_GREEN_DARK = "#006D00"
HC_BLUEBERRY  = "#0B355A"
HC_CREAM      = "#FEF9F5"
HC_MELON      = "#F27045"
HC_WATER      = "#9CD9DB"
HC_ORANGE     = "#FFB046"
HC_LEMON      = "#FFDE6F"
HC_GRAPE      = "#9F5E87"
HC_GRAY       = "#4A4A4A"
HC_BORDER     = "#E6E0D8"
HC_MUTED      = "#7A7A7A"

# Qualitative chart palette — HC brand colors in order
HC_PALETTE = [HC_GREEN, HC_MELON, HC_BLUEBERRY, "#00809C", HC_ORANGE, HC_GRAPE, HC_LEMON, HC_WATER]

CHART_FONT = dict(family="'Karla', 'Work Sans', system-ui, sans-serif", size=12, color=HC_GRAY)

# ── GLOBAL STYLES ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Bree+Serif&family=Karla:wght@400;600;700;800&family=Work+Sans:wght@400;600;700&display=swap');

/* ── page ── */
.stApp, .main .block-container { background: #FEF9F5 !important; }
html, body, [class*="css"] { font-family: 'Karla', 'Work Sans', system-ui, sans-serif; }

/* ── scorecard header ── */
.hc-title {
    font-family: 'Bree Serif', Georgia, serif;
    font-size: 36px;
    color: #1A1A1A;
    line-height: 1.1;
    margin: 0;
    letter-spacing: -0.01em;
}
.hc-eyebrow {
    font-family: 'Karla', sans-serif;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: #7A7A7A;
    margin: 6px 0 0;
}

/* ── KPI metric cards ── */
[data-testid="metric-container"] {
    background: #FFFFFF;
    border: 1.5px solid #E6E0D8;
    border-radius: 14px;
    padding: 20px 24px 16px 24px;
    box-shadow: 0 1px 2px rgba(11,53,90,0.06), 0 1px 1px rgba(11,53,90,0.04);
    transition: box-shadow 140ms cubic-bezier(0.22,0.61,0.36,1);
}
[data-testid="metric-container"]:hover {
    box-shadow: 0 6px 16px rgba(11,53,90,0.08), 0 2px 4px rgba(11,53,90,0.05);
}
[data-testid="stMetricValue"] {
    font-family: 'Bree Serif', Georgia, serif !important;
    font-size: 28px !important;
    color: #1A1A1A !important;
    line-height: 1.1 !important;
}
[data-testid="stMetricLabel"] {
    font-family: 'Karla', sans-serif !important;
    font-size: 10px !important;
    font-weight: 700 !important;
    letter-spacing: 0.12em !important;
    text-transform: uppercase !important;
    color: #7A7A7A !important;
}
[data-testid="stMetricDelta"] svg { display: none; }

/* ── sidebar ── */
section[data-testid="stSidebar"] {
    background: #0B355A !important;
}
section[data-testid="stSidebar"] * {
    color: #FEF9F5 !important;
}
section[data-testid="stSidebar"] .stSelectbox label,
section[data-testid="stSidebar"] .stRadio label,
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] small,
section[data-testid="stSidebar"] span {
    color: #FEF9F5 !important;
    font-family: 'Karla', sans-serif !important;
}
section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 {
    font-family: 'Bree Serif', Georgia, serif !important;
    color: #FEF9F5 !important;
}
section[data-testid="stSidebar"] hr {
    border-color: rgba(254,249,245,0.2) !important;
}
section[data-testid="stSidebar"] .stButton button {
    background: #008600 !important;
    color: #FFFFFF !important;
    border: none !important;
    border-radius: 999px !important;
    font-family: 'Karla', sans-serif !important;
    font-weight: 700 !important;
    transition: background 140ms cubic-bezier(0.22,0.61,0.36,1);
}
section[data-testid="stSidebar"] .stButton button:hover {
    background: #006D00 !important;
}
/* selectbox inputs on dark sidebar */
section[data-testid="stSidebar"] .stSelectbox div[data-baseweb="select"] > div {
    background: rgba(254,249,245,0.1) !important;
    border-color: rgba(254,249,245,0.3) !important;
    color: #FEF9F5 !important;
    border-radius: 8px !important;
}
/* radio buttons on dark sidebar */
section[data-testid="stSidebar"] [data-testid="stRadio"] > div {
    gap: 4px;
}
section[data-testid="stSidebar"] [data-testid="stRadio"] label {
    background: rgba(254,249,245,0.08) !important;
    border-radius: 6px;
    padding: 2px 8px;
    font-size: 12px !important;
}
section[data-testid="stSidebar"] [data-testid="stRadio"] [aria-checked="true"] + div {
    color: #008600 !important;
}

/* ── dividers ── */
hr { border-color: #E6E0D8 !important; margin: 16px 0 !important; }

/* ── tabs ── */
.stTabs [data-baseweb="tab-list"] {
    gap: 2px;
    border-bottom: 2px solid #E6E0D8;
    background: transparent;
}
.stTabs [data-baseweb="tab"] {
    font-family: 'Karla', sans-serif !important;
    font-weight: 700 !important;
    font-size: 13px !important;
    letter-spacing: 0.04em;
    color: #7A7A7A !important;
    border-radius: 8px 8px 0 0;
    padding: 8px 18px;
    border-bottom: 2px solid transparent;
    background: transparent;
    text-transform: uppercase;
}
.stTabs [aria-selected="true"] {
    color: #008600 !important;
    border-bottom: 2px solid #008600 !important;
    background: rgba(0,134,0,0.04) !important;
}

/* ── dataframe ── */
[data-testid="stDataFrame"] {
    border: 1px solid #E6E0D8 !important;
    border-radius: 12px !important;
    overflow: hidden;
}

/* ── download button ── */
.stDownloadButton button {
    background: transparent !important;
    color: #008600 !important;
    border: 2px solid #008600 !important;
    border-radius: 999px !important;
    font-family: 'Karla', sans-serif !important;
    font-weight: 700 !important;
    padding: 10px 24px !important;
    transition: all 140ms cubic-bezier(0.22,0.61,0.36,1);
}
.stDownloadButton button:hover {
    background: #008600 !important;
    color: #FFFFFF !important;
}

/* ── warning / info banners ── */
[data-testid="stAlert"] { border-radius: 12px !important; }

/* ── slider ── */
[data-testid="stSlider"] [data-baseweb="slider"] [role="slider"] {
    background: #008600 !important;
}
</style>
""", unsafe_allow_html=True)


def chart_base(fig, height=None):
    """Apply Home Chef brand styling to any Plotly figure."""
    layout = dict(
        font=CHART_FONT,
        plot_bgcolor="#FFFFFF",
        paper_bgcolor="#FEF9F5",
        title_font=dict(
            size=14, color="#1A1A1A",
            family="'Karla', 'Work Sans', sans-serif"
        ),
        xaxis=dict(
            gridcolor="#E6E0D8", linecolor="#E6E0D8",
            tickfont=dict(color=HC_GRAY, family="'Karla', sans-serif"),
            title_font=dict(color=HC_GRAY),
        ),
        yaxis=dict(
            gridcolor="#E6E0D8", linecolor="#E6E0D8",
            tickfont=dict(color=HC_GRAY, family="'Karla', sans-serif"),
            title_font=dict(color=HC_GRAY),
        ),
        legend=dict(
            font=dict(color=HC_GRAY, family="'Karla', sans-serif"),
            bgcolor="rgba(254,249,245,0.9)",
            bordercolor="#E6E0D8",
            borderwidth=1,
        ),
        hovermode="x unified",
        hoverlabel=dict(
            bgcolor="#FFFFFF",
            bordercolor="#E6E0D8",
            font=dict(color=HC_GRAY, family="'Karla', sans-serif"),
        ),
        margin=dict(t=48, b=36, l=8, r=8),
    )
    if height:
        layout["height"] = height
    fig.update_layout(**layout)
    return fig


# ── DATA LOADING ──────────────────────────────────────────────────────────────

@st.cache_data(ttl=300, show_spinner="Pulling latest data from Google Sheets…")
def load_raw():
    # On Streamlit Cloud: reads from st.secrets["gcp_service_account"]
    # Locally: falls back to the credentials file path
    if "gcp_service_account" in st.secrets:
        creds = Credentials.from_service_account_info(
            dict(st.secrets["gcp_service_account"]), scopes=SCOPES
        )
    else:
        creds = Credentials.from_service_account_file(CREDENTIALS_PATH, scopes=SCOPES)
    client = gspread.authorize(creds)
    book   = client.open_by_key(SHEET_ID)
    wms_raw   = book.worksheet("WMS-Logged YTD").get_all_values()
    meals_raw = book.worksheet("Total Meals").get_all_values()
    return wms_raw, meals_raw


def parse_wms(raw: list) -> pd.DataFrame:
    if len(raw) < 2:
        return pd.DataFrame()
    df = pd.DataFrame(raw[1:])

    col_map = {
        0:  "created_date",
        4:  "ingredient_id",
        5:  "ingredient_name",
        6:  "uom",
        7:  "quantity",
        9:  "waste_reason",
        10: "waste_reason_detail",
        12: "po_number",
        13: "received_qty",
        14: "menu_ship_date",
        15: "waste_cost",      # column P = total cost already (no further math needed)
        16: "facility",
        17: "is_rth",
    }
    valid = {k: v for k, v in col_map.items() if k < df.shape[1]}
    df    = df.rename(columns=valid)[list(valid.values())]

    df["created_date"]   = pd.to_datetime(df["created_date"],   errors="coerce")
    df["menu_ship_date"] = pd.to_datetime(df["menu_ship_date"], errors="coerce")
    df["quantity"]     = pd.to_numeric(df["quantity"],    errors="coerce").fillna(0)
    df["received_qty"] = pd.to_numeric(df["received_qty"], errors="coerce").fillna(0)

    raw_cost = pd.to_numeric(df["waste_cost"], errors="coerce").fillna(0)
    # Sheet stores removals as negative, corrections as positive.
    # Negate everything so: waste = positive cost, corrections = negative (reduce totals).
    df["waste_cost"] = raw_cost * -1

    # Normalise facility names for reliable joins
    df["facility"] = df["facility"].astype(str).str.strip()

    # Week anchor = Monday of the menu-ship week
    df["week"] = df["menu_ship_date"].dt.to_period("W").dt.start_time

    return df.dropna(subset=["created_date"])


def parse_meals(raw: list) -> pd.DataFrame:
    if len(raw) < 2:
        return pd.DataFrame()
    df = pd.DataFrame(raw[1:])

    # Column A in Total Meals = menu ship week — same key as column O in WMS
    col_map = {0: "menu_ship_date", 1: "facility", 2: "is_rth", 3: "total_meals"}
    valid = {k: v for k, v in col_map.items() if k < df.shape[1]}
    df    = df.rename(columns=valid)[list(valid.values())]

    df["menu_ship_date"] = pd.to_datetime(df["menu_ship_date"], errors="coerce")
    df["total_meals"]    = pd.to_numeric(df["total_meals"], errors="coerce").fillna(0)
    df["facility"]       = df["facility"].astype(str).str.strip()

    return df.dropna(subset=["menu_ship_date"])


def build_cpm(wms: pd.DataFrame, meals: pd.DataFrame) -> pd.DataFrame:
    """
    Joins WMS waste and Total Meals on facility + menu_ship_date (exact match —
    both sheets use the same weekly date as their key).
    CPM = waste_cost / total_meals at that grain.
    """
    waste_by_key = wms.groupby(["facility", "menu_ship_date"], as_index=False)["waste_cost"].sum()
    meals_by_key = meals.groupby(["facility", "menu_ship_date"], as_index=False)["total_meals"].sum()

    merged        = waste_by_key.merge(meals_by_key, on=["facility", "menu_ship_date"], how="left")
    merged["week"] = pd.to_datetime(merged["menu_ship_date"]).dt.to_period("W").dt.start_time
    merged["cpm"]  = merged["waste_cost"] / merged["total_meals"].replace(0, np.nan)
    return merged


# ── LOAD DATA ─────────────────────────────────────────────────────────────────

try:
    wms_raw, meals_raw = load_raw()
    wms_df   = parse_wms(wms_raw)
    meals_df = parse_meals(meals_raw)
except Exception as exc:
    st.error(f"Could not load data from Google Sheets: {exc}")
    st.stop()

if wms_df.empty:
    st.warning("WMS sheet returned no rows. Check the tab name and sharing permissions.")
    st.stop()


# ── SIDEBAR ───────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("### Produce Scorecard")
    st.caption("All filters apply to every chart and KPI.")
    st.divider()

    # ── Date preset ──
    st.markdown("**Date Range** *(by menu ship week)*")
    data_min = wms_df["menu_ship_date"].dropna().min().date()
    data_max = wms_df["menu_ship_date"].dropna().max().date()
    today    = date.today()
    jan_1    = date(today.year, 1, 1)

    preset = st.radio(
        "Quick select",
        ["YTD", "Last 4W", "Last 8W", "Last 12W", "Custom"],
        horizontal=True,
        label_visibility="collapsed",
    )

    if preset == "YTD":
        default_start, default_end = jan_1, data_max
    elif preset == "Last 4W":
        default_start, default_end = data_max - timedelta(weeks=4), data_max
    elif preset == "Last 8W":
        default_start, default_end = data_max - timedelta(weeks=8), data_max
    elif preset == "Last 12W":
        default_start, default_end = data_max - timedelta(weeks=12), data_max
    else:
        default_start, default_end = data_min, data_max

    if preset == "Custom":
        date_range = st.date_input(
            "Pick range", value=(default_start, default_end),
            min_value=data_min, max_value=data_max,
            label_visibility="collapsed",
        )
    else:
        date_range = (
            max(default_start, data_min),
            min(default_end,   data_max),
        )
        st.caption(f"{date_range[0].strftime('%b %d')} – {date_range[1].strftime('%b %d, %Y')}")

    st.divider()

    # ── Other filters ──
    facilities   = ["All"] + sorted(wms_df["facility"].dropna().unique())
    sel_facility = st.selectbox("Facility", facilities)

    reasons    = ["All"] + sorted(wms_df["waste_reason"].dropna().unique())
    sel_reason = st.selectbox("Waste Reason", reasons)

    rth_opts = ["All"] + sorted(wms_df["is_rth"].dropna().unique())
    sel_rth  = st.selectbox("RTH / Non-RTH", rth_opts)

    st.divider()
    if st.button("🔄 Refresh Data", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    st.caption(f"Last pull: {datetime.now().strftime('%b %d · %I:%M %p')}")


# ── APPLY FILTERS ─────────────────────────────────────────────────────────────

f = wms_df.copy()
if len(date_range) == 2:
    # Filter WMS on menu_ship_date — the same key used to join Total Meals
    f = f[(f["menu_ship_date"].dt.date >= date_range[0]) &
          (f["menu_ship_date"].dt.date <= date_range[1])]
if sel_facility != "All":
    f = f[f["facility"] == sel_facility]
if sel_reason != "All":
    f = f[f["waste_reason"] == sel_reason]
if sel_rth != "All":
    f = f[f["is_rth"] == sel_rth]

if f.empty:
    st.warning("No data matches the current filters.")
    st.stop()

# Filter meals to the same date window and facilities as the filtered waste data
meals_f = meals_df[
    (meals_df["menu_ship_date"].dt.date >= date_range[0]) &
    (meals_df["menu_ship_date"].dt.date <= date_range[1]) &
    (meals_df["facility"].isin(f["facility"].unique()))
] if len(date_range) == 2 else meals_df[meals_df["facility"].isin(f["facility"].unique())]


# ── KPI CALCULATIONS ──────────────────────────────────────────────────────────

total_cost  = f["waste_cost"].sum()
cpm_detail  = build_cpm(f, meals_f)

# Correct overall CPM: sum all waste / sum all matched meals (not average of ratios)
total_meals_matched = cpm_detail["total_meals"].sum()
overall_cpm = total_cost / total_meals_matched if total_meals_matched > 0 else np.nan

reason_sums    = f.groupby("waste_reason")["waste_cost"].sum()
top_reason     = reason_sums.idxmax() if not reason_sums.empty else "N/A"
top_reason_pct = (reason_sums[top_reason] / total_cost * 100) if total_cost else 0

disposal_cost  = f[
    f["waste_reason"].str.lower().str.contains("disposal", na=False)
]["waste_cost"].sum()
disposal_pct   = (disposal_cost / total_cost * 100) if total_cost else 0


# ── PAGE HEADER ───────────────────────────────────────────────────────────────

range_str = (
    f"{date_range[0].strftime('%b %d')} – {date_range[1].strftime('%b %d, %Y')}"
    if len(date_range) == 2 else ""
)
fac_str = sel_facility if sel_facility != "All" else f"{f['facility'].nunique()} facilities"
st.markdown(
    f'<p class="hc-title">Produce Waste Scorecard</p>'
    f'<p class="hc-eyebrow">{range_str} &nbsp;·&nbsp; {fac_str} &nbsp;·&nbsp; {len(f):,} records</p>',
    unsafe_allow_html=True,
)
st.divider()


# ── KPI CARDS ─────────────────────────────────────────────────────────────────

k1, k2, k3, k4 = st.columns(4)
k1.metric("Total Waste Cost", f"${total_cost:,.0f}")
k2.metric(
    "Overall CPM",
    f"${overall_cpm:.4f}" if not np.isnan(overall_cpm) else "—",
    help=f"Total waste ${total_cost:,.0f} ÷ {total_meals_matched:,.0f} matched meals",
)
k3.metric("Top Waste Reason",   top_reason, f"{top_reason_pct:.1f}% of cost")
k4.metric("True Disposal Cost", f"${disposal_cost:,.0f}", f"{disposal_pct:.1f}% of total")

st.divider()


# ── TABS ──────────────────────────────────────────────────────────────────────

tab_trends, tab_cpm, tab_facility, tab_ingredients, tab_table = st.tabs(
    ["Waste Trends", "Cost Per Meal", "By Facility", "By Ingredient", "Detail Table"]
)


# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — WASTE TRENDS
# ══════════════════════════════════════════════════════════════════════════════
with tab_trends:
    c1, c2 = st.columns(2)

    with c1:
        wk_cost = f.groupby("week")["waste_cost"].sum().reset_index()
        fig = px.line(wk_cost, x="week", y="waste_cost",
                      title="Weekly waste cost",
                      labels={"week": "Week of", "waste_cost": "Waste Cost ($)"},
                      markers=True, color_discrete_sequence=[HC_GREEN])
        fig.update_traces(line_width=2.5, marker_color=HC_GREEN)
        fig.update_layout(yaxis_tickprefix="$", yaxis_tickformat=",")
        st.plotly_chart(chart_base(fig), use_container_width=True)

    with c2:
        reason_df = (f.groupby("waste_reason")["waste_cost"].sum()
                      .reset_index().sort_values("waste_cost", ascending=False))
        fig2 = px.bar(reason_df, x="waste_reason", y="waste_cost",
                      title="Waste cost by reason  —  negative bar indicates a correction",
                      labels={"waste_reason": "Reason", "waste_cost": "Waste Cost ($)"},
                      color="waste_reason",
                      color_discrete_sequence=HC_PALETTE,
                      text_auto="$.3s")
        fig2.update_layout(yaxis_tickprefix="$", yaxis_tickformat=",",
                           showlegend=False, xaxis_title=None)
        st.plotly_chart(chart_base(fig2), use_container_width=True)

    # Stacked area by reason
    wk_reason = f.groupby(["week", "waste_reason"])["waste_cost"].sum().reset_index()
    fig3 = px.area(wk_reason, x="week", y="waste_cost", color="waste_reason",
                   title="Weekly waste cost — stacked by reason",
                   labels={"week": "Week of", "waste_cost": "Waste Cost ($)", "waste_reason": "Reason"},
                   color_discrete_sequence=HC_PALETTE)
    fig3.update_layout(yaxis_tickprefix="$", yaxis_tickformat=",")
    st.plotly_chart(chart_base(fig3), use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — CPM
# ══════════════════════════════════════════════════════════════════════════════
with tab_cpm:

    # ── Overall CPM trend (weekly) ─────────────────────────────────────────
    wk_cpm = (
        cpm_detail.groupby("week")
        .apply(lambda g: g["waste_cost"].sum() / g["total_meals"].sum()
               if g["total_meals"].sum() > 0 else np.nan)
        .reset_index(name="cpm")
    )
    fig_cpm1 = px.line(wk_cpm, x="week", y="cpm",
                        title="Weekly cost per meal — all facilities combined",
                        labels={"week": "Week of", "cpm": "CPM ($)"},
                        markers=True, color_discrete_sequence=[HC_MELON])
    fig_cpm1.update_traces(line_width=2.5, marker_color=HC_MELON)
    fig_cpm1.update_layout(yaxis_tickprefix="$", yaxis_tickformat=".4f")
    st.plotly_chart(chart_base(fig_cpm1), use_container_width=True)

    st.divider()

    # ── CPM by facility: side-by-side ─────────────────────────────────────
    c_left, c_right = st.columns(2)

    with c_left:
        # Correct facility CPM = sum(waste) / sum(meals) per facility
        fac_cpm_bar = (
            cpm_detail.groupby("facility")
            .apply(lambda g: g["waste_cost"].sum() / g["total_meals"].sum()
                   if g["total_meals"].sum() > 0 else np.nan)
            .reset_index(name="cpm")
            .dropna()
            .sort_values("cpm")
        )
        fig_fac_bar = px.bar(
            fac_cpm_bar, y="facility", x="cpm",
            orientation="h",
            title="CPM by facility",
            labels={"facility": "", "cpm": "CPM ($)"},
            color="cpm",
            color_continuous_scale=[[0, HC_GREEN], [0.5, HC_LEMON], [1, HC_MELON]],
            text_auto="$.4f",
        )
        fig_fac_bar.update_layout(
            xaxis_tickprefix="$", xaxis_tickformat=".4f",
            coloraxis_showscale=False,
            height=max(320, len(fac_cpm_bar) * 44),
        )
        st.plotly_chart(chart_base(fig_fac_bar), use_container_width=True)

    with c_right:
        # CPM summary table
        fac_cpm_tbl = (
            cpm_detail.groupby("facility")
            .agg(waste_cost=("waste_cost", "sum"), total_meals=("total_meals", "sum"))
            .reset_index()
        )
        fac_cpm_tbl["cpm"] = fac_cpm_tbl["waste_cost"] / fac_cpm_tbl["total_meals"].replace(0, np.nan)
        fac_cpm_tbl = fac_cpm_tbl.sort_values("cpm", ascending=False)

        display = fac_cpm_tbl.copy()
        display["waste_cost"]  = display["waste_cost"].map("${:,.0f}".format)
        display["total_meals"] = display["total_meals"].map("{:,.0f}".format)
        display["cpm"]         = display["cpm"].map(lambda x: f"${x:.4f}" if pd.notna(x) else "—")
        display.columns        = ["Facility", "Waste Cost", "Total Meals", "CPM"]
        st.markdown("#### CPM by Facility")
        st.dataframe(display, use_container_width=True, hide_index=True)

    st.divider()

    # ── CPM trend per facility (multi-line) ───────────────────────────────
    # Only show if ≤ 12 facilities to keep the chart readable
    n_facs = cpm_detail["facility"].nunique()
    if n_facs <= 12:
        fac_wk_cpm = (
            cpm_detail[cpm_detail["total_meals"] > 0]
            .assign(cpm=lambda d: d["waste_cost"] / d["total_meals"])
        )
        fig_multi = px.line(
            fac_wk_cpm, x="week", y="cpm", color="facility",
            title="Weekly CPM by facility",
            labels={"week": "Week of", "cpm": "CPM ($)", "facility": "Facility"},
            markers=True,
            color_discrete_sequence=HC_PALETTE,
        )
        fig_multi.update_traces(line_width=2)
        fig_multi.update_layout(yaxis_tickprefix="$", yaxis_tickformat=".4f")
        st.plotly_chart(chart_base(fig_multi, height=440), use_container_width=True)
    else:
        st.info(f"Multi-line CPM chart is hidden when more than 12 facilities are shown ({n_facs} currently). Use the Facility filter to drill into a subset.")

    # ── CPM heatmap: facility × week ─────────────────────────────────────
    heat_cpm = (
        cpm_detail[cpm_detail["total_meals"] > 0]
        .assign(cpm=lambda d: d["waste_cost"] / d["total_meals"])
        .pivot_table(index="facility", columns="week", values="cpm", aggfunc="mean")
    )
    if not heat_cpm.empty:
        heat_cpm.columns = [c.strftime("%m/%d") if hasattr(c, "strftime") else str(c)
                            for c in heat_cpm.columns]
        fig_heat = px.imshow(
            heat_cpm,
            title="CPM heatmap — facility by week",
            labels={"x": "Week of", "y": "Facility", "color": "CPM ($)"},
            color_continuous_scale=[[0, HC_GREEN], [0.5, HC_LEMON], [1, HC_MELON]],
            aspect="auto",
            text_auto="$.3f",
        )
        fig_heat.update_layout(
            coloraxis_colorbar=dict(tickprefix="$", tickformat=".3f", title="CPM"),
            height=max(320, len(heat_cpm) * 44 + 80),
            xaxis_tickangle=-45,
        )
        st.plotly_chart(chart_base(fig_heat), use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — BY FACILITY
# ══════════════════════════════════════════════════════════════════════════════
with tab_facility:
    fac_cost = f.groupby("facility")["waste_cost"].sum().reset_index().sort_values("waste_cost")
    fig_fac = px.bar(
        fac_cost, y="facility", x="waste_cost",
        orientation="h",
        title="Total waste cost by facility",
        labels={"facility": "", "waste_cost": "Waste Cost ($)"},
        color="waste_cost",
        color_continuous_scale=[[0, HC_GREEN], [0.5, HC_LEMON], [1, HC_MELON]],
        text_auto="$.3s",
    )
    fig_fac.update_layout(
        xaxis_tickprefix="$", xaxis_tickformat=",",
        coloraxis_showscale=False,
        height=max(320, len(fac_cost) * 44),
    )
    st.plotly_chart(chart_base(fig_fac), use_container_width=True)

    # Waste by facility over time (stacked bar)
    fac_wk = f.groupby(["week", "facility"])["waste_cost"].sum().reset_index()
    fig_fac_trend = px.bar(
        fac_wk, x="week", y="waste_cost", color="facility",
        title="Weekly waste cost by facility",
        labels={"week": "Week of", "waste_cost": "Waste Cost ($)", "facility": "Facility"},
        color_discrete_sequence=HC_PALETTE,
    )
    fig_fac_trend.update_layout(yaxis_tickprefix="$", yaxis_tickformat=",", barmode="stack")
    st.plotly_chart(chart_base(fig_fac_trend), use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 — BY INGREDIENT
# ══════════════════════════════════════════════════════════════════════════════
with tab_ingredients:
    c_left, c_right = st.columns([2, 1])

    with c_left:
        top_n = st.slider("Show top N ingredients", 10, 50, 20)
        ing = (
            f.groupby(["ingredient_name", "uom"])["waste_cost"]
            .sum().reset_index()
            .sort_values("waste_cost", ascending=False)
            .head(top_n)
        )
        fig_ing = px.bar(
            ing, y="ingredient_name", x="waste_cost",
            orientation="h",
            title=f"Top {top_n} ingredients by waste cost",
            labels={"ingredient_name": "", "waste_cost": "Waste Cost ($)", "uom": "UOM"},
            color="waste_cost",
            color_continuous_scale=[[0, HC_CREAM], [1, HC_MELON]],
            hover_data=["uom"], text_auto="$.3s",
        )
        fig_ing.update_layout(
            xaxis_tickprefix="$", xaxis_tickformat=",",
            yaxis={"categoryorder": "total ascending"},
            coloraxis_showscale=False,
            height=max(400, top_n * 28),
        )
        st.plotly_chart(chart_base(fig_ing), use_container_width=True)

    with c_right:
        st.markdown('<p class="hc-eyebrow">Top Ingredients</p>', unsafe_allow_html=True)
        ing_tbl = ing.copy()
        ing_tbl["waste_cost"] = ing_tbl["waste_cost"].map("${:,.2f}".format)
        ing_tbl.columns = ["Ingredient", "UOM", "Waste Cost"]
        st.dataframe(ing_tbl.reset_index(drop=True), use_container_width=True, hide_index=True)

    # Heatmap: ingredient × reason
    heat_df = (
        f.groupby(["ingredient_name", "waste_reason"])["waste_cost"]
        .sum().unstack(fill_value=0)
    )
    if not heat_df.empty:
        heat_df = heat_df.loc[heat_df.sum(axis=1).nlargest(15).index]
        fig_heat2 = px.imshow(
            heat_df,
            title="Top 15 ingredients by waste reason",
            labels={"x": "Reason", "y": "Ingredient", "color": "Cost ($)"},
            color_continuous_scale=[[0, "#FFFFFF"], [0.5, HC_LEMON], [1, HC_MELON]],
            aspect="auto",
            text_auto="$.0f",
        )
        fig_heat2.update_layout(
            height=500,
            coloraxis_colorbar=dict(tickprefix="$", tickformat=",.0f"),
        )
        st.plotly_chart(chart_base(fig_heat2), use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# TAB 5 — DETAIL TABLE
# ══════════════════════════════════════════════════════════════════════════════
with tab_table:
    display_cols = [
        "created_date", "facility", "ingredient_name", "uom",
        "quantity", "waste_reason", "waste_reason_detail",
        "menu_ship_date", "waste_cost", "is_rth",
    ]
    existing = [c for c in display_cols if c in f.columns]
    detail   = f[existing].sort_values("created_date", ascending=False).copy()
    detail["waste_cost"] = detail["waste_cost"].map("${:,.2f}".format)

    st.caption(f"{len(detail):,} rows matching current filters")
    st.dataframe(detail, use_container_width=True, hide_index=True)

    csv = f[existing].to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Download as CSV", csv, "produce_waste_filtered.csv", "text/csv")
