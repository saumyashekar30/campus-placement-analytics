-- ============================================================================
-- CAMPUS PLACEMENT ANALYTICS SYSTEM - PHASE 7: ADVANCED ANALYTICS QUERIES
-- Technology: Oracle SQL / Oracle SQL Developer / SQL*Plus (Oracle 12c/19c/21c/23c)
-- File: 04_analytics_queries.sql
-- ============================================================================

SET SQLBLANKLINES ON;
SET DEFINE OFF;
SET PAGESIZE 50;
SET LINESIZE 200;
COLUMN metric_name FORMAT A32;
COLUMN metric_value FORMAT A20;
COLUMN branch FORMAT A10;
COLUMN status FORMAT A15;
COLUMN company_name FORMAT A25;
COLUMN job_role FORMAT A28;

-- ============================================================================
-- QUERY 1: TOTAL REGISTERED STUDENTS
-- Calculates the total count of registered student profiles in the system.
-- Enforces uniqueness using COUNT(DISTINCT student_id).
-- ============================================================================
SELECT 
    COUNT(DISTINCT student_id) AS total_registered_students
FROM STUDENT;

-- ============================================================================
-- QUERY 2: UNIQUELY PLACED STUDENTS & OVERALL PLACEMENT PERCENTAGE
-- Calculates the total count of unique students who have secured and accepted
-- an offer, along with unplaced student count and overall placement percentage.
-- Safe zero-division handling included.
-- ============================================================================
SELECT 
    COUNT(DISTINCT s.student_id) AS total_students,
    COUNT(DISTINCT p.student_id) AS uniquely_placed_students,
    (COUNT(DISTINCT s.student_id) - COUNT(DISTINCT p.student_id)) AS unplaced_students,
    CASE 
        WHEN COUNT(DISTINCT s.student_id) = 0 THEN 0.00
        ELSE ROUND((COUNT(DISTINCT p.student_id) * 100.0) / COUNT(DISTINCT s.student_id), 2)
    END AS placement_percentage
FROM STUDENT s
LEFT JOIN PLACEMENT p 
    ON s.student_id = p.student_id 
   AND p.acceptance_status = 'Accepted';

-- ============================================================================
-- QUERY 3: TOTAL APPLICATIONS SUBMITTED
-- Counts the grand total of student applications submitted across all drives.
-- ============================================================================
SELECT 
    COUNT(*) AS total_applications_submitted
FROM APPLICATION;

-- ============================================================================
-- QUERY 4: APPLICATION STATUS METRICS (SELECTED, REJECTED, PENDING)
-- Aggregates applications into key operational categories:
-- - Selected: Candidate cleared all rounds and was selected
-- - Rejected: Application rejected
-- - Pending: Active pipeline in progress (Applied, Shortlisted, In Review)
-- Includes both raw counts and percentage of total applications.
-- ============================================================================
SELECT 
    COUNT(*) AS total_applications,
    COUNT(CASE WHEN status = 'Selected' THEN 1 END) AS selected_count,
    ROUND((COUNT(CASE WHEN status = 'Selected' THEN 1 END) * 100.0) / NULLIF(COUNT(*), 0), 2) AS selected_percentage,
    COUNT(CASE WHEN status = 'Rejected' THEN 1 END) AS rejected_count,
    ROUND((COUNT(CASE WHEN status = 'Rejected' THEN 1 END) * 100.0) / NULLIF(COUNT(*), 0), 2) AS rejected_percentage,
    COUNT(CASE WHEN status NOT IN ('Selected', 'Rejected') THEN 1 END) AS pending_count,
    ROUND((COUNT(CASE WHEN status NOT IN ('Selected', 'Rejected') THEN 1 END) * 100.0) / NULLIF(COUNT(*), 0), 2) AS pending_percentage
FROM APPLICATION;

-- ============================================================================
-- QUERY 5: APPLICATION STATUS DISTRIBUTION (CHART DATA)
-- Categorizes all submitted applications by their exact status values
-- for donut/pie charts and pipeline visualization.
-- ============================================================================
SELECT 
    status,
    COUNT(*) AS count,
    ROUND((COUNT(*) * 100.0) / NULLIF((SELECT COUNT(*) FROM APPLICATION), 0), 2) AS percentage
