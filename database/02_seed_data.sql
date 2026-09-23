-- ============================================================================
-- CAMPUS PLACEMENT ANALYTICS SYSTEM - PHASE 1: SAMPLE DATA (SEED DATA)
-- Technology: Oracle SQL / Oracle SQL Developer / SQL*Plus (Oracle 12c/19c/21c/23c)
-- File: 02_seed_data.sql
-- ============================================================================

SET SQLBLANKLINES ON;
SET DEFINE OFF;
SET FEEDBACK OFF;

-- ----------------------------------------------------------------------------
-- 1. INSERT STUDENTS (10 Diverse Students)
-- ----------------------------------------------------------------------------
INSERT INTO STUDENT (student_id, student_name, email, phone, branch, cgpa, tenth_percentage, twelfth_percentage, backlogs, resume_url, created_at)
VALUES (1, 'Aarav Sharma', 'aarav.sharma@college.edu', '9876543210', 'CSE', 9.42, 94.50, 92.00, 0, 'https://storage.college.edu/resumes/aarav_cse.pdf', TO_DATE('2024-01-15', 'YYYY-MM-DD'));

INSERT INTO STUDENT (student_id, student_name, email, phone, branch, cgpa, tenth_percentage, twelfth_percentage, backlogs, resume_url, created_at)
VALUES (2, 'Diya Patel', 'diya.patel@college.edu', '9876543211', 'CSE', 8.85, 91.00, 89.50, 0, 'https://storage.college.edu/resumes/diya_cse.pdf', TO_DATE('2024-01-15', 'YYYY-MM-DD'));

INSERT INTO STUDENT (student_id, student_name, email, phone, branch, cgpa, tenth_percentage, twelfth_percentage, backlogs, resume_url, created_at)
VALUES (3, 'Rohan Verma', 'rohan.verma@college.edu', '9876543212', 'IT', 8.20, 85.00, 82.50, 0, 'https://storage.college.edu/resumes/rohan_it.pdf', TO_DATE('2024-01-16', 'YYYY-MM-DD'));

INSERT INTO STUDENT (student_id, student_name, email, phone, branch, cgpa, tenth_percentage, twelfth_percentage, backlogs, resume_url, created_at)
VALUES (4, 'Ananya Iyer', 'ananya.iyer@college.edu', '9876543213', 'ECE', 8.60, 89.00, 87.00, 0, 'https://storage.college.edu/resumes/ananya_ece.pdf', TO_DATE('2024-01-16', 'YYYY-MM-DD'));

INSERT INTO STUDENT (student_id, student_name, email, phone, branch, cgpa, tenth_percentage, twelfth_percentage, backlogs, resume_url, created_at)
VALUES (5, 'Kabir Mehta', 'kabir.mehta@college.edu', '9876543214', 'ECE', 7.45, 78.00, 75.00, 1, 'https://storage.college.edu/resumes/kabir_ece.pdf', TO_DATE('2024-01-17', 'YYYY-MM-DD'));

INSERT INTO STUDENT (student_id, student_name, email, phone, branch, cgpa, tenth_percentage, twelfth_percentage, backlogs, resume_url, created_at)
VALUES (6, 'Sneha Kulkarni', 'sneha.k@college.edu', '9876543215', 'IT', 7.75, 82.00, 80.00, 0, 'https://storage.college.edu/resumes/sneha_it.pdf', TO_DATE('2024-01-17', 'YYYY-MM-DD'));

INSERT INTO STUDENT (student_id, student_name, email, phone, branch, cgpa, tenth_percentage, twelfth_percentage, backlogs, resume_url, created_at)
VALUES (7, 'Vikram Singh', 'vikram.singh@college.edu', '9876543216', 'EEE', 7.10, 74.00, 71.50, 0, 'https://storage.college.edu/resumes/vikram_eee.pdf', TO_DATE('2024-01-18', 'YYYY-MM-DD'));

INSERT INTO STUDENT (student_id, student_name, email, phone, branch, cgpa, tenth_percentage, twelfth_percentage, backlogs, resume_url, created_at)
VALUES (8, 'Pooja Reddy', 'pooja.reddy@college.edu', '9876543217', 'MECH', 6.85, 72.00, 68.00, 2, 'https://storage.college.edu/resumes/pooja_mech.pdf', TO_DATE('2024-01-18', 'YYYY-MM-DD'));

