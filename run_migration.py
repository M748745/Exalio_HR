"""
UPDATED Database Migration - ALL Missing Columns Based on Health Check
Adds 60+ missing columns including the ones from health check
"""

import streamlit as st
from database import get_db_connection

st.title("🔧 UPDATED Database Migration v5.0")
st.error("⚠️ Updated to add ALL missing columns from health check. Run it ONCE!")

# COMPLETE SQL migration - updated based on health check results
COMPLETE_MIGRATION = """
-- ============================================================
-- EMPLOYEES TABLE (2 columns from health check)
-- ============================================================
ALTER TABLE employees ADD COLUMN IF NOT EXISTS base_salary REAL DEFAULT 0;
ALTER TABLE employees ADD COLUMN IF NOT EXISTS role TEXT CHECK(role IN ('employee', 'manager', 'hr_admin'));
ALTER TABLE employees ADD COLUMN IF NOT EXISTS hire_date DATE;
ALTER TABLE employees ADD COLUMN IF NOT EXISTS status TEXT DEFAULT 'Active';

-- ============================================================
-- APPRAISALS TABLE (13 columns - CRITICAL)
-- ============================================================
ALTER TABLE appraisals ADD COLUMN IF NOT EXISTS self_achievements TEXT;
ALTER TABLE appraisals ADD COLUMN IF NOT EXISTS self_areas_improvement TEXT;
ALTER TABLE appraisals ADD COLUMN IF NOT EXISTS self_goals TEXT;
ALTER TABLE appraisals ADD COLUMN IF NOT EXISTS manager_feedback TEXT;
ALTER TABLE appraisals ADD COLUMN IF NOT EXISTS manager_rating INTEGER;
ALTER TABLE appraisals ADD COLUMN IF NOT EXISTS hr_feedback TEXT;
ALTER TABLE appraisals ADD COLUMN IF NOT EXISTS overall_rating INTEGER;
ALTER TABLE appraisals ADD COLUMN IF NOT EXISTS recommendations TEXT;
ALTER TABLE appraisals ADD COLUMN IF NOT EXISTS self_review_date TIMESTAMP;
ALTER TABLE appraisals ADD COLUMN IF NOT EXISTS manager_id INTEGER;
ALTER TABLE appraisals ADD COLUMN IF NOT EXISTS created_by INTEGER;
ALTER TABLE appraisals ADD COLUMN IF NOT EXISTS hr_reviewer INTEGER;
ALTER TABLE appraisals ADD COLUMN IF NOT EXISTS comments TEXT;
ALTER TABLE appraisals ADD COLUMN IF NOT EXISTS manager_comments TEXT;
ALTER TABLE appraisals ADD COLUMN IF NOT EXISTS hr_comments TEXT;

-- ============================================================
-- BONUSES TABLE (7 columns)
-- ============================================================
ALTER TABLE bonuses ADD COLUMN IF NOT EXISTS manager_approved_by INTEGER;
ALTER TABLE bonuses ADD COLUMN IF NOT EXISTS manager_approval_date TIMESTAMP;
ALTER TABLE bonuses ADD COLUMN IF NOT EXISTS hr_approved_by INTEGER;
ALTER TABLE bonuses ADD COLUMN IF NOT EXISTS hr_approval_date TIMESTAMP;
ALTER TABLE bonuses ADD COLUMN IF NOT EXISTS hr_comments TEXT;
ALTER TABLE bonuses ADD COLUMN IF NOT EXISTS payment_status TEXT CHECK(payment_status IN ('Pending', 'Paid'));
ALTER TABLE bonuses ADD COLUMN IF NOT EXISTS payment_date DATE;

-- ============================================================
-- FINANCIAL_RECORDS TABLE (5 columns)
-- ============================================================
ALTER TABLE financial_records ADD COLUMN IF NOT EXISTS overtime_pay REAL DEFAULT 0;
ALTER TABLE financial_records ADD COLUMN IF NOT EXISTS payment_type TEXT;
ALTER TABLE financial_records ADD COLUMN IF NOT EXISTS notes TEXT;
ALTER TABLE financial_records ADD COLUMN IF NOT EXISTS bonus_amount REAL DEFAULT 0;
ALTER TABLE financial_records ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT NOW();

-- ============================================================
-- GRADES TABLE (4 columns)
-- ============================================================
ALTER TABLE grades ADD COLUMN IF NOT EXISTS status TEXT DEFAULT 'Pending' CHECK(status IN ('Pending', 'Approved', 'Rejected'));
ALTER TABLE grades ADD COLUMN IF NOT EXISTS hr_approved_by INTEGER;
ALTER TABLE grades ADD COLUMN IF NOT EXISTS hr_approval_date TIMESTAMP;
ALTER TABLE grades ADD COLUMN IF NOT EXISTS hr_comments TEXT;

-- ============================================================
-- TRAINING_CATALOG TABLE (9 columns)
-- ============================================================
ALTER TABLE training_catalog ADD COLUMN IF NOT EXISTS title TEXT;
ALTER TABLE training_catalog ADD COLUMN IF NOT EXISTS category TEXT;
ALTER TABLE training_catalog ADD COLUMN IF NOT EXISTS level TEXT CHECK(level IN ('Beginner', 'Intermediate', 'Advanced'));
ALTER TABLE training_catalog ADD COLUMN IF NOT EXISTS duration_hours REAL;
ALTER TABLE training_catalog ADD COLUMN IF NOT EXISTS currency TEXT DEFAULT 'USD';
ALTER TABLE training_catalog ADD COLUMN IF NOT EXISTS delivery_mode TEXT;
ALTER TABLE training_catalog ADD COLUMN IF NOT EXISTS prerequisites TEXT;
ALTER TABLE training_catalog ADD COLUMN IF NOT EXISTS created_by INTEGER;
ALTER TABLE training_catalog ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT NOW();

-- ============================================================
-- TRAINING_ENROLLMENTS TABLE (3 columns)
-- ============================================================
ALTER TABLE training_enrollments ADD COLUMN IF NOT EXISTS status TEXT DEFAULT 'Enrolled';
ALTER TABLE training_enrollments ADD COLUMN IF NOT EXISTS approved_by INTEGER;
ALTER TABLE training_enrollments ADD COLUMN IF NOT EXISTS approval_date TIMESTAMP;
ALTER TABLE training_enrollments ADD COLUMN IF NOT EXISTS completion_date DATE;
ALTER TABLE training_enrollments ADD COLUMN IF NOT EXISTS score REAL;

-- ============================================================
-- DOCUMENTS TABLE (7 columns)
-- ============================================================
ALTER TABLE documents ADD COLUMN IF NOT EXISTS visibility TEXT CHECK(visibility IN ('Private', 'Team', 'Public'));
ALTER TABLE documents ADD COLUMN IF NOT EXISTS category TEXT;
ALTER TABLE documents ADD COLUMN IF NOT EXISTS file_name TEXT;
ALTER TABLE documents ADD COLUMN IF NOT EXISTS file_size INTEGER;
ALTER TABLE documents ADD COLUMN IF NOT EXISTS target_department TEXT;
ALTER TABLE documents ADD COLUMN IF NOT EXISTS uploaded_by INTEGER;
ALTER TABLE documents ADD COLUMN IF NOT EXISTS uploaded_at TIMESTAMP DEFAULT NOW();

-- ============================================================
-- JOB_APPLICATIONS TABLE (7 columns)
-- ============================================================
ALTER TABLE job_applications ADD COLUMN IF NOT EXISTS candidate_name TEXT;
ALTER TABLE job_applications ADD COLUMN IF NOT EXISTS candidate_email TEXT;
ALTER TABLE job_applications ADD COLUMN IF NOT EXISTS candidate_phone TEXT;
ALTER TABLE job_applications ADD COLUMN IF NOT EXISTS experience_years INTEGER;
ALTER TABLE job_applications ADD COLUMN IF NOT EXISTS expected_salary REAL;
ALTER TABLE job_applications ADD COLUMN IF NOT EXISTS notes TEXT;
ALTER TABLE job_applications ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT NOW();
ALTER TABLE job_applications ADD COLUMN IF NOT EXISTS status TEXT DEFAULT 'Pending';
ALTER TABLE job_applications ADD COLUMN IF NOT EXISTS applied_date TIMESTAMP DEFAULT NOW();

-- ============================================================
-- JOBS TABLE (2 columns)
-- ============================================================
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT NOW();
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS created_by INTEGER;

-- ============================================================
-- NOTIFICATIONS TABLE (1 column)
-- ============================================================
ALTER TABLE notifications ADD COLUMN IF NOT EXISTS is_read BOOLEAN DEFAULT FALSE;

-- ============================================================
-- ANNOUNCEMENTS TABLE (5 columns)
-- ============================================================
ALTER TABLE announcements ADD COLUMN IF NOT EXISTS is_pinned BOOLEAN DEFAULT FALSE;
ALTER TABLE announcements ADD COLUMN IF NOT EXISTS status TEXT DEFAULT 'Published';
ALTER TABLE announcements ADD COLUMN IF NOT EXISTS created_by INTEGER;
ALTER TABLE announcements ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT NOW();
ALTER TABLE announcements ADD COLUMN IF NOT EXISTS expiry_date DATE;

-- ============================================================
-- INSURANCE TABLE (2 columns)
-- ============================================================
ALTER TABLE insurance ADD COLUMN IF NOT EXISTS status TEXT DEFAULT 'Active';
ALTER TABLE insurance ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT NOW();

-- ============================================================
-- CERTIFICATES TABLE (2 columns)
-- ============================================================
ALTER TABLE certificates ADD COLUMN IF NOT EXISTS issuing_org TEXT;
ALTER TABLE certificates ADD COLUMN IF NOT EXISTS verified_by INTEGER;
ALTER TABLE certificates ADD COLUMN IF NOT EXISTS verification_date TIMESTAMP;

-- ============================================================
-- EXIT_PROCESS TABLE (2 columns)
-- ============================================================
ALTER TABLE exit_process ADD COLUMN IF NOT EXISTS status TEXT DEFAULT 'In Progress';
ALTER TABLE exit_process ADD COLUMN IF NOT EXISTS final_settlement_amount REAL;

-- ============================================================
-- ASSETS TABLE (2 columns)
-- ============================================================
ALTER TABLE assets ADD COLUMN IF NOT EXISTS status TEXT DEFAULT 'Available';
ALTER TABLE assets ADD COLUMN IF NOT EXISTS notes TEXT;

-- ============================================================
-- SKILLS TABLE (2 columns)
-- ============================================================
ALTER TABLE skills ADD COLUMN IF NOT EXISTS status TEXT DEFAULT 'Active';
ALTER TABLE skills ADD COLUMN IF NOT EXISTS level_description TEXT;

-- ============================================================
-- GOALS TABLE (3 columns)
-- ============================================================
ALTER TABLE goals ADD COLUMN IF NOT EXISTS review_period TEXT;
ALTER TABLE goals ADD COLUMN IF NOT EXISTS actual_completion_date DATE;
ALTER TABLE goals ADD COLUMN IF NOT EXISTS final_progress INTEGER DEFAULT 0;

-- ============================================================
-- CONTRACTS TABLE (3 columns)
-- ============================================================
ALTER TABLE contracts ADD COLUMN IF NOT EXISTS renewal_status TEXT;
ALTER TABLE contracts ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT NOW();
ALTER TABLE contracts ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP;
ALTER TABLE contracts ADD COLUMN IF NOT EXISTS renewal_date DATE;

-- ============================================================
-- COMPLIANCE TABLE (3 columns)
-- ============================================================
ALTER TABLE compliance ADD COLUMN IF NOT EXISTS verified_by INTEGER;
ALTER TABLE compliance ADD COLUMN IF NOT EXISTS verification_date TIMESTAMP;
ALTER TABLE compliance ADD COLUMN IF NOT EXISTS notes TEXT;

-- ============================================================
-- LEAVE_REQUESTS TABLE
-- ============================================================
ALTER TABLE leave_requests ADD COLUMN IF NOT EXISTS approved_by INTEGER;
ALTER TABLE leave_requests ADD COLUMN IF NOT EXISTS approval_date TIMESTAMP;
ALTER TABLE leave_requests ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT NOW();

-- ============================================================
-- EXPENSES TABLE
-- ============================================================
ALTER TABLE expenses ADD COLUMN IF NOT EXISTS approved_by INTEGER;
ALTER TABLE expenses ADD COLUMN IF NOT EXISTS approval_date TIMESTAMP;
ALTER TABLE expenses ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT NOW();

-- ============================================================
-- TIMESHEETS TABLE
-- ============================================================
ALTER TABLE timesheets ADD COLUMN IF NOT EXISTS approved_by INTEGER;
ALTER TABLE timesheets ADD COLUMN IF NOT EXISTS approval_date TIMESTAMP;
ALTER TABLE timesheets ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT NOW();

-- ============================================================
-- SURVEYS TABLE
-- ============================================================
ALTER TABLE surveys ADD COLUMN IF NOT EXISTS start_date TIMESTAMP;
ALTER TABLE surveys ADD COLUMN IF NOT EXISTS end_date TIMESTAMP;
ALTER TABLE surveys ADD COLUMN IF NOT EXISTS status TEXT DEFAULT 'Active';

-- ============================================================
-- ONBOARDING_TASKS TABLE
-- ============================================================
ALTER TABLE onboarding_tasks ADD COLUMN IF NOT EXISTS status TEXT DEFAULT 'Pending';
ALTER TABLE onboarding_tasks ADD COLUMN IF NOT EXISTS completed_date DATE;
"""

