"""
Certificates Management Module
Upload, verify, and track employee certificates and credentials
"""

import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
from database import get_db_connection
from auth import get_current_user, is_hr_admin, is_manager, create_notification, log_audit

def show_certificates_management():
    """Main certificates management interface"""
    user = get_current_user()

    st.markdown("## 🎓 Certificates Management")
    st.markdown("Upload and manage employee certificates and credentials")
    st.markdown("---")

    if is_hr_admin():
        tabs = st.tabs(["📋 All Certificates", "⏳ Pending Verification", "⚠️ Expiring Soon"])
    else:
        tabs = st.tabs(["📝 My Certificates", "➕ Upload New"])

    with tabs[0]:
        if is_hr_admin():
            show_all_certificates()
        else:
            show_my_certificates()

    with tabs[1]:
        if is_hr_admin():
            show_pending_verification()
        else:
            show_upload_certificate()

    if is_hr_admin() and len(tabs) > 2:
        with tabs[2]:
            show_expiring_certificates()

def show_my_certificates():
    """Show employee's own certificates"""
    user = get_current_user()

    st.markdown("### 📝 My Certificates")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM certificates
            WHERE emp_id = %s
            ORDER BY created_at DESC
        """, (user['employee_id'],))
        certificates = [dict(row) for row in cursor.fetchall()]

    if certificates:
        for cert in certificates:
            status_config = {
                'Pending': {'color': 'rgba(240, 180, 41, 0.1)', 'icon': '⏳'},
                'Verified': {'color': 'rgba(45, 212, 170, 0.1)', 'icon': '✅'},
                'Rejected': {'color': 'rgba(241, 100, 100, 0.1)', 'icon': '❌'}
            }

            config = status_config.get(cert['status'], status_config['Pending'])

            # Check expiry
            expiry_warning = ""
            if cert['expiry_date']:
                expiry = datetime.strptime(cert['expiry_date'], '%Y-%m-%d').date()
                days_left = (expiry - date.today()).days
                if days_left < 0:
                    expiry_warning = "<br>🔴 <strong>EXPIRED</strong>"
                elif days_left < 30:
                    expiry_warning = f"<br>⚠️ Expires in {days_left} days"

            st.markdown(f"""
                <div style="background: {config['color']}; padding: 15px; border-radius: 10px; margin-bottom: 12px; border-left: 3px solid #c9963a;">
                    <div style="font-size: 24px; margin-bottom: 5px;">{config['icon']}</div>
                    <strong style="font-size: 15px;">{cert['certificate_name']}</strong><br>
                    <small style="color: #7d96be;">
                        {cert['issuing_org'] or 'N/A'} •
                        Issued: {cert['issue_date'] or 'N/A'} •
                        Expires: {cert['expiry_date'] or 'No expiry'}
                        {expiry_warning}
                    </small><br>
                    <span style="background: rgba(58, 123, 213, 0.2); padding: 3px 10px; border-radius: 15px; font-size: 11px; margin-top: 5px; display: inline-block;">
                        {cert['status']}
                    </span>
                </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No certificates uploaded yet")

def show_upload_certificate():
    """Form to upload new certificate"""
    user = get_current_user()

    st.markdown("### ➕ Upload New Certificate")

    with st.form("certificate_form"):
        cert_name = st.text_input("Certificate Name *", placeholder="e.g., AWS Certified Solutions Architect")

        col1, col2 = st.columns(2)

        with col1:
            issuing_org = st.text_input("Issuing Organization", placeholder="e.g., Amazon Web Services")
            issue_date = st.date_input("Issue Date", value=date.today())

        with col2:
            has_expiry = st.checkbox("Has Expiry Date")
            if has_expiry:
                expiry_date = st.date_input("Expiry Date", value=date.today() + timedelta(days=365))
            else:
                expiry_date = None

        # File upload simulation
        st.markdown("**📎 Certificate File**")
        cert_file = st.file_uploader("Upload Certificate", type=['pdf', 'jpg', 'jpeg', 'png'], help="Max 5MB")

        submitted = st.form_submit_button("📤 Upload Certificate", use_container_width=True)

        if submitted:
            if not cert_name:
                st.error("❌ Please enter certificate name")
            else:
                try:
                    with get_db_connection() as conn:
                        cursor = conn.cursor()

                        # Save file info (in production, would upload to storage)
                        file_path = f"certificates/{user['employee_id']}_{datetime.now().timestamp()}.pdf" if cert_file else None

                        cursor.execute("""
                            INSERT INTO certificates (
                                emp_id, certificate_name, issuing_org, issue_date,
                                expiry_date, file_path, status
                            ) VALUES (%s, %s, %s, %s, %s, %s, 'Pending')
                        """, (user['employee_id'], cert_name, issuing_org,
                             issue_date.isoformat() if issue_date else None,
                             expiry_date.isoformat() if expiry_date else None,
                             file_path))

                        cert_id = cursor.lastrowid

                        # Notify HR
                        cursor.execute("SELECT id FROM employees WHERE department = 'Human Resources' LIMIT 1")
                        hr_emp = cursor.fetchone()
                        if hr_emp:
                            create_notification(
                                hr_emp['id'],
                                "New Certificate for Verification",
                                f"{user['full_name']} uploaded a certificate: {cert_name}",
                                'info'
                            )

                        conn.commit()
                        log_audit(f"Uploaded certificate: {cert_name}", "certificates", cert_id)

                        st.success(f"✅ Certificate uploaded successfully! ID: CERT-{cert_id}")
                        st.balloons()
                        st.rerun()

                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")

