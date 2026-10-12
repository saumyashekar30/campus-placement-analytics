-- ============================================================================
-- CAMPUS PLACEMENT ANALYTICS SYSTEM - COMPANY, BRANCH & PACKAGE ANALYTICS
-- Technology: Oracle SQL / Oracle SQL Developer / SQL*Plus (Oracle 12c/19c/21c/23c)
-- File: 05_company_analytics.sql
-- Reuses the existing STUDENT, COMPANY, APPLICATION and PLACEMENT tables.
-- An "offer" is any PLACEMENT row; a "placement" is an Accepted PLACEMENT row.
-- ============================================================================

SET SQLBLANKLINES ON;
SET DEFINE OFF;
SET PAGESIZE 50;
SET LINESIZE 200;
COLUMN company_name FORMAT A25;
COLUMN job_role FORMAT A28;
COLUMN branch FORMAT A10;

-- QUERY 1: COMPANY-WISE OFFER AND PLACEMENT COUNTS
SELECT
    c.company_id,
    c.company_name,
    c.job_role,
    COUNT(p.placement_id)                                                AS offers_made,
    COUNT(CASE WHEN p.acceptance_status = 'Accepted' THEN 1 END)         AS students_placed,
    COUNT(CASE WHEN p.acceptance_status = 'Declined' THEN 1 END)         AS offers_declined,
    COUNT(CASE WHEN p.acceptance_status = 'Pending'  THEN 1 END)         AS offers_pending
FROM COMPANY c
LEFT JOIN PLACEMENT p ON p.company_id = c.company_id
GROUP BY c.company_id, c.company_name, c.job_role
ORDER BY students_placed DESC, offers_made DESC, c.company_name;

-- QUERY 2: TOP RECRUITING COMPANIES (most students hired)
SELECT *
FROM (
    SELECT
        c.company_name,
        COUNT(p.placement_id) AS students_placed,
        DENSE_RANK() OVER (ORDER BY COUNT(p.placement_id) DESC) AS recruit_rank
    FROM COMPANY c
    JOIN PLACEMENT p ON p.company_id = c.company_id
                    AND p.acceptance_status = 'Accepted'
    GROUP BY c.company_name
)
WHERE recruit_rank <= 5
ORDER BY recruit_rank, company_name;

-- QUERY 3: BRANCH-WISE PLACEMENT COUNTS AND PERCENTAGES
SELECT
    s.branch,
    COUNT(DISTINCT s.student_id)                                         AS total_students,
    COUNT(DISTINCT p.student_id)                                         AS placed_students,
    COUNT(DISTINCT s.student_id) - COUNT(DISTINCT p.student_id)          AS unplaced_students,
    ROUND(COUNT(DISTINCT p.student_id) * 100.0
          / NULLIF(COUNT(DISTINCT s.student_id), 0), 2)                  AS placement_percentage
FROM STUDENT s
LEFT JOIN PLACEMENT p ON p.student_id = s.student_id
                     AND p.acceptance_status = 'Accepted'
GROUP BY s.branch
ORDER BY placement_percentage DESC, s.branch;

-- QUERY 4: OVERALL PACKAGE STATISTICS (highest, average, lowest)
SELECT
    COUNT(*)                          AS placements,
    MAX(package_offered)              AS highest_package,
    ROUND(AVG(package_offered), 2)    AS average_package,
    MIN(package_offered)              AS lowest_package
FROM PLACEMENT
WHERE acceptance_status = 'Accepted';

-- QUERY 5: PACKAGE COMPARISON ACROSS COMPANIES
SELECT
    c.company_name,
    COUNT(p.placement_id)                                                AS placements,
    MAX(p.package_offered)                                               AS highest_package,
    ROUND(AVG(p.package_offered), 2)                                     AS average_package,
    MIN(p.package_offered)                                               AS lowest_package,
    ROUND(AVG(p.package_offered)
          - AVG(AVG(p.package_offered)) OVER (), 2)                      AS diff_from_avg_of_companies
FROM COMPANY c
JOIN PLACEMENT p ON p.company_id = c.company_id
                AND p.acceptance_status = 'Accepted'
GROUP BY c.company_name
ORDER BY average_package DESC, c.company_name;

-- QUERY 6: BRANCH-WISE PACKAGE STATISTICS
SELECT
    s.branch,
    COUNT(*)                          AS placements,
    MAX(p.package_offered)            AS highest_package,
    ROUND(AVG(p.package_offered), 2)  AS average_package,
    MIN(p.package_offered)            AS lowest_package
FROM PLACEMENT p
JOIN STUDENT s ON s.student_id = p.student_id
WHERE p.acceptance_status = 'Accepted'
GROUP BY s.branch
ORDER BY average_package DESC;
