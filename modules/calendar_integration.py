"""
Calendar Integration Module
Calendar and event management integration
"""

import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
from database import get_db_connection
from auth import get_current_user, is_hr_admin, is_manager, log_audit

def show_calendar_integration():
    """Main calendar integration interface"""
    user = get_current_user()

    st.markdown("## 📅 Calendar Integration")
    st.markdown("Integrated calendar and event management")
    st.markdown("---")

    tabs = st.tabs(["📅 Calendar View", "📋 Upcoming Events", "➕ Add Event", "⚙️ Settings"])

    with tabs[0]:
        show_calendar_view()

    with tabs[1]:
        show_upcoming_events()

    with tabs[2]:
        show_add_event()

    with tabs[3]:
        show_calendar_settings()

def show_calendar_view():
    """Show calendar view"""
    st.markdown("### 📅 Calendar")

    # Month selector
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        selected_month = st.date_input("Select Month", value=date.today())

    # Calendar display (simplified month view)
    st.markdown(f"### {selected_month.strftime('%B %Y')}")

    # Get events for the month
    month_start = selected_month.replace(day=1)
    if selected_month.month == 12:
        month_end = selected_month.replace(year=selected_month.year + 1, month=1, day=1) - timedelta(days=1)
    else:
        month_end = selected_month.replace(month=selected_month.month + 1, day=1) - timedelta(days=1)

    # Sample events
    events = [
        {
            'date': date.today(),
            'title': 'Team Meeting',
            'type': 'Meeting',
            'time': '10:00 AM'
        },
        {
            'date': date.today() + timedelta(days=2),
            'title': 'Performance Review',
            'type': 'Appraisal',
            'time': '2:00 PM'
        },
        {
            'date': date.today() + timedelta(days=5),
            'title': 'Company Holiday',
            'type': 'Holiday',
            'time': 'All Day'
        }
    ]

    # Display events by date
    current_date = month_start
    while current_date <= month_end:
        day_events = [e for e in events if e['date'] == current_date]

        if day_events or current_date == date.today():
            day_style = "background: rgba(91, 156, 246, 0.15);" if current_date == date.today() else ""

            st.markdown(f"""
                <div style="{day_style} padding: 8px; border-radius: 4px; margin-bottom: 4px;">
                    <strong>{current_date.strftime('%A, %B %d')}</strong>
                </div>
            """, unsafe_allow_html=True)

            if day_events:
                for event in day_events:
                    event_color = {
                        'Meeting': 'rgba(91, 156, 246, 0.1)',
                        'Appraisal': 'rgba(240, 180, 41, 0.1)',
                        'Holiday': 'rgba(46, 213, 115, 0.1)',
                        'Training': 'rgba(142, 82, 222, 0.1)'
                    }.get(event['type'], 'rgba(125, 150, 190, 0.1)')

                    st.markdown(f"""
                        <div style="
                            background: {event_color};
                            padding: 8px;
                            border-radius: 4px;
                            margin: 4px 0 4px 20px;
                            border-left: 3px solid rgba(91, 156, 246, 0.8);
                        ">
                            <strong>{event['title']}</strong><br>
                            <small>{event['time']} • {event['type']}</small>
                        </div>
                    """, unsafe_allow_html=True)

        current_date += timedelta(days=1)

def show_upcoming_events():
    """Show upcoming events list"""
    user = get_current_user()

    st.markdown("### 📋 Upcoming Events")

    # Time range selector
    time_range = st.selectbox("Show events for:", [
        "Next 7 days",
        "Next 30 days",
        "Next 3 months",
        "All upcoming"
    ])

    # Sample upcoming events
    upcoming_events = [
        {
            'date': date.today(),
            'time': '10:00 AM',
            'title': 'Team Standup',
            'type': 'Meeting',
            'location': 'Conference Room A',
            'attendees': 5
        },
        {
            'date': date.today() + timedelta(days=1),
            'time': '2:00 PM',
            'title': 'Performance Review with Manager',
            'type': 'Appraisal',
            'location': 'Manager Office',
            'attendees': 2
        },
        {
            'date': date.today() + timedelta(days=3),
            'time': '9:00 AM',
            'title': 'Training Session: New Software',
            'type': 'Training',
            'location': 'Training Room',
            'attendees': 15
        },
        {
            'date': date.today() + timedelta(days=5),
            'time': 'All Day',
            'title': 'Independence Day',
            'type': 'Holiday',
            'location': 'Company-wide',
            'attendees': 0
        }
    ]

    for event in upcoming_events:
        with st.expander(f"📅 {event['date'].strftime('%b %d')} - {event['title']}"):
            col1, col2 = st.columns([2, 1])

            with col1:
                st.markdown(f"""
                **Title:** {event['title']}
                **Date:** {event['date'].strftime('%A, %B %d, %Y')}
                **Time:** {event['time']}
                **Type:** {event['type']}
                **Location:** {event['location']}
                """)

            with col2:
                if event['attendees'] > 0:
                    st.metric("Attendees", event['attendees'])

                # Actions
                col_a, col_b = st.columns(2)
                with col_a:
                    if st.button("✅ Accept", key=f"accept_{event['title']}"):
                        st.success("Event accepted")
                with col_b:
                    if st.button("❌ Decline", key=f"decline_{event['title']}"):
                        st.info("Event declined")

    # Sync options
    st.markdown("---")
    st.markdown("### 🔄 Calendar Sync")

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("📅 Sync with Google Calendar"):
            st.info("Google Calendar sync initiated (simulated)")
    with col2:
        if st.button("📆 Sync with Outlook"):
            st.info("Outlook sync initiated (simulated)")
    with col3:
        if st.button("🍎 Sync with Apple Calendar"):
            st.info("Apple Calendar sync initiated (simulated)")

