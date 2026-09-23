"""
Campus Placement Analytics System - Application Management Blueprint
Phase 6: Application & Interview Tracking Module

Routes:
    GET  /applications                   - list all applications
    GET  /applications/add               - show add form
    POST /applications/add               - create application (eligibility gated)
    GET  /applications/<id>              - application details + interviews
    POST /applications/<id>/status       - update application status
    POST /applications/<id>/delete       - delete application
"""

from datetime import datetime, date
from decimal import Decimal
from flask import Blueprint, render_template, request, redirect, url_for, flash
import database
from services.eligibility_service import check_eligibility

application_bp = Blueprint("applications", __name__, url_prefix="/applications")

# Allowed status values from the Oracle CHECK constraint
ALLOWED_STATUSES = ["Applied", "Shortlisted", "In Review", "Rejected", "Selected"]


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def _convert_value(v):
    """Convert Oracle types to Python-native types for Jinja2 compatibility."""
    if isinstance(v, Decimal):
        return float(v)
    return v


def _row_to_dict(cursor, row):
    """Convert an Oracle query row to a lowercase dictionary."""
    if not row:
        return None
    columns = [col[0].lower() for col in cursor.description]
    return {k: _convert_value(v) for k, v in zip(columns, row)}


def _rows_to_dicts(cursor, rows):
    """Convert multiple Oracle query rows to a list of lowercase dictionaries."""
    if not rows:
        return []
    columns = [col[0].lower() for col in cursor.description]
    return [{k: _convert_value(v) for k, v in zip(columns, r)} for r in rows]


