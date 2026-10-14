"""Dashboard-specific Oracle analytics: safe, bind-parameterized filters and interview metrics.

"Placement year" applies to application_date, interview_date and offer_date
respectively. The student denominator is the cohort that applied in the chosen
year/company; without a year/company filter it is the registered population.
"""
from datetime import datetime
from decimal import Decimal
import logging

from flask import Blueprint, jsonify, request
import database

dashboard_api_bp = Blueprint("dashboard_api", __name__, url_prefix="/analytics")
log = logging.getLogger(__name__)


def _value(v):
    if isinstance(v, Decimal):
        return int(v) if v == v.to_integral_value() else float(v)
    if isinstance(v, datetime):
        return v.isoformat()
    return v


def _rows(cursor):
    cols = [c[0].lower() for c in cursor.description]
    return [{key: _value(value) for key, value in zip(cols, row)}
            for row in cursor.fetchall()]


def _params():
    branch = request.args.get("branch", "").strip()
    company = request.args.get("company", "").strip()
    year = request.args.get("year", "").strip()
    if len(branch) > 20:
        raise ValueError("Invalid branch filter")
    if company and (not company.isdigit() or int(company) <= 0):
        raise ValueError("Invalid company filter")
    if year and (not year.isdigit() or not 2000 <= int(year) <= 2100):
        raise ValueError("Invalid placement year")
    return {
        "branch": branch or None,
        "company": int(company) if company else None,
        "year": int(year) if year else None,
    }


def _conditions(filters, alias="a", student="s", date_col="application_date",
                company_col="company_id"):
    clauses, binds = [], {}
    if filters["branch"]:
        clauses.append(f"{student}.branch = :branch")
        binds["branch"] = filters["branch"]
    if filters["company"]:
        clauses.append(f"{alias}.{company_col} = :company_id")
        binds["company_id"] = filters["company"]
    if filters["year"]:
        clauses.append(f"{alias}.{date_col} >= :start_date AND {alias}.{date_col} < :end_date")
        binds["start_date"] = datetime(filters["year"], 1, 1)
        binds["end_date"] = datetime(filters["year"] + 1, 1, 1)
    return (" AND ".join(clauses) if clauses else "1=1"), binds


def _query(conn, sql, binds=None):
    with conn.cursor() as cursor:
        cursor.execute(sql, binds or {})
        return _rows(cursor)


def _cohort_conditions(filters):
    clauses, binds = [], {}
    if filters["branch"]:
        clauses.append("s.branch = :branch")
        binds["branch"] = filters["branch"]
    if filters["company"] or filters["year"]:
        where, ab = _conditions({**filters, "branch": None}, alias="a")
        clauses.append(f"EXISTS (SELECT 1 FROM APPLICATION a WHERE a.student_id = s.student_id AND {where})")
        binds.update(ab)
    return " AND ".join(clauses) or "1=1", binds


def _interview_data(conn, filters):
    # Company belongs to APPLICATION, not INTERVIEW.
    where, binds = _conditions({**filters, "company": None}, alias="i", date_col="interview_date")
    if filters["company"]:
        where += " AND a.company_id = :company_id"
        binds["company_id"] = filters["company"]

    statuses = _query(conn, f"""
        SELECT i.status, COUNT(*) AS count
        FROM INTERVIEW i
        JOIN APPLICATION a ON a.application_id = i.application_id
        JOIN STUDENT s ON s.student_id = a.student_id
        WHERE {where}
        GROUP BY i.status
        ORDER BY i.status
    """, binds)
    rounds = _query(conn, f"""
        SELECT i.round_number, i.round_name,
               COUNT(*) AS total,
               SUM(CASE WHEN i.status = 'Passed' THEN 1 ELSE 0 END) AS passed,
               SUM(CASE WHEN i.status = 'Failed' THEN 1 ELSE 0 END) AS failed
        FROM INTERVIEW i
        JOIN APPLICATION a ON a.application_id = i.application_id
        JOIN STUDENT s ON s.student_id = a.student_id
        WHERE {where}
        GROUP BY i.round_number, i.round_name
        ORDER BY i.round_number, i.round_name
    """, binds)
    counts = {s["status"]: int(s["count"]) for s in statuses}
    passed, failed = counts.get("Passed", 0), counts.get("Failed", 0)
    completed = passed + failed
    return {
        "total": sum(counts.values()),
        "passed": passed, "failed": failed,
        "pending": counts.get("Pending", 0),
        "scheduled": counts.get("Scheduled", 0),
        "success_rate": round(passed * 100 / completed, 2) if completed else 0,
        "status_distribution": statuses,
        "rounds": [{**r, "pass_rate": round(r["passed"] * 100 / (r["passed"] + r["failed"]), 2)
                    if r["passed"] + r["failed"] else 0} for r in rounds],
    }


