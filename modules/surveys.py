"""
Surveys & Feedback Module
Employee engagement surveys and feedback collection
"""

import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
from database import get_db_connection
from auth import get_current_user, is_hr_admin, is_manager, create_notification, log_audit

def show_surveys_feedback():
    """Main surveys and feedback interface"""
    user = get_current_user()

    st.markdown("## 📋 Surveys & Feedback")
    st.markdown("Employee engagement surveys and feedback collection")
    st.markdown("---")

    if is_hr_admin():
        tabs = st.tabs(["📊 All Surveys", "➕ Create Survey", "📈 Results", "💬 Feedback"])
    elif is_manager():
        tabs = st.tabs(["📋 Team Surveys", "📊 Team Results", "💬 Feedback"])
    else:
        tabs = st.tabs(["📝 My Surveys", "💬 Give Feedback", "📊 My Responses"])

    with tabs[0]:
        if is_hr_admin():
            show_all_surveys()
        elif is_manager():
            show_team_surveys()
        else:
            show_my_surveys()

    with tabs[1]:
        if is_hr_admin():
            show_create_survey()
        elif is_manager():
            show_team_survey_results()
        else:
            show_give_feedback()

    if len(tabs) > 2:
        with tabs[2]:
            if is_hr_admin():
                show_survey_results()
            elif is_manager():
                show_team_feedback()
            else:
                show_my_responses()

    if len(tabs) > 3:
        with tabs[3]:
            show_feedback_management()

def show_my_surveys():
    """Show surveys available for employee"""
    user = get_current_user()

    st.markdown("### 📝 Available Surveys")

    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Get active surveys
        cursor.execute("""
            SELECT s.*,
                   (SELECT COUNT(*) FROM survey_responses
                    WHERE survey_id = s.id AND emp_id = %s) as has_responded
            FROM surveys s
            WHERE s.status = 'Active'
            AND (s.target_audience = 'All' OR s.target_department = (
                SELECT department FROM employees WHERE id = %s
            ))
            AND s.end_date >= CURRENT_DATE
            ORDER BY s.created_at DESC
        """, (user['employee_id'], user['employee_id']))
        surveys = [dict(row) for row in cursor.fetchall()]

    if surveys:
        for survey in surveys:
            has_responded = survey['has_responded'] > 0

            status_badge = "✅ Completed" if has_responded else "⏳ Pending"
            status_color = 'rgba(46, 213, 115, 0.15)' if has_responded else 'rgba(240, 180, 41, 0.15)'

            st.markdown(f"""
                <div style="
                    background: {status_color};
                    padding: 16px;
                    border-radius: 10px;
                    margin-bottom: 12px;
                    border-left: 4px solid {'#2ed573' if has_responded else '#f0b429'};
                ">
                    <h4 style="margin-top: 0;">{survey['title']} {status_badge}</h4>
                    <p>{survey.get('description', 'No description')}</p>
                    <small>📅 Closes: {survey['end_date']}</small>
                </div>
            """, unsafe_allow_html=True)

            if not has_responded:
                if st.button(f"📝 Take Survey", key=f"take_{survey['id']}"):
                    show_take_survey(survey)
            else:
                st.success("You've already completed this survey")

    else:
        st.info("No active surveys at this time")

def show_take_survey(survey):
    """Display survey for employee to complete"""
    user = get_current_user()

    st.markdown(f"### 📝 {survey['title']}")
    st.markdown(survey.get('description', ''))
    st.markdown("---")

    with st.form(f"survey_{survey['id']}"):
        st.markdown("#### Survey Questions")

        # Parse questions (assuming JSON or simple format)
        # For simplicity, using predefined question types
        responses = {}

        # Standard engagement questions
        questions = [
            {
                'id': 1,
                'text': 'How satisfied are you with your current role?',
                'type': 'scale'
            },
            {
                'id': 2,
                'text': 'Do you feel valued as part of the team?',
                'type': 'scale'
            },
            {
                'id': 3,
                'text': 'How would you rate communication within the company?',
                'type': 'scale'
            },
            {
                'id': 4,
                'text': 'Do you have the resources needed to do your job effectively?',
                'type': 'yesno'
            },
            {
                'id': 5,
                'text': 'Would you recommend this company as a great place to work?',
                'type': 'yesno'
            },
            {
                'id': 6,
                'text': 'Additional comments or suggestions:',
                'type': 'text'
            }
        ]

        for q in questions:
            st.markdown(f"**{q['id']}. {q['text']}**")

            if q['type'] == 'scale':
                responses[q['id']] = st.slider(
                    "Select rating (1 = Very Dissatisfied, 5 = Very Satisfied)",
                    1, 5, 3,
                    key=f"q_{survey['id']}_{q['id']}"
                )
            elif q['type'] == 'yesno':
                responses[q['id']] = st.radio(
                    "Select answer",
                    ["Yes", "No", "Neutral"],
                    key=f"q_{survey['id']}_{q['id']}"
                )
            elif q['type'] == 'text':
                responses[q['id']] = st.text_area(
                    "Your response",
                    key=f"q_{survey['id']}_{q['id']}"
                )

            st.markdown("---")

        submitted = st.form_submit_button("📤 Submit Survey", use_container_width=True)

        if submitted:
            submit_survey_response(survey['id'], user['employee_id'], responses)
            st.rerun()

