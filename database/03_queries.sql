-- ============================================================================
-- CAMPUS PLACEMENT ANALYTICS SYSTEM - PHASE 1: VERIFICATION AND ANALYTICS QUERIES
-- Technology: Oracle SQL / Oracle SQL Developer / SQL*Plus (Oracle 12c/19c/21c/23c)
-- File: 03_queries.sql
-- ============================================================================

SET SQLBLANKLINES ON;
SET DEFINE OFF;
SET PAGESIZE 50;
SET LINESIZE 200;
COLUMN student_name FORMAT A20;
COLUMN email FORMAT A28;
COLUMN company_name FORMAT A22;
COLUMN job_role FORMAT A24;
COLUMN branch FORMAT A8;
COLUMN round_name FORMAT A25;
COLUMN status FORMAT A12;
COLUMN tech_stack FORMAT A35;

-- ============================================================================
-- QUERY 1: DYNAMIC ELIGIBILITY FILTER FOR A SPECIFIC COMPANY
-- Demonstrates per-company custom criteria (CGPA, 10th %, 12th %, Backlogs, Allowed Branches)
-- Example: Students eligible for "Microsoft IDC" (Company ID = 2)
-- ============================================================================
SELECT 
    s.student_id,
    s.student_name,
    s.branch,
    s.cgpa,
    s.tenth_percentage AS "10th %",
    s.twelfth_percentage AS "12th %",
    s.backlogs,
    c.company_name AS "Eligible For",
    c.package AS "Package (LPA)"
FROM STUDENT s
JOIN COMPANY c ON c.company_id = 2 -- Microsoft IDC
WHERE s.cgpa >= c.required_cgpa
  AND s.tenth_percentage >= c.min_tenth_percentage
  AND s.twelfth_percentage >= c.min_twelfth_percentage
  AND s.backlogs <= c.max_backlogs
  AND s.branch IN (
      SELECT cb.branch_name 
      FROM COMPANY_BRANCH cb 
      WHERE cb.company_id = c.company_id
  )
ORDER BY s.cgpa DESC;

-- ============================================================================
-- QUERY 2: GLOBAL ELIGIBILITY MATRIX
-- Shows for each company drive how many total students meet their specific eligibility rules.
-- ============================================================================
SELECT 
    c.company_id,
    c.company_name,
    c.job_role,
    c.required_cgpa AS "Min CGPA",
    c.max_backlogs AS "Max Backlogs",
    c.package AS "Package (LPA)",
    COUNT(s.student_id) AS "Eligible Student Count"
FROM COMPANY c
LEFT JOIN STUDENT s 
    ON s.cgpa >= c.required_cgpa
   AND s.tenth_percentage >= c.min_tenth_percentage
   AND s.twelfth_percentage >= c.min_twelfth_percentage
   AND s.backlogs <= c.max_backlogs
   AND s.branch IN (
       SELECT cb.branch_name 
       FROM COMPANY_BRANCH cb 
       WHERE cb.company_id = c.company_id
   )
GROUP BY c.company_id, c.company_name, c.job_role, c.required_cgpa, c.max_backlogs, c.package
ORDER BY c.package DESC;

-- ============================================================================
-- QUERY 3: SKILL GAP ANALYSIS FOR AN APPLICANT
-- Compares skills required by a company against skills possessed by a student.
-- Identifies matching skills and missing skills.
-- Example: Student 3 (Rohan Verma) applying to Company 2 (Microsoft IDC)
-- ============================================================================
SELECT 
    req.skill_name AS "Required Skill",
    req.min_proficiency AS "Min Level Needed",
    NVL(stud.proficiency_level, 'MISSING') AS "Student Proficiency",
    CASE 
        WHEN stud.skill_name IS NOT NULL THEN 'MATCH'
        ELSE 'SKILL GAP (Needs Training)'
    END AS "Match Status"
FROM COMPANY_SKILL req
LEFT JOIN STUDENT_SKILL stud 
    ON req.skill_name = stud.skill_name 
   AND stud.student_id = 3 -- Rohan Verma
