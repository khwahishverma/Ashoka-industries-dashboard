"""
Dashboard analytics over records fetched from Supabase.

Normal sales analysis always filters transaction_type = 'Sale' so
that credit notes and sales adjustments never contaminate sales totals.
"""

import numpy as np
import pandas as pd
import streamlit as st

from database import fetch_table

CACHE_TTL = 300


def _filtered(table: str, date_column: str, start_date, end_date) -> pd.DataFrame:
    frame = fetch_table(table)
    if frame.empty:
        return frame.copy()
    start = pd.Timestamp(start_date)
    end = pd.Timestamp(end_date)
    dates = pd.to_datetime(frame[date_column], errors="coerce")
    return frame.loc[dates.between(start, end)].copy()


def _sales(start_date, end_date) -> pd.DataFrame:
    frame = _filtered("sales", "sale_date", start_date, end_date)
    if frame.empty:
        return frame
    return frame.loc[frame["transaction_type"] == "Sale"].copy()


def _number(frame: pd.DataFrame, column: str) -> pd.Series:
    return pd.to_numeric(frame[column], errors="coerce")


def _monthly(frame: pd.DataFrame, date_column: str, value_column: str, result_name: str):
    if frame.empty:
        return pd.DataFrame(columns=["month", result_name])
    data = frame.assign(
        month=pd.to_datetime(frame[date_column]).dt.strftime("%Y-%m"),
        _value=_number(frame, value_column),
    )
    return (
        data.groupby("month", as_index=False, dropna=False)["_value"]
        .sum()
        .rename(columns={"_value": result_name})
        .sort_values("month")
        .reset_index(drop=True)
    )


@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def get_date_bounds():
    """Return the full transaction date span for the sidebar's default range."""
    dates = []
    for table, column in (
        ("sales", "sale_date"),
        ("purchases", "purchase_date"),
        ("consumables", "consumable_date"),
    ):
        frame = fetch_table(table)
        if not frame.empty:
            dates.extend(pd.to_datetime(frame[column], errors="coerce").dropna().tolist())

    if not dates:
        fallback = pd.Timestamp.today().date()
        return fallback, fallback
    return min(dates).date(), max(dates).date()


@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def get_total_sales(start_date, end_date):
    frame = _sales(start_date, end_date)
    return float(_number(frame, "amount").sum()) if not frame.empty else 0.0


@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def get_total_purchases(start_date, end_date):
    frame = _filtered("purchases", "purchase_date", start_date, end_date)
    return float(_number(frame, "purchase_amount").sum()) if not frame.empty else 0.0


@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def get_total_consumables(start_date, end_date):
    frame = _filtered("consumables", "consumable_date", start_date, end_date)
    return float(_number(frame, "amount").sum()) if not frame.empty else 0.0


@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def get_total_quantity_sold(start_date, end_date):
    frame = _sales(start_date, end_date)
    return float(_number(frame, "quantity").sum()) if not frame.empty else 0.0


@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def get_sales_transaction_count(start_date, end_date):
    return len(_sales(start_date, end_date))


@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def get_purchase_transaction_count(start_date, end_date):
    return len(_filtered("purchases", "purchase_date", start_date, end_date))


@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def get_consumable_transaction_count(start_date, end_date):
    return len(_filtered("consumables", "consumable_date", start_date, end_date))


@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def get_avg_invoice_value(start_date, end_date):
    frame = _sales(start_date, end_date)
    if frame.empty:
        return 0.0
    average = _number(frame, "amount").mean()
    return round(float(average), 2) if pd.notna(average) else 0.0


@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def get_monthly_sales(start_date, end_date):
    return _monthly(_sales(start_date, end_date), "sale_date", "amount", "monthly_sales")


@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def get_monthly_purchases(start_date, end_date):
    frame = _filtered("purchases", "purchase_date", start_date, end_date)
    return _monthly(frame, "purchase_date", "purchase_amount", "monthly_purchases")


@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def get_monthly_consumables(start_date, end_date):
    frame = _filtered("consumables", "consumable_date", start_date, end_date)
    return _monthly(frame, "consumable_date", "amount", "monthly_consumables")


@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def get_monthly_sales_ranked(start_date, end_date):
    monthly = get_monthly_sales(start_date, end_date).rename(
        columns={"monthly_sales": "total_sales"}
    )
    if monthly.empty:
        monthly["sales_rank"] = pd.Series(dtype="int64")
        return monthly
    monthly["sales_rank"] = monthly["total_sales"].rank(
        method="min", ascending=False
    ).astype(int)
    monthly["total_sales"] = monthly["total_sales"].round(2)
    return monthly.sort_values(["sales_rank", "month"]).reset_index(drop=True)


@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def get_monthly_contribution(start_date, end_date):
    monthly = get_monthly_sales(start_date, end_date).rename(
        columns={"monthly_sales": "monthly_sales"}
    )
    if monthly.empty:
        monthly["pct_of_total"] = pd.Series(dtype="float64")
        return monthly
    total = monthly["monthly_sales"].sum()
    monthly["monthly_sales"] = monthly["monthly_sales"].round(2)
    monthly["pct_of_total"] = (
        (monthly["monthly_sales"] * 100 / total).round(2) if total else np.nan
    )
    return monthly


