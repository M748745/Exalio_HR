"""
Expense Claims Module
Submit and approve employee expense reimbursements
Workflow: Employee → Manager → Finance/HR
"""

import streamlit as st
import pandas as pd
from datetime import datetime, date
from database import get_db_connection
from auth import get_current_user, is_hr_admin, is_manager, is_employee, create_notification, log_audit

def show_expense_management():
    """Main expense management interface"""
    user = get_current_user()

    st.markdown("## 💰 Expense Claims")
    st.markdown("Submit and track expense reimbursements")
    st.markdown("---")

    if is_employee() and not is_manager() and not is_hr_admin():
        tabs = st.tabs(["📝 Submit Claim", "📋 My Claims", "📊 Summary"])
    else:
        tabs = st.tabs(["📝 Submit Claim", "⏳ Pending Approvals", "📋 All Claims", "📊 Statistics"])

    with tabs[0]:
        show_submit_expense()

    with tabs[1]:
        if is_employee() and not is_manager() and not is_hr_admin():
            show_my_claims()
        else:
            show_pending_approvals()

    with tabs[2]:
        if is_employee() and not is_manager() and not is_hr_admin():
            show_expense_summary()
        else:
            show_all_claims()

    if len(tabs) > 3:
        with tabs[3]:
            show_expense_statistics()

def show_submit_expense():
    """Form to submit expense claim"""
    user = get_current_user()

    st.markdown("### 📝 Submit Expense Claim")

    with st.form("expense_form"):
        col1, col2 = st.columns(2)

        with col1:
            expense_type = st.selectbox("Expense Type *", [
                "Travel",
                "Accommodation",
                "Meals",
                "Transportation",
                "Office Supplies",
                "Training & Education",
                "Client Entertainment",
                "Communication",
                "Other"
            ])

            amount = st.number_input("Amount ($) *", min_value=0.0, value=0.0, step=1.0)
            currency = st.selectbox("Currency", ["USD", "EUR", "GBP", "AED"])

        with col2:
            expense_date = st.date_input("Expense Date *", value=date.today(), max_value=date.today())

            description = st.text_area("Description *", placeholder="Provide details about this expense...")

        # Receipt upload simulation
        st.markdown("**📎 Receipt Upload**")
        receipt_file = st.file_uploader("Upload Receipt", type=['pdf', 'jpg', 'jpeg', 'png'], help="Max 5MB")

        submitted = st.form_submit_button("📤 Submit Claim", use_container_width=True)

        if submitted:
            if not all([expense_type, amount > 0, expense_date, description]):
                st.error("❌ Please fill all required fields")
            else:
                try:
                    with get_db_connection() as conn:
                        cursor = conn.cursor()

                        # Save receipt info (in production, would upload to storage)
                        receipt_path = f"receipts/{user['employee_id']}_{datetime.now().timestamp()}.pdf" if receipt_file else None

                        cursor.execute("""
                            INSERT INTO expenses (
                                emp_id, expense_type, amount, currency, expense_date,
                                description, receipt_path, status
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s, 'Pending')
                        """, (user['employee_id'], expense_type, amount, currency,
                             expense_date.isoformat(), description, receipt_path))

                        expense_id = cursor.lastrowid

                        # Notify manager
                        cursor.execute("SELECT manager_id FROM employees WHERE id = %s", (user['employee_id'],))
                        manager = cursor.fetchone()
                        if manager and manager['manager_id']:
                            create_notification(
                                manager['manager_id'],
                                "New Expense Claim",
                                f"{user['full_name']} submitted an expense claim of ${amount:.2f} for {expense_type}.",
                                'info'
                            )

                        conn.commit()
                        log_audit(f"Submitted expense claim: ${amount} for {expense_type}", "expenses", expense_id)

                        st.success(f"✅ Expense claim submitted successfully! Claim ID: EXP-{expense_id}")
                        st.balloons()
                        st.rerun()

                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")

