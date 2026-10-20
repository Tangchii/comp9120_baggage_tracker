import html
import os
import re
from datetime import timezone
from zoneinfo import ZoneInfo

import pandas as pd
import psycopg2
import psycopg2.errors
import streamlit as st

import db

# Demo-only staff credentials: the schema has no staff/account table.
# Locally these come from environment variables; on Streamlit Cloud they are
# read from Secrets (Settings -> Secrets), never from code committed to GitHub.
def _config(name, default):
    value = os.getenv(name)
    if value:
        return value
    try:
        return st.secrets.get(name, default)
    except Exception:
        return default


STAFF_PASSWORDS = {
    "Ground staff": _config("STAFF_PASSWORD", "staff9120"),
    "Supervisor": _config("SUPERVISOR_PASSWORD", "super9120"),
}

DEMO_TAG = "100006"
DEMO_EMAIL = "txz9120.eva.liu.05@gmail.com"

# Ground scans that do not change a flight segment's status.
GROUND_EVENTS = {
    "CHECK_IN": "CHECK_IN",
    "SORTING": "SORTING",
    "TRANSFER_IN": "TRANSFER",
    "TRANSFER_OUT": "TRANSFER",
    "COLLECTED": "BAGGAGE_CLAIM",
}

EVENT_LABELS = {
    "CHECK_IN": "Checked in",
    "SORTING": "Sorted",
    "LOADING": "Loaded onto aircraft",
    "TRANSFER_IN": "Transfer: received",
    "TRANSFER_OUT": "Transfer: sent on",
    "ARRIVAL": "Arrived",
    "COLLECTED": "Collected by passenger",
}

# Plain-English wording for BaggageFlight.transport_status on the passenger page.
SEGMENT_WORDS = {
    "ASSIGNED": ("Bag assigned · not loaded yet", "grey"),
    "LOADED": ("Bag on board", "blue"),
    "ARRIVED": ("Bag arrived", "green"),
}

# Display only: the database stores timezone-naive UTC (see CLAUDE_HANDOFF.md).
# Local airport time is computed in the UI so passengers do not have to convert.
AIRPORT_TZ = {
    "YYZ": "America/Toronto", "TPE": "Asia/Taipei", "BOG": "America/Bogota",
    "SYD": "Australia/Sydney", "NRT": "Asia/Tokyo", "AKL": "Pacific/Auckland",
    "LHR": "Europe/London", "CDG": "Europe/Paris", "FRA": "Europe/Berlin",
    "AMS": "Europe/Amsterdam", "LAX": "America/Los_Angeles", "SEA": "America/Los_Angeles",
    "JFK": "America/New_York", "IAD": "America/New_York", "ORD": "America/Chicago",
    "HNL": "Pacific/Honolulu", "NAN": "Pacific/Fiji", "MCO": "America/New_York",
    "PEK": "Asia/Shanghai", "HKG": "Asia/Hong_Kong",
}

st.set_page_config(page_title="TXZ Baggage Tracker", page_icon="🧳", layout="wide")


# ---------- Look and feel ----------
# Airline-app style: navy top bar, white cards on a light grey ground, blue pill
# buttons. Fonts are Streamlit's bundled Source Sans / Source Code Pro, so the
# local (offline) demo looks the same as the cloud one.

