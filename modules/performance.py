"""
Performance Management Module
Grades, evaluations, and performance tracking
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from database import get_db_connection
from auth import get_current_user, is_hr_admin, is_manager, get_accessible_employees, create_notification, log_audit

def show_performance_management():
    """Main performance management interface"""
    st.markdown("## 🏅 Grades & Performance")
    st.markdown("Track employee performance evaluations and grades")
    st.markdown("---")

    # Show approval tab for HR Admin
    if is_hr_admin():
        tabs = st.tabs(["📊 Performance Overview", "✏️ Add Evaluation", "✅ Pending Approvals", "📜 History"])

        with tabs[0]:
            show_performance_overview()

        with tabs[1]:
            show_add_evaluation()

        with tabs[2]:
            show_pending_grade_approvals()

        with tabs[3]:
            show_performance_history()
    else:
        tabs = st.tabs(["📊 Performance Overview", "✏️ Add Evaluation", "📜 History"])

        with tabs[0]:
            show_performance_overview()

        with tabs[1]:
            show_add_evaluation()

        with tabs[2]:
            show_performance_history()

def show_performance_overview():
    """Show performance statistics and distribution"""
    user = get_current_user()

    # Get grade distribution
    with get_db_connection() as conn:
        cursor = conn.cursor()

        if is_hr_admin():
            cursor.execute("""
                SELECT grade, COUNT(*) as count
                FROM employees
                WHERE status = 'Active' AND grade IS NOT NULL
                GROUP BY grade
                ORDER BY grade
            """)
        elif is_manager():
            cursor.execute("""
                SELECT grade, COUNT(*) as count
                FROM employees
                WHERE manager_id = %s AND status = 'Active' AND grade IS NOT NULL
                GROUP BY grade
                ORDER BY grade
            """, (user['employee_id'],))
        else:
            cursor.execute("""
                SELECT grade, COUNT(*) as count
                FROM employees
                WHERE id = %s AND grade IS NOT NULL
                GROUP BY grade
            """, (user['employee_id'],))

        grade_dist = [dict(row) for row in cursor.fetchall()]

    # Display grade distribution
    if grade_dist:
        st.markdown("### 📊 Grade Distribution")

        cols = st.columns(len(grade_dist))
        for idx, grade_data in enumerate(grade_dist):
            with cols[idx]:
                grade_color = {
                    'A+': '#2dd4aa',
                    'A': '#5b9cf6',
                    'B+': '#c9963a',
                    'B': '#f0b429',
                    'C+': '#fb7185',
                    'C': '#f16464',
                    'D': '#f16464'
                }.get(grade_data['grade'], '#7d96be')

                st.markdown(f"""
                    <div style="background: linear-gradient(135deg, #0e1117, #1c2535);
                                padding: 20px; border-radius: 12px; border: 1px solid #22304a; text-align: center;">
                        <div style="font-size: 32px; font-weight: bold; color: {grade_color}; margin-bottom: 5px;">
                            {grade_data['grade']}
                        </div>
                        <div style="font-size: 24px; color: #dde5f5; margin-bottom: 5px;">
                            {grade_data['count']}
                        </div>
                        <div style="font-size: 12px; color: #7d96be;">
                            employees
                        </div>
                    </div>
                """, unsafe_allow_html=True)

    st.markdown("---")

    # Recent evaluations
    st.markdown("### 📋 Recent Evaluations")

    with get_db_connection() as conn:
        cursor = conn.cursor()

        if is_hr_admin():
            cursor.execute("""
                SELECT g.*, e.first_name, e.last_name, e.employee_id, e.department
                FROM grades g
                JOIN employees e ON g.emp_id = e.id
                ORDER BY g.created_at DESC
                LIMIT 10
            """)
        elif is_manager():
            cursor.execute("""
                SELECT g.*, e.first_name, e.last_name, e.employee_id, e.department
                FROM grades g
                JOIN employees e ON g.emp_id = e.id
                WHERE e.manager_id = %s
                ORDER BY g.created_at DESC
                LIMIT 10
            """, (user['employee_id'],))
        else:
            cursor.execute("""
                SELECT g.*, e.first_name, e.last_name, e.employee_id, e.department
                FROM grades g
                JOIN employees e ON g.emp_id = e.id
                WHERE g.emp_id = %s
                ORDER BY g.created_at DESC
                LIMIT 10
            """, (user['employee_id'],))

        evaluations = [dict(row) for row in cursor.fetchall()]

    if evaluations:
        df = pd.DataFrame(evaluations)
        display_cols = ['employee_id', 'first_name', 'last_name', 'period', 'overall_grade', 'score', 'performance', 'technical', 'teamwork', 'leadership']
        df_display = df[display_cols]
        df_display.columns = ['Emp ID', 'First Name', 'Last Name', 'Period', 'Grade', 'Score', 'Performance', 'Technical', 'Teamwork', 'Leadership']
        st.dataframe(df_display, use_container_width=True, hide_index=True)
    else:
        st.info("No evaluations found")

def show_add_evaluation():
    """Form to add new performance evaluation"""
    user = get_current_user()

    if not (is_hr_admin() or is_manager()):
        st.warning("⚠️ Only managers and HR can create evaluations")
        return

    st.markdown("### ✏️ Add Performance Evaluation")

    # Get employees that can be evaluated
    employees = get_accessible_employees()

    with st.form("evaluation_form"):
        col1, col2 = st.columns(2)

        with col1:
            selected_emp_id = st.selectbox(
                "Select Employee *",
                options=[e['id'] for e in employees],
                format_func=lambda x: f"{next(e['first_name'] + ' ' + e['last_name'] for e in employees if e['id'] == x)} ({next(e['employee_id'] for e in employees if e['id'] == x)})"
            )

            period = st.text_input("Evaluation Period *", placeholder="e.g., Q1 2024, Annual 2024")

            overall_grade = st.selectbox(
                "Overall Grade *",
                options=["A+", "A", "B+", "B", "C+", "C", "D"]
            )

            score = st.slider("Overall Score", 0, 100, 75)

        with col2:
            performance = st.slider("Performance", 0, 5, 3)
            technical = st.slider("Technical Skills", 0, 5, 3)
            teamwork = st.slider("Teamwork", 0, 5, 3)
            leadership = st.slider("Leadership", 0, 5, 3)

        comments = st.text_area("Comments", placeholder="Evaluation comments and feedback...")

        submitted = st.form_submit_button("💾 Save Evaluation", use_container_width=True)

        if submitted:
            if not all([selected_emp_id, period, overall_grade]):
                st.error("❌ Please fill all required fields")
            else:
                try:
                    with get_db_connection() as conn:
                        cursor = conn.cursor()

                        # Insert evaluation with Pending status
                        cursor.execute("""
                            INSERT INTO grades (
                                emp_id, period, overall_grade, score, performance,
                                technical, teamwork, leadership, comments, evaluated_by, status
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """, (selected_emp_id, period, overall_grade, score, performance,
                             technical, teamwork, leadership, comments, user['employee_id'], 'Pending'))

                        eval_id = cursor.lastrowid

                        # DO NOT update employee grade yet - wait for HR approval

                        # Notify HR for approval
                        if is_manager():
                            # Get all HR admins
                            cursor.execute("SELECT id FROM employees WHERE role = 'hr_admin'")
                            hr_admins = cursor.fetchall()
                            for hr in hr_admins:
                                create_notification(
                                    hr['id'],
                                    "Performance Evaluation Pending Approval",
                                    f"Manager has submitted a performance evaluation for period {period}. Grade: {overall_grade}. Please review and approve.",
                                    'info',
                                    eval_id
                                )

                        conn.commit()
                        log_audit(f"Created performance evaluation for period: {period} (Pending HR Approval)", "grades", eval_id)

                        st.success(f"✅ Performance evaluation submitted for HR approval!")
                        st.info("ℹ️ The grade will be applied to the employee's profile after HR approval.")
                        st.rerun()

                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")

def show_performance_history():
    """Show complete performance history"""
    user = get_current_user()

    st.markdown("### 📜 Performance History")

    # Filters
    col1, col2, col3 = st.columns(3)
    with col1:
        search = st.text_input("🔍 Search employee")
    with col2:
        grade_filter = st.selectbox("Grade", ["All", "A+", "A", "B+", "B", "C+", "C", "D"])
    with col3:
        period_filter = st.text_input("Period", placeholder="e.g., 2024")

    with get_db_connection() as conn:
        cursor = conn.cursor()

        query = """
            SELECT g.*, e.first_name, e.last_name, e.employee_id, e.department, e.position
            FROM grades g
            JOIN employees e ON g.emp_id = e.id
            WHERE 1=1
        """
        params = []

        if is_manager():
            query += " AND e.manager_id = %s"
            params.append(user['employee_id'])
        elif not is_hr_admin():
            query += " AND g.emp_id = %s"
            params.append(user['employee_id'])

        if search:
            query += " AND (e.first_name LIKE %s OR e.last_name LIKE %s OR e.employee_id LIKE %s)"
            params.extend([f"%{search}%", f"%{search}%", f"%{search}%"])

        if grade_filter != "All":
            query += " AND g.overall_grade = %s"
            params.append(grade_filter)

        if period_filter:
            query += " AND g.period LIKE %s"
            params.append(f"%{period_filter}%")

        query += " ORDER BY g.created_at DESC LIMIT 100"

        cursor.execute(query, params)
        history = [dict(row) for row in cursor.fetchall()]

    if history:
        for eval in history:
            with st.expander(f"📊 {eval['first_name']} {eval['last_name']} - {eval['period']} (Grade: {eval['overall_grade']})"):
                col1, col2 = st.columns([2, 1])

                with col1:
                    st.markdown(f"""
                    **Employee:** {eval['first_name']} {eval['last_name']} ({eval['employee_id']})
                    **Position:** {eval['position']}
                    **Department:** {eval['department']}
                    **Period:** {eval['period']}
                    **Overall Grade:** {eval['overall_grade']}
                    **Score:** {eval['score']}/100
                    **Comments:** {eval['comments'] or 'No comments'}
                    **Evaluated:** {eval['created_at']}
                    """)

                with col2:
                    st.metric("Performance", f"{eval['performance']}/5", f"{eval['performance'] * 20}%")
                    st.metric("Technical", f"{eval['technical']}/5", f"{eval['technical'] * 20}%")
                    st.metric("Teamwork", f"{eval['teamwork']}/5", f"{eval['teamwork'] * 20}%")
                    st.metric("Leadership", f"{eval['leadership']}/5", f"{eval['leadership'] * 20}%")
    else:
        st.info("No performance history found")

def show_pending_grade_approvals():
    """Show pending grade evaluations for HR approval"""
    user = get_current_user()

    if not is_hr_admin():
        st.error("🚫 Access Denied - HR Admin Only")
        return

    st.markdown("### ✅ Pending Grade Approvals")
    st.markdown("Review and approve performance evaluations submitted by managers")
    st.markdown("---")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT g.*,
                   e.first_name, e.last_name, e.employee_id, e.position, e.department, e.grade as current_grade,
                   mgr.first_name || ' ' || mgr.last_name as manager_name
            FROM grades g
            JOIN employees e ON g.emp_id = e.id
            LEFT JOIN employees mgr ON g.evaluated_by = mgr.id
            WHERE g.status = 'Pending'
            ORDER BY g.created_at DESC
        """)
        pending_evals = cursor.fetchall()

    if not pending_evals:
        st.success("✅ No pending grade approvals!")
        return

    st.info(f"📋 {len(pending_evals)} evaluation(s) pending approval")

    for eval in pending_evals:
        status_icon = "⏳"

        with st.expander(f"{status_icon} {eval['first_name']} {eval['last_name']} - {eval['period']} (Proposed Grade: {eval['overall_grade']})"):
            col1, col2, col3 = st.columns([2, 2, 1])

            with col1:
                st.markdown("### Employee Information")
                st.markdown(f"**Name:** {eval['first_name']} {eval['last_name']}")
                st.markdown(f"**Employee ID:** {eval['employee_id']}")
                st.markdown(f"**Position:** {eval['position']}")
                st.markdown(f"**Department:** {eval['department']}")
                st.markdown(f"**Current Grade:** {eval['current_grade'] or 'Not set'}")
                st.markdown(f"**Proposed Grade:** {eval['overall_grade']}")

            with col2:
                st.markdown("### Evaluation Details")
                st.markdown(f"**Period:** {eval['period']}")
                st.markdown(f"**Overall Score:** {eval['score']}/100")
                st.markdown(f"**Evaluated By:** {eval['manager_name']}")
                st.markdown(f"**Submitted:** {eval['created_at'].strftime('%Y-%m-%d %H:%M')}")

                st.markdown("---")
                st.markdown("**Performance Metrics:**")
                st.progress(eval['performance'] / 5, text=f"Performance: {eval['performance']}/5")
                st.progress(eval['technical'] / 5, text=f"Technical: {eval['technical']}/5")
                st.progress(eval['teamwork'] / 5, text=f"Teamwork: {eval['teamwork']}/5")
                st.progress(eval['leadership'] / 5, text=f"Leadership: {eval['leadership']}/5")

            with col3:
                st.markdown("### Actions")

                # HR Comments
                hr_comments = st.text_area(
                    "HR Comments",
                    key=f"hr_comments_{eval['id']}",
                    placeholder="Add your review comments..."
                )

                col_a, col_b = st.columns(2)

                with col_a:
                    if st.button("✅ Approve", key=f"approve_{eval['id']}", use_container_width=True):
                        approve_grade_evaluation(eval['id'], eval['emp_id'], eval['overall_grade'], hr_comments)
                        st.success("Approved!")
                        st.rerun()

                with col_b:
                    if st.button("❌ Reject", key=f"reject_{eval['id']}", use_container_width=True):
                        reject_grade_evaluation(eval['id'], hr_comments)
                        st.warning("Rejected")
                        st.rerun()

            # Show manager's comments
            if eval['comments']:
                st.markdown("---")
                st.markdown("**Manager's Comments:**")
                st.info(eval['comments'])

