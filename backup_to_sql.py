"""
Export SQLite database to SQL file for manual PostgreSQL import
"""

import sqlite3

def export_sqlite_to_sql():
    """Export SQLite database to SQL INSERT statements"""

    conn = sqlite3.connect("hr_system.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    with open("hr_system_backup.sql", "w", encoding="utf-8") as f:
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
        tables = [row[0] for row in cursor.fetchall()]

        for table in tables:
            f.write(f"\n-- Table: {table}\n")

            # Get data
            cursor.execute(f"SELECT * FROM {table}")
            rows = cursor.fetchall()

            if rows:
                columns = rows[0].keys()
                for row in rows:
                    values = []
                    for val in row:
                        if val is None:
                            values.append("NULL")
                        elif isinstance(val, str):
                            # Escape single quotes
                            escaped = val.replace("'", "''")
                            values.append(f"'{escaped}'")
                        else:
                            values.append(str(val))

                    columns_str = ", ".join(columns)
                    values_str = ", ".join(values)
                    f.write(f"INSERT INTO {table} ({columns_str}) VALUES ({values_str});\n")

    print("✅ Backup created: hr_system_backup.sql")
    conn.close()

if __name__ == "__main__":
    export_sqlite_to_sql()
