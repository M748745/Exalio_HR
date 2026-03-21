"""
Organization Chart Module
Visual company hierarchy and organizational structure
"""

import streamlit as st
import pandas as pd
from database import get_db_connection
from auth import get_current_user, is_hr_admin, is_manager

def show_org_chart():
    """Main organization chart interface"""
    user = get_current_user()

    st.markdown("## 🏢 Organization Chart")
    st.markdown("Company organizational structure and hierarchy")
    st.markdown("---")

    tabs = st.tabs(["🌳 Org Tree", "📊 Departments", "📈 Statistics"])

    with tabs[0]:
        show_org_tree()

    with tabs[1]:
        show_departments_view()

    with tabs[2]:
        show_org_statistics()

def show_org_tree():
    """Show organizational tree structure"""
    st.markdown("### 🌳 Organizational Hierarchy")

    # View options
    view_type = st.radio("View", ["Full Organization", "Department View", "My Team"], horizontal=True)

    if view_type == "Full Organization":
        show_full_org_tree()
    elif view_type == "Department View":
        show_department_tree()
    else:
        show_my_team_tree()

def show_full_org_tree():
    """Show complete organizational tree"""
    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Get all employees with manager info
        cursor.execute("""
            SELECT e.id, e.employee_id, e.first_name, e.last_name,
                   e.position, e.department, e.manager_id, e.status,
                   m.first_name as manager_first, m.last_name as manager_last
            FROM employees e
            LEFT JOIN employees m ON e.manager_id = m.id
            WHERE e.status = 'Active'
            ORDER BY e.department, e.position
        """)
        employees = [dict(row) for row in cursor.fetchall()]

    if not employees:
        st.warning("No employees found")
        return

    # Build hierarchy
    # Find top-level employees (no manager or manager is themselves)
    top_level = [e for e in employees if not e['manager_id'] or e['manager_id'] == e['id']]

    if top_level:
        st.info(f"📊 Showing {len(employees)} active employees across the organization")

        for top_emp in top_level:
            display_employee_node(top_emp, employees, level=0)
    else:
        st.warning("No top-level management found")

def show_department_tree():
    """Show organization by department"""
    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Get departments
        cursor.execute("""
            SELECT DISTINCT department FROM employees
            WHERE status = 'Active' AND department IS NOT NULL
            ORDER BY department
        """)
        departments = [row['department'] for row in cursor.fetchall()]

    if not departments:
        st.warning("No departments found")
        return

    selected_dept = st.selectbox("Select Department", departments)

    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Get employees in selected department
        cursor.execute("""
            SELECT e.id, e.employee_id, e.first_name, e.last_name,
                   e.position, e.department, e.manager_id, e.status,
                   m.first_name as manager_first, m.last_name as manager_last
            FROM employees e
            LEFT JOIN employees m ON e.manager_id = m.id
            WHERE e.department = %s AND e.status = 'Active'
            ORDER BY e.position
        """, (selected_dept,))
        dept_employees = [dict(row) for row in cursor.fetchall()]

    st.markdown(f"### 🏢 {selected_dept} Department")
    st.info(f"📊 {len(dept_employees)} employees")

    # Find department head (employee with no manager in same dept or reports outside dept)
    dept_heads = []
    for emp in dept_employees:
        if not emp['manager_id']:
            dept_heads.append(emp)
        else:
            # Check if manager is in different department
            manager = next((e for e in dept_employees if e['id'] == emp['manager_id']), None)
            if not manager:
                dept_heads.append(emp)

    if dept_heads:
        for head in dept_heads:
            display_employee_node(head, dept_employees, level=0)
    else:
        # Just show all employees
        for emp in dept_employees:
            display_employee_simple(emp)