@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def get_top_sales(start_date, end_date, n=10):
    frame = _sales(start_date, end_date)
    columns = ["sale_date", "bill_no", "customer_name", "quantity", "amount"]
    if frame.empty:
        return pd.DataFrame(columns=columns)
    frame = frame.assign(amount=_number(frame, "amount"))
    return frame.sort_values("amount", ascending=False)[columns].head(int(n)).assign(
        amount=lambda data: data["amount"].round(2)
    ).reset_index(drop=True)


@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def get_customer_wise_sales(start_date, end_date):
    frame = _sales(start_date, end_date)
    columns = [
        "customer_name", "number_of_transactions", "total_quantity", "total_sales"
    ]
    if frame.empty:
        return pd.DataFrame(columns=columns)
    frame = frame.assign(
        quantity=_number(frame, "quantity"),
        amount=_number(frame, "amount"),
    )
    result = (
        frame.groupby("customer_name", as_index=False, dropna=False)
        .agg(
            number_of_transactions=("sale_id", "size"),
            total_quantity=("quantity", "sum"),
            total_sales=("amount", "sum"),
        )
        .sort_values("total_sales", ascending=False)
    )
    result["total_sales"] = result["total_sales"].round(2)
    return result[columns].reset_index(drop=True)


@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def get_sales_classification(start_date, end_date):
    frame = _sales(start_date, end_date)
    columns = ["bill_no", "sale_date", "amount", "sales_category"]
    if frame.empty:
        return pd.DataFrame(columns=columns)
    frame = frame.assign(amount=_number(frame, "amount"))
    frame["sales_category"] = np.select(
        [frame["amount"] >= 200000, frame["amount"] >= 100000],
        ["High Value", "Medium Value"],
        default="Lower Value",
    )
    return (
        frame[columns]
        .sort_values("amount", ascending=False)
        .assign(amount=lambda data: data["amount"].round(2))
        .reset_index(drop=True)
    )


@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def get_cumulative_sales(start_date, end_date):
    frame = _sales(start_date, end_date)
    columns = ["sale_date", "bill_no", "amount", "cumulative_sales"]
    if frame.empty:
        return pd.DataFrame(columns=columns)
    frame = frame.assign(amount=_number(frame, "amount")).sort_values(
        ["sale_date", "sale_id"]
    )
    frame["cumulative_sales"] = frame["amount"].cumsum().round(2)
    frame["amount"] = frame["amount"].round(2)
    return frame[columns].reset_index(drop=True)


@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def get_purchase_by_item(start_date, end_date):
    frame = _filtered("purchases", "purchase_date", start_date, end_date)
    columns = ["item_name", "purchase_records", "total_purchase_value"]
    if frame.empty:
        return pd.DataFrame(columns=columns)
    frame = frame.assign(purchase_amount=_number(frame, "purchase_amount"))
    result = (
        frame.groupby("item_name", as_index=False, dropna=False)
        .agg(
            purchase_records=("item_name", "size"),
            total_purchase_value=("purchase_amount", "sum"),
        )
        .sort_values("total_purchase_value", ascending=False)
    )
    result["total_purchase_value"] = result["total_purchase_value"].round(2)
    return result[columns].reset_index(drop=True)


@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def get_consumable_by_item(start_date, end_date):
    frame = _filtered("consumables", "consumable_date", start_date, end_date)
    columns = ["item_name", "total_quantity", "total_expenditure"]
    if frame.empty:
        return pd.DataFrame(columns=columns)
    frame = frame.assign(
        quantity=_number(frame, "quantity"),
        amount=_number(frame, "amount"),
    )
    result = (
        frame.groupby("item_name", as_index=False, dropna=False)
        .agg(total_quantity=("quantity", "sum"), total_expenditure=("amount", "sum"))
        .sort_values("total_expenditure", ascending=False)
    )
    result["total_expenditure"] = result["total_expenditure"].round(2)
    return result[columns].reset_index(drop=True)


@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def get_top_consumable_items(start_date, end_date, n=5):
    result = get_consumable_by_item(start_date, end_date)
    return result[["item_name", "total_expenditure"]].head(int(n)).reset_index(
        drop=True
    )


@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def get_sales_vs_purchases(start_date, end_date):
    sales = get_monthly_sales(start_date, end_date).rename(
        columns={"monthly_sales": "sales_value"}
    )
    purchases = get_monthly_purchases(start_date, end_date).rename(
        columns={"monthly_purchases": "purchase_value"}
    )
    result = sales.merge(purchases, on="month", how="inner")
    if result.empty:
        return pd.DataFrame(
            columns=["month", "sales_value", "purchase_value", "sales_minus_purchases"]
        )
    result["sales_value"] = result["sales_value"].round(2)
    result["purchase_value"] = result["purchase_value"].round(2)
    result["sales_minus_purchases"] = (
        result["sales_value"] - result["purchase_value"]
    ).round(2)
    return result.sort_values("month").reset_index(drop=True)


@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def get_sales_adjustments(start_date, end_date):
    frame = _filtered("sales_adjustments", "adjustment_date", start_date, end_date)
    columns = ["adjustment_date", "reference", "description", "amount", "adjustment_type"]
    if frame.empty:
        return pd.DataFrame(columns=columns)
    frame = frame.assign(amount=_number(frame, "amount"))
    return (
        frame[columns]
        .sort_values("adjustment_date")
        .assign(amount=lambda data: data["amount"].round(2))
        .reset_index(drop=True)
    )
