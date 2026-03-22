"""
Exit Management Module
Employee resignation and exit process management
"""

import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
from database import get_db_connection
from auth import get_current_user, is_hr_admin, is_manager, create_notification, log_audit

def show_exit_management():
    """Main exit management interface"""
    user = get_current_user()

    st.markdown("## 🚪 Exit Management")
    st.markdown("Manage employee resignation and exit process")
    st.markdown("---")

    if is_hr_admin():
        tabs = st.tabs(["📋 All Exits", "⏳ Pending Clearance", "✅ Resignation Requests", "📊 Exit Analytics"])
    elif is_manager():
        tabs = st.tabs(["👥 Team Exits", "✅ Resignation Requests", "📋 Clearance Tasks"])
    else:
        tabs = st.tabs(["📝 Submit Resignation", "📊 My Exit Process"])

    with tabs[0]:
        if is_hr_admin():
            show_all_exits()
        elif is_manager():
            show_team_exits()
        else:
            show_resignation_form()

    with tabs[1]:
        if is_hr_admin():
            show_pending_clearance()
        elif is_manager():
            show_resignation_approvals()
        else:
            show_my_exit_process()

    with tabs[2]:
        if is_hr_admin():
            show_resignation_approvals()
        elif is_manager():
            show_clearance_tasks()

    if len(tabs) > 3:
        with tabs[3]:
            show_exit_analytics()

def show_my_exit_process():
    """Show employee's exit process"""
    user = get_current_user()

    st.markdown("### 📝 My Exit Process")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM exit_process
            WHERE emp_id = %s
            ORDER BY created_at DESC
            LIMIT 1
        """, (user['employee_id'],))
        exit_record = cursor.fetchone()

        if exit_record:
            exit_record = dict(exit_record)

            st.markdown(f"""
                <div style="background: rgba(241, 100, 100, 0.1); padding: 20px; border-radius: 10px; margin-bottom: 20px;">
                    <h3 style="margin-top: 0;">Exit Process Status</h3>
                    <p><strong>Status:</strong> {exit_record['status']}</p>
                    <p><strong>Resignation Date:</strong> {exit_record['resignation_date']}</p>
                    <p><strong>Last Working Day:</strong> {exit_record['last_working_day']}</p>
                    <p><strong>Reason:</strong> {exit_record['reason_for_leaving']}</p>
                </div>
            """, unsafe_allow_html=True)

            # Clearance checklist
            st.markdown("### ✅ Clearance Checklist")

            checklist = [
                ("IT Equipment", exit_record.get('it_clearance', 'Pending')),
                ("Access Cards", exit_record.get('access_clearance', 'Pending')),
                ("Documentation", exit_record.get('documentation_clearance', 'Pending')),
                ("Finance", exit_record.get('finance_clearance', 'Pending')),
                ("Final Settlement", exit_record.get('final_settlement_status', 'Pending'))
            ]

            for item, status in checklist:
                icon = '✅' if status == 'Completed' else '⏳'
                st.markdown(f"{icon} **{item}**: {status}")

        else:
            st.info("No exit process initiated")

def show_exit_status():
    """Show exit process status summary"""
    user = get_current_user()

    st.markdown("### 📊 Exit Process Status")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM exit_process
            WHERE emp_id = %s
            ORDER BY created_at DESC
            LIMIT 1
        """, (user['employee_id'],))
        exit_record = cursor.fetchone()

        if exit_record:
            exit_record = dict(exit_record)

            # Calculate progress
            clearances = [
                exit_record.get('it_clearance'),
                exit_record.get('access_clearance'),
                exit_record.get('documentation_clearance'),
                exit_record.get('finance_clearance')
            ]
            completed = sum(1 for c in clearances if c == 'Completed')
            total = len(clearances)
            progress = (completed / total * 100) if total > 0 else 0

            st.metric("Clearance Progress", f"{completed}/{total} completed")
            st.progress(progress / 100)

            # Days remaining
            if exit_record['last_working_day']:
                last_day = datetime.strptime(exit_record['last_working_day'], '%Y-%m-%d').date()
                days_left = (last_day - date.today()).days
                st.metric("Days Until Last Working Day", days_left)

        else:
            st.info("No exit process")

