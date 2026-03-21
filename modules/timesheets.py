"""
Timesheets Module
Time tracking, submission, and approval workflow
"""

import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
from database import get_db_connection
from auth import get_current_user, is_hr_admin, is_manager, is_employee, create_notification, log_audit

def show_timesheet_management():
    """Main timesheet management interface"""
    user = get_current_user()

    st.markdown("## ⏰ Timesheets")
    st.markdown("Track and manage work hours")
    st.markdown("---")

    if is_hr_admin():
        tabs = st.tabs(["📊 All Timesheets", "⏳ Pending Approval", "📈 Reports", "🔥 Overtime Analytics", "⚙️ Settings"])
    elif is_manager():
        tabs = st.tabs(["📝 My Timesheets", "👥 Team Timesheets", "⏳ Pending Approval", "🔥 Team Overtime"])
    else:
        tabs = st.tabs(["📝 My Timesheets", "➕ Add Entry", "📊 Summary"])

    with tabs[0]:
        if is_hr_admin():
            show_all_timesheets()
        else:
            show_my_timesheets()

    with tabs[1]:
        if is_hr_admin():
            show_pending_approvals()
        elif is_manager():
            show_team_timesheets()
        else:
            show_add_timesheet()

    with tabs[2]:
        if is_hr_admin():
            show_timesheet_reports()
        elif is_manager():
            show_pending_approvals()
        else:
            show_timesheet_summary()

    if len(tabs) > 3:
        with tabs[3]:
            if is_hr_admin():
                show_overtime_analytics()
            elif is_manager():
                show_team_overtime()

    if len(tabs) > 4:
        with tabs[4]:
            show_timesheet_settings()

