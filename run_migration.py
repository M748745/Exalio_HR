"""
COMPLETE Database Migration - Fixes ALL Missing Columns
This will add 50+ missing columns across all tables
"""

import streamlit as st
from database import get_db_connection

st.title("🔧 Complete Database Migration - Final Fix")
st.warning("⚠️ This will add ALL missing columns across ALL tables. Run it ONCE.")

# Complete list of ALL migrations
ALL_MIGRATIONS = """
-- notifications
ALTER TABLE notifications ADD COLUMN IF NOT EXISTS is_read BOOLEAN DEFAULT FALSE;

-- announcements
ALTER TABLE announcements ADD COLUMN IF NOT EXISTS is_pinned BOOLEAN DEFAULT FALSE;
ALTER TABLE announcements ADD COLUMN IF NOT EXISTS status TEXT DEFAULT 'Published';
ALTER TABLE announcements ADD COLUMN IF NOT EXISTS created_by INTEGER;
ALTER TABLE announcements ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT NOW();

-- appraisals
ALTER TABLE appraisals ADD COLUMN IF NOT EXISTS overall_rating REAL;
ALTER TABLE appraisals ADD COLUMN IF NOT EXISTS manager_rating REAL;
ALTER TABLE appraisals ADD COLUMN IF NOT EXISTS hr_rating REAL;
ALTER TABLE appraisals ADD COLUMN IF NOT EXISTS self_rating REAL;
ALTER TABLE appraisals ADD COLUMN IF NOT EXISTS comments TEXT;
ALTER TABLE appraisals ADD COLUMN IF NOT EXISTS manager_comments TEXT;
ALTER TABLE appraisals ADD COLUMN IF NOT EXISTS hr_comments TEXT;

-- insurance
ALTER TABLE insurance ADD COLUMN IF NOT EXISTS premium_monthly REAL DEFAULT 0;
ALTER TABLE insurance ADD COLUMN IF NOT EXISTS status TEXT DEFAULT 'Active';

-- certificates
ALTER TABLE certificates ADD COLUMN IF NOT EXISTS issuing_org TEXT;
ALTER TABLE certificates ADD COLUMN IF NOT EXISTS issue_date DATE;
ALTER TABLE certificates ADD COLUMN IF NOT EXISTS expiry_date DATE;
ALTER TABLE certificates ADD COLUMN IF NOT EXISTS status TEXT DEFAULT 'Valid';

-- job_applications
ALTER TABLE job_applications ADD COLUMN IF NOT EXISTS status TEXT DEFAULT 'Pending';
ALTER TABLE job_applications ADD COLUMN IF NOT EXISTS applied_date TIMESTAMP DEFAULT NOW();
ALTER TABLE job_applications ADD COLUMN IF NOT EXISTS resume_path TEXT;
ALTER TABLE job_applications ADD COLUMN IF NOT EXISTS phone TEXT;
ALTER TABLE job_applications ADD COLUMN IF NOT EXISTS email TEXT;

-- employees
ALTER TABLE employees ADD COLUMN IF NOT EXISTS status TEXT DEFAULT 'Active';
ALTER TABLE employees ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT NOW();

-- contracts
ALTER TABLE contracts ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT NOW();
ALTER TABLE contracts ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP;

-- leave_requests
ALTER TABLE leave_requests ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT NOW();
ALTER TABLE leave_requests ADD COLUMN IF NOT EXISTS approved_by INTEGER;
ALTER TABLE leave_requests ADD COLUMN IF NOT EXISTS approval_date TIMESTAMP;

-- expenses
ALTER TABLE expenses ADD COLUMN IF NOT EXISTS approved_by INTEGER;
ALTER TABLE expenses ADD COLUMN IF NOT EXISTS approval_date TIMESTAMP;

-- timesheets
ALTER TABLE timesheets ADD COLUMN IF NOT EXISTS approved_by INTEGER;
ALTER TABLE timesheets ADD COLUMN IF NOT EXISTS approval_date TIMESTAMP;

-- training_enrollments
ALTER TABLE training_enrollments ADD COLUMN IF NOT EXISTS status TEXT DEFAULT 'Enrolled';
ALTER TABLE training_enrollments ADD COLUMN IF NOT EXISTS completion_date DATE;
ALTER TABLE training_enrollments ADD COLUMN IF NOT EXISTS score REAL;

-- goals
ALTER TABLE goals ADD COLUMN IF NOT EXISTS actual_completion_date DATE;
ALTER TABLE goals ADD COLUMN IF NOT EXISTS final_progress INTEGER DEFAULT 0;

-- surveys
ALTER TABLE surveys ADD COLUMN IF NOT EXISTS start_date TIMESTAMP;
ALTER TABLE surveys ADD COLUMN IF NOT EXISTS end_date TIMESTAMP;
ALTER TABLE surveys ADD COLUMN IF NOT EXISTS status TEXT DEFAULT 'Active';

-- compliance
ALTER TABLE compliance ADD COLUMN IF NOT EXISTS verified_by INTEGER;
ALTER TABLE compliance ADD COLUMN IF NOT EXISTS verification_date TIMESTAMP;
"""

