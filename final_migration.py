"""
FINAL Database Migration - Adds EXACTLY 16 Missing Columns
Based on actual health check comparison: expected columns vs actual database
Run this ONCE to fix all remaining issues
"""

import streamlit as st
from database import get_db_connection

st.title("🔧 FINAL Database Migration v6.0")
st.error("⚠️ This adds the EXACT 16 missing columns found by health check. Run it ONCE!")

# FINAL SQL migration - adds ONLY the missing columns
FINAL_MIGRATION = """
-- ============================================================
-- EXACT 16 MISSING COLUMNS (based on health check results)
-- ============================================================

-- 1. employees.base_salary
ALTER TABLE employees ADD COLUMN IF NOT EXISTS base_salary REAL DEFAULT 0;

-- 2. appraisals.self_achievements
ALTER TABLE appraisals ADD COLUMN IF NOT EXISTS self_achievements TEXT;

-- 3. financial_records.overtime_pay
ALTER TABLE financial_records ADD COLUMN IF NOT EXISTS overtime_pay REAL DEFAULT 0;

-- 4. training_catalog.title
ALTER TABLE training_catalog ADD COLUMN IF NOT EXISTS title TEXT;

-- 5-6. documents (emp_id, visibility)
ALTER TABLE documents ADD COLUMN IF NOT EXISTS emp_id INTEGER;
ALTER TABLE documents ADD COLUMN IF NOT EXISTS visibility TEXT;

-- 7. notifications.recipient_id
ALTER TABLE notifications ADD COLUMN IF NOT EXISTS recipient_id INTEGER;

-- 8. announcements.is_pinned
ALTER TABLE announcements ADD COLUMN IF NOT EXISTS is_pinned BOOLEAN DEFAULT FALSE;

-- 9. insurance.premium_monthly
ALTER TABLE insurance ADD COLUMN IF NOT EXISTS premium_monthly REAL DEFAULT 0;

-- 10. certificates.issuing_org
ALTER TABLE certificates ADD COLUMN IF NOT EXISTS issuing_org TEXT;

-- 11. exit_process.status
ALTER TABLE exit_process ADD COLUMN IF NOT EXISTS status TEXT;

-- 12. skills.status
ALTER TABLE skills ADD COLUMN IF NOT EXISTS status TEXT;

-- 13. goals.review_period
ALTER TABLE goals ADD COLUMN IF NOT EXISTS review_period TEXT;

-- 14. contracts.renewal_status
ALTER TABLE contracts ADD COLUMN IF NOT EXISTS renewal_status TEXT;

-- 15-16. compliance (emp_id, verified_by)
ALTER TABLE compliance ADD COLUMN IF NOT EXISTS emp_id INTEGER;
ALTER TABLE compliance ADD COLUMN IF NOT EXISTS verified_by INTEGER;
"""

if st.button("🚀 ADD FINAL 16 MISSING COLUMNS", type="primary", use_container_width=True):
    progress_bar = st.progress(0)
    status_text = st.empty()

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # Split into individual statements
            statements = [s.strip() for s in FINAL_MIGRATION.split(';') if s.strip() and 'ALTER TABLE' in s]

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
                    elif 'does not exist' in error_msg and 'relation' in error_msg:
                        skip_count += 1
                        results.append(('skip', f"{table_name} table doesn't exist"))
                    else:
                        error_count += 1
                        results.append(('error', f"{table_name}.{col_name}: {str(e)[:60]}"))

                progress_bar.progress((i + 1) / total)

            # Show results
            st.success(f"🎉 Final Migration Complete!")

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
            ✅ **Final Migration Complete! {success_count} columns added**

            **Next Steps:**
            1. Run check_remaining_errors.py to verify
            2. Expected result: 0 issues, ALL CLEAR!
            3. Go back to main app and test all modules
            """)

    except Exception as e:
        st.error(f"❌ Critical Error: {str(e)}")
        st.code(str(e))
        import traceback
        st.code(traceback.format_exc())

else:
    st.info("""
    ### 📊 Final Migration - Adds EXACTLY 16 Missing Columns:

    **Based on actual database comparison:**

    1. ✅ **employees.base_salary** - Base salary field
    2. ✅ **appraisals.self_achievements** - Self-assessment achievements
    3. ✅ **financial_records.overtime_pay** - Overtime payment tracking
    4. ✅ **training_catalog.title** - Course title
    5. ✅ **documents.emp_id** - Employee ID reference
    6. ✅ **documents.visibility** - Document visibility level
    7. ✅ **notifications.recipient_id** - Notification recipient
    8. ✅ **announcements.is_pinned** - Pin important announcements
    9. ✅ **insurance.premium_monthly** - Monthly premium amount
    10. ✅ **certificates.issuing_org** - Issuing organization
    11. ✅ **exit_process.status** - Exit process status
    12. ✅ **skills.status** - Skill status
    13. ✅ **goals.review_period** - Review period for goals
    14. ✅ **contracts.renewal_status** - Contract renewal status
    15. ✅ **compliance.emp_id** - Employee ID reference
    16. ✅ **compliance.verified_by** - Verification user

    **This is the FINAL migration based on health check results.**
    """)

    st.warning("⚠️ Safe to run multiple times - existing columns will be skipped.")

st.markdown("---")
st.caption("Final Migration Tool v6.0 - Adds Exactly 16 Missing Columns")
