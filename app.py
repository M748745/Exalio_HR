"""
Exalio HR System - Main Streamlit Application
Complete HR Management System with Role-Based Access Control
"""

import streamlit as st
from datetime import datetime, date
import pandas as pd
from database import init_database, seed_initial_data, get_db_connection
from auth import (
    login, logout, init_session, get_current_user, get_user_role,
    is_hr_admin, is_manager, is_employee, get_accessible_employees,
    get_pending_approvals, get_unread_count, get_user_notifications
)

# Import new feature modules
from modules.profile_manager import show_profile_manager, show_approval_interface
from modules.team_position_admin import show_team_position_admin
from modules.skill_matrix_admin import show_skill_matrix_admin

# Page configuration
st.set_page_config(
    page_title="Exalio HR Portal",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS styling
st.markdown("""
<style>
    /* Main theme colors */
    :root {
        --primary-color: #3a7bd5;
        --gold-color: #c9963a;
        --success-color: #2dd4aa;
        --danger-color: #f16464;
        --warning-color: #f0b429;
    }

    /* Header styling */
    .main-header {
        background: linear-gradient(135deg, #0a1628, #091e3a);
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 20px;
        border: 1px solid #22304a;
    }

    .main-header h1 {
        color: #c9963a;
        margin: 0;
        font-size: 32px;
    }

    .main-header p {
        color: #7d96be;
        margin: 5px 0 0 0;
    }

    /* Stats cards */
    .stat-card {
        background: linear-gradient(135deg, #0e1117, #1c2535);
        padding: 20px;
        border-radius: 12px;
        border: 1px solid #22304a;
        text-align: center;
        transition: transform 0.2s;
    }

    .stat-card:hover {
        transform: translateY(-3px);
        border-color: #3a7bd5;
    }

    .stat-value {
        font-size: 36px;
        font-weight: bold;
        color: #c9963a;
        margin: 10px 0;
    }

    .stat-label {
        font-size: 14px;
        color: #7d96be;
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    /* Badge styling */
    .badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: bold;
        text-transform: uppercase;
    }

    .badge-success {
        background: rgba(45, 212, 170, 0.1);
        color: #2dd4aa;
        border: 1px solid rgba(45, 212, 170, 0.3);
    }

    .badge-warning {
        background: rgba(240, 180, 41, 0.1);
        color: #f0b429;
        border: 1px solid rgba(240, 180, 41, 0.3);
    }

    .badge-danger {
        background: rgba(241, 100, 100, 0.1);
        color: #f16464;
        border: 1px solid rgba(241, 100, 100, 0.3);
    }

    .badge-info {
        background: rgba(58, 123, 213, 0.1);
        color: #5b9cf6;
        border: 1px solid rgba(58, 123, 213, 0.3);
    }

    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0e1117, #0a1428);
    }

    /* Button styling */
    .stButton>button {
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.2s;
    }

    /* Success message styling */
    .success-message {
        background: rgba(45, 212, 170, 0.1);
        border: 1px solid rgba(45, 212, 170, 0.3);
        color: #2dd4aa;
        padding: 12px;
        border-radius: 8px;
        margin: 10px 0;
    }

    /* Error message styling */
    .error-message {
        background: rgba(241, 100, 100, 0.1);
        border: 1px solid rgba(241, 100, 100, 0.3);
        color: #f16464;
        padding: 12px;
        border-radius: 8px;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

def show_login_page():
    """Display login page with role-based authentication"""
    st.markdown("""
        <div style="text-align: center; padding: 40px 0;">
            <h1 style="color: #c9963a; font-size: 48px;">🏢 Exalio HR Portal</h1>
            <p style="color: #7d96be; font-size: 18px;">Complete People Intelligence Platform</p>
        </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.markdown("### Sign In")

        # Login form
        username = st.text_input("Email / Employee ID", placeholder="admin@exalio.com")
        password = st.text_input("Password", type="password", placeholder="Enter your password")

        if st.button("🔐 Sign In", use_container_width=True):
            if username and password:
                success, user_data, error = login(username, password)

                if success:
                    st.session_state.authenticated = True
                    st.session_state.user_data = user_data
                    st.success(f"✅ Welcome back, {user_data['full_name']}!")
                    st.rerun()
                else:
                    st.error(f"❌ {error}")
            else:
                st.warning("⚠️ Please enter both username and password")

        # Demo credentials info
        with st.expander("📋 Demo Login Credentials"):
            st.markdown("""
            **HR Admin Access:**
            - Email: `admin@exalio.com`
            - Password: `admin123`

            **Manager Access:**
            - Email: `john.manager@exalio.com`
            - Password: `manager123`

            **Employee Access:**
            - Email: `sarah.dev@exalio.com`
            - Password: `emp123`
            """)

def show_dashboard():
    """Display role-based dashboard"""
    user = get_current_user()

    # Header
    st.markdown(f"""
        <div class="main-header">
            <h1>Welcome back, {user['first_name']}! 👋</h1>
            <p>{user['position']} • {user['department']}</p>
        </div>
    """, unsafe_allow_html=True)

    # Get statistics based on role
    with get_db_connection() as conn:
        cursor = conn.cursor()

        if is_hr_admin():
            # HR Admin Dashboard
            cursor.execute("SELECT COUNT(*) as cnt FROM employees WHERE status = 'Active'")
            total_employees = cursor.fetchone()['cnt']

            cursor.execute("SELECT COUNT(*) as cnt FROM contracts WHERE status = 'Active'")
            active_contracts = cursor.fetchone()['cnt']

            cursor.execute("SELECT SUM(net_pay) as total FROM financial_records WHERE period LIKE '2024%'")
            result = cursor.fetchone()
            monthly_payroll = result['total'] if result['total'] else 0

            cursor.execute("SELECT COUNT(*) as cnt FROM appraisals WHERE status IN ('Submitted', 'Manager Review', 'HR Review')")
            pending_appraisals = cursor.fetchone()['cnt']

            # Display stats
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.markdown(f"""
                    <div class="stat-card">
                        <div style="font-size: 32px;">👥</div>
                        <div class="stat-value">{total_employees}</div>
                        <div class="stat-label">Total Employees</div>
                    </div>
                """, unsafe_allow_html=True)

            with col2:
                st.markdown(f"""
                    <div class="stat-card">
                        <div style="font-size: 32px;">✅</div>
                        <div class="stat-value">{active_contracts}</div>
                        <div class="stat-label">Active Contracts</div>
                    </div>
                """, unsafe_allow_html=True)

            with col3:
                st.markdown(f"""
                    <div class="stat-card">
                        <div style="font-size: 32px;">💵</div>
                        <div class="stat-value">${monthly_payroll:,.0f}</div>
                        <div class="stat-label">Monthly Payroll</div>
                    </div>
                """, unsafe_allow_html=True)

            with col4:
                st.markdown(f"""
                    <div class="stat-card">
                        <div style="font-size: 32px;">📋</div>
                        <div class="stat-value">{pending_appraisals}</div>
                        <div class="stat-label">Pending Appraisals</div>
                    </div>
                """, unsafe_allow_html=True)

            st.markdown("---")

            # Recent employees and department breakdown
            col1, col2 = st.columns([2, 1])

            with col1:
                st.subheader("📊 Recent Employees")
                cursor.execute("""
                    SELECT employee_id, first_name, last_name, department, position, grade, status
                    FROM employees
                    ORDER BY created_at DESC
                    LIMIT 10
                """)
                recent_employees = cursor.fetchall()

                if recent_employees:
                    df = pd.DataFrame(recent_employees)
                    st.dataframe(df, use_container_width=True, hide_index=True)
                else:
                    st.info("No employees found")

            with col2:
                st.subheader("🏢 Departments")
                cursor.execute("""
                    SELECT department, COUNT(*) as count
                    FROM employees
                    WHERE status = 'Active'
                    GROUP BY department
                    ORDER BY count DESC
                """)
                dept_data = cursor.fetchall()

                if dept_data:
                    for dept in dept_data:
                        st.markdown(f"**{dept['department']}**: {dept['count']} employees")
                else:
                    st.info("No data available")

        elif is_manager():
            # Manager Dashboard
            cursor.execute("""
                SELECT COUNT(*) as cnt FROM employees
                WHERE manager_id = %s AND status = 'Active'
            """, (user['employee_id'],))
            team_size = cursor.fetchone()['cnt']

            cursor.execute("""
                SELECT COUNT(*) as cnt FROM leave_requests lr
                JOIN employees e ON lr.emp_id = e.id
                WHERE e.manager_id = %s AND lr.status = 'Pending'
            """, (user['employee_id'],))
            pending_leaves = cursor.fetchone()['cnt']

            cursor.execute("""
                SELECT COUNT(*) as cnt FROM appraisals a
                JOIN employees e ON a.emp_id = e.id
                WHERE e.manager_id = %s AND a.status = 'Submitted'
            """, (user['employee_id'],))
            pending_reviews = cursor.fetchone()['cnt']

            cursor.execute("""
                SELECT COUNT(*) as cnt FROM expenses ex
                JOIN employees e ON ex.emp_id = e.id
                WHERE e.manager_id = %s AND ex.status = 'Pending'
            """, (user['employee_id'],))
            pending_expenses = cursor.fetchone()['cnt']

            # Display stats
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.markdown(f"""
                    <div class="stat-card">
                        <div style="font-size: 32px;">👥</div>
                        <div class="stat-value">{team_size}</div>
                        <div class="stat-label">Team Members</div>
                    </div>
                """, unsafe_allow_html=True)

            with col2:
                st.markdown(f"""
                    <div class="stat-card">
                        <div style="font-size: 32px;">📅</div>
                        <div class="stat-value">{pending_leaves}</div>
                        <div class="stat-label">Pending Leaves</div>
                    </div>
                """, unsafe_allow_html=True)

            with col3:
                st.markdown(f"""
                    <div class="stat-card">
                        <div style="font-size: 32px;">📋</div>
                        <div class="stat-value">{pending_reviews}</div>
                        <div class="stat-label">Pending Reviews</div>
                    </div>
                """, unsafe_allow_html=True)

            with col4:
                st.markdown(f"""
                    <div class="stat-card">
                        <div style="font-size: 32px;">💰</div>
                        <div class="stat-value">{pending_expenses}</div>
                        <div class="stat-label">Pending Expenses</div>
                    </div>
                """, unsafe_allow_html=True)

            st.markdown("---")

            # Team overview
            st.subheader("👥 Your Team")
            cursor.execute("""
                SELECT employee_id, first_name, last_name, position, grade, status, email
                FROM employees
                WHERE manager_id = %s
                ORDER BY first_name
            """, (user['employee_id'],))
            team_members = cursor.fetchall()

            if team_members:
                df = pd.DataFrame(team_members)
                st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                st.info("You don't have any direct reports yet")

        else:
            # Employee Dashboard
            cursor.execute("""
                SELECT remaining_days, leave_type FROM leave_balance
                WHERE emp_id = %s AND year = 2024
            """, (user['employee_id'],))
            leave_data = cursor.fetchall()

            cursor.execute("""
                SELECT COUNT(*) as cnt FROM leave_requests
                WHERE emp_id = %s AND status = 'Pending'
            """, (user['employee_id'],))
            pending_requests = cursor.fetchone()['cnt']

            cursor.execute("""
                SELECT COUNT(*) as cnt FROM appraisals
                WHERE emp_id = %s AND status IN ('Draft', 'Submitted')
            """, (user['employee_id'],))
            my_appraisals = cursor.fetchone()['cnt']

            cursor.execute("""
                SELECT COUNT(*) as cnt FROM training_enrollments
                WHERE emp_id = %s AND status = 'Enrolled'
            """, (user['employee_id'],))
            active_trainings = cursor.fetchone()['cnt']

            # Display stats
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                total_leave = sum([l['remaining_days'] for l in leave_data])
                st.markdown(f"""
                    <div class="stat-card">
                        <div style="font-size: 32px;">📅</div>
                        <div class="stat-value">{total_leave:.0f}</div>
                        <div class="stat-label">Leave Days Left</div>
                    </div>
                """, unsafe_allow_html=True)

            with col2:
                st.markdown(f"""
                    <div class="stat-card">
                        <div style="font-size: 32px;">⏳</div>
                        <div class="stat-value">{pending_requests}</div>
                        <div class="stat-label">Pending Requests</div>
                    </div>
                """, unsafe_allow_html=True)

            with col3:
                st.markdown(f"""
                    <div class="stat-card">
                        <div style="font-size: 32px;">📋</div>
                        <div class="stat-value">{my_appraisals}</div>
                        <div class="stat-label">My Appraisals</div>
                    </div>
                """, unsafe_allow_html=True)

            with col4:
                st.markdown(f"""
                    <div class="stat-card">
                        <div style="font-size: 32px;">🎓</div>
                        <div class="stat-value">{active_trainings}</div>
                        <div class="stat-label">Active Trainings</div>
                    </div>
                """, unsafe_allow_html=True)

            st.markdown("---")

            # Leave balance breakdown
            col1, col2 = st.columns([1, 1])

            with col1:
                st.subheader("📅 Leave Balance")
                if leave_data:
                    for leave in leave_data:
                        st.markdown(f"**{leave['leave_type']}**: {leave['remaining_days']} days")
                else:
                    st.info("No leave balance data")

            with col2:
                st.subheader("🔔 Recent Notifications")
                notifications = get_user_notifications(5)
                if notifications:
                    for notif in notifications:
                        badge_class = "badge-info" if notif['type'] == 'info' else "badge-success"
                        st.markdown(f"""
                            <div style="padding: 10px; background: rgba(58, 123, 213, 0.05); border-radius: 8px; margin-bottom: 8px;">
                                <span class="badge {badge_class}">{notif['type']}</span>
                                <strong>{notif['title']}</strong><br>
                                <small style="color: #7d96be;">{notif['message'][:100]}...</small>
                            </div>
                        """, unsafe_allow_html=True)
                else:
                    st.info("No notifications")

def main():
    """Main application entry point"""
    # Show info if on Streamlit Cloud
    import os

    if not os.access(".", os.W_OK):
        st.info("ℹ️ Running on Streamlit Cloud with PostgreSQL")

    # Initialize PostgreSQL database on first run (only once per session)
    if 'db_initialized' not in st.session_state:
        try:
            from init_postgres_on_cloud import init_postgres_from_sqlite
            with st.spinner("🔄 Initializing PostgreSQL database..."):
                if init_postgres_from_sqlite():
                    st.session_state.db_initialized = True
                else:
                    # Try standard init
                    init_database()
                    seed_initial_data()
                    st.session_state.db_initialized = True
        except Exception as e:
            st.warning(f"Database init: {str(e)[:100]}")

    # Initialize session
    init_session()

    # Check authentication
    if not st.session_state.authenticated:
        show_login_page()
        return

    # Sidebar navigation
    user = get_current_user()

    with st.sidebar:
        st.markdown(f"""
            <div style="text-align: center; padding: 20px 0;">
                <h2 style="color: #c9963a;">🏢 Exalio HR</h2>
            </div>
        """, unsafe_allow_html=True)

        st.markdown("---")

        # User profile
        st.markdown(f"""
            <div style="background: rgba(58, 123, 213, 0.1); padding: 15px; border-radius: 10px; text-align: center;">
                <div style="font-size: 48px; margin-bottom: 10px;">👤</div>
                <div style="font-weight: bold; color: #dde5f5;">{user['full_name']}</div>
                <div style="font-size: 12px; color: #7d96be;">{user['position']}</div>
                <div style="font-size: 11px; color: #3d5272; margin-top: 5px;">
                    {user['role'].upper().replace('_', ' ')}
                </div>
            </div>
        """, unsafe_allow_html=True)

        st.markdown("---")

        # Navigation menu
        st.markdown("### 📊 Main")
        if st.button("🏠 Dashboard", use_container_width=True):
            st.session_state.current_page = 'dashboard'
            st.rerun()

        # Show different menu items based on role
        if is_hr_admin() or is_manager():
            if st.button("👥 Employees", use_container_width=True):
                st.session_state.current_page = 'employees'
                st.rerun()

        st.markdown("### 🔄 HR Modules")

        # My Profile (All employees)
        if st.button("👤 My Profile", use_container_width=True):
            st.session_state.current_page = 'my_profile'
            st.rerun()

        # Profile Approvals (Manager & HR)
        if is_manager() or is_hr_admin():
            if st.button("✅ Profile Approvals", use_container_width=True):
                st.session_state.current_page = 'profile_approvals'
                st.rerun()

        # Leave Management
        if st.button("📅 Leave Management", use_container_width=True):
            st.session_state.current_page = 'leave'
            st.rerun()

        # Performance Management
        if st.button("🏅 Performance & Grades", use_container_width=True):
            st.session_state.current_page = 'performance'
            st.rerun()

        # Appraisals
        if st.button("📋 Appraisals", use_container_width=True):
            st.session_state.current_page = 'appraisals'
            st.rerun()

        # Contracts (HR only)
        if is_hr_admin():
            if st.button("📄 Contracts", use_container_width=True):
                st.session_state.current_page = 'contracts'
                st.rerun()

        # Insurance
        if st.button("🏥 Medical Insurance", use_container_width=True):
            st.session_state.current_page = 'insurance'
            st.rerun()

        # Bonus Calculator (HR & Manager)
        if is_hr_admin() or is_manager():
            if st.button("💎 Bonus Calculator", use_container_width=True):
                st.session_state.current_page = 'bonus'
                st.rerun()

        # Expenses
        if st.button("💰 Expense Claims", use_container_width=True):
            st.session_state.current_page = 'expenses'
            st.rerun()

        # Certificates
        if st.button("🎓 Certificates", use_container_width=True):
            st.session_state.current_page = 'certificates'
            st.rerun()

        # Financial Records (HR only)
        if is_hr_admin():
            if st.button("💵 Financial Records", use_container_width=True):
                st.session_state.current_page = 'financial'
                st.rerun()

        # Recruitment (HR & Manager)
        if is_hr_admin() or is_manager():
            if st.button("💼 Recruitment", use_container_width=True):
                st.session_state.current_page = 'recruitment'
                st.rerun()

        # Training
        if st.button("🎓 Training & Development", use_container_width=True):
            st.session_state.current_page = 'training'
            st.rerun()

        # Timesheets
        if st.button("⏰ Timesheets", use_container_width=True):
            st.session_state.current_page = 'timesheets'
            st.rerun()

        # Assets (HR & Manager)
        if is_hr_admin() or is_manager():
            if st.button("💻 Asset Management", use_container_width=True):
                st.session_state.current_page = 'assets'
                st.rerun()

        # Goals & OKRs
        if st.button("🎯 Goals & OKRs", use_container_width=True):
            st.session_state.current_page = 'goals'
            st.rerun()

        # Career Development (All users)
        if st.button("🚀 Career Development", use_container_width=True):
            st.session_state.current_page = 'career'
            st.rerun()

        # Exit Management (HR & Manager)
        if is_hr_admin() or is_manager():
            if st.button("🚪 Exit Management", use_container_width=True):
                st.session_state.current_page = 'exit'
                st.rerun()

        # Documents
        if st.button("📁 Documents", use_container_width=True):
            st.session_state.current_page = 'documents'
            st.rerun()

        # Announcements
        if st.button("📢 Announcements", use_container_width=True):
            st.session_state.current_page = 'announcements'
            st.rerun()

        # Onboarding
        if is_hr_admin() or is_manager():
            if st.button("🎯 Onboarding", use_container_width=True):
                st.session_state.current_page = 'onboarding'
                st.rerun()

        # Employee Directory
        if st.button("📇 Directory", use_container_width=True):
            st.session_state.current_page = 'directory'
            st.rerun()

        # Org Chart
        if st.button("🏢 Org Chart", use_container_width=True):
            st.session_state.current_page = 'org_chart'
            st.rerun()

        # Reports & Analytics
        if is_hr_admin() or is_manager():
            if st.button("📊 Reports", use_container_width=True):
                st.session_state.current_page = 'reports'
                st.rerun()

        # Shift Scheduling
        if is_hr_admin() or is_manager():
            if st.button("📅 Shift Scheduling", use_container_width=True):
                st.session_state.current_page = 'shifts'
                st.rerun()

        # Surveys & Feedback
        if st.button("📋 Surveys & Feedback", use_container_width=True):
            st.session_state.current_page = 'surveys'
            st.rerun()

        # Compliance Tracking
        if is_hr_admin():
            if st.button("⚖️ Compliance", use_container_width=True):
                st.session_state.current_page = 'compliance'
                st.rerun()

        # PIP Management
        if is_hr_admin() or is_manager():
            if st.button("📈 PIP Management", use_container_width=True):
                st.session_state.current_page = 'pip'
                st.rerun()

        # Calendar
        if st.button("📅 Calendar", use_container_width=True):
            st.session_state.current_page = 'calendar'
            st.rerun()

        # Admin Panel
        if is_hr_admin():
            if st.button("⚙️ Admin Panel", use_container_width=True):
                st.session_state.current_page = 'admin'
                st.rerun()

            # Teams & Positions
            if st.button("🏢 Teams & Positions", use_container_width=True):
                st.session_state.current_page = 'teams_positions'
                st.rerun()

            # Skill Matrix
            if st.button("🎯 Skill Matrix", use_container_width=True):
                st.session_state.current_page = 'skill_matrix'
                st.rerun()

            # Workflow Management (Function Tree)
            if st.button("🌳 Function Organization", use_container_width=True):
                st.session_state.current_page = 'workflow_management'
                st.rerun()

        # Workflow Builder (Manager & HR)
        if is_hr_admin() or is_manager():
            if st.button("🔄 Workflow Builder", use_container_width=True):
                st.session_state.current_page = 'workflow_builder'
                st.rerun()

        # Promotion Workflow
        if st.button("🚀 Promotions", use_container_width=True):
            st.session_state.current_page = 'promotions'
            st.rerun()

        # Contract Renewal
        if st.button("📄 Contract Renewal", use_container_width=True):
            st.session_state.current_page = 'contract_renewal'
            st.rerun()

        # Certificate Tracking
        if st.button("🎓 Certificate Tracking", use_container_width=True):
            st.session_state.current_page = 'certificate_tracking'
            st.rerun()

        # Document Approval
        if st.button("📋 Document Approval", use_container_width=True):
            st.session_state.current_page = 'document_approval'
            st.rerun()

        # Asset Procurement
        if st.button("💼 Asset Procurement", use_container_width=True):
            st.session_state.current_page = 'asset_procurement'
            st.rerun()

        if st.button("💰 Budget Management", use_container_width=True):
            st.session_state.current_page = 'budget_management'
            st.rerun()

        if st.button("🎯 Goals & OKRs", use_container_width=True):
            st.session_state.current_page = 'goal_okr'
            st.rerun()

        if st.button("📋 Compliance Tracking", use_container_width=True):
            st.session_state.current_page = 'compliance'
            st.rerun()

        if st.button("🔄 Succession Planning", use_container_width=True):
            st.session_state.current_page = 'succession'
            st.rerun()

        if st.button("📋 Onboarding Tasks", use_container_width=True):
            st.session_state.current_page = 'onboarding'
            st.rerun()

        if st.button("📈 PIP Management", use_container_width=True):
            st.session_state.current_page = 'pip'
            st.rerun()

        if st.button("🏥 Insurance", use_container_width=True):
            st.session_state.current_page = 'insurance'
            st.rerun()

        if st.button("🔄 Shift Swap", use_container_width=True):
            st.session_state.current_page = 'shift_swap'
            st.rerun()

        if st.button("📢 Announcements", use_container_width=True):
            st.session_state.current_page = 'announcements'
            st.rerun()

        if st.button("📊 Surveys", use_container_width=True):
            st.session_state.current_page = 'surveys'
            st.rerun()

        if st.button("⚖️ Appraisal Calibration", use_container_width=True):
            st.session_state.current_page = 'calibration'
            st.rerun()

        # Email Integration
        if is_hr_admin():
            if st.button("📧 Email Settings", use_container_width=True):
                st.session_state.current_page = 'email'
                st.rerun()

        # Mobile View
        if st.button("📱 Mobile View", use_container_width=True):
            st.session_state.current_page = 'mobile'
            st.rerun()

        # Notifications
        unread_count = get_unread_count()
        notif_label = f"🔔 Notifications ({unread_count})" if unread_count > 0 else "🔔 Notifications"
        if st.button(notif_label, use_container_width=True):
            st.session_state.current_page = 'notifications'
            st.rerun()

        # Show pending count badge for approvals
        pending_count = get_pending_approvals()
        approval_label = f"📋 Approvals ({pending_count})" if pending_count > 0 else "📋 Approvals"

        if is_manager() or is_hr_admin():
            if st.button(approval_label, use_container_width=True):
                st.session_state.current_page = 'approvals'
                st.rerun()

        st.markdown("---")

        # Logout button
        if st.button("🚪 Logout", use_container_width=True):
            logout()
            st.rerun()

    # Main content area
    current_page = st.session_state.get('current_page', 'dashboard')

    if current_page == 'dashboard':
        show_dashboard()
    elif current_page == 'employees':
        from modules.employee_management import show_employee_management
        show_employee_management()
    elif current_page == 'leave':
        from modules.leave_management import show_leave_management
        show_leave_management()
    elif current_page == 'performance':
        from modules.performance import show_performance_management
        show_performance_management()
    elif current_page == 'appraisals':
        from modules.appraisals import show_appraisals_management
        show_appraisals_management()
    elif current_page == 'contracts':
        from modules.contracts import show_contracts_management
        show_contracts_management()
    elif current_page == 'insurance':
        from modules.insurance import show_insurance_management
        show_insurance_management()
    elif current_page == 'bonus':
        from modules.bonus import show_bonus_management
        show_bonus_management()
    elif current_page == 'notifications':
        from modules.notifications import show_notifications_center
        show_notifications_center()
    elif current_page == 'expenses':
        from modules.expenses import show_expense_management
        show_expense_management()
    elif current_page == 'certificates':
        from modules.certificates import show_certificates_management
        show_certificates_management()
    elif current_page == 'financial':
        from modules.financial import show_financial_management
        show_financial_management()
    elif current_page == 'recruitment':
        from modules.recruitment import show_recruitment_management
        show_recruitment_management()
    elif current_page == 'training':
        from modules.training import show_training_management
        show_training_management()
    elif current_page == 'timesheets':
        from modules.timesheets import show_timesheet_management
        show_timesheet_management()
    elif current_page == 'assets':
        from modules.assets import show_asset_management
        show_asset_management()
    elif current_page == 'goals':
        from modules.goals import show_goals_management
        show_goals_management()
    elif current_page == 'career':
        from modules.career_plans import show_career_plans_management
        show_career_plans_management()
    elif current_page == 'exit':
        from modules.exit_management import show_exit_management
        show_exit_management()
    elif current_page == 'documents':
        from modules.documents import show_document_management
        show_document_management()
    elif current_page == 'announcements':
        from modules.announcements import show_announcements_management
        show_announcements_management()
    elif current_page == 'onboarding':
        from modules.onboarding import show_onboarding_management
        show_onboarding_management()
    elif current_page == 'directory':
        from modules.directory import show_employee_directory
        show_employee_directory()
    elif current_page == 'org_chart':
        from modules.org_chart import show_org_chart
        show_org_chart()
    elif current_page == 'reports':
        from modules.reports import show_reports_analytics
        show_reports_analytics()
    elif current_page == 'shifts':
        from modules.shift_scheduling import show_shift_scheduling
        show_shift_scheduling()
    elif current_page == 'surveys':
        from modules.surveys import show_surveys_feedback
        show_surveys_feedback()
    elif current_page == 'compliance':
        from modules.compliance import show_compliance_tracking
        show_compliance_tracking()
    elif current_page == 'pip':
        from modules.pip import show_pip_management
        show_pip_management()
    elif current_page == 'calendar':
        from modules.calendar_integration import show_calendar_integration
        show_calendar_integration()
    elif current_page == 'admin':
        from modules.admin_panel import show_admin_panel
        show_admin_panel()
    elif current_page == 'email':
        from modules.email_integration import show_email_integration
        show_email_integration()
    elif current_page == 'mobile':
        from modules.mobile_ui import show_mobile_ui
        show_mobile_ui()
    elif current_page == 'approvals':
        st.info("📋 Unified approval workflow hub coming soon")
    elif current_page == 'my_profile':
        show_profile_manager()
    elif current_page == 'profile_approvals':
        show_approval_interface()
    elif current_page == 'teams_positions':
        show_team_position_admin()
    elif current_page == 'skill_matrix':
        show_skill_matrix_admin()
    elif current_page == 'workflow_management':
        from modules.workflow_management import show_workflow_management
        show_workflow_management()
    elif current_page == 'workflow_builder':
        from modules.workflow_builder import show_workflow_builder
        show_workflow_builder()
    elif current_page == 'promotions':
        from modules.promotion_workflow import show_promotion_workflow
        show_promotion_workflow()
    elif current_page == 'contract_renewal':
        from modules.contract_renewal import show_contract_renewal
        show_contract_renewal()
    elif current_page == 'certificate_tracking':
        from modules.certificate_tracking import show_certificate_tracking
        show_certificate_tracking()
    elif current_page == 'document_approval':
        from modules.document_approval import show_document_approval
        show_document_approval()
    elif current_page == 'asset_procurement':
        from modules.asset_procurement import show_asset_procurement
        show_asset_procurement()
    elif current_page == 'budget_management':
        from modules.budget_management import show_budget_management
        show_budget_management()
    elif current_page == 'goal_okr':
        from modules.goal_okr_review import show_goal_okr_review
        show_goal_okr_review()
    elif current_page == 'compliance':
        from modules.compliance_tracking import show_compliance_tracking
        show_compliance_tracking()
    elif current_page == 'succession':
        from modules.succession_planning import show_succession_planning
        show_succession_planning()
    elif current_page == 'onboarding':
        from modules.onboarding_tasks import show_onboarding_tasks
        show_onboarding_tasks()
    elif current_page == 'pip':
        from modules.pip_execution import show_pip_execution
        show_pip_execution()
    elif current_page == 'insurance':
        from modules.insurance_enrollment import show_insurance_enrollment
        show_insurance_enrollment()
    elif current_page == 'shift_swap':
        from modules.shift_swap import show_shift_swap
        show_shift_swap()
    elif current_page == 'announcements':
        from modules.announcement_approval import show_announcement_approval
        show_announcement_approval()
    elif current_page == 'surveys':
        from modules.survey_workflow import show_survey_workflow
        show_survey_workflow()
    elif current_page == 'calibration':
        from modules.appraisal_calibration import show_appraisal_calibration
        show_appraisal_calibration()
    else:
        show_dashboard()

if __name__ == "__main__":
    main()
