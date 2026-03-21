"""
Leave Management Module
Complete workflow: Employee Submit → Manager Approve → HR Approve
"""

import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
from database import get_db_connection
from auth import (get_current_user, is_hr_admin, is_manager, is_employee,
                 get_accessible_employees, create_notification, log_audit)

def show_leave_management():
    """Main leave management interface"""
    user = get_current_user()

    st.markdown("## 📅 Leave Management")
    st.markdown("Submit leave requests and track approval status")
    st.markdown("---")

    # Show tabs based on role
    if is_employee() and not is_manager() and not is_hr_admin():
        tabs = st.tabs(["📝 My Leave", "📊 Leave Balance", "📜 Leave History"])
        with tabs[0]:
            show_my_leave()
        with tabs[1]:
            show_leave_balance()
        with tabs[2]:
            show_leave_history()
    else:
        tabs = st.tabs(["📝 Submit Leave", "⏳ Pending Approvals", "📊 Leave Balance", "📜 All Requests"])
        with tabs[0]:
            show_my_leave()
        with tabs[1]:
            show_pending_approvals()
        with tabs[2]:
            show_leave_balance()
        with tabs[3]:
            show_all_leave_requests()

def show_my_leave():
    """Employee leave submission interface"""
    user = get_current_user()

    st.markdown("### 📝 Submit Leave Request")

    # Get leave balance
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT leave_type, remaining_days
            FROM leave_balance
            WHERE emp_id = %s AND year = %s
        """, (user['employee_id'], datetime.now().year))
        leave_balance = {row['leave_type']: row['remaining_days'] for row in cursor.fetchall()}

    # Display leave balance summary
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("🌴 Annual Leave", f"{leave_balance.get('Annual Leave', 0):.1f} days")
    with col2:
        st.metric("🤒 Sick Leave", f"{leave_balance.get('Sick Leave', 0):.1f} days")
    with col3:
        st.metric("🏠 Personal Leave", f"{leave_balance.get('Personal Leave', 0):.1f} days")

    st.markdown("---")

    # Leave request form
    with st.form("leave_request_form"):
        col1, col2 = st.columns(2)

        with col1:
            leave_type = st.selectbox(
                "Leave Type *",
                options=list(leave_balance.keys())
            )

            start_date = st.date_input(
                "Start Date *",
                min_value=date.today(),
                value=date.today()
            )

        with col2:
            end_date = st.date_input(
                "End Date *",
                min_value=start_date if start_date else date.today(),
                value=start_date if start_date else date.today()
            )

            # Calculate days
            if start_date and end_date:
                days = (end_date - start_date).days + 1
                st.metric("Total Days", f"{days} days")
            else:
                days = 0

        reason = st.text_area("Reason *", placeholder="Please provide a reason for your leave request...")

        submitted = st.form_submit_button("📤 Submit Leave Request", use_container_width=True)

        if submitted:
            if not all([leave_type, start_date, end_date, reason]):
                st.error("❌ Please fill all required fields")
            elif days <= 0:
                st.error("❌ End date must be after start date")
            elif days > leave_balance.get(leave_type, 0):
                st.error(f"❌ Insufficient leave balance. You have {leave_balance.get(leave_type, 0):.1f} days available.")
            else:
                try:
                    with get_db_connection() as conn:
                        cursor = conn.cursor()

                        # Insert leave request
                        cursor.execute("""
                            INSERT INTO leave_requests (
                                emp_id, leave_type, start_date, end_date, days, reason, status
                            ) VALUES (%s, ?, ?, ?, ?, ?, 'Pending')
                        """, (user['employee_id'], leave_type, start_date.isoformat(),
                             end_date.isoformat(), days, reason))

                        request_id = cursor.lastrowid

                        # Get manager for notification
                        cursor.execute("SELECT manager_id FROM employees WHERE id = %s", (user['employee_id'],))
                        manager_id = cursor.fetchone()['manager_id']

                        if manager_id:
                            create_notification(
                                manager_id,
                                "New Leave Request",
                                f"{user['full_name']} has requested {days} days of {leave_type} from {start_date} to {end_date}.",
                                'info'
                            )

                        conn.commit()
                        log_audit(f"Submitted leave request: {leave_type} ({days} days)", "leave_requests", request_id)

                        st.success(f"✅ Leave request submitted successfully! Request ID: LR-{request_id}")
                        st.balloons()
                        st.rerun()

                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")

    # Show my recent requests
    st.markdown("### 📋 My Recent Requests")
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM leave_requests
            WHERE emp_id = %s
            ORDER BY created_at DESC
            LIMIT 5
        """, (user['employee_id'],))
        my_requests = [dict(row) for row in cursor.fetchall()]

    if my_requests:
        for req in my_requests:
            status_color = {
                'Pending': '🟡',
                'Manager Approved': '🟢',
                'HR Approved': '✅',
                'Rejected': '🔴',
                'Cancelled': '⚪'
            }.get(req['status'], '⚪')

            st.markdown(f"""
                <div style="background: rgba(58, 123, 213, 0.05); padding: 15px; border-radius: 10px; margin-bottom: 10px; border-left: 3px solid #3a7bd5;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <strong>{status_color} {req['leave_type']}</strong><br>
                            <small style="color: #7d96be;">
                                📅 {req['start_date']} to {req['end_date']} ({req['days']} days)<br>
                                Status: {req['status']}
                            </small>
                        </div>
                        <div style="text-align: right;">
                            <small style="color: #7d96be;">LR-{req['id']}</small>
                        </div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No leave requests yet")

def show_pending_approvals():
    """Show pending leave requests for manager/HR to approve"""
    user = get_current_user()

    st.markdown("### ⏳ Pending Leave Approvals")

    with get_db_connection() as conn:
        cursor = conn.cursor()

        if is_hr_admin():
            # HR sees manager-approved requests
            cursor.execute("""
                SELECT lr.*, e.first_name, e.last_name, e.employee_id, e.department, e.position
                FROM leave_requests lr
                JOIN employees e ON lr.emp_id = e.id
                WHERE lr.status = 'Manager Approved'
                ORDER BY lr.created_at DESC
            """)
        elif is_manager():
            # Manager sees pending requests from their team
            cursor.execute("""
                SELECT lr.*, e.first_name, e.last_name, e.employee_id, e.department, e.position
                FROM leave_requests lr
                JOIN employees e ON lr.emp_id = e.id
                WHERE lr.status = 'Pending' AND e.manager_id = %s
                ORDER BY lr.created_at DESC
            """, (user['employee_id'],))
        else:
            st.info("No pending approvals")
            return

        pending = [dict(row) for row in cursor.fetchall()]

    if not pending:
        st.success("✅ No pending approvals!")
        return

    for req in pending:
        with st.expander(f"🔔 {req['first_name']} {req['last_name']} - {req['leave_type']} ({req['days']} days)"):
            col1, col2 = st.columns([2, 1])

            with col1:
                st.markdown(f"""
                **Employee:** {req['first_name']} {req['last_name']} ({req['employee_id']})
                **Position:** {req['position']}
                **Department:** {req['department']}
                **Leave Type:** {req['leave_type']}
                **Duration:** {req['start_date']} to {req['end_date']} ({req['days']} days)
                **Reason:** {req['reason']}
                **Current Status:** {req['status']}
                **Submitted:** {req['created_at']}
                """)

            with col2:
                # Check leave balance
                cursor.execute("""
                    SELECT remaining_days FROM leave_balance
                    WHERE emp_id = %s AND leave_type = %s AND year = %s
                """, (req['emp_id'], req['leave_type'], datetime.now().year))
                balance = cursor.fetchone()
                balance_days = balance['remaining_days'] if balance else 0

                st.metric("Available Balance", f"{balance_days:.1f} days")

                if balance_days < req['days']:
                    st.warning("⚠️ Insufficient balance!")

            # Approval actions
            st.markdown("---")
            col1, col2, col3 = st.columns(3)

            with col1:
                if st.button(f"✅ Approve", key=f"approve_{req['id']}", use_container_width=True):
                    approve_leave_request(req['id'], req['emp_id'], req['leave_type'], req['days'])
                    st.rerun()

            with col2:
                if st.button(f"❌ Reject", key=f"reject_{req['id']}", use_container_width=True):
                    reject_leave_request(req['id'], req['emp_id'])
                    st.rerun()

            with col3:
                comments = st.text_input("Comments", key=f"comments_{req['id']}", placeholder="Optional comments...")

def approve_leave_request(request_id, emp_id, leave_type, days):
    """Approve leave request (manager or HR)"""
    user = get_current_user()

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # Get current status
            cursor.execute("SELECT status FROM leave_requests WHERE id = %s", (request_id,))
            current_status = cursor.fetchone()['status']

            if is_manager() and current_status == 'Pending':
                # Manager approval
                cursor.execute("""
                    UPDATE leave_requests SET
                        status = 'Manager Approved',
                        manager_approved_by = %s,
                        manager_approval_date = %s
                    WHERE id = %s
                """, (user['employee_id'], datetime.now().isoformat(), request_id))

                # Notify HR
                cursor.execute("SELECT id FROM employees WHERE department = 'Human Resources' LIMIT 1")
                hr_emp = cursor.fetchone()
                if hr_emp:
                    create_notification(
                        hr_emp['id'],
                        "Leave Request - HR Approval Required",
                        f"A leave request (LR-{request_id}) has been approved by manager and requires HR approval.",
                        'info'
                    )

                # Notify employee
                create_notification(
                    emp_id,
                    "Leave Request Approved by Manager",
                    f"Your leave request (LR-{request_id}) has been approved by your manager. Awaiting HR approval.",
                    'success'
                )

                log_audit(f"Manager approved leave request LR-{request_id}", "leave_requests", request_id)
                st.success("✅ Leave request approved! Sent to HR for final approval.")

            elif is_hr_admin() and current_status == 'Manager Approved':
                # HR final approval
                cursor.execute("""
                    UPDATE leave_requests SET
                        status = 'HR Approved',
                        hr_approved_by = %s,
                        hr_approval_date = %s
                    WHERE id = %s
                """, (user['employee_id'], datetime.now().isoformat(), request_id))

                # Update leave balance
                cursor.execute("""
                    UPDATE leave_balance SET
                        used_days = used_days + %s,
                        remaining_days = remaining_days - ?
                    WHERE emp_id = %s AND leave_type = %s AND year = %s
                """, (days, days, emp_id, leave_type, datetime.now().year))

                # Notify employee
                create_notification(
                    emp_id,
                    "Leave Request Fully Approved",
                    f"Your leave request (LR-{request_id}) has been fully approved by HR. Your leave balance has been updated.",
                    'success'
                )

                log_audit(f"HR approved leave request LR-{request_id}", "leave_requests", request_id)
                st.success("✅ Leave request fully approved! Leave balance updated.")

            conn.commit()

    except Exception as e:
        st.error(f"❌ Error: {str(e)}")

def reject_leave_request(request_id, emp_id):
    """Reject leave request"""
    user = get_current_user()

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                UPDATE leave_requests SET status = 'Rejected' WHERE id = %s
            """, (request_id,))

            # Notify employee
            create_notification(
                emp_id,
                "Leave Request Rejected",
                f"Your leave request (LR-{request_id}) has been rejected. Please contact your manager for details.",
                'error'
            )

            conn.commit()
            log_audit(f"Rejected leave request LR-{request_id}", "leave_requests", request_id)
            st.warning("⚠️ Leave request rejected")

    except Exception as e:
        st.error(f"❌ Error: {str(e)}")

