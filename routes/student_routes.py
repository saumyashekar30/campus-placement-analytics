"""
Campus Placement Analytics System - Student Management Blueprint
Phase 3: Complete Student CRUD and Related Profile Management (Skills, Certs, Projects, Internships)
"""

from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash
import database
import oracledb

student_bp = Blueprint("students", __name__, url_prefix="/students")


from decimal import Decimal

def _convert_value(v):
    """Convert Oracle types to Python-native types for Jinja2 compatibility."""
    if isinstance(v, Decimal):
        return float(v)
    return v


def _row_to_dict(cursor, row):
    """Helper to convert an Oracle query row to a lowercase dictionary."""
    if not row:
        return None
    columns = [col[0].lower() for col in cursor.description]
    return {k: _convert_value(v) for k, v in zip(columns, row)}


def _rows_to_dicts(cursor, rows):
    """Helper to convert multiple Oracle query rows to a list of lowercase dictionaries."""
    if not rows:
        return []
    columns = [col[0].lower() for col in cursor.description]
    return [{k: _convert_value(v) for k, v in zip(columns, r)} for r in rows]


# ============================================================================
# 1. VIEW ALL STUDENTS (LIST VIEW)
# ============================================================================
@student_bp.route("")
def list_students():
    """
    Renders the student roster with ID, Name, Branch, CGPA, Backlogs,
    and action links (View, Edit, Delete).
    """
    students = []
    error_message = None

    try:
        conn = database.get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT student_id, student_name, branch, cgpa,
                       tenth_percentage, twelfth_percentage, backlogs
                FROM STUDENT
                ORDER BY student_id
            """)
            students = _rows_to_dicts(cursor, cursor.fetchall())
        conn.close()
    except Exception as e:
        error_message = f"Error fetching student records: {str(e)}"
        print(f"[ERROR] {error_message}")

    return render_template(
        "students/students.html",
        students=students,
        error_message=error_message
    )


# ============================================================================
# 2. ADD STUDENT (FORM & SUBMISSION)
# ============================================================================
@student_bp.route("/add", methods=["GET", "POST"])
def add_student():
    """
    GET: Displays the student creation form.
    POST: Validates inputs and inserts a new student into Oracle DB.
    """
    if request.method == "GET":
        return render_template("students/add_student.html")

    # Extract form inputs
    raw_id = request.form.get("student_id", "").strip()
    student_name = request.form.get("student_name", "").strip()
    email = request.form.get("email", "").strip()
    phone = request.form.get("phone", "").strip() or None
    branch = request.form.get("branch", "").strip().upper()
    raw_cgpa = request.form.get("cgpa", "").strip()
    raw_tenth = request.form.get("tenth_percentage", "").strip()
    raw_twelfth = request.form.get("twelfth_percentage", "").strip()
    raw_backlogs = request.form.get("backlogs", "").strip()
    resume_url = request.form.get("resume_url", "").strip() or None

    errors = []

    # 1. Validate Student ID (if provided, must be positive integer and unique)
    student_id = None
    if raw_id:
        if not raw_id.isdigit() or int(raw_id) <= 0:
            errors.append("Student ID must be a positive number (e.g., 11, 2401).")
        else:
            student_id = int(raw_id)

    # 2. Validate Name
    if not student_name or len(student_name) < 2:
        errors.append("Student Name is required (minimum 2 characters).")
    elif student_name.replace(" ", "").isdigit():
        errors.append("Student Name cannot consist entirely of numbers.")

    # 3. Validate Email
    if not email or "@" not in email or "." not in email:
        errors.append("A valid email address is required.")

    # 4. Validate Branch
    if not branch:
        errors.append("Branch selection is required.")

    # 5. Validate CGPA (0.00 to 10.00)
    cgpa = None
    try:
        cgpa = float(raw_cgpa)
        if cgpa < 0.0 or cgpa > 10.0:
            errors.append("CGPA must be between 0.00 and 10.00.")
    except (ValueError, TypeError):
        errors.append("A valid numeric CGPA is required (0.00 - 10.00).")

    # 6. Validate 10th Percentage (0.00 to 100.00)
    tenth = None
    try:
        tenth = float(raw_tenth)
        if tenth < 0.0 or tenth > 100.0:
            errors.append("10th percentage must be between 0.00% and 100.00%.")
    except (ValueError, TypeError):
        errors.append("A valid 10th percentage is required (0.00 - 100.00).")

    # 7. Validate 12th Percentage (0.00 to 100.00)
    twelfth = None
    try:
        twelfth = float(raw_twelfth)
        if twelfth < 0.0 or twelfth > 100.0:
            errors.append("12th percentage must be between 0.00% and 100.00%.")
    except (ValueError, TypeError):
        errors.append("A valid 12th percentage is required (0.00 - 100.00).")

    # 8. Validate Backlogs (>= 0)
    backlogs = 0
    try:
        backlogs = int(raw_backlogs)
        if backlogs < 0:
            errors.append("Number of backlogs cannot be negative.")
    except (ValueError, TypeError):
        errors.append("Number of backlogs must be a valid non-negative integer.")

    if errors:
        for err in errors:
            flash(err, "danger")
        return render_template("students/add_student.html", form=request.form), 400

    # Execute Database Insert
    try:
        conn = database.get_db_connection()
        with conn.cursor() as cursor:
            # Check for duplicate ID if custom ID was given
            if student_id:
                cursor.execute("SELECT COUNT(*) FROM STUDENT WHERE student_id = :id", id=student_id)
                if cursor.fetchone()[0] > 0:
                    flash(f"Student ID #{student_id} is already registered. Please choose another ID.", "danger")
                    conn.close()
                    return render_template("students/add_student.html", form=request.form), 400

            # Check for duplicate email
            cursor.execute("SELECT COUNT(*) FROM STUDENT WHERE email = :e", e=email)
            if cursor.fetchone()[0] > 0:
                flash(f"Email '{email}' is already registered with another student.", "danger")
                conn.close()
                return render_template("students/add_student.html", form=request.form), 400

            if student_id:
                insert_sql = """
                    INSERT INTO STUDENT (
                        student_id, student_name, email, phone, branch,
                        cgpa, tenth_percentage, twelfth_percentage, backlogs, resume_url
                    ) VALUES (
                        :id, :name, :email, :phone, :branch,
                        :cgpa, :tenth, :twelfth, :backlogs, :resume
                    )
                """
                cursor.execute(
                    insert_sql,
                    id=student_id, name=student_name, email=email, phone=phone,
                    branch=branch, cgpa=cgpa, tenth=tenth, twelfth=twelfth,
                    backlogs=backlogs, resume=resume_url
                )
            else:
                insert_sql = """
                    INSERT INTO STUDENT (
                        student_name, email, phone, branch,
                        cgpa, tenth_percentage, twelfth_percentage, backlogs, resume_url
                    ) VALUES (
                        :name, :email, :phone, :branch,
                        :cgpa, :tenth, :twelfth, :backlogs, :resume
                    )
                """
                cursor.execute(
                    insert_sql,
                    name=student_name, email=email, phone=phone,
                    branch=branch, cgpa=cgpa, tenth=tenth, twelfth=twelfth,
                    backlogs=backlogs, resume=resume_url
                )

            conn.commit()
        conn.close()
        flash(f"Student '{student_name}' successfully added!", "success")
        return redirect(url_for("students.list_students"))

    except oracledb.DatabaseError as db_err:
        error_obj, = db_err.args
        flash(f"Oracle Error: {error_obj.message}", "danger")
        return render_template("students/add_student.html", form=request.form), 500
    except Exception as ex:
        flash(f"Unexpected Error: {str(ex)}", "danger")
        return render_template("students/add_student.html", form=request.form), 500


# ============================================================================
# 3. VIEW STUDENT PROFILE (FULL DASHBOARD VIEW)
# ============================================================================
@student_bp.route("/<int:student_id>")
def view_profile(student_id):
    """
    Displays the complete student profile including:
    - Basic demographic and academic metrics
    - Skills (STUDENT_SKILL)
    - Certifications (CERTIFICATION)
    - Projects (PROJECT)
    - Internships (INTERNSHIP)
    """
    student = None
    skills = []
    certifications = []
    projects = []
    internships = []

    try:
        conn = database.get_db_connection()
        with conn.cursor() as cursor:
            # 1. Fetch Student Core Details
            cursor.execute("""
                SELECT student_id, student_name, email, phone, branch,
                       cgpa, tenth_percentage, twelfth_percentage, backlogs,
                       resume_url, created_at
                FROM STUDENT
                WHERE student_id = :id
            """, id=student_id)
            student = _row_to_dict(cursor, cursor.fetchone())

            if not student:
                conn.close()
                flash(f"Student #{student_id} not found.", "warning")
                return redirect(url_for("students.list_students"))

            # 2. Fetch Skills (PK is student_id + skill_name, no skill_id column)
            cursor.execute("""
                SELECT skill_name, proficiency_level
                FROM STUDENT_SKILL
                WHERE student_id = :id
                ORDER BY skill_name
            """, id=student_id)
            skills = _rows_to_dicts(cursor, cursor.fetchall())

            # 3. Fetch Certifications (alias issuing_organization -> issuing_org and certification_id -> cert_id)
            cursor.execute("""
                SELECT certification_id, certification_id AS cert_id, cert_name,
                       issuing_organization AS issuing_org,
                       issue_date, expiry_date, credential_id
                FROM CERTIFICATION
                WHERE student_id = :id
                ORDER BY issue_date DESC
            """, id=student_id)
            certifications = _rows_to_dicts(cursor, cursor.fetchall())

            # 4. Fetch Projects (alias project_title -> project_name for template)
            cursor.execute("""
                SELECT project_id, project_title AS project_name,
                       tech_stack, description, project_url, start_date, end_date
                FROM PROJECT
                WHERE student_id = :id
                ORDER BY start_date DESC
            """, id=student_id)
            projects = _rows_to_dicts(cursor, cursor.fetchall())

            # 5. Fetch Internships (table has no duration_months/stipend columns)
            cursor.execute("""
                SELECT internship_id, company_name, role,
                       start_date, end_date, description
                FROM INTERNSHIP
                WHERE student_id = :id
                ORDER BY start_date DESC
            """, id=student_id)
            internships = _rows_to_dicts(cursor, cursor.fetchall())

        conn.close()
    except Exception as e:
        flash(f"Error loading student profile: {str(e)}", "danger")
        return redirect(url_for("students.list_students"))

    return render_template(
        "students/student_profile.html",
        student=student,
        skills=skills,
        certifications=certifications,
        projects=projects,
        internships=internships
    )


# ============================================================================
# 4. EDIT STUDENT (FORM & SUBMISSION)
# ============================================================================
@student_bp.route("/<int:student_id>/edit", methods=["GET", "POST"])
def edit_student(student_id):
    """
    GET: Displays pre-filled edit form (Student ID is read-only).
    POST: Validates inputs and updates the student in Oracle DB.
    """
    conn = database.get_db_connection()

    if request.method == "GET":
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT student_id, student_name, email, phone, branch,
                           cgpa, tenth_percentage, twelfth_percentage, backlogs, resume_url
                    FROM STUDENT
                    WHERE student_id = :id
                """, id=student_id)
                student = _row_to_dict(cursor, cursor.fetchone())
            conn.close()

            if not student:
                flash(f"Student #{student_id} not found.", "warning")
                return redirect(url_for("students.list_students"))

            return render_template("students/edit_student.html", student=student)
        except Exception as e:
            conn.close()
            flash(f"Error loading student: {str(e)}", "danger")
            return redirect(url_for("students.list_students"))

    # POST Update
    student_name = request.form.get("student_name", "").strip()
    email = request.form.get("email", "").strip()
    phone = request.form.get("phone", "").strip() or None
    branch = request.form.get("branch", "").strip().upper()
    raw_cgpa = request.form.get("cgpa", "").strip()
    raw_tenth = request.form.get("tenth_percentage", "").strip()
    raw_twelfth = request.form.get("twelfth_percentage", "").strip()
    raw_backlogs = request.form.get("backlogs", "").strip()
    resume_url = request.form.get("resume_url", "").strip() or None

    errors = []

    if not student_name or len(student_name) < 2:
        errors.append("Student Name is required.")
    elif student_name.replace(" ", "").isdigit():
        errors.append("Student Name cannot consist entirely of numbers.")

    if not email or "@" not in email:
        errors.append("A valid email address is required.")

    if not branch:
        errors.append("Branch selection is required.")

    try:
        cgpa = float(raw_cgpa)
        if cgpa < 0.0 or cgpa > 10.0:
            errors.append("CGPA must be between 0.00 and 10.00.")
    except (ValueError, TypeError):
        errors.append("Valid numeric CGPA is required.")

    try:
        tenth = float(raw_tenth)
        if tenth < 0.0 or tenth > 100.0:
            errors.append("10th percentage must be between 0.00% and 100.00%.")
    except (ValueError, TypeError):
        errors.append("Valid 10th percentage is required.")

    try:
        twelfth = float(raw_twelfth)
        if twelfth < 0.0 or twelfth > 100.0:
            errors.append("12th percentage must be between 0.00% and 100.00%.")
    except (ValueError, TypeError):
        errors.append("Valid 12th percentage is required.")

    try:
        backlogs = int(raw_backlogs)
        if backlogs < 0:
            errors.append("Backlogs cannot be negative.")
    except (ValueError, TypeError):
        errors.append("Valid non-negative integer required for backlogs.")

    if errors:
        for err in errors:
            flash(err, "danger")
        student_data = dict(request.form)
        student_data["student_id"] = student_id
        conn.close()
        return render_template("students/edit_student.html", student=student_data), 400

    try:
        with conn.cursor() as cursor:
            # Check email uniqueness for other students
            cursor.execute("""
                SELECT COUNT(*) FROM STUDENT
                WHERE email = :e AND student_id != :id
            """, e=email, id=student_id)
            if cursor.fetchone()[0] > 0:
                flash(f"Email '{email}' is already in use by another student.", "danger")
                student_data = dict(request.form)
                student_data["student_id"] = student_id
                conn.close()
                return render_template("students/edit_student.html", student=student_data), 400

            cursor.execute("""
                UPDATE STUDENT
                SET student_name = :name,
                    email = :email,
                    phone = :phone,
                    branch = :branch,
                    cgpa = :cgpa,
                    tenth_percentage = :tenth,
                    twelfth_percentage = :twelfth,
                    backlogs = :backlogs,
                    resume_url = :resume
                WHERE student_id = :id
            """, name=student_name, email=email, phone=phone, branch=branch,
                 cgpa=cgpa, tenth=tenth, twelfth=twelfth, backlogs=backlogs,
                 resume=resume_url, id=student_id)

            conn.commit()
        conn.close()
        flash(f"Student #{student_id} updated successfully!", "success")
        return redirect(url_for("students.view_profile", student_id=student_id))

    except Exception as ex:
        conn.close()
        flash(f"Update failed: {str(ex)}", "danger")
        return redirect(url_for("students.edit_student", student_id=student_id))


