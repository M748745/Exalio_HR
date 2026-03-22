"""
Onboarding Checklist Module
New employee onboarding process and checklist management
"""

import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
from database import get_db_connection
from auth import get_current_user, is_hr_admin, is_manager, create_notification, log_audit

def show_onboarding_management():
    """Main onboarding interface"""
    user = get_current_user()

    st.markdown("## 🎯 Onboarding")
    st.markdown("New employee onboarding process management")
    st.markdown("---")

    if is_hr_admin():
        tabs = st.tabs(["📋 All Onboarding", "➕ Start Onboarding", "📊 Templates", "📈 Analytics"])
    elif is_manager():
        tabs = st.tabs(["👥 Team Onboarding", "✅ My Tasks"])
    else:
        tabs = st.tabs(["📝 My Onboarding", "✅ Checklist"])

    with tabs[0]:
        if is_hr_admin():
            show_all_onboarding()
        elif is_manager():
            show_team_onboarding()
        else:
            show_my_onboarding()

    with tabs[1]:
        if is_hr_admin():
            show_start_onboarding()
        elif is_manager():
            show_manager_onboarding_tasks()
        else:
            show_my_onboarding_checklist()

    if len(tabs) > 2:
        with tabs[2]:
            if is_hr_admin():
                show_onboarding_templates()

    if len(tabs) > 3:
        with tabs[3]:
            show_onboarding_analytics()

