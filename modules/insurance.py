"""
Medical Insurance Module
Track health coverage, policies, and renewals
"""

import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
from database import get_db_connection
from auth import get_current_user, is_hr_admin, get_accessible_employees, create_notification, log_audit

def show_insurance_management():
    """Main insurance management interface"""
    user = get_current_user()

    st.markdown("## 🏥 Medical Insurance")
    st.markdown("Employee health coverage, policies, and claims tracking")
    st.markdown("---")

    if is_hr_admin():
        tabs = st.tabs(["📊 Overview", "📋 All Policies", "➕ Add Policy"])
        with tabs[0]:
            show_insurance_overview()
        with tabs[1]:
            show_all_policies()
        with tabs[2]:
            show_add_policy()
    else:
        tabs = st.tabs(["📄 My Insurance", "📊 Coverage Details"])
        with tabs[0]:
            show_my_insurance()
        with tabs[1]:
            show_coverage_details()

def show_insurance_overview():
    """Dashboard overview for HR"""
    st.markdown("### 📊 Insurance Overview")

    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Statistics
        cursor.execute("SELECT COUNT(DISTINCT emp_id) as cnt FROM insurance WHERE status = 'Active'")
        covered_employees = cursor.fetchone()['cnt']

        cursor.execute("SELECT SUM(premium_monthly) as total FROM insurance WHERE status = 'Active'")
        result = cursor.fetchone()
        monthly_premium = result['total'] if result['total'] else 0

        cursor.execute("""
            SELECT COUNT(*) as cnt FROM insurance
            WHERE status = 'Active' AND renewal_date <= %s
        """, ((date.today() + timedelta(days=30)).isoformat(),))
        expiring_soon = cursor.fetchone()['cnt']

    # Display stats
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(f"""
            <div style="background: linear-gradient(135deg, #0e1117, #1c2535);
                        padding: 20px; border-radius: 12px; border: 1px solid #22304a; text-align: center;">
                <div style="font-size: 32px; margin-bottom: 10px;">👥</div>
                <div style="font-size: 36px; font-weight: bold; color: #2dd4aa; margin: 10px 0;">
                    {covered_employees}
                </div>
                <div style="font-size: 12px; color: #7d96be; text-transform: uppercase;">Covered Employees</div>
            </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
            <div style="background: linear-gradient(135deg, #0e1117, #1c2535);
                        padding: 20px; border-radius: 12px; border: 1px solid #22304a; text-align: center;">
                <div style="font-size: 32px; margin-bottom: 10px;">💰</div>
                <div style="font-size: 36px; font-weight: bold; color: #c9963a; margin: 10px 0;">
                    ${monthly_premium:,.0f}
                </div>
                <div style="font-size: 12px; color: #7d96be; text-transform: uppercase;">Monthly Premium</div>
            </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
            <div style="background: linear-gradient(135deg, #0e1117, #1c2535);
                        padding: 20px; border-radius: 12px; border: 1px solid #22304a; text-align: center;">
                <div style="font-size: 32px; margin-bottom: 10px;">⚠️</div>
                <div style="font-size: 36px; font-weight: bold; color: #f16464; margin: 10px 0;">
                    {expiring_soon}
                </div>
                <div style="font-size: 12px; color: #7d96be; text-transform: uppercase;">Expiring (30d)</div>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # Provider breakdown
    st.markdown("### 📊 Coverage by Provider")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT provider, COUNT(*) as count, SUM(premium_monthly) as total_premium
            FROM insurance
            WHERE status = 'Active'
            GROUP BY provider
            ORDER BY count DESC
        """)
        providers = [dict(row) for row in cursor.fetchall()]

    if providers:
        for prov in providers:
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                st.markdown(f"**{prov['provider']}**")
            with col2:
                st.markdown(f"{prov['count']} employees")
            with col3:
                st.markdown(f"${prov['total_premium']:,.0f}/mo")
    else:
        st.info("No active policies")

def show_all_policies():
    """Display all insurance policies"""
    st.markdown("### 📋 All Insurance Policies")

    # Filters
    col1, col2, col3 = st.columns(3)
    with col1:
        provider_filter = st.selectbox("Provider", ["All"] + get_providers())
    with col2:
        status_filter = st.selectbox("Status", ["All", "Active", "Expired", "Cancelled"])
    with col3:
        search = st.text_input("🔍 Search employee")

    with get_db_connection() as conn:
        cursor = conn.cursor()

        query = """
            SELECT i.*, e.first_name, e.last_name, e.employee_id, e.department
            FROM insurance i
            JOIN employees e ON i.emp_id = e.id
            WHERE 1=1
        """
        params = []

        if provider_filter != "All":
            query += " AND i.provider = %s"
            params.append(provider_filter)

        if status_filter != "All":
            query += " AND i.status = %s"
            params.append(status_filter)

        if search:
            query += " AND (e.first_name LIKE %s OR e.last_name LIKE %s OR e.employee_id LIKE %s)"
            params.extend([f"%{search}%", f"%{search}%", f"%{search}%"])

        query += " ORDER BY i.renewal_date ASC"

        cursor.execute(query, params)
        policies = [dict(row) for row in cursor.fetchall()]

    if policies:
        df = pd.DataFrame(policies)
        display_cols = ['employee_id', 'first_name', 'last_name', 'provider', 'plan_name',
                       'coverage_type', 'premium_monthly', 'dependants', 'renewal_date', 'status']
        df_display = df[display_cols]
        df_display.columns = ['Emp ID', 'First Name', 'Last Name', 'Provider', 'Plan',
                             'Coverage', 'Premium/Mo', 'Dependants', 'Renewal', 'Status']

        st.dataframe(df_display, use_container_width=True, hide_index=True)
    else:
        st.info("No policies found")