# ============================================================================
# 5. DELETE STUDENT (CASCADE SAFEGUARD)
# ============================================================================
@student_bp.route("/<int:student_id>/delete", methods=["POST"])
def delete_student(student_id):
    """
    Deletes the student record from Oracle STUDENT table.
    Foreign key child records (skills, certifications, projects, internships,
    applications, placements) are automatically cascaded by Oracle ON DELETE CASCADE constraints.
    """
    try:
        conn = database.get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT student_name FROM STUDENT WHERE student_id = :id", id=student_id)
            row = cursor.fetchone()
            student_name = row[0] if row else f"#{student_id}"

            cursor.execute("DELETE FROM STUDENT WHERE student_id = :id", id=student_id)
            conn.commit()
        conn.close()
        flash(f"Student '{student_name}' and all associated records have been deleted.", "info")
    except oracledb.IntegrityError as ie:
        flash(f"Cannot delete student due to database constraint: {str(ie)}", "danger")
    except Exception as e:
        flash(f"Delete failed: {str(e)}", "danger")

    return redirect(url_for("students.list_students"))


# ============================================================================
# 6. MANAGE SKILLS (ADD / DELETE)
# ============================================================================
@student_bp.route("/<int:student_id>/skills/add", methods=["POST"])
def add_skill(student_id):
    skill_name = request.form.get("skill_name", "").strip()
    proficiency = request.form.get("proficiency_level", "Intermediate").strip()

    if not skill_name:
        flash("Skill name is required.", "warning")
        return redirect(url_for("students.view_profile", student_id=student_id))

    if proficiency not in ["Beginner", "Intermediate", "Advanced", "Expert"]:
        proficiency = "Intermediate"

    try:
        conn = database.get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO STUDENT_SKILL (student_id, skill_name, proficiency_level)
                VALUES (:id, :skill, :lvl)
            """, id=student_id, skill=skill_name, lvl=proficiency)
            conn.commit()
        conn.close()
        flash(f"Skill '{skill_name}' added!", "success")
    except oracledb.IntegrityError:
        flash(f"Skill '{skill_name}' is already added for this student.", "warning")
    except Exception as e:
        flash(f"Failed to add skill: {str(e)}", "danger")

    return redirect(url_for("students.view_profile", student_id=student_id))


@student_bp.route("/<int:student_id>/skills/delete", methods=["POST"])
def delete_skill(student_id):
    """Delete a skill using skill_name POSTed from the form (PK is student_id + skill_name)."""
    skill_name = request.form.get("skill_name", "").strip()
    if not skill_name:
        flash("No skill specified for deletion.", "warning")
        return redirect(url_for("students.view_profile", student_id=student_id))
    try:
        conn = database.get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
                DELETE FROM STUDENT_SKILL
                WHERE student_id = :id AND skill_name = :skill
            """, id=student_id, skill=skill_name)
            conn.commit()
        conn.close()
        flash(f"Skill '{skill_name}' removed.", "info")
    except Exception as e:
        flash(f"Failed to remove skill: {str(e)}", "danger")

    return redirect(url_for("students.view_profile", student_id=student_id))


