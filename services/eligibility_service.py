"""
Campus Placement Analytics System - Eligibility Service
Phase 5: Student Eligibility Checking Module

Separates all dynamic, company-specific eligibility logic from Flask controllers.
Evaluates 6 independent criteria:
1. Minimum Required CGPA
2. Minimum 10th Board Percentage
3. Minimum 12th Board Percentage
4. Maximum Allowed Active Backlogs
5. Allowed Engineering Branches (Normalized from COMPANY_BRANCH)
6. Required Technical Skills (Normalized from COMPANY_SKILL, matched case-insensitively)
"""

from decimal import Decimal
import database


def _to_python(v):
    """Convert Oracle Decimal types to Python float for clean formatting."""
    if isinstance(v, Decimal):
        return float(v)
    return v


def _row_to_dict(cursor, row):
    """Convert Oracle query row to a lowercase dictionary."""
    if not row:
        return None
    cols = [col[0].lower() for col in cursor.description]
    return {k: _to_python(v) for k, v in zip(cols, row)}


def check_eligibility(student_id, company_id):
    """
    Evaluates whether a student satisfies the eligibility criteria of a specific company drive.

    Returns a structured dictionary:
    {
        "student": {...},
        "company": {...},
        "checks": {
            "cgpa": {"student_value": float, "required_value": float, "status": "PASS"|"FAIL"},
            "tenth": {"student_value": float, "required_value": float, "status": "PASS"|"FAIL"},
            "twelfth": {"student_value": float, "required_value": float, "status": "PASS"|"FAIL"},
            "backlogs": {"student_value": int, "required_value": int, "status": "PASS"|"FAIL"},
            "branch": {"student_value": str, "required_value": list, "status": "PASS"|"FAIL"},
            "skills": {"required": list, "matched": list, "missing": list, "status": "PASS"|"FAIL"}
        },
        "overall_status": "ELIGIBLE" | "NOT ELIGIBLE",
        "reasons": [str, ...]
    }
    """
    conn = database.get_db_connection()
    try:
        with conn.cursor() as cursor:
            # 1. Fetch Student Core Details
            cursor.execute("""
                SELECT student_id, student_name, email, phone, branch,
                       cgpa, tenth_percentage, twelfth_percentage, backlogs
                FROM STUDENT
                WHERE student_id = :sid
            """, sid=student_id)
            student = _row_to_dict(cursor, cursor.fetchone())
            if not student:
                raise ValueError(f"Student #{student_id} not found in database.")

            # 2. Fetch Student Skills
            cursor.execute("""
                SELECT skill_name, proficiency_level
                FROM STUDENT_SKILL
                WHERE student_id = :sid
                ORDER BY skill_name
            """, sid=student_id)
            student_skill_rows = cursor.fetchall()
            # Mapping from normalized (lowercase stripped) to display name
            student_skills = [row[0] for row in student_skill_rows]
            student_skills_map = {s.strip().lower(): s.strip() for s in student_skills}

            # 3. Fetch Company Core Details
            cursor.execute("""
                SELECT company_id, company_name, job_role, required_cgpa,
                       min_tenth_percentage, min_twelfth_percentage, max_backlogs,
                       package, job_description, application_deadline, drive_date
                FROM COMPANY
                WHERE company_id = :cid
            """, cid=company_id)
            company = _row_to_dict(cursor, cursor.fetchone())
            if not company:
                raise ValueError(f"Company #{company_id} not found in database.")

            # 4. Fetch Allowed Branches (COMPANY_BRANCH)
            cursor.execute("""
                SELECT branch_name
                FROM COMPANY_BRANCH
                WHERE company_id = :cid
                ORDER BY branch_name
            """, cid=company_id)
            allowed_branches = [row[0] for row in cursor.fetchall()]

            # 5. Fetch Required Skills (COMPANY_SKILL)
            cursor.execute("""
                SELECT skill_name, min_proficiency
                FROM COMPANY_SKILL
                WHERE company_id = :cid
                ORDER BY skill_name
            """, cid=company_id)
            required_skills_data = cursor.fetchall()
            required_skills = [row[0] for row in required_skills_data]
            required_skills_with_prof = [
                {"skill_name": row[0], "min_proficiency": row[1]} for row in required_skills_data
            ]

    finally:
        conn.close()

    # =========================================================================
    # DYNAMIC ELIGIBILITY EVALUATION (NO GLOBAL RULES)
    # =========================================================================
    reasons = []

    # 1. CGPA Check
    cgpa_pass = student["cgpa"] >= company["required_cgpa"]
    cgpa_check = {
        "student_value": student["cgpa"],
        "required_value": company["required_cgpa"],
        "status": "PASS" if cgpa_pass else "FAIL"
    }
    if not cgpa_pass:
        reasons.append(
            f"CGPA is below the required cutoff (Student: {student['cgpa']:.2f}, Required: \u2265 {company['required_cgpa']:.2f})."
        )

    # 2. 10th Percentage Check
    tenth_pass = student["tenth_percentage"] >= company["min_tenth_percentage"]
    tenth_check = {
        "student_value": student["tenth_percentage"],
        "required_value": company["min_tenth_percentage"],
        "status": "PASS" if tenth_pass else "FAIL"
    }
    if not tenth_pass:
        reasons.append(
            f"10th Board score is below the required minimum (Student: {student['tenth_percentage']:.1f}%, Required: \u2265 {company['min_tenth_percentage']:.1f}%)."
        )

    # 3. 12th Percentage Check
    twelfth_pass = student["twelfth_percentage"] >= company["min_twelfth_percentage"]
    twelfth_check = {
        "student_value": student["twelfth_percentage"],
        "required_value": company["min_twelfth_percentage"],
        "status": "PASS" if twelfth_pass else "FAIL"
    }
    if not twelfth_pass:
        reasons.append(
            f"12th Board score is below the required minimum (Student: {student['twelfth_percentage']:.1f}%, Required: \u2265 {company['min_twelfth_percentage']:.1f}%)."
        )

    # 4. Backlogs Check
    backlogs_pass = student["backlogs"] <= company["max_backlogs"]
    backlogs_check = {
        "student_value": student["backlogs"],
        "required_value": company["max_backlogs"],
        "status": "PASS" if backlogs_pass else "FAIL"
    }
    if not backlogs_pass:
        reasons.append(
            f"Active backlogs exceed maximum allowed (Student: {student['backlogs']}, Allowed: \u2264 {company['max_backlogs']})."
        )

    # 5. Branch Check (Case-insensitive comparison)
    # If company has no branch restrictions configured, all branches pass.
    if allowed_branches:
        allowed_normalized = {b.strip().upper() for b in allowed_branches}
        branch_pass = student["branch"].strip().upper() in allowed_normalized
    else:
        branch_pass = True

    branch_check = {
        "student_value": student["branch"],
        "required_value": allowed_branches if allowed_branches else ["Any Branch Allowed"],
        "status": "PASS" if branch_pass else "FAIL"
    }
    if not branch_pass:
        allowed_str = ", ".join(allowed_branches)
        reasons.append(
            f"Student's branch ({student['branch']}) is not in the company's allowed branches ({allowed_str})."
        )

    # 6. Technical Skills Check (Case-insensitive, trimmed comparison)
    # If company has no specific required skills, skill check passes.
    matched_skills = []
    missing_skills = []

    if required_skills:
        for req in required_skills:
            req_clean = req.strip()
            if req_clean.lower() in student_skills_map:
                matched_skills.append(req_clean)
            else:
                missing_skills.append(req_clean)
        skills_pass = len(missing_skills) == 0
    else:
        skills_pass = True

    skills_check = {
        "required": required_skills,
        "required_with_prof": required_skills_with_prof,
        "student_skills": student_skills,
        "matched": matched_skills,
        "missing": missing_skills,
        "status": "PASS" if skills_pass else "FAIL"
    }
    if not skills_pass:
        missing_str = ", ".join(missing_skills)
        reasons.append(
            f"Missing required technical skill(s): {missing_str}."
        )

    # =========================================================================
    # OVERALL ELIGIBILITY DETERMINATION
    # =========================================================================
    all_passed = (
        cgpa_pass and
        tenth_pass and
        twelfth_pass and
        backlogs_pass and
        branch_pass and
        skills_pass
    )

    overall_status = "ELIGIBLE" if all_passed else "NOT ELIGIBLE"

    return {
        "student": student,
        "company": company,
        "checks": {
            "cgpa": cgpa_check,
            "tenth": tenth_check,
            "twelfth": twelfth_check,
            "backlogs": backlogs_check,
            "branch": branch_check,
            "skills": skills_check
        },
        "overall_status": overall_status,
        "reasons": reasons
    }
