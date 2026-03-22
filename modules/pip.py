"""
Performance Improvement Plan (PIP) Management Module
Track and manage employee performance improvement plans
"""

import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
from database import get_db_connection
from auth import get_current_user, is_hr_admin, is_manager, create_notification, log_audit

def show_pip_management():
    """Main PIP management interface"""
    user = get_current_user()

    st.markdown("## 📈 Performance Improvement Plans")
    st.markdown("Track and manage employee performance improvement plans")
    st.markdown("---")

    if is_hr_admin():
        tabs = st.tabs(["📋 All PIPs", "➕ Create PIP", "📊 Analytics"])
    elif is_manager():
        tabs = st.tabs(["👥 Team PIPs", "➕ Initiate PIP", "📈 Progress"])
    else:
        tabs = st.tabs(["📝 My PIP", "📊 Progress"])

    with tabs[0]:
        if is_hr_admin():
            show_all_pips()
        elif is_manager():
            show_team_pips()
        else:
            show_my_pip()

    with tabs[1]:
        if is_hr_admin() or is_manager():
            show_create_pip()
        else:
            show_pip_progress()

    if len(tabs) > 2:
        with tabs[2]:
            if is_hr_admin():
                show_pip_analytics()
            else:
                show_pip_progress()

def show_my_pip():
    """Show employee's PIP"""
    user = get_current_user()

    st.markdown("### 📝 My Performance Improvement Plan")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT p.*, m.first_name as manager_first, m.last_name as manager_last
            FROM pips p
            LEFT JOIN employees m ON p.manager_id = m.id
            WHERE p.emp_id = %s
            AND p.status IN ('Active', 'In Progress')
            ORDER BY p.created_at DESC
            LIMIT 1
        """, (user['employee_id'],))
        pip = cursor.fetchone()

        if pip:
            pip = dict(pip)

            # Calculate progress
            start_date = datetime.strptime(pip['start_date'], '%Y-%m-%d').date()
            end_date = datetime.strptime(pip['end_date'], '%Y-%m-%d').date()
            today = date.today()

            total_days = (end_date - start_date).days
            days_elapsed = (today - start_date).days
            days_remaining = (end_date - today).days

            progress = (days_elapsed / total_days * 100) if total_days > 0 else 0

            st.markdown(f"""
                <div style="
                    background: linear-gradient(135deg, rgba(240, 180, 41, 0.15), rgba(240, 180, 41, 0.05));
                    padding: 20px;
                    border-radius: 10px;
                    border-left: 4px solid rgba(240, 180, 41, 0.8);
                    margin-bottom: 20px;
                ">
                    <h3 style="margin-top: 0;">Performance Improvement Plan</h3>
                    <p><strong>Status:</strong> {pip['status']}</p>
                    <p><strong>Manager:</strong> {pip.get('manager_first', 'N/A')} {pip.get('manager_last', '')}</p>
                    <p><strong>Duration:</strong> {pip['start_date']} to {pip['end_date']}</p>
                    <p><strong>Days Remaining:</strong> {days_remaining} days</p>
                </div>
            """, unsafe_allow_html=True)

            st.progress(progress / 100)

            # Reason and goals
            st.markdown("### 🎯 Improvement Areas")
            st.warning(f"**Reason for PIP:** {pip['reason']}")

            st.markdown("### 📋 Goals and Objectives")
            st.info(pip['goals'])

            st.markdown("### 📊 Expected Outcomes")
            st.info(pip['expected_outcomes'])

            # Progress notes
            st.markdown("### 📝 Progress Notes")
            if pip.get('progress_notes'):
                st.success(pip['progress_notes'])
            else:
                st.info("No progress notes yet")

            # Check-ins
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM pip_checkins
                    WHERE pip_id = %s
                    ORDER BY checkin_date DESC
                """, (pip['id'],))
                checkins = [dict(row) for row in cursor.fetchall()]

            if checkins:
                st.markdown(f"### ✅ Check-ins ({len(checkins)})")
                for checkin in checkins:
                    st.markdown(f"""
                        <div style="background: rgba(91, 156, 246, 0.1); padding: 12px; border-radius: 8px; margin-bottom: 8px;">
                            <strong>📅 {checkin['checkin_date']}</strong><br>
                            {checkin['notes']}
                        </div>
                    """, unsafe_allow_html=True)

        else:
            st.success("✅ You are not currently on a Performance Improvement Plan")

