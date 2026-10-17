# Campus Placement Analytics System

**DBMS Mini-Project / College Submission**

A database-centered web application that helps a college placement cell manage students, recruiting companies, applications, interview rounds and final placements. It demonstrates **relational database design, SQL joins/aggregations, constraints, and a Flask–Oracle integration**, with charts built using Chart.js.

**Project status:** The application and dashboard work in tested offline sample/fixture modes. **An Oracle database is required for actual insert/update/delete operations and live dashboard data.** The included seed records are *fictitious academic examples*. Do not present the browser's larger "Sample Preview" figures as Oracle query results.

## 1. Project objectives

1. Model placement data using properly related Oracle SQL tables.
2. Store and edit student, company, application and interview records.
3. Apply company-specific academic/skill eligibility criteria.
4. Enforce primary-key, foreign-key, uniqueness and domain constraints.
5. Calculate placement rates, company performance, interview outcomes and salary packages using SQL.
6. Visualize the results through a Flask dashboard.

## 2. Technology stack

| Component | Technology |
| --- | --- |
| Database | Oracle Database XE / 19c+; Oracle SQL |
| Backend | Python, Flask, python-oracledb |
| Frontend | HTML, CSS, JavaScript, Jinja2 |
| Charts | Chart.js |
| IDE | VS Code, PyCharm or any Python editor |
| Database client | Oracle SQL Developer or SQL*Plus |

No React, frontend build process or paid cloud service is required.

## 3. Run for college evaluation

### Step 1: Download and install

Install Python 3.10+ and Oracle Database (XE is sufficient), then clone the repository.

```bash
git clone https://github.com/saumyashekar30/campus-placement-analytics.git
cd campus-placement-analytics
python -m venv .venv
```

Activate the virtual environment:

- Windows PowerShell: `.venv\Scripts\Activate.ps1`
- Linux/macOS: `source .venv/bin/activate`

Then install:

```bash
pip install -r requirements.txt
```

### Step 2: Configure Oracle

Copy `.env.example` to `.env`, then set credentials for **your own academic Oracle schema**:

```dotenv
ORACLE_DB_USER=your_username
ORACLE_DB_PASSWORD=your_password
ORACLE_DB_DSN=localhost:1521/XEPDB1
```

> Never put your actual password into Git.

### Step 3: Initialize the sample database

In Oracle SQL Developer (Run Script / F5) or SQL*Plus, run:

```sql
@database/run_all.sql
```

The script creates **11 related tables**, inserts illustrative data, aligns auto-generated identity IDs after seeding, and runs the provided demonstration SQL queries.

**Important:** `01_schema.sql` *drops and recreates* these project tables. Run setup only in a disposable student project schema; **do not rerun it after adding work you want to keep**.

### Step 4: Start Flask

```bash
python app.py
```

Open **http://127.0.0.1:5000/analytics** in a browser.

Other screens: `/` (overview), `/students`, `/companies`, `/applications`, `/eligibility`, and related interview screens.

If Oracle is not connected, the analytics screen switches to an **explicitly labeled synthetic preview** so you can show the UI. For a **DBMS demonstration, connect Oracle** and show actual database queries and changes.

## 4. Seeded database: expected results

The included `02_seed_data.sql` is set in the **2024 placement cycle**. With a freshly initialized schema and no changes:

| Metric | Expected |
| --- | ---: |
| Registered students | 10 |
| Recruiting companies | 5 |
| Applications submitted | 16 |
| Distinct students with accepted placements | 6 |
| Overall placement rate | 60% |
| Selected applications | 6 |
| Rejected applications | 1 |
| Other active application statuses | 9 |
| Recorded interview rounds | 16 |
| Passed / failed interview rounds | 15 / 1 |
| Highest accepted package | ₹24.00 LPA |
| Lowest accepted package | ₹5.50 LPA |
| Average accepted package | Approximately ₹12.92 LPA |

These are *expected from the checked-in SQL seed file*, not measurements against a live Oracle instance. When connected, the placement-year filter should include **2024**.

The much larger **Sample Preview** dashboard (840 students, etc.) uses a separate fictional browser-only dataset. Always distinguish it from database results during evaluation.

## 5. Main modules

| Module | Explanation |
| --- | --- |
| Students | Create, list, edit and delete student profiles and related attributes |
| Companies | Add and maintain recruiters, job drives, eligibility requirements and required skills |
| Eligibility | Evaluate students against company CGPA, marks, branch, backlog and skill criteria |
| Applications | Track which students applied to which companies and their application status |
| Interviews | Add/edit interview rounds and record pass/fail, scores and feedback |
| Analytics | Unique placed students, offer counts, statuses, branch rates, packages and interviews |

### Team contribution division