def show_team_exits():
    """Show team member exits"""
    user = get_current_user()

    st.markdown("### 👥 Team Member Exits")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT ep.*, e.first_name, e.last_name, e.employee_id
            FROM exit_process ep
            JOIN employees e ON ep.emp_id = e.id
            WHERE e.manager_id = %s
            ORDER BY ep.created_at DESC
        """, (user['employee_id'],))
        exits = [dict(row) for row in cursor.fetchall()]

    if exits:
        for exit_rec in exits:
            with st.expander(f"🚪 {exit_rec['first_name']} {exit_rec['last_name']} - {exit_rec['status']}"):
                st.markdown(f"""
                **Employee:** {exit_rec['first_name']} {exit_rec['last_name']} ({exit_rec['employee_id']})
                **Resignation Date:** {exit_rec['resignation_date']}
                **Last Working Day:** {exit_rec['last_working_day']}
                **Reason:** {exit_rec['reason_for_leaving']}
                **Status:** {exit_rec['status']}
                """)

                if exit_rec.get('manager_feedback'):
                    st.info(f"**Your Feedback:** {exit_rec['manager_feedback']}")
                else:
                    with st.form(f"feedback_{exit_rec['id']}"):
                        feedback = st.text_area("Manager Feedback", placeholder="Provide feedback...")
                        if st.form_submit_button("💬 Submit Feedback"):
                            add_exit_feedback(exit_rec['id'], feedback, exit_rec['emp_id'])
                            st.rerun()
    else:
        st.info("No team member exits")

def show_clearance_tasks():
    """Show clearance tasks for manager"""
    st.markdown("### 📋 Clearance Tasks")

    st.info("Manager clearance tasks will appear here when team members initiate exit process")

def show_all_exits():
    """Show all exit processes"""
    st.markdown("### 📋 All Exit Processes")

    # Filters
    col1, col2 = st.columns(2)
    with col1:
        status_filter = st.selectbox("Status", ["All", "Initiated", "In Progress", "Completed", "Cancelled"])
    with col2:
        search = st.text_input("🔍 Search employee")

    with get_db_connection() as conn:
        cursor = conn.cursor()

        query = """
            SELECT ep.*, e.first_name, e.last_name, e.employee_id, e.department
            FROM exit_process ep
            JOIN employees e ON ep.emp_id = e.id
            WHERE 1=1
        """
        params = []

        if status_filter != "All":
            query += " AND ep.status = %s"
            params.append(status_filter)

        if search:
            query += " AND (e.first_name LIKE %s OR e.last_name LIKE %s OR e.employee_id LIKE %s)"
            params.extend([f"%{search}%", f"%{search}%", f"%{search}%"])

        query += " ORDER BY ep.created_at DESC"

        cursor.execute(query, params)
        exits = [dict(row) for row in cursor.fetchall()]

    if exits:
        for exit_rec in exits:
            with st.expander(f"🚪 {exit_rec['first_name']} {exit_rec['last_name']} - {exit_rec['status']}"):
                col1, col2 = st.columns([2, 1])

                with col1:
                    st.markdown(f"""
                    **Employee:** {exit_rec['first_name']} {exit_rec['last_name']} ({exit_rec['employee_id']})
                    **Department:** {exit_rec['department']}
                    **Resignation Date:** {exit_rec['resignation_date']}
                    **Last Working Day:** {exit_rec['last_working_day']}
                    **Notice Period:** {exit_rec.get('notice_period_days', 'N/A')} days
                    **Reason:** {exit_rec['reason_for_leaving']}
                    **Status:** {exit_rec['status']}
                    """)

                with col2:
                    # Clearance status
                    st.markdown("**Clearances:**")
                    st.markdown(f"IT: {exit_rec.get('it_clearance', 'Pending')}")
                    st.markdown(f"Access: {exit_rec.get('access_clearance', 'Pending')}")
                    st.markdown(f"Docs: {exit_rec.get('documentation_clearance', 'Pending')}")
                    st.markdown(f"Finance: {exit_rec.get('finance_clearance', 'Pending')}")

                # Update clearances
                st.markdown("---")
                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    if st.button("✅ IT Clear", key=f"it_{exit_rec['id']}"):
                        update_clearance(exit_rec['id'], 'it_clearance', 'Completed')
                        st.rerun()

                with col2:
                    if st.button("✅ Access Clear", key=f"access_{exit_rec['id']}"):
                        update_clearance(exit_rec['id'], 'access_clearance', 'Completed')
                        st.rerun()

                with col3:
                    if st.button("✅ Docs Clear", key=f"docs_{exit_rec['id']}"):
                        update_clearance(exit_rec['id'], 'documentation_clearance', 'Completed')
                        st.rerun()

                with col4:
                    if st.button("✅ Finance Clear", key=f"finance_{exit_rec['id']}"):
                        update_clearance(exit_rec['id'], 'finance_clearance', 'Completed')
                        st.rerun()

                # Complete exit
                if all([
                    exit_rec.get('it_clearance') == 'Completed',
                    exit_rec.get('access_clearance') == 'Completed',
                    exit_rec.get('documentation_clearance') == 'Completed',
                    exit_rec.get('finance_clearance') == 'Completed'
                ]) and exit_rec['status'] != 'Completed':
                    if st.button("🎯 Complete Exit Process", key=f"complete_{exit_rec['id']}"):
                        complete_exit(exit_rec['id'], exit_rec['emp_id'])
                        st.rerun()
    else:
        st.info("No exit processes found")

def show_pending_clearance():
    """Show exits pending clearance"""
    st.markdown("### ⏳ Pending Clearance")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT ep.*, e.first_name, e.last_name, e.employee_id
            FROM exit_process ep
            JOIN employees e ON ep.emp_id = e.id
            WHERE ep.status IN ('Initiated', 'In Progress')
            ORDER BY ep.last_working_day ASC
        """)
        pending = [dict(row) for row in cursor.fetchall()]

    if pending:
        st.info(f"📋 {len(pending)} exit process(es) pending clearance")

        for exit_rec in pending:
            st.markdown(f"""
                <div style="background: rgba(240, 180, 41, 0.1); padding: 12px; border-radius: 8px; margin-bottom: 8px;">
                    <strong>{exit_rec['first_name']} {exit_rec['last_name']}</strong> ({exit_rec['employee_id']})<br>
                    <small style="color: #7d96be;">
                        Last Day: {exit_rec['last_working_day']} •
                        IT: {exit_rec.get('it_clearance', 'Pending')} •
                        Access: {exit_rec.get('access_clearance', 'Pending')}
                    </small>
                </div>
            """, unsafe_allow_html=True)
    else:
        st.success("✅ No pending clearances!")

