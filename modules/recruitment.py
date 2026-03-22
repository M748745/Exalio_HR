"""
Recruitment & Job Applications Module
Post jobs, manage applications, shortlist candidates, schedule interviews
"""

import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
from database import get_db_connection
from auth import get_current_user, is_hr_admin, is_manager, create_notification, log_audit

def show_recruitment_management():
    """Main recruitment management interface"""
    user = get_current_user()

    st.markdown("## 💼 Recruitment & Hiring")
    st.markdown("Manage job postings and applications")
    st.markdown("---")

    if is_hr_admin():
        tabs = st.tabs(["📋 Job Postings", "📥 Applications", "⭐ Shortlisted", "📅 Interviews", "➕ Post Job"])
    elif is_manager():
        tabs = st.tabs(["📋 Department Jobs", "📥 Applications", "⭐ Shortlisted"])
    else:
        st.warning("This module is available for HR Admin and Managers only")
        return

    with tabs[0]:
        if is_hr_admin():
            show_all_jobs()
        else:
            show_department_jobs()

    with tabs[1]:
        show_applications()

    with tabs[2]:
        show_shortlisted_candidates()

    if len(tabs) > 3:
        with tabs[3]:
            show_interviews()

    if len(tabs) > 4:
        with tabs[4]:
            show_post_job()

def show_all_jobs():
    """Show all job postings"""
    st.markdown("### 📋 All Job Postings")

    # Filters
    col1, col2, col3 = st.columns(3)
    with col1:
        status_filter = st.selectbox("Status", ["All", "Open", "Closed", "On Hold"])
    with col2:
        dept_filter = st.selectbox("Department", ["All", "Engineering", "Product", "Sales", "Marketing", "Human Resources", "Finance"])
    with col3:
        search = st.text_input("🔍 Search")

    with get_db_connection() as conn:
        cursor = conn.cursor()

        query = """
            SELECT j.*, e.first_name, e.last_name,
                   (SELECT COUNT(*) FROM job_applications WHERE job_id = j.id) as application_count
            FROM jobs j
            LEFT JOIN employees e ON j.posted_by = e.id
            WHERE 1=1
        """
        params = []

        if status_filter != "All":
            query += " AND j.status = %s"
            params.append(status_filter)

        if dept_filter != "All":
            query += " AND j.department = %s"
            params.append(dept_filter)

        if search:
            query += " AND (j.title LIKE %s OR j.description LIKE %s)"
            params.extend([f"%{search}%", f"%{search}%"])

        query += " ORDER BY j.created_at DESC"

        cursor.execute(query, params)
        jobs = [dict(row) for row in cursor.fetchall()]

    if jobs:
        for job in jobs:
            status_color = {
                'Open': 'rgba(45, 212, 170, 0.1)',
                'Closed': 'rgba(125, 150, 190, 0.1)',
                'On Hold': 'rgba(240, 180, 41, 0.1)'
            }.get(job['status'], 'rgba(58, 123, 213, 0.05)')

            with st.expander(f"💼 {job['title']} - {job['department']} ({job['application_count']} applications)"):
                col1, col2 = st.columns([2, 1])

                with col1:
                    posted_date = job['created_at'].strftime('%Y-%m-%d') if job['created_at'] else 'N/A'
                    st.markdown(f"""
                    **Position:** {job['title']}
                    **Department:** {job['department']}
                    **Location:** {job['location']}
                    **Job Type:** {job.get('job_type', 'Full-time')}
                    **Salary Range:** {job.get('salary_range', 'Competitive')}
                    **Status:** {job['status']}
                    **Posted:** {posted_date}
                    **Posted by:** {job['first_name'] or 'N/A'} {job['last_name'] or ''}
                    """)

                with col2:
                    st.metric("Applications", job['application_count'])

                st.markdown(f"**Description:**\n{job['description']}")
                if job['requirements']:
                    st.markdown(f"**Requirements:**\n{job['requirements']}")

                # Actions
                if job['status'] == 'Open':
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("⏸️ Put On Hold", key=f"hold_{job['id']}"):
                            update_job_status(job['id'], 'On Hold')
                            st.rerun()
                    with col2:
                        if st.button("🔒 Close Job", key=f"close_{job['id']}"):
                            update_job_status(job['id'], 'Closed')
                            st.rerun()
                elif job['status'] == 'On Hold':
                    if st.button("▶️ Reopen Job", key=f"reopen_{job['id']}"):
                        update_job_status(job['id'], 'Open')
                        st.rerun()
    else:
        st.info("No job postings found")