INSERT INTO STUDENT (student_id, student_name, email, phone, branch, cgpa, tenth_percentage, twelfth_percentage, backlogs, resume_url, created_at)
VALUES (9, 'Aditya Nair', 'aditya.nair@college.edu', '9876543218', 'CSE', 8.15, 86.50, 84.00, 0, 'https://storage.college.edu/resumes/aditya_cse.pdf', TO_DATE('2024-01-19', 'YYYY-MM-DD'));

INSERT INTO STUDENT (student_id, student_name, email, phone, branch, cgpa, tenth_percentage, twelfth_percentage, backlogs, resume_url, created_at)
VALUES (10, 'Meera Joshi', 'meera.joshi@college.edu', '9876543219', 'MECH', 7.30, 77.00, 74.00, 0, 'https://storage.college.edu/resumes/meera_mech.pdf', TO_DATE('2024-01-19', 'YYYY-MM-DD'));

-- ----------------------------------------------------------------------------
-- 2. INSERT STUDENT SKILLS (Multiple skills per student)
-- ----------------------------------------------------------------------------
INSERT INTO STUDENT_SKILL VALUES (1, 'Python', 'Expert');
INSERT INTO STUDENT_SKILL VALUES (1, 'Docker', 'Advanced');
INSERT INTO STUDENT_SKILL VALUES (1, 'Kubernetes', 'Intermediate');
INSERT INTO STUDENT_SKILL VALUES (1, 'Cloud Computing', 'Advanced');
INSERT INTO STUDENT_SKILL VALUES (1, 'Data Structures', 'Expert');

INSERT INTO STUDENT_SKILL VALUES (2, 'Java', 'Expert');
INSERT INTO STUDENT_SKILL VALUES (2, 'C++', 'Advanced');
INSERT INTO STUDENT_SKILL VALUES (2, 'SQL', 'Advanced');
INSERT INTO STUDENT_SKILL VALUES (2, 'Data Structures', 'Expert');

INSERT INTO STUDENT_SKILL VALUES (3, 'Java', 'Advanced');
INSERT INTO STUDENT_SKILL VALUES (3, 'SQL', 'Intermediate');
INSERT INTO STUDENT_SKILL VALUES (3, 'Python', 'Intermediate');

INSERT INTO STUDENT_SKILL VALUES (4, 'C', 'Expert');
INSERT INTO STUDENT_SKILL VALUES (4, 'Embedded Systems', 'Advanced');
INSERT INTO STUDENT_SKILL VALUES (4, 'Linux', 'Advanced');
INSERT INTO STUDENT_SKILL VALUES (4, 'Data Structures', 'Intermediate');

INSERT INTO STUDENT_SKILL VALUES (5, 'C', 'Intermediate');
INSERT INTO STUDENT_SKILL VALUES (5, 'Embedded Systems', 'Intermediate');
INSERT INTO STUDENT_SKILL VALUES (5, 'Linux', 'Beginner');

INSERT INTO STUDENT_SKILL VALUES (6, 'Java', 'Advanced');
INSERT INTO STUDENT_SKILL VALUES (6, 'SQL', 'Advanced');
INSERT INTO STUDENT_SKILL VALUES (6, 'React', 'Intermediate');

INSERT INTO STUDENT_SKILL VALUES (7, 'C', 'Intermediate');
INSERT INTO STUDENT_SKILL VALUES (7, 'Linux', 'Intermediate');
INSERT INTO STUDENT_SKILL VALUES (7, 'Python', 'Beginner');

INSERT INTO STUDENT_SKILL VALUES (8, 'Python', 'Intermediate');
INSERT INTO STUDENT_SKILL VALUES (8, 'SQL', 'Beginner');
INSERT INTO STUDENT_SKILL VALUES (8, 'AutoCAD', 'Advanced');

INSERT INTO STUDENT_SKILL VALUES (9, 'Java', 'Advanced');
INSERT INTO STUDENT_SKILL VALUES (9, 'Python', 'Advanced');
INSERT INTO STUDENT_SKILL VALUES (9, 'SQL', 'Advanced');
INSERT INTO STUDENT_SKILL VALUES (9, 'Data Structures', 'Advanced');

INSERT INTO STUDENT_SKILL VALUES (10, 'Python', 'Intermediate');
INSERT INTO STUDENT_SKILL VALUES (10, 'SQL', 'Intermediate');
INSERT INTO STUDENT_SKILL VALUES (10, 'SolidWorks', 'Expert');

