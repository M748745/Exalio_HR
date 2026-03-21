"""
Exalio HR System - Database Module
SQLite Database Schema with all 32 tables for complete HR management
"""

import sqlite3
import hashlib
import os
import shutil
from datetime import datetime
from contextlib import contextmanager

DATABASE_NAME = "hr_system.db"
_shared_connection = None
_connection_lock = None

def _get_shared_connection():
    """Get or create a shared database connection"""
    global _shared_connection, _connection_lock

    if _connection_lock is None:
        import threading
        _connection_lock = threading.Lock()

    if _shared_connection is not None:
        return _shared_connection

    with _connection_lock:
        if _shared_connection is not None:
            return _shared_connection

        # Try to use file-based database first
        try:
            # Check if we can write to current directory
            test_path = ".test_write"
            with open(test_path, 'w') as f:
                f.write("test")
            os.remove(test_path)

            # Use local database file
            _shared_connection = sqlite3.connect(DATABASE_NAME, check_same_thread=False)
            _shared_connection.row_factory = sqlite3.Row
            return _shared_connection
        except:
            pass

        # Try /tmp directory
        try:
            temp_db = "/tmp/hr_system.db"
            if os.path.exists(DATABASE_NAME):
                shutil.copy2(DATABASE_NAME, temp_db)
                os.chmod(temp_db, 0o666)

            _shared_connection = sqlite3.connect(temp_db, check_same_thread=False)
            _shared_connection.row_factory = sqlite3.Row
            return _shared_connection
        except:
            pass

        # Final fallback: in-memory with data loaded
        _shared_connection = sqlite3.connect(":memory:", check_same_thread=False)
        _shared_connection.row_factory = sqlite3.Row

        # Load data from source file if it exists
        if os.path.exists(DATABASE_NAME):
            try:
                source = sqlite3.connect(DATABASE_NAME)
                source.backup(_shared_connection)
                source.close()
            except Exception as e:
                # If backup fails, database will be empty - init_database() will create tables
                pass

        return _shared_connection

@contextmanager
def get_db_connection():
    """Context manager for database connections - uses shared connection"""
    conn = _get_shared_connection()

    # Verify connection is working
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.close()
    except Exception as e:
        # Connection is broken, recreate it
        global _shared_connection
        _shared_connection = None
        conn = _get_shared_connection()

    try:
        yield conn
        conn.commit()
    except Exception as e:
        try:
            conn.rollback()
        except:
            pass
        raise

