"""
Compliance Tracking Module
Regulatory compliance monitoring and documentation
"""

import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
from database import get_db_connection
from auth import get_current_user, is_hr_admin, is_manager, create_notification, log_audit

def show_compliance_tracking():
    """Main compliance tracking interface"""
    user = get_current_user()

    st.markdown("## ⚖️ Compliance Tracking")
    st.markdown("Regulatory compliance monitoring and documentation")
    st.markdown("---")

    if is_hr_admin():
        tabs = st.tabs(["📋 Overview", "📜 Requirements", "✅ Audits", "📊 Reports", "⚠️ Issues"])
    else:
        st.warning("⚠️ Compliance tracking is only available for HR Administrators")
        return

    with tabs[0]:
        show_compliance_overview()

    with tabs[1]:
        show_compliance_requirements()

    with tabs[2]:
        show_compliance_audits()

    with tabs[3]:
        show_compliance_reports()

    with tabs[4]:
        show_compliance_issues()

def show_compliance_overview():
    """Show compliance overview dashboard"""
    st.markdown("### 📋 Compliance Overview")

    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Total requirements
        cursor.execute("SELECT COUNT(*) as cnt FROM compliance_requirements")
        total_reqs = cursor.fetchone()['cnt']

        # Compliant count
        cursor.execute("""
            SELECT COUNT(*) as cnt FROM compliance_requirements
            WHERE status = 'Compliant'
        """)
        compliant = cursor.fetchone()['cnt']

        # Overdue
        cursor.execute("""
            SELECT COUNT(*) as cnt FROM compliance_requirements
            WHERE due_date < CURRENT_DATE AND status != 'Compliant'
        """)
        overdue = cursor.fetchone()['cnt']

        # Upcoming reviews (next 30 days)
        cursor.execute("""
            SELECT COUNT(*) as cnt FROM compliance_requirements
            WHERE due_date BETWEEN CURRENT_DATE AND (CURRENT_DATE + INTERVAL '30 days')
        """)
        upcoming = cursor.fetchone()['cnt']

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Requirements", total_reqs)
    with col2:
        compliance_rate = (compliant / total_reqs * 100) if total_reqs > 0 else 0
        st.metric("Compliant", f"{compliant} ({compliance_rate:.0f}%)")
    with col3:
        st.metric("Overdue Reviews", overdue, delta=f"-{overdue}" if overdue > 0 else None)
    with col4:
        st.metric("Upcoming (30d)", upcoming)

    # Compliance progress
    st.markdown("---")
    st.markdown("### 📊 Compliance Status")
    if total_reqs > 0:
        st.progress(compliance_rate / 100)

    # Recent activity
    st.markdown("---")
    st.markdown("### 📝 Recent Compliance Activity")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM audit_logs
            WHERE entity_type = 'compliance'
            ORDER BY timestamp DESC
            LIMIT 10
        """)
        recent = [dict(row) for row in cursor.fetchall()]

    if recent:
        for activity in recent:
            timestamp_str = str(activity['timestamp'])[:16] if activity.get('timestamp') else 'N/A'
            st.markdown(f"- {activity.get('action', 'Unknown')} _{timestamp_str}_")
    else:
        st.info("No recent activity")

def show_compliance_requirements():
    """Show compliance requirements"""
    st.markdown("### 📜 Compliance Requirements")

    # Filters
    col1, col2 = st.columns(2)
    with col1:
        category_filter = st.selectbox("Category", [
            "All", "Labor Law", "Health & Safety", "Data Privacy",
            "Employment", "Tax", "Benefits", "Training"
        ])
    with col2:
        status_filter = st.selectbox("Status", ["All", "Compliant", "In Progress", "Overdue", "Not Started"])

    # Add new requirement
    with st.expander("➕ Add New Requirement"):
        with st.form("add_requirement"):
            req_name = st.text_input("Requirement Name *")
            category = st.selectbox("Category *", [
                "Labor Law", "Health & Safety", "Data Privacy",
                "Employment", "Tax", "Benefits", "Training"
            ])

            col1, col2 = st.columns(2)
            with col1:
                review_frequency = st.selectbox("Review Frequency", [
                    "Monthly", "Quarterly", "Semi-Annual", "Annual", "Biennial"
                ])
            with col2:
                next_review = st.date_input("Next Review Date *")

            description = st.text_area("Description", placeholder="Describe the requirement...")
            responsible = st.text_input("Responsible Person/Team", value="HR Team")

            if st.form_submit_button("➕ Add Requirement"):
                if req_name and category and next_review:
                    add_compliance_requirement(req_name, category, description,
                                              review_frequency, next_review, responsible)
                    st.rerun()

    # Display requirements
    st.markdown("---")

    with get_db_connection() as conn:
        cursor = conn.cursor()

        query = "SELECT * FROM compliance_requirements WHERE 1=1"
        params = []

        if category_filter != "All":
            query += " AND requirement_type = %s"
            params.append(category_filter)

        if status_filter != "All":
            query += " AND status = %s"
            params.append(status_filter)

        query += " ORDER BY next_review_date ASC"

        cursor.execute(query, params)
        requirements = [dict(row) for row in cursor.fetchall()]

    if requirements:
        for req in requirements:
            # Determine status color
            status_colors = {
                'Compliant': 'rgba(46, 213, 115, 0.15)',
                'In Progress': 'rgba(240, 180, 41, 0.15)',
                'Overdue': 'rgba(241, 100, 100, 0.15)',
                'Not Started': 'rgba(125, 150, 190, 0.1)'
            }
            color = status_colors.get(req['status'], 'rgba(125, 150, 190, 0.1)')

            # Check if overdue
            if req['next_review_date']:
                review_date = datetime.strptime(req['next_review_date'], '%Y-%m-%d').date()
                is_overdue = review_date < date.today() and req['status'] != 'Compliant'
                days_until = (review_date - date.today()).days
            else:
                is_overdue = False
                days_until = None

            with st.expander(f"{'⚠️' if is_overdue else '📜'} {req['requirement_name']} - {req['status']}"):
                st.markdown(f"""
                **Category:** {req['category']}
                **Status:** {req['status']}
                **Review Frequency:** {req['review_frequency']}
                **Next Review:** {req['next_review_date']} {f"({'Overdue by ' + str(abs(days_until)) + ' days'})" if is_overdue else f"(In {days_until} days)" if days_until and days_until >= 0 else ''}
                **Responsible:** {req['responsible_person']}
                **Last Updated:** {req.get('updated_at', 'Never')[:10]}
                """)

                if req['description']:
                    st.info(f"📝 {req['description']}")

                # Actions
                col1, col2, col3 = st.columns(3)
                with col1:
                    if req['status'] != 'Compliant':
                        if st.button("✅ Mark Compliant", key=f"comply_{req['id']}"):
                            update_requirement_status(req['id'], 'Compliant')
                            st.rerun()
                with col2:
                    if st.button("📝 Update", key=f"update_{req['id']}"):
                        st.info("Update form would open here")
                with col3:
                    if st.button("🗑️ Delete", key=f"del_{req['id']}"):
                        delete_requirement(req['id'])
                        st.rerun()
    else:
        st.info("No compliance requirements found")

def show_compliance_audits():
    """Show compliance audits"""
    st.markdown("### ✅ Compliance Audits")

    # Schedule new audit
    with st.expander("➕ Schedule New Audit"):
        with st.form("schedule_audit"):
            audit_name = st.text_input("Audit Name *")
            audit_type = st.selectbox("Audit Type *", [
                "Internal", "External", "Regulatory", "Self-Assessment"
            ])

            col1, col2 = st.columns(2)
            with col1:
                audit_date = st.date_input("Audit Date *")
            with col2:
                auditor = st.text_input("Auditor/Firm *")

            scope = st.text_area("Audit Scope", placeholder="What areas will be audited...")
            notes = st.text_area("Notes")

            if st.form_submit_button("📅 Schedule Audit"):
                if audit_name and audit_type and audit_date and auditor:
                    schedule_audit(audit_name, audit_type, audit_date, auditor, scope, notes)
                    st.rerun()

    # Display audits
    st.markdown("---")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM compliance_audits
            ORDER BY audit_date DESC
            LIMIT 20
        """)
        audits = [dict(row) for row in cursor.fetchall()]

    if audits:
        for audit in audits:
            status_icon = {
                'Scheduled': '📅',
                'In Progress': '⏳',
                'Completed': '✅',
                'Failed': '❌'
            }.get(audit['status'], '📋')

            with st.expander(f"{status_icon} {audit['audit_name']} - {audit['status']}"):
                st.markdown(f"""
                **Type:** {audit['audit_type']}
                **Date:** {audit['audit_date']}
                **Auditor:** {audit['auditor']}
                **Status:** {audit['status']}
                **Scheduled:** {audit['created_at'][:10]}
                """)

                if audit.get('scope'):
                    st.info(f"📋 **Scope:** {audit['scope']}")

                if audit.get('findings'):
                    st.warning(f"⚠️ **Findings:** {audit['findings']}")

                if audit.get('notes'):
                    st.markdown(f"**Notes:** {audit['notes']}")

                # Actions
                if audit['status'] == 'Scheduled':
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("▶️ Start Audit", key=f"start_{audit['id']}"):
                            update_audit_status(audit['id'], 'In Progress')
                            st.rerun()
                    with col2:
                        if st.button("❌ Cancel", key=f"cancel_{audit['id']}"):
                            update_audit_status(audit['id'], 'Cancelled')
                            st.rerun()

                elif audit['status'] == 'In Progress':
                    with st.form(f"complete_audit_{audit['id']}"):
                        findings = st.text_area("Findings", placeholder="Document audit findings...")
                        result = st.selectbox("Result", ["Passed", "Failed", "Partial"])

                        if st.form_submit_button("✅ Complete Audit"):
                            complete_audit(audit['id'], findings, result)
                            st.rerun()
    else:
        st.info("No audits scheduled")

