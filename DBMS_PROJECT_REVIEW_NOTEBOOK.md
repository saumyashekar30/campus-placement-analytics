# 🎓 Campus Placement Analytics System
## DBMS Project Review & Viva Presentation Notebook

---

## 📌 1. Project Overview & Problem Statement
* **Project Title:** Campus Placement Analytics System
* **Domain:** Academic & Enterprise Database Management System
* **Tech Stack:** Oracle SQL Database, Python (`python-oracledb` Thin Mode), Flask Backend, HTML5/CSS3/JS Frontend
* **Core Objective:** Eliminate manual placement coordination errors by designing a normalized relational database that enforces **company-specific eligibility criteria**, tracks **multi-round interview evaluations**, prevents duplicate/ineligible applications, and yields real-time placement analytics.

---

## 📐 2. Entity-Relationship (ER) Modeling & Architecture

### **Entities & Relationships Summary**

```
+---------------+          1:N          +------------------+
|    STUDENT    | --------------------> |  STUDENT_SKILL   |
+---------------+                       +------------------+
   |   |   |
   |   |   +--------------------------> |  CERTIFICATION   | (1:N)
   |   +------------------------------> |     PROJECT      | (1:N)
   +----------------------------------> |    INTERNSHIP    | (1:N)
   |
   | 1:N
   v
+---------------+          1:N          +------------------+
|  APPLICATION  | <-------------------- |     COMPANY      |
+---------------+                       +------------------+
   |                                       |       |
   | 1:N                                   | 1:N   | 1:N
   v                                       v       v
+---------------+             +----------------+  +------------------+
|   INTERVIEW   |             | COMPANY_BRANCH |  |  COMPANY_SKILL   |
+---------------+             +----------------+  +------------------+
   |
   | (Tracks Final Status)
   v
+---------------+
|   PLACEMENT   | (Final Offer Record)
+---------------+
```

### **Cardinality & Business Rules**
1. **Student to Application ($1 : N$):** A student can apply to multiple company drives, but only once per company (`UNIQUE(student_id, company_id)`).
2. **Company to Application ($1 : N$):** A company receives applications from multiple students.
3. **Application to Interview ($1 : N$):** Each application progresses through sequential interview rounds (`UNIQUE(application_id, round_number)`).
4. **Student to Skills/Projects/Certifications ($1 : N$):** Multi-valued student attributes are normalized into separate child tables.
5. **Company to Allowed Branches/Required Skills ($1 : N$):** Multi-valued job drive criteria are normalized.

---

## 🗄️ 3. Database Normalization (1NF to 3NF/BCNF)

During project evaluation, explain the schema evolution to prove good database design:

| Normal Form | Rule Applied in This Project | Example from Schema |
|---|---|---|
| **1NF (First Normal Form)** | Removed multi-valued & comma-separated attributes. All column values are atomic. | Instead of storing `"Python, Java, React"` in a single column in `STUDENT`, created separate `STUDENT_SKILL` table with atomic `(student_id, skill_name, proficiency_level)`. Same for `COMPANY_BRANCH`. |
| **2NF (Second Normal Form)** | Must be in 1NF and have **no partial functional dependencies** (every non-key attribute is fully functionally dependent on the entire primary key). | In `STUDENT_SKILL(student_id, skill_name)`, `proficiency_level` depends on both `student_id` and `skill_name`. In `INTERVIEW`, all attributes (`score`, `feedback`, `status`) depend entirely on `interview_id`. |
| **3NF (Third Normal Form)** | Must be in 2NF and have **no transitive dependencies** ($X \rightarrow Y$ and $Y \rightarrow Z$). | We do not store `student_name`, `cgpa`, or `company_name` in `APPLICATION` or `INTERVIEW` table. Non-key attributes depend only on the primary key, avoiding update anomalies. |

---

## 🛡️ 4. Integrity Constraints & Domain Rules

Explain how the database guarantees data consistency at the engine level:

### 1. **Entity Integrity (Primary Keys)**
* `STUDENT.student_id` (PK)
* `COMPANY.company_id` (PK)
* `APPLICATION.application_id` (PK)
* `INTERVIEW.interview_id` (PK)
* Composite PKs: `STUDENT_SKILL(student_id, skill_name)`, `COMPANY_BRANCH(company_id, branch_name)`

### 2. **Referential Integrity (Foreign Keys with CASCADE)**
* `APPLICATION` $\rightarrow$ `STUDENT(student_id) ON DELETE CASCADE`
* `APPLICATION` $\rightarrow$ `COMPANY(company_id) ON DELETE CASCADE`
* `INTERVIEW` $\rightarrow$ `APPLICATION(application_id) ON DELETE CASCADE`

### 3. **Unique Constraints (Business Logic Enforcement)**
```sql
CONSTRAINT uq_student_company_app UNIQUE (student_id, company_id)
CONSTRAINT uq_app_round UNIQUE (application_id, round_number)
```

