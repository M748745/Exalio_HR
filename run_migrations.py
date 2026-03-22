"""
Migration script to add missing tables and columns to the HR database
Run this script to update your database schema
"""

import sys
from database import get_db_connection

def run_migrations():
    """Apply all pending migrations to the database"""
    print("🚀 Starting database migrations...")

    with get_db_connection() as conn:
        cursor = conn.cursor()

        try:
            # Create shift_templates table
            print("\n📋 Creating shift_templates table...")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS shift_templates (
                    id SERIAL PRIMARY KEY,
                    shift_name TEXT NOT NULL,
                    shift_type TEXT CHECK(shift_type IN ('Morning', 'Afternoon', 'Evening', 'Night', 'Full Day', 'Flexible')),
                    start_time TIME NOT NULL,
                    end_time TIME NOT NULL,
                    department TEXT,
                    description TEXT,
                    status TEXT DEFAULT 'Active' CHECK(status IN ('Active', 'Inactive')),
                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW()
                )
            """)
            print("✅ shift_templates table created")

            # Create shift_schedules table
            print("\n📋 Creating shift_schedules table...")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS shift_schedules (
                    id SERIAL PRIMARY KEY,
                    emp_id INTEGER NOT NULL,
                    shift_id INTEGER NOT NULL,
                    shift_date DATE NOT NULL,
                    location TEXT DEFAULT 'Office',
                    notes TEXT,
                    status TEXT DEFAULT 'Scheduled' CHECK(status IN ('Scheduled', 'Confirmed', 'Completed', 'Cancelled')),
                    created_by INTEGER,
                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW(),
                    FOREIGN KEY (emp_id) REFERENCES employees(id) ON DELETE CASCADE,
                    FOREIGN KEY (shift_id) REFERENCES shift_templates(id),
                    FOREIGN KEY (created_by) REFERENCES employees(id)
                )
            """)
            print("✅ shift_schedules table created")

            # Create compliance_requirements table
            print("\n📋 Creating compliance_requirements table...")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS compliance_requirements (
                    id SERIAL PRIMARY KEY,
                    requirement_name TEXT NOT NULL,
                    requirement_type TEXT CHECK(requirement_type IN ('Legal', 'Regulatory', 'Policy', 'Safety', 'Training', 'Certification', 'Other')),
                    description TEXT,
                    department TEXT,
                    responsible_party TEXT,
                    frequency TEXT CHECK(frequency IN ('One-Time', 'Monthly', 'Quarterly', 'Semi-Annual', 'Annual', 'Biennial')),
                    last_review_date DATE,
                    next_review_date DATE NOT NULL,
                    status TEXT DEFAULT 'Pending' CHECK(status IN ('Compliant', 'Pending', 'Non-Compliant', 'In Progress')),
                    evidence_file_path TEXT,
                    notes TEXT,
                    created_by INTEGER,
                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW(),
                    FOREIGN KEY (created_by) REFERENCES employees(id)
                )
            """)
            print("✅ compliance_requirements table created")

            # Create onboarding table
            print("\n📋 Creating onboarding table...")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS onboarding (
                    id SERIAL PRIMARY KEY,
                    emp_id INTEGER NOT NULL,
                    start_date DATE NOT NULL,
                    buddy_id INTEGER,
                    orientation_date DATE,
                    it_setup TEXT DEFAULT 'Pending' CHECK(it_setup IN ('Pending', 'In Progress', 'Completed')),
                    workspace_setup TEXT DEFAULT 'Pending' CHECK(workspace_setup IN ('Pending', 'In Progress', 'Completed')),
                    system_access TEXT DEFAULT 'Pending' CHECK(system_access IN ('Pending', 'In Progress', 'Completed')),
                    email_setup TEXT DEFAULT 'Pending' CHECK(email_setup IN ('Pending', 'In Progress', 'Completed')),
                    team_introduction TEXT DEFAULT 'Pending' CHECK(team_introduction IN ('Pending', 'In Progress', 'Completed')),
                    policy_review TEXT DEFAULT 'Pending' CHECK(policy_review IN ('Pending', 'In Progress', 'Completed')),
                    training_scheduled TEXT DEFAULT 'Pending' CHECK(training_scheduled IN ('Pending', 'In Progress', 'Completed')),
                    status TEXT DEFAULT 'Pending' CHECK(status IN ('Pending', 'In Progress', 'Completed', 'Cancelled')),
                    completion_date DATE,
                    notes TEXT,
                    created_by INTEGER,
                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW(),
                    FOREIGN KEY (emp_id) REFERENCES employees(id) ON DELETE CASCADE,
                    FOREIGN KEY (buddy_id) REFERENCES employees(id),
                    FOREIGN KEY (created_by) REFERENCES employees(id)
                )
            """)
            print("✅ onboarding table created")

            # Add missing columns to training_catalog
            print("\n📋 Checking training_catalog columns...")
            cursor.execute("""
                SELECT column_name FROM information_schema.columns
                WHERE table_name='training_catalog'
            """)
            training_columns = [col['column_name'] for col in cursor.fetchall()]

            if 'title' not in training_columns:
                print("   Adding title column...")
                cursor.execute("ALTER TABLE training_catalog ADD COLUMN title TEXT")
                cursor.execute("UPDATE training_catalog SET title = course_name WHERE title IS NULL")
                cursor.execute("ALTER TABLE training_catalog ALTER COLUMN title SET NOT NULL")
                print("✅ Added title column to training_catalog")
            else:
                print("✅ title column already exists")

            if 'category' not in training_columns:
                print("   Adding category column...")
                cursor.execute("ALTER TABLE training_catalog ADD COLUMN category TEXT")
                print("✅ Added category column to training_catalog")
            else:
                print("✅ category column already exists")

            # Create budgets table
            print("\n📋 Creating budgets table...")
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
            print("✅ budgets table created")

            conn.commit()
            print("\n✅ All migrations completed successfully!")

        except Exception as e:
            conn.rollback()
            print(f"\n❌ Migration failed: {str(e)}")
            print("   Database changes have been rolled back.")
            sys.exit(1)

if __name__ == "__main__":
    run_migrations()