def show_exit_analytics():
    """Show exit analytics"""
    st.markdown("### 📊 Exit Analytics")

    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Total exits
        cursor.execute("SELECT COUNT(*) as cnt FROM exit_process")
        total = cursor.fetchone()['cnt']

        # By reason
        cursor.execute("""
            SELECT reason_for_leaving, COUNT(*) as count
            FROM exit_process
            GROUP BY reason_for_leaving
            ORDER BY count DESC
        """)
        by_reason = [dict(row) for row in cursor.fetchall()]

        # By department
        cursor.execute("""
            SELECT e.department, COUNT(*) as count
            FROM exit_process ep
            JOIN employees e ON ep.emp_id = e.id
            GROUP BY e.department
            ORDER BY count DESC
        """)
        by_dept = [dict(row) for row in cursor.fetchall()]

    st.metric("Total Exits", total)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Reasons for Leaving")
        if by_reason:
            for item in by_reason:
                st.markdown(f"**{item['reason_for_leaving']}**: {item['count']}")

    with col2:
        st.markdown("#### By Department")
        if by_dept:
            for item in by_dept:
                st.markdown(f"**{item['department']}**: {item['count']}")

def add_exit_feedback(exit_id, feedback, emp_id):
    """Add manager feedback to exit"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                UPDATE exit_process SET manager_feedback = %s
                WHERE id = %s
            """, (feedback, exit_id))

            conn.commit()
            log_audit(f"Added feedback to exit {exit_id}", "exit_process", exit_id)
            st.success("✅ Feedback added!")

    except Exception as e:
        st.error(f"❌ Error: {str(e)}")

