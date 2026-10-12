"""
Campus Placement Analytics System - Flask Application
Phase 3: Student Management Module (Full CRUD & Profile Management)
"""

import os
from decimal import Decimal
from flask import Flask, render_template, request
import database
from routes.student_routes import student_bp
from routes.company_routes import company_bp
from routes.eligibility_routes import eligibility_bp
from routes.application_routes import application_bp
from routes.interview_routes import interview_bp
from routes.analytics_routes import analytics_bp
from routes.company_analytics_routes import company_analytics_bp


def _to_python(v):
    """Convert Oracle Decimal types to float for template compatibility."""
    return float(v) if isinstance(v, Decimal) else v

app = Flask(__name__)

# Secret key required for session management and flash alert banners
app.secret_key = os.getenv("SECRET_KEY", "campus_placement_secret_key_2024")

# Register Blueprints
app.register_blueprint(student_bp)
app.register_blueprint(company_bp)
app.register_blueprint(eligibility_bp)
app.register_blueprint(application_bp)
app.register_blueprint(interview_bp)
app.register_blueprint(analytics_bp)
app.register_blueprint(company_analytics_bp)



@app.route("/")
def home():
    """
    Home Route:
    - Confirms Flask backend is active.
    - Tests the Oracle database connection in real-time.
    - Fetches total student, company, and application counts if the database is accessible.
    """
    db_connected, db_message = database.test_connection()
    student_count = 0
    company_count = 0
    application_count = 0
    selected_count = 0
    placed_count = 0
    placement_pct = 0.0

    if db_connected:
        try:
            conn = database.get_db_connection()
            with conn.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM STUDENT")
                row = cursor.fetchone()
                student_count = row[0] if row else 0

                cursor.execute("SELECT COUNT(*) FROM COMPANY")
                row = cursor.fetchone()
                company_count = row[0] if row else 0

                cursor.execute("SELECT COUNT(*) FROM APPLICATION")
                row = cursor.fetchone()
                application_count = row[0] if row else 0

                cursor.execute("SELECT COUNT(*) FROM APPLICATION WHERE status = 'Selected'")
                row = cursor.fetchone()
                selected_count = row[0] if row else 0

                cursor.execute("""
                    SELECT COUNT(DISTINCT p.student_id)
                    FROM PLACEMENT p
                    WHERE p.acceptance_status = 'Accepted'
                """)
                p_row = cursor.fetchone()
                placed_count = p_row[0] if p_row else 0
                placement_pct = round((placed_count * 100.0) / student_count, 2) if student_count > 0 else 0.0

            conn.close()
        except Exception as e:
            print(f"[WARNING] Could not fetch table counts: {e}")

    return render_template(
        "index.html",
        backend_status=True,
        db_connected=db_connected,
        db_message=db_message,
        student_count=student_count,
        company_count=company_count,
        application_count=application_count,
        selected_count=selected_count,
        placed_count=placed_count,
        placement_pct=placement_pct
    )



# ----------------------------------------------------------------------------
# Error Handlers
# ----------------------------------------------------------------------------
@app.errorhandler(404)
def page_not_found(e):
    return render_template(
        "error.html",
        error_code=404,
        error_title="Page Not Found",
        error_description="The page you requested could not be found."
    ), 404


@app.errorhandler(500)
def internal_server_error(e):
    return render_template(
        "error.html",
        error_code=500,
        error_title="Internal Server Error",
        error_description="An unexpected error occurred while processing your request."
    ), 500


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("  CAMPUS PLACEMENT ANALYTICS SYSTEM - FLASK BACKEND")
    print("  Server running at: http://127.0.0.1:5000")
    print("=" * 60 + "\n")
    app.run(debug=True, port=5000)
