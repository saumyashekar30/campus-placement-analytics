"""
Campus Placement Analytics System - Analytics Blueprint
Phase 7: Comprehensive Placement & Application Analytics Module

Routes:
    GET /analytics/overview           - JSON summary KPI metrics for dashboard cards
    GET /analytics/applications       - JSON application status counts and chart distribution
    GET /analytics/placement-summary  - JSON detailed placement rates, package stats, and branch breakdown
    GET /analytics                    - Visual analytics dashboard (HTML) or overview (JSON)
    GET /analytics/dashboard          - Visual analytics dashboard (HTML)
"""

from datetime import datetime, date
from decimal import Decimal
from flask import Blueprint, jsonify, render_template, request
import database

analytics_bp = Blueprint("analytics", __name__, url_prefix="/analytics")

# Color palette mapped to application lifecycle statuses for consistent charts
STATUS_COLORS = {
    "Selected": "#10b981",    # Emerald green
    "Shortlisted": "#3b82f6", # Blue
    "In Review": "#f59e0b",   # Amber / Orange
    "Applied": "#8b5cf6",     # Purple
    "Rejected": "#ef4444"     # Red
}

STATUS_BADGE_CLASSES = {
    "Selected": "success",
    "Shortlisted": "info",
    "In Review": "warning",
    "Applied": "primary",
    "Rejected": "danger"
}


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def _convert_value(v):
    """
    Converts Oracle-specific datatypes to standard Python primitives
    suitable for JSON serialization and Jinja2 templating.
    - Decimal is converted to int (if integral) or float.
    - Date / DateTime is converted to ISO string.
    """
    if isinstance(v, Decimal):
        if v % 1 == 0:
            return int(v)
        return float(v)
    elif isinstance(v, (datetime, date)):
        return v.isoformat()
    return v


def _row_to_dict(cursor, row):
    """Converts a single Oracle query row into a lowercase dictionary."""
    if not row:
        return None
    columns = [col[0].lower() for col in cursor.description]
    return {k: _convert_value(v) for k, v in zip(columns, row)}


def _rows_to_dicts(cursor, rows):
    """Converts a collection of Oracle query rows into a list of lowercase dictionaries."""
    if not rows:
        return []
    columns = [col[0].lower() for col in cursor.description]
    return [{k: _convert_value(v) for k, v in zip(columns, r)} for r in rows]


# ============================================================================
# CORE DATA EXTRACTION SERVICES (REUSABLE QUERIES)
# ============================================================================

