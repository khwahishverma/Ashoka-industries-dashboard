import unittest
from datetime import date
from types import SimpleNamespace
from unittest.mock import patch

import database


class FakeTable:
    def __init__(self):
        self.operation = None
        self.payload = None
        self.filter = None

    def insert(self, payload):
        self.operation, self.payload = "insert", payload
        return self

    def update(self, payload):
        self.operation, self.payload = "update", payload
        return self

    def delete(self):
        self.operation = "delete"
        return self

    def eq(self, column, value):
        self.filter = (column, value)
        return self

    def select(self, column):
        self.selected = column
        return self

    def execute(self):
        return SimpleNamespace(data=[{self.selected: 3}])


class FakeClient:
    def __init__(self):
        self.table_instance = FakeTable()
        self.table_name = None

    def table(self, name):
        self.table_name = name
        return self.table_instance


class PaginatedTable:
    def __init__(self):
        self.start = 0

    def select(self, columns):
        self.selected_columns = columns
        return self

    def range(self, start, end):
        self.start = start
        self.end = end
        return self

    def execute(self):
        size = 1000 if self.start == 0 else 1
        return SimpleNamespace(
            data=[
                {"sale_id": self.start + index + 1, "sale_date": "2026-01-01"}
                for index in range(size)
            ]
        )


class PaginatedClient:
    def __init__(self):
        self.table_instance = PaginatedTable()

    def table(self, name):
        self.name = name
        return self.table_instance


class SupabaseCrudTests(unittest.TestCase):
    def setUp(self):
        self.client = FakeClient()
        self.client_patch = patch(
            "database.get_client", return_value=self.client
        )
        self.client_patch.start()
        self.addCleanup(self.client_patch.stop)

    def test_insert_serializes_dates_and_persists_to_supabase(self):
        success, message = database.insert_record(
            "sales", {"sale_date": date(2026, 1, 2), "amount": 12.5}
        )
        self.assertTrue(success)
        self.assertIn("Rows affected: 1", message)
        self.assertEqual(self.client.table_name, "sales")
        self.assertEqual(
            self.client.table_instance.payload,
            {"sale_date": "2026-01-02", "amount": 12.5},
        )

    def test_update_and_delete_filter_by_primary_key(self):
        success, _ = database.update_record(
            "purchases", 17, {"purchase_amount": 200}
        )
        self.assertTrue(success)
        self.assertEqual(self.client.table_name, "purchases")
        self.assertEqual(
            self.client.table_instance.filter, ("purchase_id", 17)
        )

        success, _ = database.delete_record("consumables", 9)
        self.assertTrue(success)
        self.assertEqual(self.client.table_name, "consumables")
        self.assertEqual(
            self.client.table_instance.filter, ("consumable_id", 9)
        )

    def test_table_reads_past_supabase_page_limit(self):
        client = PaginatedClient()
        with patch("database.get_client", return_value=client):
            database.fetch_table.clear()
            records = database.fetch_table("sales")
        self.assertEqual(len(records), 1001)
        self.assertEqual(records.iloc[-1]["sale_id"], 1001)
        database.fetch_table.clear()


if __name__ == "__main__":
    unittest.main()
