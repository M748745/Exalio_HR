"""
Appraisal Calibration Module
Conduct calibration sessions, adjust ratings, build consensus, and finalize appraisals
"""

import streamlit as st
from datetime import datetime, date
from database import get_db_connection
from auth import get_current_user, is_hr_admin, is_manager, create_notification, log_audit

def show_appraisal_calibration():
    """Main appraisal calibration interface"""
    user = get_current_user()

    st.markdown("## ⚖️ Appraisal Calibration")
    st.markdown("Calibrate performance ratings across teams for fairness and consistency")
    st.markdown("---")

    if is_hr_admin():
        tabs = st.tabs(["📊 Calibration Sessions", "➕ Create Session", "📈 Rating Distribution", "✅ Finalize Appraisals"])
    elif is_manager():
        tabs = st.tabs(["📋 My Sessions", "👥 Team Ratings"])
    else:
        tabs = st.tabs(["📊 Calibration Status"])

    with tabs[0]:
        if is_hr_admin():
            show_all_calibration_sessions()
        elif is_manager():
            show_manager_sessions()
        else:
            show_calibration_status()

    if is_hr_admin() and len(tabs) > 1:
        with tabs[1]:
            create_calibration_session()
        with tabs[2]:
            show_rating_distribution()
        with tabs[3]:
            finalize_appraisals()
    elif is_manager() and len(tabs) > 1:
        with tabs[1]:
            show_team_ratings()