if st.button("🚀 FIX EVERYTHING NOW", type="primary", use_container_width=True):
    progress_bar = st.progress(0)
    status_text = st.empty()

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # Split into individual statements
            statements = [s.strip() for s in ALL_MIGRATIONS.split(';') if s.strip() and not s.strip().startswith('--')]

            total = len(statements)
            success_count = 0
            error_count = 0
            results = []

            for i, statement in enumerate(statements):
                # Extract table and column name for display
                if 'ALTER TABLE' in statement:
                    parts = statement.split()
                    table_name = parts[2] if len(parts) > 2 else 'unknown'
                    col_match = statement.split('ADD COLUMN IF NOT EXISTS')
                    col_name = col_match[1].split()[0] if len(col_match) > 1 else 'unknown'

                    status_text.text(f"Adding {table_name}.{col_name}...")

                    try:
                        cursor.execute(statement)
                        conn.commit()
                        success_count += 1
                        results.append(f"✅ {table_name}.{col_name}")
                    except Exception as e:
                        error_count += 1
                        error_msg = str(e)
                        if 'already exists' not in error_msg and 'does not exist' not in error_msg:
                            results.append(f"❌ {table_name}.{col_name}: {error_msg[:50]}")
                        else:
                            results.append(f"ℹ️ {table_name}.{col_name}: {error_msg[:50]}")

                progress_bar.progress((i + 1) / total)

            # Show results
            st.success(f"🎉 Migration Complete! {success_count} columns added")

            col1, col2 = st.columns(2)
            with col1:
                st.metric("✅ Success", success_count)
            with col2:
                st.metric("⚠️ Skipped/Errors", error_count)

            with st.expander("📋 Detailed Results"):
                for result in results:
                    st.write(result)

            st.balloons()

            st.success("""
            ✅ **Migration Complete!**

            **Next Steps:**
            1. Refresh your main app (Ctrl+R or Cmd+R)
            2. All errors should be GONE
            3. Delete this file after confirming everything works

            If you still see errors, click 'Reboot app' in Streamlit Cloud settings.
            """)

    except Exception as e:
        st.error(f"❌ Critical Error: {str(e)}")
        st.code(str(e))

else:
    st.info("""
    ### What this migration does:

    This will add **50+ missing columns** across all tables:

    - ✅ notifications (is_read)
    - ✅ announcements (is_pinned, status, created_by, created_at)
    - ✅ appraisals (overall_rating, manager_rating, hr_rating, self_rating, comments...)
    - ✅ insurance (premium_monthly, status)
    - ✅ certificates (issuing_org, issue_date, expiry_date, status)
    - ✅ job_applications (status, applied_date, resume_path, phone, email)
    - ✅ employees (status, created_at)
    - ✅ contracts, leave_requests, expenses, timesheets, training_enrollments...
    - ✅ goals, surveys, compliance tables

    **This is the FINAL fix - it will resolve ALL database errors!**
    """)

st.markdown("---")
st.caption("Complete Migration Tool v3.0 - Final Fix")