# ============================================================================
# 1. LIST ALL APPLICATIONS
# ============================================================================
@application_bp.route("")
def list_applications():
    """
    Displays all applications with student name, company name, job role,
    application date, and status. Uses JOINs to avoid raw ID display.
    """
    applications = []
    error_message = None

    try:
        conn = database.get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT a.application_id,
                       s.student_id, s.student_name, s.branch,
                       c.company_id, c.company_name, c.job_role, c.package,
                       a.application_date, a.status
                FROM APPLICATION a
                JOIN STUDENT s ON a.student_id = s.student_id
                JOIN COMPANY c ON a.company_id = c.company_id
                ORDER BY a.application_date DESC, a.application_id DESC
            """)
            applications = _rows_to_dicts(cursor, cursor.fetchall())
        conn.close()
    except Exception as e:
        error_message = f"Error fetching applications: {str(e)}"
        print(f"[ERROR] {error_message}")

    return render_template(
        "applications/applications.html",
        applications=applications,
        allowed_statuses=ALLOWED_STATUSES,
        error_message=error_message
    )


# ============================================================================
# 2. ADD APPLICATION (ELIGIBILITY GATED)
# ============================================================================
@application_bp.route("/add", methods=["GET", "POST"])
def add_application():
    """
    GET:  Displays student + company selection dropdowns.
    POST: Runs Phase 5 eligibility check; creates application only if ELIGIBLE.
          Blocks if ineligible (shows failed reasons) or duplicate exists.
    """
    students = []
    companies = []
    error_message = None

    # Load dropdown data for both GET and failed POST re-renders
    try:
        conn = database.get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT student_id, student_name, branch, cgpa
                FROM STUDENT ORDER BY student_name
            """)
            students = _rows_to_dicts(cursor, cursor.fetchall())

            cursor.execute("""
                SELECT company_id, company_name, job_role, package
                FROM COMPANY ORDER BY company_name
            """)
            companies = _rows_to_dicts(cursor, cursor.fetchall())
        conn.close()
    except Exception as e:
        error_message = f"Error loading form data: {str(e)}"
        print(f"[ERROR] {error_message}")

    if request.method == "GET":
        return render_template(
            "applications/add_application.html",
            students=students,
            companies=companies,
            error_message=error_message
        )

    # --- POST: Process Application Submission ---
    raw_student_id = request.form.get("student_id", "").strip()
    raw_company_id = request.form.get("company_id", "").strip()

    if not raw_student_id or not raw_company_id:
        flash("Please select both a student and a company.", "warning")
        return render_template(
            "applications/add_application.html",
            students=students, companies=companies,
            selected_student_id=raw_student_id,
            selected_company_id=raw_company_id
        )

    try:
        student_id = int(raw_student_id)
        company_id = int(raw_company_id)
    except (ValueError, TypeError):
        flash("Invalid student or company selection.", "danger")
        return redirect(url_for("applications.add_application"))

    # --- Step 1: Run Phase 5 Eligibility Check (reuse, no duplication) ---
    try:
        eligibility_result = check_eligibility(student_id, company_id)
    except ValueError as ve:
        flash(str(ve), "warning")
        return render_template(
            "applications/add_application.html",
            students=students, companies=companies,
            selected_student_id=student_id, selected_company_id=company_id
        )
    except Exception as ex:
        flash(f"Error running eligibility check: {str(ex)}", "danger")
        return render_template(
            "applications/add_application.html",
            students=students, companies=companies,
            selected_student_id=student_id, selected_company_id=company_id
        )

    # Block ineligible students
    if eligibility_result["overall_status"] != "ELIGIBLE":
        return render_template(
            "applications/add_application.html",
            students=students, companies=companies,
            selected_student_id=student_id,
            selected_company_id=company_id,
            eligibility_result=eligibility_result,
            blocked=True
        )

    # --- Step 2: Check for Duplicate Application ---
    try:
        conn = database.get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT COUNT(*) FROM APPLICATION
                WHERE student_id = :sid AND company_id = :cid
            """, sid=student_id, cid=company_id)
            if cursor.fetchone()[0] > 0:
                conn.close()
                flash(
                    f"{eligibility_result['student']['student_name']} has already "
                    f"applied to {eligibility_result['company']['company_name']}.",
                    "warning"
                )
                return render_template(
                    "applications/add_application.html",
                    students=students, companies=companies,
                    selected_student_id=student_id,
                    selected_company_id=company_id,
                    eligibility_result=eligibility_result
                )

            # --- Step 3: Insert Application ---
            cursor.execute("""
                SELECT NVL(MAX(application_id), 0) + 1 FROM APPLICATION
            """)
            new_app_id = int(cursor.fetchone()[0])

            cursor.execute("""
                INSERT INTO APPLICATION
                    (application_id, student_id, company_id, application_date, status)
                VALUES
                    (:aid, :sid, :cid, SYSDATE, 'Applied')
            """, aid=new_app_id, sid=student_id, cid=company_id)

            conn.commit()
        conn.close()
    except Exception as e:
        flash(f"Error creating application: {str(e)}", "danger")
        print(f"[ERROR] Application insert failed: {e}")
        return render_template(
            "applications/add_application.html",
            students=students, companies=companies,
            selected_student_id=student_id,
            selected_company_id=company_id,
            eligibility_result=eligibility_result
        )

    flash(
        f"Application created successfully! "
        f"{eligibility_result['student']['student_name']} \u2192 "
        f"{eligibility_result['company']['company_name']} ({eligibility_result['company']['job_role']}). "
        f"Status: Applied.",
        "success"
    )
    return redirect(url_for("applications.list_applications"))


# ============================================================================
# 3. APPLICATION DETAILS (+ INTERVIEW HISTORY)
# ============================================================================
@application_bp.route("/<int:application_id>")
def view_application(application_id):
    """
    Displays full application details and all interview rounds for this application.
    """
    application = None
    interviews = []

    try:
        conn = database.get_db_connection()
        with conn.cursor() as cursor:
            # Fetch application with student and company details
            cursor.execute("""
                SELECT a.application_id, a.application_date, a.status,
                       s.student_id, s.student_name, s.branch, s.cgpa,
                       s.tenth_percentage, s.twelfth_percentage, s.backlogs,
                       c.company_id, c.company_name, c.job_role, c.package,
                       c.application_deadline, c.drive_date
                FROM APPLICATION a
                JOIN STUDENT s ON a.student_id = s.student_id
                JOIN COMPANY c ON a.company_id = c.company_id
                WHERE a.application_id = :aid
            """, aid=application_id)
            application = _row_to_dict(cursor, cursor.fetchone())

            if not application:
                conn.close()
                flash(f"Application #{application_id} not found.", "warning")
                return redirect(url_for("applications.list_applications"))

            # Fetch all interview rounds for this application
            cursor.execute("""
                SELECT interview_id, round_number, round_name,
                       interview_date, score, status, feedback
                FROM INTERVIEW
                WHERE application_id = :aid
                ORDER BY round_number ASC
            """, aid=application_id)
            interviews = _rows_to_dicts(cursor, cursor.fetchall())

        conn.close()
    except Exception as e:
        flash(f"Error loading application: {str(e)}", "danger")
        return redirect(url_for("applications.list_applications"))

    return render_template(
        "applications/application_details.html",
        application=application,
        interviews=interviews,
        allowed_statuses=ALLOWED_STATUSES
    )


# ============================================================================
# 4. UPDATE APPLICATION STATUS
# ============================================================================
@application_bp.route("/<int:application_id>/status", methods=["POST"])
def update_status(application_id):
    """
    Updates the status of an application.
    Validates against allowed status values from the Oracle CHECK constraint.
    """
    new_status = request.form.get("status", "").strip()

    if new_status not in ALLOWED_STATUSES:
        flash(
            f"Invalid status '{new_status}'. Allowed: {', '.join(ALLOWED_STATUSES)}.",
            "danger"
        )
        return redirect(url_for("applications.view_application", application_id=application_id))

    try:
        conn = database.get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
                UPDATE APPLICATION SET status = :status
                WHERE application_id = :aid
            """, status=new_status, aid=application_id)

            if cursor.rowcount == 0:
                conn.close()
                flash(f"Application #{application_id} not found.", "warning")
                return redirect(url_for("applications.list_applications"))

            conn.commit()
        conn.close()
    except Exception as e:
        flash(f"Error updating status: {str(e)}", "danger")
        print(f"[ERROR] Status update failed: {e}")
        return redirect(url_for("applications.view_application", application_id=application_id))

    flash(f"Application status updated to '{new_status}'.", "success")
    return redirect(url_for("applications.view_application", application_id=application_id))