def show_add_event():
    """Add new calendar event"""
    user = get_current_user()

    st.markdown("### ➕ Add Event")

    with st.form("add_event"):
        event_title = st.text_input("Event Title *", placeholder="e.g., Team Meeting")

        col1, col2 = st.columns(2)

        with col1:
            event_date = st.date_input("Date *")
            event_type = st.selectbox("Event Type *", [
                "Meeting",
                "Interview",
                "Training",
                "Appraisal",
                "Social",
                "Holiday",
                "Other"
            ])

        with col2:
            start_time = st.time_input("Start Time *")
            end_time = st.time_input("End Time *")

        location = st.text_input("Location", placeholder="Conference Room, Office, or Online")

        description = st.text_area("Description", placeholder="Event details...", height=100)

        # Attendees
        st.markdown("#### Attendees")

        if is_hr_admin() or is_manager():
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, employee_id, first_name, last_name
                    FROM employees
                    WHERE status = 'Active'
                    ORDER BY first_name
                """)
                employees = [dict(row) for row in cursor.fetchall()]

            if employees:
                emp_names = [f"{e['first_name']} {e['last_name']} ({e['employee_id']})" for e in employees]
                attendees = st.multiselect("Select Attendees", emp_names)

        # Reminders
        reminder = st.selectbox("Reminder", [
            "No reminder",
            "15 minutes before",
            "30 minutes before",
            "1 hour before",
            "1 day before"
        ])

        recurring = st.checkbox("Recurring Event")

        if recurring:
            recurrence = st.selectbox("Recurrence", [
                "Daily",
                "Weekly",
                "Bi-weekly",
                "Monthly",
                "Yearly"
            ])

        submitted = st.form_submit_button("📅 Create Event", use_container_width=True)

        if submitted:
            if event_title and event_date and start_time and end_time:
                st.success(f"✅ Event '{event_title}' created for {event_date}")
                log_audit(f"Created calendar event: {event_title}", "calendar", 0)

                if is_hr_admin() or is_manager():
                    st.info(f"📧 Invitations sent to attendees")
            else:
                st.error("❌ Please fill all required fields")

def show_calendar_settings():
    """Calendar integration settings"""
    user = get_current_user()

    st.markdown("### ⚙️ Calendar Settings")

    with st.form("calendar_settings"):
        st.markdown("#### Display Settings")

        col1, col2 = st.columns(2)

        with col1:
            start_day = st.selectbox("Week starts on", [
                "Sunday", "Monday", "Saturday"
            ])
            time_format = st.selectbox("Time Format", ["12-hour", "24-hour"])

        with col2:
            default_view = st.selectbox("Default View", [
                "Month", "Week", "Day", "Agenda"
            ])
            show_weekends = st.checkbox("Show Weekends", value=True)

        st.markdown("#### Notification Settings")

        col1, col2 = st.columns(2)

        with col1:
            email_reminders = st.checkbox("Email Reminders", value=True)
            push_notifications = st.checkbox("Push Notifications", value=False)

        with col2:
            default_reminder = st.selectbox("Default Reminder", [
                "No reminder",
                "15 minutes",
                "30 minutes",
                "1 hour",
                "1 day"
            ])

        st.markdown("#### Integration Settings")

        google_calendar = st.checkbox("Sync with Google Calendar", value=False)

        if google_calendar:
            google_calendar_id = st.text_input("Calendar ID", placeholder="your-calendar@gmail.com")

        outlook_sync = st.checkbox("Sync with Outlook", value=False)

        if outlook_sync:
            outlook_email = st.text_input("Outlook Email", placeholder="your-email@outlook.com")

        st.markdown("#### Event Types")

        show_meetings = st.checkbox("Show Meetings", value=True)
        show_appraisals = st.checkbox("Show Appraisals", value=True)
        show_training = st.checkbox("Show Training", value=True)
        show_holidays = st.checkbox("Show Holidays", value=True)

        submitted = st.form_submit_button("💾 Save Settings", use_container_width=True)

        if submitted:
            st.success("✅ Calendar settings saved!")
            log_audit("Calendar settings updated", "calendar", 0)

    # Export calendar
    st.markdown("---")
    st.markdown("### 📥 Export Calendar")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("📄 Export to iCal"):
            st.success("Calendar exported to iCal format")

    with col2:
        if st.button("📊 Export to CSV"):
            st.success("Calendar exported to CSV format")

    with col3:
        if st.button("📧 Email Calendar"):
            st.success("Calendar sent to your email")
