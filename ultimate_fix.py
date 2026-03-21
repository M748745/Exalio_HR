"""
ULTIMATE FIX - Adds ALL Remaining Missing Columns
This fixes ALL errors including insurance, surveys, and survey_responses
"""

import streamlit as st
from database import get_db_connection

st.title("🔧 ULTIMATE Database Fix")
st.error("⚠️ This adds 9 MORE missing columns that were causing errors. Run it ONCE!")

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
"""

if st.button("🚀 ADD ALL 9 MISSING COLUMNS", type="primary", use_container_width=True):
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
            1. Test the app - insurance and surveys should work now!
            2. If you see any more errors, let me know immediately
            """)

    except Exception as e:
        st.error(f"❌ Critical Error: {str(e)}")
        st.code(str(e))
        import traceback
        st.code(traceback.format_exc())

else:
    st.info("""
    ### 📊 This adds 9 MORE missing columns:

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

    **These are the ACTUAL missing columns causing errors!**
    """)

    st.warning("⚠️ Safe to run multiple times - existing columns will be skipped.")

st.markdown("---")
st.caption("Ultimate Fix Tool - Adds 9 Missing Columns")
