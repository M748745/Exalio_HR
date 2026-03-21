"""
RELOAD DATA - Fixed column names
"""

from database import get_db_connection

def reload_data():
    print("=" * 60)
    print("RELOADING DATABASE")
    print("=" * 60)

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # Clear old data
            print("\n1. Clearing old data...")
            tables = ['notifications', 'leave_requests', 'financial_records', 'grades',
                     'leave_balance', 'users', 'employees']

            for table in tables:
                try:
                    cursor.execute(f"DELETE FROM {table}")
                    print(f"   ✅ {table}")
                except Exception as e:
                    print(f"   ⚠️  {table}: {e}")

            conn.commit()

            # Load data
            print("\n2. Loading all 9 employees...")
            cursor.execute("""
                INSERT INTO employees (id, employee_id, first_name, last_name, email, phone, department, team_tag, position, manager_id, grade, status, join_date, created_at, updated_at) VALUES
                (1, 'EXL-001', 'Admin', 'HR', 'admin@exalio.com', '+1234567890', 'Human Resources', NULL, 'HR Director', NULL, 'A+', 'Active', '2020-01-01', NOW(), NOW()),
                (2, 'EXL-002', 'John', 'Manager', 'john.manager@exalio.com', '+1234567891', 'Engineering', 'app', 'Engineering Manager', NULL, 'A', 'Active', '2020-06-01', NOW(), NOW()),
                (3, 'EXL-003', 'Sarah', 'Developer', 'sarah.dev@exalio.com', '+1234567892', 'Engineering', 'app', 'Senior Developer', 2, 'A', 'Active', '2021-03-15', NOW(), NOW()),
                (4, 'EXL-004', 'Mike', 'Chen', 'mike.chen@exalio.com', NULL, 'Engineering', 'app', 'Developer', 2, 'B', 'Active', '2021-01-01', NOW(), NOW()),
                (5, 'EXL-005', 'Emily', 'Brown', 'emily.brown@exalio.com', NULL, 'Marketing', NULL, 'Marketing Manager', 1, 'A', 'Active', '2021-01-01', NOW(), NOW()),
                (6, 'EXL-006', 'David', 'Wilson', 'david.wilson@exalio.com', NULL, 'Finance', NULL, 'Financial Analyst', 1, 'B+', 'Active', '2021-01-01', NOW(), NOW()),
                (7, 'EXL-007', 'Lisa', 'Anderson', 'lisa.anderson@exalio.com', NULL, 'Engineering', 'data', 'Data Engineer', 2, 'B+', 'Active', '2021-01-01', NOW(), NOW()),
                (8, 'EXL-008', 'Tom', 'Martinez', 'tom.martinez@exalio.com', NULL, 'Engineering', 'ai', 'AI Engineer', 2, 'A', 'Active', '2021-01-01', NOW(), NOW()),
                (10, 'TEST-001', 'Test', 'Employee', 'test.employee@exalio.com', NULL, 'Engineering', NULL, 'Senior Test Engineer', NULL, 'B', 'Active', '2026-03-18', NOW(), NOW())
            """)
            print("   ✅ 9 employees loaded")

            print("\n3. Loading all 9 users...")
            cursor.execute("""
                INSERT INTO users (id, username, password, role, employee_id, is_active, created_at) VALUES
                (1, 'admin@exalio.com', '240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9', 'hr_admin', 1, 1, NOW()),
                (2, 'john.manager@exalio.com', '866485796cfa8d7c0cf7111640205b83076433547577511d81f8030ae99ecea5', 'manager', 2, 1, NOW()),
                (3, 'sarah.dev@exalio.com', 'e03d3ec8d5035f8721f5dc64546e59ed790dbcb3b7b598fe57057ccd7b683b00', 'employee', 3, 1, NOW()),
                (4, 'mike.chen@exalio.com', 'e03d3ec8d5035f8721f5dc64546e59ed790dbcb3b7b598fe57057ccd7b683b00', 'employee', 4, 1, NOW()),
                (5, 'emily.brown@exalio.com', 'e03d3ec8d5035f8721f5dc64546e59ed790dbcb3b7b598fe57057ccd7b683b00', 'employee', 5, 1, NOW()),
                (6, 'david.wilson@exalio.com', 'e03d3ec8d5035f8721f5dc64546e59ed790dbcb3b7b598fe57057ccd7b683b00', 'employee', 6, 1, NOW()),
                (7, 'lisa.anderson@exalio.com', 'e03d3ec8d5035f8721f5dc64546e59ed790dbcb3b7b598fe57057ccd7b683b00', 'employee', 7, 1, NOW()),
                (8, 'tom.martinez@exalio.com', 'e03d3ec8d5035f8721f5dc64546e59ed790dbcb3b7b598fe57057ccd7b683b00', 'employee', 8, 1, NOW()),
                (10, 'test.employee@exalio.com', 'ecd71870d1963316a97e3ac3408c9835ad8cf0f3c1bc703527c30265534f75ae', 'employee', 10, 1, NOW())
            """)
            print("   ✅ 9 users loaded")
            print("      • admin@exalio.com / admin123")
            print("      • john.manager@exalio.com / manager123")
            print("      • sarah.dev@exalio.com / emp123")
            print("      • mike.chen@exalio.com / emp123")
            print("      • emily.brown@exalio.com / emp123")
            print("      • david.wilson@exalio.com / emp123")
            print("      • lisa.anderson@exalio.com / emp123")
            print("      • tom.martinez@exalio.com / emp123")
            print("      • test.employee@exalio.com / testpass")

            print("\n4. Loading leave balance (27 records)...")
            cursor.execute("""
                INSERT INTO leave_balance (emp_id, leave_type, total_days, used_days, remaining_days, year) VALUES
                (1, 'Annual Leave', 20, 0, 20, 2024), (1, 'Sick Leave', 10, 0, 10, 2024), (1, 'Personal Leave', 5, 0, 5, 2024),
                (2, 'Annual Leave', 20, 0, 20, 2024), (2, 'Sick Leave', 10, 0, 10, 2024), (2, 'Personal Leave', 5, 0, 5, 2024),
                (3, 'Annual Leave', 20, 5, 15, 2024), (3, 'Sick Leave', 10, 0, 10, 2024), (3, 'Personal Leave', 5, 0, 5, 2024),
                (4, 'Annual Leave', 20, 0, 20, 2024), (4, 'Sick Leave', 10, 0, 10, 2024), (4, 'Personal Leave', 5, 0, 5, 2024),
                (5, 'Annual Leave', 20, 0, 20, 2024), (5, 'Sick Leave', 10, 0, 10, 2024), (5, 'Personal Leave', 5, 0, 5, 2024),
                (6, 'Annual Leave', 20, 0, 20, 2024), (6, 'Sick Leave', 10, 0, 10, 2024), (6, 'Personal Leave', 5, 0, 5, 2024),
                (7, 'Annual Leave', 20, 0, 20, 2024), (7, 'Sick Leave', 10, 0, 10, 2024), (7, 'Personal Leave', 5, 0, 5, 2024),
                (8, 'Annual Leave', 20, 0, 20, 2024), (8, 'Sick Leave', 10, 0, 10, 2024), (8, 'Personal Leave', 5, 0, 5, 2024),
                (10, 'Annual Leave', 20, 0, 20, 2026), (10, 'Sick Leave', 10, 0, 10, 2026), (10, 'Personal Leave', 5, 0, 5, 2026)
            """)
            print("   ✅ 27 leave balance records")

            print("\n5. Loading grades, financial records, leave requests, notifications...")
            cursor.execute("""
                INSERT INTO grades (emp_id, period, overall_grade, score, performance, technical, teamwork, leadership, comments, evaluated_by, created_at, updated_at)
                VALUES (3, 'Q1 2024 Test', 'A', 85, 4, 5, 4, 3, 'Excellent performance', 1, NOW(), NOW())
            """)

            cursor.execute("""
                INSERT INTO financial_records (emp_id, base_salary, allowances, bonus, deductions, net_pay, currency, period, created_at)
                VALUES (3, 8000.0, 1000.0, 500.0, 200.0, 9300.0, 'USD', '2024-01', NOW())
            """)

            cursor.execute("""
                INSERT INTO leave_requests (emp_id, leave_type, start_date, end_date, days, reason, status, manager_id, hr_comments, created_at, approved_date)
                VALUES (3, 'Annual Leave', '2026-03-25', '2026-03-29', 5, 'Testing leave workflow', 'HR Approved', 2, NULL, NOW(), NOW())
            """)

            cursor.execute("""
                INSERT INTO notifications (recipient_id, title, message, type, is_read, created_at) VALUES
                (3, 'Welcome to Exalio HR System', 'Your account has been created successfully!', 'success', 0, NOW()),
                (3, 'Test Notification', 'This is a test notification', 'info', 1, NOW())
            """)
            print("   ✅ Other records loaded")

            conn.commit()

            # Verify
            print("\n" + "=" * 60)
            print("✅ DATA LOADED SUCCESSFULLY!")
            print("=" * 60)

            cursor.execute("SELECT COUNT(*) as cnt FROM employees")
            print(f"Employees: {cursor.fetchone()['cnt']}")

            cursor.execute("SELECT COUNT(*) as cnt FROM users")
            print(f"Users: {cursor.fetchone()['cnt']}")

            cursor.execute("SELECT COUNT(*) as cnt FROM leave_balance")
            print(f"Leave Balance: {cursor.fetchone()['cnt']}")

            print("\n" + "=" * 60)
            print("LOGIN NOW:")
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
    reload_data()