def show_pip_progress():
    """Show PIP progress details"""
    user = get_current_user()

    st.markdown("### 📊 PIP Progress")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM pips
            WHERE emp_id = %s
            ORDER BY created_at DESC
            LIMIT 1
        """, (user['employee_id'],))
        pip = cursor.fetchone()

    if pip:
        pip = dict(pip)

        # Timeline
        start_date = datetime.strptime(pip['start_date'], '%Y-%m-%d').date()
        end_date = datetime.strptime(pip['end_date'], '%Y-%m-%d').date()
        today = date.today()

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Start Date", pip['start_date'])
        with col2:
            st.metric("End Date", pip['end_date'])
        with col3:
            days_left = (end_date - today).days
            st.metric("Days Remaining", days_left)

        # Status
        st.markdown("### Status")
        st.info(f"Current Status: **{pip['status']}**")

    else:
        st.info("No PIP information available")

def show_team_pips():
    """Show team member PIPs (Manager view)"""
    user = get_current_user()

    st.markdown("### 👥 Team Performance Improvement Plans")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT p.*, e.first_name, e.last_name, e.employee_id
            FROM pips p
            JOIN employees e ON p.emp_id = e.id
            WHERE p.manager_id = %s
            ORDER BY p.status, p.start_date DESC
        """, (user['employee_id'],))
        pips = [dict(row) for row in cursor.fetchall()]

    if pips:
        for pip in pips:
            status_icon = {
                'Active': '⏳',
                'In Progress': '📈',
                'Completed': '✅',
                'Cancelled': '❌'
            }.get(pip['status'], '📋')

            with st.expander(f"{status_icon} {pip['first_name']} {pip['last_name']} - {pip['status']}"):
                st.markdown(f"""
                **Employee:** {pip['first_name']} {pip['last_name']} ({pip['employee_id']})
                **Status:** {pip['status']}
                **Period:** {pip['start_date']} to {pip['end_date']}
                **Reason:** {pip['reason']}
                """)

                # Goals
                st.info(f"**Goals:** {pip['goals']}")

                # Progress
                if pip.get('progress_notes'):
                    st.success(f"**Progress:** {pip['progress_notes']}")

                # Actions
                col1, col2, col3 = st.columns(3)
                with col1:
                    if pip['status'] in ['Active', 'In Progress']:
                        if st.button("📝 Add Check-in", key=f"checkin_{pip['id']}"):
                            show_add_checkin_form(pip['id'])
                with col2:
                    if pip['status'] == 'In Progress':
                        if st.button("✅ Complete", key=f"complete_{pip['id']}"):
                            complete_pip(pip['id'], 'Completed')
                            st.rerun()
                with col3:
                    if pip['status'] in ['Active', 'In Progress']:
                        if st.button("❌ Cancel", key=f"cancel_{pip['id']}"):
                            complete_pip(pip['id'], 'Cancelled')
                            st.rerun()
    else:
        st.info("No team members currently on PIP")