def show_my_timesheets():
    """Show employee's own timesheets"""
    user = get_current_user()

    st.markdown("### 📝 My Timesheets")

    # Date range filter
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("From", value=date.today() - timedelta(days=30))
    with col2:
        end_date = st.date_input("To", value=date.today())

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM timesheets
            WHERE emp_id = %s AND work_date BETWEEN %s AND %s
            ORDER BY work_date DESC
        """, (user['employee_id'], start_date.isoformat(), end_date.isoformat()))
        timesheets = [dict(row) for row in cursor.fetchall()]

    if timesheets:
        # Summary metrics
        total_hours = sum([t['hours_worked'] for t in timesheets])
        regular_hours = sum([t['regular_hours'] for t in timesheets if t['regular_hours']])
        overtime_hours = sum([t['overtime_hours'] for t in timesheets if t['overtime_hours']])

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Hours", f"{total_hours:.1f}h")
        with col2:
            st.metric("Regular Hours", f"{regular_hours:.1f}h")
        with col3:
            st.metric("Overtime", f"{overtime_hours:.1f}h")

        st.markdown("---")

        # Display timesheets
        for timesheet in timesheets:
            status_color = {
                'Draft': 'rgba(125, 150, 190, 0.1)',
                'Submitted': 'rgba(240, 180, 41, 0.1)',
                'Approved': 'rgba(45, 212, 170, 0.1)',
                'Rejected': 'rgba(241, 100, 100, 0.1)'
            }.get(timesheet['status'], 'rgba(58, 123, 213, 0.05)')

            st.markdown(f"""
                <div style="background: {status_color}; padding: 15px; border-radius: 10px; margin-bottom: 10px;">
                    <strong>📅 {timesheet['work_date']}</strong><br>
                    <small style="color: #7d96be;">
                        Hours: {timesheet['hours_worked']:.1f}h •
                        Regular: {timesheet['regular_hours'] or 0:.1f}h •
                        OT: {timesheet['overtime_hours'] or 0:.1f}h •
                        Status: {timesheet['status']}
                    </small><br>
                    {f"<small>Project: {timesheet['project_name']}</small><br>" if timesheet['project_name'] else ""}
                    {f"<small>Notes: {timesheet['notes']}</small>" if timesheet['notes'] else ""}
                </div>
            """, unsafe_allow_html=True)

            # Allow editing if Draft
            if timesheet['status'] == 'Draft':
                col1, col2, col3 = st.columns([2, 1, 1])
                with col2:
                    if st.button("✏️ Edit", key=f"edit_{timesheet['id']}"):
                        edit_timesheet(timesheet)
                        st.rerun()
                with col3:
                    if st.button("📤 Submit", key=f"submit_{timesheet['id']}"):
                        submit_timesheet(timesheet['id'])
                        st.rerun()
    else:
        st.info("No timesheets for selected period")

def show_add_timesheet():
    """Add new timesheet entry"""
    user = get_current_user()

    st.markdown("### ➕ Add Timesheet Entry")

    with st.form("add_timesheet"):
        work_date = st.date_input("Work Date *", value=date.today(), max_value=date.today())

        col1, col2 = st.columns(2)

        with col1:
            start_time = st.time_input("Start Time", value=datetime.strptime("09:00", "%H:%M").time())
            end_time = st.time_input("End Time", value=datetime.strptime("17:00", "%H:%M").time())

        with col2:
            break_minutes = st.number_input("Break (minutes)", min_value=0, value=30, step=15)
            project_name = st.text_input("Project/Task", placeholder="e.g., Client Project Alpha")

        notes = st.text_area("Notes", placeholder="Describe your work...")

        submitted = st.form_submit_button("💾 Save Entry", use_container_width=True)

        if submitted:
            # Calculate hours
            start_datetime = datetime.combine(work_date, start_time)
            end_datetime = datetime.combine(work_date, end_time)

            if end_datetime <= start_datetime:
                st.error("❌ End time must be after start time")
            else:
                total_minutes = (end_datetime - start_datetime).total_seconds() / 60
                total_minutes -= break_minutes
                hours_worked = total_minutes / 60

                # Calculate regular vs overtime (assuming 8h regular)
                regular_hours = min(hours_worked, 8)
                overtime_hours = max(0, hours_worked - 8)

                create_timesheet_entry(work_date, start_time, end_time, break_minutes,
                                     hours_worked, regular_hours, overtime_hours,
                                     project_name, notes)
                st.rerun()

def show_timesheet_summary():
    """Show personal timesheet summary"""
    user = get_current_user()

    st.markdown("### 📊 My Timesheet Summary")

    # Weekly summary
    week_start = date.today() - timedelta(days=date.today().weekday())
    week_end = week_start + timedelta(days=6)

    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Current week
        cursor.execute("""
            SELECT SUM(hours_worked) as total, SUM(regular_hours) as regular, SUM(overtime_hours) as overtime
            FROM timesheets
            WHERE emp_id = %s AND work_date BETWEEN %s AND %s
        """, (user['employee_id'], week_start.isoformat(), week_end.isoformat()))
        week_data = cursor.fetchone()

        # Current month
        month_start = date.today().replace(day=1)
        cursor.execute("""
            SELECT SUM(hours_worked) as total, SUM(regular_hours) as regular, SUM(overtime_hours) as overtime
            FROM timesheets
            WHERE emp_id = %s AND work_date >= %s
        """, (user['employee_id'], month_start.isoformat()))
        month_data = cursor.fetchone()

    st.markdown("#### This Week")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total", f"{week_data['total'] or 0:.1f}h")
    with col2:
        st.metric("Regular", f"{week_data['regular'] or 0:.1f}h")
    with col3:
        st.metric("Overtime", f"{week_data['overtime'] or 0:.1f}h")

    st.markdown("#### This Month")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total", f"{month_data['total'] or 0:.1f}h")
    with col2:
        st.metric("Regular", f"{month_data['regular'] or 0:.1f}h")
    with col3:
        st.metric("Overtime", f"{month_data['overtime'] or 0:.1f}h")

def show_team_timesheets():
    """Show team timesheets"""
    user = get_current_user()

    st.markdown("### 👥 Team Timesheets")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT t.*, e.first_name, e.last_name, e.employee_id
            FROM timesheets t
            JOIN employees e ON t.emp_id = e.id
            WHERE e.manager_id = %s
            ORDER BY t.work_date DESC
            LIMIT 50
        """, (user['employee_id'],))
        timesheets = [dict(row) for row in cursor.fetchall()]

    if timesheets:
        df = pd.DataFrame(timesheets)
        display_cols = ['work_date', 'employee_id', 'first_name', 'last_name', 'hours_worked', 'overtime_hours', 'status']
        df_display = df[display_cols]
        df_display.columns = ['Date', 'Emp ID', 'First Name', 'Last Name', 'Hours', 'OT', 'Status']

        st.dataframe(df_display, use_container_width=True, hide_index=True)
    else:
        st.info("No team timesheets found")

