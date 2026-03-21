"""
Initialize PostgreSQL database on Streamlit Cloud
This runs automatically on first deployment
"""

import streamlit as st
from database import get_db_connection
import sqlite3
import os

def init_postgres_from_sqlite():
    """Initialize PostgreSQL and migrate data from SQLite backup"""

    st.info("🔄 Initializing PostgreSQL database...")

    try:
        with get_db_connection() as pg_conn:
            pg_cursor = pg_conn.cursor()

            # Check if tables already exist
            pg_cursor.execute("""
                SELECT COUNT(*) as count FROM information_schema.tables
                WHERE table_schema = 'public' AND table_name = 'employees'
            """)
            result = pg_cursor.fetchone()

            if result and result['count'] > 0:
                st.success("✅ Database already initialized!")
                return True

            st.info("Creating database tables...")

            # Create all tables (PostgreSQL syntax)
            create_tables_sql = """
            -- 1. Employees table
            CREATE TABLE IF NOT EXISTS employees (
                id SERIAL PRIMARY KEY,
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
                status TEXT DEFAULT 'Active',
                join_date DATE NOT NULL,
                location TEXT,
                bio TEXT,
                photo TEXT,
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            );

            -- 2. Users table
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                role TEXT NOT NULL,
                employee_id INTEGER,
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT NOW(),
                last_login TIMESTAMP
            );

            -- 3. Grades table
            CREATE TABLE IF NOT EXISTS grades (
                id SERIAL PRIMARY KEY,
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
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            );

            -- 4. Leave requests
            CREATE TABLE IF NOT EXISTS leave_requests (
                id SERIAL PRIMARY KEY,
                emp_id INTEGER NOT NULL,
                leave_type TEXT NOT NULL,
                start_date DATE NOT NULL,
                end_date DATE NOT NULL,
                days INTEGER NOT NULL,
                reason TEXT,
                status TEXT DEFAULT 'Pending',
                manager_id INTEGER,
                manager_comments TEXT,
                hr_comments TEXT,
                created_at TIMESTAMP DEFAULT NOW(),
                approved_date TIMESTAMP
            );

            -- 5. Leave balance
            CREATE TABLE IF NOT EXISTS leave_balance (
                id SERIAL PRIMARY KEY,
                emp_id INTEGER NOT NULL,
                leave_type TEXT NOT NULL,
                total_days INTEGER DEFAULT 0,
                used_days INTEGER DEFAULT 0,
                remaining_days INTEGER DEFAULT 0,
                year INTEGER NOT NULL
            );

            -- 6. Notifications
            CREATE TABLE IF NOT EXISTS notifications (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                message TEXT NOT NULL,
                type TEXT DEFAULT 'info',
                related_id INTEGER,
                read_status INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT NOW()
            );

            -- 7. Audit logs
            CREATE TABLE IF NOT EXISTS audit_logs (
                id SERIAL PRIMARY KEY,
                user_id INTEGER,
                action TEXT NOT NULL,
                entity_type TEXT,
                entity_id INTEGER,
                details TEXT,
                timestamp TIMESTAMP DEFAULT NOW()
            );

            -- Continue with remaining tables (simplified for brevity)
            CREATE TABLE IF NOT EXISTS appraisals (
                id SERIAL PRIMARY KEY,
                emp_id INTEGER NOT NULL,
                period TEXT NOT NULL,
                type TEXT DEFAULT 'Annual',
                status TEXT DEFAULT 'Draft',
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
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            );

            CREATE TABLE IF NOT EXISTS contracts (id SERIAL PRIMARY KEY, emp_id INTEGER, contract_type TEXT, start_date DATE, end_date DATE, salary REAL, terms TEXT, status TEXT DEFAULT 'Active', created_at TIMESTAMP DEFAULT NOW());
            CREATE TABLE IF NOT EXISTS insurance (id SERIAL PRIMARY KEY, emp_id INTEGER, insurance_type TEXT, provider TEXT, policy_number TEXT, coverage_amount REAL, start_date DATE, end_date DATE, premium REAL, status TEXT DEFAULT 'Active', created_at TIMESTAMP DEFAULT NOW());
            CREATE TABLE IF NOT EXISTS bonuses (id SERIAL PRIMARY KEY, emp_id INTEGER, bonus_type TEXT, amount REAL, calculation_method TEXT, period TEXT, status TEXT DEFAULT 'Pending', recommended_by INTEGER, approved_by INTEGER, created_at TIMESTAMP DEFAULT NOW(), paid_date DATE);
            CREATE TABLE IF NOT EXISTS expenses (id SERIAL PRIMARY KEY, emp_id INTEGER, expense_type TEXT, amount REAL, currency TEXT DEFAULT 'USD', expense_date DATE, description TEXT, receipt TEXT, status TEXT DEFAULT 'Pending', approved_by INTEGER, created_at TIMESTAMP DEFAULT NOW());
            CREATE TABLE IF NOT EXISTS certificates (id SERIAL PRIMARY KEY, emp_id INTEGER, certificate_name TEXT, issuing_organization TEXT, issue_date DATE, expiry_date DATE, certificate_file TEXT, status TEXT DEFAULT 'Active', created_at TIMESTAMP DEFAULT NOW());
            CREATE TABLE IF NOT EXISTS financial_records (id SERIAL PRIMARY KEY, emp_id INTEGER, base_salary REAL, allowances REAL DEFAULT 0, bonus REAL DEFAULT 0, deductions REAL DEFAULT 0, net_pay REAL, currency TEXT DEFAULT 'USD', payment_date DATE, period TEXT, created_at TIMESTAMP DEFAULT NOW());
            CREATE TABLE IF NOT EXISTS payslips (id SERIAL PRIMARY KEY, emp_id INTEGER, period TEXT, base_salary REAL, allowances REAL, deductions REAL, net_pay REAL, generated_date DATE, file_path TEXT);
            CREATE TABLE IF NOT EXISTS timesheets (id SERIAL PRIMARY KEY, emp_id INTEGER, work_date DATE, hours_worked REAL, project TEXT, task_description TEXT, status TEXT DEFAULT 'Pending', approved_by INTEGER, created_at TIMESTAMP DEFAULT NOW());
            CREATE TABLE IF NOT EXISTS training_catalog (id SERIAL PRIMARY KEY, course_name TEXT, description TEXT, duration TEXT, instructor TEXT, capacity INTEGER, start_date DATE, end_date DATE, status TEXT DEFAULT 'Open', created_at TIMESTAMP DEFAULT NOW());
            CREATE TABLE IF NOT EXISTS training_enrollments (id SERIAL PRIMARY KEY, emp_id INTEGER, course_id INTEGER, enrollment_date DATE, completion_date DATE, status TEXT DEFAULT 'Enrolled', score REAL, feedback TEXT);
            CREATE TABLE IF NOT EXISTS jobs (id SERIAL PRIMARY KEY, title TEXT, department TEXT, job_type TEXT, location TEXT, description TEXT, requirements TEXT, salary_range TEXT, status TEXT DEFAULT 'Open', posted_by INTEGER, posted_date DATE, closing_date DATE, created_at TIMESTAMP DEFAULT NOW());
            CREATE TABLE IF NOT EXISTS job_applications (id SERIAL PRIMARY KEY, job_id INTEGER, candidate_name TEXT, candidate_email TEXT, candidate_phone TEXT, resume TEXT, cover_letter TEXT, status TEXT DEFAULT 'Applied', applied_date TIMESTAMP DEFAULT NOW(), reviewed_by INTEGER, review_date TIMESTAMP, notes TEXT);
            CREATE TABLE IF NOT EXISTS assets (id SERIAL PRIMARY KEY, asset_name TEXT, asset_type TEXT, serial_number TEXT, purchase_date DATE, purchase_cost REAL, assigned_to INTEGER, condition TEXT DEFAULT 'Good', status TEXT DEFAULT 'Available', created_at TIMESTAMP DEFAULT NOW());
            CREATE TABLE IF NOT EXISTS goals (id SERIAL PRIMARY KEY, emp_id INTEGER, goal_title TEXT, description TEXT, target_date DATE, status TEXT DEFAULT 'In Progress', progress INTEGER DEFAULT 0, created_by INTEGER, created_at TIMESTAMP DEFAULT NOW());
            CREATE TABLE IF NOT EXISTS career_plans (id SERIAL PRIMARY KEY, emp_id INTEGER, current_level TEXT, target_level TEXT, timeline TEXT, skills_required TEXT, milestones TEXT, status TEXT DEFAULT 'Active', created_by INTEGER, created_at TIMESTAMP DEFAULT NOW());
            CREATE TABLE IF NOT EXISTS exit_process (id SERIAL PRIMARY KEY, emp_id INTEGER, resignation_date DATE, last_working_day DATE, reason_for_leaving TEXT, exit_interview_notes TEXT, clearance_status TEXT DEFAULT 'Pending', created_at TIMESTAMP DEFAULT NOW());
            CREATE TABLE IF NOT EXISTS documents (id SERIAL PRIMARY KEY, title TEXT, category TEXT, document_type TEXT, file_path TEXT, uploaded_by INTEGER, access_level TEXT DEFAULT 'Public', status TEXT DEFAULT 'Active', created_at TIMESTAMP DEFAULT NOW());
            CREATE TABLE IF NOT EXISTS announcements (id SERIAL PRIMARY KEY, title TEXT, content TEXT, priority TEXT DEFAULT 'Normal', target_audience TEXT DEFAULT 'All', published_by INTEGER, published_date DATE, expiry_date DATE, status TEXT DEFAULT 'Active', created_at TIMESTAMP DEFAULT NOW());
            CREATE TABLE IF NOT EXISTS onboarding_tasks (id SERIAL PRIMARY KEY, emp_id INTEGER, task_name TEXT, description TEXT, assigned_to INTEGER, due_date DATE, status TEXT DEFAULT 'Pending', completed_date DATE, created_at TIMESTAMP DEFAULT NOW());
            CREATE TABLE IF NOT EXISTS shifts (id SERIAL PRIMARY KEY, shift_name TEXT, start_time TEXT, end_time TEXT, days TEXT, emp_id INTEGER, shift_date DATE, location TEXT, notes TEXT, status TEXT DEFAULT 'Assigned', created_at TIMESTAMP DEFAULT NOW());
            CREATE TABLE IF NOT EXISTS surveys (id SERIAL PRIMARY KEY, title TEXT, description TEXT, questions TEXT, target_audience TEXT DEFAULT 'All', created_by INTEGER, start_date DATE, end_date DATE, status TEXT DEFAULT 'Draft', created_at TIMESTAMP DEFAULT NOW());
            CREATE TABLE IF NOT EXISTS survey_responses (id SERIAL PRIMARY KEY, survey_id INTEGER, emp_id INTEGER, responses TEXT, submitted_at TIMESTAMP DEFAULT NOW());
            CREATE TABLE IF NOT EXISTS compliance (id SERIAL PRIMARY KEY, requirement_name TEXT, category TEXT, description TEXT, review_frequency TEXT, next_review_date DATE, responsible_person INTEGER, status TEXT DEFAULT 'Not Started', created_at TIMESTAMP DEFAULT NOW());
            CREATE TABLE IF NOT EXISTS pip_records (id SERIAL PRIMARY KEY, emp_id INTEGER, manager_id INTEGER, reason TEXT, goals TEXT, expected_outcomes TEXT, start_date DATE, end_date DATE, status TEXT DEFAULT 'Active', created_at TIMESTAMP DEFAULT NOW());
            """

            # Execute schema creation
            pg_cursor.execute(create_tables_sql)

            st.success("✅ Tables created successfully!")

            # Insert complete data from SQLite database (exported 2026-03-18)
            st.info("Loading complete data from SQLite export...")

            sample_data_sql = """
            -- Employees (9 rows - including TEST-001 employee)
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

            -- Users (9 rows - passwords: admin123 for admin, manager123 for manager, emp123 for employees, testpass for test user)
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

            -- Leave balance (27 rows - 3 leave types per employee)
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

            -- Grades (1 row - Sarah's Q1 2024 performance review)
            INSERT INTO grades (id, emp_id, period, overall_grade, score, performance, technical, teamwork, leadership, comments, evaluated_by, created_at, updated_at) VALUES
            (1, 3, 'Q1 2024 Test', 'A', 85, 4, 5, 4, 3, 'Excellent performance', 1, '2026-03-17 22:17:15', '2026-03-17 22:17:15')
            ON CONFLICT DO NOTHING;

            -- Financial records (1 row - Sarah's January 2024 payroll)
            INSERT INTO financial_records (id, emp_id, base_salary, allowances, bonus, deductions, net_pay, currency, payment_date, period, created_at) VALUES
            (1, 3, 8000.0, 1000.0, 500.0, 200.0, 9300.0, 'USD', NULL, '2024-01', '2026-03-17 20:21:52')
            ON CONFLICT DO NOTHING;

            -- Leave requests (1 row - Sarah's approved leave for March 2026)
            INSERT INTO leave_requests (id, emp_id, leave_type, start_date, end_date, days, reason, status, manager_approved_by, manager_approval_date, manager_comments, hr_approved_by, hr_approval_date, hr_comments, created_at) VALUES
            (1, 3, 'Annual Leave', '2026-03-25', '2026-03-29', 5.0, 'Testing leave workflow', 'HR Approved', 2, '2026-03-18 02:17:15', NULL, 1, '2026-03-18 02:17:15', NULL, '2026-03-17 22:17:15')
            ON CONFLICT DO NOTHING;

            -- Notifications (2 rows)
            INSERT INTO notifications (id, recipient_id, title, message, type, is_read, action_url, created_at) VALUES
            (1, 3, 'Welcome to Exalio HR System', 'Your account has been created successfully!', 'success', 0, NULL, '2026-03-17 20:21:52'),
            (2, 3, 'Test Notification', 'This is a test notification', 'info', 1, NULL, '2026-03-17 22:17:15')
            ON CONFLICT DO NOTHING;
            """

            pg_cursor.execute(sample_data_sql)

            st.success("✅ Sample data loaded successfully!")
            st.success("🎉 PostgreSQL database fully initialized!")

            return True

    except Exception as e:
        st.error(f"❌ Initialization error: {str(e)}")
        st.exception(e)
        return False

if __name__ == "__main__":
    st.set_page_config(page_title="Database Initialization")
    st.title("PostgreSQL Database Initialization")

    if st.button("Initialize Database"):
        init_postgres_from_sqlite()
