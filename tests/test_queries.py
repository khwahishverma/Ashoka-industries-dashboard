import unittest
from unittest.mock import patch

import pandas as pd
import streamlit as st

import queries


class SupabaseAnalyticsTests(unittest.TestCase):
    def setUp(self):
        self.tables = {
            "sales": pd.DataFrame(
                [
                    [1, "2026-01-01", "A", "Customer A", 2, 100, "Sale", "Jan"],
                    [2, "2026-01-31", "B", "Customer A", 3, 100000, "Sale", "Jan"],
                    [3, "2026-02-01", "C", "Customer B", 4, 200000, "Sale", "Feb"],
                    [4, "2026-02-02", "D", "Customer A", 100, 999999, "Credit Note", "Feb"],
                    [5, "2026-03-01", "E", "Customer C", 10, 500, "Sale", "Mar"],
                ],
                columns=[
                    "sale_id", "sale_date", "bill_no", "customer_name",
                    "quantity", "amount", "transaction_type", "period",
                ],
            ),
            "purchases": pd.DataFrame(
                [
                    [1, "2026-01-01", "P1", "Steel", "1", 5, 50, "Jan"],
                    [2, "2026-02-01", "P2", "Steel", "1", 2, 20, "Feb"],
                ],
                columns=[
                    "purchase_id", "purchase_date", "bill_no", "item_name",
                    "hsn_code", "gst_amount", "purchase_amount", "period",
                ],
            ),
            "consumables": pd.DataFrame(
                [[1, "2026-02-02", "C1", "Oil", 2, 10, "Feb"]],
                columns=[
                    "consumable_id", "consumable_date", "bill_no", "item_name",
                    "quantity", "amount", "period",
                ],
            ),
            "sales_adjustments": pd.DataFrame(
                [[1, "2026-01-10", "R1", "Adjustment", 7, "Credit"]],
                columns=[
                    "adjustment_id", "adjustment_date", "reference",
                    "description", "amount", "adjustment_type",
                ],
            ),
        }
        self.fetch = patch(
            "queries.fetch_table",
            side_effect=lambda table: self.tables[table].copy(),
        )
        self.fetch.start()
        self.addCleanup(self.fetch.stop)
        self.addCleanup(st.cache_data.clear)
        st.cache_data.clear()

    def test_sales_filter_excludes_adjustments_and_respects_date_bounds(self):
        start, end = pd.Timestamp("2026-01-01"), pd.Timestamp("2026-02-28")
        self.assertEqual(queries.get_total_sales(start, end), 300100)
        self.assertEqual(queries.get_total_quantity_sold(start, end), 9)
        self.assertEqual(queries.get_sales_transaction_count(start, end), 3)
        self.assertEqual(queries.get_avg_invoice_value(start, end), 100033.33)

    def test_monthly_rank_customer_and_cumulative_outputs(self):
        start, end = pd.Timestamp("2026-01-01"), pd.Timestamp("2026-02-28")
        ranked = queries.get_monthly_sales_ranked(start, end)
        self.assertEqual(ranked["month"].tolist(), ["2026-02", "2026-01"])
        self.assertEqual(ranked["sales_rank"].tolist(), [1, 2])

        customers = queries.get_customer_wise_sales(start, end)
        self.assertEqual(customers.iloc[0]["customer_name"], "Customer B")
        self.assertEqual(customers.iloc[0]["number_of_transactions"], 1)

        cumulative = queries.get_cumulative_sales(start, end)
        self.assertEqual(cumulative["cumulative_sales"].tolist(), [100, 100100, 300100])

    def test_purchase_consumable_adjustment_and_comparison_outputs(self):
        start, end = pd.Timestamp("2026-01-01"), pd.Timestamp("2026-02-28")
        self.assertEqual(
            queries.get_monthly_purchases(start, end)["monthly_purchases"].tolist(),
            [50, 20],
        )
        self.assertEqual(
            queries.get_total_consumables(start, end),
            10,
        )
        self.assertEqual(len(queries.get_sales_adjustments(start, end)), 1)
        comparison = queries.get_sales_vs_purchases(start, end)
        self.assertEqual(comparison["month"].tolist(), ["2026-01", "2026-02"])
        self.assertEqual(
            comparison["sales_minus_purchases"].tolist(),
            [100050, 199980],
        )

    def test_dashboard_table_queries_keep_expected_columns_and_values(self):
        start, end = pd.Timestamp("2026-01-01"), pd.Timestamp("2026-02-28")
        self.assertEqual(
            queries.get_top_sales(start, end)["bill_no"].tolist(),
            ["C", "B", "A"],
        )
        self.assertEqual(
            queries.get_sales_classification(start, end)["sales_category"].tolist(),
            ["High Value", "Medium Value", "Lower Value"],
        )
        self.assertEqual(
            queries.get_monthly_contribution(start, end)["pct_of_total"].round(2).tolist(),
            [33.36, 66.64],
        )
        self.assertEqual(
            queries.get_purchase_by_item(start, end).iloc[0]["total_purchase_value"],
            70,
        )
        self.assertEqual(
            queries.get_consumable_by_item(start, end).iloc[0]["total_expenditure"],
            10,
        )
        self.assertEqual(
            queries.get_top_consumable_items(start, end)["item_name"].tolist(),
            ["Oil"],
        )


if __name__ == "__main__":
    unittest.main()