CSS = """
<style>
:root {
  --navy: #0A2347; --ink: #13203A; --text2: #3A4659; --muted: #566174;
  --blue: #1B5FD6; --blue-soft: #DCE8FB; --sky: #EAF1FD;
  --ground: #F4F6FA; --line: #DDE3EC; --line2: #B7C2D3; --card: #FFFFFF;
  --green: #11733F; --green-soft: #E5F4EC; --amber: #8A4A00; --amber-soft: #FFF3E0;
  --red: #A61B1B; --red-soft: #FDECEC; --grey-soft: #EEF1F5;
  --mono: "Source Code Pro", ui-monospace, Menlo, monospace;
}
html, body, [data-testid="stApp"] { background: var(--ground); }
header[data-testid="stHeader"], [data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"],
[data-testid="stDecoration"] { display: none !important; }
.block-container, [data-testid="stMainBlockContainer"] {
  max-width: 1200px; padding-top: 0 !important; padding-bottom: 3rem;
}
h1, h2, h3 { color: var(--navy); letter-spacing: -0.01em; }

/* Top bar: a keyed st.container stretched to the full window width */
.st-key-topbar {
  background: var(--navy); width: 100vw !important; max-width: 100vw !important;
  margin-left: calc(50% - 50vw) !important; margin-top: -1rem;
  padding: 12px max(24px, calc(50vw - 576px)); box-sizing: border-box;
  min-height: 64px; justify-content: center;
}
.st-key-topbar p, .st-key-topbar span, .tb-user { color: #C9D6EC; }
.tb-brand { display: flex; align-items: center; gap: 12px; }
.tb-brand b { color: #fff; font-size: 20px; font-weight: 800; letter-spacing: .04em; }
.tb-brand span { font-size: 16px; }
.tb-user { text-align: right; font-size: 15px; }
.tb-user strong { color: #fff; }
.tb-chip { display: inline-block; font-size: 12.5px; font-weight: 700; color: var(--navy) !important;
  background: #BFD6FF; border-radius: 999px; padding: 3px 11px; margin-right: 10px; }
.st-key-logout button { background: transparent; color: #fff; border: 1px solid #6F86AD; border-radius: 999px; }
.st-key-logout button:hover { border-color: #fff; color: #fff; background: rgba(255,255,255,.08); }
.st-key-logout button p { color: #fff !important; }

/* Buttons, inputs, tabs */
[data-testid="stBaseButton-primary"] { border-radius: 999px; min-height: 48px; font-weight: 700;
  background: var(--blue); border-color: var(--blue); }
[data-testid="stBaseButton-primary"]:hover { background: #164FB3; border-color: #164FB3; }
[data-testid="stBaseButton-secondary"], [data-testid="stBaseButton-secondaryFormSubmit"] { border-radius: 999px; }
[data-testid="stBaseButton-primaryFormSubmit"] { border-radius: 999px; min-height: 48px; font-weight: 700; }
[data-testid="stForm"], .st-key-runpanel, .st-key-findbag {
  background: var(--card); border: 1px solid var(--line) !important; border-radius: 14px !important; }
.st-key-findbag { padding: 16px 20px; }
.st-key-runpanel { padding: 6px 8px; }
[class*="st-key-tx_tag"] input, .st-key-login_tag input { font-family: var(--mono); font-size: 19px; }
[data-testid="stTabs"] [role="tab"] p { font-size: 16px; font-weight: 600; }
[data-testid="stExpander"] details { background: var(--card); border-radius: 12px; }

/* Radio pickers. Selectors cover both Streamlit radio DOMs (older baseweb
   "radiogroup > label" and newer "stRadioOption"), so local and cloud match. */
[class*="st-key-segpick"], [class*="st-key-action"] { width: 100% !important; }
[class*="st-key-segpick"] [data-testid="stRadio"], [class*="st-key-action"] [data-testid="stRadio"] { width: 100%; }

/* Segment picker: options drawn as selectable cards */
[class*="st-key-segpick"] [role="radiogroup"] { gap: 10px; width: 100%; display: flex; flex-direction: column; }
[class*="st-key-segpick"] [role="radiogroup"] > div { width: 100%; }
[class*="st-key-segpick"] [data-testid="stRadioOption"],
[class*="st-key-segpick"] [role="radiogroup"] > label {
  width: 100%; box-sizing: border-box; margin: 0; background: var(--card); border: 1px solid var(--line);
  border-radius: 14px; padding: 16px 18px; cursor: pointer; }
[class*="st-key-segpick"] [data-testid="stRadioOption"]:has(input:checked),
[class*="st-key-segpick"] [role="radiogroup"] > label:has(input:checked) {
  border: 2px solid var(--blue); box-shadow: 0 0 0 4px var(--blue-soft); }
[class*="st-key-segpick"] [role="radiogroup"] p { font-size: 17px; }

/* Action picker: options drawn as a pill toggle */
[class*="st-key-action"] [role="radiogroup"] {
  display: flex; flex-direction: row; background: #E6EBF2; border-radius: 999px; padding: 4px; gap: 4px;
  width: 100%; box-sizing: border-box; flex-wrap: wrap; }
[class*="st-key-action"] [role="radiogroup"] > div { flex: 1 1 220px; display: flex; flex-direction: row; }
[class*="st-key-action"] [data-testid="stRadioOption"],
[class*="st-key-action"] [role="radiogroup"] > label {
  flex: 1 1 auto; width: 100%; box-sizing: border-box; margin: 0; justify-content: center;
  border-radius: 999px; padding: 9px 14px; cursor: pointer; }
[class*="st-key-action"] [data-testid="stRadioOption"] > div > div:first-child,
[class*="st-key-action"] [role="radiogroup"] > label > div:first-child { display: none; }
[class*="st-key-action"] [data-testid="stRadioOption"]:has(input:checked),
[class*="st-key-action"] [role="radiogroup"] > label:has(input:checked) {
  background: #fff; box-shadow: 0 1px 3px rgba(10,35,71,.18); }
[class*="st-key-action"] :has(input:checked) p { font-weight: 700; color: var(--navy); }

/* Shared pieces */
.eyebrow { font-size: 13px; font-weight: 700; letter-spacing: .08em; text-transform: uppercase; color: var(--muted); }
.mono { font-family: var(--mono); }
.pill { display: inline-block; font-size: 13px; font-weight: 700; border-radius: 999px; padding: 3px 12px; white-space: nowrap; }
.pill-grey { background: var(--grey-soft); color: var(--text2); }
.pill-blue { background: var(--blue-soft); color: #1550B8; }
.pill-green { background: var(--green-soft); color: var(--green); }
.pill-amber { background: var(--amber-soft); color: var(--amber); }
.card { background: var(--card); border: 1px solid var(--line); border-radius: 14px; padding: 20px 24px; }
.section-title { font-size: 22px; font-weight: 800; color: var(--navy); margin: 8px 0 12px; }
.small { font-size: 13px; color: var(--muted); }
.banner { display: flex; gap: 14px; align-items: baseline; flex-wrap: wrap; border-radius: 12px;
  padding: 14px 18px; margin: 4px 0 14px; font-size: 15.5px; }
.banner b { font-weight: 700; }
.banner-success { background: var(--green-soft); border: 1px solid #A9D8BE; color: #0B5530; }
.banner-error { background: var(--red-soft); border: 1px solid #F0B8B8; color: var(--red); }

/* Passenger hero */
.hero-band { width: 100vw; margin-left: calc(50% - 50vw); margin-top: -16px;
  background: linear-gradient(180deg, var(--navy) 0, var(--navy) 110px, var(--ground) 110px);
  padding: 22px max(24px, calc(50vw - 576px)) 0; }
.hero { background: var(--card); border-radius: 16px; box-shadow: 0 6px 24px rgba(10,35,71,.12);
  display: flex; flex-wrap: wrap; overflow: hidden; }
.hero-main { flex: 999 1 560px; min-width: 0; padding: 30px 34px; display: flex; flex-direction: column; gap: 12px; }
.hero-main h1 { margin: 0; padding: 0; font-size: 38px; line-height: 1.12; font-weight: 800; color: var(--navy); }
.hero-main p { margin: 0; font-size: 17px; color: var(--text2); }
.tagcard { flex: 1 1 290px; background: var(--sky); border-left: 2px dashed #B9CDF2; padding: 30px 28px;
  display: flex; flex-direction: column; gap: 16px; }
.tagcard .tagno { font-family: var(--mono); font-size: 38px; font-weight: 600; color: var(--navy); letter-spacing: .06em; }
.tagcard .grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px 16px; }
.tagcard .k { font-size: 12px; color: var(--muted); }
.tagcard .v { font-size: 16px; font-weight: 700; color: var(--ink); }
.tagcard .route { display: flex; align-items: center; gap: 8px; flex-wrap: wrap;
  font-family: var(--mono); font-size: 20px; font-weight: 600; color: var(--navy); }

.journey { position: relative; margin-top: 16px; }
.journey .track { position: absolute; top: 12px; height: 4px; border-radius: 4px; }
.journey ol { list-style: none; margin: 0; padding: 0; display: grid; position: relative; }
.journey li { display: flex; flex-direction: column; align-items: center; gap: 6px; text-align: center; margin: 0; }
.journey .dot { width: 28px; height: 28px; border-radius: 50%; box-sizing: border-box;
  display: flex; align-items: center; justify-content: center; background: #fff; border: 2px solid var(--line2); }
.journey .done .dot { background: var(--green); border-color: var(--green); }
.journey .current .dot { background: var(--blue); border-color: var(--blue); box-shadow: 0 0 0 6px var(--blue-soft); }
.journey .current .dot::after { content: ""; width: 10px; height: 10px; border-radius: 50%; background: #fff; }
.journey .lbl { font-size: 13px; font-weight: 600; color: var(--text2); line-height: 1.2; }
.journey .current .lbl { color: var(--blue); font-weight: 700; }
.journey .sub { font-size: 12px; color: var(--muted); font-family: var(--mono); }

/* Flight cards */
.flight { background: var(--card); border: 1px solid var(--line); border-radius: 14px; padding: 18px 22px; margin-bottom: 4px; }
.flight .top { display: flex; justify-content: space-between; align-items: center; gap: 12px; flex-wrap: wrap; margin-bottom: 12px; }
.flight .row { display: grid; grid-template-columns: minmax(0,1fr) minmax(0,1.2fr) minmax(0,1fr); align-items: center; gap: 12px; }
.flight .code { font-size: 30px; font-weight: 800; color: var(--navy); line-height: 1.1; }
.flight .name { font-size: 14px; color: var(--text2); }
.flight .when { font-size: 15px; font-weight: 700; margin-top: 6px; color: var(--ink); }
.flight .dur { display: flex; align-items: center; gap: 8px; color: var(--muted); font-size: 13px; }
.flight .dur i { flex: 1; border-top: 2px dotted var(--line2); }
.connection { display: flex; align-items: center; gap: 10px; padding: 8px 10px 12px; font-size: 14px; color: var(--text2); }

/* Timeline */
.timeline { list-style: none; margin: 0; padding: 0; }
.timeline li { position: relative; margin: 0 0 0 7px; padding: 0 0 18px 22px; border-left: 2px solid var(--line); }
.timeline li:last-child { border-left-color: transparent; padding-bottom: 0; }
.timeline li::before { content: ""; position: absolute; left: -9px; top: 2px; width: 16px; height: 16px;
  border-radius: 50%; box-sizing: border-box; background: #fff; border: 2px solid var(--green); }
.timeline li.latest::before { background: var(--blue); border-color: var(--blue); box-shadow: 0 0 0 4px var(--blue-soft); }
.timeline .ev { font-weight: 700; font-size: 16px; color: var(--ink); }
.timeline .ev span { font-family: var(--mono); font-size: 11.5px; color: var(--muted); font-weight: 500; margin-left: 6px; }
.timeline .where { font-size: 14px; color: var(--text2); }

/* Staff transaction steps */
.steps { list-style: none; margin: 4px 0 6px; padding: 0; display: flex; flex-direction: column; gap: 11px; }
.steps li { display: flex; gap: 12px; align-items: flex-start; font-size: 15px; margin: 0; }
.steps .n { flex: none; width: 26px; height: 26px; border-radius: 50%; background: var(--navy); color: #fff;
  font-size: 13px; font-weight: 700; display: flex; align-items: center; justify-content: center; }
.steps li.skip { color: var(--muted); }
.steps li.skip .n { background: #E6EBF2; color: var(--muted); }
.warn { font-size: 14px; padding: 10px 12px; border-radius: 10px; background: var(--amber-soft); color: var(--amber); margin: 6px 0; }

/* Supervisor */
.kpis { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 16px; margin-bottom: 8px; }
.kpi { background: var(--card); border: 1px solid var(--line); border-radius: 14px; padding: 16px 20px; }
.kpi .k { font-size: 14px; font-weight: 600; color: var(--text2); }
.kpi .v { font-size: 40px; font-weight: 800; color: var(--navy); line-height: 1.2; }
.kpi.alert { background: var(--amber-soft); border-color: #F2C98A; }
.kpi.alert .k, .kpi.alert .v { color: var(--amber); }
.gridtable { display: grid; gap: 10px 12px; align-items: center; font-size: 15px; }
.gridtable .h { font-size: 12.5px; font-weight: 700; color: var(--muted); text-transform: uppercase; letter-spacing: .05em; }
.bar { flex: 1; height: 8px; border-radius: 8px; background: #E6EBF2; overflow: hidden; }
.bar > i { display: block; height: 100%; background: var(--blue); }
.bar.full > i { background: var(--green); }
.hbar { height: 14px; border-radius: 4px; background: var(--navy); }

@media (max-width: 720px) {
  .kpis { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .hero-main h1 { font-size: 30px; }
  .journey .lbl { font-size: 11px; }
  .journey .sub { display: none; }
  .flight .code { font-size: 24px; }
  .tb-user { text-align: left; }
}
</style>
"""

