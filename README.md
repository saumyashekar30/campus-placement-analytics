# Campus Placement Analytics System

A comprehensive College Project for tracking student academic profiles, recruitment drives, dynamic company eligibility criteria, multi-round interviews, and final placement records.

---

## 📁 Project Structure

```text
Campus_Placement_project/
├── requirements.txt         # Dependencies: Flask, oracledb
├── database.py              # Oracle connection manager (thin mode)
├── app.py                   # Flask server, routes, and query handlers
├── database/                # Oracle SQL scripts
│   ├── 01_schema.sql        # 11 normalized tables, identity PKs, constraints
│   ├── 02_seed_data.sql     # 10 students, 5 companies, skills, apps, interviews, placements
│   ├── 03_queries.sql       # Analytical and verification queries
│   ├── 04_analytics_queries.sql # Phase 7: Placement, application & KPI analytics queries
│   └── run_all.sql          # Master runner script
├── routes/                  # Flask Route Blueprints
│   ├── student_routes.py    # Student profile CRUD
│   ├── company_routes.py    # Company recruitment drive management
│   ├── eligibility_routes.py# Dynamic 6-point eligibility audit
│   ├── application_routes.py# Student applications & interview pipeline
│   ├── interview_routes.py  # Multi-round evaluations & scores
│   └── analytics_routes.py  # Phase 7: Real-time Analytics JSON APIs & Dashboard
├── templates/
│   ├── base.html            # Navigation header and layout shell
│   ├── index.html           # Home page with live connection status
│   ├── analytics/           # Phase 7: Placement & Application Analytics view
│   ├── students.html        # Students table view
│   ├── companies.html       # Companies table view
│   └── error.html           # 404 / 500 error page
└── static/
    └── css/
        └── style.css        # Clean, modern CSS design
```

---

## ⚙️ Configuration (One-Time Setup)

Open [`database.py`](file:///c:/Users/Saumya/OneDrive/Desktop/Campus_Placement_project/database.py) and update your Oracle credentials:

```python
DB_USER = "your_username"      # e.g., "system" or your dedicated user
DB_PASSWORD = "your_password"  # Your Oracle database password
DB_DSN = "localhost:1521/XEPDB1"
```

---

## 🚀 How to Run on Windows

### 1. (Optional) Create & Activate Virtual Environment
Open PowerShell in the project directory:
```powershell
python -m venv venv
venv\Scripts\activate
```

### 2. Install Dependencies
```powershell
pip install -r requirements.txt
```

### 3. Start the Flask Backend
```powershell
python app.py
```

### 4. Open in Your Browser
Visit [http://127.0.0.1:5000](http://127.0.0.1:5000) in your browser:
- **Home**: `http://127.0.0.1:5000/` (Displays Flask status and Oracle connection test)
- **Analytics Dashboard**: `http://127.0.0.1:5000/analytics` (KPI cards, charts & benchmarks)
- **Students**: `http://127.0.0.1:5000/students` (Displays student records from Oracle)
- **Companies**: `http://127.0.0.1:5000/companies` (Displays company drives from Oracle)
- **Applications**: `http://127.0.0.1:5000/applications` (Application tracking pipeline)

### 5. Analytics JSON REST APIs
- `GET http://127.0.0.1:5000/analytics/overview` (Executive summary cards KPI payload)
- `GET http://127.0.0.1:5000/analytics/applications` (Application counts, statuses & chart data)
- `GET http://127.0.0.1:5000/analytics/placement-summary` (Unique placed counts, percentages & branch metrics)

