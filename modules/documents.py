"""
Document Management Module
Central repository for company documents, policies, and files
"""

import streamlit as st
import pandas as pd
from datetime import datetime, date
from database import get_db_connection
from auth import get_current_user, is_hr_admin, is_manager, create_notification, log_audit

def show_document_management():
    """Main document management interface"""
    user = get_current_user()

    st.markdown("## 📁 Document Management")
    st.markdown("Central repository for company documents and files")
    st.markdown("---")

    if is_hr_admin():
        tabs = st.tabs(["📚 All Documents", "➕ Upload Document", "📊 Categories", "🗂️ Archive"])
    elif is_manager():
        tabs = st.tabs(["📚 Team Documents", "➕ Upload", "📥 My Documents"])
    else:
        tabs = st.tabs(["📥 My Documents", "📚 Company Docs", "📊 History"])

    with tabs[0]:
        if is_hr_admin():
            show_all_documents()
        elif is_manager():
            show_team_documents()
        else:
            show_my_documents()

    with tabs[1]:
        if is_hr_admin() or is_manager():
            show_upload_document()
        else:
            show_company_documents()

    if len(tabs) > 2:
        with tabs[2]:
            if is_hr_admin():
                show_document_categories()
            elif is_manager():
                show_my_documents()
            else:
                show_document_history()

    if len(tabs) > 3:
        with tabs[3]:
            show_archived_documents()

def show_my_documents():
    """Show employee's personal documents"""
    user = get_current_user()

    st.markdown("### 📥 My Documents")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM documents
            WHERE emp_id = %s OR visibility = 'Public'
            ORDER BY created_at DESC
        """, (user['employee_id'],))
        documents = [dict(row) for row in cursor.fetchall()]

    if documents:
        for doc in documents:
            doc_icon = {
                'Policy': '📋',
                'Handbook': '📖',
                'Form': '📄',
                'Certificate': '🎓',
                'Contract': '📜',
                'Report': '📊',
                'Other': '📁'
            }.get(doc['document_type'], '📁')

            with st.expander(f"{doc_icon} {doc['document_name']}"):
                col1, col2 = st.columns([2, 1])

                with col1:
                    st.markdown(f"""
                    **Document:** {doc['document_name']}
                    **Type:** {doc['document_type']}
                    **Category:** {doc.get('category', 'General')}
                    **Uploaded:** {doc['created_at'][:10] if doc['created_at'] else 'N/A'}
                    **Visibility:** {doc.get('visibility', 'Private')}
                    """)

                    if doc.get('description'):
                        st.info(f"📝 {doc['description']}")

                with col2:
                    st.markdown(f"**File:** {doc.get('file_name', 'N/A')}")
                    st.markdown(f"**Size:** {doc.get('file_size', 0)/1024:.1f} KB" if doc.get('file_size') else "Size: N/A")

                # Download button (simulated)
                if st.button(f"📥 Download", key=f"dl_{doc['id']}"):
                    st.info("Download functionality: In production, this would download the actual file")
    else:
        st.info("No documents available")

def show_company_documents():
    """Show public company documents"""
    st.markdown("### 📚 Company Documents")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM documents
            WHERE visibility = 'Public'
            ORDER BY category, document_name
        """)
        documents = [dict(row) for row in cursor.fetchall()]

    if documents:
        # Group by category
        categories = {}
        for doc in documents:
            cat = doc.get('category', 'General')
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(doc)

        for category, docs in categories.items():
            st.markdown(f"#### 📂 {category}")
            for doc in docs:
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    st.markdown(f"**{doc['document_name']}**")
                with col2:
                    st.markdown(f"_{doc['document_type']}_")
                with col3:
                    if st.button("📥", key=f"pub_{doc['id']}"):
                        st.info("Download: File would be downloaded")
    else:
        st.info("No public documents yet")

def show_document_history():
    """Show document access history"""
    user = get_current_user()

    st.markdown("### 📊 Document Access History")

    st.info("Document access tracking would show here when implemented")