def show_compliance_reports():
    """Show compliance reports"""
    st.markdown("### 📊 Compliance Reports")

    # Report type selector
    report_type = st.selectbox("Report Type", [
        "Compliance Summary",
        "Audit History",
        "Requirements by Category",
        "Overdue Items",
        "Training Completion",
        "Document Expiry"
    ])

    if st.button("📄 Generate Report"):
        with st.spinner("Generating report..."):
            if report_type == "Compliance Summary":
                generate_compliance_summary()
            elif report_type == "Audit History":
                generate_audit_history()
            elif report_type == "Requirements by Category":
                generate_requirements_by_category()
            elif report_type == "Overdue Items":
                generate_overdue_items()
            else:
                st.info(f"{report_type} report would be generated here")

def generate_compliance_summary():
    """Generate compliance summary report"""
    st.markdown("### 📋 Compliance Summary Report")

    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Status breakdown
        cursor.execute("""
            SELECT status, COUNT(*) as count
            FROM compliance_requirements
            GROUP BY status
        """)
        status_data = [dict(row) for row in cursor.fetchall()]

        # Category breakdown
        cursor.execute("""
            SELECT category, COUNT(*) as count,
                   SUM(CASE WHEN status = 'Compliant' THEN 1 ELSE 0 END) as compliant
            FROM compliance_requirements
            GROUP BY category
        """)
        category_data = [dict(row) for row in cursor.fetchall()]

    if status_data:
        st.markdown("#### Status Breakdown")
        df = pd.DataFrame(status_data)
        st.dataframe(df, use_container_width=True, hide_index=True)

    if category_data:
        st.markdown("#### Category Breakdown")
        df = pd.DataFrame(category_data)
        df['Compliance Rate'] = (df['compliant'] / df['count'] * 100).round(1).astype(str) + '%'
        st.dataframe(df, use_container_width=True, hide_index=True)