# ============================================================================
# 7. MANAGE CERTIFICATIONS (ADD / DELETE)
# ============================================================================
@student_bp.route("/<int:student_id>/certifications/add", methods=["POST"])
def add_certification(student_id):
    cert_name = request.form.get("cert_name", "").strip()
    issuing_org = request.form.get("issuing_org", "").strip()   # form field name
    raw_issue = request.form.get("issue_date", "").strip()
    raw_expiry = request.form.get("expiry_date", "").strip()
    credential_id = request.form.get("credential_id", "").strip() or None

    if not cert_name or not issuing_org:
        flash("Certification Name and Organization are required.", "warning")
        return redirect(url_for("students.view_profile", student_id=student_id))

    try:
        issue_date = datetime.strptime(raw_issue, "%Y-%m-%d").date() if raw_issue else datetime.now().date()
        expiry_date = datetime.strptime(raw_expiry, "%Y-%m-%d").date() if raw_expiry else None

        if expiry_date and expiry_date < issue_date:
            flash("Expiry date cannot be earlier than issue date.", "danger")
            return redirect(url_for("students.view_profile", student_id=student_id))

        conn = database.get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO CERTIFICATION (
                    student_id, cert_name, issuing_organization,
                    issue_date, expiry_date, credential_id
                ) VALUES (
                    :id, :name, :org, :issue, :expiry, :cred
                )
            """, id=student_id, name=cert_name, org=issuing_org,
                 issue=issue_date, expiry=expiry_date, cred=credential_id)
            conn.commit()
        conn.close()
        flash(f"Certification '{cert_name}' added!", "success")
    except Exception as e:
        flash(f"Failed to add certification: {str(e)}", "danger")

    return redirect(url_for("students.view_profile", student_id=student_id))


@student_bp.route("/<int:student_id>/certifications/<int:cert_id>/delete", methods=["POST"])
def delete_certification(student_id, cert_id):
    try:
        conn = database.get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
                DELETE FROM CERTIFICATION
                WHERE certification_id = :cid AND student_id = :sid
            """, cid=cert_id, sid=student_id)
            conn.commit()
        conn.close()
        flash("Certification removed.", "info")
    except Exception as e:
        flash(f"Failed to remove certification: {str(e)}", "danger")

    return redirect(url_for("students.view_profile", student_id=student_id))


