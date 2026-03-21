"""
Training Management Module
Course catalog, enrollment, approval workflow, completion tracking
"""

import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
from database import get_db_connection
from auth import get_current_user, is_hr_admin, is_manager, is_employee, create_notification, log_audit

def show_training_management():
    """Main training management interface"""
    user = get_current_user()

    st.markdown("## 🎓 Training & Development")
    st.markdown("Manage courses, enrollments, and skill development")
    st.markdown("---")

    if is_hr_admin():
        tabs = st.tabs(["📚 Course Catalog", "📋 All Enrollments", "⏳ Pending Approvals", "➕ Add Course"])
    elif is_manager():
        tabs = st.tabs(["📚 Course Catalog", "👥 Team Enrollments", "⏳ Pending Approvals"])
    else:
        tabs = st.tabs(["📚 Available Courses", "📋 My Enrollments", "✅ Completed"])

    with tabs[0]:
        if is_hr_admin() or is_manager():
            show_course_catalog_admin()
        else:
            show_available_courses()

    with tabs[1]:
        if is_hr_admin():
            show_all_enrollments()
        elif is_manager():
            show_team_enrollments()
        else:
            show_my_enrollments()

    with tabs[2]:
        if is_hr_admin() or is_manager():
            show_pending_approvals()
        else:
            show_completed_courses()

    if len(tabs) > 3:
        with tabs[3]:
            show_add_course()

def show_available_courses():
    """Show courses available for enrollment"""
    user = get_current_user()

    st.markdown("### 📚 Available Training Courses")

    # Filters
    col1, col2 = st.columns(2)
    with col1:
        category_filter = st.selectbox("Category", ["All", "Technical", "Leadership", "Soft Skills", "Compliance", "Product"])
    with col2:
        search = st.text_input("🔍 Search courses")

    with get_db_connection() as conn:
        cursor = conn.cursor()

        query = """
            SELECT c.*,
                   (SELECT COUNT(*) FROM training_enrollments WHERE course_id = c.id) as enrollment_count,
                   (SELECT status FROM training_enrollments WHERE course_id = c.id AND emp_id = %s) as my_status
            FROM training_catalog c
            WHERE c.status = 'Active'
        """
        params = [user['employee_id']]

        if category_filter != "All":
            query += " AND c.category = %s"
            params.append(category_filter)

        if search:
            query += " AND (c.title LIKE %s OR c.description LIKE %s)"
            params.extend([f"%{search}%", f"%{search}%"])

        query += " ORDER BY c.created_at DESC"

        cursor.execute(query, params)
        courses = [dict(row) for row in cursor.fetchall()]

    if courses:
        for course in courses:
            title = course.get('course_name', course.get('title', 'Untitled'))
            duration = course.get('duration', course.get('duration_hours', 'N/A'))
            with st.expander(f"📚 {title} ({duration})"):
                col1, col2 = st.columns([2, 1])

                with col1:
                    st.markdown(f"""
                    **Course:** {title}
                    **Provider:** {course.get('provider', 'N/A')}
                    **Duration:** {duration}
                    **Description:** {course.get('description', 'No description')}
                    """)

                with col2:
                    st.metric("Enrolled", course.get('enrollment_count', 0))
                    if course.get('cost'):
                        st.metric("Cost", f"${course.get('cost', 0):,.2f}")

                # Enrollment status
                if course.get('my_status'):
                    st.success(f"✅ You are {course.get('my_status')} for this course")
                else:
                    if st.button("📝 Request Enrollment", key=f"enroll_{course.get('id', 0)}"):
                        request_enrollment(course.get('id'))
                        st.rerun()
    else:
        st.info("No courses available")

