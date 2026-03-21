"""
Emergency Migration Runner
Add this to your app temporarily to run the migration
"""

import streamlit as st
from database import get_db_connection

st.title("🔧 Emergency Database Migration")
st.warning("This is a one-time migration script. Run it once to fix the database.")

if st.button("🚀 Run Migration Now"):
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # Check if column exists
            st.info("Checking if is_read column exists...")
            cursor.execute("""
                SELECT column_name FROM information_schema.columns
                WHERE table_name='notifications' AND column_name='is_read'
            """)

            if cursor.fetchone():
                st.success("✅ is_read column already exists! No migration needed.")
            else:
                # Add the column
                st.info("Adding is_read column to notifications table...")
                cursor.execute("""
                    ALTER TABLE notifications
                    ADD COLUMN is_read BOOLEAN DEFAULT FALSE
                """)
                conn.commit()
                st.success("✅ Successfully added is_read column!")
                st.balloons()

            st.info("Verifying column...")
            cursor.execute("""
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_name='notifications'
                ORDER BY ordinal_position
            """)

            columns = cursor.fetchall()
            st.write("**Notifications table columns:**")
            for col in columns:
                st.write(f"- {col['column_name']} ({col['data_type']})")

    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
        st.code(str(e))

st.markdown("---")
st.info("""
**After running this migration:**
1. The is_read column will be added
2. Reload your main app
3. The error should disappear
4. You can delete this file after
""")