@dashboard_api_bp.get("/filters")
def filters():
    try:
        conn = database.get_db_connection()
        try:
            branches = _query(conn, "SELECT DISTINCT branch FROM STUDENT ORDER BY branch")
            companies = _query(conn, "SELECT company_id, company_name FROM COMPANY ORDER BY company_name")
            years = _query(conn, """
                SELECT DISTINCT yr FROM (
                    SELECT EXTRACT(YEAR FROM application_date) AS yr FROM APPLICATION
                    UNION SELECT EXTRACT(YEAR FROM offer_date) AS yr FROM PLACEMENT
                    UNION SELECT EXTRACT(YEAR FROM interview_date) AS yr FROM INTERVIEW
                ) WHERE yr IS NOT NULL ORDER BY yr DESC
            """)
        finally:
            conn.close()
        return jsonify({"success": True, "data": {
            "branches": [b["branch"] for b in branches],
            "companies": companies, "years": [int(y["yr"]) for y in years]
        }})
    except Exception:
        log.exception("Unable to load dashboard filters")
        return jsonify({"success": False, "error": "Filter options are unavailable."}), 503


@dashboard_api_bp.get("/interviews")
def interview_analytics():
    try:
        f = _params()
    except ValueError as exc:
        return jsonify({"success": False, "error": str(exc)}), 400
    try:
        conn = database.get_db_connection()
        try:
            data = _interview_data(conn, f)
        finally:
            conn.close()
        return jsonify({"success": True, "data": data})
    except Exception:
        log.exception("Interview analytics unavailable")
        return jsonify({"success": False, "error": "Interview analytics are unavailable."}), 503