def show_department_jobs():
    """Show jobs for manager's department"""
    user = get_current_user()

    st.markdown("### 📋 Department Job Postings")

    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Get manager's department
        cursor.execute("SELECT department FROM employees WHERE id = %s", (user['employee_id'],))
        result = cursor.fetchone()
        department = result['department'] if result else None

        if not department:
            st.warning("Unable to determine your department")
            return

        cursor.execute("""
            SELECT j.*,
                   (SELECT COUNT(*) FROM job_applications WHERE job_id = j.id) as application_count
            FROM jobs j
            WHERE j.department = %s
            ORDER BY j.created_at DESC
        """, (department,))
        jobs = [dict(row) for row in cursor.fetchall()]

    if jobs:
        for job in jobs:
            with st.expander(f"💼 {job['title']} ({job['application_count']} applications)"):
                posted_date = job['created_at'].strftime('%Y-%m-%d') if job['created_at'] else 'N/A'
                st.markdown(f"""
                **Location:** {job['location']}
                **Job Type:** {job.get('job_type', 'Full-time')}
                **Salary Range:** {job.get('salary_range', 'Competitive')}
                **Status:** {job['status']}
                **Posted:** {posted_date}
                """)
                st.metric("Applications", job['application_count'])
    else:
        st.info("No job postings for your department")

def show_applications():
    """Show job applications"""
    st.markdown("### 📥 Job Applications")

    # Filters
    col1, col2 = st.columns(2)
    with col1:
        status_filter = st.selectbox("Status", ["All", "Applied", "Screening", "Shortlisted", "Interview", "Offered", "Rejected"])
    with col2:
        search = st.text_input("🔍 Search candidate")

    with get_db_connection() as conn:
        cursor = conn.cursor()

        query = """
            SELECT a.*, j.title as job_title, j.department
            FROM job_applications a
            JOIN jobs j ON a.job_id = j.id
            WHERE 1=1
        """
        params = []

        # Manager filter
        if is_manager() and not is_hr_admin():
            user = get_current_user()
            cursor.execute("SELECT department FROM employees WHERE id = %s", (user['employee_id'],))
            result = cursor.fetchone()
            if result:
                query += " AND j.department = %s"
                params.append(result['department'])

        if status_filter != "All":
            query += " AND a.status = %s"
            params.append(status_filter)

        if search:
            query += " AND (a.candidate_name LIKE %s OR a.candidate_email LIKE %s)"
            params.extend([f"%{search}%", f"%{search}%"])

        query += " ORDER BY a.created_at DESC LIMIT 50"

        cursor.execute(query, params)
        applications = [dict(row) for row in cursor.fetchall()]

    if applications:
        for app in applications:
            status_color = {
                'Applied': 'rgba(58, 123, 213, 0.1)',
                'Screening': 'rgba(240, 180, 41, 0.1)',
                'Shortlisted': 'rgba(91, 156, 246, 0.1)',
                'Interview': 'rgba(201, 150, 58, 0.1)',
                'Offered': 'rgba(45, 212, 170, 0.1)',
                'Rejected': 'rgba(241, 100, 100, 0.1)'
            }.get(app['status'], 'rgba(58, 123, 213, 0.05)')

            with st.expander(f"👤 {app['candidate_name']} - {app['job_title']} ({app['status']})"):
                col1, col2 = st.columns([2, 1])

                with col1:
                    applied_date = app['created_at'].strftime('%Y-%m-%d') if app['created_at'] else 'N/A'
                    st.markdown(f"""
                    **Candidate:** {app['candidate_name']}
                    **Email:** {app['candidate_email']}
                    **Phone:** {app['candidate_phone']}
                    **Position:** {app['job_title']}
                    **Department:** {app['department']}
                    **Status:** {app['status']}
                    **Applied:** {applied_date}
                    **Experience:** {app['experience_years'] or 0} years
                    """)

                with col2:
                    if app['expected_salary']:
                        st.metric("Expected Salary", f"${app['expected_salary']:,.0f}")

                if app['cover_letter']:
                    st.markdown(f"**Cover Letter:**\n{app['cover_letter']}")

                if app['notes']:
                    st.info(f"**Notes:** {app['notes']}")

                # Actions
                st.markdown("---")
                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    if app['status'] not in ['Shortlisted', 'Offered'] and st.button("⭐ Shortlist", key=f"short_{app['id']}"):
                        update_application_status(app['id'], 'Shortlisted', app['job_id'])
                        st.rerun()

                with col2:
                    if app['status'] == 'Shortlisted' and st.button("📅 Schedule Interview", key=f"interview_{app['id']}"):
                        update_application_status(app['id'], 'Interview', app['job_id'])
                        st.rerun()

                with col3:
                    if app['status'] == 'Interview' and st.button("✅ Make Offer", key=f"offer_{app['id']}"):
                        update_application_status(app['id'], 'Offered', app['job_id'])
                        st.rerun()

                with col4:
                    if app['status'] not in ['Rejected', 'Offered'] and st.button("❌ Reject", key=f"reject_{app['id']}"):
                        update_application_status(app['id'], 'Rejected', app['job_id'])
                        st.rerun()

                # Add notes
                with st.form(f"notes_{app['id']}"):
                    notes = st.text_area("Add Notes", value=app['notes'] or "", key=f"notes_text_{app['id']}")
                    if st.form_submit_button("💾 Save Notes"):
                        save_application_notes(app['id'], notes)
                        st.rerun()
    else:
        st.info("No applications found")