-- ----------------------------------------------------------------------------
-- 3. INSERT CERTIFICATIONS
-- ----------------------------------------------------------------------------
INSERT INTO CERTIFICATION (certification_id, student_id, cert_name, issuing_organization, issue_date, expiry_date, credential_id)
VALUES (1, 1, 'Google Cloud Certified Professional Cloud Architect', 'Google Cloud', TO_DATE('2023-06-10', 'YYYY-MM-DD'), TO_DATE('2025-06-10', 'YYYY-MM-DD'), 'GCP-ARCH-84920');

INSERT INTO CERTIFICATION (certification_id, student_id, cert_name, issuing_organization, issue_date, expiry_date, credential_id)
VALUES (2, 1, 'Certified Kubernetes Administrator (CKA)', 'Linux Foundation', TO_DATE('2023-09-15', 'YYYY-MM-DD'), TO_DATE('2026-09-15', 'YYYY-MM-DD'), 'CKA-99482');

INSERT INTO CERTIFICATION (certification_id, student_id, cert_name, issuing_organization, issue_date, expiry_date, credential_id)
VALUES (3, 2, 'Oracle Certified Professional: Java SE 11 Developer', 'Oracle', TO_DATE('2023-04-20', 'YYYY-MM-DD'), NULL, 'OCP-JAVA-11-7362');

INSERT INTO CERTIFICATION (certification_id, student_id, cert_name, issuing_organization, issue_date, expiry_date, credential_id)
VALUES (4, 3, 'AWS Certified Solutions Architect - Associate', 'Amazon Web Services', TO_DATE('2023-11-05', 'YYYY-MM-DD'), TO_DATE('2026-11-05', 'YYYY-MM-DD'), 'AWS-SAA-38291');

INSERT INTO CERTIFICATION (certification_id, student_id, cert_name, issuing_organization, issue_date, expiry_date, credential_id)
VALUES (5, 4, 'Arm Accredited Engineer (AAE)', 'Arm Education', TO_DATE('2023-08-12', 'YYYY-MM-DD'), NULL, 'ARM-AAE-5521');

INSERT INTO CERTIFICATION (certification_id, student_id, cert_name, issuing_organization, issue_date, expiry_date, credential_id)
VALUES (6, 9, 'Microsoft Certified: Azure Fundamentals', 'Microsoft', TO_DATE('2023-10-01', 'YYYY-MM-DD'), NULL, 'MS-AZ900-1092');

-- ----------------------------------------------------------------------------
-- 4. INSERT PROJECTS
-- ----------------------------------------------------------------------------
INSERT INTO PROJECT (project_id, student_id, project_title, tech_stack, description, project_url, start_date, end_date)
VALUES (1, 1, 'Distributed Cloud Storage Engine', 'Python, Docker, Kubernetes, gRPC', 'Built a fault-tolerant distributed object store with multi-node replication and consistency guarantees.', 'https://github.com/aarav/cloud-store', TO_DATE('2023-07-01', 'YYYY-MM-DD'), TO_DATE('2023-11-30', 'YYYY-MM-DD'));

INSERT INTO PROJECT (project_id, student_id, project_title, tech_stack, description, project_url, start_date, end_date)
VALUES (2, 2, 'High-Throughput Trading Engine Simulator', 'C++, Java, Multithreading, Socket Programming', 'Engineered an in-memory matching engine processing 50,000 order transactions/sec with low latency.', 'https://github.com/diya/matching-engine', TO_DATE('2023-08-15', 'YYYY-MM-DD'), TO_DATE('2023-12-20', 'YYYY-MM-DD'));

INSERT INTO PROJECT (project_id, student_id, project_title, tech_stack, description, project_url, start_date, end_date)
VALUES (3, 3, 'Microservices E-Commerce Backend', 'Java, Spring Boot, PostgreSQL, Docker', 'Architected a resilient microservice ordering and payment pipeline with event-driven messaging.', 'https://github.com/rohan/ecommerce-backend', TO_DATE('2023-06-01', 'YYYY-MM-DD'), TO_DATE('2023-09-15', 'YYYY-MM-DD'));

INSERT INTO PROJECT (project_id, student_id, project_title, tech_stack, description, project_url, start_date, end_date)
VALUES (4, 4, 'Real-Time RTOS Sensor Telemetry Unit', 'C, Embedded Systems, FreeRTOS, STM32', 'Created an embedded sensory aggregator reporting environmental and accelerometer telemetry over CAN bus.', 'https://github.com/ananya/rtos-telemetry', TO_DATE('2023-05-10', 'YYYY-MM-DD'), TO_DATE('2023-08-30', 'YYYY-MM-DD'));