def show_all_timesheets():
    """Show all timesheets (HR view)"""
    st.markdown("### 📊 All Timesheets")

    # Filters
    col1, col2, col3 = st.columns(3)
    with col1:
        status_filter = st.selectbox("Status", ["All", "Draft", "Submitted", "Approved", "Rejected"])
    with col2:
        start_date = st.date_input("From", value=date.today() - timedelta(days=30))
    with col3:
        end_date = st.date_input("To", value=date.today())

    search = st.text_input("🔍 Search employee")

    with get_db_connection() as conn:
        cursor = conn.cursor()

        query = """
            SELECT t.*, e.first_name, e.last_name, e.employee_id, e.department
            FROM timesheets t
            JOIN employees e ON t.emp_id = e.id
            WHERE t.work_date BETWEEN %s AND %s
        """
        params = [start_date.isoformat(), end_date.isoformat()]

        if status_filter != "All":
            query += " AND t.status = %s"
            params.append(status_filter)

        if search:
            query += " AND (e.first_name LIKE %s OR e.last_name LIKE %s OR e.employee_id LIKE %s)"
            params.extend([f"%{search}%", f"%{search}%", f"%{search}%"])

        query += " ORDER BY t.work_date DESC LIMIT 100"

        cursor.execute(query, params)
        timesheets = [dict(row) for row in cursor.fetchall()]

    if timesheets:
        df = pd.DataFrame(timesheets)
        display_cols = ['work_date', 'employee_id', 'first_name', 'last_name', 'department',
                       'hours_worked', 'regular_hours', 'overtime_hours', 'status']
        df_display = df[display_cols]
        df_display.columns = ['Date', 'Emp ID', 'First Name', 'Last Name', 'Dept', 'Hours', 'Regular', 'OT', 'Status']

        st.dataframe(df_display, use_container_width=True, hide_index=True)

        # Export option
        if st.button("📥 Export to CSV"):
            csv = df_display.to_csv(index=False)
            st.download_button("Download CSV", csv, "timesheets.csv", "text/csv")
    else:
        st.info("No timesheets found")

