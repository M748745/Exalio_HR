"""
Career Development Plans Module
Individual development planning and career progression tracking
"""

import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
from database import get_db_connection
from auth import get_current_user, is_hr_admin, is_manager, create_notification, log_audit

def show_career_plans_management():
    """Main career plans interface"""
    user = get_current_user()

    st.markdown("## 🚀 Career Development Plans")
    st.markdown("Plan and track career growth and development")
    st.markdown("---")

    if is_hr_admin():
        tabs = st.tabs(["📋 All Plans", "📊 Progress Overview", "💡 Recommendations"])
    elif is_manager():
        tabs = st.tabs(["👥 Team Plans", "➕ Create Plan", "📊 Team Progress"])
    else:
        tabs = st.tabs(["🚀 My Career Plan", "📈 Progress", "📚 Resources"])

    with tabs[0]:
        if is_hr_admin():
            show_all_career_plans()
        elif is_manager():
            show_team_career_plans()
        else:
            show_my_career_plan()

    with tabs[1]:
        if is_hr_admin():
            show_progress_overview()
        elif is_manager():
            show_create_career_plan()
        else:
            show_career_progress()

    if len(tabs) > 2:
        with tabs[2]:
            if is_hr_admin():
                show_career_recommendations()
            elif is_manager():
                show_team_career_progress()
            else:
                show_career_resources()

def show_my_career_plan():
    """Show employee's career development plan"""
    user = get_current_user()

    st.markdown("### 🚀 My Career Development Plan")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM career_plans
            WHERE emp_id = %s
            ORDER BY created_at DESC
            LIMIT 1
        """, (user['employee_id'],))
        plan = cursor.fetchone()

        if plan:
            plan = dict(plan)

            st.markdown(f"""
                <div style="background: rgba(91, 156, 246, 0.1); padding: 20px; border-radius: 10px; margin-bottom: 20px;">
                    <h3 style="color: #c9963a; margin-top: 0;">🎯 Career Goal</h3>
                    <p style="font-size: 18px;"><strong>{plan.get('target_level', plan.get('target_position', 'Not specified'))}</strong></p>
                    <p style="color: #7d96be;">Timeline: {plan.get('timeline', 'Not specified')}</p>
                </div>
            """, unsafe_allow_html=True)

            # Current state
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("#### 📍 Current Level")
                st.info(f"{plan.get('current_level', plan.get('current_position', 'N/A'))}")

            with col2:
                st.markdown("#### 🎯 Target Level")
                st.success(f"{plan.get('target_level', plan.get('target_position', 'N/A'))}")

            # Development areas
            if plan.get('development_areas'):
                st.markdown("### 📈 Development Areas")
                st.markdown(plan['development_areas'])

            # Skills to develop
            if plan.get('skills_to_develop'):
                st.markdown("### 💪 Skills to Develop")
                st.markdown(plan['skills_to_develop'])

            # Action items
            if plan.get('action_items'):
                st.markdown("### ✅ Action Items")
                st.markdown(plan['action_items'])

            # Progress tracking
            if plan.get('progress'):
                st.markdown("### 📊 Progress")
                progress = plan.get('progress_percentage', 0)
                st.progress(progress / 100)
                st.markdown(plan['progress'])

            # Update progress
            st.markdown("---")
            with st.form("update_career_progress"):
                new_progress = st.slider("Progress %", 0, 100, int(plan.get('progress_percentage', 0)))
                progress_notes = st.text_area("Progress Update", placeholder="What have you accomplished?")

                if st.form_submit_button("💾 Update Progress"):
                    update_career_plan_progress(plan['id'], new_progress, progress_notes)
                    st.rerun()

        else:
            st.info("📝 No career development plan yet. Your manager or HR can create one for you.")

def show_career_progress():
    """Show career progress metrics"""
    user = get_current_user()

    st.markdown("### 📈 Career Progress")

    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Get current plan
        cursor.execute("""
            SELECT * FROM career_plans
            WHERE emp_id = %s
            ORDER BY created_at DESC
            LIMIT 1
        """, (user['employee_id'],))
        plan = cursor.fetchone()

        if plan:
            plan = dict(plan)
            progress = plan.get('progress_percentage', 0)

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Overall Progress", f"{progress}%")
            with col2:
                st.metric("Target Position", plan.get('target_position', 'N/A'))
            with col3:
                target_date = plan.get('target_date')
                if target_date:
                    days_left = (datetime.strptime(target_date, '%Y-%m-%d').date() - date.today()).days
                    st.metric("Days to Target", days_left)

            # Related goals
            cursor.execute("""
                SELECT * FROM goals
                WHERE emp_id = %s AND goal_type = 'Skill Development'
                AND status IN ('Active', 'In Progress')
                ORDER BY created_at DESC
                LIMIT 5
            """, (user['employee_id'],))
            goals = [dict(row) for row in cursor.fetchall()]

            if goals:
                st.markdown("### 🎯 Related Development Goals")
                for goal in goals:
                    goal_progress = goal.get('progress_percentage', 0)
                    st.markdown(f"**{goal['title']}** - {goal_progress}%")
                    st.progress(goal_progress / 100)

def show_career_resources():
    """Show career development resources"""
    st.markdown("### 📚 Career Development Resources")

    st.markdown("""
    #### 🎓 Recommended Training
    - Leadership Development Program
    - Technical Skills Enhancement
    - Communication & Soft Skills
    - Industry Certifications

    #### 📖 Learning Resources
    - Internal Knowledge Base
    - Online Courses (Coursera, Udemy)
    - Mentorship Program
    - Industry Conferences

    #### 🤝 Networking Opportunities
    - Internal Tech Talks
    - Department Meetings
    - Cross-functional Projects
    - Professional Associations
    """)

    st.info("💡 Talk to your manager about specific resources for your career path")

def show_team_career_plans():
    """Show team career plans (Manager view)"""
    user = get_current_user()

    st.markdown("### 👥 Team Career Development Plans")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT cp.*, e.first_name, e.last_name, e.employee_id, e.position
            FROM career_plans cp
            JOIN employees e ON cp.emp_id = e.id
            WHERE e.manager_id = %s
            ORDER BY cp.created_at DESC
        """, (user['employee_id'],))
        plans = [dict(row) for row in cursor.fetchall()]

    if plans:
        for plan in plans:
            progress = plan.get('progress_percentage', 0)

            current_disp = plan.get('current_level', plan.get('current_position', 'N/A'))
            target_disp = plan.get('target_level', plan.get('target_position', 'N/A'))

            with st.expander(f"🚀 {plan.get('first_name', 'N/A')} {plan.get('last_name', '')}: {current_disp} → {target_disp}"):
                col1, col2 = st.columns([2, 1])

                with col1:
                    st.markdown(f"""
                    **Employee:** {plan.get('first_name', 'N/A')} {plan.get('last_name', '')} ({plan.get('employee_id', 'N/A')})
                    **Current:** {current_disp}
                    **Target:** {target_disp}
                    **Timeline:** {plan.get('timeline', 'Not set')}
                    **Status:** {plan.get('status', 'N/A')}
                    """)

                with col2:
                    st.metric("Progress", f"{progress}%")

                st.progress(progress / 100)

                if plan.get('development_areas'):
                    st.info(f"**Development Areas:** {plan['development_areas']}")

                # Review button
                if st.button(f"📝 Review Plan", key=f"review_{plan['id']}"):
                    st.info("Review functionality coming soon")
    else:
        st.info("No career plans for team members yet")

