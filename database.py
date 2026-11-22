"""
database.py
------------
Handles the live MySQL connection for the Ashoka Industries dashboard.

Credentials are read from environment variables (via a local .env file,
see .env.example) so nothing sensitive is hard-coded or committed.
"""

import os
import streamlit as st
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", "3306")),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME", "ashoka_industries"),
}


@st.cache_resource(show_spinner=False)
def get_connection():
    """
    Creates (and caches) a single live MySQL connection for the app's
    lifetime. Streamlit re-uses this across reruns instead of opening
    a new connection on every interaction.
    """
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except Error as e:
        st.session_state["db_error"] = str(e)
        return None


def get_status():
    """Returns (is_connected: bool, message: str) for a sidebar status indicator."""
    conn = get_connection()
    if conn is not None and conn.is_connected():
        return True, f"Connected to '{DB_CONFIG['database']}' @ {DB_CONFIG['host']}"
    err = st.session_state.get("db_error", "Unknown connection error")
    return False, err


def run_query(query: str, params=None):
    """
    Executes a read-only SQL query against the live database and
    returns the result as a pandas DataFrame. Returns an empty
    DataFrame (rather than raising) on failure, so the dashboard can
    degrade gracefully with a visible warning instead of crashing.
    """
    import pandas as pd

    conn = get_connection()

    # If the cached connection dropped (e.g. MySQL restarted), retry once.
    if conn is None or not conn.is_connected():
        get_connection.clear()
        conn = get_connection()

    if conn is None:
        st.error(
            "Could not connect to the MySQL database. "
            "Check your `.env` credentials and that MySQL is running."
        )
        return pd.DataFrame()

    try:
        return pd.read_sql(query, conn, params=params)
    except Error as e:
        st.error(f"Query failed: {e}")
        return pd.DataFrame()


def execute_write(query: str, params=None):
    """Execute INSERT/UPDATE/DELETE safely with commit/rollback."""
    conn = get_connection()
    if conn is None or not conn.is_connected():
        get_connection.clear()
        conn = get_connection()
    if conn is None:
        return False, "Database connection unavailable."
    cursor = None
    try:
        cursor = conn.cursor()
        cursor.execute(query, params or ())
        conn.commit()
        return True, f"Operation successful. Rows affected: {cursor.rowcount}"
    except Error as e:
        conn.rollback()
        return False, f"Database operation failed: {e}"
    finally:
        if cursor is not None:
            cursor.close()