def _fetch_overview_data():
    """
    Executes Oracle SQL queries to aggregate executive overview metrics.
    Ensures zero duplicate counting by using DISTINCT student identifiers.
    """
    conn = database.get_db_connection()
    try:
        with conn.cursor() as cursor:
            # 1. Total Registered Students & Uniquely Placed Students (Accepted offers)
            cursor.execute("""
                SELECT 
                    COUNT(DISTINCT s.student_id) AS total_students,
                    COUNT(DISTINCT p.student_id) AS placed_students
                FROM STUDENT s
                LEFT JOIN PLACEMENT p 
                    ON s.student_id = p.student_id 
                   AND p.acceptance_status = 'Accepted'
            """)
            stud_row = cursor.fetchone()
            total_students = int(stud_row[0]) if stud_row else 0
            placed_students = int(stud_row[1]) if stud_row else 0
            unplaced_students = max(0, total_students - placed_students)
            placement_pct = round((placed_students * 100.0) / total_students, 2) if total_students > 0 else 0.0

            # 2. Total Applications & Categorized Pipeline (Selected, Rejected, Pending)
            cursor.execute("""
                SELECT 
                    COUNT(*) AS total_applications,
                    COUNT(CASE WHEN status = 'Selected' THEN 1 END) AS selected_count,
                    COUNT(CASE WHEN status = 'Rejected' THEN 1 END) AS rejected_count,
                    COUNT(CASE WHEN status NOT IN ('Selected', 'Rejected') THEN 1 END) AS pending_count
                FROM APPLICATION
            """)
            app_row = cursor.fetchone()
            total_applications = int(app_row[0]) if app_row else 0
            selected_count = int(app_row[1]) if app_row else 0
            rejected_count = int(app_row[2]) if app_row else 0
            pending_count = int(app_row[3]) if app_row else 0

            # 3. Active Company Count
            cursor.execute("SELECT COUNT(*) FROM COMPANY")
            comp_row = cursor.fetchone()
            total_companies = int(comp_row[0]) if comp_row else 0

            # 4. Salary Package Benchmarks (from accepted placements)
            cursor.execute("""
                SELECT 
                    COUNT(placement_id) AS total_offers,
                    NVL(MAX(package_offered), 0.00) AS highest_package,
                    NVL(ROUND(AVG(package_offered), 2), 0.00) AS avg_package,
                    NVL(ROUND(MEDIAN(package_offered), 2), 0.00) AS median_package,
                    NVL(MIN(package_offered), 0.00) AS lowest_package
                FROM PLACEMENT
                WHERE acceptance_status = 'Accepted'
            """)
            pkg_row = cursor.fetchone()
            pkg_stats = {
                "total_offers": int(pkg_row[0]) if pkg_row else 0,
                "highest_package_lpa": _convert_value(pkg_row[1]) if pkg_row else 0.0,
                "avg_package_lpa": _convert_value(pkg_row[2]) if pkg_row else 0.0,
                "median_package_lpa": _convert_value(pkg_row[3]) if pkg_row else 0.0,
                "lowest_package_lpa": _convert_value(pkg_row[4]) if pkg_row else 0.0
            }

            # 5. Application Status Distribution Breakdown
            cursor.execute("""
                SELECT 
                    status,
                    COUNT(*) AS count,
                    ROUND((COUNT(*) * 100.0) / NULLIF((SELECT COUNT(*) FROM APPLICATION), 0), 2) AS percentage
                FROM APPLICATION
                GROUP BY status
                ORDER BY count DESC, status ASC
            """)
            distribution = _rows_to_dicts(cursor, cursor.fetchall())

            # Attach styling metadata to distribution items
            for item in distribution:
                item["color"] = STATUS_COLORS.get(item["status"], "#6b7280")
                item["badge_class"] = STATUS_BADGE_CLASSES.get(item["status"], "secondary")

        return {
            "summary_cards": {
                "total_students": total_students,
                "uniquely_placed_students": placed_students,
                "unplaced_students": unplaced_students,
                "placement_percentage": placement_pct,
                "total_applications": total_applications,
                "selected_applications": selected_count,
                "rejected_applications": rejected_count,
                "pending_applications": pending_count,
                "total_companies": total_companies,
                "package_stats": pkg_stats
            },
            "application_status_summary": {
                "selected": selected_count,
                "rejected": rejected_count,
                "pending": pending_count,
                "selected_percentage": round((selected_count * 100.0) / total_applications, 2) if total_applications > 0 else 0.0,
                "rejected_percentage": round((rejected_count * 100.0) / total_applications, 2) if total_applications > 0 else 0.0,
                "pending_percentage": round((pending_count * 100.0) / total_applications, 2) if total_applications > 0 else 0.0
            },
            "status_distribution": distribution
        }
    finally:
        conn.close()


def _fetch_application_analytics_data():
    """
    Extracts deep application status distribution, charting data, and company breakdown.
    """
    conn = database.get_db_connection()
    try:
        with conn.cursor() as cursor:
            # 1. Status aggregates
            cursor.execute("""
                SELECT 
                    COUNT(*) AS total_applications,
                    COUNT(CASE WHEN status = 'Selected' THEN 1 END) AS selected_count,
                    COUNT(CASE WHEN status = 'Rejected' THEN 1 END) AS rejected_count,
                    COUNT(CASE WHEN status NOT IN ('Selected', 'Rejected') THEN 1 END) AS pending_count
                FROM APPLICATION
            """)
            row = cursor.fetchone()
            total_apps = int(row[0]) if row else 0
            selected_cnt = int(row[1]) if row else 0
            rejected_cnt = int(row[2]) if row else 0
            pending_cnt = int(row[3]) if row else 0

            # 2. Detailed distribution
            cursor.execute("""
                SELECT 
                    status,
                    COUNT(*) AS count,
                    ROUND((COUNT(*) * 100.0) / NULLIF((SELECT COUNT(*) FROM APPLICATION), 0), 2) AS percentage
                FROM APPLICATION
                GROUP BY status
                ORDER BY count DESC, status ASC
            """)
            distribution = _rows_to_dicts(cursor, cursor.fetchall())

            # Prepare chart structures
            labels = []
            counts = []
            percentages = []
            colors = []
            for item in distribution:
                labels.append(item["status"])
                counts.append(item["count"])
                percentages.append(item["percentage"])
                colors.append(STATUS_COLORS.get(item["status"], "#6b7280"))
                item["color"] = STATUS_COLORS.get(item["status"], "#6b7280")
                item["badge_class"] = STATUS_BADGE_CLASSES.get(item["status"], "secondary")

            # 3. Company-wise application breakdown
            cursor.execute("""
                SELECT 
                    c.company_id,
                    c.company_name,
                    c.job_role,
                    COUNT(a.application_id) AS total_applicants,
                    COUNT(CASE WHEN a.status = 'Selected' THEN 1 END) AS selected_count,
                    COUNT(CASE WHEN a.status = 'Rejected' THEN 1 END) AS rejected_count,
                    COUNT(CASE WHEN a.status NOT IN ('Selected', 'Rejected') THEN 1 END) AS pending_count
                FROM COMPANY c
                LEFT JOIN APPLICATION a ON c.company_id = a.company_id
                GROUP BY c.company_id, c.company_name, c.job_role
                ORDER BY total_applicants DESC, c.company_name ASC
            """)
            company_apps = _rows_to_dicts(cursor, cursor.fetchall())

            # 4. Recent Applications sample
            cursor.execute("""
                SELECT 
                    a.application_id,
                    s.student_name,
                    s.branch,
                    c.company_name,
                    c.job_role,
                    a.application_date,
                    a.status
                FROM APPLICATION a
                JOIN STUDENT s ON a.student_id = s.student_id
                JOIN COMPANY c ON a.company_id = c.company_id
                ORDER BY a.application_date DESC, a.application_id DESC
                FETCH FIRST 10 ROWS ONLY
            """)
            recent_apps = _rows_to_dicts(cursor, cursor.fetchall())
            for app in recent_apps:
                app["badge_class"] = STATUS_BADGE_CLASSES.get(app["status"], "secondary")

        return {
            "total_applications": total_apps,
            "status_metrics": {
                "selected": {
                    "count": selected_cnt,
                    "percentage": round((selected_cnt * 100.0) / total_apps, 2) if total_apps > 0 else 0.0
                },
                "rejected": {
                    "count": rejected_cnt,
                    "percentage": round((rejected_cnt * 100.0) / total_apps, 2) if total_apps > 0 else 0.0
                },
                "pending": {
                    "count": pending_cnt,
                    "percentage": round((pending_cnt * 100.0) / total_apps, 2) if total_apps > 0 else 0.0
                }
            },
            "status_distribution": distribution,
            "chart_data": {
                "labels": labels,
                "counts": counts,
                "percentages": percentages,
                "background_colors": colors
            },
            "company_distribution": company_apps,
            "recent_applications": recent_apps
        }
    finally:
        conn.close()


