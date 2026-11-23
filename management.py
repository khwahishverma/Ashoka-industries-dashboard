"""Database CRUD operations used by the dashboard management pages."""

import pandas as pd

from database import (
    delete_record as delete_supabase_record,
    fetch_table,
    insert_record,
    update_record as update_supabase_record,
)


TABLES = {
    "Sales": {
        "table": "sales",
        "pk": "sale_id",
        "fields": [
            ("sale_date", "Sale Date", "date"),
            ("bill_no", "Bill Number", "text"),
            ("customer_name", "Customer Name", "text"),
            ("quantity", "Quantity", "number"),
            ("amount", "Amount", "number"),
            ("transaction_type", "Transaction Type", "text"),
            ("period", "Period", "text"),
        ],
    },
    "Purchases": {
        "table": "purchases",
        "pk": "purchase_id",
        "fields": [
            ("purchase_date", "Purchase Date", "date"),
            ("bill_no", "Bill Number", "text"),
            ("item_name", "Item Name", "text"),
            ("hsn_code", "HSN Code", "text"),
            ("gst_amount", "GST Amount", "number"),
            ("purchase_amount", "Purchase Amount", "number"),
            ("period", "Period", "text"),
        ],
    },
    "Consumables": {
        "table": "consumables",
        "pk": "consumable_id",
        "fields": [
            ("consumable_date", "Consumable Date", "date"),
            ("bill_no", "Bill Number", "text"),
            ("item_name", "Item Name", "text"),
            ("quantity", "Quantity", "number"),
            ("amount", "Amount", "number"),
            ("period", "Period", "text"),
        ],
    },
    "Sales Adjustments": {
        "table": "sales_adjustments",
        "pk": "adjustment_id",
        "fields": [
            ("adjustment_date", "Adjustment Date", "date"),
            ("reference", "Reference", "text"),
            ("description", "Description", "text"),
            ("amount", "Amount", "number"),
            ("adjustment_type", "Adjustment Type", "text"),
        ],
    },
}


def get_records(category: str) -> pd.DataFrame:
    config = TABLES[category]
    records = fetch_table(config["table"])
    return records.sort_values(config["pk"], ascending=False).reset_index(drop=True)


def add_record(category: str, values: dict):
    config = TABLES[category]
    payload = {field[0]: values[field[0]] for field in config["fields"]}
    return insert_record(config["table"], payload)


def update_record(category: str, record_id, values: dict):
    config = TABLES[category]
    payload = {field[0]: values[field[0]] for field in config["fields"]}
    return update_supabase_record(config["table"], record_id, payload)


def delete_record(category: str, record_id):
    config = TABLES[category]
    return delete_supabase_record(config["table"], record_id)
