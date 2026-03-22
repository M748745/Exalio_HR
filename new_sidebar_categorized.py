# NEW CATEGORIZED SIDEBAR CODE
# Replace lines 608-828 in app.py with this code

            if st.button("⏰ Timesheets", key="timesheets", use_container_width=True):
                st.session_state.current_page = 'timesheets'
                st.rerun()

            if is_hr_admin() or is_manager():
                if st.button("📅 Shift Scheduling", key="shifts", use_container_width=True):
                    st.session_state.current_page = 'shifts'
                    st.rerun()

            if st.button("🔄 Shift Swap", key="shift_swap", use_container_width=True):
                st.session_state.current_page = 'shift_swap'
                st.rerun()

        # 3. PERFORMANCE & DEVELOPMENT
        with st.expander("📈 **Performance & Development**", expanded=False):
            if st.button("🏅 Performance & Grades", key="performance", use_container_width=True):
                st.session_state.current_page = 'performance'
                st.rerun()

            if st.button("📋 Appraisals", key="appraisals", use_container_width=True):
                st.session_state.current_page = 'appraisals'
                st.rerun()

            if is_hr_admin():
                if st.button("⚖️ Appraisal Calibration", key="calibration", use_container_width=True):
                    st.session_state.current_page = 'calibration'
                    st.rerun()

            if st.button("🎯 Goals & OKRs", key="goals_okr", use_container_width=True):
                st.session_state.current_page = 'goal_okr'
                st.rerun()

            if st.button("📈 PIP Management", key="pip", use_container_width=True):
                st.session_state.current_page = 'pip'
                st.rerun()

            if st.button("🎓 Training & Development", key="training", use_container_width=True):
                st.session_state.current_page = 'training'
                st.rerun()

            if st.button("🎓 Certificates", key="certificates", use_container_width=True):
                st.session_state.current_page = 'certificates'
                st.rerun()

            if st.button("🎓 Certificate Tracking", key="cert_tracking", use_container_width=True):
                st.session_state.current_page = 'certificate_tracking'
                st.rerun()

        # 4. COMPENSATION & BENEFITS
        with st.expander("💰 **Compensation & Benefits**", expanded=False):
            if is_hr_admin():
                if st.button("💵 Financial Records", key="financial", use_container_width=True):
                    st.session_state.current_page = 'financial'
                    st.rerun()

            if is_hr_admin() or is_manager():
                if st.button("💎 Bonus Calculator", key="bonus", use_container_width=True):
                    st.session_state.current_page = 'bonus'
                    st.rerun()

            if st.button("🏥 Medical Insurance", key="insurance", use_container_width=True):
                st.session_state.current_page = 'insurance'
                st.rerun()

            if st.button("💰 Expense Claims", key="expenses", use_container_width=True):
                st.session_state.current_page = 'expenses'
                st.rerun()

            if is_hr_admin():
                if st.button("📄 Contracts", key="contracts", use_container_width=True):
                    st.session_state.current_page = 'contracts'
                    st.rerun()

            if st.button("📄 Contract Renewal", key="contract_renewal", use_container_width=True):
                st.session_state.current_page = 'contract_renewal'
                st.rerun()

        # 5. RECRUITMENT & ONBOARDING
        with st.expander("💼 **Recruitment & Onboarding**", expanded=False):
            if is_hr_admin() or is_manager():
                if st.button("💼 Recruitment", key="recruitment", use_container_width=True):
                    st.session_state.current_page = 'recruitment'
                    st.rerun()

            if st.button("📋 Onboarding Tasks", key="onboarding", use_container_width=True):
                st.session_state.current_page = 'onboarding'
                st.rerun()

            if st.button("🔄 Succession Planning", key="succession", use_container_width=True):
                st.session_state.current_page = 'succession'
                st.rerun()

        # 6. ASSETS & PROCUREMENT
        with st.expander("💻 **Assets & Procurement**", expanded=False):
            if is_hr_admin() or is_manager():
                if st.button("💻 Asset Management", key="assets", use_container_width=True):
                    st.session_state.current_page = 'assets'
                    st.rerun()

            if st.button("💼 Asset Procurement", key="asset_procurement", use_container_width=True):
                st.session_state.current_page = 'asset_procurement'
                st.rerun()

            if st.button("💰 Budget Management", key="budget", use_container_width=True):
                st.session_state.current_page = 'budget_management'
                st.rerun()

        # 7. DOCUMENTS & COMPLIANCE
        with st.expander("📁 **Documents & Compliance**", expanded=False):
            if st.button("📁 Documents", key="documents", use_container_width=True):
                st.session_state.current_page = 'documents'
                st.rerun()

            if st.button("📋 Document Approval", key="doc_approval", use_container_width=True):
                st.session_state.current_page = 'document_approval'
                st.rerun()

            if st.button("📋 Compliance Tracking", key="compliance", use_container_width=True):
                st.session_state.current_page = 'compliance'
                st.rerun()

        # 8. TEAM STRUCTURE
        with st.expander("🏢 **Team Structure**", expanded=False):
            if st.button("🏢 Org Chart", key="org_chart", use_container_width=True):
                st.session_state.current_page = 'org_chart'
                st.rerun()

            if is_hr_admin():
                if st.button("🏢 Teams & Positions", key="teams", use_container_width=True):
                    st.session_state.current_page = 'teams_positions'
                    st.rerun()

                if st.button("🎯 Skill Matrix", key="skills", use_container_width=True):
                    st.session_state.current_page = 'skill_matrix'
                    st.rerun()

        # 9. WORKFLOW & APPROVALS
        with st.expander("🔄 **Workflow & Approvals**", expanded=False):
            if st.button("🚀 Promotions", key="promotions", use_container_width=True):
                st.session_state.current_page = 'promotions'
                st.rerun()

            if is_hr_admin() or is_manager():
                if st.button("🔄 Workflow Builder", key="workflow_builder", use_container_width=True):
                    st.session_state.current_page = 'workflow_builder'
                    st.rerun()

            if is_hr_admin():
                if st.button("🌳 Function Organization", key="workflow_mgmt", use_container_width=True):
                    st.session_state.current_page = 'workflow_management'
                    st.rerun()

        # 10. COMMUNICATION
        with st.expander("📢 **Communication**", expanded=False):
            if st.button("📢 Announcements", key="announcements", use_container_width=True):
                st.session_state.current_page = 'announcements'
                st.rerun()

            if st.button("📊 Surveys", key="surveys", use_container_width=True):
                st.session_state.current_page = 'surveys'
                st.rerun()

            if st.button("📅 Calendar", key="calendar", use_container_width=True):
                st.session_state.current_page = 'calendar'
                st.rerun()

        # 11. REPORTS & ANALYTICS
        if is_hr_admin() or is_manager():
            with st.expander("📊 **Reports & Analytics**", expanded=False):
                if st.button("📊 Reports", key="reports", use_container_width=True):
                    st.session_state.current_page = 'reports'
                    st.rerun()

        # 12. SETTINGS & ADMIN
        if is_hr_admin():
            with st.expander("⚙️ **Settings & Admin**", expanded=False):
                if st.button("⚙️ Admin Panel", key="admin", use_container_width=True):
                    st.session_state.current_page = 'admin'
                    st.rerun()

                if st.button("📧 Email Settings", key="email", use_container_width=True):
                    st.session_state.current_page = 'email'
                    st.rerun()

        # Mobile View - Always available
        st.markdown("---")
        if st.button("📱 Mobile View", key="mobile", use_container_width=True):
            st.session_state.current_page = 'mobile'
            st.rerun()