INSERT INTO PROJECT (project_id, student_id, project_title, tech_stack, description, project_url, start_date, end_date)
VALUES (5, 9, 'Campus Placement Prediction AI Model', 'Python, Scikit-Learn, Flask, Oracle SQL', 'Trained predictive machine learning models to identify placement probabilities and recommend targeted skills.', 'https://github.com/aditya/placement-analytics', TO_DATE('2023-09-01', 'YYYY-MM-DD'), TO_DATE('2023-12-15', 'YYYY-MM-DD'));

-- ----------------------------------------------------------------------------
-- 5. INSERT INTERNSHIPS
-- ----------------------------------------------------------------------------
INSERT INTO INTERNSHIP (internship_id, student_id, company_name, role, start_date, end_date, description)
VALUES (1, 1, 'Red Hat Technologies', 'Cloud Platform Intern', TO_DATE('2023-05-15', 'YYYY-MM-DD'), TO_DATE('2023-07-25', 'YYYY-MM-DD'), 'Automated OpenShift deployment pipelines and optimized container networking.');

INSERT INTO INTERNSHIP (internship_id, student_id, company_name, role, start_date, end_date, description)
VALUES (2, 2, 'Morgan Stanley', 'Summer Analyst - Tech', TO_DATE('2023-05-20', 'YYYY-MM-DD'), TO_DATE('2023-07-20', 'YYYY-MM-DD'), 'Developed automated settlement reconciliation tools using Java and Oracle DB.');

INSERT INTO INTERNSHIP (internship_id, student_id, company_name, role, start_date, end_date, description)
VALUES (3, 4, 'Texas Instruments', 'Embedded Software Intern', TO_DATE('2023-05-10', 'YYYY-MM-DD'), TO_DATE('2023-07-15', 'YYYY-MM-DD'), 'Wrote device driver firmware for low-power I2C/SPI sensor interfaces.');

INSERT INTO INTERNSHIP (internship_id, student_id, company_name, role, start_date, end_date, description)
VALUES (4, 9, 'Cognizant Technology Solutions', 'Data Engineering Intern', TO_DATE('2023-06-01', 'YYYY-MM-DD'), TO_DATE('2023-07-31', 'YYYY-MM-DD'), 'Assisted in building ETL pipelines and structured reporting dashboards using SQL.');

-- ----------------------------------------------------------------------------
-- 6. INSERT COMPANIES (5 Companies with Distinct Eligibility Criteria)
-- ----------------------------------------------------------------------------
-- Company 1: Premium Cloud firm (High bar, 0 backlogs, CSE/IT only)
INSERT INTO COMPANY (company_id, company_name, job_role, required_cgpa, min_tenth_percentage, min_twelfth_percentage, max_backlogs, package, job_description, application_deadline, drive_date)
VALUES (1, 'Google Cloud India', 'Cloud Solutions Engineer', 8.50, 80.00, 80.00, 0, 24.00, 'Design scalable hybrid-cloud solutions and architect distributed backend infrastructure.', TO_DATE('2024-02-28', 'YYYY-MM-DD'), TO_DATE('2024-03-05', 'YYYY-MM-DD'));

-- Company 2: Tier-1 Tech (High bar, 0 backlogs, CSE/IT/ECE)
INSERT INTO COMPANY (company_id, company_name, job_role, required_cgpa, min_tenth_percentage, min_twelfth_percentage, max_backlogs, package, job_description, application_deadline, drive_date)
VALUES (2, 'Microsoft IDC', 'Software Development Engineer', 8.00, 75.00, 75.00, 0, 18.50, 'Build mission-critical cloud services and developer tooling on Azure.', TO_DATE('2024-03-01', 'YYYY-MM-DD'), TO_DATE('2024-03-08', 'YYYY-MM-DD'));

-- Company 3: Hardware and Semiconductor (Specific branches ECE/EEE/CSE, 0 backlogs)
INSERT INTO COMPANY (company_id, company_name, job_role, required_cgpa, min_tenth_percentage, min_twelfth_percentage, max_backlogs, package, job_description, application_deadline, drive_date)
VALUES (3, 'Qualcomm Technologies', 'Embedded Systems Engineer', 7.50, 70.00, 70.00, 0, 14.50, 'Develop firmware, BSP drivers, and low-level communication protocols.', TO_DATE('2024-03-10', 'YYYY-MM-DD'), TO_DATE('2024-03-15', 'YYYY-MM-DD'));

