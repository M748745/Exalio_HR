"""
Goal & OKR Review Cycle Module
Set goals, track progress, conduct reviews, and measure achievements
"""

import streamlit as st
import pandas as pd
from datetime import datetime, date
from database import get_db_connection
from auth import get_current_user, is_hr_admin, is_manager, create_notification, log_audit

def show_goal_okr_review():
    """Main goal and OKR review interface"""
    user = get_current_user()

    st.markdown("## 🎯 Goals & OKR Management")
    st.markdown("Set objectives, track key results, and conduct quarterly reviews")
    st.markdown("---")

    if is_hr_admin():
        tabs = st.tabs(["📊 All Goals", "📈 Progress Overview", "✅ Review Queue", "➕ Set Company Goals", "📊 Analytics"])
    elif is_manager():
        tabs = st.tabs(["🎯 My Goals", "👥 Team Goals", "📝 Assign Goals", "📊 Progress Report"])
    else:
        tabs = st.tabs(["🎯 My Goals", "📈 My Progress"])

    with tabs[0]:
        if is_hr_admin():
            show_all_goals()
        elif is_manager():
            show_manager_goals()
        else:
            show_employee_goals()

    with tabs[1]:
        if is_hr_admin():
            show_progress_overview()
        elif is_manager():
            show_team_goals()
        else:
            show_my_progress()

    if is_hr_admin() and len(tabs) > 2:
        with tabs[2]:
            show_review_queue()
        with tabs[3]:
            set_company_goals()
        with tabs[4]:
            show_goal_analytics()
    elif is_manager() and len(tabs) > 2:
        with tabs[2]:
            assign_team_goals()
        with tabs[3]:
            show_progress_report()

def show_all_goals():
    """Show all company goals"""
    st.markdown("### 📊 All Goals & OKRs")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT g.*, e.first_name, e.last_name, e.department, e.employee_id
            FROM goals g
            JOIN employees e ON g.emp_id = e.id
            WHERE g.status != 'Cancelled'
            ORDER BY g.review_period DESC, e.department
        """)
        goals = [dict(row) for row in cursor.fetchall()]

    if goals:
        for goal in goals:
            progress = goal.get('progress', 0) or 0
            status_icon = '🟢' if progress >= 75 else '🟡' if progress >= 50 else '🔴'

            with st.expander(f"{status_icon} {goal['first_name']} {goal['last_name']} ({goal['department']}) - {goal['goal_title']} - {progress}%"):
                col1, col2 = st.columns([2, 1])
                with col1:
                    # goal_type column doesn't exist - removed
                    st.write(f"**Description:** {goal['description']}")
                    st.write(f"**Period:** {goal['review_period']}")
                    if goal.get('key_results'):
                        st.write(f"**Key Results:** {goal['key_results']}")
                with col2:
                    st.metric("Progress", f"{progress}%")
                    st.metric("Weight", f"{goal.get('weight', 100)}%")
                    st.write(f"**Status:** {goal['status']}")
                    st.write(f"**Due:** {goal['target_date']}")

                st.progress(progress / 100)

                if goal.get('last_updated'):
                    st.caption(f"Last updated: {goal['last_updated']}")
    else:
        st.info("No goals set yet")

def set_company_goals():
    """Set company or team goals"""
    st.markdown("### ➕ Set Company/Team Goals")

    with st.form("set_goal"):
        col1, col2 = st.columns(2)
        with col1:
            goal_type = st.selectbox("Goal Type *", ["Company OKR", "Department Goal", "Project Goal", "Individual KPI"])
            department = st.selectbox("Department", ["All", "Engineering", "Sales", "Marketing", "HR", "Finance", "Operations"])
            goal_title = st.text_input("Goal Title *")
        with col2:
            review_period = st.selectbox("Review Period *", ["Q1 2024", "Q2 2024", "Q3 2024", "Q4 2024", "Annual 2024"])
            target_date = st.date_input("Target Date *")
            weight = st.number_input("Weight (%)", min_value=0, max_value=100, value=100)

        description = st.text_area("Goal Description *")
        key_results = st.text_area("Key Results (OKRs) - one per line")
        measurement_criteria = st.text_area("Measurement Criteria")

        submitted = st.form_submit_button("💾 Set Goal")

        if submitted and goal_title and description:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO goals (emp_id, goal_type, goal_title, description, key_results,
                                      review_period, target_date, weight, measurement_criteria,
                                      status, progress, created_by)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'Active', 0, %s)
                """, (get_current_user()['employee_id'], goal_type, goal_title, description,
                     key_results, review_period, target_date, weight, measurement_criteria,
                     get_current_user()['employee_id']))
                conn.commit()
                st.success("✅ Goal created successfully!")
                log_audit(get_current_user()['id'], f"Created goal: {goal_title}", "goals")

