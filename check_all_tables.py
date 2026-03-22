"""Check all tables referenced in error messages"""

from database import get_db_connection

tables_to_check = [
    'training_enrollments',
    'training_catalog',
    'assets',
    'documents',
    'audit_logs',
    'shift_schedules',
    'shift_templates',
    'teams',
    'positions',
    'promotion_requests',
    'asset_requests',
    'certificates',
    'goals',
    'compliance_requirements',
    'onboarding'
]

with get_db_connection() as conn:
    cursor = conn.cursor()

    for table in tables_to_check:
        # Check if table exists
        cursor.execute("""
            SELECT COUNT(*) as cnt FROM information_schema.tables
            WHERE table_name = %s
        """, (table,))

        if cursor.fetchone()['cnt'] == 0:
            print(f"\n❌ Table '{table}' DOES NOT EXIST")
            continue

        print(f"\n✅ Table '{table}' exists")
        print(f"   Columns:")
        cursor.execute("""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_name = %s
            ORDER BY ordinal_position
        """, (table,))

        for row in cursor.fetchall():
            print(f"      - {row['column_name']} ({row['data_type']})")