def show_pending_approvals():
    """Show timesheets pending approval"""
    user = get_current_user()

    st.markdown("### ⏳ Pending Approvals")

    with get_db_connection() as conn:
        cursor = conn.cursor()

        if is_hr_admin():
            # HR can approve all
            cursor.execute("""
                SELECT t.*, e.first_name, e.last_name, e.employee_id
                FROM timesheets t
                JOIN employees e ON t.emp_id = e.id
                WHERE t.status = 'Submitted'
                ORDER BY t.work_date ASC
            """)
        elif is_manager():
            # Manager approves team
            cursor.execute("""
                SELECT t.*, e.first_name, e.last_name, e.employee_id
                FROM timesheets t
                JOIN employees e ON t.emp_id = e.id
                WHERE e.manager_id = %s AND t.status = 'Submitted'
                ORDER BY t.work_date ASC
            """, (user['employee_id'],))
        else:
            st.info("No approvals available")
            return

        pending = [dict(row) for row in cursor.fetchall()]

    if pending:
        st.info(f"📋 {len(pending)} timesheet(s) awaiting approval")

        for timesheet in pending:
            has_overtime = timesheet['overtime_hours'] and timesheet['overtime_hours'] > 0

            # Highlight entries with overtime
            expander_label = f"⏰ {timesheet['first_name']} {timesheet['last_name']} - {timesheet['work_date']} ({timesheet['hours_worked']:.1f}h)"
            if has_overtime:
                expander_label = f"🔥 {expander_label} - **OVERTIME: {timesheet['overtime_hours']:.1f}h**"

            with st.expander(expander_label):
                col1, col2 = st.columns([2, 1])

                with col1:
                    st.markdown(f"""
                    **Employee:** {timesheet['first_name']} {timesheet['last_name']} ({timesheet['employee_id']})
                    **Date:** {timesheet['work_date']}
                    **Hours Worked:** {timesheet['hours_worked']:.1f}h
                    **Regular Hours:** {timesheet['regular_hours'] or 0:.1f}h
                    **Overtime:** {timesheet['overtime_hours'] or 0:.1f}h
                    **Start:** {timesheet['start_time']}
                    **End:** {timesheet['end_time']}
                    **Break:** {timesheet['break_minutes']} minutes
                    """)

                with col2:
                    st.metric("Total Hours", f"{timesheet['hours_worked']:.1f}h")
                    if has_overtime:
                        st.metric("⚠️ OT Hours", f"{timesheet['overtime_hours']:.1f}h",
                                 delta=f"{timesheet['overtime_hours']:.1f}h over regular",
                                 delta_color="inverse")

                if timesheet['project_name']:
                    st.info(f"**Project:** {timesheet['project_name']}")

                if timesheet['notes']:
                    st.info(f"**Notes:** {timesheet['notes']}")

                # Show overtime warning and justification requirement
                if has_overtime:
                    st.warning(f"⚠️ **Overtime Detected:** {timesheet['overtime_hours']:.1f} hours")
                    st.markdown(f"""
                    <div style="background: rgba(255, 193, 7, 0.1); padding: 10px; border-radius: 5px; border-left: 4px solid #ffc107;">
                        <strong>Overtime Rate:</strong> 1.5x regular rate<br>
                        <strong>Estimated OT Cost:</strong> Additional compensation will be processed
                    </div>
                    """, unsafe_allow_html=True)

                    overtime_justification = st.text_area(
                        "Overtime Justification (Required for approval)",
                        key=f"ot_just_{timesheet['id']}",
                        placeholder="Explain why overtime was necessary and approved..."
                    )

                # Approval actions
                st.markdown("---")
                col1, col2 = st.columns(2)

                with col1:
                    approve_label = "✅ Approve (with OT)" if has_overtime else "✅ Approve"
                    can_approve = True

                    if has_overtime and is_manager():
                        # Manager must provide justification for OT
                        if 'overtime_justification' in locals() and not overtime_justification:
                            can_approve = False
                            st.caption("⚠️ Justification required for overtime approval")

                    if st.button(approve_label, key=f"approve_ts_{timesheet['id']}",
                               use_container_width=True, disabled=not can_approve):
                        ot_just = overtime_justification if has_overtime and 'overtime_justification' in locals() else None
                        approve_timesheet(timesheet['id'], timesheet['emp_id'],
                                        timesheet['overtime_hours'], ot_just)
                        st.rerun()

                with col2:
                    if st.button("❌ Reject", key=f"reject_ts_{timesheet['id']}", use_container_width=True):
                        reject_timesheet(timesheet['id'], timesheet['emp_id'])
                        st.rerun()
    else:
        st.success("✅ No timesheets pending approval!")

