"""
Onboarding Task Tracking Module
Automated task assignment, progress tracking, and completion monitoring for new hires
"""

import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
from database import get_db_connection
from auth import get_current_user, is_hr_admin, is_manager, create_notification, log_audit

def show_onboarding_tasks():
    """Main onboarding task tracking interface"""
    user = get_current_user()

    st.markdown("## 📋 Onboarding Task Management")
    st.markdown("Track and manage onboarding tasks for new hires")
    st.markdown("---")

    if is_hr_admin():
        tabs = st.tabs(["📊 All Onboarding", "➕ Create Tasks", "📈 Progress Overview", "📊 Analytics"])
    elif is_manager():
        tabs = st.tabs(["👥 Team Onboarding", "📋 My Tasks"])
    else:
        tabs = st.tabs(["📋 My Onboarding Tasks", "📊 My Progress"])

    with tabs[0]:
        if is_hr_admin():
            show_all_onboarding()
        elif is_manager():
            show_team_onboarding()
        else:
            show_my_onboarding_tasks()

    if is_hr_admin() and len(tabs) > 1:
        with tabs[1]:
            create_onboarding_tasks()
        with tabs[2]:
            show_progress_overview()
        with tabs[3]:
            show_onboarding_analytics()
    elif is_manager() and len(tabs) > 1:
        with tabs[1]:
            show_manager_tasks()
    elif not is_hr_admin() and not is_manager() and len(tabs) > 1:
        with tabs[1]:
            show_my_progress()

def show_all_onboarding():
    """Show all onboarding progress"""
    st.markdown("### 📊 All Onboarding Progress")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT e.id, e.first_name, e.last_name, e.department, e.join_date,
                   COUNT(ot.id) as total_tasks,
                   SUM(CASE WHEN ot.status = 'Completed' THEN 1 ELSE 0 END) as completed_tasks
            FROM employees e
            LEFT JOIN onboarding_tasks ot ON e.id = ot.emp_id
            WHERE e.join_date >= CURRENT_DATE - INTERVAL '90 days'
            GROUP BY e.id, e.first_name, e.last_name, e.department, e.join_date
            ORDER BY e.join_date DESC
        """)
        onboarding = [dict(row) for row in cursor.fetchall()]

    if onboarding:
        for emp in onboarding:
            completion_rate = (emp['completed_tasks'] / emp['total_tasks'] * 100) if emp['total_tasks'] > 0 else 0
            status_icon = '✅' if completion_rate == 100 else '🟢' if completion_rate >= 75 else '🟡' if completion_rate >= 50 else '🔴'

            with st.expander(f"{status_icon} {emp['first_name']} {emp['last_name']} - {emp['department']} - {completion_rate:.0f}% complete"):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Join Date", emp['join_date'])
                with col2:
                    st.metric("Total Tasks", emp['total_tasks'])
                with col3:
                    st.metric("Completed", emp['completed_tasks'])

                st.progress(completion_rate / 100)

                # Show tasks
                with get_db_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT * FROM onboarding_tasks
                        WHERE emp_id = %s
                        ORDER BY due_date
                    """, (emp['id'],))
                    tasks = [dict(row) for row in cursor.fetchall()]

                if tasks:
                    for task in tasks:
                        task_icon = '✅' if task['status'] == 'Completed' else '🔴' if task['status'] == 'Overdue' else '🟡'
                        st.write(f"{task_icon} {task['task_name']} - {task['task_type']} - Due: {task['due_date']} - {task['status']}")
    else:
        st.info("No recent onboarding employees")

