# Campus Placement Analytics

Flask + Oracle SQL web application for tracking students, placement drives, applications, interviews and accepted offers, with a responsive Chart.js analytics dashboard.

**Status:** The dashboards and Flask API contracts are covered by automated tests. A connection to a real Oracle instance is required to verify database queries, CRUD operations and production data. An **explicitly marked synthetic sample preview** is available when Oracle is offline; sample figures are *not* institutional placement statistics.

## Features

| Area | What it provides |
| --- | --- |
| Student management | Student profiles, qualifications and academic history |
| Company drives | Recruiting companies, roles and eligibility requirements |
| Eligibility | Compare students with company-specific eligibility criteria |
| Applications | Application lifecycle: Applied, Shortlisted, In Review, Selected, Rejected |
| Interviews | Scheduled and completed rounds, outcomes, scores and feedback |
| Placement analytics | Registered vs uniquely placed students, placement percentage, application funnel |
| Company and salary analytics | Offers and accepted placements by company, branch performance, accepted salary packages (LPA) |
| Dashboard | Responsive cards and five Chart.js charts, filters, retry/refresh, CSV export, mobile navigation and honest empty/error states |

### Analytics dashboard

Open **`/analytics`** or **`/analytics/dashboard`**. The interface includes:

- Four headline KPIs, a placement-rate gauge, an application-status doughnut, branch placement bars, a recruiter comparison, salary/package comparison and interview outcomes.
- Dropdowns for **branch, company and placement year**. Filter values come from the Oracle database when available.
- Refresh, clear filters, sample preview, return-to-live, retry and CSV download. The CSV filename explicitly says **SAMPLE** when exported from sample mode.
- Automatic timeout/error handling when Oracle is unavailable. The dashboard remains usable for interaction testing with clearly labeled, *synthetic* figures.

A live-data view never silently merges synthetic figures with real figures. Filters in sample mode use invented data and should not be used for research conclusions.

## Technologies

Python 3, Flask 3, Oracle Database (via `python-oracledb` Thin mode), Oracle SQL, Jinja2, HTML/CSS/JavaScript and Chart.js 4 (CDN). The frontend has no Node build step.

## Repository layout

```text
app.py                        Flask application and blueprint registration
database.py                   Oracle connection configuration via .env
database/
  01_schema.sql               Tables, constraints and relationships
  02_seed_data.sql            Sample Oracle student/company data
  03_queries.sql              General verification queries
  04_analytics_queries.sql    Overall and application analytics SQL
  05_company_analytics.sql    Company/branch/package aggregation SQL
  run_all.sql                 SQL*Plus/SQL Developer setup runner
routes/
  student_routes.py           Student management
  company_routes.py           Company management
  eligibility_routes.py       Eligibility checker
  application_routes.py       Applications
  interview_routes.py         Interview record management
  analytics_routes.py         Person 1 overview/application/placement APIs
  company_analytics_routes.py Person 2 company/branch/package APIs
  dashboard_api_routes.py     Person 3 filter/interview/scoped APIs
services/
  analytics_service.py        Company/branch/package Oracle aggregations
  eligibility_service.py      Eligibility logic
templates/
  analytics/dashboard.html    Dashboard layout
static/
  css/dashboard.css           Dashboard styles and responsive design
  js/dashboard.js             Chart.js, filters, export, loading/error states
docs/DASHBOARD.md             Detailed endpoint and filtering notes
tests/
  test_dashboard_api.py       Dashboard API/mock DB tests
  test_contributor_contract.py Person 2 JSON and aggregation contract tests
  browser_smoke.py            Offline/preview control test (Selenium)
  fixture_server.py           Test-only Flask server with mocked SQL results
  browser_contract.py         Cross-contributor end-to-end UI test
  browser_all_controls.py     Every dashboard button/filter browser check
requirements-hp360.txt        Extra Linux preview/test dependencies
scripts/host_hp360.sh         Private-only Gunicorn preview runner
```

## Quick start

### 1. Prerequisites

- Python 3.10+ and an Oracle 19c/21c/23c database (XE works).
- Access to an Oracle account that can create tables and run the setup SQL.
- Browser access to jsDelivr for Chart.js and Google Fonts. If these networks are unavailable, metrics/tables can still load but charts need Chart.js hosted locally.

### 2. Install dependencies

**Windows (PowerShell):**

```powershell
git clone https://github.com/saumyashekar30/campus-placement-analytics.git
cd campus-placement-analytics
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

**Linux / HP360:**

```bash
git clone https://github.com/saumyashekar30/campus-placement-analytics.git
cd campus-placement-analytics
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
```

### 3. Configure Oracle

Edit `.env`, keeping real credentials out of Git:

```dotenv
ORACLE_DB_USER=your_oracle_username
ORACLE_DB_PASSWORD=your_oracle_password
ORACLE_DB_DSN=localhost:1521/XEPDB1
```

Initialize the database in Oracle SQL*Plus or SQL Developer as the chosen schema owner:

```sql
@database/run_all.sql
```

**Caution:** `01_schema.sql` drops and recreates the project tables. Run this on an isolated development schema, never on a database containing data you need to retain.

### 4. Run locally

```bash
python app.py
```

Open `http://127.0.0.1:5000/analytics` for the dashboard. Other modules: `/`, `/students`, `/companies`, `/eligibility`, `/applications`.

