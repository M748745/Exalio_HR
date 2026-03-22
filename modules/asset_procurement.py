"""
Asset Procurement Module
Manage asset requests, approvals, purchases, and assignments
"""

import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
from database import get_db_connection
from auth import get_current_user, is_hr_admin, is_manager, create_notification, log_audit

def show_asset_procurement():
    """Main asset procurement interface"""
    user = get_current_user()

    st.markdown("## 💼 Asset Procurement & Management")
    st.markdown("Request, approve, and manage company assets")
    st.markdown("---")

    if is_hr_admin():
        tabs = st.tabs(["📦 All Assets", "⏳ Pending Requests", "✅ Approved Requests", "🛒 Purchase Orders", "📊 Analytics", "➕ Add Asset"])
    elif is_manager():
        tabs = st.tabs(["👥 Team Assets", "⏳ Pending Approval", "➕ New Request"])
    else:
        tabs = st.tabs(["💼 My Assets", "➕ Request Asset", "📋 My Requests"])

    with tabs[0]:
        if is_hr_admin():
            show_all_assets()
        elif is_manager():
            show_team_assets()
        else:
            show_my_assets()

    with tabs[1]:
        if is_hr_admin() or is_manager():
            show_pending_requests()
        else:
            request_asset()

    with tabs[2]:
        if is_hr_admin():
            show_approved_requests()
        else:
            show_my_requests()

    if is_hr_admin() and len(tabs) > 3:
        with tabs[3]:
            show_purchase_orders()
        with tabs[4]:
            show_asset_analytics()
        with tabs[5]:
            add_asset()