def update_clearance(exit_id, clearance_field, status):
    """Update clearance status"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(f"""
                UPDATE exit_process SET
                    {clearance_field} = %s,
                    status = 'In Progress'
                WHERE id = %s
            """, (status, exit_id))

            conn.commit()
            log_audit(f"Updated {clearance_field} for exit {exit_id}", "exit_process", exit_id)
            st.success(f"✅ {clearance_field.replace('_', ' ').title()} updated!")

    except Exception as e:
        st.error(f"❌ Error: {str(e)}")

def complete_exit(exit_id, emp_id):
    """Complete exit process"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                UPDATE exit_process SET
                    status = 'Completed',
                    exit_date = %s
                WHERE id = %s
            """, (datetime.now().isoformat(), exit_id))

            # Update employee status
            cursor.execute("UPDATE employees SET status = 'Inactive' WHERE id = %s", (emp_id,))

            conn.commit()
            log_audit(f"Completed exit process {exit_id}", "exit_process", exit_id)
            st.success("✅ Exit process completed!")
            st.balloons()

    except Exception as e:
        st.error(f"❌ Error: {str(e)}")

def show_resignation_form():
    """Employee resignation submission form"""
    user = get_current_user()

    st.markdown("### 📝 Submit Resignation")
    st.markdown("Submit your resignation notice to your manager and HR")
    st.markdown("---")

    # Check if already has pending resignation
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM exit_process
            WHERE emp_id = %s AND status IN ('Pending', 'Manager Acknowledged', 'In Progress')
        """, (user['employee_id'],))
        existing = cursor.fetchone()

    if existing:
        st.warning("⚠️ You already have a pending resignation/exit process.")
        st.markdown(f"**Status:** {existing['status']}")
        st.markdown(f"**Resignation Date:** {existing['resignation_date']}")
        st.markdown(f"**Last Working Day:** {existing['last_working_day']}")
        return

    with st.form("resignation_form"):
        st.markdown("### Resignation Details")

        resignation_date = st.date_input(
            "Resignation Date *",
            value=date.today(),
            help="The date you are submitting this resignation"
        )

        notice_period_days = st.number_input(
            "Notice Period (Days) *",
            min_value=0,
            max_value=90,
            value=30,
            help="Standard notice period as per your contract"
        )

        proposed_last_day = resignation_date + timedelta(days=notice_period_days)
        last_working_day = st.date_input(
            "Proposed Last Working Day *",
            value=proposed_last_day,
            min_value=resignation_date
        )

        reason = st.selectbox(
            "Reason for Leaving *",
            options=[
                "Career Growth",
                "Better Opportunity",
                "Personal Reasons",
                "Relocation",
                "Health Reasons",
                "Further Studies",
                "Retirement",
                "Other"
            ]
        )

        additional_comments = st.text_area(
            "Additional Comments",
            placeholder="Any additional information you'd like to share...",
            help="Optional: Provide more details about your resignation"
        )

        st.markdown("---")
        st.markdown("### Handover Plan")

        handover_notes = st.text_area(
            "Handover Notes",
            placeholder="Describe your key responsibilities and what needs to be handed over...",
            help="Help us prepare for a smooth transition"
        )

        submitted = st.form_submit_button("📤 Submit Resignation", use_container_width=True)

        if submitted:
            try:
                with get_db_connection() as conn:
                    cursor = conn.cursor()

                    # Create exit process record
                    cursor.execute("""
                        INSERT INTO exit_process (
                            emp_id, resignation_date, last_working_day, reason_for_leaving,
                            status, exit_type, handover_notes, notice_period
                        ) VALUES (%s, %s, %s, %s, 'Pending', 'Resignation', %s, %s)
                    """, (user['employee_id'], resignation_date.isoformat(),
                         last_working_day.isoformat(),
                         f"{reason}. {additional_comments}" if additional_comments else reason,
                         handover_notes, notice_period_days))

                    exit_id = cursor.lastrowid

                    # Get manager
                    cursor.execute("SELECT manager_id FROM employees WHERE id = %s", (user['employee_id'],))
                    result = cursor.fetchone()

                    # Notify manager
                    if result and result['manager_id']:
                        create_notification(
                            result['manager_id'],
                            "Employee Resignation Submitted",
                            f"{user['full_name']} has submitted a resignation. Last working day: {last_working_day.strftime('%Y-%m-%d')}. Please review and acknowledge.",
                            'warning',
                            exit_id
                        )

                    # Notify HR
                    cursor.execute("SELECT id FROM employees WHERE role = 'hr_admin'")
                    hr_admins = cursor.fetchall()
                    for hr in hr_admins:
                        create_notification(
                            hr['id'],
                            "New Resignation Submitted",
                            f"{user['full_name']} has submitted a resignation. Last working day: {last_working_day.strftime('%Y-%m-%d')}.",
                            'warning',
                            exit_id
                        )

                    conn.commit()
                    log_audit(f"Employee submitted resignation, last day: {last_working_day}", "exit_process", exit_id)

                    st.success("✅ Resignation submitted successfully!")
                    st.info("Your manager will review and acknowledge your resignation. HR will initiate the exit process.")
                    st.rerun()

            except Exception as e:
                st.error(f"❌ Error: {str(e)}")

