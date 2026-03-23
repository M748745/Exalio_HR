"""
Skill Matrix Administration Module
Manage skills, skill requirements for teams/positions, and employee skill assessments
HR Admin only
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from database import get_db_connection
from auth import get_current_user, is_hr_admin

def show_skill_matrix_admin():
    """Main skill matrix administration interface"""
    if not is_hr_admin():
        st.error("🚫 Access Denied - HR Admin Only")
        return

    st.markdown("## 🎯 Skill Matrix Administration")
    st.markdown("Manage skills, team requirements, and employee skill assessments")
    st.markdown("---")

    tabs = st.tabs(["📚 Skills Library", "🎯 Team Skill Matrix", "👤 Employee Skills", "📊 Skill Gap Analysis"])

    with tabs[0]:
        manage_skills()

    with tabs[1]:
        manage_team_skills()

    with tabs[2]:
        manage_employee_skills()

    with tabs[3]:
        show_skill_gap_analysis()

def manage_skills():
    """Manage the skills library with editable table"""
    st.markdown("### 📚 Skills Library Configuration")
    st.markdown("Manage skills catalog - Each row can be edited or deleted")

    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("➕ Add New Skill", use_container_width=True, type="primary"):
            st.session_state.show_add_skill = True

    # Display existing skills
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT s.id, s.skill_name, s.category, s.description, s.created_at,
                       COUNT(DISTINCT ts.team_id) as team_count,
                       COUNT(DISTINCT es.emp_id) as employee_count
                FROM skills s
                LEFT JOIN team_skills ts ON s.id = ts.skill_id
                LEFT JOIN employee_skills es ON s.id = es.skill_id
                GROUP BY s.id, s.skill_name, s.category, s.description, s.created_at
                ORDER BY s.category, s.skill_name
            """)
            skills = cursor.fetchall()
    except Exception as e:
        st.error(f"Error loading skills: {str(e)}")
        skills = []

    if skills:
        st.markdown("---")
        st.markdown("#### 📋 Skills Configuration Table")

        # Category filter
        all_categories = sorted(set(skill['category'] or 'Other' for skill in skills))
        selected_categories = st.multiselect(
            "Filter by Category",
            all_categories,
            default=all_categories,
            key="skill_category_filter"
        )

        # Display skills as table
        filtered_skills = [s for s in skills if (s['category'] or 'Other') in selected_categories]

        for skill in filtered_skills:
            cat_icon = {
                "Programming": "💻",
                "Frontend": "🎨",
                "Backend": "⚙️",
                "Database": "🗄️",
                "Cloud": "☁️",
                "DevOps": "🔧",
                "AI/ML": "🤖",
                "Analytics": "📊",
                "Soft Skills": "🤝",
                "Marketing": "📣",
                "Design": "✨"
            }.get(skill['category'], "🎯")

            with st.container():
                col1, col2, col3, col4, col5, col6 = st.columns([3, 2, 1.5, 1.5, 1, 1])

                with col1:
                    st.markdown(f"**{cat_icon} {skill['skill_name']}**")
                    st.caption(f"ID: {skill['id']}")

                with col2:
                    st.markdown(f"**{skill['category'] or 'Other'}**")
                    desc_preview = (skill['description'] or 'No description')[:40] + "..."
                    st.caption(desc_preview)

                with col3:
                    st.markdown(f"**Teams:** {skill['team_count']}")

                with col4:
                    st.markdown(f"**Employees:** {skill['employee_count']}")

                with col5:
                    if st.button("✏️ Edit", key=f"edit_skill_{skill['id']}", use_container_width=True):
                        st.session_state.edit_skill_id = skill['id']
                        st.rerun()

                with col6:
                    if st.button("🗑️ Delete", key=f"del_skill_{skill['id']}", use_container_width=True, type="secondary"):
                        if st.session_state.get(f'confirm_del_skill_{skill["id"]}', False):
                            delete_skill(skill['id'])
                            st.success(f"✅ Deleted skill: {skill['skill_name']}")
                            st.rerun()
                        else:
                            st.session_state[f'confirm_del_skill_{skill["id"]}'] = True
                            st.warning("⚠️ Click Delete again to confirm")

                # Show expandable details
                with st.expander("View Details", expanded=False):
                    st.markdown(f"**Full Description:** {skill['description'] or 'No description'}")
                    st.markdown(f"**Created:** {skill.get('created_at', 'N/A')}")

                st.markdown("---")
    else:
        st.info("📋 No skills configured yet. Click 'Add New Skill' to create your first skill.")

    # Add/Edit Skill Modal
    if st.session_state.get('show_add_skill', False):
        show_skill_form()

    if st.session_state.get('edit_skill_id'):
        show_skill_form(st.session_state.edit_skill_id)