def show_all_pips():
    """Show all PIPs (HR view)"""
    st.markdown("### 📋 All Performance Improvement Plans")

    # Filters
    col1, col2 = st.columns(2)
    with col1:
        status_filter = st.selectbox("Status", ["All", "Active", "In Progress", "Completed", "Cancelled"])
    with col2:
        search = st.text_input("🔍 Search employee")

    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Use correct table name and handle employee_id gracefully
        query = """
            SELECT p.*, e.first_name, e.last_name, e.id as employee_id, e.department,
                   m.first_name as manager_first, m.last_name as manager_last
            FROM pips p
            JOIN employees e ON p.emp_id = e.id
            LEFT JOIN employees m ON p.manager_id = m.id
            WHERE 1=1
        """
        params = []

        if status_filter != "All":
            query += " AND p.status = %s"
            params.append(status_filter)

        if search:
            query += " AND (e.first_name LIKE %s OR e.last_name LIKE %s)"
            params.extend([f"%{search}%", f"%{search}%"])

        query += " ORDER BY p.start_date DESC"

        cursor.execute(query, params)
        pips = [dict(row) for row in cursor.fetchall()]

    if pips:
        st.info(f"📊 {len(pips)} PIP(s) found")

        for pip in pips:
            with st.expander(f"📋 {pip['first_name']} {pip['last_name']} - {pip['status']}"):
                col1, col2 = st.columns([2, 1])

                with col1:
                    st.markdown(f"""
                    **Employee:** {pip['first_name']} {pip['last_name']} ({pip['employee_id']})
                    **Department:** {pip['department']}
                    **Manager:** {pip.get('manager_first', 'N/A')} {pip.get('manager_last', '')}
                    **Period:** {pip['start_date']} to {pip['end_date']}
                    **Status:** {pip['status']}
                    """)

                with col2:
                    # Calculate days
                    start = datetime.strptime(pip['start_date'], '%Y-%m-%d').date()
                    end = datetime.strptime(pip['end_date'], '%Y-%m-%d').date()
                    days_left = (end - date.today()).days
                    st.metric("Days Remaining", days_left if days_left > 0 else "Expired")

                st.markdown("---")
                st.warning(f"**Reason:** {pip['reason']}")
                st.info(f"**Goals:** {pip['goals']}")
                st.info(f"**Expected Outcomes:** {pip['expected_outcomes']}")

                if pip.get('progress_notes'):
                    st.success(f"**Progress:** {pip['progress_notes']}")

                # Actions
                if pip['status'] in ['Active', 'In Progress']:
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("✅ Mark Completed", key=f"comp_{pip['id']}"):
                            complete_pip(pip['id'], 'Completed')
                            st.rerun()
                    with col2:
                        if st.button("❌ Cancel PIP", key=f"canc_{pip['id']}"):
                            complete_pip(pip['id'], 'Cancelled')
                            st.rerun()
    else:
        st.info("No PIPs found")

def show_create_pip():
    """Create new PIP"""
    user = get_current_user()

    st.markdown("### ➕ Create Performance Improvement Plan")

    with st.form("create_pip"):
        # Get employees
        with get_db_connection() as conn:
            cursor = conn.cursor()

            if is_manager():
                # Manager can only create PIPs for their team
                cursor.execute("""
                    SELECT id, employee_id, first_name, last_name
                    FROM employees
                    WHERE manager_id = %s AND status = 'Active'
                """, (user['employee_id'],))
            else:
                # HR can create PIPs for anyone
                cursor.execute("""
                    SELECT id, employee_id, first_name, last_name, department
                    FROM employees
                    WHERE status = 'Active'
                    ORDER BY first_name
                """)

            employees = [dict(row) for row in cursor.fetchall()]

        if employees:
            emp_options = {
                f"{e['first_name']} {e['last_name']} ({e['employee_id']})": e['id']
                for e in employees
            }
            selected_emp = st.selectbox("Select Employee *", list(emp_options.keys()))

            reason = st.text_area(
                "Reason for PIP *",
                placeholder="Describe the performance issues that led to this PIP...",
                height=100
            )

            goals = st.text_area(
                "Goals and Objectives *",
                placeholder="Specific, measurable goals the employee must achieve...",
                height=150
            )

            expected_outcomes = st.text_area(
                "Expected Outcomes *",
                placeholder="What success looks like at the end of this PIP...",
                height=100
            )

            col1, col2 = st.columns(2)
            with col1:
                start_date = st.date_input("Start Date *", value=date.today())
                duration = st.selectbox("Duration *", ["30 days", "60 days", "90 days", "Custom"])

            with col2:
                if duration == "Custom":
                    end_date = st.date_input("End Date *")
                else:
                    days = int(duration.split()[0])
                    end_date = start_date + timedelta(days=days)
                    st.date_input("End Date *", value=end_date, disabled=True)

            submitted = st.form_submit_button("📝 Create PIP", use_container_width=True)

            if submitted:
                if all([selected_emp, reason, goals, expected_outcomes]):
                    emp_id = emp_options[selected_emp]
                    create_pip(emp_id, user['employee_id'], reason, goals,
                             expected_outcomes, start_date, end_date)
                    st.rerun()
                else:
                    st.error("❌ Please fill all required fields")
        else:
            st.warning("No employees available to create PIP for")

