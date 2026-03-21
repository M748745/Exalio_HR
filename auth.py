"""
Exalio HR System - Authentication Module
Role-based access control for HR Admin, Manager, and Employee
"""

import streamlit as st
from datetime import datetime
from database import get_db_connection, hash_password

def login(username, password):
    """
    Authenticate user and return user data with role
    Returns: (success, user_data, error_message)
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Get user with hashed password
        hashed_pw = hash_password(password)
        cursor.execute("""
            SELECT u.id, u.username, u.role, u.employee_id, u.is_active,
                   e.id as emp_id, e.first_name, e.last_name, e.department,
                   e.position, e.photo, e.manager_id, e.team_tag
            FROM users u
            LEFT JOIN employees e ON u.employee_id = e.id
            WHERE u.username = %s AND u.password = %s AND u.is_active = 1
        """, (username, hashed_pw))

        user = cursor.fetchone()

        if not user:
            return False, None, "Invalid username or password"

        # Update last login
        cursor.execute("""
            UPDATE users SET last_login = %s WHERE id = %s
        """, (datetime.now().isoformat(), user['id']))
        conn.commit()

        user_data = {
            'user_id': user['id'],
            'username': user['username'],
            'role': user['role'],
            'employee_id': user['emp_id'],
            'first_name': user['first_name'],
            'last_name': user['last_name'],
            'full_name': f"{user['first_name']} {user['last_name']}",
            'department': user['department'],
            'position': user['position'],
            'photo': user['photo'],
            'manager_id': user['manager_id'],
            'team_tag': user['team_tag']
        }

        return True, user_data, None

def logout():
    """Clear session state and logout user"""
    for key in list(st.session_state.keys()):
        del st.session_state[key]

def init_session():
    """Initialize session state variables"""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'user_data' not in st.session_state:
        st.session_state.user_data = None
    if 'current_page' not in st.session_state:
        st.session_state.current_page = 'dashboard'

def get_current_user():
    """Get current logged-in user data"""
    return st.session_state.get('user_data', None)

def get_user_role():
    """Get current user's role"""
    user = get_current_user()
    return user['role'] if user else None

def is_hr_admin():
    """Check if current user is HR Admin"""
    return get_user_role() == 'hr_admin'

def is_manager():
    """Check if current user is Manager"""
    return get_user_role() == 'manager'

def is_employee():
    """Check if current user is Employee"""
    return get_user_role() == 'employee'

