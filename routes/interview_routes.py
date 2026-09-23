"""
Campus Placement Analytics System - Interview Management Blueprint
Phase 6: Application & Interview Tracking Module

Routes:
    GET  /applications/<application_id>/interviews/add  - show add interview form
    POST /applications/<application_id>/interviews/add  - create interview record
    GET  /interviews/<interview_id>/edit                 - show edit form
    POST /interviews/<interview_id>/edit                 - update interview record
    POST /interviews/<interview_id>/delete               - delete interview record
"""

from decimal import Decimal
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash
import database

interview_bp = Blueprint("interviews", __name__)

# Allowed interview status values from Oracle CHECK constraint
ALLOWED_INTERVIEW_STATUSES = ["Scheduled", "Passed", "Failed", "Pending"]


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def _convert_value(v):
    """Convert Oracle types to Python-native types."""
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
    """Convert multiple Oracle rows to a list of lowercase dictionaries."""
    if not rows:
        return []
    columns = [col[0].lower() for col in cursor.description]
    return [{k: _convert_value(v) for k, v in zip(columns, r)} for r in rows]


def _get_application_context(cursor, application_id):
    """
    Helper: fetch application + student + company context for a given application_id.
    Returns dict or None if not found.
    """
    cursor.execute("""
        SELECT a.application_id, a.status,
               s.student_id, s.student_name, s.branch,
               c.company_id, c.company_name, c.job_role
        FROM APPLICATION a
        JOIN STUDENT s ON a.student_id = s.student_id
        JOIN COMPANY c ON a.company_id = c.company_id
        WHERE a.application_id = :aid
    """, aid=application_id)
    return _row_to_dict(cursor, cursor.fetchone())


# ============================================================================
# 1. ADD INTERVIEW ROUND
# ============================================================================
@interview_bp.route(
    "/applications/<int:application_id>/interviews/add",
    methods=["GET", "POST"]
)
def add_interview(application_id):
    """
    GET:  Shows the add interview form for a given application.
    POST: Validates and inserts a new interview round record.

    Validation:
    - application must exist
    - round_number must be a positive integer and unique for this application
    - round_name must not be empty
    - score is optional; if provided must be 0–100
    - interview_date must be a valid date
    - status must be one of the allowed values
    """
    application = None

    try:
        conn = database.get_db_connection()
        with conn.cursor() as cursor:
            application = _get_application_context(cursor, application_id)
        conn.close()
    except Exception as e:
        flash(f"Error loading application context: {str(e)}", "danger")
        return redirect(url_for("applications.list_applications"))

    if not application:
        flash(f"Application #{application_id} not found.", "warning")
        return redirect(url_for("applications.list_applications"))

    if request.method == "GET":
        return render_template(
            "interviews/add_interview.html",
            application=application,
            allowed_statuses=ALLOWED_INTERVIEW_STATUSES
        )

    # --- POST: Validate and Insert ---
    raw_round_number  = request.form.get("round_number", "").strip()
    round_name        = request.form.get("round_name", "").strip()
    raw_interview_date = request.form.get("interview_date", "").strip()
    raw_score         = request.form.get("score", "").strip()
    status            = request.form.get("status", "Scheduled").strip()
    feedback          = request.form.get("feedback", "").strip() or None

    errors = []

    # Validate round_number
    round_number = None
    if not raw_round_number:
        errors.append("Round number is required.")
    else:
        try:
            round_number = int(raw_round_number)
            if round_number < 1:
                errors.append("Round number must be a positive integer (>= 1).")
        except ValueError:
            errors.append("Round number must be a valid positive integer.")

    # Validate round_name
    if not round_name:
        errors.append("Round name is required (e.g., Technical, HR, Managerial).")

    # Validate interview_date
    interview_date = None
    if not raw_interview_date:
        errors.append("Interview date is required.")
    else:
        try:
            interview_date = datetime.strptime(raw_interview_date, "%Y-%m-%d").date()
        except ValueError:
            errors.append("Interview date must be a valid date (YYYY-MM-DD).")

    # Validate score (optional; 0–100 if provided)
    score = None
    if raw_score:
        try:
            score = float(raw_score)
            if score < 0.0 or score > 100.0:
                errors.append("Score must be between 0 and 100.")
        except ValueError:
            errors.append("Score must be a valid number (0–100).")

    # Validate status
    if status not in ALLOWED_INTERVIEW_STATUSES:
        errors.append(f"Invalid status. Allowed: {', '.join(ALLOWED_INTERVIEW_STATUSES)}.")

    if errors:
        for err in errors:
            flash(err, "danger")
        return render_template(
            "interviews/add_interview.html",
            application=application,
            allowed_statuses=ALLOWED_INTERVIEW_STATUSES,
            form=request.form
        )

    # Insert into DB
    try:
        conn = database.get_db_connection()
        with conn.cursor() as cursor:
            # Check for duplicate round_number for this application
            cursor.execute("""
                SELECT COUNT(*) FROM INTERVIEW
                WHERE application_id = :aid AND round_number = :rn
            """, aid=application_id, rn=round_number)
            if cursor.fetchone()[0] > 0:
                conn.close()
                flash(
                    f"Round #{round_number} already exists for this application. "
                    f"Please use a different round number.",
                    "warning"
                )
                return render_template(
                    "interviews/add_interview.html",
                    application=application,
                    allowed_statuses=ALLOWED_INTERVIEW_STATUSES,
                    form=request.form
                )

            # Get next interview_id
            cursor.execute("SELECT NVL(MAX(interview_id), 0) + 1 FROM INTERVIEW")
            new_id = int(cursor.fetchone()[0])

            cursor.execute("""
                INSERT INTO INTERVIEW
                    (interview_id, application_id, round_number, round_name,
                     interview_date, score, status, feedback)
                VALUES
                    (:iid, :aid, :rn, :rname, :idate, :score, :status, :feedback)
            """,
                iid=new_id,
                aid=application_id,
                rn=round_number,
                rname=round_name,
                idate=interview_date,
                score=score,
                status=status,
                feedback=feedback
            )
            conn.commit()
        conn.close()
    except Exception as e:
        flash(f"Error adding interview round: {str(e)}", "danger")
        print(f"[ERROR] Interview insert failed: {e}")
        return render_template(
            "interviews/add_interview.html",
            application=application,
            allowed_statuses=ALLOWED_INTERVIEW_STATUSES,
            form=request.form
        )

    flash(f"Interview round '{round_name}' (Round #{round_number}) added successfully.", "success")
    return redirect(url_for("applications.view_application", application_id=application_id))