def show_my_enrollments():
    """Show employee's enrollments"""
    user = get_current_user()

    st.markdown("### 📋 My Training Enrollments")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT e.*, c.title, c.category, c.duration_hours, c.provider
            FROM training_enrollments e
            JOIN training_catalog c ON e.course_id = c.id
            WHERE e.emp_id = %s
            ORDER BY e.created_at DESC
        """, (user['employee_id'],))
        enrollments = [dict(row) for row in cursor.fetchall()]

    if enrollments:
        for enrollment in enrollments:
            status_config = {
                'Requested': {'color': 'rgba(240, 180, 41, 0.1)', 'icon': '⏳'},
                'Approved': {'color': 'rgba(91, 156, 246, 0.1)', 'icon': '✅'},
                'Enrolled': {'color': 'rgba(45, 212, 170, 0.1)', 'icon': '📚'},
                'Completed': {'color': 'rgba(45, 212, 170, 0.2)', 'icon': '🎓'},
                'Cancelled': {'color': 'rgba(125, 150, 190, 0.1)', 'icon': '❌'}
            }

            config = status_config.get(enrollment['status'], status_config['Requested'])

            st.markdown(f"""
                <div style="background: {config['color']}; padding: 15px; border-radius: 10px; margin-bottom: 12px; border-left: 3px solid #c9963a;">
                    <div style="font-size: 24px; margin-bottom: 5px;">{config['icon']}</div>
                    <strong style="font-size: 15px;">{enrollment['title']}</strong><br>
                    <small style="color: #7d96be;">
                        {enrollment['category']} •
                        {enrollment['duration_hours']}h •
                        {enrollment['provider']}<br>
                        Status: {enrollment['status']} •
                        Requested: {enrollment['created_at'][:10]}
                    </small>
                </div>
            """, unsafe_allow_html=True)

            # Mark as completed
            if enrollment['status'] == 'Enrolled':
                col1, col2 = st.columns([3, 1])
                with col2:
                    if st.button("✅ Mark Complete", key=f"complete_{enrollment['id']}"):
                        mark_training_complete(enrollment['id'])
                        st.rerun()
    else:
        st.info("No enrollments yet")

def show_completed_courses():
    """Show completed courses"""
    user = get_current_user()

    st.markdown("### ✅ Completed Courses")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT e.*, c.title, c.category, c.duration_hours
            FROM training_enrollments e
            JOIN training_catalog c ON e.course_id = c.id
            WHERE e.emp_id = %s AND e.status = 'Completed'
            ORDER BY e.completion_date DESC
        """, (user['employee_id'],))
        completed = [dict(row) for row in cursor.fetchall()]

    if completed:
        total_hours = sum([c['duration_hours'] for c in completed if c['duration_hours']])
        st.metric("Total Training Hours", f"{total_hours}h")

        for course in completed:
            st.markdown(f"""
                <div style="background: rgba(45, 212, 170, 0.1); padding: 15px; border-radius: 10px; margin-bottom: 10px;">
                    <strong>🎓 {course.get('course_name', course.get('title', 'Untitled'))}</strong><br>
                    <small style="color: #7d96be;">
                        {course.get('duration', course.get('duration_hours', 'N/A'))} •
                        Completed: {course.get('completion_date', 'N/A')[:10] if course.get('completion_date') else 'N/A'}
                    </small>
                </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No completed courses yet")

def show_course_catalog_admin():
    """Show full course catalog for admins"""
    st.markdown("### 📚 Training Course Catalog")

    # Filters
    col1, col2, col3 = st.columns(3)
    with col1:
        status_filter = st.selectbox("Status", ["All", "Active", "Inactive"])
    with col2:
        category_filter = st.selectbox("Category", ["All", "Technical", "Leadership", "Soft Skills", "Compliance", "Product"])
    with col3:
        search = st.text_input("🔍 Search")

    with get_db_connection() as conn:
        cursor = conn.cursor()

        query = """
            SELECT c.*,
                   (SELECT COUNT(*) FROM training_enrollments WHERE course_id = c.id) as enrollment_count
            FROM training_catalog c
            WHERE 1=1
        """
        params = []

        if status_filter != "All":
            query += " AND c.status = %s"
            params.append(status_filter)

        if category_filter != "All":
            query += " AND c.category = %s"
            params.append(category_filter)

        if search:
            query += " AND (c.title LIKE %s OR c.description LIKE %s)"
            params.extend([f"%{search}%", f"%{search}%"])

        query += " ORDER BY c.created_at DESC"

        cursor.execute(query, params)
        courses = [dict(row) for row in cursor.fetchall()]

    if courses:
        for course in courses:
            with st.expander(f"📚 {course.get('course_name', 'Untitled')} - {course.get('enrollment_count', 0)} enrollments"):
                col1, col2 = st.columns([2, 1])

                with col1:
                    st.markdown(f"""
                    **Title:** {course.get('course_name', 'N/A')}
                    **Provider:** {course.get('provider', 'N/A')}
                    **Duration:** {course.get('duration', 'N/A')}
                    **Cost:** ${course.get('cost', 0):,.2f}
                    **Max Participants:** {course.get('max_participants', 'N/A')}
                    **Status:** {course.get('status', 'N/A')}
                    """)

                with col2:
                    st.metric("Total Enrollments", course.get('enrollment_count', 0))

                st.markdown(f"**Description:**\n{course.get('description', 'No description')}")

                # Toggle status
                if course.get('status') == 'Active':
                    if st.button("⏸️ Deactivate", key=f"deactivate_{course.get('id', 0)}"):
                        update_course_status(course.get('id'), 'Inactive')
                        st.rerun()
                else:
                    if st.button("▶️ Activate", key=f"activate_{course.get('id', 0)}"):
                        update_course_status(course.get('id'), 'Active')
                        st.rerun()
    else:
        st.info("No courses found")

def show_all_enrollments():
    """Show all training enrollments"""
    st.markdown("### 📋 All Training Enrollments")

    # Filters
    col1, col2 = st.columns(2)
    with col1:
        status_filter = st.selectbox("Status", ["All", "Requested", "Approved", "Enrolled", "Completed", "Cancelled"])
    with col2:
        search = st.text_input("🔍 Search employee")

    with get_db_connection() as conn:
        cursor = conn.cursor()

        query = """
            SELECT e.*, c.title as course_title, c.category, c.cost,
                   emp.first_name, emp.last_name, emp.employee_id, emp.department
            FROM training_enrollments e
            JOIN training_catalog c ON e.course_id = c.id
            JOIN employees emp ON e.emp_id = emp.id
            WHERE 1=1
        """
        params = []

        if status_filter != "All":
            query += " AND e.status = %s"
            params.append(status_filter)

        if search:
            query += " AND (emp.first_name LIKE %s OR emp.last_name LIKE %s OR emp.employee_id LIKE %s)"
            params.extend([f"%{search}%", f"%{search}%", f"%{search}%"])

        query += " ORDER BY e.created_at DESC LIMIT 50"

        cursor.execute(query, params)
        enrollments = [dict(row) for row in cursor.fetchall()]

    if enrollments:
        df = pd.DataFrame(enrollments)
        display_cols = ['employee_id', 'first_name', 'last_name', 'course_title', 'category', 'status', 'created_at']
        df_display = df[display_cols]
        df_display.columns = ['Emp ID', 'First Name', 'Last Name', 'Course', 'Category', 'Status', 'Requested']
        df_display['Requested'] = df_display['Requested'].str[:10]

        st.dataframe(df_display, use_container_width=True, hide_index=True)
    else:
        st.info("No enrollments found")

def show_team_enrollments():
    """Show team training enrollments"""
    user = get_current_user()

    st.markdown("### 👥 Team Training Enrollments")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT e.*, c.title as course_title, c.category, c.duration_hours,
                   emp.first_name, emp.last_name, emp.employee_id
            FROM training_enrollments e
            JOIN training_catalog c ON e.course_id = c.id
            JOIN employees emp ON e.emp_id = emp.id
            WHERE emp.manager_id = %s
            ORDER BY e.created_at DESC
        """, (user['employee_id'],))
        enrollments = [dict(row) for row in cursor.fetchall()]

    if enrollments:
        for enrollment in enrollments:
            with st.expander(f"📚 {enrollment['first_name']} {enrollment['last_name']} - {enrollment['course_title']} ({enrollment['status']})"):
                st.markdown(f"""
                **Employee:** {enrollment['first_name']} {enrollment['last_name']} ({enrollment['employee_id']})
                **Course:** {enrollment['course_title']}
                **Category:** {enrollment['category']}
                **Duration:** {enrollment['duration_hours']} hours
                **Status:** {enrollment['status']}
                **Requested:** {enrollment['created_at'][:10]}
                """)

                if enrollment['completion_date']:
                    st.success(f"✅ Completed: {enrollment['completion_date'][:10]}")
    else:
        st.info("No team enrollments found")

