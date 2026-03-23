"""
Asset Management Module
Track company assets (laptops, phones, equipment) assigned to employees
"""

import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
from database import get_db_connection
from auth import get_current_user, is_hr_admin, is_manager, create_notification, log_audit

def show_asset_management():
    """Main asset management interface"""
    user = get_current_user()

    st.markdown("## 💻 Asset Management")
    st.markdown("Track and manage company assets")
    st.markdown("---")

    if is_hr_admin():
        tabs = st.tabs(["📋 All Assets", "➕ Add Asset", "👥 Assignments", "📊 Reports"])
    elif is_manager():
        tabs = st.tabs(["👥 Team Assets", "📋 My Assets"])
    else:
        tabs = st.tabs(["📋 My Assets", "📊 History"])

    with tabs[0]:
        if is_hr_admin():
            show_all_assets()
        elif is_manager():
            show_team_assets()
        else:
            show_my_assets()

    with tabs[1]:
        if is_hr_admin():
            show_add_asset()
        else:
            show_asset_history()

    if len(tabs) > 2:
        with tabs[2]:
            if is_hr_admin():
                show_asset_assignments()

    if len(tabs) > 3:
        with tabs[3]:
            show_asset_reports()

def show_my_assets():
    """Show employee's assigned assets"""
    user = get_current_user()

    st.markdown("### 📋 My Assigned Assets")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM assets
            WHERE assigned_to = %s AND status = 'Assigned'
            ORDER BY created_at DESC
        """, (user['employee_id'],))
        assets = [dict(row) for row in cursor.fetchall()]

    if assets:
        for asset in assets:
            asset_icon = {
                'Laptop': '💻',
                'Desktop': '🖥️',
                'Phone': '📱',
                'Tablet': '📱',
                'Monitor': '🖥️',
                'Keyboard': '⌨️',
                'Mouse': '🖱️',
                'Headset': '🎧',
                'Other': '📦'
            }.get(asset['asset_type'], '📦')

            condition_color = {
                'New': 'rgba(45, 212, 170, 0.1)',
                'Good': 'rgba(91, 156, 246, 0.1)',
                'Fair': 'rgba(240, 180, 41, 0.1)',
                'Poor': 'rgba(241, 100, 100, 0.1)'
            }.get(asset['condition'], 'rgba(58, 123, 213, 0.05)')

            st.markdown(f"""
                <div style="background: {condition_color}; padding: 15px; border-radius: 10px; margin-bottom: 12px; border-left: 3px solid #c9963a;">
                    <div style="font-size: 24px; margin-bottom: 5px;">{asset_icon}</div>
                    <strong style="font-size: 15px;">{asset['asset_name']}</strong><br>
                    <small style="color: #7d96be;">
                        Type: {asset['asset_type']} •
                        Serial: {asset['serial_number'] or 'N/A'}<br>
                        Created: {asset.get('created_at', 'N/A')[:10] if asset.get('created_at') else 'N/A'} •
                        Condition: {asset['condition']}
                    </small>
                </div>
            """, unsafe_allow_html=True)

            if asset['notes']:
                st.info(f"📝 Notes: {asset['notes']}")

            # Report issue
            if st.button(f"⚠️ Report Issue", key=f"report_{asset['id']}"):
                report_asset_issue(asset['id'])
                st.rerun()
    else:
        st.info("No assets currently assigned to you")

def show_asset_history():
    """Show asset assignment history"""
    user = get_current_user()

    st.markdown("### 📊 Asset History")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM assets
            WHERE assigned_to = %s OR assigned_to IS NULL
            ORDER BY created_at DESC
        """, (user['employee_id'],))
        history = [dict(row) for row in cursor.fetchall()]

    if history:
        for asset in history:
            status_badge = {
                'Assigned': '🟢 Active',
                'Returned': '⚪ Returned',
                'Damaged': '🔴 Damaged',
                'Lost': '🔴 Lost'
            }.get(asset['status'], asset['status'])

            st.markdown(f"""
                <div style="background: rgba(58, 123, 213, 0.05); padding: 12px; border-radius: 8px; margin-bottom: 8px;">
                    <strong>{asset['asset_name']}</strong> ({asset['asset_type']})<br>
                    <small style="color: #7d96be;">
                        {status_badge} •
                        Created: {asset.get('created_at', 'N/A')[:10] if asset.get('created_at') else 'N/A'}
                    </small>
                </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No asset history")

def show_team_assets():
    """Show team assets (Manager view)"""
    user = get_current_user()

    st.markdown("### 👥 Team Assets")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT a.*, e.first_name, e.last_name, e.employee_id
            FROM assets a
            LEFT JOIN employees e ON a.assigned_to = e.id
            WHERE e.manager_id = %s AND a.status = 'Assigned'
            ORDER BY a.created_at DESC
        """, (user['employee_id'],))
        assets = [dict(row) for row in cursor.fetchall()]

    if assets:
        df = pd.DataFrame(assets)
        display_cols = ['employee_id', 'first_name', 'last_name', 'asset_name', 'asset_type', 'serial_number', 'condition']
        df_display = df[display_cols]
        df_display.columns = ['Emp ID', 'First Name', 'Last Name', 'Asset', 'Type', 'Serial', 'Condition']

        st.dataframe(df_display, use_container_width=True, hide_index=True)
    else:
        st.info("No assets assigned to team members")

