"""
Appraisals Management Module
Complete self-review → manager review → HR review workflow
"""

import streamlit as st
import pandas as pd
from datetime import datetime, date
from database import get_db_connection
from auth import get_current_user, is_hr_admin, is_manager, is_employee, create_notification, log_audit

def show_appraisals_management():
    """Main appraisals management interface"""
    user = get_current_user()

    st.markdown("## 📋 Performance Appraisals")
    st.markdown("Complete 360-degree performance review workflow")
    st.markdown("---")

    if is_hr_admin():
        tabs = st.tabs(["📊 All Appraisals", "⏳ Pending HR Review", "✅ Completed", "➕ Create New"])
    elif is_manager():
        tabs = st.tabs(["📋 Team Appraisals", "⏳ Pending My Review", "➕ Create New"])
    else:
        tabs = st.tabs(["📝 My Appraisals", "📊 History"])

    with tabs[0]:
        if is_hr_admin():
            show_all_appraisals()
        elif is_manager():
            show_team_appraisals()
        else:
            show_my_appraisals()

    with tabs[1]:
        if is_hr_admin():
            show_pending_hr_review()
        elif is_manager():
            show_pending_manager_review()
        else:
            show_appraisal_history()

    if len(tabs) > 2:
        with tabs[2]:
            if is_hr_admin():
                show_completed_appraisals()
            else:
                show_create_appraisal()

    if len(tabs) > 3:
        with tabs[3]:
            show_create_appraisal()

