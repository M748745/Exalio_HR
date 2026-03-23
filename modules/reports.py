"""
Advanced Reports & Analytics Module
Comprehensive reporting and data analytics for HR
"""

import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
from database import get_db_connection
from auth import get_current_user, is_hr_admin, is_manager

def show_reports_analytics():
    """Main reports and analytics interface"""
    user = get_current_user()

    st.markdown("## 📊 Reports & Analytics")
    st.markdown("Comprehensive HR data insights and reporting")
    st.markdown("---")

    if is_hr_admin():
        tabs = st.tabs([
            "📈 Overview", "👥 Workforce", "💰 Compensation",
            "📅 Leave & Attendance", "🎯 Performance", "📉 Turnover"
        ])

        with tabs[0]:
            show_overview_report()
        with tabs[1]:
            show_workforce_analytics()
        with tabs[2]:
            show_compensation_report()
        with tabs[3]:
            show_leave_attendance_report()
        with tabs[4]:
            show_performance_report()
        with tabs[5]:
            show_turnover_report()

    elif is_manager():
        tabs = st.tabs(["📊 Team Overview", "📈 Team Performance", "📅 Team Attendance"])

        with tabs[0]:
            show_team_overview()
        with tabs[1]:
            show_team_performance()
        with tabs[2]:
            show_team_attendance()
    else:
        st.info("Reports are available for HR Admin and Managers only")

def show_overview_report():
    """Show comprehensive overview report"""
    st.markdown("### 📈 HR Overview Dashboard")

    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Key metrics
        cursor.execute("SELECT COUNT(*) as cnt FROM employees WHERE status = 'Active'")
        total_employees = cursor.fetchone()['cnt']

        cursor.execute("SELECT COUNT(*) as cnt FROM employees WHERE hire_date >= CURRENT_DATE - INTERVAL '30 days'")
        new_hires = cursor.fetchone()['cnt']

        cursor.execute("SELECT COUNT(*) as cnt FROM exit_process WHERE status = 'In Progress'")
        pending_exits = cursor.fetchone()['cnt']

        cursor.execute("SELECT COUNT(*) as cnt FROM leave_requests WHERE status = 'Pending'")
        pending_leaves = cursor.fetchone()['cnt']

    # Display key metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Employees", total_employees, delta=f"+{new_hires} this month")

    with col2:
        st.metric("New Hires (30d)", new_hires)

    with col3:
        st.metric("Pending Exits", pending_exits)

    with col4:
        st.metric("Pending Leaves", pending_leaves)

    st.markdown("---")

    # Department breakdown
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 🏢 Employees by Department")
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT department, COUNT(*) as count
                FROM employees
                WHERE status = 'Active'
                GROUP BY department
                ORDER BY count DESC
            """)
            dept_data = [dict(row) for row in cursor.fetchall()]

        if dept_data:
            df = pd.DataFrame(dept_data)
            st.dataframe(df, use_container_width=True, hide_index=True)

    with col2:
        st.markdown("#### 📊 Recent Activity")
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT action, timestamp
                FROM audit_logs
                ORDER BY timestamp DESC
                LIMIT 10
            """)
            recent_activity = [dict(row) for row in cursor.fetchall()]

        if recent_activity:
            for activity in recent_activity:
                timestamp_str = str(activity['timestamp'])[:16] if activity.get('timestamp') else 'N/A'
                st.markdown(f"- {activity['action']} _{timestamp_str}_")