def show_my_team_tree():
    """Show my team hierarchy"""
    user = get_current_user()

    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Get current user's full info
        cursor.execute("""
            SELECT * FROM employees WHERE id = %s
        """, (user['employee_id'],))
        current_emp = dict(cursor.fetchone())

        # Get team members
        cursor.execute("""
            SELECT e.id, e.employee_id, e.first_name, e.last_name,
                   e.position, e.department, e.manager_id, e.status
            FROM employees e
            WHERE e.manager_id = %s AND e.status = 'Active'
            ORDER BY e.first_name, e.last_name
        """, (user['employee_id'],))
        team_members = [dict(row) for row in cursor.fetchall()]

    st.markdown(f"### 👥 {current_emp['first_name']}'s Team")

    if team_members:
        st.info(f"📊 You manage {len(team_members)} direct report(s)")

        # Display current user
        st.markdown(f"""
            <div style="
                background: linear-gradient(135deg, rgba(91, 156, 246, 0.2), rgba(142, 158, 255, 0.15));
                padding: 16px;
                border-radius: 10px;
                border-left: 4px solid rgba(91, 156, 246, 0.8);
                margin-bottom: 16px;
            ">
                <strong>{current_emp['first_name']} {current_emp['last_name']}</strong> (You)<br>
                <small>{current_emp['position']} • {current_emp['department']}</small>
            </div>
        """, unsafe_allow_html=True)

        # Display team members
        for member in team_members:
            display_team_member(member, level=1)

            # Get their reports
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM employees
                    WHERE manager_id = %s AND status = 'Active'
                """, (member['id'],))
                sub_reports = [dict(row) for row in cursor.fetchall()]

            if sub_reports:
                for sub in sub_reports:
                    display_team_member(sub, level=2)
    else:
        st.info("You have no direct reports")

def display_employee_node(employee, all_employees, level=0):
    """Display employee node with hierarchy"""
    indent = "    " * level
    icon = "👤" if level == 0 else "↳"

    # Count direct reports
    direct_reports = [e for e in all_employees if e['manager_id'] == employee['id'] and e['id'] != employee['id']]

    st.markdown(f"""
        <div style="
            margin-left: {level * 40}px;
            padding: 12px;
            margin-bottom: 8px;
            background: {'linear-gradient(135deg, rgba(91, 156, 246, 0.15), rgba(142, 158, 255, 0.1))' if level == 0 else 'rgba(125, 150, 190, 0.05)'};
            border-radius: 8px;
            border-left: 3px solid {'rgba(91, 156, 246, 0.8)' if level == 0 else 'rgba(125, 150, 190, 0.3)'};
        ">
            <strong>{icon} {employee['first_name']} {employee['last_name']}</strong>
            {f"<span style='color: rgba(91, 156, 246, 0.8);'> • {len(direct_reports)} reports</span>" if direct_reports else ""}<br>
            <small style="color: #7d96be;">{employee['position']} • {employee['department']} • {employee['employee_id']}</small>
        </div>
    """, unsafe_allow_html=True)

    # Recursively display direct reports
    if direct_reports:
        for report in direct_reports:
            display_employee_node(report, all_employees, level + 1)

def display_employee_simple(employee):
    """Simple employee display"""
    st.markdown(f"""
        <div style="
            padding: 12px;
            margin-bottom: 8px;
            background: rgba(125, 150, 190, 0.05);
            border-radius: 8px;
        ">
            <strong>{employee['first_name']} {employee['last_name']}</strong><br>
            <small>{employee['position']} • {employee['employee_id']}</small>
        </div>
    """, unsafe_allow_html=True)

def display_team_member(member, level=1):
    """Display team member in hierarchy"""
    indent = level * 40

    st.markdown(f"""
        <div style="
            margin-left: {indent}px;
            padding: 12px;
            margin-bottom: 8px;
            background: rgba(125, 150, 190, 0.08);
            border-radius: 8px;
            border-left: 2px solid rgba(125, 150, 190, 0.3);
        ">
            <strong>{'└─' if level > 0 else ''} {member['first_name']} {member['last_name']}</strong><br>
            <small style="color: #7d96be;">{member['position']} • {member['employee_id']}</small>
        </div>
    """, unsafe_allow_html=True)

def show_departments_view():
    """Show departments overview"""
    st.markdown("### 📊 Departments Overview")

    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Get department statistics
        cursor.execute("""
            SELECT
                department,
                COUNT(*) as employee_count,
                COUNT(CASE WHEN status = 'Active' THEN 1 END) as active_count,
                COUNT(DISTINCT manager_id) as managers_count
            FROM employees
            WHERE department IS NOT NULL
            GROUP BY department
            ORDER BY employee_count DESC
        """)
        dept_stats = [dict(row) for row in cursor.fetchall()]

    if dept_stats:
        # Department cards
        for i in range(0, len(dept_stats), 2):
            col1, col2 = st.columns(2)

            with col1:
                if i < len(dept_stats):
                    show_department_card(dept_stats[i])

            with col2:
                if i + 1 < len(dept_stats):
                    show_department_card(dept_stats[i + 1])
    else:
        st.info("No departments found")

def show_department_card(dept_stat):
    """Display department card"""
    dept_icons = {
        'Engineering': '💻',
        'Product': '📱',
        'Sales': '💰',
        'Marketing': '📢',
        'Human Resources': '👥',
        'Finance': '💵',
        'Operations': '⚙️'
    }

    icon = dept_icons.get(dept_stat['department'], '🏢')

    st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, rgba(91, 156, 246, 0.1), rgba(142, 158, 255, 0.05));
            padding: 20px;
            border-radius: 12px;
            margin-bottom: 16px;
            border: 1px solid rgba(125, 150, 190, 0.2);
        ">
            <h3 style="margin-top: 0;">{icon} {dept_stat['department']}</h3>
            <p style="margin: 8px 0;">
                <strong>Total Employees:</strong> {dept_stat['employee_count']}<br>
                <strong>Active:</strong> {dept_stat['active_count']}<br>
                <strong>Managers:</strong> {dept_stat['managers_count']}
            </p>
        </div>
    """, unsafe_allow_html=True)

    if st.button(f"View {dept_stat['department']}", key=f"dept_{dept_stat['department']}"):
        show_department_details(dept_stat['department'])

