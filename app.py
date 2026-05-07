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
FULL_WASTE_THRESHOLD = 0.95

st.set_page_config(
    page_title="Produce Scorecard — Home Chef",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded",
)

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

HC_PALETTE = [HC_GREEN, HC_MELON, HC_BLUEBERRY, "#00809C", HC_ORANGE, HC_GRAPE, HC_LEMON, HC_WATER]

# ── GLOBAL STYLES ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Bree+Serif&family=Karla:wght@400;600;700;800&family=Work+Sans:wght@400;600;700&display=swap');

/* ── page ── */
.stApp, .main .block-container { background: #FEF9F5 !important; }
.main .block-container { padding-top: 2.5rem; padding-bottom: 4rem; max-width: 1480px; }
html, body, [class*="css"] { font-family: 'Karla','Work Sans',system-ui,sans-serif; color: #4A4A4A; }

/* ── custom HTML elements ── */
.hc-eyebrow-green {
    font-family: 'Karla',sans-serif;
    font-size: 11px; font-weight: 700;
    letter-spacing: 0.14em; text-transform: uppercase;
    color: #008600; margin: 0 0 8px;
}
.hc-title {
    font-family: 'Bree Serif', Georgia, serif !important;
    font-size: 62px !important; line-height: 1.0 !important;
    color: #1A1A1A !important; margin: 0 !important; letter-spacing: -0.02em !important;
}
.hc-eyebrow {
    font-family: 'Karla',sans-serif;
    font-size: 11px; font-weight: 700;
    letter-spacing: 0.14em; text-transform: uppercase;
    color: #7A7A7A; margin: 10px 0 0;
}
.hc-section-head {
    border-top: 1px solid #E6E0D8;
    padding-top: 28px;
    margin-top: 36px;
    margin-bottom: 16px;
}
.hc-section-head__eyebrow {
    font-family: 'Karla',sans-serif;
    font-size: 11px; font-weight: 700;
    letter-spacing: 0.14em; text-transform: uppercase;
    color: #008600; margin: 0 0 4px;
}
.hc-section-head__title {
    font-family: 'Bree Serif', Georgia, serif;
    font-size: 22px; line-height: 1.15;
    color: #1A1A1A; margin: 0;
}

/* ── dividers ── */
hr { border-color: #E6E0D8 !important; margin: 20px 0 !important; }

/* ── Plotly chart wrappers — card treatment ── */
[data-testid="stPlotlyChart"] {
    background: #FFFFFF;
    border: 1px solid #E6E0D8;
    border-radius: 16px;
    overflow: hidden;
    box-shadow: 0 1px 3px rgba(11,53,90,0.05);
}

/* ── sidebar — blueberry control rail ── */
section[data-testid="stSidebar"] {
    background: #0B355A !important;
    padding-top: 1.5rem;
}
section[data-testid="stSidebar"] * { color: #FEF9F5 !important; }
section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 {
    font-family: 'Bree Serif', Georgia, serif !important;
    font-size: 18px !important;
    color: #FEF9F5 !important;
    margin-bottom: 4px;
}
section[data-testid="stSidebar"] [data-testid="stCaptionContainer"] {
    color: rgba(254,249,245,0.6) !important;
    font-size: 11px !important;
}
section[data-testid="stSidebar"] hr {
    border-color: rgba(254,249,245,0.14) !important;
    margin: 14px 0 !important;
}
section[data-testid="stSidebar"] strong,
section[data-testid="stSidebar"] p strong {
    font-family: 'Karla',sans-serif !important;
    font-size: 10.5px !important; font-weight: 700 !important;
    letter-spacing: 0.14em !important; text-transform: uppercase !important;
    color: rgba(254,249,245,0.6) !important;
}
section[data-testid="stSidebar"] .stSelectbox div[data-baseweb="select"] > div {
    background: rgba(254,249,245,0.08) !important;
    border: 1px solid rgba(254,249,245,0.2) !important;
    border-radius: 8px !important;
    color: #FEF9F5 !important;
    font-size: 13px;
}
/* st.pills — date preset selector */
section[data-testid="stSidebar"] [data-testid="stPills"] {
    gap: 4px !important;
}
section[data-testid="stSidebar"] [data-testid="stPills"] button {
    background: rgba(254,249,245,0.10) !important;
    border: 1px solid rgba(254,249,245,0.15) !important;
    border-radius: 999px !important;
    color: rgba(254,249,245,0.75) !important;
    font-family: 'Karla',sans-serif !important;
    font-size: 11px !important;
    font-weight: 700 !important;
    padding: 4px 10px !important;
    white-space: nowrap !important;
}
section[data-testid="stSidebar"] [data-testid="stPills"] button[aria-pressed="true"],
section[data-testid="stSidebar"] [data-testid="stPills"] button[data-active="true"] {
    background: #FEF9F5 !important;
    border-color: #FEF9F5 !important;
    color: #0B355A !important;
}
section[data-testid="stSidebar"] .stButton button {
    background: #008600 !important;
    color: #FFFFFF !important;
    border: 0 !important;
    border-radius: 999px !important;
    font-family: 'Karla',sans-serif !important;
    font-weight: 700 !important;
    padding: 11px 16px !important;
}
section[data-testid="stSidebar"] .stButton button:hover { background: #006D00 !important; }

/* ── tabs ── */
.stTabs [data-baseweb="tab-list"] {
    gap: 4px;
    border-bottom: 1.5px solid #E6E0D8;
    background: transparent;
    margin-top: 16px;
}
.stTabs [data-baseweb="tab"] {
    font-family: 'Karla',sans-serif !important;
    font-weight: 700 !important;
    font-size: 11.5px !important;
    letter-spacing: 0.12em;
    color: #7A7A7A !important;
    border-radius: 0 !important;
    padding: 12px 18px;
    border-bottom: 2px solid transparent;
    background: transparent !important;
    text-transform: uppercase;
    margin-bottom: -1.5px;
}
.stTabs [aria-selected="true"] {
    color: #008600 !important;
    border-bottom: 2px solid #008600 !important;
    background: transparent !important;
}

/* ── dataframes ── */
[data-testid="stDataFrame"] {
    border: 1px solid #E6E0D8 !important;
    border-radius: 16px !important;
    overflow: hidden;
    background: #fff;
}

/* ── download button ── */
.stDownloadButton button {
    background: transparent !important;
    color: #008600 !important;
    border: 1.5px solid #008600 !important;
    border-radius: 999px !important;
    font-family: 'Karla',sans-serif !important;
    font-weight: 700 !important;
    font-size: 13px !important;
    padding: 9px 22px !important;
}
.stDownloadButton button:hover { background: #008600 !important; color: #fff !important; }

/* ── alerts ── */
[data-testid="stAlert"] { border-radius: 12px !important; }

/* ── slider ── */
[data-testid="stSlider"] [data-baseweb="slider"] [role="slider"] { background: #008600 !important; }
</style>
""", unsafe_allow_html=True)


# ── PASSWORD GATE ─────────────────────────────────────────────────────────────
def check_password():
    if st.session_state.get("authenticated"):
        return True
    st.markdown('<p class="hc-title" style="margin-bottom:8px">Produce Scorecard</p>', unsafe_allow_html=True)
    pw = st.text_input("Password", type="password", placeholder="Enter team password")
    if pw:
        try:
            correct = st.secrets.get("app_password", "")
        except Exception:
            correct = ""
        if pw == correct or correct == "":
            st.session_state["authenticated"] = True
            st.rerun()
        else:
            st.error("Incorrect password.")
    return False

if not check_password():
    st.stop()


# ── CHART BASE ────────────────────────────────────────────────────────────────
def chart_base(fig, height=None):
    """Apply Home Chef brand styling to any Plotly figure."""
    layout = dict(
        font=dict(family="'Karla','Work Sans',sans-serif", size=12, color=HC_GRAY),
        plot_bgcolor="#FFFFFF",
        paper_bgcolor="#FFFFFF",
        title=dict(
            font=dict(size=15, color="#1A1A1A", family="'Bree Serif',Georgia,serif"),
            x=0, xanchor="left", y=0.97, pad=dict(t=2, l=4),
        ),
        xaxis=dict(
            gridcolor="#EEE8DD", linecolor="#E6E0D8", zeroline=False,
            tickfont=dict(color=HC_MUTED, family="'Karla',sans-serif", size=11),
            title_font=dict(color=HC_MUTED, size=11),
        ),
        yaxis=dict(
            gridcolor="#EEE8DD", linecolor="#E6E0D8", zeroline=False,
            tickfont=dict(color=HC_MUTED, family="'Karla',sans-serif", size=11),
            title_font=dict(color=HC_MUTED, size=11),
        ),
        legend=dict(
            font=dict(color=HC_GRAY, family="'Karla',sans-serif", size=11),
            bgcolor="rgba(0,0,0,0)",
            bordercolor="rgba(0,0,0,0)", borderwidth=0,
            orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
        ),
        hovermode="x unified",
        hoverlabel=dict(
            bgcolor="#FFFFFF", bordercolor="#E6E0D8",
            font=dict(color="#1A1A1A", family="'Karla',sans-serif", size=12),
        ),
        margin=dict(t=48, b=28, l=52, r=24),
    )
    if height:
        layout["height"] = height
    fig.update_layout(**layout)
    return fig


def section_head(eyebrow: str, title: str):
    """Renders a ruled section header with HC eyebrow + Bree Serif title."""
    st.markdown(
        f'<div class="hc-section-head">'
        f'<p class="hc-section-head__eyebrow">{eyebrow}</p>'
        f'<h2 class="hc-section-head__title">{title}</h2>'
        f'</div>',
        unsafe_allow_html=True,
    )


def kpi_card(label: str, value: str, delta: str = None,
             delta_positive: bool = None, help_text: str = None) -> str:
    """
    Returns HTML for a branded KPI card.
    Render with st.markdown(..., unsafe_allow_html=True) inside a column.
    delta_positive=True  → green badge
    delta_positive=False → melon badge
    delta_positive=None  → gray badge
    """
    delta_html = ""
    if delta and delta not in ("—", ""):
        if delta_positive is True:
            bg, fg = "rgba(0,134,0,0.12)", HC_GREEN
        elif delta_positive is False:
            bg, fg = "rgba(242,112,69,0.12)", HC_MELON
        else:
            bg, fg = "rgba(74,74,74,0.08)", HC_MUTED
        delta_html = (
            f'<div style="margin-top:10px;display:inline-block;padding:3px 10px;'
            f'border-radius:999px;background:{bg};font-family:Karla,sans-serif;'
            f'font-size:11px;font-weight:700;color:{fg};letter-spacing:0.03em">{delta}</div>'
        )
    title_attr = f' title="{help_text}"' if help_text else ""
    return (
        f'<div{title_attr} style="background:#FFFFFF;border:1px solid {HC_BORDER};border-radius:16px;'
        f'padding:22px 24px 20px;box-shadow:0 1px 3px rgba(11,53,90,0.06);'
        f'min-height:128px;height:100%">'
        f'<div style="font-family:Karla,sans-serif;font-size:10.5px;font-weight:700;'
        f'letter-spacing:0.14em;text-transform:uppercase;color:{HC_MUTED};margin-bottom:10px">{label}</div>'
        f'<div style="font-family:\'Bree Serif\',Georgia,serif;font-size:32px;line-height:1;'
        f'color:#1A1A1A;letter-spacing:-0.01em">{value}</div>'
        f'{delta_html}'
        f'</div>'
    )


# ── DATA LOADING ──────────────────────────────────────────────────────────────

@st.cache_data(ttl=300, show_spinner="Pulling latest data from Google Sheets…")
def load_raw():
    try:
        creds = Credentials.from_service_account_info(
            dict(st.secrets["gcp_service_account"]), scopes=SCOPES
        )
    except Exception:
        creds = Credentials.from_service_account_file(CREDENTIALS_PATH, scopes=SCOPES)
    client = gspread.authorize(creds)
    book   = client.open_by_key(SHEET_ID)
    wms_raw    = book.worksheet("WMS-Logged YTD").get_all_values()
    meals_raw  = book.worksheet("Total Meals").get_all_values()
    menus_raw  = book.worksheet("Menus").get_all_values()
    shorts_raw = book.worksheet("Shorts Logs").get_all_values()
    return wms_raw, meals_raw, menus_raw, shorts_raw


def parse_wms(raw: list) -> pd.DataFrame:
    if len(raw) < 2:
        return pd.DataFrame()
    df = pd.DataFrame(raw[1:])

    col_map = {
        0:  "created_date",
        2:  "lot_id",
        4:  "ingredient_id",
        5:  "ingredient_name",
        6:  "uom",
        7:  "quantity",
        9:  "waste_reason",
        10: "waste_reason_detail",
        12: "po_number",
        13: "received_qty",
        14: "menu_ship_date",
        15: "waste_cost",
        16: "facility",
        17: "is_rth",
    }
    valid = {k: v for k, v in col_map.items() if k < df.shape[1]}
    df    = df.rename(columns=valid)[list(valid.values())]

    df["created_date"]   = pd.to_datetime(df["created_date"],   errors="coerce")
    df["menu_ship_date"] = pd.to_datetime(df["menu_ship_date"], errors="coerce")

    # Both quantity and cost are negative in the sheet (removals).
    # Negate so waste = positive, corrections = negative (they reduce totals).
    df["quantity"]     = pd.to_numeric(df["quantity"],     errors="coerce").fillna(0) * -1
    df["received_qty"] = pd.to_numeric(df["received_qty"], errors="coerce").fillna(0)
    df["waste_cost"]   = pd.to_numeric(df["waste_cost"],   errors="coerce").fillna(0) * -1

    df["facility"] = df["facility"].astype(str).str.strip()
    df["week"]     = df["menu_ship_date"].dt.to_period("W").dt.start_time

    return df.dropna(subset=["created_date"])


def parse_meals(raw: list) -> pd.DataFrame:
    if len(raw) < 2:
        return pd.DataFrame()
    df = pd.DataFrame(raw[1:])

    col_map = {0: "menu_ship_date", 1: "facility", 2: "is_rth", 3: "total_meals"}
    valid = {k: v for k, v in col_map.items() if k < df.shape[1]}
    df    = df.rename(columns=valid)[list(valid.values())]

    df["menu_ship_date"] = pd.to_datetime(df["menu_ship_date"], errors="coerce")
    df["total_meals"]    = pd.to_numeric(df["total_meals"], errors="coerce").fillna(0)
    df["facility"]       = df["facility"].astype(str).str.strip()

    return df.dropna(subset=["menu_ship_date"])


def parse_shorts(raw: list) -> pd.DataFrame:
    if len(raw) < 2:
        return pd.DataFrame()
    df = pd.DataFrame(raw[1:])

    col_map = {
        2:  "facility",
        4:  "menu_ship_week",
        6:  "shorted_ingredient",
        7:  "short_reason",
        11: "brand",
        23: "category",
    }
    valid = {k: v for k, v in col_map.items() if k < df.shape[1]}
    df    = df.rename(columns=valid)[list(valid.values())]

    df["menu_ship_week"]     = pd.to_datetime(df["menu_ship_week"], errors="coerce")
    df["facility"]           = df["facility"].astype(str).str.strip()
    df["shorted_ingredient"] = df["shorted_ingredient"].astype(str).str.strip()
    df["short_reason"]       = df["short_reason"].astype(str).str.strip()
    df["category"]           = df["category"].astype(str).str.strip()
    df["week"]               = df["menu_ship_week"].dt.to_period("W").dt.start_time

    # Only produce shorts
    df = df[df["category"].str.lower() == "produce"]

    return df.dropna(subset=["menu_ship_week"])


def build_cpm(wms: pd.DataFrame, meals: pd.DataFrame) -> pd.DataFrame:
    """
    Joins WMS waste and Total Meals on facility + menu_ship_date (exact match).
    CPM = waste_cost / total_meals at that grain.
    """
    waste_by_key = wms.groupby(["facility", "menu_ship_date"], as_index=False)["waste_cost"].sum()
    meals_by_key = meals.groupby(["facility", "menu_ship_date"], as_index=False)["total_meals"].sum()

    merged         = waste_by_key.merge(meals_by_key, on=["facility", "menu_ship_date"], how="left")
    merged["week"] = pd.to_datetime(merged["menu_ship_date"]).dt.to_period("W").dt.start_time
    merged["cpm"]  = merged["waste_cost"] / merged["total_meals"].replace(0, np.nan)
    return merged


def build_po_analysis(wms: pd.DataFrame) -> pd.DataFrame:
    """One row per PO-ingredient combination across all lot IDs."""
    po = wms[wms["po_number"].astype(str).str.strip().ne("")].copy()
    po["po_number"] = po["po_number"].astype(str).str.strip()

    agg = po.groupby(["po_number", "ingredient_name"]).agg(
        facility       = ("facility",       "first"),
        menu_ship_date = ("menu_ship_date", "first"),
        waste_qty      = ("quantity",       "sum"),
        received_qty   = ("received_qty",   "sum"),
        waste_cost     = ("waste_cost",     "sum"),
        waste_reason   = ("waste_reason",   lambda x: x.mode()[0] if not x.mode().empty else ""),
        n_lots         = ("lot_id",         "nunique"),
    ).reset_index()

    agg["pct_wasted"]     = (agg["waste_qty"] / agg["received_qty"].replace(0, np.nan) * 100).clip(upper=100)
    agg["full_po_wasted"] = agg["pct_wasted"] >= (FULL_WASTE_THRESHOLD * 100)

    return agg


# ── LOAD DATA ─────────────────────────────────────────────────────────────────

try:
    wms_raw, meals_raw, menus_raw, shorts_raw = load_raw()
    wms_df    = parse_wms(wms_raw)
    meals_df  = parse_meals(meals_raw)
    shorts_df = parse_shorts(shorts_raw)
    menu_weeks = sorted(set(
        pd.to_datetime(row[1], errors="coerce")
        for row in menus_raw[1:]
        if len(row) > 1 and row[1].strip()
    ) - {pd.NaT})
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

    st.markdown("**Menu Ship Week**")
    data_min = wms_df["menu_ship_date"].dropna().min().date()
    data_max = wms_df["menu_ship_date"].dropna().max().date()
    today    = date.today()
    jan_1    = date(today.year, 1, 1)

    preset = st.pills(
        "Quick select",
        ["YTD", "4W", "8W", "12W", "Pick"],
        default="YTD",
        label_visibility="collapsed",
    )
    if preset is None:
        preset = "YTD"

    wms_week_dates = set(wms_df["menu_ship_date"].dt.date.dropna().unique())
    week_date_objs = sorted([w.date() for w in menu_weeks if w.date() in wms_week_dates])
    week_labels    = [w.strftime("%b %d, %Y") for w in week_date_objs]
    week_label_map = {w.strftime("%b %d, %Y"): w for w in week_date_objs}

    selected_weeks = None

    if preset == "YTD":
        date_range = (jan_1, data_max)
        st.caption(f"{date_range[0].strftime('%b %d')} – {date_range[1].strftime('%b %d, %Y')}")
    elif preset == "4W":
        date_range = (data_max - timedelta(weeks=4), data_max)
        st.caption(f"{date_range[0].strftime('%b %d')} – {date_range[1].strftime('%b %d, %Y')}")
    elif preset == "8W":
        date_range = (data_max - timedelta(weeks=8), data_max)
        st.caption(f"{date_range[0].strftime('%b %d')} – {date_range[1].strftime('%b %d, %Y')}")
    elif preset == "12W":
        date_range = (data_max - timedelta(weeks=12), data_max)
        st.caption(f"{date_range[0].strftime('%b %d')} – {date_range[1].strftime('%b %d, %Y')}")
    else:
        date_range    = (data_min, data_max)
        chosen_labels = st.multiselect(
            "Pick menu weeks",
            options=week_labels,
            default=[],
            label_visibility="collapsed",
            placeholder="Choose one or more menu weeks…",
        )
        selected_weeks = [week_label_map[l] for l in chosen_labels]

    st.divider()

    facilities   = ["All"] + sorted(wms_df["facility"].dropna().unique())
    sel_facility = st.selectbox("Facility", facilities)

    reasons    = ["All"] + sorted(wms_df["waste_reason"].dropna().unique())
    sel_reason = st.selectbox("Waste Reason", reasons)

    rth_opts = ["All"] + sorted(wms_df["is_rth"].dropna().unique())
    sel_rth  = st.selectbox("RTH / Non-RTH", rth_opts)

    st.divider()
    if st.button("Refresh Data", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    st.caption(f"Last pull: {datetime.now().strftime('%b %d · %I:%M %p')}")


# ── APPLY FILTERS ─────────────────────────────────────────────────────────────

f = wms_df.copy()

if selected_weeks is not None:
    if not selected_weeks:
        st.info("Select one or more menu weeks from the sidebar to view data.")
        st.stop()
    f = f[f["menu_ship_date"].dt.date.isin(selected_weeks)]
else:
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

if selected_weeks is not None:
    meals_f = meals_df[
        meals_df["menu_ship_date"].dt.date.isin(selected_weeks) &
        meals_df["facility"].isin(f["facility"].unique())
    ]
else:
    meals_f = meals_df[
        (meals_df["menu_ship_date"].dt.date >= date_range[0]) &
        (meals_df["menu_ship_date"].dt.date <= date_range[1]) &
        (meals_df["facility"].isin(f["facility"].unique()))
    ]

# Shorts: apply date + facility filters only (no waste reason / RTH)
if not shorts_df.empty:
    if selected_weeks is not None:
        shorts_f = shorts_df[shorts_df["menu_ship_week"].dt.date.isin(selected_weeks)]
    else:
        shorts_f = shorts_df[
            (shorts_df["menu_ship_week"].dt.date >= date_range[0]) &
            (shorts_df["menu_ship_week"].dt.date <= date_range[1])
        ]
    if sel_facility != "All":
        shorts_f = shorts_f[shorts_f["facility"] == sel_facility]
else:
    shorts_f = shorts_df.copy()


# ── KPI CALCULATIONS ──────────────────────────────────────────────────────────

total_cost          = f["waste_cost"].sum()
cpm_detail          = build_cpm(f, meals_f)
total_meals_matched = cpm_detail["total_meals"].sum()
overall_cpm         = total_cost / total_meals_matched if total_meals_matched > 0 else np.nan

reason_sums    = f.groupby("waste_reason")["waste_cost"].sum()
top_reason     = reason_sums.idxmax() if not reason_sums.empty else "N/A"
top_reason_pct = (reason_sums[top_reason] / total_cost * 100) if total_cost else 0

disposal_cost = f[
    f["waste_reason"].str.lower().str.contains("disposal", na=False)
]["waste_cost"].sum()
disposal_pct  = (disposal_cost / total_cost * 100) if total_cost else 0

# Prior-period comparison for Total Waste Cost delta badge
if selected_weeks is None:
    span        = date_range[1] - date_range[0]
    prior_start = date_range[0] - span
    prior_end   = date_range[0] - timedelta(days=1)
    prior_cost  = wms_df.loc[
        (wms_df["menu_ship_date"].dt.date >= prior_start) &
        (wms_df["menu_ship_date"].dt.date <= prior_end),
        "waste_cost",
    ].sum()
    cost_delta_pct = (total_cost - prior_cost) / prior_cost * 100 if prior_cost else np.nan
else:
    cost_delta_pct = np.nan

if not np.isnan(cost_delta_pct):
    arrow           = "↓" if cost_delta_pct < 0 else "↑"
    cost_delta_str  = f"{arrow} {abs(cost_delta_pct):.1f}% vs prior period"
    cost_delta_good = cost_delta_pct < 0
else:
    cost_delta_str  = None
    cost_delta_good = None


# ── PAGE HEADER ───────────────────────────────────────────────────────────────

range_str = (
    f"{date_range[0].strftime('%b %d')} – {date_range[1].strftime('%b %d, %Y')}"
    if len(date_range) == 2 else ""
)
fac_str = sel_facility if sel_facility != "All" else f"{f['facility'].nunique()} facilities"

st.markdown(
    f'<div class="hc-eyebrow-green">Internal &nbsp;·&nbsp; Operations</div>'
    f'<p class="hc-title">Produce Waste Scorecard</p>'
    f'<p class="hc-eyebrow">{range_str} &nbsp;·&nbsp; {fac_str} &nbsp;·&nbsp; {len(f):,} records</p>',
    unsafe_allow_html=True,
)
st.divider()


# ── KPI CARDS ─────────────────────────────────────────────────────────────────
# Custom HTML cards — st.metric() resists CSS overrides, so we render our own.

k1, k2, k3, k4 = st.columns(4)

with k1:
    st.markdown(kpi_card(
        "Total Waste Cost",
        f"${total_cost:,.0f}",
        delta=cost_delta_str,
        delta_positive=cost_delta_good,
    ), unsafe_allow_html=True)

with k2:
    cpm_val    = f"${overall_cpm:.4f}" if not np.isnan(overall_cpm) else "—"
    meals_note = (f"{total_meals_matched/1e6:.1f}M meals matched"
                  if total_meals_matched > 0 else None)
    st.markdown(kpi_card(
        "Overall CPM",
        cpm_val,
        delta=meals_note,
        delta_positive=None,
        help_text=f"Total waste ${total_cost:,.0f} / {total_meals_matched:,.0f} matched meals",
    ), unsafe_allow_html=True)

with k3:
    st.markdown(kpi_card(
        "Top Waste Reason",
        top_reason,
        delta=f"{top_reason_pct:.1f}% of cost",
        delta_positive=None,
    ), unsafe_allow_html=True)

with k4:
    st.markdown(kpi_card(
        "True Disposal Cost",
        f"${disposal_cost:,.0f}",
        delta=f"{disposal_pct:.1f}% of total",
        delta_positive=None,
    ), unsafe_allow_html=True)

st.divider()


# ── TABS ──────────────────────────────────────────────────────────────────────

tab_trends, tab_cpm, tab_facility, tab_ingredients, tab_po, tab_shorts, tab_table = st.tabs(
    ["Waste Trends", "Cost Per Meal", "By Facility", "By Ingredient", "Purchase Orders", "Shorts Log", "Detail Table"]
)


# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — WASTE TRENDS
# ══════════════════════════════════════════════════════════════════════════════
with tab_trends:
    c1, c2 = st.columns(2)

    with c1:
        wk_cost = f.groupby("week")["waste_cost"].sum().reset_index()
        fig = px.line(
            wk_cost, x="week", y="waste_cost",
            title="Weekly waste cost",
            labels={"week": "Week of", "waste_cost": "Waste Cost ($)"},
            markers=True, color_discrete_sequence=[HC_GREEN],
        )
        fig.update_traces(
            line_width=2,
            marker=dict(size=7, color="#FFFFFF", line=dict(width=2, color=HC_GREEN)),
        )
        fig.update_layout(yaxis_tickprefix="$", yaxis_tickformat=",")
        st.plotly_chart(chart_base(fig), use_container_width=True)

    with c2:
        reason_df = (
            f.groupby("waste_reason")["waste_cost"]
            .sum().reset_index()
            .sort_values("waste_cost", ascending=False)
        )
        fig2 = px.bar(
            reason_df, x="waste_reason", y="waste_cost",
            title="Waste cost by reason — negative bar indicates a correction",
            labels={"waste_reason": "Reason", "waste_cost": "Waste Cost ($)"},
            color="waste_reason",
            color_discrete_sequence=HC_PALETTE,
            text_auto="$.3s",
        )
        fig2.update_layout(
            yaxis_tickprefix="$", yaxis_tickformat=",",
            showlegend=False, xaxis_title=None,
        )
        st.plotly_chart(chart_base(fig2), use_container_width=True)

    section_head("Over time", "Weekly waste by reason")
    wk_reason = f.groupby(["week", "waste_reason"])["waste_cost"].sum().reset_index()
    fig3 = px.area(
        wk_reason, x="week", y="waste_cost", color="waste_reason",
        title="Weekly waste cost — stacked by reason",
        labels={"week": "Week of", "waste_cost": "Waste Cost ($)", "waste_reason": "Reason"},
        color_discrete_sequence=HC_PALETTE,
    )
    fig3.update_layout(yaxis_tickprefix="$", yaxis_tickformat=",")
    st.plotly_chart(chart_base(fig3), use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — CPM
# ══════════════════════════════════════════════════════════════════════════════
with tab_cpm:

    wk_cpm = (
        cpm_detail.groupby("week")
        .apply(lambda g: g["waste_cost"].sum() / g["total_meals"].sum()
               if g["total_meals"].sum() > 0 else np.nan)
        .reset_index(name="cpm")
    )
    fig_cpm1 = px.line(
        wk_cpm, x="week", y="cpm",
        title="Weekly cost per meal — all facilities combined",
        labels={"week": "Week of", "cpm": "CPM ($)"},
        markers=True, color_discrete_sequence=[HC_MELON],
    )
    fig_cpm1.update_traces(
        line_width=2,
        marker=dict(size=7, color="#FFFFFF", line=dict(width=2, color=HC_MELON)),
    )
    fig_cpm1.update_layout(yaxis_tickprefix="$", yaxis_tickformat=".4f")
    st.plotly_chart(chart_base(fig_cpm1), use_container_width=True)

    section_head("By facility", "CPM breakdown")

    c_left, c_right = st.columns(2)

    with c_left:
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
        fac_cpm_tbl = (
            cpm_detail.groupby("facility")
            .agg(waste_cost=("waste_cost", "sum"), total_meals=("total_meals", "sum"))
            .reset_index()
        )
        fac_cpm_tbl["cpm"] = fac_cpm_tbl["waste_cost"] / fac_cpm_tbl["total_meals"].replace(0, np.nan)
        fac_cpm_tbl = fac_cpm_tbl.sort_values("cpm", ascending=False)

        st.markdown(
            '<p class="hc-eyebrow" style="color:#008600;margin-bottom:6px">Summary</p>'
            '<h3 style="font-family:\'Bree Serif\',Georgia,serif;font-size:20px;'
            'color:#1A1A1A;margin:0 0 12px">CPM by facility</h3>',
            unsafe_allow_html=True,
        )
        st.dataframe(
            fac_cpm_tbl,
            use_container_width=True,
            hide_index=True,
            column_config={
                "facility":    st.column_config.TextColumn("Facility"),
                "waste_cost":  st.column_config.NumberColumn("Waste cost",  format="$%.0f"),
                "total_meals": st.column_config.NumberColumn("Total meals", format="%.0f"),
                "cpm":         st.column_config.NumberColumn("CPM",         format="$%.4f"),
            },
        )

    n_facs = cpm_detail["facility"].nunique()
    if n_facs <= 12:
        section_head("Trend", "Weekly CPM by facility")
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
        st.info(
            f"Multi-line CPM chart hidden when more than 12 facilities are shown "
            f"({n_facs} currently). Use the Facility filter to drill in."
        )

    heat_cpm = (
        cpm_detail[cpm_detail["total_meals"] > 0]
        .assign(cpm=lambda d: d["waste_cost"] / d["total_meals"])
        .pivot_table(index="facility", columns="week", values="cpm", aggfunc="mean")
    )
    if not heat_cpm.empty:
        section_head("Heatmap", "CPM by facility x week")
        heat_cpm.columns = [
            c.strftime("%m/%d") if hasattr(c, "strftime") else str(c)
            for c in heat_cpm.columns
        ]
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

    section_head("Over time", "Weekly waste by facility")
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
            f.groupby("ingredient_name")["waste_cost"]
            .sum().reset_index()
            .sort_values("waste_cost", ascending=False)
            .head(top_n)
        )
        fig_ing = px.bar(
            ing, y="ingredient_name", x="waste_cost",
            orientation="h",
            title=f"Top {top_n} ingredients by waste cost",
            labels={"ingredient_name": "", "waste_cost": "Waste Cost ($)"},
            color="waste_cost",
            color_continuous_scale=[[0, HC_CREAM], [1, HC_MELON]],
            text_auto="$.3s",
        )
        fig_ing.update_layout(
            xaxis_tickprefix="$", xaxis_tickformat=",",
            yaxis={"categoryorder": "total ascending"},
            coloraxis_showscale=False,
            height=max(400, top_n * 28),
        )
        st.plotly_chart(chart_base(fig_ing), use_container_width=True)

    with c_right:
        st.markdown(
            '<p class="hc-eyebrow" style="color:#008600;margin-bottom:6px">Ranked table</p>'
            '<h3 style="font-family:\'Bree Serif\',Georgia,serif;font-size:20px;'
            'color:#1A1A1A;margin:0 0 12px">Top ingredients</h3>',
            unsafe_allow_html=True,
        )
        st.dataframe(
            ing.reset_index(drop=True),
            use_container_width=True,
            hide_index=True,
            column_config={
                "ingredient_name": st.column_config.TextColumn("Ingredient"),
                "waste_cost":      st.column_config.NumberColumn("Waste cost", format="$%.2f"),
            },
        )

    section_head("Breakdown", "Ingredients by waste reason")
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
# TAB 5 — PURCHASE ORDERS
# ══════════════════════════════════════════════════════════════════════════════
with tab_po:
    po_df = build_po_analysis(f)

    full_waste = po_df[po_df["full_po_wasted"]]
    total_pos  = len(po_df)
    n_full     = len(full_waste)
    full_cost  = full_waste["waste_cost"].sum()
    avg_pct    = po_df["pct_wasted"].mean() if total_pos else 0

    p1, p2, p3, p4 = st.columns(4)
    with p1:
        st.markdown(kpi_card("Total POs in Period", f"{total_pos:,}"), unsafe_allow_html=True)
    with p2:
        st.markdown(kpi_card(
            "Avg % of PO Wasted", f"{avg_pct:.1f}%",
            help_text="Average across all POs: waste qty / received qty",
        ), unsafe_allow_html=True)
    with p3:
        st.markdown(kpi_card(
            "Fully Wasted POs", f"{n_full:,}",
            delta=f">= {int(FULL_WASTE_THRESHOLD*100)}% of received qty",
            delta_positive=(n_full == 0),
        ), unsafe_allow_html=True)
    with p4:
        st.markdown(kpi_card("Cost of Fully Wasted POs", f"${full_cost:,.0f}"), unsafe_allow_html=True)

    st.divider()

    if n_full > 0:
        section_head("Alert", "Fully wasted purchase orders")
        st.caption(
            f"{n_full} PO{'s' if n_full != 1 else ''} where "
            f">= {int(FULL_WASTE_THRESHOLD*100)}% of received quantity was wasted "
            f"— aggregated across all lot IDs per PO."
        )

        ff1, ff2, ff3 = st.columns(3)
        with ff1:
            fac_opts = ["All"] + sorted(full_waste["facility"].dropna().unique())
            tbl_fac  = st.selectbox("Filter by facility",   fac_opts, key="po_fac")
        with ff2:
            ing_opts = ["All"] + sorted(full_waste["ingredient_name"].dropna().unique())
            tbl_ing  = st.selectbox("Filter by ingredient", ing_opts, key="po_ing")
        with ff3:
            rsn_opts = ["All"] + sorted(full_waste["waste_reason"].dropna().unique())
            tbl_rsn  = st.selectbox("Filter by reason",     rsn_opts, key="po_rsn")

        tbl_data = full_waste.copy()
        if tbl_fac != "All": tbl_data = tbl_data[tbl_data["facility"]        == tbl_fac]
        if tbl_ing != "All": tbl_data = tbl_data[tbl_data["ingredient_name"] == tbl_ing]
        if tbl_rsn != "All": tbl_data = tbl_data[tbl_data["waste_reason"]    == tbl_rsn]

        full_display = tbl_data[[
            "po_number", "facility", "ingredient_name", "menu_ship_date",
            "waste_qty", "received_qty", "pct_wasted", "waste_cost", "n_lots", "waste_reason",
        ]].sort_values("waste_cost", ascending=False).copy()

        st.caption(f"{len(full_display):,} POs shown")
        st.dataframe(
            full_display,
            use_container_width=True,
            hide_index=True,
            column_config={
                "po_number":       st.column_config.TextColumn("PO Number"),
                "facility":        st.column_config.TextColumn("Facility"),
                "ingredient_name": st.column_config.TextColumn("Ingredient"),
                "menu_ship_date":  st.column_config.DateColumn("Menu week",     format="MMM D, YYYY"),
                "waste_qty":       st.column_config.NumberColumn("Waste qty",    format="%.2f"),
                "received_qty":    st.column_config.NumberColumn("Received qty", format="%.2f"),
                "pct_wasted":      st.column_config.ProgressColumn(
                                       "% Wasted", min_value=0, max_value=100, format="%.1f%%"),
                "waste_cost":      st.column_config.NumberColumn("Waste cost",   format="$%.2f"),
                "n_lots":          st.column_config.NumberColumn("Lots",         format="%d"),
                "waste_reason":    st.column_config.TextColumn("Primary reason"),
            },
        )
    else:
        st.success("No fully wasted POs in the selected period.")

    st.divider()

    c1, c2 = st.columns(2)

    with c1:
        fig_dist = px.histogram(
            po_df[po_df["pct_wasted"] > 0],
            x="pct_wasted", nbins=20,
            title="Distribution of POs by % wasted",
            labels={"pct_wasted": "% of PO Wasted", "count": "Number of POs"},
            color_discrete_sequence=[HC_GREEN],
        )
        fig_dist.add_vrect(
            x0=FULL_WASTE_THRESHOLD * 100, x1=100,
            fillcolor=HC_MELON, opacity=0.15,
            annotation_text="Fully wasted zone",
            annotation_font_color=HC_MELON,
            annotation_position="top left",
            line_width=0,
        )
        fig_dist.update_layout(xaxis_ticksuffix="%")
        st.plotly_chart(chart_base(fig_dist), use_container_width=True)

    with c2:
        top_po = po_df.nlargest(15, "waste_cost")
        fig_top = px.bar(
            top_po.sort_values("waste_cost"),
            y="po_number", x="waste_cost",
            orientation="h",
            title="Top 15 POs by waste cost",
            labels={"po_number": "PO Number", "waste_cost": "Waste Cost ($)"},
            color="full_po_wasted",
            color_discrete_map={True: HC_MELON, False: HC_GREEN},
            hover_data=["ingredient_name", "facility", "pct_wasted"],
            text_auto="$.3s",
        )
        fig_top.update_layout(
            xaxis_tickprefix="$", xaxis_tickformat=",",
            legend_title_text="Fully Wasted",
        )
        st.plotly_chart(chart_base(fig_top), use_container_width=True)

    section_head("Ingredients", "PO waste by ingredient")
    st.caption("Aggregated across all POs and lot IDs per ingredient.")

    ing_po = (
        po_df.groupby("ingredient_name")
        .agg(
            avg_pct_wasted   = ("pct_wasted",    "mean"),
            total_pos        = ("po_number",      "count"),
            fully_wasted_pos = ("full_po_wasted", "sum"),
            total_waste_cost = ("waste_cost",     "sum"),
            total_waste_qty  = ("waste_qty",      "sum"),
            total_received   = ("received_qty",   "sum"),
        )
        .reset_index()
    )
    ing_po["pct_pos_fully_wasted"] = (
        ing_po["fully_wasted_pos"] / ing_po["total_pos"] * 100
    ).fillna(0)
    ing_po["overall_pct_wasted"] = (
        ing_po["total_waste_qty"] / ing_po["total_received"].replace(0, np.nan) * 100
    ).clip(upper=100).fillna(0)

    top_n_ing = st.slider("Show top N ingredients", 10, 50, 20, key="po_ing_slider")
    top_ing   = ing_po.nlargest(top_n_ing, "avg_pct_wasted")

    ci1, ci2 = st.columns(2)

    with ci1:
        fig_ing_pct = px.bar(
            top_ing.sort_values("avg_pct_wasted"),
            y="ingredient_name", x="avg_pct_wasted",
            orientation="h",
            title=f"Top {top_n_ing} ingredients — avg % of PO wasted",
            labels={"ingredient_name": "", "avg_pct_wasted": "Avg % of PO Wasted"},
            color="avg_pct_wasted",
            color_continuous_scale=[[0, HC_GREEN], [0.5, HC_LEMON], [1, HC_MELON]],
            text_auto=".1f",
        )
        fig_ing_pct.update_traces(texttemplate="%{x:.1f}%", textposition="outside")
        fig_ing_pct.update_layout(
            xaxis_ticksuffix="%",
            yaxis={"categoryorder": "total ascending"},
            coloraxis_showscale=False,
            height=max(400, top_n_ing * 28),
        )
        st.plotly_chart(chart_base(fig_ing_pct), use_container_width=True)

    with ci2:
        fig_ing_cost = px.bar(
            top_ing.sort_values("total_waste_cost"),
            y="ingredient_name", x="total_waste_cost",
            orientation="h",
            title=f"Top {top_n_ing} ingredients — total PO waste cost",
            labels={"ingredient_name": "", "total_waste_cost": "Total Waste Cost ($)"},
            color="avg_pct_wasted",
            color_continuous_scale=[[0, HC_GREEN], [0.5, HC_LEMON], [1, HC_MELON]],
            text_auto="$.3s",
        )
        fig_ing_cost.update_layout(
            xaxis_tickprefix="$", xaxis_tickformat=",",
            yaxis={"categoryorder": "total ascending"},
            coloraxis_showscale=False,
            height=max(400, top_n_ing * 28),
        )
        st.plotly_chart(chart_base(fig_ing_cost), use_container_width=True)

    section_head("Summary", "Ingredient summary table")
    ing_display = ing_po.sort_values("avg_pct_wasted", ascending=False).copy()
    ing_display = ing_display[[
        "ingredient_name", "total_pos", "fully_wasted_pos",
        "pct_pos_fully_wasted", "avg_pct_wasted", "overall_pct_wasted", "total_waste_cost",
    ]]
    st.dataframe(
        ing_display,
        use_container_width=True,
        hide_index=True,
        column_config={
            "ingredient_name":      st.column_config.TextColumn("Ingredient"),
            "total_pos":            st.column_config.NumberColumn("Total POs",        format="%d"),
            "fully_wasted_pos":     st.column_config.NumberColumn("Fully wasted POs", format="%d"),
            "pct_pos_fully_wasted": st.column_config.ProgressColumn(
                                        "% POs fully wasted",  min_value=0, max_value=100, format="%.1f%%"),
            "avg_pct_wasted":       st.column_config.ProgressColumn(
                                        "Avg % wasted per PO", min_value=0, max_value=100, format="%.1f%%"),
            "overall_pct_wasted":   st.column_config.ProgressColumn(
                                        "Overall % wasted",    min_value=0, max_value=100, format="%.1f%%"),
            "total_waste_cost":     st.column_config.NumberColumn("Total waste cost", format="$%.2f"),
        },
    )

    st.divider()

    scatter_data = po_df[(po_df["received_qty"] > 0) & (po_df["waste_qty"] > 0)]
    fig_scatter = px.scatter(
        scatter_data,
        x="received_qty", y="waste_qty",
        color="full_po_wasted",
        color_discrete_map={True: HC_MELON, False: HC_GREEN},
        hover_data=["po_number", "ingredient_name", "facility", "pct_wasted"],
        title="Received quantity vs. waste quantity — log scale, by PO",
        labels={
            "received_qty":   "Received Qty (log)",
            "waste_qty":      "Waste Qty (log)",
            "full_po_wasted": "Fully Wasted",
        },
        log_x=True, log_y=True, opacity=0.7,
    )
    log_min = max(scatter_data[["received_qty", "waste_qty"]].min().min(), 0.01)
    log_max = scatter_data[["received_qty", "waste_qty"]].max().max()
    fig_scatter.add_shape(
        type="line",
        x0=log_min, y0=log_min, x1=log_max, y1=log_max,
        line=dict(color=HC_MELON, dash="dash", width=1.5),
    )
    fig_scatter.add_annotation(
        x=np.log10(log_max) * 0.85, y=np.log10(log_max) * 0.97,
        text="100% wasted line",
        showarrow=False,
        font=dict(color=HC_MELON, size=11),
        xref="x", yref="y",
    )
    st.plotly_chart(chart_base(fig_scatter, height=450), use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# TAB 6 — SHORTS LOG
# ══════════════════════════════════════════════════════════════════════════════
with tab_shorts:
    if shorts_f.empty:
        st.info("No produce shorts found for the selected period and filters.")
    else:
        # ── KPI cards ────────────────────────────────────────────────────────
        total_shorts    = len(shorts_f)
        top_short_ing   = shorts_f["shorted_ingredient"].mode()[0] if total_shorts else "—"
        top_short_rsn   = shorts_f["short_reason"].mode()[0] if total_shorts else "—"
        facs_affected   = shorts_f["facility"].nunique()

        sk1, sk2, sk3, sk4 = st.columns(4)
        with sk1:
            st.markdown(kpi_card("Total Produce Shorts", f"{total_shorts:,}"), unsafe_allow_html=True)
        with sk2:
            st.markdown(kpi_card("Most Shorted Ingredient", top_short_ing), unsafe_allow_html=True)
        with sk3:
            st.markdown(kpi_card("Top Short Reason", top_short_rsn), unsafe_allow_html=True)
        with sk4:
            st.markdown(kpi_card("Facilities Affected", f"{facs_affected}"), unsafe_allow_html=True)

        st.divider()

        # ── Row 1: top ingredients + reason breakdown ─────────────────────
        r1a, r1b = st.columns(2)

        with r1a:
            top_n_s = st.slider("Show top N ingredients", 10, 50, 20, key="shorts_ing_slider")
            ing_counts = (
                shorts_f.groupby("shorted_ingredient")
                .size().reset_index(name="shorts")
                .sort_values("shorts", ascending=False)
                .head(top_n_s)
            )
            fig_sing = px.bar(
                ing_counts.sort_values("shorts"),
                y="shorted_ingredient", x="shorts",
                orientation="h",
                title=f"Top {top_n_s} most shorted produce ingredients",
                labels={"shorted_ingredient": "", "shorts": "Short count"},
                color="shorts",
                color_continuous_scale=[[0, HC_CREAM], [1, HC_MELON]],
                text_auto=True,
            )
            fig_sing.update_layout(
                yaxis={"categoryorder": "total ascending"},
                coloraxis_showscale=False,
                height=max(400, top_n_s * 28),
            )
            st.plotly_chart(chart_base(fig_sing), use_container_width=True)

        with r1b:
            rsn_counts = (
                shorts_f.groupby("short_reason")
                .size().reset_index(name="shorts")
                .sort_values("shorts", ascending=False)
            )
            fig_srsn = px.bar(
                rsn_counts,
                x="short_reason", y="shorts",
                title="Short count by reason",
                labels={"short_reason": "Reason", "shorts": "Short count"},
                color="short_reason",
                color_discrete_sequence=HC_PALETTE,
                text_auto=True,
            )
            fig_srsn.update_layout(showlegend=False, xaxis_title=None)
            st.plotly_chart(chart_base(fig_srsn), use_container_width=True)

        # ── Weekly trend ──────────────────────────────────────────────────
        section_head("Over time", "Weekly produce shorts")
        wk_shorts = shorts_f.groupby("week").size().reset_index(name="shorts")
        fig_swk = px.line(
            wk_shorts, x="week", y="shorts",
            title="Weekly produce short count",
            labels={"week": "Week of", "shorts": "Short count"},
            markers=True, color_discrete_sequence=[HC_MELON],
        )
        fig_swk.update_traces(
            line_width=2,
            marker=dict(size=7, color="#FFFFFF", line=dict(width=2, color=HC_MELON)),
        )
        st.plotly_chart(chart_base(fig_swk), use_container_width=True)

        # ── Reason × facility heatmap ─────────────────────────────────────
        section_head("By facility", "Short reason breakdown per site")
        heat_s = (
            shorts_f.groupby(["facility", "short_reason"])
            .size().unstack(fill_value=0)
        )
        if not heat_s.empty:
            fig_sheat = px.imshow(
                heat_s,
                title="Short count — facility by reason",
                labels={"x": "Reason", "y": "Facility", "color": "Shorts"},
                color_continuous_scale=[[0, "#FFFFFF"], [0.5, HC_LEMON], [1, HC_MELON]],
                aspect="auto",
                text_auto=True,
            )
            fig_sheat.update_layout(
                height=max(320, len(heat_s) * 44 + 80),
                coloraxis_colorbar=dict(title="Shorts"),
            )
            st.plotly_chart(chart_base(fig_sheat), use_container_width=True)

        # ── Shorts vs waste cost correlation ──────────────────────────────
        section_head("Correlation", "Shorts vs waste cost by week")
        st.caption(
            "Each point is one facility-week. Weeks with more shorts trending "
            "toward higher waste cost suggest a supply disruption signal."
        )
        shorts_by_wk = (
            shorts_f.groupby(["facility", "week"])
            .size().reset_index(name="short_count")
        )
        waste_by_wk = (
            f.groupby(["facility", "week"])["waste_cost"]
            .sum().reset_index()
        )
        corr_df = shorts_by_wk.merge(waste_by_wk, on=["facility", "week"], how="inner")

        if not corr_df.empty:
            fig_corr = px.scatter(
                corr_df,
                x="short_count", y="waste_cost",
                color="facility",
                color_discrete_sequence=HC_PALETTE,
                hover_data=["facility", "week", "short_count", "waste_cost"],
                title="Weekly shorts vs waste cost — by facility",
                labels={
                    "short_count": "Produce shorts (count)",
                    "waste_cost":  "Waste cost ($)",
                    "facility":    "Facility",
                },
                trendline="ols",
                opacity=0.75,
            )
            fig_corr.update_layout(
                yaxis_tickprefix="$", yaxis_tickformat=",",
                height=460,
            )
            st.plotly_chart(chart_base(fig_corr), use_container_width=True)
        else:
            st.info("Not enough overlapping weeks between shorts and waste data to plot correlation.")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 7 — DETAIL TABLE
# ══════════════════════════════════════════════════════════════════════════════
with tab_table:
    # Toolbar: full-text search + column filters
    tt1, tt2, tt3, tt4 = st.columns([3, 1.4, 1.4, 1.4])
    with tt1:
        search = st.text_input(
            "Search",
            placeholder="Search ingredients, reasons, facilities…",
            label_visibility="collapsed",
            key="dt_search",
        )
    with tt2:
        dt_fac = st.selectbox(
            "Facility", ["All facilities"] + sorted(f["facility"].dropna().unique()),
            label_visibility="collapsed", key="dt_fac",
        )
    with tt3:
        dt_rsn = st.selectbox(
            "Reason", ["All reasons"] + sorted(f["waste_reason"].dropna().unique()),
            label_visibility="collapsed", key="dt_rsn",
        )
    with tt4:
        dt_uom = st.selectbox(
            "UOM", ["All UOMs"] + sorted(f["uom"].dropna().unique()),
            label_visibility="collapsed", key="dt_uom",
        )

    dt = f.copy()
    if dt_fac != "All facilities": dt = dt[dt["facility"]     == dt_fac]
    if dt_rsn != "All reasons":    dt = dt[dt["waste_reason"] == dt_rsn]
    if dt_uom != "All UOMs":       dt = dt[dt["uom"]          == dt_uom]
    if search:
        s  = search.lower()
        dt = dt[
            dt["ingredient_name"].str.lower().str.contains(s, na=False) |
            dt["facility"].str.lower().str.contains(s, na=False) |
            dt["waste_reason"].str.lower().str.contains(s, na=False) |
            dt["waste_reason_detail"].str.lower().str.contains(s, na=False)
        ]

    st.markdown(
        f'<p class="hc-eyebrow" style="margin-bottom:8px">'
        f'{len(dt):,} rows &nbsp;·&nbsp; sorted by created date desc</p>',
        unsafe_allow_html=True,
    )

    display_cols = [
        "created_date", "facility", "ingredient_name", "uom",
        "quantity", "waste_reason", "waste_reason_detail",
        "menu_ship_date", "waste_cost", "is_rth",
    ]
    existing = [c for c in display_cols if c in dt.columns]
    detail   = dt[existing].sort_values("created_date", ascending=False).copy()

    st.dataframe(
        detail,
        use_container_width=True,
        hide_index=True,
        height=560,
        column_config={
            "created_date":        st.column_config.DateColumn("Created",      format="MMM D, YYYY"),
            "facility":            st.column_config.TextColumn("Facility"),
            "ingredient_name":     st.column_config.TextColumn("Ingredient"),
            "uom":                 st.column_config.TextColumn("UOM",          width="small"),
            "quantity":            st.column_config.NumberColumn("Qty",        format="%.2f"),
            "waste_reason":        st.column_config.TextColumn("Reason"),
            "waste_reason_detail": st.column_config.TextColumn("Detail"),
            "menu_ship_date":      st.column_config.DateColumn("Menu week",    format="MMM D"),
            "waste_cost":          st.column_config.NumberColumn("Waste cost", format="$%.2f"),
            "is_rth":              st.column_config.TextColumn("RTH",          width="small"),
        },
    )

    csv = dt[existing].to_csv(index=False).encode("utf-8")
    st.download_button("Download as CSV", csv, "produce_waste_filtered.csv", "text/csv")
