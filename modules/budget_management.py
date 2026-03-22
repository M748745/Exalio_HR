"""
Budget Management Module
Manage department budgets, track expenses, and monitor variance
"""

import streamlit as st
import pandas as pd
from datetime import datetime, date
from database import get_db_connection
from auth import get_current_user, is_hr_admin, is_manager, create_notification, log_audit

def show_budget_management():
    """Main budget management interface"""
    user = get_current_user()

    st.markdown("## 💰 Budget Management")
    st.markdown("Plan, track, and manage department budgets")
    st.markdown("---")

    if is_hr_admin():
        tabs = st.tabs(["📊 All Budgets", "📈 Budget vs Actual", "✅ Approvals", "➕ Create Budget", "📊 Analytics"])
    elif is_manager():
        tabs = st.tabs(["💼 My Budget", "📊 Expenses", "📈 Variance Report"])
    else:
        tabs = st.tabs(["📊 Department Budget"])

    with tabs[0]:
        if is_hr_admin():
            show_all_budgets()
        elif is_manager():
            show_manager_budget()
        else:
            show_department_info()

    with tabs[1]:
        if is_hr_admin():
            show_budget_variance()
        elif is_manager():
            show_my_expenses()

    if is_hr_admin() and len(tabs) > 2:
        with tabs[2]:
            show_budget_approvals()
        with tabs[3]:
            create_budget()
        with tabs[4]:
            show_budget_analytics()
    elif is_manager() and len(tabs) > 2:
        with tabs[2]:
            show_variance_report()

def show_all_budgets():
    """Show all department budgets"""
    st.markdown("### 📊 All Department Budgets")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT
                b.id, b.department, b.fiscal_year, b.period_month, b.amount,
                b.category, b.notes, b.status, b.created_by, b.created_at, b.updated_at,
                COALESCE(SUM(e.amount), 0) as spent,
                b.amount - COALESCE(SUM(e.amount), 0) as remaining
            FROM budgets b
            LEFT JOIN expenses e ON b.department = e.department
                AND e.status = 'Approved'
                AND EXTRACT(YEAR FROM e.expense_date) = b.fiscal_year
                AND EXTRACT(MONTH FROM e.expense_date) = b.period_month
            WHERE b.status = 'Active'
            GROUP BY b.id, b.department, b.amount, b.fiscal_year, b.period_month, b.category,
                     b.notes, b.status, b.created_by, b.created_at, b.updated_at
            ORDER BY b.fiscal_year DESC, b.period_month DESC
        """)
        budgets = [dict(row) for row in cursor.fetchall()]

    if budgets:
        for budget in budgets:
            utilization = (budget['spent'] / budget['amount'] * 100) if budget['amount'] > 0 else 0
            color = '🟢' if utilization < 75 else '🟡' if utilization < 90 else '🔴'

            with st.expander(f"{color} {budget['department']} - FY{budget['fiscal_year']} Month {budget['period_month']} - {utilization:.1f}% utilized"):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Budget", f"${budget['amount']:,.2f}")
                with col2:
                    st.metric("Spent", f"${budget['spent']:,.2f}", delta=f"-${budget['spent']:,.2f}", delta_color="inverse")
                with col3:
                    st.metric("Remaining", f"${budget['remaining']:,.2f}")

                st.progress(min(utilization / 100, 1.0))
    else:
        st.info("No active budgets")

def create_budget():
    """Create new budget"""
    st.markdown("### ➕ Create Department Budget")

    with st.form("create_budget"):
        col1, col2 = st.columns(2)
        with col1:
            department = st.selectbox("Department *", ["Engineering", "Sales", "Marketing", "HR", "Finance", "Operations"])
            fiscal_year = st.number_input("Fiscal Year *", min_value=2024, max_value=2030, value=2024)
            period_month = st.selectbox("Period Month *", list(range(1, 13)))
        with col2:
            amount = st.number_input("Budget Amount ($) *", min_value=0.0, step=1000.0)
            category = st.selectbox("Category", ["Operational", "Capital", "Project", "General"])

        notes = st.text_area("Notes")
        submitted = st.form_submit_button("💾 Create Budget")

        if submitted and department and amount > 0:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO budgets (department, fiscal_year, period_month, amount, category, notes, status, created_by)
                    VALUES (%s, %s, %s, %s, %s, %s, 'Active', %s)
                """, (department, fiscal_year, period_month, amount, category, notes, get_current_user()['employee_id']))
                conn.commit()
                st.success("✅ Budget created successfully!")

def show_manager_budget():
    """Show manager's department budget"""
    user = get_current_user()
    st.markdown("### 💼 My Department Budget")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT department FROM employees WHERE id = %s", (user['employee_id'],))
        dept = cursor.fetchone()
        if dept:
            cursor.execute("""
                SELECT b.*, COALESCE(SUM(e.amount), 0) as spent
                FROM budgets b
                LEFT JOIN expenses e ON b.department = e.department AND e.status = 'Approved'
                WHERE b.department = %s AND b.status = 'Active'
                GROUP BY b.id
                ORDER BY b.fiscal_year DESC
            """, (dept['department'],))
            budgets = [dict(row) for row in cursor.fetchall()]

            if budgets:
                for b in budgets:
                    remaining = b['amount'] - b['spent']
                    st.markdown(f"**FY{b['fiscal_year']} Month {b['period_month']}:** ${b['amount']:,.2f} | Spent: ${b['spent']:,.2f} | Remaining: ${remaining:,.2f}")
            else:
                st.info("No budget allocated")

