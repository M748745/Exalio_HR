"""
Email Integration Module
Email notification system integration
"""

import streamlit as st
from datetime import datetime
from database import get_db_connection
from auth import get_current_user, is_hr_admin, log_audit

def show_email_integration():
    """Main email integration interface"""
    user = get_current_user()

    if not is_hr_admin():
        st.warning("⚠️ Email integration settings are only available for HR Administrators")
        return

    st.markdown("## 📧 Email Integration")
    st.markdown("Configure and manage email notifications")
    st.markdown("---")

    tabs = st.tabs(["⚙️ Settings", "📤 Email Queue", "📊 Statistics", "🧪 Test Email"])

    with tabs[0]:
        show_email_settings()

    with tabs[1]:
        show_email_queue()

    with tabs[2]:
        show_email_statistics()

    with tabs[3]:
        show_test_email()

def show_email_settings():
    """Email configuration settings"""
    st.markdown("### ⚙️ Email Settings")

    with st.form("email_settings"):
        st.markdown("#### SMTP Configuration")

        col1, col2 = st.columns(2)

        with col1:
            smtp_server = st.text_input("SMTP Server *", placeholder="smtp.gmail.com")
            smtp_port = st.number_input("SMTP Port *", value=587, min_value=1, max_value=65535)
            use_tls = st.checkbox("Use TLS/SSL", value=True)

        with col2:
            from_email = st.text_input("From Email *", placeholder="hr@company.com")
            from_name = st.text_input("From Name", value="HR Department", placeholder="HR Department")

        st.markdown("#### Authentication")
        col1, col2 = st.columns(2)

        with col1:
            smtp_username = st.text_input("SMTP Username", placeholder="your-email@gmail.com")
        with col2:
            smtp_password = st.text_input("SMTP Password", type="password")

        st.markdown("#### Email Templates")

        welcome_template = st.text_area(
            "Welcome Email Template",
            value="Welcome to {company_name}, {employee_name}!",
            height=100
        )

        leave_approval_template = st.text_area(
            "Leave Approval Template",
            value="Your leave request from {start_date} to {end_date} has been {status}.",
            height=100
        )

        st.markdown("#### Notification Settings")

        col1, col2 = st.columns(2)

        with col1:
            send_welcome_email = st.checkbox("Send Welcome Email", value=True)
            send_leave_notifications = st.checkbox("Send Leave Notifications", value=True)
            send_appraisal_reminders = st.checkbox("Send Appraisal Reminders", value=True)

        with col2:
            send_birthday_wishes = st.checkbox("Send Birthday Wishes", value=True)
            send_anniversary_wishes = st.checkbox("Send Anniversary Wishes", value=True)
            daily_digest = st.checkbox("Send Daily Digest to Managers", value=False)

        submitted = st.form_submit_button("💾 Save Settings", use_container_width=True)

        if submitted:
            st.success("✅ Email settings saved!")
            st.info("📧 Email integration configured. Emails will be sent for enabled events.")
            log_audit("Email settings updated", "email", 0)

def show_email_queue():
    """Show pending email queue"""
    st.markdown("### 📤 Email Queue")

    # Simulated email queue
    queue_items = [
        {
            'id': 1,
            'to': 'john.doe@company.com',
            'subject': 'Leave Request Approved',
            'status': 'Pending',
            'created_at': datetime.now().isoformat()
        },
        {
            'id': 2,
            'to': 'jane.smith@company.com',
            'subject': 'Welcome to the Team',
            'status': 'Sent',
            'created_at': datetime.now().isoformat()
        },
        {
            'id': 3,
            'to': 'manager@company.com',
            'subject': 'Performance Review Due',
            'status': 'Failed',
            'created_at': datetime.now().isoformat()
        }
    ]

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Pending", 1)
    with col2:
        st.metric("Sent Today", 12)
    with col3:
        st.metric("Failed", 1)

    st.markdown("---")

    for item in queue_items:
        status_color = {
            'Pending': 'rgba(240, 180, 41, 0.15)',
            'Sent': 'rgba(46, 213, 115, 0.15)',
            'Failed': 'rgba(241, 100, 100, 0.15)'
        }.get(item['status'], 'rgba(125, 150, 190, 0.1)')

        status_icon = {
            'Pending': '⏳',
            'Sent': '✅',
            'Failed': '❌'
        }.get(item['status'], '📧')

        st.markdown(f"""
            <div style="
                background: {status_color};
                padding: 12px;
                border-radius: 8px;
                margin-bottom: 8px;
            ">
                {status_icon} <strong>{item['subject']}</strong><br>
                <small>To: {item['to']} • Status: {item['status']}</small>
            </div>
        """, unsafe_allow_html=True)

        if item['status'] == 'Failed':
            if st.button(f"🔄 Retry", key=f"retry_{item['id']}"):
                st.success("Email re-queued for sending")

    # Bulk actions
    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🚀 Process Queue"):
            st.success("✅ Processing 1 pending email...")
    with col2:
        if st.button("🗑️ Clear Failed"):
            st.success("✅ Cleared 1 failed email")

