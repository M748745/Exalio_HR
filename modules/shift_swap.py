"""
Shift Swap Approval Module
Manage shift swap requests, approvals, and schedule updates
"""

import streamlit as st
from datetime import datetime, date
from database import get_db_connection
from auth import get_current_user, is_hr_admin, is_manager, create_notification, log_audit

def show_shift_swap():
    """Main shift swap interface"""
    user = get_current_user()

    st.markdown("## 🔄 Shift Swap Management")
    st.markdown("Request and approve shift swaps between employees")
    st.markdown("---")

    if is_hr_admin():
        tabs = st.tabs(["📊 All Requests", "✅ Pending Approvals", "📅 Approved Swaps"])
    elif is_manager():
        tabs = st.tabs(["📋 Team Requests", "✅ Approve Swaps"])
    else:
        tabs = st.tabs(["📋 My Requests", "➕ Request Swap"])

    with tabs[0]:
        if is_hr_admin():
            show_all_swap_requests()
        elif is_manager():
            show_team_swap_requests()
        else:
            show_my_swap_requests()

    with tabs[1]:
        if is_hr_admin():
            show_pending_approvals()
        elif is_manager():
            approve_swap_requests()
        else:
            request_shift_swap()

    if is_hr_admin() and len(tabs) > 2:
        with tabs[2]:
            show_approved_swaps()