-- Company 4: Mass Recruiter - Digital Cadre (Moderate bar, 1 backlog allowed, CSE/IT/ECE/EEE)
INSERT INTO COMPANY (company_id, company_name, job_role, required_cgpa, min_tenth_percentage, min_twelfth_percentage, max_backlogs, package, job_description, application_deadline, drive_date)
VALUES (4, 'TCS Digital', 'Systems Engineer - Digital', 7.00, 65.00, 65.00, 1, 7.50, 'Deliver enterprise digital solutions, cloud integrations, and enterprise web applications.', TO_DATE('2024-03-15', 'YYYY-MM-DD'), TO_DATE('2024-03-20', 'YYYY-MM-DD'));

-- Company 5: Broad IT/Consulting (Relaxed bar, 2 backlogs allowed, All Branches)
INSERT INTO COMPANY (company_id, company_name, job_role, required_cgpa, min_tenth_percentage, min_twelfth_percentage, max_backlogs, package, job_description, application_deadline, drive_date)
VALUES (5, 'Apex Global Tech', 'Associate Software Engineer', 6.50, 60.00, 60.00, 2, 5.50, 'Develop, test, and support business software solutions across global client accounts.', TO_DATE('2024-03-25', 'YYYY-MM-DD'), TO_DATE('2024-03-30', 'YYYY-MM-DD'));

-- ----------------------------------------------------------------------------
-- 7. INSERT COMPANY ALLOWED BRANCHES (Normalized 1:N Branch Criteria)
-- ----------------------------------------------------------------------------
-- Google Cloud: CSE, IT
INSERT INTO COMPANY_BRANCH VALUES (1, 'CSE');
INSERT INTO COMPANY_BRANCH VALUES (1, 'IT');

-- Microsoft IDC: CSE, IT, ECE
INSERT INTO COMPANY_BRANCH VALUES (2, 'CSE');
INSERT INTO COMPANY_BRANCH VALUES (2, 'IT');
INSERT INTO COMPANY_BRANCH VALUES (2, 'ECE');

-- Qualcomm: ECE, EEE, CSE
INSERT INTO COMPANY_BRANCH VALUES (3, 'ECE');
INSERT INTO COMPANY_BRANCH VALUES (3, 'EEE');
INSERT INTO COMPANY_BRANCH VALUES (3, 'CSE');

-- TCS Digital: CSE, IT, ECE, EEE
INSERT INTO COMPANY_BRANCH VALUES (4, 'CSE');
INSERT INTO COMPANY_BRANCH VALUES (4, 'IT');
INSERT INTO COMPANY_BRANCH VALUES (4, 'ECE');
INSERT INTO COMPANY_BRANCH VALUES (4, 'EEE');

-- Apex Global Tech: CSE, IT, ECE, EEE, MECH
INSERT INTO COMPANY_BRANCH VALUES (5, 'CSE');
INSERT INTO COMPANY_BRANCH VALUES (5, 'IT');
INSERT INTO COMPANY_BRANCH VALUES (5, 'ECE');
INSERT INTO COMPANY_BRANCH VALUES (5, 'EEE');
INSERT INTO COMPANY_BRANCH VALUES (5, 'MECH');

-- ----------------------------------------------------------------------------
-- 8. INSERT COMPANY REQUIRED SKILLS (Normalized 1:N Skill Criteria)
-- ----------------------------------------------------------------------------
-- Google Cloud Skills
INSERT INTO COMPANY_SKILL VALUES (1, 'Python', 'Advanced');
INSERT INTO COMPANY_SKILL VALUES (1, 'Cloud Computing', 'Intermediate');
INSERT INTO COMPANY_SKILL VALUES (1, 'Docker', 'Intermediate');

-- Microsoft IDC Skills
INSERT INTO COMPANY_SKILL VALUES (2, 'Java', 'Advanced');
INSERT INTO COMPANY_SKILL VALUES (2, 'C++', 'Intermediate');
INSERT INTO COMPANY_SKILL VALUES (2, 'Data Structures', 'Advanced');

-- Qualcomm Skills
INSERT INTO COMPANY_SKILL VALUES (3, 'C', 'Advanced');
INSERT INTO COMPANY_SKILL VALUES (3, 'Embedded Systems', 'Intermediate');
INSERT INTO COMPANY_SKILL VALUES (3, 'Linux', 'Intermediate');

-- TCS Digital Skills
INSERT INTO COMPANY_SKILL VALUES (4, 'Java', 'Intermediate');
INSERT INTO COMPANY_SKILL VALUES (4, 'SQL', 'Intermediate');

-- Apex Global Tech Skills
INSERT INTO COMPANY_SKILL VALUES (5, 'Python', 'Beginner');
INSERT INTO COMPANY_SKILL VALUES (5, 'SQL', 'Beginner');