def show_add_checkin_form(pip_id):
    """Add check-in form"""
    with st.form(f"add_checkin_{pip_id}"):
        st.markdown("#### Add Check-in")
        checkin_date = st.date_input("Check-in Date", value=date.today())
        notes = st.text_area("Notes *", placeholder="Document progress, concerns, achievements...")

        if st.form_submit_button("✅ Add Check-in"):
            if notes:
                add_pip_checkin(pip_id, checkin_date, notes)
                st.rerun()

def show_pip_analytics():
    """Show PIP analytics"""
    st.markdown("### 📊 PIP Analytics")

    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Total PIPs
        cursor.execute("SELECT COUNT(*) as cnt FROM pips")
        total = cursor.fetchone()['cnt']

        # Active PIPs
        cursor.execute("""
            SELECT COUNT(*) as cnt FROM pips
            WHERE status IN ('Active', 'In Progress')
        """)
        active = cursor.fetchone()['cnt']

        # Completed successfully
        cursor.execute("""
            SELECT COUNT(*) as cnt FROM pips
            WHERE status = 'Completed'
        """)
        completed = cursor.fetchone()['cnt']

        # Success rate
        cursor.execute("""
            SELECT COUNT(*) as cnt FROM pips
            WHERE status IN ('Completed', 'Cancelled')
        """)
        finished = cursor.fetchone()['cnt']
        success_rate = (completed / finished * 100) if finished > 0 else 0

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total PIPs", total)
    with col2:
        st.metric("Active", active)
    with col3:
        st.metric("Completed", completed)
    with col4:
        st.metric("Success Rate", f"{success_rate:.1f}%")

    # Status breakdown
    st.markdown("---")
    st.markdown("### 📊 Status Distribution")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT status, COUNT(*) as count
            FROM pips
            GROUP BY status
            ORDER BY count DESC
        """)
        status_dist = [dict(row) for row in cursor.fetchall()]

    if status_dist:
        df = pd.DataFrame(status_dist)
        df.columns = ['Status', 'Count']
        st.dataframe(df, use_container_width=True, hide_index=True)

def create_pip(emp_id, manager_id, reason, goals, expected_outcomes, start_date, end_date):
    """Create new PIP"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO pips (
                    emp_id, manager_id, reason, goals, expected_outcomes,
                    start_date, end_date, status
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, 'Active')
            """, (emp_id, manager_id, reason, goals, expected_outcomes,
                 start_date.isoformat(), end_date.isoformat()))

            pip_id = cursor.lastrowid

            # Notify employee
            create_notification(emp_id,
                              "A Performance Improvement Plan has been created for you",
                              "pip")

            # Notify HR
            cursor.execute("SELECT id FROM employees WHERE role = 'HR Admin' LIMIT 1")
            hr = cursor.fetchone()
            if hr:
                create_notification(hr['id'], f"New PIP created for employee", "pip")

            conn.commit()
            log_audit(f"Created PIP for employee {emp_id}", "pip", pip_id)
            st.warning(f"⚠️ PIP created! ID: PIP-{pip_id}")

    except Exception as e:
        st.error(f"❌ Error: {str(e)}")

def complete_pip(pip_id, status):
    """Complete or cancel PIP"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                UPDATE pips SET
                    status = %s,
                    end_date = %s
                WHERE id = %s
            """, (status, datetime.now().isoformat(), pip_id))

            # Get employee for notification
            cursor.execute("SELECT emp_id FROM pips WHERE id = %s", (pip_id,))
            pip = cursor.fetchone()

            if pip:
                create_notification(pip['emp_id'],
                                  f"Your PIP has been {status.lower()}",
                                  "pip")

            conn.commit()
            log_audit(f"PIP {pip_id} {status}", "pip", pip_id)
            st.success(f"✅ PIP {status.lower()}!")

    except Exception as e:
        st.error(f"❌ Error: {str(e)}")

def add_pip_checkin(pip_id, checkin_date, notes):
    """Add PIP check-in"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO pip_checkins (
                    pip_id, checkin_date, notes
                ) VALUES (%s, %s, %s)
            """, (pip_id, checkin_date.isoformat(), notes))

            # Update PIP status to In Progress
            cursor.execute("""
                UPDATE pips SET status = 'In Progress'
                WHERE id = %s AND status = 'Active'
            """, (pip_id,))

            conn.commit()
            log_audit(f"Added check-in to PIP {pip_id}", "pip", pip_id)
            st.success("✅ Check-in added!")

    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
