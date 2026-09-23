"""
Campus Placement Analytics System - Eligibility Checking Blueprint
Phase 5: Student Eligibility Checking Module
"""

from decimal import Decimal
from flask import Blueprint, render_template, request, redirect, url_for, flash
import database
from services.eligibility_service import check_eligibility

eligibility_bp = Blueprint("eligibility", __name__, url_prefix="/eligibility")


def _to_python(v):
    if isinstance(v, Decimal):
        return float(v)
    return v


def _rows_to_dicts(cursor, rows):
    if not rows:
        return []
    cols = [col[0].lower() for col in cursor.description]
    return [{k: _to_python(v) for k, v in zip(cols, r)} for r in rows]


@eligibility_bp.route("")
def eligibility_home():
    """
    Renders the student & company drive selection form for eligibility checking.
    Supports pre-selecting student or company via URL parameters:
    /eligibility?student_id=1
    /eligibility?company_id=2
    """
    selected_student_id = request.args.get("student_id", type=int)
    selected_company_id = request.args.get("company_id", type=int)

    students = []
    companies = []
    error_message = None

    try:
        conn = database.get_db_connection()
        with conn.cursor() as cursor:
            # Fetch all students for dropdown
            cursor.execute("""
                SELECT student_id, student_name, branch, cgpa
                FROM STUDENT
                ORDER BY student_name
            """)
            students = _rows_to_dicts(cursor, cursor.fetchall())

            # Fetch all companies for dropdown
            cursor.execute("""
                SELECT company_id, company_name, job_role, package
                FROM COMPANY
                ORDER BY company_name
            """)
            companies = _rows_to_dicts(cursor, cursor.fetchall())

        conn.close()
    except Exception as e:
        error_message = f"Failed to load records from database: {str(e)}"
        print(f"[ERROR] {error_message}")

    return render_template(
        "eligibility/eligibility.html",
        students=students,
        companies=companies,
        selected_student_id=selected_student_id,
        selected_company_id=selected_company_id,
        error_message=error_message
    )


@eligibility_bp.route("/check", methods=["GET", "POST"])
def check_eligibility_route():
    """
    Evaluates eligibility between chosen student and company.
    Supports both POST submission from the form and GET with query parameters.
    """
    if request.method == "POST":
        raw_student_id = request.form.get("student_id", "").strip()
        raw_company_id = request.form.get("company_id", "").strip()
    else:
        raw_student_id = request.args.get("student_id", "").strip()
        raw_company_id = request.args.get("company_id", "").strip()

    if not raw_student_id or not raw_company_id:
        flash("Please select both a student and a recruiting company to check eligibility.", "warning")
        return redirect(url_for("eligibility.eligibility_home"))

    try:
        student_id = int(raw_student_id)
        company_id = int(raw_company_id)
    except (ValueError, TypeError):
        flash("Invalid student or company selection.", "danger")
        return redirect(url_for("eligibility.eligibility_home"))

    try:
        result = check_eligibility(student_id, company_id)
        return render_template("eligibility/result.html", result=result)
    except ValueError as ve:
        flash(str(ve), "warning")
        return redirect(url_for("eligibility.eligibility_home"))
    except Exception as ex:
        flash(f"Error checking eligibility: {str(ex)}", "danger")
        return redirect(url_for("eligibility.eligibility_home"))