def show_resignation_approvals():
    """Manager and HR interface to review resignation requests"""
    user = get_current_user()

    st.markdown("### ✅ Resignation Requests")
    st.markdown("---")

    with get_db_connection() as conn:
        cursor = conn.cursor()

        if is_manager() and not is_hr_admin():
            # Manager sees team resignations
            cursor.execute("""
                SELECT ep.*,
                       e.first_name, e.last_name, e.employee_id, e.position
                FROM exit_process ep
                JOIN employees e ON ep.emp_id = e.id
                WHERE e.manager_id = %s AND ep.status = 'Pending'
                ORDER BY ep.created_at DESC
            """, (user['employee_id'],))
        elif is_hr_admin():
            # HR sees all resignations
            cursor.execute("""
                SELECT ep.*,
                       e.first_name, e.last_name, e.employee_id, e.position, e.department
                FROM exit_process ep
                JOIN employees e ON ep.emp_id = e.id
                WHERE ep.status IN ('Pending', 'Manager Acknowledged')
                ORDER BY ep.created_at DESC
            """)
        else:
            st.error("Access denied")
            return

        resignations = cursor.fetchall()

    if not resignations:
        st.success("✅ No pending resignation requests!")
        return

    st.info(f"📋 {len(resignations)} resignation(s) pending review")

    for resignation in resignations:
        status_icon = "📝" if resignation['status'] == 'Pending' else "✅"

        with st.expander(f"{status_icon} {resignation['first_name']} {resignation['last_name']} - Last Day: {resignation['last_working_day']}"):
            col1, col2, col3 = st.columns([2, 2, 1])

            with col1:
                st.markdown("### Employee Information")
                st.markdown(f"**Name:** {resignation['first_name']} {resignation['last_name']}")
                st.markdown(f"**Employee ID:** {resignation['employee_id']}")
                st.markdown(f"**Position:** {resignation['position']}")
                if 'department' in resignation:
                    st.markdown(f"**Department:** {resignation['department']}")

            with col2:
                st.markdown("### Resignation Details")
                st.markdown(f"**Resignation Date:** {resignation['resignation_date']}")
                st.markdown(f"**Last Working Day:** {resignation['last_working_day']}")
                st.markdown(f"**Notice Period:** {resignation.get('notice_period', 'N/A')} days")
                st.markdown(f"**Reason:** {resignation['reason_for_leaving']}")
                st.markdown(f"**Status:** {resignation['status']}")

                if resignation.get('handover_notes'):
                    st.markdown("---")
                    st.markdown("**Handover Notes:**")
                    st.info(resignation['handover_notes'])

            with col3:
                st.markdown("### Actions")

                comments = st.text_area(
                    "Comments",
                    key=f"comments_{resignation['id']}",
                    placeholder="Add your comments..."
                )

                if is_manager() and resignation['status'] == 'Pending':
                    if st.button("✅ Acknowledge", key=f"ack_{resignation['id']}", use_container_width=True):
                        acknowledge_resignation(resignation['id'], resignation['emp_id'], comments)
                        st.success("Acknowledged!")
                        st.rerun()

                elif is_hr_admin():
                    col_a, col_b = st.columns(2)

                    with col_a:
                        if st.button("✅ Start Exit Process", key=f"start_{resignation['id']}", use_container_width=True):
                            start_exit_process(resignation['id'], resignation['emp_id'], comments)
                            st.success("Exit process started!")
                            st.rerun()

                    with col_b:
                        if st.button("❌ Reject", key=f"reject_{resignation['id']}", use_container_width=True):
                            reject_resignation(resignation['id'], resignation['emp_id'], comments)
                            st.warning("Rejected")
                            st.rerun()

