"""
Contract Renewal Module
Manage employee and vendor contract renewals with expiry tracking and approval workflow
"""

import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
from database import get_db_connection
from auth import get_current_user, is_hr_admin, is_manager, create_notification, log_audit

def show_contract_renewal():
    """Main contract renewal management interface"""
    user = get_current_user()

    st.markdown("## 📄 Contract Renewal Management")
    st.markdown("Track and manage contract renewals with automated expiry alerts")
    st.markdown("---")

    if is_hr_admin():
        tabs = st.tabs(["📋 All Contracts", "⏰ Expiring Soon", "✅ Renewal Requests", "📊 Analytics", "➕ Add Contract"])
    elif is_manager():
        tabs = st.tabs(["📋 Team Contracts", "⏰ Expiring Soon", "✅ Renewal Requests"])
    else:
        tabs = st.tabs(["📋 My Contract", "🔔 Notifications"])

    with tabs[0]:
        if is_hr_admin():
            show_all_contracts()
        elif is_manager():
            show_team_contracts()
        else:
            show_my_contract()

    with tabs[1]:
        if is_hr_admin() or is_manager():
            show_expiring_contracts()
        else:
            show_my_notifications()

    with tabs[2]:
        if is_hr_admin() or is_manager():
            show_renewal_requests()

    if is_hr_admin() and len(tabs) > 3:
        with tabs[3]:
            show_contract_analytics()
        with tabs[4]:
            add_contract()

def show_all_contracts():
    """Show all contracts for HR"""
    st.markdown("### 📋 All Contracts")

    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Get all contracts with employee details
        cursor.execute("""
            SELECT
                c.id,
                c.emp_id,
                e.employee_id,
                e.first_name || ' ' || e.last_name as name,
                e.department,
                c.contract_type,
                c.start_date,
                c.end_date,
                c.status,
                c.renewal_status,
                (c.end_date - CURRENT_DATE) as days_remaining
            FROM contracts c
            JOIN employees e ON c.emp_id = e.id
            ORDER BY c.end_date ASC
        """)
        contracts = [dict(row) for row in cursor.fetchall()]

    if contracts:
        # Filter controls
        col1, col2, col3 = st.columns(3)
        with col1:
            status_filter = st.selectbox("Status", ["All", "Active", "Expired", "Terminated", "Renewed"])
        with col2:
            type_filter = st.selectbox("Type", ["All", "Permanent", "Fixed-Term", "Contract", "Probation"])
        with col3:
            dept_filter = st.selectbox("Department", ["All"] + list(set([c['department'] for c in contracts if c['department']])))

        # Apply filters
        filtered = contracts
        if status_filter != "All":
            filtered = [c for c in filtered if c['status'] == status_filter]
        if type_filter != "All":
            filtered = [c for c in filtered if c['contract_type'] == type_filter]
        if dept_filter != "All":
            filtered = [c for c in filtered if c['department'] == dept_filter]

        st.markdown(f"**Total Contracts:** {len(filtered)}")

        # Display contracts
        for contract in filtered:
            days_remaining = contract.get('days_remaining')

            # Convert to int if it's a different type
            try:
                if days_remaining is not None:
                    days_remaining = int(days_remaining)
            except (ValueError, TypeError):
                days_remaining = None

            # Color coding based on days remaining
            if days_remaining is None:
                status_color = 'rgba(200, 200, 200, 0.1)'  # Gray - Unknown
                status_emoji = "⚪"
            elif days_remaining < 0:
                status_color = 'rgba(241, 100, 100, 0.1)'  # Red - Expired
                status_emoji = "🔴"
            elif days_remaining <= 30:
                status_color = 'rgba(255, 193, 7, 0.1)'  # Yellow - Expiring soon
                status_emoji = "🟡"
            elif days_remaining <= 90:
                status_color = 'rgba(240, 180, 41, 0.1)'  # Orange - Attention needed
                status_emoji = "🟠"
            else:
                status_color = 'rgba(45, 212, 170, 0.1)'  # Green - Active
                status_emoji = "🟢"

            with st.expander(f"{status_emoji} {contract['name']} ({contract['employee_id']}) - {contract['contract_type']} - Ends: {contract['end_date']}"):
                col1, col2 = st.columns([2, 1])

                with col1:
                    st.markdown(f"""
                    **Employee:** {contract['name']} ({contract['employee_id']})
                    **Department:** {contract['department']}
                    **Contract Type:** {contract['contract_type']}
                    **Start Date:** {contract['start_date']}
                    **End Date:** {contract['end_date']}
                    **Status:** {contract['status']}
                    **Renewal Status:** {contract['renewal_status'] or 'N/A'}
                    """)

                with col2:
                    if days_remaining is not None and days_remaining >= 0:
                        st.metric("Days Remaining", f"{days_remaining} days",
                                 delta=f"{days_remaining} days left",
                                 delta_color="inverse" if days_remaining <= 30 else "normal")
                    elif days_remaining is not None:
                        try:
                            abs_days = abs(int(days_remaining))
                        except (ValueError, TypeError):
                            abs_days = 0
                        st.metric("Status", "EXPIRED",
                                 delta=f"{abs_days} days ago",
                                 delta_color="inverse")

                # Action buttons
                st.markdown("---")
                col1, col2, col3 = st.columns(3)

                with col1:
                    if contract['status'] == 'Active' and days_remaining is not None and days_remaining <= 90:
                        if st.button("🔄 Initiate Renewal", key=f"renew_{contract['id']}", use_container_width=True):
                            initiate_renewal(contract['id'], contract['emp_id'])
                            st.rerun()

                with col2:
                    if st.button("📝 View Details", key=f"view_{contract['id']}", use_container_width=True):
                        show_contract_details(contract['id'])

                with col3:
                    if contract['status'] == 'Active':
                        if st.button("❌ Terminate", key=f"term_{contract['id']}", use_container_width=True):
                            terminate_contract(contract['id'], contract['emp_id'])
                            st.rerun()
    else:
        st.info("No contracts found")

