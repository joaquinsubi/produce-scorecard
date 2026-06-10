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
    color: #008600 !important; margin: 0 0 4px;
}
.hc-section-head__title {
    font-family: 'Bree Serif', Georgia, serif;
    font-size: 22px; line-height: 1.15;
    color: #1A1A1A !important; margin: 0;
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
section[data-testid="stSidebar"] [data-testid="stPills"] button,
section[data-testid="stSidebar"] [data-testid="stBaseButton-pills"],
section[data-testid="stSidebar"] button[kind="pills"],
section[data-testid="stSidebar"] .stPills button {
    background: #1A4F7A !important;
    border: 1px solid rgba(254,249,245,0.25) !important;
    border-radius: 999px !important;
    color: rgba(254,249,245,0.85) !important;
    font-family: 'Karla',sans-serif !important;
    font-size: 11px !important;
    font-weight: 700 !important;
    padding: 4px 10px !important;
    white-space: nowrap !important;
}
section[data-testid="stSidebar"] [data-testid="stPills"] button[aria-pressed="true"],
section[data-testid="stSidebar"] [data-testid="stPills"] button[data-active="true"],
section[data-testid="stSidebar"] [data-testid="stBaseButton-pills"][aria-pressed="true"],
section[data-testid="stSidebar"] [data-testid="stBaseButton-pills"][data-active="true"],
section[data-testid="stSidebar"] button[kind="pills"][aria-pressed="true"] {
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

/* ── expanders ── */
[data-testid="stExpander"] {
    border: 1px solid #E6E0D8 !important;
    border-radius: 12px !important;
    background: #FFFFFF !important;
    margin-bottom: 12px !important;
    overflow: hidden !important;
}
[data-testid="stExpander"] summary {
    background: #FFFFFF !important;
    padding: 14px 20px !important;
    font-family: 'Karla', sans-serif !important;
    font-size: 13px !important;
    font-weight: 700 !important;
    letter-spacing: 0.06em !important;
    text-transform: uppercase !important;
    color: #0B355A !important;
    border-radius: 12px !important;
}
[data-testid="stExpander"] summary:hover {
    background: #F5F0EB !important;
}
[data-testid="stExpander"] summary svg {
    color: #008600 !important;
    fill: #008600 !important;
}
[data-testid="stExpander"] > div:last-child {
    padding: 8px 20px 20px !important;
    background: #FFFFFF !important;
    color: #1A1A1A !important;
}

/* ── equal-height KPI card columns ── */
[data-testid="stHorizontalBlock"] { align-items: stretch !important; }
[data-testid="stHorizontalBlock"] [data-testid="stColumn"] > div {
    height: 100% !important;
    display: flex !important;
    flex-direction: column !important;
}
[data-testid="stHorizontalBlock"] [data-testid="stColumn"] > div > div[data-testid="stMarkdownContainer"] {
    flex: 1 !important;
    display: flex !important;
    flex-direction: column !important;
}
[data-testid="stHorizontalBlock"] [data-testid="stColumn"] > div > div[data-testid="stMarkdownContainer"] > div {
    height: 100% !important;
}

/* ── dark-mode compat: portal-rendered dropdowns escape the theme vars ── */
[data-baseweb="popover"],
[data-baseweb="tooltip"] {
    background-color: #FFFFFF !important;
    border: 1px solid #E6E0D8 !important;
    border-radius: 12px !important;
    box-shadow: 0 4px 16px rgba(11,53,90,0.12) !important;
}
[data-baseweb="menu"] [role="option"] {
    background-color: #FFFFFF !important;
    color: #1A1A1A !important;
}
[data-baseweb="menu"] [role="option"]:hover,
[data-baseweb="menu"] [role="option"][aria-selected="true"] {
    background-color: #F5F0EB !important;
    color: #1A1A1A !important;
}

/* multiselect tags */
[data-baseweb="tag"] {
    background-color: rgba(0,134,0,0.10) !important;
    color: #008600 !important;
    border-color: rgba(0,134,0,0.25) !important;
}
[data-baseweb="tag"] span { color: #008600 !important; }

/* text input in detail table search bar */
.stTextInput input {
    background-color: #FFFFFF !important;
    color: #1A1A1A !important;
    border: 1px solid #E6E0D8 !important;
    border-radius: 8px !important;
}
.stTextInput input::placeholder { color: #7A7A7A !important; }

/* selectbox control in main content */
.main .stSelectbox [data-baseweb="select"] > div {
    background-color: #FFFFFF !important;
    color: #1A1A1A !important;
    border-color: #E6E0D8 !important;
}
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
    """Renders a ruled section header with a Bree Serif title."""
    st.markdown(
        f'<div class="hc-section-head">'
        f'<h2 class="hc-section-head__title">{title}</h2>'
        f'</div>',
        unsafe_allow_html=True,
    )


def fmt_weeks(df: pd.DataFrame, col: str = "week") -> pd.DataFrame:
    """Sort by the ISO week string then reformat to 'Mmm D' for display.
    Using category strings prevents Plotly's JS from UTC→local conversion."""
    df = df.sort_values(col).copy()
    df[col] = (
        pd.to_datetime(df[col], errors="coerce")
        .dt.strftime("%b %d")
        .str.replace(r" 0(\d)$", r" \1", regex=True)  # strip leading zero: "May 01" → "May 1"
    )
    return df


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
        f'min-height:140px;height:100%;box-sizing:border-box;">'
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
    po_raw     = book.worksheet("Purchase Orders").get_all_values()
    rvw_raw    = book.worksheet("Received_vs_Wasted").get_all_values()
    cars_raw   = book.worksheet("CARs").get_all_values()
    return wms_raw, meals_raw, menus_raw, shorts_raw, po_raw, rvw_raw, cars_raw


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
    df["week"]     = (df["menu_ship_date"] - pd.to_timedelta(df["menu_ship_date"].dt.dayofweek, unit="D")).dt.normalize().dt.strftime("%Y-%m-%d")

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

    # Normalize facility names to match WMS names
    FACILITY_MAP = {
        "chicago midway": "Chicago",
        "chicago":        "Chicago",
        "skyview":        "Skyview",
        "san bernardino": "San Bernardino",
        "baltimore":      "Baltimore",
    }

    df["menu_ship_week"]     = pd.to_datetime(df["menu_ship_week"], errors="coerce")
    df["facility"]           = (df["facility"].astype(str).str.strip()
                                 .apply(lambda x: FACILITY_MAP.get(x.lower(), x)))
    df["shorted_ingredient"] = df["shorted_ingredient"].astype(str).str.strip()
    df["short_reason"]       = df["short_reason"].astype(str).str.strip()
    df["category"]           = df["category"].astype(str).str.strip()
    df["week"]               = (df["menu_ship_week"] - pd.to_timedelta(df["menu_ship_week"].dt.dayofweek, unit="D")).dt.normalize().dt.strftime("%Y-%m-%d")

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
    _d = pd.to_datetime(merged["menu_ship_date"])
    merged["week"] = (_d - pd.to_timedelta(_d.dt.dayofweek, unit="D")).dt.normalize().dt.strftime("%Y-%m-%d")
    merged["cpm"]  = merged["waste_cost"] / merged["total_meals"].replace(0, np.nan)
    return merged


def parse_rvw(raw: list) -> pd.DataFrame:
    """Parse Received_vs_Wasted sheet.
    Col A=menu_ship_week, B=facility, C=ingredient_id, D=po_number,
    E=uom, F=total_received, G=total_wasted, H=pct_wasted
    """
    if len(raw) < 2:
        return pd.DataFrame()
    df = pd.DataFrame(raw[1:])
    col_map = {0: "menu_ship_week", 1: "facility", 2: "ingredient_id",
               3: "po_number", 5: "total_received", 6: "total_wasted", 7: "pct_wasted_rvw"}
    valid = {k: v for k, v in col_map.items() if k < df.shape[1]}
    df = df.rename(columns=valid)[list(valid.values())]
    df["menu_ship_week"] = pd.to_datetime(df["menu_ship_week"], errors="coerce")
    df["po_number"]      = df["po_number"].astype(str).str.strip()
    df["ingredient_id"]  = df["ingredient_id"].astype(str).str.strip()
    for col in ["total_received", "total_wasted"]:
        df[col] = pd.to_numeric(
            df[col].astype(str).str.replace(",", "").str.replace("$", "").str.strip(),
            errors="coerce"
        ).fillna(0)
    df["pct_wasted_rvw"] = pd.to_numeric(
        df["pct_wasted_rvw"].astype(str).str.replace("%", "").str.strip(),
        errors="coerce"
    )
    return df.dropna(subset=["po_number"])


def parse_cars(raw: list) -> pd.DataFrame:
    """Parse CARs sheet.
    D=report_date, E=meal, G=ingredient_name_raw,
    N=po_numbers, O=supplier, P=ship_week, Y=investigation_number,
    Z=ingredient_id, AA=category (keep 'Produce' only), AB=facility.
    """
    if len(raw) < 2:
        return pd.DataFrame()
    df = pd.DataFrame(raw[1:])
    col_map = {
        3:  "report_date",
        4:  "meal",
        6:  "ingredient_name_raw",
        13: "po_numbers",
        14: "supplier",
        15: "ship_week",
        24: "investigation_number",
        25: "ingredient_id",
        26: "category",
        27: "facility",
    }
    valid = {k: v for k, v in col_map.items() if k < df.shape[1]}
    df = df.rename(columns=valid)[list(valid.values())]

    # Keep Produce CARs only
    if "category" in df.columns:
        df = df[df["category"].astype(str).str.strip().str.lower() == "produce"].copy()

    df["ship_week"]            = pd.to_datetime(df["ship_week"],   errors="coerce")
    df["report_date"]          = pd.to_datetime(df["report_date"], errors="coerce")
    df["ingredient_id"]        = df["ingredient_id"].astype(str).str.strip()
    df["supplier"]             = df["supplier"].astype(str).str.strip()
    df["facility"]             = df["facility"].astype(str).str.strip()
    df["investigation_number"] = df["investigation_number"].astype(str).str.strip()
    df["po_numbers"]           = df["po_numbers"].astype(str).str.strip()
    df["meal"]                 = df["meal"].astype(str).str.strip()
    return df.dropna(subset=["ship_week"])


def build_po_analysis(wms: pd.DataFrame, rvw: pd.DataFrame) -> pd.DataFrame:
    """One row per PO-ingredient combination. Uses Received_vs_Wasted for
    correct total received/wasted quantities across all lot IDs."""
    po = wms[wms["po_number"].astype(str).str.strip().ne("")].copy()
    po["po_number"]     = po["po_number"].astype(str).str.strip()
    po["ingredient_id"] = po["ingredient_id"].astype(str).str.strip()

    agg = po.groupby(["po_number", "ingredient_id", "ingredient_name"]).agg(
        facility       = ("facility",       "first"),
        menu_ship_date = ("menu_ship_date", "first"),
        waste_cost     = ("waste_cost",     "sum"),
        waste_reason   = ("waste_reason",   lambda x: x.mode()[0] if not x.mode().empty else ""),
        n_lots         = ("lot_id",         "nunique"),
        wms_waste_qty  = ("quantity",       "sum"),
        wms_recv_qty   = ("received_qty",   "sum"),
    ).reset_index()

    # Join Received_vs_Wasted for correct total quantities
    if not rvw.empty:
        # Aggregate across all rows per PO+ingredient before joining — multiple rows
        # can exist (e.g. one per facility) and drop_duplicates() would keep an arbitrary
        # one, inflating pct_wasted when the 100% row sorts first.
        rvw_agg = (
            rvw.groupby(["po_number", "ingredient_id"], as_index=False)
            .agg(total_received=("total_received", "sum"), total_wasted=("total_wasted", "sum"))
        )
        rvw_agg["pct_wasted_rvw"] = (
            rvw_agg["total_wasted"] / rvw_agg["total_received"].replace(0, np.nan) * 100
        ).clip(upper=100)
        agg = agg.merge(rvw_agg, on=["po_number", "ingredient_id"], how="left")
        agg["received_qty"] = agg["total_received"].fillna(agg["wms_recv_qty"])
        agg["waste_qty"]    = agg["total_wasted"].fillna(agg["wms_waste_qty"])
        agg["pct_wasted"]   = agg["pct_wasted_rvw"].fillna(
            (agg["wms_waste_qty"] / agg["wms_recv_qty"].replace(0, np.nan) * 100).clip(upper=100)
        )
    else:
        agg["received_qty"] = agg["wms_recv_qty"]
        agg["waste_qty"]    = agg["wms_waste_qty"]
        agg["pct_wasted"]   = (agg["waste_qty"] / agg["received_qty"].replace(0, np.nan) * 100).clip(upper=100)

    agg["pct_wasted"]     = agg["pct_wasted"].clip(upper=100)
    agg["full_po_wasted"] = agg["pct_wasted"] >= (FULL_WASTE_THRESHOLD * 100)
    return agg


# ── LOAD DATA ─────────────────────────────────────────────────────────────────

try:
    wms_raw, meals_raw, menus_raw, shorts_raw, po_raw, rvw_raw, cars_raw = load_raw()
    wms_df    = parse_wms(wms_raw)
    meals_df  = parse_meals(meals_raw)
    shorts_df = parse_shorts(shorts_raw)
    rvw_df    = parse_rvw(rvw_raw)
    cars_df   = parse_cars(cars_raw)
    # Join ingredient names from WMS lookup; fall back to raw combined text from col G
    if not cars_df.empty and not wms_df.empty:
        _ing_lkp = wms_df[["ingredient_id", "ingredient_name"]].drop_duplicates("ingredient_id")
        cars_df  = cars_df.merge(_ing_lkp, on="ingredient_id", how="left")
        cars_df["ingredient_name"] = cars_df["ingredient_name"].fillna(
            cars_df["ingredient_name_raw"]
        )
    elif not cars_df.empty:
        cars_df["ingredient_name"] = cars_df["ingredient_name_raw"]

    # Parse Purchase Orders sheet: col A=PO#, col B=facility, col K=ship week, col N=case cost
    _po_rows = []
    for _row in po_raw[1:]:
        if len(_row) > 13:
            try:
                _cost = float(str(_row[13]).replace(",", "").replace("$", "").strip())
            except (ValueError, TypeError):
                continue
            _date = pd.to_datetime(_row[10], errors="coerce") if len(_row) > 10 else pd.NaT
            _fac  = str(_row[1]).strip() if len(_row) > 1 else ""
            _po   = str(_row[0]).strip() if len(_row) > 0 else ""
            _iid  = str(_row[2]).strip() if len(_row) > 2 else ""
            _po_rows.append({
                "po_number":      _po,
                "ingredient_id":  _iid,
                "menu_ship_week": _date,
                "facility":       _fac,
                "case_cost":      _cost,
            })
    po_costs_df = pd.DataFrame(_po_rows) if _po_rows else pd.DataFrame(
        columns=["po_number", "ingredient_id", "menu_ship_week", "facility", "case_cost"]
    )
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
    st.caption("Adjust filters and press Apply.")
    st.divider()

    # Pre-compute date anchors — don't depend on filter state
    data_min = wms_df["menu_ship_date"].dropna().min().date()
    data_max = wms_df["menu_ship_date"].dropna().max().date()
    today    = date.today()
    # Fiscal year starts Feb 1; if we're still in Jan, roll back to prior year
    fiscal_start = (
        date(today.year, 2, 1) if today.month >= 2
        else date(today.year - 1, 2, 1)
    )

    wms_week_dates = set(wms_df["menu_ship_date"].dt.date.dropna().unique())
    week_date_objs = sorted([w.date() for w in menu_weeks if w.date() in wms_week_dates])
    week_labels    = [w.strftime("%b %d, %Y") for w in week_date_objs]
    week_label_map = {w.strftime("%b %d, %Y"): w for w in week_date_objs}

    st.markdown("**Menu Ship Week**")
    preset = st.pills(
        "Quick select",
        ["YTD", "4W", "8W", "12W", "Pick"],
        default="YTD",
        label_visibility="collapsed",
    )
    if preset is None:
        preset = "YTD"

    # Multiselect only shown (and only meaningful) when Pick is active
    if preset == "Pick":
        chosen_labels = st.multiselect(
            "Pick menu weeks",
            options=week_labels,
            default=[],
            label_visibility="collapsed",
            placeholder="Choose one or more menu weeks…",
        )
    else:
        chosen_labels = []

    st.divider()
    facilities   = ["All"] + sorted(wms_df["facility"].dropna().unique())
    sel_facility = st.selectbox("Facility", facilities)

    reasons    = ["All"] + sorted(wms_df["waste_reason"].dropna().unique())
    sel_reason = st.selectbox("Waste Reason", reasons)

    rth_opts = ["All"] + sorted(wms_df["is_rth"].dropna().unique())
    sel_rth  = st.selectbox("RTH / Non-RTH", rth_opts)

    # Derive the active date range
    selected_weeks = None
    if preset == "YTD":
        date_range = (fiscal_start, data_max)
    elif preset == "4W":
        date_range = (data_max - timedelta(weeks=4), data_max)
    elif preset == "8W":
        date_range = (data_max - timedelta(weeks=8), data_max)
    elif preset == "12W":
        date_range = (data_max - timedelta(weeks=12), data_max)
    else:  # Pick
        date_range     = (data_min, data_max)
        selected_weeks = [week_label_map[l] for l in chosen_labels]

    if preset != "Pick":
        st.caption(f"{date_range[0].strftime('%b %d')} – {date_range[1].strftime('%b %d, %Y')}")
    elif chosen_labels:
        st.caption(f"{len(chosen_labels)} week{'s' if len(chosen_labels) != 1 else ''} selected")

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

# Filter Purchase Orders CASE_COST by same date + facility as main data
_pc = po_costs_df.copy()
if not _pc.empty:
    if selected_weeks is not None:
        _pc = _pc[_pc["menu_ship_week"].dt.date.isin(selected_weeks)]
    else:
        _pc = _pc[
            (_pc["menu_ship_week"].dt.date >= date_range[0]) &
            (_pc["menu_ship_week"].dt.date <= date_range[1])
        ]
    if sel_facility != "All":
        _pc = _pc[_pc["facility"].str.lower() == sel_facility.lower()]
total_case_cost = _pc["case_cost"].sum() if not _pc.empty else 0.0

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
    f'<p class="hc-title">Produce Scorecard</p>'
    f'<p class="hc-eyebrow">{range_str} &nbsp;·&nbsp; {fac_str} &nbsp;·&nbsp; {len(f):,} records</p>',
    unsafe_allow_html=True,
)
st.divider()


# ── HELPERS ───────────────────────────────────────────────────────────────────

def _nid(s):
    """Normalize ingredient_id to a canonical string for joins."""
    try:
        return str(int(float(str(s).strip())))
    except (ValueError, TypeError):
        return str(s).strip()


# ── TABS ──────────────────────────────────────────────────────────────────────

tab_summary, tab_ingredient, tab_shorts, tab_trends, tab_po, tab_table, tab_cars = st.tabs(
    ["Summary", "Ingredient Lookup", "Shorts Log", "Waste Trends", "Purchase Orders", "Detail Table", "CARs"]
)


# ══════════════════════════════════════════════════════════════════════════════
# TAB 0 — SUMMARY
# ══════════════════════════════════════════════════════════════════════════════
with tab_summary:

    # ── KPI cards ──────────────────────────────────────────────────────────────
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
        if not shorts_f.empty:
            _n_wks = shorts_f["week"].nunique()
            _avg   = len(shorts_f) / _n_wks if _n_wks > 0 else 0
            st.markdown(kpi_card(
                "Avg Shorts / Week",
                f"{_avg:.1f}",
                delta=f"{len(shorts_f):,} total produce shorts",
                delta_positive=None,
            ), unsafe_allow_html=True)
        else:
            st.markdown(kpi_card("Avg Shorts / Week", "—"), unsafe_allow_html=True)

    with k4:
        if total_case_cost > 0:
            pct_cost_wasted = total_cost / total_case_cost * 100
            st.markdown(kpi_card(
                "% of Cost Wasted",
                f"{pct_cost_wasted:.1f}%",
                delta=f"${total_cost:,.0f} waste / ${total_case_cost:,.0f} purchased",
                delta_positive=None,
                help_text="Total waste cost ÷ total case cost from Purchase Orders",
            ), unsafe_allow_html=True)
        else:
            st.markdown(kpi_card("% of Cost Wasted", "—"), unsafe_allow_html=True)

    st.divider()

    # ── Row 1: Shorts ───────────────────────────────────────────────────────────
    section_head("Shorts", "Shorts by ingredient & site")
    sc1, sc2 = st.columns(2)

    with sc1:
        if not shorts_f.empty:
            top_shorted = (
                shorts_f.groupby("shorted_ingredient")
                .size().reset_index(name="shorts")
                .sort_values("shorts", ascending=False)
                .head(10)
            )
            fig_sum_sing = px.bar(
                top_shorted.sort_values("shorts"),
                y="shorted_ingredient", x="shorts",
                orientation="h",
                title="Top 10 most shorted ingredients",
                labels={"shorted_ingredient": "", "shorts": "Short count"},
                color="shorts",
                color_continuous_scale=[[0, HC_CREAM], [1, HC_MELON]],
                text_auto=True,
            )
            fig_sum_sing.update_layout(
                yaxis={"categoryorder": "total ascending"},
                coloraxis_showscale=False,
                height=360,
            )
            st.plotly_chart(chart_base(fig_sum_sing), use_container_width=True)
        else:
            st.info("No produce shorts in the selected period.")

    with sc2:
        if not shorts_f.empty:
            fac_shorts_sum = (
                shorts_f.groupby("facility")
                .size().reset_index(name="shorts")
                .sort_values("shorts", ascending=True)
            )
            fig_sum_sfac = px.bar(
                fac_shorts_sum,
                y="facility", x="shorts",
                orientation="h",
                title="Shorts by site",
                labels={"facility": "", "shorts": "Short count"},
                color="shorts",
                color_continuous_scale=[[0, HC_CREAM], [1, HC_BLUEBERRY]],
                text_auto=True,
            )
            fig_sum_sfac.update_layout(
                coloraxis_showscale=False,
                height=360,
            )
            st.plotly_chart(chart_base(fig_sum_sfac), use_container_width=True)
        else:
            st.info("No produce shorts in the selected period.")

    # ── Row 2: Waste cost & CPM ─────────────────────────────────────────────────
    section_head("Waste", "Cost by facility")
    wc1, wc2 = st.columns(2)

    with wc1:
        fac_cost_sum = (
            f.groupby("facility")["waste_cost"]
            .sum().reset_index()
            .sort_values("waste_cost")
        )
        fig_sum_fac = px.bar(
            fac_cost_sum, y="facility", x="waste_cost",
            orientation="h",
            title="Total waste cost by facility",
            labels={"facility": "", "waste_cost": "Waste Cost ($)"},
            color="waste_cost",
            color_continuous_scale=[[0, HC_GREEN], [0.5, HC_LEMON], [1, HC_MELON]],
            text_auto="$.3s",
        )
        fig_sum_fac.update_layout(
            xaxis_tickprefix="$", xaxis_tickformat=",",
            coloraxis_showscale=False,
            height=360,
        )
        st.plotly_chart(chart_base(fig_sum_fac), use_container_width=True)

    with wc2:
        fac_cpm_sum = (
            cpm_detail.groupby("facility")
            .apply(lambda g: g["waste_cost"].sum() / g["total_meals"].sum()
                   if g["total_meals"].sum() > 0 else np.nan)
            .reset_index(name="cpm")
            .dropna()
            .sort_values("cpm")
        )
        fig_sum_cpm = px.bar(
            fac_cpm_sum, y="facility", x="cpm",
            orientation="h",
            title="CPM by facility",
            labels={"facility": "", "cpm": "CPM ($)"},
            color="cpm",
            color_continuous_scale=[[0, HC_GREEN], [0.5, HC_LEMON], [1, HC_MELON]],
            text_auto="$.4f",
        )
        fig_sum_cpm.update_layout(
            xaxis_tickprefix="$", xaxis_tickformat=".4f",
            coloraxis_showscale=False,
            height=360,
        )
        st.plotly_chart(chart_base(fig_sum_cpm), use_container_width=True)

    # ── Row 3: Top ingredients by waste cost ────────────────────────────────────
    section_head("Ingredients", "Top produce by waste cost")
    top_ing_sum = (
        f.groupby("ingredient_name")["waste_cost"]
        .sum().reset_index()
        .sort_values("waste_cost", ascending=False)
        .head(10)
    )
    fig_sum_ing = px.bar(
        top_ing_sum.sort_values("waste_cost"),
        y="ingredient_name", x="waste_cost",
        orientation="h",
        title="Top 10 ingredients by waste cost",
        labels={"ingredient_name": "", "waste_cost": "Waste Cost ($)"},
        color="waste_cost",
        color_continuous_scale=[[0, HC_CREAM], [1, HC_MELON]],
        text_auto="$.3s",
    )
    fig_sum_ing.update_layout(
        xaxis_tickprefix="$", xaxis_tickformat=",",
        yaxis={"categoryorder": "total ascending"},
        coloraxis_showscale=False,
        height=360,
    )
    st.plotly_chart(chart_base(fig_sum_ing), use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# TAB — INGREDIENT LOOKUP
# ══════════════════════════════════════════════════════════════════════════════
with tab_ingredient:

    # Date + facility filtered WMS — no reason/RTH filter so all waste shows
    ing_base = wms_df.copy()
    if selected_weeks is not None:
        ing_base = ing_base[ing_base["menu_ship_date"].dt.date.isin(selected_weeks)]
    else:
        ing_base = ing_base[
            (ing_base["menu_ship_date"].dt.date >= date_range[0]) &
            (ing_base["menu_ship_date"].dt.date <= date_range[1])
        ]
    if sel_facility != "All":
        ing_base = ing_base[ing_base["facility"] == sel_facility]

    ing_opts = (
        ing_base[["ingredient_name", "ingredient_id"]]
        .dropna(subset=["ingredient_name"])
        .assign(ingredient_name=lambda d: d["ingredient_name"].str.strip())
        .drop_duplicates("ingredient_name")
        .sort_values("ingredient_name")
    )

    # Each option embeds both name and ID so Streamlit's built-in selectbox
    # search filters on either — no separate text input needed.
    ing_labels        = [
        f"{row['ingredient_name']}  ·  ID: {_nid(str(row['ingredient_id']))}"
        for _, row in ing_opts.iterrows()
    ]
    ing_label_to_name = dict(zip(ing_labels, ing_opts["ingredient_name"].tolist()))
    ing_label_to_id   = dict(zip(ing_labels, ing_opts["ingredient_id"].tolist()))

    if not ing_labels:
        st.warning("No ingredients found in the current date/facility window.")
    else:
        sel_label = st.selectbox(
            "Search ingredient by name or ID",
            ing_labels,
            index=None,
            placeholder="Type an ingredient name or ID…",
            label_visibility="collapsed",
            key="ing_lookup_select",
        )

    if not ing_labels or sel_label is None:
        st.markdown(
            '<p style="font-family:Karla,sans-serif;font-size:14px;color:#7A7A7A;'
            'margin-top:32px;text-align:center">'
            'Click the field above and start typing to find an ingredient.</p>',
            unsafe_allow_html=True,
        )
    else:
        sel_ing = ing_label_to_name[sel_label]
        ing_id  = ing_label_to_id[sel_label]
        ing_wms = ing_base[ing_base["ingredient_name"] == sel_ing]
        _iuom   = ing_wms["uom"].dropna().mode()
        ing_uom = _iuom.iloc[0] if not _iuom.empty else ""

        st.markdown(
            f'<div style="margin:16px 0 24px">'
            f'<div style="font-family:Karla,sans-serif;font-size:11px;font-weight:700;'
            f'letter-spacing:0.14em;text-transform:uppercase;color:{HC_MUTED};margin-bottom:4px">'
            f'ID: {ing_id}&nbsp;&nbsp;·&nbsp;&nbsp;UOM: {ing_uom}</div>'
            f'<div style="font-family:\'Bree Serif\',Georgia,serif;font-size:28px;'
            f'color:#1A1A1A">{sel_ing}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

        # ── KPIs ─────────────────────────────────────────────────────────────
        total_ing_cost = ing_wms["waste_cost"].sum()

        _poc = po_costs_df.copy()
        if not _poc.empty:
            if selected_weeks is not None:
                _poc = _poc[_poc["menu_ship_week"].dt.date.isin(selected_weeks)]
            else:
                _poc = _poc[
                    (_poc["menu_ship_week"].dt.date >= date_range[0]) &
                    (_poc["menu_ship_week"].dt.date <= date_range[1])
                ]
            if sel_facility != "All":
                _poc = _poc[_poc["facility"].str.lower() == sel_facility.lower()]
            _poc = _poc[_poc["ingredient_id"].astype(str).str.strip() == str(ing_id).strip()]
        ing_spend   = _poc["case_cost"].sum() if not _poc.empty else 0.0
        ing_pct_wst = (total_ing_cost / ing_spend * 100) if ing_spend > 0 else np.nan

        ing_po     = build_po_analysis(ing_wms, rvw_df)
        avg_po_pct = ing_po["pct_wasted"].mean() if not ing_po.empty else np.nan
        n_full_po  = int(ing_po["full_po_wasted"].sum()) if not ing_po.empty else 0

        ing_shorts = (
            shorts_f[shorts_f["shorted_ingredient"].str.lower() == sel_ing.lower()]
            if not shorts_f.empty else pd.DataFrame()
        )

        ing_cars = pd.DataFrame()
        if not cars_df.empty:
            _nid_ing = _nid(ing_id)
            ing_cars = cars_df[
                (cars_df["ingredient_id"].apply(_nid) == _nid_ing) |
                (cars_df["ingredient_name"].str.lower() == sel_ing.lower())
            ].copy()
            if selected_weeks is not None:
                _sw2 = {w.date() if hasattr(w, "date") else w for w in selected_weeks}
                ing_cars = ing_cars[ing_cars["ship_week"].dt.date.isin(_sw2)]
            else:
                ing_cars = ing_cars[
                    (ing_cars["ship_week"].dt.date >= date_range[0]) &
                    (ing_cars["ship_week"].dt.date <= date_range[1])
                ]
            if sel_facility != "All":
                ing_cars = ing_cars[ing_cars["facility"] == sel_facility]

        kc1, kc2, kc3, kc4, kc5 = st.columns(5)
        with kc1:
            st.markdown(kpi_card("Total Waste Cost", f"${total_ing_cost:,.0f}"), unsafe_allow_html=True)
        with kc2:
            st.markdown(kpi_card(
                "Total Spend (POs)",
                f"${ing_spend:,.0f}" if ing_spend > 0 else "—",
                help_text="Total case cost from Purchase Orders sheet",
            ), unsafe_allow_html=True)
        with kc3:
            st.markdown(kpi_card(
                "% of Spend Wasted",
                f"{ing_pct_wst:.1f}%" if not np.isnan(ing_pct_wst) else "—",
                delta=f"${total_ing_cost:,.0f} waste / ${ing_spend:,.0f} purchased" if ing_spend > 0 else None,
                delta_positive=None,
                help_text="Total waste cost ÷ total case cost from Purchase Orders",
            ), unsafe_allow_html=True)
        with kc4:
            st.markdown(kpi_card(
                "Avg PO Waste %",
                f"{avg_po_pct:.1f}%" if not np.isnan(avg_po_pct) else "—",
                delta=f"{n_full_po} fully wasted PO line{'s' if n_full_po != 1 else ''}",
                delta_positive=(n_full_po == 0),
            ), unsafe_allow_html=True)
        with kc5:
            _sn = len(ing_shorts)
            st.markdown(kpi_card(
                "Total Shorts",
                f"{_sn:,}",
                delta=(
                    f"{ing_shorts['facility'].nunique()} site{'s' if ing_shorts['facility'].nunique() != 1 else ''} affected"
                    if _sn > 0 else None
                ),
                delta_positive=None,
            ), unsafe_allow_html=True)

        st.divider()

        # ── Waste by facility ─────────────────────────────────────────────────
        section_head("", "Waste by facility")
        wf1, wf2 = st.columns(2)

        with wf1:
            fac_ing_cost = (
                ing_wms.groupby("facility")["waste_cost"]
                .sum().reset_index().sort_values("waste_cost")
            )
            fig_ic = px.bar(
                fac_ing_cost, y="facility", x="waste_cost",
                orientation="h",
                title="Waste cost by facility ($)",
                labels={"facility": "", "waste_cost": "Waste Cost ($)"},
                color="waste_cost",
                color_continuous_scale=[[0, HC_GREEN], [0.5, HC_LEMON], [1, HC_MELON]],
                text_auto="$.3s",
            )
            fig_ic.update_layout(
                xaxis_tickprefix="$", coloraxis_showscale=False,
                height=max(280, len(fac_ing_cost) * 52),
            )
            st.plotly_chart(chart_base(fig_ic), use_container_width=True)

        with wf2:
            fac_ing_qty = (
                ing_wms.groupby("facility")["quantity"]
                .sum().reset_index().sort_values("quantity")
            )
            fig_iq = px.bar(
                fac_ing_qty, y="facility", x="quantity",
                orientation="h",
                title=f"Waste quantity by facility ({ing_uom})",
                labels={"facility": "", "quantity": f"Qty ({ing_uom})"},
                color="quantity",
                color_continuous_scale=[[0, HC_GREEN], [0.5, HC_LEMON], [1, HC_MELON]],
                text_auto=",.1f",
            )
            fig_iq.update_layout(
                coloraxis_showscale=False,
                height=max(280, len(fac_ing_qty) * 52),
            )
            st.plotly_chart(chart_base(fig_iq), use_container_width=True)

        # ── Weekly trend + reason breakdown ───────────────────────────────────
        section_head("", "Trends & breakdown")
        wt1, wt2 = st.columns(2)

        with wt1:
            wk_ing = fmt_weeks(ing_wms.groupby("week")["waste_cost"].sum().reset_index())
            fig_iw = px.line(
                wk_ing, x="week", y="waste_cost",
                title="Weekly waste cost",
                labels={"week": "Week of", "waste_cost": "Waste Cost ($)"},
                markers=True, color_discrete_sequence=[HC_MELON],
            )
            fig_iw.update_traces(
                line_width=2,
                marker=dict(size=7, color="#FFFFFF", line=dict(width=2, color=HC_MELON)),
            )
            fig_iw.update_layout(yaxis_tickprefix="$", xaxis_type="category")
            st.plotly_chart(chart_base(fig_iw), use_container_width=True)

        with wt2:
            rsn_ing = (
                ing_wms.groupby("waste_reason")["waste_cost"]
                .sum().reset_index().sort_values("waste_cost", ascending=False)
            )
            fig_ir = px.bar(
                rsn_ing, x="waste_reason", y="waste_cost",
                title="Waste cost by reason",
                labels={"waste_reason": "", "waste_cost": "Waste Cost ($)"},
                color="waste_reason",
                color_discrete_sequence=HC_PALETTE,
                text_auto="$.3s",
            )
            fig_ir.update_layout(
                yaxis_tickprefix="$", showlegend=False, xaxis_title=None,
            )
            st.plotly_chart(chart_base(fig_ir), use_container_width=True)

        # ── PO Lines ──────────────────────────────────────────────────────────
        if not ing_po.empty:
            section_head("", "Purchase order lines")
            po_disp = ing_po[[
                "po_number", "facility", "menu_ship_date",
                "received_qty", "waste_qty", "pct_wasted",
                "waste_cost", "waste_reason", "n_lots", "full_po_wasted",
            ]].sort_values("menu_ship_date", ascending=False).copy()
            st.dataframe(
                po_disp,
                use_container_width=True,
                hide_index=True,
                height=min(500, 40 + len(po_disp) * 35),
                column_config={
                    "po_number":      st.column_config.TextColumn("PO Number"),
                    "facility":       st.column_config.TextColumn("Facility"),
                    "menu_ship_date": st.column_config.DateColumn("Menu week",    format="MMM D, YYYY"),
                    "received_qty":   st.column_config.NumberColumn("Received",   format="%,.2f"),
                    "waste_qty":      st.column_config.NumberColumn("Wasted",     format="%,.2f"),
                    "pct_wasted":     st.column_config.ProgressColumn("% Wasted", min_value=0, max_value=100, format="%.1f%%"),
                    "waste_cost":     st.column_config.NumberColumn("Waste cost", format="$%,.2f"),
                    "waste_reason":   st.column_config.TextColumn("Primary reason"),
                    "n_lots":         st.column_config.NumberColumn("Lots",       format="%d"),
                    "full_po_wasted": st.column_config.CheckboxColumn("Fully wasted"),
                },
            )

        # ── Shorts ────────────────────────────────────────────────────────────
        if not ing_shorts.empty:
            section_head("", "Shorts")
            ss1, ss2 = st.columns(2)

            with ss1:
                wk_sht = fmt_weeks(ing_shorts.groupby("week").size().reset_index(name="shorts"))
                fig_isw = px.bar(
                    wk_sht, x="week", y="shorts",
                    title="Weekly shorts",
                    labels={"week": "Week of", "shorts": "Short count"},
                    color_discrete_sequence=[HC_MELON],
                )
                fig_isw.update_layout(xaxis_type="category")
                st.plotly_chart(chart_base(fig_isw), use_container_width=True)

            with ss2:
                rsn_sht = (
                    ing_shorts.groupby("short_reason").size()
                    .reset_index(name="shorts").sort_values("shorts", ascending=False)
                )
                fig_isr = px.bar(
                    rsn_sht, x="short_reason", y="shorts",
                    title="Shorts by reason",
                    labels={"short_reason": "", "shorts": "Short count"},
                    color="short_reason",
                    color_discrete_sequence=HC_PALETTE,
                    text_auto=True,
                )
                fig_isr.update_layout(showlegend=False, xaxis_title=None)
                st.plotly_chart(chart_base(fig_isr), use_container_width=True)

            sht_tbl = (
                ing_shorts[["menu_ship_week", "facility", "short_reason", "brand"]]
                .sort_values("menu_ship_week", ascending=False).copy()
            )
            sht_tbl["menu_ship_week"] = sht_tbl["menu_ship_week"].dt.date
            st.dataframe(
                sht_tbl,
                use_container_width=True,
                hide_index=True,
                height=min(360, 40 + len(sht_tbl) * 35),
                column_config={
                    "menu_ship_week": st.column_config.DateColumn("Ship Week",    format="MMM D, YYYY"),
                    "facility":       st.column_config.TextColumn("Facility"),
                    "short_reason":   st.column_config.TextColumn("Reason Code"),
                    "brand":          st.column_config.TextColumn("Vendor / Brand"),
                },
            )

        # ── CARs ──────────────────────────────────────────────────────────────
        if not ing_cars.empty:
            section_head("", "Corrective action records (CARs)")
            st.caption(f"{len(ing_cars):,} CARs for {sel_ing} in the selected period.")
            st.dataframe(
                ing_cars[[
                    "investigation_number", "ship_week", "report_date",
                    "facility", "supplier", "po_numbers", "meal",
                ]].sort_values("ship_week", ascending=False),
                use_container_width=True,
                hide_index=True,
                height=min(400, 40 + len(ing_cars) * 35),
                column_config={
                    "investigation_number": st.column_config.TextColumn("CAR #"),
                    "ship_week":            st.column_config.DateColumn("Ship Week",   format="MMM D, YYYY"),
                    "report_date":          st.column_config.DateColumn("Report Date", format="MMM D, YYYY"),
                    "facility":             st.column_config.TextColumn("Facility"),
                    "supplier":             st.column_config.TextColumn("Vendor"),
                    "po_numbers":           st.column_config.TextColumn("PO Numbers"),
                    "meal":                 st.column_config.TextColumn("Meal"),
                },
            )


# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — WASTE TRENDS  (General + By Ingredient expanders)
# ══════════════════════════════════════════════════════════════════════════════
with tab_trends:

    with st.expander("General", expanded=True):
        st.markdown(
            '<div style="margin-bottom:20px">'
            '<h2 class="hc-section-head__title">Overall Waste</h2>'
            '</div>',
            unsafe_allow_html=True,
        )
        fac_cost_tr = f.groupby("facility")["waste_cost"].sum().reset_index().sort_values("waste_cost")
        reason_df   = (
            f.groupby("waste_reason")["waste_cost"]
            .sum().reset_index()
            .sort_values("waste_cost", ascending=False)
        )
        row1_h = max(380, len(fac_cost_tr) * 52)

        c1, c2 = st.columns(2)

        with c1:
            fig_fac_tr = px.bar(
                fac_cost_tr, y="facility", x="waste_cost",
                orientation="h",
                title="Total waste cost by facility",
                labels={"facility": "", "waste_cost": "Waste Cost ($)"},
                color="waste_cost",
                color_continuous_scale=[[0, HC_GREEN], [0.5, HC_LEMON], [1, HC_MELON]],
                text_auto="$.3s",
            )
            fig_fac_tr.update_layout(
                xaxis_tickprefix="$", xaxis_tickformat=",",
                coloraxis_showscale=False,
                height=row1_h,
            )
            st.plotly_chart(chart_base(fig_fac_tr), use_container_width=True)

        with c2:
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
                height=row1_h,
            )
            st.plotly_chart(chart_base(fig2), use_container_width=True)

        section_head("By facility", "Weekly waste cost by facility")
        fac_wk_tr = fmt_weeks(f.groupby(["week", "facility"])["waste_cost"].sum().reset_index())
        fig_fac_wk = px.bar(
            fac_wk_tr, x="week", y="waste_cost", color="facility",
            title="Weekly waste cost by facility",
            labels={"week": "Week of", "waste_cost": "Waste Cost ($)", "facility": "Facility"},
            color_discrete_sequence=HC_PALETTE,
        )
        fig_fac_wk.update_layout(yaxis_tickprefix="$", yaxis_tickformat=",", barmode="stack",
                                  xaxis_type="category")
        st.plotly_chart(chart_base(fig_fac_wk), use_container_width=True)

        st.markdown(
            '<div style="border-top:2px solid #008600;padding-top:28px;margin-top:44px;margin-bottom:16px">'
            '<h2 class="hc-section-head__title" style="font-size:26px">Cost Per Meal</h2>'
            '</div>',
            unsafe_allow_html=True,
        )
        wk_cpm = fmt_weeks(
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
        fig_cpm1.update_layout(yaxis_tickprefix="$", yaxis_tickformat=".4f", xaxis_type="category")
        st.plotly_chart(chart_base(fig_cpm1), use_container_width=True)

        section_head("By facility", "CPM breakdown")
        c_cpm_left, c_cpm_right = st.columns(2)

        with c_cpm_left:
            fac_cpm_bar = (
                cpm_detail.groupby("facility")
                .apply(lambda g: g["waste_cost"].sum() / g["total_meals"].sum()
                       if g["total_meals"].sum() > 0 else np.nan)
                .reset_index(name="cpm")
                .dropna()
                .sort_values("cpm")
            )
            fig_fac_cpm = px.bar(
                fac_cpm_bar, y="facility", x="cpm",
                orientation="h",
                title="CPM by facility",
                labels={"facility": "", "cpm": "CPM ($)"},
                color="cpm",
                color_continuous_scale=[[0, HC_GREEN], [0.5, HC_LEMON], [1, HC_MELON]],
                text_auto="$.4f",
            )
            fig_fac_cpm.update_layout(
                xaxis_tickprefix="$", xaxis_tickformat=".4f",
                coloraxis_showscale=False,
                height=max(320, len(fac_cpm_bar) * 44),
            )
            st.plotly_chart(chart_base(fig_fac_cpm), use_container_width=True)

        with c_cpm_right:
            fac_cpm_tbl = (
                cpm_detail.groupby("facility")
                .agg(waste_cost=("waste_cost", "sum"), total_meals=("total_meals", "sum"))
                .reset_index()
            )
            fac_cpm_tbl["cpm"] = fac_cpm_tbl["waste_cost"] / fac_cpm_tbl["total_meals"].replace(0, np.nan)
            fac_cpm_tbl = fac_cpm_tbl.sort_values("cpm", ascending=False)
            st.markdown(
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
                    "waste_cost":  st.column_config.NumberColumn("Waste cost",  format="$%,.0f"),
                    "total_meals": st.column_config.NumberColumn("Total meals", format="%,.0f"),
                    "cpm":         st.column_config.NumberColumn("CPM",         format="$%.4f"),
                },
            )

        heat_cpm = (
            cpm_detail[cpm_detail["total_meals"] > 0]
            .assign(cpm=lambda d: d["waste_cost"] / d["total_meals"])
            .pivot_table(index="facility", columns="week", values="cpm", aggfunc="mean")
        )
        if not heat_cpm.empty:
            section_head("Heatmap", "CPM heatmap — facility × week")
            heat_cpm.columns = [
                pd.Timestamp(c).strftime("%b %d").replace(" 0", "  ").strip() if isinstance(c, str) and c
                else (c.strftime("%b %d").replace(" 0", "  ").strip() if hasattr(c, "strftime") else str(c))
                for c in heat_cpm.columns
            ]
            fig_cpm_heat = px.imshow(
                heat_cpm,
                title="CPM heatmap — facility by week",
                labels={"x": "Week of", "y": "Facility", "color": "CPM ($)"},
                color_continuous_scale=[[0, HC_GREEN], [0.5, HC_LEMON], [1, HC_MELON]],
                aspect="auto",
                text_auto="$.3f",
            )
            fig_cpm_heat.update_layout(
                coloraxis_colorbar=dict(tickprefix="$", tickformat=".3f", title="CPM"),
                height=max(320, len(heat_cpm) * 44 + 80),
                xaxis_tickangle=-45,
            )
            st.plotly_chart(chart_base(fig_cpm_heat), use_container_width=True)

    with st.expander("By Ingredient", expanded=False):
        top_n = st.slider("Show top N ingredients", 10, 50, 20, key="ing_slider")

        # Consistent site color map — shared by both charts so legends match
        all_facs = sorted(f["facility"].dropna().unique())
        fac_color_map = {fac: HC_PALETTE[i % len(HC_PALETTE)] for i, fac in enumerate(all_facs)}

        ing = (
            f.groupby("ingredient_name")["waste_cost"]
            .sum().reset_index()
            .sort_values("waste_cost", ascending=False)
            .head(top_n)
        )
        ing_names = ing["ingredient_name"].tolist()
        # Ascending list → first item = BOTTOM of chart, last = TOP → highest on top
        ing_order = ing.sort_values("waste_cost", ascending=True)["ingredient_name"].tolist()

        # Chart 1: waste cost stacked by facility, highest waste cost on top
        ing_fac = (
            f[f["ingredient_name"].isin(ing_names)]
            .groupby(["ingredient_name", "facility"])["waste_cost"]
            .sum().reset_index()
        )
        fig_ing = px.bar(
            ing_fac,
            y="ingredient_name", x="waste_cost",
            color="facility",
            orientation="h",
            title=f"Top {top_n} ingredients by waste cost",
            labels={"ingredient_name": "", "waste_cost": "Waste Cost ($)", "facility": "Site"},
            color_discrete_map=fac_color_map,
            category_orders={"ingredient_name": ing_order},
        )
        fig_ing.update_layout(
            xaxis_tickprefix="$", xaxis_tickformat=",",
            barmode="stack",
            yaxis={"categoryorder": "array", "categoryarray": ing_order},
            height=max(400, top_n * 28),
        )
        st.plotly_chart(chart_base(fig_ing), use_container_width=True)

        # Chart 2: exact total spend from PO sheet col N (case_cost), same ingredient order
        # Join: po_costs_df (po_number + ingredient_id → case_cost) × WMS (ingredient_id → name)
        section_head("Breakdown", "Total spend on those ingredients")

        # Filter PO cost rows to the same date range + facility as the main filters
        pc = po_costs_df.copy()
        if not pc.empty:
            if selected_weeks is not None:
                pc = pc[pc["menu_ship_week"].dt.date.isin(selected_weeks)]
            else:
                pc = pc[
                    (pc["menu_ship_week"].dt.date >= date_range[0]) &
                    (pc["menu_ship_week"].dt.date <= date_range[1])
                ]
            if sel_facility != "All":
                pc = pc[pc["facility"].str.lower() == sel_facility.lower()]

        # Map ingredient_id → ingredient_name via filtered WMS
        ing_id_map = (
            f[["ingredient_id", "ingredient_name"]]
            .assign(ingredient_id=lambda d: d["ingredient_id"].astype(str).str.strip())
            .drop_duplicates("ingredient_id")
        )
        pc = pc.assign(ingredient_id=pc["ingredient_id"].astype(str).str.strip())
        pc_named = pc.merge(ing_id_map, on="ingredient_id", how="inner")

        spend_fac = (
            pc_named[pc_named["ingredient_name"].isin(ing_names)]
            .groupby(["ingredient_name", "facility"])["case_cost"]
            .sum().reset_index()
        )

        if not spend_fac.empty and spend_fac["case_cost"].sum() > 0:
            fig_spend = px.bar(
                spend_fac,
                y="ingredient_name", x="case_cost",
                color="facility",
                orientation="h",
                title=f"Total spend — top {top_n} ingredients",
                labels={"ingredient_name": "", "case_cost": "Total Spend ($)", "facility": "Site"},
                color_discrete_map=fac_color_map,
                category_orders={"ingredient_name": ing_order},
            )
            fig_spend.update_layout(
                xaxis_tickprefix="$", xaxis_tickformat=",",
                barmode="stack",
                yaxis={"categoryorder": "array", "categoryarray": ing_order},
                height=max(400, top_n * 28),
            )
            st.plotly_chart(chart_base(fig_spend), use_container_width=True)
        else:
            st.info("PO cost data not available for the selected period.")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — PURCHASE ORDERS
# ══════════════════════════════════════════════════════════════════════════════
with tab_po:
    po_df = build_po_analysis(f, rvw_df)

    rvw_win = rvw_df.dropna(subset=["menu_ship_week"]).copy()
    if selected_weeks is not None:
        _sw = {w.date() if hasattr(w, "date") else w for w in selected_weeks}
        rvw_win = rvw_win[rvw_win["menu_ship_week"].dt.date.isin(_sw)]
    else:
        rvw_win = rvw_win[
            (rvw_win["menu_ship_week"].dt.date >= date_range[0]) &
            (rvw_win["menu_ship_week"].dt.date <= date_range[1])
        ]
    if sel_facility != "All":
        rvw_win = rvw_win[rvw_win["facility"] == sel_facility]

    full_waste = po_df[po_df["full_po_wasted"]]
    n_full     = len(full_waste)
    full_cost  = full_waste["waste_cost"].sum()
    # Count and average from RVW so 0-waste POs are included.
    if not rvw_win.empty:
        total_pos = rvw_win[["po_number", "ingredient_id"]].drop_duplicates().shape[0]
        avg_pct   = rvw_win["pct_wasted_rvw"].clip(upper=100).fillna(0).mean()
    else:
        total_pos = len(po_df)
        avg_pct   = po_df["pct_wasted"].mean() if po_df.shape[0] else 0

    p1, p2, p3, p4 = st.columns(4)
    with p1:
        st.markdown(kpi_card("Total PO Lines", f"{total_pos:,}",
            help_text="One line = one unique PO × ingredient combination"), unsafe_allow_html=True)
    with p2:
        st.markdown(kpi_card(
            "Avg % of Line Wasted", f"{avg_pct:.1f}%",
            help_text="Average across all PO lines: waste qty / received qty",
        ), unsafe_allow_html=True)
    with p3:
        st.markdown(kpi_card(
            "Fully Wasted Lines", f"{n_full:,}",
            delta=f">= {int(FULL_WASTE_THRESHOLD*100)}% of received qty",
            delta_positive=(n_full == 0),
        ), unsafe_allow_html=True)
    with p4:
        st.markdown(kpi_card("Cost of Fully Wasted Lines", f"${full_cost:,.0f}"), unsafe_allow_html=True)

    st.divider()

    if n_full > 0:
        section_head("Alert", "Fully wasted PO lines")
        st.caption(
            f"{n_full} PO line{'s' if n_full != 1 else ''} where "
            f">= {int(FULL_WASTE_THRESHOLD*100)}% of received quantity was wasted "
            f"— one line = one PO × ingredient, aggregated across all lot IDs."
        )

        st.markdown('<p class="hc-eyebrow" style="margin-bottom:6px">Filter the table below</p>', unsafe_allow_html=True)
        ff1, ff2, ff3 = st.columns(3)
        with ff1:
            st.markdown('<p style="font-family:Karla,sans-serif;font-size:11px;font-weight:700;letter-spacing:0.1em;text-transform:uppercase;color:#7A7A7A;margin-bottom:4px">Facility</p>', unsafe_allow_html=True)
            fac_opts = ["All"] + sorted(full_waste["facility"].dropna().unique())
            tbl_fac  = st.selectbox("Facility",   fac_opts, key="po_fac", label_visibility="collapsed")
        with ff2:
            st.markdown('<p style="font-family:Karla,sans-serif;font-size:11px;font-weight:700;letter-spacing:0.1em;text-transform:uppercase;color:#7A7A7A;margin-bottom:4px">Ingredient</p>', unsafe_allow_html=True)
            ing_opts = ["All"] + sorted(full_waste["ingredient_name"].dropna().unique())
            tbl_ing  = st.selectbox("Ingredient", ing_opts, key="po_ing", label_visibility="collapsed")
        with ff3:
            st.markdown('<p style="font-family:Karla,sans-serif;font-size:11px;font-weight:700;letter-spacing:0.1em;text-transform:uppercase;color:#7A7A7A;margin-bottom:4px">Reason</p>', unsafe_allow_html=True)
            rsn_opts = ["All"] + sorted(full_waste["waste_reason"].dropna().unique())
            tbl_rsn  = st.selectbox("Reason",     rsn_opts, key="po_rsn", label_visibility="collapsed")

        tbl_data = full_waste.copy()
        if tbl_fac != "All": tbl_data = tbl_data[tbl_data["facility"]        == tbl_fac]
        if tbl_ing != "All": tbl_data = tbl_data[tbl_data["ingredient_name"] == tbl_ing]
        if tbl_rsn != "All": tbl_data = tbl_data[tbl_data["waste_reason"]    == tbl_rsn]

        full_display = tbl_data[[
            "po_number", "facility", "ingredient_name", "menu_ship_date",
            "waste_qty", "received_qty", "pct_wasted", "waste_cost", "n_lots", "waste_reason",
        ]].sort_values("waste_cost", ascending=False).copy()

        st.caption(f"{len(full_display):,} PO lines shown")
        st.dataframe(
            full_display,
            use_container_width=True,
            hide_index=True,
            column_config={
                "po_number":       st.column_config.TextColumn("PO Number"),
                "facility":        st.column_config.TextColumn("Facility"),
                "ingredient_name": st.column_config.TextColumn("Ingredient"),
                "menu_ship_date":  st.column_config.DateColumn("Menu week",     format="MMM D, YYYY"),
                "waste_qty":       st.column_config.NumberColumn("Waste qty",    format="%,.2f"),
                "received_qty":    st.column_config.NumberColumn("Received qty", format="%,.2f"),
                "pct_wasted":      st.column_config.ProgressColumn(
                                       "% Wasted", min_value=0, max_value=100, format="%.1f%%"),
                "waste_cost":      st.column_config.NumberColumn("Waste cost",   format="$%,.2f"),
                "n_lots":          st.column_config.NumberColumn("Lots",         format="%d"),
                "waste_reason":    st.column_config.TextColumn("Primary reason"),
            },
        )
    else:
        st.success("No fully wasted PO lines in the selected period.")

    st.divider()

    c1, c2 = st.columns(2)

    with c1:
        fig_dist = px.histogram(
            po_df[po_df["pct_wasted"] > 0],
            x="pct_wasted", nbins=20,
            title="Distribution of PO lines by % wasted",
            labels={"pct_wasted": "% of Line Wasted", "count": "Number of PO lines"},
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
            title="Top 15 PO lines by waste cost",
            labels={"po_number": "PO Number", "waste_cost": "Waste Cost ($)"},
            color="full_po_wasted",
            color_discrete_map={True: HC_MELON, False: HC_GREEN},
            hover_data=["ingredient_name", "facility", "pct_wasted"],
            text_auto="$.3s",
        )
        fig_top.update_layout(
            xaxis_tickprefix="$", xaxis_tickformat=",",
            legend_title_text="Fully Wasted Line",
        )
        st.plotly_chart(chart_base(fig_top), use_container_width=True)

    section_head("Ingredients", "PO waste by ingredient")
    st.caption("One PO line = one PO × ingredient combination, aggregated across all lot IDs.")

    ing_po = (
        po_df.groupby(["ingredient_name", "ingredient_id"])
        .agg(
            fully_wasted_pos = ("full_po_wasted", "sum"),
            total_waste_cost = ("waste_cost",     "sum"),
            total_waste_qty  = ("waste_qty",      "sum"),
            total_received   = ("received_qty",   "sum"),
        )
        .reset_index()
    )

    # Use the already-filtered rvw_win (computed at top of tab) as source of truth.
    if not rvw_win.empty:
        ing_po["_idk"] = ing_po["ingredient_id"].apply(_nid)
        _rw = rvw_win.copy()
        _rw["_idk"] = _rw["ingredient_id"].apply(_nid)
        _rw["_pct"] = _rw["pct_wasted_rvw"].clip(upper=100).fillna(0)
        ing_rvw = _rw.groupby("_idk", as_index=False).agg(overall_pct_wasted=("_pct", "mean"))
        ing_po = ing_po.merge(ing_rvw[["_idk", "overall_pct_wasted"]], on="_idk", how="left")
        ing_po["overall_pct_wasted"] = ing_po["overall_pct_wasted"].fillna(
            (ing_po["total_waste_qty"] / ing_po["total_received"].replace(0, np.nan) * 100)
            .clip(upper=100).fillna(0)
        )
        ing_po.drop(columns=["_idk"], inplace=True)
    else:
        ing_po["overall_pct_wasted"] = (
            ing_po["total_waste_qty"] / ing_po["total_received"].replace(0, np.nan) * 100
        ).clip(upper=100).fillna(0)

    top_n_ing = st.slider("Show top N ingredients", 10, 50, 20, key="po_ing_slider")
    top_ing   = ing_po.nlargest(top_n_ing, "overall_pct_wasted")

    ci1, ci2 = st.columns(2)

    with ci1:
        fig_ing_pct = px.bar(
            top_ing.sort_values("overall_pct_wasted"),
            y="ingredient_name", x="overall_pct_wasted",
            orientation="h",
            title=f"Top {top_n_ing} ingredients — % of PO wasted",
            labels={"ingredient_name": "", "overall_pct_wasted": "% of Qty Wasted"},
            color="overall_pct_wasted",
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
        po_heat = po_df.copy()
        _d = pd.to_datetime(po_heat["menu_ship_date"])
        po_heat["week"] = (_d - pd.to_timedelta(_d.dt.dayofweek, unit="D")).dt.normalize().dt.strftime("%Y-%m-%d")
        top_ing_names = top_ing["ingredient_name"].tolist()
        po_heat = po_heat[po_heat["ingredient_name"].isin(top_ing_names)]

        pivot = (
            po_heat.groupby(["ingredient_name", "week"])["waste_cost"]
            .sum()
            .unstack(fill_value=0)
        )
        # Bar chart: categoryorder=total ascending → highest % at top.
        # px.imshow puts row 0 at the top, so sort descending here so both charts
        # have the same ingredient at the top and bottom.
        pct_order = top_ing.sort_values("overall_pct_wasted", ascending=False)["ingredient_name"].tolist()
        pivot = pivot.loc[[name for name in pct_order if name in pivot.index]]
        # Convert YYYY-MM-DD column headers to "Mmm D" strings so Plotly
        # treats them as categories rather than UTC timestamps.
        pivot.columns = [
            pd.Timestamp(c).strftime("%b %d").replace(" 0", "  ").strip()
            if isinstance(c, str) else str(c)
            for c in pivot.columns
        ]

        fig_ing_heat = px.imshow(
            pivot,
            title=f"Top {top_n_ing} ingredients — waste cost by week",
            labels={"x": "Week of", "y": "", "color": "Waste cost ($)"},
            color_continuous_scale=[[0, "#FFFFFF"], [0.2, HC_LEMON], [1, HC_MELON]],
            aspect="auto",
        )
        fig_ing_heat.update_layout(
            height=max(400, top_n_ing * 28),
            coloraxis_colorbar=dict(title="$", tickprefix="$", tickformat=","),
            xaxis_title=None,
        )
        st.plotly_chart(chart_base(fig_ing_heat), use_container_width=True)



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
        top_vendor      = shorts_f["brand"].mode()[0] if total_shorts and "brand" in shorts_f.columns else "—"

        sk1, sk2, sk3, sk4 = st.columns(4)
        with sk1:
            st.markdown(kpi_card("Total Produce Shorts", f"{total_shorts:,}"), unsafe_allow_html=True)
        with sk2:
            st.markdown(kpi_card("Most Shorted Ingredient", top_short_ing), unsafe_allow_html=True)
        with sk3:
            st.markdown(kpi_card("Top Short Reason", top_short_rsn), unsafe_allow_html=True)
        with sk4:
            st.markdown(kpi_card("Top Vendor", top_vendor), unsafe_allow_html=True)

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
            st.markdown('<div style="height:58px"></div>', unsafe_allow_html=True)
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
            fig_srsn.update_layout(
                showlegend=False,
                xaxis_title=None,
                height=max(400, top_n_s * 28),
            )
            st.plotly_chart(chart_base(fig_srsn), use_container_width=True)

        # ── Weekly trend ──────────────────────────────────────────────────
        section_head("Over time", "Weekly produce shorts")
        wk_shorts = fmt_weeks(shorts_f.groupby("week").size().reset_index(name="shorts"))
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
        fig_swk.update_layout(xaxis_type="category")
        st.plotly_chart(chart_base(fig_swk), use_container_width=True)

        # ── Reason × facility heatmap ─────────────────────────────────────
        section_head("By facility", "Short reason breakdown per site")
        heat_s = (
            shorts_f.groupby(["facility", "short_reason"])
            .size().unstack(fill_value=0)
        )
        if not heat_s.empty:
            reason_order = heat_s.sum(axis=0).sort_values(ascending=False).index.tolist()
            heat_s = heat_s[reason_order]
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

        # ── Ingredient drill-down ─────────────────────────────────────────
        with st.expander("Ingredient deep dive", expanded=False):

            ing_options = (
                shorts_f.groupby("shorted_ingredient")
                .size().sort_values(ascending=False)
                .index.tolist()
            )
            selected_ing = st.selectbox(
                "Select an ingredient",
                ing_options,
                key="shorts_drilldown_ing",
            )

            drill = shorts_f[shorts_f["shorted_ingredient"] == selected_ing].copy()

            # KPIs
            d_total   = len(drill)
            d_facs    = drill["facility"].nunique()
            d_top_rsn = drill["short_reason"].mode()[0] if d_total else "—"
            d_weeks   = drill["week"].nunique()

            dk1, dk2, dk3, dk4 = st.columns(4)
            with dk1:
                st.markdown(kpi_card("Total Shorts", f"{d_total:,}"), unsafe_allow_html=True)
            with dk2:
                st.markdown(kpi_card("Facilities Affected", f"{d_facs}"), unsafe_allow_html=True)
            with dk3:
                st.markdown(kpi_card("Top Reason", d_top_rsn), unsafe_allow_html=True)
            with dk4:
                st.markdown(kpi_card("Weeks Affected", f"{d_weeks}"), unsafe_allow_html=True)

            st.markdown('<div style="height:16px"></div>', unsafe_allow_html=True)

            # Charts row
            da, db = st.columns(2)

            with da:
                wk_drill = fmt_weeks(drill.groupby("week").size().reset_index(name="shorts"))
                fig_dwk = px.bar(
                    wk_drill, x="week", y="shorts",
                    title=f"Weekly shorts — {selected_ing}",
                    labels={"week": "Menu ship week", "shorts": "Short count"},
                    color_discrete_sequence=[HC_MELON],
                )
                fig_dwk.update_layout(xaxis_type="category")
                st.plotly_chart(chart_base(fig_dwk), use_container_width=True)

            with db:
                fac_drill = (
                    drill.groupby("facility").size()
                    .reset_index(name="shorts")
                    .sort_values("shorts", ascending=True)
                )
                fig_dfac = px.bar(
                    fac_drill, y="facility", x="shorts",
                    orientation="h",
                    title="Shorts by facility",
                    labels={"facility": "", "shorts": "Short count"},
                    color="shorts",
                    color_continuous_scale=[[0, HC_CREAM], [1, HC_BLUEBERRY]],
                    text_auto=True,
                )
                fig_dfac.update_layout(coloraxis_showscale=False)
                st.plotly_chart(chart_base(fig_dfac), use_container_width=True)

            rsn_drill = (
                drill.groupby("short_reason").size()
                .reset_index(name="shorts")
                .sort_values("shorts", ascending=False)
            )
            fig_drsn = px.bar(
                rsn_drill, x="short_reason", y="shorts",
                title="Shorts by reason code",
                labels={"short_reason": "", "shorts": "Short count"},
                color="short_reason",
                color_discrete_sequence=HC_PALETTE,
                text_auto=True,
            )
            fig_drsn.update_layout(showlegend=False, xaxis_title=None)
            st.plotly_chart(chart_base(fig_drsn), use_container_width=True)

            # Detail table — grouped so identical week/facility/reason/vendor rows are collapsed
            section_head("Records", f"All short records — {selected_ing}")
            drill_display = (
                drill.groupby(["menu_ship_week", "facility", "short_reason", "brand"], dropna=False)
                .size()
                .reset_index(name="count")
                .sort_values(["menu_ship_week", "count"], ascending=[False, False])
            )
            drill_display["menu_ship_week"] = drill_display["menu_ship_week"].dt.date
            max_count = int(drill_display["count"].max()) if len(drill_display) else 1
            st.dataframe(
                drill_display,
                use_container_width=True,
                hide_index=True,
                height=min(480, 40 + len(drill_display) * 35),
                column_config={
                    "menu_ship_week": st.column_config.DateColumn("Menu Ship Week", format="MMM D, YYYY"),
                    "facility":       st.column_config.TextColumn("Facility"),
                    "short_reason":   st.column_config.TextColumn("Reason Code"),
                    "brand":          st.column_config.TextColumn("Vendor / Brand"),
                    "count":          st.column_config.ProgressColumn(
                                          "# Records", min_value=0, max_value=max_count, format="%d"),
                },
            )



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
            "quantity":            st.column_config.NumberColumn("Qty",        format="%,.2f"),
            "waste_reason":        st.column_config.TextColumn("Reason"),
            "waste_reason_detail": st.column_config.TextColumn("Detail"),
            "menu_ship_date":      st.column_config.DateColumn("Menu week",    format="MMM D"),
            "waste_cost":          st.column_config.NumberColumn("Waste cost", format="$%,.2f"),
            "is_rth":              st.column_config.TextColumn("RTH",          width="small"),
        },
    )

    csv = dt[existing].to_csv(index=False).encode("utf-8")
    st.download_button("Download as CSV", csv, "produce_waste_filtered.csv", "text/csv")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 6 — CARs
# ══════════════════════════════════════════════════════════════════════════════
with tab_cars:
    if cars_df.empty:
        st.info("No Produce CARs found. Check that the 'CARs' sheet is accessible and contains rows where Category = 'Produce'.")
    else:
        # ── Apply same date + facility filters as sidebar ─────────────────────
        cars_f = cars_df.copy()
        if selected_weeks is not None:
            _sw = {w.date() if hasattr(w, "date") else w for w in selected_weeks}
            cars_f = cars_f[cars_f["ship_week"].dt.date.isin(_sw)]
        else:
            cars_f = cars_f[
                (cars_f["ship_week"].dt.date >= date_range[0]) &
                (cars_f["ship_week"].dt.date <= date_range[1])
            ]
        if sel_facility != "All":
            cars_f = cars_f[cars_f["facility"] == sel_facility]

        if cars_f.empty:
            st.info("No CARs match the current filters.")
        else:
            # ── KPI chips ─────────────────────────────────────────────────────
            total_cars    = len(cars_f)
            n_car_weeks   = cars_f["ship_week"].nunique()
            cars_per_week = total_cars / n_car_weeks if n_car_weeks else 0
            top_car_ing   = (
                cars_f["ingredient_name"].dropna()
                .replace("", pd.NA).dropna()
                .mode()
            )
            top_car_ing   = top_car_ing.iloc[0] if not top_car_ing.empty else "—"
            top_car_vend  = (
                cars_f["supplier"].dropna()
                .replace("", pd.NA).dropna()
                .mode()
            )
            top_car_vend  = top_car_vend.iloc[0] if not top_car_vend.empty else "—"

            k1, k2, k3, k4 = st.columns(4)
            with k1:
                st.markdown(kpi_card("Total CARs", f"{total_cars:,}",
                    help_text="Produce CARs in the selected period"), unsafe_allow_html=True)
            with k2:
                st.markdown(kpi_card("CARs / Week", f"{cars_per_week:.1f}",
                    help_text="Total CARs ÷ distinct ship weeks"), unsafe_allow_html=True)
            with k3:
                st.markdown(kpi_card("Most Affected Ingredient", top_car_ing), unsafe_allow_html=True)
            with k4:
                st.markdown(kpi_card("Most Affected Vendor", top_car_vend), unsafe_allow_html=True)

            st.divider()

            # ── CARs by facility over time ────────────────────────────────────
            section_head("", "CARs by facility — weekly")
            cars_f["_week"] = (
                cars_f["ship_week"]
                - pd.to_timedelta(cars_f["ship_week"].dt.dayofweek, unit="D")
            ).dt.normalize().dt.strftime("%Y-%m-%d")

            weekly_fac = (
                cars_f.groupby(["_week", "facility"])
                .size().reset_index(name="cars")
            )
            weekly_fac["week_label"] = (
                pd.to_datetime(weekly_fac["_week"])
                .dt.strftime("%b %d")
                .str.replace(r" 0(\d)$", r" \1", regex=True)
            )
            _wk_order = (
                weekly_fac.drop_duplicates("_week")
                .sort_values("_week")["week_label"]
                .tolist()
            )

            fig_cars_trend = px.bar(
                weekly_fac,
                x="week_label", y="cars",
                color="facility",
                barmode="stack",
                title="CARs by facility — weekly",
                labels={"week_label": "Ship Week", "cars": "CAR Count", "facility": "Facility"},
                color_discrete_sequence=HC_PALETTE,
                category_orders={"week_label": _wk_order},
            )
            fig_cars_trend.update_layout(
                xaxis_type="category",
                xaxis_tickangle=-35,
                legend_title_text="Facility",
                yaxis_title="CAR Count",
            )
            st.plotly_chart(chart_base(fig_cars_trend), use_container_width=True)

            # ── Top ingredients & vendors ─────────────────────────────────────
            section_head("", "Top ingredients & vendors by CAR count")
            ca1, ca2 = st.columns(2)

            with ca1:
                _top_ing_names = (
                    cars_f.groupby("ingredient_name").size()
                    .nlargest(15).index.tolist()
                )
                ing_by_fac = (
                    cars_f[cars_f["ingredient_name"].isin(_top_ing_names)]
                    .groupby(["ingredient_name", "facility"])
                    .size().reset_index(name="cars")
                )
                _ing_order = (
                    ing_by_fac.groupby("ingredient_name")["cars"]
                    .sum().sort_values().index.tolist()
                )
                fig_ing_cars = px.bar(
                    ing_by_fac,
                    y="ingredient_name", x="cars",
                    color="facility",
                    orientation="h",
                    barmode="stack",
                    title="Top 15 ingredients by CAR count",
                    labels={"ingredient_name": "", "cars": "CAR Count", "facility": "Facility"},
                    color_discrete_sequence=HC_PALETTE,
                    category_orders={"ingredient_name": _ing_order},
                )
                fig_ing_cars.update_layout(
                    yaxis={"categoryorder": "array", "categoryarray": _ing_order},
                    xaxis_title="CAR Count",
                    legend_title_text="Facility",
                )
                st.plotly_chart(chart_base(fig_ing_cars), use_container_width=True)

            with ca2:
                _top_vend_names = (
                    cars_f.groupby("supplier").size()
                    .nlargest(15).index.tolist()
                )
                vend_by_fac = (
                    cars_f[cars_f["supplier"].isin(_top_vend_names)]
                    .groupby(["supplier", "facility"])
                    .size().reset_index(name="cars")
                )
                _vend_order = (
                    vend_by_fac.groupby("supplier")["cars"]
                    .sum().sort_values().index.tolist()
                )
                fig_vend_cars = px.bar(
                    vend_by_fac,
                    y="supplier", x="cars",
                    color="facility",
                    orientation="h",
                    barmode="stack",
                    title="Top 15 vendors by CAR count",
                    labels={"supplier": "", "cars": "CAR Count", "facility": "Facility"},
                    color_discrete_sequence=HC_PALETTE,
                    category_orders={"supplier": _vend_order},
                )
                fig_vend_cars.update_layout(
                    yaxis={"categoryorder": "array", "categoryarray": _vend_order},
                    xaxis_title="CAR Count",
                    legend_title_text="Facility",
                )
                st.plotly_chart(chart_base(fig_vend_cars), use_container_width=True)

            # ── Detail table ──────────────────────────────────────────────────
            section_head("", "CAR detail")
            tf1, tf2, tf3 = st.columns(3)
            with tf1:
                car_fac_opts = ["All"] + sorted(cars_f["facility"].dropna().unique())
                car_fac_sel  = st.selectbox("Facility", car_fac_opts, key="car_fac")
            with tf2:
                car_ing_opts = ["All"] + sorted(cars_f["ingredient_name"].dropna().unique())
                car_ing_sel  = st.selectbox("Ingredient", car_ing_opts, key="car_ing")
            with tf3:
                car_vend_opts = ["All"] + sorted(cars_f["supplier"].dropna().unique())
                car_vend_sel  = st.selectbox("Supplier", car_vend_opts, key="car_vend")

            car_tbl = cars_f.copy()
            if car_fac_sel  != "All": car_tbl = car_tbl[car_tbl["facility"]        == car_fac_sel]
            if car_ing_sel  != "All": car_tbl = car_tbl[car_tbl["ingredient_name"] == car_ing_sel]
            if car_vend_sel != "All": car_tbl = car_tbl[car_tbl["supplier"]        == car_vend_sel]

            st.caption(f"{len(car_tbl):,} CARs shown")
            st.dataframe(
                car_tbl[[
                    "investigation_number", "ship_week", "report_date",
                    "facility", "ingredient_name", "supplier", "po_numbers", "meal",
                ]].sort_values("ship_week", ascending=False),
                use_container_width=True,
                hide_index=True,
                height=500,
                column_config={
                    "investigation_number": st.column_config.TextColumn("CAR #"),
                    "ship_week":            st.column_config.DateColumn("Ship Week",   format="MMM D, YYYY"),
                    "report_date":          st.column_config.DateColumn("Report Date", format="MMM D, YYYY"),
                    "facility":             st.column_config.TextColumn("Facility"),
                    "ingredient_name":      st.column_config.TextColumn("Ingredient"),
                    "supplier":             st.column_config.TextColumn("Vendor"),
                    "po_numbers":           st.column_config.TextColumn("PO Numbers"),
                    "meal":                 st.column_config.TextColumn("Meal"),
                },
            )
