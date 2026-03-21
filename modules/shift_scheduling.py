"""
Shift Scheduling Module
Workforce scheduling and shift management
"""

import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
from database import get_db_connection
from auth import get_current_user, is_hr_admin, is_manager, create_notification, log_audit

def show_shift_scheduling():
    """Main shift scheduling interface"""
    user = get_current_user()

    st.markdown("## 📅 Shift Scheduling")
    st.markdown("Workforce scheduling and shift management")
    st.markdown("---")

    if is_hr_admin():
        tabs = st.tabs(["📋 All Schedules", "➕ Create Schedule", "👥 Shift Assignments", "📊 Analytics"])
    elif is_manager():
        tabs = st.tabs(["📅 Team Schedule", "➕ Assign Shifts", "📊 Coverage"])
    else:
        tabs = st.tabs(["📅 My Schedule", "🔄 Shift Swaps"])

    with tabs[0]:
        if is_hr_admin():
            show_all_schedules()
        elif is_manager():
            show_team_schedule()
        else:
            show_my_schedule()

    with tabs[1]:
        if is_hr_admin():
            show_create_schedule()
        elif is_manager():
            show_assign_shifts()
        else:
            show_shift_swaps()

    if len(tabs) > 2:
        with tabs[2]:
            if is_hr_admin():
                show_shift_assignments()
            else:
                show_coverage_report()

    if len(tabs) > 3:
        with tabs[3]:
            show_shift_analytics()

def show_my_schedule():
    """Show employee's schedule"""
    user = get_current_user()

    st.markdown("### 📅 My Schedule")

    # Date range selector
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("From", value=date.today())
    with col2:
        end_date = st.date_input("To", value=date.today() + timedelta(days=7))

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT ss.*, st.shift_name, st.start_time, st.end_time, st.shift_type
            FROM shift_schedules ss
            JOIN shift_templates st ON ss.shift_id = st.id
            WHERE ss.emp_id = %s
            AND ss.shift_date BETWEEN %s AND %s
            ORDER BY ss.shift_date, st.start_time
        """, (user['employee_id'], start_date.isoformat(), end_date.isoformat()))
        shifts = [dict(row) for row in cursor.fetchall()]

    if shifts:
        # Group by date
        shifts_by_date = {}
        for shift in shifts:
            shift_date = shift['shift_date']
            if shift_date not in shifts_by_date:
                shifts_by_date[shift_date] = []
            shifts_by_date[shift_date].append(shift)

        # Display by date
        for shift_date, day_shifts in sorted(shifts_by_date.items()):
            date_obj = datetime.strptime(shift_date, '%Y-%m-%d').date()
            day_name = date_obj.strftime('%A')

            st.markdown(f"#### 📅 {day_name}, {shift_date}")

            for shift in day_shifts:
                shift_color = {
                    'Morning': 'rgba(240, 180, 41, 0.15)',
                    'Evening': 'rgba(91, 156, 246, 0.15)',
                    'Night': 'rgba(142, 82, 222, 0.15)',
                    'Full Day': 'rgba(46, 213, 115, 0.15)'
                }.get(shift['shift_type'], 'rgba(125, 150, 190, 0.1)')

                st.markdown(f"""
                    <div style="
                        background: {shift_color};
                        padding: 12px;
                        border-radius: 8px;
                        margin-bottom: 8px;
                        border-left: 4px solid rgba(91, 156, 246, 0.8);
                    ">
                        <strong>{shift['shift_name']}</strong> - {shift['shift_type']}<br>
                        <small>⏰ {shift['start_time']} - {shift['end_time']}</small><br>
                        <small>📍 {shift.get('location', 'Office')}</small>
                    </div>
                """, unsafe_allow_html=True)

            st.markdown("---")
    else:
        st.info("No shifts scheduled for this period")

def show_shift_swaps():
    """Show shift swap requests"""
    user = get_current_user()

    st.markdown("### 🔄 Shift Swap Requests")

    with st.form("request_swap"):
        st.markdown("#### Request a Shift Swap")

        # Get my upcoming shifts
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT ss.id, ss.shift_date, st.shift_name, st.start_time, st.end_time
                FROM shift_schedules ss
                JOIN shift_templates st ON ss.shift_id = st.id
                WHERE ss.emp_id = %s AND ss.shift_date >= CURRENT_DATE
                ORDER BY ss.shift_date
                LIMIT 30
            """, (user['employee_id'],))
            my_shifts = [dict(row) for row in cursor.fetchall()]

        if my_shifts:
            shift_options = {
                f"{s['shift_date']} - {s['shift_name']} ({s['start_time']}-{s['end_time']})": s['id']
                for s in my_shifts
            }
            selected_shift = st.selectbox("Select Shift to Swap", list(shift_options.keys()))

            # Get potential swap partners (same department)
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, employee_id, first_name, last_name
                    FROM employees
                    WHERE department = (SELECT department FROM employees WHERE id = %s)
                    AND id != %s AND status = 'Active'
                """, (user['employee_id'], user['employee_id']))
                colleagues = [dict(row) for row in cursor.fetchall()]

            if colleagues:
                colleague_options = {
                    f"{c['first_name']} {c['last_name']} ({c['employee_id']})": c['id']
                    for c in colleagues
                }
                selected_colleague = st.selectbox("Swap With", list(colleague_options.keys()))

                reason = st.text_area("Reason for Swap", placeholder="Please provide a reason...")

                submitted = st.form_submit_button("📤 Request Swap")

                if submitted and reason:
                    shift_id = shift_options[selected_shift]
                    colleague_id = colleague_options[selected_colleague]
                    request_shift_swap(user['employee_id'], shift_id, colleague_id, reason)
                    st.rerun()
            else:
                st.warning("No colleagues available for swap")
        else:
            st.info("No upcoming shifts to swap")

def show_team_schedule():
    """Show team schedule for manager"""
    user = get_current_user()

    st.markdown("### 📅 Team Schedule")

    # Week selector
    week_start = st.date_input("Week Starting", value=date.today())

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT e.first_name, e.last_name, e.employee_id,
                   ss.shift_date, st.shift_name, st.start_time, st.end_time, st.shift_type
            FROM employees e
            LEFT JOIN shift_schedules ss ON e.id = ss.emp_id
            LEFT JOIN shift_templates st ON ss.shift_id = st.id
            WHERE e.manager_id = %s
            AND ss.shift_date BETWEEN %s AND %s
            ORDER BY ss.shift_date, e.first_name
        """, (user['employee_id'],
              week_start.isoformat(),
              (week_start + timedelta(days=6)).isoformat()))
        team_shifts = [dict(row) for row in cursor.fetchall()]

    if team_shifts:
        # Create a table view
        df_data = []
        for shift in team_shifts:
            df_data.append({
                'Employee': f"{shift['first_name']} {shift['last_name']}",
                'ID': shift['employee_id'],
                'Date': shift['shift_date'],
                'Shift': shift['shift_name'],
                'Type': shift['shift_type'],
                'Time': f"{shift['start_time']}-{shift['end_time']}"
            })

        df = pd.DataFrame(df_data)
        st.dataframe(df, use_container_width=True, hide_index=True)

        # Export option
        if st.button("📥 Export Schedule"):
            st.success("Schedule exported (simulated)")
    else:
        st.info("No shifts scheduled for team this week")