def generate_audit_history():
    """Generate audit history report"""
    st.markdown("### ✅ Audit History Report")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT audit_name, audit_type, audit_date, status, result
            FROM compliance_audits
            ORDER BY audit_date DESC
        """)
        audits = [dict(row) for row in cursor.fetchall()]

    if audits:
        df = pd.DataFrame(audits)
        df.columns = ['Audit', 'Type', 'Date', 'Status', 'Result']
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No audit history available")

def generate_requirements_by_category():
    """Generate requirements by category report"""
    st.markdown("### 📊 Requirements by Category")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT category, COUNT(*) as total,
                   SUM(CASE WHEN status = 'Compliant' THEN 1 ELSE 0 END) as compliant,
                   SUM(CASE WHEN status = 'Overdue' OR next_review_date < CURRENT_DATE THEN 1 ELSE 0 END) as overdue
            FROM compliance_requirements
            GROUP BY category
            ORDER BY total DESC
        """)
        data = [dict(row) for row in cursor.fetchall()]

    if data:
        df = pd.DataFrame(data)
        df.columns = ['Category', 'Total', 'Compliant', 'Overdue']
        st.dataframe(df, use_container_width=True, hide_index=True)

def generate_overdue_items():
    """Generate overdue items report"""
    st.markdown("### ⚠️ Overdue Compliance Items")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT requirement_name, category, next_review_date,
                   EXTRACT(DAY FROM (CURRENT_DATE - next_review_date)) as days_overdue
            FROM compliance_requirements
            WHERE next_review_date < CURRENT_DATE
            AND status != 'Compliant'
            ORDER BY next_review_date ASC
        """)
        overdue = [dict(row) for row in cursor.fetchall()]

    if overdue:
        df = pd.DataFrame(overdue)
        df['days_overdue'] = df['days_overdue'].round(0).astype(int)
        df.columns = ['Requirement', 'Category', 'Review Date', 'Days Overdue']
        st.dataframe(df, use_container_width=True, hide_index=True)
        st.warning(f"⚠️ {len(overdue)} item(s) overdue for review")
    else:
        st.success("✅ No overdue items!")

def show_compliance_issues():
    """Show compliance issues and violations"""
    st.markdown("### ⚠️ Compliance Issues")

    # Report new issue
    with st.expander("➕ Report Compliance Issue"):
        with st.form("report_issue"):
            issue_title = st.text_input("Issue Title *")
            severity = st.selectbox("Severity *", ["Low", "Medium", "High", "Critical"])

            col1, col2 = st.columns(2)
            with col1:
                category = st.selectbox("Category", [
                    "Policy Violation", "Regulatory", "Safety", "Data Privacy",
                    "Discrimination", "Harassment", "Other"
                ])
            with col2:
                discovered_date = st.date_input("Discovered Date *")

            description = st.text_area("Description *", placeholder="Describe the issue in detail...")
            corrective_action = st.text_area("Corrective Action Plan", placeholder="What actions will be taken...")

            if st.form_submit_button("⚠️ Report Issue"):
                if issue_title and description:
                    report_compliance_issue(issue_title, severity, category,
                                          discovered_date, description, corrective_action)
                    st.rerun()

    # Display issues
    st.markdown("---")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM compliance_issues
            ORDER BY
                CASE severity
                    WHEN 'Critical' THEN 1
                    WHEN 'High' THEN 2
                    WHEN 'Medium' THEN 3
                    WHEN 'Low' THEN 4
                END,
                discovered_date DESC
        """)
        issues = [dict(row) for row in cursor.fetchall()]

    if issues:
        for issue in issues:
            severity_colors = {
                'Critical': 'rgba(241, 100, 100, 0.2)',
                'High': 'rgba(240, 180, 41, 0.2)',
                'Medium': 'rgba(91, 156, 246, 0.15)',
                'Low': 'rgba(125, 150, 190, 0.1)'
            }
            color = severity_colors.get(issue['severity'], 'rgba(125, 150, 190, 0.1)')

            icon = {'Critical': '🔴', 'High': '🟠', 'Medium': '🟡', 'Low': '⚪'}.get(issue['severity'], '⚠️')

            with st.expander(f"{icon} {issue['issue_title']} - {issue['severity']}"):
                st.markdown(f"""
                **Severity:** {issue['severity']}
                **Category:** {issue['category']}
                **Discovered:** {issue['discovered_date']}
                **Status:** {issue['status']}
                """)

                st.warning(f"**Description:** {issue['description']}")

                if issue.get('corrective_action'):
                    st.info(f"**Corrective Action:** {issue['corrective_action']}")

                if issue.get('resolution_notes'):
                    st.success(f"**Resolution:** {issue['resolution_notes']}")

                # Actions
                if issue['status'] != 'Resolved':
                    with st.form(f"resolve_{issue['id']}"):
                        resolution = st.text_area("Resolution Notes")
                        if st.form_submit_button("✅ Resolve Issue"):
                            resolve_issue(issue['id'], resolution)
                            st.rerun()
    else:
        st.success("✅ No compliance issues reported!")

