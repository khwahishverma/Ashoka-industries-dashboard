"""
queries.py
----------
All SQL retrieval for the dashboard lives here, one function per
analysis. Every function accepts a (start_date, end_date) tuple so
the sidebar date filter can drive every KPI, chart and table from a
single control.

The underlying logic mirrors the SQL already written and verified in
the MySQL phase of this project (see /sql/schema_setup.sql) - it is
not a new analysis, just the same logic exposed to Python.

Normal sales analysis always filters transaction_type = 'Sale' so
that the one Credit Note row and the separate sales_adjustments
entries never contaminate sales totals, per the project's accounting
rules.
"""

import streamlit as st
import pandas as pd
from database import run_query

CACHE_TTL = 300  # seconds


# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------

def _date_filter(column: str, start_date, end_date) -> str:
    return f"{column} BETWEEN '{start_date}' AND '{end_date}'"


@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def get_date_bounds():
    """Return the full transaction date span for the sidebar's default range."""
    df = run_query("""
        SELECT MIN(d) AS min_date, MAX(d) AS max_date FROM (
            SELECT sale_date AS d FROM sales
            UNION ALL SELECT purchase_date FROM purchases
            UNION ALL SELECT consumable_date FROM consumables
        ) all_dates
    """)
    if df.empty or pd.isna(df.loc[0, "min_date"]):
        fallback = pd.Timestamp.today().date()
        return fallback, fallback
    min_date = pd.to_datetime(df.loc[0, "min_date"]).date()
    max_date = pd.to_datetime(df.loc[0, "max_date"]).date()
    return min_date, max_date


# ---------------------------------------------------------------------
# Executive Overview KPIs
# ---------------------------------------------------------------------

@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def get_total_sales(start_date, end_date):
    q = f"""
        SELECT COALESCE(SUM(amount), 0) AS total_sales
        FROM sales
        WHERE transaction_type = 'Sale' AND {_date_filter('sale_date', start_date, end_date)}
    """
    return float(run_query(q).loc[0, "total_sales"])


@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def get_total_purchases(start_date, end_date):
    q = f"""
        SELECT COALESCE(SUM(purchase_amount), 0) AS total_purchases
        FROM purchases
        WHERE {_date_filter('purchase_date', start_date, end_date)}
    """
    return float(run_query(q).loc[0, "total_purchases"])


@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def get_total_consumables(start_date, end_date):
    q = f"""
        SELECT COALESCE(SUM(amount), 0) AS total_consumables
        FROM consumables
        WHERE {_date_filter('consumable_date', start_date, end_date)}
    """
    return float(run_query(q).loc[0, "total_consumables"])


@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def get_total_quantity_sold(start_date, end_date):
    q = f"""
        SELECT COALESCE(SUM(quantity), 0) AS total_qty
        FROM sales
        WHERE transaction_type = 'Sale' AND {_date_filter('sale_date', start_date, end_date)}
    """
    return float(run_query(q).loc[0, "total_qty"])


@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def get_sales_transaction_count(start_date, end_date):
    q = f"""
        SELECT COUNT(*) AS cnt FROM sales
        WHERE transaction_type = 'Sale' AND {_date_filter('sale_date', start_date, end_date)}
    """
    return int(run_query(q).loc[0, "cnt"])


@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def get_purchase_transaction_count(start_date, end_date):
    q = f"SELECT COUNT(*) AS cnt FROM purchases WHERE {_date_filter('purchase_date', start_date, end_date)}"
    return int(run_query(q).loc[0, "cnt"])


@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def get_consumable_transaction_count(start_date, end_date):
    q = f"SELECT COUNT(*) AS cnt FROM consumables WHERE {_date_filter('consumable_date', start_date, end_date)}"
    return int(run_query(q).loc[0, "cnt"])


@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def get_avg_invoice_value(start_date, end_date):
    q = f"""
        SELECT ROUND(AVG(amount), 2) AS avg_invoice FROM sales
        WHERE transaction_type = 'Sale' AND {_date_filter('sale_date', start_date, end_date)}
    """
    val = run_query(q).loc[0, "avg_invoice"]
    return float(val) if val is not None else 0.0