# ============================================================================
# 5. DELETE APPLICATION
# ============================================================================
@application_bp.route("/<int:application_id>/delete", methods=["POST"])
def delete_application(application_id):
    """
    Deletes an application and all its associated interviews (CASCADE via FK).
    """
    try:
        conn = database.get_db_connection()
        with conn.cursor() as cursor:
            # Fetch label for flash message before deletion
            cursor.execute("""
                SELECT s.student_name, c.company_name
                FROM APPLICATION a
                JOIN STUDENT s ON a.student_id = s.student_id
                JOIN COMPANY c ON a.company_id = c.company_id
                WHERE a.application_id = :aid
            """, aid=application_id)
            row = cursor.fetchone()
            label = f"#{application_id}" if not row else f"{row[0]} \u2192 {row[1]}"

            cursor.execute("""
                DELETE FROM APPLICATION WHERE application_id = :aid
            """, aid=application_id)
            conn.commit()
        conn.close()
    except Exception as e:
        flash(f"Error deleting application: {str(e)}", "danger")
        print(f"[ERROR] Application delete failed: {e}")
        return redirect(url_for("applications.view_application", application_id=application_id))

    flash(f"Application ({label}) and all related interviews have been deleted.", "success")
    return redirect(url_for("applications.list_applications"))
