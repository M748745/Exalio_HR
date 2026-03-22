"""Count all tables in the database"""

from database import get_db_connection

with get_db_connection() as conn:
    cursor = conn.cursor()

    # Get all tables
    cursor.execute("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
        AND table_type = 'BASE TABLE'
        ORDER BY table_name
    """)

    tables = cursor.fetchall()

    print(f"\n📊 Total Tables: {len(tables)}\n")
    print("=" * 50)

    for i, row in enumerate(tables, 1):
        print(f"{i:2d}. {row['table_name']}")

    print("=" * 50)
    print(f"\n✅ Total: {len(tables)} tables")

    # Check for the new tables specifically
    new_tables = ['shift_templates', 'shift_schedules', 'compliance_requirements', 'onboarding']
    print("\n🔍 Checking for newly added tables:")
    for table in new_tables:
        cursor.execute("""
            SELECT COUNT(*) as cnt FROM information_schema.tables
            WHERE table_name = %s
        """, (table,))
        exists = cursor.fetchone()['cnt'] > 0
        status = "✅ EXISTS" if exists else "❌ MISSING"
        print(f"   {status}: {table}")
