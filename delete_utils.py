"""
Delete Utility Functions
Admin-only delete operations for all HR functions with audit logging
"""

import streamlit as st
from database import get_db_connection
from auth import is_hr_admin, get_current_user, log_audit


def admin_delete_with_confirmation(table_name, record_id, record_description, id_column="id"):
    """
    Show delete confirmation dialog and perform deletion if confirmed

    Args:
        table_name: Database table name
        record_id: ID of the record to delete
        record_description: Human-readable description for confirmation
        id_column: Name of the ID column (default: 'id')

    Returns:
        True if deleted, False otherwise
    """
    if not is_hr_admin():
        st.error("❌ Delete operations are restricted to HR Admin only")
        return False

    # Create unique key for this delete operation
    confirm_key = f"confirm_delete_{table_name}_{record_id}"

    if confirm_key not in st.session_state:
        st.session_state[confirm_key] = False

    # First click: Show confirmation
    if not st.session_state[confirm_key]:
        st.session_state[confirm_key] = True
        st.warning(f"⚠️ Click again to confirm deletion of: {record_description}")
        return False

    # Second click: Perform deletion
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # Check if record exists
            cursor.execute(f"SELECT * FROM {table_name} WHERE {id_column} = %s", (record_id,))
            record = cursor.fetchone()

            if not record:
                st.error(f"❌ Record not found in {table_name}")
                return False

            # Perform deletion
            cursor.execute(f"DELETE FROM {table_name} WHERE {id_column} = %s", (record_id,))
            conn.commit()

            # Log audit
            user = get_current_user()
            log_audit(
                f"DELETED record from {table_name}: {record_description}",
                table_name,
                record_id
            )

            # Clear confirmation state
            del st.session_state[confirm_key]

            st.success(f"✅ Successfully deleted: {record_description}")
            return True

    except Exception as e:
        st.error(f"❌ Error deleting record: {str(e)}")
        # Clear confirmation state on error
        if confirm_key in st.session_state:
            del st.session_state[confirm_key]
        return False


def render_delete_button(table_name, record_id, record_description, button_key, id_column="id", use_container_width=True):
    """
    Render a delete button with confirmation logic

    Args:
        table_name: Database table name
        record_id: ID of the record to delete
        record_description: Human-readable description
        button_key: Unique key for the button
        id_column: Name of the ID column
        use_container_width: Whether button should use full width

    Returns:
        True if deletion was performed and page should rerun
    """
    if not is_hr_admin():
        return False

    confirm_key = f"confirm_delete_{table_name}_{record_id}"

    # Check if in confirmation mode
    in_confirmation = st.session_state.get(confirm_key, False)

    if in_confirmation:
        button_label = "⚠️ Confirm Delete"
        button_type = "primary"
    else:
        button_label = "🗑️ Delete"
        button_type = "secondary"

    if st.button(button_label, key=button_key, use_container_width=use_container_width, type=button_type):
        if admin_delete_with_confirmation(table_name, record_id, record_description, id_column):
            st.rerun()
            return True

    return False


def cascade_delete_employee(employee_id):
    """
    Delete employee and all related records with cascade
    Only for HR Admin

    Args:
        employee_id: ID of employee to delete

    Returns:
        True if successful, False otherwise
    """
    if not is_hr_admin():
        st.error("❌ Delete operations are restricted to HR Admin only")
        return False

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # Get employee info for logging
            cursor.execute("""
                SELECT employee_id, first_name, last_name
                FROM employees
                WHERE id = %s
            """, (employee_id,))
            emp = cursor.fetchone()

            if not emp:
                st.error("❌ Employee not found")
                return False

            emp_desc = f"{emp['first_name']} {emp['last_name']} ({emp['employee_id']})"

            # Delete related records in order (to handle foreign keys)
            tables_to_clean = [
                'leave_requests',
                'leave_balance',
                'appraisals',
                'performance_history',
                'contracts',
                'financial_records',
                'training_enrollments',
                'certificates',
                'goals',
                'career_plans',
                'exit_interviews',
                'assets',
                'expenses',
                'timesheets',
                'shifts',
                'onboarding_tasks',
                'employee_skills',
                'documents',
                'notifications',
                'audit_log'
            ]

            deleted_counts = {}

            for table in tables_to_clean:
                try:
                    cursor.execute(f"DELETE FROM {table} WHERE emp_id = %s", (employee_id,))
                    deleted_counts[table] = cursor.rowcount
                except Exception as e:
                    # Some tables might not exist or have different column names
                    pass

            # Finally delete the employee
            cursor.execute("DELETE FROM employees WHERE id = %s", (employee_id,))

            conn.commit()

            # Log audit
            user = get_current_user()
            log_audit(
                f"CASCADE DELETED employee and all related records: {emp_desc}",
                "employees",
                employee_id
            )

            st.success(f"✅ Successfully deleted employee {emp_desc} and all related records")

            # Show deletion summary
            with st.expander("📋 Deletion Summary"):
                for table, count in deleted_counts.items():
                    if count > 0:
                        st.write(f"- {table}: {count} records")

            return True

    except Exception as e:
        st.error(f"❌ Error during cascade deletion: {str(e)}")
        return False