def show_all_assets():
    """Show all company assets"""
    st.markdown("### 📦 All Company Assets")

    with get_db_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                a.id,
                a.asset_name,
                a.asset_type,
                a.serial_number,
                a.purchase_date,
                a.purchase_cost,
                a.condition,
                a.status,
                a.assigned_to,
                e.first_name || ' ' || e.last_name as assigned_name
            FROM assets a
            LEFT JOIN employees e ON a.assigned_to = e.id
            ORDER BY a.purchase_date DESC
        """)
        assets = [dict(row) for row in cursor.fetchall()]

    if assets:
        # Filters
        col1, col2, col3 = st.columns(3)
        with col1:
            type_filter = st.selectbox("Asset Type", ["All"] + list(set([a['asset_type'] for a in assets if a['asset_type']])))
        with col2:
            status_filter = st.selectbox("Status", ["All", "Available", "Assigned", "Maintenance", "Retired"])
        with col3:
            condition_filter = st.selectbox("Condition", ["All", "New", "Good", "Fair", "Poor"])

        # Apply filters
        filtered = assets
        if type_filter != "All":
            filtered = [a for a in filtered if a['asset_type'] == type_filter]
        if status_filter != "All":
            filtered = [a for a in filtered if a['status'] == status_filter]
        if condition_filter != "All":
            filtered = [a for a in filtered if a['condition'] == condition_filter]

        st.markdown(f"**Total Assets:** {len(filtered)} | **Total Value:** ${sum([a['purchase_cost'] or 0 for a in filtered]):,.2f}")

        # Display assets
        for asset in filtered:
            status_emoji = {
                'Available': '🟢',
                'Assigned': '🟡',
                'Maintenance': '🔧',
                'Retired': '⚫'
            }.get(asset['status'], '🔵')

            with st.expander(f"{status_emoji} {asset['asset_name']} ({asset['asset_type']}) - {asset['status']}"):
                col1, col2 = st.columns([2, 1])

                with col1:
                    st.markdown(f"""
                    **Asset:** {asset['asset_name']}
                    **Type:** {asset['asset_type']}
                    **Serial #:** {asset['serial_number'] or 'N/A'}
                    **Condition:** {asset['condition']}
                    **Status:** {asset['status']}
                    **Assigned To:** {asset['assigned_name'] or 'Unassigned'}
                    **Purchase Date:** {asset['purchase_date']}
                    **Purchase Cost:** ${asset['purchase_cost'] or 0:,.2f}
                    """)

                with col2:
                    st.metric("Value", f"${asset['purchase_cost'] or 0:,.2f}")
                    st.metric("Condition", asset['condition'])

                # Actions
                st.markdown("---")
                col1, col2, col3 = st.columns(3)

                with col1:
                    if asset['status'] == 'Available':
                        if st.button("👤 Assign", key=f"assign_{asset['id']}", use_container_width=True):
                            st.session_state[f'assigning_{asset["id"]}'] = True
                            st.rerun()

                with col2:
                    if st.button("🔧 Maintenance", key=f"maint_{asset['id']}", use_container_width=True):
                        mark_maintenance(asset['id'])
                        st.rerun()

                with col3:
                    if asset['assigned_to']:
                        if st.button("↩️ Return", key=f"return_{asset['id']}", use_container_width=True):
                            return_asset(asset['id'])
                            st.rerun()

                # Assignment form
                if st.session_state.get(f'assigning_{asset["id"]}', False):
                    st.markdown("### Assign Asset")
                    with get_db_connection() as conn:
                        cursor = conn.cursor()
                        cursor.execute("SELECT id, employee_id, first_name, last_name FROM employees WHERE status = 'Active'")
                        employees = [dict(row) for row in cursor.fetchall()]

                    emp_options = {f"{e['employee_id']} - {e['first_name']} {e['last_name']}": e['id'] for e in employees}
                    selected_emp = st.selectbox("Select Employee", options=list(emp_options.keys()), key=f"select_emp_{asset['id']}")

                    if st.button("✅ Confirm Assignment", key=f"confirm_{asset['id']}"):
                        emp_id = emp_options[selected_emp]
                        assign_asset(asset['id'], emp_id)
                        del st.session_state[f'assigning_{asset["id"]}']
                        st.rerun()
    else:
        st.info("No assets found")

def show_pending_requests():
    """Show pending asset requests"""
    user = get_current_user()
    st.markdown("### ⏳ Pending Asset Requests")

    with get_db_connection() as conn:
        cursor = conn.cursor()

        if is_hr_admin():
            # HR sees all pending
            cursor.execute("""
                SELECT
                    ar.id,
                    ar.emp_id,
                    e.employee_id,
                    e.first_name || ' ' || e.last_name as requester_name,
                    e.department,
                    ar.asset_type,
                    ar.justification,
                    ar.status,
                    ar.requested_date
                FROM asset_requests ar
                JOIN employees e ON ar.emp_id = e.id
                WHERE ar.status IN ('Pending', 'Manager Approved')
                ORDER BY ar.requested_date ASC
            """)
        else:
            # Manager sees team requests
            cursor.execute("""
                SELECT
                    ar.id,
                    ar.emp_id,
                    e.id as employee_id,
                    e.first_name || ' ' || e.last_name as requester_name,
                    ar.asset_type,
                    ar.asset_description,
                    ar.justification,
                    ar.estimated_cost,
                    ar.urgency,
                    ar.status,
                    ar.requested_date
                FROM asset_requests ar
                JOIN employees e ON ar.emp_id = e.id
                WHERE ar.status = 'Pending'
                AND e.manager_id = %s
                ORDER BY ar.requested_date ASC
            """, (user['employee_id'],))

        pending = [dict(row) for row in cursor.fetchall()]

    if pending:
        st.info(f"📋 {len(pending)} request(s) awaiting approval")

        for req in pending:
            urgency_color = {
                'Low': 'rgba(45, 212, 170, 0.1)',
                'Medium': 'rgba(240, 180, 41, 0.1)',
                'High': 'rgba(255, 193, 7, 0.1)',
                'Critical': 'rgba(241, 100, 100, 0.1)'
            }.get(req['urgency'], 'rgba(58, 123, 213, 0.05)')

            urgency_emoji = {'Low': '🟢', 'Medium': '🟡', 'High': '🟠', 'Critical': '🔴'}.get(req['urgency'], '🔵')

            with st.expander(f"{urgency_emoji} {req['requester_name']} - {req['asset_type']} - {req['urgency']} Priority"):
                st.markdown(f"""
                **Requester:** {req['requester_name']} ({req['employee_id']})
                **Department:** {req.get('department', 'N/A')}
                **Asset Type:** {req['asset_type']}
                **Description:** {req['asset_description']}
                **Justification:** {req['justification']}
                **Estimated Cost:** ${req['estimated_cost']:,.2f}
                **Urgency:** {req['urgency']}
                **Status:** {req['status']}
                **Requested:** {req['requested_date']}
                """)

                if req.get('manager_status') == 'Approved' and is_hr_admin():
                    st.success("✅ Manager has approved this request")

                # Approval actions
                st.markdown("---")
                approval_comments = st.text_area("Comments", key=f"comments_{req['id']}",
                                                placeholder="Add approval/rejection comments...")

                col1, col2 = st.columns(2)

                with col1:
                    if st.button("✅ Approve", key=f"approve_req_{req['id']}", use_container_width=True, type="primary"):
                        approve_asset_request(req['id'], req['emp_id'], approval_comments)
                        st.rerun()

                with col2:
                    if st.button("❌ Reject", key=f"reject_req_{req['id']}", use_container_width=True):
                        if approval_comments:
                            reject_asset_request(req['id'], req['emp_id'], approval_comments)
                            st.rerun()
                        else:
                            st.error("Please provide rejection reason")
    else:
        st.success("✅ No pending asset requests!")

def request_asset():
    """Employee asset request form"""
    user = get_current_user()
    st.markdown("### ➕ Request New Asset")

    with st.form("asset_request_form"):
        st.info("📝 Submit a request for new equipment or assets")

        col1, col2 = st.columns(2)

        with col1:
            asset_type = st.selectbox("Asset Type *", [
                "Laptop",
                "Desktop Computer",
                "Monitor",
                "Mobile Phone",
                "Tablet",
                "Keyboard",
                "Mouse",
                "Headset",
                "Webcam",
                "Printer",
                "Office Chair",
                "Desk",
                "Software License",
                "Other Equipment"
            ])

            asset_description = st.text_area("Description *",
                                            placeholder="Detailed description of the asset needed...")

            justification = st.text_area("Business Justification *",
                                        placeholder="Explain why this asset is needed...")

        with col2:
            estimated_cost = st.number_input("Estimated Cost ($) *", min_value=0.0, step=10.0)

            urgency = st.selectbox("Urgency *", ["Low", "Medium", "High", "Critical"])

            preferred_vendor = st.text_input("Preferred Vendor (Optional)",
                                           placeholder="e.g., Dell, Apple, HP")

            required_by_date = st.date_input("Required By", value=date.today() + timedelta(days=30))

        additional_notes = st.text_area("Additional Notes",
                                       placeholder="Any other relevant information...")

        submitted = st.form_submit_button("📤 Submit Request", use_container_width=True)

        if submitted and asset_type and asset_description and justification:
            try:
                with get_db_connection() as conn:
                    cursor = conn.cursor()

                    cursor.execute("""
                        INSERT INTO asset_requests (
                            emp_id, asset_type, asset_description, justification,
                            estimated_cost, urgency, preferred_vendor,
                            required_by_date, additional_notes, status, requested_date
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'Pending', %s)
                    """, (user['employee_id'], asset_type, asset_description, justification,
                         estimated_cost, urgency, preferred_vendor,
                         required_by_date.isoformat(), additional_notes,
                         datetime.now().isoformat()))

                    request_id = cursor.lastrowid

                    # Notify manager
                    cursor.execute("SELECT manager_id FROM employees WHERE id = %s", (user['employee_id'],))
                    result = cursor.fetchone()

                    if result and result['manager_id']:
                        create_notification(
                            result['manager_id'],
                            "Asset Request Approval Required",
                            f"{user['full_name']} requested {asset_type} - {urgency} priority (Request ID: {request_id})",
                            'info'
                        )

                    conn.commit()
                    log_audit(f"Submitted asset request {request_id} for {asset_type}", "asset_requests", request_id)
                    st.success(f"✅ Asset request submitted! Request ID: {request_id}")

            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
        elif submitted:
            st.error("Please fill all required fields")

def approve_asset_request(request_id, emp_id, comments=None):
    """Approve asset request"""
    user = get_current_user()

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # Get request details
            cursor.execute("SELECT asset_type, urgency FROM asset_requests WHERE id = %s", (request_id,))
            req = dict(cursor.fetchone())

            if is_manager():
                # Manager approval
                cursor.execute("""
                    UPDATE asset_requests SET
                        manager_status = 'Approved',
                        manager_id = %s,
                        manager_approval_date = %s,
                        manager_comments = %s,
                        status = 'Manager Approved'
                    WHERE id = %s
                """, (user['employee_id'], datetime.now().isoformat(), comments, request_id))

                # Notify HR
                create_notification(
                    None,
                    "Asset Request - HR Approval Required",
                    f"Manager approved asset request for {req['asset_type']} (Request ID: {request_id})",
                    'info',
                    is_hr_notification=True
                )

                st.success("✅ Request approved! Forwarded to HR for procurement.")

            elif is_hr_admin():
                # HR approval - create purchase order
                cursor.execute("""
                    UPDATE asset_requests SET
                        hr_status = 'Approved',
                        hr_id = %s,
                        hr_approval_date = %s,
                        hr_comments = %s,
                        status = 'Approved - Procurement'
                    WHERE id = %s
                """, (user['employee_id'], datetime.now().isoformat(), comments, request_id))

                # Notify requester
                create_notification(
                    emp_id,
                    "Asset Request Approved",
                    f"Your asset request for {req['asset_type']} has been approved and is being procured.",
                    'success'
                )

                st.success("✅ Request approved! Ready for procurement.")

            conn.commit()
            log_audit(f"Approved asset request {request_id}", "asset_requests", request_id)

    except Exception as e:
        st.error(f"❌ Error: {str(e)}")

def reject_asset_request(request_id, emp_id, reason):
    """Reject asset request"""
    user = get_current_user()

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT asset_type FROM asset_requests WHERE id = %s", (request_id,))
            req = dict(cursor.fetchone())

            if is_manager():
                cursor.execute("""
                    UPDATE asset_requests SET
                        manager_status = 'Rejected',
                        manager_id = %s,
                        manager_approval_date = %s,
                        manager_comments = %s,
                        status = 'Rejected'
                    WHERE id = %s
                """, (user['employee_id'], datetime.now().isoformat(), reason, request_id))
            elif is_hr_admin():
                cursor.execute("""
                    UPDATE asset_requests SET
                        hr_status = 'Rejected',
                        hr_id = %s,
                        hr_approval_date = %s,
                        hr_comments = %s,
                        status = 'Rejected'
                    WHERE id = %s
                """, (user['employee_id'], datetime.now().isoformat(), reason, request_id))

            # Notify requester
            create_notification(
                emp_id,
                "Asset Request Rejected",
                f"Your asset request for {req['asset_type']} was not approved. Reason: {reason}",
                'warning'
            )

            conn.commit()
            log_audit(f"Rejected asset request {request_id}. Reason: {reason}", "asset_requests", request_id)
            st.warning("⚠️ Request rejected")

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
                    assigned_date = %s,
                    status = 'Assigned'
                WHERE id = %s
            """, (emp_id, datetime.now().isoformat(), asset_id))

            # Notify employee
            cursor.execute("SELECT asset_name FROM assets WHERE id = %s", (asset_id,))
            asset = dict(cursor.fetchone())

            create_notification(
                emp_id,
                "Asset Assigned",
                f"Asset '{asset['asset_name']}' has been assigned to you. Please confirm receipt.",
                'info'
            )

            conn.commit()
            log_audit(f"Assigned asset {asset_id} to employee {emp_id}", "assets", asset_id)
            st.success("✅ Asset assigned successfully!")

    except Exception as e:
        st.error(f"❌ Error: {str(e)}")