### 4. **Check / Domain Constraints (Data Validation)**
```sql
-- Academic Boundaries
CONSTRAINT chk_stud_cgpa CHECK (cgpa BETWEEN 0.00 AND 10.00)
CONSTRAINT chk_stud_tenth CHECK (tenth_percentage BETWEEN 0.00 AND 100.00)
CONSTRAINT chk_stud_backlogs CHECK (backlogs >= 0)

-- Evaluation & Score Boundaries
CONSTRAINT chk_interview_score CHECK (score BETWEEN 0.00 AND 100.00)

-- State Machines (Enumerated Check Constraints)
CONSTRAINT chk_app_status CHECK (status IN ('Applied', 'Shortlisted', 'In Review', 'Rejected', 'Selected'))
CONSTRAINT chk_interview_status CHECK (status IN ('Scheduled', 'Passed', 'Failed', 'Pending'))
```

---

## 💻 5. Key SQL Queries for Review Demonstration

### **Query 1: Complex Multi-Table JOIN (Student Application & Interview Status)**
> *Shows all candidate applications, company packages, and latest interview rounds.*

```sql
SELECT 
    s.student_id,
    s.student_name,
    s.branch,
    s.cgpa,
    c.company_name,
    c.job_role,
    c.package AS package_lpa,
    a.application_date,
    a.status AS application_status,
    i.round_number,
    i.round_name,
    i.score AS interview_score,
    i.status AS round_result
FROM APPLICATION a
JOIN STUDENT s ON a.student_id = s.student_id
JOIN COMPANY c ON a.company_id = c.company_id
LEFT JOIN INTERVIEW i ON a.application_id = i.application_id
ORDER BY s.student_name, a.application_id, i.round_number;
```

---

### **Query 2: Branch-wise Placement Analytics (Aggregation + GROUP BY)**
> *Calculates total offers, average package, and highest package secured per engineering branch.*

```sql
SELECT 
    s.branch,
    COUNT(DISTINCT s.student_id) AS total_registered,
    COUNT(DISTINCT p.placement_id) AS total_placed,
    ROUND((COUNT(DISTINCT p.placement_id) * 100.0) / COUNT(DISTINCT s.student_id), 2) AS placement_percentage,
    ROUND(AVG(p.package_offered), 2) AS avg_package_lpa,
    MAX(p.package_offered) AS highest_package_lpa
FROM STUDENT s
LEFT JOIN PLACEMENT p ON s.student_id = p.student_id AND p.acceptance_status = 'Accepted'
GROUP BY s.branch
ORDER BY highest_package_lpa DESC NULLS LAST;
```

---

### **Query 3: Company-Specific Eligibility Verification Query**
> *Demonstrates evaluating a student against dynamic company cutoffs (No Global Rules).*

```sql
SELECT 
    s.student_name,
    c.company_name,
    CASE WHEN s.cgpa >= c.required_cgpa THEN 'PASS' ELSE 'FAIL' END AS cgpa_check,
    CASE WHEN s.tenth_percentage >= c.min_tenth_percentage THEN 'PASS' ELSE 'FAIL' END AS tenth_check,
    CASE WHEN s.twelfth_percentage >= c.min_twelfth_percentage THEN 'PASS' ELSE 'FAIL' END AS twelfth_check,
    CASE WHEN s.backlogs <= c.max_backlogs THEN 'PASS' ELSE 'FAIL' END AS backlog_check,
    CASE WHEN EXISTS (
        SELECT 1 FROM COMPANY_BRANCH cb 
        WHERE cb.company_id = c.company_id AND cb.branch_name = s.branch
    ) THEN 'PASS' ELSE 'FAIL' END AS branch_check
FROM STUDENT s, COMPANY c
WHERE s.student_id = :selected_student_id 
  AND c.company_id = :selected_company_id;
```

---

### **Query 4: Top Performing Students by Interview Average (Subquery + HAVING)**
> *Finds students with an average interview score $\ge 85$ across multiple rounds.*

```sql
SELECT 
    s.student_name,
    s.branch,
    c.company_name,
    COUNT(i.interview_id) AS rounds_faced,
    ROUND(AVG(i.score), 2) AS avg_interview_score
FROM INTERVIEW i
JOIN APPLICATION a ON i.application_id = a.application_id
JOIN STUDENT s ON a.student_id = s.student_id
JOIN COMPANY c ON a.company_id = c.company_id
WHERE i.score IS NOT NULL
GROUP BY s.student_name, s.branch, c.company_name
HAVING AVG(i.score) >= 85.0
ORDER BY avg_interview_score DESC;
```

---

## ⚡ 6. ACID Properties & Transaction Management

Explain how the Python Flask backend interacts with Oracle SQL securely:

1. **Atomicity & Consistency:**
   - Multi-step operations (e.g., creating a company and inserting normalized branch/skill records) are wrapped within single database transactions.
   - `conn.commit()` is issued only when all sub-records succeed; `conn.rollback()` executes if an exception occurs.
2. **Isolation:**
   - Handled via Oracle's Read Committed isolation level to prevent dirty reads.
