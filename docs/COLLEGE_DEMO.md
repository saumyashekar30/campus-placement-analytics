# College Demo and Viva Guide

**Campus Placement Analytics System — Oracle SQL + Flask**

This is a DBMS course project. The main evidence is **Oracle schema design, constraints, queries and their integration with Flask**. The browser's synthetic sample mode is only a UI backup.

## A. Before the review

- [ ] Have Python and project dependencies installed: `pip install -r requirements.txt`.
- [ ] Start Oracle Database XE / an Oracle pluggable DB and connect through SQL Developer.
- [ ] Configure your private `.env` with `ORACLE_DB_USER`, `ORACLE_DB_PASSWORD` and `ORACLE_DB_DSN`.
- [ ] Initialize the schema once with `@database/run_all.sql` on a **disposable** Oracle project account. This resets project tables.
- [ ] Confirm all 11 tables exist; **do not rerun** setup once you create demonstration records you want to retain.
- [ ] Start `python app.py` and open `http://127.0.0.1:5000/analytics`.
- [ ] Confirm the dashboard displays **real seeded data for 2024**, not “Sample Preview”.
- [ ] Prepare a copy of the SQL queries and the source code in VS Code/SQL Developer.
- [ ] Leave passwords out of screenshots, screen shares and presentation slides.

If Oracle is not available, use **Sample Preview**, but state explicitly that it is a frontend demonstration and not a database-backed result. Do not claim database integration passed without connecting an Oracle instance.

## B. Suggested five-minute demo

| Time | Show | Explain |
| --- | --- | --- |
| 0:00–0:40 | Problem statement + SQL schema | Why a relational database replaces manual spreadsheets |
| 0:40–1:30 | Oracle tables + primary/foreign keys | 11 tables; normalization; links between students, companies and applications |
| 1:30–2:20 | Students and Companies screens | Basic CRUD and varying recruiter eligibility criteria |
| 2:20–3:10 | Applications + interview rounds | Unique company applications, status rules, multi-round interview records |
| 3:10–4:10 | Analytics dashboard + filters | Application status, distinct placed students, packages, branch and company charts |
| 4:10–5:00 | SQL query and updated result | Show a real SQL aggregation, then refresh the UI to explain the Flask API flow |

The **three presenters** can split this naturally: Person 1 covers overall/applications; Person 2 covers company/branch/packages; Person 3 covers interviews/dashboard.

## C. Seeded 2024 Oracle data: expected answers

On a freshly seeded schema, the SQL files provide:

| Check | Expected value |
| --- | ---: |
| Students | 10 |
| Companies | 5 |
| Applications | 16 |
| Selected applications | 6 |
| Rejected applications | 1 |
| In-process applications | 9 |
| Accepted placement records | 6 |
| Distinct placed students | 6 |
| Placement percentage | 60% |
| Interview rounds | 16 |
| Passed rounds | 15 |
| Failed rounds | 1 |
| Highest accepted package | ₹24.00 LPA |
| Lowest accepted package | ₹5.50 LPA |
| Average accepted package | ₹12.92 LPA (rounded) |

These expected answers are based on the checked-in `database/02_seed_data.sql`; they have **not been validated against a live Oracle instance in the automated browser test environment**.

## D. SQL queries to demonstrate

Run these against the actual seeded Oracle schema. You should be able to explain every JOIN, WHERE and GROUP BY.

**1. All entity tables (schema verification)**

```sql
SELECT table_name
FROM user_tables
WHERE table_name IN ('STUDENT','STUDENT_SKILL','CERTIFICATION',
  'PROJECT','INTERNSHIP','COMPANY','COMPANY_BRANCH',
  'COMPANY_SKILL','APPLICATION','INTERVIEW','PLACEMENT')
ORDER BY table_name;
```

**2. Registered and uniquely placed students**

```sql
SELECT
  (SELECT COUNT(*) FROM STUDENT) AS total_students,
  (SELECT COUNT(DISTINCT student_id)
   FROM PLACEMENT WHERE acceptance_status = 'Accepted') AS placed_students
FROM dual;
```

**3. Application status pipeline**

```sql
SELECT status, COUNT(*) AS total
FROM APPLICATION
GROUP BY status
ORDER BY status;
```

**4. Company-wise placement counts**