def show_my_appraisals():
    """Show employee's own appraisals"""
    user = get_current_user()

    st.markdown("### 📝 My Performance Appraisals")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT a.*, e.first_name, e.last_name
            FROM appraisals a
            LEFT JOIN employees e ON a.manager_id = e.id
            WHERE a.emp_id = %s
            ORDER BY a.created_at DESC
        """, (user['employee_id'],))
        appraisals = [dict(row) for row in cursor.fetchall()]

    if appraisals:
        for appraisal in appraisals:
            status_config = {
                'Draft': {'color': 'rgba(125, 150, 190, 0.1)', 'icon': '📝'},
                'Submitted': {'color': 'rgba(240, 180, 41, 0.1)', 'icon': '⏳'},
                'Manager Review': {'color': 'rgba(91, 156, 246, 0.1)', 'icon': '👁️'},
                'HR Review': {'color': 'rgba(58, 123, 213, 0.1)', 'icon': '📋'},
                'Completed': {'color': 'rgba(45, 212, 170, 0.1)', 'icon': '✅'}
            }

            config = status_config.get(appraisal['status'], status_config['Draft'])

            with st.expander(f"{config['icon']} {appraisal['period']} - {appraisal['status']}"):
                col1, col2 = st.columns([2, 1])

                with col1:
                    st.markdown(f"""
                    **Period:** {appraisal['period']}
                    **Status:** {appraisal['status']}
                    **Reviewer:** {appraisal['first_name'] or 'N/A'} {appraisal['last_name'] or ''}
                    **Submitted:** {appraisal['created_at'][:10] if appraisal['created_at'] else 'N/A'}
                    """)

                with col2:
                    if appraisal['overall_rating']:
                        st.metric("Overall Rating", f"{appraisal['overall_rating']}/5")

                # Self-review section
                if appraisal['self_achievements']:
                    st.markdown("**🌟 My Achievements:**")
                    st.info(appraisal['self_achievements'])

                if appraisal['self_areas_improvement']:
                    st.markdown("**📈 Areas for Improvement:**")
                    st.info(appraisal['self_areas_improvement'])

                # Manager feedback
                if appraisal['manager_feedback']:
                    st.markdown("**👤 Manager Feedback:**")
                    st.success(appraisal['manager_feedback'])

                # HR feedback
                if appraisal['hr_feedback']:
                    st.markdown("**📋 HR Feedback:**")
                    st.success(appraisal['hr_feedback'])

                # Submit self-review if in Draft
                if appraisal['status'] == 'Draft':
                    st.markdown("---")
                    with st.form(f"self_review_{appraisal['id']}"):
                        achievements = st.text_area("My Achievements", value=appraisal['self_achievements'] or "",
                                                   placeholder="List your key accomplishments...")
                        improvements = st.text_area("Areas for Improvement", value=appraisal['self_areas_improvement'] or "",
                                                   placeholder="What would you like to improve?")
                        goals = st.text_area("Future Goals", value=appraisal['self_goals'] or "",
                                           placeholder="Your goals for next period...")

                        if st.form_submit_button("📤 Submit Self-Review"):
                            submit_self_review(appraisal['id'], achievements, improvements, goals, appraisal['manager_id'])
                            st.rerun()
    else:
        st.info("No appraisals yet")

def show_appraisal_history():
    """Show historical appraisals"""
    user = get_current_user()

    st.markdown("### 📊 Appraisal History")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM appraisals
            WHERE emp_id = %s AND status = 'Completed'
            ORDER BY period DESC
        """, (user['employee_id'],))
        history = [dict(row) for row in cursor.fetchall()]

    if history:
        ratings = [h['overall_rating'] for h in history if h['overall_rating']]
        if ratings:
            avg_rating = sum(ratings) / len(ratings)
            st.metric("Average Rating", f"{avg_rating:.2f}/5")

        for appraisal in history:
            st.markdown(f"""
                <div style="background: rgba(45, 212, 170, 0.1); padding: 15px; border-radius: 10px; margin-bottom: 10px;">
                    <strong>{appraisal['period']}</strong> - Rating: {appraisal['overall_rating'] or 'N/A'}/5<br>
                    <small style="color: #7d96be;">Completed: {appraisal['hr_review_date'] or appraisal['created_at'][:10]}</small>
                </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No completed appraisals yet")

def show_team_appraisals():
    """Show manager's team appraisals"""
    user = get_current_user()

    st.markdown("### 📋 Team Appraisals")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT a.*, e.first_name, e.last_name, e.employee_id, e.position
            FROM appraisals a
            JOIN employees e ON a.emp_id = e.id
            WHERE e.manager_id = %s OR a.manager_id = %s
            ORDER BY a.created_at DESC
        """, (user['employee_id'], user['employee_id']))
        appraisals = [dict(row) for row in cursor.fetchall()]

    if appraisals:
        # Statistics
        total = len(appraisals)
        pending = len([a for a in appraisals if a['status'] in ['Submitted', 'Manager Review']])
        completed = len([a for a in appraisals if a['status'] == 'Completed'])

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Appraisals", total)
        with col2:
            st.metric("Pending Review", pending)
        with col3:
            st.metric("Completed", completed)

        st.markdown("---")

        # Filter
        status_filter = st.selectbox("Filter by Status", ["All", "Submitted", "Manager Review", "HR Review", "Completed"])

        # Display appraisals
        for appraisal in appraisals:
            if status_filter != "All" and appraisal['status'] != status_filter:
                continue

            with st.expander(f"📋 {appraisal['first_name']} {appraisal['last_name']} - {appraisal['period']} ({appraisal['status']})"):
                show_appraisal_details(appraisal, is_manager=True)
    else:
        st.info("No team appraisals found")

def show_pending_manager_review():
    """Show appraisals pending manager review"""
    user = get_current_user()

    st.markdown("### ⏳ Pending My Review")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT a.*, e.first_name, e.last_name, e.employee_id, e.position
            FROM appraisals a
            JOIN employees e ON a.emp_id = e.id
            WHERE (e.manager_id = %s OR a.manager_id = %s) AND a.status = 'Submitted'
            ORDER BY a.created_at ASC
        """, (user['employee_id'], user['employee_id']))
        pending = [dict(row) for row in cursor.fetchall()]

    if pending:
        st.info(f"📋 {len(pending)} appraisal(s) awaiting your review")

        for appraisal in pending:
            with st.expander(f"📋 {appraisal['first_name']} {appraisal['last_name']} - {appraisal['period']}"):
                show_appraisal_details(appraisal, is_manager=True, allow_review=True)
    else:
        st.success("✅ No appraisals pending review!")