def show_give_feedback():
    """Employee gives feedback"""
    user = get_current_user()

    st.markdown("### 💬 Give Feedback")

    with st.form("give_feedback"):
        st.markdown("Share your thoughts, ideas, or concerns anonymously")

        feedback_type = st.selectbox("Feedback Type", [
            "General Feedback",
            "Process Improvement",
            "Work Environment",
            "Management",
            "Team Collaboration",
            "Other"
        ])

        subject = st.text_input("Subject *", placeholder="Brief summary of your feedback")

        feedback = st.text_area(
            "Your Feedback *",
            placeholder="Please share your thoughts...",
            height=200
        )

        anonymous = st.checkbox("Submit anonymously", value=False)

        submitted = st.form_submit_button("💬 Submit Feedback", use_container_width=True)

        if submitted:
            if subject and feedback:
                submit_feedback(
                    user['employee_id'] if not anonymous else None,
                    feedback_type,
                    subject,
                    feedback
                )
                st.success("✅ Thank you for your feedback!")
                st.rerun()
            else:
                st.error("❌ Please fill all required fields")

def show_my_responses():
    """Show employee's survey responses"""
    user = get_current_user()

    st.markdown("### 📊 My Survey Responses")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT sr.*, s.title, s.description
            FROM survey_responses sr
            JOIN surveys s ON sr.survey_id = s.id
            WHERE sr.emp_id = %s
            ORDER BY sr.submitted_at DESC
        """, (user['employee_id'],))
        responses = [dict(row) for row in cursor.fetchall()]

    if responses:
        for response in responses:
            st.markdown(f"""
                <div style="
                    background: rgba(91, 156, 246, 0.1);
                    padding: 12px;
                    border-radius: 8px;
                    margin-bottom: 8px;
                ">
                    <strong>{response['title']}</strong><br>
                    <small>Submitted: {response['submitted_at'][:10]}</small>
                </div>
            """, unsafe_allow_html=True)
    else:
        st.info("You haven't completed any surveys yet")

def show_team_surveys():
    """Show team survey participation (Manager view)"""
    user = get_current_user()

    st.markdown("### 📋 Team Survey Participation")

    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Get active surveys
        cursor.execute("""
            SELECT * FROM surveys
            WHERE status = 'Active'
            AND end_date >= CURRENT_DATE
        """)
        active_surveys = [dict(row) for row in cursor.fetchall()]

    if active_surveys:
        for survey in active_surveys:
            with get_db_connection() as conn:
                cursor = conn.cursor()

                # Get team size
                cursor.execute("""
                    SELECT COUNT(*) as cnt FROM employees
                    WHERE manager_id = %s AND status = 'Active'
                """, (user['employee_id'],))
                team_size = cursor.fetchone()['cnt']

                # Get responses from team
                cursor.execute("""
                    SELECT COUNT(*) as cnt FROM survey_responses sr
                    JOIN employees e ON sr.emp_id = e.id
                    WHERE sr.survey_id = %s AND e.manager_id = %s
                """, (survey['id'], user['employee_id']))
                responses = cursor.fetchone()['cnt']

            participation = (responses / team_size * 100) if team_size > 0 else 0

            st.markdown(f"#### {survey['title']}")
            st.markdown(f"**Participation:** {responses}/{team_size} ({participation:.0f}%)")
            st.progress(participation / 100)
            st.markdown("---")
    else:
        st.info("No active surveys")

def show_team_survey_results():
    """Show team survey results"""
    st.markdown("### 📊 Team Survey Results")
    st.info("Detailed team survey results would be displayed here")

def show_team_feedback():
    """Show team feedback"""
    st.markdown("### 💬 Team Feedback")
    st.info("Team feedback overview would be displayed here")

def show_all_surveys():
    """Show all surveys (HR view)"""
    st.markdown("### 📊 All Surveys")

    # Filters
    col1, col2 = st.columns(2)
    with col1:
        status_filter = st.selectbox("Status", ["All", "Draft", "Active", "Closed"])
    with col2:
        search = st.text_input("🔍 Search")

    with get_db_connection() as conn:
        cursor = conn.cursor()

        query = "SELECT * FROM surveys WHERE 1=1"
        params = []

        if status_filter != "All":
            query += " AND status = %s"
            params.append(status_filter)

        if search:
            query += " AND (title LIKE %s OR description LIKE %s)"
            params.extend([f"%{search}%", f"%{search}%"])

        query += " ORDER BY created_at DESC"

        cursor.execute(query, params)
        surveys = [dict(row) for row in cursor.fetchall()]

    if surveys:
        for survey in surveys:
            # Get response count
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT COUNT(*) as cnt FROM survey_responses
                    WHERE survey_id = %s
                """, (survey['id'],))
                response_count = cursor.fetchone()['cnt']

            with st.expander(f"📋 {survey['title']} - {survey['status']} ({response_count} responses)"):
                st.markdown(f"""
                **Title:** {survey['title']}
                **Description:** {survey.get('description', 'N/A')}
                **Target:** {survey['target_audience']}
                **Start Date:** {survey['start_date']}
                **End Date:** {survey['end_date']}
                **Status:** {survey['status']}
                **Responses:** {response_count}
                """)

                # Actions
                col1, col2, col3 = st.columns(3)
                with col1:
                    if survey['status'] == 'Draft' and st.button("✅ Activate", key=f"act_{survey['id']}"):
                        update_survey_status(survey['id'], 'Active')
                        st.rerun()
                with col2:
                    if survey['status'] == 'Active' and st.button("🔒 Close", key=f"close_{survey['id']}"):
                        update_survey_status(survey['id'], 'Closed')
                        st.rerun()
                with col3:
                    if st.button("📊 View Results", key=f"results_{survey['id']}"):
                        st.info("Results view")
    else:
        st.info("No surveys found")

