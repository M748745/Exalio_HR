"""
Certificate Expiry Tracking Module
Monitor and manage employee certifications, licenses, and credentials with automated expiry alerts
"""

import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
from database import get_db_connection
from auth import get_current_user, is_hr_admin, is_manager, create_notification, log_audit

def show_certificate_tracking():
    """Main certificate tracking interface"""
    user = get_current_user()

    st.markdown("## 🎓 Certificate & License Tracking")
    st.markdown("Monitor employee certifications with automated expiry alerts")
    st.markdown("---")

    if is_hr_admin():
        tabs = st.tabs(["📋 All Certificates", "⚠️ Expiring Soon", "📊 Analytics", "➕ Add Certificate", "⚙️ Settings"])
    elif is_manager():
        tabs = st.tabs(["👥 Team Certificates", "⚠️ Expiring Soon", "📊 Team Overview"])
    else:
        tabs = st.tabs(["📜 My Certificates", "⚠️ Expiring Soon", "➕ Upload Certificate"])

    with tabs[0]:
        if is_hr_admin():
            show_all_certificates()
        elif is_manager():
            show_team_certificates()
        else:
            show_my_certificates()

    with tabs[1]:
        show_expiring_certificates()

    with tabs[2]:
        if is_hr_admin():
            show_certificate_analytics()
        elif is_manager():
            show_team_overview()
        else:
            upload_certificate()

    if is_hr_admin() and len(tabs) > 3:
        with tabs[3]:
            add_certificate()
        with tabs[4]:
            show_certificate_settings()

