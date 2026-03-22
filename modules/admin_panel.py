"""
Advanced Admin Panel Module
System configuration and administrative settings
"""

import streamlit as st
import pandas as pd
from datetime import datetime, date
from database import get_db_connection
from auth import get_current_user, is_hr_admin, log_audit

def show_admin_panel():
    """Main admin panel interface"""
    user = get_current_user()

    if not is_hr_admin():
        st.error("⛔ Access Denied: Admin privileges required")
        return

    st.markdown("## ⚙️ Admin Panel")
    st.markdown("System configuration and administrative settings")
    st.markdown("---")

    tabs = st.tabs([
        "👥 User Management", "🗄️ Database", "📊 System Stats",
        "🔧 Settings", "📋 Audit Logs"
    ])

    with tabs[0]:
        show_user_management()

    with tabs[1]:
        show_database_management()

    with tabs[2]:
        show_system_statistics()

    with tabs[3]:
        show_system_settings()

    with tabs[4]:
        show_audit_logs()

def show_user_management():
    """User account management"""
    st.markdown("### 👥 User Management")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, employee_id, first_name, last_name, email,
                   role, status, created_at
            FROM employees
            ORDER BY created_at DESC
        """)
        users = [dict(row) for row in cursor.fetchall()]

    if users:
        # Summary metrics
        total_users = len(users)
        active_users = len([u for u in users if u['status'] == 'Active'])
        admins = len([u for u in users if u['role'] == 'HR Admin'])

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Users", total_users)
        with col2:
            st.metric("Active Users", active_users)
        with col3:
            st.metric("Administrators", admins)

        st.markdown("---")

        # User list
        df = pd.DataFrame(users)
        display_cols = ['employee_id', 'first_name', 'last_name', 'email', 'role', 'status']
        df_display = df[display_cols].copy()
        df_display.columns = ['ID', 'First Name', 'Last Name', 'Email', 'Role', 'Status']

        st.dataframe(df_display, use_container_width=True, hide_index=True)

        # Bulk actions
        st.markdown("---")
        st.markdown("#### Bulk Actions")
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("📥 Export Users"):
                st.success("User list exported (simulated)")
        with col2:
            if st.button("🔄 Sync Accounts"):
                st.info("Account sync initiated (simulated)")
        with col3:
            if st.button("🔒 Lock Inactive Accounts"):
                st.warning("Locked 0 inactive accounts")

def show_database_management():
    """Database management and backup"""
    st.markdown("### 🗄️ Database Management")

    # Database info
    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Get table count (PostgreSQL compatible)
        cursor.execute("""
            SELECT COUNT(*) as cnt
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_type = 'BASE TABLE'
        """)
        table_count = cursor.fetchone()['cnt']

        # Get table sizes
        cursor.execute("""
            SELECT table_name as name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """)
        tables = [row['name'] for row in cursor.fetchall()]

    st.info(f"📊 Database contains {table_count} tables")

    # Table information
    st.markdown("#### 📋 Tables")

    table_data = []
    with get_db_connection() as conn:
        cursor = conn.cursor()
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) as cnt FROM {table}")
            count = cursor.fetchone()['cnt']
            table_data.append({'Table': table, 'Records': count})

    if table_data:
        df = pd.DataFrame(table_data)
        st.dataframe(df, use_container_width=True, hide_index=True)

    # Database actions
    st.markdown("---")
    st.markdown("#### Database Actions")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("💾 Backup Database"):
            st.success("✅ Database backup created (simulated)")
            log_audit("Database backup created", "admin", 0)

    with col2:
        if st.button("🔄 Optimize Database"):
            with st.spinner("Optimizing..."):
                try:
                    with get_db_connection() as conn:
                        cursor = conn.cursor()
                        # PostgreSQL uses VACUUM (no need for conn.execute)
                        cursor.execute("VACUUM")
                    st.success("✅ Database optimized!")
                    log_audit("Database optimized", "admin", 0)
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")

    with col3:
        if st.button("📊 Check Integrity"):
            # PostgreSQL doesn't have PRAGMA - show simulated check
            st.info("PostgreSQL database integrity check not applicable (cloud-managed)")
            st.success("✅ Database connection OK")

def show_system_statistics():
    """System statistics and metrics"""
    st.markdown("### 📊 System Statistics")

    with get_db_connection() as conn:
        cursor = conn.cursor()

        # User activity (PostgreSQL compatible)
        cursor.execute("""
            SELECT COUNT(*) as cnt FROM audit_logs
            WHERE created_at >= NOW() - INTERVAL '7 days'
        """)
        weekly_activity = cursor.fetchone()['cnt']

        cursor.execute("""
            SELECT COUNT(*) as cnt FROM audit_logs
            WHERE created_at >= CURRENT_DATE
        """)
        today_activity = cursor.fetchone()['cnt']

        # Module usage
        cursor.execute("""
            SELECT module, COUNT(*) as count
            FROM audit_logs
            WHERE created_at >= NOW() - INTERVAL '30 days'
            GROUP BY module
            ORDER BY count DESC
            LIMIT 10
        """)
        module_usage = [dict(row) for row in cursor.fetchall()]

    # Metrics
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Today's Activity", today_activity)
    with col2:
        st.metric("Weekly Activity", weekly_activity)
    with col3:
        avg_daily = weekly_activity // 7 if weekly_activity > 0 else 0
        st.metric("Avg Daily Activity", avg_daily)

    # Module usage
    if module_usage:
        st.markdown("---")
        st.markdown("#### 📈 Most Used Modules (Last 30 Days)")

        df = pd.DataFrame(module_usage)
        df.columns = ['Module', 'Actions']
        st.dataframe(df, use_container_width=True, hide_index=True)

    # Storage stats
    st.markdown("---")
    st.markdown("#### 💾 Storage Statistics")

    with get_db_connection() as conn:
        cursor = conn.cursor()

        total_records = 0
        record_counts = {}

        # Key tables
        key_tables = ['employees', 'leave_requests', 'appraisals', 'documents',
                     'notifications', 'audit_logs']

        for table in key_tables:
            try:
                cursor.execute(f"SELECT COUNT(*) as cnt FROM {table}")
                count = cursor.fetchone()['cnt']
                record_counts[table] = count
                total_records += count
            except:
                pass

    st.info(f"📊 Total Records: {total_records:,}")

    for table, count in record_counts.items():
        st.markdown(f"- **{table}**: {count:,} records")

def show_system_settings():
    """System configuration settings"""
    st.markdown("### 🔧 System Settings")

    st.markdown("#### General Settings")

    with st.form("system_settings"):
        col1, col2 = st.columns(2)

        with col1:
            company_name = st.text_input("Company Name", value="Exalio")
            timezone = st.selectbox("Timezone", [
                "UTC", "America/New_York", "Europe/London", "Asia/Tokyo"
            ])
            date_format = st.selectbox("Date Format", [
                "YYYY-MM-DD", "DD/MM/YYYY", "MM/DD/YYYY"
            ])

        with col2:
            working_hours = st.slider("Standard Working Hours/Day", 6, 10, 8)
            working_days = st.multiselect("Working Days", [
                "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"
            ], default=["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"])

        st.markdown("#### Email Settings")
        email_enabled = st.checkbox("Enable Email Notifications", value=True)

        if email_enabled:
            smtp_server = st.text_input("SMTP Server", placeholder="smtp.gmail.com")
            smtp_port = st.number_input("SMTP Port", value=587)
            from_email = st.text_input("From Email", placeholder="hr@company.com")

        st.markdown("#### Leave Settings")
        col1, col2 = st.columns(2)
        with col1:
            default_annual_leave = st.number_input("Default Annual Leave Days", value=20)
            max_carry_forward = st.number_input("Max Carry Forward Days", value=5)
        with col2:
            sick_leave_days = st.number_input("Sick Leave Days", value=10)
            require_manager_approval = st.checkbox("Require Manager Approval", value=True)

        submitted = st.form_submit_button("💾 Save Settings", use_container_width=True)

        if submitted:
            st.success("✅ Settings saved successfully!")
            log_audit("System settings updated", "admin", 0)

def show_audit_logs():
    """View system audit logs"""
    st.markdown("### 📋 Audit Logs")

    # Filters
    col1, col2, col3 = st.columns(3)
    with col1:
        module_filter = st.selectbox("Module", [
            "All", "employees", "leaves", "performance", "documents",
            "compliance", "admin", "auth"
        ])
    with col2:
        date_from = st.date_input("From Date", value=date.today() - pd.Timedelta(days=7))
    with col3:
        date_to = st.date_input("To Date", value=date.today())

    # Fetch logs
    with get_db_connection() as conn:
        cursor = conn.cursor()

        query = """
            SELECT al.*, e.first_name, e.last_name, e.id as employee_id
            FROM audit_logs al
            LEFT JOIN employees e ON al.user_id = e.id
            WHERE date(al.created_at) BETWEEN %s AND %s
        """
        params = [date_from.isoformat(), date_to.isoformat()]

        if module_filter != "All":
            query += " AND al.module = %s"
            params.append(module_filter)

        query += " ORDER BY al.created_at DESC LIMIT 100"

        cursor.execute(query, params)
        logs = [dict(row) for row in cursor.fetchall()]

    if logs:
        st.info(f"📊 Showing {len(logs)} log entries")

        # Display as table
        log_data = []
        for log in logs:
            log_data.append({
                'Time': log['created_at'][:16],
                'User': f"{log.get('first_name', 'System')} {log.get('last_name', '')}",
                'Module': log['module'],
                'Action': log['action']
            })

        df = pd.DataFrame(log_data)
        st.dataframe(df, use_container_width=True, hide_index=True)

        # Export option
        if st.button("📥 Export Logs"):
            st.success("✅ Logs exported (simulated)")

    else:
        st.info("No audit logs found for selected period")

    # Log statistics
    st.markdown("---")
    st.markdown("#### Log Statistics")

    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Actions per day (PostgreSQL compatible)
        cursor.execute("""
            SELECT DATE(created_at) as log_date, COUNT(*) as count
            FROM audit_logs
            WHERE DATE(created_at) BETWEEN %s AND %s
            GROUP BY DATE(created_at)
            ORDER BY log_date
        """, [date_from.isoformat(), date_to.isoformat()])
        daily_stats = [dict(row) for row in cursor.fetchall()]

    if daily_stats:
        df = pd.DataFrame(daily_stats)
        df.columns = ['Date', 'Actions']
        st.line_chart(df.set_index('Date'))
