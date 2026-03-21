from database import get_db_connection

with get_db_connection() as conn:
    cursor = conn.cursor()

    print("Checking Employee EXL-003...")
    cursor.execute("SELECT * FROM employees WHERE employee_id = 'EXL-003'")
    emp = cursor.fetchone()
    if emp:
        print(f"✅ Employee found: {emp['first_name']} {emp['last_name']} (ID: {emp['id']})")

        cursor.execute("SELECT * FROM leave_balance WHERE emp_id = ?", (emp['id'],))
        balances = cursor.fetchall()
        if balances:
            print(f"✅ Found {len(balances)} leave balance records:")
            for b in balances:
                print(f"   - {b['leave_type']}: {b['remaining_days']}/{b['total_days']} days")
        else:
            print("❌ No leave balance records found! Creating them now...")

            leave_types = [
                ('Annual Leave', 20.0),
                ('Sick Leave', 10.0),
                ('Personal Leave', 5.0)
            ]
            for leave_type, total_days in leave_types:
                cursor.execute("""
                    INSERT INTO leave_balance (emp_id, leave_type, total_days, remaining_days, year)
                    VALUES (?, ?, ?, ?, 2024)
                """, (emp['id'], leave_type, total_days, total_days))
            conn.commit()
            print("✅ Leave balances created!")
    else:
        print("❌ Employee not found!")
