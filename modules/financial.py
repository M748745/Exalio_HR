"""
Financial Records & Payroll Module
Manage salaries, allowances, deductions, and payroll
"""

import streamlit as st
import pandas as pd
from datetime import datetime, date
from database import get_db_connection
from auth import get_current_user, is_hr_admin, create_notification, log_audit

def show_financial_management():
    """Main financial management interface"""
    user = get_current_user()

    st.markdown("## 💰 Financial Records & Payroll")
    st.markdown("Manage salaries, allowances, deductions, and payroll")
    st.markdown("---")

    if not is_hr_admin():
        tabs = st.tabs(["💵 My Salary", "📄 Payslips"])
        with tabs[0]:
            show_my_salary()
        with tabs[1]:
            show_my_payslips()
    else:
        tabs = st.tabs(["📊 Overview", "📋 All Records", "➕ Add Record", "💳 Generate Payslips"])
        with tabs[0]:
            show_financial_overview()
        with tabs[1]:
            show_all_financial_records()
        with tabs[2]:
            show_add_financial_record()
        with tabs[3]:
            show_generate_payslips()

def show_financial_overview():
    """Financial statistics overview"""
    st.markdown("### 📊 Financial Overview")

    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Monthly payroll
        cursor.execute("""
            SELECT SUM(net_pay) as total FROM financial_records
            WHERE period LIKE %s
        """, (f"{datetime.now().year}-%",))
        monthly_payroll = cursor.fetchone()['total'] or 0

        # Total bonuses
        cursor.execute("""
            SELECT SUM(amount) as total FROM bonuses
            WHERE status = 'Paid'
        """)
        total_bonuses = cursor.fetchone()['total'] or 0

        # Average salary
        cursor.execute("""
            SELECT AVG(base_salary) as avg FROM financial_records
        """)
        avg_salary = cursor.fetchone()['avg'] or 0

        # Active employees
        cursor.execute("""
            SELECT COUNT(DISTINCT emp_id) as cnt FROM financial_records
        """)
        active_employees = cursor.fetchone()['cnt']

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(f"""
            <div style="background: linear-gradient(135deg, #0e1117, #1c2535);
                        padding: 20px; border-radius: 12px; border: 1px solid #22304a; text-align: center;">
                <div style="font-size: 32px; margin-bottom: 10px;">💵</div>
                <div style="font-size: 32px; font-weight: bold; color: #c9963a;">
                    ${monthly_payroll:,.0f}
                </div>
                <div style="font-size: 12px; color: #7d96be; text-transform: uppercase;">Annual Payroll</div>
            </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
            <div style="background: linear-gradient(135deg, #0e1117, #1c2535);
                        padding: 20px; border-radius: 12px; border: 1px solid #22304a; text-align: center;">
                <div style="font-size: 32px; margin-bottom: 10px;">💎</div>
                <div style="font-size: 32px; font-weight: bold; color: #c9963a;">
                    ${total_bonuses:,.0f}
                </div>
                <div style="font-size: 12px; color: #7d96be; text-transform: uppercase;">Total Bonuses</div>
            </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
            <div style="background: linear-gradient(135deg, #0e1117, #1c2535);
                        padding: 20px; border-radius: 12px; border: 1px solid #22304a; text-align: center;">
                <div style="font-size: 32px; margin-bottom: 10px;">📊</div>
                <div style="font-size: 32px; font-weight: bold; color: #5b9cf6;">
                    ${avg_salary:,.0f}
                </div>
                <div style="font-size: 12px; color: #7d96be; text-transform: uppercase;">Average Salary</div>
            </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown(f"""
            <div style="background: linear-gradient(135deg, #0e1117, #1c2535);
                        padding: 20px; border-radius: 12px; border: 1px solid #22304a; text-align: center;">
                <div style="font-size: 32px; margin-bottom: 10px;">👥</div>
                <div style="font-size: 32px; font-weight: bold; color: #2dd4aa;">
                    {active_employees}
                </div>
                <div style="font-size: 12px; color: #7d96be; text-transform: uppercase;">On Payroll</div>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # Department breakdown
    st.markdown("### 🏢 Payroll by Department")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT e.department, SUM(f.net_pay) as total, COUNT(DISTINCT f.emp_id) as count
            FROM financial_records f
            JOIN employees e ON f.emp_id = e.id
            GROUP BY e.department
            ORDER BY total DESC
        """)
        dept_payroll = [dict(row) for row in cursor.fetchall()]

    if dept_payroll:
        for dept in dept_payroll:
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                st.markdown(f"**{dept['department']}**")
            with col2:
                st.markdown(f"{dept['count']} employees")
            with col3:
                st.markdown(f"${dept['total']:,.2f}")

def show_all_financial_records():
    """Display all financial records"""
    st.markdown("### 📋 All Financial Records")

    # Filters
    col1, col2, col3 = st.columns(3)
    with col1:
        dept_filter = st.selectbox("Department", ["All"] + get_departments())
    with col2:
        period_filter = st.text_input("Period (YYYY-MM)", placeholder="2024-01")
    with col3:
        search = st.text_input("🔍 Search employee")

    with get_db_connection() as conn:
        cursor = conn.cursor()

        query = """
            SELECT f.*, e.first_name, e.last_name, e.employee_id, e.department
            FROM financial_records f
            JOIN employees e ON f.emp_id = e.id
            WHERE 1=1
        """
        params = []

        if dept_filter != "All":
            query += " AND e.department = %s"
            params.append(dept_filter)

        if period_filter:
            query += " AND f.period LIKE %s"
            params.append(f"%{period_filter}%")

        if search:
            query += " AND (e.first_name LIKE %s OR e.last_name LIKE %s OR e.employee_id LIKE %s)"
            params.extend([f"%{search}%", f"%{search}%", f"%{search}%"])

        query += " ORDER BY f.created_at DESC LIMIT 100"

        cursor.execute(query, params)
        records = [dict(row) for row in cursor.fetchall()]

    if records:
        df = pd.DataFrame(records)
        display_cols = ['employee_id', 'first_name', 'last_name', 'base_salary',
                       'allowances', 'bonus', 'deductions', 'net_pay', 'period']
        df_display = df[display_cols]
        df_display.columns = ['Emp ID', 'First Name', 'Last Name', 'Base',
                             'Allowances', 'Bonus', 'Deductions', 'Net Pay', 'Period']

        st.dataframe(df_display, use_container_width=True, hide_index=True)

        # Export button
        if st.button("📥 Export to CSV", use_container_width=True):
            csv = df_display.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name=f"payroll_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
    else:
        st.info("No financial records found")

def show_add_financial_record():
    """Form to add financial record"""
    st.markdown("### ➕ Add Financial Record")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, first_name, last_name, employee_id FROM employees WHERE status = 'Active'")
        employees = [dict(row) for row in cursor.fetchall()]

    with st.form("financial_form"):
        selected_emp_id = st.selectbox(
            "Employee *",
            options=[e['id'] for e in employees],
            format_func=lambda x: f"{next(e['first_name'] + ' ' + e['last_name'] for e in employees if e['id'] == x)} ({next(e['employee_id'] for e in employees if e['id'] == x)})"
        )

        col1, col2 = st.columns(2)

        with col1:
            base_salary = st.number_input("Base Salary ($) *", min_value=0.0, value=5000.0, step=100.0)
            allowances = st.number_input("Allowances ($)", min_value=0.0, value=500.0, step=50.0)
            bonus = st.number_input("Bonus ($)", min_value=0.0, value=0.0, step=100.0)

        with col2:
            deductions = st.number_input("Deductions ($)", min_value=0.0, value=200.0, step=50.0)
            currency = st.selectbox("Currency", ["USD", "EUR", "GBP", "AED"])
            period = st.text_input("Period *", placeholder="YYYY-MM", value=datetime.now().strftime("%Y-%m"))

        net_pay = base_salary + allowances + bonus - deductions
        st.metric("Net Pay", f"${net_pay:,.2f}")

        submitted = st.form_submit_button("💾 Save Record", use_container_width=True)

        if submitted:
            if not all([selected_emp_id, base_salary > 0, period]):
                st.error("❌ Please fill all required fields")
            else:
                try:
                    with get_db_connection() as conn:
                        cursor = conn.cursor()

                        cursor.execute("""
                            INSERT INTO financial_records (
                                emp_id, base_salary, allowances, bonus, deductions,
                                net_pay, currency, period
                            ) VALUES (%s, ?, ?, ?, ?, ?, ?, ?)
                        """, (selected_emp_id, base_salary, allowances, bonus, deductions,
                             net_pay, currency, period))

                        record_id = cursor.lastrowid
                        conn.commit()
                        log_audit(f"Created financial record for period: {period}", "financial_records", record_id)

                        st.success(f"✅ Financial record created successfully!")
                        st.balloons()
                        st.rerun()

                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")

def show_generate_payslips():
    """Generate payslips for a period"""
    st.markdown("### 💳 Generate Payslips")

    period = st.text_input("Period (YYYY-MM) *", value=datetime.now().strftime("%Y-%m"))

    if st.button("🔍 Load Financial Data for Period", use_container_width=True):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT f.*, e.first_name, e.last_name, e.employee_id
                FROM financial_records f
                JOIN employees e ON f.emp_id = e.id
                WHERE f.period = %s
            """, (period,))
            records = [dict(row) for row in cursor.fetchall()]

        if records:
            st.success(f"✅ Found {len(records)} financial records for {period}")

            if st.button("💳 Generate Payslips for All", use_container_width=True):
                generated_count = 0
                with get_db_connection() as conn:
                    cursor = conn.cursor()
                    user = get_current_user()

                    for record in records:
                        # Check if payslip already exists
                        cursor.execute("""
                            SELECT id FROM payslips WHERE emp_id = %s AND period = %s
                        """, (record['emp_id'], period))

                        if not cursor.fetchone():
                            cursor.execute("""
                                INSERT INTO payslips (
                                    emp_id, period, base_salary, allowances, bonus,
                                    deductions, net_pay, generated_by
                                ) VALUES (%s, ?, ?, ?, ?, ?, ?, ?)
                            """, (record['emp_id'], period, record['base_salary'],
                                 record['allowances'], record['bonus'], record['deductions'],
                                 record['net_pay'], user['employee_id']))

                            # Notify employee
                            create_notification(
                                record['emp_id'],
                                "Payslip Available",
                                f"Your payslip for {period} is now available.",
                                'success'
                            )
                            generated_count += 1

                    conn.commit()

                st.success(f"✅ Generated {generated_count} payslips!")
                st.balloons()
        else:
            st.warning(f"⚠️ No financial records found for {period}")

