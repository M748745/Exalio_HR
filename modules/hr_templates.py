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

    if is_hr_admin():
        tabs = st.tabs(["📚 All Templates", "➕ Upload Template", "📊 Popular Templates", "⚙️ Manage Catalog"])
    else:
        tabs = st.tabs(["📚 All Templates", "📊 Popular Templates"])

    with tabs[0]:
        show_all_templates()

    if is_hr_admin():
        with tabs[1]:
            show_add_template()

        with tabs[2]:
            show_popular_templates()

        with tabs[3]:
            show_manage_catalog()
    else:
        with tabs[1]:
            show_popular_templates()


def show_all_templates():
    """Display all available HR templates"""
    st.markdown("### 📚 Available HR Templates")

    # DEBUG: Show admin status
    if is_hr_admin():
        st.success("✅ You are logged in as HR Admin - You can manage templates in the 'Manage Catalog' tab")
    else:
        st.info("ℹ️ You are logged in as a regular user")

    # Get template categories from database
    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Check if table exists, if not create it
        try:
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_name = 'hr_template_catalog'
                )
            """)
            table_exists = cursor.fetchone()[0]

            if not table_exists:
                # Create table
                cursor.execute("""
                    CREATE TABLE hr_template_catalog (
                        id SERIAL PRIMARY KEY,
                        template_name TEXT NOT NULL,
                        category TEXT NOT NULL,
                        description TEXT,
                        is_active INTEGER DEFAULT 1,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        created_by INTEGER,
                        display_order INTEGER DEFAULT 0
                    )
                """)
                conn.commit()

            # Initialize default templates if table is empty
            cursor.execute("SELECT COUNT(*) as count FROM hr_template_catalog")
            if cursor.fetchone()['count'] == 0:
                init_default_templates(cursor)
                conn.commit()

            # Load templates from database
            cursor.execute("""
                SELECT id, template_name, category, description
                FROM hr_template_catalog
                WHERE is_active = 1
                ORDER BY category, display_order, template_name
            """)
            catalog_templates = [dict(row) for row in cursor.fetchall()]

        except Exception as e:
            st.error(f"Error loading templates: {str(e)}")
            catalog_templates = []

    # Group by category
    categories = {}
    category_icons = {
        "Forms": "📝",
        "Letters": "📄",
        "Policies": "📋",
        "Evaluations": "📊",
        "Onboarding": "🎓",
        "Offboarding": "🚪",
        "Other": "📁"
    }

    for template in catalog_templates:
        cat = template['category']
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(template)

    # Get saved templates (uploaded files) from database
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
        icon = category_icons.get(category, "📁")
        with st.expander(f"{icon} {category} ({len(templates)} templates)"):
            for template in templates:
                # Check if template file is uploaded
                saved = next((t for t in saved_templates if t['document_name'] == template['template_name']), None)

                if is_hr_admin() and saved:
                    col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
                else:
                    col1, col2, col3 = st.columns([3, 1, 1])

                with col1:
                    st.markdown(f"**{template['template_name']}**")
                    if template.get('description'):
                        st.caption(template['description'])

                with col2:
                    if saved:
                        if is_hr_admin():
                            st.markdown("✅ Uploaded")
                        else:
                            st.markdown("✅ Available")
                    else:
                        st.markdown("📥 Not Uploaded")

                with col3:
                    if saved and saved.get('file_content'):
                        if st.button("📥 Download", key=f"dl_{template['id']}_{saved['id']}"):
                            from modules.documents import download_document
                            download_document(saved['id'], saved['file_name'], saved.get('mime_type', 'application/pdf'))
                    else:
                        if st.button("📄 Info", key=f"info_{template['id']}"):
                            show_template_preview(template['template_name'])

                # Admin delete button for uploaded files
                if is_hr_admin() and saved:
                    with col4:
                        template_desc = f"File: {template['template_name']}"
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


def init_default_templates(cursor):
    """Initialize default template catalog"""
    default_templates = [
        # Forms
        ("Leave Request Form", "Forms", "Standard form for employees to request time off"),
        ("Expense Claim Form", "Forms", "Form for submitting business expense reimbursements"),
        ("Timesheet Template", "Forms", "Weekly/monthly timesheet for tracking work hours"),
        ("Training Request Form", "Forms", "Request form for training and development programs"),
        ("Asset Request Form", "Forms", "Form to request company assets and equipment"),

        # Letters
        ("Job Offer Letter", "Letters", "Professional job offer template with position details"),
        ("Promotion Letter", "Letters", "Letter template for employee promotions"),
        ("Warning Letter", "Letters", "Formal warning letter template for disciplinary actions"),
        ("Termination Letter", "Letters", "Employee termination letter template"),
        ("Reference Letter", "Letters", "Employment reference letter template"),

        # Policies
        ("Employee Handbook", "Policies", "Complete employee handbook covering all policies"),
        ("Code of Conduct", "Policies", "Company code of conduct and ethics policy"),
        ("Remote Work Policy", "Policies", "Policy for remote and hybrid work arrangements"),
        ("Leave Policy", "Policies", "Comprehensive leave policy documentation"),
        ("Expense Policy", "Policies", "Company expense reimbursement policy"),

        # Evaluations
        ("Performance Appraisal Form", "Evaluations", "Annual performance review template"),
        ("360-Degree Feedback Form", "Evaluations", "Multi-source feedback evaluation form"),
        ("Probation Review Form", "Evaluations", "Employee probation period assessment"),
        ("Self-Assessment Template", "Evaluations", "Employee self-evaluation form"),
        ("Goal Setting Template", "Evaluations", "SMART goals and objectives template"),

        # Onboarding
        ("Onboarding Checklist", "Onboarding", "Complete new hire onboarding checklist"),
        ("New Hire Information Form", "Onboarding", "Personal information collection form"),
        ("Equipment Assignment Form", "Onboarding", "IT equipment and access request form"),
        ("Emergency Contact Form", "Onboarding", "Emergency contact information form"),
        ("Confidentiality Agreement", "Onboarding", "NDA and confidentiality agreement"),

        # Offboarding
        ("Exit Interview Template", "Offboarding", "Structured exit interview questionnaire"),
        ("Exit Checklist", "Offboarding", "Employee departure checklist"),
        ("Knowledge Transfer Template", "Offboarding", "Documentation for knowledge handover"),
        ("Final Settlement Form", "Offboarding", "Final payroll and benefits settlement"),
        ("Clearance Certificate", "Offboarding", "Employee clearance and release certificate")
    ]

    for idx, (name, category, description) in enumerate(default_templates):
        cursor.execute("""
            INSERT INTO hr_template_catalog (template_name, category, description, display_order)
            VALUES (%s, %s, %s, %s)
        """, (name, category, description, idx))


def show_manage_catalog():
    """Admin interface to manage template catalog"""
    st.markdown("### ⚙️ Manage Template Catalog")
    st.markdown("Add, edit, or delete template names from the catalog")
    st.markdown("---")

    # Add new template
    with st.expander("➕ Add New Template Name", expanded=False):
        with st.form("add_template_name"):
            col1, col2 = st.columns(2)

            with col1:
                new_name = st.text_input("Template Name *", placeholder="e.g., Performance Improvement Plan")
                new_category = st.selectbox("Category *", [
                    "Forms", "Letters", "Policies", "Evaluations", "Onboarding", "Offboarding", "Other"
                ])

            with col2:
                new_description = st.text_area("Description", placeholder="Brief description of this template...")
                new_order = st.number_input("Display Order", min_value=0, value=0, help="Lower numbers appear first")

            submitted = st.form_submit_button("➕ Add Template Name", use_container_width=True)

            if submitted:
                if not all([new_name, new_category]):
                    st.error("❌ Please fill template name and category")
                else:
                    try:
                        user = get_current_user()
                        with get_db_connection() as conn:
                            cursor = conn.cursor()

                            cursor.execute("""
                                INSERT INTO hr_template_catalog (
                                    template_name, category, description, display_order, created_by
                                ) VALUES (%s, %s, %s, %s, %s)
                            """, (new_name, new_category, new_description, new_order, user['employee_id']))

                            conn.commit()
                            log_audit(f"Added template to catalog: {new_name}", "hr_template_catalog", cursor.lastrowid)
                            st.success(f"✅ Template '{new_name}' added to catalog!")
                            st.rerun()

                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")

    st.markdown("---")

    # List all templates with delete option
    st.markdown("### 📋 Current Template Catalog")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, template_name, category, description, display_order, is_active
            FROM hr_template_catalog
            ORDER BY category, display_order, template_name
        """)
        all_templates = [dict(row) for row in cursor.fetchall()]

    if all_templates:
        # Group by category
        by_category = {}
        for template in all_templates:
            cat = template['category']
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(template)

        for category, templates in by_category.items():
            st.markdown(f"#### 📂 {category} ({len(templates)} templates)")

            for template in templates:
                col1, col2, col3, col4 = st.columns([3, 1, 1, 1])

                with col1:
                    status = "✅ Active" if template['is_active'] else "❌ Inactive"
                    st.markdown(f"**{template['template_name']}** ({status})")
                    if template.get('description'):
                        st.caption(template['description'])

                with col2:
                    st.markdown(f"Order: {template['display_order']}")

                with col3:
                    if template['is_active']:
                        if st.button("❌ Deactivate", key=f"deact_{template['id']}", use_container_width=True):
                            toggle_template_status(template['id'], 0)
                            st.rerun()
                    else:
                        if st.button("✅ Activate", key=f"act_{template['id']}", use_container_width=True):
                            toggle_template_status(template['id'], 1)
                            st.rerun()

                with col4:
                    template_desc = f"Template: {template['template_name']}"
                    if render_delete_button("hr_template_catalog", template['id'], template_desc, f"del_cat_{template['id']}"):
                        st.rerun()

                st.markdown("---")
    else:
        st.info("No templates in catalog. Click 'Add New Template Name' to get started.")


def toggle_template_status(template_id, new_status):
    """Toggle template active status"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE hr_template_catalog
                SET is_active = %s
                WHERE id = %s
            """, (new_status, template_id))
            conn.commit()

            status_text = "activated" if new_status else "deactivated"
            log_audit(f"Template {status_text}", "hr_template_catalog", template_id)
            st.success(f"✅ Template {status_text} successfully!")

    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