def show_create_career_plan():
    """Create career development plan"""
    user = get_current_user()

    st.markdown("### ➕ Create Career Development Plan")

    # Select employee
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, employee_id, first_name, last_name, position
            FROM employees
            WHERE manager_id = %s AND status = 'Active'
        """, (user['employee_id'],))
        employees = [dict(row) for row in cursor.fetchall()]

    if not employees:
        st.warning("No team members found")
        return

    emp_options = {f"{e['first_name']} {e['last_name']} ({e['employee_id']})": e for e in employees}
    selected_emp = st.selectbox("Select Employee", list(emp_options.keys()))
    employee = emp_options[selected_emp]

    with st.form("create_career_plan"):
        st.markdown(f"**Current Position:** {employee['position']}")

        col1, col2 = st.columns(2)

        with col1:
            current_level = st.selectbox("Current Level", ["Junior", "Mid-Level", "Senior", "Lead", "Principal"])
            target_position = st.text_input("Target Position *", placeholder="e.g., Senior Software Engineer")

        with col2:
            target_level = st.selectbox("Target Level", ["Mid-Level", "Senior", "Lead", "Principal", "Manager"])
            target_date = st.date_input("Target Date", value=date.today() + timedelta(days=365))

        development_areas = st.text_area("Development Areas *", placeholder="Areas that need development...")
        skills_to_develop = st.text_area("Skills to Develop *", placeholder="List specific skills needed...")
        action_items = st.text_area("Action Items", placeholder="Concrete steps to achieve the goal...")

        submitted = st.form_submit_button("🚀 Create Plan", use_container_width=True)

        if submitted:
            if not all([target_position, development_areas, skills_to_develop]):
                st.error("❌ Please fill all required fields")
            else:
                create_career_plan(employee['id'], employee['position'], current_level,
                                 target_position, target_level, target_date,
                                 development_areas, skills_to_develop, action_items)
                st.rerun()

def show_team_career_progress():
    """Show team career progress overview"""
    user = get_current_user()

    st.markdown("### 📊 Team Career Progress")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT
                COUNT(*) as total_plans,
                0 as avg_progress
            FROM career_plans cp
            JOIN employees e ON cp.emp_id = e.id
            WHERE e.manager_id = %s
        """, (user['employee_id'],))
        stats = cursor.fetchone()

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Plans", stats['total_plans'])
    with col2:
        st.metric("Avg Progress", f"{stats['avg_progress'] or 0:.1f}%")