def show_timesheet_reports():
    """Show timesheet reports and analytics"""
    st.markdown("### 📈 Timesheet Reports")

    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Total hours by department
        cursor.execute("""
            SELECT e.department, SUM(t.hours_worked) as total_hours, SUM(t.overtime_hours) as total_overtime
            FROM timesheets t
            JOIN employees e ON t.emp_id = e.id
            WHERE t.status = 'Approved'
            GROUP BY e.department
            ORDER BY total_hours DESC
        """)
        dept_data = [dict(row) for row in cursor.fetchall()]

    if dept_data:
        st.markdown("### 📊 Hours by Department")
        for dept in dept_data:
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                st.markdown(f"**{dept['department']}**")
            with col2:
                st.markdown(f"{dept['total_hours']:,.1f}h")
            with col3:
                st.markdown(f"OT: {dept['total_overtime'] or 0:,.1f}h")
    else:
        st.info("No timesheet data available")

def show_timesheet_settings():
    """Timesheet settings for HR"""
    st.markdown("### ⚙️ Timesheet Settings")

    st.info("⚙️ Settings configuration coming soon")

    st.markdown("""
    **Planned Settings:**
    - Regular hours per day (default: 8h)
    - Overtime calculation rules
    - Approval workflow configuration
    - Submission deadlines
    - Required fields
    """)