def show_all_calibration_sessions():
    """Show all calibration sessions"""
    st.markdown("### 📊 All Calibration Sessions")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT cs.*, e.first_name, e.last_name,
                   COUNT(DISTINCT csr.id) as ratings_count
            FROM calibration_sessions cs
            JOIN employees e ON cs.created_by = e.id
            LEFT JOIN calibration_session_ratings csr ON cs.id = csr.session_id
            GROUP BY cs.id, cs.session_name, cs.session_date, cs.review_period,
                     cs.departments, cs.status, cs.created_by, cs.created_at,
                     e.first_name, e.last_name
            ORDER BY cs.session_date DESC
        """)
        sessions = [dict(row) for row in cursor.fetchall()]

    if sessions:
        for session in sessions:
            status_icon = '✅' if session['status'] == 'Completed' else '🟡' if session['status'] == 'In Progress' else '📝'
            with st.expander(f"{status_icon} {session['session_name']} - {session['review_period']} - {session['status']}"):
                col1, col2 = st.columns([2, 1])
                with col1:
                    st.write(f"**Session Date:** {session['session_date']}")
                    st.write(f"**Departments:** {session['departments']}")
                    st.write(f"**Created by:** {session['first_name']} {session['last_name']}")
                with col2:
                    st.metric("Ratings Reviewed", session['ratings_count'])
                    st.write(f"**Status:** {session['status']}")

                if session['status'] == 'Scheduled':
                    if st.button(f"▶️ Start Session - {session['id']}", key=f"start_{session['id']}"):
                        with get_db_connection() as conn:
                            cursor = conn.cursor()
                            cursor.execute("""
                                UPDATE calibration_sessions SET status = 'In Progress' WHERE id = %s
                            """, (session['id'],))
                            conn.commit()
                        st.success("✅ Session started!")
                        st.rerun()

                elif session['status'] == 'In Progress':
                    # Show ratings to calibrate
                    with get_db_connection() as conn:
                        cursor = conn.cursor()
                        cursor.execute("""
                            SELECT csr.*, e.first_name, e.last_name, e.position, e.department,
                                   a.rating as current_rating
                            FROM calibration_session_ratings csr
                            JOIN employees e ON csr.emp_id = e.id
                            LEFT JOIN appraisals a ON csr.appraisal_id = a.id
                            WHERE csr.session_id = %s
                            ORDER BY e.department, e.first_name
                        """, (session['id'],))
                        ratings = [dict(row) for row in cursor.fetchall()]

                    if ratings:
                        st.markdown("#### Ratings to Calibrate")
                        for rating in ratings:
                            with st.expander(f"{rating['first_name']} {rating['last_name']} - {rating['position']} ({rating['department']})"):
                                col1, col2, col3 = st.columns(3)
                                with col1:
                                    st.metric("Initial Rating", rating['initial_rating'])
                                with col2:
                                    st.metric("Calibrated Rating", rating['calibrated_rating'] or "Not Set")
                                with col3:
                                    new_rating = st.selectbox(f"Adjust Rating - {rating['id']}",
                                                            ["Outstanding", "Exceeds Expectations", "Meets Expectations",
                                                             "Needs Improvement", "Unsatisfactory"],
                                                            key=f"rating_{rating['id']}")

                                justification = st.text_area(f"Calibration Justification - {rating['id']}", key=f"just_{rating['id']}")

                                if st.button(f"💾 Update Rating - {rating['id']}", key=f"update_{rating['id']}"):
                                    with get_db_connection() as conn:
                                        cursor = conn.cursor()
                                        cursor.execute("""
                                            UPDATE calibration_session_ratings SET
                                                calibrated_rating = %s,
                                                calibration_notes = %s,
                                                calibrated_by = %s,
                                                calibration_date = %s
                                            WHERE id = %s
                                        """, (new_rating, justification, get_current_user()['employee_id'],
                                             date.today(), rating['id']))
                                        conn.commit()
                                    st.success("✅ Rating updated!")
                                    st.rerun()

                    if st.button(f"✅ Complete Session - {session['id']}", key=f"complete_{session['id']}"):
                        with get_db_connection() as conn:
                            cursor = conn.cursor()
                            cursor.execute("""
                                UPDATE calibration_sessions SET status = 'Completed' WHERE id = %s
                            """, (session['id'],))
                            conn.commit()
                        st.success("✅ Calibration session completed!")
                        st.rerun()
    else:
        st.info("No calibration sessions created")

def create_calibration_session():
    """Create new calibration session"""
    st.markdown("### ➕ Create Calibration Session")

    with st.form("create_session"):
        session_name = st.text_input("Session Name *")
        session_date = st.date_input("Session Date *", value=date.today())

        col1, col2 = st.columns(2)
        with col1:
            review_period = st.selectbox("Review Period *", ["Q1 2024", "Q2 2024", "Q3 2024", "Q4 2024", "Annual 2024"])
        with col2:
            departments = st.multiselect("Departments *", ["Engineering", "Sales", "Marketing", "HR", "Finance", "Operations"])

        notes = st.text_area("Session Notes")

        submitted = st.form_submit_button("💾 Create Session")

        if submitted and session_name and departments:
            dept_str = ", ".join(departments)

            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO calibration_sessions (session_name, session_date, review_period,
                                                      departments, notes, status, created_by)
                    VALUES (%s, %s, %s, %s, %s, 'Scheduled', %s)
                """, (session_name, session_date, review_period, dept_str, notes,
                     get_current_user()['employee_id']))
                session_id = cursor.lastrowid

                # Add appraisals from selected departments to the session
                for dept in departments:
                    cursor.execute("""
                        SELECT a.id, a.emp_id, a.rating
                        FROM appraisals a
                        JOIN employees e ON a.emp_id = e.id
                        WHERE e.department = %s AND a.status IN ('Manager Review', 'HR Review')
                        ORDER BY e.first_name
                    """, (dept,))
                    appraisals = cursor.fetchall()

                    for appraisal in appraisals:
                        cursor.execute("""
                            INSERT INTO calibration_session_ratings (session_id, emp_id, appraisal_id, initial_rating)
                            VALUES (%s, %s, %s, %s)
                        """, (session_id, appraisal['emp_id'], appraisal['id'], appraisal['rating']))

                conn.commit()

            log_audit(get_current_user()['id'], f"Created calibration session: {session_name}", "calibration_sessions")
            st.success(f"✅ Calibration session created!")