PLANE = (
    '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" aria-hidden="true">'
    '<path d="M2 13l8-1 5-8h2l-2 8 5 .5 2-2.5h2l-1.5 4 1.5 4h-2l-2-2.5-5 .5 2 8h-2l-5-8-8-1z" '
    'stroke="#1B5FD6" stroke-width="1.5" stroke-linejoin="round"/></svg>'
)
BAG_MARK = (
    '<svg width="30" height="30" viewBox="0 0 30 30" fill="none" aria-hidden="true">'
    '<rect x="5" y="8" width="20" height="17" rx="3" stroke="#fff" stroke-width="2"/>'
    '<path d="M11 8V5.5A1.5 1.5 0 0 1 12.5 4h5A1.5 1.5 0 0 1 19 5.5V8" stroke="#fff" stroke-width="2"/>'
    '<path d="M5 15h20" stroke="#6FA8FF" stroke-width="2"/></svg>'
)
CHECK = (
    '<svg width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden="true">'
    '<path d="M3 7.5l2.5 2.5L11 4.5" stroke="#fff" stroke-width="2" stroke-linecap="round" '
    'stroke-linejoin="round"/></svg>'
)
CLOCK = (
    '<svg width="18" height="18" viewBox="0 0 18 18" fill="none" aria-hidden="true">'
    '<circle cx="9" cy="9" r="7" stroke="#566174" stroke-width="1.5"/>'
    '<path d="M9 5v4l3 2" stroke="#566174" stroke-width="1.5" stroke-linecap="round"/></svg>'
)


