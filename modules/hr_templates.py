"""
HR Templates Module
Pre-loaded HR document templates and forms
"""

import streamlit as st
from datetime import datetime
from database import get_db_connection
from auth import get_current_user, is_hr_admin, log_audit
from modules.delete_utils import render_delete_button


def show_hr_templates():
    """Display HR templates library"""
    st.markdown("## 📋 HR Templates Library")
    st.markdown("Download and customize ready-to-use HR templates")
    st.markdown("---")

    tabs = st.tabs(["📚 All Templates", "➕ Add Template", "📊 Popular Templates"])

    with tabs[0]:
        show_all_templates()

    with tabs[1]:
        if is_hr_admin():
            show_add_template()
        else:
            st.info("Only HR Admin can add templates")

    with tabs[2]:
        show_popular_templates()


def show_all_templates():
    """Display all available HR templates"""
    st.markdown("### 📚 Available HR Templates")

    # Template categories
    categories = {
        "📝 Forms": [
            "Leave Request Form",
            "Expense Claim Form",
            "Timesheet Template",
            "Training Request Form",
            "Asset Request Form"
        ],
        "📄 Letters": [
            "Job Offer Letter",
            "Promotion Letter",
            "Warning Letter",
            "Termination Letter",
            "Reference Letter"
        ],
        "📋 Policies": [
            "Employee Handbook",
            "Code of Conduct",
            "Remote Work Policy",
            "Leave Policy",
            "Expense Policy"
        ],
        "📊 Evaluations": [
            "Performance Appraisal Form",
            "360-Degree Feedback Form",
            "Probation Review Form",
            "Self-Assessment Template",
            "Goal Setting Template"
        ],
        "🎓 Onboarding": [
            "Onboarding Checklist",
            "New Hire Information Form",
            "Equipment Assignment Form",
            "Emergency Contact Form",
            "Confidentiality Agreement"
        ],
        "🚪 Offboarding": [
            "Exit Interview Template",
            "Exit Checklist",
            "Knowledge Transfer Template",
            "Final Settlement Form",
            "Clearance Certificate"
        ]
    }

    # Get saved templates from database
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM documents
            WHERE category = 'HR Template' AND visibility = 'Public'
            ORDER BY download_count DESC, document_name
        """)
        saved_templates = [dict(row) for row in cursor.fetchall()]

    # Display categories
    for category, templates in categories.items():
        with st.expander(f"{category} ({len(templates)} templates)"):
            for template in templates:
                # Check if template exists in database
                saved = next((t for t in saved_templates if t['document_name'] == template), None)

                if is_hr_admin() and saved:
                    col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
                else:
                    col1, col2, col3 = st.columns([3, 1, 1])

                with col1:
                    st.markdown(f"**{template}**")

                with col2:
                    if saved:
                        st.markdown("✅ Uploaded")
                    else:
                        st.markdown("📥 Default")

                with col3:
                    if st.button("📄 View", key=f"view_{template}"):
                        show_template_preview(template)

                # Admin delete button for uploaded templates
                if is_hr_admin() and saved:
                    with col4:
                        template_desc = f"Template: {template}"
                        if render_delete_button("documents", saved['id'], template_desc, f"del_tpl_{saved['id']}"):
                            st.rerun()

    # Display saved custom templates
    if saved_templates:
        st.markdown("---")
        st.markdown("### 💾 Custom Uploaded Templates")
        for template in saved_templates:
            if template['document_name'] not in [t for cats in categories.values() for t in cats]:
                if is_hr_admin():
                    col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
                else:
                    col1, col2, col3 = st.columns([3, 1, 1])

                with col1:
                    st.markdown(f"**{template['document_name']}**")
                with col2:
                    st.markdown(f"📥 {template.get('download_count', 0)} downloads")
                with col3:
                    if st.button("📥 Download", key=f"dl_custom_{template['id']}"):
                        from modules.documents import download_document
                        download_document(template['id'], template['file_name'], template.get('mime_type', 'application/pdf'))

                # Admin delete button for custom templates
                if is_hr_admin():
                    with col4:
                        template_desc = f"Custom Template: {template['document_name']}"
                        if render_delete_button("documents", template['id'], template_desc, f"del_custom_{template['id']}"):
                            st.rerun()


def show_template_preview(template_name):
    """Show template preview and details"""
    st.markdown(f"### 📄 {template_name}")

    # Template descriptions
    descriptions = {
        "Leave Request Form": "Standard form for employees to request time off. Includes leave type, dates, reason, and approval section.",
        "Expense Claim Form": "Form for submitting business expense reimbursements. Includes expense details, receipts, and approval workflow.",
        "Job Offer Letter": "Professional job offer template with position details, compensation, benefits, and start date.",
        "Performance Appraisal Form": "Comprehensive performance review form with rating scales, competencies, and development plans.",
        "Employee Handbook": "Complete employee handbook template covering policies, procedures, code of conduct, and benefits.",
        "Onboarding Checklist": "Step-by-step checklist for new employee onboarding, from pre-hire to first 90 days.",
        "Exit Interview Template": "Structured exit interview questionnaire to gather feedback from departing employees.",
    }

    description = descriptions.get(template_name, "Professional HR template ready for customization.")
    st.info(f"📝 {description}")

    # Check if template is uploaded
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM documents
            WHERE document_name = %s AND category = 'HR Template'
            LIMIT 1
        """, (template_name,))
        saved_template = cursor.fetchone()

    if saved_template and saved_template.get('file_content'):
        st.success("✅ This template is available for download")
        if st.button("📥 Download Template", key=f"dl_{template_name}"):
            from modules.documents import download_document
            download_document(saved_template['id'], saved_template['file_name'], saved_template.get('mime_type', 'application/pdf'))
    else:
        st.warning("⚠️ Template file not yet uploaded. Contact HR Admin to upload this template.")