def show_department_details(department):
    """Show detailed department information"""
    st.markdown(f"### 🏢 {department} - Detailed View")

    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Get all employees in department
        cursor.execute("""
            SELECT e.*, m.first_name as manager_first, m.last_name as manager_last
            FROM employees e
            LEFT JOIN employees m ON e.manager_id = m.id
            WHERE e.department = %s
            ORDER BY e.position, e.first_name
        """, (department,))
        employees = [dict(row) for row in cursor.fetchall()]

    if employees:
        # Group by position
        positions = {}
        for emp in employees:
            pos = emp['position']
            if pos not in positions:
                positions[pos] = []
            positions[pos].append(emp)

        for position, emps in positions.items():
            st.markdown(f"#### {position} ({len(emps)})")
            for emp in emps:
                col1, col2, col3 = st.columns([2, 2, 1])
                with col1:
                    st.markdown(f"**{emp['first_name']} {emp['last_name']}**")
                with col2:
                    st.markdown(f"📧 {emp['email']}")
                with col3:
                    status_icon = '✅' if emp['status'] == 'Active' else '⏸️'
                    st.markdown(f"{status_icon} {emp['status']}")
    else:
        st.info("No employees in this department")

def show_org_statistics():
    """Show organizational statistics"""
    st.markdown("### 📈 Organization Statistics")

    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Total employees
        cursor.execute("SELECT COUNT(*) as cnt FROM employees WHERE status = 'Active'")
        total_active = cursor.fetchone()['cnt']

        # Total departments
        cursor.execute("SELECT COUNT(DISTINCT department) as cnt FROM employees WHERE department IS NOT NULL")
        total_depts = cursor.fetchone()['cnt']

        # Total managers
        cursor.execute("""
            SELECT COUNT(DISTINCT manager_id) as cnt FROM employees
            WHERE manager_id IS NOT NULL AND manager_id != id
        """)
        total_managers = cursor.fetchone()['cnt']

        # Average team size
        cursor.execute("""
            SELECT AVG(team_size) as avg_size FROM (
                SELECT manager_id, COUNT(*) as team_size
                FROM employees
                WHERE manager_id IS NOT NULL AND status = 'Active'
                GROUP BY manager_id
            )
        """)
        avg_result = cursor.fetchone()
        avg_team_size = avg_result['avg_size'] if avg_result and avg_result['avg_size'] else 0

    # Display metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Active Employees", total_active)

    with col2:
        st.metric("Departments", total_depts)

    with col3:
        st.metric("Managers", total_managers)

    with col4:
        st.metric("Avg Team Size", f"{avg_team_size:.1f}" if avg_team_size else "0")

    st.markdown("---")

    # Department breakdown
    with get_db_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT department, COUNT(*) as count
            FROM employees
            WHERE status = 'Active' AND department IS NOT NULL
            GROUP BY department
            ORDER BY count DESC
        """)
        dept_breakdown = [dict(row) for row in cursor.fetchall()]

    if dept_breakdown:
        st.markdown("### 📊 Employee Distribution by Department")

        # Create a simple bar chart using markdown
        max_count = max(d['count'] for d in dept_breakdown)

        for dept in dept_breakdown:
            percentage = (dept['count'] / max_count * 100) if max_count > 0 else 0
            st.markdown(f"""
                <div style="margin-bottom: 12px;">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                        <span><strong>{dept['department']}</strong></span>
                        <span>{dept['count']} employees</span>
                    </div>
                    <div style="background: rgba(125, 150, 190, 0.2); border-radius: 10px; height: 24px;">
                        <div style="background: linear-gradient(90deg, rgba(91, 156, 246, 0.8), rgba(142, 158, 255, 0.8));
                                    width: {percentage}%; border-radius: 10px; height: 100%;"></div>
                    </div>
                </div>
            """, unsafe_allow_html=True)

    # Hierarchy depth
    st.markdown("---")
    st.markdown("### 🌳 Organizational Depth")

    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Get hierarchy levels (simplified)
        cursor.execute("""
            SELECT
                COUNT(CASE WHEN manager_id IS NULL THEN 1 END) as top_level,
                COUNT(CASE WHEN manager_id IS NOT NULL THEN 1 END) as managed
            FROM employees
            WHERE status = 'Active'
        """)
        hierarchy = dict(cursor.fetchone())

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Top Level", hierarchy['top_level'])
    with col2:
        st.metric("With Managers", hierarchy['managed'])
