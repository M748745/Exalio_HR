"""Test PostgreSQL connection with various methods"""

import psycopg2
import socket

# Test DNS resolution
print("Testing DNS resolution...")
try:
    ip = socket.getaddrinfo("db.goblvamlyonthzsjfzgr.supabase.co", 5432)
    print(f"✅ DNS resolved: {ip[0][4][0]}")
except Exception as e:
    print(f"❌ DNS failed: {e}")

# Test connection with connect_timeout
print("\nTesting PostgreSQL connection...")
try:
    conn = psycopg2.connect(
        host="db.goblvamlyonthzsjfzgr.supabase.co",
        port=5432,
        database="postgres",
        user="postgres",
        password="admin748745420701",
        connect_timeout=10
    )
    print("✅ Connection successful!")
    cursor = conn.cursor()
    cursor.execute("SELECT version()")
    print(f"PostgreSQL version: {cursor.fetchone()[0]}")
    conn.close()
except Exception as e:
    print(f"❌ Connection failed: {e}")
    print(f"Error type: {type(e).__name__}")