def show_all_appraisals():
    """Show all appraisals (HR view)"""
    st.markdown("### 📊 All Performance Appraisals")

    # Filters
    col1, col2, col3 = st.columns(3)
    with col1:
        status_filter = st.selectbox("Status", ["All", "Draft", "Submitted", "Manager Review", "HR Review", "Completed"])
    with col2:
        period_filter = st.text_input("Period (e.g., 2024-Q1)")
    with col3:
        search = st.text_input("🔍 Search employee")

    with get_db_connection() as conn:
        cursor = conn.cursor()

        query = """
            SELECT a.*, e.first_name, e.last_name, e.employee_id, e.department, e.position
            FROM appraisals a
            JOIN employees e ON a.emp_id = e.id
            WHERE 1=1
        """
        params = []

        if status_filter != "All":
            query += " AND a.status = %s"
            params.append(status_filter)

        if period_filter:
            query += " AND a.period LIKE %s"
            params.append(f"%{period_filter}%")

        if search:
            query += " AND (e.first_name LIKE %s OR e.last_name LIKE %s OR e.employee_id LIKE %s)"
            params.extend([f"%{search}%", f"%{search}%", f"%{search}%"])

        query += " ORDER BY a.created_at DESC LIMIT 50"

        cursor.execute(query, params)
        appraisals = [dict(row) for row in cursor.fetchall()]

    if appraisals:
        for appraisal in appraisals:
            with st.expander(f"📋 {appraisal['first_name']} {appraisal['last_name']} - {appraisal['period']} ({appraisal['status']})"):
                show_appraisal_details(appraisal, is_hr=True, allow_hr_review=appraisal['status']=='HR Review')
    else:
        st.info("No appraisals found")