FROM APPLICATION
GROUP BY status
ORDER BY count DESC, status ASC;

-- ============================================================================
-- QUERY 6: CONSOLIDATED EXECUTIVE OVERVIEW (DASHBOARD KPI CARDS)
-- Retrieves all high-level placement KPIs in a single CTE query:
-- - Student metrics (registered, placed, unplaced, %)
-- - Application metrics (total, selected, rejected, pending)
-- - Company metrics (active recruiting drives)
-- - Salary benchmarks (highest, average, lowest, median LPA)
-- ============================================================================
WITH 
stud_kpis AS (
    SELECT 
        COUNT(DISTINCT s.student_id) AS total_students,
        COUNT(DISTINCT p.student_id) AS placed_students
    FROM STUDENT s
    LEFT JOIN PLACEMENT p 
        ON s.student_id = p.student_id 
       AND p.acceptance_status = 'Accepted'
),
app_kpis AS (
    SELECT 
        COUNT(*) AS total_applications,
        COUNT(CASE WHEN status = 'Selected' THEN 1 END) AS selected_applications,
        COUNT(CASE WHEN status = 'Rejected' THEN 1 END) AS rejected_applications,
        COUNT(CASE WHEN status NOT IN ('Selected', 'Rejected') THEN 1 END) AS pending_applications
    FROM APPLICATION
),
comp_kpis AS (
    SELECT COUNT(*) AS total_companies FROM COMPANY
),
pkg_kpis AS (
    SELECT 
        NVL(MAX(package_offered), 0.00) AS highest_package_lpa,
        NVL(ROUND(AVG(package_offered), 2), 0.00) AS avg_package_lpa,
        NVL(MIN(package_offered), 0.00) AS lowest_package_lpa,
        NVL(ROUND(MEDIAN(package_offered), 2), 0.00) AS median_package_lpa
    FROM PLACEMENT
    WHERE acceptance_status = 'Accepted'
)
SELECT 
    sk.total_students,
    sk.placed_students,
    (sk.total_students - sk.placed_students) AS unplaced_students,
    CASE 
        WHEN sk.total_students = 0 THEN 0.00 
        ELSE ROUND((sk.placed_students * 100.0) / sk.total_students, 2) 
    END AS placement_percentage,
    ak.total_applications,
    ak.selected_applications,
    ak.rejected_applications,
    ak.pending_applications,
    ck.total_companies,
    pk.highest_package_lpa,
    pk.avg_package_lpa,
    pk.lowest_package_lpa,
    pk.median_package_lpa
FROM stud_kpis sk
CROSS JOIN app_kpis ak
CROSS JOIN comp_kpis ck
CROSS JOIN pkg_kpis pk;

-- ============================================================================
-- QUERY 7: DEPARTMENT-WISE (BRANCH-WISE) PLACEMENT SUMMARY
-- Analyzes placement performance per academic department without duplicate
-- counting of students or offers.
-- ============================================================================
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
ORDER BY placement_percentage DESC, total_students DESC;

-- ============================================================================
-- QUERY 8: SALARY PACKAGE BENCHMARKS (OFFERED CTC IN LPA)
-- Provides statistical metrics for salary compensation across accepted offers.
-- ============================================================================
SELECT 
    COUNT(placement_id) AS total_offers_accepted,
    NVL(MAX(package_offered), 0.00) AS highest_package_lpa,
    NVL(ROUND(AVG(package_offered), 2), 0.00) AS average_package_lpa,
    NVL(ROUND(MEDIAN(package_offered), 2), 0.00) AS median_package_lpa,
    NVL(MIN(package_offered), 0.00) AS lowest_package_lpa
FROM PLACEMENT
WHERE acceptance_status = 'Accepted';

-- ============================================================================
-- QUERY 9: COMPANY RECRUITMENT & HIRING CONVERSION FUNNEL
-- Shows each company drive's applicant volume, hiring counts, and conversion rate.
-- ============================================================================
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
LEFT JOIN PLACEMENT p ON c.company_id = p.company_id AND p.acceptance_status = 'Accepted'
GROUP BY c.company_id, c.company_name, c.job_role, c.package
ORDER BY total_hires DESC, offered_ctc_lpa DESC;
