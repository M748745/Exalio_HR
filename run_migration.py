"""
Complete Database Migration - Fix All Missing Columns
Run this once to fix all database schema issues
"""

import streamlit as st
from database import get_db_connection

st.title("🔧 Complete Database Migration")
st.warning("⚠️ This will fix ALL missing columns in your database. Run it once.")

if st.button("🚀 Run Complete Migration Now", type="primary"):
    with st.spinner("Running migrations..."):
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                migrations_run = []
                errors = []

                # Migration 1: Add is_read column to notifications table
                st.info("Migration 1: Checking notifications.is_read...")
                try:
                    cursor.execute("""
                        SELECT column_name FROM information_schema.columns
                        WHERE table_name='notifications' AND column_name='is_read'
                    """)
                    if not cursor.fetchone():
                        cursor.execute("ALTER TABLE notifications ADD COLUMN is_read BOOLEAN DEFAULT FALSE")
                        conn.commit()
                        migrations_run.append("✅ Added is_read column to notifications")
                    else:
                        migrations_run.append("ℹ️ is_read column already exists in notifications")
                except Exception as e:
                    errors.append(f"❌ notifications.is_read: {str(e)}")

                # Migration 2: Add is_pinned column to announcements table
                st.info("Migration 2: Checking announcements.is_pinned...")
                try:
                    cursor.execute("""
                        SELECT column_name FROM information_schema.columns
                        WHERE table_name='announcements' AND column_name='is_pinned'
                    """)
                    if not cursor.fetchone():
                        cursor.execute("ALTER TABLE announcements ADD COLUMN is_pinned BOOLEAN DEFAULT FALSE")
                        conn.commit()
                        migrations_run.append("✅ Added is_pinned column to announcements")
                    else:
                        migrations_run.append("ℹ️ is_pinned column already exists in announcements")
                except Exception as e:
                    errors.append(f"❌ announcements.is_pinned: {str(e)}")

                # Migration 3: Add status column to announcements if missing
                st.info("Migration 3: Checking announcements.status...")
                try:
                    cursor.execute("""
                        SELECT column_name FROM information_schema.columns
                        WHERE table_name='announcements' AND column_name='status'
                    """)
                    if not cursor.fetchone():
                        cursor.execute("ALTER TABLE announcements ADD COLUMN status TEXT DEFAULT 'Published'")
                        conn.commit()
                        migrations_run.append("✅ Added status column to announcements")
                    else:
                        migrations_run.append("ℹ️ status column already exists in announcements")
                except Exception as e:
                    errors.append(f"❌ announcements.status: {str(e)}")

                # Migration 4: Add created_by column to announcements if missing
                st.info("Migration 4: Checking announcements.created_by...")
                try:
                    cursor.execute("""
                        SELECT column_name FROM information_schema.columns
                        WHERE table_name='announcements' AND column_name='created_by'
                    """)
                    if not cursor.fetchone():
                        cursor.execute("ALTER TABLE announcements ADD COLUMN created_by INTEGER")
                        conn.commit()
                        migrations_run.append("✅ Added created_by column to announcements")
                    else:
                        migrations_run.append("ℹ️ created_by column already exists in announcements")
                except Exception as e:
                    errors.append(f"❌ announcements.created_by: {str(e)}")

                # Display results
                st.success("🎉 Migration Complete!")

                if migrations_run:
                    st.write("**Migrations executed:**")
                    for msg in migrations_run:
                        st.write(msg)

                if errors:
                    st.error("**Errors encountered:**")
                    for err in errors:
                        st.write(err)

                # Show final schema
                st.info("Verifying announcements table schema...")
                cursor.execute("""
                    SELECT column_name, data_type, column_default
                    FROM information_schema.columns
                    WHERE table_name='announcements'
                    ORDER BY ordinal_position
                """)
                columns = cursor.fetchall()
                st.write("**Announcements table columns:**")
                for col in columns:
                    st.write(f"- {col['column_name']} ({col['data_type']}) - Default: {col['column_default']}")

                st.info("Verifying notifications table schema...")
                cursor.execute("""
                    SELECT column_name, data_type, column_default
                    FROM information_schema.columns
                    WHERE table_name='notifications'
                    ORDER BY ordinal_position
                """)
                columns = cursor.fetchall()
                st.write("**Notifications table columns:**")
                for col in columns:
                    st.write(f"- {col['column_name']} ({col['data_type']}) - Default: {col['column_default']}")

                st.balloons()

        except Exception as e:
            st.error(f"❌ Critical Error: {str(e)}")
            st.code(str(e))

st.markdown("---")
st.info("""
**After running this migration:**
1. All missing columns will be added
2. Reload your main app (refresh the page)
3. All errors should disappear
4. You can delete this file after success
""")

st.markdown("---")
st.caption("If you still see errors after this, click 'Reboot app' in Streamlit Cloud settings")