-- ----------------------------------------------------------------------------
-- 9. INSERT APPLICATIONS (Multi-stage tracking)
-- ----------------------------------------------------------------------------
-- Student 1 (Aarav - CSE - 9.42 CGPA) applied to Google and Microsoft
INSERT INTO APPLICATION (application_id, student_id, company_id, application_date, status)
VALUES (1, 1, 1, TO_DATE('2024-02-15', 'YYYY-MM-DD'), 'Selected');

INSERT INTO APPLICATION (application_id, student_id, company_id, application_date, status)
VALUES (2, 1, 2, TO_DATE('2024-02-16', 'YYYY-MM-DD'), 'Shortlisted');

-- Student 2 (Diya - CSE - 8.85 CGPA) applied to Google and Microsoft
INSERT INTO APPLICATION (application_id, student_id, company_id, application_date, status)
VALUES (3, 2, 1, TO_DATE('2024-02-16', 'YYYY-MM-DD'), 'Shortlisted');

INSERT INTO APPLICATION (application_id, student_id, company_id, application_date, status)
VALUES (4, 2, 2, TO_DATE('2024-02-17', 'YYYY-MM-DD'), 'Selected');

-- Student 3 (Rohan - IT - 8.20 CGPA) applied to Microsoft and TCS
INSERT INTO APPLICATION (application_id, student_id, company_id, application_date, status)
VALUES (5, 3, 2, TO_DATE('2024-02-18', 'YYYY-MM-DD'), 'Rejected');

INSERT INTO APPLICATION (application_id, student_id, company_id, application_date, status)
VALUES (6, 3, 4, TO_DATE('2024-02-19', 'YYYY-MM-DD'), 'Selected');

-- Student 4 (Ananya - ECE - 8.60 CGPA) applied to Qualcomm and Microsoft
INSERT INTO APPLICATION (application_id, student_id, company_id, application_date, status)
VALUES (7, 4, 3, TO_DATE('2024-02-18', 'YYYY-MM-DD'), 'Selected');

INSERT INTO APPLICATION (application_id, student_id, company_id, application_date, status)
VALUES (8, 4, 2, TO_DATE('2024-02-20', 'YYYY-MM-DD'), 'Shortlisted');

-- Student 5 (Kabir - ECE - 7.45 CGPA, 1 Backlog) applied to TCS Digital
INSERT INTO APPLICATION (application_id, student_id, company_id, application_date, status)
VALUES (9, 5, 4, TO_DATE('2024-02-21', 'YYYY-MM-DD'), 'In Review');

-- Student 6 (Sneha - IT - 7.75 CGPA) applied to TCS Digital
INSERT INTO APPLICATION (application_id, student_id, company_id, application_date, status)
VALUES (10, 6, 4, TO_DATE('2024-02-22', 'YYYY-MM-DD'), 'Selected');

-- Student 7 (Vikram - EEE - 7.10 CGPA) applied to TCS Digital and Apex Global
INSERT INTO APPLICATION (application_id, student_id, company_id, application_date, status)
VALUES (11, 7, 4, TO_DATE('2024-02-22', 'YYYY-MM-DD'), 'Shortlisted');

INSERT INTO APPLICATION (application_id, student_id, company_id, application_date, status)
VALUES (12, 7, 5, TO_DATE('2024-02-24', 'YYYY-MM-DD'), 'Selected');

-- Student 8 (Pooja - MECH - 6.85 CGPA, 2 Backlogs) applied to Apex Global Tech
INSERT INTO APPLICATION (application_id, student_id, company_id, application_date, status)
VALUES (13, 8, 5, TO_DATE('2024-02-25', 'YYYY-MM-DD'), 'Shortlisted');

-- Student 9 (Aditya - CSE - 8.15 CGPA) applied to Microsoft and TCS
INSERT INTO APPLICATION (application_id, student_id, company_id, application_date, status)
VALUES (14, 9, 2, TO_DATE('2024-02-20', 'YYYY-MM-DD'), 'In Review');

INSERT INTO APPLICATION (application_id, student_id, company_id, application_date, status)
VALUES (15, 9, 4, TO_DATE('2024-02-22', 'YYYY-MM-DD'), 'Shortlisted');

-- Student 10 (Meera - MECH - 7.30 CGPA) applied to Apex Global Tech
INSERT INTO APPLICATION (application_id, student_id, company_id, application_date, status)
VALUES (16, 10, 5, TO_DATE('2024-02-26', 'YYYY-MM-DD'), 'In Review');

