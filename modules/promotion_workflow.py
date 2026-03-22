"""
Promotion Workflow Module
Complete career advancement process with approval chain
Workflow: Nomination → Manager Approval → HR Review → Budget Approval → Implementation
"""

import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
from database import get_db_connection
from auth import get_current_user, is_hr_admin, is_manager, create_notification, log_audit

def show_promotion_workflow():
    """Main promotion workflow interface"""
    user = get_current_user()

    st.markdown("## 🚀 Promotion Workflow")
    st.markdown("Manage career advancement and promotion requests")
    st.markdown("---")

    if is_hr_admin():
        tabs = st.tabs(["📋 All Requests", "⏳ Pending Approvals", "➕ Nominate Employee", "📊 Analytics"])
    elif is_manager():
        tabs = st.tabs(["📋 Team Promotions", "⏳ Pending Approvals", "➕ Nominate Employee"])
    else:
        tabs = st.tabs(["📋 My Promotion History", "📊 Eligibility Check"])

    with tabs[0]:
        if is_hr_admin():
            show_all_promotions()
        elif is_manager():
            show_team_promotions()
        else:
            show_my_promotions()

    with tabs[1]:
        if is_hr_admin() or is_manager():
            show_pending_approvals()
        else:
            show_eligibility_check()

    if len(tabs) > 2:
        with tabs[2]:
            show_nomination_form()

    if len(tabs) > 3:
        with tabs[3]:
            show_promotion_analytics()


def show_nomination_form():
    """Form to nominate employee for promotion"""
    user = get_current_user()

    st.markdown("### ➕ Nominate Employee for Promotion")

    # Get accessible employees
    with get_db_connection() as conn:
        cursor = conn.cursor()

        if is_manager():
            cursor.execute("""
                SELECT id, employee_id, first_name, last_name, position, grade, join_date
                FROM employees
                WHERE manager_id = %s AND status = 'Active'
                ORDER BY first_name
            """, (user['employee_id'],))
        else:  # HR can nominate anyone
            cursor.execute("""
                SELECT id, employee_id, first_name, last_name, position, grade, join_date
                FROM employees
                WHERE status = 'Active'
                ORDER BY first_name
            """)

        employees = cursor.fetchall()

    if not employees:
        st.info("No employees available for nomination")
        return

    with st.form("promotion_nomination_form"):
        # Select employee
        emp_options = {e['id']: f"{e['first_name']} {e['last_name']} ({e['employee_id']}) - {e['position']}" for e in employees}
        selected_emp_id = st.selectbox("Select Employee *", options=list(emp_options.keys()), format_func=lambda x: emp_options[x])

        if selected_emp_id:
            selected_emp = next(e for e in employees if e['id'] == selected_emp_id)

            # Get employee details
            with get_db_connection() as conn:
                cursor = conn.cursor()

                # Calculate years in current role
                join_date = selected_emp['join_date']
                years_in_role = (date.today() - join_date).days / 365.25

                # Get current salary from financial records
                cursor.execute("""
                    SELECT base_salary FROM financial_records
                    WHERE emp_id = %s
                    ORDER BY created_at DESC
                    LIMIT 1
                """, (selected_emp_id,))
                salary_record = cursor.fetchone()
                current_salary = salary_record['base_salary'] if salary_record else 0

                # Get latest performance rating
                cursor.execute("""
                    SELECT overall_grade FROM appraisals
                    WHERE emp_id = %s AND status = 'Completed'
                    ORDER BY created_at DESC
                    LIMIT 1
                """, (selected_emp_id,))
                appraisal = cursor.fetchone()
                performance_rating = appraisal['overall_grade'] if appraisal else 'N/A'

            # Display current info
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Current Position", selected_emp['position'])
            with col2:
                st.metric("Current Grade", selected_emp['grade'] or 'N/A')
            with col3:
                st.metric("Years in Role", f"{years_in_role:.1f}")

            col1, col2 = st.columns(2)
            with col1:
                st.metric("Current Salary", f"${current_salary:,.0f}")
            with col2:
                st.metric("Performance Rating", performance_rating)

            st.markdown("---")

            # Proposed changes
            st.markdown("### Proposed Promotion Details")

            col1, col2 = st.columns(2)
            with col1:
                # Get all positions
                with get_db_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT DISTINCT position_name, level FROM positions WHERE status = 'Active' ORDER BY position_name")
                    positions = cursor.fetchall()

                position_options = [p['position_name'] for p in positions]
                proposed_position = st.selectbox("Proposed Position *", options=position_options)

            with col2:
                grade_options = ['A+', 'A', 'A-', 'B+', 'B', 'B-', 'C+', 'C']
                proposed_grade = st.selectbox("Proposed Grade *", options=grade_options)

            proposed_salary = st.number_input(
                "Proposed Salary *",
                min_value=0.0,
                value=float(current_salary * 1.15),  # Default 15% increase
                step=1000.0,
                format="%.2f"
            )

            salary_increase = ((proposed_salary - current_salary) / current_salary * 100) if current_salary > 0 else 0
            st.info(f"💰 Salary Increase: {salary_increase:.1f}%")

            justification = st.text_area(
                "Justification for Promotion *",
                placeholder="Provide detailed justification including achievements, skills, performance, and business impact...",
                height=150
            )

            manager_recommendation = st.text_area(
                "Manager Recommendation" if is_manager() else "Nomination Comments",
                placeholder="Additional comments and recommendation...",
                height=100
            )

            effective_date = st.date_input(
                "Proposed Effective Date",
                min_value=date.today(),
                value=date.today() + timedelta(days=30)
            )

            submitted = st.form_submit_button("📤 Submit Promotion Request", use_container_width=True, type="primary")

            if submitted:
                if not all([proposed_position, proposed_grade, proposed_salary, justification]):
                    st.error("❌ Please fill all required fields")
                else:
                    submit_promotion_request(
                        selected_emp_id,
                        selected_emp['position'],
                        selected_emp['grade'],
                        current_salary,
                        proposed_position,
                        proposed_grade,
                        proposed_salary,
                        justification,
                        performance_rating,
                        years_in_role,
                        manager_recommendation,
                        effective_date
                    )