def show_all_assets():
    """Show all assets (HR Admin view)"""
    st.markdown("### 📋 All Company Assets")

    # Filters
    col1, col2, col3 = st.columns(3)
    with col1:
        status_filter = st.selectbox("Status", ["All", "Available", "Assigned", "Maintenance", "Retired", "Lost", "Damaged"])
    with col2:
        type_filter = st.selectbox("Type", ["All", "Laptop", "Desktop", "Phone", "Tablet", "Monitor", "Keyboard", "Mouse", "Headset", "Other"])
    with col3:
        search = st.text_input("🔍 Search")

    with get_db_connection() as conn:
        cursor = conn.cursor()

        query = """
            SELECT a.*, e.first_name, e.last_name, e.id as employee_id
            FROM assets a
            LEFT JOIN employees e ON a.assigned_to = e.id
            WHERE 1=1
        """
        params = []

        if status_filter != "All":
            query += " AND a.status = %s"
            params.append(status_filter)

        if type_filter != "All":
            query += " AND a.asset_type = %s"
            params.append(type_filter)

        if search:
            query += " AND (a.asset_name LIKE %s OR a.serial_number LIKE %s)"
            params.extend([f"%{search}%", f"%{search}%"])

        query += " ORDER BY a.created_at DESC"

        cursor.execute(query, params)
        assets = [dict(row) for row in cursor.fetchall()]

    if assets:
        for asset in assets:
            with st.expander(f"📦 {asset.get('asset_name', 'N/A')} ({asset.get('asset_type', 'N/A')}) - {asset.get('status', 'N/A')}"):
                col1, col2 = st.columns([2, 1])

                with col1:
                    st.markdown(f"""
                    **Asset:** {asset.get('asset_name', 'N/A')}
                    **Type:** {asset.get('asset_type', 'N/A')}
                    **Serial Number:** {asset.get('serial_number', 'N/A')}
                    **Purchase Date:** {asset.get('purchase_date', 'N/A')}
                    **Purchase Cost:** ${asset.get('purchase_cost', 0):,.2f}
                    **Condition:** {asset.get('condition', 'N/A')}
                    **Status:** {asset.get('status', 'N/A')}
                    **Created:** {asset.get('created_at', 'N/A')[:10] if asset.get('created_at') else 'N/A'}
                    """)

                    if asset.get('assigned_to'):
                        st.markdown(f"""
                        **Assigned To:** {asset.get('first_name', 'N/A')} {asset.get('last_name', '')} ({asset.get('employee_id', 'N/A')})
                        """)

                with col2:
                    if asset.get('purchase_cost'):
                        st.metric("Value", f"${asset.get('purchase_cost', 0):,.2f}")

                if asset.get('notes'):
                    st.info(f"📝 Notes: {asset.get('notes')}")

                # Actions
                st.markdown("---")

                if asset['status'] == 'Available':
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("👤 Assign Asset", key=f"assign_{asset['id']}"):
                            show_assign_asset_form(asset['id'])
                    with col2:
                        if st.button("🔧 Send to Maintenance", key=f"maint_{asset['id']}"):
                            update_asset_status(asset['id'], 'Maintenance')
                            st.rerun()

                elif asset['status'] == 'Assigned':
                    if st.button("↩️ Return Asset", key=f"return_{asset['id']}"):
                        return_asset(asset['id'])
                        st.rerun()

                elif asset['status'] == 'Maintenance':
                    if st.button("✅ Mark Available", key=f"available_{asset['id']}"):
                        update_asset_status(asset['id'], 'Available')
                        st.rerun()
    else:
        st.info("No assets found")