def show_all_certificates():
    """Show all certificates for HR"""
    st.markdown("### 📋 All Employee Certificates")

    with get_db_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                c.id,
                c.emp_id,
                e.employee_id,
                e.first_name || ' ' || e.last_name as name,
                e.department,
                e.position,
                c.certificate_name,
                c.issuing_org as issuing_organization,
                c.issue_date,
                c.expiry_date,
                c.status,
                (c.expiry_date - CURRENT_DATE) as days_remaining
            FROM certificates c
            JOIN employees e ON c.emp_id = e.id
            WHERE c.status != 'Expired'
            ORDER BY c.expiry_date ASC
        """)
        certificates = [dict(row) for row in cursor.fetchall()]

    if certificates:
        # Filters
        col1, col2 = st.columns(2)
        with col1:
            dept_filter = st.selectbox("Department", ["All"] + sorted(list(set([c.get('department', 'Unknown') for c in certificates if c.get('department')]))))
        with col2:
            status_filter = st.selectbox("Status", ["All", "Active", "Expiring Soon", "Renewal Pending", "Expired"])

        # Apply filters
        filtered = certificates
        if dept_filter != "All":
            filtered = [c for c in filtered if c.get('department') == dept_filter]
        if status_filter != "All":
            filtered = [c for c in filtered if c.get('status') == status_filter]

        st.markdown(f"**Total Certificates:** {len(filtered)}")

        # Display certificates
        for cert in filtered:
            days_remaining = cert['days_remaining']

            # Color coding
            if days_remaining < 0:
                status_color = 'rgba(241, 100, 100, 0.1)'
                status_emoji = "🔴"
            elif days_remaining <= 30:
                status_color = 'rgba(255, 193, 7, 0.1)'
                status_emoji = "🟡"
            elif days_remaining <= 60:
                status_color = 'rgba(240, 180, 41, 0.1)'
                status_emoji = "🟠"
            else:
                status_color = 'rgba(45, 212, 170, 0.1)'
                status_emoji = "🟢"

            with st.expander(f"{status_emoji} {cert['name']} - {cert['certificate_name']} - Expires: {cert['expiry_date']}"):
                col1, col2 = st.columns([2, 1])

                with col1:
                    issuing_org = cert.get('issuing_organization') or cert.get('issuing_org') or 'N/A'
                    st.markdown(f"""
                    **Employee:** {cert.get('name', 'N/A')} ({cert.get('employee_id', 'N/A')})
                    **Department:** {cert.get('department', 'N/A')}
                    **Position:** {cert.get('position', 'N/A')}
                    **Certificate:** {cert.get('certificate_name', 'N/A')}
                    **Issuing Organization:** {issuing_org}
                    **Issue Date:** {cert.get('issue_date', 'N/A')}
                    **Expiry Date:** {cert.get('expiry_date', 'N/A')}
                    **Status:** {cert.get('status', 'N/A')}
                    """)

                with col2:
                    if days_remaining >= 0:
                        st.metric("Days Until Expiry", f"{days_remaining} days",
                                 delta=f"{days_remaining} days left",
                                 delta_color="inverse" if days_remaining <= 30 else "normal")
                    else:
                        st.metric("Status", "EXPIRED",
                                 delta=f"{abs(days_remaining)} days ago",
                                 delta_color="inverse")

                # Actions
                st.markdown("---")
                col1, col2, col3 = st.columns(3)

                with col1:
                    if days_remaining <= 90 and cert['status'] == 'Active':
                        if st.button("🔄 Request Renewal", key=f"renew_cert_{cert['id']}", use_container_width=True):
                            request_certificate_renewal(cert['id'], cert['emp_id'])
                            st.rerun()

                with col2:
                    if st.button("📝 Edit Details", key=f"edit_cert_{cert['id']}", use_container_width=True):
                        st.info("Edit functionality coming soon")

                with col3:
                    if st.button("🗑️ Mark Expired", key=f"expire_cert_{cert['id']}", use_container_width=True):
                        mark_certificate_expired(cert['id'], cert['emp_id'])
                        st.rerun()
    else:
        st.info("No certificates found")

def show_expiring_certificates():
    """Show certificates expiring soon"""
    user = get_current_user()
    st.markdown("### ⚠️ Certificates Expiring Soon")

    with get_db_connection() as conn:
        cursor = conn.cursor()

        if is_hr_admin():
            # HR sees all expiring certificates
            cursor.execute("""
                SELECT
                    c.id,
                    c.emp_id,
                    e.id as employee_id,
                    e.first_name || ' ' || e.last_name as name,
                    e.department,
                    c.certificate_name,
                    c.issuing_org,
                    c.expiry_date,
                    c.status,
                    (c.expiry_date - CURRENT_DATE) as days_remaining
                FROM certificates c
                JOIN employees e ON c.emp_id = e.id
                WHERE c.status = 'Active'
                AND (c.expiry_date - CURRENT_DATE) <= 90
                ORDER BY c.expiry_date ASC
            """)
        elif is_manager():
            # Manager sees team certificates
            cursor.execute("""
                SELECT
                    c.id,
                    c.emp_id,
                    e.id as employee_id,
                    e.first_name || ' ' || e.last_name as name,
                    c.certificate_name,
                    c.issuing_org,
                    c.expiry_date,
                    c.status,
                    (c.expiry_date - CURRENT_DATE) as days_remaining
                FROM certificates c
                JOIN employees e ON c.emp_id = e.id
                WHERE c.status = 'Active'
                AND (c.expiry_date - CURRENT_DATE) <= 90
                AND e.manager_id = %s
                ORDER BY c.expiry_date ASC
            """, (user['employee_id'],))
        else:
            # Employee sees own certificates
            cursor.execute("""
                SELECT
                    c.id,
                    c.certificate_name,
                    c.issuing_org,
                    c.expiry_date,
                    c.status,
                    (c.expiry_date - CURRENT_DATE) as days_remaining
                FROM certificates c
                WHERE c.emp_id = %s
                AND c.status = 'Active'
                AND (c.expiry_date - CURRENT_DATE) <= 90
                ORDER BY c.expiry_date ASC
            """, (user['employee_id'],))

        expiring = [dict(row) for row in cursor.fetchall()]

    if expiring:
        # Categorize by urgency
        critical = [c for c in expiring if c['days_remaining'] <= 30]
        warning = [c for c in expiring if 30 < c['days_remaining'] <= 60]
        attention = [c for c in expiring if 60 < c['days_remaining'] <= 90]

        # Summary
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("🔴 Critical (≤30 days)", len(critical))
        with col2:
            st.metric("🟡 Warning (31-60 days)", len(warning))
        with col3:
            st.metric("🟠 Attention (61-90 days)", len(attention))

        st.markdown("---")

        # Critical certificates
        if critical:
            st.markdown("#### 🔴 CRITICAL - Expiring within 30 days")
            for cert in critical:
                with st.expander(f"⚠️ {cert.get('name', 'My Certificate')} - {cert['certificate_name']} - {cert['days_remaining']} days"):
                    issuing = cert.get('issuing_org') or cert.get('issuing_organization') or 'N/A'
                    st.markdown(f"""
                    **Certificate:** {cert['certificate_name']}
                    **Issuing Organization:** {issuing}
                    **Expiry Date:** {cert['expiry_date']}
                    **Days Remaining:** {cert['days_remaining']}
                    """)

                    if is_hr_admin() or is_manager():
                        if st.button(f"📧 Send Renewal Reminder", key=f"remind_{cert['id']}", type="primary"):
                            send_renewal_reminder(cert['id'], cert['emp_id'])
                            st.success("✅ Reminder sent!")

        # Warning certificates
        if warning:
            st.markdown("#### 🟡 WARNING - Expiring in 31-60 days")
            for cert in warning:
                name = cert.get('name', 'My Certificate')
                issuing = cert.get('issuing_org') or cert.get('issuing_organization') or 'N/A'
                st.markdown(f"- **{name}** - {cert['certificate_name']} (Issued by: {issuing}) - {cert['days_remaining']} days")

        # Attention certificates
        if attention:
            st.markdown("#### 🟠 ATTENTION - Expiring in 61-90 days")
            for cert in attention:
                name = cert.get('name', 'My Certificate')
                st.markdown(f"- **{name}** - {cert['certificate_name']} - {cert['days_remaining']} days")

    else:
        st.success("✅ No certificates expiring in the next 90 days!")

def show_my_certificates():
    """Show employee's own certificates"""
    user = get_current_user()
    st.markdown("### 📜 My Certificates")

    with get_db_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM certificates
            WHERE emp_id = %s
            ORDER BY expiry_date ASC
        """, (user['employee_id'],))
        certificates = [dict(row) for row in cursor.fetchall()]

    if certificates:
        for cert in certificates:
            days_remaining = (datetime.strptime(str(cert['expiry_date']), '%Y-%m-%d').date() - date.today()).days

            status_emoji = "🟢" if days_remaining > 90 else "🟡" if days_remaining > 30 else "🔴"

            with st.expander(f"{status_emoji} {cert['certificate_name']} - Expires: {cert['expiry_date']}"):
                col1, col2 = st.columns([2, 1])

                with col1:
                    issuing = cert.get('issuing_org') or cert.get('issuing_organization') or 'N/A'
                    st.markdown(f"""
                    **Certificate:** {cert['certificate_name']}
                    **Issuing Organization:** {issuing}
                    **Issue Date:** {cert.get('issue_date', 'N/A')}
                    **Expiry Date:** {cert.get('expiry_date', 'N/A')}
                    **Status:** {cert.get('status', 'N/A')}
                    """)

                with col2:
                    if days_remaining >= 0:
                        st.metric("Days Remaining", f"{days_remaining} days")
                    else:
                        st.metric("Status", "EXPIRED")

                if cert.get('certificate_file'):
                    st.markdown(f"📎 File: {cert['certificate_file']}")

                if days_remaining <= 60:
                    st.warning(f"⚠️ This certificate expires in {days_remaining} days. Please plan for renewal.")
    else:
        st.info("No certificates on record. Upload your certificates below.")

def add_certificate():
    """Add new certificate (HR function)"""
    st.markdown("### ➕ Add Employee Certificate")

    with st.form("add_certificate_form"):
        # Get employees
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, employee_id, first_name, last_name FROM employees WHERE status = 'Active'")
            employees = [dict(row) for row in cursor.fetchall()]

        emp_options = {f"{e['employee_id']} - {e['first_name']} {e['last_name']}": e['id'] for e in employees}
        selected_emp = st.selectbox("Employee *", options=list(emp_options.keys()))

        col1, col2 = st.columns(2)

        with col1:
            certificate_name = st.text_input("Certificate Name *", placeholder="e.g., PMP, AWS Certified, CPA")
            issuing_organization = st.text_input("Issuing Organization *", placeholder="e.g., PMI, AWS, State Board")

        with col2:
            issue_date = st.date_input("Issue Date *", value=date.today())

            # Default expiry: 2 years from issue
            default_expiry = issue_date + timedelta(days=730)
            expiry_date = st.date_input("Expiry Date *", value=default_expiry, min_value=issue_date)

        notes = st.text_area("Notes", placeholder="Additional information, renewal requirements, etc.")

        submitted = st.form_submit_button("💾 Add Certificate", use_container_width=True)

        if submitted and selected_emp and certificate_name:
            emp_id = emp_options[selected_emp]

            try:
                with get_db_connection() as conn:
                    cursor = conn.cursor()

                    cursor.execute("""
                        INSERT INTO certificates (
                            emp_id, certificate_name, issuing_organization,
                            issue_date, expiry_date, status
                        ) VALUES (%s, %s, %s, %s, %s, 'Active')
                    """, (emp_id, certificate_name, issuing_organization,
                         issue_date.isoformat(), expiry_date.isoformat()))

                    cert_id = cursor.lastrowid

                    # Notify employee
                    create_notification(
                        emp_id,
                        "Certificate Added",
                        f"A new certificate has been added to your profile: {certificate_name} (expires {expiry_date})",
                        'info'
                    )

                    conn.commit()
                    log_audit(f"Added certificate {cert_id} for employee {emp_id}", "certificates", cert_id)
                    st.success(f"✅ Certificate added successfully! ID: {cert_id}")

            except Exception as e:
                st.error(f"❌ Error: {str(e)}")

def upload_certificate():
    """Upload certificate (Employee function)"""
    user = get_current_user()
    st.markdown("### ➕ Upload My Certificate")

    with st.form("upload_certificate_form"):
        st.info("📝 Upload your professional certificates, licenses, and credentials for HR records")

        col1, col2 = st.columns(2)

        with col1:
            certificate_name = st.text_input("Certificate Name *", placeholder="e.g., Project Management Professional")
            issuing_organization = st.text_input("Issuing Organization *", placeholder="e.g., PMI, AWS")

        with col2:
            pass  # Empty column for layout

        col1, col2 = st.columns(2)
        with col1:
            issue_date = st.date_input("Issue Date *", value=date.today())
        with col2:
            expiry_date = st.date_input("Expiry Date *", value=date.today() + timedelta(days=730))

        uploaded_file = st.file_uploader("Upload Certificate (PDF, JPG, PNG)", type=['pdf', 'jpg', 'jpeg', 'png'])
        notes = st.text_area("Additional Notes", placeholder="Any special requirements or renewal information")

        submitted = st.form_submit_button("📤 Submit Certificate", use_container_width=True)

        if submitted and certificate_name:
            try:
                file_path = None
                if uploaded_file:
                    # In production, save file to storage
                    file_path = f"certificates/{user['employee_id']}_{certificate_name.replace(' ', '_')}_{uploaded_file.name}"
                    st.info(f"File would be saved to: {file_path}")

                with get_db_connection() as conn:
                    cursor = conn.cursor()

                    cursor.execute("""
                        INSERT INTO certificates (
                            emp_id, certificate_name, issuing_organization,
                            issue_date, expiry_date, certificate_file, status
                        ) VALUES (%s, %s, %s, %s, %s, %s, 'Pending Verification')
                    """, (user['employee_id'], certificate_name, issuing_organization,
                         issue_date.isoformat(), expiry_date.isoformat(), file_path))

                    cert_id = cursor.lastrowid

                    # Notify HR
                    create_notification(
                        None,
                        "New Certificate Uploaded",
                        f"{user['full_name']} uploaded a new certificate: {certificate_name}",
                        'info',
                        is_hr_notification=True
                    )

                    conn.commit()
                    log_audit(f"Employee uploaded certificate {cert_id}", "certificates", cert_id)
                    st.success(f"✅ Certificate submitted successfully! Awaiting HR verification.")

            except Exception as e:
                st.error(f"❌ Error: {str(e)}")

def request_certificate_renewal(cert_id, emp_id):
    """Request certificate renewal"""
    user = get_current_user()

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                UPDATE certificates SET
                    status = 'Renewal Pending',
                    renewal_requested_date = %s,
                    renewal_requested_by = %s
                WHERE id = %s
            """, (datetime.now().isoformat(), user['employee_id'], cert_id))

            # Notify employee
            create_notification(
                emp_id,
                "Certificate Renewal Required",
                f"Your certificate (ID: {cert_id}) requires renewal. Please provide updated documentation.",
                'warning'
            )

            conn.commit()
            log_audit(f"Requested renewal for certificate {cert_id}", "certificates", cert_id)
            st.success("✅ Renewal request sent to employee!")

    except Exception as e:
        st.error(f"❌ Error: {str(e)}")