def show_expiring_contracts():
    """Show contracts expiring within next 90 days"""
    st.markdown("### ⏰ Contracts Expiring Soon")

    with get_db_connection() as conn:
        cursor = conn.cursor()

        if is_hr_admin():
            # HR sees all expiring contracts
            cursor.execute("""
                SELECT
                    c.id,
                    c.emp_id,
                    e.employee_id,
                    e.first_name || ' ' || e.last_name as name,
                    e.department,
                    e.position,
                    c.contract_type,
                    c.end_date,
                    c.renewal_status,
                    (c.end_date - CURRENT_DATE) as days_remaining
                FROM contracts c
                JOIN employees e ON c.emp_id = e.id
                WHERE c.status = 'Active'
                AND (c.end_date - CURRENT_DATE) <= 90
                ORDER BY c.end_date ASC
            """)
        else:
            # Manager sees team contracts
            user = get_current_user()
            cursor.execute("""
                SELECT
                    c.id,
                    c.emp_id,
                    e.employee_id,
                    e.first_name || ' ' || e.last_name as name,
                    e.position,
                    c.contract_type,
                    c.end_date,
                    c.renewal_status,
                    (c.end_date - CURRENT_DATE) as days_remaining
                FROM contracts c
                JOIN employees e ON c.emp_id = e.id
                WHERE c.status = 'Active'
                AND (c.end_date - CURRENT_DATE) <= 90
                AND e.manager_id = %s
                ORDER BY c.end_date ASC
            """, (user['employee_id'],))

        expiring = [dict(row) for row in cursor.fetchall()]

    if expiring:
        # Categorize by urgency
        critical = [c for c in expiring if c['days_remaining'] <= 30]
        warning = [c for c in expiring if 30 < c['days_remaining'] <= 60]
        attention = [c for c in expiring if 60 < c['days_remaining'] <= 90]

        # Show summary
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("🔴 Critical (≤30 days)", len(critical))
        with col2:
            st.metric("🟡 Warning (31-60 days)", len(warning))
        with col3:
            st.metric("🟠 Attention (61-90 days)", len(attention))

        st.markdown("---")

        # Critical contracts
        if critical:
            st.markdown("#### 🔴 CRITICAL - Expiring within 30 days")
            for contract in critical:
                with st.expander(f"⚠️ {contract['name']} - {contract['days_remaining']} days remaining"):
                    st.markdown(f"""
                    **Employee:** {contract['name']} ({contract['employee_id']})
                    **Position:** {contract.get('position', 'N/A')}
                    **Department:** {contract.get('department', 'N/A')}
                    **Contract Type:** {contract['contract_type']}
                    **End Date:** {contract['end_date']}
                    **Renewal Status:** {contract['renewal_status'] or 'Not Initiated'}
                    """)

                    if not contract['renewal_status'] or contract['renewal_status'] == 'Not Initiated':
                        if st.button(f"🔄 Initiate Renewal NOW", key=f"init_crit_{contract['id']}", type="primary"):
                            initiate_renewal(contract['id'], contract['emp_id'])
                            st.rerun()
                    elif contract['renewal_status'] == 'Pending Approval':
                        if st.button(f"✅ Approve Renewal", key=f"approve_crit_{contract['id']}", type="primary"):
                            approve_renewal(contract['id'], contract['emp_id'])
                            st.rerun()

        # Warning contracts
        if warning:
            st.markdown("#### 🟡 WARNING - Expiring in 31-60 days")
            for contract in warning:
                st.markdown(f"- **{contract['name']}** ({contract['contract_type']}) - {contract['days_remaining']} days")

        # Attention contracts
        if attention:
            st.markdown("#### 🟠 ATTENTION - Expiring in 61-90 days")
            for contract in attention:
                st.markdown(f"- **{contract['name']}** ({contract['contract_type']}) - {contract['days_remaining']} days")

    else:
        st.success("✅ No contracts expiring in the next 90 days!")

