"""
Campus Placement Analytics System - Database Connection Module
Phase 2: Oracle SQL Database Connection using python-oracledb (Thin Mode)
"""

import os
import oracledb

# ============================================================================
# LOAD CONFIGURATION FROM .env FILE
# ============================================================================
def _load_env_file():
    """Loads environment variables from .env file with fallback parser."""
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        # Simple native fallback parser if python-dotenv is not installed
        env_path = os.path.join(os.path.dirname(__file__), ".env")
        if os.path.exists(env_path):
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, val = line.split("=", 1)
                        key = key.strip()
                        val = val.strip().strip("'\"")
                        if key not in os.environ:
                            os.environ[key] = val

_load_env_file()

# ============================================================================
# ORACLE DATABASE CONFIGURATION
# ----------------------------------------------------------------------------
# Reads from .env file or environment variables.
# Fallback defaults are provided if .env is missing.
# ============================================================================
DB_USER = os.getenv("ORACLE_DB_USER", "your_username")
DB_PASSWORD = os.getenv("ORACLE_DB_PASSWORD", "your_password")
DB_DSN = os.getenv("ORACLE_DB_DSN", "localhost:1521/XEPDB1")


def get_db_connection():
    """
    Establishes and returns an active connection to the Oracle database.
    Uses python-oracledb Thin Mode by default (no Oracle Instant Client needed).
    
    Raises:
        oracledb.Error: If the connection to Oracle fails.
    """
    connection = oracledb.connect(
        user=DB_USER,
        password=DB_PASSWORD,
        dsn=DB_DSN
    )
    return connection


def test_connection():
    """
    Verifies that the Oracle database is reachable and credentials are valid.
    
    Returns:
        tuple: (bool: is_connected, str: message_or_version)
    """
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT banner FROM v$version WHERE ROWNUM = 1")
            row = cursor.fetchone()
            version_banner = row[0] if row else "Connected to Oracle Database"
        conn.close()
        return True, version_banner
    except oracledb.Error as e:
        error_obj, = e.args
        error_msg = f"Oracle Connection Failed: {error_obj.message}"
        print(f"[ERROR] {error_msg}")
        return False, error_msg
    except Exception as ex:
        error_msg = f"Unexpected Error: {str(ex)}"
        print(f"[ERROR] {error_msg}")
        return False, error_msg
