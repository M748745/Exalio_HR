"""
Announcements Module
Company-wide announcements and communications
"""

import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
from database import get_db_connection
from auth import get_current_user, is_hr_admin, is_manager, create_notification, log_audit

def show_announcements_management():
    """Main announcements interface"""
    user = get_current_user()

    st.markdown("## 📢 Announcements")
    st.markdown("Company-wide news and communications")
    st.markdown("---")

    if is_hr_admin():
        tabs = st.tabs(["📢 All Announcements", "➕ Create New", "📊 Analytics"])
    elif is_manager():
        tabs = st.tabs(["📢 Company News", "➕ Team Announcement"])
    else:
        tabs = st.tabs(["📢 Announcements", "🔖 Bookmarked"])

    with tabs[0]:
        if is_hr_admin():
            show_all_announcements_admin()
        else:
            show_all_announcements()

    with tabs[1]:
        if is_hr_admin() or is_manager():
            show_create_announcement()
        else:
            show_bookmarked_announcements()

    if len(tabs) > 2:
        with tabs[2]:
            show_announcement_analytics()

def show_all_announcements():
    """Show all announcements for user"""
    user = get_current_user()

    st.markdown("### 📢 Company Announcements")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT a.*, e.first_name, e.last_name
            FROM announcements a
            LEFT JOIN employees e ON a.created_by = e.id
            WHERE a.status = 'Published'
            AND (a.target_audience = 'All' OR a.target_department = (
                SELECT department FROM employees WHERE id = %s
            ))
            ORDER BY a.is_pinned DESC, a.created_at DESC
        """, (user['employee_id'],))
        announcements = [dict(row) for row in cursor.fetchall()]

    if announcements:
        for announcement in announcements:
            priority_config = {
                'Critical': {'color': 'rgba(241, 100, 100, 0.2)', 'icon': '🔴'},
                'High': {'color': 'rgba(240, 180, 41, 0.15)', 'icon': '🟠'},
                'Normal': {'color': 'rgba(91, 156, 246, 0.1)', 'icon': '🔵'},
                'Low': {'color': 'rgba(125, 150, 190, 0.1)', 'icon': '⚪'}
            }

            config = priority_config.get(announcement['priority'], priority_config['Normal'])
            pin_badge = '📌 ' if announcement.get('is_pinned') else ''

            with st.expander(f"{pin_badge}{config['icon']} {announcement['title']}"):
                col1, col2 = st.columns([3, 1])

                with col1:
                    st.markdown(f"### {announcement['title']}")
                    st.markdown(f"*Posted by {announcement.get('first_name', 'HR')} {announcement.get('last_name', 'Team')} on {announcement['created_at'][:10]}*")

                with col2:
                    st.markdown(f"**Priority:** {announcement['priority']}")
                    if announcement.get('expiry_date'):
                        expiry = datetime.strptime(announcement['expiry_date'], '%Y-%m-%d').date()
                        days_left = (expiry - date.today()).days
                        if days_left > 0:
                            st.info(f"⏰ Expires in {days_left} days")
                        else:
                            st.warning("⏰ Expired")

                st.markdown("---")
                st.markdown(announcement['content'])

                if announcement.get('attachments'):
                    st.info(f"📎 Attachments: {announcement['attachments']}")

                # Actions
                col1, col2 = st.columns([4, 1])
                with col2:
                    if st.button("🔖", key=f"bookmark_{announcement['id']}", help="Bookmark"):
                        st.success("Bookmarked!")
    else:
        st.info("📭 No announcements at this time")

def show_bookmarked_announcements():
    """Show bookmarked announcements"""
    st.markdown("### 🔖 Bookmarked Announcements")

    st.info("Bookmarked announcements feature coming soon")

def show_all_announcements_admin():
    """Show all announcements (Admin view)"""
    st.markdown("### 📢 All Announcements")

    # Filters
    col1, col2 = st.columns(2)
    with col1:
        status_filter = st.selectbox("Status", ["All", "Draft", "Published", "Expired"])
    with col2:
        priority_filter = st.selectbox("Priority", ["All", "Critical", "High", "Normal", "Low"])

    with get_db_connection() as conn:
        cursor = conn.cursor()

        query = """
            SELECT a.*, e.first_name, e.last_name, e.employee_id
            FROM announcements a
            LEFT JOIN employees e ON a.created_by = e.id
            WHERE 1=1
        """
        params = []

        if status_filter != "All":
            query += " AND a.status = %s"
            params.append(status_filter)

        if priority_filter != "All":
            query += " AND a.priority = %s"
            params.append(priority_filter)

        query += " ORDER BY a.is_pinned DESC, a.created_at DESC"

        cursor.execute(query, params)
        announcements = [dict(row) for row in cursor.fetchall()]

    if announcements:
        for announcement in announcements:
            with st.expander(f"{'📌' if announcement.get('is_pinned') else '📢'} {announcement['title']} - {announcement['status']}"):
                col1, col2 = st.columns([2, 1])

                with col1:
                    st.markdown(f"""
                    **Title:** {announcement['title']}
                    **Priority:** {announcement['priority']}
                    **Target:** {announcement['target_audience']} {f"({announcement['target_department']})" if announcement.get('target_department') else ''}
                    **Status:** {announcement['status']}
                    **Created:** {str(announcement['created_at'])[:10] if announcement.get('created_at') else 'N/A'}
                    **Created By:** {announcement.get('first_name', 'N/A')} {announcement.get('last_name', '')}
                    """)

                with col2:
                    if announcement.get('is_pinned'):
                        st.success("📌 Pinned")
                    if announcement.get('expiry_date'):
                        st.markdown(f"**Expires:** {announcement['expiry_date']}")

                st.markdown("---")
                st.markdown(f"**Content:**\n{announcement['content']}")

                # Actions
                st.markdown("---")
                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    if announcement['status'] == 'Draft' and st.button("✅ Publish", key=f"pub_{announcement['id']}"):
                        update_announcement_status(announcement['id'], 'Published')
                        st.rerun()

                with col2:
                    if not announcement.get('is_pinned') and st.button("📌 Pin", key=f"pin_{announcement['id']}"):
                        pin_announcement(announcement['id'], True)
                        st.rerun()
                    elif announcement.get('is_pinned') and st.button("📍 Unpin", key=f"unpin_{announcement['id']}"):
                        pin_announcement(announcement['id'], False)
                        st.rerun()

                with col3:
                    if st.button("✏️ Edit", key=f"edit_{announcement['id']}"):
                        st.info("Edit functionality would open here")

                with col4:
                    if st.button("🗑️ Delete", key=f"del_{announcement['id']}"):
                        delete_announcement(announcement['id'])
                        st.rerun()
    else:
        st.info("No announcements found")

def show_create_announcement():
    """Create new announcement"""
    user = get_current_user()

    st.markdown("### ➕ Create New Announcement")

    with st.form("create_announcement"):
        title = st.text_input("Title *", placeholder="e.g., Company Holiday Notice")

        col1, col2 = st.columns(2)

        with col1:
            priority = st.selectbox("Priority *", ["Normal", "High", "Critical", "Low"])

            if is_hr_admin():
                target_audience = st.selectbox("Target Audience *", ["All", "Department", "Team"])
            else:
                target_audience = "Team"

        with col2:
            expiry_date = st.date_input("Expiry Date (optional)", value=date.today() + timedelta(days=30))

            if target_audience == "Department":
                target_dept = st.selectbox("Department", [
                    "Engineering", "Product", "Sales", "Marketing",
                    "Human Resources", "Finance", "Operations"
                ])
            else:
                target_dept = None

        content = st.text_area("Announcement Content *", placeholder="Write your announcement here...", height=200)

        is_pinned = st.checkbox("📌 Pin this announcement") if is_hr_admin() else False

        submitted = st.form_submit_button("📢 Create Announcement", use_container_width=True)

        if submitted:
            if not all([title, priority, target_audience, content]):
                st.error("❌ Please fill all required fields")
            else:
                create_announcement(title, content, priority, target_audience,
                                  target_dept, expiry_date, is_pinned)
                st.rerun()

def show_announcement_analytics():
    """Show announcement analytics"""
    st.markdown("### 📊 Announcement Analytics")

    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Total announcements
        cursor.execute("SELECT COUNT(*) as cnt FROM announcements")
        total = cursor.fetchone()['cnt']

        # By priority
        cursor.execute("""
            SELECT priority, COUNT(*) as count
            FROM announcements
            GROUP BY priority
            ORDER BY count DESC
        """)
        by_priority = [dict(row) for row in cursor.fetchall()]

        # Recent activity
        cursor.execute("""
            SELECT COUNT(*) as cnt FROM announcements
            WHERE created_at >= NOW() - INTERVAL '30 days'
        """)
        recent = cursor.fetchone()['cnt']

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Announcements", total)
    with col2:
        st.metric("This Month", recent)
    with col3:
        st.metric("Active", total)

    if by_priority:
        st.markdown("### 📊 By Priority")
        for item in by_priority:
            st.markdown(f"**{item['priority']}**: {item['count']}")

def create_announcement(title, content, priority, target_audience,
                       target_dept, expiry_date, is_pinned):
    """Create new announcement"""
    user = get_current_user()

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            status = 'Published' if is_hr_admin() else 'Draft'

            cursor.execute("""
                INSERT INTO announcements (
                    title, content, priority, target_audience,
                    target_department, expiry_date, is_pinned,
                    status, created_by
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (title, content, priority, target_audience,
                 target_dept, expiry_date.isoformat() if expiry_date else None,
                 1 if is_pinned else 0, status, user['employee_id']))

            announcement_id = cursor.lastrowid

            # Notify relevant users if published
            if status == 'Published':
                notify_users_about_announcement(title, target_audience, target_dept)

            conn.commit()
            log_audit(f"Created announcement: {title}", "announcements", announcement_id)
            st.success(f"✅ Announcement created! ID: ANN-{announcement_id}")
            st.balloons()

    except Exception as e:
        st.error(f"❌ Error: {str(e)}")

