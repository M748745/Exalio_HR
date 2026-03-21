"""
Performance Improvement Plan (PIP) Execution Module
Create PIPs, track goals, monitor progress, and document outcomes
"""

import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
from database import get_db_connection
from auth import get_current_user, is_hr_admin, is_manager, create_notification, log_audit

def show_pip_execution():
    """Main PIP execution interface"""
    user = get_current_user()

    st.markdown("## 📈 Performance Improvement Plans (PIP)")
    st.markdown("Track and manage performance improvement initiatives")
    st.markdown("---")

    if is_hr_admin():
        tabs = st.tabs(["📊 All PIPs", "➕ Create PIP", "📅 Active PIPs", "📊 PIP Analytics"])
    elif is_manager():
        tabs = st.tabs(["👥 Team PIPs", "➕ Initiate PIP", "📋 PIP Reviews"])
    else:
        tabs = st.tabs(["📋 My PIP", "📈 My Progress"])

    with tabs[0]:
        if is_hr_admin():
            show_all_pips()
        elif is_manager():
            show_team_pips()
        else:
            show_my_pip()

    if is_hr_admin() and len(tabs) > 1:
        with tabs[1]:
            create_pip()
        with tabs[2]:
            show_active_pips()
        with tabs[3]:
            show_pip_analytics()
    elif is_manager() and len(tabs) > 1:
        with tabs[1]:
            initiate_pip()
        with tabs[2]:
            show_pip_reviews()
    elif not is_hr_admin() and not is_manager() and len(tabs) > 1:
        with tabs[1]:
            show_pip_progress()

def show_all_pips():
    """Show all PIPs"""
    st.markdown("### 📊 All Performance Improvement Plans")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT p.*, e.first_name, e.last_name, e.department, e.position
            FROM pips p
            JOIN employees e ON p.emp_id = e.id
            ORDER BY p.start_date DESC
        """)
        pips = [dict(row) for row in cursor.fetchall()]

    if pips:
        for pip in pips:
            status_icon = '✅' if pip['status'] == 'Successful' else '🔴' if pip['status'] == 'Unsuccessful' else '🟡'

            with st.expander(f"{status_icon} {pip['first_name']} {pip['last_name']} - {pip['department']} - {pip['status']}"):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Position:** {pip['position']}")
                    st.write(f"**Start Date:** {pip['start_date']}")
                    st.write(f"**End Date:** {pip['end_date']}")
                    st.write(f"**Status:** {pip['status']}")
                with col2:
                    if pip['review_frequency']:
                        st.write(f"**Review Frequency:** {pip['review_frequency']}")
                    if pip['outcome']:
                        st.write(f"**Outcome:** {pip['outcome']}")

                if pip['performance_issues']:
                    st.markdown("**Performance Issues:**")
                    st.info(pip['performance_issues'])

                if pip['improvement_goals']:
                    st.markdown("**Improvement Goals:**")
                    st.warning(pip['improvement_goals'])

                if pip['support_resources']:
                    st.markdown("**Support & Resources:**")
                    st.success(pip['support_resources'])

                # Progress updates
                with get_db_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT * FROM pip_progress
                        WHERE pip_id = %s
                        ORDER BY review_date DESC
                    """, (pip['id'],))
                    progress_updates = [dict(row) for row in cursor.fetchall()]

                if progress_updates:
                    st.markdown("**Progress Updates:**")
                    for update in progress_updates:
                        st.write(f"📅 {update['review_date']}: {update['status']} - {update['notes']}")
    else:
        st.info("No PIPs in the system")