def create_onboarding_tasks():
    """Create onboarding tasks for new hire"""
    st.markdown("### ➕ Create Onboarding Tasks")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, first_name, last_name, department, join_date
            FROM employees
            WHERE join_date >= CURRENT_DATE - INTERVAL '90 days'
            ORDER BY join_date DESC
        """)
        new_hires = [dict(row) for row in cursor.fetchall()]

    if new_hires:
        with st.form("create_tasks"):
            emp_options = {f"{e['first_name']} {e['last_name']} - {e['department']} (Joined: {e['join_date']})": e['id'] for e in new_hires}
            selected_employee = st.selectbox("Select New Hire *", list(emp_options.keys()))

            st.markdown("#### Standard Onboarding Tasks")
            standard_tasks = [
                {"name": "Complete HR paperwork", "type": "Administrative", "days": 1, "owner": "HR"},
                {"name": "IT equipment setup", "type": "Technical", "days": 1, "owner": "IT"},
                {"name": "Security badge issuance", "type": "Administrative", "days": 2, "owner": "Security"},
                {"name": "Email and system access", "type": "Technical", "days": 1, "owner": "IT"},
                {"name": "Department orientation", "type": "Training", "days": 3, "owner": "Manager"},
                {"name": "Safety training", "type": "Training", "days": 5, "owner": "HR"},
                {"name": "Company policies review", "type": "Training", "days": 7, "owner": "HR"},
                {"name": "Team introduction meeting", "type": "Social", "days": 3, "owner": "Manager"},
                {"name": "Assign buddy/mentor", "type": "Social", "days": 1, "owner": "Manager"},
                {"name": "First project assignment", "type": "Work", "days": 7, "owner": "Manager"},
                {"name": "30-day check-in", "type": "Review", "days": 30, "owner": "HR"},
                {"name": "60-day review", "type": "Review", "days": 60, "owner": "Manager"},
                {"name": "90-day probation review", "type": "Review", "days": 90, "owner": "HR"},
            ]

            selected_tasks = []
            for task in standard_tasks:
                if st.checkbox(f"{task['name']} ({task['type']}) - Day {task['days']}", value=True, key=task['name']):
                    selected_tasks.append(task)

            # Custom task
            st.markdown("#### Add Custom Task")
            col1, col2 = st.columns(2)
            with col1:
                custom_task_name = st.text_input("Custom Task Name")
                custom_task_type = st.selectbox("Task Type", ["Administrative", "Technical", "Training", "Work", "Review", "Social"])
            with col2:
                custom_days = st.number_input("Days from join date", min_value=1, max_value=90, value=7)
                custom_owner = st.selectbox("Task Owner", ["HR", "Manager", "IT", "Department", "Buddy"])

            submitted = st.form_submit_button("💾 Create Onboarding Tasks")

            if submitted and selected_employee:
                emp_id = emp_options[selected_employee]

                # Get employee join date
                emp = [e for e in new_hires if e['id'] == emp_id][0]
                join_date = datetime.strptime(str(emp['join_date']), '%Y-%m-%d').date()

                with get_db_connection() as conn:
                    cursor = conn.cursor()

                    # Create selected standard tasks
                    for task in selected_tasks:
                        due_date = join_date + timedelta(days=task['days'])
                        cursor.execute("""
                            INSERT INTO onboarding_tasks (emp_id, task_name, task_type, description,
                                                         assigned_to, due_date, status, created_by)
                            VALUES (%s, %s, %s, %s, %s, %s, 'Pending', %s)
                        """, (emp_id, task['name'], task['type'],
                             f"Standard onboarding task - {task['type']}", task['owner'],
                             due_date, get_current_user()['employee_id']))

                    # Create custom task if provided
                    if custom_task_name:
                        custom_due_date = join_date + timedelta(days=custom_days)
                        cursor.execute("""
                            INSERT INTO onboarding_tasks (emp_id, task_name, task_type, assigned_to,
                                                         due_date, status, created_by)
                            VALUES (%s, %s, %s, %s, %s, 'Pending', %s)
                        """, (emp_id, custom_task_name, custom_task_type, custom_owner,
                             custom_due_date, get_current_user()['employee_id']))

                    conn.commit()

                create_notification(emp_id, "Onboarding Tasks Assigned",
                                  f"{len(selected_tasks)} onboarding tasks have been assigned to you", "info")
                log_audit(get_current_user()['id'], f"Created onboarding tasks for employee {emp_id}", "onboarding_tasks")
                st.success(f"✅ Created {len(selected_tasks)} onboarding tasks!")
    else:
        st.info("No recent new hires found")

def show_my_onboarding_tasks():
    """Show employee's onboarding tasks"""
    user = get_current_user()
    st.markdown("### 📋 My Onboarding Tasks")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM onboarding_tasks
            WHERE emp_id = %s
            ORDER BY due_date
        """, (user['employee_id'],))
        tasks = [dict(row) for row in cursor.fetchall()]

    if tasks:
        for task in tasks:
            days_remaining = (datetime.strptime(str(task['due_date']), '%Y-%m-%d').date() - date.today()).days if task['due_date'] else 999
            status_icon = '✅' if task['status'] == 'Completed' else '🔴' if days_remaining < 0 else '🟡'

            with st.expander(f"{status_icon} {task['task_name']} - {task['task_type']}"):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Type:** {task['task_type']}")
                    st.write(f"**Assigned To:** {task['assigned_to']}")
                    st.write(f"**Due Date:** {task['due_date']}")
                with col2:
                    st.write(f"**Status:** {task['status']}")
                    if days_remaining >= 0 and task['status'] != 'Completed':
                        st.write(f"**Days Remaining:** {days_remaining}")

                if task['description']:
                    st.info(task['description'])

                if task['status'] != 'Completed':
                    completion_notes = st.text_area(f"Completion Notes - {task['id']}", key=f"notes_{task['id']}")
                    if st.button(f"✅ Mark Complete - {task['id']}", key=f"complete_{task['id']}"):
                        with get_db_connection() as conn:
                            cursor = conn.cursor()
                            cursor.execute("""
                                UPDATE onboarding_tasks SET
                                    status = 'Completed',
                                    completion_date = %s,
                                    completion_notes = %s
                                WHERE id = %s
                            """, (date.today().isoformat(), completion_notes, task['id']))
                            conn.commit()
                            st.success("✅ Task completed!")
                            st.rerun()
    else:
        st.info("No onboarding tasks assigned. Welcome aboard!")

def show_team_onboarding():
    """Show team onboarding status"""
    user = get_current_user()
    st.markdown("### 👥 Team Onboarding Status")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT department FROM employees WHERE id = %s", (user['employee_id'],))
        dept_row = cursor.fetchone()

        if dept_row:
            dept = dept_row['department']
            cursor.execute("""
                SELECT e.id, e.first_name, e.last_name, e.join_date,
                       COUNT(ot.id) as total_tasks,
                       SUM(CASE WHEN ot.status = 'Completed' THEN 1 ELSE 0 END) as completed_tasks
                FROM employees e
                LEFT JOIN onboarding_tasks ot ON e.id = ot.emp_id
                WHERE e.department = %s AND e.join_date >= CURRENT_DATE - INTERVAL '90 days'
                GROUP BY e.id, e.first_name, e.last_name, e.join_date
                ORDER BY e.join_date DESC
            """, (dept,))
            team = [dict(row) for row in cursor.fetchall()]

            if team:
                for member in team:
                    completion_rate = (member['completed_tasks'] / member['total_tasks'] * 100) if member['total_tasks'] > 0 else 0
                    st.write(f"**{member['first_name']} {member['last_name']}** - Joined: {member['join_date']} - Progress: {completion_rate:.0f}%")
                    st.progress(completion_rate / 100)
                    st.markdown("---")
            else:
                st.info("No recent new hires in your department")

def show_manager_tasks():
    """Show tasks assigned to manager"""
    st.markdown("### 📋 My Onboarding Tasks (As Owner)")
    st.info("Tasks assigned to you as the manager/owner")

def show_my_progress():
    """Show employee onboarding progress"""
    user = get_current_user()
    st.markdown("### 📊 My Onboarding Progress")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN status = 'Completed' THEN 1 ELSE 0 END) as completed
            FROM onboarding_tasks WHERE emp_id = %s
        """, (user['employee_id'],))
        stats = dict(cursor.fetchone())

    if stats['total']:
        completion_rate = (stats['completed'] / stats['total'] * 100)
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Tasks", stats['total'])
        with col2:
            st.metric("Completed", stats['completed'])
        with col3:
            st.metric("Completion Rate", f"{completion_rate:.1f}%")

        st.progress(completion_rate / 100)

        if completion_rate == 100:
            st.success("🎉 Congratulations! You've completed all onboarding tasks!")
    else:
        st.info("No onboarding tasks assigned yet")

