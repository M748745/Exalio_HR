"""
Document Approval Module
Manage document creation, review, approval, and version control
"""

import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
from database import get_db_connection
from auth import get_current_user, is_hr_admin, is_manager, create_notification, log_audit

def show_document_approval():
    """Main document approval interface"""
    user = get_current_user()

    st.markdown("## 📋 Document Management & Approval")
    st.markdown("Create, review, and approve company documents with version control")
    st.markdown("---")

    if is_hr_admin():
        tabs = st.tabs(["📚 All Documents", "⏳ Pending Approval", "✅ Approved", "📊 Analytics", "➕ Create Document", "⚙️ Settings"])
    elif is_manager():
        tabs = st.tabs(["📚 My Documents", "⏳ Pending Approval", "➕ Create Document"])
    else:
        tabs = st.tabs(["📚 Available Documents", "📥 My Downloads"])

    with tabs[0]:
        if is_hr_admin():
            show_all_documents()
        elif is_manager():
            show_my_documents()
        else:
            show_available_documents()

    with tabs[1]:
        if is_hr_admin() or is_manager():
            show_pending_approvals()
        else:
            show_my_downloads()

    with tabs[2]:
        if is_hr_admin():
            show_approved_documents()
        else:
            create_document()

    if is_hr_admin() and len(tabs) > 3:
        with tabs[3]:
            show_document_analytics()
        with tabs[4]:
            create_document()
        with tabs[5]:
            show_document_settings()

