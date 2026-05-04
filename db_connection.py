# db_connection.py
# Handles MySQL database connection using mysql-connector-python

import mysql.connector
from mysql.connector import Error
import os

# ── Connection Configuration ────────────────────────────────
DB_CONFIG = {
    "host":     os.getenv("DB_HOST",     "localhost"),
    "user":     os.getenv("DB_USER",     "root"),
    "password": os.getenv("DB_PASSWORD", "haidang249"),          
    "database": os.getenv("DB_NAME",     "delivery_system"),
    "charset":  "utf8mb4",
}


def get_connection():
    """Return a new MySQL connection. Raises on failure."""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except Error as e:
        raise ConnectionError(f"[DB] Cannot connect to MySQL: {e}")


def test_connection():
    """Quick connectivity check. Prints status."""
    try:
        conn = get_connection()
        print(f"[DB] Connected  →  {DB_CONFIG['host']} / {DB_CONFIG['database']}")
        conn.close()
        return True
    except ConnectionError as e:
        print(e)
        return False