def hash_password(password):
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def init_database():
    """Initialize all database tables"""
    with get_db_connection() as conn:
        cursor = conn.cursor()

        # 1. Users table (Authentication)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('employee', 'manager', 'hr_admin')),
                employee_id INTEGER,
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP,
                FOREIGN KEY (employee_id) REFERENCES employees(id)
            )
        """)

        # 2. Employees table (Core employee data)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS employees (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id TEXT UNIQUE NOT NULL,
                first_name TEXT NOT NULL,
                last_name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                phone TEXT,
                date_of_birth DATE,
                gender TEXT,
                national_id TEXT,
                address TEXT,
                emergency_contact TEXT,
                department TEXT NOT NULL,
                team_tag TEXT,
                position TEXT NOT NULL,
                manager_id INTEGER,
                grade TEXT,
                status TEXT DEFAULT 'Active' CHECK(status IN ('Active', 'Inactive', 'On Leave', 'Terminated')),
                join_date DATE NOT NULL,
                location TEXT,
                bio TEXT,
                photo TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (manager_id) REFERENCES employees(id)
            )
        """)

        # 3. Grades table (Performance evaluations)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS grades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                emp_id INTEGER NOT NULL,
                period TEXT NOT NULL,
                overall_grade TEXT NOT NULL,
                score INTEGER DEFAULT 0,
                performance INTEGER DEFAULT 0,
                technical INTEGER DEFAULT 0,
                teamwork INTEGER DEFAULT 0,
                leadership INTEGER DEFAULT 0,
                comments TEXT,
                evaluated_by INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (emp_id) REFERENCES employees(id),
                FOREIGN KEY (evaluated_by) REFERENCES employees(id)
            )
        """)

        # 4. Appraisals table (Multi-step appraisal workflow)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS appraisals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                emp_id INTEGER NOT NULL,
                period TEXT NOT NULL,
                type TEXT DEFAULT 'Annual',
                status TEXT DEFAULT 'Draft' CHECK(status IN ('Draft', 'Submitted', 'Manager Review', 'HR Review', 'Completed', 'Rejected')),
                self_rating TEXT,
                self_comments TEXT,
                manager_rating TEXT,
                manager_comments TEXT,
                hr_rating TEXT,
                hr_comments TEXT,
                reviewer_id INTEGER,
                due_date DATE,
                submitted_date TIMESTAMP,
                manager_review_date TIMESTAMP,
                hr_review_date TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (emp_id) REFERENCES employees(id),
                FOREIGN KEY (reviewer_id) REFERENCES employees(id)
            )
        """)

        # 5. Career plans table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS career_plans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                emp_id INTEGER NOT NULL,
                current_level TEXT,
                target_level TEXT,
                timeline TEXT,
                skills_required TEXT,
                milestones TEXT,
                status TEXT DEFAULT 'Active',
                created_by INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (emp_id) REFERENCES employees(id),
                FOREIGN KEY (created_by) REFERENCES employees(id)
            )
        """)

        # 6. Jobs table (Open positions)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                department TEXT NOT NULL,
                job_type TEXT NOT NULL,
                location TEXT,
                description TEXT,
                requirements TEXT,
                salary_range TEXT,
                status TEXT DEFAULT 'Open' CHECK(status IN ('Open', 'Closed', 'On Hold')),
                posted_by INTEGER,
                posted_date DATE,
                closing_date DATE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (posted_by) REFERENCES employees(id)
            )
        """)

        # 7. Job applications table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS job_applications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id INTEGER NOT NULL,
                emp_id INTEGER NOT NULL,
                cover_letter TEXT,
                status TEXT DEFAULT 'Pending' CHECK(status IN ('Pending', 'Shortlisted', 'Interviewed', 'Accepted', 'Rejected')),
                applied_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                reviewed_by INTEGER,
                review_date TIMESTAMP,
                notes TEXT,
                FOREIGN KEY (job_id) REFERENCES jobs(id),
                FOREIGN KEY (emp_id) REFERENCES employees(id),
                FOREIGN KEY (reviewed_by) REFERENCES employees(id)
            )
        """)

        # 8. Financial records table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS financial_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                emp_id INTEGER NOT NULL,
                base_salary REAL NOT NULL,
                allowances REAL DEFAULT 0,
                bonus REAL DEFAULT 0,
                deductions REAL DEFAULT 0,
                net_pay REAL NOT NULL,
                currency TEXT DEFAULT 'USD',
                payment_date DATE,
                period TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (emp_id) REFERENCES employees(id)
            )
        """)

        # 9. Bonuses table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bonuses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                emp_id INTEGER NOT NULL,
                bonus_type TEXT NOT NULL,
                amount REAL NOT NULL,
                calculation_method TEXT,
                period TEXT,
                status TEXT DEFAULT 'Pending' CHECK(status IN ('Pending', 'Manager Approved', 'HR Approved', 'Paid', 'Rejected')),
                recommended_by INTEGER,
                approved_by INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                paid_date DATE,
                FOREIGN KEY (emp_id) REFERENCES employees(id),
                FOREIGN KEY (recommended_by) REFERENCES employees(id),
                FOREIGN KEY (approved_by) REFERENCES employees(id)
            )
        """)

        # 10. Insurance table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS insurance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                emp_id INTEGER NOT NULL,
                provider TEXT NOT NULL,
                plan_name TEXT NOT NULL,
                coverage_type TEXT,
                premium_monthly REAL NOT NULL,
                network TEXT,
                dependants INTEGER DEFAULT 0,
                start_date DATE NOT NULL,
                renewal_date DATE NOT NULL,
                status TEXT DEFAULT 'Active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (emp_id) REFERENCES employees(id)
            )
        """)

        # 11. Contracts table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS contracts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                emp_id INTEGER NOT NULL,
                contract_type TEXT NOT NULL,
                start_date DATE NOT NULL,
                end_date DATE,
                status TEXT DEFAULT 'Active' CHECK(status IN ('Active', 'Expired', 'Renewed', 'Terminated')),
                renewal_status TEXT DEFAULT 'Not Due',
                terms TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (emp_id) REFERENCES employees(id)
            )
        """)

        # 12. Leave requests table (Workflow)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS leave_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                emp_id INTEGER NOT NULL,
                leave_type TEXT NOT NULL,
                start_date DATE NOT NULL,
                end_date DATE NOT NULL,
                days REAL NOT NULL,
                reason TEXT,
                status TEXT DEFAULT 'Pending' CHECK(status IN ('Pending', 'Manager Approved', 'HR Approved', 'Rejected', 'Cancelled')),
                manager_approved_by INTEGER,
                manager_approval_date TIMESTAMP,
                manager_comments TEXT,
                hr_approved_by INTEGER,
                hr_approval_date TIMESTAMP,
                hr_comments TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (emp_id) REFERENCES employees(id),
                FOREIGN KEY (manager_approved_by) REFERENCES employees(id),
                FOREIGN KEY (hr_approved_by) REFERENCES employees(id)
            )
        """)

        # 13. Leave balance table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS leave_balance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                emp_id INTEGER NOT NULL,
                leave_type TEXT NOT NULL,
                total_days REAL NOT NULL,
                used_days REAL DEFAULT 0,
                remaining_days REAL NOT NULL,
                year INTEGER NOT NULL,
                FOREIGN KEY (emp_id) REFERENCES employees(id),
                UNIQUE(emp_id, leave_type, year)
            )
        """)

        # 14. Certificates table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS certificates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                emp_id INTEGER NOT NULL,
                certificate_name TEXT NOT NULL,
                issuing_org TEXT,
                issue_date DATE,
                expiry_date DATE,
                file_path TEXT,
                status TEXT DEFAULT 'Pending' CHECK(status IN ('Pending', 'Verified', 'Rejected')),
                verified_by INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (emp_id) REFERENCES employees(id),
                FOREIGN KEY (verified_by) REFERENCES employees(id)
            )
        """)

        # 15. Notifications table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                recipient_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                message TEXT NOT NULL,
                type TEXT DEFAULT 'info',
                is_read INTEGER DEFAULT 0,
                action_url TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (recipient_id) REFERENCES employees(id)
            )
        """)

        # 16. Expenses table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                emp_id INTEGER NOT NULL,
                expense_type TEXT NOT NULL,
                amount REAL NOT NULL,
                currency TEXT DEFAULT 'USD',
                expense_date DATE NOT NULL,
                description TEXT,
                receipt_path TEXT,
                status TEXT DEFAULT 'Pending' CHECK(status IN ('Pending', 'Manager Approved', 'Finance Approved', 'Paid', 'Rejected')),
                manager_approved_by INTEGER,
                manager_approval_date TIMESTAMP,
                finance_approved_by INTEGER,
                finance_approval_date TIMESTAMP,
                paid_date DATE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (emp_id) REFERENCES employees(id),
                FOREIGN KEY (manager_approved_by) REFERENCES employees(id),
                FOREIGN KEY (finance_approved_by) REFERENCES employees(id)
            )
        """)

        # 17. Payslips table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS payslips (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                emp_id INTEGER NOT NULL,
                period TEXT NOT NULL,
                base_salary REAL NOT NULL,
                allowances REAL DEFAULT 0,
                bonus REAL DEFAULT 0,
                overtime REAL DEFAULT 0,
                deductions REAL DEFAULT 0,
                tax REAL DEFAULT 0,
                net_pay REAL NOT NULL,
                payment_date DATE,
                generated_by INTEGER,
                generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (emp_id) REFERENCES employees(id),
                FOREIGN KEY (generated_by) REFERENCES employees(id)
            )
        """)

        # 18. Training catalog table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS training_catalog (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                course_name TEXT NOT NULL,
                provider TEXT,
                description TEXT,
                duration TEXT,
                cost REAL DEFAULT 0,
                max_participants INTEGER,
                status TEXT DEFAULT 'Active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 19. Training enrollments table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS training_enrollments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                course_id INTEGER NOT NULL,
                emp_id INTEGER NOT NULL,
                enrollment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'Pending' CHECK(status IN ('Pending', 'Manager Approved', 'HR Approved', 'Enrolled', 'Completed', 'Rejected')),
                completion_date DATE,
                certificate_path TEXT,
                manager_approved_by INTEGER,
                hr_approved_by INTEGER,
                FOREIGN KEY (course_id) REFERENCES training_catalog(id),
                FOREIGN KEY (emp_id) REFERENCES employees(id),
                FOREIGN KEY (manager_approved_by) REFERENCES employees(id),
                FOREIGN KEY (hr_approved_by) REFERENCES employees(id)
            )
        """)

        # 20. Documents table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                emp_id INTEGER NOT NULL,
                document_type TEXT NOT NULL,
                document_name TEXT NOT NULL,
                file_path TEXT,
                issue_date DATE,
                expiry_date DATE,
                status TEXT DEFAULT 'Pending',
                approved_by INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (emp_id) REFERENCES employees(id),
                FOREIGN KEY (approved_by) REFERENCES employees(id)
            )
        """)

        # 21. Exit process table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS exit_process (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                emp_id INTEGER NOT NULL,
                resignation_date DATE NOT NULL,
                last_working_day DATE,
                reason TEXT,
                exit_interview_status TEXT DEFAULT 'Pending',
                exit_interview_notes TEXT,
                clearance_status TEXT DEFAULT 'Pending',
                it_clearance INTEGER DEFAULT 0,
                finance_clearance INTEGER DEFAULT 0,
                hr_clearance INTEGER DEFAULT 0,
                final_settlement REAL DEFAULT 0,
                status TEXT DEFAULT 'Submitted',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (emp_id) REFERENCES employees(id)
            )
        """)

        # 22. Timesheets table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS timesheets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                emp_id INTEGER NOT NULL,
                work_date DATE NOT NULL,
                hours_worked REAL NOT NULL,
                overtime_hours REAL DEFAULT 0,
                project_name TEXT,
                description TEXT,
                status TEXT DEFAULT 'Pending' CHECK(status IN ('Pending', 'Approved', 'Rejected')),
                approved_by INTEGER,
                approval_date TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (emp_id) REFERENCES employees(id),
                FOREIGN KEY (approved_by) REFERENCES employees(id)
            )
        """)

        # 23. Assets table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS assets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                asset_type TEXT NOT NULL,
                asset_name TEXT NOT NULL,
                asset_tag TEXT UNIQUE,
                assigned_to INTEGER,
                assigned_date DATE,
                return_date DATE,
                condition TEXT DEFAULT 'Good',
                value REAL,
                purchase_date DATE,
                warranty_expiry DATE,
                status TEXT DEFAULT 'Available',
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (assigned_to) REFERENCES employees(id)
            )
        """)

        # 24. PIP records table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pip_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                emp_id INTEGER NOT NULL,
                start_date DATE NOT NULL,
                end_date DATE NOT NULL,
                reason TEXT NOT NULL,
                goals TEXT,
                progress TEXT,
                status TEXT DEFAULT 'Active' CHECK(status IN ('Active', 'Completed', 'Failed', 'Cancelled')),
                created_by INTEGER,
                review_meetings TEXT,
                final_outcome TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (emp_id) REFERENCES employees(id),
                FOREIGN KEY (created_by) REFERENCES employees(id)
            )
        """)

        # 25. Onboarding tasks table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS onboarding_tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                emp_id INTEGER NOT NULL,
                task_name TEXT NOT NULL,
                description TEXT,
                assigned_to INTEGER,
                due_date DATE,
                status TEXT DEFAULT 'Pending' CHECK(status IN ('Pending', 'In Progress', 'Completed')),
                completed_date TIMESTAMP,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (emp_id) REFERENCES employees(id),
                FOREIGN KEY (assigned_to) REFERENCES employees(id)
            )
        """)

        # 26. Goals table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS goals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                emp_id INTEGER NOT NULL,
                goal_type TEXT DEFAULT 'Individual',
                goal_title TEXT NOT NULL,
                description TEXT,
                target_date DATE,
                progress INTEGER DEFAULT 0,
                status TEXT DEFAULT 'Active',
                created_by INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (emp_id) REFERENCES employees(id),
                FOREIGN KEY (created_by) REFERENCES employees(id)
            )
        """)

        # 27. Announcements table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS announcements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                category TEXT,
                priority TEXT DEFAULT 'Normal',
                target_audience TEXT DEFAULT 'All',
                posted_by INTEGER NOT NULL,
                posted_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expiry_date DATE,
                is_active INTEGER DEFAULT 1,
                FOREIGN KEY (posted_by) REFERENCES employees(id)
            )
        """)

        # 28. Shifts table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS shifts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                emp_id INTEGER NOT NULL,
                shift_date DATE NOT NULL,
                shift_start TIME NOT NULL,
                shift_end TIME NOT NULL,
                shift_type TEXT,
                status TEXT DEFAULT 'Scheduled',
                swap_requested_with INTEGER,
                approved_by INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (emp_id) REFERENCES employees(id),
                FOREIGN KEY (swap_requested_with) REFERENCES employees(id),
                FOREIGN KEY (approved_by) REFERENCES employees(id)
            )
        """)

        # 29. Surveys table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS surveys (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                survey_name TEXT NOT NULL,
                description TEXT,
                questions TEXT NOT NULL,
                target_audience TEXT DEFAULT 'All',
                created_by INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                closing_date DATE,
                is_active INTEGER DEFAULT 1,
                FOREIGN KEY (created_by) REFERENCES employees(id)
            )
        """)

        # 30. Survey responses table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS survey_responses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                survey_id INTEGER NOT NULL,
                emp_id INTEGER NOT NULL,
                responses TEXT NOT NULL,
                submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (survey_id) REFERENCES surveys(id),
                FOREIGN KEY (emp_id) REFERENCES employees(id)
            )
        """)

        # 31. Compliance table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS compliance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                emp_id INTEGER NOT NULL,
                requirement_name TEXT NOT NULL,
                requirement_type TEXT,
                due_date DATE,
                completion_date DATE,
                status TEXT DEFAULT 'Pending',
                certificate_path TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (emp_id) REFERENCES employees(id)
            )
        """)

        # 32. Audit logs table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                action TEXT NOT NULL,
                table_name TEXT,
                record_id INTEGER,
                old_values TEXT,
                new_values TEXT,
                ip_address TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)

        conn.commit()
        print("✅ Database initialized successfully with 32 tables!")