def show_create_survey():
    """Create new survey"""
    st.markdown("### ➕ Create New Survey")

    with st.form("create_survey"):
        title = st.text_input("Survey Title *", placeholder="e.g., Q1 Employee Engagement Survey")

        description = st.text_area(
            "Description",
            placeholder="Explain the purpose of this survey..."
        )

        col1, col2 = st.columns(2)

        with col1:
            target_audience = st.selectbox("Target Audience *", ["All", "Department", "Team"])
            start_date = st.date_input("Start Date *", value=date.today())

        with col2:
            if target_audience == "Department":
                target_dept = st.selectbox("Department", [
                    "Engineering", "Sales", "Marketing", "HR", "Finance", "Operations"
                ])
            else:
                target_dept = None

            end_date = st.date_input("End Date *", value=date.today() + timedelta(days=14))

        survey_type = st.selectbox("Survey Type", [
            "Engagement",
            "Satisfaction",
            "Feedback",
            "Pulse Check",
            "Exit Survey",
            "Custom"
        ])

        submitted = st.form_submit_button("📋 Create Survey", use_container_width=True)

        if submitted:
            if title and start_date and end_date:
                create_survey(title, description, target_audience, target_dept,
                            start_date, end_date, survey_type)
                st.rerun()
            else:
                st.error("❌ Please fill all required fields")

def show_survey_results():
    """Show survey results and analytics"""
    st.markdown("### 📈 Survey Results & Analytics")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM surveys
            WHERE status IN ('Active', 'Closed')
            ORDER BY created_at DESC
        """)
        surveys = [dict(row) for row in cursor.fetchall()]

    if surveys:
        survey_options = {f"{s['title']} ({s['status']})": s['id'] for s in surveys}
        selected = st.selectbox("Select Survey", list(survey_options.keys()))

        if selected:
            survey_id = survey_options[selected]

            with get_db_connection() as conn:
                cursor = conn.cursor()

                # Total responses
                cursor.execute("""
                    SELECT COUNT(*) as cnt FROM survey_responses
                    WHERE survey_id = %s
                """, (survey_id,))
                total_responses = cursor.fetchone()['cnt']

                # Average completion time (if tracked)
                cursor.execute("""
                    SELECT AVG(EXTRACT(EPOCH FROM (submitted_at - started_at))/86400.0) as avg_time
                    FROM survey_responses
                    WHERE survey_id = %s AND started_at IS NOT NULL
                """, (survey_id,))
                avg_time_result = cursor.fetchone()

            col1, col2 = st.columns(2)
            with col1:
                st.metric("Total Responses", total_responses)
            with col2:
                avg_time = avg_time_result['avg_time'] if avg_time_result and avg_time_result['avg_time'] else 0
                st.metric("Avg. Completion Time", f"{avg_time:.1f} min" if avg_time else "N/A")

            st.markdown("---")
            st.markdown("### 📊 Response Analysis")
            st.info("Detailed response breakdown and analytics would be displayed here with charts")
    else:
        st.info("No surveys with responses yet")

def show_feedback_management():
    """Manage employee feedback"""
    st.markdown("### 💬 Employee Feedback Management")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT f.*, e.first_name, e.last_name, e.employee_id
            FROM feedback f
            LEFT JOIN employees e ON f.emp_id = e.id
            ORDER BY f.created_at DESC
            LIMIT 50
        """)
        feedback_items = [dict(row) for row in cursor.fetchall()]

    if feedback_items:
        for item in feedback_items:
            author = f"{item.get('first_name', 'Anonymous')} {item.get('last_name', '')}" if item['emp_id'] else "Anonymous"

            with st.expander(f"💬 {item['subject']} - {author}"):
                st.markdown(f"""
                **From:** {author}
                **Type:** {item['feedback_type']}
                **Date:** {item['created_at'][:10]}
                **Status:** {item.get('status', 'New')}
                """)

                st.markdown("---")
                st.markdown(f"**Feedback:**")
                st.info(item['feedback_text'])

                # HR response
                if item.get('hr_response'):
                    st.success(f"**HR Response:** {item['hr_response']}")
                else:
                    with st.form(f"respond_{item['id']}"):
                        response = st.text_area("HR Response")
                        if st.form_submit_button("💬 Respond"):
                            add_feedback_response(item['id'], response)
                            st.rerun()
    else:
        st.info("No feedback submitted yet")

