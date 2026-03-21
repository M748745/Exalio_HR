"""
Database Health Check - Identifies ALL Remaining Issues
Run this AFTER running run_migration.py to see what's still broken
"""

import streamlit as st
from database import get_db_connection

st.title("🔍 Database Health Check")
st.info("This checks for ALL remaining database issues after migration")

if st.button("🔍 Check Database Health", type="primary", use_container_width=True):

    with st.spinner("Analyzing database..."):
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()

                # Lists to track issues
                missing_tables = []
                missing_columns = []
                existing_tables = []
                all_good = []

                # ============================================================
                # Check all tables that modules expect
                # ============================================================

                expected_tables = {
                    'employees': ['id', 'first_name', 'last_name', 'department', 'position', 'hire_date', 'base_salary', 'role', 'status'],
                    'appraisals': ['id', 'emp_id', 'status', 'overall_rating', 'manager_rating', 'hr_feedback', 'self_achievements', 'manager_id'],
                    'bonuses': ['id', 'emp_id', 'amount', 'status', 'manager_approved_by', 'hr_approved_by', 'payment_status'],
                    'financial_records': ['id', 'emp_id', 'base_salary', 'overtime_pay', 'payment_type', 'bonus_amount'],
                    'grades': ['id', 'emp_id', 'status', 'hr_approved_by'],
                    'training_catalog': ['id', 'title', 'category', 'level', 'duration_hours', 'created_by'],
                    'training_enrollments': ['id', 'emp_id', 'course_id', 'status', 'approved_by'],
                    'documents': ['id', 'emp_id', 'visibility', 'category', 'file_name', 'file_size'],
                    'job_applications': ['id', 'job_id', 'candidate_name', 'candidate_email', 'status', 'created_at'],
                    'jobs': ['id', 'title', 'status', 'created_at'],
                    'notifications': ['id', 'recipient_id', 'is_read'],
                    'announcements': ['id', 'title', 'is_pinned', 'status', 'created_by'],
                    'insurance': ['id', 'emp_id', 'premium_monthly', 'status'],
                    'certificates': ['id', 'emp_id', 'issuing_org', 'status'],
                    'exit_process': ['id', 'emp_id', 'status'],
                    'assets': ['id', 'asset_name', 'status'],
                    'skills': ['id', 'skill_name', 'status'],
                    'goals': ['id', 'emp_id', 'review_period'],
                    'contracts': ['id', 'emp_id', 'renewal_status'],
                    'compliance': ['id', 'emp_id', 'verified_by'],
                    'leave_requests': ['id', 'emp_id', 'status'],
                    'expenses': ['id', 'emp_id', 'status'],
                    'timesheets': ['id', 'emp_id', 'status'],

                    # New module tables
                    'promotion_requests': ['id', 'emp_id', 'status'],
                    'compliance_requirements': ['id', 'requirement_name'],
                    'shift_swaps': ['id', 'requester_emp_id', 'status'],
                    'calibration_sessions': ['id', 'session_name', 'status'],
                    'calibration_session_ratings': ['id', 'session_id', 'emp_id'],
                    'succession_plans': ['id', 'key_position_emp_id'],
                    'onboarding_tasks': ['id', 'emp_id', 'status'],
                    'pips': ['id', 'emp_id', 'status'],
                    'pip_progress': ['id', 'pip_id'],
                }

                # Get all tables in database
                cursor.execute("""
                    SELECT table_name
                    FROM information_schema.tables
                    WHERE table_schema='public'
                """)
                db_tables = [row['table_name'] for row in cursor.fetchall()]

                # Check each expected table
                for table_name, expected_columns in expected_tables.items():
                    if table_name not in db_tables:
                        missing_tables.append(table_name)
                    else:
                        existing_tables.append(table_name)

                        # Check columns in this table
                        cursor.execute(f"""
                            SELECT column_name
                            FROM information_schema.columns
                            WHERE table_name='{table_name}'
                        """)
                        actual_columns = [row['column_name'] for row in cursor.fetchall()]

                        table_missing_cols = []
                        for col in expected_columns:
                            if col not in actual_columns:
                                table_missing_cols.append(col)

                        if table_missing_cols:
                            missing_columns.append({
                                'table': table_name,
                                'columns': table_missing_cols
                            })
                        else:
                            all_good.append(table_name)

                # ============================================================
                # Display Results
                # ============================================================

                st.markdown("---")
                st.header("📊 Health Check Results")

                # Summary metrics
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("✅ Tables OK", len(all_good), delta="Complete")
                with col2:
                    st.metric("⚠️ Missing Columns", len(missing_columns), delta="Need fixing")
                with col3:
                    st.metric("❌ Missing Tables", len(missing_tables), delta="Need creating")
                with col4:
                    total_issues = len(missing_columns) + len(missing_tables)
                    st.metric("Total Issues", total_issues)

                # Missing Tables
                if missing_tables:
                    st.error(f"### ❌ Missing Tables ({len(missing_tables)})")
                    st.write("These tables don't exist in your database:")
                    for table in missing_tables:
                        st.write(f"- **{table}**")

                    st.info("💡 **Solution:** Upload and run `create_missing_tables.py`")

                # Missing Columns
                if missing_columns:
                    st.warning(f"### ⚠️ Tables with Missing Columns ({len(missing_columns)})")
                    for item in missing_columns:
                        with st.expander(f"📋 {item['table']} - {len(item['columns'])} missing columns"):
                            for col in item['columns']:
                                st.write(f"- `{col}`")

                    st.info("💡 **Solution:** Re-run `run_migration.py` or add these manually")

                # All Good
                if all_good:
                    with st.expander(f"✅ Healthy Tables ({len(all_good)})", expanded=False):
                        for table in all_good:
                            st.write(f"- {table}")

                # Overall status
                st.markdown("---")
                if not missing_tables and not missing_columns:
                    st.success("🎉 **ALL CLEAR!** Your database is healthy. No errors expected.")
                    st.balloons()
                else:
                    st.error(f"⚠️ **{total_issues} issues found**. Follow the solutions above to fix them.")

                    # Generate fix commands
                    st.markdown("### 🔧 Next Steps:")
                    if missing_tables:
                        st.code("""
# I'll create create_missing_tables.py for you
# Upload it to GitHub and run it
                        """, language="bash")

                    if missing_columns:
                        st.code("""
# Re-run run_migration.py to add missing columns
# Or wait for the updated version
                        """, language="bash")

        except Exception as e:
            st.error(f"❌ Error during health check: {str(e)}")
            st.code(str(e))
            import traceback
            st.code(traceback.format_exc())

else:
    st.markdown("""
    ### How to use this tool:

    1. **Upload** this file to GitHub (if not already done)
    2. **Access** it at: `https://your-app-url/check_remaining_errors.py`
    3. **Click** the "Check Database Health" button
    4. **Review** the results to see what's still broken
    5. **Follow** the recommended solutions

    This will give you a complete picture of ALL remaining database issues.
    """)

st.markdown("---")
st.caption("Database Health Check v1.0 - Comprehensive Error Detection")