def show_my_onboarding():
    """Show employee's onboarding progress"""
    user = get_current_user()

    st.markdown("### 📝 My Onboarding Progress")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM onboarding
            WHERE emp_id = %s
            ORDER BY created_at DESC
            LIMIT 1
        """, (user['employee_id'],))
        onboarding = cursor.fetchone()

        if onboarding:
            onboarding = dict(onboarding)

            # Calculate progress
            total_tasks = 10  # Standard checklist items
            completed_tasks = sum([
                1 if onboarding.get('it_setup') == 'Completed' else 0,
                1 if onboarding.get('workspace_setup') == 'Completed' else 0,
                1 if onboarding.get('system_access') == 'Completed' else 0,
                1 if onboarding.get('email_setup') == 'Completed' else 0,
                1 if onboarding.get('team_introduction') == 'Completed' else 0,
                1 if onboarding.get('policy_review') == 'Completed' else 0,
                1 if onboarding.get('training_scheduled') == 'Completed' else 0,
                1 if onboarding.get('manager_meeting') == 'Completed' else 0,
                1 if onboarding.get('hr_orientation') == 'Completed' else 0,
                1 if onboarding.get('buddy_assigned') == 'Completed' else 0
            ])
            progress = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0

            st.markdown(f"""
                <div style="background: linear-gradient(135deg, rgba(91, 156, 246, 0.15), rgba(142, 158, 255, 0.1)); padding: 20px; border-radius: 10px; margin-bottom: 20px;">
                    <h3 style="margin-top: 0;">Welcome to the Team! 🎉</h3>
                    <p><strong>Start Date:</strong> {onboarding['start_date']}</p>
                    <p><strong>Status:</strong> {onboarding['status']}</p>
                    <p><strong>Progress:</strong> {completed_tasks}/{total_tasks} tasks completed ({progress:.0f}%)</p>
                </div>
            """, unsafe_allow_html=True)

            st.progress(progress / 100)

            # Show buddy info if assigned
            if onboarding.get('buddy_emp_id'):
                cursor.execute("""
                    SELECT first_name, last_name, email FROM employees WHERE id = %s
                """, (onboarding['buddy_emp_id'],))
                buddy = cursor.fetchone()
                if buddy:
                    buddy = dict(buddy)
                    st.info(f"👥 **Your Onboarding Buddy:** {buddy['first_name']} {buddy['last_name']} ({buddy['email']})")

        else:
            st.info("No onboarding record found")

def show_my_onboarding_checklist():
    """Show employee's onboarding checklist"""
    user = get_current_user()

    st.markdown("### ✅ My Onboarding Checklist")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM onboarding
            WHERE emp_id = %s
            ORDER BY created_at DESC
            LIMIT 1
        """, (user['employee_id'],))
        onboarding = cursor.fetchone()

        if onboarding:
            onboarding = dict(onboarding)

            checklist = [
                ("IT Equipment Setup", onboarding.get('it_setup', 'Pending')),
                ("Workspace Setup", onboarding.get('workspace_setup', 'Pending')),
                ("System Access Granted", onboarding.get('system_access', 'Pending')),
                ("Email Setup", onboarding.get('email_setup', 'Pending')),
                ("Team Introduction", onboarding.get('team_introduction', 'Pending')),
                ("Policy Review", onboarding.get('policy_review', 'Pending')),
                ("Training Scheduled", onboarding.get('training_scheduled', 'Pending')),
                ("Manager 1:1 Meeting", onboarding.get('manager_meeting', 'Pending')),
                ("HR Orientation", onboarding.get('hr_orientation', 'Pending')),
                ("Buddy Assigned", onboarding.get('buddy_assigned', 'Pending'))
            ]

            for task, status in checklist:
                if status == 'Completed':
                    st.success(f"✅ {task}")
                elif status == 'In Progress':
                    st.warning(f"⏳ {task}")
                else:
                    st.info(f"⏰ {task}")

            # Notes section
            if onboarding.get('notes'):
                st.markdown("---")
                st.markdown("### 📝 Notes")
                st.info(onboarding['notes'])

        else:
            st.info("No onboarding checklist yet")

def show_team_onboarding():
    """Show team member onboarding (Manager view)"""
    user = get_current_user()

    st.markdown("### 👥 Team Member Onboarding")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT o.*, e.first_name, e.last_name, e.employee_id
            FROM onboarding o
            JOIN employees e ON o.emp_id = e.id
            WHERE e.manager_id = %s
            ORDER BY o.start_date DESC
        """, (user['employee_id'],))
        onboardings = [dict(row) for row in cursor.fetchall()]

    if onboardings:
        for onboard in onboardings:
            # Calculate progress
            completed = sum([
                1 if onboard.get('it_setup') == 'Completed' else 0,
                1 if onboard.get('workspace_setup') == 'Completed' else 0,
                1 if onboard.get('system_access') == 'Completed' else 0,
                1 if onboard.get('email_setup') == 'Completed' else 0,
                1 if onboard.get('team_introduction') == 'Completed' else 0,
                1 if onboard.get('policy_review') == 'Completed' else 0,
                1 if onboard.get('training_scheduled') == 'Completed' else 0,
                1 if onboard.get('manager_meeting') == 'Completed' else 0,
                1 if onboard.get('hr_orientation') == 'Completed' else 0,
                1 if onboard.get('buddy_assigned') == 'Completed' else 0
            ])
            progress = (completed / 10 * 100)

            with st.expander(f"🎯 {onboard['first_name']} {onboard['last_name']} - {progress:.0f}% complete"):
                st.markdown(f"""
                **Employee:** {onboard['first_name']} {onboard['last_name']} ({onboard['employee_id']})
                **Start Date:** {onboard['start_date']}
                **Status:** {onboard['status']}
                **Progress:** {completed}/10 tasks
                """)

                st.progress(progress / 100)

                # Quick actions
                col1, col2 = st.columns(2)
                with col1:
                    if onboard.get('manager_meeting') != 'Completed':
                        if st.button("✅ Mark 1:1 Complete", key=f"meeting_{onboard['id']}"):
                            update_onboarding_task(onboard['id'], 'manager_meeting', 'Completed')
                            st.rerun()
                with col2:
                    if onboard.get('team_introduction') != 'Completed':
                        if st.button("✅ Team Intro Done", key=f"intro_{onboard['id']}"):
                            update_onboarding_task(onboard['id'], 'team_introduction', 'Completed')
                            st.rerun()
    else:
        st.info("No team onboarding in progress")

