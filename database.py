"""
Exalio HR System - Database Module
SQLite Database Schema with all 32 tables for complete HR management
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import streamlit as st
import hashlib
import os
import shutil
from datetime import datetime
from contextlib import contextmanager
import socket





def resolve_ipv4_only(hostname):
    '''Resolve hostname to IPv4 address only, ignoring IPv6'''
    try:
        # Get all address info for the hostname
        addr_info = socket.getaddrinfo(hostname, None, socket.AF_INET)  # AF_INET = IPv4 only
        if addr_info:
            # Return the first IPv4 address
            ipv4_address = addr_info[0][4][0]
            return ipv4_address
    except Exception as e:
        # If resolution fails, return the hostname as-is
        return hostname
    return hostname

def get_connection_string():
    '''Get PostgreSQL connection string from Streamlit secrets'''
    try:
        return st.secrets["connections"]["postgresql"]["url"]
    except:
        # Fallback: Neon PostgreSQL (IPv4-only, serverless)
        return "postgresql://neondb_owner:npg_R2UAT4WQkCMi@ep-weathered-pond-ammen3lb-pooler.c-5.us-east-1.aws.neon.tech/neondb?sslmode=require"

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
            _shared_connection.row_factory = RealDictCursor
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
            _shared_connection.row_factory = RealDictCursor
            return _shared_connection
        except:
            pass

        # Final fallback: in-memory with data loaded
        _shared_connection = sqlite3.connect(":memory:", check_same_thread=False)
        _shared_connection.row_factory = RealDictCursor

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
    '''Context manager for PostgreSQL database connections'''
    conn = None
    try:
        # Get connection string - use it directly for Neon
        # Neon is IPv4-only by design, no need to resolve
        conn_str = get_connection_string()

        # Connect directly with the connection string
        # Neon hostnames are IPv4-only and include endpoint routing info
        conn = psycopg2.connect(
            conn_str,
            cursor_factory=RealDictCursor,
            connect_timeout=10
        )

        yield conn
        conn.commit()
    except Exception as e:
        if conn:
            conn.rollback()
        raise

def hash_password(password):
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def apply_migrations(cursor):
    """Apply database schema migrations"""
    try:
        # For PostgreSQL, we need to check information_schema instead of PRAGMA
        # Migration 1: Add overtime approval fields to timesheets
        cursor.execute("""
            SELECT column_name FROM information_schema.columns
            WHERE table_name='timesheets'
        """)
        columns = [col['column_name'] for col in cursor.fetchall()]

        if 'overtime_approved' not in columns:
            cursor.execute("ALTER TABLE timesheets ADD COLUMN overtime_approved TEXT DEFAULT 'No'")
            print("✅ Added overtime_approved column to timesheets")

        if 'overtime_justification' not in columns:
            cursor.execute("ALTER TABLE timesheets ADD COLUMN overtime_justification TEXT")
            print("✅ Added overtime_justification column to timesheets")

        # Migration 2: Add missing timesheet fields if they don't exist
        if 'start_time' not in columns:
            cursor.execute("ALTER TABLE timesheets ADD COLUMN start_time TEXT")
            print("✅ Added start_time column to timesheets")

        if 'end_time' not in columns:
            cursor.execute("ALTER TABLE timesheets ADD COLUMN end_time TEXT")
            print("✅ Added end_time column to timesheets")

        if 'break_minutes' not in columns:
            cursor.execute("ALTER TABLE timesheets ADD COLUMN break_minutes INTEGER DEFAULT 0")
            print("✅ Added break_minutes column to timesheets")

        if 'regular_hours' not in columns:
            cursor.execute("ALTER TABLE timesheets ADD COLUMN regular_hours REAL DEFAULT 0")
            print("✅ Added regular_hours column to timesheets")

        if 'notes' not in columns:
            cursor.execute("ALTER TABLE timesheets ADD COLUMN notes TEXT")
            print("✅ Added notes column to timesheets")

        # Migration 3: Add document approval fields
        cursor.execute("""
            SELECT column_name FROM information_schema.columns
            WHERE table_name='documents'
        """)
        doc_columns = [col['column_name'] for col in cursor.fetchall()]

        if 'version' not in doc_columns:
            cursor.execute("ALTER TABLE documents ADD COLUMN version TEXT DEFAULT '1.0'")
            print("✅ Added version column to documents")

        if 'approval_status' not in doc_columns:
            cursor.execute("ALTER TABLE documents ADD COLUMN approval_status TEXT DEFAULT 'Pending'")
            print("✅ Added approval_status column to documents")

        if 'approved_by' not in doc_columns:
            cursor.execute("ALTER TABLE documents ADD COLUMN approved_by INTEGER")
            print("✅ Added approved_by column to documents")

        if 'approval_date' not in doc_columns:
            cursor.execute("ALTER TABLE documents ADD COLUMN approval_date TIMESTAMP")
            print("✅ Added approval_date column to documents")

        if 'review_comments' not in doc_columns:
            cursor.execute("ALTER TABLE documents ADD COLUMN review_comments TEXT")
            print("✅ Added review_comments column to documents")

        if 'effective_date' not in doc_columns:
            cursor.execute("ALTER TABLE documents ADD COLUMN effective_date DATE")
            print("✅ Added effective_date column to documents")

        if 'expiry_date' not in doc_columns:
            cursor.execute("ALTER TABLE documents ADD COLUMN expiry_date DATE")
            print("✅ Added expiry_date column to documents")

        if 'requires_manager_approval' not in doc_columns:
            cursor.execute("ALTER TABLE documents ADD COLUMN requires_manager_approval INTEGER DEFAULT 0")
            print("✅ Added requires_manager_approval column to documents")

        if 'auto_publish_on_approval' not in doc_columns:
            cursor.execute("ALTER TABLE documents ADD COLUMN auto_publish_on_approval INTEGER DEFAULT 1")
            print("✅ Added auto_publish_on_approval column to documents")

        if 'approval_notes' not in doc_columns:
            cursor.execute("ALTER TABLE documents ADD COLUMN approval_notes TEXT")
            print("✅ Added approval_notes column to documents")

        if 'download_count' not in doc_columns:
            cursor.execute("ALTER TABLE documents ADD COLUMN download_count INTEGER DEFAULT 0")
            print("✅ Added download_count column to documents")

        if 'archived_date' not in doc_columns:
            cursor.execute("ALTER TABLE documents ADD COLUMN archived_date TIMESTAMP")
            print("✅ Added archived_date column to documents")

        if 'content' not in doc_columns:
            cursor.execute("ALTER TABLE documents ADD COLUMN content TEXT")
            print("✅ Added content column to documents")

        if 'description' not in doc_columns:
            cursor.execute("ALTER TABLE documents ADD COLUMN description TEXT")
            print("✅ Added description column to documents")

    except Exception as e:
        print(f"⚠️ Migration warning: {str(e)}")

def init_database():
    """Initialize all database tables"""
    with get_db_connection() as conn:
        cursor = conn.cursor()

        # 1. Users table (Authentication)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('employee', 'manager', 'hr_admin')),
                employee_id INTEGER,
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT NOW(),
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
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW(),
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
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW(),
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
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW(),
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
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW(),
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
                created_at TIMESTAMP DEFAULT NOW(),
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
                applied_date TIMESTAMP DEFAULT NOW(),
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
                created_at TIMESTAMP DEFAULT NOW(),
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
                created_at TIMESTAMP DEFAULT NOW(),
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
                created_at TIMESTAMP DEFAULT NOW(),
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
                created_at TIMESTAMP DEFAULT NOW(),
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
                created_at TIMESTAMP DEFAULT NOW(),
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
                created_at TIMESTAMP DEFAULT NOW(),
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
                created_at TIMESTAMP DEFAULT NOW(),
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
                created_at TIMESTAMP DEFAULT NOW(),
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
                generated_at TIMESTAMP DEFAULT NOW(),
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
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)

        # 19. Training enrollments table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS training_enrollments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                course_id INTEGER NOT NULL,
                emp_id INTEGER NOT NULL,
                enrollment_date TIMESTAMP DEFAULT NOW(),
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
                created_at TIMESTAMP DEFAULT NOW(),
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
                created_at TIMESTAMP DEFAULT NOW(),
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
                created_at TIMESTAMP DEFAULT NOW(),
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
                created_at TIMESTAMP DEFAULT NOW(),
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
                created_at TIMESTAMP DEFAULT NOW(),
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
                created_at TIMESTAMP DEFAULT NOW(),
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
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW(),
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
                posted_date TIMESTAMP DEFAULT NOW(),
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
                created_at TIMESTAMP DEFAULT NOW(),
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
                created_at TIMESTAMP DEFAULT NOW(),
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
                submitted_at TIMESTAMP DEFAULT NOW(),
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
                created_at TIMESTAMP DEFAULT NOW(),
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
                created_at TIMESTAMP DEFAULT NOW(),
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)

        # 33. Teams table (Organizational teams configuration)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS teams (
                id SERIAL PRIMARY KEY,
                team_name TEXT NOT NULL,
                department TEXT NOT NULL,
                team_lead_id INTEGER,
                description TEXT,
                status TEXT DEFAULT 'Active' CHECK(status IN ('Active', 'Inactive')),
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW(),
                FOREIGN KEY (team_lead_id) REFERENCES employees(id)
            )
        """)

        # 34. Positions table (Job positions configuration)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS positions (
                id SERIAL PRIMARY KEY,
                position_name TEXT NOT NULL,
                team_id INTEGER,
                level TEXT,
                description TEXT,
                status TEXT DEFAULT 'Active' CHECK(status IN ('Active', 'Inactive')),
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW(),
                FOREIGN KEY (team_id) REFERENCES teams(id) ON DELETE SET NULL
            )
        """)

        # 35. Skills table (Skills library)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS skills (
                id SERIAL PRIMARY KEY,
                skill_name TEXT NOT NULL UNIQUE,
                category TEXT,
                description TEXT,
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            )
        """)

        # 36. Team skills table (Skills required per team/position)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS team_skills (
                id SERIAL PRIMARY KEY,
                team_id INTEGER NOT NULL,
                skill_id INTEGER NOT NULL,
                position_id INTEGER,
                required_level TEXT DEFAULT 'Intermediate' CHECK(required_level IN ('Beginner', 'Intermediate', 'Advanced', 'Expert')),
                priority TEXT DEFAULT 'Medium' CHECK(priority IN ('High', 'Medium', 'Low')),
                created_at TIMESTAMP DEFAULT NOW(),
                FOREIGN KEY (team_id) REFERENCES teams(id) ON DELETE CASCADE,
                FOREIGN KEY (skill_id) REFERENCES skills(id) ON DELETE CASCADE,
                FOREIGN KEY (position_id) REFERENCES positions(id) ON DELETE CASCADE,
                UNIQUE(team_id, skill_id, COALESCE(position_id, 0))
            )
        """)

        # 37. Employee skills table (Employee skill assessments)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS employee_skills (
                id SERIAL PRIMARY KEY,
                emp_id INTEGER NOT NULL,
                skill_id INTEGER NOT NULL,
                proficiency_level TEXT DEFAULT 'Beginner' CHECK(proficiency_level IN ('Beginner', 'Intermediate', 'Advanced', 'Expert')),
                years_experience INTEGER DEFAULT 0,
                certified BOOLEAN DEFAULT FALSE,
                last_assessed_date DATE,
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW(),
                FOREIGN KEY (emp_id) REFERENCES employees(id) ON DELETE CASCADE,
                FOREIGN KEY (skill_id) REFERENCES skills(id) ON DELETE CASCADE,
                UNIQUE(emp_id, skill_id)
            )
        """)

        # 38. Contracts table (Contract renewal workflow)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS contracts (
                id SERIAL PRIMARY KEY,
                emp_id INTEGER NOT NULL,
                contract_type TEXT NOT NULL CHECK(contract_type IN ('Permanent', 'Fixed-Term', 'Contract', 'Probation')),
                start_date DATE NOT NULL,
                end_date DATE NOT NULL,
                terms TEXT,
                status TEXT DEFAULT 'Active' CHECK(status IN ('Active', 'Expired', 'Terminated', 'Renewed')),
                renewal_status TEXT CHECK(renewal_status IN ('Not Initiated', 'Pending Approval', 'Approved', 'Rejected')),
                new_end_date DATE,
                renewal_terms TEXT,
                renewal_notes TEXT,
                renewal_requested_by INTEGER,
                renewal_requested_date TIMESTAMP,
                renewed_by INTEGER,
                renewed_date TIMESTAMP,
                termination_date TIMESTAMP,
                terminated_by INTEGER,
                created_by INTEGER,
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW(),
                FOREIGN KEY (emp_id) REFERENCES employees(id) ON DELETE CASCADE,
                FOREIGN KEY (renewal_requested_by) REFERENCES employees(id),
                FOREIGN KEY (renewed_by) REFERENCES employees(id),
                FOREIGN KEY (terminated_by) REFERENCES employees(id),
                FOREIGN KEY (created_by) REFERENCES employees(id)
            )
        """)

        # 39. Certificates table (Certificate expiry tracking)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS certificates (
                id SERIAL PRIMARY KEY,
                emp_id INTEGER NOT NULL,
                certificate_name TEXT NOT NULL,
                certificate_type TEXT NOT NULL,
                certificate_number TEXT,
                issuing_authority TEXT NOT NULL,
                issue_date DATE NOT NULL,
                expiry_date DATE NOT NULL,
                status TEXT DEFAULT 'Active' CHECK(status IN ('Active', 'Expired', 'Renewal Pending', 'Pending Verification')),
                certificate_file_path TEXT,
                notes TEXT,
                renewal_requested_date TIMESTAMP,
                renewal_requested_by INTEGER,
                expired_date TIMESTAMP,
                created_by INTEGER,
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW(),
                FOREIGN KEY (emp_id) REFERENCES employees(id) ON DELETE CASCADE,
                FOREIGN KEY (renewal_requested_by) REFERENCES employees(id),
                FOREIGN KEY (created_by) REFERENCES employees(id)
            )
        """)

        # 40. Enhanced Documents table (Document approval workflow)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS document_history (
                id SERIAL PRIMARY KEY,
                document_id INTEGER NOT NULL,
                emp_id INTEGER NOT NULL,
                action TEXT NOT NULL CHECK(action IN ('download', 'view', 'edit', 'approve', 'reject')),
                download_date TIMESTAMP DEFAULT NOW(),
                notes TEXT,
                FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE,
                FOREIGN KEY (emp_id) REFERENCES employees(id) ON DELETE CASCADE
            )
        """)

        # 41. Asset requests table (Asset procurement workflow)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS asset_requests (
                id SERIAL PRIMARY KEY,
                emp_id INTEGER NOT NULL,
                asset_type TEXT NOT NULL,
                asset_description TEXT NOT NULL,
                justification TEXT NOT NULL,
                estimated_cost REAL NOT NULL,
                urgency TEXT CHECK(urgency IN ('Low', 'Medium', 'High', 'Critical')),
                preferred_vendor TEXT,
                required_by_date DATE,
                additional_notes TEXT,
                status TEXT DEFAULT 'Pending' CHECK(status IN ('Pending', 'Manager Approved', 'Approved - Procurement', 'Rejected', 'Fulfilled')),
                manager_status TEXT,
                manager_id INTEGER,
                manager_approval_date TIMESTAMP,
                manager_comments TEXT,
                hr_status TEXT,
                hr_id INTEGER,
                hr_approval_date TIMESTAMP,
                hr_comments TEXT,
                requested_date TIMESTAMP DEFAULT NOW(),
                FOREIGN KEY (emp_id) REFERENCES employees(id) ON DELETE CASCADE,
                FOREIGN KEY (manager_id) REFERENCES employees(id),
                FOREIGN KEY (hr_id) REFERENCES employees(id)
            )
        """)

        # 42. Budgets table (Department budget management)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS budgets (
                id SERIAL PRIMARY KEY,
                department TEXT NOT NULL,
                fiscal_year INTEGER NOT NULL,
                period_month INTEGER CHECK(period_month BETWEEN 1 AND 12),
                amount REAL NOT NULL,
                category TEXT CHECK(category IN ('Operational', 'Capital', 'Project', 'General')),
                notes TEXT,
                status TEXT DEFAULT 'Active' CHECK(status IN ('Active', 'Inactive', 'Closed')),
                created_by INTEGER,
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW(),
                FOREIGN KEY (created_by) REFERENCES employees(id)
            )
        """)

        # 43. Goals table (Goal and OKR tracking)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS goals (
                id SERIAL PRIMARY KEY,
                emp_id INTEGER NOT NULL,
                goal_type TEXT CHECK(goal_type IN ('Company OKR', 'Department Goal', 'Project Goal', 'Individual KPI', 'Development Goal', 'Performance Goal')),
                goal_title TEXT NOT NULL,
                description TEXT NOT NULL,
                key_results TEXT,
                review_period TEXT,
                target_date DATE NOT NULL,
                weight INTEGER DEFAULT 100,
                measurement_criteria TEXT,
                status TEXT DEFAULT 'Active' CHECK(status IN ('Active', 'Reviewed', 'Cancelled', 'Completed')),
                progress INTEGER DEFAULT 0,
                progress_notes TEXT,
                achievement_rating TEXT,
                review_notes TEXT,
                review_date TIMESTAMP,
                reviewed_by INTEGER,
                created_by INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT NOW(),
                last_updated TIMESTAMP,
                FOREIGN KEY (emp_id) REFERENCES employees(id) ON DELETE CASCADE,
                FOREIGN KEY (created_by) REFERENCES employees(id),
                FOREIGN KEY (reviewed_by) REFERENCES employees(id)
            )
        """)

        # 44. Promotion requests table (Career advancement workflow)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS promotion_requests (
                id SERIAL PRIMARY KEY,
                emp_id INTEGER NOT NULL,
                current_position TEXT NOT NULL,
                current_grade TEXT,
                current_salary REAL,
                proposed_position TEXT NOT NULL,
                proposed_grade TEXT,
                proposed_salary REAL,
                justification TEXT NOT NULL,
                performance_rating TEXT,
                years_in_current_role REAL,
                manager_recommendation TEXT,
                status TEXT DEFAULT 'Pending' CHECK(status IN ('Pending', 'Manager Approved', 'HR Review', 'Budget Approved', 'Approved', 'Rejected', 'Implemented')),
                nominated_by INTEGER,
                manager_approved_by INTEGER,
                manager_approval_date TIMESTAMP,
                manager_comments TEXT,
                hr_approved_by INTEGER,
                hr_approval_date TIMESTAMP,
                hr_comments TEXT,
                budget_approved_by INTEGER,
                budget_approval_date TIMESTAMP,
                effective_date DATE,
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW(),
                FOREIGN KEY (emp_id) REFERENCES employees(id) ON DELETE CASCADE,
                FOREIGN KEY (nominated_by) REFERENCES employees(id),
                FOREIGN KEY (manager_approved_by) REFERENCES employees(id),
                FOREIGN KEY (hr_approved_by) REFERENCES employees(id),
                FOREIGN KEY (budget_approved_by) REFERENCES employees(id)
            )
        """)

        # 45. Succession Plans table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS succession_plans (
                id SERIAL PRIMARY KEY,
                key_position_emp_id INTEGER NOT NULL,
                successor_emp_id INTEGER,
                criticality TEXT CHECK(criticality IN ('Critical', 'High', 'Medium', 'Low')),
                risk_level TEXT CHECK(risk_level IN ('High', 'Medium', 'Low')),
                readiness_level TEXT CHECK(readiness_level IN ('Ready Now', '1-2 Years', '2-3 Years', '3+ Years')),
                development_plan TEXT,
                target_readiness_date DATE,
                notes TEXT,
                status TEXT DEFAULT 'Active' CHECK(status IN ('Active', 'Inactive')),
                created_by INTEGER,
                created_at TIMESTAMP DEFAULT NOW(),
                FOREIGN KEY (key_position_emp_id) REFERENCES employees(id) ON DELETE CASCADE,
                FOREIGN KEY (successor_emp_id) REFERENCES employees(id),
                FOREIGN KEY (created_by) REFERENCES employees(id)
            )
        """)

        # 46. Onboarding Tasks table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS onboarding_tasks (
                id SERIAL PRIMARY KEY,
                emp_id INTEGER NOT NULL,
                task_name TEXT NOT NULL,
                task_type TEXT CHECK(task_type IN ('Administrative', 'Technical', 'Training', 'Work', 'Review', 'Social')),
                description TEXT,
                assigned_to TEXT,
                due_date DATE,
                status TEXT DEFAULT 'Pending' CHECK(status IN ('Pending', 'In Progress', 'Completed', 'Overdue')),
                completion_date DATE,
                completion_notes TEXT,
                created_by INTEGER,
                created_at TIMESTAMP DEFAULT NOW(),
                FOREIGN KEY (emp_id) REFERENCES employees(id) ON DELETE CASCADE,
                FOREIGN KEY (created_by) REFERENCES employees(id)
            )
        """)

        # 47. Performance Improvement Plans (PIPs) table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pips (
                id SERIAL PRIMARY KEY,
                emp_id INTEGER NOT NULL,
                start_date DATE NOT NULL,
                end_date DATE NOT NULL,
                performance_issues TEXT NOT NULL,
                improvement_goals TEXT NOT NULL,
                success_criteria TEXT,
                support_resources TEXT,
                consequences TEXT,
                review_frequency TEXT,
                status TEXT DEFAULT 'Active' CHECK(status IN ('Active', 'Successful', 'Unsuccessful', 'Cancelled')),
                outcome TEXT,
                created_by INTEGER,
                created_at TIMESTAMP DEFAULT NOW(),
                FOREIGN KEY (emp_id) REFERENCES employees(id) ON DELETE CASCADE,
                FOREIGN KEY (created_by) REFERENCES employees(id)
            )
        """)

        # 48. PIP Progress table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pip_progress (
                id SERIAL PRIMARY KEY,
                pip_id INTEGER NOT NULL,
                review_date DATE NOT NULL,
                status TEXT CHECK(status IN ('On Track', 'Needs Improvement', 'Off Track', 'Exceeding Expectations')),
                notes TEXT,
                action_items TEXT,
                reviewed_by INTEGER,
                created_at TIMESTAMP DEFAULT NOW(),
                FOREIGN KEY (pip_id) REFERENCES pips(id) ON DELETE CASCADE,
                FOREIGN KEY (reviewed_by) REFERENCES employees(id)
            )
        """)

        # 49. Insurance Plans table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS insurance_plans (
                id SERIAL PRIMARY KEY,
                plan_name TEXT NOT NULL,
                plan_type TEXT CHECK(plan_type IN ('Health', 'Dental', 'Vision', 'Life', 'Disability')),
                monthly_premium REAL NOT NULL,
                deductible REAL,
                max_out_of_pocket REAL,
                coverage_details TEXT,
                status TEXT DEFAULT 'Active' CHECK(status IN ('Active', 'Inactive')),
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)

        # 50. Insurance Enrollments table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS insurance_enrollments (
                id SERIAL PRIMARY KEY,
                emp_id INTEGER NOT NULL,
                plan_name TEXT NOT NULL,
                coverage_type TEXT CHECK(coverage_type IN ('Employee Only', 'Employee + Spouse', 'Employee + Children', 'Family')),
                monthly_premium REAL,
                dependents_covered TEXT,
                enrollment_date DATE NOT NULL,
                effective_date DATE NOT NULL,
                status TEXT DEFAULT 'Pending' CHECK(status IN ('Pending', 'Active', 'Rejected', 'Cancelled')),
                approved_by INTEGER,
                approval_date DATE,
                created_at TIMESTAMP DEFAULT NOW(),
                FOREIGN KEY (emp_id) REFERENCES employees(id) ON DELETE CASCADE,
                FOREIGN KEY (approved_by) REFERENCES employees(id)
            )
        """)

        # 51. Shift Swaps table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS shift_swaps (
                id SERIAL PRIMARY KEY,
                requester_emp_id INTEGER NOT NULL,
                swapper_emp_id INTEGER NOT NULL,
                shift_date DATE NOT NULL,
                shift_type TEXT CHECK(shift_type IN ('Morning', 'Afternoon', 'Evening', 'Night', 'Full Day')),
                reason TEXT NOT NULL,
                request_date DATE NOT NULL,
                status TEXT DEFAULT 'Pending' CHECK(status IN ('Pending', 'Approved', 'Rejected')),
                approved_by INTEGER,
                approval_date DATE,
                created_at TIMESTAMP DEFAULT NOW(),
                FOREIGN KEY (requester_emp_id) REFERENCES employees(id) ON DELETE CASCADE,
                FOREIGN KEY (swapper_emp_id) REFERENCES employees(id) ON DELETE CASCADE,
                FOREIGN KEY (approved_by) REFERENCES employees(id)
            )
        """)

        # 52. Announcements table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS announcements (
                id SERIAL PRIMARY KEY,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                announcement_type TEXT CHECK(announcement_type IN ('General', 'HR Policy', 'Event', 'Holiday', 'Emergency', 'System', 'Team Update', 'Other')),
                priority TEXT CHECK(priority IN ('High', 'Medium', 'Low')),
                target_audience TEXT NOT NULL,
                status TEXT DEFAULT 'Pending' CHECK(status IN ('Draft', 'Pending', 'Published', 'Rejected')),
                created_by INTEGER NOT NULL,
                approved_by INTEGER,
                approval_date TIMESTAMP,
                published_date TIMESTAMP,
                created_at TIMESTAMP DEFAULT NOW(),
                FOREIGN KEY (created_by) REFERENCES employees(id),
                FOREIGN KEY (approved_by) REFERENCES employees(id)
            )
        """)

        # 53. Surveys table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS surveys (
                id SERIAL PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                survey_type TEXT CHECK(survey_type IN ('Employee Satisfaction', 'Engagement', '360 Feedback', 'Exit Survey', 'Training Feedback', 'Pulse Check', 'Other')),
                target_audience TEXT NOT NULL,
                start_date DATE NOT NULL,
                end_date DATE NOT NULL,
                is_anonymous BOOLEAN DEFAULT FALSE,
                status TEXT DEFAULT 'Draft' CHECK(status IN ('Draft', 'Active', 'Closed')),
                created_by INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT NOW(),
                FOREIGN KEY (created_by) REFERENCES employees(id)
            )
        """)

        # 54. Survey Questions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS survey_questions (
                id SERIAL PRIMARY KEY,
                survey_id INTEGER NOT NULL,
                question_text TEXT NOT NULL,
                question_type TEXT CHECK(question_type IN ('Rating (1-5)', 'Yes/No', 'Text')),
                question_order INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT NOW(),
                FOREIGN KEY (survey_id) REFERENCES surveys(id) ON DELETE CASCADE
            )
        """)

        # 55. Survey Responses table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS survey_responses (
                id SERIAL PRIMARY KEY,
                survey_id INTEGER NOT NULL,
                emp_id INTEGER NOT NULL,
                response_date DATE NOT NULL,
                created_at TIMESTAMP DEFAULT NOW(),
                FOREIGN KEY (survey_id) REFERENCES surveys(id) ON DELETE CASCADE,
                FOREIGN KEY (emp_id) REFERENCES employees(id) ON DELETE CASCADE
            )
        """)

        # 56. Survey Answers table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS survey_answers (
                id SERIAL PRIMARY KEY,
                response_id INTEGER NOT NULL,
                question_id INTEGER NOT NULL,
                answer_value TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT NOW(),
                FOREIGN KEY (response_id) REFERENCES survey_responses(id) ON DELETE CASCADE,
                FOREIGN KEY (question_id) REFERENCES survey_questions(id) ON DELETE CASCADE
            )
        """)

        # 57. Calibration Sessions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS calibration_sessions (
                id SERIAL PRIMARY KEY,
                session_name TEXT NOT NULL,
                session_date DATE NOT NULL,
                review_period TEXT NOT NULL,
                departments TEXT NOT NULL,
                notes TEXT,
                status TEXT DEFAULT 'Scheduled' CHECK(status IN ('Scheduled', 'In Progress', 'Completed')),
                created_by INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT NOW(),
                FOREIGN KEY (created_by) REFERENCES employees(id)
            )
        """)

        # 58. Calibration Session Ratings table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS calibration_session_ratings (
                id SERIAL PRIMARY KEY,
                session_id INTEGER NOT NULL,
                emp_id INTEGER NOT NULL,
                appraisal_id INTEGER,
                initial_rating TEXT,
                calibrated_rating TEXT,
                calibration_notes TEXT,
                calibrated_by INTEGER,
                calibration_date DATE,
                created_at TIMESTAMP DEFAULT NOW(),
                FOREIGN KEY (session_id) REFERENCES calibration_sessions(id) ON DELETE CASCADE,
                FOREIGN KEY (emp_id) REFERENCES employees(id) ON DELETE CASCADE,
                FOREIGN KEY (appraisal_id) REFERENCES appraisals(id),
                FOREIGN KEY (calibrated_by) REFERENCES employees(id)
            )
        """)

        # Apply database migrations for new fields
        apply_migrations(cursor)

        conn.commit()
        print("✅ Database initialized successfully with 58 tables!")

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
                VALUES (%s, ?, ?, ?, ?, ?, ?, 'Active', '2021-01-01', ?, ?)
            """, emp)
            emp_id = cursor.lastrowid

            # Create user accounts for each employee
            cursor.execute("""
                INSERT INTO users (username, password, role, employee_id, is_active)
                VALUES (%s, ?, 'employee', ?, 1)
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
                    VALUES (%s, ?, ?, 0, ?, 2024)
                """, (emp[0], leave_type, total_days, total_days))

        # Add sample financial records
        cursor.execute("""
            INSERT INTO financial_records (emp_id, base_salary, allowances, bonus, deductions, net_pay, period)
            VALUES (%s, 8000, 1000, 500, 200, 9300, '2024-01')
        """, (employee_emp_id,))

        # Add sample notifications
        cursor.execute("""
            INSERT INTO notifications (recipient_id, title, message, type)
            VALUES (%s, 'Welcome to Exalio HR System', 'Your account has been created successfully!', 'success')
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
