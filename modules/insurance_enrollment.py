"""
Insurance Enrollment Module
Plan selection, enrollment workflow, approval process, and tracking
"""

import streamlit as st
from datetime import datetime, date
from database import get_db_connection
from auth import get_current_user, is_hr_admin, is_manager, create_notification, log_audit

def show_insurance_enrollment():
    """Main insurance enrollment interface"""
    user = get_current_user()

    st.markdown("## 🏥 Insurance Enrollment")
    st.markdown("Manage health insurance and benefits enrollment")
    st.markdown("---")

    if is_hr_admin():
        tabs = st.tabs(["📊 All Enrollments", "📋 Pending Approvals", "💼 Insurance Plans", "➕ Add Plan"])
    elif is_manager():
        tabs = st.tabs(["📋 My Enrollment", "👥 Team Enrollments"])
    else:
        tabs = st.tabs(["📋 My Enrollment", "💼 Available Plans", "📝 Enroll"])

    with tabs[0]:
        if is_hr_admin():
            show_all_enrollments()
        else:
            show_my_enrollment()

    with tabs[1]:
        if is_hr_admin():
            show_pending_approvals()
        elif is_manager():
            show_team_enrollments()
        else:
            show_available_plans()

    if is_hr_admin() and len(tabs) > 2:
        with tabs[2]:
            show_insurance_plans()
        with tabs[3]:
            add_insurance_plan()
    elif not is_hr_admin() and not is_manager() and len(tabs) > 2:
        with tabs[2]:
            enroll_in_plan()

def show_all_enrollments():
    """Show all insurance enrollments"""
    st.markdown("### 📊 All Insurance Enrollments")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT ie.*, e.first_name, e.last_name, e.department
            FROM insurance_enrollments ie
            JOIN employees e ON ie.emp_id = e.id
            ORDER BY ie.enrollment_date DESC
        """)
        enrollments = [dict(row) for row in cursor.fetchall()]

    if enrollments:
        for enrollment in enrollments:
            status_icon = '✅' if enrollment['status'] == 'Active' else '🟡' if enrollment['status'] == 'Pending' else '🔴'
            with st.expander(f"{status_icon} {enrollment['first_name']} {enrollment['last_name']} - {enrollment['plan_name']} - {enrollment['status']}"):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Plan:** {enrollment['plan_name']}")
                    st.write(f"**Coverage Type:** {enrollment['coverage_type']}")
                    st.write(f"**Enrollment Date:** {enrollment['enrollment_date']}")
                with col2:
                    st.write(f"**Premium:** ${enrollment.get('monthly_premium', 0):,.2f}/month")
                    st.write(f"**Effective Date:** {enrollment['effective_date']}")
                    st.write(f"**Status:** {enrollment['status']}")

                if enrollment['status'] == 'Pending':
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button(f"✅ Approve - {enrollment['id']}", key=f"approve_{enrollment['id']}"):
                            with get_db_connection() as conn:
                                cursor = conn.cursor()
                                cursor.execute("""
                                    UPDATE insurance_enrollments SET
                                        status = 'Active',
                                        approved_by = %s,
                                        approval_date = %s
                                    WHERE id = %s
                                """, (get_current_user()['employee_id'], date.today(), enrollment['id']))
                                conn.commit()
                            create_notification(enrollment['emp_id'], "Insurance Enrollment Approved",
                                              f"Your {enrollment['plan_name']} enrollment has been approved", "success")
                            st.success("✅ Approved!")
                            st.rerun()
                    with col2:
                        if st.button(f"❌ Reject - {enrollment['id']}", key=f"reject_{enrollment['id']}"):
                            with get_db_connection() as conn:
                                cursor = conn.cursor()
                                cursor.execute("""
                                    UPDATE insurance_enrollments SET status = 'Rejected'
                                    WHERE id = %s
                                """, (enrollment['id'],))
                                conn.commit()
                            create_notification(enrollment['emp_id'], "Insurance Enrollment Rejected",
                                              f"Your {enrollment['plan_name']} enrollment was not approved", "error")
                            st.warning("Rejected")
                            st.rerun()
    else:
        st.info("No enrollments found")

def show_my_enrollment():
    """Show employee's current enrollment"""
    user = get_current_user()
    st.markdown("### 📋 My Insurance Enrollment")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM insurance_enrollments
            WHERE emp_id = %s
            ORDER BY enrollment_date DESC
            LIMIT 1
        """, (user['employee_id'],))
        enrollment = cursor.fetchone()

    if enrollment:
        enrollment = dict(enrollment)
        if enrollment['status'] == 'Active':
            st.success(f"✅ Currently enrolled in: **{enrollment['plan_name']}**")
        elif enrollment['status'] == 'Pending':
            st.warning(f"🟡 Enrollment pending approval: **{enrollment['plan_name']}**")

        col1, col2 = st.columns(2)
        with col1:
            st.metric("Plan", enrollment['plan_name'])
            st.metric("Coverage", enrollment['coverage_type'])
        with col2:
            st.metric("Monthly Premium", f"${enrollment.get('monthly_premium', 0):,.2f}")
            st.metric("Effective Date", enrollment['effective_date'])

        if enrollment.get('dependents_covered'):
            st.write(f"**Dependents:** {enrollment['dependents_covered']}")
    else:
        st.info("Not currently enrolled in any insurance plan")

def show_available_plans():
    """Show available insurance plans"""
    st.markdown("### 💼 Available Insurance Plans")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM insurance_plans
            WHERE status = 'Active'
            ORDER BY plan_type, monthly_premium
        """)
        plans = [dict(row) for row in cursor.fetchall()]

    if plans:
        for plan in plans:
            with st.expander(f"{plan['plan_name']} - {plan['plan_type']} - ${plan['monthly_premium']:,.2f}/month"):
                st.write(f"**Coverage Details:** {plan.get('coverage_details', 'N/A')}")
                st.write(f"**Deductible:** ${plan.get('deductible', 0):,.2f}")
                st.write(f"**Max Out-of-Pocket:** ${plan.get('max_out_of_pocket', 0):,.2f}")
    else:
        st.info("No insurance plans available")