def show_renewal_requests():
    """Show pending renewal requests"""
    st.markdown("### ✅ Pending Renewal Requests")

    with get_db_connection() as conn:
        cursor = conn.cursor()

        if is_hr_admin():
            cursor.execute("""
                SELECT
                    c.id,
                    c.emp_id,
                    e.employee_id,
                    e.first_name || ' ' || e.last_name as name,
                    e.department,
                    c.contract_type,
                    c.end_date,
                    c.renewal_date,
                    c.renewal_status,
                    c.terms
                FROM contracts c
                JOIN employees e ON c.emp_id = e.id
                WHERE c.renewal_status = 'Pending Approval'
                ORDER BY c.updated_at DESC
            """)
        else:
            user = get_current_user()
            cursor.execute("""
                SELECT
                    c.id,
                    c.emp_id,
                    e.employee_id,
                    e.first_name || ' ' || e.last_name as name,
                    c.contract_type,
                    c.end_date,
                    c.renewal_date,
                    c.renewal_status,
                    c.terms
                FROM contracts c
                JOIN employees e ON c.emp_id = e.id
                WHERE c.renewal_status = 'Pending Approval'
                AND e.manager_id = %s
                ORDER BY c.updated_at DESC
            """, (user['employee_id'],))

        pending = [dict(row) for row in cursor.fetchall()]

    if pending:
        st.info(f"📋 {len(pending)} renewal request(s) awaiting approval")

        for contract in pending:
            with st.expander(f"📄 {contract['name']} - {contract['contract_type']} Renewal"):
                st.markdown(f"""
                **Employee:** {contract['name']} ({contract['employee_id']})
                **Department:** {contract.get('department', 'N/A')}
                **Contract Type:** {contract['contract_type']}
                **Current End Date:** {contract['end_date']}
                **Renewal Date:** {contract.get('renewal_date', 'Not set')}
                **Status:** {contract['renewal_status']}
                **Terms:** {contract.get('terms', 'N/A')}
                """)

                # Approval actions
                st.markdown("---")
                col1, col2 = st.columns(2)

                with col1:
                    if st.button("✅ Approve Renewal", key=f"approve_renewal_{contract['id']}", use_container_width=True):
                        approve_renewal(contract['id'], contract['emp_id'])
                        st.rerun()

                with col2:
                    if st.button("❌ Reject Renewal", key=f"reject_renewal_{contract['id']}", use_container_width=True):
                        reject_renewal(contract['id'], contract['emp_id'])
                        st.rerun()
    else:
        st.success("✅ No pending renewal requests!")

