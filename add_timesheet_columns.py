"""
Add Missing Columns to Timesheets Table
This script adds overtime tracking columns to the timesheets table
"""

from database import get_db_connection

def add_timesheet_columns():
    """Add regular_hours, overtime_hours, and break_minutes columns"""
    print('=' * 60)
    print('ADDING MISSING COLUMNS TO TIMESHEETS TABLE')
    print('=' * 60)

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            print('\n1. Adding columns...')
            cursor.execute("""
                ALTER TABLE timesheets
                ADD COLUMN IF NOT EXISTS regular_hours NUMERIC(5,2) DEFAULT 0,
                ADD COLUMN IF NOT EXISTS overtime_hours NUMERIC(5,2) DEFAULT 0,
                ADD COLUMN IF NOT EXISTS break_minutes INTEGER DEFAULT 0
            """)

            conn.commit()
            print('   ✅ Columns added successfully')

            # Verify
            print('\n2. Verifying columns...')
            cursor.execute("""
                SELECT column_name FROM information_schema.columns
                WHERE table_name='timesheets'
                AND column_name IN ('regular_hours', 'overtime_hours', 'break_minutes')
            """)
            columns = cursor.fetchall()

            if len(columns) == 3:
                print(f'   ✅ Verified {len(columns)} columns:')
                for col in columns:
                    print(f'      - {col["column_name"]}')
            else:
                print(f'   ⚠️ Warning: Expected 3 columns, found {len(columns)}')

            print('\n' + '=' * 60)
            print('✅ TIMESHEET COLUMNS ADDED SUCCESSFULLY!')
            print('=' * 60)
            return True

    except Exception as e:
        print(f'\n❌ ERROR: {str(e)}')
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    add_timesheet_columns()
