# Handoff Notes (for whichever AI / person edits this next)

Project: COMP9120 group project — TXZ Baggage Tracker.
Stack: Streamlit + psycopg2 + PostgreSQL. Report language and UI are in English.

## Files

- `app.py` — UI: login (passenger / ground staff / supervisor), passenger
  tracking page, staff "confirm loading/arrival" transaction page + ground
  scan form, supervisor dashboard. Styling is one CSS block (`CSS`) plus small
  HTML builders (`hero_html`, `journey_html`, `flights_html`, `history_html`,
  `transaction_steps`); DB values always go through `esc()` (html.escape)
  before being put in HTML. Widgets styled by CSS use `key=` so Streamlit adds
  an `st-key-...` class (top bar, segment picker, action toggle, run panel).
- `.streamlit/config.toml` — colour theme only (no secrets, safe to commit).
- `db.py` — ALL SQL. `advance_segment()` is the assessed multi-step
  transaction: SELECT ... FOR UPDATE, status/business-rule checks, INSERT
  ScanEvent, UPDATE BaggageFlight, commit/rollback. Do not split it into
  separate commits.
- `database/01_schema.sql`, `02_sample_data.sql` — schema + demo data.
  `reset_database.sql` wipes the public schema so 01+02 can be re-run.
- `README.md` — local run, Neon + Streamlit Cloud deploy, demo logins.

## Hard constraints

1. Connection is dual-mode and must stay that way: if `DATABASE_URL`
   (env var or Streamlit Secrets) exists → cloud (Neon); otherwise local
   `baggage_demo` via PG* env vars. Never hard-code a connection string
   or password in code.
2. Do NOT change the database schema. The report's ER diagram and
   normalisation section are already written against these 8 tables.
   Staff passwords are demo-only (schema has no staff table) and are read
   from env/Secrets with demo defaults in `app.py`.
3. UI text stays in English (assessors watch the video / live demo).
4. Timestamps are timezone-naive UTC; new scans use
   `(now() AT TIME ZONE 'UTC')`. Keep that. Local airport time is computed
   in the UI only (`AIRPORT_TZ` + `fmt_local` in `app.py`); nothing local is
   ever written to the database. Never use bare `now()` / `CURRENT_TIMESTAMP`
   for a TIMESTAMP column: on the local Mac Postgres the session time zone
   is Australia/Sydney, so it would store Sydney time (+10/+11 h), while Neon
   would store UTC. (`MissingReport.reported_at DEFAULT CURRENT_TIMESTAMP`
   has this trap; the app never inserts reports, so it is not hit today.
   If you add an insert, pass `(now() AT TIME ZONE 'UTC')` explicitly.)

## Main bag for the demo video

Passenger Eva Liu, tag `100006`, email `eliu6879@gmail.com`.
Staff password `staff9120`, supervisor `super9120`.
Suggested flow: passenger view (bag at FRA) → staff confirm loading with
"simulate failure" on (rollback: scan count unchanged) → again for real
(LOADED) → supervisor dashboard.

## Run / verify after editing

```bash
# Postgres.app must be running; local DB baggage_demo already has demo data
~/.venvs/comp9120-baggage/bin/streamlit run app.py   # http://localhost:8501
# or double-click Open-Local.command
```

If you change schema or data: re-run reset + 01 + 02 against the target DB
(see README "Updating after deployment").

## Working agreement between editors

- One editor at a time on the same file — file writes overwrite each other.
- If you change behaviour, update this file and `README.md` demo flow so
  the next editor (human or AI) sees what happened.

## Change log

- 2026-10-20 (Cursor agent): cloud-ready package — DATABASE_URL support,
  Secrets-based staff passwords, database/ SQL folder, reset script,
  deploy README, Open-Local.command launcher. Local + cloud modes tested.
- 2026-10-20 (Claude, Cowork): UI redesign, behaviour unchanged. New theme
  (`.streamlit/config.toml` + CSS), centred login with "Fill demo login"
  buttons, passenger page with last-location card, one-line journey status,
  visual route (airport stops + flight legs with status chips) and a
  newest-first tracking timeline (old tables kept under "Show as tables"),
  times shown as UTC plus airport local time. Staff transaction page split
  into Step 1/2/3 with a plain-English preview of the transaction steps and a
  warning when the chosen action will be rejected (button still runs it, for
  the business-rule demo). Supervisor: progress-bar column on loading
  progress. Sidebar shows "Database: Local PostgreSQL / Cloud (Neon)".
  `db.py`: only added display helper `connection_mode()`; all SQL and
  `advance_segment()` untouched. Schema/data untouched. `requirements.txt`:
  `streamlit>=1.50` (the existing `width="stretch"` calls need it) and
  `tzdata` (local-time display on Linux/Windows). Tested against a Postgres
  with session time zone Australia/Sydney: rollback demo (scan count 2 -> 2),
  real load (2 -> 3), business-rule rejection, ground scan, DATABASE_URL mode.
- 2026-10-20 (Claude, Cowork), second pass: airline-app style from the design
  canvas, behaviour unchanged. Navy top bar replaces the sidebar (Log out and
  the Local/Cloud database chip live there). Passenger: status hero with bag
  journey stepper (check-in, load/arrive per segment, claim) and a bag-tag
  card; flight cards with local + UTC times, flight duration and connection
  time; scan history timeline. Staff: segment picker drawn as cards (still a
  radio, same index logic), action as a pill toggle, run panel with the 4
  transaction steps; button text names the action ("Confirm loading onto
  TXZ501"). Supervisor: KPI tiles, "Needs attention" list, progress bars,
  bar list for open reports; full tables kept in expanders. Theme colours in
  `.streamlit/config.toml` updated. `db.py`, SQL, schema untouched. Retested
  on a Sydney-time-zone Postgres: rollback 2 -> 2, commit 2 -> 3, business
  rule rejection 2 -> 2, ground scan, phone width (390 px) without sideways
  scroll.
- 2026-10-20 (Claude, Cowork): supervisor "Loading progress by flight" card now
  lists the most recent departures first (was lowest progress first), so a
  flight just confirmed by ground staff is visible without expanding. Display
  only; query unchanged.
