"""
Team & Position Administration Module
Configure teams, positions, and organizational structure
HR Admin only
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from database import get_db_connection
from auth import get_current_user, is_hr_admin

def show_team_position_admin():
    """Main team and position administration interface"""
    if not is_hr_admin():
        st.error("🚫 Access Denied - HR Admin Only")
        return

    st.markdown("## 🏢 Team & Position Administration")
    st.markdown("Configure organizational teams and positions")
    st.markdown("---")

    tabs = st.tabs(["👥 Teams", "💼 Positions", "🔗 Assignments"])

    with tabs[0]:
        manage_teams()

    with tabs[1]:
        manage_positions()

    with tabs[2]:
        manage_assignments()

def manage_teams():
    """Manage teams with editable table"""
    st.markdown("### 👥 Teams Configuration")
    st.markdown("Manage organizational teams - Each row can be edited or deleted")

    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("➕ Add New Team", use_container_width=True, type="primary"):
            st.session_state.show_add_team = True

    # Display existing teams as editable table
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT t.*,
                   e.first_name || ' ' || e.last_name as team_lead_name,
                   COUNT(DISTINCT p.id) as position_count,
                   COUNT(DISTINCT emp.id) as employee_count
            FROM teams t
            LEFT JOIN employees e ON t.team_lead_id = e.id
            LEFT JOIN positions p ON p.team_id = t.id
            LEFT JOIN employees emp ON emp.team_tag = t.team_name OR emp.department = t.department
            GROUP BY t.id, t.team_name, t.department, t.team_lead_id, t.description,
                     t.status, t.created_at, e.first_name, e.last_name
            ORDER BY t.team_name
        """)
        teams = cursor.fetchall()

    if teams:
        st.markdown("---")
        # Create table header
        st.markdown("#### 📋 Teams Table")

        # Display as a structured table with action buttons
        for idx, team in enumerate(teams):
            status_icon = "🟢" if team['status'] == 'Active' else "🔴"

            # Create container for each row
            with st.container():
                col1, col2, col3, col4, col5, col6 = st.columns([2, 2, 2, 1, 1, 1])

                with col1:
                    st.markdown(f"**{status_icon} {team['team_name']}**")
                    st.caption(f"ID: {team['id']}")

                with col2:
                    st.markdown(f"🏢 {team['department']}")
                    st.caption(f"Positions: {team['position_count']}")

                with col3:
                    st.markdown(f"👤 {team['team_lead_name'] or 'No lead'}")
                    st.caption(f"Employees: {team['employee_count']}")

                with col4:
                    st.markdown(f"**{team['status']}**")

                with col5:
                    if st.button("✏️ Edit", key=f"edit_team_{team['id']}", use_container_width=True):
                        st.session_state.edit_team_id = team['id']
                        st.rerun()

                with col6:
                    if st.button("🗑️ Delete", key=f"del_team_{team['id']}", use_container_width=True, type="secondary"):
                        if st.session_state.get(f'confirm_del_team_{team["id"]}', False):
                            delete_team(team['id'])
                            st.success(f"✅ Deleted team: {team['team_name']}")
                            st.rerun()
                        else:
                            st.session_state[f'confirm_del_team_{team["id"]}'] = True
                            st.warning("⚠️ Click Delete again to confirm")

                # Show expandable details
                with st.expander("View Details", expanded=False):
                    st.markdown(f"**Description:** {team['description'] or 'No description'}")
                    st.markdown(f"**Created:** {team['created_at']}")
                    # updated_at column doesn't exist in teams table - removed

                st.markdown("---")
    else:
        st.info("📋 No teams configured yet. Click 'Add New Team' to create your first team.")

    # Add/Edit Team Modal
    if st.session_state.get('show_add_team', False):
        show_team_form()

    if st.session_state.get('edit_team_id'):
        show_team_form(st.session_state.edit_team_id)