3. **Durability:**
   - Oracle Redo logs and committed transactions persist across application server restarts.
4. **Security & SQL Injection Prevention:**
   - All backend queries strictly use **parameterized bind variables** (`:id`, `:sid`, `:cid`) rather than string concatenation.

---

## 🎯 7. Top 10 Expected Viva Questions & Model Answers

### **Q1: Why did you choose Oracle SQL over SQLite or MySQL?**
> **Answer:** Oracle SQL provides enterprise-grade constraint enforcement (`CHECK`, composite `UNIQUE`, `CASCADE` triggers), robust sequence generation (`NVL(MAX(...), 0) + 1`), strict ACID compliance, and rich analytical functions for heavy data warehousing and placement reporting.

### **Q2: Why is there no global eligibility cutoff in your system?**
> **Answer:** Real campus placement drives have company-specific criteria. A tier-1 product company might require 8.5 CGPA with 0 backlogs and CSE/IT branches only, while a mass recruiter might allow 6.5 CGPA with 2 backlogs across all branches. Our schema normalizes criteria per company in `COMPANY`, `COMPANY_BRANCH`, and `COMPANY_SKILL`.

### **Q3: How do you prevent a student from applying twice to the same company?**
> **Answer:** We enforce this at both database and application levels:
> 1. At the Database layer: Unique constraint `CONSTRAINT uq_student_company_app UNIQUE (student_id, company_id)`.
> 2. At the Application layer: A pre-check query checks `COUNT(*) WHERE student_id = :sid AND company_id = :cid` before initiating the insert.

### **Q4: What happens if a student record is deleted?**
> **Answer:** Due to `ON DELETE CASCADE` on all foreign key constraints (`STUDENT_SKILL`, `CERTIFICATION`, `PROJECT`, `INTERNSHIP`, `APPLICATION`), deleting a student cleanly removes all child records, preventing orphaned tuples and maintaining referential integrity.

### **Q5: In which Normal Form is your database schema?**
> **Answer:** The schema is fully in **3NF / BCNF**. Multi-valued attributes are separated into child tables (1NF), all non-key columns depend strictly on the complete primary key (2NF), and there are no transitive dependencies between non-key attributes (3NF).

### **Q6: How do you validate student skills against company required skills?**
> **Answer:** We execute a relational comparison between `STUDENT_SKILL` (containing student proficiency) and `COMPANY_SKILL` (containing required proficiency: Beginner $\le$ Intermediate $\le$ Expert), validating that the student possesses all mandatory skills at or above the minimum required level.

### **Q7: What is the relationship between APPLICATION and INTERVIEW tables?**
> **Answer:** It is a $1 : N$ (One-to-Many) relationship. An application can have multiple sequential interview rounds (Round 1: Coding, Round 2: Technical, Round 3: HR). Each round has its own score, date, result, and feedback.

### **Q8: How do you protect your backend against SQL Injection?**
> **Answer:** We never concatenate user inputs directly into SQL strings. We use Oracle named bind parameters (`:param_name`) with `python-oracledb`, ensuring the database engine treats all input values strictly as literals.

### **Q9: Can an ineligible student force an application into the database?**
> **Answer:** No. When a user submits an application, the backend runs the 6-point eligibility audit (`check_eligibility()`). If any criterion fails (CGPA, 10th %, 12th %, backlogs, branch, or skills), the transaction is blocked, and all failed reasons are returned to the user.

### **Q10: What is the role of the PLACEMENT table?**
> **Answer:** While `APPLICATION` tracks the entire funnel (Applied, Shortlisted, In Review, Rejected, Selected), `PLACEMENT` stores the final offer details (salary package offered, offer letter date, acceptance status, joining date) for selected candidates.

### **Q11: How do you guarantee zero duplicate counting in placement percentage calculations?**
> **Answer:** A candidate may hold multiple applications and interview records across different drives. To prevent double counting, our analytics queries strictly apply `COUNT(DISTINCT s.student_id)` and join against `PLACEMENT` records with `acceptance_status = 'Accepted'`. Safe division using `NULLIF` and `CASE` statements protects against division-by-zero when no students are registered.

---

## 📈 8. Phase 7: Real-Time Analytics & JSON Reporting APIs

| Endpoint | Method | Output Format | Description |
|---|---|---|---|
| `/analytics/overview` | `GET` | JSON | Executive KPI summary cards (students, placed, %, apps, active companies, package benchmarks) |
| `/analytics/applications` | `GET` | JSON | Application counts (selected, rejected, pending), full status distribution, chart payload, company breakdown |
| `/analytics/placement-summary` | `GET` | JSON | Institute placement rate, salary benchmarks (highest, average, median, lowest LPA), department-wise breakdown, company conversion funnel |
| `/analytics` or `/analytics/dashboard` | `GET` | HTML / JSON | Interactive visual analytics dashboard with live Chart.js donut chart and metrics cards |

---
*Created for DBMS Project Evaluation & Viva Defense &bull; Campus Placement Analytics System*

