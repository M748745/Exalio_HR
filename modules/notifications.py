"""
Notifications Center Module
Centralized notification management and history
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from database import get_db_connection
from auth import get_current_user, get_user_notifications, mark_notification_read, get_unread_count

def show_notifications_center():
    """Main notifications center interface"""
    user = get_current_user()

    st.markdown("## 🔔 Notifications Center")
    st.markdown("View and manage all your notifications")
    st.markdown("---")

    # Unread count
    unread_count = get_unread_count()

    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(f"### 📬 You have **{unread_count}** unread notifications")

    with col2:
        if st.button("✅ Mark All as Read", use_container_width=True):
            mark_all_as_read()
            st.rerun()

    st.markdown("---")

    # Tabs for different notification views
    tabs = st.tabs(["📬 Unread", "📋 All Notifications", "📊 By Type"])

    with tabs[0]:
        show_unread_notifications()

    with tabs[1]:
        show_all_notifications()

    with tabs[2]:
        show_by_type()

def show_unread_notifications():
    """Show only unread notifications"""
    user = get_current_user()

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM notifications
            WHERE recipient_id = %s AND is_read = 0
            ORDER BY created_at DESC
        """, (user['employee_id'],))
        notifications = [dict(row) for row in cursor.fetchall()]

    if notifications:
        for notif in notifications:
            display_notification(notif, show_actions=True)
    else:
        st.success("✅ No unread notifications!")

def show_all_notifications():
    """Show all notifications"""
    user = get_current_user()

    # Pagination
    page_size = 20
    page = st.number_input("Page", min_value=1, value=1, step=1)
    offset = (page - 1) * page_size

    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Get total count
        cursor.execute("""
            SELECT COUNT(*) as cnt FROM notifications
            WHERE recipient_id = %s
        """, (user['employee_id'],))
        total_count = cursor.fetchone()['cnt']

        # Get notifications
        cursor.execute("""
            SELECT * FROM notifications
            WHERE recipient_id = %s
            ORDER BY created_at DESC
            LIMIT %s OFFSET %s
        """, (user['employee_id'], page_size, offset))
        notifications = [dict(row) for row in cursor.fetchall()]

    st.markdown(f"Showing {offset + 1}-{min(offset + page_size, total_count)} of {total_count} notifications")

    if notifications:
        for notif in notifications:
            display_notification(notif, show_actions=True)
    else:
        st.info("No notifications yet")

def show_by_type():
    """Show notifications grouped by type"""
    user = get_current_user()

    with get_db_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT type, COUNT(*) as count
            FROM notifications
            WHERE recipient_id = %s
            GROUP BY type
            ORDER BY count DESC
        """, (user['employee_id'],))
        type_stats = [dict(row) for row in cursor.fetchall()]

    if type_stats:
        st.markdown("### 📊 Notifications by Type")

        for stat in type_stats:
            type_icon = {
                'info': '📢',
                'success': '✅',
                'warning': '⚠️',
                'error': '❌'
            }.get(stat['type'], '📌')

            st.markdown(f"{type_icon} **{stat['type'].upper()}**: {stat['count']} notifications")

        st.markdown("---")

        # Show notifications for selected type
        selected_type = st.selectbox("Filter by Type", ["All"] + [s['type'] for s in type_stats])

        query = """
            SELECT * FROM notifications
            WHERE recipient_id = %s
        """
        params = [user['employee_id']]

        if selected_type != "All":
            query += " AND type = %s"
            params.append(selected_type)

        query += " ORDER BY created_at DESC LIMIT 50"

        cursor.execute(query, params)
        notifications = [dict(row) for row in cursor.fetchall()]

        for notif in notifications:
            display_notification(notif, show_actions=True)
    else:
        st.info("No notifications yet")

def display_notification(notif, show_actions=True):
    """Display a single notification card"""
    # Type styling
    type_config = {
        'info': {'color': 'rgba(58, 123, 213, 0.1)', 'icon': '📢', 'border': '#3a7bd5'},
        'success': {'color': 'rgba(45, 212, 170, 0.1)', 'icon': '✅', 'border': '#2dd4aa'},
        'warning': {'color': 'rgba(240, 180, 41, 0.1)', 'icon': '⚠️', 'border': '#f0b429'},
        'error': {'color': 'rgba(241, 100, 100, 0.1)', 'icon': '❌', 'border': '#f16464'}
    }

    config = type_config.get(notif['type'], type_config['info'])

    # Read/unread styling
    opacity = "0.5" if notif['is_read'] else "1.0"
    read_badge = "" if notif['is_read'] else "<span style='background: #f16464; color: white; padding: 2px 8px; border-radius: 10px; font-size: 10px; margin-left: 10px;'>NEW</span>"

    st.markdown(f"""
        <div style="background: {config['color']}; padding: 15px; border-radius: 10px;
                    margin-bottom: 12px; border-left: 3px solid {config['border']};
                    opacity: {opacity};">
            <div style="display: flex; justify-content: space-between; align-items: start;">
                <div style="flex: 1;">
                    <div style="font-size: 24px; margin-bottom: 5px;">{config['icon']}</div>
                    <strong style="font-size: 15px;">{notif['title']}</strong> {read_badge}<br>
                    <p style="margin: 8px 0; font-size: 13px; color: #dde5f5;">{notif['message']}</p>
                    <small style="color: #7d96be; font-size: 11px;">
                        {datetime.fromisoformat(notif['created_at']).strftime('%Y-%m-%d %I:%M %p')}
                    </small>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    if show_actions and not notif['is_read']:
        col1, col2 = st.columns([1, 5])
        with col1:
            if st.button("✓ Mark Read", key=f"read_{notif['id']}", use_container_width=True):
                mark_notification_read(notif['id'])
                st.rerun()

def mark_all_as_read():
    """Mark all notifications as read"""
    user = get_current_user()

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE notifications
                SET is_read = 1
                WHERE recipient_id = %s AND is_read = 0
            """, (user['employee_id'],))
            conn.commit()

        st.success("✅ All notifications marked as read!")

    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
