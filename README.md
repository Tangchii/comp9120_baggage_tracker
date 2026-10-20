# TXZ Baggage Tracker — COMP9120 Prototype

Streamlit prototype connected to PostgreSQL. Passengers check their bag's last
recorded location and itinerary; ground staff record scans and confirm loading /
arrival as a multi-step transaction (with rollback and row-lock demos);
supervisors see transfer exceptions and loading statistics.

```
app.py                  Streamlit interface (login, passenger, staff, supervisor)
db.py                   All SQL + the confirm-loading/arrival transaction
requirements.txt        Python dependencies
database/
  01_schema.sql         Table definitions (run once on an empty database)
  02_sample_data.sql    Demo data (run once, right after 01)
  03_sample_queries.sql Reference queries only — not used by the app
  reset_database.sql    Wipes the public schema so 01+02 can be re-run
.streamlit/
  secrets.toml.example  Template for Streamlit Cloud Secrets (no real passwords)
```

## Demo logins

| Role | Login |
|---|---|
| Passenger | Tag `100006`, email `eliu6879@gmail.com` |
| Ground staff | Password `staff9120` |
| Supervisor | Role "Supervisor", password `super9120` |

Suggested video flow (under 3 minutes): log in as Eva Liu and show bag 100006
waiting at FRA; as ground staff, run "Confirm loading" once with the
"Fail after inserting the scan" option on (scan count unchanged = rollback),
then again for real (status becomes LOADED); finally open the supervisor
dashboard for transfer exceptions and open reports by airport.

## Run locally

**Easy way (Mac):** double-click `Open-Local.command` in this folder. It starts
Postgres.app if needed, then launches the app and opens
<http://localhost:8501>. Close it with Control+C in that window, or just close
the window. No internet is needed for the local version.

**Manual way:**

1. Start Postgres.app and create the demo database once (skip if it exists):

```bash
PG=/Applications/Postgres.app/Contents/Versions/latest/bin
$PG/createdb baggage_demo
$PG/psql -d baggage_demo -f database/01_schema.sql
$PG/psql -d baggage_demo -f database/02_sample_data.sql
```

2. Install dependencies and start the app:

```bash
python3 -m venv ~/.venvs/comp9120-baggage
~/.venvs/comp9120-baggage/bin/pip install -r requirements.txt
~/.venvs/comp9120-baggage/bin/streamlit run app.py
# open http://localhost:8501
```

With no configuration the app connects to local database `baggage_demo`
(via `PGHOST`/`PGPORT`/`PGDATABASE`/`PGUSER`/`PGPASSWORD` if set).

## Deploy to the cloud (Neon + Streamlit Community Cloud)

### 1. Create the cloud database (Neon)

1. Sign up at <https://neon.tech> and create a project (free tier is fine).
2. In the project dashboard click **Connect** and copy the connection string.
   For the app, prefer the **pooled** endpoint (host contains `-pooler`).
   It looks like:
   `postgresql://user:password@ep-xxx-pooler.region.aws.neon.tech/dbname?sslmode=require`
3. Load the schema and demo data from your machine (same SQL files as local):

```bash
PG=/Applications/Postgres.app/Contents/Versions/latest/bin
URL="postgresql://user:password@ep-xxx.region.aws.neon.tech/dbname?sslmode=require"
$PG/psql "$URL" -f database/01_schema.sql
$PG/psql "$URL" -f database/02_sample_data.sql
```

   (Alternatively paste each file into Neon's **SQL Editor** and run it —
   run `01_schema.sql` first, then `02_sample_data.sql`.)

   Alternative — copy your *current local state* instead of fresh demo data:

```bash
$PG/pg_dump -d baggage_demo -f baggage_backup.sql
$PG/psql "$URL" -f baggage_backup.sql
```

### 2. Put the code on GitHub

Create a GitHub repository whose root contains `app.py`, `db.py` and
`requirements.txt` (i.e. push the contents of this `prototype/` folder).
`.gitignore` already excludes `.streamlit/secrets.toml`, so no password can
be committed by accident.

### 3. Deploy on Streamlit Community Cloud

1. Go to <https://share.streamlit.io>, sign in with GitHub, **New app**.
2. Select the repository/branch and set the main file to `app.py`.
3. Open **Advanced settings → Secrets** and paste (see
   `.streamlit/secrets.toml.example`):

```toml
DATABASE_URL = "postgresql://user:password@ep-xxx-pooler.region.aws.neon.tech/dbname?sslmode=require"
STAFF_PASSWORD = "staff9120"
SUPERVISOR_PASSWORD = "super9120"
```

4. Deploy. The app reads `DATABASE_URL` from Secrets (see `db.py`), so no
   code change is needed between local and cloud.

### Updating after deployment

- **Code / layout changes:** push to GitHub — Streamlit Cloud redeploys
  automatically.
- **Data changes:** run the SQL against the Neon URL with `psql` as above.
- **Reset demo data before filming:** run `database/reset_database.sql`,
  then `01_schema.sql`, then `02_sample_data.sql` against the Neon URL.

## Notes

- All stored timestamps are timezone-naive and interpreted as UTC; new scans
  use the database server's UTC clock, so local (Sydney) and cloud (UTC)
  servers record the same values. The passenger page also shows each time in
  the airport's local time; that conversion happens only in the interface.
- The staff and supervisor top bar shows "Local database" or "Cloud database",
  so the video makes clear which version is running.
- Demo shortcuts: the login page has "Fill demo login" buttons, and the staff
  transaction page previews each step and warns when an action will be
  rejected (you can still run it to demonstrate the business rule).
- Keep the local version working as a backup for the Week 12/13 live
  demonstration in case venue Wi-Fi is unreliable. Both run the same code;
  only the connection settings differ.
- Do not commit `baggage_backup.sql` or a real `secrets.toml` to GitHub.