def show_manager_goals():
    """Show manager's own goals"""
    user = get_current_user()
    st.markdown("### 🎯 My Goals")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM goals
            WHERE emp_id = %s AND status != 'Cancelled'
            ORDER BY review_period DESC, target_date
        """, (user['employee_id'],))
        goals = [dict(row) for row in cursor.fetchall()]

    if goals:
        for goal in goals:
            progress = goal.get('progress', 0) or 0
            with st.expander(f"{goal['goal_title']} - {progress}% complete"):
                st.write(f"**Type:** {goal['goal_type']}")
                st.write(f"**Description:** {goal['description']}")
                st.write(f"**Period:** {goal['review_period']}")
                st.progress(progress / 100)

                # Update progress
                new_progress = st.slider(f"Update Progress - {goal['id']}", 0, 100, progress, key=f"progress_{goal['id']}")
                update_notes = st.text_area(f"Progress Notes - {goal['id']}", key=f"notes_{goal['id']}")

                if st.button(f"💾 Update Progress - {goal['id']}", key=f"btn_{goal['id']}"):
                    with get_db_connection() as conn:
                        cursor = conn.cursor()
                        cursor.execute("""
                            UPDATE goals SET
                                progress = %s,
                                progress_notes = %s,
                                last_updated = %s
                            WHERE id = %s
                        """, (new_progress, update_notes, datetime.now().isoformat(), goal['id']))
                        conn.commit()
                        st.success("✅ Progress updated!")
                        st.rerun()
    else:
        st.info("No goals assigned yet")

def show_employee_goals():
    """Show employee's goals"""
    user = get_current_user()
    st.markdown("### 🎯 My Goals & OKRs")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM goals
            WHERE emp_id = %s AND status != 'Cancelled'
            ORDER BY target_date
        """, (user['employee_id'],))
        goals = [dict(row) for row in cursor.fetchall()]

    if goals:
        for goal in goals:
            progress = goal.get('progress', 0) or 0
            status_icon = '✅' if progress == 100 else '🟢' if progress >= 75 else '🟡' if progress >= 50 else '🔴'

            with st.expander(f"{status_icon} {goal['goal_title']} - {progress}%"):
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"**Type:** {goal['goal_type']}")
                    st.write(f"**Description:** {goal['description']}")
                    if goal.get('key_results'):
                        st.write(f"**Key Results:**")
                        for kr in goal['key_results'].split('\n'):
                            if kr.strip():
                                st.write(f"  • {kr.strip()}")
                with col2:
                    st.metric("Progress", f"{progress}%")
                    st.write(f"**Due:** {goal['target_date']}")

                st.progress(progress / 100)

                # Self-update progress
                new_progress = st.slider(f"Update My Progress", 0, 100, progress, key=f"emp_progress_{goal['id']}")
                notes = st.text_area("Progress Update", key=f"emp_notes_{goal['id']}")

                if st.button("💾 Update", key=f"emp_btn_{goal['id']}"):
                    with get_db_connection() as conn:
                        cursor = conn.cursor()
                        cursor.execute("""
                            UPDATE goals SET
                                progress = %s,
                                progress_notes = %s,
                                last_updated = %s
                            WHERE id = %s
                        """, (new_progress, notes, datetime.now().isoformat(), goal['id']))
                        conn.commit()
                        st.success("✅ Progress updated!")
                        st.rerun()
    else:
        st.info("No goals assigned yet. Contact your manager to set your goals.")

def show_team_goals():
    """Show manager's team goals"""
    user = get_current_user()
    st.markdown("### 👥 Team Goals")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT department FROM employees WHERE id = %s", (user['employee_id'],))
        dept_row = cursor.fetchone()

        if dept_row:
            dept = dept_row['department']
            cursor.execute("""
                SELECT g.*, e.first_name, e.last_name, e.position
                FROM goals g
                JOIN employees e ON g.emp_id = e.id
                WHERE e.department = %s AND g.status != 'Cancelled'
                ORDER BY e.first_name, g.target_date
            """, (dept,))
            goals = [dict(row) for row in cursor.fetchall()]

            if goals:
                for goal in goals:
                    progress = goal.get('progress', 0) or 0
                    status_icon = '🟢' if progress >= 75 else '🟡' if progress >= 50 else '🔴'

                    with st.expander(f"{status_icon} {goal['first_name']} {goal['last_name']} - {goal['goal_title']} - {progress}%"):
                        st.write(f"**Position:** {goal['position']}")
                        st.write(f"**Goal:** {goal['description']}")
                        st.progress(progress / 100)

                        if goal.get('progress_notes'):
                            st.info(f"Latest update: {goal['progress_notes']}")
            else:
                st.info("No team goals found")