def show_all_documents():
    """Show all documents for HR"""
    st.markdown("### 📚 All Documents")

    with get_db_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                d.id,
                d.title,
                d.category,
                d.document_type,
                d.version,
                d.status,
                d.access_level,
                d.uploaded_by,
                e.first_name || ' ' || e.last_name as author_name,
                d.created_at,
                d.approval_status,
                d.effective_date,
                d.expiry_date,
                COALESCE(d.download_count, 0) as downloads
            FROM documents d
            LEFT JOIN employees e ON d.uploaded_by = e.id
            ORDER BY d.created_at DESC
        """)
        documents = [dict(row) for row in cursor.fetchall()]

    if documents:
        # Filters
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            category_filter = st.selectbox("Category", ["All"] + list(set([d['category'] for d in documents if d['category']])))
        with col2:
            type_filter = st.selectbox("Type", ["All"] + list(set([d['document_type'] for d in documents if d['document_type']])))
        with col3:
            status_filter = st.selectbox("Status", ["All", "Active", "Draft", "Archived", "Expired"])
        with col4:
            approval_filter = st.selectbox("Approval", ["All", "Pending", "Approved", "Rejected", "Under Review"])

        # Apply filters
        filtered = documents
        if category_filter != "All":
            filtered = [d for d in filtered if d['category'] == category_filter]
        if type_filter != "All":
            filtered = [d for d in filtered if d['document_type'] == type_filter]
        if status_filter != "All":
            filtered = [d for d in filtered if d['status'] == status_filter]
        if approval_filter != "All":
            filtered = [d for d in filtered if d['approval_status'] == approval_filter]

        st.markdown(f"**Total Documents:** {len(filtered)}")

        # Display documents
        for doc in filtered:
            status_emoji = {
                'Active': '🟢',
                'Draft': '🟡',
                'Archived': '⚪',
                'Expired': '🔴'
            }.get(doc['status'], '🔵')

            approval_emoji = {
                'Approved': '✅',
                'Pending': '⏳',
                'Rejected': '❌',
                'Under Review': '👀'
            }.get(doc['approval_status'], '❓')

            with st.expander(f"{status_emoji} {approval_emoji} {doc['title']} (v{doc['version']}) - {doc['document_type']}"):
                col1, col2 = st.columns([2, 1])

                with col1:
                    st.markdown(f"""
                    **Title:** {doc['title']}
                    **Category:** {doc['category']}
                    **Type:** {doc['document_type']}
                    **Version:** {doc['version']}
                    **Author:** {doc['author_name']}
                    **Status:** {doc['status']}
                    **Approval Status:** {doc['approval_status']}
                    **Access Level:** {doc['access_level']}
                    **Created:** {doc['created_at']}
                    **Effective Date:** {doc['effective_date'] or 'N/A'}
                    **Expiry Date:** {doc['expiry_date'] or 'Never'}
                    """)

                with col2:
                    st.metric("Downloads", doc['downloads'])
                    st.metric("Version", f"v{doc['version']}")

                # Actions
                st.markdown("---")
                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    if doc['approval_status'] == 'Pending':
                        if st.button("✅ Approve", key=f"approve_{doc['id']}", use_container_width=True):
                            approve_document(doc['id'], doc['created_by'])
                            st.rerun()

                with col2:
                    if doc['approval_status'] == 'Pending':
                        if st.button("❌ Reject", key=f"reject_{doc['id']}", use_container_width=True):
                            reject_document(doc['id'], doc['created_by'])
                            st.rerun()

                with col3:
                    if st.button("📝 Edit", key=f"edit_{doc['id']}", use_container_width=True):
                        st.info("Edit functionality - opens document editor")

                with col4:
                    if doc['status'] == 'Active':
                        if st.button("📦 Archive", key=f"archive_{doc['id']}", use_container_width=True):
                            archive_document(doc['id'])
                            st.rerun()
    else:
        st.info("No documents found")

def show_pending_approvals():
    """Show documents pending approval"""
    user = get_current_user()
    st.markdown("### ⏳ Documents Pending Approval")

    with get_db_connection() as conn:
        cursor = conn.cursor()

        if is_hr_admin():
            # HR approves all documents
            cursor.execute("""
                SELECT
                    d.id,
                    d.title,
                    d.category,
                    d.document_type,
                    d.version,
                    d.description,
                    d.uploaded_by,
                    e.first_name || ' ' || e.last_name as author_name,
                    d.created_at,
                    d.approval_notes
                FROM documents d
                LEFT JOIN employees e ON d.uploaded_by = e.id
                WHERE d.approval_status = 'Pending'
                ORDER BY d.created_at ASC
            """)
        else:
            # Manager approves department documents
            cursor.execute("""
                SELECT
                    d.id,
                    d.title,
                    d.category,
                    d.document_type,
                    d.version,
                    d.description,
                    d.uploaded_by,
                    e.first_name || ' ' || e.last_name as author_name,
                    d.created_at,
                    d.approval_notes
                FROM documents d
                LEFT JOIN employees e ON d.uploaded_by = e.id
                WHERE d.approval_status = 'Pending'
                AND d.requires_manager_approval = 1
                AND e.manager_id = %s
                ORDER BY d.created_at ASC
            """, (user['employee_id'],))

        pending = [dict(row) for row in cursor.fetchall()]

    if pending:
        st.info(f"📋 {len(pending)} document(s) awaiting approval")

        for doc in pending:
            with st.expander(f"📄 {doc['title']} (v{doc['version']}) - by {doc['author_name']}"):
                st.markdown(f"""
                **Title:** {doc['title']}
                **Category:** {doc['category']}
                **Type:** {doc['document_type']}
                **Version:** {doc['version']}
                **Author:** {doc['author_name']}
                **Submitted:** {doc['created_at']}
                """)

                if doc.get('description'):
                    st.markdown("**Description:**")
                    st.info(doc['description'])

                if doc.get('approval_notes'):
                    st.markdown("**Approval Notes:**")
                    st.warning(doc['approval_notes'])

                # Review form
                st.markdown("---")
                review_notes = st.text_area("Review Comments", key=f"review_{doc['id']}",
                                           placeholder="Add your review comments...")

                col1, col2 = st.columns(2)

                with col1:
                    if st.button("✅ Approve", key=f"approve_doc_{doc['id']}", use_container_width=True, type="primary"):
                        approve_document(doc['id'], doc['created_by'], review_notes)
                        st.rerun()

                with col2:
                    if st.button("❌ Reject", key=f"reject_doc_{doc['id']}", use_container_width=True):
                        if review_notes:
                            reject_document(doc['id'], doc['created_by'], review_notes)
                            st.rerun()
                        else:
                            st.error("⚠️ Please provide rejection reason in comments")
    else:
        st.success("✅ No documents pending approval!")

def create_document():
    """Create new document"""
    user = get_current_user()
    st.markdown("### ➕ Create New Document")

    with st.form("create_document_form"):
        st.info("📝 Create a new company document for review and approval")

        col1, col2 = st.columns(2)

        with col1:
            title = st.text_input("Document Title *", placeholder="e.g., Remote Work Policy 2024")

            category = st.selectbox("Category *", [
                "Policy",
                "Procedure",
                "Handbook",
                "Form",
                "Template",
                "Guide",
                "Standard Operating Procedure (SOP)",
                "Work Instruction",
                "Other"
            ])

            document_type = st.selectbox("Type *", [
                "HR Policy",
                "IT Policy",
                "Safety Policy",
                "Financial Procedure",
                "Employee Handbook",
                "Form Template",
                "Process Guide",
                "Compliance Document",
                "Training Material",
                "Other"
            ])

        with col2:
            access_level = st.selectbox("Access Level *", [
                "Public - All Employees",
                "Managers Only",
                "HR Only",
                "Department Specific",
                "Confidential"
            ])

            effective_date = st.date_input("Effective Date", value=date.today())

            has_expiry = st.checkbox("Set Expiry Date")
            expiry_date = None
            if has_expiry:
                expiry_date = st.date_input("Expiry Date", value=date.today() + timedelta(days=365))

        description = st.text_area("Description *",
                                  placeholder="Brief description of the document purpose and content...")

        content = st.text_area("Document Content *",
                              height=300,
                              placeholder="Enter the document content here...\n\nYou can use markdown formatting.")

        uploaded_file = st.file_uploader("Or Upload File (PDF, DOCX, TXT)",
                                        type=['pdf', 'docx', 'doc', 'txt'])

        approval_notes = st.text_area("Approval Notes",
                                     placeholder="Any specific notes for approvers...")

        col1, col2 = st.columns(2)
        with col1:
            requires_manager_approval = st.checkbox("Requires Manager Approval", value=True)
        with col2:
            auto_publish = st.checkbox("Auto-publish after approval", value=True)

        submitted = st.form_submit_button("📤 Submit for Approval", use_container_width=True)

        if submitted and title and description and (content or uploaded_file):
            try:
                file_path = None
                if uploaded_file:
                    # In production, save to document storage
                    file_path = f"documents/{user['employee_id']}_{title.replace(' ', '_')}_{uploaded_file.name}"
                    st.info(f"File would be saved to: {file_path}")

                with get_db_connection() as conn:
                    cursor = conn.cursor()

                    cursor.execute("""
                        INSERT INTO documents (
                            title, category, document_type, description, content,
                            file_path, version, status, approval_status,
                            access_level, effective_date, expiry_date,
                            requires_manager_approval, auto_publish_on_approval,
                            approval_notes, created_by
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (title, category, document_type, description, content,
                         file_path, '1.0', 'Draft', 'Pending',
                         access_level, effective_date.isoformat(),
                         expiry_date.isoformat() if expiry_date else None,
                         1 if requires_manager_approval else 0,
                         1 if auto_publish else 0,
                         approval_notes, user['employee_id']))

                    doc_id = cursor.lastrowid

                    # Notify approvers
                    if is_hr_admin():
                        # If HR creates, notify all HR for review
                        create_notification(
                            None,
                            "New Document for Review",
                            f"New document '{title}' created by {user['full_name']} needs review (Doc ID: {doc_id})",
                            'info',
                            is_hr_notification=True
                        )
                    elif requires_manager_approval:
                        # Notify manager
                        cursor.execute("SELECT manager_id FROM employees WHERE id = %s", (user['employee_id'],))
                        result = cursor.fetchone()
                        if result and result['manager_id']:
                            create_notification(
                                result['manager_id'],
                                "Document Approval Required",
                                f"Document '{title}' submitted by {user['full_name']} requires your approval (Doc ID: {doc_id})",
                                'info'
                            )

                    conn.commit()
                    log_audit(f"Created document {doc_id}: {title}", "documents", doc_id)
                    st.success(f"✅ Document created successfully! ID: {doc_id}")
                    st.info("📧 Approval notifications have been sent.")

            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
        elif submitted:
            st.error("❌ Please fill all required fields")