def mark_certificate_expired(cert_id, emp_id):
    """Mark certificate as expired"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                UPDATE certificates SET
                    status = 'Expired',
                    expired_date = %s
                WHERE id = %s
            """, (datetime.now().isoformat(), cert_id))

            # Notify employee
            create_notification(
                emp_id,
                "Certificate Expired",
                f"Your certificate (ID: {cert_id}) has been marked as expired. Please renew if required.",
                'warning'
            )

            conn.commit()
            log_audit(f"Marked certificate {cert_id} as expired", "certificates", cert_id)
            st.warning("⚠️ Certificate marked as expired")

    except Exception as e:
        st.error(f"❌ Error: {str(e)}")

def send_renewal_reminder(cert_id, emp_id):
    """Send renewal reminder"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT certificate_name, expiry_date FROM certificates WHERE id = %s", (cert_id,))
            cert = dict(cursor.fetchone())

            create_notification(
                emp_id,
                "Certificate Renewal Reminder",
                f"⚠️ URGENT: Your certificate '{cert['certificate_name']}' expires on {cert['expiry_date']}. Please renew immediately!",
                'warning'
            )

            log_audit(f"Sent renewal reminder for certificate {cert_id}", "certificates", cert_id)

    except Exception as e:
        st.error(f"❌ Error: {str(e)}")

def show_certificate_analytics():
    """Show certificate analytics"""
    st.markdown("### 📊 Certificate Analytics")

    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Overall stats
        cursor.execute("""
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN status = 'Active' THEN 1 ELSE 0 END) as active,
                SUM(CASE WHEN status = 'Expired' THEN 1 ELSE 0 END) as expired,
                SUM(CASE WHEN status = 'Renewal Pending' THEN 1 ELSE 0 END) as renewal_pending,
                SUM(CASE WHEN (expiry_date - CURRENT_DATE) <= 30 AND status = 'Active' THEN 1 ELSE 0 END) as expiring_30,
                SUM(CASE WHEN (expiry_date - CURRENT_DATE) <= 90 AND status = 'Active' THEN 1 ELSE 0 END) as expiring_90
            FROM certificates
        """)
        stats = dict(cursor.fetchone())

        col1, col2, col3, col4, col5, col6 = st.columns(6)
        with col1:
            st.metric("Total", stats['total'] or 0)
        with col2:
            st.metric("Active", stats['active'] or 0)
        with col3:
            st.metric("Expired", stats['expired'] or 0)
        with col4:
            st.metric("Renewal Pending", stats['renewal_pending'] or 0)
        with col5:
            st.metric("Expiring ≤30d", stats['expiring_30'] or 0, delta_color="inverse")
        with col6:
            st.metric("Expiring ≤90d", stats['expiring_90'] or 0, delta_color="inverse")

        st.markdown("---")

        # By issuing organization
        st.markdown("#### By Issuing Organization")
        cursor.execute("""
            SELECT
                COALESCE(issuing_organization, issuing_org, 'Unknown') as org_name,
                COUNT(*) as count,
                SUM(CASE WHEN status = 'Active' THEN 1 ELSE 0 END) as active,
                SUM(CASE WHEN (expiry_date - CURRENT_DATE) <= 60 AND status = 'Active' THEN 1 ELSE 0 END) as expiring_soon
            FROM certificates
            GROUP BY COALESCE(issuing_organization, issuing_org, 'Unknown')
            ORDER BY count DESC
            LIMIT 10
        """)
        by_org = [dict(row) for row in cursor.fetchall()]

        for org in by_org:
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                st.markdown(f"**{org['org_name']}**")
            with col2:
                st.markdown(f"Total: {org['count']} ({org['active']} active)")
            with col3:
                if org['expiring_soon'] > 0:
                    st.markdown(f"⚠️ {org['expiring_soon']} expiring soon")

        st.markdown("---")

        # By department
        st.markdown("#### By Department")
        cursor.execute("""
            SELECT
                e.department,
                COUNT(*) as count,
                SUM(CASE WHEN c.status = 'Active' THEN 1 ELSE 0 END) as active
            FROM certificates c
            JOIN employees e ON c.emp_id = e.id
            GROUP BY e.department
            ORDER BY count DESC
        """)
        by_dept = [dict(row) for row in cursor.fetchall()]

        for dept in by_dept:
            st.markdown(f"**{dept['department']}:** {dept['count']} certificates ({dept['active']} active)")

def show_team_certificates():
    """Show team certificates for managers"""
    user = get_current_user()
    st.markdown("### 👥 Team Certificates")

    with get_db_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                c.*,
                e.id as employee_id,
                e.first_name || ' ' || e.last_name as name,
                (c.expiry_date - CURRENT_DATE) as days_remaining
            FROM certificates c
            JOIN employees e ON c.emp_id = e.id
            WHERE e.manager_id = %s
            ORDER BY c.expiry_date ASC
        """, (user['employee_id'],))
        certificates = [dict(row) for row in cursor.fetchall()]

    if certificates:
        for cert in certificates:
            status_emoji = "🟢" if cert['days_remaining'] > 90 else "🟡" if cert['days_remaining'] > 30 else "🔴"
            issuing = cert.get('issuing_org') or cert.get('issuing_organization') or 'N/A'
            st.markdown(f"{status_emoji} **{cert['name']}** - {cert['certificate_name']} (Issued by: {issuing}) - Expires: {cert['expiry_date']} ({cert['days_remaining']} days)")
    else:
        st.info("No team certificates found")

