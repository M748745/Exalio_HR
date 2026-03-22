"""
Database Diagnostic Tool - Shows ACTUAL Database Structure on Streamlit Cloud
Run this on Streamlit Cloud to see what columns actually exist
"""

import streamlit as st
from database import get_db_connection

st.title("🔍 Database Diagnostic Tool")
st.info("This shows the ACTUAL database structure on Streamlit Cloud")

if st.button("🔍 Diagnose Database", type="primary", use_container_width=True):
    with st.spinner("Analyzing database..."):
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()

                # Get all tables
                cursor.execute("""
                    SELECT table_name
                    FROM information_schema.tables
                    WHERE table_schema = 'public'
                    ORDER BY table_name
                """)
                tables = [row['table_name'] for row in cursor.fetchall()]

                st.success(f"Found {len(tables)} tables in database")

                # For each table, show columns
                for table in tables:
                    with st.expander(f"📋 {table}", expanded=False):
                        cursor.execute(f"""
                            SELECT column_name, data_type, is_nullable
                            FROM information_schema.columns
                            WHERE table_name = '{table}'
                            ORDER BY ordinal_position
                        """)
                        columns = cursor.fetchall()

                        st.write(f"**Columns ({len(columns)}):**")
                        for col in columns:
                            nullable = "NULL" if col['is_nullable'] == 'YES' else "NOT NULL"
                            st.write(f"- `{col['column_name']}` ({col['data_type']}) {nullable}")

                # Check for specific missing columns that cause errors
                st.markdown("---")
                st.header("❌ Missing Columns Check")

                critical_columns = {
                    'employees': ['employee_id', 'hire_date', 'base_salary', 'role', 'status'],
                    'insurance': ['plan_name', 'coverage_type', 'network', 'dependants', 'renewal_date'],
                    'surveys': ['target_department', 'survey_type'],
                    'survey_responses': ['started_at'],
                    'training_catalog': ['max_participants', 'title'],
                    'training_enrollments': ['score', 'approved_by', 'approval_date'],
                    'expenses': ['manager_approved_by', 'manager_approval_date', 'finance_approved_by', 'finance_approval_date'],
                    'leave_requests': ['manager_approved_by', 'manager_approval_date', 'hr_approved_by', 'hr_approval_date'],
                    'goals': ['target_value', 'actual_completion_date', 'final_progress'],
                    'timesheets': ['project_name'],
                    'employee_skills': ['updated_at'],
                }

                missing_count = 0
                for table, expected_cols in critical_columns.items():
                    if table not in tables:
                        st.error(f"❌ TABLE `{table}` DOES NOT EXIST!")
                        missing_count += len(expected_cols)
                        continue

                    # Get actual columns
                    cursor.execute(f"""
                        SELECT column_name
                        FROM information_schema.columns
                        WHERE table_name = '{table}'
                    """)
                    actual_cols = [row['column_name'] for row in cursor.fetchall()]

                    # Check missing
                    missing = [col for col in expected_cols if col not in actual_cols]

                    if missing:
                        st.error(f"**{table}**: Missing {len(missing)} columns")
                        for col in missing:
                            st.write(f"  ❌ `{col}`")
                            missing_count += 1
                    else:
                        st.success(f"**{table}**: All critical columns exist ✅")

                if missing_count == 0:
                    st.balloons()
                    st.success("🎉 NO MISSING COLUMNS! Database is healthy!")
                else:
                    st.error(f"⚠️ Found {missing_count} missing columns")
                    st.info("💡 Run ultimate_fix.py to add missing columns")

        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
            import traceback
            st.code(traceback.format_exc())

else:
    st.markdown("""
    ### How to use this tool:

    1. Upload this file to GitHub
    2. Wait for Streamlit Cloud to sync
    3. Go to: `https://your-app-url/diagnose_database.py`
    4. Click the "Diagnose Database" button
    5. See EXACTLY what columns exist vs what's missing

    This will show the REAL database structure on Streamlit Cloud.
    """)

st.markdown("---")
st.caption("Database Diagnostic Tool - Shows Actual Database Schema")