def show_add_asset():
    """Add new asset"""
    st.markdown("### ➕ Add New Asset")

    with st.form("add_asset"):
        asset_name = st.text_input("Asset Name *", placeholder="e.g., MacBook Pro 16\"")

        col1, col2 = st.columns(2)

        with col1:
            asset_type = st.selectbox("Asset Type *", [
                "Laptop", "Desktop", "Phone", "Tablet", "Monitor",
                "Keyboard", "Mouse", "Headset", "Other"
            ])
            serial_number = st.text_input("Serial Number", placeholder="S/N or IMEI")
            purchase_date = st.date_input("Purchase Date", value=date.today())

        with col2:
            purchase_cost = st.number_input("Purchase Cost ($)", min_value=0.0, value=0.0, step=100.0)
            condition = st.selectbox("Condition *", ["New", "Good", "Fair", "Poor"])
            warranty_expiry = st.date_input("Warranty Expiry", value=date.today() + timedelta(days=365))

        notes = st.text_area("Notes", placeholder="Additional information about the asset...")

        submitted = st.form_submit_button("📦 Add Asset", use_container_width=True)

        if submitted:
            if not all([asset_name, asset_type, condition]):
                st.error("❌ Please fill all required fields")
            else:
                create_asset(asset_name, asset_type, serial_number, purchase_date, purchase_cost, condition, warranty_expiry, notes)
                st.rerun()

def show_assign_asset_form(asset_id):
    """Show form to assign asset"""
    st.markdown("#### Assign Asset to Employee")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, employee_id, first_name, last_name FROM employees WHERE status = 'Active'")
        employees = [dict(row) for row in cursor.fetchall()]

    emp_options = {f"{e['first_name']} {e['last_name']} ({e['employee_id']})": e['id'] for e in employees}
    selected_emp = st.selectbox("Select Employee", list(emp_options.keys()))

    if st.button("✅ Assign"):
        emp_id = emp_options[selected_emp]
        assign_asset(asset_id, emp_id)
        st.rerun()

def show_asset_assignments():
    """Show asset assignment history"""
    st.markdown("### 👥 Asset Assignments")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT a.*, e.first_name, e.last_name, e.employee_id, e.department
            FROM assets a
            LEFT JOIN employees e ON a.assigned_to = e.id
            WHERE a.status IN ('Assigned', 'Available')
            ORDER BY a.created_at DESC
            LIMIT 50
        """)
        assignments = [dict(row) for row in cursor.fetchall()]

    if assignments:
        for assignment in assignments:
            status_icon = '🟢' if assignment.get('status') == 'Assigned' else '⚪'
            created_date_str = str(assignment.get('created_at', ''))[:10] if assignment.get('created_at') else 'N/A'
            first_name = assignment.get('first_name', 'Unknown') if assignment.get('assigned_to') else 'Unassigned'
            last_name = assignment.get('last_name', '') if assignment.get('assigned_to') else ''
            employee_id = assignment.get('employee_id', 'N/A') if assignment.get('assigned_to') else 'N/A'
            department = assignment.get('department', 'N/A') if assignment.get('assigned_to') else 'N/A'
            asset_name = assignment.get('asset_name', 'Unknown Asset')

            st.markdown(f"""
                <div style="background: rgba(58, 123, 213, 0.05); padding: 12px; border-radius: 8px; margin-bottom: 8px;">
                    {status_icon} <strong>{asset_name}</strong> →
                    {first_name} {last_name} ({employee_id})<br>
                    <small style="color: #7d96be;">
                        Department: {department} •
                        Created: {created_date_str}
                    </small>
                </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No assignment history")

