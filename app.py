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


def _to_python(v):
    """Convert Oracle Decimal types to float for template compatibility."""
    return float(v) if isinstance(v, Decimal) else v

app = Flask(__name__)

# Secret key required for session management and flash alert banners
app.secret_key = os.getenv("SECRET_KEY", "campus_placement_secret_key_2024")

# Register Blueprints
app.register_blueprint(student_bp)
app.register_blueprint(company_bp)


@app.route("/")
def home():
    """
    Home Route:
    - Confirms Flask backend is active.
    - Tests the Oracle database connection in real-time.
    - Fetches total student and company counts if the database is accessible.
    """
    db_connected, db_message = database.test_connection()
    student_count = 0
    company_count = 0

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
            conn.close()
        except Exception as e:
            print(f"[WARNING] Could not fetch table counts: {e}")

    return render_template(
        "index.html",
        backend_status=True,
        db_connected=db_connected,
        db_message=db_message,
        student_count=student_count,
        company_count=company_count
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