# ---------------------------------------------------------------------
# Monthly series (Sales / Purchases / Consumables)
# ---------------------------------------------------------------------

@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def get_monthly_sales(start_date, end_date):
    q = f"""
        SELECT DATE_FORMAT(sale_date, '%Y-%m') AS month, SUM(amount) AS monthly_sales
        FROM sales
        WHERE transaction_type = 'Sale' AND {_date_filter('sale_date', start_date, end_date)}
        GROUP BY DATE_FORMAT(sale_date, '%Y-%m')
        ORDER BY month
    """
    return run_query(q)


@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def get_monthly_purchases(start_date, end_date):
    q = f"""
        SELECT DATE_FORMAT(purchase_date, '%Y-%m') AS month, SUM(purchase_amount) AS monthly_purchases
        FROM purchases
        WHERE {_date_filter('purchase_date', start_date, end_date)}
        GROUP BY DATE_FORMAT(purchase_date, '%Y-%m')
        ORDER BY month
    """
    return run_query(q)


@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def get_monthly_consumables(start_date, end_date):
    q = f"""
        SELECT DATE_FORMAT(consumable_date, '%Y-%m') AS month, SUM(amount) AS monthly_consumables
        FROM consumables
        WHERE {_date_filter('consumable_date', start_date, end_date)}
        GROUP BY DATE_FORMAT(consumable_date, '%Y-%m')
        ORDER BY month
    """
    return run_query(q)


@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def get_monthly_sales_ranked(start_date, end_date):
    """Monthly sales with RANK() via a CTE, matching the verified SQL phase result."""
    q = f"""
        WITH monthly_sales AS (
            SELECT DATE_FORMAT(sale_date, '%Y-%m') AS month, SUM(amount) AS total_sales
            FROM sales
            WHERE transaction_type = 'Sale' AND {_date_filter('sale_date', start_date, end_date)}
            GROUP BY DATE_FORMAT(sale_date, '%Y-%m')
        )
        SELECT month, ROUND(total_sales, 2) AS total_sales,
               RANK() OVER (ORDER BY total_sales DESC) AS sales_rank
        FROM monthly_sales
        ORDER BY sales_rank
    """
    return run_query(q)


@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def get_monthly_contribution(start_date, end_date):
    q = f"""
        SELECT month, ROUND(monthly_sales, 2) AS monthly_sales,
               ROUND(monthly_sales * 100 / (
                   SELECT SUM(amount) FROM sales
                   WHERE transaction_type = 'Sale' AND {_date_filter('sale_date', start_date, end_date)}
               ), 2) AS pct_of_total
        FROM (
            SELECT DATE_FORMAT(sale_date, '%Y-%m') AS month, SUM(amount) AS monthly_sales
            FROM sales
            WHERE transaction_type = 'Sale' AND {_date_filter('sale_date', start_date, end_date)}
            GROUP BY DATE_FORMAT(sale_date, '%Y-%m')
        ) monthly
        ORDER BY month
    """
    return run_query(q)


# ---------------------------------------------------------------------
# Sales Analytics
# ---------------------------------------------------------------------

@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def get_top_sales(start_date, end_date, n=10):
    q = f"""
        SELECT sale_date, bill_no, customer_name, quantity, ROUND(amount, 2) AS amount
        FROM sales
        WHERE transaction_type = 'Sale' AND {_date_filter('sale_date', start_date, end_date)}
        ORDER BY amount DESC
        LIMIT {int(n)}
    """
    return run_query(q)


@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def get_customer_wise_sales(start_date, end_date):
    q = f"""
        SELECT customer_name, COUNT(*) AS number_of_transactions,
               SUM(quantity) AS total_quantity, ROUND(SUM(amount), 2) AS total_sales
        FROM sales
        WHERE transaction_type = 'Sale' AND {_date_filter('sale_date', start_date, end_date)}
        GROUP BY customer_name
        ORDER BY total_sales DESC
    """
    return run_query(q)