def show_shortlisted_candidates():
    """Show shortlisted candidates"""
    st.markdown("### ⭐ Shortlisted Candidates")

    with get_db_connection() as conn:
        cursor = conn.cursor()

        query = """
            SELECT a.*, j.title as job_title, j.department
            FROM job_applications a
            JOIN jobs j ON a.job_id = j.id
            WHERE a.status IN ('Shortlisted', 'Interview')
        """
        params = []

        # Manager filter
        if is_manager() and not is_hr_admin():
            user = get_current_user()
            cursor.execute("SELECT department FROM employees WHERE id = %s", (user['employee_id'],))
            result = cursor.fetchone()
            if result:
                query += " AND j.department = %s"
                params.append(result['department'])

        query += " ORDER BY a.created_at DESC"

        cursor.execute(query, params)
        shortlisted = [dict(row) for row in cursor.fetchall()]

    if shortlisted:
        for candidate in shortlisted:
            st.markdown(f"""
                <div style="background: rgba(91, 156, 246, 0.1); padding: 15px; border-radius: 10px; margin-bottom: 10px;">
                    <strong>{candidate['candidate_name']}</strong> - {candidate['job_title']}<br>
                    <small style="color: #7d96be;">
                        {candidate['candidate_email']} •
                        {candidate['experience_years'] or 0} years exp •
                        Status: {candidate['status']}
                    </small>
                </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No shortlisted candidates")

def show_interviews():
    """Show scheduled interviews"""
    st.markdown("### 📅 Scheduled Interviews")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT a.*, j.title as job_title, j.department
            FROM job_applications a
            JOIN jobs j ON a.job_id = j.id
            WHERE a.status = 'Interview'
            ORDER BY a.created_at DESC
        """)
        interviews = [dict(row) for row in cursor.fetchall()]

    if interviews:
        for interview in interviews:
            st.markdown(f"""
                <div style="background: rgba(201, 150, 58, 0.1); padding: 15px; border-radius: 10px; margin-bottom: 10px;">
                    <strong>📅 {interview['candidate_name']}</strong> - {interview['job_title']}<br>
                    <small style="color: #7d96be;">
                        {interview['candidate_email']} •
                        {interview['candidate_phone']}
                    </small>
                </div>
            """, unsafe_allow_html=True)

            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ Make Offer", key=f"offer_int_{interview['id']}"):
                    update_application_status(interview['id'], 'Offered', interview['job_id'])
                    st.rerun()
            with col2:
                if st.button("❌ Reject", key=f"reject_int_{interview['id']}"):
                    update_application_status(interview['id'], 'Rejected', interview['job_id'])
                    st.rerun()
    else:
        st.info("No scheduled interviews")

