"""
Employee Profile Manager Module
Allows employees to view and update their profile with approval workflow
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from database import get_db_connection
from auth import get_current_user, is_hr_admin, is_manager, create_notification, log_audit

def show_profile_manager():
    """Main profile manager interface"""
    user = get_current_user()

    st.markdown("## 👤 My Profile Manager")
    st.markdown("View and update your profile information")
    st.markdown("---")

    tabs = st.tabs(["📋 Profile Info", "✏️ Update Requests", "🎯 My Skills", "📝 Custom Fields"])

    with tabs[0]:
        show_profile_info()

    with tabs[1]:
        show_update_requests()

    with tabs[2]:
        show_my_skills()

    with tabs[3]:
        show_custom_fields()

def show_profile_info():
    """Display current profile information"""
    user = get_current_user()

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT e.*, t.team_name, p.position_name, p.level
            FROM employees e
            LEFT JOIN teams t ON e.team_tag = (SELECT team_name FROM teams WHERE id = (
                SELECT team_id FROM positions WHERE position_name = e.position LIMIT 1
            ))
            LEFT JOIN positions p ON e.position = p.position_name
            WHERE e.id = %s
        """, (user['employee_id'],))
        employee = cursor.fetchone()

    if not employee:
        st.error("Employee not found")
        return

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Basic Information")
        st.markdown(f"**Employee ID:** {employee['employee_id']}")
        st.markdown(f"**Name:** {employee['first_name']} {employee['last_name']}")
        st.markdown(f"**Email:** {employee['email']}")
        st.markdown(f"**Phone:** {employee['phone'] or 'Not set'}")
        st.markdown(f"**Department:** {employee['department']}")
        st.markdown(f"**Position:** {employee['position']}")
        st.markdown(f"**Grade:** {employee['grade'] or 'Not assigned'}")
        st.markdown(f"**Status:** {employee['status']}")

    with col2:
        st.markdown("### Additional Information")
        st.markdown(f"**Date of Birth:** {employee['date_of_birth'] or 'Not set'}")
        st.markdown(f"**Gender:** {employee['gender'] or 'Not set'}")
        st.markdown(f"**Join Date:** {employee['join_date']}")
        st.markdown(f"**Location:** {employee['location'] or 'Not set'}")
        st.markdown(f"**Address:** {employee['address'] or 'Not set'}")
        st.markdown(f"**Emergency Contact:** {employee['emergency_contact'] or 'Not set'}")

    st.markdown("---")
    st.markdown("### 📝 Request Profile Update")
    st.info("To update any information, submit a request below. It will be reviewed by your manager and HR.")

    with st.form("profile_update_form"):
        field = st.selectbox("Select Field to Update", [
            "phone", "address", "emergency_contact", "location",
            "date_of_birth", "gender", "bio"
        ])

        current_value = employee.get(field, "")
        st.text_input("Current Value", value=current_value or "Not set", disabled=True)

        new_value = st.text_input("New Value *", placeholder="Enter new value")
        reason = st.text_area("Reason for Update *", placeholder="Why are you updating this field?")

        if st.form_submit_button("Submit Request", use_container_width=True):
            if new_value and reason:
                with get_db_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT INTO profile_update_requests
                        (emp_id, field_name, current_value, requested_value, reason, status, requested_date)
                        VALUES (%s, %s, %s, %s, %s, %s, NOW())
                    """, (user['employee_id'], field, current_value, new_value, reason, 'Pending'))
                    conn.commit()

                st.success("✅ Update request submitted! Your manager will review it.")
                st.rerun()
            else:
                st.error("Please fill in all required fields")

def show_update_requests():
    """Show employee's profile update requests"""
    user = get_current_user()

    st.markdown("### Your Update Requests")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT pur.*,
                   m.first_name || ' ' || m.last_name as manager_name,
                   hr.first_name || ' ' || hr.last_name as hr_name
            FROM profile_update_requests pur
            LEFT JOIN employees m ON pur.manager_approved_by = m.id
            LEFT JOIN employees hr ON pur.hr_approved_by = hr.id
            WHERE pur.emp_id = %s
            ORDER BY pur.requested_date DESC
        """, (user['employee_id'],))
        requests = cursor.fetchall()

    if not requests:
        st.info("No update requests submitted")
        return

    for req in requests:
        status_color = {
            'Pending': '🟡',
            'Manager Approved': '🟢',
            'HR Approved': '✅',
            'Rejected': '🔴'
        }.get(req['status'], '⚪')

        with st.expander(f"{status_color} {req['field_name']} - {req['status']} ({req['requested_date'].strftime('%Y-%m-%d')})"):
            col1, col2 = st.columns(2)

            with col1:
                st.markdown(f"**Current Value:** {req['current_value'] or 'None'}")
                st.markdown(f"**Requested Value:** {req['requested_value']}")
                st.markdown(f"**Reason:** {req['reason']}")

            with col2:
                st.markdown(f"**Status:** {req['status']}")
                st.markdown(f"**Requested:** {req['requested_date'].strftime('%Y-%m-%d %H:%M')}")

                if req['manager_approved_by']:
                    st.markdown(f"**Manager:** {req['manager_name']} ({req['manager_approval_date'].strftime('%Y-%m-%d')})")
                    if req['manager_comments']:
                        st.markdown(f"*Manager Comment:* {req['manager_comments']}")

                if req['hr_approved_by']:
                    st.markdown(f"**HR:** {req['hr_name']} ({req['hr_approval_date'].strftime('%Y-%m-%d')})")
                    if req['hr_comments']:
                        st.markdown(f"*HR Comment:* {req['hr_comments']}")

def show_my_skills():
    """Display employee's skills"""
    user = get_current_user()

    st.markdown("### 🎯 My Skills")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT s.skill_name, s.category, es.proficiency_level,
                   es.years_experience, es.certified, es.created_at
            FROM employee_skills es
            JOIN skills s ON es.skill_id = s.id
            WHERE es.emp_id = %s
            ORDER BY s.category, s.skill_name
        """, (user['employee_id'],))
        skills = cursor.fetchall()

    if not skills:
        st.info("No skills recorded yet. Contact HR to add your skills.")
        return

    # Group by category
    categories = {}
    for skill in skills:
        cat = skill['category']
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(skill)

    for category, cat_skills in categories.items():
        st.markdown(f"#### {category}")

        cols = st.columns(3)
        for idx, skill in enumerate(cat_skills):
            with cols[idx % 3]:
                cert_badge = "🏆 Certified" if skill['certified'] else ""
                st.markdown(f"""
                    <div style="background: linear-gradient(135deg, #0e1117, #1c2535);
                                padding: 15px; border-radius: 10px; border: 1px solid #22304a;
                                margin-bottom: 10px;">
                        <h4 style="margin: 0; color: #c9963a;">{skill['skill_name']}</h4>
                        <p style="margin: 5px 0; color: #7d96be;">
                            <strong>Level:</strong> {skill['proficiency_level']}<br>
                            <strong>Experience:</strong> {skill['years_experience']} years<br>
                            {cert_badge}
                        </p>
                    </div>
                """, unsafe_allow_html=True)

def show_custom_fields():
    """Display and edit custom profile fields"""
    user = get_current_user()

    st.markdown("### 📝 Additional Information")

    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Get all active custom fields
        cursor.execute("""
            SELECT cpf.*, ecf.field_value
            FROM custom_profile_fields cpf
            LEFT JOIN employee_custom_fields ecf
                ON cpf.id = ecf.field_id AND ecf.emp_id = %s
            WHERE cpf.status = 'Active'
            ORDER BY cpf.category, cpf.field_label
        """, (user['employee_id'],))
        fields = cursor.fetchall()

    if not fields:
        st.info("No custom fields configured")
        return

    # Group by category
    categories = {}
    for field in fields:
        cat = field['category'] or 'Other'
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(field)

    for category, cat_fields in categories.items():
        st.markdown(f"#### {category}")

        for field in cat_fields:
            col1, col2 = st.columns([3, 1])

            with col1:
                current_value = field['field_value'] or 'Not set'
                st.text_input(
                    field['field_label'],
                    value=current_value,
                    disabled=True,
                    key=f"custom_{field['id']}"
                )

            with col2:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("Update", key=f"update_{field['id']}"):
                    st.session_state[f'editing_{field["id"]}'] = True
                    st.rerun()

        st.markdown("---")

    st.info("💡 To update these fields, submit a profile update request above.")

# Approval interface for managers and HR
def show_approval_interface():
    """Interface for managers and HR to approve profile updates"""
    user = get_current_user()

    if not (is_manager() or is_hr_admin()):
        st.error("Access denied")
        return

    st.markdown("## ✅ Profile Update Approvals")
    st.markdown("Review and approve employee profile change requests")
    st.markdown("---")

    with get_db_connection() as conn:
        cursor = conn.cursor()

        if is_manager():
            # Get requests from team members
            cursor.execute("""
                SELECT pur.*,
                       e.first_name || ' ' || e.last_name as employee_name,
                       e.employee_id, e.position
                FROM profile_update_requests pur
                JOIN employees e ON pur.emp_id = e.id
                WHERE e.manager_id = %s AND pur.status = 'Pending'
                ORDER BY pur.requested_date DESC
            """, (user['employee_id'],))
        else:  # HR Admin
            # Get requests approved by manager
            cursor.execute("""
                SELECT pur.*,
                       e.first_name || ' ' || e.last_name as employee_name,
                       e.employee_id, e.position
                FROM profile_update_requests pur
                JOIN employees e ON pur.emp_id = e.id
                WHERE pur.status = 'Manager Approved'
                ORDER BY pur.requested_date DESC
            """)

        requests = cursor.fetchall()

    if not requests:
        st.success("No pending approvals!")
        return

    for req in requests:
        with st.expander(f"📝 {req['employee_name']} ({req['employee_id']}) - {req['field_name']}"):
            col1, col2 = st.columns([2, 1])

            with col1:
                st.markdown(f"**Employee:** {req['employee_name']} ({req['position']})")
                st.markdown(f"**Field:** {req['field_name']}")
                st.markdown(f"**Current Value:** {req['current_value'] or 'None'}")
                st.markdown(f"**Requested Value:** {req['requested_value']}")
                st.markdown(f"**Reason:** {req['reason']}")
                st.markdown(f"**Requested:** {req['requested_date'].strftime('%Y-%m-%d %H:%M')}")

            with col2:
                comments = st.text_area("Comments (optional)", key=f"comments_{req['id']}")

                col_a, col_b = st.columns(2)
                with col_a:
                    if st.button("✅ Approve", key=f"approve_{req['id']}", use_container_width=True):
                        approve_request(req['id'], req['emp_id'], req['field_name'],
                                      req['requested_value'], comments, is_hr_admin())
                        st.success("Approved!")
                        st.rerun()

                with col_b:
                    if st.button("❌ Reject", key=f"reject_{req['id']}", use_container_width=True):
                        reject_request(req['id'], comments, is_hr_admin())
                        st.warning("Rejected")
                        st.rerun()

def approve_request(request_id, emp_id, field_name, new_value, comments, is_hr):
    """Approve a profile update request"""
    user = get_current_user()

    with get_db_connection() as conn:
        cursor = conn.cursor()

        if is_hr:
            # HR final approval - update employee record
            cursor.execute(f"""
                UPDATE employees
                SET {field_name} = %s
                WHERE id = %s
            """, (new_value, emp_id))

            cursor.execute("""
                UPDATE profile_update_requests
                SET status = 'HR Approved',
                    hr_approved_by = %s,
                    hr_approval_date = NOW(),
                    hr_comments = %s
                WHERE id = %s
            """, (user['employee_id'], comments, request_id))

            # Notify employee
            create_notification(
                emp_id,
                "Profile Update Approved",
                f"Your profile update request for '{field_name}' has been approved by HR. Your profile has been updated.",
                'success'
            )

            log_audit(f"HR approved profile update request {request_id}", "profile_update_requests", request_id)
        else:
            # Manager approval
            cursor.execute("""
                UPDATE profile_update_requests
                SET status = 'Manager Approved',
                    manager_approved_by = %s,
                    manager_approval_date = NOW(),
                    manager_comments = %s
                WHERE id = %s
            """, (user['employee_id'], comments, request_id))

            # Notify employee and HR
            create_notification(
                emp_id,
                "Profile Update - Manager Approved",
                f"Your profile update request for '{field_name}' has been approved by your manager. Awaiting HR approval.",
                'info'
            )

            # Notify HR
            cursor.execute("SELECT id FROM employees WHERE department = 'Human Resources' LIMIT 1")
            hr_emp = cursor.fetchone()
            if hr_emp:
                create_notification(
                    hr_emp['id'],
                    "Profile Update - HR Approval Required",
                    f"A profile update request (#{request_id}) has been approved by manager and requires HR approval.",
                    'info'
                )

            log_audit(f"Manager approved profile update request {request_id}", "profile_update_requests", request_id)

        conn.commit()

def reject_request(request_id, comments, is_hr):
    """Reject a profile update request"""
    user = get_current_user()

    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Get employee ID for notification
        cursor.execute("SELECT emp_id, field_name FROM profile_update_requests WHERE id = %s", (request_id,))
        req = cursor.fetchone()
        emp_id = req['emp_id']
        field_name = req['field_name']

        if is_hr:
            cursor.execute("""
                UPDATE profile_update_requests
                SET status = 'Rejected',
                    hr_approved_by = %s,
                    hr_approval_date = NOW(),
                    hr_comments = %s
                WHERE id = %s
            """, (user['employee_id'], comments, request_id))

            # Notify employee
            create_notification(
                emp_id,
                "Profile Update Rejected",
                f"Your profile update request for '{field_name}' has been rejected by HR. Reason: {comments or 'No reason provided'}",
                'warning'
            )

            log_audit(f"HR rejected profile update request {request_id}", "profile_update_requests", request_id)
        else:
            cursor.execute("""
                UPDATE profile_update_requests
                SET status = 'Rejected',
                    manager_approved_by = %s,
                    manager_approval_date = NOW(),
                    manager_comments = %s
                WHERE id = %s
            """, (user['employee_id'], comments, request_id))

            # Notify employee
            create_notification(
                emp_id,
                "Profile Update Rejected",
                f"Your profile update request for '{field_name}' has been rejected by your manager. Reason: {comments or 'No reason provided'}",
                'warning'
            )

            log_audit(f"Manager rejected profile update request {request_id}", "profile_update_requests", request_id)

        conn.commit()