def add_compliance_requirement(name, category, description, frequency, next_review, responsible):
    """Add new compliance requirement"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO compliance_requirements (
                    requirement_name, category, description,
                    review_frequency, next_review_date,
                    responsible_person, status
                ) VALUES (%s, %s, %s, %s, %s, %s, 'Not Started')
            """, (name, category, description, frequency,
                 next_review.isoformat(), responsible))

            req_id = cursor.lastrowid

            conn.commit()
            log_audit(f"Added compliance requirement: {name}", "compliance", req_id)
            st.success(f"✅ Requirement added! ID: COMP-{req_id}")

    except Exception as e:
        st.error(f"❌ Error: {str(e)}")

def update_requirement_status(req_id, status):
    """Update requirement status"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE compliance_requirements SET status = %s, updated_at = %s
                WHERE id = %s
            """, (status, datetime.now().isoformat(), req_id))
            conn.commit()
            log_audit(f"Updated requirement {req_id} to {status}", "compliance", req_id)
            st.success(f"✅ Status updated to {status}!")

    except Exception as e:
        st.error(f"❌ Error: {str(e)}")

def delete_requirement(req_id):
    """Delete requirement"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM compliance_requirements WHERE id = %s", (req_id,))
            conn.commit()
            log_audit(f"Deleted requirement {req_id}", "compliance", req_id)
            st.success("✅ Requirement deleted!")

    except Exception as e:
        st.error(f"❌ Error: {str(e)}")

def schedule_audit(name, audit_type, audit_date, auditor, scope, notes):
    """Schedule compliance audit"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO compliance_audits (
                    audit_name, audit_type, audit_date, auditor,
                    scope, notes, status
                ) VALUES (%s, %s, %s, %s, %s, %s, 'Scheduled')
            """, (name, audit_type, audit_date.isoformat(), auditor, scope, notes))

            audit_id = cursor.lastrowid

            conn.commit()
            log_audit(f"Scheduled audit: {name}", "compliance", audit_id)
            st.success(f"✅ Audit scheduled! ID: AUD-{audit_id}")

    except Exception as e:
        st.error(f"❌ Error: {str(e)}")

def update_audit_status(audit_id, status):
    """Update audit status"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE compliance_audits SET status = %s WHERE id = %s", (status, audit_id))
            conn.commit()
            log_audit(f"Updated audit {audit_id} to {status}", "compliance", audit_id)
            st.success(f"✅ Audit {status.lower()}!")

    except Exception as e:
        st.error(f"❌ Error: {str(e)}")