# ============================================================================
# 2. EDIT INTERVIEW ROUND
# ============================================================================
@interview_bp.route("/interviews/<int:interview_id>/edit", methods=["GET", "POST"])
def edit_interview(interview_id):
    """
    GET:  Shows pre-filled edit form for an interview round.
    POST: Validates and updates the interview record.
    """
    interview = None
    application = None

    try:
        conn = database.get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT interview_id, application_id, round_number, round_name,
                       interview_date, score, status, feedback
                FROM INTERVIEW
                WHERE interview_id = :iid
            """, iid=interview_id)
            interview = _row_to_dict(cursor, cursor.fetchone())

            if not interview:
                conn.close()
                flash(f"Interview #{interview_id} not found.", "warning")
                return redirect(url_for("applications.list_applications"))

            application = _get_application_context(cursor, interview["application_id"])
        conn.close()
    except Exception as e:
        flash(f"Error loading interview: {str(e)}", "danger")
        return redirect(url_for("applications.list_applications"))

    if request.method == "GET":
        return render_template(
            "interviews/edit_interview.html",
            interview=interview,
            application=application,
            allowed_statuses=ALLOWED_INTERVIEW_STATUSES
        )

    # --- POST: Validate and Update ---
    round_name        = request.form.get("round_name", "").strip()
    raw_interview_date = request.form.get("interview_date", "").strip()
    raw_score         = request.form.get("score", "").strip()
    status            = request.form.get("status", "").strip()
    feedback          = request.form.get("feedback", "").strip() or None

    errors = []

    if not round_name:
        errors.append("Round name is required.")

    interview_date = None
    if not raw_interview_date:
        errors.append("Interview date is required.")
    else:
        try:
            interview_date = datetime.strptime(raw_interview_date, "%Y-%m-%d").date()
        except ValueError:
            errors.append("Interview date must be a valid date (YYYY-MM-DD).")

    score = None
    if raw_score:
        try:
            score = float(raw_score)
            if score < 0.0 or score > 100.0:
                errors.append("Score must be between 0 and 100.")
        except ValueError:
            errors.append("Score must be a valid number (0–100).")

    if status not in ALLOWED_INTERVIEW_STATUSES:
        errors.append(f"Invalid status. Allowed: {', '.join(ALLOWED_INTERVIEW_STATUSES)}.")

    if errors:
        for err in errors:
            flash(err, "danger")
        return render_template(
            "interviews/edit_interview.html",
            interview=interview,
            application=application,
            allowed_statuses=ALLOWED_INTERVIEW_STATUSES,
            form=request.form
        )

    try:
        conn = database.get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
                UPDATE INTERVIEW
                SET round_name     = :rname,
                    interview_date = :idate,
                    score          = :score,
                    status         = :status,
                    feedback       = :feedback
                WHERE interview_id = :iid
            """,
                rname=round_name,
                idate=interview_date,
                score=score,
                status=status,
                feedback=feedback,
                iid=interview_id
            )
            conn.commit()
        conn.close()
    except Exception as e:
        flash(f"Error updating interview: {str(e)}", "danger")
        print(f"[ERROR] Interview update failed: {e}")
        return render_template(
            "interviews/edit_interview.html",
            interview=interview,
            application=application,
            allowed_statuses=ALLOWED_INTERVIEW_STATUSES,
            form=request.form
        )

    flash(f"Interview round '{round_name}' updated successfully.", "success")
    return redirect(url_for("applications.view_application", application_id=interview["application_id"]))


# ============================================================================
# 3. DELETE INTERVIEW ROUND
# ============================================================================
@interview_bp.route("/interviews/<int:interview_id>/delete", methods=["POST"])
def delete_interview(interview_id):
    """
    Deletes a single interview round record.
    The parent application is NOT deleted.
    """
    application_id = None

    try:
        conn = database.get_db_connection()
        with conn.cursor() as cursor:
            # Fetch application_id and round_name for redirect + flash
            cursor.execute("""
                SELECT application_id, round_name
                FROM INTERVIEW WHERE interview_id = :iid
            """, iid=interview_id)
            row = cursor.fetchone()
            if not row:
                conn.close()
                flash(f"Interview #{interview_id} not found.", "warning")
                return redirect(url_for("applications.list_applications"))

            application_id = row[0]
            round_name = row[1]

            cursor.execute("""
                DELETE FROM INTERVIEW WHERE interview_id = :iid
            """, iid=interview_id)
            conn.commit()
        conn.close()
    except Exception as e:
        flash(f"Error deleting interview: {str(e)}", "danger")
        print(f"[ERROR] Interview delete failed: {e}")
        if application_id:
            return redirect(url_for("applications.view_application", application_id=application_id))
        return redirect(url_for("applications.list_applications"))

    flash(f"Interview round '{round_name}' deleted. Application record remains intact.", "success")
    return redirect(url_for("applications.view_application", application_id=application_id))
