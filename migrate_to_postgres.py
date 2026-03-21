"""
Migration Script: SQLite to PostgreSQL
Copies all data from hr_system.db to PostgreSQL on Supabase
"""

import sqlite3
import psycopg2
from psycopg2.extras import execute_batch
import streamlit as st

# PostgreSQL connection
PG_CONN_STRING = "postgresql://postgres:admin748745420701@db.goblvamlyonthzsjfzgr.supabase.co:5432/postgres"

def migrate_sqlite_to_postgres():
    """Complete migration from SQLite to PostgreSQL"""

    print("🚀 Starting migration from SQLite to PostgreSQL...")

    # Connect to SQLite
    sqlite_conn = sqlite3.connect("hr_system.db")
    sqlite_conn.row_factory = sqlite3.Row
    sqlite_cursor = sqlite_conn.cursor()

    # Connect to PostgreSQL
    pg_conn = psycopg2.connect(PG_CONN_STRING)
    pg_cursor = pg_conn.cursor()

    try:
        # Get all tables from SQLite
        sqlite_cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in sqlite_cursor.fetchall()]

        print(f"Found {len(tables)} tables to migrate")

        for table in tables:
            if table == 'sqlite_sequence':
                continue

            print(f"\n📋 Migrating table: {table}")

            # Get SQLite table schema
            sqlite_cursor.execute(f"PRAGMA table_info({table})")
            columns_info = sqlite_cursor.fetchall()
            columns = [col[1] for col in columns_info]

            # Create PostgreSQL table
            create_pg_table(pg_cursor, table, columns_info)

            # Copy data
            sqlite_cursor.execute(f"SELECT * FROM {table}")
            rows = sqlite_cursor.fetchall()

            if rows:
                print(f"  Copying {len(rows)} rows...")
                copy_data(pg_cursor, table, columns, rows)
            else:
                print(f"  No data to copy")

        pg_conn.commit()
        print("\n✅ Migration completed successfully!")

    except Exception as e:
        pg_conn.rollback()
        print(f"\n❌ Migration failed: {str(e)}")
        raise
    finally:
        sqlite_conn.close()
        pg_conn.close()

def create_pg_table(cursor, table_name, columns_info):
    """Create PostgreSQL table with schema conversion"""

    column_defs = []
    for col in columns_info:
        col_name = col[1]
        col_type = col[2]
        not_null = col[3]
        default_val = col[4]
        is_pk = col[5]

        # Convert SQLite types to PostgreSQL types
        pg_type = convert_type(col_type)

        # Build column definition
        col_def = f"{col_name} {pg_type}"

        if is_pk:
            if col_name == 'id':
                col_def = f"{col_name} SERIAL PRIMARY KEY"
            else:
                col_def += " PRIMARY KEY"
        elif not_null:
            col_def += " NOT NULL"

        if default_val and not is_pk:
            if default_val == "CURRENT_TIMESTAMP":
                col_def += " DEFAULT CURRENT_TIMESTAMP"
            elif default_val.isdigit():
                col_def += f" DEFAULT {default_val}"
            else:
                col_def += f" DEFAULT '{default_val}'"

        column_defs.append(col_def)

    create_sql = f"CREATE TABLE IF NOT EXISTS {table_name} ({', '.join(column_defs)})"

    try:
        cursor.execute(f"DROP TABLE IF EXISTS {table_name} CASCADE")
        cursor.execute(create_sql)
        print(f"  Table {table_name} created")
    except Exception as e:
        print(f"  Warning: {str(e)}")

def convert_type(sqlite_type):
    """Convert SQLite data types to PostgreSQL"""
    sqlite_type = sqlite_type.upper()

    type_mapping = {
        'INTEGER': 'INTEGER',
        'TEXT': 'TEXT',
        'REAL': 'REAL',
        'BLOB': 'BYTEA',
        'DATE': 'DATE',
        'TIMESTAMP': 'TIMESTAMP',
    }

    for sql_type, pg_type in type_mapping.items():
        if sql_type in sqlite_type:
            return pg_type

    return 'TEXT'  # Default

def copy_data(cursor, table_name, columns, rows):
    """Copy data from SQLite to PostgreSQL"""

    placeholders = ', '.join(['%s'] * len(columns))
    columns_str = ', '.join(columns)

    insert_sql = f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})"

    # Convert rows to list of tuples
    data = [tuple(dict(row).values()) for row in rows]

    execute_batch(cursor, insert_sql, data, page_size=100)

if __name__ == "__main__":
    migrate_sqlite_to_postgres()