def create_timesheet_entry(work_date, start_time, end_time, break_minutes,
                          hours_worked, regular_hours, overtime_hours,
                          project_name, notes):
    """Create new timesheet entry"""
    user = get_current_user()

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO timesheets (
                    emp_id, work_date, start_time, end_time, break_minutes,
                    hours_worked, regular_hours, overtime_hours,
                    project_name, notes, status
                ) VALUES (%s, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Draft')
            """, (user['employee_id'], work_date.isoformat(),
                 start_time.strftime("%H:%M"), end_time.strftime("%H:%M"),
                 break_minutes, hours_worked, regular_hours, overtime_hours,
                 project_name, notes))

            timesheet_id = cursor.lastrowid

            conn.commit()
            log_audit(f"Created timesheet entry for {work_date}", "timesheets", timesheet_id)
            st.success(f"✅ Timesheet entry saved! ID: TS-{timesheet_id}")

    except Exception as e:
        st.error(f"❌ Error: {str(e)}")

def submit_timesheet(timesheet_id):
    """Submit timesheet for approval"""
    user = get_current_user()

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("UPDATE timesheets SET status = 'Submitted' WHERE id = %s", (timesheet_id,))

            # Notify manager
            cursor.execute("SELECT manager_id FROM employees WHERE id = %s", (user['employee_id'],))
            result = cursor.fetchone()

            if result and result['manager_id']:
                create_notification(
                    result['manager_id'],
                    "Timesheet Submitted",
                    f"{user['full_name']} submitted a timesheet for approval (TS-{timesheet_id}).",
                    'info'
                )

            conn.commit()
            log_audit(f"Submitted timesheet {timesheet_id}", "timesheets", timesheet_id)
            st.success("✅ Timesheet submitted for approval!")

    except Exception as e:
        st.error(f"❌ Error: {str(e)}")

def approve_timesheet(timesheet_id, emp_id, overtime_hours=None, overtime_justification=None):
    """Approve timesheet with overtime processing"""
    user = get_current_user()

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # Get timesheet details for overtime processing
            cursor.execute("""
                SELECT t.*, e.base_salary
                FROM timesheets t
                JOIN employees e ON t.emp_id = e.id
                WHERE t.id = %s
            """, (timesheet_id,))
            timesheet = dict(cursor.fetchone())

            # Update timesheet status
            cursor.execute("""
                UPDATE timesheets SET
                    status = 'Approved',
                    approved_by = %s,
                    approval_date = %s,
                    overtime_approved = %s,
                    overtime_justification = %s
                WHERE id = %s
            """, (user['employee_id'], datetime.now().isoformat(),
                 'Yes' if overtime_hours and overtime_hours > 0 else 'No',
                 overtime_justification, timesheet_id))

            # Process overtime payment if applicable
            if overtime_hours and overtime_hours > 0:
                # Calculate overtime pay
                # Assuming base_salary is monthly, calculate hourly rate
                # Monthly salary / 160 hours (approx 20 days * 8 hours) = hourly rate
                # Overtime rate = 1.5x hourly rate
                monthly_salary = timesheet.get('base_salary', 0)
                if monthly_salary:
                    hourly_rate = monthly_salary / 160  # Standard monthly hours
                    overtime_rate = hourly_rate * 1.5
                    overtime_payment = overtime_hours * overtime_rate

                    # Create financial record for overtime payment
                    cursor.execute("""
                        INSERT INTO financial_records (
                            emp_id, overtime_pay, payment_type, period, notes
                        ) VALUES (%s, %s, %s, %s, %s)
                    """, (emp_id, overtime_payment, 'Overtime Payment',
                         datetime.now().strftime("%Y-%m"),
                         f"Overtime approval for TS-{timesheet_id}: {overtime_hours:.1f}h @ {overtime_rate:.2f}/h. Justification: {overtime_justification or 'N/A'}"))

                    overtime_msg = f" with {overtime_hours:.1f}h overtime (${overtime_payment:.2f} compensation processed)"
                    log_audit(f"Approved timesheet {timesheet_id} with overtime: {overtime_hours:.1f}h, payment: ${overtime_payment:.2f}", "timesheets", timesheet_id)
                else:
                    overtime_msg = f" with {overtime_hours:.1f}h overtime (salary info unavailable for payment calculation)"
                    log_audit(f"Approved timesheet {timesheet_id} with overtime: {overtime_hours:.1f}h (no payment - salary missing)", "timesheets", timesheet_id)
            else:
                overtime_msg = ""
                log_audit(f"Approved timesheet {timesheet_id}", "timesheets", timesheet_id)

            # Notify employee
            notification_msg = f"Your timesheet (TS-{timesheet_id}) has been approved{overtime_msg}."
            create_notification(
                emp_id,
                "Timesheet Approved",
                notification_msg,
                'success'
            )

            conn.commit()
            st.success(f"✅ Timesheet approved{overtime_msg}!")

    except Exception as e:
        st.error(f"❌ Error: {str(e)}")

def reject_timesheet(timesheet_id, emp_id):
    """Reject timesheet"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("UPDATE timesheets SET status = 'Rejected' WHERE id = %s", (timesheet_id,))

            create_notification(
                emp_id,
                "Timesheet Rejected",
                f"Your timesheet (TS-{timesheet_id}) was rejected. Please review and resubmit.",
                'warning'
            )

            conn.commit()
            log_audit(f"Rejected timesheet {timesheet_id}", "timesheets", timesheet_id)
            st.warning("⚠️ Timesheet rejected")

    except Exception as e:
        st.error(f"❌ Error: {str(e)}")

def edit_timesheet(timesheet):
    """Edit existing timesheet"""
    st.info("⚙️ Edit functionality coming soon")

def show_overtime_analytics():
    """Show overtime analytics for HR"""
    st.markdown("### 🔥 Overtime Analytics")

    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Total overtime stats
        cursor.execute("""
            SELECT
                COUNT(*) as total_entries,
                SUM(overtime_hours) as total_ot_hours,
                COUNT(DISTINCT emp_id) as employees_with_ot,
                SUM(CASE WHEN overtime_approved = 'Yes' THEN overtime_hours ELSE 0 END) as approved_ot_hours
            FROM timesheets
            WHERE overtime_hours > 0 AND status = 'Approved'
        """)
        stats = dict(cursor.fetchone())

        # Display overview metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total OT Entries", stats['total_entries'] or 0)
        with col2:
            st.metric("Total OT Hours", f"{stats['total_ot_hours'] or 0:.1f}h")
        with col3:
            st.metric("Employees with OT", stats['employees_with_ot'] or 0)
        with col4:
            st.metric("Approved OT Hours", f"{stats['approved_ot_hours'] or 0:.1f}h")

        st.markdown("---")

        # Department-wise overtime
        st.markdown("#### 📊 Overtime by Department")
        cursor.execute("""
            SELECT
                e.department,
                COUNT(*) as ot_entries,
                SUM(t.overtime_hours) as total_ot,
                AVG(t.overtime_hours) as avg_ot,
                SUM(CASE WHEN t.overtime_approved = 'Yes' THEN 1 ELSE 0 END) as approved_count
            FROM timesheets t
            JOIN employees e ON t.emp_id = e.id
            WHERE t.overtime_hours > 0 AND t.status = 'Approved'
            GROUP BY e.department
            ORDER BY total_ot DESC
        """)
        dept_ot = [dict(row) for row in cursor.fetchall()]

        if dept_ot:
            for dept in dept_ot:
                with st.expander(f"📌 {dept['department']} - {dept['total_ot']:.1f}h total"):
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("OT Entries", dept['ot_entries'])
                    with col2:
                        st.metric("Avg OT/Entry", f"{dept['avg_ot']:.1f}h")
                    with col3:
                        st.metric("Approved", dept['approved_count'])
        else:
            st.info("No overtime data available")

        st.markdown("---")

        # Top employees by overtime
        st.markdown("#### 👥 Top 10 Employees by Overtime")
        cursor.execute("""
            SELECT
                e.employee_id,
                e.first_name || ' ' || e.last_name as name,
                e.department,
                COUNT(*) as ot_entries,
                SUM(t.overtime_hours) as total_ot,
                AVG(t.overtime_hours) as avg_ot
            FROM timesheets t
            JOIN employees e ON t.emp_id = e.id
            WHERE t.overtime_hours > 0 AND t.status = 'Approved'
            GROUP BY e.id, e.employee_id, e.first_name, e.last_name, e.department
            ORDER BY total_ot DESC
            LIMIT 10
        """)
        top_employees = [dict(row) for row in cursor.fetchall()]

        if top_employees:
            for idx, emp in enumerate(top_employees, 1):
                st.markdown(f"""
                **{idx}. {emp['name']}** ({emp['employee_id']}) - {emp['department']}
                - Total OT: **{emp['total_ot']:.1f}h** | Entries: {emp['ot_entries']} | Avg: {emp['avg_ot']:.1f}h
                """)
        else:
            st.info("No overtime data available")

def show_team_overtime():
    """Show team overtime for managers"""
    user = get_current_user()
    st.markdown("### 🔥 Team Overtime Summary")

    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Team overtime stats
        cursor.execute("""
            SELECT
                e.employee_id,
                e.first_name || ' ' || e.last_name as name,
                COUNT(*) as ot_entries,
                SUM(t.overtime_hours) as total_ot,
                SUM(CASE WHEN t.overtime_approved = 'Yes' THEN t.overtime_hours ELSE 0 END) as approved_ot
            FROM timesheets t
            JOIN employees e ON t.emp_id = e.id
            WHERE e.manager_id = %s AND t.overtime_hours > 0 AND t.status = 'Approved'
            GROUP BY e.id, e.employee_id, e.first_name, e.last_name
            ORDER BY total_ot DESC
        """, (user['employee_id'],))
        team_ot = [dict(row) for row in cursor.fetchall()]

        if team_ot:
            total_team_ot = sum([emp['total_ot'] for emp in team_ot])
            total_approved_ot = sum([emp['approved_ot'] for emp in team_ot])

            col1, col2 = st.columns(2)
            with col1:
                st.metric("Total Team OT", f"{total_team_ot:.1f}h")
            with col2:
                st.metric("Approved Team OT", f"{total_approved_ot:.1f}h")

            st.markdown("---")
            st.markdown("#### Team Members")

            for emp in team_ot:
                with st.expander(f"👤 {emp['name']} ({emp['employee_id']}) - {emp['total_ot']:.1f}h"):
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("OT Entries", emp['ot_entries'])
                    with col2:
                        st.metric("Total OT", f"{emp['total_ot']:.1f}h")
                    with col3:
                        st.metric("Approved OT", f"{emp['approved_ot']:.1f}h")
        else:
            st.info("No team overtime recorded")
