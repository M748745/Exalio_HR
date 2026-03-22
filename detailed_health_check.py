"""
DETAILED Database Health Check - Shows EXACT Missing Columns
This shows the actual column names that are missing
"""

import streamlit as st
from database import get_db_connection

st.title("🔍 Detailed Database Health Check")
st.info("This shows the EXACT missing column names")

if st.button("🔍 Show Exact Missing Columns", type="primary", use_container_width=True):

    with st.spinner("Analyzing database..."):
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()

                missing_details = []

                # Check each table
                tables_to_check = {
                    'employees': ['hire_date', 'base_salary', 'role', 'status'],
                    'appraisals': ['overall_rating', 'manager_rating', 'hr_feedback', 'self_achievements', 'manager_id', 'self_review_date', 'created_by', 'hr_reviewer', 'comments', 'manager_comments', 'hr_comments', 'self_areas_improvement', 'self_goals', 'manager_feedback', 'recommendations'],
                    'financial_records': ['overtime_pay', 'payment_type', 'bonus_amount', 'created_at', 'notes'],
                    'training_catalog': ['title', 'category', 'level', 'duration_hours', 'created_by', 'currency', 'delivery_mode', 'prerequisites', 'created_at'],
                    'training_enrollments': ['status', 'approved_by', 'approval_date', 'completion_date', 'score'],
                    'documents': ['visibility', 'category', 'file_name', 'file_size', 'target_department', 'uploaded_by', 'uploaded_at'],
                    'notifications': ['is_read'],
                    'announcements': ['is_pinned', 'status', 'created_by', 'created_at', 'expiry_date'],
                    'insurance': ['status', 'created_at', 'premium_monthly'],
                    'certificates': ['issuing_org', 'verified_by', 'verification_date', 'status'],
                    'exit_process': ['status', 'final_settlement_amount'],
                    'assets': ['status', 'notes'],
                    'skills': ['status', 'level_description'],
                    'goals': ['review_period', 'actual_completion_date', 'final_progress'],
                    'contracts': ['renewal_status', 'created_at', 'updated_at', 'renewal_date'],
                    'compliance': ['verified_by', 'verification_date', 'notes'],
                    'bonuses': ['manager_approved_by', 'manager_approval_date', 'hr_approved_by', 'hr_approval_date', 'hr_comments', 'payment_status', 'payment_date'],
                    'grades': ['status', 'hr_approved_by', 'hr_approval_date', 'hr_comments'],
                    'leave_requests': ['approved_by', 'approval_date', 'created_at'],
                    'expenses': ['approved_by', 'approval_date', 'created_at'],
                    'timesheets': ['approved_by', 'approval_date', 'created_at'],
                    'jobs': ['created_at', 'created_by'],
                    'job_applications': ['candidate_name', 'candidate_email', 'candidate_phone', 'experience_years', 'expected_salary', 'notes', 'created_at', 'status', 'applied_date'],
                    'surveys': ['start_date', 'end_date', 'status'],
                    'onboarding_tasks': ['status', 'completed_date'],
                }

                for table_name, columns_to_check in tables_to_check.items():
                    # Check if table exists
                    cursor.execute(f"""
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables
                            WHERE table_schema = 'public'
                            AND table_name = '{table_name}'
                        );
                    """)
                    table_exists = cursor.fetchone()[0]

                    if not table_exists:
                        missing_details.append({
                            'table': table_name,
                            'issue': 'TABLE_MISSING',
                            'columns': []
                        })
                        continue

                    # Get actual columns
                    cursor.execute(f"""
                        SELECT column_name
                        FROM information_schema.columns
                        WHERE table_name='{table_name}'
                    """)
                    actual_columns = [row['column_name'] for row in cursor.fetchall()]

                    # Check which columns are missing
                    missing_cols = []
                    for col in columns_to_check:
                        if col not in actual_columns:
                            missing_cols.append(col)

                    if missing_cols:
                        missing_details.append({
                            'table': table_name,
                            'issue': 'MISSING_COLUMNS',
                            'columns': missing_cols
                        })

                # Display Results
                st.markdown("---")
                if not missing_details:
                    st.success("🎉 **ALL CLEAR!** No missing columns found.")
                    st.balloons()
                else:
                    st.error(f"### ❌ Found Issues in {len(missing_details)} Tables")

                    for item in missing_details:
                        if item['issue'] == 'TABLE_MISSING':
                            st.error(f"**{item['table']}** - TABLE DOES NOT EXIST")
                        else:
                            st.warning(f"**{item['table']}** - Missing {len(item['columns'])} columns:")
                            for col in item['columns']:
                                st.write(f"  - `{col}`")
                            st.markdown("---")

                    # Generate SQL to fix
                    st.markdown("### 🔧 SQL to Fix Missing Columns:")
                    sql_fixes = []
                    for item in missing_details:
                        if item['issue'] == 'MISSING_COLUMNS':
                            for col in item['columns']:
                                # Guess the column type based on name
                                if col.endswith('_id') or col.endswith('_by'):
                                    col_type = "INTEGER"
                                elif col.endswith('_date'):
                                    col_type = "DATE"
                                elif col.endswith('_at'):
                                    col_type = "TIMESTAMP DEFAULT NOW()"
                                elif col in ['is_read', 'is_pinned']:
                                    col_type = "BOOLEAN DEFAULT FALSE"
                                elif col in ['status', 'role', 'category', 'level', 'title', 'delivery_mode', 'prerequisites', 'currency', 'payment_type', 'visibility', 'file_name', 'target_department', 'payment_status', 'renewal_status', 'review_period']:
                                    col_type = "TEXT"
                                elif col in ['base_salary', 'overtime_pay', 'bonus_amount', 'duration_hours', 'score', 'premium_monthly', 'final_settlement_amount', 'expected_salary']:
                                    col_type = "REAL DEFAULT 0"
                                elif col in ['final_progress', 'file_size', 'experience_years']:
                                    col_type = "INTEGER DEFAULT 0"
                                else:
                                    col_type = "TEXT"

                                sql_fixes.append(f"ALTER TABLE {item['table']} ADD COLUMN IF NOT EXISTS {col} {col_type};")

                    st.code('\n'.join(sql_fixes), language='sql')

        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
            import traceback
            st.code(traceback.format_exc())

else:
    st.markdown("""
    ### This tool will:

    1. Check ALL expected columns in each table
    2. Show you EXACTLY which columns are missing
    3. Generate the SQL needed to fix them

    Click the button above to start the detailed check.
    """)

st.markdown("---")
st.caption("Detailed Health Check v2.0 - Shows Exact Missing Columns")