def approve_document(doc_id, author_id, review_notes=None):
    """Approve document"""
    user = get_current_user()

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # Get document details
            cursor.execute("""
                SELECT title, auto_publish_on_approval, version
                FROM documents
                WHERE id = %s
            """, (doc_id,))
            doc = dict(cursor.fetchone())

            # Update approval status
            new_status = 'Active' if doc['auto_publish_on_approval'] else 'Draft'

            cursor.execute("""
                UPDATE documents SET
                    approval_status = 'Approved',
                    approved_by = %s,
                    approval_date = %s,
                    review_comments = %s,
                    status = %s
                WHERE id = %s
            """, (user['employee_id'], datetime.now().isoformat(),
                 review_notes, new_status, doc_id))

            # Notify author
            notify_msg = f"Your document '{doc['title']}' (v{doc['version']}) has been approved"
            if new_status == 'Active':
                notify_msg += " and is now published."
            else:
                notify_msg += ". You can now publish it."

            create_notification(
                author_id,
                "Document Approved",
                notify_msg,
                'success'
            )

            conn.commit()
            log_audit(f"Approved document {doc_id}: {doc['title']}", "documents", doc_id)

            if new_status == 'Active':
                st.success(f"✅ Document approved and published!")
            else:
                st.success(f"✅ Document approved!")

    except Exception as e:
        st.error(f"❌ Error: {str(e)}")

