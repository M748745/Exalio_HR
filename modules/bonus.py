"""
Bonus Calculator Module
Calculate and manage employee bonuses based on performance and grade
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from database import get_db_connection
from auth import get_current_user, is_hr_admin, is_manager, get_accessible_employees, create_notification, log_audit

# Grade multipliers for bonus calculation
GRADE_MULTIPLIERS = {
    'A+': 2.0,
    'A': 1.8,
    'B+': 1.5,
    'B': 1.2,
    'C+': 1.0,
    'C': 0.8,
    'D': 0.5
}

def show_bonus_management():
    """Main bonus calculator interface"""
    st.markdown("## 💎 Bonus Calculator")
    st.markdown("Calculate and manage employee bonuses based on performance")
    st.markdown("---")

    if not (is_hr_admin() or is_manager()):
        st.warning("⚠️ This module is only accessible to HR Admin and Managers")
        return

    if is_hr_admin():
        tabs = st.tabs(["🧮 Calculator", "📋 Bonus Records", "✅ Pending Approvals", "📊 Statistics"])
    else:
        tabs = st.tabs(["🧮 Calculator", "📋 Bonus Records", "📊 Statistics"])

    with tabs[0]:
        show_bonus_calculator()

    with tabs[1]:
        show_bonus_records()

    with tabs[2]:
        if is_hr_admin():
            show_bonus_approvals()
        else:
            show_bonus_statistics()

    if len(tabs) > 3:
        with tabs[3]:
            show_bonus_statistics()

def show_bonus_calculator():
    """Interactive bonus calculator"""
    st.markdown("### 🧮 Bonus Calculator")

    col1, col2 = st.columns([2, 1])

    with col1:
        employees = get_accessible_employees()

        selected_emp_id = st.selectbox(
            "Select Employee",
            options=[e['id'] for e in employees],
            format_func=lambda x: f"{next(e['first_name'] + ' ' + e['last_name'] for e in employees if e['id'] == x)} ({next(e['employee_id'] for e in employees if e['id'] == x)})"
        )

        # Get employee details
        employee = next((e for e in employees if e['id'] == selected_emp_id), None)

        if employee:
            # Get salary
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT base_salary FROM financial_records
                    WHERE emp_id = %s
                    ORDER BY created_at DESC
                    LIMIT 1
                """, (selected_emp_id,))
                salary_record = cursor.fetchone()
                base_salary = salary_record['base_salary'] if salary_record else 5000.0

            st.markdown(f"""
            **Employee:** {employee['first_name']} {employee['last_name']}
            **Position:** {employee['position']}
            **Grade:** {employee['grade'] or 'N/A'}
            **Base Salary:** ${base_salary:,.2f}
            """)

            bonus_type = st.selectbox("Bonus Type", [
                "Performance Bonus",
                "Annual Bonus",
                "Project Bonus",
                "Retention Bonus",
                "Holiday Bonus",
                "Discretionary"
            ])

            calculation_method = st.selectbox("Calculation Method", [
                "By Grade Level",
                "% of Salary",
                "Fixed Amount"
            ])

            if calculation_method == "By Grade Level":
                if employee['grade'] and employee['grade'] in GRADE_MULTIPLIERS:
                    multiplier = GRADE_MULTIPLIERS[employee['grade']]
                    suggested_pct = multiplier * 10  # Convert to percentage
                    calculated_bonus = base_salary * (suggested_pct / 100)

                    st.info(f"💡 Grade {employee['grade']} Multiplier: {multiplier}x → Suggested: {suggested_pct}%")
                    bonus_amount = st.number_input(
                        "Bonus Amount ($)",
                        min_value=0.0,
                        value=calculated_bonus,
                        step=100.0
                    )
                else:
                    st.warning("⚠️ Employee grade not set. Please use another method.")
                    bonus_amount = st.number_input("Bonus Amount ($)", min_value=0.0, value=1000.0, step=100.0)

            elif calculation_method == "% of Salary":
                percentage = st.slider("Percentage of Salary", 0, 50, 10)
                bonus_amount = base_salary * (percentage / 100)
                st.info(f"💰 {percentage}% of ${base_salary:,.2f} = ${bonus_amount:,.2f}")

            else:  # Fixed Amount
                bonus_amount = st.number_input("Fixed Bonus Amount ($)", min_value=0.0, value=1000.0, step=100.0)

            period = st.text_input("Period", placeholder="e.g., Q1 2024, Annual 2024", value=f"Q{(datetime.now().month-1)//3 + 1} {datetime.now().year}")

    with col2:
        # Bonus preview
        st.markdown("### 💰 Bonus Preview")

        st.markdown(f"""
            <div style="background: linear-gradient(135deg, rgba(201, 150, 58, 0.1), rgba(58, 123, 213, 0.06));
                        border: 1px solid rgba(201, 150, 58, 0.25); border-radius: 12px;
                        padding: 20px; text-align: center;">
                <div style="font-size: 42px; font-weight: bold; color: #c9963a; margin: 10px 0;">
                    ${bonus_amount:,.2f}
                </div>
                <div style="font-size: 12px; color: #7d96be;">CALCULATED BONUS</div>
            </div>
        """, unsafe_allow_html=True)

        st.markdown("---")

        # Grade multiplier table
        st.markdown("### 📊 Grade Multipliers")
        for grade, mult in GRADE_MULTIPLIERS.items():
            st.markdown(f"**Grade {grade}:** {mult}x → {mult*10}%")

    # Save bonus button
    if st.button("💾 Recommend Bonus", use_container_width=True):
        try:
            user = get_current_user()
            with get_db_connection() as conn:
                cursor = conn.cursor()

                # Manager recommends, HR approves
                if is_manager() and not is_hr_admin():
                    # Manager recommendation - needs HR approval
                    cursor.execute("""
                        INSERT INTO bonuses (
                            emp_id, bonus_type, amount, calculation_method,
                            period, status, recommended_by, manager_approved_by, manager_approval_date
                        ) VALUES (%s, %s, %s, %s, %s, 'Manager Approved', %s, %s, NOW())
                    """, (selected_emp_id, bonus_type, bonus_amount, calculation_method,
                         period, user['employee_id'], user['employee_id']))

                    bonus_id = cursor.lastrowid

                    # Notify HR for approval
                    cursor.execute("SELECT id FROM employees WHERE role = 'hr_admin'")
                    hr_admins = cursor.fetchall()
                    for hr in hr_admins:
                        create_notification(
                            hr['id'],
                            "Bonus Pending HR Approval",
                            f"Manager recommended a {bonus_type} of ${bonus_amount:,.2f} for {period}. Please review and approve.",
                            'info',
                            bonus_id
                        )

                    # Notify employee
                    create_notification(
                        selected_emp_id,
                        "Bonus Recommended",
                        f"Your manager has recommended a {bonus_type} of ${bonus_amount:,.2f} for {period}. Awaiting HR approval.",
                        'info'
                    )

                    conn.commit()
                    log_audit(f"Manager recommended bonus: ${bonus_amount} for {period} (Pending HR approval)", "bonuses", bonus_id)
                    st.success(f"✅ Bonus recommended! Awaiting HR approval.")
                    st.info("ℹ️ This bonus will be processed after HR approval.")

                elif is_hr_admin():
                    # HR direct approval (skip manager stage)
                    cursor.execute("""
                        INSERT INTO bonuses (
                            emp_id, bonus_type, amount, calculation_method,
                            period, status, recommended_by, manager_approved_by, manager_approval_date,
                            hr_approved_by, hr_approval_date
                        ) VALUES (%s, %s, %s, %s, %s, 'HR Approved', %s, %s, NOW(), %s, NOW())
                    """, (selected_emp_id, bonus_type, bonus_amount, calculation_method,
                         period, user['employee_id'], user['employee_id'], user['employee_id']))

                    bonus_id = cursor.lastrowid

                    # Notify employee
                    create_notification(
                        selected_emp_id,
                        "Bonus Approved",
                        f"A {bonus_type} of ${bonus_amount:,.2f} for {period} has been approved and will be processed.",
                        'success'
                    )

                    conn.commit()
                    log_audit(f"HR approved bonus: ${bonus_amount} for {period}", "bonuses", bonus_id)
                    st.success(f"✅ Bonus approved and ready for payment!")
                    st.balloons()

                st.rerun()

        except Exception as e:
            st.error(f"❌ Error: {str(e)}")