def create_survey(title, description, target_audience, target_dept, start_date, end_date, survey_type):
    """Create new survey"""
    user = get_current_user()

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO surveys (
                    title, description, target_audience, target_department,
                    start_date, end_date, survey_type, status, created_by
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, 'Draft', %s)
            """, (title, description, target_audience, target_dept,
                 start_date.isoformat(), end_date.isoformat(), survey_type, user['employee_id']))

            survey_id = cursor.lastrowid

            conn.commit()
            log_audit(f"Created survey: {title}", "surveys", survey_id)
            st.success(f"✅ Survey created! ID: SUR-{survey_id}")
            st.balloons()

    except Exception as e:
        st.error(f"❌ Error: {str(e)}")

def update_survey_status(survey_id, status):
    """Update survey status"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE surveys SET status = %s WHERE id = %s", (status, survey_id))
            conn.commit()
            log_audit(f"Updated survey {survey_id} status to {status}", "surveys", survey_id)
            st.success(f"✅ Survey {status.lower()}!")

    except Exception as e:
        st.error(f"❌ Error: {str(e)}")

def submit_survey_response(survey_id, emp_id, responses):
    """Submit survey response"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # Convert responses to JSON string
            import json
            responses_json = json.dumps(responses)

            cursor.execute("""
                INSERT INTO survey_responses (
                    survey_id, emp_id, responses, submitted_at
                ) VALUES (%s, %s, %s, %s)
            """, (survey_id, emp_id, responses_json, datetime.now().isoformat()))

            conn.commit()
            log_audit(f"Submitted survey response {survey_id}", "survey_responses", survey_id)
            st.success("✅ Survey submitted! Thank you for your feedback!")
            st.balloons()

    except Exception as e:
        st.error(f"❌ Error: {str(e)}")

def submit_feedback(emp_id, feedback_type, subject, feedback_text):
    """Submit employee feedback"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO feedback (
                    emp_id, feedback_type, subject, feedback_text, status
                ) VALUES (%s, %s, %s, %s, 'New')
            """, (emp_id, feedback_type, subject, feedback_text))

            feedback_id = cursor.lastrowid

            # Notify HR
            cursor.execute("SELECT id FROM employees WHERE role = 'HR Admin' LIMIT 1")
            hr = cursor.fetchone()
            if hr:
                create_notification(hr['id'], f"New feedback received: {subject}", "feedback")

            conn.commit()
            log_audit(f"Submitted feedback: {subject}", "feedback", feedback_id)

    except Exception as e:
        st.error(f"❌ Error: {str(e)}")

def add_feedback_response(feedback_id, response):
    """Add HR response to feedback"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                UPDATE feedback SET
                    hr_response = %s,
                    status = 'Responded',
                    responded_at = %s
                WHERE id = %s
            """, (response, datetime.now().isoformat(), feedback_id))

            # Notify employee if not anonymous
            cursor.execute("SELECT emp_id FROM feedback WHERE id = %s", (feedback_id,))
            feedback = cursor.fetchone()
            if feedback and feedback['emp_id']:
                create_notification(feedback['emp_id'], "HR has responded to your feedback", "feedback")

            conn.commit()
            log_audit(f"Responded to feedback {feedback_id}", "feedback", feedback_id)
            st.success("✅ Response added!")

    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