def show_pending_approvals():
    """Show enrollments pending approval"""
    user = get_current_user()

    st.markdown("### ⏳ Pending Training Approvals")

    with get_db_connection() as conn:
        cursor = conn.cursor()

        if is_hr_admin():
            # HR sees manager-approved requests
            cursor.execute("""
                SELECT e.*, c.title as course_title, c.category, c.cost, c.provider,
                       emp.first_name, emp.last_name, emp.employee_id, emp.department
                FROM training_enrollments e
                JOIN training_catalog c ON e.course_id = c.id
                JOIN employees emp ON e.emp_id = emp.id
                WHERE e.status = 'Approved'
                ORDER BY e.created_at ASC
            """)
        elif is_manager():
            # Manager sees team requests
            cursor.execute("""
                SELECT e.*, c.title as course_title, c.category, c.cost, c.provider,
                       emp.first_name, emp.last_name, emp.employee_id
                FROM training_enrollments e
                JOIN training_catalog c ON e.course_id = c.id
                JOIN employees emp ON e.emp_id = emp.id
                WHERE emp.manager_id = %s AND e.status = 'Requested'
                ORDER BY e.created_at ASC
            """, (user['employee_id'],))
        else:
            st.info("No approvals available")
            return

        pending = [dict(row) for row in cursor.fetchall()]

    if pending:
        st.info(f"📋 {len(pending)} training request(s) awaiting approval")

        for request in pending:
            with st.expander(f"📚 {request['first_name']} {request['last_name']} - {request['course_title']}"):
                col1, col2 = st.columns([2, 1])

                with col1:
                    st.markdown(f"""
                    **Employee:** {request['first_name']} {request['last_name']} ({request['employee_id']})
                    **Department:** {request.get('department', 'N/A')}
                    **Course:** {request['course_title']}
                    **Category:** {request['category']}
                    **Provider:** {request['provider']}
                    **Status:** {request['status']}
                    **Requested:** {request['created_at'][:10]}
                    """)

                with col2:
                    if request['cost']:
                        st.metric("Course Cost", f"${request['cost']:,.2f}")

                # Approval actions
                st.markdown("---")
                col1, col2 = st.columns(2)

                with col1:
                    if st.button("✅ Approve", key=f"approve_train_{request['id']}", use_container_width=True):
                        approve_training_request(request['id'], request['emp_id'])
                        st.rerun()

                with col2:
                    if st.button("❌ Reject", key=f"reject_train_{request['id']}", use_container_width=True):
                        reject_training_request(request['id'], request['emp_id'])
                        st.rerun()
    else:
        st.success("✅ No training requests pending approval!")