def submit_promotion_request(emp_id, current_position, current_grade, current_salary,
                            proposed_position, proposed_grade, proposed_salary,
                            justification, performance_rating, years_in_role,
                            manager_recommendation, effective_date):
    """Submit a promotion request"""
    user = get_current_user()

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # Determine initial status based on nominator
            initial_status = 'Manager Approved' if is_manager() else 'Pending'

            cursor.execute("""
                INSERT INTO promotion_requests (
                    emp_id, current_position, current_grade, current_salary,
                    proposed_position, proposed_grade, proposed_salary,
                    justification, performance_rating, years_in_current_role,
                    manager_recommendation, status, nominated_by, effective_date,
                    manager_approved_by, manager_approval_date
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                emp_id, current_position, current_grade, current_salary,
                proposed_position, proposed_grade, proposed_salary,
                justification, performance_rating, years_in_role,
                manager_recommendation, initial_status, user['employee_id'], effective_date,
                user['employee_id'] if is_manager() else None,
                datetime.now() if is_manager() else None
            ))

            request_id = cursor.lastrowid

            # Notify employee
            create_notification(
                emp_id,
                "Promotion Nomination",
                f"You have been nominated for promotion to {proposed_position}. The request is under review.",
                'success'
            )

            # Notify HR if manager submitted
            if is_manager():
                cursor.execute("SELECT id FROM employees WHERE department = 'Human Resources' LIMIT 1")
                hr_emp = cursor.fetchone()
                if hr_emp:
                    create_notification(
                        hr_emp['id'],
                        "New Promotion Request - HR Review Required",
                        f"A promotion request (PR-{request_id}) has been submitted and requires HR review.",
                        'info'
                    )
            else:
                # Notify manager if HR submitted
                cursor.execute("SELECT manager_id FROM employees WHERE id = %s", (emp_id,))
                manager = cursor.fetchone()
                if manager and manager['manager_id']:
                    create_notification(
                        manager['manager_id'],
                        "Promotion Request - Manager Approval Required",
                        f"A promotion request (PR-{request_id}) requires your approval.",
                        'info'
                    )

            conn.commit()
            log_audit(f"Submitted promotion request PR-{request_id} for employee {emp_id}", "promotion_requests", request_id)

            st.success(f"✅ Promotion request submitted successfully! Request ID: PR-{request_id}")
            st.balloons()
            st.rerun()

    except Exception as e:
        st.error(f"❌ Error: {str(e)}")


def show_pending_approvals():
    """Show pending promotion requests for approval"""
    user = get_current_user()

    st.markdown("### ⏳ Pending Promotion Approvals")

    with get_db_connection() as conn:
        cursor = conn.cursor()

        if is_manager():
            # Manager sees pending requests from their team
            cursor.execute("""
                SELECT pr.*, e.first_name, e.last_name, e.employee_id, e.department
                FROM promotion_requests pr
                JOIN employees e ON pr.emp_id = e.id
                WHERE e.manager_id = %s AND pr.status = 'Pending'
                ORDER BY pr.created_at DESC
            """, (user['employee_id'],))
        elif is_hr_admin():
            # HR sees manager-approved requests
            cursor.execute("""
                SELECT pr.*, e.first_name, e.last_name, e.employee_id, e.department,
                       m.first_name || ' ' || m.last_name as requested_by_name
                FROM promotion_requests pr
                JOIN employees e ON pr.emp_id = e.id
                LEFT JOIN employees m ON pr.requested_by = m.id
                WHERE pr.status IN ('Manager Approved', 'HR Review', 'Budget Approved')
                ORDER BY pr.created_at DESC
            """)
        else:
            st.info("No pending approvals")
            return

        requests = cursor.fetchall()

    if not requests:
        st.success("✅ No pending approvals!")
        return

    for req in requests:
        status_icon = {
            'Pending': '⏳',
            'Manager Approved': '✅',
            'HR Review': '🔍',
            'Budget Approved': '💰',
            'Approved': '🎉',
            'Rejected': '❌'
        }.get(req['status'], '📋')

        salary_increase = ((req['proposed_salary'] - req['current_salary']) / req['current_salary'] * 100) if req['current_salary'] > 0 else 0

        with st.expander(f"{status_icon} {req['first_name']} {req['last_name']} - {req['proposed_position']} ({salary_increase:.1f}% increase)"):
            col1, col2 = st.columns([2, 1])

            with col1:
                st.markdown(f"""
                **Employee:** {req['first_name']} {req['last_name']} ({req['employee_id']})
                **Department:** {req['department']}

                **Current:** {req['current_position']} ({req['current_grade']}) - ${req['current_salary']:,.0f}
                **Proposed:** {req['proposed_position']} ({req['proposed_grade']}) - ${req['proposed_salary']:,.0f}
                **Increase:** {salary_increase:.1f}%

                **Performance Rating:** {req['performance_rating']}
                **Years in Current Role:** {req['years_in_current_role']:.1f}

                **Justification:**
                {req['justification']}
                """)

                if req.get('manager_recommendation'):
                    st.markdown(f"**Manager Recommendation:**\n{req['manager_recommendation']}")

                if req.get('nominated_by_name'):
                    st.markdown(f"**Nominated By:** {req['nominated_by_name']}")

            with col2:
                st.markdown("**Effective Date:**")
                st.info(str(req['effective_date']))

                st.markdown("**Status:**")
                st.info(req['status'])

            # Approval actions
            st.markdown("---")

            comments = st.text_area("Comments", key=f"comments_{req['id']}", placeholder="Optional comments...")

            col1, col2, col3 = st.columns(3)

            with col1:
                if st.button("✅ Approve", key=f"approve_{req['id']}", use_container_width=True, type="primary"):
                    approve_promotion(req['id'], req['emp_id'], req['status'], comments,
                                    req['proposed_position'], req['proposed_grade'], req['proposed_salary'])
                    st.rerun()

            with col2:
                if st.button("❌ Reject", key=f"reject_{req['id']}", use_container_width=True):
                    reject_promotion(req['id'], req['emp_id'], comments)
                    st.rerun()

            with col3:
                if is_hr_admin() and req['status'] == 'Approved':
                    if st.button("🚀 Implement", key=f"implement_{req['id']}", use_container_width=True):
                        implement_promotion(req['id'], req['emp_id'], req['proposed_position'],
                                          req['proposed_grade'], req['proposed_salary'])
                        st.rerun()


def approve_promotion(request_id, emp_id, current_status, comments, proposed_position, proposed_grade, proposed_salary):
    """Approve a promotion request"""
    user = get_current_user()

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            if is_manager() and current_status == 'Pending':
                # Manager approval
                new_status = 'Manager Approved'
                cursor.execute("""
                    UPDATE promotion_requests SET
                        status = %s,
                        manager_approved_by = %s,
                        manager_approval_date = %s,
                        manager_comments = %s
                    WHERE id = %s
                """, (new_status, user['employee_id'], datetime.now(), comments, request_id))

                # Notify HR
                cursor.execute("SELECT id FROM employees WHERE department = 'Human Resources' LIMIT 1")
                hr_emp = cursor.fetchone()
                if hr_emp:
                    create_notification(
                        hr_emp['id'],
                        "Promotion Request - HR Review Required",
                        f"Promotion request PR-{request_id} has been approved by manager and requires HR review.",
                        'info'
                    )

                # Notify employee
                create_notification(
                    emp_id,
                    "Promotion Request - Manager Approved",
                    f"Your promotion request has been approved by your manager. Awaiting HR review.",
                    'success'
                )

                log_audit(f"Manager approved promotion request PR-{request_id}", "promotion_requests", request_id)
                st.success("✅ Promotion request approved! Sent to HR for review.")

            elif is_hr_admin() and current_status in ['Manager Approved', 'HR Review', 'Budget Approved']:
                # HR can advance through stages
                if current_status == 'Manager Approved':
                    new_status = 'HR Review'
                    message = "Promotion is now under HR review."
                elif current_status == 'HR Review':
                    new_status = 'Budget Approved'
                    message = "Promotion budget approved. Ready for final approval."
                else:  # Budget Approved
                    new_status = 'Approved'
                    message = "Promotion fully approved! Ready to implement."

                cursor.execute("""
                    UPDATE promotion_requests SET
                        status = %s,
                        hr_approved_by = %s,
                        hr_approval_date = %s,
                        hr_comments = %s
                    WHERE id = %s
                """, (new_status, user['employee_id'], datetime.now(), comments, request_id))

                # Notify employee
                create_notification(
                    emp_id,
                    f"Promotion Request - {new_status}",
                    message,
                    'success'
                )

                log_audit(f"HR updated promotion request PR-{request_id} to {new_status}", "promotion_requests", request_id)
                st.success(f"✅ {message}")

            conn.commit()

    except Exception as e:
        st.error(f"❌ Error: {str(e)}")


def reject_promotion(request_id, emp_id, comments):
    """Reject a promotion request"""
    user = get_current_user()

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                UPDATE promotion_requests SET
                    status = 'Rejected',
                    hr_comments = %s
                WHERE id = %s
            """, (comments, request_id))

            # Notify employee
            create_notification(
                emp_id,
                "Promotion Request Rejected",
                f"Your promotion request has been rejected. Reason: {comments or 'No reason provided'}",
                'warning'
            )

            conn.commit()
            log_audit(f"Rejected promotion request PR-{request_id}", "promotion_requests", request_id)

            st.warning("⚠️ Promotion request rejected")

    except Exception as e:
        st.error(f"❌ Error: {str(e)}")