def show_skill_form(skill_id=None):
    """Form to add or edit a skill"""
    st.markdown("---")
    st.markdown("### " + ("Edit Skill" if skill_id else "Add New Skill"))

    # Get existing data if editing
    skill_data = None
    if skill_id:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM skills WHERE id = %s", (skill_id,))
            skill_data = cursor.fetchone()

    with st.form("skill_form"):
        skill_name = st.text_input("Skill Name *", value=skill_data['skill_name'] if skill_data else "")
        category = st.selectbox("Category", [
            "Programming", "Frontend", "Backend", "Database", "Cloud", "DevOps",
            "AI/ML", "Analytics", "Soft Skills", "Marketing", "Design", "Other"
        ])
        description = st.text_area("Description", value=skill_data['description'] if skill_data else "")

        col1, col2 = st.columns(2)
        with col1:
            submit = st.form_submit_button("💾 Save", use_container_width=True)
        with col2:
            cancel = st.form_submit_button("❌ Cancel", use_container_width=True)

        if submit and skill_name:
            save_skill(skill_id, skill_name, category, description)
            st.session_state.show_add_skill = False
            st.session_state.edit_skill_id = None
            st.success("✅ Skill saved!")
            st.rerun()

        if cancel:
            st.session_state.show_add_skill = False
            st.session_state.edit_skill_id = None
            st.rerun()

def save_skill(skill_id, skill_name, category, description):
    """Save skill to database"""
    with get_db_connection() as conn:
        cursor = conn.cursor()

        if skill_id:
            cursor.execute("""
                UPDATE skills
                SET skill_name = %s, category = %s, description = %s
                WHERE id = %s
            """, (skill_name, category, description, skill_id))
        else:
            cursor.execute("""
                INSERT INTO skills (skill_name, category, description)
                VALUES (%s, %s, %s)
            """, (skill_name, category, description))

        conn.commit()

def delete_skill(skill_id):
    """Delete a skill"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM skills WHERE id = %s", (skill_id,))
        conn.commit()

def manage_team_skills():
    """Manage skill requirements for teams and positions"""
    st.markdown("### Team Skill Matrix")
    st.markdown("Define required skills for each team and position")

    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("➕ Add Requirement", use_container_width=True):
            st.session_state.show_add_team_skill = True

    # Display team skill matrix
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT ts.*, t.team_name, p.position_name, s.skill_name, s.category
            FROM team_skills ts
            JOIN teams t ON ts.team_id = t.id
            LEFT JOIN positions p ON ts.position_id = p.id
            JOIN skills s ON ts.skill_id = s.id
            ORDER BY t.team_name, p.position_name, s.category, s.skill_name
        """)
        team_skills = cursor.fetchall()

    if team_skills:
        # Group by team
        teams = {}
        for ts in team_skills:
            team = ts['team_name']
            if team not in teams:
                teams[team] = {}

            position = ts['position_name'] or 'Team-wide'
            if position not in teams[team]:
                teams[team][position] = []

            teams[team][position].append(ts)

        for team_name, positions in teams.items():
            st.markdown(f"#### 🏢 {team_name}")

            for position_name, skills in positions.items():
                st.markdown(f"**{position_name}:**")

                df_data = []
                for skill in skills:
                    priority_icon = {"High": "🔴", "Medium": "🟡", "Low": "🟢"}.get(skill['priority'], "⚪")
                    df_data.append({
                        'Skill': skill['skill_name'],
                        'Category': skill['category'],
                        'Required Level': skill['required_level'],
                        'Priority': f"{priority_icon} {skill['priority']}",
                        'ID': skill['id']
                    })

                if df_data:
                    df = pd.DataFrame(df_data)

                    # Display with delete buttons
                    for idx, row in df.iterrows():
                        col1, col2, col3, col4, col5 = st.columns([3, 2, 2, 2, 1])
                        with col1:
                            st.markdown(f"**{row['Skill']}**")
                        with col2:
                            st.markdown(row['Category'])
                        with col3:
                            st.markdown(row['Required Level'])
                        with col4:
                            st.markdown(row['Priority'])
                        with col5:
                            if st.button("🗑️", key=f"del_ts_{row['ID']}"):
                                delete_team_skill(row['ID'])
                                st.rerun()

                st.markdown("---")
    else:
        st.info("No team skill requirements configured yet")

    # Add Team Skill Modal
    if st.session_state.get('show_add_team_skill', False):
        show_team_skill_form()