def complete_audit(audit_id, findings, result):
    """Complete compliance audit"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE compliance_audits SET
                    status = 'Completed',
                    findings = %s,
                    result = %s,
                    completed_date = %s
                WHERE id = %s
            """, (findings, result, datetime.now().isoformat(), audit_id))
            conn.commit()
            log_audit(f"Completed audit {audit_id} with result: {result}", "compliance", audit_id)
            st.success(f"✅ Audit completed with result: {result}!")

    except Exception as e:
        st.error(f"❌ Error: {str(e)}")

def report_compliance_issue(title, severity, category, discovered_date, description, corrective_action):
    """Report compliance issue"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO compliance_issues (
                    issue_title, severity, category, discovered_date,
                    description, corrective_action, status
                ) VALUES (%s, %s, %s, %s, %s, %s, 'Open')
            """, (title, severity, category, discovered_date.isoformat(),
                 description, corrective_action))

            issue_id = cursor.lastrowid

            conn.commit()
            log_audit(f"Reported compliance issue: {title}", "compliance", issue_id)
            st.warning(f"⚠️ Issue reported! ID: ISSUE-{issue_id}")

    except Exception as e:
        st.error(f"❌ Error: {str(e)}")

def resolve_issue(issue_id, resolution):
    """Resolve compliance issue"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE compliance_issues SET
                    status = 'Resolved',
                    resolution_notes = %s,
                    resolved_date = %s
                WHERE id = %s
            """, (resolution, datetime.now().isoformat(), issue_id))
            conn.commit()
            log_audit(f"Resolved issue {issue_id}", "compliance", issue_id)
            st.success("✅ Issue resolved!")

    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