def create_pip():
    """Create new PIP"""
    st.markdown("### ➕ Create Performance Improvement Plan")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, first_name, last_name, department, position
            FROM employees WHERE status = 'Active'
            ORDER BY first_name
        """)
        employees = [dict(row) for row in cursor.fetchall()]

    if employees:
        with st.form("create_pip"):
            emp_options = {f"{e['first_name']} {e['last_name']} - {e['position']} ({e['department']})": e['id'] for e in employees}
            selected_employee = st.selectbox("Select Employee *", list(emp_options.keys()))

            col1, col2 = st.columns(2)
            with col1:
                start_date = st.date_input("PIP Start Date *", value=date.today())
                duration_days = st.number_input("Duration (days) *", min_value=30, max_value=180, value=90)
            with col2:
                end_date = start_date + timedelta(days=duration_days)
                st.write(f"**End Date:** {end_date}")
                review_frequency = st.selectbox("Review Frequency *", ["Weekly", "Bi-weekly", "Monthly"])

            performance_issues = st.text_area("Performance Issues & Concerns *",
                                             placeholder="Describe specific performance issues that led to this PIP...")

            improvement_goals = st.text_area("Improvement Goals & Expectations *",
                                            placeholder="Define clear, measurable goals for improvement...")

            success_criteria = st.text_area("Success Criteria *",
                                           placeholder="What does success look like? How will it be measured?")

            support_resources = st.text_area("Support & Resources Provided",
                                            placeholder="Training, coaching, tools, or resources available...")

            consequences = st.text_area("Consequences of Non-Improvement",
                                       placeholder="Potential outcomes if goals are not met...")

            submitted = st.form_submit_button("💾 Create PIP")

            if submitted and selected_employee and performance_issues and improvement_goals:
                emp_id = emp_options[selected_employee]

                with get_db_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT INTO pips (emp_id, start_date, end_date, performance_issues,
                                         improvement_goals, success_criteria, support_resources,
                                         consequences, review_frequency, status, created_by)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'Active', %s)
                    """, (emp_id, start_date, end_date, performance_issues, improvement_goals,
                         success_criteria, support_resources, consequences, review_frequency,
                         get_current_user()['employee_id']))
                    pip_id = cursor.lastrowid
                    conn.commit()

                create_notification(emp_id, "Performance Improvement Plan Initiated",
                                  "A Performance Improvement Plan has been created for you. Please review the details.", "warning")
                log_audit(get_current_user()['id'], f"Created PIP {pip_id} for employee {emp_id}", "pips")
                st.success("✅ PIP created successfully!")
    else:
        st.info("No employees found")

def show_active_pips():
    """Show currently active PIPs"""
    st.markdown("### 📅 Active PIPs")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT p.*, e.first_name, e.last_name, e.department
            FROM pips p
            JOIN employees e ON p.emp_id = e.id
            WHERE p.status = 'Active' AND p.end_date >= CURRENT_DATE
            ORDER BY p.end_date
        """)
        active_pips = [dict(row) for row in cursor.fetchall()]

    if active_pips:
        for pip in active_pips:
            days_remaining = (datetime.strptime(str(pip['end_date']), '%Y-%m-%d').date() - date.today()).days
            st.write(f"🟡 **{pip['first_name']} {pip['last_name']}** ({pip['department']}) - {days_remaining} days remaining")

            # Add progress update
            with st.expander(f"Add Progress Update - PIP {pip['id']}"):
                with st.form(f"progress_{pip['id']}"):
                    progress_status = st.selectbox("Status", ["On Track", "Needs Improvement", "Off Track", "Exceeding Expectations"], key=f"status_{pip['id']}")
                    progress_notes = st.text_area("Progress Notes", key=f"notes_{pip['id']}")
                    action_items = st.text_area("Action Items", key=f"action_{pip['id']}")

                    if st.form_submit_button("💾 Add Update"):
                        with get_db_connection() as conn:
                            cursor = conn.cursor()
                            cursor.execute("""
                                INSERT INTO pip_progress (pip_id, review_date, status, notes, action_items, reviewed_by)
                                VALUES (%s, %s, %s, %s, %s, %s)
                            """, (pip['id'], date.today(), progress_status, progress_notes,
                                 action_items, get_current_user()['employee_id']))
                            conn.commit()
                        create_notification(pip['emp_id'], "PIP Progress Update",
                                          f"A progress update has been added to your PIP. Status: {progress_status}", "info")
                        st.success("✅ Progress update added!")
                        st.rerun()
    else:
        st.info("No active PIPs")

def show_team_pips():
    """Show team PIPs for managers"""
    user = get_current_user()
    st.markdown("### 👥 Team Performance Improvement Plans")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT department FROM employees WHERE id = %s", (user['employee_id'],))
        dept_row = cursor.fetchone()

        if dept_row:
            dept = dept_row['department']
            cursor.execute("""
                SELECT p.*, e.first_name, e.last_name, e.position
                FROM pips p
                JOIN employees e ON p.emp_id = e.id
                WHERE e.department = %s
                ORDER BY p.start_date DESC
            """, (dept,))
            pips = [dict(row) for row in cursor.fetchall()]

            if pips:
                for pip in pips:
                    status_icon = '✅' if pip['status'] == 'Successful' else '🔴' if pip['status'] == 'Unsuccessful' else '🟡'
                    st.write(f"{status_icon} **{pip['first_name']} {pip['last_name']}** - {pip['position']} - {pip['status']} - {pip['start_date']} to {pip['end_date']}")
            else:
                st.info("No PIPs for your team")

def initiate_pip():
    """Manager initiates PIP"""
    st.markdown("### ➕ Initiate PIP for Team Member")
    st.info("Contact HR to formally create a Performance Improvement Plan")

def show_pip_reviews():
    """Show PIP reviews"""
    st.markdown("### 📋 PIP Reviews")
    st.info("Upcoming PIP review sessions")

def show_my_pip():
    """Show employee's PIP"""
    user = get_current_user()
    st.markdown("### 📋 My Performance Improvement Plan")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM pips
            WHERE emp_id = %s AND status = 'Active'
            ORDER BY start_date DESC
            LIMIT 1
        """, (user['employee_id'],))
        pip = cursor.fetchone()

    if pip:
        pip = dict(pip)
        days_remaining = (datetime.strptime(str(pip['end_date']), '%Y-%m-%d').date() - date.today()).days

        st.warning(f"⚠️ Active PIP: {pip['start_date']} to {pip['end_date']} ({days_remaining} days remaining)")

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Performance Issues:**")
            st.info(pip['performance_issues'])
        with col2:
            st.markdown("**Improvement Goals:**")
            st.success(pip['improvement_goals'])

        if pip['success_criteria']:
            st.markdown("**Success Criteria:**")
            st.write(pip['success_criteria'])

        if pip['support_resources']:
            st.markdown("**Available Support:**")
            st.write(pip['support_resources'])

        # Progress updates
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM pip_progress
                WHERE pip_id = %s
                ORDER BY review_date DESC
            """, (pip['id'],))
            progress = [dict(row) for row in cursor.fetchall()]

        if progress:
            st.markdown("### 📈 Progress Updates")
            for update in progress:
                st.write(f"📅 **{update['review_date']}** - Status: {update['status']}")
                st.write(f"Notes: {update['notes']}")
                if update['action_items']:
                    st.write(f"Action Items: {update['action_items']}")
                st.markdown("---")
    else:
        st.success("✅ No active PIP")