def show_team_skill_form():
    """Form to add team skill requirement"""
    st.markdown("---")
    st.markdown("### Add Skill Requirement")

    # Get teams, positions, and skills
    with get_db_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT id, team_name FROM teams WHERE status = 'Active' ORDER BY team_name")
        teams = {t['id']: t['team_name'] for t in cursor.fetchall()}

        cursor.execute("SELECT id, position_name, team_id FROM positions WHERE status = 'Active' ORDER BY position_name")
        positions = cursor.fetchall()

        cursor.execute("SELECT id, skill_name, category FROM skills ORDER BY category, skill_name")
        skills = cursor.fetchall()

    with st.form("team_skill_form"):
        team_id = st.selectbox("Team *", options=list(teams.keys()), format_func=lambda x: teams[x])

        # Filter positions by selected team
        team_positions = [p for p in positions if p['team_id'] == team_id]
        position_options = {0: "Team-wide (all positions)"}
        position_options.update({p['id']: p['position_name'] for p in team_positions})

        position_id = st.selectbox("Position", options=list(position_options.keys()),
                                  format_func=lambda x: position_options[x])

        skill_id = st.selectbox("Skill *", options=[s['id'] for s in skills],
                               format_func=lambda x: next((s['skill_name'] + f" ({s['category']})"
                                                          for s in skills if s['id'] == x), ""))

        required_level = st.selectbox("Required Proficiency Level",
                                     ["Beginner", "Intermediate", "Advanced", "Expert"])
        priority = st.selectbox("Priority", ["High", "Medium", "Low"])

        col1, col2 = st.columns(2)
        with col1:
            submit = st.form_submit_button("💾 Save", use_container_width=True)
        with col2:
            cancel = st.form_submit_button("❌ Cancel", use_container_width=True)

        if submit:
            save_team_skill(team_id, skill_id, position_id if position_id != 0 else None,
                          required_level, priority)
            st.session_state.show_add_team_skill = False
            st.success("✅ Skill requirement added!")
            st.rerun()

        if cancel:
            st.session_state.show_add_team_skill = False
            st.rerun()

def save_team_skill(team_id, skill_id, position_id, required_level, priority):
    """Save team skill requirement"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO team_skills (team_id, skill_id, position_id, required_level, priority)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (team_id, skill_id, position_id) DO UPDATE
            SET required_level = EXCLUDED.required_level,
                priority = EXCLUDED.priority
        """, (team_id, skill_id, position_id, required_level, priority))
        conn.commit()

def delete_team_skill(team_skill_id):
    """Delete team skill requirement"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM team_skills WHERE id = %s", (team_skill_id,))
        conn.commit()

def manage_employee_skills():
    """Manage employee skill assessments"""
    st.markdown("### Employee Skills Management")

    # Get all employees
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, employee_id, first_name || ' ' || last_name as name, position, department
            FROM employees
            WHERE status = 'Active'
            ORDER BY first_name
        """)
        employees = cursor.fetchall()

    employee_id = st.selectbox("Select Employee",
                               options=[e['id'] for e in employees],
                               format_func=lambda x: next((f"{e['name']} ({e['position']})"
                                                          for e in employees if e['id'] == x), ""))

    if employee_id:
        st.markdown("---")

        # Get employee's current skills
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT es.*, s.skill_name, s.category
                FROM employee_skills es
                JOIN skills s ON es.skill_id = s.id
                WHERE es.emp_id = %s
                ORDER BY s.category, s.skill_name
            """, (employee_id,))
            emp_skills = cursor.fetchall()

        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown("#### Current Skills")
        with col2:
            if st.button("➕ Add Skill", use_container_width=True):
                st.session_state.show_add_emp_skill = True
                st.session_state.selected_emp_id = employee_id

        if emp_skills:
            for skill in emp_skills:
                cert_badge = "🏆" if skill['certified'] else ""
                with st.expander(f"{cert_badge} {skill['skill_name']} - {skill['proficiency_level']}"):
                    col1, col2, col3 = st.columns([2, 2, 1])

                    with col1:
                        st.markdown(f"**Skill:** {skill['skill_name']}")
                        st.markdown(f"**Category:** {skill['category']}")
                        st.markdown(f"**Level:** {skill['proficiency_level']}")

                    with col2:
                        st.markdown(f"**Experience:** {skill['years_experience']} years")
                        st.markdown(f"**Certified:** {'Yes 🏆' if skill['certified'] else 'No'}")
                        st.markdown(f"**Added:** {skill['created_at'].strftime('%Y-%m-%d')}")

                    with col3:
                        if st.button("🗑️ Remove", key=f"del_es_{skill['id']}"):
                            delete_employee_skill(skill['id'])
                            st.rerun()
        else:
            st.info("No skills recorded for this employee")

    # Add Employee Skill Modal
    if st.session_state.get('show_add_emp_skill', False):
        show_employee_skill_form()

def show_employee_skill_form():
    """Form to add employee skill"""
    st.markdown("---")
    st.markdown("### Add Employee Skill")

    emp_id = st.session_state.get('selected_emp_id')

    # Get all skills
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, skill_name, category FROM skills ORDER BY category, skill_name")
        skills = cursor.fetchall()

    with st.form("employee_skill_form"):
        skill_id = st.selectbox("Skill *", options=[s['id'] for s in skills],
                               format_func=lambda x: next((s['skill_name'] + f" ({s['category']})"
                                                          for s in skills if s['id'] == x), ""))

        proficiency_level = st.selectbox("Proficiency Level *",
                                        ["Beginner", "Intermediate", "Advanced", "Expert"])
        years_experience = st.number_input("Years of Experience", min_value=0, max_value=50, value=1)
        certified = st.checkbox("Certified")

        col1, col2 = st.columns(2)
        with col1:
            submit = st.form_submit_button("💾 Save", use_container_width=True)
        with col2:
            cancel = st.form_submit_button("❌ Cancel", use_container_width=True)

        if submit:
            save_employee_skill(emp_id, skill_id, proficiency_level, years_experience, certified)
            st.session_state.show_add_emp_skill = False
            st.success("✅ Skill added!")
            st.rerun()

        if cancel:
            st.session_state.show_add_emp_skill = False
            st.rerun()

def save_employee_skill(emp_id, skill_id, proficiency_level, years_experience, certified):
    """Save employee skill"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO employee_skills (emp_id, skill_id, proficiency_level, years_experience, certified)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (emp_id, skill_id) DO UPDATE
            SET proficiency_level = EXCLUDED.proficiency_level,
                years_experience = EXCLUDED.years_experience,
                certified = EXCLUDED.certified
        """, (emp_id, skill_id, proficiency_level, years_experience, certified))
        conn.commit()

def delete_employee_skill(skill_id):
    """Delete employee skill"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM employee_skills WHERE id = %s", (skill_id,))
        conn.commit()