def assign_team_goals():
    """Manager assigns goals to team members"""
    user = get_current_user()
    st.markdown("### 📝 Assign Goals to Team Members")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT department FROM employees WHERE id = %s", (user['employee_id'],))
        dept_row = cursor.fetchone()

        if dept_row:
            dept = dept_row['department']
            cursor.execute("""
                SELECT id, first_name, last_name, position
                FROM employees
                WHERE department = %s AND status = 'Active' AND id != %s
                ORDER BY first_name
            """, (dept, user['employee_id']))
            team_members = [dict(row) for row in cursor.fetchall()]

            if team_members:
                with st.form("assign_goal"):
                    employee_options = {f"{m['first_name']} {m['last_name']} - {m['position']}": m['id'] for m in team_members}
                    selected_employee = st.selectbox("Select Team Member *", list(employee_options.keys()))

                    col1, col2 = st.columns(2)
                    with col1:
                        goal_type = st.selectbox("Goal Type *", ["Individual KPI", "Project Goal", "Development Goal", "Performance Goal"])
                        goal_title = st.text_input("Goal Title *")
                    with col2:
                        review_period = st.selectbox("Review Period *", ["Q1 2024", "Q2 2024", "Q3 2024", "Q4 2024"])
                        target_date = st.date_input("Target Date *")

                    description = st.text_area("Goal Description *")
                    key_results = st.text_area("Key Results/Milestones")
                    weight = st.number_input("Weight (%)", min_value=0, max_value=100, value=100)

                    submitted = st.form_submit_button("💾 Assign Goal")

                    if submitted and selected_employee and goal_title and description:
                        emp_id = employee_options[selected_employee]
                        with get_db_connection() as conn:
                            cursor = conn.cursor()
                            cursor.execute("""
                                INSERT INTO goals (emp_id, goal_type, goal_title, description, key_results,
                                                  review_period, target_date, weight, status, progress, created_by)
                                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'Active', 0, %s)
                            """, (emp_id, goal_type, goal_title, description, key_results,
                                 review_period, target_date, weight, user['employee_id']))
                            goal_id = cursor.lastrowid
                            conn.commit()

                            create_notification(emp_id, "New Goal Assigned",
                                              f"Your manager has assigned you a new goal: {goal_title}", "info")
                            log_audit(user['id'], f"Assigned goal {goal_id} to employee {emp_id}", "goals")
                            st.success(f"✅ Goal assigned to {selected_employee}!")
            else:
                st.info("No team members found")

