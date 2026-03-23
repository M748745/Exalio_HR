"""
Employee Directory Module
Searchable company-wide employee directory
"""

import streamlit as st
import pandas as pd
from database import get_db_connection
from auth import get_current_user, is_hr_admin, is_manager

def show_employee_directory():
    """Main employee directory interface"""
    user = get_current_user()

    st.markdown("## 📇 Employee Directory")
    st.markdown("Search and browse company employees")
    st.markdown("---")

    # Search and filter section
    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        search_term = st.text_input("🔍 Search", placeholder="Name, email, employee ID, department...")

    with col2:
        department_filter = st.selectbox("Department", [
            "All", "Engineering", "Product", "Sales", "Marketing",
            "Human Resources", "Finance", "Operations"
        ])

    with col3:
        status_filter = st.selectbox("Status", ["All", "Active", "Inactive", "On Leave"])

    # View mode selection
    view_mode = st.radio("View Mode", ["Grid View", "List View", "Table View"], horizontal=True)

    st.markdown("---")

    # Fetch employees
    with get_db_connection() as conn:
        cursor = conn.cursor()

        query = """
            SELECT e.*,
                   m.first_name as manager_first,
                   m.last_name as manager_last,
                   m.employee_id as manager_emp_id
            FROM employees e
            LEFT JOIN employees m ON e.manager_id = m.id
            WHERE 1=1
        """
        params = []

        if search_term:
            query += """ AND (
                e.first_name LIKE %s OR
                e.last_name LIKE %s OR
                e.email LIKE %s OR
                e.employee_id LIKE %s OR
                e.department LIKE %s OR
                e.position LIKE %s
            )"""
            search_pattern = f"%{search_term}%"
            params.extend([search_pattern] * 6)

        if department_filter != "All":
            query += " AND e.department = %s"
            params.append(department_filter)

        if status_filter != "All":
            query += " AND e.status = %s"
            params.append(status_filter)

        query += " ORDER BY e.first_name, e.last_name"

        cursor.execute(query, params)
        employees = [dict(row) for row in cursor.fetchall()]

    # Display count
    st.info(f"📊 Found {len(employees)} employee(s)")

    if employees:
        if view_mode == "Grid View":
            show_grid_view(employees)
        elif view_mode == "List View":
            show_list_view(employees)
        else:
            show_table_view(employees)
    else:
        st.warning("No employees found matching your criteria")

def show_grid_view(employees):
    """Show employees in grid/card view"""
    # Display in rows of 3
    for i in range(0, len(employees), 3):
        cols = st.columns(3)
        for j in range(3):
            if i + j < len(employees):
                emp = employees[i + j]
                with cols[j]:
                    show_employee_card(emp)

def show_employee_card(emp):
    """Display single employee card"""
    status_colors = {
        'Active': 'rgba(46, 213, 115, 0.15)',
        'Inactive': 'rgba(241, 100, 100, 0.15)',
        'On Leave': 'rgba(240, 180, 41, 0.15)'
    }

    status_color = status_colors.get(emp['status'], 'rgba(125, 150, 190, 0.1)')

    # Avatar placeholder (using first letter of first and last name)
    avatar = f"{emp['first_name'][0]}{emp['last_name'][0]}".upper()

    card_html = f"""
        <div style="
            background: {status_color};
            border: 1px solid rgba(125, 150, 190, 0.2);
            border-radius: 12px;
            padding: 16px;
            margin-bottom: 16px;
            text-align: center;
        ">
            <div style="
                width: 60px;
                height: 60px;
                border-radius: 50%;
                background: linear-gradient(135deg, rgba(91, 156, 246, 0.8), rgba(142, 158, 255, 0.8));
                margin: 0 auto 12px;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 24px;
                font-weight: bold;
                color: white;
            ">{avatar}</div>
            <h4 style="margin: 8px 0 4px 0;">{emp['first_name']} {emp['last_name']}</h4>
            <p style="color: rgba(91, 156, 246, 0.9); margin: 4px 0; font-size: 13px;">{emp['position']}</p>
            <p style="color: #7d96be; margin: 4px 0; font-size: 12px;">{emp['department']}</p>
            <hr style="border: none; border-top: 1px solid rgba(125, 150, 190, 0.2); margin: 12px 0;">
            <p style="margin: 4px 0; font-size: 12px;">
                <strong>ID:</strong> {emp['employee_id']}<br>
                <strong>Email:</strong> {emp['email']}<br>
                <strong>Status:</strong> {emp['status']}
            </p>
        </div>
    """

    st.markdown(card_html, unsafe_allow_html=True)

    # Contact button
    if st.button(f"📧 Contact", key=f"contact_{emp['id']}", use_container_width=True):
        show_employee_details(emp)