def show_skill_gap_analysis():
    """Show skill gap analysis"""
    st.markdown("### 📊 Skill Gap Analysis")
    st.markdown("Compare required skills vs actual employee skills")

    # Get all teams
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, team_name FROM teams WHERE status = 'Active' ORDER BY team_name")
        teams = cursor.fetchall()

    team_id = st.selectbox("Select Team", options=[t['id'] for t in teams],
                          format_func=lambda x: next((t['team_name'] for t in teams if t['id'] == x), ""))

    if team_id:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # Get required skills for team
            cursor.execute("""
                SELECT DISTINCT s.id, s.skill_name, s.category, ts.required_level, ts.priority
                FROM team_skills ts
                JOIN skills s ON ts.skill_id = s.id
                WHERE ts.team_id = %s
                ORDER BY ts.priority DESC, s.skill_name
            """, (team_id,))
            required_skills = cursor.fetchall()

            # Get team members and their skills
            cursor.execute("""
                SELECT e.id, e.first_name || ' ' || e.last_name as name,
                       e.position, COUNT(DISTINCT es.skill_id) as skill_count
                FROM employees e
                LEFT JOIN employee_skills es ON e.id = es.emp_id
                LEFT JOIN teams t ON t.id = %s
                WHERE e.department = t.department AND e.status = 'Active'
                GROUP BY e.id, e.first_name, e.last_name, e.position
                ORDER BY e.first_name
            """, (team_id,))
            team_members = cursor.fetchall()

        st.markdown(f"#### Team Members: {len(team_members)}")
        st.markdown(f"#### Required Skills: {len(required_skills)}")
        st.markdown("---")

        # Skill coverage matrix
        st.markdown("### Skill Coverage Matrix")

        for skill in required_skills:
            st.markdown(f"#### {skill['skill_name']} ({skill['category']}) - Required: {skill['required_level']}")

            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT e.first_name || ' ' || e.last_name as name,
                           e.position, es.proficiency_level, es.certified
                    FROM employees e
                    LEFT JOIN employee_skills es ON e.id = es.emp_id AND es.skill_id = %s
                    LEFT JOIN teams t ON t.id = %s
                    WHERE e.department = t.department AND e.status = 'Active'
                    ORDER BY e.first_name
                """, (skill['id'], team_id))
                emp_with_skill = cursor.fetchall()

            has_skill = [e for e in emp_with_skill if e['proficiency_level']]
            missing = len(team_members) - len(has_skill)

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Employees with skill", len(has_skill))
            with col2:
                st.metric("Skill gap", missing, delta=f"-{missing}" if missing > 0 else "0")
            with col3:
                coverage = (len(has_skill) / len(team_members) * 100) if team_members else 0
                st.metric("Coverage", f"{coverage:.0f}%")

            if has_skill:
                for emp in has_skill:
                    cert = "🏆" if emp['certified'] else ""
                    st.markdown(f"- {emp['name']} ({emp['position']}) - {emp['proficiency_level']} {cert}")

            st.markdown("---")
