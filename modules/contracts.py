"""
Contracts Management Module
Track employment contracts, renewals, and expiry
"""

import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
from database import get_db_connection
from auth import get_current_user, is_hr_admin, is_manager, get_accessible_employees, create_notification, log_audit

def show_contracts_management():
    """Main contracts management interface"""
    st.markdown("## 📄 Contracts Management")
    st.markdown("Employment agreements, renewals, and expiry tracking")
    st.markdown("---")

    if not is_hr_admin():
        st.warning("⚠️ This module is only accessible to HR Admin")
        return

    tabs = st.tabs(["📋 All Contracts", "➕ Add Contract", "⚠️ Expiring Soon"])

    with tabs[0]:
        show_all_contracts()

    with tabs[1]:
        show_add_contract()

    with tabs[2]:
        show_expiring_contracts()

def show_all_contracts():
    """Display all employment contracts"""
    st.markdown("### 📋 All Contracts")

    # Filters
    col1, col2, col3 = st.columns(3)
    with col1:
        status_filter = st.selectbox("Status", ["All", "Active", "Expired", "Renewed", "Terminated"])
    with col2:
        type_filter = st.selectbox("Contract Type", ["All", "Permanent", "Fixed-Term", "Contract", "Internship"])
    with col3:
        search = st.text_input("🔍 Search employee")

    with get_db_connection() as conn:
        cursor = conn.cursor()

        query = """
            SELECT c.*, e.first_name, e.last_name, e.employee_id, e.department, e.position
            FROM contracts c
            JOIN employees e ON c.emp_id = e.id
            WHERE 1=1
        """
        params = []

        if status_filter != "All":
            query += " AND c.status = %s"
            params.append(status_filter)

        if type_filter != "All":
            query += " AND c.contract_type = %s"
            params.append(type_filter)

        if search:
            query += " AND (e.first_name LIKE %s OR e.last_name LIKE %s OR e.employee_id LIKE %s)"
            params.extend([f"%{search}%", f"%{search}%", f"%{search}%"])

        query += " ORDER BY c.end_date ASC"

        cursor.execute(query, params)
        contracts = [dict(row) for row in cursor.fetchall()]

    if contracts:
        for contract in contracts:
            # Calculate days until expiry
            if contract['end_date']:
                end_date = datetime.strptime(contract['end_date'], '%Y-%m-%d').date()
                days_left = (end_date - date.today()).days
                urgency = "🔴" if days_left < 30 else "🟡" if days_left < 90 else "🟢"
            else:
                days_left = None
                urgency = "🟢"

            with st.expander(f"{urgency} {contract['first_name']} {contract['last_name']} - {contract['contract_type']} ({contract['status']})"):
                col1, col2 = st.columns([2, 1])

                with col1:
                    st.markdown(f"""
                    **Employee:** {contract['first_name']} {contract['last_name']} ({contract['employee_id']})
                    **Position:** {contract['position']}
                    **Department:** {contract['department']}
                    **Contract Type:** {contract['contract_type']}
                    **Start Date:** {contract['start_date']}
                    **End Date:** {contract['end_date'] or 'Permanent'}
                    **Status:** {contract['status']}
                    **Terms:** {contract['terms'] or 'N/A'}
                    """)

                with col2:
                    if days_left is not None:
                        st.metric("Days Until Expiry", days_left)
                        if days_left < 0:
                            st.error("⚠️ Contract Expired!")
                        elif days_left < 30:
                            st.warning("⚠️ Expiring Soon!")

                # Actions
                col1, col2, col3 = st.columns(3)
                with col1:
                    if st.button("🔄 Renew", key=f"renew_{contract['id']}", use_container_width=True):
                        renew_contract(contract['id'], contract['emp_id'])
                        st.rerun()

                with col2:
                    if st.button("❌ Terminate", key=f"terminate_{contract['id']}", use_container_width=True):
                        terminate_contract(contract['id'], contract['emp_id'])
                        st.rerun()

                with col3:
                    if st.button("✏️ Edit", key=f"edit_{contract['id']}", use_container_width=True):
                        st.session_state.edit_contract_id = contract['id']
                        st.rerun()
    else:
        st.info("No contracts found")