def show_bonus_records():
    """Display all bonus records"""
    st.markdown("### 📋 Bonus Records")

    # Filters
    col1, col2, col3 = st.columns(3)
    with col1:
        status_filter = st.selectbox("Status", ["All", "Pending", "Manager Approved", "HR Approved", "Paid", "Rejected"])
    with col2:
        type_filter = st.selectbox("Type", ["All", "Performance Bonus", "Annual Bonus", "Project Bonus", "Retention Bonus", "Holiday Bonus", "Discretionary"])
    with col3:
        search = st.text_input("🔍 Search employee")

    with get_db_connection() as conn:
        cursor = conn.cursor()

        query = """
            SELECT b.*, e.first_name, e.last_name, e.id as employee_id, e.department
            FROM bonuses b
            JOIN employees e ON b.emp_id = e.id
            WHERE 1=1
        """
        params = []

        user = get_current_user()
        if is_manager() and not is_hr_admin():
            query += " AND e.manager_id = %s"
            params.append(user['employee_id'])

        if status_filter != "All":
            query += " AND b.status = %s"
            params.append(status_filter)

        if type_filter != "All":
            query += " AND b.bonus_type = %s"
            params.append(type_filter)

        if search:
            query += " AND (e.first_name LIKE %s OR e.last_name LIKE %s OR e.employee_id LIKE %s)"
            params.extend([f"%{search}%", f"%{search}%", f"%{search}%"])

        query += " ORDER BY b.created_at DESC LIMIT 50"

        cursor.execute(query, params)
        bonuses = [dict(row) for row in cursor.fetchall()]

    if bonuses:
        for bonus in bonuses:
            status_color = {
                'Pending': 'rgba(240, 180, 41, 0.1)',
                'Manager Approved': 'rgba(91, 156, 246, 0.1)',
                'HR Approved': 'rgba(45, 212, 170, 0.1)',
                'Paid': 'rgba(45, 212, 170, 0.2)',
                'Rejected': 'rgba(241, 100, 100, 0.1)'
            }.get(bonus['status'], 'rgba(58, 123, 213, 0.05)')

            with st.expander(f"💰 {bonus['first_name']} {bonus['last_name']} - ${bonus['amount']:,.2f} ({bonus['status']})"):
                col1, col2 = st.columns([2, 1])

                with col1:
                    st.markdown(f"""
                    **Employee:** {bonus['first_name']} {bonus['last_name']} ({bonus['employee_id']})
                    **Department:** {bonus['department']}
                    **Bonus Type:** {bonus['bonus_type']}
                    **Amount:** ${bonus['amount']:,.2f}
                    **Calculation Method:** {bonus['calculation_method'] or 'N/A'}
                    **Period:** {bonus['period'] or 'N/A'}
                    **Status:** {bonus['status']}
                    **Created:** {bonus['created_at']}
                    """)

                with col2:
                    st.metric("Bonus Amount", f"${bonus['amount']:,.2f}")

                    if bonus['status'] == 'Pending' and is_hr_admin():
                        if st.button("✅ Approve", key=f"approve_bonus_{bonus['id']}"):
                            approve_bonus(bonus['id'], bonus['emp_id'])
                            st.rerun()

                        if st.button("❌ Reject", key=f"reject_bonus_{bonus['id']}"):
                            reject_bonus(bonus['id'], bonus['emp_id'])
                            st.rerun()
    else:
        st.info("No bonus records found")