def esc(value):
    return html.escape("" if value is None else str(value))


def raw_html(markup):
    """Render trusted markup built in this file (DB values go through esc())."""
    st.markdown(markup, unsafe_allow_html=True)


def pill(text, tone):
    return f'<span class="pill pill-{tone}">{esc(text)}</span>'


def to_local(dt, airport_code):
    """Stored naive UTC -> aware local datetime at the airport, or None."""
    tz_name = AIRPORT_TZ.get(airport_code)
    if dt is None or tz_name is None:
        return None
    try:
        return dt.replace(tzinfo=timezone.utc).astimezone(ZoneInfo(tz_name))
    except Exception:  # no tz database available: just show UTC
        return None


def fmt_utc(dt, with_year=False):
    if dt is None:
        return "—"
    return dt.strftime("%d %b %Y, %H:%M UTC" if with_year else "%d %b %H:%M UTC")


def fmt_local(dt, airport_code):
    """Short local time, e.g. '13:10 local' (date added when it differs from UTC)."""
    local = to_local(dt, airport_code)
    if local is None:
        return ""
    return local.strftime("%H:%M local" if local.date() == dt.date() else "%d %b %H:%M local")


def when_html(dt, airport_code):
    """Two-line time: local first (what a traveller reads), UTC underneath."""
    local = to_local(dt, airport_code)
    if local is None:
        return f'<div class="when">{esc(dt.strftime("%d %b, %H:%M"))} UTC</div>'
    return (f'<div class="when">{esc(local.strftime("%d %b, %H:%M"))}</div>'
            f'<div class="small">local · {esc(dt.strftime("%H:%M"))} UTC</div>')


def stamp(dt, airport_code):
    """One-line time for lists: '17 Oct, 13:10 local · 11:10 UTC'."""
    local = to_local(dt, airport_code)
    utc = dt.strftime("%H:%M UTC")
    if local is None:
        return dt.strftime("%d %b, %H:%M UTC")
    return f'{local.strftime("%d %b, %H:%M")} local · {utc}'