def show_department_info():
    """Show budget info for employees"""
    st.markdown("### 📊 Department Budget Information")
    st.info("Contact your manager for budget details")

def show_budget_variance():
    """Show budget variance report"""
    st.markdown("### 📈 Budget vs Actual Variance")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT
                b.department,
                b.fiscal_year,
                b.period_month,
                b.amount as budget,
                COALESCE(SUM(e.amount), 0) as actual,
                b.amount - COALESCE(SUM(e.amount), 0) as variance,
                CASE
                    WHEN COALESCE(SUM(e.amount), 0) > b.amount THEN 'Over Budget'
                    WHEN COALESCE(SUM(e.amount), 0) > b.amount * 0.9 THEN 'Near Limit'
                    ELSE 'Within Budget'
                END as status
            FROM budgets b
            LEFT JOIN expenses e ON b.department = e.department
                AND e.status = 'Paid'
                AND EXTRACT(YEAR FROM e.expense_date) = b.fiscal_year
                AND EXTRACT(MONTH FROM e.expense_date) = b.period_month
            WHERE b.status = 'Active'
            GROUP BY b.id, b.department, b.fiscal_year, b.period_month, b.amount
            ORDER BY b.fiscal_year DESC, b.period_month DESC
        """)
        variances = [dict(row) for row in cursor.fetchall()]

    if variances:
        for v in variances:
            variance_pct = (v['variance'] / v['budget'] * 100) if v['budget'] > 0 else 0
            color = '🟢' if v['status'] == 'Within Budget' else '🟡' if v['status'] == 'Near Limit' else '🔴'

            with st.expander(f"{color} {v['department']} - FY{v['fiscal_year']}/M{v['period_month']} - {v['status']}"):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Budget", f"${v['budget']:,.2f}")
                with col2:
                    st.metric("Actual", f"${v['actual']:,.2f}")
                with col3:
                    delta_color = "normal" if v['variance'] >= 0 else "inverse"
                    st.metric("Variance", f"${v['variance']:,.2f}", delta=f"{variance_pct:.1f}%", delta_color=delta_color)
    else:
        st.info("No variance data available")

def show_budget_approvals():
    """Show pending budget approvals"""
    st.markdown("### ✅ Budget Approvals")
    st.info("No pending approvals")

def show_budget_analytics():
    """Show budget analytics"""
    st.markdown("### 📊 Budget Analytics")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT
                SUM(amount) as total_budget,
                COUNT(DISTINCT department) as dept_count
            FROM budgets WHERE status = 'Active'
        """)
        stats = dict(cursor.fetchone())

        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total Budget", f"${stats['total_budget'] or 0:,.2f}")
        with col2:
            st.metric("Departments", stats['dept_count'] or 0)

def show_my_expenses():
    """Show manager's department expenses"""
    user = get_current_user()
    st.markdown("### 📊 Department Expenses")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT department FROM employees WHERE id = %s", (user['employee_id'],))
        dept_row = cursor.fetchone()

        if dept_row:
            dept = dept_row['department']
            cursor.execute("""
                SELECT e.*, emp.first_name, emp.last_name
                FROM expenses e
                JOIN employees emp ON e.emp_id = emp.id
                WHERE emp.department = %s
                ORDER BY e.expense_date DESC
                LIMIT 50
            """, (dept,))
            expenses = [dict(row) for row in cursor.fetchall()]

            if expenses:
                for expense in expenses:
                    status_color = '🟢' if expense['status'] == 'Paid' else '🟡' if 'Approved' in expense['status'] else '🔴'
                    with st.expander(f"{status_color} {expense['first_name']} {expense['last_name']} - {expense['expense_type']} - ${expense['amount']:,.2f}"):
                        st.write(f"**Date:** {expense['expense_date']}")
                        st.write(f"**Status:** {expense['status']}")
                        st.write(f"**Description:** {expense['description']}")
            else:
                st.info("No expenses found")

def show_variance_report():
    """Show variance report for manager"""
    user = get_current_user()
    st.markdown("### 📈 Variance Report")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT department FROM employees WHERE id = %s", (user['employee_id'],))
        dept_row = cursor.fetchone()

        if dept_row:
            dept = dept_row['department']
            cursor.execute("""
                SELECT
                    b.fiscal_year,
                    b.period_month,
                    b.amount as budget,
                    COALESCE(SUM(e.amount), 0) as spent,
                    b.amount - COALESCE(SUM(e.amount), 0) as remaining
                FROM budgets b
                LEFT JOIN expenses e ON b.department = e.department
                    AND e.status = 'Paid'
                    AND EXTRACT(YEAR FROM e.expense_date) = b.fiscal_year
                    AND EXTRACT(MONTH FROM e.expense_date) = b.period_month
                WHERE b.department = %s AND b.status = 'Active'
                GROUP BY b.id, b.fiscal_year, b.period_month, b.amount
                ORDER BY b.fiscal_year DESC, b.period_month DESC
            """, (dept,))
            variances = [dict(row) for row in cursor.fetchall()]

            if variances:
                for v in variances:
                    utilization = (v['spent'] / v['budget'] * 100) if v['budget'] > 0 else 0
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric(f"FY{v['fiscal_year']}/M{v['period_month']} Budget", f"${v['budget']:,.2f}")
                    with col2:
                        st.metric("Spent", f"${v['spent']:,.2f}", delta=f"-{utilization:.1f}%", delta_color="inverse")
                    with col3:
                        st.metric("Remaining", f"${v['remaining']:,.2f}")
                    st.progress(min(utilization / 100, 1.0))
                    st.markdown("---")
            else:
                st.info("No budget variance data available")