def show_add_course():
    """Add new course to catalog"""
    st.markdown("### ➕ Add New Training Course")

    with st.form("add_course"):
        title = st.text_input("Course Title *", placeholder="e.g., Advanced Python Programming")

        col1, col2 = st.columns(2)

        with col1:
            category = st.selectbox("Category *", ["Technical", "Leadership", "Soft Skills", "Compliance", "Product"])
            provider = st.text_input("Provider *", placeholder="e.g., Coursera, Udemy, Internal")
            level = st.selectbox("Level *", ["Beginner", "Intermediate", "Advanced"])

        with col2:
            duration_hours = st.number_input("Duration (hours) *", min_value=0.5, value=10.0, step=0.5)
            cost = st.number_input("Cost ($)", min_value=0.0, value=0.0, step=10.0)
            delivery_mode = st.selectbox("Delivery Mode *", ["Online", "In-Person", "Hybrid", "Self-Paced"])

        description = st.text_area("Description *", placeholder="Describe what the course covers...")
        prerequisites = st.text_area("Prerequisites", placeholder="Any required prior knowledge or courses...")

        submitted = st.form_submit_button("📚 Add Course", use_container_width=True)

        if submitted:
            if not all([title, category, provider, level, duration_hours, delivery_mode, description]):
                st.error("❌ Please fill all required fields")
            else:
                create_course(title, category, provider, level, duration_hours, cost, delivery_mode, description, prerequisites)
                st.rerun()