def show_assign_shifts():
    """Manager assigns shifts to team"""
    user = get_current_user()

    st.markdown("### ➕ Assign Shifts to Team")

    with st.form("assign_shift"):
        # Get team members
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, employee_id, first_name, last_name
                FROM employees
                WHERE manager_id = %s AND status = 'Active'
            """, (user['employee_id'],))
            team = [dict(row) for row in cursor.fetchall()]

        if team:
            emp_options = {
                f"{e['first_name']} {e['last_name']} ({e['employee_id']})": e['id']
                for e in team
            }
            selected_emp = st.selectbox("Select Employee *", list(emp_options.keys()))

            # Get shift templates
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM shift_templates WHERE status = 'Active'")
                shift_templates = [dict(row) for row in cursor.fetchall()]

            if shift_templates:
                shift_options = {
                    f"{s['shift_name']} ({s['start_time']}-{s['end_time']}) - {s['shift_type']}": s['id']
                    for s in shift_templates
                }
                selected_shift = st.selectbox("Select Shift *", list(shift_options.keys()))

                col1, col2 = st.columns(2)
                with col1:
                    shift_date = st.date_input("Shift Date *", value=date.today())
                with col2:
                    location = st.text_input("Location", value="Office")

                notes = st.text_area("Notes", placeholder="Any special instructions...")

                submitted = st.form_submit_button("📅 Assign Shift", use_container_width=True)

                if submitted:
                    emp_id = emp_options[selected_emp]
                    shift_id = shift_options[selected_shift]
                    assign_shift(emp_id, shift_id, shift_date, location, notes)
                    st.rerun()
            else:
                st.warning("No shift templates available. Contact HR to create shift templates.")
        else:
            st.info("No team members found")

def show_coverage_report():
    """Show shift coverage report"""
    st.markdown("### 📊 Shift Coverage")

    week_start = st.date_input("Week Starting", value=date.today())

    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Get shifts per day
        cursor.execute("""
            SELECT shift_date, COUNT(*) as shift_count
            FROM shift_schedules
            WHERE shift_date BETWEEN %s AND %s
            GROUP BY shift_date
            ORDER BY shift_date
        """, (week_start.isoformat(), (week_start + timedelta(days=6)).isoformat()))
        coverage = [dict(row) for row in cursor.fetchall()]

    if coverage:
        for day in coverage:
            date_obj = datetime.strptime(day['shift_date'], '%Y-%m-%d')
            day_name = date_obj.strftime('%A')
            st.markdown(f"**{day_name}, {day['shift_date']}**: {day['shift_count']} shifts")
    else:
        st.info("No coverage data for selected week")

def show_all_schedules():
    """Show all schedules (HR view)"""
    st.markdown("### 📋 All Shift Schedules")

    # Filters
    col1, col2, col3 = st.columns(3)
    with col1:
        dept_filter = st.selectbox("Department", ["All", "Engineering", "Sales", "Operations", "Support"])
    with col2:
        date_filter = st.date_input("Date", value=date.today())
    with col3:
        shift_type_filter = st.selectbox("Shift Type", ["All", "Morning", "Evening", "Night", "Full Day"])

    with get_db_connection() as conn:
        cursor = conn.cursor()

        query = """
            SELECT ss.*, e.first_name, e.last_name, e.employee_id, e.department,
                   st.shift_name, st.start_time, st.end_time, st.shift_type
            FROM shift_schedules ss
            JOIN employees e ON ss.emp_id = e.id
            JOIN shift_templates st ON ss.shift_id = st.id
            WHERE ss.shift_date = %s
        """
        params = [date_filter.isoformat()]

        if dept_filter != "All":
            query += " AND e.department = %s"
            params.append(dept_filter)

        if shift_type_filter != "All":
            query += " AND st.shift_type = %s"
            params.append(shift_type_filter)

        query += " ORDER BY st.start_time, e.first_name"

        cursor.execute(query, params)
        schedules = [dict(row) for row in cursor.fetchall()]

    if schedules:
        st.info(f"📊 {len(schedules)} shift(s) scheduled for {date_filter}")

        for schedule in schedules:
            with st.expander(f"👤 {schedule['first_name']} {schedule['last_name']} - {schedule['shift_name']}"):
                st.markdown(f"""
                **Employee:** {schedule['first_name']} {schedule['last_name']} ({schedule['employee_id']})
                **Department:** {schedule['department']}
                **Shift:** {schedule['shift_name']} - {schedule['shift_type']}
                **Time:** {schedule['start_time']} - {schedule['end_time']}
                **Location:** {schedule.get('location', 'Office')}
                """)

                if schedule.get('notes'):
                    st.info(f"📝 Notes: {schedule['notes']}")

                # Actions
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("✏️ Edit", key=f"edit_{schedule['id']}"):
                        st.info("Edit functionality")
                with col2:
                    if st.button("🗑️ Remove", key=f"del_{schedule['id']}"):
                        remove_shift_assignment(schedule['id'])
                        st.rerun()
    else:
        st.info("No shifts scheduled for selected date")

def show_create_schedule():
    """Create shift schedule (HR)"""
    st.markdown("### ➕ Create Shift Schedule")

    # Option 1: Single assignment
    with st.expander("📅 Single Shift Assignment", expanded=True):
        with st.form("single_assignment"):
            # Get employees
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, employee_id, first_name, last_name, department
                    FROM employees WHERE status = 'Active'
                    ORDER BY first_name
                """)
                employees = [dict(row) for row in cursor.fetchall()]

            if employees:
                emp_options = {
                    f"{e['first_name']} {e['last_name']} ({e['employee_id']}) - {e['department']}": e['id']
                    for e in employees
                }
                selected_emp = st.selectbox("Employee *", list(emp_options.keys()))

                # Get shift templates
                with get_db_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT * FROM shift_templates WHERE status = 'Active'")
                    shifts = [dict(row) for row in cursor.fetchall()]

                if shifts:
                    shift_options = {
                        f"{s['shift_name']} ({s['start_time']}-{s['end_time']}) - {s['shift_type']}": s['id']
                        for s in shifts
                    }
                    selected_shift = st.selectbox("Shift *", list(shift_options.keys()))

                    col1, col2 = st.columns(2)
                    with col1:
                        shift_date = st.date_input("Date *")
                    with col2:
                        location = st.text_input("Location", value="Office")

                    notes = st.text_area("Notes")

                    if st.form_submit_button("📅 Assign Shift"):
                        emp_id = emp_options[selected_emp]
                        shift_id = shift_options[selected_shift]
                        assign_shift(emp_id, shift_id, shift_date, location, notes)
                        st.rerun()

    # Option 2: Bulk assignment
    with st.expander("📋 Bulk Shift Assignment"):
        st.info("Bulk assignment: Upload CSV with columns: employee_id, shift_id, date, location")
        uploaded_file = st.file_uploader("Upload CSV", type=['csv'])
        if uploaded_file and st.button("📤 Process Bulk Upload"):
            st.success("Bulk upload processed (simulated)")