def show_workforce_analytics():
    """Show detailed workforce analytics"""
    st.markdown("### 👥 Workforce Analytics")

    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Total workforce
        cursor.execute("SELECT COUNT(*) as cnt FROM employees")
        total = cursor.fetchone()['cnt']

        cursor.execute("SELECT COUNT(*) as cnt FROM employees WHERE status = 'Active'")
        active = cursor.fetchone()['cnt']

        cursor.execute("SELECT COUNT(*) as cnt FROM employees WHERE status = 'Inactive'")
        inactive = cursor.fetchone()['cnt']

        cursor.execute("SELECT COUNT(*) as cnt FROM employees WHERE status = 'On Leave'")
        on_leave = cursor.fetchone()['cnt']

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total", total)
    with col2:
        st.metric("Active", active)
    with col3:
        st.metric("Inactive", inactive)
    with col4:
        st.metric("On Leave", on_leave)

    st.markdown("---")

    # Department analysis
    st.markdown("### 📊 Department Analysis")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT
                department,
                COUNT(*) as total,
                COUNT(CASE WHEN status = 'Active' THEN 1 END) as active,
                AVG(CAST(substr(salary, 2) as REAL)) as avg_salary
            FROM employees
            WHERE department IS NOT NULL
            GROUP BY department
            ORDER BY total DESC
        """)
        dept_analysis = [dict(row) for row in cursor.fetchall()]

    if dept_analysis:
        df = pd.DataFrame(dept_analysis)
        df['avg_salary'] = df['avg_salary'].apply(lambda x: f"${x:,.0f}" if pd.notna(x) else "N/A")
        df.columns = ['Department', 'Total', 'Active', 'Avg Salary']
        st.dataframe(df, use_container_width=True, hide_index=True)

    st.markdown("---")

    # Tenure analysis
    st.markdown("### 📅 Employee Tenure Distribution")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT
                CASE
                    WHEN EXTRACT(EPOCH FROM (CURRENT_DATE - hire_date)) / 86400 < 365 THEN '< 1 year'
                    WHEN EXTRACT(EPOCH FROM (CURRENT_DATE - hire_date)) / 86400 < 730 THEN '1-2 years'
                    WHEN EXTRACT(EPOCH FROM (CURRENT_DATE - hire_date)) / 86400 < 1095 THEN '2-3 years'
                    WHEN EXTRACT(EPOCH FROM (CURRENT_DATE - hire_date)) / 86400 < 1825 THEN '3-5 years'
                    ELSE '5+ years'
                END as tenure_group,
                COUNT(*) as count
            FROM employees
            WHERE status = 'Active' AND hire_date IS NOT NULL
            GROUP BY tenure_group
        """)
        tenure_data = [dict(row) for row in cursor.fetchall()]

    if tenure_data:
        df = pd.DataFrame(tenure_data)
        df.columns = ['Tenure', 'Employees']
        st.dataframe(df, use_container_width=True, hide_index=True)

def show_compensation_report():
    """Show compensation and salary analytics"""
    st.markdown("### 💰 Compensation Analytics")

    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Salary statistics
        cursor.execute("""
            SELECT
                AVG(CAST(substr(salary, 2) as REAL)) as avg_salary,
                MIN(CAST(substr(salary, 2) as REAL)) as min_salary,
                MAX(CAST(substr(salary, 2) as REAL)) as max_salary
            FROM employees
            WHERE status = 'Active' AND salary IS NOT NULL
        """)
        salary_stats = dict(cursor.fetchone())

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Average Salary", f"${salary_stats['avg_salary']:,.0f}" if salary_stats['avg_salary'] else "N/A")
    with col2:
        st.metric("Min Salary", f"${salary_stats['min_salary']:,.0f}" if salary_stats['min_salary'] else "N/A")
    with col3:
        st.metric("Max Salary", f"${salary_stats['max_salary']:,.0f}" if salary_stats['max_salary'] else "N/A")

    st.markdown("---")

    # Salary by department
    st.markdown("### 💵 Salary by Department")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT
                department,
                COUNT(*) as employees,
                AVG(CAST(substr(salary, 2) as REAL)) as avg_salary,
                MIN(CAST(substr(salary, 2) as REAL)) as min_salary,
                MAX(CAST(substr(salary, 2) as REAL)) as max_salary
            FROM employees
            WHERE status = 'Active' AND salary IS NOT NULL AND department IS NOT NULL
            GROUP BY department
            ORDER BY avg_salary DESC
        """)
        dept_salary = [dict(row) for row in cursor.fetchall()]

    if dept_salary:
        df = pd.DataFrame(dept_salary)
        df['avg_salary'] = df['avg_salary'].apply(lambda x: f"${x:,.0f}")
        df['min_salary'] = df['min_salary'].apply(lambda x: f"${x:,.0f}")
        df['max_salary'] = df['max_salary'].apply(lambda x: f"${x:,.0f}")
        df.columns = ['Department', 'Employees', 'Avg Salary', 'Min Salary', 'Max Salary']
        st.dataframe(df, use_container_width=True, hide_index=True)

    st.markdown("---")

    # Bonus summary
    st.markdown("### 🎁 Bonus Summary")

    with get_db_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT COUNT(*) as cnt, SUM(CAST(substr(bonus_amount, 2) as REAL)) as total
            FROM bonus_calculations
            WHERE status = 'Approved'
        """)
        bonus_stats = dict(cursor.fetchone())

        cursor.execute("""
            SELECT COUNT(*) as cnt FROM bonus_calculations WHERE status = 'Pending'
        """)
        pending_bonus = cursor.fetchone()['cnt']

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Approved Bonuses", bonus_stats['cnt'] or 0)
    with col2:
        st.metric("Total Amount", f"${bonus_stats['total']:,.0f}" if bonus_stats['total'] else "$0")
    with col3:
        st.metric("Pending Approval", pending_bonus)