-- ----------------------------------------------------------------------------
-- 10. INSERT INTERVIEWS (Multiple Rounds with Scores and Statuses)
-- ----------------------------------------------------------------------------
-- App 1: Aarav @ Google Cloud (Round 1: Coding, Round 2: System Design, Round 3: HR)
INSERT INTO INTERVIEW (interview_id, application_id, round_number, round_name, interview_date, score, status, feedback)
VALUES (1, 1, 1, 'Technical Coding Round', TO_DATE('2024-03-01', 'YYYY-MM-DD'), 95.00, 'Passed', 'Exceptional data structure mastery and clean Python code.');

INSERT INTO INTERVIEW (interview_id, application_id, round_number, round_name, interview_date, score, status, feedback)
VALUES (2, 1, 2, 'System Design and Cloud Architecture', TO_DATE('2024-03-03', 'YYYY-MM-DD'), 92.00, 'Passed', 'Clear understanding of distributed caching, microservices, and Kubernetes.');

INSERT INTO INTERVIEW (interview_id, application_id, round_number, round_name, interview_date, score, status, feedback)
VALUES (3, 1, 3, 'Leadership and HR Round', TO_DATE('2024-03-05', 'YYYY-MM-DD'), 90.00, 'Passed', 'High cultural alignment, articulate communicator.');

-- App 4: Diya @ Microsoft IDC (Round 1: Coding, Round 2: Architecture, Round 3: HR)
INSERT INTO INTERVIEW (interview_id, application_id, round_number, round_name, interview_date, score, status, feedback)
VALUES (4, 4, 1, 'Data Structures and Algorithms', TO_DATE('2024-03-02', 'YYYY-MM-DD'), 94.00, 'Passed', 'Flawless graph search and dynamic programming solution.');

INSERT INTO INTERVIEW (interview_id, application_id, round_number, round_name, interview_date, score, status, feedback)
VALUES (5, 4, 2, 'Object-Oriented Design', TO_DATE('2024-03-04', 'YYYY-MM-DD'), 88.00, 'Passed', 'Solid modular design principles and concurrency management in Java.');

INSERT INTO INTERVIEW (interview_id, application_id, round_number, round_name, interview_date, score, status, feedback)
VALUES (6, 4, 3, 'HR and Behavioral', TO_DATE('2024-03-06', 'YYYY-MM-DD'), 85.00, 'Passed', 'Great team player and enthusiastic.');

-- App 5: Rohan @ Microsoft IDC (Round 1: Failed)
INSERT INTO INTERVIEW (interview_id, application_id, round_number, round_name, interview_date, score, status, feedback)
VALUES (7, 5, 1, 'Data Structures and Algorithms', TO_DATE('2024-03-02', 'YYYY-MM-DD'), 52.00, 'Failed', 'Struggled with tree balancing and algorithmic complexity.');

-- App 6: Rohan @ TCS Digital (Round 1: Cleared, Round 2: Cleared)
INSERT INTO INTERVIEW (interview_id, application_id, round_number, round_name, interview_date, score, status, feedback)
VALUES (8, 6, 1, 'Technical Assessment', TO_DATE('2024-03-12', 'YYYY-MM-DD'), 84.00, 'Passed', 'Good programming logic and strong SQL query knowledge.');

INSERT INTO INTERVIEW (interview_id, application_id, round_number, round_name, interview_date, score, status, feedback)
VALUES (9, 6, 2, 'Managerial and HR', TO_DATE('2024-03-14', 'YYYY-MM-DD'), 80.00, 'Passed', 'Solid problem solver with positive mindset.');

-- App 7: Ananya @ Qualcomm (Round 1: C/OS, Round 2: Embedded Systems, Round 3: HR)
INSERT INTO INTERVIEW (interview_id, application_id, round_number, round_name, interview_date, score, status, feedback)
VALUES (10, 7, 1, 'Low-Level C Programming and OS', TO_DATE('2024-03-11', 'YYYY-MM-DD'), 92.00, 'Passed', 'Deep pointer manipulation and memory barrier comprehension.');

INSERT INTO INTERVIEW (interview_id, application_id, round_number, round_name, interview_date, score, status, feedback)
VALUES (11, 7, 2, 'Microcontrollers and Protocols', TO_DATE('2024-03-13', 'YYYY-MM-DD'), 89.00, 'Passed', 'Thorough understanding of UART/SPI/I2C, DMA, and RTOS threads.');