def show_team_form(team_id=None):
    """Form to add or edit a team"""
    st.markdown("---")
    st.markdown("### " + ("Edit Team" if team_id else "Add New Team"))

    # Get existing data if editing
    team_data = None
    if team_id:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM teams WHERE id = %s", (team_id,))
            team_data = cursor.fetchone()

    # Get all employees for team lead selection
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, first_name || ' ' || last_name as name FROM employees WHERE status = 'Active' ORDER BY first_name")
        employees = cursor.fetchall()

    employee_options = {e['id']: e['name'] for e in employees}
    employee_options[0] = "Not assigned"

    with st.form("team_form"):
        team_name = st.text_input("Team Name *", value=team_data['team_name'] if team_data else "")
        department = st.text_input("Department *", value=team_data['department'] if team_data else "")

        team_lead_id = st.selectbox(
            "Team Lead",
            options=list(employee_options.keys()),
            format_func=lambda x: employee_options[x],
            index=list(employee_options.keys()).index(team_data['team_lead_id'] if team_data and team_data['team_lead_id'] else 0)
        )

        description = st.text_area("Description", value=team_data['description'] if team_data else "")
        status = st.selectbox("Status", ["Active", "Inactive"],
                            index=0 if not team_data or team_data['status'] == 'Active' else 1)

        col1, col2 = st.columns(2)
        with col1:
            submit = st.form_submit_button("💾 Save", use_container_width=True)
        with col2:
            cancel = st.form_submit_button("❌ Cancel", use_container_width=True)

        if submit and team_name and department:
            save_team(team_id, team_name, department, team_lead_id if team_lead_id != 0 else None,
                     description, status)
            st.session_state.show_add_team = False
            st.session_state.edit_team_id = None
            st.success("✅ Team saved!")
            st.rerun()

        if cancel:
            st.session_state.show_add_team = False
            st.session_state.edit_team_id = None
            st.rerun()

def save_team(team_id, team_name, department, team_lead_id, description, status):
    """Save team to database"""
    with get_db_connection() as conn:
        cursor = conn.cursor()

        if team_id:
            cursor.execute("""
                UPDATE teams
                SET team_name = %s, department = %s, team_lead_id = %s,
                    description = %s, status = %s
                WHERE id = %s
            """, (team_name, department, team_lead_id, description, status, team_id))
        else:
            cursor.execute("""
                INSERT INTO teams (team_name, department, team_lead_id, description, status)
                VALUES (%s, %s, %s, %s, %s)
            """, (team_name, department, team_lead_id, description, status))

        conn.commit()

def delete_team(team_id):
    """Delete a team"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM teams WHERE id = %s", (team_id,))
        conn.commit()

def manage_positions():
    """Manage positions with editable table"""
    st.markdown("### 💼 Positions Configuration")
    st.markdown("Manage job positions - Each row can be edited or deleted")

    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("➕ Add New Position", use_container_width=True, type="primary"):
            st.session_state.show_add_position = True

    # Display existing positions
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT p.*, t.team_name,
                   COUNT(e.id) as employee_count
            FROM positions p
            LEFT JOIN teams t ON p.team_id = t.id
            LEFT JOIN employees e ON e.position = p.position_name
            GROUP BY p.id, p.position_name, p.team_id, p.level, p.description,
                     p.status, p.created_at, p.updated_at, t.team_name
            ORDER BY t.team_name NULLS LAST, p.level, p.position_name
        """)
        positions = cursor.fetchall()

    if positions:
        st.markdown("---")
        st.markdown("#### 📋 Positions Table")

        # Display as structured table
        for pos in positions:
            status_icon = "🟢" if pos['status'] == 'Active' else "🔴"
            team_name = pos['team_name'] or 'Unassigned'

            with st.container():
                col1, col2, col3, col4, col5, col6 = st.columns([3, 2, 1.5, 1, 1, 1])

                with col1:
                    st.markdown(f"**{status_icon} {pos['position_name']}**")
                    st.caption(f"ID: {pos['id']}")

                with col2:
                    st.markdown(f"🏢 {team_name}")
                    st.caption(f"Employees: {pos['employee_count']}")

                with col3:
                    level_icon = {
                        "Junior": "🌱",
                        "Mid-level": "🌿",
                        "Senior": "🌳",
                        "Lead": "⭐",
                        "Manager": "👔",
                        "Director": "🎯"
                    }.get(pos['level'], "📌")
                    st.markdown(f"{level_icon} {pos['level'] or 'Not set'}")

                with col4:
                    st.markdown(f"**{pos['status']}**")

                with col5:
                    if st.button("✏️ Edit", key=f"edit_pos_{pos['id']}", use_container_width=True):
                        st.session_state.edit_position_id = pos['id']
                        st.rerun()

                with col6:
                    if st.button("🗑️ Delete", key=f"del_pos_{pos['id']}", use_container_width=True, type="secondary"):
                        if st.session_state.get(f'confirm_del_pos_{pos["id"]}', False):
                            delete_position(pos['id'])
                            st.success(f"✅ Deleted position: {pos['position_name']}")
                            st.rerun()
                        else:
                            st.session_state[f'confirm_del_pos_{pos["id"]}'] = True
                            st.warning("⚠️ Click Delete again to confirm")

                # Show expandable details
                with st.expander("View Details", expanded=False):
                    st.markdown(f"**Description:** {pos['description'] or 'No description'}")
                    st.markdown(f"**Created:** {pos['created_at']}")
                    st.markdown(f"**Last Updated:** {pos['updated_at']}")

                st.markdown("---")
    else:
        st.info("📋 No positions configured yet. Click 'Add New Position' to create your first position.")

    # Add/Edit Position Modal
    if st.session_state.get('show_add_position', False):
        show_position_form()

    if st.session_state.get('edit_position_id'):
        show_position_form(st.session_state.edit_position_id)