def approve_grade_evaluation(eval_id, emp_id, new_grade, hr_comments):
    """Approve grade evaluation and update employee grade"""
    user = get_current_user()

    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Update evaluation status
        cursor.execute("""
            UPDATE grades
            SET status = 'Approved',
                hr_approved_by = %s,
                hr_approval_date = NOW(),
                hr_comments = %s
            WHERE id = %s
        """, (user['employee_id'], hr_comments, eval_id))

        # NOW update employee grade after HR approval
        cursor.execute("""
            UPDATE employees
            SET grade = %s
            WHERE id = %s
        """, (new_grade, emp_id))

        # Notify employee
        create_notification(
            emp_id,
            "Performance Evaluation Approved",
            f"Your performance evaluation has been approved by HR. Your new grade is: {new_grade}",
            'success',
            eval_id
        )

        # Notify the manager who created it
        cursor.execute("SELECT evaluated_by FROM grades WHERE id = %s", (eval_id,))
        manager_id = cursor.fetchone()['evaluated_by']
        if manager_id:
            create_notification(
                manager_id,
                "Performance Evaluation Approved",
                f"The performance evaluation you submitted has been approved by HR. Grade: {new_grade}",
                'success',
                eval_id
            )

        conn.commit()
        log_audit(f"Approved performance evaluation ID {eval_id}, updated grade to {new_grade}", "grades", eval_id)