def show_pending_approvals():
    """Show expenses pending approval"""
    user = get_current_user()

    st.markdown("### ⏳ Pending Approvals")

    with get_db_connection() as conn:
        cursor = conn.cursor()

        if is_hr_admin():
            # HR sees manager-approved claims
            cursor.execute("""
                SELECT ex.*, e.first_name, e.last_name, e.employee_id, e.department
                FROM expenses ex
                JOIN employees e ON ex.emp_id = e.id
                WHERE ex.status = 'Manager Approved'
                ORDER BY ex.created_at DESC
            """)
        elif is_manager():
            # Manager sees pending claims from team
            cursor.execute("""
                SELECT ex.*, e.first_name, e.last_name, e.employee_id, e.department
                FROM expenses ex
                JOIN employees e ON ex.emp_id = e.id
                WHERE ex.status = 'Pending' AND e.manager_id = %s
                ORDER BY ex.created_at DESC
            """, (user['employee_id'],))
        else:
            st.info("No approvals available")
            return

        pending = [dict(row) for row in cursor.fetchall()]

    if not pending:
        st.success("✅ No pending approvals!")
        return

    for expense in pending:
        with st.expander(f"💰 {expense['first_name']} {expense['last_name']} - ${expense['amount']:.2f} ({expense['expense_type']})"):
            col1, col2 = st.columns([2, 1])

            with col1:
                st.markdown(f"""
                **Employee:** {expense['first_name']} {expense['last_name']} ({expense['employee_id']})
                **Department:** {expense['department']}
                **Expense Type:** {expense['expense_type']}
                **Amount:** ${expense['amount']:.2f} {expense['currency']}
                **Date:** {expense['expense_date']}
                **Description:** {expense['description']}
                **Receipt:** {'✅ Attached' if expense['receipt_path'] else '❌ Not attached'}
                **Status:** {expense['status']}
                **Submitted:** {expense['created_at']}
                """)

            with col2:
                st.metric("Claim Amount", f"${expense['amount']:.2f}")

            # Approval actions
            st.markdown("---")
            col1, col2, col3 = st.columns(3)

            with col1:
                if st.button(f"✅ Approve", key=f"approve_exp_{expense['id']}", use_container_width=True):
                    approve_expense(expense['id'], expense['emp_id'], expense['amount'])
                    st.rerun()

            with col2:
                if st.button(f"❌ Reject", key=f"reject_exp_{expense['id']}", use_container_width=True):
                    reject_expense(expense['id'], expense['emp_id'])
                    st.rerun()

            with col3:
                comments = st.text_input("Comments", key=f"comments_exp_{expense['id']}", placeholder="Optional...")

def show_my_claims():
    """Show employee's own expense claims"""
    user = get_current_user()

    st.markdown("### 📋 My Expense Claims")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM expenses
            WHERE emp_id = %s
            ORDER BY created_at DESC
        """, (user['employee_id'],))
        claims = [dict(row) for row in cursor.fetchall()]

    if claims:
        for claim in claims:
            status_color = {
                'Pending': 'rgba(240, 180, 41, 0.1)',
                'Manager Approved': 'rgba(91, 156, 246, 0.1)',
                'Finance Approved': 'rgba(45, 212, 170, 0.1)',
                'Paid': 'rgba(45, 212, 170, 0.2)',
                'Rejected': 'rgba(241, 100, 100, 0.1)'
            }.get(claim['status'], 'rgba(58, 123, 213, 0.05)')

            st.markdown(f"""
                <div style="background: {status_color}; padding: 15px; border-radius: 10px; margin-bottom: 12px; border-left: 3px solid #c9963a;">
                    <strong>{claim['expense_type']}</strong> - ${claim['amount']:.2f} {claim['currency']}<br>
                    <small style="color: #7d96be;">
                        📅 {claim['expense_date']} • Status: {claim['status']}<br>
                        EXP-{claim['id']} • Submitted: {claim['created_at'][:10]}
                    </small>
                </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No expense claims yet")

def show_all_claims():
    """Show all expense claims"""
    user = get_current_user()

    st.markdown("### 📋 All Expense Claims")

    # Filters
    col1, col2, col3 = st.columns(3)
    with col1:
        status_filter = st.selectbox("Status", ["All", "Pending", "Manager Approved", "Finance Approved", "Paid", "Rejected"])
    with col2:
        type_filter = st.selectbox("Type", ["All", "Travel", "Accommodation", "Meals", "Transportation", "Office Supplies", "Other"])
    with col3:
        search = st.text_input("🔍 Search employee")

    with get_db_connection() as conn:
        cursor = conn.cursor()

        query = """
            SELECT ex.*, e.first_name, e.last_name, e.employee_id, e.department
            FROM expenses ex
            JOIN employees e ON ex.emp_id = e.id
            WHERE 1=1
        """
        params = []

        if is_manager() and not is_hr_admin():
            query += " AND e.manager_id = %s"
            params.append(user['employee_id'])

        if status_filter != "All":
            query += " AND ex.status = %s"
            params.append(status_filter)

        if type_filter != "All":
            query += " AND ex.expense_type = %s"
            params.append(type_filter)

        if search:
            query += " AND (e.first_name LIKE %s OR e.last_name LIKE %s OR e.employee_id LIKE %s)"
            params.extend([f"%{search}%", f"%{search}%", f"%{search}%"])

        query += " ORDER BY ex.created_at DESC LIMIT 50"

        cursor.execute(query, params)
        claims = [dict(row) for row in cursor.fetchall()]

    if claims:
        df = pd.DataFrame(claims)
        display_cols = ['employee_id', 'first_name', 'last_name', 'expense_type', 'amount', 'currency', 'expense_date', 'status']
        df_display = df[display_cols]
        df_display.columns = ['Emp ID', 'First Name', 'Last Name', 'Type', 'Amount', 'Currency', 'Date', 'Status']

        st.dataframe(df_display, use_container_width=True, hide_index=True)
    else:
        st.info("No expense claims found")

