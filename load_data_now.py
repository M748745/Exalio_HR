"""
Load seed data into Neon PostgreSQL database NOW
Run this script to initialize the database with all SQLite data
"""

from database import get_db_connection
import sys

def check_and_load_data():
    """Check if data exists and load if needed"""

    print("=" * 60)
    print("NEON DATABASE INITIALIZATION")
    print("=" * 60)

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # Check if employees table exists
            print("\n1. Checking if tables exist...")
            cursor.execute("""
                SELECT COUNT(*) as count FROM information_schema.tables
                WHERE table_schema = 'public' AND table_name = 'employees'
            """)
            result = cursor.fetchone()

            if not result or result['count'] == 0:
                print("   ❌ Tables don't exist! Creating them now...")

                # Run full initialization
                from init_postgres_on_cloud import init_postgres_from_sqlite
                success = init_postgres_from_sqlite()

                if success:
                    print("\n   ✅ Database initialized successfully!")
                else:
                    print("\n   ❌ Initialization failed!")
                    return False
            else:
                print("   ✅ Tables exist")

                # Check if data exists
                print("\n2. Checking data...")
                cursor.execute("SELECT COUNT(*) as cnt FROM employees")
                emp_count = cursor.fetchone()['cnt']
                print(f"   Employees: {emp_count}")

                cursor.execute("SELECT COUNT(*) as cnt FROM users")
                user_count = cursor.fetchone()['cnt']
                print(f"   Users: {user_count}")

                if emp_count == 0 or user_count == 0:
                    print("\n   ❌ No data found! Loading data now...")

                    # Load just the data (tables already exist)
                    print("\n3. Loading seed data...")

                    sample_data_sql = """
                    -- Employees (9 rows)
                    INSERT INTO employees (id, employee_id, first_name, last_name, email, phone, date_of_birth, gender, national_id, address, emergency_contact, department, team_tag, position, manager_id, grade, status, join_date, location, bio, photo, created_at, updated_at) VALUES
                    (1, 'EXL-001', 'Admin', 'HR', 'admin@exalio.com', '+1234567890', NULL, NULL, NULL, NULL, NULL, 'Human Resources', NULL, 'HR Director', NULL, 'A+', 'Active', '2020-01-01', NULL, NULL, NULL, '2026-03-17 20:21:52', '2026-03-17 20:21:52'),
                    (2, 'EXL-002', 'John', 'Manager', 'john.manager@exalio.com', '+1234567891', NULL, NULL, NULL, NULL, NULL, 'Engineering', 'app', 'Engineering Manager', NULL, 'A', 'Active', '2020-06-01', NULL, NULL, NULL, '2026-03-17 20:21:52', '2026-03-17 20:21:52'),
                    (3, 'EXL-003', 'Sarah', 'Developer', 'sarah.dev@exalio.com', '+1234567892', NULL, NULL, NULL, NULL, NULL, 'Engineering', 'app', 'Senior Developer', 2, 'A', 'Active', '2021-03-15', NULL, NULL, NULL, '2026-03-17 20:21:52', '2026-03-17 20:21:52'),
                    (4, 'EXL-004', 'Mike', 'Chen', 'mike.chen@exalio.com', NULL, NULL, NULL, NULL, NULL, NULL, 'Engineering', 'app', 'Developer', 2, 'B', 'Active', '2021-01-01', NULL, NULL, NULL, '2026-03-17 20:21:52', '2026-03-17 20:21:52'),
                    (5, 'EXL-005', 'Emily', 'Brown', 'emily.brown@exalio.com', NULL, NULL, NULL, NULL, NULL, NULL, 'Marketing', NULL, 'Marketing Manager', 1, 'A', 'Active', '2021-01-01', NULL, NULL, NULL, '2026-03-17 20:21:52', '2026-03-17 20:21:52'),
                    (6, 'EXL-006', 'David', 'Wilson', 'david.wilson@exalio.com', NULL, NULL, NULL, NULL, NULL, NULL, 'Finance', NULL, 'Financial Analyst', 1, 'B+', 'Active', '2021-01-01', NULL, NULL, NULL, '2026-03-17 20:21:52', '2026-03-17 20:21:52'),
                    (7, 'EXL-007', 'Lisa', 'Anderson', 'lisa.anderson@exalio.com', NULL, NULL, NULL, NULL, NULL, NULL, 'Engineering', 'data', 'Data Engineer', 2, 'B+', 'Active', '2021-01-01', NULL, NULL, NULL, '2026-03-17 20:21:52', '2026-03-17 20:21:52'),
                    (8, 'EXL-008', 'Tom', 'Martinez', 'tom.martinez@exalio.com', NULL, NULL, NULL, NULL, NULL, NULL, 'Engineering', 'ai', 'AI Engineer', 2, 'A', 'Active', '2021-01-01', NULL, NULL, NULL, '2026-03-17 20:21:52', '2026-03-17 20:21:52'),
                    (10, 'TEST-001', 'Test', 'Employee', 'test.employee@exalio.com', NULL, NULL, NULL, NULL, NULL, NULL, 'Engineering', NULL, 'Senior Test Engineer', NULL, 'B', 'Active', '2026-03-18', NULL, NULL, NULL, '2026-03-18 02:17:15', '2026-03-18 02:17:15')
                    ON CONFLICT (employee_id) DO NOTHING;

                    -- Users (9 rows)
                    INSERT INTO users (id, username, password, role, employee_id, is_active, created_at, last_login) VALUES
                    (1, 'admin@exalio.com', '240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9', 'hr_admin', 1, 1, '2026-03-17 20:21:52', '2026-03-18 02:17:15'),
                    (2, 'john.manager@exalio.com', '866485796cfa8d7c0cf7111640205b83076433547577511d81f8030ae99ecea5', 'manager', 2, 1, '2026-03-17 20:21:52', '2026-03-18 02:17:15'),
                    (3, 'sarah.dev@exalio.com', 'e03d3ec8d5035f8721f5dc64546e59ed790dbcb3b7b598fe57057ccd7b683b00', 'employee', 3, 1, '2026-03-17 20:21:52', '2026-03-18 02:17:15'),
                    (4, 'mike.chen@exalio.com', 'e03d3ec8d5035f8721f5dc64546e59ed790dbcb3b7b598fe57057ccd7b683b00', 'employee', 4, 1, '2026-03-17 20:21:52', NULL),
                    (5, 'emily.brown@exalio.com', 'e03d3ec8d5035f8721f5dc64546e59ed790dbcb3b7b598fe57057ccd7b683b00', 'employee', 5, 1, '2026-03-17 20:21:52', NULL),
                    (6, 'david.wilson@exalio.com', 'e03d3ec8d5035f8721f5dc64546e59ed790dbcb3b7b598fe57057ccd7b683b00', 'employee', 6, 1, '2026-03-17 20:21:52', NULL),
                    (7, 'lisa.anderson@exalio.com', 'e03d3ec8d5035f8721f5dc64546e59ed790dbcb3b7b598fe57057ccd7b683b00', 'employee', 7, 1, '2026-03-17 20:21:52', NULL),
                    (8, 'tom.martinez@exalio.com', 'e03d3ec8d5035f8721f5dc64546e59ed790dbcb3b7b598fe57057ccd7b683b00', 'employee', 8, 1, '2026-03-17 20:21:52', NULL),
                    (10, 'test.employee@exalio.com', 'ecd71870d1963316a97e3ac3408c9835ad8cf0f3c1bc703527c30265534f75ae', 'employee', 10, 1, '2026-03-17 22:17:15', NULL)
                    ON CONFLICT (username) DO NOTHING;

                    -- Leave balance (27 rows)
                    INSERT INTO leave_balance (id, emp_id, leave_type, total_days, used_days, remaining_days, year) VALUES
                    (1, 1, 'Annual Leave', 20.0, 0.0, 20.0, 2024),
                    (2, 1, 'Sick Leave', 10.0, 0.0, 10.0, 2024),
                    (3, 1, 'Personal Leave', 5.0, 0.0, 5.0, 2024),
                    (4, 6, 'Annual Leave', 20.0, 0.0, 20.0, 2024),
                    (5, 6, 'Sick Leave', 10.0, 0.0, 10.0, 2024),
                    (6, 6, 'Personal Leave', 5.0, 0.0, 5.0, 2024),
                    (7, 5, 'Annual Leave', 20.0, 0.0, 20.0, 2024),
                    (8, 5, 'Sick Leave', 10.0, 0.0, 10.0, 2024),
                    (9, 5, 'Personal Leave', 5.0, 0.0, 5.0, 2024),
                    (10, 2, 'Annual Leave', 20.0, 0.0, 20.0, 2024),
                    (11, 2, 'Sick Leave', 10.0, 0.0, 10.0, 2024),
                    (12, 2, 'Personal Leave', 5.0, 0.0, 5.0, 2024),
                    (13, 7, 'Annual Leave', 20.0, 0.0, 20.0, 2024),
                    (14, 7, 'Sick Leave', 10.0, 0.0, 10.0, 2024),
                    (15, 7, 'Personal Leave', 5.0, 0.0, 5.0, 2024),
                    (16, 4, 'Annual Leave', 20.0, 0.0, 20.0, 2024),
                    (17, 4, 'Sick Leave', 10.0, 0.0, 10.0, 2024),
                    (18, 4, 'Personal Leave', 5.0, 0.0, 5.0, 2024),
                    (19, 3, 'Annual Leave', 20.0, 5.0, 15.0, 2024),
                    (20, 3, 'Sick Leave', 10.0, 0.0, 10.0, 2024),
                    (21, 3, 'Personal Leave', 5.0, 0.0, 5.0, 2024),
                    (22, 8, 'Annual Leave', 20.0, 0.0, 20.0, 2024),
                    (23, 8, 'Sick Leave', 10.0, 0.0, 10.0, 2024),
                    (24, 8, 'Personal Leave', 5.0, 0.0, 5.0, 2024),
                    (28, 10, 'Annual Leave', 20.0, 0.0, 20.0, 2026),
                    (29, 10, 'Sick Leave', 10.0, 0.0, 10.0, 2026),
                    (30, 10, 'Personal Leave', 5.0, 0.0, 5.0, 2026)
                    ON CONFLICT DO NOTHING;

                    -- Grades (1 row)
                    INSERT INTO grades (id, emp_id, period, overall_grade, score, performance, technical, teamwork, leadership, comments, evaluated_by, created_at, updated_at) VALUES
                    (1, 3, 'Q1 2024 Test', 'A', 85, 4, 5, 4, 3, 'Excellent performance', 1, '2026-03-17 22:17:15', '2026-03-17 22:17:15')
                    ON CONFLICT DO NOTHING;

                    -- Financial records (1 row)
                    INSERT INTO financial_records (id, emp_id, base_salary, allowances, bonus, deductions, net_pay, currency, payment_date, period, created_at) VALUES
                    (1, 3, 8000.0, 1000.0, 500.0, 200.0, 9300.0, 'USD', NULL, '2024-01', '2026-03-17 20:21:52')
                    ON CONFLICT DO NOTHING;

                    -- Leave requests (1 row)
                    INSERT INTO leave_requests (id, emp_id, leave_type, start_date, end_date, days, reason, status, manager_approved_by, manager_approval_date, manager_comments, hr_approved_by, hr_approval_date, hr_comments, created_at) VALUES
                    (1, 3, 'Annual Leave', '2026-03-25', '2026-03-29', 5.0, 'Testing leave workflow', 'HR Approved', 2, '2026-03-18 02:17:15', NULL, 1, '2026-03-18 02:17:15', NULL, '2026-03-17 22:17:15')
                    ON CONFLICT DO NOTHING;

                    -- Notifications (2 rows)
                    INSERT INTO notifications (id, recipient_id, title, message, type, is_read, action_url, created_at) VALUES
                    (1, 3, 'Welcome to Exalio HR System', 'Your account has been created successfully!', 'success', 0, NULL, '2026-03-17 20:21:52'),
                    (2, 3, 'Test Notification', 'This is a test notification', 'info', 1, NULL, '2026-03-17 22:17:15')
                    ON CONFLICT DO NOTHING;
                    """

                    cursor.execute(sample_data_sql)
                    conn.commit()

                    print("   ✅ Data loaded successfully!")
                else:
                    print("   ✅ Data already exists")

            # Verify final state
            print("\n" + "=" * 60)
            print("FINAL VERIFICATION")
            print("=" * 60)

            cursor.execute("SELECT COUNT(*) as cnt FROM employees")
            emp_count = cursor.fetchone()['cnt']
            print(f"✅ Employees: {emp_count}")

            cursor.execute("SELECT COUNT(*) as cnt FROM users")
            user_count = cursor.fetchone()['cnt']
            print(f"✅ Users: {user_count}")

            cursor.execute("SELECT COUNT(*) as cnt FROM leave_balance")
            leave_count = cursor.fetchone()['cnt']
            print(f"✅ Leave Balance: {leave_count}")

            # Show users
            print("\n" + "=" * 60)
            print("USERS IN DATABASE")
            print("=" * 60)
            cursor.execute("SELECT username, role FROM users ORDER BY id")
            users = cursor.fetchall()
            for user in users:
                print(f"  • {user['username']} ({user['role']})")

            print("\n" + "=" * 60)
            print("✅ DATABASE READY!")
            print("=" * 60)
            print("\nYou can now login with:")
            print("  Username: admin@exalio.com")
            print("  Password: admin123")
            print("=" * 60)

            return True

    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = check_and_load_data()
    sys.exit(0 if success else 1)
