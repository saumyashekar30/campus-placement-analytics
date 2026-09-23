"""
Campus Placement Analytics System - Company Management Blueprint
Phase 4: Company Management & Company-Specific Eligibility Criteria
"""

from datetime import datetime
from decimal import Decimal
from flask import Blueprint, render_template, request, redirect, url_for, flash
import database
import oracledb

company_bp = Blueprint("companies", __name__, url_prefix="/companies")


def _convert_value(v):
    """Convert Oracle types (Decimal, datetime) to Python-native types for Jinja2 compatibility."""
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
# 1. VIEW ALL COMPANIES (LIST VIEW)
# ============================================================================
@company_bp.route("")
def list_companies():
    """
    Renders the company placement drives list showing:
    Company ID, Company Name, Job Role, Package (CTC), Required CGPA,
    Min 10th %, Min 12th %, Max Backlogs, Application Deadline, and Action buttons.
    """
    companies = []
    error_message = None

    try:
        conn = database.get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT company_id, company_name, job_role, required_cgpa,
                       min_tenth_percentage, min_twelfth_percentage, max_backlogs,
                       package, application_deadline, drive_date
                FROM COMPANY
                ORDER BY company_id
            """)
            companies = _rows_to_dicts(cursor, cursor.fetchall())
        conn.close()
    except Exception as e:
        error_message = f"Error fetching company records: {str(e)}"
        print(f"[ERROR] {error_message}")

    return render_template(
        "companies/companies.html",
        companies=companies,
        error_message=error_message
    )


# ============================================================================
# 2. ADD COMPANY / JOB DRIVE (FORM & SUBMISSION)
# ============================================================================
@company_bp.route("/add", methods=["GET", "POST"])
def add_company():
    """
    GET: Displays the company drive creation form.
    POST: Validates inputs and inserts records into COMPANY, COMPANY_BRANCH, and COMPANY_SKILL.
    """
    if request.method == "GET":
        return render_template("companies/add_company.html")

    # Extract inputs
    company_name = request.form.get("company_name", "").strip()
    job_role = request.form.get("job_role", "").strip()
    raw_cgpa = request.form.get("required_cgpa", "").strip()
    raw_tenth = request.form.get("min_tenth_percentage", "").strip()
    raw_twelfth = request.form.get("min_twelfth_percentage", "").strip()
    raw_backlogs = request.form.get("max_backlogs", "").strip()
    raw_package = request.form.get("package", "").strip()
    job_description = request.form.get("job_description", "").strip() or None
    raw_deadline = request.form.get("application_deadline", "").strip()
    raw_drive_date = request.form.get("drive_date", "").strip()

    # Branches selected (checkboxes)
    branches = request.form.getlist("branches")

    # Initial skills entered (optional comma-separated or newline-separated)
    raw_skills = request.form.get("skills_text", "").strip()

    errors = []

    # 1. Validate Company Name
    if not company_name or len(company_name) < 2:
        errors.append("Company Name is required (minimum 2 characters).")

    # 2. Validate Job Role
    if not job_role or len(job_role) < 2:
        errors.append("Job Role is required (minimum 2 characters).")

    # 3. Validate Required CGPA (0.00 to 10.00)
    cgpa = 0.0
    try:
        cgpa = float(raw_cgpa)
        if cgpa < 0.0 or cgpa > 10.0:
            errors.append("Required CGPA must be between 0.00 and 10.00.")
    except (ValueError, TypeError):
        errors.append("A valid numeric CGPA is required (0.00 - 10.00).")

    # 4. Validate Min 10th % (0.00 to 100.00)
    tenth = 0.0
    try:
        tenth = float(raw_tenth)
        if tenth < 0.0 or tenth > 100.0:
            errors.append("Minimum 10th percentage must be between 0.00% and 100.00%.")
    except (ValueError, TypeError):
        errors.append("A valid 10th percentage is required (0.00 - 100.00).")

    # 5. Validate Min 12th % (0.00 to 100.00)
    twelfth = 0.0
    try:
        twelfth = float(raw_twelfth)
        if twelfth < 0.0 or twelfth > 100.0:
            errors.append("Minimum 12th percentage must be between 0.00% and 100.00%.")
    except (ValueError, TypeError):
        errors.append("A valid 12th percentage is required (0.00 - 100.00).")

    # 6. Validate Max Backlogs (>= 0)
    backlogs = 0
    try:
        backlogs = int(raw_backlogs)
        if backlogs < 0:
            errors.append("Max Backlogs cannot be negative.")
    except (ValueError, TypeError):
        errors.append("A valid non-negative integer is required for backlogs.")

    # 7. Validate Package (>= 0)
    package = 0.0
    try:
        package = float(raw_package)
        if package < 0.0:
            errors.append("Package cannot be negative.")
    except (ValueError, TypeError):
        errors.append("A valid positive numeric package (CTC in LPA) is required.")

    # 8. Validate Deadline
    deadline = None
    if not raw_deadline:
        errors.append("Application deadline is required.")
    else:
        try:
            deadline = datetime.strptime(raw_deadline, "%Y-%m-%d").date()
        except ValueError:
            errors.append("Application deadline must be a valid date in YYYY-MM-DD format.")

    # Optional Drive Date
    drive_date = None
    if raw_drive_date:
        try:
            drive_date = datetime.strptime(raw_drive_date, "%Y-%m-%d").date()
            if deadline and drive_date < deadline:
                errors.append("Drive date cannot precede application deadline.")
        except ValueError:
            errors.append("Drive date must be a valid date in YYYY-MM-DD format.")

    # 9. Validate Branches (at least one required)
    clean_branches = [b.strip().upper() for b in branches if b.strip()]
    if not clean_branches:
        errors.append("At least one allowed branch must be selected.")

    if errors:
        for err in errors:
            flash(err, "danger")
        return render_template("companies/add_company.html", form=request.form, selected_branches=branches), 400

    try:
        conn = database.get_db_connection()
        with conn.cursor() as cursor:
            # Determine next sequential company_id
            cursor.execute("SELECT NVL(MAX(company_id), 0) + 1 FROM COMPANY")
            company_id = int(cursor.fetchone()[0])

            insert_company_sql = """
                INSERT INTO COMPANY (
                    company_id, company_name, job_role, required_cgpa,
                    min_tenth_percentage, min_twelfth_percentage,
                    max_backlogs, package, job_description,
                    application_deadline, drive_date
                ) VALUES (
                    :id, :name, :role, :cgpa,
                    :tenth, :twelfth,
                    :backlogs, :pkg, :descr,
                    :deadline, :drive_date
                )
            """
            cursor.execute(
                insert_company_sql,
                id=company_id, name=company_name, role=job_role, cgpa=cgpa,
                tenth=tenth, twelfth=twelfth,
                backlogs=backlogs, pkg=package, descr=job_description,
                deadline=deadline, drive_date=drive_date
            )

            # Insert normalized COMPANY_BRANCH records
            for br in clean_branches:
                cursor.execute("""
                    INSERT INTO COMPANY_BRANCH (company_id, branch_name)
                    VALUES (:cid, :bname)
                """, cid=company_id, bname=br)

            # Insert initial skills if provided (comma-separated: e.g. "Python, SQL, C++")
            if raw_skills:
                skill_list = [s.strip() for s in raw_skills.replace("\n", ",").split(",") if s.strip()]
                seen_skills = set()
                for sk in skill_list:
                    sk_normalized = sk[:50]
                    if sk_normalized.lower() not in seen_skills:
                        seen_skills.add(sk_normalized.lower())
                        cursor.execute("""
                            INSERT INTO COMPANY_SKILL (company_id, skill_name, min_proficiency)
                            VALUES (:cid, :sname, 'Intermediate')
                        """, cid=company_id, sname=sk_normalized)

            conn.commit()
        conn.close()

        flash(f"Company drive '{company_name}' successfully added!", "success")
        return redirect(url_for("companies.view_company", company_id=company_id))

    except oracledb.DatabaseError as db_err:
        error_obj, = db_err.args
        flash(f"Oracle Database Error: {error_obj.message}", "danger")
        return render_template("companies/add_company.html", form=request.form, selected_branches=branches), 500
    except Exception as ex:
        flash(f"Unexpected Error: {str(ex)}", "danger")
        return render_template("companies/add_company.html", form=request.form, selected_branches=branches), 500


# ============================================================================
# 3. VIEW COMPANY DETAILS & ELIGIBILITY CRITERIA (DASHBOARD VIEW)
# ============================================================================
@company_bp.route("/<int:company_id>")
def view_company(company_id):
    """
    Displays complete company drive details and company-specific eligibility criteria:
    - Company details (Name, Role, Package, Description, Application Deadline, Drive Date)
    - Academic eligibility cutoffs (Required CGPA, 10th %, 12th %, Max Backlogs)
    - Normalized allowed branches (COMPANY_BRANCH)
    - Normalized required skills and proficiency (COMPANY_SKILL)
    """
    company = None
    branches = []
    skills = []
    applications = []

    try:
        conn = database.get_db_connection()
        with conn.cursor() as cursor:
            # 1. Fetch Company Core Details
            cursor.execute("""
                SELECT company_id, company_name, job_role, required_cgpa,
                       min_tenth_percentage, min_twelfth_percentage, max_backlogs,
                       package, job_description, application_deadline, drive_date
                FROM COMPANY
                WHERE company_id = :id
            """, id=company_id)
            company = _row_to_dict(cursor, cursor.fetchone())

            if not company:
                conn.close()
                flash(f"Company #{company_id} not found.", "warning")
                return redirect(url_for("companies.list_companies"))

            # 2. Fetch Allowed Branches (COMPANY_BRANCH)
            cursor.execute("""
                SELECT branch_name
                FROM COMPANY_BRANCH
                WHERE company_id = :id
                ORDER BY branch_name
            """, id=company_id)
            branches = [row[0] for row in cursor.fetchall()]

            # 3. Fetch Required Skills (COMPANY_SKILL)
            cursor.execute("""
                SELECT skill_name, min_proficiency
                FROM COMPANY_SKILL
                WHERE company_id = :id
                ORDER BY skill_name
            """, id=company_id)
            skills = _rows_to_dicts(cursor, cursor.fetchall())

            # 4. Fetch Applications / Applicants (Phase 6)
            cursor.execute("""
                SELECT a.application_id, a.student_id, s.student_name, s.branch,
                       s.cgpa, a.application_date, a.status
                FROM APPLICATION a
                JOIN STUDENT s ON a.student_id = s.student_id
                WHERE a.company_id = :id
                ORDER BY a.application_date DESC, a.application_id DESC
            """, id=company_id)
            applications = _rows_to_dicts(cursor, cursor.fetchall())

        conn.close()
    except Exception as e:
        flash(f"Error loading company profile: {str(e)}", "danger")
        return redirect(url_for("companies.list_companies"))

    return render_template(
        "companies/company_profile.html",
        company=company,
        branches=branches,
        skills=skills,
        applications=applications
    )


# ============================================================================
# 4. EDIT COMPANY (FORM & SUBMISSION)
# ============================================================================
@company_bp.route("/<int:company_id>/edit", methods=["GET", "POST"])
def edit_company(company_id):
    """
    GET: Displays pre-filled edit form with current criteria and checked branches.
    POST: Validates inputs, updates COMPANY table, and synchronizes COMPANY_BRANCH records.
    """
    conn = database.get_db_connection()

    if request.method == "GET":
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT company_id, company_name, job_role, required_cgpa,
                           min_tenth_percentage, min_twelfth_percentage, max_backlogs,
                           package, job_description, application_deadline, drive_date
                    FROM COMPANY
                    WHERE company_id = :id
                """, id=company_id)
                company = _row_to_dict(cursor, cursor.fetchone())

                if not company:
                    conn.close()
                    flash(f"Company #{company_id} not found.", "warning")
                    return redirect(url_for("companies.list_companies"))

                cursor.execute("""
                    SELECT branch_name FROM COMPANY_BRANCH
                    WHERE company_id = :id
                    ORDER BY branch_name
                """, id=company_id)
                current_branches = [row[0] for row in cursor.fetchall()]

            conn.close()
            return render_template("companies/edit_company.html", company=company, selected_branches=current_branches)
        except Exception as e:
            conn.close()
            flash(f"Error loading company: {str(e)}", "danger")
            return redirect(url_for("companies.list_companies"))

    # POST Update
    company_name = request.form.get("company_name", "").strip()
    job_role = request.form.get("job_role", "").strip()
    raw_cgpa = request.form.get("required_cgpa", "").strip()
    raw_tenth = request.form.get("min_tenth_percentage", "").strip()
    raw_twelfth = request.form.get("min_twelfth_percentage", "").strip()
    raw_backlogs = request.form.get("max_backlogs", "").strip()
    raw_package = request.form.get("package", "").strip()
    job_description = request.form.get("job_description", "").strip() or None
    raw_deadline = request.form.get("application_deadline", "").strip()
    raw_drive_date = request.form.get("drive_date", "").strip()
    branches = request.form.getlist("branches")

    errors = []

    if not company_name or len(company_name) < 2:
        errors.append("Company Name is required.")

    if not job_role or len(job_role) < 2:
        errors.append("Job Role is required.")

    try:
        cgpa = float(raw_cgpa)
        if cgpa < 0.0 or cgpa > 10.0:
            errors.append("Required CGPA must be between 0.00 and 10.00.")
    except (ValueError, TypeError):
        errors.append("Valid numeric CGPA is required.")

    try:
        tenth = float(raw_tenth)
        if tenth < 0.0 or tenth > 100.0:
            errors.append("Minimum 10th percentage must be between 0.00% and 100.00%.")
    except (ValueError, TypeError):
        errors.append("Valid 10th percentage is required.")

    try:
        twelfth = float(raw_twelfth)
        if twelfth < 0.0 or twelfth > 100.0:
            errors.append("Minimum 12th percentage must be between 0.00% and 100.00%.")
    except (ValueError, TypeError):
        errors.append("Valid 12th percentage is required.")

    try:
        backlogs = int(raw_backlogs)
        if backlogs < 0:
            errors.append("Max Backlogs cannot be negative.")
    except (ValueError, TypeError):
        errors.append("Valid non-negative integer is required for backlogs.")

    try:
        package = float(raw_package)
        if package < 0.0:
            errors.append("Package cannot be negative.")
    except (ValueError, TypeError):
        errors.append("Valid positive numeric package (CTC) is required.")

    deadline = None
    if not raw_deadline:
        errors.append("Application deadline is required.")
    else:
        try:
            deadline = datetime.strptime(raw_deadline, "%Y-%m-%d").date()
        except ValueError:
            errors.append("Invalid application deadline date.")

    drive_date = None
    if raw_drive_date:
        try:
            drive_date = datetime.strptime(raw_drive_date, "%Y-%m-%d").date()
            if deadline and drive_date < deadline:
                errors.append("Drive date cannot precede application deadline.")
        except ValueError:
            errors.append("Invalid drive date.")

    clean_branches = [b.strip().upper() for b in branches if b.strip()]
    if not clean_branches:
        errors.append("At least one allowed branch must be selected.")

    if errors:
        for err in errors:
            flash(err, "danger")
        company_data = dict(request.form)
        company_data["company_id"] = company_id
        conn.close()
        return render_template("companies/edit_company.html", company=company_data, selected_branches=branches), 400

    try:
        with conn.cursor() as cursor:
            # 1. Update COMPANY record
            cursor.execute("""
                UPDATE COMPANY
                SET company_name = :name,
                    job_role = :role,
                    required_cgpa = :cgpa,
                    min_tenth_percentage = :tenth,
                    min_twelfth_percentage = :twelfth,
                    max_backlogs = :backlogs,
                    package = :pkg,
                    job_description = :descr,
                    application_deadline = :deadline,
                    drive_date = :drive_date
                WHERE company_id = :id
            """, name=company_name, role=job_role, cgpa=cgpa,
                 tenth=tenth, twelfth=twelfth, backlogs=backlogs,
                 pkg=package, descr=job_description,
                 deadline=deadline, drive_date=drive_date, id=company_id)

            # 2. Synchronize COMPANY_BRANCH: Remove unselected, add new
            cursor.execute("SELECT branch_name FROM COMPANY_BRANCH WHERE company_id = :id", id=company_id)
            existing_branches = {row[0] for row in cursor.fetchall()}
            new_branches = set(clean_branches)

            to_remove = existing_branches - new_branches
            to_add = new_branches - existing_branches

            for br in to_remove:
                cursor.execute("""
                    DELETE FROM COMPANY_BRANCH
                    WHERE company_id = :id AND branch_name = :bname
                """, id=company_id, bname=br)

            for br in to_add:
                cursor.execute("""
                    INSERT INTO COMPANY_BRANCH (company_id, branch_name)
                    VALUES (:id, :bname)
                """, id=company_id, bname=br)

            conn.commit()
        conn.close()

        flash(f"Company drive #{company_id} ('{company_name}') updated successfully!", "success")
        return redirect(url_for("companies.view_company", company_id=company_id))

    except Exception as ex:
        conn.close()
        flash(f"Update failed: {str(ex)}", "danger")
        return redirect(url_for("companies.edit_company", company_id=company_id))