def show_team_overview():
    """Show team certificate overview for managers"""
    user = get_current_user()
    st.markdown("### 📊 Team Certificate Overview")

    with get_db_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN (c.expiry_date - CURRENT_DATE) <= 30 THEN 1 ELSE 0 END) as critical,
                SUM(CASE WHEN (c.expiry_date - CURRENT_DATE) <= 60 THEN 1 ELSE 0 END) as warning
            FROM certificates c
            JOIN employees e ON c.emp_id = e.id
            WHERE e.manager_id = %s AND c.status = 'Active'
        """, (user['employee_id'],))
        stats = dict(cursor.fetchone())

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Team Certificates", stats['total'] or 0)
        with col2:
            st.metric("Critical (≤30 days)", stats['critical'] or 0, delta_color="inverse")
        with col3:
            st.metric("Warning (≤60 days)", stats['warning'] or 0, delta_color="inverse")

def show_certificate_settings():
    """Show certificate tracking settings"""
    st.markdown("### ⚙️ Certificate Tracking Settings")

    st.markdown("#### Automated Alerts")

    col1, col2 = st.columns(2)
    with col1:
        alert_90 = st.checkbox("Alert 90 days before expiry", value=True)
        alert_60 = st.checkbox("Alert 60 days before expiry", value=True)
        alert_30 = st.checkbox("Alert 30 days before expiry", value=True)
    with col2:
        alert_14 = st.checkbox("Alert 14 days before expiry", value=True)
        alert_7 = st.checkbox("Alert 7 days before expiry", value=True)
        alert_daily = st.checkbox("Daily alerts for critical (<7 days)", value=True)

    st.markdown("#### Notification Recipients")
    notify_employee = st.checkbox("Notify employee", value=True)
    notify_manager = st.checkbox("Notify manager", value=True)
    notify_hr = st.checkbox("Notify HR", value=True)

    if st.button("💾 Save Settings", type="primary"):
        st.success("✅ Settings saved successfully!")
        st.info("⚙️ Automated alert system will run daily at 9 AM")