def create_course(title, category, provider, level, duration_hours, cost, delivery_mode, description, prerequisites):
    """Create new training course"""
    user = get_current_user()

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO training_catalog (
                    title, category, provider, level, duration_hours, cost,
                    currency, delivery_mode, description, prerequisites, status, created_by
                ) VALUES (%s, ?, ?, ?, ?, ?, 'USD', ?, ?, ?, 'Active', ?)
            """, (title, category, provider, level, duration_hours, cost,
                 delivery_mode, description, prerequisites, user['employee_id']))

            course_id = cursor.lastrowid

            conn.commit()
            log_audit(f"Created training course: {title}", "training_catalog", course_id)
            st.success(f"✅ Course added successfully! ID: COURSE-{course_id}")
            st.balloons()

    except Exception as e:
        st.error(f"❌ Error: {str(e)}")

def request_enrollment(course_id):
    """Request enrollment in a course"""
    user = get_current_user()

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # Get manager
            cursor.execute("SELECT manager_id FROM employees WHERE id = %s", (user['employee_id'],))
            result = cursor.fetchone()
            manager_id = result['manager_id'] if result else None

            cursor.execute("""
                INSERT INTO training_enrollments (
                    emp_id, course_id, status
                ) VALUES (%s, ?, 'Requested')
            """, (user['employee_id'], course_id))

            enrollment_id = cursor.lastrowid

            # Notify manager
            if manager_id:
                cursor.execute("SELECT title FROM training_catalog WHERE id = %s", (course_id,))
                course = cursor.fetchone()

                create_notification(
                    manager_id,
                    "Training Enrollment Request",
                    f"{user['full_name']} requested enrollment in: {course.get('course_name', course.get('title', 'a course'))}",
                    'info'
                )

            conn.commit()
            log_audit(f"Requested training enrollment for course {course_id}", "training_enrollments", enrollment_id)
            st.success("✅ Enrollment request submitted!")
            st.balloons()

    except Exception as e:
        st.error(f"❌ Error: {str(e)}")

def approve_training_request(enrollment_id, emp_id):
    """Approve training request"""
    user = get_current_user()

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            if is_manager() and not is_hr_admin():
                # Manager approval
                cursor.execute("""
                    UPDATE training_enrollments SET
                        status = 'Approved',
                        approved_by = %s,
                        approval_date = %s
                    WHERE id = %s
                """, (user['employee_id'], datetime.now().isoformat(), enrollment_id))

                # Notify HR
                cursor.execute("SELECT id FROM employees WHERE department = 'Human Resources' LIMIT 1")
                hr_emp = cursor.fetchone()
                if hr_emp:
                    create_notification(
                        hr_emp['id'],
                        "Training Requires Final Approval",
                        f"A training enrollment (ID: {enrollment_id}) has been approved by manager.",
                        'info'
                    )

                create_notification(emp_id, "Training Request Approved",
                                  "Your training request has been approved by your manager. Awaiting HR approval.", 'success')

            elif is_hr_admin():
                # HR final approval
                cursor.execute("""
                    UPDATE training_enrollments SET
                        status = 'Enrolled',
                        approved_by = %s,
                        approval_date = %s
                    WHERE id = %s
                """, (user['employee_id'], datetime.now().isoformat(), enrollment_id))

                create_notification(emp_id, "Training Enrollment Confirmed",
                                  "Your training enrollment has been confirmed. You can begin the course.", 'success')

            conn.commit()
            log_audit(f"Approved training enrollment {enrollment_id}", "training_enrollments", enrollment_id)
            st.success("✅ Training request approved!")

    except Exception as e:
        st.error(f"❌ Error: {str(e)}")

def reject_training_request(enrollment_id, emp_id):
    """Reject training request"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("UPDATE training_enrollments SET status = 'Cancelled' WHERE id = %s", (enrollment_id,))

            create_notification(emp_id, "Training Request Not Approved",
                              "Your training enrollment request was not approved. Please contact your manager for details.", 'warning')

            conn.commit()
            log_audit(f"Rejected training enrollment {enrollment_id}", "training_enrollments", enrollment_id)
            st.warning("⚠️ Training request rejected")

    except Exception as e:
        st.error(f"❌ Error: {str(e)}")