def reject_document(doc_id, author_id, review_notes=None):
    """Reject document"""
    user = get_current_user()

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT title, version
                FROM documents
                WHERE id = %s
            """, (doc_id,))
            doc = dict(cursor.fetchone())

            cursor.execute("""
                UPDATE documents SET
                    approval_status = 'Rejected',
                    approved_by = %s,
                    approval_date = %s,
                    review_comments = %s
                WHERE id = %s
            """, (user['employee_id'], datetime.now().isoformat(), review_notes, doc_id))

            # Notify author
            create_notification(
                author_id,
                "Document Rejected",
                f"Your document '{doc['title']}' (v{doc['version']}) was not approved. Reason: {review_notes or 'See reviewer comments'}",
                'warning'
            )

            conn.commit()
            log_audit(f"Rejected document {doc_id}: {doc['title']}. Reason: {review_notes}", "documents", doc_id)
            st.warning(f"⚠️ Document rejected")

    except Exception as e:
        st.error(f"❌ Error: {str(e)}")

def archive_document(doc_id):
    """Archive document"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                UPDATE documents SET
                    status = 'Archived',
                    archived_date = %s
                WHERE id = %s
            """, (datetime.now().isoformat(), doc_id))

            conn.commit()
            log_audit(f"Archived document {doc_id}", "documents", doc_id)
            st.info("📦 Document archived")

    except Exception as e:
        st.error(f"❌ Error: {str(e)}")

def show_approved_documents():
    """Show approved/active documents"""
    st.markdown("### ✅ Approved Documents")

    with get_db_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                d.id,
                d.title,
                d.category,
                d.document_type,
                d.version,
                d.status,
                d.approval_date,
                e.first_name || ' ' || e.last_name as approver_name,
                d.download_count
            FROM documents d
            LEFT JOIN employees e ON d.approved_by = e.id
            WHERE d.approval_status = 'Approved'
            ORDER BY d.approval_date DESC
        """)
        documents = [dict(row) for row in cursor.fetchall()]

    if documents:
        st.markdown(f"**Total Approved:** {len(documents)}")

        for doc in documents:
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.markdown(f"**{doc['title']}** (v{doc['version']}) - {doc['document_type']}")
            with col2:
                st.markdown(f"Approved: {doc['approval_date']}")
            with col3:
                st.markdown(f"📥 {doc['download_count'] or 0} downloads")
    else:
        st.info("No approved documents")