def show_leave_attendance_report():
    """Show leave and attendance analytics"""
    st.markdown("### 📅 Leave & Attendance Analytics")

    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Leave statistics
        cursor.execute("""
            SELECT
                COUNT(*) as total_requests,
                COUNT(CASE WHEN status = 'Approved' THEN 1 END) as approved,
                COUNT(CASE WHEN status = 'Rejected' THEN 1 END) as rejected,
                COUNT(CASE WHEN status = 'Pending' THEN 1 END) as pending
            FROM leave_requests
        """)
        leave_stats = dict(cursor.fetchone())

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Requests", leave_stats['total_requests'])
    with col2:
        st.metric("Approved", leave_stats['approved'])
    with col3:
        st.metric("Rejected", leave_stats['rejected'])
    with col4:
        st.metric("Pending", leave_stats['pending'])

    st.markdown("---")

    # Leave by type
    st.markdown("### 📊 Leave Requests by Type")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT
                leave_type,
                COUNT(*) as count,
                SUM(days_requested) as total_days
            FROM leave_requests
            WHERE status = 'Approved'
            GROUP BY leave_type
            ORDER BY count DESC
        """)
        leave_by_type = [dict(row) for row in cursor.fetchall()]

    if leave_by_type:
        df = pd.DataFrame(leave_by_type)
        df.columns = ['Leave Type', 'Requests', 'Total Days']
        st.dataframe(df, use_container_width=True, hide_index=True)

    st.markdown("---")

    # Timesheet summary
    st.markdown("### ⏰ Timesheet Summary")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT
                COUNT(*) as total_entries,
                SUM(hours_worked) as total_hours,
                AVG(hours_worked) as avg_hours
            FROM timesheets
            WHERE status = 'Approved'
        """)
        timesheet_stats = dict(cursor.fetchone())

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Total Entries", timesheet_stats['total_entries'] or 0)
    with col2:
        st.metric("Total Hours", f"{timesheet_stats['total_hours']:,.1f}" if timesheet_stats['total_hours'] else "0")
    with col3:
        st.metric("Avg Hours/Entry", f"{timesheet_stats['avg_hours']:.1f}" if timesheet_stats['avg_hours'] else "0")

def show_performance_report():
    """Show performance analytics"""
    st.markdown("### 🎯 Performance Analytics")

    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Grade distribution
        cursor.execute("""
            SELECT
                grade,
                COUNT(*) as count
            FROM performance_grades
            WHERE year = strftime('%Y', 'now')
            GROUP BY grade
            ORDER BY
                CASE grade
                    WHEN 'A+' THEN 1
                    WHEN 'A' THEN 2
                    WHEN 'B+' THEN 3
                    WHEN 'B' THEN 4
                    WHEN 'C' THEN 5
                    WHEN 'D' THEN 6
                END
        """)
        grade_dist = [dict(row) for row in cursor.fetchall()]

    if grade_dist:
        st.markdown("#### 📊 Current Year Grade Distribution")
        df = pd.DataFrame(grade_dist)
        df.columns = ['Grade', 'Employees']

        col1, col2 = st.columns([2, 1])

        with col1:
            st.dataframe(df, use_container_width=True, hide_index=True)

        with col2:
            total = sum(item['count'] for item in grade_dist)
            for item in grade_dist:
                percentage = (item['count'] / total * 100) if total > 0 else 0
                st.markdown(f"**{item['grade']}**: {percentage:.1f}%")

    st.markdown("---")

    # Appraisal completion
    st.markdown("### 📋 Appraisal Status")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT
                status,
                COUNT(*) as count
            FROM appraisals
            WHERE year = strftime('%Y', 'now')
            GROUP BY status
        """)
        appraisal_status = [dict(row) for row in cursor.fetchall()]

    if appraisal_status:
        df = pd.DataFrame(appraisal_status)
        df.columns = ['Status', 'Count']
        st.dataframe(df, use_container_width=True, hide_index=True)

    st.markdown("---")

    # Goals completion
    st.markdown("### 🎯 Goals Completion Rate")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT
                COUNT(*) as total,
                COUNT(CASE WHEN status = 'Completed' THEN 1 END) as completed,
                AVG(progress_percentage) as avg_progress
            FROM goals
        """)
        goals_stats = dict(cursor.fetchone())

    if goals_stats['total']:
        completion_rate = (goals_stats['completed'] / goals_stats['total'] * 100) if goals_stats['total'] > 0 else 0

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Total Goals", goals_stats['total'])
        with col2:
            st.metric("Completed", goals_stats['completed'])
        with col3:
            st.metric("Completion Rate", f"{completion_rate:.1f}%")

        st.progress(completion_rate / 100)

