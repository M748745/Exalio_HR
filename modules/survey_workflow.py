"""
Survey Workflow Module
Create surveys, distribute, collect responses, and analyze results
"""

import streamlit as st
from datetime import datetime, date
from database import get_db_connection
from auth import get_current_user, is_hr_admin, is_manager, create_notification, log_audit

def show_survey_workflow():
    """Main survey workflow interface"""
    user = get_current_user()

    st.markdown("## 📊 Survey Management")
    st.markdown("Create, distribute, and analyze employee surveys")
    st.markdown("---")

    if is_hr_admin():
        tabs = st.tabs(["📊 All Surveys", "➕ Create Survey", "📈 Results & Analytics", "📋 Active Surveys"])
    elif is_manager():
        tabs = st.tabs(["📊 Available Surveys", "📈 Team Responses"])
    else:
        tabs = st.tabs(["📊 My Surveys", "✅ Complete Survey"])

    with tabs[0]:
        if is_hr_admin():
            show_all_surveys()
        elif is_manager():
            show_available_surveys_manager()
        else:
            show_my_surveys()

    if is_hr_admin() and len(tabs) > 1:
        with tabs[1]:
            create_survey()
        with tabs[2]:
            show_survey_analytics()
        with tabs[3]:
            show_active_surveys()
    elif is_manager() and len(tabs) > 1:
        with tabs[1]:
            show_team_responses()
    elif not is_hr_admin() and not is_manager() and len(tabs) > 1:
        with tabs[1]:
            complete_survey()

def show_all_surveys():
    """Show all surveys"""
    st.markdown("### 📊 All Surveys")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT s.*, e.first_name, e.last_name,
                   COUNT(DISTINCT sr.id) as response_count
            FROM surveys s
            JOIN employees e ON s.created_by = e.id
            LEFT JOIN survey_responses sr ON s.id = sr.survey_id
            GROUP BY s.id, s.title, s.description, s.survey_type, s.status, s.created_at,
                     s.start_date, s.end_date, s.target_audience, s.created_by,
                     e.first_name, e.last_name
            ORDER BY s.created_at DESC
        """)
        surveys = [dict(row) for row in cursor.fetchall()]

    if surveys:
        for survey in surveys:
            status_icon = '✅' if survey['status'] == 'Closed' else '🟢' if survey['status'] == 'Active' else '📝'
            with st.expander(f"{status_icon} {survey['title']} - {survey['status']} - {survey['response_count']} responses"):
                col1, col2 = st.columns([2, 1])
                with col1:
                    st.write(f"**Description:** {survey['description']}")
                    st.write(f"**Type:** {survey['survey_type']}")
                    st.write(f"**Created by:** {survey['first_name']} {survey['last_name']}")
                with col2:
                    st.metric("Responses", survey['response_count'])
                    st.write(f"**Target:** {survey['target_audience']}")
                    st.write(f"**Period:** {survey['start_date']} to {survey['end_date']}")
                    st.write(f"**Status:** {survey['status']}")

                if survey['status'] == 'Draft':
                    if st.button(f"▶️ Activate Survey - {survey['id']}", key=f"activate_{survey['id']}"):
                        with get_db_connection() as conn:
                            cursor = conn.cursor()
                            cursor.execute("""
                                UPDATE surveys SET status = 'Active' WHERE id = %s
                            """, (survey['id'],))
                            conn.commit()

                        # Notify target audience
                        with get_db_connection() as conn:
                            cursor = conn.cursor()
                            if survey['target_audience'] == 'All':
                                cursor.execute("SELECT id FROM employees WHERE status = 'Active'")
                            else:
                                cursor.execute("SELECT id FROM employees WHERE department = %s AND status = 'Active'", (survey['target_audience'],))

                            employees = cursor.fetchall()
                            for emp in employees:
                                create_notification(emp['id'], f"New Survey: {survey['title']}",
                                                  survey['description'], 'info')

                        st.success("✅ Survey activated!")
                        st.rerun()

                elif survey['status'] == 'Active':
                    if st.button(f"⏸️ Close Survey - {survey['id']}", key=f"close_{survey['id']}"):
                        with get_db_connection() as conn:
                            cursor = conn.cursor()
                            cursor.execute("UPDATE surveys SET status = 'Closed' WHERE id = %s", (survey['id'],))
                            conn.commit()
                        st.success("✅ Survey closed!")
                        st.rerun()
    else:
        st.info("No surveys created")

def create_survey():
    """Create new survey"""
    st.markdown("### ➕ Create Survey")

    with st.form("create_survey"):
        title = st.text_input("Survey Title *")
        description = st.text_area("Description *")

        col1, col2 = st.columns(2)
        with col1:
            survey_type = st.selectbox("Survey Type *", ["Employee Satisfaction", "Engagement", "360 Feedback", "Exit Survey", "Training Feedback", "Pulse Check", "Other"])
            target_audience = st.selectbox("Target Audience *", ["All", "Engineering", "Sales", "Marketing", "HR", "Finance", "Operations"])
        with col2:
            start_date = st.date_input("Start Date *", value=date.today())
            end_date = st.date_input("End Date *")

        st.markdown("#### Survey Questions")
        num_questions = st.number_input("Number of Questions", min_value=1, max_value=20, value=5)

        questions = []
        for i in range(int(num_questions)):
            with st.expander(f"Question {i+1}"):
                q_text = st.text_input(f"Question {i+1} *", key=f"q_{i}")
                q_type = st.selectbox(f"Type", ["Rating (1-5)", "Yes/No", "Text"], key=f"type_{i}")
                if q_text:
                    questions.append({"question": q_text, "type": q_type})

        is_anonymous = st.checkbox("Anonymous Responses")

        submitted = st.form_submit_button("💾 Create Survey")

        if submitted and title and description and len(questions) > 0:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO surveys (title, description, survey_type, target_audience,
                                        start_date, end_date, is_anonymous, status, created_by)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, 'Draft', %s)
                """, (title, description, survey_type, target_audience,
                     start_date, end_date, is_anonymous, get_current_user()['employee_id']))
                survey_id = cursor.lastrowid

                # Save questions
                for idx, q in enumerate(questions):
                    cursor.execute("""
                        INSERT INTO survey_questions (survey_id, question_text, question_type, question_order)
                        VALUES (%s, %s, %s, %s)
                    """, (survey_id, q['question'], q['type'], idx + 1))

                conn.commit()

            log_audit(get_current_user()['id'], f"Created survey: {title}", "surveys")
            st.success(f"✅ Survey created with {len(questions)} questions!")