@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def get_sales_classification(start_date, end_date):
    q = f"""
        SELECT bill_no, sale_date, ROUND(amount, 2) AS amount,
            CASE
                WHEN amount >= 200000 THEN 'High Value'
                WHEN amount >= 100000 THEN 'Medium Value'
                ELSE 'Lower Value'
            END AS sales_category
        FROM sales
        WHERE transaction_type = 'Sale' AND {_date_filter('sale_date', start_date, end_date)}
        ORDER BY amount DESC
    """
    return run_query(q)


@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def get_cumulative_sales(start_date, end_date):
    q = f"""
        SELECT sale_date, bill_no, ROUND(amount, 2) AS amount,
               ROUND(SUM(amount) OVER (ORDER BY sale_date, sale_id), 2) AS cumulative_sales
        FROM sales
        WHERE transaction_type = 'Sale' AND {_date_filter('sale_date', start_date, end_date)}
        ORDER BY sale_date, sale_id
    """
    return run_query(q)


# ---------------------------------------------------------------------
# Procurement Analytics
# ---------------------------------------------------------------------

@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def get_purchase_by_item(start_date, end_date):
    q = f"""
        SELECT item_name, COUNT(*) AS purchase_records, ROUND(SUM(purchase_amount), 2) AS total_purchase_value
        FROM purchases
        WHERE {_date_filter('purchase_date', start_date, end_date)}
        GROUP BY item_name
        ORDER BY total_purchase_value DESC
    """
    return run_query(q)


# ---------------------------------------------------------------------
# Consumables Analytics
# ---------------------------------------------------------------------

@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def get_consumable_by_item(start_date, end_date):
    q = f"""
        SELECT item_name, SUM(quantity) AS total_quantity, ROUND(SUM(amount), 2) AS total_expenditure
        FROM consumables
        WHERE {_date_filter('consumable_date', start_date, end_date)}
        GROUP BY item_name
        ORDER BY total_expenditure DESC
    """
    return run_query(q)


@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def get_top_consumable_items(start_date, end_date, n=5):
    q = f"""
        SELECT item_name, ROUND(SUM(amount), 2) AS total_expenditure
        FROM consumables
        WHERE {_date_filter('consumable_date', start_date, end_date)}
        GROUP BY item_name
        ORDER BY total_expenditure DESC
        LIMIT {int(n)}
    """
    return run_query(q)


# ---------------------------------------------------------------------
# Sales vs Purchases
# ---------------------------------------------------------------------

@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def get_sales_vs_purchases(start_date, end_date):
    q = f"""
        SELECT s.month, ROUND(s.sales_value, 2) AS sales_value, ROUND(p.purchase_value, 2) AS purchase_value,
               ROUND(s.sales_value - p.purchase_value, 2) AS sales_minus_purchases
        FROM (
            SELECT DATE_FORMAT(sale_date, '%Y-%m') AS month, SUM(amount) AS sales_value
            FROM sales
            WHERE transaction_type = 'Sale' AND {_date_filter('sale_date', start_date, end_date)}
            GROUP BY DATE_FORMAT(sale_date, '%Y-%m')
        ) s
        JOIN (
            SELECT DATE_FORMAT(purchase_date, '%Y-%m') AS month, SUM(purchase_amount) AS purchase_value
            FROM purchases
            WHERE {_date_filter('purchase_date', start_date, end_date)}
            GROUP BY DATE_FORMAT(purchase_date, '%Y-%m')
        ) p ON s.month = p.month
        ORDER BY s.month
    """
    return run_query(q)


# ---------------------------------------------------------------------
# Accounting Adjustments (kept separate from normal sales analysis)
# ---------------------------------------------------------------------

@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def get_sales_adjustments(start_date, end_date):
    q = f"""
        SELECT adjustment_date, reference, description,
               ROUND(amount, 2) AS amount, adjustment_type
        FROM sales_adjustments
        WHERE {_date_filter('adjustment_date', start_date, end_date)}
        ORDER BY adjustment_date
    """
    return run_query(q)