def show_bonus_statistics():
    """Show bonus statistics"""
    st.markdown("### 📊 Bonus Statistics")

    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Total bonuses paid
        cursor.execute("""
            SELECT SUM(amount) as total, COUNT(*) as count
            FROM bonuses
            WHERE status = 'Paid'
        """)
        stats = dict(cursor.fetchone())

        # By type
        cursor.execute("""
            SELECT bonus_type, SUM(amount) as total, COUNT(*) as count
            FROM bonuses
            WHERE status IN ('HR Approved', 'Paid')
            GROUP BY bonus_type
            ORDER BY total DESC
        """)
        by_type = [dict(row) for row in cursor.fetchall()]

    # Display stats
    col1, col2 = st.columns(2)

    with col1:
        st.metric("Total Bonuses Paid", f"${stats['total'] or 0:,.2f}")

    with col2:
        st.metric("Number of Bonuses", stats['count'] or 0)

    st.markdown("---")
    st.markdown("### 💰 Bonuses by Type")

    if by_type:
        for bonus_type in by_type:
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                st.markdown(f"**{bonus_type['bonus_type']}**")
            with col2:
                st.markdown(f"{bonus_type['count']} bonuses")
            with col3:
                st.markdown(f"${bonus_type['total']:,.2f}")
    else:
        st.info("No bonus data available")

