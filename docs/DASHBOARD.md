# Placement Intelligence Dashboard

Built as the frontend/interview-analytics portion of the Campus Placement Analytics project. Uses existing Flask/Jinja structure, Oracle SQL and Chart.js; no Node.js build step.

## Start

1. Configure `.env` based on `.env.example`. Connect to an Oracle database with schema and data from `database/`.
2. Install dependencies: `pip install -r requirements.txt`.
3. Start: `python app.py` and open `http://127.0.0.1:5000/analytics` or `/analytics/dashboard`.

The page loads even without Oracle; automatically switches to a clearly labeled **synthetic sample-data preview** when Oracle cannot respond; a permanent Sample Preview control is also available. The preview is synthetic and must never be used as real results.

## API integration

The unfiltered dashboard calls the existing contributor endpoints (no edits to their analytics SQL):

| Source | Endpoint | Content |
|---|---|---|
| Person 1 | `GET /analytics/overview` | Registered students, unique placements, applications, package KPI |
| Person 1 | `GET /analytics/applications` | Application status donut + recent applications |
| Person 1 | `GET /analytics/placement-summary` | Branch summaries/fallback |
| Person 2 | `GET /analytics/companies` | Offers, companies, hires |
| Person 2 | `GET /analytics/branches` | Placement percentages by branch |
| Person 2 | `GET /analytics/packages` | Package comparisons |
| Person 3 | `GET /analytics/interviews` | Interview outcomes and pass rates |
| Person 3 | `GET /analytics/filters` | Available branches, companies and placement years |
| Person 3 | `GET /analytics/dashboard-scoped?branch=CSE&company=2&year=2026` | Consistently filtered KPI, charts, interviews, and activity |

Both new analytics routes return `{"success": true, "data": ...}` on success. A query parameter can be omitted to disable that filter. Invalid query parameters return HTTP 400; an unavailable database returns HTTP 503 without exposing credentials.

**Year interpretation:** Application counts use `APPLICATION.application_date`, interviews use `INTERVIEW.interview_date`, and accepted placements use `PLACEMENT.offer_date`. For a company/year selection, the student denominator is the cohort of students with an application matching those selections; for the unfiltered dashboard, it is every registered student. A student is only counted once in placement metrics, regardless of application or offer count. Salary statistics use **accepted** placement records. The interview pass rate is `Passed / (Passed + Failed)`: scheduled and pending rounds are not completed outcomes.

The API uses bound Oracle parameters (not interpolated user data), and all query results are shown as text in JavaScript, not as unescaped HTML.

## Dashboard features

- Four KPI cards, placement rate gauge, application distribution doughnut, branch rate bars, recruiter offer/hire comparison, package benchmark chart, interview outcomes chart, and recent application roster.
- Three database-backed filters (branch, recruiter, year), refresh, reset, CSV export, mobile navigation, partial failures, explicit empty state, and sample-data preview.
- Frontend in `templates/analytics/dashboard.html`, `static/css/dashboard.css` and `static/js/dashboard.js`.
- The existing application analytics routes remain unchanged except that dashboard HTML is now rendered immediately, without waiting for three synchronous Oracle queries.

## Verification

Run `python -m unittest discover -s tests -p "test_dashboard_api.py" -v` to run mocked integration and input validation tests (does not require an Oracle instance).

A real Oracle instance is needed to verify data-dependent queries against the seeded database. Chart.js loads from jsDelivr and fonts from Google Fonts, so visual charts/fonts require network access unless those assets are hosted locally.


## Browser integration verification

- `python -m unittest discover -s tests -p "test_*.py"` tests Person 2 company, branch, and package transformations alongside the dashboard API.
- Run Flask on port 5059 and execute `python tests/browser_smoke.py` for offline-preview, filters, charts, reset, retry, export, and mobile-navigation tests.
- Run `python tests/fixture_server.py` on port 5077 and execute `python tests/browser_contract.py` to verify the existing Person 1 and Person 2 Flask routes feed all five charts. These are **mocked service contracts**, not live Oracle SQL benchmark results.
- Browser tests need Selenium and a headless Chrome/Chromium + ChromeDriver. No test fixtures are installed in production.