def show_leave_balance():
    """Show leave balance for current user"""
    user = get_current_user()

    st.markdown("### 📊 Leave Balance")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM leave_balance
            WHERE emp_id = %s AND year = %s
        """, (user['employee_id'], datetime.now().year))
        balances = [dict(row) for row in cursor.fetchall()]

    if balances:
        col1, col2, col3 = st.columns(3)

        for idx, balance in enumerate(balances):
            with [col1, col2, col3][idx % 3]:
                used_pct = (balance['used_days'] / balance['total_days'] * 100) if balance['total_days'] > 0 else 0

                st.markdown(f"""
                    <div style="background: linear-gradient(135deg, #0e1117, #1c2535);
                                padding: 20px; border-radius: 12px; border: 1px solid #22304a; text-align: center;">
                        <h4 style="color: #c9963a; margin: 0 0 10px 0;">{balance['leave_type']}</h4>
                        <div style="font-size: 32px; font-weight: bold; color: #5b9cf6; margin: 10px 0;">
                            {balance['remaining_days']:.1f}
                        </div>
                        <small style="color: #7d96be;">days remaining</small>
                        <div style="margin-top: 10px; font-size: 12px; color: #7d96be;">
                            Used: {balance['used_days']:.1f} / {balance['total_days']:.1f} days
                        </div>
                        <div style="background: #1c2535; border-radius: 10px; height: 6px; margin-top: 10px; overflow: hidden;">
                            <div style="background: linear-gradient(90deg, #3a7bd5, #c9963a); height: 100%; width: {used_pct}%;"></div>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
    else:
        st.info("No leave balance data available")