# ============================================================================
# 5. DELETE COMPANY (CASCADE SAFEGUARD)
# ============================================================================
@company_bp.route("/<int:company_id>/delete", methods=["POST"])
def delete_company(company_id):
    """
    Deletes the company record from Oracle COMPANY table.
    Foreign key child records (COMPANY_BRANCH, COMPANY_SKILL, APPLICATION, PLACEMENT)
    are automatically cascaded via Oracle ON DELETE CASCADE constraints.
    """
    try:
        conn = database.get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT company_name FROM COMPANY WHERE company_id = :id", id=company_id)
            row = cursor.fetchone()
            company_name = row[0] if row else f"#{company_id}"

            cursor.execute("DELETE FROM COMPANY WHERE company_id = :id", id=company_id)
            conn.commit()
        conn.close()
        flash(f"Company '{company_name}' and all associated criteria have been deleted.", "info")
    except oracledb.IntegrityError as ie:
        flash(f"Cannot delete company due to database constraint: {str(ie)}", "danger")
    except Exception as e:
        flash(f"Delete failed: {str(e)}", "danger")

    return redirect(url_for("companies.list_companies"))


# ============================================================================
# 6. MANAGE ALLOWED BRANCHES (INLINE ADD / DELETE)
# ============================================================================
@company_bp.route("/<int:company_id>/branches/add", methods=["POST"])
def add_branch(company_id):
    """Add a new allowed branch for this company."""
    branch = request.form.get("branch_name", "").strip().upper()
    if not branch:
        flash("Branch name is required.", "warning")
        return redirect(url_for("companies.view_company", company_id=company_id))

    try:
        conn = database.get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO COMPANY_BRANCH (company_id, branch_name)
                VALUES (:id, :bname)
            """, id=company_id, bname=branch)
            conn.commit()
        conn.close()
        flash(f"Branch '{branch}' added to allowed branches!", "success")
    except oracledb.IntegrityError:
        flash(f"Branch '{branch}' is already allowed for this company.", "warning")
    except Exception as e:
        flash(f"Failed to add branch: {str(e)}", "danger")

    return redirect(url_for("companies.view_company", company_id=company_id))


@company_bp.route("/<int:company_id>/branches/delete", methods=["POST"])
@company_bp.route("/<int:company_id>/branches/<string:branch>/delete", methods=["POST"])
def delete_branch(company_id, branch=None):
    """Delete an allowed branch (via URL param or POST body)."""
    branch_name = branch or request.form.get("branch_name", "").strip().upper()
    if not branch_name:
        flash("No branch specified for deletion.", "warning")
        return redirect(url_for("companies.view_company", company_id=company_id))

    try:
        conn = database.get_db_connection()
        with conn.cursor() as cursor:
            # Check how many branches are remaining (company should have at least 1)
            cursor.execute("SELECT COUNT(*) FROM COMPANY_BRANCH WHERE company_id = :id", id=company_id)
            count = cursor.fetchone()[0]
            if count <= 1:
                flash("Cannot remove branch. A company drive must have at least one allowed branch.", "warning")
                conn.close()
                return redirect(url_for("companies.view_company", company_id=company_id))

            cursor.execute("""
                DELETE FROM COMPANY_BRANCH
                WHERE company_id = :id AND branch_name = :bname
            """, id=company_id, bname=branch_name)
            conn.commit()
        conn.close()
        flash(f"Branch '{branch_name}' removed.", "info")
    except Exception as e:
        flash(f"Failed to remove branch: {str(e)}", "danger")

    return redirect(url_for("companies.view_company", company_id=company_id))


# ============================================================================
# 7. MANAGE REQUIRED SKILLS (INLINE ADD / DELETE)
# ============================================================================
@company_bp.route("/<int:company_id>/skills/add", methods=["POST"])
def add_skill(company_id):
    """Add a required skill and minimum proficiency level for this company."""
    skill_name = request.form.get("skill_name", "").strip()
    proficiency = request.form.get("min_proficiency", "Intermediate").strip()

    if not skill_name:
        flash("Skill name is required.", "warning")
        return redirect(url_for("companies.view_company", company_id=company_id))

    if proficiency not in ["Beginner", "Intermediate", "Advanced", "Expert"]:
        proficiency = "Intermediate"

    try:
        conn = database.get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO COMPANY_SKILL (company_id, skill_name, min_proficiency)
                VALUES (:id, :sname, :prof)
            """, id=company_id, sname=skill_name, prof=proficiency)
            conn.commit()
        conn.close()
        flash(f"Required skill '{skill_name}' ({proficiency}) added!", "success")
    except oracledb.IntegrityError:
        flash(f"Skill '{skill_name}' is already listed for this company.", "warning")
    except Exception as e:
        flash(f"Failed to add skill: {str(e)}", "danger")

    return redirect(url_for("companies.view_company", company_id=company_id))


@company_bp.route("/<int:company_id>/skills/delete", methods=["POST"])
@company_bp.route("/<int:company_id>/skills/<string:skill_name>/delete", methods=["POST"])
def delete_skill(company_id, skill_name=None):
    """Delete a required skill (via URL param or POST body)."""
    target_skill = skill_name or request.form.get("skill_name", "").strip()
    if not target_skill:
        flash("No skill specified for deletion.", "warning")
        return redirect(url_for("companies.view_company", company_id=company_id))

    try:
        conn = database.get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
                DELETE FROM COMPANY_SKILL
                WHERE company_id = :id AND skill_name = :sname
            """, id=company_id, sname=target_skill)
            conn.commit()
        conn.close()
        flash(f"Skill '{target_skill}' removed from requirements.", "info")
    except Exception as e:
        flash(f"Failed to remove skill: {str(e)}", "danger")

    return redirect(url_for("companies.view_company", company_id=company_id))
