"""
insights.py
-----------
Turns the query results into plain-language, data-driven findings.
Every value here is derived at runtime from whatever the current
sidebar filter returns - nothing is hard-coded, so insights update
automatically if the date range changes or new transactions are
added to the database.

Strictly descriptive: no profit/margin/ROI claims, no causal
speculation the data cannot support.
"""

import pandas as pd
from utils import format_inr, month_label
import queries as q


def build_insights(start_date, end_date) -> dict:
    monthly_sales = q.get_monthly_sales(start_date, end_date)
    monthly_purchases = q.get_monthly_purchases(start_date, end_date)
    monthly_consumables = q.get_monthly_consumables(start_date, end_date)
    purchase_by_item = q.get_purchase_by_item(start_date, end_date)
    consumable_by_item = q.get_consumable_by_item(start_date, end_date)
    customer_sales = q.get_customer_wise_sales(start_date, end_date)

    result = {}

    # --- Sales: highest / lowest month ---
    if not monthly_sales.empty:
        top_row = monthly_sales.loc[monthly_sales["monthly_sales"].idxmax()]
        low_row = monthly_sales.loc[monthly_sales["monthly_sales"].idxmin()]
        result["highest_sales_month"] = month_label(top_row["month"])
        result["highest_sales_value"] = top_row["monthly_sales"]
        result["lowest_sales_month"] = month_label(low_row["month"])
        result["lowest_sales_value"] = low_row["monthly_sales"]
        result["sales_month_count"] = len(monthly_sales)
    else:
        result["highest_sales_month"] = None
        result["lowest_sales_month"] = None

    # --- Purchases: concentration ---
    if not purchase_by_item.empty:
        top_purchase = purchase_by_item.iloc[0]
        result["top_purchase_item"] = top_purchase["item_name"]
        result["top_purchase_value"] = top_purchase["total_purchase_value"]
        result["top_purchase_share"] = round(
            100 * top_purchase["total_purchase_value"]
            / purchase_by_item["total_purchase_value"].sum(),
            1
        ) if purchase_by_item["total_purchase_value"].sum() else 0
    else:
        result["top_purchase_item"] = None

    # --- Consumables: concentration ---
    if not consumable_by_item.empty:
        top_consumable = consumable_by_item.iloc[0]
        result["top_consumable_item"] = top_consumable["item_name"]
        result["top_consumable_value"] = top_consumable["total_expenditure"]
        result["top_consumable_share"] = round(
            100 * top_consumable["total_expenditure"]
            / consumable_by_item["total_expenditure"].sum(),
            1
        ) if consumable_by_item["total_expenditure"].sum() else 0
    else:
        result["top_consumable_item"] = None

    # --- Customer concentration (factual, no invented diversity) ---
    if not customer_sales.empty:
        result["customer_count"] = len(customer_sales)
        result["top_customer"] = customer_sales.iloc[0]["customer_name"]
        result["top_customer_share"] = round(
            100 * customer_sales.iloc[0]["total_sales"]
            / customer_sales["total_sales"].sum(),
            1
        ) if customer_sales["total_sales"].sum() else 0
    else:
        result["customer_count"] = 0

    # --- Sales vs Purchases pattern (value comparison only, never "profit") ---
    if not monthly_sales.empty and not monthly_purchases.empty:
        merged = monthly_sales.merge(monthly_purchases, on="month", how="inner")
        if not merged.empty:
            merged["diff"] = merged["monthly_sales"] - merged["monthly_purchases"]
            result["months_sales_exceed_purchases"] = int(
                (merged["diff"] > 0).sum()
            )
            result["months_compared"] = len(merged)

    return result


