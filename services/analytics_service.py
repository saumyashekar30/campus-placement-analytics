"""
Campus Placement Analytics System - Analytics Service
Company, Branch & Package Analytics

Runs the Oracle aggregation queries (mirrors database/05_company_analytics.sql)
and shapes the results into chart-ready JSON structures.
An "offer" is any PLACEMENT row; a "placement" is an Accepted PLACEMENT row.
"""

from decimal import Decimal
import database

TOP_COMPANY_LIMIT = 5

COMPANY_SQL = """
    SELECT c.company_id, c.company_name, c.job_role,
           COUNT(p.placement_id) AS offers_made,
           COUNT(CASE WHEN p.acceptance_status = 'Accepted' THEN 1 END) AS students_placed,
           COUNT(CASE WHEN p.acceptance_status = 'Declined' THEN 1 END) AS offers_declined,
           COUNT(CASE WHEN p.acceptance_status = 'Pending'  THEN 1 END) AS offers_pending
    FROM COMPANY c
    LEFT JOIN PLACEMENT p ON p.company_id = c.company_id
    GROUP BY c.company_id, c.company_name, c.job_role
    ORDER BY students_placed DESC, offers_made DESC, c.company_name
"""

BRANCH_SQL = """
    SELECT s.branch,
           COUNT(DISTINCT s.student_id) AS total_students,
           COUNT(DISTINCT p.student_id) AS placed_students,
           COUNT(DISTINCT s.student_id) - COUNT(DISTINCT p.student_id) AS unplaced_students,
           ROUND(COUNT(DISTINCT p.student_id) * 100.0
                 / NULLIF(COUNT(DISTINCT s.student_id), 0), 2) AS placement_percentage
    FROM STUDENT s
    LEFT JOIN PLACEMENT p ON p.student_id = s.student_id
                         AND p.acceptance_status = 'Accepted'
    GROUP BY s.branch
    ORDER BY placement_percentage DESC, s.branch
"""

PACKAGE_OVERALL_SQL = """
    SELECT COUNT(*) AS placements,
           MAX(package_offered) AS highest_package,
           ROUND(AVG(package_offered), 2) AS average_package,
           MIN(package_offered) AS lowest_package
    FROM PLACEMENT
    WHERE acceptance_status = 'Accepted'
"""

PACKAGE_BY_COMPANY_SQL = """
    SELECT c.company_name,
           COUNT(p.placement_id) AS placements,
           MAX(p.package_offered) AS highest_package,
           ROUND(AVG(p.package_offered), 2) AS average_package,
           MIN(p.package_offered) AS lowest_package
    FROM COMPANY c
    JOIN PLACEMENT p ON p.company_id = c.company_id
                    AND p.acceptance_status = 'Accepted'
    GROUP BY c.company_name
    ORDER BY average_package DESC, c.company_name
"""

PACKAGE_BY_BRANCH_SQL = """
    SELECT s.branch,
           COUNT(*) AS placements,
           MAX(p.package_offered) AS highest_package,
           ROUND(AVG(p.package_offered), 2) AS average_package,
           MIN(p.package_offered) AS lowest_package
    FROM PLACEMENT p
    JOIN STUDENT s ON s.student_id = p.student_id
    WHERE p.acceptance_status = 'Accepted'
    GROUP BY s.branch
    ORDER BY average_package DESC
"""


def _convert(v):
    """Oracle Decimal -> int/float for JSON serialization."""
    if isinstance(v, Decimal):
        return int(v) if v % 1 == 0 else float(v)
    return v


def _query(sql):
    """Run a SELECT and return a list of lowercase-keyed dicts."""
    conn = database.get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql)
            cols = [c[0].lower() for c in cursor.description]
            return [{k: _convert(v) for k, v in zip(cols, row)} for row in cursor.fetchall()]
    finally:
        conn.close()


def _num(v):
    return v if v is not None else 0


def get_company_analytics():
    """Company-wise offer/placement counts and the top recruiting companies."""
    companies = _query(COMPANY_SQL)
    recruiting = [c for c in companies if c["students_placed"] > 0]
    top = recruiting[:TOP_COMPANY_LIMIT]
    # Include everyone tied with the last top entry
    if top:
        cutoff = top[-1]["students_placed"]
        top = [c for c in recruiting if c["students_placed"] >= cutoff]
    return {
        "summary": {
            "total_companies": len(companies),
            "total_offers": sum(c["offers_made"] for c in companies),
            "total_placements": sum(c["students_placed"] for c in companies),
        },
        "companies": companies,
        "top_recruiters": [
            {"company_name": c["company_name"], "students_placed": c["students_placed"]}
            for c in top
        ],
        "chart": {
            "labels": [c["company_name"] for c in companies],
            "datasets": [
                {"label": "Offers Made", "data": [c["offers_made"] for c in companies]},
                {"label": "Students Placed", "data": [c["students_placed"] for c in companies]},
            ],
        },
    }


def get_branch_analytics():
    """Branch-wise placement counts and percentages."""
    branches = _query(BRANCH_SQL)
    for b in branches:
        b["placement_percentage"] = _num(b["placement_percentage"])
    total = sum(b["total_students"] for b in branches)
    placed = sum(b["placed_students"] for b in branches)
    return {
        "summary": {
            "total_students": total,
            "placed_students": placed,
            "overall_placement_percentage": round(placed * 100.0 / total, 2) if total else 0.0,
        },
        "branches": branches,
        "chart": {
            "labels": [b["branch"] for b in branches],
            "datasets": [
                {"label": "Placed Students", "data": [b["placed_students"] for b in branches]},
                {"label": "Unplaced Students", "data": [b["unplaced_students"] for b in branches]},
                {"label": "Placement %", "data": [b["placement_percentage"] for b in branches]},
            ],
        },
    }


def get_package_analytics():
    """Highest/average/lowest packages overall, per company and per branch."""
    overall = _query(PACKAGE_OVERALL_SQL)[0]
    overall = {k: _num(v) for k, v in overall.items()}
    by_company = _query(PACKAGE_BY_COMPANY_SQL)
    by_branch = _query(PACKAGE_BY_BRANCH_SQL)

    avg_all = overall["average_package"]
    for c in by_company:
        c["diff_from_overall_average"] = round(c["average_package"] - avg_all, 2)

    def chart(rows, key):
        return {
            "labels": [r[key] for r in rows],
            "datasets": [
                {"label": "Highest Package", "data": [r["highest_package"] for r in rows]},
                {"label": "Average Package", "data": [r["average_package"] for r in rows]},
                {"label": "Lowest Package", "data": [r["lowest_package"] for r in rows]},
            ],
        }

    return {
        "overall": overall,
        "by_company": by_company,
        "by_branch": by_branch,
        "chart": {
            "company_comparison": chart(by_company, "company_name"),
            "branch_comparison": chart(by_branch, "branch"),
        },
    }