def show_my_salary():
    """Employee view of own salary"""
    user = get_current_user()

    st.markdown("### 💵 My Salary Information")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM financial_records
            WHERE emp_id = %s
            ORDER BY created_at DESC
            LIMIT 1
        """, (user['employee_id'],))
        salary_record = cursor.fetchone()

    if salary_record:
        salary = dict(salary_record)

        col1, col2 = st.columns([2, 1])

        with col1:
            st.markdown(f"""
                <div style="background: linear-gradient(135deg, rgba(201, 150, 58, 0.1), rgba(58, 123, 213, 0.06));
                            border: 1px solid rgba(201, 150, 58, 0.25); border-radius: 12px;
                            padding: 25px; margin-bottom: 20px;">
                    <h3 style="color: #c9963a; margin: 0 0 20px 0;">💰 Salary Breakdown</h3>
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px;">
                        <div>
                            <strong>Base Salary:</strong><br>
                            <span style="font-size: 24px; color: #dde5f5;">${salary['base_salary']:,.2f}</span>
                        </div>
                        <div>
                            <strong>Allowances:</strong><br>
                            <span style="font-size: 24px; color: #2dd4aa;">${salary['allowances']:,.2f}</span>
                        </div>
                        <div>
                            <strong>Bonus:</strong><br>
                            <span style="font-size: 24px; color: #c9963a;">${salary['bonus']:,.2f}</span>
                        </div>
                        <div>
                            <strong>Deductions:</strong><br>
                            <span style="font-size: 24px; color: #f16464;">-${salary['deductions']:,.2f}</span>
                        </div>
                    </div>
                    <hr style="border: none; border-top: 1px solid rgba(255,255,255,0.1); margin: 20px 0;">
                    <div style="text-align: center;">
                        <strong style="font-size: 16px;">NET PAY</strong><br>
                        <span style="font-size: 36px; font-weight: bold; color: #c9963a;">
                            ${salary['net_pay']:,.2f}
                        </span>
                        <div style="font-size: 12px; color: #7d96be; margin-top: 5px;">
                            {salary['currency']} • Period: {salary['period'] or 'Current'}
                        </div>
                    </div>
                </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown("### 📊 Composition")
            total = salary['base_salary'] + salary['allowances'] + salary['bonus']
            base_pct = (salary['base_salary'] / total * 100) if total > 0 else 0
            allow_pct = (salary['allowances'] / total * 100) if total > 0 else 0
            bonus_pct = (salary['bonus'] / total * 100) if total > 0 else 0

            st.markdown(f"Base: {base_pct:.1f}%")
            st.markdown(f"Allowances: {allow_pct:.1f}%")
            st.markdown(f"Bonus: {bonus_pct:.1f}%")
    else:
        st.info("💡 No salary information available. Please contact HR.")

def show_my_payslips():
    """Employee view of own payslips"""
    user = get_current_user()

    st.markdown("### 📄 My Payslips")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM payslips
            WHERE emp_id = %s
            ORDER BY generated_at DESC
        """, (user['employee_id'],))
        payslips = [dict(row) for row in cursor.fetchall()]

    if payslips:
        for payslip in payslips:
            with st.expander(f"📄 Payslip - {payslip['period']}"):
                st.markdown(f"""
                **Period:** {payslip['period']}
                **Base Salary:** ${payslip['base_salary']:,.2f}
                **Allowances:** ${payslip['allowances']:,.2f}
                **Bonus:** ${payslip['bonus']:,.2f}
                **Deductions:** ${payslip['deductions']:,.2f}
                **Net Pay:** ${payslip['net_pay']:,.2f}
                **Generated:** {payslip['generated_at']}
                """)

                if st.button(f"📥 Download PDF", key=f"download_{payslip['id']}"):
                    st.info("PDF generation will be implemented")
    else:
        st.info("No payslips available yet")

def get_departments():
    """Get list of departments"""
    return [
        "Engineering",
        "Marketing",
        "Finance",
        "Human Resources",
        "Operations",
        "Sales",
        "Legal",
        "Design"
    ]