def show_add_template():
    """Add new HR template (Admin only)"""
    st.markdown("### ➕ Upload HR Template")

    with st.form("add_template"):
        template_name = st.text_input("Template Name *", placeholder="e.g., Leave Request Form")

        col1, col2 = st.columns(2)
        with col1:
            template_category = st.selectbox("Category *", [
                "Forms", "Letters", "Policies", "Evaluations", "Onboarding", "Offboarding", "Other"
            ])

        with col2:
            template_type = st.selectbox("Document Type *", [
                "Form", "Policy", "Handbook", "Certificate", "Report", "Guideline"
            ])

        description = st.text_area("Description", placeholder="Brief description of what this template is for...")

        uploaded_file = st.file_uploader("Upload Template File *", type=['pdf', 'doc', 'docx', 'xls', 'xlsx'])

        submitted = st.form_submit_button("📤 Upload Template", use_container_width=True)

        if submitted:
            if not all([template_name, template_category, template_type, uploaded_file]):
                st.error("❌ Please fill all required fields and upload a file")
            else:
                try:
                    user = get_current_user()

                    file_name = uploaded_file.name
                    file_size = uploaded_file.size
                    file_content = uploaded_file.read()
                    mime_type = uploaded_file.type

                    # Check file size (limit to 10MB for templates)
                    if file_size > 10 * 1024 * 1024:
                        st.error("❌ File too large. Maximum size is 10MB for templates.")
                        return

                    with get_db_connection() as conn:
                        cursor = conn.cursor()

                        file_path = f"templates/{user['employee_id']}_{datetime.now().timestamp()}_{file_name}"

                        cursor.execute("""
                            INSERT INTO documents (
                                emp_id, document_name, document_type, category,
                                description, file_name, file_path, file_size,
                                visibility, status, file_content, mime_type
                            ) VALUES (%s, %s, %s, 'HR Template', %s, %s, %s, %s, 'Public', 'Active', %s, %s)
                        """, (user['employee_id'], template_name, template_type,
                             description, file_name, file_path, file_size,
                             file_content, mime_type))

                        template_id = cursor.lastrowid
                        conn.commit()

                        log_audit(f"Uploaded HR template: {template_name}", "documents", template_id)
                        st.success(f"✅ Template uploaded successfully! ID: TPL-{template_id}")
                        st.balloons()
                        st.rerun()

                except Exception as e:
                    st.error(f"❌ Error uploading template: {str(e)}")


def show_popular_templates():
    """Show most downloaded templates"""
    st.markdown("### 📊 Most Popular Templates")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, document_name, document_type, download_count, file_size, created_at
            FROM documents
            WHERE category = 'HR Template' AND visibility = 'Public'
            ORDER BY download_count DESC
            LIMIT 10
        """)
        popular = [dict(row) for row in cursor.fetchall()]

    if popular:
        for idx, template in enumerate(popular, 1):
            with st.container():
                if is_hr_admin():
                    col1, col2, col3, col4, col5 = st.columns([3, 1, 1, 1, 1])
                else:
                    col1, col2, col3, col4 = st.columns([3, 1, 1, 1])

                with col1:
                    st.markdown(f"**{idx}. {template['document_name']}**")
                    st.markdown(f"<small>{template['document_type']}</small>", unsafe_allow_html=True)

                with col2:
                    st.metric("Downloads", template.get('download_count', 0))

                with col3:
                    size_kb = template.get('file_size', 0) / 1024
                    st.markdown(f"📦 {size_kb:.0f} KB")

                with col4:
                    if st.button("📥", key=f"pop_{idx}"):
                        st.info(f"Download {template['document_name']}")

                # Admin delete button
                if is_hr_admin():
                    with col5:
                        template_desc = f"Popular Template: {template['document_name']}"
                        if render_delete_button("documents", template['id'], template_desc, f"del_pop_{template['id']}"):
                            st.rerun()

                st.markdown("---")
    else:
        st.info("No templates uploaded yet. Upload templates to see statistics.")


def get_template_content(template_name):
    """Get template content from database"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT file_content, mime_type, file_name
            FROM documents
            WHERE document_name = %s AND category = 'HR Template'
            LIMIT 1
        """, (template_name,))
        return cursor.fetchone()