def show_position_form(position_id=None):
    """Form to add or edit a position"""
    st.markdown("---")
    st.markdown("### " + ("Edit Position" if position_id else "Add New Position"))

    # Get existing data if editing
    position_data = None
    if position_id:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM positions WHERE id = %s", (position_id,))
            position_data = cursor.fetchone()

    # Get all teams
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, team_name FROM teams WHERE status = 'Active' ORDER BY team_name")
        teams = cursor.fetchall()

    team_options = {t['id']: t['team_name'] for t in teams}
    team_options[0] = "No team"

    with st.form("position_form"):
        position_name = st.text_input("Position Name *",
                                      value=position_data['position_name'] if position_data else "")

        team_id = st.selectbox(
            "Team",
            options=list(team_options.keys()),
            format_func=lambda x: team_options[x],
            index=list(team_options.keys()).index(position_data['team_id'] if position_data and position_data['team_id'] else 0)
        )

        level = st.selectbox("Level", ["Junior", "Mid-level", "Senior", "Lead", "Manager", "Director"],
                           index=0)

        description = st.text_area("Description",
                                  value=position_data['description'] if position_data else "")
        status = st.selectbox("Status", ["Active", "Inactive"],
                            index=0 if not position_data or position_data['status'] == 'Active' else 1)

        col1, col2 = st.columns(2)
        with col1:
            submit = st.form_submit_button("💾 Save", use_container_width=True)
        with col2:
            cancel = st.form_submit_button("❌ Cancel", use_container_width=True)

        if submit and position_name:
            save_position(position_id, position_name, team_id if team_id != 0 else None,
                        level, description, status)
            st.session_state.show_add_position = False
            st.session_state.edit_position_id = None
            st.success("✅ Position saved!")
            st.rerun()

        if cancel:
            st.session_state.show_add_position = False
            st.session_state.edit_position_id = None
            st.rerun()

def save_position(position_id, position_name, team_id, level, description, status):
    """Save position to database"""
    with get_db_connection() as conn:
        cursor = conn.cursor()

        if position_id:
            cursor.execute("""
                UPDATE positions
                SET position_name = %s, team_id = %s, level = %s,
                    description = %s, status = %s
                WHERE id = %s
            """, (position_name, team_id, level, description, status, position_id))
        else:
            cursor.execute("""
                INSERT INTO positions (position_name, team_id, level, description, status)
                VALUES (%s, %s, %s, %s, %s)
            """, (position_name, team_id, level, description, status))

        conn.commit()

def delete_position(position_id):
    """Delete a position"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM positions WHERE id = %s", (position_id,))
        conn.commit()

def manage_assignments():
    """View and manage team/position assignments"""
    st.markdown("### Employee Assignments")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT e.id, e.employee_id, e.first_name || ' ' || e.last_name as name,
                   e.position, e.department, e.team_tag,
                   t.id as team_id, t.team_name,
                   p.id as position_id
            FROM employees e
            LEFT JOIN teams t ON e.team_tag = t.team_name
            LEFT JOIN positions p ON e.position = p.position_name AND p.team_id = t.id
            WHERE e.status = 'Active'
            ORDER BY e.department, e.position, e.first_name
        """)
        employees = cursor.fetchall()

    # Group by department
    departments = {}
    for emp in employees:
        dept = emp['department']
        if dept not in departments:
            departments[dept] = []
        departments[dept].append(emp)

    for dept, dept_emps in departments.items():
        st.markdown(f"#### 🏢 {dept}")

        df_data = []
        for emp in dept_emps:
            df_data.append({
                'Employee ID': emp['employee_id'],
                'Name': emp['name'],
                'Position': emp['position'],
                'Team': emp['team_name'] or 'Not assigned',
                'Assigned to System': '✅' if emp['team_id'] and emp['position_id'] else '❌'
            })

        df = pd.DataFrame(df_data)
        st.dataframe(df, use_container_width=True, hide_index=True)

    st.markdown("---")
    st.info("💡 To assign employees to teams/positions, edit the employee record in Employee Management module.")