def return_asset(asset_id):
    """Return asset"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                UPDATE assets SET
                    assigned_to = NULL,
                    return_date = %s,
                    status = 'Available'
                WHERE id = %s
            """, (datetime.now().isoformat(), asset_id))

            conn.commit()
            log_audit(f"Returned asset {asset_id}", "assets", asset_id)
            st.success("✅ Asset returned and now available")

    except Exception as e:
        st.error(f"❌ Error: {str(e)}")

def mark_maintenance(asset_id):
    """Mark asset for maintenance"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("UPDATE assets SET status = 'Maintenance' WHERE id = %s", (asset_id,))

            conn.commit()
            log_audit(f"Marked asset {asset_id} for maintenance", "assets", asset_id)
            st.info("🔧 Asset marked for maintenance")

    except Exception as e:
        st.error(f"❌ Error: {str(e)}")

def show_my_assets():
    """Show employee's assigned assets"""
    user = get_current_user()
    st.markdown("### 💼 My Assigned Assets")

    with get_db_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM assets
            WHERE assigned_to = %s
            ORDER BY assigned_date DESC
        """, (user['employee_id'],))
        assets = [dict(row) for row in cursor.fetchall()]

    if assets:
        for asset in assets:
            st.markdown(f"""
            **{asset['asset_name']}** ({asset['asset_type']})
            - Serial #: {asset['serial_number'] or 'N/A'}
            - Condition: {asset['condition']}
            - Assigned: {asset['assigned_date']}
            """)
    else:
        st.info("No assets assigned to you")

def show_my_requests():
    """Show employee's asset requests"""
    user = get_current_user()
    st.markdown("### 📋 My Asset Requests")

    with get_db_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM asset_requests
            WHERE emp_id = %s
            ORDER BY requested_date DESC
        """, (user['employee_id'],))
        requests = [dict(row) for row in cursor.fetchall()]

    if requests:
        for req in requests:
            status_emoji = {'Pending': '⏳', 'Manager Approved': '👍', 'Approved - Procurement': '✅', 'Rejected': '❌'}.get(req['status'], '🔵')
            st.markdown(f"{status_emoji} **{req['asset_type']}** - {req['status']} (Requested: {req['requested_date']})")
    else:
        st.info("No asset requests")

def show_approved_requests():
    """Show approved requests for procurement"""
    st.markdown("### ✅ Approved Requests - Ready for Procurement")

    with get_db_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                ar.*,
                e.first_name || ' ' || e.last_name as requester_name
            FROM asset_requests ar
            JOIN employees e ON ar.emp_id = e.id
            WHERE ar.status = 'Approved - Procurement'
            ORDER BY ar.urgency DESC, ar.requested_date ASC
        """)
        approved = [dict(row) for row in cursor.fetchall()]

    if approved:
        for req in approved:
            st.markdown(f"🛒 **{req['asset_type']}** for {req['requester_name']} - ${req['estimated_cost']:,.2f}")
    else:
        st.info("No approved requests pending procurement")