def initiate_renewal(contract_id, emp_id):
    """Initiate contract renewal process"""
    user = get_current_user()

    st.markdown("### 🔄 Initiate Contract Renewal")

    with st.form(f"renewal_form_{contract_id}"):
        # Get current contract details
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM contracts WHERE id = %s", (contract_id,))
            contract = dict(cursor.fetchone())

        current_end = datetime.strptime(str(contract['end_date']), '%Y-%m-%d').date()
        default_new_end = current_end + timedelta(days=365)  # Default 1 year extension

        new_end_date = st.date_input("New End Date", value=default_new_end, min_value=current_end)
        renewal_terms = st.text_area("Renewal Terms", value="Same terms as current contract")

        submitted = st.form_submit_button("📤 Submit Renewal Request", use_container_width=True)

        if submitted:
            try:
                with get_db_connection() as conn:
                    cursor = conn.cursor()

                    cursor.execute("""
                        UPDATE contracts SET
                            renewal_status = 'Pending Approval',
                            renewal_date = %s,
                            terms = %s,
                            updated_at = %s
                        WHERE id = %s
                    """, (new_end_date.isoformat(), renewal_terms,
                         datetime.now().isoformat(), contract_id))

                    # Notify HR
                    create_notification(
                        None,  # To HR
                        "Contract Renewal Request",
                        f"Contract renewal requested for {contract['emp_id']} (Contract ID: {contract_id})",
                        'info',
                        is_hr_notification=True
                    )

                    # Notify employee
                    create_notification(
                        emp_id,
                        "Contract Renewal Initiated",
                        f"Your contract renewal has been initiated and is pending approval. New end date: {new_end_date}",
                        'info'
                    )

                    conn.commit()
                    log_audit(f"Initiated contract renewal for contract {contract_id}", "contracts", contract_id)
                    st.success("✅ Contract renewal request submitted!")

            except Exception as e:
                st.error(f"❌ Error: {str(e)}")

def approve_renewal(contract_id, emp_id):
    """Approve contract renewal"""
    user = get_current_user()

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # Get renewal details
            cursor.execute("""
                SELECT renewal_date, terms
                FROM contracts
                WHERE id = %s
            """, (contract_id,))
            renewal = dict(cursor.fetchone())

            # Update contract
            cursor.execute("""
                UPDATE contracts SET
                    end_date = %s,
                    renewal_status = 'Approved',
                    updated_at = %s,
                    status = 'Active'
                WHERE id = %s
            """, (renewal['renewal_date'], datetime.now().isoformat(), contract_id))

            # Notify employee
            create_notification(
                emp_id,
                "Contract Renewed",
                f"Your contract has been successfully renewed until {renewal['renewal_date']}. Terms: {renewal['terms']}",
                'success'
            )

            conn.commit()
            log_audit(f"Approved contract renewal {contract_id}, new end date: {renewal['renewal_date']}", "contracts", contract_id)
            st.success(f"✅ Contract renewed until {renewal['renewal_date']}!")

    except Exception as e:
        st.error(f"❌ Error: {str(e)}")

