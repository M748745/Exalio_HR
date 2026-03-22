"""
Announcement Approval Module
Create, approve, and publish company announcements
"""

import streamlit as st
from datetime import datetime, date
from database import get_db_connection
from auth import get_current_user, is_hr_admin, is_manager, create_notification, log_audit

def show_announcement_approval():
    """Main announcement approval interface"""
    user = get_current_user()

    st.markdown("## 📢 Announcement Management")
    st.markdown("Create, approve, and publish company announcements")
    st.markdown("---")

    if is_hr_admin():
        tabs = st.tabs(["📊 All Announcements", "✅ Pending Approval", "➕ Create Announcement", "📊 Analytics"])
    elif is_manager():
        tabs = st.tabs(["📋 My Announcements", "➕ Draft Announcement"])
    else:
        tabs = st.tabs(["📢 Company Announcements"])

    with tabs[0]:
        if is_hr_admin():
            show_all_announcements()
        elif is_manager():
            show_my_announcements()
        else:
            show_company_announcements()

    if is_hr_admin() and len(tabs) > 1:
        with tabs[1]:
            show_pending_approvals()
        with tabs[2]:
            create_announcement()
        with tabs[3]:
            show_analytics()
    elif is_manager() and len(tabs) > 1:
        with tabs[1]:
            draft_announcement()