def show_all_career_plans():
    """Show all career plans (HR view)"""
    st.markdown("### 📋 All Career Development Plans")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT cp.*, e.first_name, e.last_name, e.employee_id, e.department
            FROM career_plans cp
            JOIN employees e ON cp.emp_id = e.id
            ORDER BY cp.created_at DESC
            LIMIT 50
        """)
        plans = [dict(row) for row in cursor.fetchall()]

    if plans:
        df = pd.DataFrame(plans)
        # Use actual schema column names: current_level, target_level (no progress_percentage in schema)
        available_cols = [col for col in ['employee_id', 'first_name', 'last_name', 'department', 'current_level', 'target_level', 'status'] if col in df.columns]
        df_display = df[available_cols]

        # Rename columns for display
        col_mapping = {
            'employee_id': 'Emp ID',
            'first_name': 'First Name',
            'last_name': 'Last Name',
            'department': 'Dept',
            'current_level': 'Current Level',
            'target_level': 'Target Level',
            'status': 'Status'
        }
        df_display = df_display.rename(columns={k: v for k, v in col_mapping.items() if k in df_display.columns})

        st.dataframe(df_display, use_container_width=True, hide_index=True)
    else:
        st.info("No career plans yet")

def show_progress_overview():
    """Show overall career progress"""
    st.markdown("### 📊 Career Development Overview")

    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Overall stats
        cursor.execute("""
            SELECT
                COUNT(*) as total_plans,
                0 as avg_progress
            FROM career_plans
        """)
        stats = cursor.fetchone()

        # By department
        cursor.execute("""
            SELECT e.department, COUNT(*) as plan_count, 0 as avg_progress
            FROM career_plans cp
            JOIN employees e ON cp.emp_id = e.id
            GROUP BY e.department
            ORDER BY plan_count DESC
        """)
        by_dept = [dict(row) for row in cursor.fetchall()]

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Plans", stats['total_plans'])
    with col2:
        st.metric("Avg Progress", f"{stats['avg_progress'] or 0:.1f}%")

    if by_dept:
        st.markdown("### 🏢 Plans by Department")
        for dept in by_dept:
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                st.markdown(f"**{dept['department']}**")
            with col2:
                st.markdown(f"{dept['plan_count']} plans")
            with col3:
                st.markdown(f"{dept['avg_progress'] or 0:.1f}%")

def show_career_recommendations():
    """Show career path recommendations"""
    st.markdown("### 💡 Career Path Recommendations")

    st.markdown("""
    #### 🎯 Common Career Paths

    **Engineering Track:**
    - Junior Developer → Mid-Level → Senior → Lead → Principal → Architect

    **Management Track:**
    - Individual Contributor → Team Lead → Engineering Manager → Director → VP

    **Specialist Track:**
    - Developer → Senior Developer → Staff Engineer → Principal Engineer

    #### 📚 Development Focus Areas
    - **Technical:** Advanced programming, system design, architecture
    - **Leadership:** Team management, mentoring, communication
    - **Business:** Strategy, product knowledge, stakeholder management
    - **Soft Skills:** Negotiation, presentation, cross-functional collaboration
    """)

def create_career_plan(emp_id, current_position, current_level, target_position,
                       target_level, target_date, development_areas,
                       skills_to_develop, action_items):
    """Create new career development plan"""
    user = get_current_user()

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO career_plans (
                    emp_id, current_position, current_level, target_position,
                    target_level, target_date, development_areas,
                    skills_to_develop, action_items, created_by
                ) VALUES (%s, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (emp_id, current_position, current_level, target_position,
                 target_level, target_date.isoformat() if target_date else None,
                 development_areas, skills_to_develop, action_items,
                 user['employee_id']))

            plan_id = cursor.lastrowid

            # Notify employee
            create_notification(
                emp_id,
                "Career Development Plan Created",
                f"Your manager has created a career development plan for you.",
                'success'
            )

            conn.commit()
            log_audit(f"Created career plan for employee {emp_id}", "career_plans", plan_id)
            st.success(f"✅ Career plan created successfully! ID: CDP-{plan_id}")
            st.balloons()

    except Exception as e:
        st.error(f"❌ Error: {str(e)}")

def update_career_plan_progress(plan_id, progress, notes):
    """Update career plan progress"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                UPDATE career_plans SET
                    progress_percentage = %s,
                    progress = progress || '\n\n' || ? || ' - ' || ?
                WHERE id = %s
            """, (progress, datetime.now().strftime("%Y-%m-%d"), notes, plan_id))

            conn.commit()
            log_audit(f"Updated career plan {plan_id} progress to {progress}%", "career_plans", plan_id)
            st.success("✅ Progress updated!")

    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
