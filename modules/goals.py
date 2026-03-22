"""
Goals & OKRs Module
Objectives and Key Results tracking system
"""

import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
from database import get_db_connection
from auth import get_current_user, is_hr_admin, is_manager, create_notification, log_audit

def show_goals_management():
    """Main goals management interface"""
    user = get_current_user()

    st.markdown("## 🎯 Goals & OKRs")
    st.markdown("Set and track objectives and key results")
    st.markdown("---")

    if is_hr_admin():
        tabs = st.tabs(["📊 Company Goals", "👥 All Employee Goals", "📈 Progress Dashboard"])
    elif is_manager():
        tabs = st.tabs(["🎯 My Goals", "👥 Team Goals", "➕ Set Goal"])
    else:
        tabs = st.tabs(["🎯 My Goals", "➕ Add Goal", "📊 Progress"])

    with tabs[0]:
        if is_hr_admin():
            show_company_goals()
        else:
            show_my_goals()

    with tabs[1]:
        if is_hr_admin():
            show_all_employee_goals()
        elif is_manager():
            show_team_goals()
        else:
            show_add_goal()

    if len(tabs) > 2:
        with tabs[2]:
            if is_hr_admin():
                show_progress_dashboard()
            elif is_manager():
                show_add_goal()
            else:
                show_goal_progress()

def show_my_goals():
    """Show employee's goals"""
    user = get_current_user()

    st.markdown("### 🎯 My Goals & Objectives")

    # Filter by period
    period_filter = st.selectbox("Period", ["Current", "All", "Q1 2024", "Q2 2024", "Q3 2024", "Q4 2024", "2024"])

    with get_db_connection() as conn:
        cursor = conn.cursor()

        query = """
            SELECT * FROM goals
            WHERE emp_id = %s
        """
        params = [user['employee_id']]

        if period_filter != "All":
            if period_filter == "Current":
                query += " AND status IN ('Active', 'In Progress')"
            else:
                query += " AND period = %s"
                params.append(period_filter)

        query += " ORDER BY created_at DESC"

        cursor.execute(query, params)
        goals = [dict(row) for row in cursor.fetchall()]

    if goals:
        for goal in goals:
            # Calculate progress
            progress = goal['progress_percentage'] or 0

            status_config = {
                'Active': {'color': 'rgba(91, 156, 246, 0.1)', 'icon': '🎯'},
                'In Progress': {'color': 'rgba(240, 180, 41, 0.1)', 'icon': '⏳'},
                'Completed': {'color': 'rgba(45, 212, 170, 0.1)', 'icon': '✅'},
                'Cancelled': {'color': 'rgba(125, 150, 190, 0.1)', 'icon': '❌'},
                'Overdue': {'color': 'rgba(241, 100, 100, 0.1)', 'icon': '⚠️'}
            }

            config = status_config.get(goal['status'], status_config['Active'])

            with st.expander(f"{config['icon']} {goal['title']} - {progress}% Complete"):
                col1, col2 = st.columns([2, 1])

                with col1:
                    st.markdown(f"""
                    **Goal:** {goal['title']}
                    **Type:** {goal['goal_type']}
                    **Period:** {goal['period']}
                    **Status:** {goal['status']}
                    **Due Date:** {goal['due_date'] or 'No deadline'}
                    """)

                    if goal['description']:
                        st.markdown(f"**Description:**\n{goal['description']}")

                with col2:
                    st.metric("Progress", f"{progress}%")
                    if goal['target_value'] and goal['current_value']:
                        st.metric("Achievement", f"{goal['current_value']}/{goal['target_value']}")

                # Progress bar
                st.progress(progress / 100)

                # Update progress
                st.markdown("---")
                st.markdown("#### Update Progress")

                with st.form(f"update_goal_{goal['id']}"):
                    new_progress = st.slider("Progress %", 0, 100, int(progress))
                    new_current = st.number_input("Current Value", value=float(goal['current_value'] or 0))
                    notes = st.text_area("Progress Notes", placeholder="What have you accomplished?")

                    if st.form_submit_button("💾 Update Progress"):
                        update_goal_progress(goal['id'], new_progress, new_current, notes)
                        st.rerun()

                # Mark complete
                if goal['status'] != 'Completed' and progress >= 100:
                    if st.button("✅ Mark as Completed", key=f"complete_{goal['id']}"):
                        complete_goal(goal['id'])
                        st.rerun()
    else:
        st.info("No goals set yet. Click 'Add Goal' to create your first goal!")