def enroll_in_plan():
    """Enroll in insurance plan"""
    st.markdown("### 📝 Enroll in Insurance Plan")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM insurance_plans WHERE status = 'Active' ORDER BY plan_type, monthly_premium
        """)
        plans = [dict(row) for row in cursor.fetchall()]

    if plans:
        with st.form("enroll"):
            plan_options = {f"{p['plan_name']} - {p['plan_type']} (${p['monthly_premium']}/month)": p for p in plans}
            selected_plan = st.selectbox("Select Plan *", list(plan_options.keys()))

            coverage_type = st.selectbox("Coverage Type *", ["Employee Only", "Employee + Spouse", "Employee + Children", "Family"])
            dependents_covered = st.text_input("Dependent Names (if applicable)")
            effective_date = st.date_input("Requested Effective Date *", value=date.today())

            submitted = st.form_submit_button("💾 Submit Enrollment")

            if submitted and selected_plan:
                plan = plan_options[selected_plan]

                with get_db_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT INTO insurance_enrollments (emp_id, plan_name, coverage_type,
                                                          monthly_premium, dependents_covered,
                                                          enrollment_date, effective_date, status)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, 'Pending')
                    """, (get_current_user()['employee_id'], plan['plan_name'], coverage_type,
                         plan['monthly_premium'], dependents_covered, date.today(), effective_date))
                    conn.commit()

                log_audit(get_current_user()['id'], f"Enrolled in insurance plan: {plan['plan_name']}", "insurance_enrollments")
                st.success("✅ Enrollment submitted for approval!")
    else:
        st.info("No plans available for enrollment")

def show_pending_approvals():
    """Show pending insurance approvals"""
    st.markdown("### 📋 Pending Insurance Approvals")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT ie.*, e.first_name, e.last_name
            FROM insurance_enrollments ie
            JOIN employees e ON ie.emp_id = e.id
            WHERE ie.status = 'Pending'
            ORDER BY ie.enrollment_date
        """)
        pending = [dict(row) for row in cursor.fetchall()]

    if pending:
        for enrollment in pending:
            st.write(f"🟡 {enrollment['first_name']} {enrollment['last_name']} - {enrollment['plan_name']} - {enrollment['coverage_type']}")
    else:
        st.success("✅ No pending approvals")

def show_insurance_plans():
    """Show all insurance plans"""
    st.markdown("### 💼 Insurance Plans")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM insurance_plans ORDER BY plan_type, monthly_premium")
        plans = [dict(row) for row in cursor.fetchall()]

    if plans:
        for plan in plans:
            st.write(f"**{plan['plan_name']}** - {plan['plan_type']} - ${plan['monthly_premium']}/month - Status: {plan['status']}")
    else:
        st.info("No insurance plans configured")

def add_insurance_plan():
    """Add new insurance plan"""
    st.markdown("### ➕ Add Insurance Plan")

    with st.form("add_plan"):
        col1, col2 = st.columns(2)
        with col1:
            plan_name = st.text_input("Plan Name *")
            plan_type = st.selectbox("Plan Type *", ["Health", "Dental", "Vision", "Life", "Disability"])
            monthly_premium = st.number_input("Monthly Premium ($) *", min_value=0.0, step=10.0)
        with col2:
            deductible = st.number_input("Deductible ($)", min_value=0.0, step=100.0)
            max_out_of_pocket = st.number_input("Max Out-of-Pocket ($)", min_value=0.0, step=100.0)
            status = st.selectbox("Status", ["Active", "Inactive"])

        coverage_details = st.text_area("Coverage Details")

        submitted = st.form_submit_button("💾 Add Plan")

        if submitted and plan_name and monthly_premium > 0:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO insurance_plans (plan_name, plan_type, monthly_premium,
                                                 deductible, max_out_of_pocket, coverage_details, status)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (plan_name, plan_type, monthly_premium, deductible,
                     max_out_of_pocket, coverage_details, status))
                conn.commit()
            log_audit(get_current_user()['id'], f"Added insurance plan: {plan_name}", "insurance_plans")
            st.success("✅ Insurance plan added!")

def show_team_enrollments():
    """Show team insurance enrollments"""
    user = get_current_user()
    st.markdown("### 👥 Team Insurance Enrollments")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT department FROM employees WHERE id = %s", (user['employee_id'],))
        dept_row = cursor.fetchone()

        if dept_row:
            dept = dept_row['department']
            cursor.execute("""
                SELECT ie.*, e.first_name, e.last_name
                FROM insurance_enrollments ie
                JOIN employees e ON ie.emp_id = e.id
                WHERE e.department = %s AND ie.status = 'Active'
                ORDER BY e.first_name
            """, (dept,))
            enrollments = [dict(row) for row in cursor.fetchall()]

            if enrollments:
                for enrollment in enrollments:
                    st.write(f"👤 {enrollment['first_name']} {enrollment['last_name']} - {enrollment['plan_name']} - {enrollment['coverage_type']}")
            else:
                st.info("No active enrollments in your team")