def show_asset_reports():
    """Show asset reports and statistics"""
    st.markdown("### 📊 Asset Reports")

    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Total assets by status
        cursor.execute("""
            SELECT status, COUNT(*) as count
            FROM assets
            GROUP BY status
            ORDER BY count DESC
        """)
        status_data = [dict(row) for row in cursor.fetchall()]

        # Total assets by type
        cursor.execute("""
            SELECT asset_type, COUNT(*) as count
            FROM assets
            GROUP BY asset_type
            ORDER BY count DESC
        """)
        type_data = [dict(row) for row in cursor.fetchall()]

        # Total value
        cursor.execute("SELECT SUM(purchase_cost) as total FROM assets")
        total_value = cursor.fetchone()['total'] or 0

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 📊 Assets by Status")
        for item in status_data:
            st.markdown(f"**{item['status']}**: {item['count']}")

    with col2:
        st.markdown("#### 📦 Assets by Type")
        for item in type_data:
            st.markdown(f"**{item['asset_type']}**: {item['count']}")

    st.markdown("---")
    st.metric("💰 Total Asset Value", f"${total_value:,.2f}")

def create_asset(asset_name, asset_type, serial_number, purchase_date, purchase_cost, condition, warranty_expiry, notes):
    """Create new asset"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO assets (
                    asset_name, asset_type, serial_number, purchase_date,
                    purchase_cost, condition, notes, status
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, 'Available')
            """, (asset_name, asset_type, serial_number,
                 purchase_date.isoformat() if purchase_date else None,
                 purchase_cost, condition, notes))

            asset_id = cursor.lastrowid

            conn.commit()
            log_audit(f"Created asset: {asset_name}", "assets", asset_id)
            st.success(f"✅ Asset created successfully! ID: ASSET-{asset_id}")
            st.balloons()

    except Exception as e:
        st.error(f"❌ Error: {str(e)}")

def assign_asset(asset_id, emp_id):
    """Assign asset to employee"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                UPDATE assets SET
                    assigned_to = %s,
                    status = 'Assigned'
                WHERE id = %s
            """, (emp_id, asset_id))

            # Get asset and employee info
            cursor.execute("SELECT asset_name FROM assets WHERE id = %s", (asset_id,))
            asset = cursor.fetchone()

            create_notification(
                emp_id,
                "Asset Assigned",
                f"You have been assigned: {asset['asset_name']}",
                'info'
            )

            conn.commit()
            log_audit(f"Assigned asset {asset_id} to employee {emp_id}", "assets", asset_id)
            st.success("✅ Asset assigned successfully!")

    except Exception as e:
        st.error(f"❌ Error: {str(e)}")

def return_asset(asset_id):
    """Return asset from employee"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                UPDATE assets SET
                    status = 'Available',
                    assigned_to = NULL
                WHERE id = %s
            """, (asset_id,))

            conn.commit()
            log_audit(f"Returned asset {asset_id}", "assets", asset_id)
            st.success("✅ Asset returned successfully!")

    except Exception as e:
        st.error(f"❌ Error: {str(e)}")

def update_asset_status(asset_id, status):
    """Update asset status"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE assets SET status = %s WHERE id = %s", (status, asset_id))
            conn.commit()
            log_audit(f"Updated asset {asset_id} status to {status}", "assets", asset_id)
            st.success(f"✅ Asset status updated to {status}")

    except Exception as e:
        st.error(f"❌ Error: {str(e)}")

def report_asset_issue(asset_id):
    """Report issue with asset"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("UPDATE assets SET status = 'Maintenance' WHERE id = %s", (asset_id,))

            # Notify HR
            cursor.execute("SELECT id FROM employees WHERE department = 'Human Resources' LIMIT 1")
            hr_emp = cursor.fetchone()
            if hr_emp:
                create_notification(
                    hr_emp['id'],
                    "Asset Issue Reported",
                    f"An asset issue has been reported (ASSET-{asset_id})",
                    'warning'
                )

            conn.commit()
            log_audit(f"Reported issue with asset {asset_id}", "assets", asset_id)
            st.success("✅ Issue reported. Asset marked for maintenance.")

    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