def reject_grade_evaluation(eval_id, hr_comments):
    """Reject grade evaluation"""
    user = get_current_user()

    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Update evaluation status
        cursor.execute("""
            UPDATE grades
            SET status = 'Rejected',
                hr_approved_by = %s,
                hr_approval_date = NOW(),
                hr_comments = %s
            WHERE id = %s
        """, (user['employee_id'], hr_comments, eval_id))

        # Get employee and manager info
        cursor.execute("""
            SELECT emp_id, evaluated_by
            FROM grades
            WHERE id = %s
        """, (eval_id,))
        eval_info = cursor.fetchone()

        # Notify employee
        create_notification(
            eval_info['emp_id'],
            "Performance Evaluation Rejected",
            f"Your performance evaluation has been rejected by HR. Reason: {hr_comments or 'No reason provided'}",
            'warning',
            eval_id
        )

        # Notify manager
        if eval_info['evaluated_by']:
            create_notification(
                eval_info['evaluated_by'],
                "Performance Evaluation Rejected",
                f"The performance evaluation you submitted has been rejected by HR. Reason: {hr_comments or 'No reason provided'}",
                'warning',
                eval_id
            )

        conn.commit()
        log_audit(f"Rejected performance evaluation ID {eval_id}", "grades", eval_id)
