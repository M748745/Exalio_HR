"""
Compliance Tracking Module
Track compliance requirements, deadlines, and completion status
"""

import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
from database import get_db_connection
from auth import get_current_user, is_hr_admin, is_manager, create_notification, log_audit

def show_compliance_tracking():
    """Main compliance tracking interface"""
    user = get_current_user()

    st.markdown("## 📋 Compliance Tracking")
    st.markdown("Monitor regulatory compliance, deadlines, and completion status")
    st.markdown("---")

    if is_hr_admin():
        tabs = st.tabs(["📊 All Compliance", "⚠️ Overdue Items", "📅 Upcoming Deadlines", "➕ Add Requirement", "📊 Analytics"])
    elif is_manager():
        tabs = st.tabs(["📋 My Compliance", "👥 Team Compliance", "⚠️ Alerts"])
    else:
        tabs = st.tabs(["📋 My Compliance", "⚠️ Pending Items"])

    with tabs[0]:
        if is_hr_admin():
            show_all_compliance()
        elif is_manager():
            show_manager_compliance()
        else:
            show_employee_compliance()

    with tabs[1]:
        if is_hr_admin():
            show_overdue_compliance()
        elif is_manager():
            show_team_compliance()
        else:
            show_pending_items()

    if is_hr_admin() and len(tabs) > 2:
        with tabs[2]:
            show_upcoming_deadlines()
        with tabs[3]:
            add_compliance_requirement()
        with tabs[4]:
            show_compliance_analytics()
    elif is_manager() and len(tabs) > 2:
        with tabs[2]:
            show_compliance_alerts()

def show_all_compliance():
    """Show all compliance requirements"""
    st.markdown("### 📊 All Compliance Requirements")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT c.*, e.first_name, e.last_name, e.department
            FROM compliance c
            JOIN employees e ON c.emp_id = e.id
            ORDER BY c.due_date, c.status
        """)
        requirements = [dict(row) for row in cursor.fetchall()]

    if requirements:
        for req in requirements:
            days_remaining = (datetime.strptime(str(req['due_date']), '%Y-%m-%d').date() - date.today()).days if req['due_date'] else 999
            status_icon = '✅' if req['status'] == 'Completed' else '🔴' if days_remaining < 0 else '🟡' if days_remaining <= 30 else '🟢'

            with st.expander(f"{status_icon} {req['first_name']} {req['last_name']} - {req['requirement_name']} - {req['status']}"):
                col1, col2 = st.columns([2, 1])
                with col1:
                    st.write(f"**Department:** {req['department']}")
                    st.write(f"**Type:** {req['requirement_type']}")
                    st.write(f"**Due Date:** {req['due_date']}")
                    if req['completion_date']:
                        st.write(f"**Completed:** {req['completion_date']}")
                with col2:
                    st.metric("Status", req['status'])
                    if days_remaining >= 0:
                        st.metric("Days Until Due", days_remaining)
                    else:
                        st.metric("Days Overdue", abs(days_remaining))

                if req['certificate_path']:
                    st.info(f"Certificate: {req['certificate_path']}")

                if req['status'] != 'Completed':
                    if st.button(f"✅ Mark Complete - {req['id']}", key=f"complete_{req['id']}"):
                        with get_db_connection() as conn:
                            cursor = conn.cursor()
                            cursor.execute("""
                                UPDATE compliance SET
                                    status = 'Completed',
                                    completion_date = %s
                                WHERE id = %s
                            """, (date.today().isoformat(), req['id']))
                            conn.commit()
                            create_notification(req['emp_id'], "Compliance Completed",
                                              f"Your compliance requirement '{req['requirement_name']}' has been marked complete", "success")
                            st.success("✅ Marked as complete!")
                            st.rerun()
    else:
        st.info("No compliance requirements found")

def add_compliance_requirement():
    """Add new compliance requirement"""
    st.markdown("### ➕ Add Compliance Requirement")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, first_name, last_name, department FROM employees WHERE status = 'Active' ORDER BY first_name")
        employees = [dict(row) for row in cursor.fetchall()]

    if employees:
        with st.form("add_compliance"):
            employee_options = {f"{e['first_name']} {e['last_name']} - {e['department']}": e['id'] for e in employees}
            selected_employee = st.selectbox("Employee *", list(employee_options.keys()))

            col1, col2 = st.columns(2)
            with col1:
                requirement_name = st.text_input("Requirement Name *")
                requirement_type = st.selectbox("Type *", ["Regulatory", "Safety", "Training", "Certification", "Policy", "Audit", "Other"])
            with col2:
                due_date = st.date_input("Due Date *")

            submitted = st.form_submit_button("💾 Add Requirement")

            if submitted and selected_employee and requirement_name:
                emp_id = employee_options[selected_employee]
                with get_db_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT INTO compliance (emp_id, requirement_name, requirement_type, due_date, status)
                        VALUES (%s, %s, %s, %s, 'Pending')
                    """, (emp_id, requirement_name, requirement_type, due_date))
                    conn.commit()
                    create_notification(emp_id, "New Compliance Requirement",
                                      f"New requirement assigned: {requirement_name}. Due: {due_date}", "warning")
                    log_audit(get_current_user()['id'], f"Added compliance requirement: {requirement_name}", "compliance")
                    st.success("✅ Compliance requirement added!")