def show_available_documents():
    """Show available documents for employees"""
    user = get_current_user()
    st.markdown("### 📚 Available Documents")

    with get_db_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                d.id,
                d.title,
                d.category,
                d.document_type,
                d.version,
                d.description,
                d.effective_date,
                d.file_path
            FROM documents d
            WHERE d.status = 'Active'
            AND d.approval_status = 'Approved'
            AND (d.access_level = 'Public - All Employees' OR d.access_level IS NULL)
            ORDER BY d.effective_date DESC
        """)
        documents = [dict(row) for row in cursor.fetchall()]

    if documents:
        # Category filter
        categories = list(set([d['category'] for d in documents if d['category']]))
        selected_category = st.selectbox("Filter by Category", ["All"] + categories)

        filtered = documents if selected_category == "All" else [d for d in documents if d['category'] == selected_category]

        for doc in filtered:
            with st.expander(f"📄 {doc['title']} (v{doc['version']})"):
                st.markdown(f"""
                **Category:** {doc['category']}
                **Type:** {doc['document_type']}
                **Version:** {doc['version']}
                **Effective Date:** {doc['effective_date']}
                """)

                if doc.get('description'):
                    st.info(doc['description'])

                if st.button(f"📥 Download", key=f"download_{doc['id']}", use_container_width=True):
                    record_download(doc['id'], user['employee_id'])
                    st.success(f"✅ Document downloaded!")
                    st.info(f"In production, file would be downloaded from: {doc.get('file_path', 'N/A')}")
    else:
        st.info("No documents available")

def show_my_downloads():
    """Show employee's download history"""
    user = get_current_user()
    st.markdown("### 📥 My Download History")

    with get_db_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                dh.download_date,
                d.title,
                d.version,
                d.category
            FROM document_history dh
            JOIN documents d ON dh.document_id = d.id
            WHERE dh.emp_id = %s
            ORDER BY dh.download_date DESC
            LIMIT 50
        """, (user['employee_id'],))
        downloads = [dict(row) for row in cursor.fetchall()]

    if downloads:
        for dl in downloads:
            st.markdown(f"📄 **{dl['title']}** (v{dl['version']}) - {dl['category']} - Downloaded: {dl['download_date']}")
    else:
        st.info("No download history")

def record_download(doc_id, emp_id):
    """Record document download"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # Increment download count
            cursor.execute("""
                UPDATE documents SET
                    download_count = COALESCE(download_count, 0) + 1
                WHERE id = %s
            """, (doc_id,))

            # Record in history
            cursor.execute("""
                INSERT INTO document_history (document_id, emp_id, action, download_date)
                VALUES (%s, %s, 'download', %s)
            """, (doc_id, emp_id, datetime.now().isoformat()))

            conn.commit()

    except Exception as e:
        st.error(f"❌ Error recording download: {str(e)}")