def show_add_goal():
    """Add new goal"""
    user = get_current_user()

    st.markdown("### ➕ Set New Goal")

    with st.form("add_goal"):
        title = st.text_input("Goal Title *", placeholder="e.g., Increase team productivity by 20%")

        col1, col2 = st.columns(2)

        with col1:
            goal_type = st.selectbox("Goal Type *", [
                "Individual", "Team", "Company", "Skill Development",
                "Performance", "Project", "Sales", "Other"
            ])
            period = st.selectbox("Period *", [
                "Q1 2024", "Q2 2024", "Q3 2024", "Q4 2024",
                "2024", "2025", "Custom"
            ])

        with col2:
            due_date = st.date_input("Due Date", value=date.today() + timedelta(days=90))
            priority = st.selectbox("Priority", ["High", "Medium", "Low"])

        description = st.text_area("Description", placeholder="Describe the goal and why it's important...")

        # Key Results / Metrics
        st.markdown("#### 📊 Measurable Target")
        col1, col2 = st.columns(2)
        with col1:
            target_value = st.number_input("Target Value", value=100.0, help="What's the target number?")
        with col2:
            unit = st.text_input("Unit", placeholder="e.g., %, units, customers", value="%")

        submitted = st.form_submit_button("🎯 Set Goal", use_container_width=True)

        if submitted:
            if not all([title, goal_type, period]):
                st.error("❌ Please fill all required fields")
            else:
                # Get manager if employee
                manager_id = None
                if not is_manager() and not is_hr_admin():
                    with get_db_connection() as conn:
                        cursor = conn.cursor()
                        cursor.execute("SELECT manager_id FROM employees WHERE id = %s", (user['employee_id'],))
                        result = cursor.fetchone()
                        manager_id = result['manager_id'] if result else None

                create_goal(title, goal_type, period, due_date, priority, description, target_value, unit, manager_id)
                st.rerun()

def show_goal_progress():
    """Show goal progress summary"""
    user = get_current_user()

    st.markdown("### 📊 My Goal Progress")

    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Overall statistics
        cursor.execute("""
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN status = 'Completed' THEN 1 ELSE 0 END) as completed,
                SUM(CASE WHEN status IN ('Active', 'In Progress') THEN 1 ELSE 0 END) as active,
                AVG(progress_percentage) as avg_progress
            FROM goals
            WHERE emp_id = %s
        """, (user['employee_id'],))
        stats = cursor.fetchone()

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Goals", stats['total'])
    with col2:
        st.metric("Active", stats['active'])
    with col3:
        st.metric("Completed", stats['completed'])
    with col4:
        st.metric("Avg Progress", f"{stats['avg_progress'] or 0:.1f}%")

    # Goals by type
    st.markdown("---")
    st.markdown("#### 📊 Goals by Type")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT goal_type, COUNT(*) as count, AVG(progress_percentage) as avg_progress
            FROM goals
            WHERE emp_id = %s
            GROUP BY goal_type
            ORDER BY count DESC
        """, (user['employee_id'],))
        by_type = [dict(row) for row in cursor.fetchall()]

    if by_type:
        for item in by_type:
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                st.markdown(f"**{item['goal_type']}**")
            with col2:
                st.markdown(f"{item['count']} goals")
            with col3:
                st.markdown(f"{item['avg_progress'] or 0:.1f}% avg")

def show_team_goals():
    """Show team goals (Manager view)"""
    user = get_current_user()

    st.markdown("### 👥 Team Goals")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT g.*, e.first_name, e.last_name, e.employee_id
            FROM goals g
            JOIN employees e ON g.emp_id = e.id
            WHERE e.manager_id = %s
            ORDER BY g.created_at DESC
        """, (user['employee_id'],))
        goals = [dict(row) for row in cursor.fetchall()]

    if goals:
        for goal in goals:
            progress = goal['progress_percentage'] or 0

            with st.expander(f"🎯 {goal['first_name']} {goal['last_name']}: {goal['title']} ({progress}%)"):
                col1, col2 = st.columns([2, 1])

                with col1:
                    st.markdown(f"""
                    **Employee:** {goal['first_name']} {goal['last_name']} ({goal['employee_id']})
                    **Goal:** {goal['title']}
                    **Type:** {goal['goal_type']}
                    **Period:** {goal['period']}
                    **Status:** {goal['status']}
                    **Due:** {goal['due_date'] or 'No deadline'}
                    **Progress:** {progress}%
                    """)

                with col2:
                    st.metric("Progress", f"{progress}%")

                st.progress(progress / 100)

                if goal['description']:
                    st.info(f"**Description:** {goal['description']}")

                # Manager can provide feedback
                with st.form(f"feedback_{goal['id']}"):
                    feedback = st.text_area("Manager Feedback", placeholder="Provide guidance and feedback...")
                    if st.form_submit_button("💬 Send Feedback"):
                        add_goal_feedback(goal['id'], feedback, goal['emp_id'])
                        st.rerun()
    else:
        st.info("No team goals yet")