def show_add_policy():
    """Form to add insurance policy"""
    st.markdown("### ➕ Add Insurance Policy")

    employees = get_accessible_employees()

    with st.form("insurance_form"):
        col1, col2 = st.columns(2)

        with col1:
            selected_emp_id = st.selectbox(
                "Select Employee *",
                options=[e['id'] for e in employees],
                format_func=lambda x: f"{next(e['first_name'] + ' ' + e['last_name'] for e in employees if e['id'] == x)} ({next(e['employee_id'] for e in employees if e['id'] == x)})"
            )

            provider = st.selectbox("Provider *", get_providers())
            plan_name = st.text_input("Plan Name *", placeholder="e.g., Gold Plan, Family Plan")
            coverage_type = st.selectbox("Coverage Type", ["Individual", "Individual + Spouse", "Family", "Dependants"])

        with col2:
            premium_monthly = st.number_input("Monthly Premium ($) *", min_value=0.0, value=200.0, step=10.0)
            network = st.selectbox("Network", ["PPO", "HMO", "EPO", "POS"])
            dependants = st.number_input("Number of Dependants", min_value=0, max_value=10, value=0)
            status = st.selectbox("Status", ["Active", "Pending", "Expired", "Cancelled"])

        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Start Date *", value=date.today())
        with col2:
            renewal_date = st.date_input("Renewal Date *", value=date.today() + timedelta(days=365))

        submitted = st.form_submit_button("💾 Save Policy", use_container_width=True)

        if submitted:
            if not all([selected_emp_id, provider, plan_name, premium_monthly, start_date, renewal_date]):
                st.error("❌ Please fill all required fields")
            else:
                try:
                    with get_db_connection() as conn:
                        cursor = conn.cursor()

                        cursor.execute("""
                            INSERT INTO insurance (
                                emp_id, provider, plan_name, coverage_type, premium_monthly,
                                network, dependants, start_date, renewal_date, status
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """, (selected_emp_id, provider, plan_name, coverage_type, premium_monthly,
                             network, dependants, start_date.isoformat(), renewal_date.isoformat(), status))

                        policy_id = cursor.lastrowid

                        # Notify employee
                        create_notification(
                            selected_emp_id,
                            "Insurance Policy Added",
                            f"A new {plan_name} insurance policy from {provider} has been added to your account.",
                            'success'
                        )

                        conn.commit()
                        log_audit(f"Created insurance policy: {provider} - {plan_name}", "insurance", policy_id)

                        st.success("✅ Insurance policy created successfully!")
                        st.balloons()
                        st.rerun()

                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")

def show_my_insurance():
    """Show employee's own insurance"""
    user = get_current_user()

    st.markdown("### 📄 My Insurance Coverage")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM insurance
            WHERE emp_id = %s
            ORDER BY start_date DESC
        """, (user['employee_id'],))
        policies = [dict(row) for row in cursor.fetchall()]

    if policies:
        for policy in policies:
            status_color = "rgba(45, 212, 170, 0.1)" if policy['status'] == 'Active' else "rgba(241, 100, 100, 0.1)"

            st.markdown(f"""
                <div style="background: {status_color}; padding: 20px; border-radius: 12px; margin-bottom: 15px; border: 1px solid #22304a;">
                    <h3 style="color: #c9963a; margin: 0 0 15px 0;">{policy['provider']} - {policy['plan_name']}</h3>
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px;">
                        <div>
                            <strong>Coverage Type:</strong> {policy['coverage_type']}<br>
                            <strong>Network:</strong> {policy['network']}<br>
                            <strong>Dependants:</strong> {policy['dependants']}
                        </div>
                        <div>
                            <strong>Premium:</strong> ${policy['premium_monthly']:.2f}/month<br>
                            <strong>Start Date:</strong> {policy['start_date']}<br>
                            <strong>Renewal:</strong> {policy['renewal_date']}
                        </div>
                    </div>
                    <div style="margin-top: 15px; padding-top: 15px; border-top: 1px solid rgba(255,255,255,0.1);">
                        <span style="background: rgba(45, 212, 170, 0.2); padding: 4px 12px; border-radius: 20px; font-size: 11px;">
                            {policy['status']}
                        </span>
                    </div>
                </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No insurance coverage found. Please contact HR.")

def show_coverage_details():
    """Show detailed coverage information"""
    st.markdown("### 📊 Coverage Details")

    st.info("💡 Contact HR for detailed coverage information and claims processing")

    st.markdown("""
    ### 📞 Insurance Support

    For questions about your insurance coverage:
    - 📧 Email: hr@exalio.com
    - 📞 Phone: +1-555-HR-HELP
    - 🕒 Hours: Mon-Fri 9AM-5PM
    """)

def get_providers():
    """Get list of insurance providers"""
    return [
        "Blue Cross Blue Shield",
        "UnitedHealthcare",
        "Aetna",
        "Cigna",
        "Humana",
        "Kaiser Permanente",
        "Anthem",
        "Other"
    ]