def show_document_analytics():
    """Show document analytics"""
    st.markdown("### 📊 Document Analytics")

    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Overall stats
        cursor.execute("""
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN status = 'Active' THEN 1 ELSE 0 END) as active,
                SUM(CASE WHEN status = 'Draft' THEN 1 ELSE 0 END) as draft,
                SUM(CASE WHEN status = 'Archived' THEN 1 ELSE 0 END) as archived,
                SUM(CASE WHEN approval_status = 'Pending' THEN 1 ELSE 0 END) as pending_approval,
                SUM(COALESCE(download_count, 0)) as total_downloads
            FROM documents
        """)
        stats = dict(cursor.fetchone())

        col1, col2, col3, col4, col5, col6 = st.columns(6)
        with col1:
            st.metric("Total", stats['total'] or 0)
        with col2:
            st.metric("Active", stats['active'] or 0)
        with col3:
            st.metric("Draft", stats['draft'] or 0)
        with col4:
            st.metric("Archived", stats['archived'] or 0)
        with col5:
            st.metric("Pending", stats['pending_approval'] or 0, delta_color="inverse")
        with col6:
            st.metric("Downloads", stats['total_downloads'] or 0)

        st.markdown("---")

        # By category
        st.markdown("#### By Category")
        cursor.execute("""
            SELECT
                category,
                COUNT(*) as count,
                SUM(CASE WHEN status = 'Active' THEN 1 ELSE 0 END) as active,
                SUM(COALESCE(download_count, 0)) as downloads
            FROM documents
            GROUP BY category
            ORDER BY count DESC
        """)
        by_category = [dict(row) for row in cursor.fetchall()]

        for cat in by_category:
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                st.markdown(f"**{cat['category']}**")
            with col2:
                st.markdown(f"Total: {cat['count']} ({cat['active']} active)")
            with col3:
                st.markdown(f"📥 {cat['downloads']} downloads")

        st.markdown("---")

        # Most downloaded
        st.markdown("#### 📈 Most Downloaded Documents")
        cursor.execute("""
            SELECT title, version, category, download_count
            FROM documents
            WHERE download_count > 0
            ORDER BY download_count DESC
            LIMIT 10
        """)
        top_docs = [dict(row) for row in cursor.fetchall()]

        if top_docs:
            for idx, doc in enumerate(top_docs, 1):
                st.markdown(f"{idx}. **{doc['title']}** (v{doc['version']}) - {doc['category']} - {doc['download_count']} downloads")
        else:
            st.info("No download data yet")

def show_my_documents():
    """Show documents created by manager"""
    user = get_current_user()
    st.markdown("### 📚 My Documents")

    with get_db_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM documents
            WHERE created_by = %s
            ORDER BY created_at DESC
        """, (user['employee_id'],))
        documents = [dict(row) for row in cursor.fetchall()]

    if documents:
        for doc in documents:
            status_emoji = {'Active': '🟢', 'Draft': '🟡', 'Archived': '⚪'}.get(doc['status'], '🔵')
            approval_emoji = {'Approved': '✅', 'Pending': '⏳', 'Rejected': '❌'}.get(doc['approval_status'], '❓')

            st.markdown(f"{status_emoji} {approval_emoji} **{doc['title']}** (v{doc['version']}) - {doc['status']} - {doc['approval_status']}")
    else:
        st.info("No documents created yet")

def show_document_settings():
    """Show document management settings"""
    st.markdown("### ⚙️ Document Management Settings")

    st.markdown("#### Approval Workflow")
    col1, col2 = st.columns(2)
    with col1:
        require_manager = st.checkbox("Require Manager Approval", value=True)
        require_hr = st.checkbox("Require HR Approval", value=True)
    with col2:
        auto_version = st.checkbox("Auto-increment version on approval", value=True)
        auto_archive = st.checkbox("Auto-archive expired documents", value=True)

    st.markdown("#### Access Control")
    default_access = st.selectbox("Default Access Level", [
        "Public - All Employees",
        "Managers Only",
        "HR Only"
    ])

    st.markdown("#### Retention Policy")
    retention_days = st.number_input("Archive documents after (days)", min_value=30, value=365)

    if st.button("💾 Save Settings", type="primary"):
        st.success("✅ Settings saved successfully!")