def show_shift_assignments():
    """Show shift assignments overview"""
    st.markdown("### 👥 Shift Assignments Overview")

    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Upcoming shifts count
        cursor.execute("""
            SELECT COUNT(*) as cnt FROM shift_schedules
            WHERE shift_date >= CURRENT_DATE
        """)
        upcoming = cursor.fetchone()['cnt']

        # Today's shifts
        cursor.execute("""
            SELECT COUNT(*) as cnt FROM shift_schedules
            WHERE shift_date = CURRENT_DATE
        """)
        today = cursor.fetchone()['cnt']

        # Unassigned shifts (if tracking)
        cursor.execute("""
            SELECT COUNT(*) as cnt FROM shift_templates
            WHERE status = 'Active'
        """)
        templates = cursor.fetchone()['cnt']

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Upcoming Shifts", upcoming)
    with col2:
        st.metric("Today's Shifts", today)
    with col3:
        st.metric("Shift Templates", templates)

    st.markdown("---")
    st.markdown("### 📊 Shift Distribution")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT st.shift_type, COUNT(*) as count
            FROM shift_schedules ss
            JOIN shift_templates st ON ss.shift_id = st.id
            WHERE ss.shift_date >= CURRENT_DATE
            GROUP BY st.shift_type
        """)
        distribution = [dict(row) for row in cursor.fetchall()]

    if distribution:
        for item in distribution:
            st.markdown(f"**{item['shift_type']}**: {item['count']} shifts")

def show_shift_analytics():
    """Show shift analytics"""
    st.markdown("### 📊 Shift Analytics")

    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Total shifts
        cursor.execute("SELECT COUNT(*) as cnt FROM shift_schedules")
        total = cursor.fetchone()['cnt']

        # This month
        cursor.execute("""
            SELECT COUNT(*) as cnt FROM shift_schedules
            WHERE shift_date >= DATE_TRUNC('month', NOW())::DATE
        """)
        this_month = cursor.fetchone()['cnt']

        # Most common shift
        cursor.execute("""
            SELECT st.shift_name, COUNT(*) as count
            FROM shift_schedules ss
            JOIN shift_templates st ON ss.shift_id = st.id
            GROUP BY st.shift_name
            ORDER BY count DESC
            LIMIT 1
        """)
        popular = cursor.fetchone()
        popular_shift = dict(popular) if popular else {'shift_name': 'N/A', 'count': 0}

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Shifts", total)
    with col2:
        st.metric("This Month", this_month)
    with col3:
        st.metric("Most Common", f"{popular_shift['shift_name']} ({popular_shift['count']})")

def assign_shift(emp_id, shift_id, shift_date, location, notes):
    """Assign shift to employee"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO shift_schedules (
                    emp_id, shift_id, shift_date, location, notes, status
                ) VALUES (%s, ?, ?, ?, ?, 'Assigned')
            """, (emp_id, shift_id, shift_date.isoformat(), location, notes))

            schedule_id = cursor.lastrowid

            # Notify employee
            create_notification(emp_id, f"New shift assigned for {shift_date}", "shift")

            conn.commit()
            log_audit(f"Assigned shift {shift_id} to employee {emp_id}", "shift_schedules", schedule_id)
            st.success(f"✅ Shift assigned! ID: SHIFT-{schedule_id}")

    except Exception as e:
        st.error(f"❌ Error: {str(e)}")

def remove_shift_assignment(schedule_id):
    """Remove shift assignment"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM shift_schedules WHERE id = %s", (schedule_id,))
            conn.commit()
            log_audit(f"Removed shift assignment {schedule_id}", "shift_schedules", schedule_id)
            st.success("✅ Shift assignment removed!")

    except Exception as e:
        st.error(f"❌ Error: {str(e)}")

def request_shift_swap(emp_id, shift_id, swap_with_id, reason):
    """Request shift swap"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # Create swap request (using a generic approach since table might not exist)
            # In production, you'd have a shift_swaps table

            # Notify the colleague
            create_notification(swap_with_id, f"Shift swap request from employee", "shift")

            # Notify manager
            cursor.execute("SELECT manager_id FROM employees WHERE id = %s", (emp_id,))
            manager = cursor.fetchone()
            if manager and manager['manager_id']:
                create_notification(manager['manager_id'], f"Shift swap request pending approval", "shift")

            conn.commit()
            log_audit(f"Shift swap requested by {emp_id}", "shift_schedules", shift_id)
            st.success("✅ Shift swap request submitted!")

    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