def _fetch_placement_summary_data():
    """
    Extracts branch-wise placement performance, institute-wide salary benchmarks,
    and company recruitment hiring conversions.
    """
    conn = database.get_db_connection()
    try:
        with conn.cursor() as cursor:
            # 1. Overall student & placement numbers
            cursor.execute("""
                SELECT 
                    COUNT(DISTINCT s.student_id) AS total_students,
                    COUNT(DISTINCT p.student_id) AS placed_students
                FROM STUDENT s
                LEFT JOIN PLACEMENT p 
                    ON s.student_id = p.student_id 
                   AND p.acceptance_status = 'Accepted'
            """)
            row = cursor.fetchone()
            total_students = int(row[0]) if row else 0
            placed_students = int(row[1]) if row else 0
            unplaced_students = max(0, total_students - placed_students)
            placement_pct = round((placed_students * 100.0) / total_students, 2) if total_students > 0 else 0.0

            # 2. Package stats
            cursor.execute("""
                SELECT 
                    COUNT(placement_id) AS total_offers,
                    NVL(MAX(package_offered), 0.00) AS highest_package,
                    NVL(ROUND(AVG(package_offered), 2), 0.00) AS avg_package,
                    NVL(ROUND(MEDIAN(package_offered), 2), 0.00) AS median_package,
                    NVL(MIN(package_offered), 0.00) AS lowest_package
                FROM PLACEMENT
                WHERE acceptance_status = 'Accepted'
            """)
            pkg_row = cursor.fetchone()
            salary_benchmarks = {
                "total_offers_accepted": int(pkg_row[0]) if pkg_row else 0,
                "highest_package_lpa": _convert_value(pkg_row[1]) if pkg_row else 0.0,
                "average_package_lpa": _convert_value(pkg_row[2]) if pkg_row else 0.0,
                "median_package_lpa": _convert_value(pkg_row[3]) if pkg_row else 0.0,
                "lowest_package_lpa": _convert_value(pkg_row[4]) if pkg_row else 0.0
            }

            # 3. Branch-wise placement summary
            cursor.execute("""
                SELECT 
                    s.branch,
                    COUNT(DISTINCT s.student_id) AS total_students,
                    COUNT(DISTINCT p.student_id) AS placed_students,
                    (COUNT(DISTINCT s.student_id) - COUNT(DISTINCT p.student_id)) AS unplaced_students,
                    CASE 
                        WHEN COUNT(DISTINCT s.student_id) = 0 THEN 0.00
                        ELSE ROUND((COUNT(DISTINCT p.student_id) * 100.0) / COUNT(DISTINCT s.student_id), 2)
                    END AS placement_percentage,
                    NVL(MAX(p.package_offered), 0.00) AS highest_package_lpa,
                    NVL(ROUND(AVG(p.package_offered), 2), 0.00) AS avg_package_lpa,
                    NVL(MIN(p.package_offered), 0.00) AS lowest_package_lpa
                FROM STUDENT s
                LEFT JOIN PLACEMENT p 
                    ON s.student_id = p.student_id 
                   AND p.acceptance_status = 'Accepted'
                GROUP BY s.branch
                ORDER BY placement_percentage DESC, total_students DESC
            """)
            branch_summary = _rows_to_dicts(cursor, cursor.fetchall())

            # 4. Company conversion funnel
            cursor.execute("""
                SELECT 
                    c.company_id,
                    c.company_name,
                    c.job_role,
                    c.package AS offered_ctc_lpa,
                    COUNT(DISTINCT a.application_id) AS total_applicants,
                    COUNT(DISTINCT p.placement_id) AS total_hires,
                    CASE 
                        WHEN COUNT(DISTINCT a.application_id) = 0 THEN 0.00
                        ELSE ROUND((COUNT(DISTINCT p.placement_id) * 100.0) / COUNT(DISTINCT a.application_id), 2)
                    END AS conversion_percentage
                FROM COMPANY c
                LEFT JOIN APPLICATION a ON c.company_id = a.company_id
                LEFT JOIN PLACEMENT p 
                    ON c.company_id = p.company_id 
                   AND p.acceptance_status = 'Accepted'
                GROUP BY c.company_id, c.company_name, c.job_role, c.package
                ORDER BY total_hires DESC, offered_ctc_lpa DESC
            """)
            company_funnel = _rows_to_dicts(cursor, cursor.fetchall())

        return {
            "total_students": total_students,
            "uniquely_placed_students": placed_students,
            "unplaced_students": unplaced_students,
            "placement_percentage": placement_pct,
            "salary_benchmarks": salary_benchmarks,
            "branch_summary": branch_summary,
            "company_hiring_funnel": company_funnel
        }
    finally:
        conn.close()