WHERE req.company_id = 2   -- Microsoft IDC
ORDER BY "Match Status" ASC;

-- ============================================================================
-- QUERY 4: COMPLETE APPLICATION AND INTERVIEW PROGRESSION FUNNEL
-- Displays student details, company, current application status, interview rounds, and scores.
-- ============================================================================
SELECT 
    s.student_name,
    s.branch,
    c.company_name,
    a.application_date,
    a.status AS "App Status",
    i.round_number AS "Round",
    i.round_name,
    i.score,
    i.status AS "Round Status"
FROM APPLICATION a
JOIN STUDENT s ON a.student_id = s.student_id
JOIN COMPANY c ON a.company_id = c.company_id
LEFT JOIN INTERVIEW i ON a.application_id = i.application_id
ORDER BY s.student_name, a.application_id, i.round_number;

-- ============================================================================
-- QUERY 5: DEPARTMENT-WISE (BRANCH-WISE) PLACEMENT ANALYTICS
-- Calculates total registered students, placed count, placement %, max package, and average package.
-- ============================================================================
SELECT 
    s.branch,
    COUNT(s.student_id) AS "Total Students",
    COUNT(p.placement_id) AS "Placed Students",
    ROUND((COUNT(p.placement_id) / COUNT(s.student_id)) * 100, 2) AS "Placement %",
    NVL(MAX(p.package_offered), 0.00) AS "Highest Package (LPA)",
    NVL(ROUND(AVG(p.package_offered), 2), 0.00) AS "Avg Package (LPA)"
FROM STUDENT s
LEFT JOIN PLACEMENT p ON s.student_id = p.student_id AND p.acceptance_status = 'Accepted'
GROUP BY s.branch
ORDER BY "Placement %" DESC, "Avg Package (LPA)" DESC;

-- ============================================================================
-- QUERY 6: FINAL PLACEMENT ROLL SHEET
-- Complete list of placed students with their packages, companies, and roles.
-- ============================================================================
SELECT 
    p.placement_id,
    s.student_name,
    s.branch,
    s.cgpa,
    c.company_name,
    c.job_role,
    p.package_offered AS "Package (LPA)",
    p.offer_date,
    p.acceptance_status,
    p.joining_date
FROM PLACEMENT p
JOIN STUDENT s ON p.student_id = s.student_id
JOIN COMPANY c ON p.company_id = c.company_id
ORDER BY p.package_offered DESC;

-- ============================================================================
-- QUERY 7: UNPLACED HIGH-PERFORMERS ACTION LIST
-- Identifies unplaced students with high CGPA (>= 7.50) so placement officers can target them for upcoming drives.
-- ============================================================================
SELECT 
    s.student_id,
    s.student_name,
    s.branch,
    s.cgpa,
    s.backlogs,
    s.email,
    s.phone
FROM STUDENT s
WHERE s.student_id NOT IN (
    SELECT student_id 
    FROM PLACEMENT 
    WHERE acceptance_status = 'Accepted'
)
AND s.cgpa >= 7.50
ORDER BY s.cgpa DESC;

-- ============================================================================
-- QUERY 8: COMPANY DRIVE PERFORMANCE SUMMARY
-- Recaps drives, showing applicants, interviewees, and final hiring counts.
-- ============================================================================
SELECT 
    c.company_name,
    c.job_role,
    c.package AS "Offered CTC (LPA)",
    COUNT(DISTINCT a.application_id) AS "Total Applicants",
    COUNT(DISTINCT p.placement_id) AS "Total Hires"
FROM COMPANY c
LEFT JOIN APPLICATION a ON c.company_id = a.company_id
LEFT JOIN PLACEMENT p ON c.company_id = p.company_id AND p.acceptance_status = 'Accepted'
GROUP BY c.company_id, c.company_name, c.job_role, c.package
ORDER BY "Total Hires" DESC, c.package DESC;
