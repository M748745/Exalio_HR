"""
Check for missing columns in all core tables
"""

from database import get_db_connection

# Expected columns for each table based on module usage
expected_columns = {
    'employees': ['id', 'employee_id', 'first_name', 'last_name', 'department', 'position',
                  'manager_id', 'join_date', 'status', 'email', 'phone', 'team_tag'],
    'training_catalog': ['id', 'course_name', 'title', 'category', 'provider', 'description',
                         'duration', 'cost', 'max_participants', 'status'],
    'training_enrollments': ['id', 'emp_id', 'course_id', 'enrollment_date', 'status',
                            'completion_date', 'approved_by'],
    'documents': ['id', 'emp_id', 'title', 'document_type', 'file_path', 'status',
                  'created_at', 'uploaded_by'],
    'certificates': ['id', 'emp_id', 'certificate_name', 'issuing_organization',
                    'issue_date', 'expiry_date', 'status'],
    'promotion_requests': ['id', 'emp_id', 'current_position', 'proposed_position',
                          'status', 'requested_by', 'manager_approved_by', 'hr_approved_by'],
    'asset_requests': ['id', 'emp_id', 'asset_type', 'justification', 'status',
                      'requested_date', 'manager_approved_by'],
    'goals': ['id', 'emp_id', 'goal_title', 'description', 'target_date', 'status',
              'progress', 'review_period', 'created_by'],
    'teams': ['id', 'team_name', 'department', 'team_lead_id', 'description',
              'status', 'created_at'],
    'positions': ['id', 'position_name', 'team_id', 'level', 'description',
                  'status', 'created_at'],
    'compliance_requirements': ['id', 'requirement_name', 'requirement_type',
                               'due_date', 'status', 'created_by'],
    'onboarding': ['id', 'emp_id', 'start_date', 'buddy_id', 'it_setup',
                  'workspace_setup', 'system_access', 'status'],
    'shift_templates': ['id', 'shift_name', 'shift_type', 'start_time', 'end_time'],
    'shift_schedules': ['id', 'emp_id', 'shift_id', 'shift_date', 'location', 'status'],
    'audit_logs': ['id', 'user_id', 'action', 'timestamp'],
}

print("\n🔍 Checking for missing columns...\n")
print("=" * 70)

with get_db_connection() as conn:
    cursor = conn.cursor()

    missing_report = []
    all_good = []

    for table_name, expected_cols in expected_columns.items():
        # Check if table exists
        cursor.execute("""
            SELECT COUNT(*) as cnt FROM information_schema.tables
            WHERE table_name = %s
        """, (table_name,))

        if cursor.fetchone()['cnt'] == 0:
            print(f"❌ TABLE MISSING: {table_name}")
            missing_report.append({
                'table': table_name,
                'issue': 'TABLE_MISSING',
                'columns': []
            })
            continue

        # Get actual columns
        cursor.execute("""
            SELECT column_name FROM information_schema.columns
            WHERE table_name = %s
            ORDER BY ordinal_position
        """, (table_name,))

        actual_cols = [row['column_name'] for row in cursor.fetchall()]

        # Find missing columns
        missing_cols = [col for col in expected_cols if col not in actual_cols]

        if missing_cols:
            print(f"\n⚠️  TABLE: {table_name}")
            print(f"   Missing {len(missing_cols)} columns:")
            for col in missing_cols:
                print(f"      - {col}")

            missing_report.append({
                'table': table_name,
                'issue': 'MISSING_COLUMNS',
                'columns': missing_cols
            })
        else:
            all_good.append(table_name)
            print(f"✅ {table_name} - All required columns present")

print("\n" + "=" * 70)
print(f"\n📊 Summary:")
print(f"   ✅ Tables OK: {len(all_good)}")
print(f"   ⚠️  Tables with missing columns: {len([r for r in missing_report if r['issue'] == 'MISSING_COLUMNS'])}")
print(f"   ❌ Missing tables: {len([r for r in missing_report if r['issue'] == 'TABLE_MISSING'])}")

# Generate SQL fixes
if missing_report:
    print("\n\n🔧 SQL to fix missing columns:")
    print("=" * 70)

    for item in missing_report:
        if item['issue'] == 'MISSING_COLUMNS':
            print(f"\n-- Fix {item['table']}")
            for col in item['columns']:
                # Guess column type
                if col.endswith('_id') or col == 'id':
                    col_type = "INTEGER"
                elif col.endswith('_date'):
                    col_type = "DATE"
                elif col.endswith('_at'):
                    col_type = "TIMESTAMP DEFAULT NOW()"
                elif col in ['status', 'description', 'title', 'category', 'position',
                            'department', 'shift_type', 'location', 'action']:
                    col_type = "TEXT"
                elif col in ['cost', 'progress']:
                    col_type = "REAL DEFAULT 0"
                else:
                    col_type = "TEXT"

                print(f"ALTER TABLE {item['table']} ADD COLUMN IF NOT EXISTS {col} {col_type};")

print("\n" + "=" * 70)
