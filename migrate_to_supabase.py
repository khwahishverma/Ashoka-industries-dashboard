"""Idempotently copy the local MySQL records to Supabase, preserving IDs."""

import os
from datetime import date, datetime
from decimal import Decimal

import mysql.connector
from dotenv import load_dotenv
from supabase import create_client

from database import TABLE_COLUMNS, TABLE_PRIMARY_KEYS

BATCH_SIZE = 500


def _mysql_config():
    return {
        "host": os.getenv("DB_HOST", "localhost"),
        "port": int(os.getenv("DB_PORT", "3306")),
        "user": os.getenv("DB_USER", "root"),
        "password": os.getenv("DB_PASSWORD", ""),
        "database": os.getenv("DB_NAME", "ashoka_industries"),
    }


def _json_value(value):
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return str(value)
    return value


def main():
    load_dotenv()
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = (
        os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_SECRET_KEY")
    )
    if not supabase_url or not supabase_key:
        raise RuntimeError(
            "Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY "
            "(or SUPABASE_SECRET_KEY) before running the migration."
        )

    client = create_client(supabase_url, supabase_key)
    connection = mysql.connector.connect(**_mysql_config())
    try:
        for table, columns in TABLE_COLUMNS.items():
            primary_key = TABLE_PRIMARY_KEYS[table]
            cursor = connection.cursor(dictionary=True)
            migrated = 0
            try:
                cursor.execute(f"SELECT * FROM `{table}` ORDER BY `{primary_key}`")
                while True:
                    source_rows = cursor.fetchmany(BATCH_SIZE)
                    if not source_rows:
                        break
                    rows = [
                        {column: _json_value(row[column]) for column in columns}
                        for row in source_rows
                    ]
                    response = (
                        client.table(table)
                        .upsert(rows, on_conflict=primary_key)
                        .select(primary_key)
                        .execute()
                    )
                    saved_rows = response.data or []
                    expected_ids = {row[primary_key] for row in rows}
                    saved_ids = {row[primary_key] for row in saved_rows}
                    if len(saved_rows) != len(rows) or saved_ids != expected_ids:
                        raise RuntimeError(
                            f"Migration verification failed for {table}: "
                            f"sent {len(rows)} rows, received "
                            f"{len(saved_rows)} matching confirmations."
                        )
                    migrated += len(saved_rows)
            finally:
                cursor.close()
            print(f"{table}: migrated and verified {migrated} rows")
    finally:
        connection.close()

    print(
        "Migration complete. Run the four identity-sequence reset statements "
        "in README.md before adding new records."
    )


if __name__ == "__main__":
    main()