INSERT INTO INTERVIEW (interview_id, application_id, round_number, round_name, interview_date, score, status, feedback)
VALUES (12, 7, 3, 'HR and Fitment Round', TO_DATE('2024-03-15', 'YYYY-MM-DD'), 86.00, 'Passed', 'Excellent communication and clear career aspirations.');

-- App 10: Sneha @ TCS Digital
INSERT INTO INTERVIEW (interview_id, application_id, round_number, round_name, interview_date, score, status, feedback)
VALUES (13, 10, 1, 'Technical Assessment', TO_DATE('2024-03-12', 'YYYY-MM-DD'), 81.00, 'Passed', 'Good full-stack awareness and clean SQL queries.');

INSERT INTO INTERVIEW (interview_id, application_id, round_number, round_name, interview_date, score, status, feedback)
VALUES (14, 10, 2, 'Managerial and HR', TO_DATE('2024-03-14', 'YYYY-MM-DD'), 78.00, 'Passed', 'Ready to deploy on modern client frameworks.');

-- App 12: Vikram @ Apex Global
INSERT INTO INTERVIEW (interview_id, application_id, round_number, round_name, interview_date, score, status, feedback)
VALUES (15, 12, 1, 'General Technical and Aptitude', TO_DATE('2024-03-26', 'YYYY-MM-DD'), 76.00, 'Passed', 'Sound logical reasoning and basic programming skills.');

INSERT INTO INTERVIEW (interview_id, application_id, round_number, round_name, interview_date, score, status, feedback)
VALUES (16, 12, 2, 'HR Interview', TO_DATE('2024-03-28', 'YYYY-MM-DD'), 75.00, 'Passed', 'Enthusiastic and adaptable.');

-- ----------------------------------------------------------------------------
-- 11. INSERT PLACEMENTS (1 Student -> 1 Final Placement Record)
-- ----------------------------------------------------------------------------
-- Student 1 (Aarav) accepted offer from Google Cloud (24.00 LPA)
INSERT INTO PLACEMENT (placement_id, student_id, company_id, application_id, offer_date, package_offered, acceptance_status, joining_date)
VALUES (1, 1, 1, 1, TO_DATE('2024-03-08', 'YYYY-MM-DD'), 24.00, 'Accepted', TO_DATE('2024-07-15', 'YYYY-MM-DD'));

-- Student 2 (Diya) accepted offer from Microsoft IDC (18.50 LPA)
INSERT INTO PLACEMENT (placement_id, student_id, company_id, application_id, offer_date, package_offered, acceptance_status, joining_date)
VALUES (2, 2, 2, 4, TO_DATE('2024-03-10', 'YYYY-MM-DD'), 18.50, 'Accepted', TO_DATE('2024-07-20', 'YYYY-MM-DD'));

-- Student 3 (Rohan) accepted offer from TCS Digital (7.50 LPA)
INSERT INTO PLACEMENT (placement_id, student_id, company_id, application_id, offer_date, package_offered, acceptance_status, joining_date)
VALUES (3, 3, 4, 6, TO_DATE('2024-03-16', 'YYYY-MM-DD'), 7.50, 'Accepted', TO_DATE('2024-08-01', 'YYYY-MM-DD'));

-- Student 4 (Ananya) accepted offer from Qualcomm Technologies (14.50 LPA)
INSERT INTO PLACEMENT (placement_id, student_id, company_id, application_id, offer_date, package_offered, acceptance_status, joining_date)
VALUES (4, 4, 3, 7, TO_DATE('2024-03-18', 'YYYY-MM-DD'), 14.50, 'Accepted', TO_DATE('2024-08-05', 'YYYY-MM-DD'));

-- Student 6 (Sneha) accepted offer from TCS Digital (7.50 LPA)
INSERT INTO PLACEMENT (placement_id, student_id, company_id, application_id, offer_date, package_offered, acceptance_status, joining_date)
VALUES (5, 6, 4, 10, TO_DATE('2024-03-16', 'YYYY-MM-DD'), 7.50, 'Accepted', TO_DATE('2024-08-01', 'YYYY-MM-DD'));

-- Student 7 (Vikram) accepted offer from Apex Global Tech (5.50 LPA)
INSERT INTO PLACEMENT (placement_id, student_id, company_id, application_id, offer_date, package_offered, acceptance_status, joining_date)
VALUES (6, 7, 5, 12, TO_DATE('2024-03-29', 'YYYY-MM-DD'), 5.50, 'Accepted', TO_DATE('2024-08-10', 'YYYY-MM-DD'));

COMMIT;