def show_expense_summary():
    """Show personal expense summary"""
    user = get_current_user()

    st.markdown("### 📊 My Expense Summary")

    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Total claimed
        cursor.execute("""
            SELECT SUM(amount) as total FROM expenses
            WHERE emp_id = %s
        """, (user['employee_id'],))
        total = cursor.fetchone()['total'] or 0

        # Approved
        cursor.execute("""
            SELECT SUM(amount) as total FROM expenses
            WHERE emp_id = %s AND status IN ('Finance Approved', 'Paid')
        """, (user['employee_id'],))
        approved = cursor.fetchone()['total'] or 0

        # Pending
        cursor.execute("""
            SELECT SUM(amount) as total FROM expenses
            WHERE emp_id = %s AND status IN ('Pending', 'Manager Approved')
        """, (user['employee_id'],))
        pending = cursor.fetchone()['total'] or 0

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Total Claimed", f"${total:.2f}")
    with col2:
        st.metric("Approved", f"${approved:.2f}")
    with col3:
        st.metric("Pending", f"${pending:.2f}")

def show_expense_statistics():
    """Show expense statistics"""
    st.markdown("### 📊 Expense Statistics")

    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Total expenses by type
        cursor.execute("""
            SELECT expense_type, SUM(amount) as total, COUNT(*) as count
            FROM expenses
            WHERE status IN ('Manager Approved', 'Finance Approved', 'Paid')
            GROUP BY expense_type
            ORDER BY total DESC
        """)
        by_type = [dict(row) for row in cursor.fetchall()]

    if by_type:
        st.markdown("### 💰 Expenses by Type")
        for exp_type in by_type:
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                st.markdown(f"**{exp_type['expense_type']}**")
            with col2:
                st.markdown(f"{exp_type['count']} claims")
            with col3:
                st.markdown(f"${exp_type['total']:,.2f}")
    else:
        st.info("No expense data available")

def approve_expense(expense_id, emp_id, amount):
    """Approve expense claim"""
    user = get_current_user()

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # Get current status
            cursor.execute("SELECT status FROM expenses WHERE id = %s", (expense_id,))
            current_status = cursor.fetchone()['status']

            if is_manager() and current_status == 'Pending':
                # Manager approval
                cursor.execute("""
                    UPDATE expenses SET
                        status = 'Manager Approved',
                        manager_approved_by = %s,
                        manager_approval_date = %s
                    WHERE id = %s
                """, (user['employee_id'], datetime.now().isoformat(), expense_id))

                # Notify HR/Finance
                cursor.execute("SELECT id FROM employees WHERE department = 'Human Resources' LIMIT 1")
                hr_emp = cursor.fetchone()
                if hr_emp:
                    create_notification(
                        hr_emp['id'],
                        "Expense Requires Finance Approval",
                        f"An expense claim (EXP-{expense_id}) for ${amount:.2f} has been approved by manager.",
                        'info'
                    )

                create_notification(emp_id, "Expense Approved by Manager",
                                  f"Your expense claim (EXP-{expense_id}) has been approved by your manager. Awaiting finance approval.", 'success')

                log_audit(f"Manager approved expense EXP-{expense_id}", "expenses", expense_id)
                st.success("✅ Expense approved! Sent to finance for processing.")

            elif is_hr_admin() and current_status == 'Manager Approved':
                # Finance approval
                cursor.execute("""
                    UPDATE expenses SET
                        status = 'Finance Approved',
                        finance_approved_by = %s,
                        finance_approval_date = %s
                    WHERE id = %s
                """, (user['employee_id'], datetime.now().isoformat(), expense_id))

                create_notification(emp_id, "Expense Fully Approved",
                                  f"Your expense claim (EXP-{expense_id}) for ${amount:.2f} has been approved and will be reimbursed.", 'success')

                log_audit(f"Finance approved expense EXP-{expense_id}", "expenses", expense_id)
                st.success("✅ Expense fully approved! Ready for reimbursement.")

            conn.commit()

    except Exception as e:
        st.error(f"❌ Error: {str(e)}")

def reject_expense(expense_id, emp_id):
    """Reject expense claim"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("UPDATE expenses SET status = 'Rejected' WHERE id = %s", (expense_id,))

            create_notification(emp_id, "Expense Claim Rejected",
                              f"Your expense claim (EXP-{expense_id}) has been rejected. Please contact your manager for details.", 'error')

            conn.commit()
            log_audit(f"Rejected expense EXP-{expense_id}", "expenses", expense_id)
            st.warning("⚠️ Expense claim rejected")

    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