def implement_promotion(request_id, emp_id, new_position, new_grade, new_salary):
    """Implement an approved promotion - update employee record"""
    user = get_current_user()

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # Update employee record
            cursor.execute("""
                UPDATE employees SET
                    position = %s,
                    grade = %s,
                    updated_at = %s
                WHERE id = %s
            """, (new_position, new_grade, datetime.now(), emp_id))

            # Add new financial record
            cursor.execute("""
                INSERT INTO financial_records (emp_id, base_salary, net_pay, period)
                VALUES (%s, %s, %s, %s)
            """, (emp_id, new_salary, new_salary, datetime.now().strftime('%Y-%m')))

            # Update promotion request status
            cursor.execute("""
                UPDATE promotion_requests SET
                    status = 'Implemented'
                WHERE id = %s
            """, (request_id,))

            # Notify employee
            create_notification(
                emp_id,
                "Promotion Implemented!",
                f"Congratulations! Your promotion to {new_position} ({new_grade}) has been implemented. Your new salary is ${new_salary:,.0f}.",
                'success'
            )

            conn.commit()
            log_audit(f"Implemented promotion PR-{request_id} for employee {emp_id}", "promotion_requests", request_id)

            st.success("🎉 Promotion implemented successfully!")
            st.balloons()

    except Exception as e:
        st.error(f"❌ Error: {str(e)}")