def show_pip_progress():
    """Show PIP progress"""
    user = get_current_user()
    st.markdown("### 📈 My PIP Progress")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT p.*, COUNT(pp.id) as review_count
            FROM pips p
            LEFT JOIN pip_progress pp ON p.id = pp.pip_id
            WHERE p.emp_id = %s AND p.status = 'Active'
            GROUP BY p.id
        """, (user['employee_id'],))
        pip = cursor.fetchone()

    if pip:
        pip = dict(pip)
        st.metric("Total Reviews", pip['review_count'])
        st.write(f"Review Frequency: {pip['review_frequency']}")
    else:
        st.info("No active PIP")

def show_pip_analytics():
    """Show PIP analytics"""
    st.markdown("### 📊 PIP Analytics")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT
                COUNT(*) as total_pips,
                SUM(CASE WHEN status = 'Active' THEN 1 ELSE 0 END) as active_pips,
                SUM(CASE WHEN status = 'Successful' THEN 1 ELSE 0 END) as successful_pips,
                SUM(CASE WHEN status = 'Unsuccessful' THEN 1 ELSE 0 END) as unsuccessful_pips
            FROM pips
        """)
        stats = dict(cursor.fetchone())

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total PIPs", stats['total_pips'] or 0)
    with col2:
        st.metric("Active", stats['active_pips'] or 0)
    with col3:
        st.metric("Successful", stats['successful_pips'] or 0)
    with col4:
        st.metric("Unsuccessful", stats['unsuccessful_pips'] or 0)

    if stats['total_pips'] and stats['total_pips'] > 0:
        success_rate = (stats['successful_pips'] / (stats['successful_pips'] + stats['unsuccessful_pips']) * 100) if (stats['successful_pips'] + stats['unsuccessful_pips']) > 0 else 0
        st.metric("Success Rate", f"{success_rate:.1f}%")