def reject_renewal(contract_id, emp_id):
    """Reject contract renewal"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                UPDATE contracts SET
                    renewal_status = 'Rejected',
                    renewal_date = NULL,
                    updated_at = %s
                WHERE id = %s
            """, (datetime.now().isoformat(), contract_id))

            # Notify employee
            create_notification(
                emp_id,
                "Contract Renewal Not Approved",
                f"Your contract renewal request (ID: {contract_id}) was not approved. Please contact HR.",
                'warning'
            )

            conn.commit()
            log_audit(f"Rejected contract renewal {contract_id}", "contracts", contract_id)
            st.warning("⚠️ Contract renewal rejected")

    except Exception as e:
        st.error(f"❌ Error: {str(e)}")

def terminate_contract(contract_id, emp_id):
    """Terminate a contract"""
    user = get_current_user()

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                UPDATE contracts SET
                    status = 'Terminated',
                    termination_date = %s,
                    terminated_by = %s
                WHERE id = %s
            """, (datetime.now().isoformat(), user['employee_id'], contract_id))

            # Notify employee
            create_notification(
                emp_id,
                "Contract Terminated",
                f"Your contract (ID: {contract_id}) has been terminated as of today.",
                'warning'
            )

            conn.commit()
            log_audit(f"Terminated contract {contract_id}", "contracts", contract_id)
            st.warning("⚠️ Contract terminated")

    except Exception as e:
        st.error(f"❌ Error: {str(e)}")

def show_contract_analytics():
    """Show contract analytics"""
    st.markdown("### 📊 Contract Analytics")

    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Overall stats
        cursor.execute("""
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN status = 'Active' THEN 1 ELSE 0 END) as active,
                SUM(CASE WHEN status = 'Expired' THEN 1 ELSE 0 END) as expired,
                SUM(CASE WHEN (end_date - CURRENT_DATE) <= 30 AND status = 'Active' THEN 1 ELSE 0 END) as expiring_30,
                SUM(CASE WHEN (end_date - CURRENT_DATE) <= 90 AND status = 'Active' THEN 1 ELSE 0 END) as expiring_90
            FROM contracts
        """)
        stats = dict(cursor.fetchone())

        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            st.metric("Total Contracts", stats['total'] or 0)
        with col2:
            st.metric("Active", stats['active'] or 0)
        with col3:
            st.metric("Expired", stats['expired'] or 0)
        with col4:
            st.metric("Expiring ≤30d", stats['expiring_30'] or 0, delta_color="inverse")
        with col5:
            st.metric("Expiring ≤90d", stats['expiring_90'] or 0, delta_color="inverse")

        st.markdown("---")

        # By contract type
        st.markdown("#### By Contract Type")
        cursor.execute("""
            SELECT
                contract_type,
                COUNT(*) as count,
                SUM(CASE WHEN status = 'Active' THEN 1 ELSE 0 END) as active
            FROM contracts
            GROUP BY contract_type
            ORDER BY count DESC
        """)
        by_type = [dict(row) for row in cursor.fetchall()]

        for ctype in by_type:
            st.markdown(f"**{ctype['contract_type']}:** {ctype['count']} total ({ctype['active']} active)")

def add_contract():
    """Add new contract"""
    st.markdown("### ➕ Add New Contract")

    with st.form("add_contract_form"):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, employee_id, first_name, last_name FROM employees WHERE status = 'Active'")
            employees = [dict(row) for row in cursor.fetchall()]

        emp_options = {f"{e['employee_id']} - {e['first_name']} {e['last_name']}": e['id'] for e in employees}
        selected_emp = st.selectbox("Employee *", options=list(emp_options.keys()))

        contract_type = st.selectbox("Contract Type *", ["Permanent", "Fixed-Term", "Contract", "Probation"])
        start_date = st.date_input("Start Date *", value=date.today())

        duration_months = st.number_input("Duration (months)", min_value=1, value=12)
        end_date = st.date_input("End Date *", value=date.today() + timedelta(days=duration_months*30))

        terms = st.text_area("Contract Terms", placeholder="Salary, benefits, working hours, etc...")

        submitted = st.form_submit_button("💾 Create Contract", use_container_width=True)

        if submitted and selected_emp:
            emp_id = emp_options[selected_emp]

            try:
                with get_db_connection() as conn:
                    cursor = conn.cursor()

                    cursor.execute("""
                        INSERT INTO contracts (
                            emp_id, contract_type, start_date, end_date,
                            terms, status, created_by
                        ) VALUES (%s, %s, %s, %s, %s, 'Active', %s)
                    """, (emp_id, contract_type, start_date.isoformat(),
                         end_date.isoformat(), terms, get_current_user()['employee_id']))

                    contract_id = cursor.lastrowid

                    # Notify employee
                    create_notification(
                        emp_id,
                        "New Contract Created",
                        f"A new {contract_type} contract has been created for you (ID: {contract_id}). Valid from {start_date} to {end_date}.",
                        'info'
                    )

                    conn.commit()
                    log_audit(f"Created new contract {contract_id} for employee {emp_id}", "contracts", contract_id)
                    st.success(f"✅ Contract created successfully! ID: {contract_id}")

            except Exception as e:
                st.error(f"❌ Error: {str(e)}")

def show_my_contract():
    """Show employee's own contract"""
    user = get_current_user()
    st.markdown("### 📋 My Contract")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM contracts
            WHERE emp_id = %s AND status = 'Active'
            ORDER BY end_date DESC
            LIMIT 1
        """, (user['employee_id'],))
        contract = cursor.fetchone()

        if contract:
            contract = dict(contract)
            days_remaining = (datetime.strptime(str(contract['end_date']), '%Y-%m-%d').date() - date.today()).days

            col1, col2 = st.columns([2, 1])
            with col1:
                st.markdown(f"""
                **Contract Type:** {contract['contract_type']}
                **Start Date:** {contract['start_date']}
                **End Date:** {contract['end_date']}
                **Status:** {contract['status']}
                **Renewal Status:** {contract.get('renewal_status', 'N/A') or 'N/A'}
                """)
            with col2:
                if days_remaining > 0:
                    st.metric("Days Remaining", f"{days_remaining} days")
                else:
                    st.metric("Status", "EXPIRED")

            if contract.get('terms'):
                st.markdown("**Contract Terms:**")
                st.info(contract['terms'])
        else:
            st.info("No active contract found")

def show_my_notifications():
    """Show contract-related notifications"""
    user = get_current_user()
    st.markdown("### 🔔 Contract Notifications")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM notifications
            WHERE emp_id = %s AND message LIKE '%contract%'
            ORDER BY created_at DESC
            LIMIT 20
        """, (user['employee_id'],))
        notifications = [dict(row) for row in cursor.fetchall()]

    if notifications:
        for notif in notifications:
            st.info(f"**{notif['title']}** - {notif['message']} ({notif['created_at']})")
    else:
        st.info("No contract notifications")

def show_contract_details(contract_id):
    """Show detailed contract information"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM contracts WHERE id = %s", (contract_id,))
        contract = dict(cursor.fetchone())

    st.markdown("### 📄 Contract Details")
    st.json(contract)

def show_team_contracts():
    """Show team member contracts for managers"""
    user = get_current_user()
    st.markdown("### 📋 Team Contracts")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT
                c.*,
                e.employee_id,
                e.first_name || ' ' || e.last_name as name,
                (c.end_date - CURRENT_DATE) as days_remaining
            FROM contracts c
            JOIN employees e ON c.emp_id = e.id
            WHERE e.manager_id = %s
            ORDER BY c.end_date ASC
        """, (user['employee_id'],))
        contracts = [dict(row) for row in cursor.fetchall()]

    if contracts:
        for contract in contracts:
            status_emoji = "🟢" if contract['days_remaining'] > 90 else "🟡" if contract['days_remaining'] > 30 else "🔴"
            st.markdown(f"{status_emoji} **{contract['name']}** - {contract['contract_type']} - Ends: {contract['end_date']} ({contract['days_remaining']} days)")
    else:
        st.info("No team contracts found")