def show_overdue_compliance():
    """Show overdue compliance items"""
    st.markdown("### ⚠️ Overdue Compliance Items")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT c.*, e.first_name, e.last_name, e.department
            FROM compliance c
            JOIN employees e ON c.emp_id = e.id
            WHERE c.status != 'Completed' AND c.due_date < CURRENT_DATE
            ORDER BY c.due_date
        """)
        overdue = [dict(row) for row in cursor.fetchall()]

    if overdue:
        st.warning(f"⚠️ {len(overdue)} overdue items found!")
        for item in overdue:
            days_overdue = (date.today() - datetime.strptime(str(item['due_date']), '%Y-%m-%d').date()).days
            st.error(f"🔴 {item['first_name']} {item['last_name']} - {item['requirement_name']} - {days_overdue} days overdue")
    else:
        st.success("✅ No overdue compliance items!")

def show_upcoming_deadlines():
    """Show upcoming compliance deadlines"""
    st.markdown("### 📅 Upcoming Deadlines (Next 30 Days)")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT c.*, e.first_name, e.last_name, e.department
            FROM compliance c
            JOIN employees e ON c.emp_id = e.id
            WHERE c.status != 'Completed'
              AND c.due_date >= CURRENT_DATE
              AND c.due_date <= CURRENT_DATE + INTERVAL '30 days'
            ORDER BY c.due_date
        """)
        upcoming = [dict(row) for row in cursor.fetchall()]

    if upcoming:
        for item in upcoming:
            days_remaining = (datetime.strptime(str(item['due_date']), '%Y-%m-%d').date() - date.today()).days
            color = '🟡' if days_remaining <= 7 else '🟢'
            st.write(f"{color} {item['first_name']} {item['last_name']} - {item['requirement_name']} - Due in {days_remaining} days ({item['due_date']})")
    else:
        st.info("No upcoming deadlines in the next 30 days")