def show_add_contract():
    """Form to add new contract"""
    st.markdown("### ➕ Add New Contract")

    employees = get_accessible_employees()

    with st.form("contract_form"):
        col1, col2 = st.columns(2)

        with col1:
            selected_emp_id = st.selectbox(
                "Select Employee *",
                options=[e['id'] for e in employees],
                format_func=lambda x: f"{next(e['first_name'] + ' ' + e['last_name'] for e in employees if e['id'] == x)} ({next(e['employee_id'] for e in employees if e['id'] == x)})"
            )

            contract_type = st.selectbox(
                "Contract Type *",
                options=["Permanent", "Fixed-Term", "Contract", "Internship", "Part-Time"]
            )

            start_date = st.date_input("Start Date *", value=date.today())

        with col2:
            if contract_type == "Permanent":
                end_date = None
                st.info("Permanent contracts have no end date")
            else:
                end_date = st.date_input("End Date *", value=date.today() + timedelta(days=365))

            status = st.selectbox("Status", ["Active", "Pending", "Expired", "Terminated"])

        terms = st.text_area("Contract Terms", placeholder="Enter contract terms and conditions...")

        submitted = st.form_submit_button("💾 Save Contract", use_container_width=True)

        if submitted:
            if not all([selected_emp_id, contract_type, start_date]):
                st.error("❌ Please fill all required fields")
            else:
                try:
                    with get_db_connection() as conn:
                        cursor = conn.cursor()

                        cursor.execute("""
                            INSERT INTO contracts (
                                emp_id, contract_type, start_date, end_date, status, terms
                            ) VALUES (%s, %s, %s, %s, %s, %s)
                        """, (selected_emp_id, contract_type, start_date.isoformat(),
                             end_date.isoformat() if end_date else None, status, terms))

                        contract_id = cursor.lastrowid

                        # Notify employee
                        create_notification(
                            selected_emp_id,
                            "New Contract Created",
                            f"A new {contract_type} contract has been created for you.",
                            'info'
                        )

                        conn.commit()
                        log_audit(f"Created contract: {contract_type}", "contracts", contract_id)

                        st.success("✅ Contract created successfully!")
                        st.balloons()
                        st.rerun()

                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")

def show_expiring_contracts():
    """Show contracts expiring soon"""
    st.markdown("### ⚠️ Contracts Expiring Soon")

    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Get contracts expiring in next 90 days
        future_date = (date.today() + timedelta(days=90)).isoformat()

        cursor.execute("""
            SELECT c.*, e.first_name, e.last_name, e.employee_id, e.department
            FROM contracts c
            JOIN employees e ON c.emp_id = e.id
            WHERE c.status = 'Active'
            AND c.end_date IS NOT NULL
            AND c.end_date <= %s
            ORDER BY c.end_date ASC
        """, (future_date,))

        expiring = [dict(row) for row in cursor.fetchall()]

    if expiring:
        for contract in expiring:
            end_date = datetime.strptime(contract['end_date'], '%Y-%m-%d').date()
            days_left = (end_date - date.today()).days

            if days_left < 0:
                urgency = "🔴 EXPIRED"
                color = "rgba(241, 100, 100, 0.1)"
            elif days_left < 30:
                urgency = f"🔴 {days_left} days left"
                color = "rgba(241, 100, 100, 0.1)"
            else:
                urgency = f"🟡 {days_left} days left"
                color = "rgba(240, 180, 41, 0.1)"

            st.markdown(f"""
                <div style="background: {color}; padding: 15px; border-radius: 10px; margin-bottom: 10px;">
                    <strong>{urgency}</strong> - {contract['first_name']} {contract['last_name']}<br>
                    <small>{contract['contract_type']} • End Date: {contract['end_date']}</small>
                </div>
            """, unsafe_allow_html=True)

            col1, col2 = st.columns([1, 4])
            with col1:
                if st.button("🔄 Renew Now", key=f"renew_exp_{contract['id']}"):
                    renew_contract(contract['id'], contract['emp_id'])
                    st.rerun()
    else:
        st.success("✅ No contracts expiring in the next 90 days!")

def renew_contract(contract_id, emp_id):
    """Renew an existing contract"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # Update old contract
            cursor.execute("""
                UPDATE contracts SET
                    status = 'Renewed',
                    renewal_status = 'Renewed'
                WHERE id = %s
            """, (contract_id,))

            # Get old contract details
            cursor.execute("SELECT * FROM contracts WHERE id = %s", (contract_id,))
            old_contract = dict(cursor.fetchone())

            # Create new contract
            new_start = datetime.strptime(old_contract['end_date'], '%Y-%m-%d').date()
            new_end = new_start + timedelta(days=365)

            cursor.execute("""
                INSERT INTO contracts (
                    emp_id, contract_type, start_date, end_date, status, terms
                ) VALUES (%s, %s, %s, %s, 'Active', %s)
            """, (emp_id, old_contract['contract_type'], new_start.isoformat(),
                 new_end.isoformat(), old_contract['terms']))

            # Notify employee
            create_notification(
                emp_id,
                "Contract Renewed",
                f"Your {old_contract['contract_type']} contract has been renewed until {new_end}.",
                'success'
            )

            conn.commit()
            log_audit(f"Renewed contract ID: {contract_id}", "contracts", contract_id)
            st.success("✅ Contract renewed successfully!")

    except Exception as e:
        st.error(f"❌ Error: {str(e)}")

def terminate_contract(contract_id, emp_id):
    """Terminate a contract"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                UPDATE contracts SET
                    status = 'Terminated'
                WHERE id = %s
            """, (contract_id,))

            # Notify employee
            create_notification(
                emp_id,
                "Contract Terminated",
                "Your employment contract has been terminated.",
                'warning'
            )

            conn.commit()
            log_audit(f"Terminated contract ID: {contract_id}", "contracts", contract_id)
            st.warning("⚠️ Contract terminated")

    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