def show_my_promotions():
    """Show employee's promotion history"""
    user = get_current_user()

    st.markdown("### 📋 My Promotion History")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM promotion_requests
            WHERE emp_id = %s
            ORDER BY created_at DESC
        """, (user['employee_id'],))
        promotions = cursor.fetchall()

    if not promotions:
        st.info("No promotion requests yet")
        return

    for promo in promotions:
        status_color = {
            'Pending': '🟡',
            'Manager Approved': '🟢',
            'HR Review': '🔵',
            'Budget Approved': '🟣',
            'Approved': '✅',
            'Rejected': '🔴',
            'Implemented': '🎉'
        }.get(promo['status'], '⚪')

        st.markdown(f"""
        <div style="background: rgba(58, 123, 213, 0.05); padding: 15px; border-radius: 10px; margin-bottom: 10px; border-left: 3px solid #3a7bd5;">
            <strong>{status_color} {promo['current_position']} → {promo['proposed_position']}</strong><br>
            <small style="color: #7d96be;">
                Status: {promo['status']}<br>
                Requested: {promo['created_at'][:10]}<br>
                {f"Effective Date: {promo['effective_date']}" if promo['effective_date'] else ''}
            </small>
        </div>
        """, unsafe_allow_html=True)


def show_eligibility_check():
    """Check promotion eligibility for employee"""
    user = get_current_user()

    st.markdown("### 📊 Promotion Eligibility Check")

    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Get employee details
        cursor.execute("SELECT * FROM employees WHERE id = %s", (user['employee_id'],))
        employee = cursor.fetchone()

        # Calculate years in current role
        join_date = employee['join_date']
        years_in_role = (date.today() - join_date).days / 365.25

        # Get latest performance rating
        cursor.execute("""
            SELECT overall_grade, score FROM appraisals
            WHERE emp_id = %s AND status = 'Completed'
            ORDER BY created_at DESC
            LIMIT 1
        """, (user['employee_id'],))
        appraisal = cursor.fetchone()

    # Eligibility criteria
    st.markdown("### Eligibility Criteria")

    criteria = {
        "Minimum 1 year in current role": years_in_role >= 1.0,
        "Performance rating of B+ or higher": appraisal and appraisal['overall_grade'] in ['A+', 'A', 'A-', 'B+'] if appraisal else False,
        "No active PIP": True,  # Would check PIP table
        "No pending promotion requests": True  # Would check promotion_requests
    }

    for criterion, met in criteria.items():
        icon = "✅" if met else "❌"
        st.markdown(f"{icon} {criterion}")

    st.markdown("---")

    # Overall eligibility
    eligible = all(criteria.values())

    if eligible:
        st.success("🎉 You appear eligible for promotion! Discuss with your manager.")
    else:
        st.warning("⚠️ You may not currently meet all promotion criteria. Work with your manager on a development plan.")


def show_team_promotions():
    """Show promotion requests for team (Manager view)"""
    user = get_current_user()

    st.markdown("### 📋 Team Promotion Requests")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT pr.*, e.first_name, e.last_name, e.employee_id
            FROM promotion_requests pr
            JOIN employees e ON pr.emp_id = e.id
            WHERE e.manager_id = %s
            ORDER BY pr.created_at DESC
        """, (user['employee_id'],))
        promotions = cursor.fetchall()

    if not promotions:
        st.info("No promotion requests from your team")
        return

    # Display as table
    df_data = []
    for promo in promotions:
        df_data.append({
            'ID': f"PR-{promo['id']}",
            'Employee': f"{promo['first_name']} {promo['last_name']}",
            'Current': promo['current_position'],
            'Proposed': promo['proposed_position'],
            'Status': promo['status'],
            'Date': promo['created_at'][:10]
        })

    df = pd.DataFrame(df_data)
    st.dataframe(df, use_container_width=True, hide_index=True)