def duration(start, end):
    minutes = int((end - start).total_seconds() // 60)
    return f"{minutes // 60} h {minutes % 60:02d} m"


def safe_key(text):
    return re.sub(r"\W", "_", text or "")


def db_error_message(err):
    if isinstance(err, psycopg2.errors.ForeignKeyViolation):
        return (
            "Rejected by the database: this flight is not part of the bag's itinerary "
            f"(foreign key `{err.diag.constraint_name}`)."
        )
    if isinstance(err, psycopg2.errors.CheckViolation):
        return f"Rejected by the database: check constraint `{err.diag.constraint_name}` failed."
    return f"Database error: {err.diag.message_primary or err}"


def table(rows, columns=None, column_config=None):
    """Read-only table. Datetime columns are labelled (UTC) because that is what is stored."""
    df = pd.DataFrame(rows)
    if df.empty:
        st.caption("No rows.")
        return
    if columns:
        df = df[columns]
    config = dict(column_config or {})
    labels = {}
    for col in df.columns:
        label = col.replace("_", " ").capitalize()
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            label += " (UTC)"
            config.setdefault(label, st.column_config.DatetimeColumn(label, format="D MMM YYYY, HH:mm"))
        labels[col] = label
    df = df.rename(columns=labels)
    config = {labels.get(k, k): v for k, v in config.items()}
    st.dataframe(df, hide_index=True, width="stretch", column_config=config)


def show_flash():
    """Result of the last transaction, shown as a banner. Text is unchanged from db/app."""
    flash = st.session_state.pop("flash", None)
    if flash:
        kind, message = flash
        title, _, detail = message.partition("  \n")
        raw_html(
            f'<div class="banner banner-{"success" if kind == "success" else "error"}" role="status">'
            f'<b>{esc(title)}</b><span>{esc(detail)}</span></div>'
        )


def airport_names():
    return {a["airport_code"]: a["name"] for a in db.airports()}


def journey_status(segments, loc):
    """Short status derived only from BaggageFlight statuses + latest scan."""
    if not segments:
        return None
    in_air = next((s for s in segments if s["transport_status"] == "LOADED"), None)
    if in_air:
        return ("blue", "On board", in_air)
    if all(s["transport_status"] == "ARRIVED" for s in segments):
        if loc and loc["event_type"] == "COLLECTED":
            return ("green", "Collected", None)
        return ("green", "Arrived at destination", None)
    nxt = next(s for s in segments if s["transport_status"] == "ASSIGNED")
    return ("amber", "Waiting to be loaded", nxt)


# ---------- Top bar ----------

def top_bar(user=None):
    with st.container(key="topbar"):
        left, right = st.columns([3, 2], vertical_alignment="center")
        area = {"Passenger": "Baggage Tracker", "Ground staff": "Ground operations",
                "Supervisor": "Operations"}.get(user["role"] if user else None, "Baggage Tracker")
        left.markdown(
            f'<div class="tb-brand">{BAG_MARK}<b>TXZ</b><span>{esc(area)}</span></div>',
            unsafe_allow_html=True,
        )
        if user is None:
            return
        with right:
            info, button = st.columns([3, 1.1], vertical_alignment="center")
            chip = ""
            if user["role"] != "Passenger":
                mode = db.connection_mode()
                chip = f'<span class="tb-chip">{"Cloud database" if mode == "cloud" else "Local database"}</span>'
            who = f"Signed in as <strong>{esc(user['name'])}</strong>" if user["role"] == "Passenger" \
                else f"<strong>{esc(user['role'])}</strong>"
            info.markdown(f'<div class="tb-user">{chip}{who}</div>', unsafe_allow_html=True)
            if button.button("Log out", key="logout", width="stretch"):
                st.session_state.clear()
                st.rerun()


# ---------- Login ----------

def _fill_passenger_demo():
    st.session_state.login_tag = DEMO_TAG
    st.session_state.login_email = DEMO_EMAIL


def _fill_staff_demo(role):
    st.session_state.login_role = role
    st.session_state.login_password = STAFF_PASSWORDS[role]


def login_page():
    top_bar()
    _, mid, _ = st.columns([1, 1.5, 1])
    with mid:
        st.write("")
        st.title("Track your bag")
        st.caption("COMP9120 prototype · PostgreSQL baggage tracking")
        passenger_tab, staff_tab = st.tabs(["I'm a passenger", "Airport staff"])

        with passenger_tab:
            with st.form("passenger_login", border=True):
                tag = st.text_input("Baggage tag number", placeholder="e.g. 100001", key="login_tag")
                email = st.text_input("Booking email", placeholder="name@example.com", key="login_email")
                if st.form_submit_button("Track my bag", type="primary", width="stretch"):
                    user = db.passenger_login(tag, email)
                    if user:
                        st.session_state.user = {"role": "Passenger", "tag": tag.strip(), **user}
                        st.rerun()
                    st.error("No bag with this tag belongs to that email.")
            st.button("Fill demo login (Eva Liu, bag 100006)", key="demo_passenger",
                      on_click=_fill_passenger_demo, width="stretch")
            st.caption(f"Demo: `{DEMO_TAG}` / `{DEMO_EMAIL}`")

        with staff_tab:
            with st.form("staff_login", border=True):
                role = st.selectbox("Role", list(STAFF_PASSWORDS), key="login_role")
                password = st.text_input("Password", type="password", key="login_password")
                if st.form_submit_button("Sign in", type="primary", width="stretch"):
                    if password == STAFF_PASSWORDS[role]:
                        st.session_state.user = {"role": role, "name": role}
                        st.rerun()
                    st.error("Incorrect password.")
            c1, c2 = st.columns(2)
            c1.button("Fill ground staff", key="demo_staff", on_click=_fill_staff_demo,
                      args=("Ground staff",), width="stretch")
            c2.button("Fill supervisor", key="demo_super", on_click=_fill_staff_demo,
                      args=("Supervisor",), width="stretch")
            st.caption("Demo passwords: `staff9120` (ground staff), `super9120` (supervisor)")


# ---------- Passenger ----------

def journey_html(segments, history):
    """Bag journey stepper: check-in, then load/arrive per segment, then claim."""
    events = {h["event_type"] for h in history}
    steps = [("Checked in", segments[0]["departure_airport"], bool(history))]
    for i, s in enumerate(segments):
        last = i == len(segments) - 1
        steps.append(("Loaded", s["flight_number"], s["transport_status"] in ("LOADED", "ARRIVED")))
        steps.append(("Arrived" if last else "Transfer", s["arrival_airport"],
                      s["transport_status"] == "ARRIVED"))
    steps.append(("Baggage claim", segments[-1]["arrival_airport"], "COLLECTED" in events))

    current = next((i for i, (_, _, done) in enumerate(steps) if not done), None)
    n = len(steps)
    reached = (current if current is not None else n - 1) / (n - 1)
    inset = 50 / n
    fill = f"{reached * 100:.1f}%"
    items = []
    for i, (label, sub, done) in enumerate(steps):
        cls = "done" if done else ("current" if i == current else "")
        dot = CHECK if done else ""
        items.append(
            f'<li class="{cls}"><span class="dot">{dot}</span>'
            f'<span class="lbl">{esc(label)}</span><span class="sub">{esc(sub)}</span></li>'
        )
    return (
        f'<div class="journey" aria-label="Bag journey">'
        f'<div class="track" style="left:{inset:.2f}%;right:{inset:.2f}%;'
        f'background:linear-gradient(90deg,#11733F {fill},#DDE3EC {fill})"></div>'
        f'<ol style="grid-template-columns:repeat({n},minmax(0,1fr))">{"".join(items)}</ol></div>'
    )


def hero_html(user, tag, weight, segments, history, loc, names):
    status = journey_status(segments, loc)
    lines = []
    if loc is None:
        headline = "This bag has not been scanned yet"
    elif status and status[1] == "On board":
        s = status[2]
        headline = f"Your bag is on board {s['flight_number']}"
    elif status and status[1] == "Collected":
        headline = "Your bag has been collected"
    elif status and status[1] == "Arrived at destination":
        headline = f"Your bag has arrived at {loc['airport_name']} ({loc['airport_code']})"
    else:
        headline = f"Your bag is at {loc['airport_name']} ({loc['airport_code']})"

    if loc:
        local = to_local(loc["scanned_at"], loc["airport_code"])
        when = (f'{local:%d %b, %H:%M} local time <span class="small">'
                f'({loc["scanned_at"]:%H:%M} UTC)</span>') if local else esc(fmt_utc(loc["scanned_at"]))
        lines.append(
            f'<p>{esc(EVENT_LABELS.get(loc["event_type"], loc["event_type"]))} at '
            f'<strong>{esc(loc["point_name"])}</strong> · {when}</p>'
        )
    if status and status[2] is not None:
        s = status[2]
        if status[1] == "On board":
            lines.append(
                f'<p>Next: arrival at <strong>{esc(names.get(s["arrival_airport"], s["arrival_airport"]))}'
                f'</strong>, scheduled {esc(fmt_local(s["scheduled_arrival"], s["arrival_airport"]) or fmt_utc(s["scheduled_arrival"]))}</p>'
            )
        else:
            lines.append(
                f'<p>Next: loading onto <strong class="mono">{esc(s["flight_number"])}</strong> to '
                f'{esc(names.get(s["arrival_airport"], s["arrival_airport"]))}, departs '
                f'{esc(fmt_local(s["scheduled_departure"], s["departure_airport"]) or fmt_utc(s["scheduled_departure"]))}</p>'
            )

    chip = pill(status[1], status[0]) if status else ""
    journey = journey_html(segments, history) if segments else ""
    stops = [segments[0]["departure_airport"]] + [s["arrival_airport"] for s in segments] if segments else []
    route = f" {PLANE} ".join(f"<span>{esc(c)}</span>" for c in stops)
    origin = stops[0] if stops else "—"
    final = stops[-1] if stops else "—"
    return (
        '<div class="hero-band"><div class="hero"><div class="hero-main">'
        f'<div style="display:flex;gap:10px;align-items:center;flex-wrap:wrap">'
        f'<span class="eyebrow">Bag status</span>{chip}</div>'
        f'<h1>{esc(headline)}</h1>{"".join(lines)}{journey}'
        '<div class="small">Based on the most recent scan event, not real-time GPS.</div>'
        '</div><div class="tagcard"><span class="eyebrow" style="color:#3A4659">Bag tag</span>'
        f'<span class="tagno">{esc(tag)}</span><div class="grid">'
        f'<div><div class="k">Passenger</div><div class="v">{esc(user["name"])}</div></div>'
        f'<div><div class="k">Weight</div><div class="v">{esc(weight)} kg</div></div>'
        f'<div><div class="k">From</div><div class="v">{esc(origin)}</div></div>'
        f'<div><div class="k">Final destination</div><div class="v">{esc(final)}</div></div>'
        f'</div><div class="route">{route}</div></div></div></div>'
    )


def flights_html(segments, names):
    parts = []
    for i, s in enumerate(segments):
        words, tone = SEGMENT_WORDS.get(s["transport_status"], (s["transport_status"], "grey"))
        dep, arr = s["departure_airport"], s["arrival_airport"]
        parts.append(
            '<div class="flight"><div class="top"><div style="display:flex;gap:12px;align-items:center">'
            f'<span class="small" style="font-weight:700">Flight {i + 1} of {len(segments)}</span>'
            f'<span class="mono" style="font-weight:600;font-size:16px">{esc(s["flight_number"])}</span></div>'
            f'{pill(words, tone)}</div><div class="row">'
            f'<div><div class="code">{esc(dep)}</div><div class="name">{esc(names.get(dep, ""))}</div>'
            f'{when_html(s["scheduled_departure"], dep)}</div>'
            f'<div class="dur" aria-hidden="true"><i></i><span>'
            f'{esc(duration(s["scheduled_departure"], s["scheduled_arrival"]))}</span><i></i></div>'
            f'<div style="text-align:right"><div class="code">{esc(arr)}</div>'
            f'<div class="name">{esc(names.get(arr, ""))}</div>'
            f'{when_html(s["scheduled_arrival"], arr)}</div></div></div>'
        )
        if i + 1 < len(segments):
            nxt = segments[i + 1]
            parts.append(
                f'<div class="connection">{CLOCK}Connection in {esc(names.get(arr, arr))} · '
                f'{esc(duration(s["scheduled_arrival"], nxt["scheduled_departure"]))}</div>'
            )
    return "".join(parts)


def history_html(history):
    items = []
    for i, h in enumerate(reversed(history)):  # newest first
        flight = f" · {h['flight_number']}" if h["flight_number"] else ""
        items.append(
            f'<li class="{"latest" if i == 0 else ""}">'
            f'<div class="ev">{esc(EVENT_LABELS.get(h["event_type"], h["event_type"]))}'
            f'<span>{esc(h["event_type"])}</span></div>'
            f'<div class="where">{esc(h["point_name"])}{esc(flight)}</div>'
            f'<div class="small">{esc(stamp(h["scanned_at"], h["airport_code"]))}</div></li>'
        )
    return f'<ol class="timeline">{"".join(items)}</ol>'


def passenger_page(user):
    bags = db.passenger_bags(user["passenger_id"])
    tags = [b["tag_code"] for b in bags]
    weights = {b["tag_code"]: b["weight"] for b in bags}
    default = tags.index(user["tag"]) if user["tag"] in tags else 0
    tag = tags[default]
    if len(tags) > 1:
        tag = st.radio(
            "Your bags", tags, index=default, horizontal=True,
            format_func=lambda t: f"Tag {t} · {weights[t]} kg",
        )

    names = airport_names()
    loc = db.latest_location(tag)
    segments = db.itinerary(tag)
    history = db.scan_history(tag)

    raw_html(hero_html(user, tag, weights[tag], segments, history, loc, names))

    report = db.open_report(tag)
    if report:
        st.write("")
        st.warning(
            f"**Open missing-baggage report** since {fmt_utc(report['reported_at'], True)}  \n"
            f"{report['description']}"
        )

    st.write("")
    left, right = st.columns([1.65, 1], gap="large")
    with left:
        raw_html('<div class="section-title">Your flights</div>')
        if segments:
            raw_html(flights_html(segments, names))
        else:
            st.info("No flights assigned to this bag.")
    with right:
        raw_html('<div class="section-title">Scan history</div>')
        if history:
            raw_html(f'<div class="card">{history_html(history)}</div>')
        else:
            st.caption("No scans recorded yet.")

    st.write("")
    with st.expander("Show full data tables"):
        st.markdown("**Flight itinerary**")
        table(segments, [
            "segment_order", "flight_number", "departure_airport", "arrival_airport",
            "scheduled_departure", "scheduled_arrival", "transport_status",
        ])
        st.markdown("**Tracking history** (oldest first)")
        table(history)


# ---------- Ground staff ----------

def transaction_steps(action, seg):
    rule = db.SEGMENT_ACTIONS[action]
    airport = seg[rule["airport_column"]]
    if action != "LOAD":
        step2 = '<li class="skip"><span class="n">2</span><span>Previous segment check: not needed for an arrival</span></li>'
    elif seg["segment_order"] == 1:
        step2 = '<li class="skip"><span class="n">2</span><span>Previous segment check: not needed for the first flight</span></li>'
    else:
        step2 = '<li><span class="n">2</span><span>Check the previous segment has <strong>ARRIVED</strong></span></li>'
    return (
        '<ol class="steps">'
        f'<li><span class="n">1</span><span>Lock segment {esc(seg["flight_number"])} '
        f'(<span class="mono">SELECT … FOR UPDATE</span>) and check it is '
        f'<strong>{rule["from_status"]}</strong></span></li>'
        f'{step2}'
        f'<li><span class="n">3</span><span>Record a <strong>{rule["event_type"]}</strong> scan at '
        f'{esc(airport)}</span></li>'
        f'<li><span class="n">4</span><span>Set the segment to <strong>{rule["to_status"]}</strong>, '
        'then commit</span></li></ol>'
    )


def segment_transaction_tab():
    show_flash()
    with st.container(key="findbag"):
        c1, c2 = st.columns([1, 2], vertical_alignment="bottom")
        tag = c1.text_input("Bag tag", value=DEMO_TAG, key="tx_tag").strip()
        segments = db.itinerary(tag)
        if segments:
            stops = [segments[0]["departure_airport"]] + [s["arrival_airport"] for s in segments]
            c2.markdown(
                f'<div style="padding-bottom:10px;font-size:15px;color:#3A4659">'
                f'<span class="mono" style="font-weight:600">{" → ".join(esc(x) for x in stops)}</span>'
                f' · {len(segments)} flight segment{"s" if len(segments) > 1 else ""}</div>',
                unsafe_allow_html=True,
            )
    if not segments:
        st.info("No itinerary found for this tag.")
        return

    st.write("")
    left, right = st.columns([1.25, 1], gap="large")
    signature = safe_key(tag) + "_" + "".join(s["transport_status"][0] for s in segments)

    with left:
        raw_html('<div class="section-title">1. Choose a flight segment</div>')
        next_open = next(
            (i for i, s in enumerate(segments) if s["transport_status"] != "ARRIVED"), 0
        )
        seg = segments[st.radio(
            "Flight segment",
            range(len(segments)),
            index=next_open,
            key=f"segpick_{signature}",
            label_visibility="collapsed",
            format_func=lambda i: (
                f"Segment {segments[i]['segment_order']} · **{segments[i]['flight_number']}** · "
                f"{segments[i]['departure_airport']} → {segments[i]['arrival_airport']} · "
                f"{segments[i]['transport_status']}"
            ),
        )]
        raw_html('<div class="section-title" style="margin-top:18px">2. Choose an action</div>')
        action = st.radio(
            "Action",
            ["LOAD", "ARRIVE"],
            index=1 if seg["transport_status"] == "LOADED" else 0,
            key=f"action_{signature}_{seg['flight_id']}",
            label_visibility="collapsed",
            horizontal=True,
            format_func=lambda a: {
                "LOAD": "Confirm loading · ASSIGNED → LOADED",
                "ARRIVE": "Confirm arrival · LOADED → ARRIVED",
            }[a],
        )

    with right:
        with st.container(key="runpanel"):
            raw_html(
                '<div class="section-title" style="margin-top:4px">3. Run the transaction</div>'
                '<p style="margin:0 0 8px;color:#3A4659">One database transaction. '
                'If any step fails, nothing is saved.</p>'
            )
            raw_html(transaction_steps(action, seg))
            expected = db.SEGMENT_ACTIONS[action]["from_status"]
            if seg["transport_status"] != expected:
                raw_html(
                    f'<div class="warn">This segment is {esc(seg["transport_status"])}, not {expected}, '
                    'so the database will reject it. Useful for showing the business rule.</div>'
                )

            with st.expander("Demo options: failure and locking"):
                simulate_failure = st.checkbox("Fail after inserting the scan (shows rollback)")
                hold_seconds = st.number_input(
                    "Hold the row lock for N seconds before committing (open a second tab to test)",
                    min_value=0, max_value=30, value=0,
                )

            rule = db.SEGMENT_ACTIONS[action]
            label = (f"Confirm loading onto {seg['flight_number']}" if action == "LOAD"
                     else f"Confirm arrival at {seg[rule['airport_column']]}")
            if simulate_failure:
                label += " (will fail on purpose)"
            elif hold_seconds:
                label += f" (holds lock {int(hold_seconds)}s)"
            if st.button(label, type="primary", width="stretch"):
                before = db.scan_count(tag)
                with st.spinner("Running transaction…"):
                    try:
                        message = db.advance_segment(tag, seg["flight_id"], action,
                                                     simulate_failure, int(hold_seconds))
                        kind = "success"
                    except db.SimulatedFailure as err:
                        message, kind = f"{err} The whole transaction was rolled back.", "error"
                    except db.BusinessRuleError as err:
                        message, kind = f"Rejected: {err} Nothing was changed.", "error"
                    except psycopg2.Error as err:
                        message, kind = db_error_message(err), "error"
                after = db.scan_count(tag)
                st.session_state.flash = (kind, f"{message}  \nScan events for {tag}: {before} → {after}")
                st.rerun()


def record_scan_tab():
    st.caption(
        "LOADING and ARRIVAL scans go through the transaction tab, "
        "so the segment status always matches the scan history."
    )
    airport_rows = db.airports()
    flight_rows = db.flights()
    with st.form("record_scan", border=True):
        c1, c2 = st.columns(2)
        with c1:
            tag = st.text_input("Bag tag", value=DEMO_TAG)
            airport = st.selectbox(
                "Airport", [a["airport_code"] for a in airport_rows],
                format_func=lambda c: f"{c} – {next(a['name'] for a in airport_rows if a['airport_code'] == c)}",
            )
        with c2:
            event_type = st.selectbox(
                "Event", list(GROUND_EVENTS),
                format_func=lambda e: f"{EVENT_LABELS[e]} ({e})",
            )
            flight_index = st.selectbox(
                "Related flight (optional)",
                [None] + list(range(len(flight_rows))),
                format_func=lambda i: "None" if i is None else (
                    f"{flight_rows[i]['flight_number']} "
                    f"{flight_rows[i]['departure_airport']} → {flight_rows[i]['arrival_airport']} "
                    f"({flight_rows[i]['scheduled_departure']:%m-%d %H:%M} UTC)"
                ),
            )
        flight = None if flight_index is None else flight_rows[flight_index]
        if st.form_submit_button("Record scan", type="primary"):
            try:
                scan_id = db.record_scan(
                    tag.strip(), airport, GROUND_EVENTS[event_type], event_type,
                    flight["flight_id"] if flight else None,
                )
                st.success(f"Scan #{scan_id} recorded: {tag} {event_type} at {airport}.")
            except db.BusinessRuleError as err:
                st.error(str(err))
            except psycopg2.Error as err:
                st.error(db_error_message(err))


def staff_page():
    st.title("Baggage handling")
    tx_tab, scan_tab = st.tabs(["Confirm loading / arrival", "Record ground scan"])
    with tx_tab:
        segment_transaction_tab()
    with scan_tab:
        record_scan_tab()


# ---------- Supervisor ----------

def supervisor_page():
    st.title("Today at a glance")
    counts = db.summary_counts()
    exceptions = db.transfer_exceptions()

    raw_html(
        '<div class="kpis">'
        f'<div class="kpi"><div class="k">Bags tracked</div><div class="v">{counts["bags"]}</div></div>'
        f'<div class="kpi"><div class="k">Segments in flight</div><div class="v">{counts["in_flight"]}</div></div>'
        f'<div class="kpi"><div class="k">Open missing reports</div><div class="v">{counts["open_reports"]}</div></div>'
        f'<div class="kpi{" alert" if exceptions else ""}"><div class="k">Transfer exceptions</div>'
        f'<div class="v">{len(exceptions)}</div></div></div>'
    )

    raw_html(
        '<div class="section-title" style="margin-top:18px">Needs attention</div>'
        '<p class="small" style="margin:-6px 0 10px">Previous segment ARRIVED, but the connecting '
        'segment is still ASSIGNED after its scheduled departure. Flags a missing loading '
        'confirmation for review.</p>'
    )
    if exceptions:
        cols = "grid-template-columns:minmax(0,.8fr) minmax(0,1.2fr) minmax(0,.8fr) minmax(0,1fr) minmax(0,1.3fr) minmax(0,.9fr)"
        rows = [
            f'<span class="h">Tag</span><span class="h">Passenger</span><span class="h">Flight</span>'
            f'<span class="h">Route</span><span class="h">Scheduled departure</span><span class="h">Status</span>'
        ]
        for e in exceptions:
            local = to_local(e["scheduled_departure"], e["departure_airport"])
            when = (f'{local:%d %b, %H:%M} local<br><span class="small">{e["scheduled_departure"]:%H:%M} UTC</span>'
                    if local else esc(fmt_utc(e["scheduled_departure"])))
            rows.append(
                f'<span class="mono" style="font-weight:600">{esc(e["tag_code"])}</span>'
                f'<span>{esc(e["passenger"])}</span><span class="mono">{esc(e["flight_number"])}</span>'
                f'<span style="font-weight:700">{esc(e["departure_airport"])} → {esc(e["arrival_airport"])}</span>'
                f'<span>{when}</span><span>{pill("Not loaded · " + e["transport_status"], "amber")}</span>'
            )
        raw_html(f'<div class="card"><div class="gridtable" style="{cols}">{"".join(rows)}</div></div>')
    else:
        st.success("No transfer exceptions.")

    st.write("")
    left, right = st.columns([1.7, 1], gap="large")
    progress = db.flight_load_progress()
    for row in progress:
        done = (row["loaded"] or 0) + (row["arrived"] or 0)
        row["loaded_or_arrived"] = done / row["bags"] if row["bags"] else 0.0

    with left:
        raw_html('<div class="section-title">Loading progress by flight</div>')
        # Most recent departures first: the flights staff are working on now.
        with_bags = sorted((r for r in progress if r["bags"]),
                           key=lambda r: r["scheduled_departure"], reverse=True)
        cols = "grid-template-columns:minmax(0,.8fr) minmax(0,1fr) minmax(0,2fr) minmax(0,.4fr)"
        rows = ['<span class="h">Flight</span><span class="h">Route</span>'
                '<span class="h">Loaded or arrived</span><span class="h" style="text-align:right">Bags</span>']
        for r in with_bags[:6]:
            pct = r["loaded_or_arrived"]
            rows.append(
                f'<span class="mono">{esc(r["flight_number"])}</span>'
                f'<span>{esc(r["departure_airport"])} → {esc(r["arrival_airport"])}</span>'
                f'<span style="display:flex;align-items:center;gap:10px">'
                f'<span class="bar{" full" if pct >= 1 else ""}"><i style="width:{pct * 100:.0f}%"></i></span>'
                f'<span style="width:42px;text-align:right">{pct:.0%}</span></span>'
                f'<span style="text-align:right">{r["bags"]}</span>'
            )
        raw_html(f'<div class="card"><div class="gridtable" style="{cols}">{"".join(rows)}</div>'
                 '<p class="small" style="margin:12px 0 0">Most recent departures first.</p></div>')
        with st.expander(f"Show all {len(progress)} flights"):
            table(progress, [
                "flight_number", "departure_airport", "arrival_airport", "scheduled_departure",
                "loaded_or_arrived", "bags", "assigned", "loaded", "arrived",
            ], column_config={
                "loaded_or_arrived": st.column_config.ProgressColumn(
                    "Loaded or arrived", min_value=0.0, max_value=1.0, format="percent",
                ),
            })

    with right:
        raw_html('<div class="section-title">Open reports by last airport</div>')
        by_airport = db.open_reports_by_airport()
        if by_airport:
            top = max(r["open_reports"] for r in by_airport)
            bars = "".join(
                f'<div style="display:grid;grid-template-columns:52px minmax(0,1fr) 28px;gap:12px;'
                f'align-items:center;margin-bottom:12px"><span class="mono" style="font-weight:600">'
                f'{esc(r["last_recorded_airport"])}</span><span><span class="hbar" style="display:block;'
                f'width:{r["open_reports"] / top * 100:.0f}%"></span></span>'
                f'<span style="text-align:right;font-weight:700">{r["open_reports"]}</span></div>'
                for r in by_airport
            )
            raw_html(f'<div class="card">{bars}</div>')
        else:
            st.info("No open reports.")

    with st.expander("Show transfer exceptions as a table"):
        table(exceptions)


# ---------- Main ----------

st.markdown(CSS, unsafe_allow_html=True)

try:
    db.query("SELECT 1")
except psycopg2.OperationalError as err:
    top_bar()
    st.error(f"Cannot connect to PostgreSQL: {err}")
    st.stop()

user = st.session_state.get("user")
if user is None:
    login_page()
else:
    top_bar(user)
    if user["role"] == "Passenger":
        passenger_page(user)
    elif user["role"] == "Ground staff":
        staff_page()
    else:
        supervisor_page()