def show_list_view(employees):
    """Show employees in list view"""
    for emp in employees:
        with st.container():
            col1, col2, col3, col4 = st.columns([1, 2, 2, 1])

            # Avatar
            with col1:
                avatar = f"{emp['first_name'][0]}{emp['last_name'][0]}".upper()
                st.markdown(f"""
                    <div style="
                        width: 50px;
                        height: 50px;
                        border-radius: 50%;
                        background: linear-gradient(135deg, rgba(91, 156, 246, 0.8), rgba(142, 158, 255, 0.8));
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        font-size: 20px;
                        font-weight: bold;
                        color: white;
                        margin: 8px 0;
                    ">{avatar}</div>
                """, unsafe_allow_html=True)

            # Name and Position
            with col2:
                st.markdown(f"**{emp['first_name']} {emp['last_name']}**")
                st.markdown(f"<small>{emp['position']}</small>", unsafe_allow_html=True)

            # Contact Info
            with col3:
                st.markdown(f"📧 {emp['email']}")
                st.markdown(f"<small>🏢 {emp['department']}</small>", unsafe_allow_html=True)

            # Action
            with col4:
                if st.button("View", key=f"view_{emp['id']}"):
                    show_employee_details(emp)

            st.markdown("---")

def show_table_view(employees):
    """Show employees in table view"""
    df = pd.DataFrame(employees)

    # Select relevant columns
    display_cols = ['employee_id', 'first_name', 'last_name', 'email',
                   'department', 'position', 'status']

    # Rename for display
    df_display = df[display_cols].copy()
    df_display.columns = ['ID', 'First Name', 'Last Name', 'Email',
                         'Department', 'Position', 'Status']

    st.dataframe(df_display, use_container_width=True, hide_index=True)

    # Detail view selector
    st.markdown("---")
    selected_id = st.selectbox("View Details",
                              options=[f"{e['first_name']} {e['last_name']} ({e['employee_id']})"
                                      for e in employees])

    if selected_id:
        # Find selected employee
        emp_name = selected_id.split('(')[0].strip()
        selected_emp = next((e for e in employees
                           if f"{e['first_name']} {e['last_name']}" == emp_name), None)
        if selected_emp and st.button("View Profile"):
            show_employee_details(selected_emp)

def show_employee_details(emp):
    """Show detailed employee information in modal-style expander"""
    st.markdown("---")
    st.markdown("### 👤 Employee Profile")

    col1, col2 = st.columns([1, 2])

    with col1:
        # Large avatar
        avatar = f"{emp['first_name'][0]}{emp['last_name'][0]}".upper()
        st.markdown(f"""
            <div style="
                width: 120px;
                height: 120px;
                border-radius: 50%;
                background: linear-gradient(135deg, rgba(91, 156, 246, 0.8), rgba(142, 158, 255, 0.8));
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 48px;
                font-weight: bold;
                color: white;
                margin: 20px auto;
            ">{avatar}</div>
        """, unsafe_allow_html=True)

        # Status badge
        status_colors = {
            'Active': '#2ed573',
            'Inactive': '#ff6348',
            'On Leave': '#ffa502'
        }
        status_color = status_colors.get(emp['status'], '#7d96be')

        st.markdown(f"""
            <div style="
                text-align: center;
                padding: 8px;
                background: {status_color}22;
                border: 1px solid {status_color};
                border-radius: 20px;
                margin: 10px 0;
                color: {status_color};
                font-weight: bold;
            ">{emp['status']}</div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        ### {emp['first_name']} {emp['last_name']}
        **{emp['position']}**

        ---

        **Employee ID:** {emp['employee_id']}
        **Department:** {emp['department']}
        **Email:** {emp['email']}
        **Phone:** {emp.get('phone', 'N/A')}
        **Date of Birth:** {emp.get('date_of_birth', 'N/A')}
        **Hire Date:** {emp.get('hire_date', 'N/A')}
        """)

        # Manager info
        if emp.get('manager_first'):
            st.markdown(f"""
            **Reports To:** {emp['manager_first']} {emp['manager_last']} ({emp['manager_emp_id']})
            """)

        # Additional details
        if emp.get('emergency_contact'):
            st.info(f"🚨 **Emergency Contact:** {emp['emergency_contact']}")

    # Action buttons
    st.markdown("---")
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("📧 Send Email", use_container_width=True):
            st.info(f"Email client would open to: {emp['email']}")

    with col2:
        if st.button("📞 Call", use_container_width=True):
            st.info(f"Would initiate call to: {emp.get('phone', 'N/A')}")

    with col3:
        if st.button("👥 View Team", use_container_width=True):
            show_team_members(emp['id'])

def show_team_members(manager_id):
    """Show employees reporting to a manager"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM employees
            WHERE manager_id = %s
            AND status = 'Active'
            ORDER BY first_name, last_name
        """, (manager_id,))
        team = [dict(row) for row in cursor.fetchall()]

    if team:
        st.markdown("### 👥 Team Members")
        for member in team:
            st.markdown(f"- **{member['first_name']} {member['last_name']}** - {member['position']}")
    else:
        st.info("No direct reports")

def get_department_stats():
    """Get department-wise employee count"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT department, COUNT(*) as count
            FROM employees
            WHERE status = 'Active'
            GROUP BY department
            ORDER BY count DESC
        """)
        return [dict(row) for row in cursor.fetchall()]