def require_role(*allowed_roles):
    """
    Decorator to restrict access to specific roles
    Usage: @require_role('hr_admin', 'manager')
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            user_role = get_user_role()
            if user_role not in allowed_roles:
                st.error(f"🚫 Access Denied. This feature requires {', '.join(allowed_roles)} role.")
                return None
            return func(*args, **kwargs)
        return wrapper
    return decorator

def get_team_members(manager_id):
    """Get all employees under a specific manager"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM employees WHERE manager_id = %s AND status = 'Active'
        """, (manager_id,))
        return [dict(row) for row in cursor.fetchall()]

def get_accessible_employees():
    """
    Get employees accessible to current user based on role
    - HR Admin: All employees
    - Manager: Own team members
    - Employee: Only self
    """
    user = get_current_user()
    if not user:
        return []

    with get_db_connection() as conn:
        cursor = conn.cursor()

        if user['role'] == 'hr_admin':
            # HR Admin sees all employees
            cursor.execute("SELECT * FROM employees ORDER BY first_name")
        elif user['role'] == 'manager':
            # Manager sees only their team
            cursor.execute("""
                SELECT * FROM employees
                WHERE manager_id = %s OR id = %s
                ORDER BY first_name
            """, (user['employee_id'], user['employee_id']))
        else:
            # Employee sees only themselves
            cursor.execute("""
                SELECT * FROM employees WHERE id = %s
            """, (user['employee_id'],))

        return [dict(row) for row in cursor.fetchall()]

def can_access_employee(target_emp_id):
    """Check if current user can access specific employee's data"""
    user = get_current_user()
    if not user:
        return False

    if user['role'] == 'hr_admin':
        return True

    if user['role'] == 'manager':
        # Check if employee is in manager's team
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id FROM employees
                WHERE id = %s AND (manager_id = %s OR id = %s)
            """, (target_emp_id, user['employee_id'], user['employee_id']))
            return cursor.fetchone() is not None

    # Employee can only access their own data
    return target_emp_id == user['employee_id']

def can_approve_leave(leave_request):
    """Check if current user can approve a leave request"""
    user = get_current_user()
    if not user:
        return False

    if user['role'] == 'hr_admin':
        # HR can approve if manager already approved
        return leave_request['status'] == 'Manager Approved'

    if user['role'] == 'manager':
        # Manager can approve if pending and employee is in their team
        if leave_request['status'] == 'Pending':
            return can_access_employee(leave_request['emp_id'])

    return False

def can_approve_expense(expense):
    """Check if current user can approve an expense claim"""
    user = get_current_user()
    if not user:
        return False

    if user['role'] == 'hr_admin' or user['role'] == 'manager':
        if expense['status'] == 'Pending':
            return can_access_employee(expense['emp_id'])

    return False

def get_pending_approvals():
    """Get count of pending approvals for current user"""
    user = get_current_user()
    if not user:
        return 0

    count = 0

    with get_db_connection() as conn:
        cursor = conn.cursor()

        if user['role'] == 'manager':
            # Count pending leave requests from team
            cursor.execute("""
                SELECT COUNT(*) as cnt FROM leave_requests lr
                JOIN employees e ON lr.emp_id = e.id
                WHERE e.manager_id = %s AND lr.status = 'Pending'
            """, (user['employee_id'],))
            count += cursor.fetchone()['cnt']

            # Count pending expense claims
            cursor.execute("""
                SELECT COUNT(*) as cnt FROM expenses ex
                JOIN employees e ON ex.emp_id = e.id
                WHERE e.manager_id = %s AND ex.status = 'Pending'
            """, (user['employee_id'],))
            count += cursor.fetchone()['cnt']

            # Count pending timesheets
            cursor.execute("""
                SELECT COUNT(*) as cnt FROM timesheets ts
                JOIN employees e ON ts.emp_id = e.id
                WHERE e.manager_id = %s AND ts.status = 'Pending'
            """, (user['employee_id'],))
            count += cursor.fetchone()['cnt']

        elif user['role'] == 'hr_admin':
            # Count leave requests approved by manager but pending HR
            cursor.execute("""
                SELECT COUNT(*) as cnt FROM leave_requests
                WHERE status = 'Manager Approved'
            """)
            count += cursor.fetchone()['cnt']

            # Count pending appraisals
            cursor.execute("""
                SELECT COUNT(*) as cnt FROM appraisals
                WHERE status IN ('Manager Review', 'HR Review')
            """)
            count += cursor.fetchone()['cnt']

            # Count pending training enrollments
            cursor.execute("""
                SELECT COUNT(*) as cnt FROM training_enrollments
                WHERE status = 'Manager Approved'
            """)
            count += cursor.fetchone()['cnt']

    return count

def create_notification(recipient_id, title, message, notif_type='info'):
    """Create a notification for a user"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO notifications (recipient_id, title, message, type)
            VALUES (%s, %s, %s, %s)
        """, (recipient_id, title, message, notif_type))
        conn.commit()

def get_user_notifications(limit=10):
    """Get notifications for current user"""
    user = get_current_user()
    if not user:
        return []

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM notifications
            WHERE recipient_id = %s
            ORDER BY created_at DESC
            LIMIT %s
        """, (user['employee_id'], limit))
        return [dict(row) for row in cursor.fetchall()]

def mark_notification_read(notification_id):
    """Mark a notification as read"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE notifications SET is_read = 1 WHERE id = %s
        """, (notification_id,))
        conn.commit()

def get_unread_count():
    """Get count of unread notifications for current user"""
    user = get_current_user()
    if not user:
        return 0

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) as cnt FROM notifications
            WHERE recipient_id = %s AND is_read = 0
        """, (user['employee_id'],))
        return cursor.fetchone()['cnt']

def log_audit(action, table_name=None, record_id=None, old_values=None, new_values=None):
    """Log user action for audit trail"""
    user = get_current_user()
    if not user:
        return

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO audit_logs (user_id, action, table_name, record_id, old_values, new_values)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (user['user_id'], action, table_name, record_id, old_values, new_values))
        conn.commit()