def show_progress_overview():
    """Show company-wide onboarding progress"""
    st.markdown("### 📈 Onboarding Progress Overview")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT
                COUNT(DISTINCT emp_id) as total_employees,
                COUNT(*) as total_tasks,
                SUM(CASE WHEN status = 'Completed' THEN 1 ELSE 0 END) as completed_tasks
            FROM onboarding_tasks
        """)
        stats = dict(cursor.fetchone())

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Onboarding Employees", stats['total_employees'] or 0)
    with col2:
        st.metric("Total Tasks", stats['total_tasks'] or 0)
    with col3:
        st.metric("Completed Tasks", stats['completed_tasks'] or 0)

def show_onboarding_analytics():
    """Show onboarding analytics"""
    st.markdown("### 📊 Onboarding Analytics")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT
                task_type,
                COUNT(*) as total,
                SUM(CASE WHEN status = 'Completed' THEN 1 ELSE 0 END) as completed
            FROM onboarding_tasks
            GROUP BY task_type
            ORDER BY total DESC
        """)
        task_analytics = [dict(row) for row in cursor.fetchall()]

    if task_analytics:
        st.markdown("#### Task Completion by Type")
        for analytics in task_analytics:
            completion_rate = (analytics['completed'] / analytics['total'] * 100) if analytics['total'] > 0 else 0
            st.write(f"**{analytics['task_type']}:** {analytics['completed']}/{analytics['total']} ({completion_rate:.1f}%)")
            st.progress(completion_rate / 100)