def show_company_goals():
    """Show company-wide goals"""
    st.markdown("### 📊 Company Goals & OKRs")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM goals
            WHERE goal_type IN ('Company', 'Team')
            ORDER BY created_at DESC
        """)
        company_goals = [dict(row) for row in cursor.fetchall()]

    if company_goals:
        for goal in company_goals:
            progress = goal.get('progress', goal.get('progress_percentage', 0)) or 0

            st.markdown(f"""
                <div style="background: rgba(58, 123, 213, 0.05); padding: 15px; border-radius: 10px; margin-bottom: 12px;">
                    <strong>{goal.get('goal_title', goal.get('title', 'Untitled'))}</strong><br>
                    <small style="color: #7d96be;">
                        Type: {goal.get('goal_type', 'N/A')} •
                        Progress: {progress}%
                    </small>
                </div>
            """, unsafe_allow_html=True)

            st.progress(progress / 100)
    else:
        st.info("No company goals set yet")

def show_all_employee_goals():
    """Show all employee goals (HR view)"""
    st.markdown("### 👥 All Employee Goals")

    # Filters
    col1, col2 = st.columns(2)
    with col1:
        status_filter = st.selectbox("Status", ["All", "Active", "In Progress", "Completed", "Cancelled"])
    with col2:
        search = st.text_input("🔍 Search employee")

    with get_db_connection() as conn:
        cursor = conn.cursor()

        query = """
            SELECT g.*, e.first_name, e.last_name, e.employee_id, e.department
            FROM goals g
            JOIN employees e ON g.emp_id = e.id
            WHERE 1=1
        """
        params = []

        if status_filter != "All":
            query += " AND g.status = %s"
            params.append(status_filter)

        if search:
            query += " AND (e.first_name LIKE %s OR e.last_name LIKE %s OR e.employee_id LIKE %s)"
            params.extend([f"%{search}%", f"%{search}%", f"%{search}%"])

        query += " ORDER BY g.created_at DESC LIMIT 50"

        cursor.execute(query, params)
        goals = [dict(row) for row in cursor.fetchall()]

    if goals:
        df = pd.DataFrame(goals)
        display_cols = ['employee_id', 'first_name', 'last_name', 'title', 'goal_type', 'period', 'progress_percentage', 'status']
        df_display = df[display_cols]
        df_display.columns = ['Emp ID', 'First Name', 'Last Name', 'Goal', 'Type', 'Period', 'Progress %', 'Status']

        st.dataframe(df_display, use_container_width=True, hide_index=True)
    else:
        st.info("No goals found")

def show_progress_dashboard():
    """Show progress dashboard with analytics"""
    st.markdown("### 📈 Progress Dashboard")

    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Overall stats
        cursor.execute("""
            SELECT
                COUNT(*) as total_goals,
                AVG(progress_percentage) as avg_progress,
                SUM(CASE WHEN status = 'Completed' THEN 1 ELSE 0 END) as completed_goals
            FROM goals
        """)
        overall = cursor.fetchone()

        # By department
        cursor.execute("""
            SELECT e.department, COUNT(*) as goal_count, AVG(g.progress_percentage) as avg_progress
            FROM goals g
            JOIN employees e ON g.emp_id = e.id
            GROUP BY e.department
            ORDER BY goal_count DESC
        """)
        by_dept = [dict(row) for row in cursor.fetchall()]

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Goals", overall['total_goals'])
    with col2:
        st.metric("Completed", overall['completed_goals'])
    with col3:
        st.metric("Avg Progress", f"{overall['avg_progress'] or 0:.1f}%")

    st.markdown("---")
    st.markdown("#### 🏢 Goals by Department")

    if by_dept:
        for dept in by_dept:
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                st.markdown(f"**{dept['department']}**")
            with col2:
                st.markdown(f"{dept['goal_count']} goals")
            with col3:
                st.markdown(f"{dept['avg_progress'] or 0:.1f}%")

def create_goal(title, goal_type, period, due_date, priority, description, target_value, unit, manager_id):
    """Create new goal"""
    user = get_current_user()

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO goals (
                    emp_id, title, goal_type, period, due_date,
                    priority, description, target_value, unit, status
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'Active')
            """, (user['employee_id'], title, goal_type, period,
                 due_date.isoformat() if due_date else None,
                 priority, description, target_value, unit))

            goal_id = cursor.lastrowid

            # Notify manager
            if manager_id:
                create_notification(
                    manager_id,
                    "New Goal Set",
                    f"{user['full_name']} set a new goal: {title}",
                    'info'
                )

            conn.commit()
            log_audit(f"Created goal: {title}", "goals", goal_id)
            st.success(f"✅ Goal created successfully! ID: GOAL-{goal_id}")
            st.balloons()

    except Exception as e:
        st.error(f"❌ Error: {str(e)}")