def show_purchase_orders():
    """Show purchase orders"""
    st.markdown("### 🛒 Purchase Orders")
    st.info("Purchase order management - Coming soon")

def show_asset_analytics():
    """Show asset analytics"""
    st.markdown("### 📊 Asset Analytics")

    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Overall stats
        cursor.execute("""
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN status = 'Available' THEN 1 ELSE 0 END) as available,
                SUM(CASE WHEN status = 'Assigned' THEN 1 ELSE 0 END) as assigned,
                SUM(CASE WHEN status = 'Maintenance' THEN 1 ELSE 0 END) as maintenance,
                SUM(purchase_cost) as total_value
            FROM assets
        """)
        stats = dict(cursor.fetchone())

        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            st.metric("Total Assets", stats['total'] or 0)
        with col2:
            st.metric("Available", stats['available'] or 0)
        with col3:
            st.metric("Assigned", stats['assigned'] or 0)
        with col4:
            st.metric("Maintenance", stats['maintenance'] or 0)
        with col5:
            st.metric("Total Value", f"${stats['total_value'] or 0:,.0f}")

        st.markdown("---")

        # By asset type
        st.markdown("#### By Asset Type")
        cursor.execute("""
            SELECT
                asset_type,
                COUNT(*) as count,
                SUM(CASE WHEN status = 'Assigned' THEN 1 ELSE 0 END) as assigned,
                SUM(purchase_cost) as value
            FROM assets
            GROUP BY asset_type
            ORDER BY count DESC
        """)
        by_type = [dict(row) for row in cursor.fetchall()]

        for atype in by_type:
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                st.markdown(f"**{atype['asset_type']}**")
            with col2:
                st.markdown(f"Total: {atype['count']} ({atype['assigned']} assigned)")
            with col3:
                st.markdown(f"Value: ${atype['value'] or 0:,.0f}")