@dashboard_api_bp.get("/dashboard-scoped")
def scoped_analytics():
    try:
        f = _params()
    except ValueError as exc:
        return jsonify({"success": False, "error": str(exc)}), 400

    try:
        conn = database.get_db_connection()
        try:
            cohort, cohort_binds = _cohort_conditions(f)
            students = _query(conn, f"SELECT COUNT(*) AS total FROM STUDENT s WHERE {cohort}", cohort_binds)[0]["total"]

            app_where, app_binds = _conditions(f)
            app_rows = _query(conn, f"""
                SELECT a.status, COUNT(*) AS count
                FROM APPLICATION a JOIN STUDENT s ON s.student_id = a.student_id
                WHERE {app_where} GROUP BY a.status ORDER BY count DESC, a.status
            """, app_binds)

            place_where, place_binds = _conditions(f, alias="p", date_col="offer_date")
            accepted_where = f"{place_where} AND p.acceptance_status = 'Accepted' AND {cohort}"
            place_binds.update(cohort_binds)
            placement = _query(conn, f"""
                SELECT COUNT(DISTINCT p.student_id) AS placed,
                       COUNT(*) AS accepted_offers,
                       NVL(MAX(p.package_offered), 0) AS highest,
                       NVL(ROUND(AVG(p.package_offered), 2), 0) AS average,
                       NVL(MIN(p.package_offered), 0) AS lowest
                FROM PLACEMENT p JOIN STUDENT s ON s.student_id = p.student_id
                WHERE {accepted_where}
            """, place_binds)[0]

            # Preserve the same branch-cohort denominator across all visualizations.
            join_clauses = ["p.student_id = s.student_id", "p.acceptance_status = 'Accepted'"]
            join_binds = dict(cohort_binds)
            if f["company"]:
                join_clauses.append("p.company_id = :place_company_id")
                join_binds["place_company_id"] = f["company"]
            if f["year"]:
                join_clauses.append("p.offer_date >= :place_start AND p.offer_date < :place_end")
                join_binds["place_start"] = datetime(f["year"], 1, 1)
                join_binds["place_end"] = datetime(f["year"] + 1, 1, 1)
            branches = _query(conn, f"""
                SELECT s.branch, COUNT(DISTINCT s.student_id) AS total_students,
                       COUNT(DISTINCT p.student_id) AS placed_students
                FROM STUDENT s
                LEFT JOIN PLACEMENT p ON {" AND ".join(join_clauses)}
                WHERE {cohort}
                GROUP BY s.branch ORDER BY s.branch
            """, join_binds)
            for row in branches:
                row["placement_percentage"] = round(row["placed_students"] * 100 / row["total_students"], 2) if row["total_students"] else 0

            recruiters = _query(conn, f"""
                SELECT c.company_id, c.company_name,
                       COUNT(*) AS offers_made,
                       SUM(CASE WHEN p.acceptance_status = 'Accepted' THEN 1 ELSE 0 END) AS students_placed,
                       NVL(ROUND(AVG(CASE WHEN p.acceptance_status = 'Accepted' THEN p.package_offered END), 2), 0) AS average_package,
                       NVL(MAX(CASE WHEN p.acceptance_status = 'Accepted' THEN p.package_offered END), 0) AS highest_package
                FROM PLACEMENT p
                JOIN STUDENT s ON s.student_id = p.student_id
                JOIN COMPANY c ON c.company_id = p.company_id
                WHERE {place_where} AND {cohort}
                GROUP BY c.company_id, c.company_name
                ORDER BY students_placed DESC, c.company_name
            """, place_binds)
            app_companies = _query(conn, f"""
                SELECT a.company_id, COUNT(*) AS applications
                FROM APPLICATION a JOIN STUDENT s ON s.student_id = a.student_id
                WHERE {app_where}
                GROUP BY a.company_id
            """, app_binds)
            app_map = {r["company_id"]: r["applications"] for r in app_companies}
            for company in recruiters:
                company["applications"] = app_map.get(company["company_id"], 0)

            recent = _query(conn, f"""
                SELECT a.application_id, s.student_name, s.branch,
                       c.company_name, a.status, a.application_date
                FROM APPLICATION a
                JOIN STUDENT s ON s.student_id = a.student_id
                JOIN COMPANY c ON c.company_id = a.company_id
                WHERE {app_where}
                ORDER BY a.application_date DESC, a.application_id DESC
                FETCH FIRST 8 ROWS ONLY
            """, app_binds)

            interview = _interview_data(conn, f)
        finally:
            conn.close()

        counts = {r["status"]: r["count"] for r in app_rows}
        apps = sum(counts.values())
        selected, rejected = counts.get("Selected", 0), counts.get("Rejected", 0)
        pending = apps - selected - rejected
        placed = placement["placed"]
        return jsonify({"success": True, "data": {
            "summary": {
                "students": students, "placed": placed,
                "placement_rate": round(placed * 100 / students, 2) if students else 0,
                "applications": apps, "selected": selected,
                "rejected": rejected, "pending": pending,
                "companies": len(app_map),
                "highest_package": placement["highest"],
                "average_package": placement["average"],
                "lowest_package": placement["lowest"],
            },
            "statuses": app_rows,
            "branches": branches,
            "companies": recruiters,
            "recent": recent,
            "interviews": interview,
            "filters": f,
            "year_note": "Year filters applications by submission, interviews by interview date and placements by offer date."
        }})
    except Exception:
        log.exception("Scoped placement analytics unavailable")
        return jsonify({"success": False, "error": "Filtered analytics are unavailable."}), 503