def update_announcement_status(announcement_id, status):
    """Update announcement status"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE announcements SET status = %s WHERE id = %s", (status, announcement_id))
            conn.commit()
            log_audit(f"Updated announcement {announcement_id} status to {status}", "announcements", announcement_id)
            st.success(f"✅ Announcement {status.lower()}!")

    except Exception as e:
        st.error(f"❌ Error: {str(e)}")

def pin_announcement(announcement_id, pinned):
    """Pin/unpin announcement"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE announcements SET is_pinned = %s WHERE id = %s",
                         (1 if pinned else 0, announcement_id))
            conn.commit()
            log_audit(f"{'Pinned' if pinned else 'Unpinned'} announcement {announcement_id}", "announcements", announcement_id)
            st.success(f"✅ Announcement {'pinned' if pinned else 'unpinned'}!")

    except Exception as e:
        st.error(f"❌ Error: {str(e)}")

def delete_announcement(announcement_id):
    """Delete announcement"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE announcements SET status = 'Deleted' WHERE id = %s", (announcement_id,))
            conn.commit()
            log_audit(f"Deleted announcement {announcement_id}", "announcements", announcement_id)
            st.success("✅ Announcement deleted!")

    except Exception as e:
        st.error(f"❌ Error: {str(e)}")

def notify_users_about_announcement(title, target_audience, target_dept):
    """Notify users about new announcement"""
    # In production, this would send notifications to relevant users
    pass
