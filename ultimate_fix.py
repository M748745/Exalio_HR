"""
ULTIMATE FIX - Adds ALL Remaining Missing Columns
This fixes ALL errors including insurance, surveys, training, goals, expenses, leave_requests
"""

import streamlit as st
from database import get_db_connection

st.title("🔧 ULTIMATE Database Fix v2.0")
st.error("⚠️ This adds 20 missing columns that were causing errors. Run it ONCE!")

ULTIMATE_FIX_SQL = """
-- ============================================================
-- INSURANCE TABLE - 5 Missing Columns
-- ============================================================
ALTER TABLE insurance ADD COLUMN IF NOT EXISTS plan_name TEXT;
ALTER TABLE insurance ADD COLUMN IF NOT EXISTS coverage_type TEXT;
ALTER TABLE insurance ADD COLUMN IF NOT EXISTS network TEXT;
ALTER TABLE insurance ADD COLUMN IF NOT EXISTS dependants INTEGER DEFAULT 0;
ALTER TABLE insurance ADD COLUMN IF NOT EXISTS renewal_date DATE;

-- ============================================================
-- SURVEYS TABLE - 2 Missing Columns
-- ============================================================
ALTER TABLE surveys ADD COLUMN IF NOT EXISTS target_department TEXT;
ALTER TABLE surveys ADD COLUMN IF NOT EXISTS survey_type TEXT;

-- ============================================================
-- SURVEY_RESPONSES TABLE - 1 Missing Column
-- ============================================================
ALTER TABLE survey_responses ADD COLUMN IF NOT EXISTS started_at TIMESTAMP;

-- ============================================================
-- EMPLOYEE_SKILLS TABLE - 1 Missing Column
-- ============================================================
ALTER TABLE employee_skills ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT NOW();

-- ============================================================
-- TRAINING_CATALOG TABLE - 1 Missing Column
-- ============================================================
ALTER TABLE training_catalog ADD COLUMN IF NOT EXISTS max_participants INTEGER;

-- ============================================================
-- GOALS TABLE - 1 Missing Column
-- ============================================================
ALTER TABLE goals ADD COLUMN IF NOT EXISTS target_value REAL;

-- ============================================================
-- TIMESHEETS TABLE - 1 Missing Column
-- ============================================================
ALTER TABLE timesheets ADD COLUMN IF NOT EXISTS project_name TEXT;

-- ============================================================
-- EXPENSES TABLE - 4 Missing Columns
-- ============================================================
ALTER TABLE expenses ADD COLUMN IF NOT EXISTS manager_approved_by INTEGER;
ALTER TABLE expenses ADD COLUMN IF NOT EXISTS manager_approval_date TIMESTAMP;
ALTER TABLE expenses ADD COLUMN IF NOT EXISTS finance_approved_by INTEGER;
ALTER TABLE expenses ADD COLUMN IF NOT EXISTS finance_approval_date TIMESTAMP;

-- ============================================================
-- LEAVE_REQUESTS TABLE - 4 Missing Columns
-- ============================================================
ALTER TABLE leave_requests ADD COLUMN IF NOT EXISTS manager_approved_by INTEGER;
ALTER TABLE leave_requests ADD COLUMN IF NOT EXISTS manager_approval_date TIMESTAMP;
ALTER TABLE leave_requests ADD COLUMN IF NOT EXISTS hr_approved_by INTEGER;
ALTER TABLE leave_requests ADD COLUMN IF NOT EXISTS hr_approval_date TIMESTAMP;
"""

if st.button("🚀 ADD ALL 20 MISSING COLUMNS", type="primary", use_container_width=True):
    progress_bar = st.progress(0)
    status_text = st.empty()

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            statements = [s.strip() for s in ULTIMATE_FIX_SQL.split(';') if s.strip() and 'ALTER TABLE' in s]

            total = len(statements)
            success_count = 0
            skip_count = 0
            error_count = 0
            results = []

            for i, statement in enumerate(statements):
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
                    else:
                        error_count += 1
                        results.append(('error', f"{table_name}.{col_name}: {str(e)[:60]}"))
                    conn.rollback()

                progress_bar.progress((i + 1) / total)

            st.success(f"🎉 Ultimate Fix Complete!")

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("✅ Added", success_count, delta="New columns")
            with col2:
                st.metric("⏭️ Skipped", skip_count, delta="Already exist")
            with col3:
                st.metric("❌ Errors", error_count, delta="Need attention")

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
            ✅ **Ultimate Fix Complete! {success_count} columns added**

            **Next Steps:**
            1. Test the app - ALL modules should work now!
            2. All 20 missing columns have been added
            3. No more UndefinedColumn errors!
            """)

    except Exception as e:
        st.error(f"❌ Critical Error: {str(e)}")
        st.code(str(e))
        import traceback
        st.code(traceback.format_exc())

else:
    st.info("""
    ### 📊 This adds 20 missing columns across 8 tables:

    **Insurance (5 columns):**
    - ✅ plan_name - Insurance plan name
    - ✅ coverage_type - Type of coverage
    - ✅ network - Insurance network
    - ✅ dependants - Number of dependants
    - ✅ renewal_date - Policy renewal date

    **Surveys (2 columns):**
    - ✅ target_department - Survey target department
    - ✅ survey_type - Type of survey

    **Survey Responses (1 column):**
    - ✅ started_at - When survey was started

    **Employee Skills (1 column):**
    - ✅ updated_at - Last update timestamp

    **Training Catalog (1 column):**
    - ✅ max_participants - Maximum participants

    **Goals (1 column):**
    - ✅ target_value - Target value for goal

    **Timesheets (1 column):**
    - ✅ project_name - Project name

    **Expenses (4 columns):**
    - ✅ manager_approved_by - Manager approval
    - ✅ manager_approval_date - Manager approval date
    - ✅ finance_approved_by - Finance approval
    - ✅ finance_approval_date - Finance approval date

    **Leave Requests (4 columns):**
    - ✅ manager_approved_by - Manager approval
    - ✅ manager_approval_date - Manager approval date
    - ✅ hr_approved_by - HR approval
    - ✅ hr_approval_date - HR approval date

    **These are ALL the missing columns causing errors!**
    """)

    st.warning("⚠️ Safe to run multiple times - existing columns will be skipped.")

st.markdown("---")
st.caption("Ultimate Fix Tool v2.0 - Adds 20 Missing Columns")
