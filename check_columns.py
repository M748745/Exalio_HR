"""Check what columns actually exist in problematic tables"""

from database import get_db_connection

with get_db_connection() as conn:
    cursor = conn.cursor()

    # Check compliance_requirements columns
    print("📋 compliance_requirements columns:")
    cursor.execute("""
        SELECT column_name FROM information_schema.columns
        WHERE table_name = 'compliance_requirements'
        ORDER BY ordinal_position
    """)
    for row in cursor.fetchall():
        print(f"  - {row['column_name']}")

    # Check documents columns
    print("\n📋 documents columns:")
    cursor.execute("""
        SELECT column_name FROM information_schema.columns
        WHERE table_name = 'documents'
        ORDER BY ordinal_position
    """)
    for row in cursor.fetchall():
        print(f"  - {row['column_name']}")
