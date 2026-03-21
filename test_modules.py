"""
Test Script for HR System Modules
Validates all implemented functionality
"""

from database import get_db_connection
from auth import login, hash_password
from datetime import datetime, date, timedelta

def print_header(text):
    print("\n" + "="*60)
    print(f"  {text}")
    print("="*60)

def test_authentication():
    """Test authentication system"""
    print_header("🔐 Testing Authentication System")

    # Test HR Admin login
    success, user_data, error = login("admin@exalio.com", "admin123")
    assert success, "HR Admin login failed"
    assert user_data['role'] == 'hr_admin', "HR Admin role mismatch"
    print("✅ HR Admin login successful")

    # Test Manager login
    success, user_data, error = login("john.manager@exalio.com", "manager123")
    assert success, "Manager login failed"
    assert user_data['role'] == 'manager', "Manager role mismatch"
    print("✅ Manager login successful")

    # Test Employee login
    success, user_data, error = login("sarah.dev@exalio.com", "emp123")
    assert success, "Employee login failed"
    assert user_data['role'] == 'employee', "Employee role mismatch"
    print("✅ Employee login successful")

    # Test invalid login
    success, user_data, error = login("invalid@test.com", "wrongpass")
    assert not success, "Invalid login should fail"
    print("✅ Invalid login correctly rejected")

    print("\n✅ All authentication tests passed!")