def seed_initial_data():
    """Seed database with initial demo data"""
    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Check if data already exists
        cursor.execute("SELECT COUNT(*) FROM users")
        if cursor.fetchone()[0] > 0:
            print("⚠️  Database already contains data. Skipping seed.")
            return

        # Create HR Admin
        cursor.execute("""
            INSERT INTO employees (employee_id, first_name, last_name, email, phone,
                                 department, position, grade, status, join_date, team_tag)
            VALUES ('EXL-001', 'Admin', 'HR', 'admin@exalio.com', '+1234567890',
                   'Human Resources', 'HR Director', 'A+', 'Active', '2020-01-01', NULL)
        """)
        admin_emp_id = cursor.lastrowid

        cursor.execute("""
            INSERT INTO users (username, password, role, employee_id, is_active)
            VALUES ('admin@exalio.com', ?, 'hr_admin', ?, 1)
        """, (hash_password('admin123'), admin_emp_id))

        # Create Manager
        cursor.execute("""
            INSERT INTO employees (employee_id, first_name, last_name, email, phone,
                                 department, position, grade, status, join_date, team_tag)
            VALUES ('EXL-002', 'John', 'Manager', 'john.manager@exalio.com', '+1234567891',
                   'Engineering', 'Engineering Manager', 'A', 'Active', '2020-06-01', 'app')
        """)
        manager_emp_id = cursor.lastrowid

        cursor.execute("""
            INSERT INTO users (username, password, role, employee_id, is_active)
            VALUES ('john.manager@exalio.com', ?, 'manager', ?, 1)
        """, (hash_password('manager123'), manager_emp_id))

        # Create Employee
        cursor.execute("""
            INSERT INTO employees (employee_id, first_name, last_name, email, phone,
                                 department, position, grade, status, join_date, manager_id, team_tag)
            VALUES ('EXL-003', 'Sarah', 'Developer', 'sarah.dev@exalio.com', '+1234567892',
                   'Engineering', 'Senior Developer', 'B+', 'Active', '2021-03-15', ?, 'app')
        """, (manager_emp_id,))
        employee_emp_id = cursor.lastrowid

        cursor.execute("""
            INSERT INTO users (username, password, role, employee_id, is_active)
            VALUES ('sarah.dev@exalio.com', ?, 'employee', ?, 1)
        """, (hash_password('emp123'), employee_emp_id))

        # Add more sample employees
        sample_employees = [
            ('EXL-004', 'Mike', 'Chen', 'mike.chen@exalio.com', 'Engineering', 'Developer', 'B', manager_emp_id, 'app'),
            ('EXL-005', 'Emily', 'Brown', 'emily.brown@exalio.com', 'Marketing', 'Marketing Manager', 'A', admin_emp_id, None),
            ('EXL-006', 'David', 'Wilson', 'david.wilson@exalio.com', 'Finance', 'Financial Analyst', 'B+', admin_emp_id, None),
            ('EXL-007', 'Lisa', 'Anderson', 'lisa.anderson@exalio.com', 'Engineering', 'Data Engineer', 'B+', manager_emp_id, 'data'),
            ('EXL-008', 'Tom', 'Martinez', 'tom.martinez@exalio.com', 'Engineering', 'AI Engineer', 'A', manager_emp_id, 'ai'),
        ]

        for emp in sample_employees:
            cursor.execute("""
                INSERT INTO employees (employee_id, first_name, last_name, email,
                                     department, position, grade, status, join_date, manager_id, team_tag)
                VALUES (?, ?, ?, ?, ?, ?, ?, 'Active', '2021-01-01', ?, ?)
            """, emp)
            emp_id = cursor.lastrowid

            # Create user accounts for each employee
            cursor.execute("""
                INSERT INTO users (username, password, role, employee_id, is_active)
                VALUES (?, ?, 'employee', ?, 1)
            """, (emp[3], hash_password('emp123'), emp_id))

        # Add leave balances for all employees
        cursor.execute("SELECT id FROM employees")
        all_employees = cursor.fetchall()

        for emp in all_employees:
            leave_types = [
                ('Annual Leave', 20.0),
                ('Sick Leave', 10.0),
                ('Personal Leave', 5.0)
            ]
            for leave_type, total_days in leave_types:
                cursor.execute("""
                    INSERT INTO leave_balance (emp_id, leave_type, total_days, used_days, remaining_days, year)
                    VALUES (?, ?, ?, 0, ?, 2024)
                """, (emp[0], leave_type, total_days, total_days))

        # Add sample financial records
        cursor.execute("""
            INSERT INTO financial_records (emp_id, base_salary, allowances, bonus, deductions, net_pay, period)
            VALUES (?, 8000, 1000, 500, 200, 9300, '2024-01')
        """, (employee_emp_id,))

        # Add sample notifications
        cursor.execute("""
            INSERT INTO notifications (recipient_id, title, message, type)
            VALUES (?, 'Welcome to Exalio HR System', 'Your account has been created successfully!', 'success')
        """, (employee_emp_id,))

        conn.commit()
        print("✅ Demo data seeded successfully!")
        print("\n📋 Login Credentials:")
        print("━" * 50)
        print("HR Admin:  admin@exalio.com / admin123")
        print("Manager:   john.manager@exalio.com / manager123")
        print("Employee:  sarah.dev@exalio.com / emp123")
        print("━" * 50)

if __name__ == "__main__":
    print("🚀 Initializing Exalio HR System Database...")
    init_database()
    seed_initial_data()
    print("\n✅ Database setup complete!")