# ============================================================================
# 8. MANAGE PROJECTS (ADD / DELETE)
# ============================================================================
@student_bp.route("/<int:student_id>/projects/add", methods=["POST"])
def add_project(student_id):
    title = request.form.get("project_name", "").strip()   # form sends 'project_name'
    tech_stack = request.form.get("tech_stack", "").strip() or "General"
    description = request.form.get("description", "").strip() or None
    project_url = request.form.get("project_url", "").strip() or None
    raw_start = request.form.get("start_date", "").strip()
    raw_end = request.form.get("end_date", "").strip()

    if not title:
        flash("Project name is required.", "warning")
        return redirect(url_for("students.view_profile", student_id=student_id))

    try:
        start_date = datetime.strptime(raw_start, "%Y-%m-%d").date() if raw_start else None
        end_date = datetime.strptime(raw_end, "%Y-%m-%d").date() if raw_end else None

        if start_date and end_date and end_date < start_date:
            flash("End date cannot precede start date.", "danger")
            return redirect(url_for("students.view_profile", student_id=student_id))

        conn = database.get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO PROJECT (
                    student_id, project_title, tech_stack, description,
                    project_url, start_date, end_date
                ) VALUES (
                    :id, :title, :tech, :descr, :url, :sdate, :edate
                )
            """, id=student_id, title=title, tech=tech_stack, descr=description,
                 url=project_url, sdate=start_date, edate=end_date)
            conn.commit()
        conn.close()
        flash(f"Project '{title}' added!", "success")
    except Exception as e:
        flash(f"Failed to add project: {str(e)}", "danger")

    return redirect(url_for("students.view_profile", student_id=student_id))


@student_bp.route("/<int:student_id>/projects/<int:project_id>/delete", methods=["POST"])
def delete_project(student_id, project_id):
    try:
        conn = database.get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
                DELETE FROM PROJECT
                WHERE project_id = :pid AND student_id = :sid
            """, pid=project_id, sid=student_id)
            conn.commit()
        conn.close()
        flash("Project removed.", "info")
    except Exception as e:
        flash(f"Failed to remove project: {str(e)}", "danger")

    return redirect(url_for("students.view_profile", student_id=student_id))