def show_pending_hr_review():
    """Show appraisals pending HR review"""
    st.markdown("### ⏳ Pending HR Review")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT a.*, e.first_name, e.last_name, e.employee_id, e.department
            FROM appraisals a
            JOIN employees e ON a.emp_id = e.id
            WHERE a.status = 'HR Review'
            ORDER BY a.manager_review_date ASC
        """)
        pending = [dict(row) for row in cursor.fetchall()]

    if pending:
        st.info(f"📋 {len(pending)} appraisal(s) awaiting HR review")

        for appraisal in pending:
            with st.expander(f"📋 {appraisal['first_name']} {appraisal['last_name']} - {appraisal['period']}"):
                show_appraisal_details(appraisal, is_hr=True, allow_hr_review=True)
    else:
        st.success("✅ No appraisals pending HR review!")

def show_completed_appraisals():
    """Show completed appraisals"""
    st.markdown("### ✅ Completed Appraisals")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT a.*, e.first_name, e.last_name, e.employee_id, e.department
            FROM appraisals a
            JOIN employees e ON a.emp_id = e.id
            WHERE a.status = 'Completed'
            ORDER BY a.hr_review_date DESC
            LIMIT 20
        """)
        completed = [dict(row) for row in cursor.fetchall()]

    if completed:
        for appraisal in completed:
            st.markdown(f"""
                <div style="background: rgba(45, 212, 170, 0.1); padding: 15px; border-radius: 10px; margin-bottom: 10px;">
                    <strong>{appraisal['first_name']} {appraisal['last_name']}</strong> - {appraisal['period']}<br>
                    <small style="color: #7d96be;">
                        Rating: {appraisal['overall_rating'] or 'N/A'}/5 •
                        Completed: {appraisal['hr_review_date'][:10] if appraisal['hr_review_date'] else 'N/A'}
                    </small>
                </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No completed appraisals yet")

def show_create_appraisal():
    """Create new appraisal"""
    st.markdown("### ➕ Create New Appraisal")

    with st.form("create_appraisal"):
        # Employee selection
        employees = get_appraisal_employees()

        if not employees:
            st.warning("No employees available for appraisal")
            st.form_submit_button("Create Appraisal", disabled=True)
            return

        emp_options = {f"{e['first_name']} {e['last_name']} ({e['employee_id']})": e['id'] for e in employees}
        selected_emp = st.selectbox("Select Employee *", list(emp_options.keys()))

        period = st.text_input("Period *", placeholder="e.g., 2024-Q1, 2024-Annual", value=f"{datetime.now().year}-Q{(datetime.now().month-1)//3 + 1}")

        submitted = st.form_submit_button("📋 Create Appraisal", use_container_width=True)

        if submitted:
            if not all([selected_emp, period]):
                st.error("❌ Please fill all required fields")
            else:
                emp_id = emp_options[selected_emp]
                create_new_appraisal(emp_id, period)
                st.rerun()

def show_appraisal_details(appraisal, is_manager=False, is_hr=False, allow_review=False, allow_hr_review=False):
    """Display detailed appraisal information"""
    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown(f"""
        **Employee:** {appraisal['first_name']} {appraisal['last_name']} ({appraisal['employee_id']})
        **Position:** {appraisal.get('position', 'N/A')}
        **Department:** {appraisal.get('department', 'N/A')}
        **Period:** {appraisal['period']}
        **Status:** {appraisal['status']}
        """)

    with col2:
        if appraisal['overall_rating']:
            st.metric("Overall Rating", f"{appraisal['overall_rating']}/5")

    st.markdown("---")

    # Self-review
    if appraisal['self_achievements']:
        st.markdown("**🌟 Employee Self-Review:**")
        st.markdown(f"**Achievements:**\n{appraisal['self_achievements']}")
        if appraisal['self_areas_improvement']:
            st.markdown(f"**Areas for Improvement:**\n{appraisal['self_areas_improvement']}")
        if appraisal['self_goals']:
            st.markdown(f"**Future Goals:**\n{appraisal['self_goals']}")

    # Manager review
    if appraisal['manager_feedback']:
        st.markdown("**👤 Manager Review:**")
        st.markdown(f"**Feedback:**\n{appraisal['manager_feedback']}")
        if appraisal['manager_rating']:
            st.markdown(f"**Rating:** {appraisal['manager_rating']}/5")

    # HR review
    if appraisal['hr_feedback']:
        st.markdown("**📋 HR Review:**")
        st.markdown(f"**Feedback:**\n{appraisal['hr_feedback']}")
        if appraisal['overall_rating']:
            st.markdown(f"**Final Rating:** {appraisal['overall_rating']}/5")

    # Manager review form
    if allow_review and is_manager:
        st.markdown("---")
        st.markdown("### 👤 Provide Manager Review")
        with st.form(f"manager_review_{appraisal['id']}"):
            feedback = st.text_area("Manager Feedback *", placeholder="Provide detailed feedback on performance...")
            rating = st.slider("Manager Rating *", 1, 5, 3)

            col1, col2 = st.columns(2)
            with col1:
                if st.form_submit_button("✅ Submit Review", use_container_width=True):
                    submit_manager_review(appraisal['id'], appraisal['emp_id'], feedback, rating)
                    st.rerun()

    # HR review form
    if allow_hr_review and is_hr:
        st.markdown("---")
        st.markdown("### 📋 Provide HR Review")
        with st.form(f"hr_review_{appraisal['id']}"):
            hr_feedback = st.text_area("HR Feedback *", placeholder="Final review and recommendations...")
            overall_rating = st.slider("Overall Rating *", 1, 5, 3)
            recommendations = st.text_area("Recommendations", placeholder="Training, promotion, development plans...")

            col1, col2 = st.columns(2)
            with col1:
                if st.form_submit_button("✅ Complete Appraisal", use_container_width=True):
                    complete_appraisal(appraisal['id'], appraisal['emp_id'], hr_feedback, overall_rating, recommendations)
                    st.rerun()

def get_appraisal_employees():
    """Get list of employees who can receive appraisals"""
    user = get_current_user()

    with get_db_connection() as conn:
        cursor = conn.cursor()

        if is_hr_admin():
            cursor.execute("""
                SELECT id, employee_id, first_name, last_name, position
                FROM employees
                WHERE status = 'Active'
                ORDER BY first_name
            """)
        elif is_manager():
            cursor.execute("""
                SELECT id, employee_id, first_name, last_name, position
                FROM employees
                WHERE manager_id = %s AND status = 'Active'
                ORDER BY first_name
            """, (user['employee_id'],))
        else:
            return []

        return [dict(row) for row in cursor.fetchall()]

def create_new_appraisal(emp_id, period):
    """Create a new appraisal"""
    user = get_current_user()

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # Get manager
            cursor.execute("SELECT manager_id FROM employees WHERE id = %s", (emp_id,))
            result = cursor.fetchone()
            manager_id = result['manager_id'] if result else None

            cursor.execute("""
                INSERT INTO appraisals (
                    emp_id, period, status, manager_id, created_by
                ) VALUES (%s, %s, 'Draft', %s, %s)
            """, (emp_id, period, manager_id, user['employee_id']))

            appraisal_id = cursor.lastrowid

            # Notify employee
            create_notification(
                emp_id,
                "New Performance Appraisal",
                f"A performance appraisal for {period} has been created. Please complete your self-review.",
                'info'
            )

            conn.commit()
            log_audit(f"Created appraisal for period {period}", "appraisals", appraisal_id)
            st.success(f"✅ Appraisal created successfully! ID: APR-{appraisal_id}")
            st.balloons()

    except Exception as e:
        st.error(f"❌ Error: {str(e)}")

def submit_self_review(appraisal_id, achievements, improvements, goals, manager_id):
    """Submit employee self-review"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                UPDATE appraisals SET
                    self_achievements = %s,
                    self_areas_improvement = %s,
                    self_goals = %s,
                    status = 'Submitted',
                    self_review_date = %s
                WHERE id = %s
            """, (achievements, improvements, goals, datetime.now().isoformat(), appraisal_id))

            # Notify manager
            if manager_id:
                create_notification(
                    manager_id,
                    "Appraisal Self-Review Submitted",
                    f"An employee has completed their self-review for appraisal APR-{appraisal_id}.",
                    'info'
                )

            conn.commit()
            log_audit(f"Submitted self-review for appraisal {appraisal_id}", "appraisals", appraisal_id)
            st.success("✅ Self-review submitted successfully!")

    except Exception as e:
        st.error(f"❌ Error: {str(e)}")

def submit_manager_review(appraisal_id, emp_id, feedback, rating):
    """Submit manager review"""
    user = get_current_user()

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                UPDATE appraisals SET
                    manager_feedback = %s,
                    manager_rating = %s,
                    status = 'HR Review',
                    manager_review_date = %s
                WHERE id = %s
            """, (feedback, rating, datetime.now().isoformat(), appraisal_id))

            # Notify HR
            cursor.execute("SELECT id FROM employees WHERE department = 'Human Resources' LIMIT 1")
            hr_emp = cursor.fetchone()
            if hr_emp:
                create_notification(
                    hr_emp['id'],
                    "Appraisal Awaiting HR Review",
                    f"Manager review completed for appraisal APR-{appraisal_id}.",
                    'info'
                )

            # Notify employee
            create_notification(
                emp_id,
                "Manager Review Completed",
                f"Your manager has completed their review for your appraisal (APR-{appraisal_id}).",
                'success'
            )

            conn.commit()
            log_audit(f"Submitted manager review for appraisal {appraisal_id}", "appraisals", appraisal_id)
            st.success("✅ Manager review submitted successfully!")

    except Exception as e:
        st.error(f"❌ Error: {str(e)}")

