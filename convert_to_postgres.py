"""
Convert database.py from SQLite to PostgreSQL
"""

import re

# Read the SQLite version
with open("database_sqlite_backup.py", "r", encoding="utf-8") as f:
    content = f.read()

# Replace imports
content = content.replace("import sqlite3", "import psycopg2\nfrom psycopg2.extras import RealDictCursor\nimport streamlit as st")

# Replace connection code
old_connection_code = r"def _get_shared_connection\(\):.*?return _shared_connection"
new_connection_code = """def get_connection_string():
    '''Get PostgreSQL connection string from Streamlit secrets'''
    try:
        return st.secrets["connections"]["postgresql"]["url"]
    except:
        return "postgresql://postgres:admin748745420701@db.thshwxkuauahwvfaocnt.supabase.co:5432/postgres\""""

content = re.sub(old_connection_code, new_connection_code, content, flags=re.DOTALL)

# Replace get_db_connection
old_context = r"@contextmanager\ndef get_db_connection\(\):.*?raise"
new_context = """@contextmanager
def get_db_connection():
    '''Context manager for PostgreSQL database connections'''
    conn = None
    try:
        conn = psycopg2.connect(get_connection_string(), cursor_factory=RealDictCursor)
        yield conn
        conn.commit()
    except Exception as e:
        if conn:
            conn.rollback()
        raise"""

content = re.sub(old_context, new_context, content, flags=re.DOTALL)

# Replace SQL syntax
content = content.replace("INTEGER PRIMARY KEY SERIAL", "SERIAL PRIMARY KEY")
content = content.replace("id INTEGER PRIMARY KEY SERIAL", "id SERIAL PRIMARY KEY")
content = content.replace("CURRENT_TIMESTAMP", "NOW()")

# Replace sqlite3.Row with dict
content = content.replace("sqlite3.Row", "RealDictCursor")
content = content.replace(".row_factory = sqlite3.Row", "")

# Remove DATABASE_NAME and related
content = re.sub(r'DATABASE_NAME = "hr_system\.db"', "", content)
content = re.sub(r'_shared_connection = None', "", content)
content = re.sub(r'_connection_lock = None', "", content)

# Write the new file
with open("database.py", "w", encoding="utf-8") as f:
    f.write(content)

print("✅ Converted database.py to PostgreSQL!")