def show_all_certificates():
    """Show all certificates (HR view)"""
    st.markdown("### 📋 All Certificates")

    # Filters
    col1, col2, col3 = st.columns(3)
    with col1:
        status_filter = st.selectbox("Status", ["All", "Pending", "Verified", "Rejected"])
    with col2:
        expiry_filter = st.selectbox("Expiry", ["All", "Active", "Expiring Soon", "Expired"])
    with col3:
        search = st.text_input("🔍 Search")

    with get_db_connection() as conn:
        cursor = conn.cursor()

        query = """
            SELECT c.*, e.first_name, e.last_name, e.employee_id, e.department
            FROM certificates c
            JOIN employees e ON c.emp_id = e.id
            WHERE 1=1
        """
        params = []

        if status_filter != "All":
            query += " AND c.status = %s"
            params.append(status_filter)

        if search:
            query += " AND (e.first_name LIKE %s OR e.last_name LIKE %s OR c.certificate_name LIKE %s)"
            params.extend([f"%{search}%", f"%{search}%", f"%{search}%"])

        query += " ORDER BY c.created_at DESC"

        cursor.execute(query, params)
        certificates = [dict(row) for row in cursor.fetchall()]

        # Apply expiry filter
        if expiry_filter != "All":
            filtered = []
            for cert in certificates:
                if cert['expiry_date']:
                    expiry = datetime.strptime(cert['expiry_date'], '%Y-%m-%d').date()
                    days_left = (expiry - date.today()).days

                    if expiry_filter == "Expiring Soon" and 0 <= days_left <= 30:
                        filtered.append(cert)
                    elif expiry_filter == "Expired" and days_left < 0:
                        filtered.append(cert)
                    elif expiry_filter == "Active" and days_left >= 0:
                        filtered.append(cert)
                elif expiry_filter == "Active":
                    filtered.append(cert)

            certificates = filtered

    if certificates:
        for cert in certificates:
            with st.expander(f"🎓 {cert['certificate_name']} - {cert['first_name']} {cert['last_name']} ({cert['status']})"):
                col1, col2 = st.columns([2, 1])

                with col1:
                    st.markdown(f"""
                    **Employee:** {cert['first_name']} {cert['last_name']} ({cert['employee_id']})
                    **Department:** {cert['department']}
                    **Certificate:** {cert['certificate_name']}
                    **Issuing Org:** {cert['issuing_org'] or 'N/A'}
                    **Issue Date:** {cert['issue_date'] or 'N/A'}
                    **Expiry Date:** {cert['expiry_date'] or 'No expiry'}
                    **Status:** {cert['status']}
                    **Uploaded:** {cert['created_at']}
                    """)

                with col2:
                    if cert['expiry_date']:
                        expiry = datetime.strptime(cert['expiry_date'], '%Y-%m-%d').date()
                        days_left = (expiry - date.today()).days
                        st.metric("Days Until Expiry", days_left)
                        if days_left < 0:
                            st.error("⚠️ Expired!")
                        elif days_left < 30:
                            st.warning("⚠️ Expiring Soon!")

                # Actions
                if cert['status'] == 'Pending':
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("✅ Verify", key=f"verify_{cert['id']}", use_container_width=True):
                            verify_certificate(cert['id'], cert['emp_id'])
                            st.rerun()
                    with col2:
                        if st.button("❌ Reject", key=f"reject_{cert['id']}", use_container_width=True):
                            reject_certificate(cert['id'], cert['emp_id'])
                            st.rerun()
    else:
        st.info("No certificates found")