def complete_appraisal(appraisal_id, emp_id, hr_feedback, overall_rating, recommendations):
    """Complete appraisal with HR review and auto-update employee grade"""
    user = get_current_user()

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # Get appraisal period for grade record
            cursor.execute("SELECT period FROM appraisals WHERE id = %s", (appraisal_id,))
            appraisal_data = cursor.fetchone()
            period = appraisal_data['period'] if appraisal_data else datetime.now().strftime('%Y-Q%s' % ((datetime.now().month-1)//3 + 1))

            # Update appraisal status
            cursor.execute("""
                UPDATE appraisals SET
                    hr_feedback = %s,
                    overall_rating = %s,
                    recommendations = %s,
                    status = 'Completed',
                    hr_review_date = %s,
                    hr_reviewer = %s
                WHERE id = %s
            """, (hr_feedback, overall_rating, recommendations,
                 datetime.now().isoformat(), user['employee_id'], appraisal_id))

            # AUTO-UPDATE EMPLOYEE GRADE based on overall rating
            # Rating to Grade mapping
            grade_mapping = {
                5: 'A+',
                4.5: 'A',
                4: 'A-',
                3.5: 'B+',
                3: 'B',
                2.5: 'B-',
                2: 'C+',
                1.5: 'C',
                1: 'C-'
            }

            # Find closest grade
            new_grade = grade_mapping.get(overall_rating, 'B')
            if overall_rating not in grade_mapping:
                # Find closest rating
                for rating in sorted(grade_mapping.keys(), reverse=True):
                    if overall_rating >= rating:
                        new_grade = grade_mapping[rating]
                        break

            # Update employee grade
            cursor.execute("""
                UPDATE employees SET
                    grade = %s,
                    updated_at = %s
                WHERE id = %s
            """, (new_grade, datetime.now().isoformat(), emp_id))

            # Insert into grades table for history
            cursor.execute("""
                INSERT INTO grades (emp_id, period, overall_grade, score, evaluated_by, created_at)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (emp_id, period, new_grade, overall_rating * 20, user['employee_id'], datetime.now().isoformat()))

            st.info(f"📈 Employee grade automatically updated to: {new_grade}")

            # Notify employee
            create_notification(
                emp_id,
                "Appraisal Completed - Grade Updated",
                f"Your performance appraisal (APR-{appraisal_id}) has been completed with an overall rating of {overall_rating}/5. Your grade has been updated to {new_grade}.",
                'success'
            )

            conn.commit()
            log_audit(f"Completed appraisal {appraisal_id} with rating {overall_rating} and updated grade to {new_grade}", "appraisals", appraisal_id)
            st.success("✅ Appraisal completed successfully! Employee grade auto-updated!")
            st.balloons()

    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