def show_rating_distribution():
    """Show rating distribution across company"""
    st.markdown("### 📈 Rating Distribution Analysis")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT
                rating,
                COUNT(*) as count,
                ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1) as percentage
            FROM appraisals
            WHERE status IN ('Manager Review', 'HR Review', 'Finalized')
            GROUP BY rating
            ORDER BY
                CASE rating
                    WHEN 'Outstanding' THEN 1
                    WHEN 'Exceeds Expectations' THEN 2
                    WHEN 'Meets Expectations' THEN 3
                    WHEN 'Needs Improvement' THEN 4
                    WHEN 'Unsatisfactory' THEN 5
                END
        """)
        distribution = [dict(row) for row in cursor.fetchall()]

    if distribution:
        st.markdown("#### Overall Rating Distribution")
        for dist in distribution:
            st.write(f"**{dist['rating']}:** {dist['count']} employees ({dist['percentage']}%)")
            st.progress(dist['percentage'] / 100)
            st.markdown("---")

        # Department-wise distribution
        st.markdown("#### Department-wise Distribution")
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    e.department,
                    a.rating,
                    COUNT(*) as count
                FROM appraisals a
                JOIN employees e ON a.emp_id = e.id
                WHERE a.status IN ('Manager Review', 'HR Review', 'Finalized')
                GROUP BY e.department, a.rating
                ORDER BY e.department, a.rating
            """)
            dept_dist = [dict(row) for row in cursor.fetchall()]

        if dept_dist:
            current_dept = None
            for item in dept_dist:
                if item['department'] != current_dept:
                    current_dept = item['department']
                    st.markdown(f"**{current_dept}:**")
                st.write(f"  - {item['rating']}: {item['count']}")
    else:
        st.info("No rating data available")

def finalize_appraisals():
    """Finalize appraisals after calibration"""
    st.markdown("### ✅ Finalize Appraisals")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT csr.*,
                   e.first_name, e.last_name, e.department,
                   a.id as appraisal_id
            FROM calibration_session_ratings csr
            JOIN calibration_sessions cs ON csr.session_id = cs.id
            JOIN employees e ON csr.emp_id = e.id
            LEFT JOIN appraisals a ON csr.appraisal_id = a.id
            WHERE cs.status = 'Completed'
              AND csr.calibrated_rating IS NOT NULL
              AND a.status != 'Finalized'
            ORDER BY e.department, e.first_name
        """)
        ratings = [dict(row) for row in cursor.fetchall()]

    if ratings:
        st.info(f"📋 {len(ratings)} appraisals ready to finalize")

        for rating in ratings:
            with st.expander(f"{rating['first_name']} {rating['last_name']} - {rating['department']}"):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Initial Rating:** {rating['initial_rating']}")
                with col2:
                    st.write(f"**Calibrated Rating:** {rating['calibrated_rating']}")

                if rating.get('calibration_notes'):
                    st.info(f"Calibration Notes: {rating['calibration_notes']}")

                if st.button(f"✅ Finalize Appraisal - {rating['id']}", key=f"finalize_{rating['id']}"):
                    with get_db_connection() as conn:
                        cursor = conn.cursor()

                        # Update appraisal with calibrated rating
                        cursor.execute("""
                            UPDATE appraisals SET
                                rating = %s,
                                status = 'Finalized',
                                finalized_date = %s,
                                finalized_by = %s
                            WHERE id = %s
                        """, (rating['calibrated_rating'], date.today(),
                             get_current_user()['employee_id'], rating['appraisal_id']))

                        conn.commit()

                    create_notification(rating['emp_id'], "Appraisal Finalized",
                                      f"Your performance appraisal has been finalized. Final Rating: {rating['calibrated_rating']}", "info")
                    log_audit(get_current_user()['id'], f"Finalized appraisal for employee {rating['emp_id']}", "appraisals")
                    st.success("✅ Appraisal finalized!")
                    st.rerun()

        if st.button("✅ Finalize All"):
            with get_db_connection() as conn:
                cursor = conn.cursor()
                for rating in ratings:
                    cursor.execute("""
                        UPDATE appraisals SET
                            rating = %s,
                            status = 'Finalized',
                            finalized_date = %s,
                            finalized_by = %s
                        WHERE id = %s
                    """, (rating['calibrated_rating'], date.today(),
                         get_current_user()['employee_id'], rating['appraisal_id']))

                    create_notification(rating['emp_id'], "Appraisal Finalized",
                                      f"Your performance appraisal has been finalized. Final Rating: {rating['calibrated_rating']}", "info")

                conn.commit()

            st.success(f"✅ All {len(ratings)} appraisals finalized!")
            st.rerun()
    else:
        st.success("✅ No appraisals pending finalization")

def show_manager_sessions():
    """Show manager's calibration sessions"""
    st.markdown("### 📋 My Calibration Sessions")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT department FROM employees WHERE id = %s", (get_current_user()['employee_id'],))
        dept_row = cursor.fetchone()

        if dept_row:
            dept = dept_row['department']
            cursor.execute("""
                SELECT cs.*, COUNT(DISTINCT csr.id) as ratings_count
                FROM calibration_sessions cs
                LEFT JOIN calibration_session_ratings csr ON cs.id = csr.session_id
                WHERE cs.departments LIKE %s
                GROUP BY cs.id
                ORDER BY cs.session_date DESC
            """, (f'%{dept}%',))
            sessions = [dict(row) for row in cursor.fetchall()]

            if sessions:
                for session in sessions:
                    st.write(f"**{session['session_name']}** - {session['session_date']} - {session['status']} - {session['ratings_count']} ratings")
            else:
                st.info("No calibration sessions for your department")