def show_leave_history():
    """Show complete leave history"""
    user = get_current_user()

    st.markdown("### 📜 Leave History")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM leave_requests
            WHERE emp_id = %s
            ORDER BY created_at DESC
        """, (user['employee_id'],))
        history = [dict(row) for row in cursor.fetchall()]

    if history:
        df = pd.DataFrame(history)
        display_columns = ['id', 'leave_type', 'start_date', 'end_date', 'days', 'status', 'created_at']
        df_display = df[display_columns]
        df_display.columns = ['ID', 'Leave Type', 'Start Date', 'End Date', 'Days', 'Status', 'Submitted']

        st.dataframe(df_display, use_container_width=True, hide_index=True)
    else:
        st.info("No leave history found")

def show_all_leave_requests():
    """Show all leave requests (for managers and HR)"""
    user = get_current_user()

    st.markdown("### 📜 All Leave Requests")

    # Filters
    col1, col2, col3 = st.columns(3)
    with col1:
        status_filter = st.selectbox("Status", ["All", "Pending", "Manager Approved", "HR Approved", "Rejected"])
    with col2:
        leave_type_filter = st.selectbox("Leave Type", ["All", "Annual Leave", "Sick Leave", "Personal Leave"])
    with col3:
        search = st.text_input("🔍 Search employee")

    with get_db_connection() as conn:
        cursor = conn.cursor()

        if is_hr_admin():
            query = """
                SELECT lr.*, e.first_name, e.last_name, e.employee_id, e.department
                FROM leave_requests lr
                JOIN employees e ON lr.emp_id = e.id
                WHERE 1=1
            """
            params = []
        elif is_manager():
            query = """
                SELECT lr.*, e.first_name, e.last_name, e.employee_id, e.department
                FROM leave_requests lr
                JOIN employees e ON lr.emp_id = e.id
                WHERE e.manager_id = %s
            """
            params = [user['employee_id']]
        else:
            st.info("Access restricted")
            return

        if status_filter != "All":
            query += " AND lr.status = %s"
            params.append(status_filter)

        if leave_type_filter != "All":
            query += " AND lr.leave_type = %s"
            params.append(leave_type_filter)

        if search:
            query += " AND (e.first_name LIKE %s OR e.last_name LIKE %s OR e.employee_id LIKE %s)"
            params.extend([f"%{search}%", f"%{search}%", f"%{search}%"])

        query += " ORDER BY lr.created_at DESC LIMIT 50"

        cursor.execute(query, params)
        requests = [dict(row) for row in cursor.fetchall()]

    if requests:
        df = pd.DataFrame(requests)
        display_columns = ['employee_id', 'first_name', 'last_name', 'leave_type', 'start_date', 'end_date', 'days', 'status']
        df_display = df[display_columns]
        df_display.columns = ['Emp ID', 'First Name', 'Last Name', 'Leave Type', 'Start', 'End', 'Days', 'Status']

        st.dataframe(df_display, use_container_width=True, hide_index=True)
    else:
        st.info("No leave requests found")