def show_progress_overview():
    """Show company-wide progress overview"""
    st.markdown("### 📈 Company-Wide Progress Overview")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT
                COUNT(*) as total_goals,
                AVG(progress) as avg_progress,
                SUM(CASE WHEN progress >= 100 THEN 1 ELSE 0 END) as completed_goals,
                SUM(CASE WHEN progress < 50 THEN 1 ELSE 0 END) as at_risk_goals
            FROM goals WHERE status = 'Active'
        """)
        stats = dict(cursor.fetchone())

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Goals", stats['total_goals'] or 0)
        with col2:
            st.metric("Avg Progress", f"{stats['avg_progress'] or 0:.1f}%")
        with col3:
            st.metric("Completed", stats['completed_goals'] or 0)
        with col4:
            st.metric("At Risk (<50%)", stats['at_risk_goals'] or 0)

def show_my_progress():
    """Show employee's goal progress"""
    user = get_current_user()
    st.markdown("### 📈 My Goal Progress")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT
                COUNT(*) as total,
                AVG(progress) as avg_progress,
                SUM(CASE WHEN progress >= 100 THEN 1 ELSE 0 END) as completed
            FROM goals WHERE emp_id = %s AND status = 'Active'
        """, (user['employee_id'],))
        stats = dict(cursor.fetchone())

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("My Goals", stats['total'] or 0)
        with col2:
            st.metric("Avg Progress", f"{stats['avg_progress'] or 0:.1f}%")
        with col3:
            st.metric("Completed", stats['completed'] or 0)

def show_review_queue():
    """Show goals pending quarterly review"""
    st.markdown("### ✅ Quarterly Review Queue")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT g.*, e.first_name, e.last_name, e.department
            FROM goals g
            JOIN employees e ON g.emp_id = e.id
            WHERE g.status = 'Active' AND g.target_date <= CURRENT_DATE + INTERVAL '30 days'
            ORDER BY g.target_date
        """)
        goals = [dict(row) for row in cursor.fetchall()]

    if goals:
        for goal in goals:
            with st.expander(f"{goal['first_name']} {goal['last_name']} - {goal['goal_title']} - Due: {goal['target_date']}"):
                st.write(f"**Department:** {goal['department']}")
                st.write(f"**Progress:** {goal.get('progress', 0)}%")
                st.write(f"**Description:** {goal['description']}")

                rating = st.selectbox(f"Achievement Rating - {goal['id']}", ["Exceeded", "Met", "Partially Met", "Not Met"], key=f"rating_{goal['id']}")
                review_notes = st.text_area(f"Review Notes - {goal['id']}", key=f"review_{goal['id']}")

                if st.button(f"✅ Complete Review - {goal['id']}", key=f"review_btn_{goal['id']}"):
                    with get_db_connection() as conn:
                        cursor = conn.cursor()
                        cursor.execute("""
                            UPDATE goals SET
                                status = 'Reviewed',
                                achievement_rating = %s,
                                review_notes = %s,
                                review_date = %s,
                                reviewed_by = %s
                            WHERE id = %s
                        """, (rating, review_notes, datetime.now().isoformat(),
                             get_current_user()['employee_id'], goal['id']))
                        conn.commit()
                        create_notification(goal['emp_id'], "Goal Review Completed",
                                          f"Your goal '{goal['goal_title']}' has been reviewed. Rating: {rating}", "success")
                        st.success("✅ Review completed!")
                        st.rerun()
    else:
        st.info("No goals pending review")

def show_progress_report():
    """Manager's team progress report"""
    user = get_current_user()
    st.markdown("### 📊 Team Progress Report")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT department FROM employees WHERE id = %s", (user['employee_id'],))
        dept_row = cursor.fetchone()

        if dept_row:
            dept = dept_row['department']
            cursor.execute("""
                SELECT
                    e.first_name,
                    e.last_name,
                    COUNT(g.id) as total_goals,
                    AVG(g.progress) as avg_progress,
                    SUM(CASE WHEN g.progress >= 100 THEN 1 ELSE 0 END) as completed
                FROM employees e
                LEFT JOIN goals g ON e.id = g.emp_id AND g.status = 'Active'
                WHERE e.department = %s AND e.status = 'Active'
                GROUP BY e.id, e.first_name, e.last_name
                ORDER BY e.first_name
            """, (dept,))
            reports = [dict(row) for row in cursor.fetchall()]

            if reports:
                for report in reports:
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.write(f"**{report['first_name']} {report['last_name']}**")
                    with col2:
                        st.metric("Goals", report['total_goals'] or 0)
                    with col3:
                        st.metric("Avg Progress", f"{report['avg_progress'] or 0:.1f}%")
                    with col4:
                        st.metric("Completed", report['completed'] or 0)
                    st.markdown("---")

def show_goal_analytics():
    """Goal analytics dashboard"""
    st.markdown("### 📊 Goal Analytics")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT
                department,
                COUNT(*) as total_goals,
                AVG(progress) as avg_progress
            FROM goals g
            JOIN employees e ON g.emp_id = e.id
            WHERE g.status = 'Active'
            GROUP BY department
            ORDER BY avg_progress DESC
        """)
        dept_stats = [dict(row) for row in cursor.fetchall()]

    if dept_stats:
        st.markdown("#### Department Performance")
        for stat in dept_stats:
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                st.write(f"**{stat['department']}**")
            with col2:
                st.metric("Goals", stat['total_goals'])
            with col3:
                st.metric("Progress", f"{stat['avg_progress']:.1f}%")
            st.markdown("---")