def show_all_swap_requests():
    """Show all shift swap requests"""
    st.markdown("### 📊 All Shift Swap Requests")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT ss.*,
                   e1.first_name as requester_first, e1.last_name as requester_last,
                   e2.first_name as swapper_first, e2.last_name as swapper_last
            FROM shift_swaps ss
            JOIN employees e1 ON ss.requester_emp_id = e1.id
            JOIN employees e2 ON ss.swapper_emp_id = e2.id
            ORDER BY ss.request_date DESC
        """)
        swaps = [dict(row) for row in cursor.fetchall()]

    if swaps:
        for swap in swaps:
            status_icon = '✅' if swap['status'] == 'Approved' else '🔴' if swap['status'] == 'Rejected' else '🟡'
            with st.expander(f"{status_icon} {swap['requester_first']} {swap['requester_last']} ↔️ {swap['swapper_first']} {swap['swapper_last']} - {swap['status']}"):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Shift Date:** {swap['shift_date']}")
                    st.write(f"**Shift Type:** {swap['shift_type']}")
                    st.write(f"**Request Date:** {swap['request_date']}")
                with col2:
                    st.write(f"**Status:** {swap['status']}")
                    st.write(f"**Reason:** {swap.get('reason', 'N/A')}")

                if swap['status'] == 'Pending':
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button(f"✅ Approve - {swap['id']}", key=f"approve_{swap['id']}"):
                            with get_db_connection() as conn:
                                cursor = conn.cursor()
                                cursor.execute("""
                                    UPDATE shift_swaps SET
                                        status = 'Approved',
                                        approved_by = %s,
                                        approval_date = %s
                                    WHERE id = %s
                                """, (get_current_user()['employee_id'], date.today(), swap['id']))
                                conn.commit()
                            create_notification(swap['requester_emp_id'], "Shift Swap Approved",
                                              f"Your shift swap request for {swap['shift_date']} has been approved", "success")
                            create_notification(swap['swapper_emp_id'], "Shift Swap Approved",
                                              f"Shift swap confirmed for {swap['shift_date']}", "success")
                            st.success("✅ Approved!")
                            st.rerun()
                    with col2:
                        if st.button(f"❌ Reject - {swap['id']}", key=f"reject_{swap['id']}"):
                            with get_db_connection() as conn:
                                cursor = conn.cursor()
                                cursor.execute("""
                                    UPDATE shift_swaps SET status = 'Rejected' WHERE id = %s
                                """, (swap['id'],))
                                conn.commit()
                            create_notification(swap['requester_emp_id'], "Shift Swap Rejected",
                                              "Your shift swap request was not approved", "error")
                            st.warning("Rejected")
                            st.rerun()
    else:
        st.info("No shift swap requests")

def request_shift_swap():
    """Request shift swap"""
    user = get_current_user()
    st.markdown("### ➕ Request Shift Swap")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT department FROM employees WHERE id = %s", (user['employee_id'],))
        dept_row = cursor.fetchone()

        if dept_row:
            dept = dept_row['department']
            cursor.execute("""
                SELECT id, first_name, last_name, position
                FROM employees
                WHERE department = %s AND id != %s AND status = 'Active'
                ORDER BY first_name
            """, (dept, user['employee_id']))
            colleagues = [dict(row) for row in cursor.fetchall()]

            if colleagues:
                with st.form("swap_request"):
                    emp_options = {f"{c['first_name']} {c['last_name']} - {c['position']}": c['id'] for c in colleagues}
                    swap_with = st.selectbox("Swap With *", list(emp_options.keys()))

                    col1, col2 = st.columns(2)
                    with col1:
                        shift_date = st.date_input("Shift Date *")
                        shift_type = st.selectbox("Shift Type *", ["Morning", "Afternoon", "Evening", "Night", "Full Day"])
                    with col2:
                        reason = st.text_area("Reason for Swap *")

                    submitted = st.form_submit_button("💾 Submit Request")

                    if submitted and swap_with and reason:
                        swapper_id = emp_options[swap_with]

                        with get_db_connection() as conn:
                            cursor = conn.cursor()
                            cursor.execute("""
                                INSERT INTO shift_swaps (requester_emp_id, swapper_emp_id, shift_date,
                                                        shift_type, reason, request_date, status)
                                VALUES (%s, %s, %s, %s, %s, %s, 'Pending')
                            """, (user['employee_id'], swapper_id, shift_date, shift_type, reason, date.today()))
                            conn.commit()

                        create_notification(swapper_id, "Shift Swap Request",
                                          f"{user['first_name']} {user['last_name']} requests to swap shifts with you on {shift_date}", "info")
                        log_audit(user['id'], f"Requested shift swap for {shift_date}", "shift_swaps")
                        st.success("✅ Shift swap request submitted!")
            else:
                st.info("No colleagues available for shift swap")

def show_my_swap_requests():
    """Show employee's swap requests"""
    user = get_current_user()
    st.markdown("### 📋 My Shift Swap Requests")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT ss.*, e.first_name, e.last_name
            FROM shift_swaps ss
            JOIN employees e ON ss.swapper_emp_id = e.id
            WHERE ss.requester_emp_id = %s
            ORDER BY ss.request_date DESC
        """, (user['employee_id'],))
        requests = [dict(row) for row in cursor.fetchall()]

    if requests:
        for req in requests:
            status_icon = '✅' if req['status'] == 'Approved' else '🔴' if req['status'] == 'Rejected' else '🟡'
            st.write(f"{status_icon} Swap with {req['first_name']} {req['last_name']} on {req['shift_date']} - {req['shift_type']} - {req['status']}")
    else:
        st.info("No shift swap requests")

def show_team_swap_requests():
    """Show team shift swap requests"""
    user = get_current_user()
    st.markdown("### 📋 Team Shift Swap Requests")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT department FROM employees WHERE id = %s", (user['employee_id'],))
        dept_row = cursor.fetchone()

        if dept_row:
            dept = dept_row['department']
            cursor.execute("""
                SELECT ss.*,
                       e1.first_name as req_first, e1.last_name as req_last,
                       e2.first_name as swap_first, e2.last_name as swap_last
                FROM shift_swaps ss
                JOIN employees e1 ON ss.requester_emp_id = e1.id
                JOIN employees e2 ON ss.swapper_emp_id = e2.id
                WHERE e1.department = %s
                ORDER BY ss.request_date DESC
            """, (dept,))
            swaps = [dict(row) for row in cursor.fetchall()]

            if swaps:
                for swap in swaps:
                    status_icon = '✅' if swap['status'] == 'Approved' else '🔴' if swap['status'] == 'Rejected' else '🟡'
                    st.write(f"{status_icon} {swap['req_first']} {swap['req_last']} ↔️ {swap['swap_first']} {swap['swap_last']} - {swap['shift_date']} - {swap['status']}")

def approve_swap_requests():
    """Approve shift swap requests"""
    st.markdown("### ✅ Approve Shift Swaps")

    user = get_current_user()
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT department FROM employees WHERE id = %s", (user['employee_id'],))
        dept_row = cursor.fetchone()

        if dept_row:
            dept = dept_row['department']
            cursor.execute("""
                SELECT ss.*,
                       e1.first_name as req_first, e1.last_name as req_last,
                       e2.first_name as swap_first, e2.last_name as swap_last
                FROM shift_swaps ss
                JOIN employees e1 ON ss.requester_emp_id = e1.id
                JOIN employees e2 ON ss.swapper_emp_id = e2.id
                WHERE e1.department = %s AND ss.status = 'Pending'
                ORDER BY ss.shift_date
            """, (dept,))
            pending = [dict(row) for row in cursor.fetchall()]

            if pending:
                for swap in pending:
                    with st.expander(f"{swap['req_first']} {swap['req_last']} ↔️ {swap['swap_first']} {swap['swap_last']} - {swap['shift_date']}"):
                        st.write(f"**Shift:** {swap['shift_type']}")
                        st.write(f"**Reason:** {swap['reason']}")

                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button(f"✅ Approve", key=f"app_{swap['id']}"):
                                with get_db_connection() as conn:
                                    cursor = conn.cursor()
                                    cursor.execute("""
                                        UPDATE shift_swaps SET
                                            status = 'Approved',
                                            approved_by = %s,
                                            approval_date = %s
                                        WHERE id = %s
                                    """, (user['employee_id'], date.today(), swap['id']))
                                    conn.commit()
                                create_notification(swap['requester_emp_id'], "Shift Swap Approved", "Your shift swap was approved", "success")
                                st.success("✅ Approved!")
                                st.rerun()
                        with col2:
                            if st.button(f"❌ Reject", key=f"rej_{swap['id']}"):
                                with get_db_connection() as conn:
                                    cursor = conn.cursor()
                                    cursor.execute("UPDATE shift_swaps SET status = 'Rejected' WHERE id = %s", (swap['id'],))
                                    conn.commit()
                                st.warning("Rejected")
                                st.rerun()
            else:
                st.success("✅ No pending swap requests")

def show_pending_approvals():
    """Show pending approvals"""
    st.markdown("### ✅ Pending Approvals")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT ss.*, e1.first_name as req_first, e1.last_name as req_last
            FROM shift_swaps ss
            JOIN employees e1 ON ss.requester_emp_id = e1.id
            WHERE ss.status = 'Pending'
            ORDER BY ss.shift_date
        """)
        pending = [dict(row) for row in cursor.fetchall()]

    if pending:
        for swap in pending:
            st.write(f"🟡 {swap['req_first']} {swap['req_last']} - {swap['shift_date']} - {swap['shift_type']}")
    else:
        st.success("✅ No pending approvals")

def show_approved_swaps():
    """Show approved swaps"""
    st.markdown("### 📅 Approved Shift Swaps")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT ss.*,
                   e1.first_name as req_first, e1.last_name as req_last,
                   e2.first_name as swap_first, e2.last_name as swap_last
            FROM shift_swaps ss
            JOIN employees e1 ON ss.requester_emp_id = e1.id
            JOIN employees e2 ON ss.swapper_emp_id = e2.id
            WHERE ss.status = 'Approved'
            ORDER BY ss.shift_date DESC
            LIMIT 50
        """)
        approved = [dict(row) for row in cursor.fetchall()]

    if approved:
        for swap in approved:
            st.write(f"✅ {swap['shift_date']}: {swap['req_first']} {swap['req_last']} ↔️ {swap['swap_first']} {swap['swap_last']} - {swap['shift_type']}")
    else:
        st.info("No approved swaps")