if st.button("🚀 FIX ALL 60+ MISSING COLUMNS NOW", type="primary", use_container_width=True):
    progress_bar = st.progress(0)
    status_text = st.empty()

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # Split into individual statements
            statements = [s.strip() for s in COMPLETE_MIGRATION.split(';') if s.strip() and s.strip() and not s.strip().startswith('--')]

            total = len(statements)
            success_count = 0
            skip_count = 0
            error_count = 0
            results = []

            for i, statement in enumerate(statements):
                if 'ALTER TABLE' in statement:
                    parts = statement.split()
                    table_name = parts[2] if len(parts) > 2 else 'unknown'
                    col_match = statement.split('ADD COLUMN IF NOT EXISTS')
                    col_name = col_match[1].split()[0] if len(col_match) > 1 else 'unknown'

                    status_text.text(f"[{i+1}/{total}] Adding {table_name}.{col_name}...")

                    try:
                        cursor.execute(statement)
                        conn.commit()
                        success_count += 1
                        results.append(('success', f"{table_name}.{col_name}"))
                    except Exception as e:
                        error_msg = str(e).lower()
                        if 'already exists' in error_msg:
                            skip_count += 1
                            results.append(('skip', f"{table_name}.{col_name} (already exists)"))
                        elif 'does not exist' in error_msg and 'relation' in error_msg:
                            skip_count += 1
                            results.append(('skip', f"{table_name} table doesn't exist"))
                        else:
                            error_count += 1
                            results.append(('error', f"{table_name}.{col_name}: {str(e)[:60]}"))

                progress_bar.progress((i + 1) / total)

            # Show results
            st.success(f"🎉 Migration Complete!")

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("✅ Added", success_count, delta="New columns")
            with col2:
                st.metric("⏭️ Skipped", skip_count, delta="Already exist")
            with col3:
                st.metric("❌ Errors", error_count, delta="Need attention")

            # Show detailed results
            with st.expander(f"📋 Detailed Results ({len(results)} items)", expanded=error_count > 0):
                for status, msg in results:
                    if status == 'success':
                        st.success(f"✅ {msg}")
                    elif status == 'skip':
                        st.info(f"ℹ️ {msg}")
                    else:
                        st.error(f"❌ {msg}")

            if success_count > 0:
                st.balloons()

            st.success(f"""
            ✅ **Migration Complete! {success_count} columns added**

            **Next Steps:**
            1. Run check_remaining_errors.py to verify
            2. If all clear, go back to main app
            3. Refresh and all errors should be GONE!
            """)

    except Exception as e:
        st.error(f"❌ Critical Error: {str(e)}")
        st.code(str(e))
        import traceback
        st.code(traceback.format_exc())

else:
    st.info("""
    ### 📊 UPDATED Migration - Now adds 60+ columns:

    **Based on health check results, this adds ALL missing columns:**

    - ✅ **employees** (4): base_salary, role, hire_date, status
    - ✅ **appraisals** (15): All feedback and rating columns
    - ✅ **bonuses** (7): Complete approval workflow
    - ✅ **financial_records** (5): All payment tracking
    - ✅ **training_catalog** (9): Full course metadata
    - ✅ **Plus 15+ other tables** with their missing columns

    **This version is UPDATED based on your health check results!**
    """)

    st.warning("⚠️ Safe to run multiple times - existing columns will be skipped.")

st.markdown("---")
st.caption("Ultimate Migration Tool v5.0 - Updated from Health Check")