def show_team_documents():
    """Show team documents (Manager view)"""
    user = get_current_user()

    st.markdown("### 📚 Team Documents")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT d.*, e.first_name, e.last_name, e.employee_id
            FROM documents d
            LEFT JOIN employees e ON d.emp_id = e.id
            WHERE e.manager_id = %s OR d.visibility = 'Public'
            ORDER BY d.created_at DESC
        """, (user['employee_id'],))
        documents = [dict(row) for row in cursor.fetchall()]

    if documents:
        for doc in documents:
            with st.expander(f"📁 {doc['document_name']} - {doc.get('first_name', 'Company')} {doc.get('last_name', 'Doc')}"):
                st.markdown(f"""
                **Document:** {doc['document_name']}
                **Type:** {doc['document_type']}
                **Owner:** {doc.get('first_name', 'N/A')} {doc.get('last_name', '')} ({doc.get('employee_id', 'Company')})
                **Uploaded:** {doc['created_at'][:10]}
                **Visibility:** {doc.get('visibility', 'Private')}
                """)
    else:
        st.info("No team documents")

def show_upload_document():
    """Upload new document"""
    user = get_current_user()

    st.markdown("### ➕ Upload Document")

    with st.form("upload_document"):
        document_name = st.text_input("Document Name *", placeholder="e.g., Employee Handbook 2024")

        col1, col2 = st.columns(2)

        with col1:
            document_type = st.selectbox("Document Type *", [
                "Policy", "Handbook", "Form", "Certificate",
                "Contract", "Report", "Guideline", "Other"
            ])
            category = st.text_input("Category", placeholder="e.g., HR Policies", value="General")

        with col2:
            visibility = st.selectbox("Visibility *", ["Private", "Team", "Public"])
            target_dept = st.text_input("Target Department (optional)", placeholder="All departments if empty")

        description = st.text_area("Description", placeholder="Brief description of the document...")

        # File upload (simulated)
        uploaded_file = st.file_uploader("Upload File", type=['pdf', 'doc', 'docx', 'xls', 'xlsx', 'txt'])

        submitted = st.form_submit_button("📤 Upload Document", use_container_width=True)

        if submitted:
            if not all([document_name, document_type, visibility]):
                st.error("❌ Please fill all required fields")
            else:
                file_name = uploaded_file.name if uploaded_file else "document.pdf"
                file_size = uploaded_file.size if uploaded_file else 0
                create_document(document_name, document_type, category, visibility,
                              description, file_name, file_size, target_dept)
                st.rerun()

def show_all_documents():
    """Show all documents (HR view)"""
    st.markdown("### 📚 All Documents")

    # Filters
    col1, col2, col3 = st.columns(3)
    with col1:
        type_filter = st.selectbox("Type", ["All", "Policy", "Handbook", "Form", "Certificate", "Contract", "Report", "Other"])
    with col2:
        visibility_filter = st.selectbox("Visibility", ["All", "Private", "Team", "Public"])
    with col3:
        search = st.text_input("🔍 Search")

    with get_db_connection() as conn:
        cursor = conn.cursor()

        query = """
            SELECT d.*, e.first_name, e.last_name, e.employee_id
            FROM documents d
            LEFT JOIN employees e ON d.emp_id = e.id
            WHERE 1=1
        """
        params = []

        if type_filter != "All":
            query += " AND d.document_type = %s"
            params.append(type_filter)

        # visibility_filter removed - column doesn't exist in schema

        if search:
            query += " AND d.document_name LIKE %s"
            params.append(f"%{search}%")

        query += " ORDER BY d.created_at DESC LIMIT 50"

        cursor.execute(query, params)
        documents = [dict(row) for row in cursor.fetchall()]

    if documents:
        df = pd.DataFrame(documents)
        # Use only columns that exist in schema
        available_cols = [col for col in ['document_name', 'document_type', 'status', 'created_at'] if col in df.columns]
        df_display = df[available_cols].copy()

        # Rename columns for display
        col_mapping = {
            'document_name': 'Document',
            'document_type': 'Type',
            'status': 'Status',
            'created_at': 'Uploaded'
        }
        df_display = df_display.rename(columns={k: v for k, v in col_mapping.items() if k in df_display.columns})
        df_display['Uploaded'] = df_display['Uploaded'].str[:10]

        st.dataframe(df_display, use_container_width=True, hide_index=True)

        # Bulk actions
        st.markdown("---")
        if st.button("📥 Export List"):
            st.success("Document list exported (simulated)")
    else:
        st.info("No documents found")

def show_document_categories():
    """Show document categories"""
    st.markdown("### 📊 Document Categories")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT category, COUNT(*) as count, document_type
            FROM documents
            WHERE status = 'Active'
            GROUP BY category, document_type
            ORDER BY count DESC
        """)
        categories = [dict(row) for row in cursor.fetchall()]

    if categories:
        for cat in categories:
            st.markdown(f"**{cat['category']}** - {cat['document_type']}: {cat['count']} documents")
    else:
        st.info("No categories yet")

def show_archived_documents():
    """Show archived documents"""
    st.markdown("### 🗂️ Archived Documents")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM documents
            WHERE status = 'Archived'
            ORDER BY updated_at DESC
            LIMIT 20
        """)
        archived = [dict(row) for row in cursor.fetchall()]

    if archived:
        for doc in archived:
            st.markdown(f"📦 **{doc['document_name']}** - Archived on {doc.get('updated_at', 'N/A')[:10]}")
    else:
        st.info("No archived documents")

def create_document(document_name, document_type, category, visibility,
                   description, file_name, file_size, target_dept):
    """Create new document record"""
    user = get_current_user()

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # Simulate file upload path
            file_path = f"documents/{user['employee_id']}_{datetime.now().timestamp()}_{file_name}"

            cursor.execute("""
                INSERT INTO documents (
                    emp_id, document_name, document_type, category,
                    description, file_name, file_path, file_size,
                    visibility, target_department, status
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'Active')
            """, (user['employee_id'], document_name, document_type, category,
                 description, file_name, file_path, file_size,
                 visibility, target_dept))

            doc_id = cursor.lastrowid

            conn.commit()
            log_audit(f"Uploaded document: {document_name}", "documents", doc_id)
            st.success(f"✅ Document uploaded successfully! ID: DOC-{doc_id}")
            st.balloons()

    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