# ============================================================================
# 9. MANAGE INTERNSHIPS (ADD / DELETE)
# ============================================================================
@student_bp.route("/<int:student_id>/internships/add", methods=["POST"])
def add_internship(student_id):
    company_name = request.form.get("company_name", "").strip()
    role = request.form.get("role", "").strip()
    raw_start = request.form.get("start_date", "").strip()
    raw_end = request.form.get("end_date", "").strip()
    description = request.form.get("description", "").strip() or None
    # NOTE: duration_months and stipend are NOT columns in the INTERNSHIP table

    if not company_name or not role:
        flash("Company Name and Role are required.", "warning")
        return redirect(url_for("students.view_profile", student_id=student_id))

    try:
        start_date = datetime.strptime(raw_start, "%Y-%m-%d").date() if raw_start else None
        end_date = datetime.strptime(raw_end, "%Y-%m-%d").date() if raw_end else None

        if start_date and end_date and end_date < start_date:
            flash("End date cannot precede start date.", "danger")
            return redirect(url_for("students.view_profile", student_id=student_id))

        conn = database.get_db_connection()
        with conn.cursor() as cursor:
            if start_date:
                cursor.execute("""
                    INSERT INTO INTERNSHIP (
                        student_id, company_name, role,
                        start_date, end_date, description
                    ) VALUES (
                        :id, :company, :role, :sdate, :edate, :descr
                    )
                """, id=student_id, company=company_name, role=role,
                     sdate=start_date, edate=end_date, descr=description)
            else:
                # start_date is NOT NULL in schema — use SYSDATE as fallback
                cursor.execute("""
                    INSERT INTO INTERNSHIP (
                        student_id, company_name, role,
                        start_date, end_date, description
                    ) VALUES (
                        :id, :company, :role, SYSDATE, :edate, :descr
                    )
                """, id=student_id, company=company_name, role=role,
                     edate=end_date, descr=description)
            conn.commit()
        conn.close()
        flash(f"Internship at '{company_name}' added!", "success")
    except Exception as e:
        flash(f"Failed to add internship: {str(e)}", "danger")

    return redirect(url_for("students.view_profile", student_id=student_id))


@student_bp.route("/<int:student_id>/internships/<int:internship_id>/delete", methods=["POST"])
def delete_internship(student_id, internship_id):
    try:
        conn = database.get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
                DELETE FROM INTERNSHIP
                WHERE internship_id = :iid AND student_id = :sid
            """, iid=internship_id, sid=student_id)
            conn.commit()
        conn.close()
        flash("Internship record removed.", "info")
    except Exception as e:
        flash(f"Failed to remove internship: {str(e)}", "danger")

    return redirect(url_for("students.view_profile", student_id=student_id))