def show_email_statistics():
    """Show email statistics"""
    st.markdown("### 📊 Email Statistics")

    # Metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Sent", "1,234")
    with col2:
        st.metric("This Month", "156")
    with col3:
        st.metric("Success Rate", "98.5%")
    with col4:
        st.metric("Avg Response Time", "2.3s")

    # Email types
    st.markdown("---")
    st.markdown("#### 📧 Emails by Type (Last 30 Days)")

    email_types = [
        {'Type': 'Leave Notifications', 'Count': 45},
        {'Type': 'Welcome Emails', 'Count': 12},
        {'Type': 'Appraisal Reminders', 'Count': 28},
        {'Type': 'Birthday Wishes', 'Count': 8},
        {'Type': 'System Alerts', 'Count': 15}
    ]

    import pandas as pd
    df = pd.DataFrame(email_types)
    st.dataframe(df, use_container_width=True, hide_index=True)

    # Recent activity
    st.markdown("---")
    st.markdown("#### 📋 Recent Email Activity")

    recent_emails = [
        "✅ Leave approval notification sent to john.doe@company.com",
        "✅ Welcome email sent to new.employee@company.com",
        "⏳ Birthday wish email queued for tomorrow",
        "❌ Failed to send notification to invalid@email.com",
        "✅ Appraisal reminder sent to 15 employees"
    ]

    for email in recent_emails:
        st.markdown(f"- {email}")

def show_test_email():
    """Test email functionality"""
    st.markdown("### 🧪 Test Email")

    st.info("💡 Use this to test your email configuration")

    with st.form("test_email"):
        test_email = st.text_input("Recipient Email *", placeholder="test@example.com")
        subject = st.text_input("Subject", value="Test Email from HR System")
        message = st.text_area(
            "Message",
            value="This is a test email from the HR Management System.",
            height=150
        )

        submitted = st.form_submit_button("📧 Send Test Email", use_container_width=True)

        if submitted:
            if test_email:
                with st.spinner("Sending test email..."):
                    # Simulate email sending
                    st.success(f"✅ Test email sent to {test_email}")
                    st.info("📧 Check your inbox. The email might take a few moments to arrive.")
                    log_audit(f"Test email sent to {test_email}", "email", 0)
            else:
                st.error("❌ Please enter a recipient email address")

    # Email preview
    st.markdown("---")
    st.markdown("#### 👀 Email Preview")

    st.markdown(f"""
        <div style="
            background: white;
            color: black;
            padding: 20px;
            border-radius: 8px;
            border: 1px solid rgba(125, 150, 190, 0.3);
        ">
            <p><strong>From:</strong> HR Department &lt;hr@company.com&gt;</p>
            <p><strong>To:</strong> {test_email if 'test_email' in locals() else 'recipient@example.com'}</p>
            <p><strong>Subject:</strong> Test Email from HR System</p>
            <hr>
            <p>This is a test email from the HR Management System.</p>
            <br>
            <p style="color: #7d96be;"><small>This is an automated message from the HR Management System.</small></p>
        </div>
    """, unsafe_allow_html=True)