def mark_training_complete(enrollment_id):
    """Mark training as completed and auto-update employee skills"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # Get enrollment details
            cursor.execute("""
                SELECT te.emp_id, te.course_id, tc.course_name, tc.category
                FROM training_enrollments te
                JOIN training_catalog tc ON te.course_id = tc.id
                WHERE te.id = %s
            """, (enrollment_id,))
            enrollment = cursor.fetchone()

            if not enrollment:
                st.error("❌ Enrollment not found")
                return

            # Mark training as completed
            cursor.execute("""
                UPDATE training_enrollments SET
                    status = 'Completed',
                    completion_date = %s
                WHERE id = %s
            """, (datetime.now().isoformat(), enrollment_id))

            # AUTO-UPDATE SKILLS: Add course skills to employee profile
            emp_id = enrollment['emp_id']
            course_name = enrollment['course_name']
            category = enrollment['category']

            # Check if skill exists for this course/category
            cursor.execute("""
                SELECT id FROM skills
                WHERE skill_name = %s OR category = %s
                LIMIT 1
            """, (course_name, category))
            skill = cursor.fetchone()

            if skill:
                skill_id = skill['id']

                # Check if employee already has this skill
                cursor.execute("""
                    SELECT id, proficiency_level FROM employee_skills
                    WHERE emp_id = %s AND skill_id = %s
                """, (emp_id, skill_id))
                existing_skill = cursor.fetchone()

                if existing_skill:
                    # Upgrade proficiency level
                    level_upgrade = {
                        'Beginner': 'Intermediate',
                        'Intermediate': 'Advanced',
                        'Advanced': 'Expert',
                        'Expert': 'Expert'
                    }
                    new_level = level_upgrade.get(existing_skill['proficiency_level'], 'Intermediate')

                    cursor.execute("""
                        UPDATE employee_skills SET
                            proficiency_level = %s,
                            years_experience = years_experience + 0.5,
                            updated_at = %s
                        WHERE id = %s
                    """, (new_level, datetime.now().isoformat(), existing_skill['id']))

                    st.info(f"📈 Skill upgraded to {new_level}")
                else:
                    # Add new skill
                    cursor.execute("""
                        INSERT INTO employee_skills (emp_id, skill_id, proficiency_level, years_experience, certified)
                        VALUES (%s, %s, 'Intermediate', 0.5, FALSE)
                    """, (emp_id, skill_id))

                    st.info(f"✨ New skill added to profile: {course_name}")

                # Send notification to employee
                create_notification(
                    emp_id,
                    "Training Completed - Skills Updated",
                    f"Congratulations! You've completed '{course_name}'. Your skills profile has been automatically updated.",
                    'success'
                )

            conn.commit()
            log_audit(f"Completed training enrollment {enrollment_id} and updated skills", "training_enrollments", enrollment_id)
            st.success("✅ Training marked as completed! Skills profile auto-updated!")
            st.balloons()

    except Exception as e:
        st.error(f"❌ Error: {str(e)}")

def update_course_status(course_id, status):
    """Update course status"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE training_catalog SET status = %s WHERE id = %s", (status, course_id))
            conn.commit()
            log_audit(f"Updated course {course_id} status to {status}", "training_catalog", course_id)
            st.success(f"✅ Course status updated to {status}")

    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