- **Person 1 — Overall and Application Analytics:** Oracle SQL, summary cards and application-status Flask endpoints.
- **Person 2 — Company, Branch and Package Analytics:** Aggregation queries and Flask JSON APIs for hiring, branches and packages.
- **Person 3 — Interviews and Dashboard:** Interview outcomes, Chart.js frontend, filters and API integration.

All three modules are integrated on the dashboard feature branch and proposed for review in a pull request to `main`.

## 6. Database design and concepts demonstrated

The schema has **11 tables**: `STUDENT`, `STUDENT_SKILL`, `CERTIFICATION`, `PROJECT`, `INTERNSHIP`, `COMPANY`, `COMPANY_BRANCH`, `COMPANY_SKILL`, `APPLICATION`, `INTERVIEW` and `PLACEMENT`.

The college-level DBMS concepts to highlight are:

- **Normalization:** Separate tables for student skills and eligible company branches instead of comma-separated fields.
- **Primary keys & foreign keys:** Link students and companies through applications, interviews and placements.
- **Constraints:** CGPA range, marks range, allowed statuses, unique email, and no duplicate application to one company by the same student.
- **JOINS:** Student, company, application, interview and placement comparisons.
- **Aggregations:** `COUNT`, `COUNT(DISTINCT)`, `AVG`, `MIN`, `MAX`, `GROUP BY` and conditional counts.
- **SQL analytics:** Placement rates, hiring funnels, salaries, company- and branch-wise results.
- **Parameterized SQL:** Binds for the branch/company/year dashboard filters.

**Definitions:** A uniquely placed student has an **Accepted** placement; salary analytics use accepted offers. Interview success rate is **Passed ÷ (Passed + Failed)**, excluding Scheduled/Pending records. Filtered year data uses application dates, interview dates or offer dates depending on the chart.

## 7. Dashboard and APIs

The dashboard at `/analytics` has KPI cards, a placement gauge and five Chart.js charts:

- Application status
- Branch placement percentage
- Recruiter comparison
- Company salary/package comparison
- Interview-round outcomes

**API endpoints**

| Owner | Flask endpoint | Purpose |
| --- | --- | --- |
| Person 1 | `/analytics/overview` | KPIs |
| Person 1 | `/analytics/applications` | Status distribution and recent applications |
| Person 1 | `/analytics/placement-summary` | Overall placement and branch/company summaries |
| Person 2 | `/analytics/companies` | Recruiting company counts |
| Person 2 | `/analytics/branches` | Department placement data |
| Person 2 | `/analytics/packages` | Salary benchmarks |
| Person 3 | `/analytics/interviews` | Interview outcomes |
| Person 3 | `/analytics/filters` | Database-backed filter choices |
| Person 3 | `/analytics/dashboard-scoped` | Filtered dashboard data |

For example, `/analytics/dashboard-scoped?branch=CSE&company=2&year=2024` filters relevant analytics by Oracle company ID and academic year.

See [Dashboard API and metric details](docs/DASHBOARD.md).

## 8. Demonstration and viva

Follow the **[College Demo and Viva Checklist](docs/COLLEGE_DEMO.md)**. It includes a suggested five-minute walkthrough, 2024 SQL checks, expected results, what each teammate should explain, and common viva questions about keys, joins and normalization.

For a complete DBMS demonstration, prepare to show one insert/update in Oracle and the corresponding refreshed Flask result. The browser-only preview is intended only for showing the UI layout when the database is offline.

## 9. Tests

The team has automated tests for backend calculation contracts and dashboard controls:

```bash
python -m unittest discover -s tests -p "test_*.py" -v
```

For optional Selenium Chrome-based interaction checks, install `selenium` and Chrome/Chromium with a matching ChromeDriver. The offline, contract and every-button scripts are under `tests/`. These use mocked API responses for integration tests and **cannot replace an actual Oracle test**.

The `requirements-hp360.txt` and `scripts/host_hp360.sh` files are optional helpers for a private team preview; **hosting on HP360 is not necessary for college submission**.

## 10. Project files

```text
database/               Oracle schema, sample data and analysis scripts
database/run_all.sql     One-time academic database setup
database/06_sync_identity.sql  Align IDs so CRUD adds work after seeding
routes/                 Flask routes for students, companies, interviews and analytics
services/               SQL aggregation and eligibility services
templates/              HTML and Jinja pages
static/                 CSS, JavaScript and Chart.js integration
tests/                  Calculation tests and optional Selenium scripts
docs/COLLEGE_DEMO.md    Evaluation walkthrough and viva notes
docs/DASHBOARD.md       Detailed dashboard integration
DBMS_PROJECT_REVIEW_NOTEBOOK.md  Longer DBMS theory/review notes
```

**Scope:** This is a course project built for learning and demonstrating DBMS concepts, not an authenticated university placement portal or a production application.