def show_all_announcements():
    """Show all announcements"""
    st.markdown("### 📊 All Announcements")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT a.*, e.first_name, e.last_name
            FROM announcements a
            JOIN employees e ON a.created_by = e.id
            ORDER BY a.created_at DESC
        """)
        announcements = [dict(row) for row in cursor.fetchall()]

    if announcements:
        for ann in announcements:
            status_icon = '✅' if ann['status'] == 'Published' else '🟡' if ann['status'] == 'Pending' else '📝'
            with st.expander(f"{status_icon} {ann['title']} - {ann['status']} - {ann['created_at'][:10]}"):
                col1, col2 = st.columns([2, 1])
                with col1:
                    st.markdown(f"**Content:** {ann['content']}")
                    st.write(f"**Created by:** {ann['first_name']} {ann['last_name']}")
                with col2:
                    st.write(f"**Type:** {ann['announcement_type']}")
                    st.write(f"**Target:** {ann['target_audience']}")
                    st.write(f"**Priority:** {ann['priority']}")
                    st.write(f"**Status:** {ann['status']}")

                if ann['status'] == 'Pending':
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button(f"✅ Approve & Publish - {ann['id']}", key=f"approve_{ann['id']}"):
                            with get_db_connection() as conn:
                                cursor = conn.cursor()
                                cursor.execute("""
                                    UPDATE announcements SET
                                        status = 'Published',
                                        approved_by = %s,
                                        approval_date = %s,
                                        published_date = %s
                                    WHERE id = %s
                                """, (get_current_user()['employee_id'], datetime.now(), datetime.now(), ann['id']))
                                conn.commit()

                            # Notify all employees based on target audience
                            with get_db_connection() as conn:
                                cursor = conn.cursor()
                                if ann['target_audience'] == 'All':
                                    cursor.execute("SELECT id FROM employees WHERE status = 'Active'")
                                elif ann['target_audience'] != 'All':
                                    cursor.execute("SELECT id FROM employees WHERE department = %s AND status = 'Active'", (ann['target_audience'],))

                                employees = cursor.fetchall()
                                for emp in employees:
                                    create_notification(emp['id'], ann['title'], ann['content'], 'info')

                            st.success("✅ Announcement published!")
                            st.rerun()
                    with col2:
                        if st.button(f"❌ Reject - {ann['id']}", key=f"reject_{ann['id']}"):
                            with get_db_connection() as conn:
                                cursor = conn.cursor()
                                cursor.execute("UPDATE announcements SET status = 'Rejected' WHERE id = %s", (ann['id'],))
                                conn.commit()
                            create_notification(ann['created_by'], "Announcement Rejected",
                                              f"Your announcement '{ann['title']}' was not approved", "warning")
                            st.warning("Rejected")
                            st.rerun()
    else:
        st.info("No announcements")

def create_announcement():
    """Create new announcement"""
    st.markdown("### ➕ Create Announcement")

    with st.form("create_announcement"):
        title = st.text_input("Title *")

        col1, col2 = st.columns(2)
        with col1:
            announcement_type = st.selectbox("Type *", ["General", "HR Policy", "Event", "Holiday", "Emergency", "System", "Other"])
            priority = st.selectbox("Priority *", ["High", "Medium", "Low"])
        with col2:
            target_audience = st.selectbox("Target Audience *", ["All", "Engineering", "Sales", "Marketing", "HR", "Finance", "Operations"])

        content = st.text_area("Content *", height=200)
        auto_publish = st.checkbox("Publish Immediately (Skip Approval)", value=False)

        submitted = st.form_submit_button("💾 Create Announcement")

        if submitted and title and content:
            status = 'Published' if auto_publish else 'Pending'

            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO announcements (title, content, announcement_type, priority,
                                               target_audience, status, created_by)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (title, content, announcement_type, priority, target_audience,
                     status, get_current_user()['employee_id']))

                if auto_publish:
                    cursor.execute("""
                        UPDATE announcements SET
                            approved_by = %s,
                            approval_date = %s,
                            published_date = %s
                        WHERE id = (SELECT MAX(id) FROM announcements)
                    """, (get_current_user()['employee_id'], datetime.now(), datetime.now()))

                conn.commit()

            if auto_publish:
                # Notify all employees
                with get_db_connection() as conn:
                    cursor = conn.cursor()
                    if target_audience == 'All':
                        cursor.execute("SELECT id FROM employees WHERE status = 'Active'")
                    else:
                        cursor.execute("SELECT id FROM employees WHERE department = %s AND status = 'Active'", (target_audience,))

                    employees = cursor.fetchall()
                    for emp in employees:
                        create_notification(emp['id'], title, content, 'info')

            log_audit(get_current_user()['id'], f"Created announcement: {title}", "announcements")
            st.success(f"✅ Announcement {'published' if auto_publish else 'submitted for approval'}!")

def show_company_announcements():
    """Show published announcements for employees"""
    user = get_current_user()
    st.markdown("### 📢 Company Announcements")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT department FROM employees WHERE id = %s", (user['employee_id'],))
        dept = cursor.fetchone()['department']

        cursor.execute("""
            SELECT a.*, e.first_name, e.last_name
            FROM announcements a
            JOIN employees e ON a.created_by = e.id
            WHERE a.status = 'Published'
              AND (a.target_audience = 'All' OR a.target_audience = %s)
            ORDER BY a.published_date DESC
            LIMIT 20
        """, (dept,))
        announcements = [dict(row) for row in cursor.fetchall()]

    if announcements:
        for ann in announcements:
            priority_icon = '🔴' if ann['priority'] == 'High' else '🟡' if ann['priority'] == 'Medium' else '🟢'
            with st.expander(f"{priority_icon} {ann['title']} - {ann['published_date'][:10]}"):
                st.markdown(f"**{ann['content']}**")
                st.caption(f"Posted by {ann['first_name']} {ann['last_name']} | Type: {ann['announcement_type']}")
    else:
        st.info("No announcements available")

def show_my_announcements():
    """Show manager's announcements"""
    user = get_current_user()
    st.markdown("### 📋 My Announcements")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM announcements
            WHERE created_by = %s
            ORDER BY created_at DESC
        """, (user['employee_id'],))
        announcements = [dict(row) for row in cursor.fetchall()]

    if announcements:
        for ann in announcements:
            status_icon = '✅' if ann['status'] == 'Published' else '🟡' if ann['status'] == 'Pending' else '🔴'
            st.write(f"{status_icon} **{ann['title']}** - {ann['status']} - {ann['created_at'][:10]}")
    else:
        st.info("No announcements created")

def draft_announcement():
    """Manager drafts announcement"""
    st.markdown("### ➕ Draft Announcement")

    with st.form("draft_announcement"):
        title = st.text_input("Title *")
        content = st.text_area("Content *", height=150)

        col1, col2 = st.columns(2)
        with col1:
            announcement_type = st.selectbox("Type *", ["General", "Team Update", "Event", "Other"])
        with col2:
            priority = st.selectbox("Priority", ["High", "Medium", "Low"])

        submitted = st.form_submit_button("💾 Submit for Approval")

        if submitted and title and content:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT department FROM employees WHERE id = %s", (get_current_user()['employee_id'],))
                dept = cursor.fetchone()['department']

                cursor.execute("""
                    INSERT INTO announcements (title, content, announcement_type, priority,
                                               target_audience, status, created_by)
                    VALUES (%s, %s, %s, %s, %s, 'Pending', %s)
                """, (title, content, announcement_type, priority, dept, get_current_user()['employee_id']))
                conn.commit()

            log_audit(get_current_user()['id'], f"Drafted announcement: {title}", "announcements")
            st.success("✅ Announcement submitted for approval!")

def show_pending_approvals():
    """Show pending announcements"""
    st.markdown("### ✅ Pending Approvals")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT a.*, e.first_name, e.last_name
            FROM announcements a
            JOIN employees e ON a.created_by = e.id
            WHERE a.status = 'Pending'
            ORDER BY a.created_at
        """)
        pending = [dict(row) for row in cursor.fetchall()]

    if pending:
        for ann in pending:
            st.write(f"🟡 **{ann['title']}** - by {ann['first_name']} {ann['last_name']} - {ann['announcement_type']}")
    else:
        st.success("✅ No pending approvals")

def show_analytics():
    """Show announcement analytics"""
    st.markdown("### 📊 Announcement Analytics")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN status = 'Published' THEN 1 ELSE 0 END) as published,
                SUM(CASE WHEN status = 'Pending' THEN 1 ELSE 0 END) as pending
            FROM announcements
        """)
        stats = dict(cursor.fetchone())

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Announcements", stats['total'] or 0)
    with col2:
        st.metric("Published", stats['published'] or 0)
    with col3:
        st.metric("Pending Approval", stats['pending'] or 0)
