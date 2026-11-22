"""Database CRUD operations used by the dashboard management pages."""

import pandas as pd

from database import execute_write, run_query


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
    return run_query(
        f"SELECT * FROM {config['table']} ORDER BY {config['pk']} DESC"
    )


def add_record(category: str, values: dict):
    config = TABLES[category]
    columns = [field[0] for field in config["fields"]]
    placeholders = ", ".join(["%s"] * len(columns))
    query = (
        f"INSERT INTO {config['table']} ({', '.join(columns)}) "
        f"VALUES ({placeholders})"
    )
    return execute_write(query, tuple(values[column] for column in columns))


def update_record(category: str, record_id, values: dict):
    config = TABLES[category]
    columns = [field[0] for field in config["fields"]]
    assignments = ", ".join(f"{column} = %s" for column in columns)
    query = (
        f"UPDATE {config['table']} SET {assignments} "
        f"WHERE {config['pk']} = %s"
    )
    params = tuple(values[column] for column in columns) + (record_id,)
    return execute_write(query, params)


def delete_record(category: str, record_id):
    config = TABLES[category]
    query = f"DELETE FROM {config['table']} WHERE {config['pk']} = %s"
    return execute_write(query, (record_id,))