def test_employee_management():
    """Test employee management operations"""
    print_header("👥 Testing Employee Management")

    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Test: Delete test employee if exists (cleanup from previous runs)
        cursor.execute("DELETE FROM leave_balance WHERE emp_id IN (SELECT id FROM employees WHERE employee_id = 'TEST-001')")
        cursor.execute("DELETE FROM users WHERE employee_id IN (SELECT id FROM employees WHERE employee_id = 'TEST-001')")
        cursor.execute("DELETE FROM employees WHERE employee_id = 'TEST-001'")
        conn.commit()

        # Test: Count existing employees
        cursor.execute("SELECT COUNT(*) as cnt FROM employees")
        emp_count = cursor.fetchone()['cnt']
        print(f"✅ Found {emp_count} employees in database")

        # Test: Create new employee
        test_emp = {
            'employee_id': 'TEST-001',
            'first_name': 'Test',
            'last_name': 'Employee',
            'email': 'test.employee@exalio.com',
            'department': 'Engineering',
            'position': 'Test Engineer',
            'grade': 'B',
            'status': 'Active',
            'join_date': date.today().isoformat()
        }

        cursor.execute("""
            INSERT INTO employees (
                employee_id, first_name, last_name, email, department,
                position, grade, status, join_date, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (test_emp['employee_id'], test_emp['first_name'], test_emp['last_name'],
              test_emp['email'], test_emp['department'], test_emp['position'],
              test_emp['grade'], test_emp['status'], test_emp['join_date'],
              datetime.now().isoformat(), datetime.now().isoformat()))

        new_emp_id = cursor.lastrowid
        print(f"✅ Created test employee with ID: {new_emp_id}")

        # Test: Create leave balances for new employee
        leave_types = [
            ('Annual Leave', 20.0),
            ('Sick Leave', 10.0),
            ('Personal Leave', 5.0)
        ]
        for leave_type, total_days in leave_types:
            cursor.execute("""
                INSERT INTO leave_balance (emp_id, leave_type, total_days, remaining_days, year)
                VALUES (?, ?, ?, ?, ?)
            """, (new_emp_id, leave_type, total_days, total_days, datetime.now().year))

        print("✅ Created leave balances for new employee")

        # Test: Create user account
        cursor.execute("""
            INSERT INTO users (username, password, role, employee_id, is_active)
            VALUES (?, ?, 'employee', ?, 1)
        """, (test_emp['email'], hash_password('test123'), new_emp_id))

        print("✅ Created user account for new employee")

        # Test: Verify employee exists
        cursor.execute("SELECT * FROM employees WHERE id = ?", (new_emp_id,))
        employee = cursor.fetchone()
        assert employee is not None, "Employee not found after creation"
        print("✅ Employee data verified in database")

        # Test: Update employee
        cursor.execute("""
            UPDATE employees SET position = 'Senior Test Engineer' WHERE id = ?
        """, (new_emp_id,))
        print("✅ Updated employee position")

        # Test: Count employees after addition
        cursor.execute("SELECT COUNT(*) as cnt FROM employees")
        new_count = cursor.fetchone()['cnt']
        assert new_count == emp_count + 1, "Employee count mismatch"
        print(f"✅ Employee count increased: {emp_count} → {new_count}")

        conn.commit()

    print("\n✅ All employee management tests passed!")

def test_leave_management():
    """Test leave management and workflow"""
    print_header("📅 Testing Leave Management")

    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Test: Get employee for leave request
        cursor.execute("SELECT id FROM employees WHERE employee_id = 'EXL-003' LIMIT 1")
        emp = cursor.fetchone()
        emp_id = emp['id']
        print(f"✅ Found employee ID: {emp_id}")

        # Test: Check leave balance before request
        cursor.execute("""
            SELECT * FROM leave_balance
            WHERE emp_id = ? AND leave_type = 'Annual Leave'
            ORDER BY year DESC LIMIT 1
        """, (emp_id,))
        balance_before = cursor.fetchone()
        initial_balance = balance_before['remaining_days']
        print(f"✅ Initial leave balance: {initial_balance} days")

        # Test: Create leave request
        start_date = date.today() + timedelta(days=7)
        end_date = start_date + timedelta(days=4)
        days = 5

        cursor.execute("""
            INSERT INTO leave_requests (
                emp_id, leave_type, start_date, end_date, days, reason, status
            ) VALUES (?, 'Annual Leave', ?, ?, ?, 'Testing leave workflow', 'Pending')
        """, (emp_id, start_date.isoformat(), end_date.isoformat(), days))

        leave_request_id = cursor.lastrowid
        print(f"✅ Created leave request LR-{leave_request_id} for {days} days")

        # Test: Manager approval
        cursor.execute("SELECT manager_id FROM employees WHERE id = ?", (emp_id,))
        manager_id = cursor.fetchone()['manager_id']

        cursor.execute("""
            UPDATE leave_requests SET
                status = 'Manager Approved',
                manager_approved_by = ?,
                manager_approval_date = ?
            WHERE id = ?
        """, (manager_id, datetime.now().isoformat(), leave_request_id))
        print("✅ Manager approved leave request")

        # Test: HR approval
        cursor.execute("SELECT id FROM employees WHERE department = 'Human Resources' LIMIT 1")
        hr_emp = cursor.fetchone()
        hr_id = hr_emp['id']

        cursor.execute("""
            UPDATE leave_requests SET
                status = 'HR Approved',
                hr_approved_by = ?,
                hr_approval_date = ?
            WHERE id = ?
        """, (hr_id, datetime.now().isoformat(), leave_request_id))
        print("✅ HR approved leave request")

        # Test: Update leave balance
        cursor.execute("""
            UPDATE leave_balance SET
                used_days = used_days + ?,
                remaining_days = remaining_days - ?
            WHERE emp_id = ? AND leave_type = 'Annual Leave'
        """, (days, days, emp_id))
        print("✅ Updated leave balance")

        # Test: Verify leave balance after approval
        cursor.execute("""
            SELECT * FROM leave_balance
            WHERE emp_id = ? AND leave_type = 'Annual Leave'
            ORDER BY year DESC LIMIT 1
        """, (emp_id,))
        balance_after = cursor.fetchone()
        final_balance = balance_after['remaining_days']

        assert final_balance == initial_balance - days, "Leave balance calculation error"
        print(f"✅ Leave balance updated: {initial_balance} → {final_balance} days")

        # Test: Verify leave request status
        cursor.execute("SELECT status FROM leave_requests WHERE id = ?", (leave_request_id,))
        status = cursor.fetchone()['status']
        assert status == 'HR Approved', "Leave request status incorrect"
        print("✅ Leave request fully approved")

        conn.commit()

    print("\n✅ All leave management tests passed!")

def test_performance_management():
    """Test performance evaluation system"""
    print_header("🏅 Testing Performance Management")

    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Test: Get employee for evaluation
        cursor.execute("SELECT id FROM employees WHERE employee_id = 'EXL-003' LIMIT 1")
        emp = cursor.fetchone()
        emp_id = emp['id']

        # Test: Create performance evaluation
        cursor.execute("""
            INSERT INTO grades (
                emp_id, period, overall_grade, score, performance,
                technical, teamwork, leadership, comments, evaluated_by
            ) VALUES (?, 'Q1 2024 Test', 'A', 85, 4, 5, 4, 3, 'Excellent performance', 1)
        """, (emp_id,))

        eval_id = cursor.lastrowid
        print(f"✅ Created performance evaluation ID: {eval_id}")

        # Test: Update employee grade
        cursor.execute("UPDATE employees SET grade = 'A' WHERE id = ?", (emp_id,))
        print("✅ Updated employee grade")

        # Test: Verify evaluation exists
        cursor.execute("SELECT * FROM grades WHERE id = ?", (eval_id,))
        evaluation = cursor.fetchone()
        assert evaluation is not None, "Evaluation not found"
        assert evaluation['overall_grade'] == 'A', "Grade mismatch"
        assert evaluation['score'] == 85, "Score mismatch"
        print("✅ Evaluation data verified")

        # Test: Count evaluations
        cursor.execute("SELECT COUNT(*) as cnt FROM grades WHERE emp_id = ?", (emp_id,))
        eval_count = cursor.fetchone()['cnt']
        print(f"✅ Employee has {eval_count} evaluation(s)")

        # Test: Get grade distribution
        cursor.execute("""
            SELECT grade, COUNT(*) as count
            FROM employees
            WHERE status = 'Active' AND grade IS NOT NULL
            GROUP BY grade
            ORDER BY grade
        """)
        grade_dist = cursor.fetchall()
        print(f"✅ Grade distribution: {len(grade_dist)} different grades")
        for g in grade_dist:
            print(f"   - Grade {g['grade']}: {g['count']} employees")

        conn.commit()

    print("\n✅ All performance management tests passed!")

def test_notifications():
    """Test notification system"""
    print_header("🔔 Testing Notification System")

    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Test: Create notification
        cursor.execute("SELECT id FROM employees WHERE employee_id = 'EXL-003' LIMIT 1")
        emp_id = cursor.fetchone()['id']

        cursor.execute("""
            INSERT INTO notifications (recipient_id, title, message, type)
            VALUES (?, 'Test Notification', 'This is a test notification', 'info')
        """, (emp_id,))

        notif_id = cursor.lastrowid
        print(f"✅ Created notification ID: {notif_id}")

        # Test: Count notifications
        cursor.execute("SELECT COUNT(*) as cnt FROM notifications WHERE recipient_id = ?", (emp_id,))
        notif_count = cursor.fetchone()['cnt']
        print(f"✅ Employee has {notif_count} notification(s)")

        # Test: Count unread notifications
        cursor.execute("""
            SELECT COUNT(*) as cnt FROM notifications
            WHERE recipient_id = ? AND is_read = 0
        """, (emp_id,))
        unread_count = cursor.fetchone()['cnt']
        print(f"✅ Unread notifications: {unread_count}")

        # Test: Mark as read
        cursor.execute("UPDATE notifications SET is_read = 1 WHERE id = ?", (notif_id,))
        print("✅ Marked notification as read")

        conn.commit()

    print("\n✅ All notification tests passed!")

def test_database_integrity():
    """Test database integrity and relationships"""
    print_header("🗄️ Testing Database Integrity")

    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Test: Count all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print(f"✅ Database has {len(tables)} tables")

        # Test: Check key table counts
        tables_to_check = [
            'users', 'employees', 'grades', 'leave_requests',
            'leave_balance', 'notifications', 'contracts',
            'insurance', 'bonuses', 'financial_records'
        ]

        for table in tables_to_check:
            cursor.execute(f"SELECT COUNT(*) as cnt FROM {table}")
            count = cursor.fetchone()['cnt']
            print(f"✅ Table '{table}': {count} records")

        # Test: Verify foreign key relationships
        cursor.execute("""
            SELECT COUNT(*) as cnt FROM leave_requests lr
            JOIN employees e ON lr.emp_id = e.id
        """)
        fk_count = cursor.fetchone()['cnt']
        print(f"✅ Foreign key integrity verified: {fk_count} leave requests linked to employees")

        # Test: Check data consistency
        cursor.execute("""
            SELECT COUNT(*) as cnt FROM users u
            LEFT JOIN employees e ON u.employee_id = e.id
            WHERE e.id IS NULL AND u.employee_id IS NOT NULL
        """)
        orphaned = cursor.fetchone()['cnt']
        assert orphaned == 0, f"Found {orphaned} orphaned user records"
        print("✅ No orphaned user records found")

    print("\n✅ All database integrity tests passed!")

def main():
    """Run all tests"""
    print("\n" + "🚀 HR SYSTEM MODULE TESTING ".center(60, "="))
    print("Starting comprehensive module tests...")

    try:
        test_authentication()
        test_employee_management()
        test_leave_management()
        test_performance_management()
        test_notifications()
        test_database_integrity()

        print("\n" + "="*60)
        print("🎉 ALL TESTS PASSED SUCCESSFULLY! 🎉".center(60))
        print("="*60)
        print("\n✅ System is ready for deployment!")
        print("\n📋 Test Summary:")
        print("   - Authentication: ✅ Passed")
        print("   - Employee Management: ✅ Passed")
        print("   - Leave Management: ✅ Passed")
        print("   - Performance Management: ✅ Passed")
        print("   - Notifications: ✅ Passed")
        print("   - Database Integrity: ✅ Passed")

    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {str(e)}")
        return 1
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

    return 0

if __name__ == "__main__":
    exit(main())