def show_bonus_approvals():
    """HR approval interface for bonuses"""
    user = get_current_user()

    if not is_hr_admin():
        st.error("🚫 Access Denied - HR Admin Only")
        return

    st.markdown("### ✅ Bonus Approvals")
    st.markdown("Review and approve bonus recommendations from managers")
    st.markdown("---")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT b.*,
                   e.first_name, e.last_name, e.id as employee_id, e.position, e.department,
                   mgr.first_name || ' ' || mgr.last_name as manager_name
            FROM bonuses b
            JOIN employees e ON b.emp_id = e.id
            LEFT JOIN employees mgr ON b.manager_approved_by = mgr.id
            WHERE b.status = 'Manager Approved'
            ORDER BY b.created_at DESC
        """)
        pending_bonuses = cursor.fetchall()

    if not pending_bonuses:
        st.success("✅ No pending bonus approvals!")
        return

    st.info(f"📋 {len(pending_bonuses)} bonus(es) pending HR approval")

    for bonus in pending_bonuses:
        with st.expander(f"💰 {bonus['first_name']} {bonus['last_name']} - ${bonus['amount']:,.2f} ({bonus['bonus_type']})"):
            col1, col2, col3 = st.columns([2, 2, 1])

            with col1:
                st.markdown("### Employee Information")
                st.markdown(f"**Name:** {bonus['first_name']} {bonus['last_name']}")
                st.markdown(f"**Employee ID:** {bonus['employee_id']}")
                st.markdown(f"**Position:** {bonus['position']}")
                st.markdown(f"**Department:** {bonus['department']}")

            with col2:
                st.markdown("### Bonus Details")
                st.markdown(f"**Type:** {bonus['bonus_type']}")
                st.markdown(f"**Amount:** ${bonus['amount']:,.2f}")
                st.markdown(f"**Period:** {bonus['period']}")
                st.markdown(f"**Calculation:** {bonus['calculation_method'] or 'N/A'}")
                st.markdown(f"**Recommended by:** {bonus['manager_name']}")
                st.markdown(f"**Recommended on:** {bonus['manager_approval_date'].strftime('%Y-%m-%d')}")

            with col3:
                st.markdown("### Actions")

                hr_comments = st.text_area(
                    "HR Comments",
                    key=f"hr_comments_{bonus['id']}",
                    placeholder="Add comments..."
                )

                col_a, col_b = st.columns(2)

                with col_a:
                    if st.button("✅ Approve", key=f"approve_{bonus['id']}", use_container_width=True):
                        approve_bonus_hr(bonus['id'], bonus['emp_id'], bonus['amount'], bonus['bonus_type'], hr_comments)
                        st.success("Approved!")
                        st.rerun()

                with col_b:
                    if st.button("❌ Reject", key=f"reject_{bonus['id']}", use_container_width=True):
                        reject_bonus_hr(bonus['id'], bonus['emp_id'], hr_comments)
                        st.warning("Rejected")
                        st.rerun()

def approve_bonus_hr(bonus_id, emp_id, amount, bonus_type, hr_comments):
    """HR approves bonus and processes payment"""
    user = get_current_user()

    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Update bonus to approved status
        cursor.execute("""
            UPDATE bonuses
            SET status = 'HR Approved',
                hr_approved_by = %s,
                hr_approval_date = NOW(),
                hr_comments = %s,
                payment_status = 'Pending',
                payment_date = %s
            WHERE id = %s
        """, (user['employee_id'], hr_comments, datetime.now().date(), bonus_id))

        # Create financial record for bonus payment
        cursor.execute("""
            INSERT INTO financial_records (emp_id, bonus_amount, payment_type, period)
            VALUES (%s, %s, %s, %s)
        """, (emp_id, amount, 'Bonus Payment', datetime.now().strftime('%Y-%m')))

        # Update total compensation
        cursor.execute("""
            SELECT base_salary FROM financial_records
            WHERE emp_id = %s
            ORDER BY created_at DESC
            LIMIT 1
        """, (emp_id,))
        salary_record = cursor.fetchone()
        base_salary = salary_record['base_salary'] if salary_record else 0

        # Update status to paid after financial record created
        cursor.execute("""
            UPDATE bonuses
            SET payment_status = 'Paid',
                paid_date = NOW()
            WHERE id = %s
        """, (bonus_id,))

        # Notify employee
        create_notification(
            emp_id,
            "Bonus Approved & Processed",
            f"Great news! Your {bonus_type} of ${amount:,.2f} has been approved by HR and processed for payment. You will receive it in the next payroll cycle.",
            'success',
            bonus_id
        )

        # Notify manager
        cursor.execute("SELECT manager_approved_by FROM bonuses WHERE id = %s", (bonus_id,))
        result = cursor.fetchone()
        if result and result['manager_approved_by']:
            create_notification(
                result['manager_approved_by'],
                "Bonus Approved by HR",
                f"The bonus you recommended (${amount:,.2f}) has been approved by HR.",
                'success',
                bonus_id
            )

        conn.commit()
        log_audit(f"HR approved bonus ID {bonus_id}, amount ${amount}", "bonuses", bonus_id)

def reject_bonus_hr(bonus_id, emp_id, hr_comments):
    """HR rejects bonus"""
    user = get_current_user()

    with get_db_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE bonuses
            SET status = 'Rejected',
                hr_approved_by = %s,
                hr_approval_date = NOW(),
                hr_comments = %s
            WHERE id = %s
        """, (user['employee_id'], hr_comments, bonus_id))

        # Get bonus details
        cursor.execute("SELECT bonus_type, amount, manager_approved_by FROM bonuses WHERE id = %s", (bonus_id,))
        bonus = cursor.fetchone()

        # Notify employee
        create_notification(
            emp_id,
            "Bonus Not Approved",
            f"Your {bonus['bonus_type']} recommendation was not approved by HR. Reason: {hr_comments or 'No reason provided'}",
            'warning',
            bonus_id
        )

        # Notify manager
        if bonus['manager_approved_by']:
            create_notification(
                bonus['manager_approved_by'],
                "Bonus Rejected by HR",
                f"The bonus you recommended was rejected by HR. Reason: {hr_comments or 'No reason provided'}",
                'warning',
                bonus_id
            )

        conn.commit()
        log_audit(f"HR rejected bonus ID {bonus_id}", "bonuses", bonus_id)