# ============================================================================
# API ENDPOINT 1: GET /analytics/overview
# ============================================================================
@analytics_bp.route("/overview")
def get_analytics_overview():
    """
    Returns high-level placement KPIs and application summary statistics
    in JSON format for summary cards and executive dashboards.
    """
    try:
        data = _fetch_overview_data()
        return jsonify({
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            **data
        }), 200
    except Exception as e:
        print(f"[ERROR] /analytics/overview failed: {e}")
        return jsonify({
            "status": "error",
            "message": f"Database query failed: {str(e)}"
        }), 500


# ============================================================================
# API ENDPOINT 2: GET /analytics/applications
# ============================================================================
@analytics_bp.route("/applications")
def get_application_analytics():
    """
    Returns detailed application lifecycle statistics:
    - Total submitted applications
    - Categorized counts: selected, rejected, pending (with percentages)
    - Full status distribution for charts
    - Company-wise applicant counts
    - Recent applications roster
    """
    try:
        data = _fetch_application_analytics_data()
        return jsonify({
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            **data
        }), 200
    except Exception as e:
        print(f"[ERROR] /analytics/applications failed: {e}")
        return jsonify({
            "status": "error",
            "message": f"Database query failed: {str(e)}"
        }), 500


# ============================================================================
# API ENDPOINT 3: GET /analytics/placement-summary
# ============================================================================
@analytics_bp.route("/placement-summary")
def get_placement_summary():
    """
    Returns comprehensive placement statistics:
    - Registered students, uniquely placed students, and placement percentage
    - Salary package statistics (highest, average, median, lowest LPA)
    - Department/branch-wise placement breakdown
    - Company hiring conversion statistics
    """
    try:
        data = _fetch_placement_summary_data()
        return jsonify({
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            **data
        }), 200
    except Exception as e:
        print(f"[ERROR] /analytics/placement-summary failed: {e}")
        return jsonify({
            "status": "error",
            "message": f"Database query failed: {str(e)}"
        }), 500


# ============================================================================
# WEB VIEW / DASHBOARD: GET /analytics & GET /analytics/dashboard
# ============================================================================
@analytics_bp.route("")
@analytics_bp.route("/dashboard")
def analytics_dashboard():
    """
    Renders the modern Analytics Dashboard web interface.
    If requested with query parameter '?format=json' or header 'Accept: application/json',
    returns JSON overview data directly.
    """
    if (request.args.get("format") == "json" or 
            request.headers.get("Accept") == "application/json"):
        return get_analytics_overview()

    # Render immediately; the dashboard loads APIs asynchronously so database
    # outages cannot prevent the interface and retry controls from opening.
    return render_template("analytics/dashboard.html")