def show_manager_compliance():
    """Show manager's compliance"""
    user = get_current_user()
    st.markdown("### 📋 My Compliance Requirements")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM compliance
            WHERE emp_id = %s
            ORDER BY due_date
        """, (user['employee_id'],))
        requirements = [dict(row) for row in cursor.fetchall()]

    if requirements:
        for req in requirements:
            status_icon = '✅' if req['status'] == 'Completed' else '🟡'
            st.write(f"{status_icon} {req['requirement_name']} - {req['requirement_type']} - Due: {req['due_date']} - Status: {req['status']}")
    else:
        st.info("No compliance requirements")

def show_team_compliance():
    """Show team compliance status"""
    user = get_current_user()
    st.markdown("### 👥 Team Compliance")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT department FROM employees WHERE id = %s", (user['employee_id'],))
        dept_row = cursor.fetchone()

        if dept_row:
            dept = dept_row['department']
            cursor.execute("""
                SELECT c.*, e.first_name, e.last_name
                FROM compliance c
                JOIN employees e ON c.emp_id = e.id
                WHERE e.department = %s
                ORDER BY c.due_date
            """, (dept,))
            requirements = [dict(row) for row in cursor.fetchall()]

            if requirements:
                for req in requirements:
                    status_icon = '✅' if req['status'] == 'Completed' else '🔴' if req['due_date'] < str(date.today()) else '🟡'
                    st.write(f"{status_icon} {req['first_name']} {req['last_name']} - {req['requirement_name']} - {req['status']}")

def show_employee_compliance():
    """Show employee compliance"""
    user = get_current_user()
    st.markdown("### 📋 My Compliance Requirements")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM compliance
            WHERE emp_id = %s
            ORDER BY due_date
        """, (user['employee_id'],))
        requirements = [dict(row) for row in cursor.fetchall()]

    if requirements:
        for req in requirements:
            days_remaining = (datetime.strptime(str(req['due_date']), '%Y-%m-%d').date() - date.today()).days if req['due_date'] else 999
            status_icon = '✅' if req['status'] == 'Completed' else '🔴' if days_remaining < 0 else '🟡'

            with st.expander(f"{status_icon} {req['requirement_name']} - {req['status']}"):
                st.write(f"**Type:** {req['requirement_type']}")
                st.write(f"**Due Date:** {req['due_date']}")
                if days_remaining >= 0 and req['status'] != 'Completed':
                    st.warning(f"⏰ {days_remaining} days remaining")
                elif days_remaining < 0 and req['status'] != 'Completed':
                    st.error(f"⚠️ {abs(days_remaining)} days overdue!")

                if req['status'] == 'Completed':
                    st.success(f"✅ Completed on {req['completion_date']}")

def show_pending_items():
    """Show pending compliance items"""
    user = get_current_user()
    st.markdown("### ⚠️ Pending Items")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM compliance
            WHERE emp_id = %s AND status != 'Completed'
            ORDER BY due_date
        """, (user['employee_id'],))
        pending = [dict(row) for row in cursor.fetchall()]

    if pending:
        for item in pending:
            days_remaining = (datetime.strptime(str(item['due_date']), '%Y-%m-%d').date() - date.today()).days
            urgency = '🔴 Urgent!' if days_remaining < 7 else '🟡 Due Soon' if days_remaining < 30 else '🟢 On Track'
            st.write(f"{urgency} {item['requirement_name']} - Due: {item['due_date']} ({days_remaining} days)")
    else:
        st.success("✅ All compliance items complete!")

def show_compliance_alerts():
    """Show compliance alerts for managers"""
    st.markdown("### ⚠️ Team Compliance Alerts")
    st.info("Monitor team compliance status and upcoming deadlines")

def show_compliance_analytics():
    """Show compliance analytics"""
    st.markdown("### 📊 Compliance Analytics")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN status = 'Completed' THEN 1 ELSE 0 END) as completed,
                SUM(CASE WHEN due_date < CURRENT_DATE AND status != 'Completed' THEN 1 ELSE 0 END) as overdue
            FROM compliance
        """)
        stats = dict(cursor.fetchone())

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Requirements", stats['total'] or 0)
        with col2:
            st.metric("Completed", stats['completed'] or 0)
        with col3:
            st.metric("Overdue", stats['overdue'] or 0)

        completion_rate = (stats['completed'] / stats['total'] * 100) if stats['total'] > 0 else 0
        st.metric("Completion Rate", f"{completion_rate:.1f}%")
        st.progress(completion_rate / 100)