def executive_summary_lines(start_date, end_date) -> list:
    """Six short, data-grounded lines answering the assignment's required executive-summary questions."""
    ins = build_insights(start_date, end_date)
    lines = []

    if ins.get("highest_sales_month"):
        lines.append(
            f"Sales ranged from {format_inr(ins['lowest_sales_value'])} in "
            f"{ins['lowest_sales_month']} to "
            f"{format_inr(ins['highest_sales_value'])} in "
            f"{ins['highest_sales_month']} across the "
            f"{ins['sales_month_count']}-month period on record."
        )

    if ins.get("top_customer"):
        if ins["customer_count"] == 1:
            lines.append(
                f"All recorded sales in this period are to a single customer, "
                f"{ins['top_customer']}."
            )
        else:
            lines.append(
                f"{ins['top_customer']} accounts for "
                f"{ins['top_customer_share']}% of total sales value across "
                f"{ins['customer_count']} customers on record."
            )

    if ins.get("top_purchase_item"):
        lines.append(
            f"Purchasing is concentrated in '{ins['top_purchase_item']}', "
            f"representing {ins['top_purchase_share']}% of total purchase value."
        )

    if ins.get("top_consumable_item"):
        lines.append(
            f"Consumable expenditure is concentrated in "
            f"'{ins['top_consumable_item']}', representing "
            f"{ins['top_consumable_share']}% of total consumable spend."
        )

    if ins.get("months_compared"):
        lines.append(
            f"Sales value exceeded purchase value in "
            f"{ins['months_sales_exceed_purchases']} of "
            f"{ins['months_compared']} compared months "
            f"(a value comparison, not a profit calculation)."
        )

    lines.append(
        "Management can use the filters on this dashboard to monitor "
        "these patterns on an ongoing, monthly basis."
    )

    return lines


def key_conclusions(start_date, end_date) -> list:
    ins = build_insights(start_date, end_date)
    bullets = []

    if ins.get("highest_sales_month"):
        bullets.append(
            f"The highest observed monthly sales value was recorded in "
            f"{ins['highest_sales_month']}."
        )
        bullets.append(
            f"The lowest observed monthly sales value was recorded in "
            f"{ins['lowest_sales_month']}."
        )

    if ins.get("top_purchase_item"):
        bullets.append(
            f"Purchase expenditure was concentrated in "
            f"'{ins['top_purchase_item']}'."
        )

    if ins.get("top_consumable_item"):
        bullets.append(
            f"Consumable expenditure was concentrated in "
            f"'{ins['top_consumable_item']}'."
        )

    if ins.get("customer_count") == 1:
        bullets.append(
            "Recorded sales show a single-customer concentration during this period."
        )

    bullets.append(
        "The dashboard provides management with monthly, filterable visibility "
        "into sales, purchase and consumable expenditure patterns."
    )

    return bullets


def recommendations(start_date, end_date) -> list:
    """Each item: (finding, implication, action) - grounded in the current filtered data."""
    ins = build_insights(start_date, end_date)
    recs = []

    if ins.get("highest_sales_month") and ins.get("lowest_sales_month"):
        recs.append({
            "finding": (
                f"Monthly sales value ranged from "
                f"{format_inr(ins['lowest_sales_value'])} in "
                f"{ins['lowest_sales_month']} to "
                f"{format_inr(ins['highest_sales_value'])} in "
                f"{ins['highest_sales_month']}."
            ),
            "implication": (
                "Sales value is not evenly distributed across the period on record."
            ),
            "action": (
                "Review monthly sales patterns and billing timing to support "
                "monthly planning."
            ),
        })

    if ins.get("customer_count") == 1:
        recs.append({
            "finding": (
                f"All recorded sales in this period are attributed to one customer "
                f"({ins.get('top_customer')})."
            ),
            "implication": (
                "Recorded sales value is concentrated in a single buyer relationship."
            ),
            "action": (
                "Maintain structured account records for this relationship and "
                "evaluate the value of diversifying the customer base over time."
            ),
        })

    if ins.get("top_purchase_item"):
        recs.append({
            "finding": (
                f"'{ins['top_purchase_item']}' represents "
                f"{ins['top_purchase_share']}% of total purchase value."
            ),
            "implication": (
                "A large share of procurement spend sits in one item category."
            ),
            "action": (
                "Establish a review threshold or approval step for high-value "
                "purchases in this category."
            ),
        })

    if ins.get("top_consumable_item"):
        recs.append({
            "finding": (
                f"'{ins['top_consumable_item']}' represents "
                f"{ins['top_consumable_share']}% of consumable expenditure."
            ),
            "implication": (
                "Consumable spend is concentrated rather than evenly spread across items."
            ),
            "action": (
                "Track this item's usage and pricing separately and set a "
                "monitoring threshold for it."
            ),
        })

    return recs