```sql
SELECT c.company_name,
       COUNT(DISTINCT p.student_id) AS placed_students
FROM COMPANY c
LEFT JOIN PLACEMENT p ON c.company_id = p.company_id
                      AND p.acceptance_status = 'Accepted'
GROUP BY c.company_name
ORDER BY placed_students DESC, c.company_name;
```

**5. Branch-wise placement percentages**

```sql
SELECT s.branch,
       COUNT(DISTINCT s.student_id) AS total,
       COUNT(DISTINCT p.student_id) AS placed,
       ROUND(100 * COUNT(DISTINCT p.student_id) /
             NULLIF(COUNT(DISTINCT s.student_id), 0), 2) AS placement_pct
FROM STUDENT s
LEFT JOIN PLACEMENT p ON s.student_id = p.student_id
                     AND p.acceptance_status = 'Accepted'
GROUP BY s.branch ORDER BY s.branch;
```

**6. Accepted package statistics (in LPA)**

```sql
SELECT ROUND(AVG(package_offered), 2) AS avg_lpa,
       MAX(package_offered) AS highest_lpa,
       MIN(package_offered) AS lowest_lpa
FROM PLACEMENT WHERE acceptance_status = 'Accepted';
```

**7. Interview success rate (completed rounds only)**

```sql
SELECT SUM(CASE WHEN status = 'Passed' THEN 1 ELSE 0 END) AS passed,
       SUM(CASE WHEN status = 'Failed' THEN 1 ELSE 0 END) AS failed,
       ROUND(100 * SUM(CASE WHEN status = 'Passed' THEN 1 ELSE 0 END) /
           NULLIF(SUM(CASE WHEN status IN ('Passed','Failed') THEN 1 ELSE 0 END), 0), 2) AS pass_pct
FROM INTERVIEW;
```

## E. Suggested interactive CRUD demonstration

After running the setup (and confirming `06_sync_identity.sql` ran):

1. Open **Students → Add Student**. Enter a new dummy student with a unique email and valid marks/CGPA; save it.
2. Confirm the row was inserted by running `SELECT * FROM STUDENT ORDER BY student_id DESC;` in SQL Developer.
3. Open that student's profile, edit one harmless field, save and show the updated SQL row.
4. Compare eligibility against one of the five existing recruiters to demonstrate company-specific constraints.
5. Add an application for the new student using the Application form and show the `APPLICATION` row.
6. Refresh Analytics and explain the changed registered-student/application totals.
7. Optional: Remove only the dummy record through the app (avoid deleting seeded examples during your viva).

**Identity-key note:** The seed uses fixed IDs to make JOIN demonstrations repeatable. `database/06_sync_identity.sql` advances each identity generator to the first available value so CRUD insertions don't collide with the seeded keys.

## F. Common viva questions

**Why use a DBMS rather than Excel?** Constraints, efficient joins, consistent updates, fewer duplicate records, and reusable aggregate queries.

**What is normalization?** Splitting data so each relation models one entity/fact. Here student skills and company-eligible branches have separate child tables; this avoids repeated multi-value fields.

**Primary key versus foreign key?** A primary key uniquely identifies each row. A foreign key references another table and enforces referential integrity.

**Why a composite key?** For example `STUDENT_SKILL(student_id, skill_name)` prevents recording the same skill twice for the same student.

**What is the relationship among Student, Company and Application?** Each student can submit many applications; each company receives many applications; one student-company combination is unique.

**Why count distinct students?** Students may apply to multiple companies. The placement percentage must count each successfully placed student once, rather than counting applications.

**How do you calculate percentage?** Placed distinct students ÷ total registered students × 100. The example has 6 ÷ 10 × 100 = 60%.

**What does the backend do?** Flask registers routes, executes Oracle queries with `python-oracledb`, converts rows into JSON or Jinja templates, and serves Chart.js-ready data.

**How is SQL injected safely?** Variable filter values use Oracle bind parameters instead of concatenating user input into SQL statements.

**What happens if Oracle is down?** Dashboard endpoints return errors and the UI can show a clearly labeled synthetic preview; database updates cannot work until Oracle is reconnected.

## G. Review limitations

- No live Oracle server is provided in the repository; each college team must configure one.
- All browser automation with simulated API responses checks frontend/Flask integration, **not** whether queries run correctly on a particular Oracle version.
- The synthetic preview and fictitious SQL seed are **two different datasets**. Never combine their numbers in a project report.
- This is an **academic demonstration**. University-wide access control, student data privacy compliance and large-scale deployment are outside the submission scope.