def show_all_promotions():
    """Show all promotion requests (HR Admin view)"""
    st.markdown("### 📋 All Promotion Requests")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT pr.*, e.first_name, e.last_name, e.employee_id, e.department
            FROM promotion_requests pr
            JOIN employees e ON pr.emp_id = e.id
            ORDER BY pr.created_at DESC
        """)
        promotions = cursor.fetchall()

    if not promotions:
        st.info("No promotion requests in the system")
        return

    # Filter by status
    status_filter = st.selectbox("Filter by Status", ["All", "Pending", "Manager Approved", "HR Review", "Budget Approved", "Approved", "Rejected", "Implemented"])

    filtered_promotions = [p for p in promotions if status_filter == "All" or p['status'] == status_filter]

    # Display as table
    df_data = []
    for promo in filtered_promotions:
        salary_increase = ((promo['proposed_salary'] - promo['current_salary']) / promo['current_salary'] * 100) if promo['current_salary'] > 0 else 0

        df_data.append({
            'ID': f"PR-{promo['id']}",
            'Employee': f"{promo['first_name']} {promo['last_name']}",
            'Department': promo['department'],
            'Current': promo['current_position'],
            'Proposed': promo['proposed_position'],
            'Increase %': f"{salary_increase:.1f}%",
            'Status': promo['status'],
            'Date': promo['created_at'][:10]
        })

    df = pd.DataFrame(df_data)
    st.dataframe(df, use_container_width=True, hide_index=True)


def show_promotion_analytics():
    """Show promotion analytics (HR Admin view)"""
    st.markdown("### 📊 Promotion Analytics")

    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Total promotions by status
        cursor.execute("""
            SELECT status, COUNT(*) as count
            FROM promotion_requests
            GROUP BY status
            ORDER BY count DESC
        """)
        status_counts = cursor.fetchall()

        # Promotions by department
        cursor.execute("""
            SELECT e.department, COUNT(*) as count
            FROM promotion_requests pr
            JOIN employees e ON pr.emp_id = e.id
            WHERE pr.status = 'Implemented'
            GROUP BY e.department
            ORDER BY count DESC
        """)
        dept_promotions = cursor.fetchall()

    # Display metrics
    col1, col2, col3 = st.columns(3)

    total_requests = sum(s['count'] for s in status_counts)
    implemented = next((s['count'] for s in status_counts if s['status'] == 'Implemented'), 0)
    pending = next((s['count'] for s in status_counts if s['status'] in ['Pending', 'Manager Approved', 'HR Review']), 0)

    with col1:
        st.metric("Total Requests", total_requests)
    with col2:
        st.metric("Implemented", implemented)
    with col3:
        st.metric("Pending", pending)

    st.markdown("---")

    # Status breakdown
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### By Status")
        for status in status_counts:
            st.markdown(f"**{status['status']}:** {status['count']}")

    with col2:
        if dept_promotions:
            st.markdown("#### By Department (Implemented)")
            for dept in dept_promotions:
                st.markdown(f"**{dept['department']}:** {dept['count']}")
