"""
Employee Management Module
CRUD operations for employee records with role-based access
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from database import get_db_connection
from auth import get_current_user, is_hr_admin, is_manager, get_accessible_employees, log_audit

def show_employee_management():
    """Main employee management interface"""
    user = get_current_user()

    st.markdown("## 👥 Employee Management")
    st.markdown("Manage all employee profiles and records")
    st.markdown("---")

    # Action buttons
    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])

    with col1:
        search_term = st.text_input("🔍 Search employees", placeholder="Name, ID, email...")

    with col2:
        view_mode = st.selectbox("View", ["Cards", "Table"], label_visibility="collapsed")

    with col3:
        dept_filter = st.selectbox("Department", ["All"] + get_departments(), label_visibility="collapsed")

    with col4:
        if is_hr_admin():
            if st.button("➕ Add Employee", use_container_width=True):
                st.session_state.show_employee_modal = True
                st.session_state.edit_employee_id = None
                st.rerun()

    st.markdown("---")

    # Get employees based on role
    employees = get_accessible_employees()

    # Apply filters
    if search_term:
        employees = [e for e in employees if
                    search_term.lower() in e['first_name'].lower() or
                    search_term.lower() in e['last_name'].lower() or
                    search_term.lower() in e['employee_id'].lower() or
                    (e['email'] and search_term.lower() in e['email'].lower())]

    if dept_filter != "All":
        employees = [e for e in employees if e['department'] == dept_filter]

    # Display employees
    if not employees:
        st.info("No employees found")
        return

    if view_mode == "Table":
        display_employees_table(employees)
    else:
        display_employees_cards(employees)

    # Modal for add/edit employee
    if st.session_state.get('show_employee_modal', False):
        show_employee_modal()

def display_employees_cards(employees):
    """Display employees in card view"""
    cols = st.columns(3)

    for idx, emp in enumerate(employees):
        with cols[idx % 3]:
            with st.container():
                st.markdown(f"""
                    <div style="background: linear-gradient(135deg, #0e1117, #1c2535);
                                padding: 20px; border-radius: 12px; border: 1px solid #22304a;
                                margin-bottom: 16px; transition: transform 0.2s;">
                        <div style="text-align: center; margin-bottom: 15px;">
                            <div style="font-size: 48px; margin-bottom: 10px;">👤</div>
                            <h3 style="margin: 0; color: #c9963a;">{emp['first_name']} {emp['last_name']}</h3>
                            <p style="color: #7d96be; font-size: 12px; margin: 5px 0;">{emp['position']}</p>
                            <span style="background: rgba(58, 123, 213, 0.1); color: #5b9cf6;
                                       padding: 3px 10px; border-radius: 20px; font-size: 11px;
                                       border: 1px solid rgba(58, 123, 213, 0.3);">
                                {emp['employee_id']}
                            </span>
                        </div>
                        <div style="font-size: 12px; color: #7d96be;">
                            <p>📧 {emp['email'] or 'N/A'}</p>
                            <p>🏢 {emp['department']}</p>
                            <p>📊 Grade: <span style="color: #c9963a;">{emp['grade'] or 'N/A'}</span></p>
                            <p>📅 Joined: {emp['join_date']}</p>
                        </div>
                    </div>
                """, unsafe_allow_html=True)

                col1, col2 = st.columns(2)
                with col1:
                    if st.button("👁️ View", key=f"view_{emp['id']}", use_container_width=True):
                        st.session_state.view_employee_id = emp['id']
                        st.rerun()

                with col2:
                    if is_hr_admin() or (is_manager() and emp['manager_id'] == get_current_user()['employee_id']):
                        if st.button("✏️ Edit", key=f"edit_{emp['id']}", use_container_width=True):
                            st.session_state.show_employee_modal = True
                            st.session_state.edit_employee_id = emp['id']
                            st.rerun()

def display_employees_table(employees):
    """Display employees in table view"""
    df = pd.DataFrame(employees)

    # Select and rename columns
    display_columns = {
        'employee_id': 'Employee ID',
        'first_name': 'First Name',
        'last_name': 'Last Name',
        'email': 'Email',
        'department': 'Department',
        'position': 'Position',
        'grade': 'Grade',
        'status': 'Status',
        'join_date': 'Join Date'
    }

    df_display = df[list(display_columns.keys())].rename(columns=display_columns)

    # Add action column
    st.dataframe(
        df_display,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Status": st.column_config.TextColumn(
                "Status",
                width="small"
            ),
            "Grade": st.column_config.TextColumn(
                "Grade",
                width="small"
            )
        }
    )

    # Action buttons below table
    if is_hr_admin():
        st.markdown("---")
        selected_id = st.selectbox(
            "Select employee to edit",
            options=[e['id'] for e in employees],
            format_func=lambda x: f"{next(e['first_name'] + ' ' + e['last_name'] for e in employees if e['id'] == x)} ({next(e['employee_id'] for e in employees if e['id'] == x)})"
        )

        col1, col2 = st.columns([1, 5])
        with col1:
            if st.button("✏️ Edit Selected"):
                st.session_state.show_employee_modal = True
                st.session_state.edit_employee_id = selected_id
                st.rerun()

def show_employee_modal():
    """Modal dialog for adding/editing employee"""
    edit_id = st.session_state.get('edit_employee_id', None)

    if edit_id:
        st.markdown("### ✏️ Edit Employee")
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM employees WHERE id = %s", (edit_id,))
            employee = dict(cursor.fetchone())
    else:
        st.markdown("### ➕ Add New Employee")
        employee = {}

    with st.form("employee_form"):
        col1, col2 = st.columns(2)

        with col1:
            first_name = st.text_input("First Name *", value=employee.get('first_name', ''))
            last_name = st.text_input("Last Name *", value=employee.get('last_name', ''))
            employee_id = st.text_input("Employee ID *", value=employee.get('employee_id', ''))
            email = st.text_input("Email *", value=employee.get('email', ''))
            phone = st.text_input("Phone", value=employee.get('phone', ''))
            date_of_birth = st.date_input("Date of Birth", value=None)
            gender = st.selectbox("Gender", ["Male", "Female", "Other"],
                                index=["Male", "Female", "Other"].index(employee.get('gender', 'Male')))

        with col2:
            department = st.selectbox("Department *", get_departments(),
                                     index=get_departments().index(employee.get('department', 'Engineering')))
            position = st.text_input("Position *", value=employee.get('position', ''))

            # Get managers for dropdown
            managers = get_manager_list()
            manager_id = st.selectbox("Manager",
                                     options=[None] + [m['id'] for m in managers],
                                     format_func=lambda x: "None" if x is None else next((f"{m['first_name']} {m['last_name']}" for m in managers if m['id'] == x), "None"),
                                     index=0)

            grade = st.selectbox("Grade", ["A+", "A", "B+", "B", "C+", "C", "D"],
                               index=["A+", "A", "B+", "B", "C+", "C", "D"].index(employee.get('grade', 'B')))

            status = st.selectbox("Status", ["Active", "Inactive", "On Leave", "Terminated"],
                                index=["Active", "Inactive", "On Leave", "Terminated"].index(employee.get('status', 'Active')))

            join_date = st.date_input("Join Date *", value=datetime.strptime(employee.get('join_date', datetime.now().strftime('%Y-%m-%d')), '%Y-%m-%d'))

            team_tag = st.selectbox("Team", ["None", "app", "data", "ai", "pm"],
                                   index=["None", "app", "data", "ai", "pm"].index(employee.get('team_tag') or 'None'))

        location = st.text_input("Location", value=employee.get('location', ''))
        national_id = st.text_input("National ID", value=employee.get('national_id', ''))
        address = st.text_area("Address", value=employee.get('address', ''))
        emergency_contact = st.text_input("Emergency Contact", value=employee.get('emergency_contact', ''))
        bio = st.text_area("Bio", value=employee.get('bio', ''))

        col1, col2, col3 = st.columns([1, 1, 3])

        with col1:
            submitted = st.form_submit_button("💾 Save", use_container_width=True)

        with col2:
            cancelled = st.form_submit_button("❌ Cancel", use_container_width=True)

        if cancelled:
            st.session_state.show_employee_modal = False
            st.rerun()

        if submitted:
            if not all([first_name, last_name, employee_id, email, department, position]):
                st.error("Please fill all required fields marked with *")
            else:
                try:
                    with get_db_connection() as conn:
                        cursor = conn.cursor()

                        team_tag_value = None if team_tag == "None" else team_tag

                        if edit_id:
                            # Update existing employee
                            cursor.execute("""
                                UPDATE employees SET
                                    first_name = %s, last_name = %s, employee_id = %s, email = %s,
                                    phone = %s, date_of_birth = %s, gender = %s, department = %s,
                                    position = %s, manager_id = %s, grade = %s, status = %s,
                                    join_date = %s, location = %s, national_id = %s, address = %s,
                                    emergency_contact = %s, bio = %s, team_tag = %s, updated_at = %s
                                WHERE id = %s
                            """, (first_name, last_name, employee_id, email, phone,
                                 date_of_birth, gender, department, position, manager_id,
                                 grade, status, join_date, location, national_id, address,
                                 emergency_contact, bio, team_tag_value, datetime.now().isoformat(), edit_id))

                            log_audit(f"Updated employee: {first_name} {last_name}", "employees", edit_id)
                            st.success(f"✅ Employee {first_name} {last_name} updated successfully!")
                        else:
                            # Insert new employee
                            cursor.execute("""
                                INSERT INTO employees (
                                    first_name, last_name, employee_id, email, phone,
                                    date_of_birth, gender, department, position, manager_id,
                                    grade, status, join_date, location, national_id, address,
                                    emergency_contact, bio, team_tag, created_at, updated_at
                                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                            """, (first_name, last_name, employee_id, email, phone,
                                 date_of_birth, gender, department, position, manager_id,
                                 grade, status, join_date, location, national_id, address,
                                 emergency_contact, bio, team_tag_value,
                                 datetime.now().isoformat(), datetime.now().isoformat()))

                            new_emp_id = cursor.lastrowid

                            # Create leave balances for new employee
                            leave_types = [
                                ('Annual Leave', 20.0),
                                ('Sick Leave', 10.0),
                                ('Personal Leave', 5.0)
                            ]
                            for leave_type, total_days in leave_types:
                                cursor.execute("""
                                    INSERT INTO leave_balance (emp_id, leave_type, total_days, remaining_days, year)
                                    VALUES (%s, %s, %s, %s, %s)
                                """, (new_emp_id, leave_type, total_days, total_days, datetime.now().year))

                            # Create user account
                            from auth import hash_password
                            cursor.execute("""
                                INSERT INTO users (username, password, role, employee_id, is_active)
                                VALUES (%s, %s, 'employee', %s, 1)
                            """, (email, hash_password('emp123'), new_emp_id))

                            log_audit(f"Created new employee: {first_name} {last_name}", "employees", new_emp_id)
                            st.success(f"✅ Employee {first_name} {last_name} created successfully!")

                        conn.commit()
                        st.session_state.show_employee_modal = False
                        st.rerun()

                except Exception as e:
                    st.error(f"Error: {str(e)}")

def get_departments():
    """Get list of departments"""
    return [
        "Engineering",
        "Marketing",
        "Finance",
        "Human Resources",
        "Operations",
        "Sales",
        "Legal",
        "Design",
        "Product",
        "Customer Support"
    ]

def get_manager_list():
    """Get list of employees who can be managers"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, first_name, last_name, position
            FROM employees
            WHERE status = 'Active'
            AND position LIKE '%Manager%' OR position LIKE '%Director%' OR position LIKE '%Head%'
            ORDER BY first_name
        """)
        return [dict(row) for row in cursor.fetchall()]
