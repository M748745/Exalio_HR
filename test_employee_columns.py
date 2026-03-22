"""
Quick test to check employees table columns
"""
import streamlit as st
from database import get_db_connection

st.title("🔍 Employee Table Column Test")

if st.button("Test Query"):
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # Show all columns in employees table
            cursor.execute("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'employees'
                ORDER BY column_name
            """)
            cols = [row['column_name'] for row in cursor.fetchall()]

            st.success(f"Found {len(cols)} columns in employees table:")
            st.write(cols)

            # Check if employee_id exists
            if 'employee_id' in cols:
                st.success("✅ employee_id column EXISTS")

                # Try to select it
                cursor.execute("SELECT id, employee_id FROM employees LIMIT 1")
                result = cursor.fetchone()
                if result:
                    st.success(f"✅ Can SELECT employee_id: {dict(result)}")
            else:
                st.error("❌ employee_id column DOES NOT EXIST")

            # Try the problematic query
            st.markdown("---")
            st.write("Testing the actual assets query...")
            cursor.execute("""
                SELECT a.*, e.first_name, e.last_name, e.employee_id, e.department
                FROM assets a
                LEFT JOIN employees e ON a.assigned_to = e.id
                LIMIT 1
            """)
            result = cursor.fetchone()
            if result:
                st.success("✅ Assets query works!")
                st.write(dict(result))
            else:
                st.info("No results (no assets assigned)")

    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
        import traceback
        st.code(traceback.format_exc())