def show_turnover_report():
    """Show employee turnover analytics"""
    st.markdown("### 📉 Turnover Analytics")

    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Exit statistics
        cursor.execute("""
            SELECT COUNT(*) as cnt FROM exit_process
        """)
        total_exits = cursor.fetchone()['cnt']

        cursor.execute("""
            SELECT COUNT(*) as cnt FROM exit_process
            WHERE created_at >= NOW() - INTERVAL '365 days'
        """)
        exits_this_year = cursor.fetchone()['cnt']

        cursor.execute("""
            SELECT COUNT(*) as cnt FROM exit_process
            WHERE status = 'In Progress'
        """)
        pending_exits = cursor.fetchone()['cnt']

        # Calculate turnover rate
        cursor.execute("SELECT COUNT(*) as cnt FROM employees WHERE status = 'Active'")
        active_employees = cursor.fetchone()['cnt']

        turnover_rate = (exits_this_year / active_employees * 100) if active_employees > 0 else 0

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Exits", total_exits)
    with col2:
        st.metric("This Year", exits_this_year)
    with col3:
        st.metric("Pending", pending_exits)
    with col4:
        st.metric("Turnover Rate", f"{turnover_rate:.1f}%")

    st.markdown("---")

    # Exit reasons
    st.markdown("### 📊 Exit Reasons")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT
                reason_for_leaving,
                COUNT(*) as count
            FROM exit_process
            GROUP BY reason_for_leaving
            ORDER BY count DESC
        """)
        exit_reasons = [dict(row) for row in cursor.fetchall()]

    if exit_reasons:
        df = pd.DataFrame(exit_reasons)
        df.columns = ['Reason', 'Count']
        st.dataframe(df, use_container_width=True, hide_index=True)

    st.markdown("---")

    # Exits by department
    st.markdown("### 🏢 Exits by Department")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT
                e.department,
                COUNT(*) as exit_count
            FROM exit_process ep
            JOIN employees e ON ep.emp_id = e.id
            GROUP BY e.department
            ORDER BY exit_count DESC
        """)
        dept_exits = [dict(row) for row in cursor.fetchall()]

    if dept_exits:
        df = pd.DataFrame(dept_exits)
        df.columns = ['Department', 'Exits']
        st.dataframe(df, use_container_width=True, hide_index=True)

def show_team_overview():
    """Show team overview for managers"""
    user = get_current_user()

    st.markdown("### 📊 Team Overview")

    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Get team members
        cursor.execute("""
            SELECT * FROM employees
            WHERE manager_id = %s AND status = 'Active'
        """, (user['employee_id'],))
        team = [dict(row) for row in cursor.fetchall()]

    if team:
        st.metric("Team Size", len(team))

        # Team composition
        st.markdown("#### 👥 Team Composition")

        df = pd.DataFrame(team)
        display_df = df[['employee_id', 'first_name', 'last_name', 'position', 'department']]
        display_df.columns = ['ID', 'First Name', 'Last Name', 'Position', 'Department']
        st.dataframe(display_df, use_container_width=True, hide_index=True)

    else:
        st.info("No team members found")

def show_team_performance():
    """Show team performance for managers"""
    user = get_current_user()

    st.markdown("### 📈 Team Performance")

    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Get team performance grades
        cursor.execute("""
            SELECT e.first_name, e.last_name, pg.grade, pg.year
            FROM performance_grades pg
            JOIN employees e ON pg.emp_id = e.id
            WHERE e.manager_id = %s
            ORDER BY pg.year DESC, pg.grade
        """, (user['employee_id'],))
        team_performance = [dict(row) for row in cursor.fetchall()]

    if team_performance:
        df = pd.DataFrame(team_performance)
        df.columns = ['First Name', 'Last Name', 'Grade', 'Year']
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No performance data available")

def show_team_attendance():
    """Show team attendance for managers"""
    user = get_current_user()

    st.markdown("### 📅 Team Attendance")

    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Get team leave requests
        cursor.execute("""
            SELECT e.first_name, e.last_name, lr.leave_type, lr.start_date,
                   lr.end_date, lr.days_requested, lr.status
            FROM leave_requests lr
            JOIN employees e ON lr.emp_id = e.id
            WHERE e.manager_id = %s
            ORDER BY lr.start_date DESC
            LIMIT 20
        """, (user['employee_id'],))
        team_leaves = [dict(row) for row in cursor.fetchall()]

    if team_leaves:
        df = pd.DataFrame(team_leaves)
        df.columns = ['First Name', 'Last Name', 'Type', 'Start', 'End', 'Days', 'Status']
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No leave records found")
