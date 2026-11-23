"""Supabase access for the Ashoka Industries dashboard."""

import os
from datetime import date, datetime
from decimal import Decimal

import httpx
import pandas as pd
import streamlit as st
from postgrest.exceptions import APIError
from supabase import Client, create_client

from dotenv import load_dotenv

load_dotenv()

TABLE_COLUMNS = {
    "sales": [
        "sale_id", "sale_date", "bill_no", "customer_name", "quantity",
        "amount", "transaction_type", "period",
    ],
    "purchases": [
        "purchase_id", "purchase_date", "bill_no", "item_name", "hsn_code",
        "gst_amount", "purchase_amount", "period",
    ],
    "consumables": [
        "consumable_id", "consumable_date", "bill_no", "item_name",
        "quantity", "amount", "period",
    ],
    "sales_adjustments": [
        "adjustment_id", "adjustment_date", "reference", "description",
        "amount", "adjustment_type",
    ],
}

TABLE_PRIMARY_KEYS = {
    "sales": "sale_id",
    "purchases": "purchase_id",
    "consumables": "consumable_id",
    "sales_adjustments": "adjustment_id",
}

DATE_COLUMNS = {
    "sales": "sale_date",
    "purchases": "purchase_date",
    "consumables": "consumable_date",
    "sales_adjustments": "adjustment_date",
}
PAGE_SIZE = 1000


def _config_value(key: str):
    value = os.getenv(key)
    if value:
        return value
    try:
        return st.secrets.get(key)
    except (FileNotFoundError, KeyError):
        return None


@st.cache_resource(show_spinner=False)
def get_client() -> Client:
    """Create the server-side Supabase client from environment/Streamlit secrets."""
    url = _config_value("SUPABASE_URL")
    key = _config_value("SUPABASE_SERVICE_ROLE_KEY") or _config_value(
        "SUPABASE_SECRET_KEY"
    )
    if not url or not key:
        raise ValueError(
            "Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY "
            "(or SUPABASE_SECRET_KEY) in the app environment or Streamlit secrets."
        )
    return create_client(url, key)


def get_status():
    """Return (is_connected, message) for the sidebar database status."""
    try:
        get_client().table("sales").select("sale_id").limit(1).execute()
        return True, "Connected to Supabase"
    except (ValueError, APIError, httpx.HTTPError) as error:
        st.session_state["db_error"] = str(error)
        return False, str(error)


@st.cache_data(ttl=60, show_spinner=False)
def fetch_table(table: str) -> pd.DataFrame:
    """Fetch every row from a dashboard table, paginating past the API row limit."""
    if table not in TABLE_COLUMNS:
        raise ValueError(f"Unknown dashboard table: {table}")

    client = get_client()
    rows = []
    offset = 0
    while True:
        response = (
            client.table(table)
            .select("*")
            .range(offset, offset + PAGE_SIZE - 1)
            .execute()
        )
        page = response.data or []
        rows.extend(page)
        if len(page) < PAGE_SIZE:
            break
        offset += PAGE_SIZE

    frame = pd.DataFrame(rows, columns=TABLE_COLUMNS[table])
    date_column = DATE_COLUMNS[table]
    frame[date_column] = pd.to_datetime(frame[date_column], errors="coerce")
    return frame


def _json_value(value):
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return str(value)
    return value


def _request_error(error):
    return f"Supabase operation failed: {error}"


def insert_record(table: str, values: dict):
    try:
        result = get_client().table(table).insert(
            {key: _json_value(value) for key, value in values.items()}
        ).select(TABLE_PRIMARY_KEYS[table]).execute()
        count = len(result.data or [])
        return True, f"Record added to Supabase. Rows affected: {count}"
    except (ValueError, APIError, httpx.HTTPError) as error:
        return False, _request_error(error)


def update_record(table: str, record_id, values: dict):
    primary_key = TABLE_PRIMARY_KEYS[table]
    try:
        result = (
            get_client()
            .table(table)
            .update({key: _json_value(value) for key, value in values.items()})
            .eq(primary_key, record_id)
            .select(primary_key)
            .execute()
        )
        count = len(result.data or [])
        if not count:
            return False, "No matching record was updated."
        return True, f"Record updated in Supabase. Rows affected: {count}"
    except (ValueError, APIError, httpx.HTTPError) as error:
        return False, _request_error(error)


def delete_record(table: str, record_id):
    primary_key = TABLE_PRIMARY_KEYS[table]
    try:
        result = (
            get_client()
            .table(table)
            .delete()
            .eq(primary_key, record_id)
            .select(primary_key)
            .execute()
        )
        count = len(result.data or [])
        if not count:
            return False, "No matching record was deleted."
        return True, f"Record deleted from Supabase. Rows affected: {count}"
    except (ValueError, APIError, httpx.HTTPError) as error:
        return False, _request_error(error)