def show_team_ratings():
    """Show team ratings for calibration"""
    user = get_current_user()
    st.markdown("### 👥 Team Ratings for Calibration")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT department FROM employees WHERE id = %s", (user['employee_id'],))
        dept_row = cursor.fetchone()

        if dept_row:
            dept = dept_row['department']
            cursor.execute("""
                SELECT e.first_name, e.last_name, e.position, a.rating, a.status
                FROM employees e
                LEFT JOIN appraisals a ON e.id = a.emp_id
                WHERE e.department = %s AND e.status = 'Active'
                ORDER BY e.first_name
            """, (dept,))
            team_ratings = [dict(row) for row in cursor.fetchall()]

            if team_ratings:
                for member in team_ratings:
                    rating = member['rating'] if member['rating'] else "Not Rated"
                    st.write(f"👤 {member['first_name']} {member['last_name']} - {member['position']} - Rating: {rating}")
            else:
                st.info("No team members found")

def show_calibration_status():
    """Show calibration status for employees"""
    user = get_current_user()
    st.markdown("### 📊 My Appraisal Calibration Status")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT csr.*, cs.session_name, cs.session_date, cs.status
            FROM calibration_session_ratings csr
            JOIN calibration_sessions cs ON csr.session_id = cs.id
            WHERE csr.emp_id = %s
            ORDER BY cs.session_date DESC
            LIMIT 1
        """, (user['employee_id'],))
        calibration = cursor.fetchone()

    if calibration:
        calibration = dict(calibration)
        if calibration['calibrated_rating']:
            st.success(f"✅ Your appraisal has been calibrated")
            st.write(f"**Session:** {calibration['session_name']}")
            st.write(f"**Initial Rating:** {calibration['initial_rating']}")
            st.write(f"**Calibrated Rating:** {calibration['calibrated_rating']}")
        else:
            st.info(f"🟡 Your appraisal is under calibration in session: {calibration['session_name']}")
    else:
        st.info("Your appraisal has not entered calibration yet")