The default Flask launch is **development only** (debug mode). Never expose it publicly. For an HP360/Tailscale **private test preview**, use a WSGI server such as Gunicorn, disable debug mode, supply a random `SECRET_KEY`, and bind only to a private Tailscale IP or localhost. **This application does not yet have user login/authorization**, so do not host student data on an unrestricted network. The preview can operate without Oracle using its clearly labeled sample mode.

## Analytics JSON API

All paths below are GET requests. See [dashboard integration notes](docs/DASHBOARD.md) for response schemas and year/cohort semantics.

| Owner | Endpoint | Result |
| --- | --- | --- |
| Person 1 | `/analytics/overview` | Registered students, distinct placements, application counts, salary KPI |
| Person 1 | `/analytics/applications` | Status breakdown, recruiting company applications, recent submissions |
| Person 1 | `/analytics/placement-summary` | Placement rate, branch summary, company hiring funnel |
| Person 2 | `/analytics/companies` | Company offers and placements, top recruiters |
| Person 2 | `/analytics/branches` | Branch-wide placement percentages |
| Person 2 | `/analytics/packages` | Highest, average and lowest accepted offers overall and by group |
| Person 3 | `/analytics/interviews` | Interview status and round results; completed-round pass rate |
| Person 3 | `/analytics/filters` | Available branches, companies and recorded years |
| Person 3 | `/analytics/dashboard-scoped` | Filtered dashboard summaries, charts and recent applications |

The final three Person 3 endpoints support query parameters where applicable:

```text
/analytics/dashboard-scoped?branch=CSE&company=2&year=2026
/analytics/interviews?branch=CSE&company=2&year=2026
```

Company is an Oracle `company_id`, not a name. The filtered routes use Oracle bind parameters rather than interpolating user-supplied values into SQL.

**Metric definitions:** A placed student is counted once if they have an *Accepted* placement. Packages use accepted offers. Interview success rate is `Passed / (Passed + Failed)` (Scheduled and Pending are excluded). Placement year means application submission year for application metrics, interview date year for interviews, and offer date year for accepted placements; see the detailed notes for cohort denominators.

## Automated testing

**Unit/API tests** (Oracle mocked; no live DB required):

```bash
python -m unittest discover -s tests -p "test_*.py" -v
```

**Headless browser tests** (additional test-only dependency: `pip install selenium`, installed Chromium/Chrome and compatible ChromeDriver):

Start the real app with Oracle unavailable on `http://127.0.0.1:5059`, then:

```bash
python tests/browser_smoke.py
```

To test the actual contributed Flask route implementations with *mocked aggregations* and no Oracle DB, start a separate process:

```bash
python tests/fixture_server.py
# In a second terminal:
python tests/browser_contract.py
```

Run `python tests/browser_all_controls.py` while **both** the offline app (5059) and test-only fixture server (5077) are running. It exercises all 8 dashboard buttons, three filters, mobile menu, navigation anchors, live/sample exports, retry and both offline/fixture pathways.

`fixture_server.py` binds to localhost port 5077. It is a **test-only fake data service**, not a production or real-data deployment. A cross-contributor browser pass establishes JSON/UI compatibility, **not** the correctness of SQL executed against a real Oracle database.

Before merging a PR, also check the full workflow against the seeded Oracle schema: student/company CRUD, eligibility, application/interview editing, placed-student uniqueness, accepted package calculations, filtered dashboard queries, error states and network accessibility.

## Private HP360 preview hosting

To start the combined app privately on HP360 (Linux):

```bash
python -m pip install -r requirements-hp360.txt
PLACEMENT_BIND_IP="$(tailscale ip -4)" PLACEMENT_PORT=5088 bash scripts/host_hp360.sh
```

Visit `http://<HP360-TAILSCALE-IP>:5088/analytics` from another **authorized device on the same tailnet**. The runner binds to loopback and that specific tailnet address, refuses public binds, uses Gunicorn with Flask debug disabled, and generates an ephemeral `SECRET_KEY` if not set. No changes to Tailscale Serve/Funnel are made. Use `PLACEMENT_BIND_IP=127.0.0.1` for local-only preview.

**Security note:** The project does not yet implement user authentication. A Tailscale connection limits network access but is not application-level authorization. The private preview URL uses HTTP; browsers may warn about downloaded CSV blobs because HTTP is not a secure web origin. Use localhost or configure trusted private HTTPS before deploying real student data. Do not expose live student data to a broad tailnet or the public internet without adding user authentication, access controls and data handling safeguards. Without Oracle, the browser clearly labels all preview metrics as *synthetic*.

## Contributors and Git workflow

- **Person 1 — Overall & application analytics:** Oracle queries and `routes/analytics_routes.py`.
- **Person 2 — Company, branch & package analytics:** Oracle queries, `services/analytics_service.py` and `routes/company_analytics_routes.py`.
- **Person 3 — Interview analytics and dashboard:** `routes/dashboard_api_routes.py`, template, CSS, JavaScript and integration tests.

The first two branches have already been merged into `main`; dashboard work is proposed through a dedicated pull request. Do not merge or push directly to `main` without review.

## Security and deployment limitations

- No authentication, permissions or student-level data isolation currently exists. Keep real student/placement records on a trusted, restricted network.
- Never commit `.env`, credentials, raw student exports or browser screenshots containing personal information.
- Set a strong non-default `SECRET_KEY`; do not expose `app.py` debug mode to a network.
- Tailscale/private-network previews are for testing, **not** evidence of production security.
- Live Oracle integration and database migrations must be validated by the team before production use.

_Refer to [docs/DASHBOARD.md](docs/DASHBOARD.md) for frontend and API integration details._