def show_post_job():
    """Post a new job"""
    st.markdown("### ➕ Post New Job")

    with st.form("post_job"):
        title = st.text_input("Job Title *", placeholder="e.g., Senior Software Engineer")

        col1, col2 = st.columns(2)

        with col1:
            department = st.selectbox("Department *", [
                "Engineering", "Product", "Sales", "Marketing",
                "Human Resources", "Finance", "Operations", "Customer Success"
            ])
            location = st.text_input("Location *", placeholder="e.g., Remote, New York, Dubai")
            job_type = st.selectbox("Job Type *", ["Full-time", "Part-time", "Contract", "Internship"])

        with col2:
            salary_range = st.text_input("Salary Range *", placeholder="e.g., $50,000 - $80,000", value="$50,000 - $80,000")

        description = st.text_area("Job Description *", placeholder="Describe the role, responsibilities, and what the candidate will be doing...")
        requirements = st.text_area("Requirements *", placeholder="List the required skills, qualifications, and experience...")

        submitted = st.form_submit_button("📤 Post Job", use_container_width=True)

        if submitted:
            if not all([title, department, location, job_type, salary_range, description, requirements]):
                st.error("❌ Please fill all required fields")
            else:
                create_job_posting(title, department, location, job_type, salary_range, description, requirements)
                st.rerun()

def create_job_posting(title, department, location, job_type, salary_range, description, requirements):
    """Create a new job posting"""
    user = get_current_user()

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO jobs (
                    title, department, location, job_type,
                    salary_range, description, requirements,
                    status, posted_by, posted_date
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, 'Open', %s, %s)
            """, (title, department, location, job_type,
                 salary_range, description, requirements,
                 user['employee_id'], datetime.now().date().isoformat()))

            job_id = cursor.lastrowid

            conn.commit()
            log_audit(f"Posted job: {title}", "jobs", job_id)
            st.success(f"✅ Job posted successfully! ID: JOB-{job_id}")
            st.balloons()

    except Exception as e:
        st.error(f"❌ Error: {str(e)}")

def update_job_status(job_id, status):
    """Update job status"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE jobs SET status = %s WHERE id = %s", (status, job_id))
            conn.commit()
            log_audit(f"Updated job {job_id} status to {status}", "jobs", job_id)
            st.success(f"✅ Job status updated to {status}")

    except Exception as e:
        st.error(f"❌ Error: {str(e)}")

def update_application_status(app_id, status, job_id):
    """Update application status"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # Get candidate info
            cursor.execute("SELECT candidate_name, candidate_email FROM job_applications WHERE id = %s", (app_id,))
            candidate = cursor.fetchone()

            cursor.execute("UPDATE job_applications SET status = %s WHERE id = %s", (status, app_id))

            # Get job title
            cursor.execute("SELECT title FROM jobs WHERE id = %s", (job_id,))
            job = cursor.fetchone()

            conn.commit()
            log_audit(f"Updated application {app_id} status to {status}", "job_applications", app_id)
            st.success(f"✅ Application status updated to {status}")

            # In production, send email to candidate
            st.info(f"📧 Email notification would be sent to {candidate['candidate_email']}")

    except Exception as e:
        st.error(f"❌ Error: {str(e)}")

def save_application_notes(app_id, notes):
    """Save notes for application"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE job_applications SET notes = %s WHERE id = %s", (notes, app_id))
            conn.commit()
            log_audit(f"Updated notes for application {app_id}", "job_applications", app_id)
            st.success("✅ Notes saved successfully")

    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