def show_manager_onboarding_tasks():
    """Show manager-specific onboarding tasks"""
    user = get_current_user()

    st.markdown("### ✅ My Onboarding Tasks")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT o.*, e.first_name, e.last_name, e.employee_id
            FROM onboarding o
            JOIN employees e ON o.emp_id = e.id
            WHERE e.manager_id = %s
            AND (o.manager_meeting != 'Completed' OR o.team_introduction != 'Completed')
            AND o.status = 'In Progress'
            ORDER BY o.start_date ASC
        """, (user['employee_id'],))
        pending_tasks = [dict(row) for row in cursor.fetchall()]

    if pending_tasks:
        st.warning(f"📋 You have {len(pending_tasks)} pending onboarding task(s)")

        for task in pending_tasks:
            st.markdown(f"""
                <div style="background: rgba(240, 180, 41, 0.1); padding: 12px; border-radius: 8px; margin-bottom: 8px;">
                    <strong>{task['first_name']} {task['last_name']}</strong> ({task['employee_id']})<br>
                    <small>Started: {task['start_date']}</small>
                </div>
            """, unsafe_allow_html=True)

            col1, col2 = st.columns(2)
            with col1:
                if task.get('manager_meeting') != 'Completed':
                    st.info("⏰ Schedule 1:1 meeting")
            with col2:
                if task.get('team_introduction') != 'Completed':
                    st.info("⏰ Introduce to team")
    else:
        st.success("✅ No pending onboarding tasks!")

def show_all_onboarding():
    """Show all onboarding processes (HR view)"""
    st.markdown("### 📋 All Onboarding Processes")

    # Filters
    col1, col2 = st.columns(2)
    with col1:
        status_filter = st.selectbox("Status", ["All", "Pending", "In Progress", "Completed", "Cancelled"])
    with col2:
        search = st.text_input("🔍 Search employee")

    with get_db_connection() as conn:
        cursor = conn.cursor()

        query = """
            SELECT o.*, e.first_name, e.last_name, e.employee_id, e.department
            FROM onboarding o
            JOIN employees e ON o.emp_id = e.id
            WHERE 1=1
        """
        params = []

        if status_filter != "All":
            query += " AND o.status = %s"
            params.append(status_filter)

        if search:
            query += " AND (e.first_name LIKE %s OR e.last_name LIKE %s OR e.employee_id LIKE %s)"
            params.extend([f"%{search}%", f"%{search}%", f"%{search}%"])

        query += " ORDER BY o.start_date DESC"

        cursor.execute(query, params)
        onboardings = [dict(row) for row in cursor.fetchall()]

    if onboardings:
        for onboard in onboardings:
            # Calculate progress
            completed = sum([
                1 if onboard.get('it_setup') == 'Completed' else 0,
                1 if onboard.get('workspace_setup') == 'Completed' else 0,
                1 if onboard.get('system_access') == 'Completed' else 0,
                1 if onboard.get('email_setup') == 'Completed' else 0,
                1 if onboard.get('team_introduction') == 'Completed' else 0,
                1 if onboard.get('policy_review') == 'Completed' else 0,
                1 if onboard.get('training_scheduled') == 'Completed' else 0,
                1 if onboard.get('manager_meeting') == 'Completed' else 0,
                1 if onboard.get('hr_orientation') == 'Completed' else 0,
                1 if onboard.get('buddy_assigned') == 'Completed' else 0
            ])
            progress = (completed / 10 * 100)

            with st.expander(f"🎯 {onboard['first_name']} {onboard['last_name']} - {onboard['status']} ({progress:.0f}%)"):
                col1, col2 = st.columns([2, 1])

                with col1:
                    st.markdown(f"""
                    **Employee:** {onboard['first_name']} {onboard['last_name']} ({onboard['employee_id']})
                    **Department:** {onboard['department']}
                    **Start Date:** {onboard['start_date']}
                    **Expected Completion:** {onboard.get('expected_completion_date', 'N/A')}
                    **Status:** {onboard['status']}
                    """)

                with col2:
                    st.metric("Progress", f"{completed}/10")
                    st.progress(progress / 100)

                # Checklist
                st.markdown("---")
                st.markdown("**Checklist:**")

                tasks = [
                    ("it_setup", "IT Equipment Setup"),
                    ("workspace_setup", "Workspace Setup"),
                    ("system_access", "System Access"),
                    ("email_setup", "Email Setup"),
                    ("team_introduction", "Team Introduction"),
                    ("policy_review", "Policy Review"),
                    ("training_scheduled", "Training Scheduled"),
                    ("manager_meeting", "Manager 1:1"),
                    ("hr_orientation", "HR Orientation"),
                    ("buddy_assigned", "Buddy Assigned")
                ]

                col1, col2 = st.columns(2)
                for i, (key, label) in enumerate(tasks):
                    status = onboard.get(key, 'Pending')
                    icon = '✅' if status == 'Completed' else '⏳' if status == 'In Progress' else '⏰'

                    if i % 2 == 0:
                        with col1:
                            if st.button(f"{icon} {label}", key=f"{key}_{onboard['id']}"):
                                new_status = 'Completed' if status != 'Completed' else 'Pending'
                                update_onboarding_task(onboard['id'], key, new_status)
                                st.rerun()
                    else:
                        with col2:
                            if st.button(f"{icon} {label}", key=f"{key}_{onboard['id']}"):
                                new_status = 'Completed' if status != 'Completed' else 'Pending'
                                update_onboarding_task(onboard['id'], key, new_status)
                                st.rerun()

                # Complete onboarding
                if completed == 10 and onboard['status'] != 'Completed':
                    st.markdown("---")
                    if st.button("🎉 Complete Onboarding", key=f"complete_{onboard['id']}"):
                        complete_onboarding(onboard['id'], onboard['emp_id'])
                        st.rerun()

    else:
        st.info("No onboarding processes found")

def show_start_onboarding():
    """Start new onboarding process"""
    st.markdown("### ➕ Start New Onboarding")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        # Get employees without onboarding
        cursor.execute("""
            SELECT e.id, e.employee_id, e.first_name, e.last_name, e.department
            FROM employees e
            LEFT JOIN onboarding o ON e.id = o.emp_id
            WHERE o.id IS NULL
            AND e.status = 'Active'
            ORDER BY e.first_name
        """)
        employees = [dict(row) for row in cursor.fetchall()]

    if not employees:
        st.warning("⚠️ All active employees have onboarding records")
        return

    with st.form("start_onboarding"):
        employee_options = {f"{e['first_name']} {e['last_name']} ({e['employee_id']})": e['id']
                           for e in employees}
        selected_emp = st.selectbox("Select Employee *", list(employee_options.keys()))

        col1, col2 = st.columns(2)

        with col1:
            start_date = st.date_input("Start Date *", value=date.today())
            expected_completion = st.date_input("Expected Completion *",
                                              value=date.today() + timedelta(days=30))

        with col2:
            # Get potential buddies
            cursor.execute("""
                SELECT id, employee_id, first_name, last_name
                FROM employees
                WHERE status = 'Active'
                ORDER BY first_name
            """)
            buddies = [dict(row) for row in cursor.fetchall()]
            buddy_options = {"None": None}
            buddy_options.update({f"{b['first_name']} {b['last_name']} ({b['employee_id']})": b['id']
                                 for b in buddies})
            selected_buddy = st.selectbox("Assign Onboarding Buddy", list(buddy_options.keys()))

        notes = st.text_area("Notes", placeholder="Any special instructions or notes...")

        submitted = st.form_submit_button("🎯 Start Onboarding", use_container_width=True)

        if submitted:
            if not all([selected_emp, start_date, expected_completion]):
                st.error("❌ Please fill all required fields")
            else:
                emp_id = employee_options[selected_emp]
                buddy_id = buddy_options[selected_buddy]
                create_onboarding(emp_id, start_date, expected_completion, buddy_id, notes)
                st.rerun()

def show_onboarding_templates():
    """Show onboarding templates"""
    st.markdown("### 📊 Onboarding Templates")

    templates = [
        {
            "name": "Standard Employee Onboarding",
            "duration": "30 days",
            "tasks": 10,
            "description": "Default onboarding process for all employees"
        },
        {
            "name": "Manager Onboarding",
            "duration": "45 days",
            "tasks": 15,
            "description": "Extended onboarding for management positions"
        },
        {
            "name": "Remote Employee Onboarding",
            "duration": "30 days",
            "tasks": 12,
            "description": "Specialized process for remote workers"
        }
    ]

    for template in templates:
        with st.expander(f"📋 {template['name']}"):
            st.markdown(f"""
            **Duration:** {template['duration']}
            **Tasks:** {template['tasks']}
            **Description:** {template['description']}
            """)

    st.info("Template customization feature coming soon")

def show_onboarding_analytics():
    """Show onboarding analytics"""
    st.markdown("### 📈 Onboarding Analytics")

    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Total onboarding
        cursor.execute("SELECT COUNT(*) as cnt FROM onboarding")
        total = cursor.fetchone()['cnt']

        # Active onboarding
        cursor.execute("""
            SELECT COUNT(*) as cnt FROM onboarding WHERE status = 'In Progress'
        """)
        active = cursor.fetchone()['cnt']

        # Completed
        cursor.execute("""
            SELECT COUNT(*) as cnt FROM onboarding WHERE status = 'Completed'
        """)
        completed = cursor.fetchone()['cnt']

        # Average completion time
        cursor.execute("""
            SELECT AVG(EXTRACT(EPOCH FROM (updated_at - start_date)) / 86400.0) as avg_days
            FROM onboarding
            WHERE status = 'Completed'
        """)
        avg_result = cursor.fetchone()
        avg_days = avg_result['avg_days'] if avg_result and avg_result['avg_days'] else 0

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Onboarding", total)
    with col2:
        st.metric("In Progress", active)
    with col3:
        st.metric("Completed", completed)
    with col4:
        st.metric("Avg. Days to Complete", f"{avg_days:.0f}" if avg_days else "N/A")

    # Completion rate
    if total > 0:
        completion_rate = (completed / total * 100)
        st.markdown("### Completion Rate")
        st.progress(completion_rate / 100)
        st.markdown(f"**{completion_rate:.1f}%** of onboarding processes completed")

def create_onboarding(emp_id, start_date, expected_completion, buddy_id, notes):
    """Create new onboarding process"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO onboarding (
                    emp_id, start_date, expected_completion_date,
                    buddy_emp_id, notes, status,
                    it_setup, workspace_setup, system_access, email_setup,
                    team_introduction, policy_review, training_scheduled,
                    manager_meeting, hr_orientation, buddy_assigned
                ) VALUES (%s, %s, %s, %s, %s, 'In Progress',
                         'Pending', 'Pending', 'Pending', 'Pending',
                         'Pending', 'Pending', 'Pending',
                         'Pending', 'Pending', %s)
            """, (emp_id, start_date.isoformat(), expected_completion.isoformat(),
                 buddy_id, notes, 'Completed' if buddy_id else 'Pending'))

            onboarding_id = cursor.lastrowid

            # Notify employee
            create_notification(emp_id, "Welcome! Your onboarding process has started", "onboarding")

            # Notify buddy if assigned
            if buddy_id:
                create_notification(buddy_id, f"You've been assigned as an onboarding buddy", "onboarding")

            conn.commit()
            log_audit(f"Started onboarding process for employee {emp_id}", "onboarding", onboarding_id)
            st.success(f"✅ Onboarding started! ID: ONB-{onboarding_id}")
            st.balloons()

    except Exception as e:
        st.error(f"❌ Error: {str(e)}")

def update_onboarding_task(onboarding_id, task_field, status):
    """Update onboarding task status"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(f"""
                UPDATE onboarding SET {task_field} = %s
                WHERE id = %s
            """, (status, onboarding_id))

            # Check if all tasks completed
            cursor.execute("""
                SELECT * FROM onboarding WHERE id = %s
            """, (onboarding_id,))
            onboard = dict(cursor.fetchone())

            all_completed = all([
                onboard.get('it_setup') == 'Completed',
                onboard.get('workspace_setup') == 'Completed',
                onboard.get('system_access') == 'Completed',
                onboard.get('email_setup') == 'Completed',
                onboard.get('team_introduction') == 'Completed',
                onboard.get('policy_review') == 'Completed',
                onboard.get('training_scheduled') == 'Completed',
                onboard.get('manager_meeting') == 'Completed',
                onboard.get('hr_orientation') == 'Completed',
                onboard.get('buddy_assigned') == 'Completed'
            ])

            if all_completed:
                cursor.execute("""
                    UPDATE onboarding SET status = 'Completed'
                    WHERE id = %s
                """, (onboarding_id,))

            conn.commit()
            log_audit(f"Updated onboarding task {task_field} to {status}", "onboarding", onboarding_id)
            st.success(f"✅ Task updated!")

    except Exception as e:
        st.error(f"❌ Error: {str(e)}")

def complete_onboarding(onboarding_id, emp_id):
    """Complete onboarding process"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                UPDATE onboarding SET
                    status = 'Completed',
                    completion_date = %s
                WHERE id = %s
            """, (datetime.now().isoformat(), onboarding_id))

            # Notify employee
            create_notification(emp_id, "Congratulations! Your onboarding is complete!", "onboarding")

            conn.commit()
            log_audit(f"Completed onboarding {onboarding_id}", "onboarding", onboarding_id)
            st.success("✅ Onboarding completed!")
            st.balloons()

    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
