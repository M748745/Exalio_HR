"""
Schema verification script to check all required tables and columns exist
"""

from database import get_db_connection

def verify_schema():
    """Verify that all required tables and columns exist"""
    print("🔍 Verifying database schema...")

    required_tables = {
        'shift_templates': ['id', 'shift_name', 'shift_type', 'start_time', 'end_time'],
        'shift_schedules': ['id', 'emp_id', 'shift_id', 'shift_date', 'location'],
        'compliance_requirements': ['id', 'requirement_name', 'requirement_type', 'next_review_date', 'status'],
        'onboarding': ['id', 'emp_id', 'start_date', 'it_setup', 'workspace_setup', 'system_access'],
        'training_catalog': ['id', 'course_name', 'title', 'category'],
        'documents': ['id', 'emp_id', 'document_name', 'created_at'],
    }

    all_ok = True

    with get_db_connection() as conn:
        cursor = conn.cursor()

        for table_name, required_columns in required_tables.items():
            print(f"\n📋 Checking table: {table_name}")

            # Check if table exists
            cursor.execute("""
                SELECT COUNT(*) as cnt FROM information_schema.tables
                WHERE table_name = %s
            """, (table_name,))
            table_exists = cursor.fetchone()['cnt'] > 0

            if not table_exists:
                print(f"   ❌ Table '{table_name}' does not exist!")
                all_ok = False
                continue
            else:
                print(f"   ✅ Table exists")

            # Check columns
            cursor.execute("""
                SELECT column_name FROM information_schema.columns
                WHERE table_name = %s
            """, (table_name,))
            existing_columns = [row['column_name'] for row in cursor.fetchall()]

            for col in required_columns:
                if col in existing_columns:
                    print(f"      ✅ Column '{col}' exists")
                else:
                    print(f"      ❌ Column '{col}' is missing!")
                    all_ok = False

    if all_ok:
        print("\n✅ All required tables and columns exist!")
        return True
    else:
        print("\n❌ Some tables or columns are missing. Please run migrations.")
        return False

if __name__ == "__main__":
    import sys
    result = verify_schema()
    sys.exit(0 if result else 1)