def update_goal_progress(goal_id, progress, current_value, notes):
    """Update goal progress"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                UPDATE goals SET
                    progress_percentage = %s,
                    current_value = %s,
                    notes = %s,
                    status = CASE
                        WHEN %s >= 100 THEN 'Completed'
                        WHEN %s > 0 THEN 'In Progress'
                        ELSE status
                    END
                WHERE id = %s
            """, (progress, current_value, notes, progress, progress, goal_id))

            conn.commit()
            log_audit(f"Updated goal {goal_id} progress to {progress}%", "goals", goal_id)
            st.success("✅ Progress updated!")

    except Exception as e:
        st.error(f"❌ Error: {str(e)}")

def complete_goal(goal_id):
    """Mark goal as completed"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                UPDATE goals SET
                    status = 'Completed',
                    progress_percentage = 100,
                    completion_date = %s
                WHERE id = %s
            """, (datetime.now().isoformat(), goal_id))

            conn.commit()
            log_audit(f"Completed goal {goal_id}", "goals", goal_id)
            st.success("🎉 Goal completed! Congratulations!")
            st.balloons()

    except Exception as e:
        st.error(f"❌ Error: {str(e)}")

def add_goal_feedback(goal_id, feedback, emp_id):
    """Add manager feedback to goal"""
    user = get_current_user()

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                UPDATE goals SET notes = notes || '\n\nManager Feedback: ' || %s                 WHERE id = %s
            """, (feedback, goal_id))

            create_notification(
                emp_id,
                "Goal Feedback Received",
                f"Your manager provided feedback on your goal.",
                'info'
            )

            conn.commit()
            log_audit(f"Added feedback to goal {goal_id}", "goals", goal_id)
            st.success("✅ Feedback added!")

    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