def add_asset():
    """Add new asset to inventory"""
    st.markdown("### ➕ Add Asset to Inventory")

    with st.form("add_asset_form"):
        col1, col2 = st.columns(2)

        with col1:
            asset_name = st.text_input("Asset Name *", placeholder="e.g., MacBook Pro 16\"")
            asset_type = st.selectbox("Asset Type *", [
                "Laptop", "Desktop Computer", "Monitor", "Mobile Phone",
                "Tablet", "Keyboard", "Mouse", "Headset", "Webcam",
                "Printer", "Office Chair", "Desk", "Software License", "Other"
            ])
            serial_number = st.text_input("Serial Number", placeholder="Unique identifier")

        with col2:
            purchase_date = st.date_input("Purchase Date *", value=date.today())
            purchase_cost = st.number_input("Purchase Cost ($) *", min_value=0.0, step=10.0)
            condition = st.selectbox("Condition *", ["New", "Good", "Fair", "Poor"])

        submitted = st.form_submit_button("💾 Add Asset", use_container_width=True)

        if submitted and asset_name and asset_type:
            try:
                with get_db_connection() as conn:
                    cursor = conn.cursor()

                    cursor.execute("""
                        INSERT INTO assets (
                            asset_name, asset_type, serial_number,
                            purchase_date, purchase_cost, condition, status
                        ) VALUES (%s, %s, %s, %s, %s, %s, 'Available')
                    """, (asset_name, asset_type, serial_number,
                         purchase_date.isoformat(), purchase_cost, condition))

                    asset_id = cursor.lastrowid

                    conn.commit()
                    log_audit(f"Added asset {asset_id}: {asset_name}", "assets", asset_id)
                    st.success(f"✅ Asset added to inventory! ID: {asset_id}")

            except Exception as e:
                st.error(f"❌ Error: {str(e)}")

def show_team_assets():
    """Show team assets for managers"""
    user = get_current_user()
    st.markdown("### 👥 Team Assets")

    with get_db_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                a.*,
                e.id as employee_id,
                e.first_name || ' ' || e.last_name as emp_name
            FROM assets a
            JOIN employees e ON a.assigned_to = e.id
            WHERE e.manager_id = %s
            ORDER BY a.assigned_date DESC
        """, (user['employee_id'],))
        assets = [dict(row) for row in cursor.fetchall()]

    if assets:
        for asset in assets:
            st.markdown(f"💼 **{asset['emp_name']}** - {asset['asset_name']} ({asset['asset_type']})")
    else:
        st.info("No assets assigned to team members")