def show_pending_verification():
    """Show certificates pending verification"""
    st.markdown("### ⏳ Pending Verification")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT c.*, e.first_name, e.last_name, e.employee_id
            FROM certificates c
            JOIN employees e ON c.emp_id = e.id
            WHERE c.status = 'Pending'
            ORDER BY c.created_at ASC
        """)
        pending = [dict(row) for row in cursor.fetchall()]

    if pending:
        st.info(f"📋 {len(pending)} certificate(s) awaiting verification")

        for cert in pending:
            st.markdown(f"""
                <div style="background: rgba(240, 180, 41, 0.1); padding: 15px; border-radius: 10px; margin-bottom: 12px;">
                    <strong>{cert['certificate_name']}</strong><br>
                    <small>{cert['first_name']} {cert['last_name']} ({cert['employee_id']})</small>
                </div>
            """, unsafe_allow_html=True)

            col1, col2 = st.columns([1, 4])
            with col1:
                if st.button("✅ Verify", key=f"verify_pend_{cert['id']}"):
                    verify_certificate(cert['id'], cert['emp_id'])
                    st.rerun()
    else:
        st.success("✅ No certificates pending verification!")

def show_expiring_certificates():
    """Show certificates expiring soon"""
    st.markdown("### ⚠️ Certificates Expiring Soon")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT c.*, e.first_name, e.last_name, e.employee_id
            FROM certificates c
            JOIN employees e ON c.emp_id = e.id
            WHERE c.status = 'Verified' AND c.expiry_date IS NOT NULL
            ORDER BY c.expiry_date ASC
        """)
        all_certs = [dict(row) for row in cursor.fetchall()]

    expiring = []
    for cert in all_certs:
        expiry = datetime.strptime(cert['expiry_date'], '%Y-%m-%d').date()
        days_left = (expiry - date.today()).days
        if days_left <= 60:
            cert['days_left'] = days_left
            expiring.append(cert)

    if expiring:
        for cert in expiring:
            if cert['days_left'] < 0:
                urgency = "🔴 EXPIRED"
                color = "rgba(241, 100, 100, 0.2)"
            elif cert['days_left'] < 30:
                urgency = f"🔴 {cert['days_left']} days left"
                color = "rgba(241, 100, 100, 0.1)"
            else:
                urgency = f"🟡 {cert['days_left']} days left"
                color = "rgba(240, 180, 41, 0.1)"

            st.markdown(f"""
                <div style="background: {color}; padding: 15px; border-radius: 10px; margin-bottom: 10px;">
                    <strong>{urgency}</strong> - {cert['certificate_name']}<br>
                    <small>{cert['first_name']} {cert['last_name']} • Expires: {cert['expiry_date']}</small>
                </div>
            """, unsafe_allow_html=True)
    else:
        st.success("✅ No certificates expiring in the next 60 days!")

def verify_certificate(cert_id, emp_id):
    """Verify a certificate"""
    user = get_current_user()

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                UPDATE certificates SET
                    status = 'Verified',
                    verified_by = %s
                WHERE id = %s
            """, (user['employee_id'], cert_id))

            create_notification(
                emp_id,
                "Certificate Verified",
                f"Your certificate has been verified and approved.",
                'success'
            )

            conn.commit()
            log_audit(f"Verified certificate ID: {cert_id}", "certificates", cert_id)
            st.success("✅ Certificate verified!")

    except Exception as e:
        st.error(f"❌ Error: {str(e)}")

def reject_certificate(cert_id, emp_id):
    """Reject a certificate"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("UPDATE certificates SET status = 'Rejected' WHERE id = %s", (cert_id,))

            create_notification(
                emp_id,
                "Certificate Not Verified",
                "Your certificate could not be verified. Please contact HR for details.",
                'warning'
            )

            conn.commit()
            log_audit(f"Rejected certificate ID: {cert_id}", "certificates", cert_id)
            st.warning("⚠️ Certificate rejected")

    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