def show_my_surveys():
    """Show surveys available to employee"""
    user = get_current_user()
    st.markdown("### 📊 Available Surveys")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT department FROM employees WHERE id = %s", (user['employee_id'],))
        dept = cursor.fetchone()['department']

        cursor.execute("""
            SELECT s.*,
                   CASE WHEN sr.id IS NOT NULL THEN 1 ELSE 0 END as completed
            FROM surveys s
            LEFT JOIN survey_responses sr ON s.id = sr.survey_id AND sr.emp_id = %s
            WHERE s.status = 'Active'
              AND (s.target_audience = 'All' OR s.target_audience = %s)
              AND s.end_date >= CURRENT_DATE
            ORDER BY s.end_date
        """, (user['employee_id'], dept))
        surveys = [dict(row) for row in cursor.fetchall()]

    if surveys:
        for survey in surveys:
            completion_icon = '✅' if survey['completed'] else '📝'
            st.write(f"{completion_icon} **{survey['title']}** - {survey['survey_type']} - Due: {survey['end_date']}")
            if not survey['completed']:
                st.caption(f"📋 {survey['description']}")
    else:
        st.info("No surveys available")

def complete_survey():
    """Complete a survey"""
    user = get_current_user()
    st.markdown("### ✅ Complete Survey")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT department FROM employees WHERE id = %s", (user['employee_id'],))
        dept = cursor.fetchone()['department']

        cursor.execute("""
            SELECT s.*
            FROM surveys s
            LEFT JOIN survey_responses sr ON s.id = sr.survey_id AND sr.emp_id = %s
            WHERE s.status = 'Active'
              AND sr.id IS NULL
              AND (s.target_audience = 'All' OR s.target_audience = %s)
              AND s.end_date >= CURRENT_DATE
            ORDER BY s.end_date
        """, (user['employee_id'], dept))
        surveys = [dict(row) for row in cursor.fetchall()]

    if surveys:
        survey_options = {f"{s['title']} (Due: {s['end_date']})": s['id'] for s in surveys}
        selected_survey = st.selectbox("Select Survey", list(survey_options.keys()))

        if selected_survey:
            survey_id = survey_options[selected_survey]

            # Get survey questions
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM survey_questions
                    WHERE survey_id = %s
                    ORDER BY question_order
                """, (survey_id,))
                questions = [dict(row) for row in cursor.fetchall()]

            if questions:
                with st.form("survey_response"):
                    responses = {}
                    for q in questions:
                        st.markdown(f"**{q['question_order']}. {q['question_text']}**")
                        if q['question_type'] == "Rating (1-5)":
                            responses[q['id']] = st.slider(f"Rating - Q{q['question_order']}", 1, 5, 3, key=f"q_{q['id']}")
                        elif q['question_type'] == "Yes/No":
                            responses[q['id']] = "Yes" if st.checkbox(f"Yes - Q{q['question_order']}", key=f"q_{q['id']}") else "No"
                        else:  # Text
                            responses[q['id']] = st.text_area(f"Answer - Q{q['question_order']}", key=f"q_{q['id']}")

                    submitted = st.form_submit_button("💾 Submit Survey")

                    if submitted:
                        with get_db_connection() as conn:
                            cursor = conn.cursor()

                            # Create response record
                            cursor.execute("""
                                INSERT INTO survey_responses (survey_id, emp_id, response_date)
                                VALUES (%s, %s, %s)
                            """, (survey_id, user['employee_id'], date.today()))
                            response_id = cursor.lastrowid

                            # Save answers
                            for question_id, answer in responses.items():
                                cursor.execute("""
                                    INSERT INTO survey_answers (response_id, question_id, answer_value)
                                    VALUES (%s, %s, %s)
                                """, (response_id, question_id, str(answer)))

                            conn.commit()

                        st.success("✅ Survey submitted! Thank you for your feedback.")
                        st.rerun()
    else:
        st.success("✅ You've completed all available surveys!")

def show_survey_analytics():
    """Show survey results and analytics"""
    st.markdown("### 📈 Survey Results & Analytics")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM surveys WHERE status IN ('Active', 'Closed') ORDER BY created_at DESC
        """)
        surveys = [dict(row) for row in cursor.fetchall()]

    if surveys:
        survey_options = {s['title']: s['id'] for s in surveys}
        selected_survey = st.selectbox("Select Survey", list(survey_options.keys()))

        if selected_survey:
            survey_id = survey_options[selected_survey]

            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT COUNT(*) as response_count FROM survey_responses WHERE survey_id = %s
                """, (survey_id,))
                response_count = cursor.fetchone()['response_count']

            st.metric("Total Responses", response_count)

            # Show question-wise analytics
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM survey_questions WHERE survey_id = %s ORDER BY question_order
                """, (survey_id,))
                questions = [dict(row) for row in cursor.fetchall()]

            for q in questions:
                st.markdown(f"**{q['question_order']}. {q['question_text']}**")

                with get_db_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT answer_value, COUNT(*) as count
                        FROM survey_answers
                        WHERE question_id = %s
                        GROUP BY answer_value
                        ORDER BY count DESC
                    """, (q['id'],))
                    answers = [dict(row) for row in cursor.fetchall()]

                if answers and q['question_type'] == "Rating (1-5)":
                    ratings = {int(a['answer_value']): a['count'] for a in answers if a['answer_value'].isdigit()}
                    avg_rating = sum(rating * count for rating, count in ratings.items()) / sum(ratings.values()) if ratings else 0
                    st.metric("Average Rating", f"{avg_rating:.2f}/5")

                elif answers:
                    for ans in answers:
                        st.write(f"- {ans['answer_value']}: {ans['count']} responses")

                st.markdown("---")
    else:
        st.info("No surveys with responses")

def show_active_surveys():
    """Show active surveys"""
    st.markdown("### 📋 Active Surveys")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT s.*, COUNT(DISTINCT sr.id) as responses
            FROM surveys s
            LEFT JOIN survey_responses sr ON s.id = sr.survey_id
            WHERE s.status = 'Active'
            GROUP BY s.id
            ORDER BY s.end_date
        """)
        active = [dict(row) for row in cursor.fetchall()]

    if active:
        for survey in active:
            st.write(f"🟢 **{survey['title']}** - {survey['responses']} responses - Ends: {survey['end_date']}")
    else:
        st.info("No active surveys")

def show_available_surveys_manager():
    """Show available surveys for managers"""
    show_my_surveys()

def show_team_responses():
    """Show team survey responses"""
    st.markdown("### 📈 Team Survey Responses")
    st.info("View survey participation rates for your team")