def acknowledge_resignation(exit_id, emp_id, comments):
    """Manager acknowledges employee resignation"""
    user = get_current_user()

    with get_db_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE exit_process
            SET status = 'Manager Acknowledged',
                manager_comments = %s
            WHERE id = %s
        """, (comments, exit_id))

        # Notify employee
        create_notification(
            emp_id,
            "Resignation Acknowledged",
            f"Your manager has acknowledged your resignation. {comments if comments else 'HR will initiate the exit process.'}",
            'info',
            exit_id
        )

        # Notify HR
        cursor.execute("SELECT id FROM employees WHERE role = 'hr_admin'")
        hr_admins = cursor.fetchall()
        for hr in hr_admins:
            create_notification(
                hr['id'],
                "Resignation Acknowledged by Manager",
                f"Manager has acknowledged a resignation. Please initiate the exit process.",
                'info',
                exit_id
            )

        conn.commit()
        log_audit(f"Manager acknowledged resignation {exit_id}", "exit_process", exit_id)

def start_exit_process(exit_id, emp_id, comments):
    """HR starts the exit process"""
    user = get_current_user()

    with get_db_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE exit_process
            SET status = 'In Progress',
                hr_comments = %s
            WHERE id = %s
        """, (comments, exit_id))

        # Notify employee
        create_notification(
            emp_id,
            "Exit Process Initiated",
            f"HR has initiated your exit process. You will be guided through the clearance steps. {comments if comments else ''}",
            'info',
            exit_id
        )

        conn.commit()
        log_audit(f"HR started exit process {exit_id}", "exit_process", exit_id)

def reject_resignation(exit_id, emp_id, comments):
    """HR rejects resignation (rare case)"""
    user = get_current_user()

    with get_db_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE exit_process
            SET status = 'Rejected',
                hr_comments = %s
            WHERE id = %s
        """, (comments, exit_id))

        # Notify employee
        create_notification(
            emp_id,
            "Resignation Request Rejected",
            f"Your resignation has been rejected. Reason: {comments or 'Please contact HR for details.'}",
            'warning',
            exit_id
        )

        conn.commit()
        log_audit(f"HR rejected resignation {exit_id}", "exit_process", exit_id)
