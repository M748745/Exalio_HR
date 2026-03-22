"""
Succession Planning Module
Identify key positions, nominate successors, track development and readiness
"""

import streamlit as st
import pandas as pd
from datetime import datetime, date
from database import get_db_connection
from auth import get_current_user, is_hr_admin, is_manager, create_notification, log_audit

def show_succession_planning():
    """Main succession planning interface"""
    user = get_current_user()

    st.markdown("## 🔄 Succession Planning")
    st.markdown("Identify critical roles and develop future leaders")
    st.markdown("---")

    if is_hr_admin():
        tabs = st.tabs(["📊 All Plans", "🎯 Key Positions", "👥 Talent Pool", "➕ Create Plan", "📊 Readiness Matrix"])
    elif is_manager():
        tabs = st.tabs(["📋 Department Plans", "👥 Potential Successors"])
    else:
        tabs = st.tabs(["📊 My Development Plan"])

    with tabs[0]:
        if is_hr_admin():
            show_all_succession_plans()
        elif is_manager():
            show_department_plans()
        else:
            show_my_development_plan()

    if is_hr_admin() and len(tabs) > 1:
        with tabs[1]:
            show_key_positions()
        with tabs[2]:
            show_talent_pool()
        with tabs[3]:
            create_succession_plan()
        with tabs[4]:
            show_readiness_matrix()
    elif is_manager() and len(tabs) > 1:
        with tabs[1]:
            show_potential_successors()

def show_all_succession_plans():
    """Show all succession plans"""
    st.markdown("### 📊 All Succession Plans")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT sp.*, e.first_name, e.last_name, e.position, e.department,
                   s.first_name as successor_first, s.last_name as successor_last
            FROM succession_plans sp
            JOIN employees e ON sp.key_position_emp_id = e.id
            LEFT JOIN employees s ON sp.successor_emp_id = s.id
            ORDER BY sp.criticality DESC, sp.readiness_level
        """)
        plans = [dict(row) for row in cursor.fetchall()]

    if plans:
        for plan in plans:
            criticality_icon = '🔴' if plan['criticality'] == 'Critical' else '🟡' if plan['criticality'] == 'High' else '🟢'
            readiness_icon = '✅' if plan['readiness_level'] == 'Ready Now' else '🟡' if plan['readiness_level'] == '1-2 Years' else '🔵'

            with st.expander(f"{criticality_icon} {plan['position']} ({plan['first_name']} {plan['last_name']}) - {plan['department']}"):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Current Holder:** {plan['first_name']} {plan['last_name']}")
                    st.write(f"**Department:** {plan['department']}")
                    st.write(f"**Criticality:** {plan['criticality']}")
                    st.write(f"**Risk:** {plan.get('risk_level', 'N/A')}")
                with col2:
                    if plan['successor_emp_id']:
                        st.write(f"**Successor:** {plan['successor_first']} {plan['successor_last']}")
                        st.write(f"**Readiness:** {plan['readiness_level']}")
                        st.write(f"{readiness_icon} Development Progress")
                    else:
                        st.warning("⚠️ No successor identified")

                if plan.get('development_plan'):
                    with st.expander("Development Plan"):
                        st.write(plan['development_plan'])
    else:
        st.info("No succession plans created yet")

def create_succession_plan():
    """Create new succession plan"""
    st.markdown("### ➕ Create Succession Plan")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, first_name, last_name, position, department
            FROM employees WHERE status = 'Active'
            ORDER BY first_name
        """)
        employees = [dict(row) for row in cursor.fetchall()]

    if employees:
        with st.form("create_succession"):
            emp_options = {f"{e['first_name']} {e['last_name']} - {e['position']} ({e['department']})": e['id'] for e in employees}

            col1, col2 = st.columns(2)
            with col1:
                key_position = st.selectbox("Key Position Holder *", list(emp_options.keys()))
                criticality = st.selectbox("Position Criticality *", ["Critical", "High", "Medium", "Low"])
                risk_level = st.selectbox("Succession Risk", ["High", "Medium", "Low"])
            with col2:
                successor = st.selectbox("Identified Successor", ["None"] + list(emp_options.keys()))
                readiness_level = st.selectbox("Successor Readiness", ["Ready Now", "1-2 Years", "2-3 Years", "3+ Years"])
                target_date = st.date_input("Target Readiness Date")

            development_plan = st.text_area("Development Plan & Actions")
            notes = st.text_area("Additional Notes")

            submitted = st.form_submit_button("💾 Create Succession Plan")

            if submitted and key_position:
                key_emp_id = emp_options[key_position]
                successor_emp_id = emp_options[successor] if successor != "None" else None

                with get_db_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT INTO succession_plans (key_position_emp_id, successor_emp_id, criticality,
                                                     risk_level, readiness_level, development_plan,
                                                     target_readiness_date, notes, status, created_by)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'Active', %s)
                    """, (key_emp_id, successor_emp_id, criticality, risk_level, readiness_level,
                         development_plan, target_date, notes, get_current_user()['employee_id']))
                    conn.commit()

                    if successor_emp_id:
                        create_notification(successor_emp_id, "Succession Plan - Development Opportunity",
                                          "You have been identified as a successor for a key position", "info")

                    log_audit(get_current_user()['id'], f"Created succession plan for position {key_position}", "succession_plans")
                    st.success("✅ Succession plan created!")

def show_key_positions():
    """Show critical positions"""
    st.markdown("### 🎯 Key/Critical Positions")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT sp.*, e.first_name, e.last_name, e.position, e.department
            FROM succession_plans sp
            JOIN employees e ON sp.key_position_emp_id = e.id
            WHERE sp.criticality IN ('Critical', 'High')
            ORDER BY sp.criticality DESC
        """)
        positions = [dict(row) for row in cursor.fetchall()]

    if positions:
        for pos in positions:
            icon = '🔴' if pos['criticality'] == 'Critical' else '🟡'
            st.write(f"{icon} **{pos['position']}** - {pos['first_name']} {pos['last_name']} ({pos['department']}) - Risk: {pos.get('risk_level', 'N/A')}")
    else:
        st.info("No critical positions identified")

def show_talent_pool():
    """Show talent pool for succession"""
    st.markdown("### 👥 Talent Pool for Succession")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT DISTINCT e.*, sp.readiness_level, sp.development_plan
            FROM employees e
            JOIN succession_plans sp ON e.id = sp.successor_emp_id
            WHERE sp.status = 'Active'
            ORDER BY e.department, e.first_name
        """)
        talents = [dict(row) for row in cursor.fetchall()]

    if talents:
        for talent in talents:
            st.write(f"👤 **{talent['first_name']} {talent['last_name']}** - {talent['position']} ({talent['department']}) - Readiness: {talent['readiness_level']}")
    else:
        st.info("No successors identified yet")

def show_department_plans():
    """Show department succession plans"""
    user = get_current_user()
    st.markdown("### 📋 Department Succession Plans")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT department FROM employees WHERE id = %s", (user['employee_id'],))
        dept_row = cursor.fetchone()

        if dept_row:
            dept = dept_row['department']
            cursor.execute("""
                SELECT sp.*, e.first_name, e.last_name, e.position,
                       s.first_name as successor_first, s.last_name as successor_last
                FROM succession_plans sp
                JOIN employees e ON sp.key_position_emp_id = e.id
                LEFT JOIN employees s ON sp.successor_emp_id = s.id
                WHERE e.department = %s
                ORDER BY sp.criticality DESC
            """, (dept,))
            plans = [dict(row) for row in cursor.fetchall()]

            if plans:
                for plan in plans:
                    st.write(f"**{plan['position']}** ({plan['first_name']} {plan['last_name']}) → Successor: {plan['successor_first']} {plan['successor_last'] if plan['successor_first'] else 'Not Assigned'}")
            else:
                st.info("No succession plans for this department")

def show_potential_successors():
    """Show potential successors in department"""
    user = get_current_user()
    st.markdown("### 👥 Potential Successors")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT department FROM employees WHERE id = %s", (user['employee_id'],))
        dept_row = cursor.fetchone()

        if dept_row:
            dept = dept_row['department']
            cursor.execute("""
                SELECT e.*, sp.readiness_level
                FROM employees e
                LEFT JOIN succession_plans sp ON e.id = sp.successor_emp_id
                WHERE e.department = %s AND e.status = 'Active'
                ORDER BY e.first_name
            """, (dept,))
            candidates = [dict(row) for row in cursor.fetchall()]

            if candidates:
                for candidate in candidates:
                    readiness = candidate['readiness_level'] if candidate['readiness_level'] else 'Not in plan'
                    st.write(f"👤 {candidate['first_name']} {candidate['last_name']} - {candidate['position']} - Readiness: {readiness}")

def show_my_development_plan():
    """Show employee development plan"""
    user = get_current_user()
    st.markdown("### 📊 My Development Plan")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT sp.*, e.first_name, e.last_name, e.position as target_position
            FROM succession_plans sp
            JOIN employees e ON sp.key_position_emp_id = e.id
            WHERE sp.successor_emp_id = %s
        """, (user['employee_id'],))
        plan = cursor.fetchone()

    if plan:
        plan = dict(plan)
        st.success(f"✨ You are being developed for: **{plan['target_position']}**")
        st.write(f"**Current Holder:** {plan['first_name']} {plan['last_name']}")
        st.write(f"**Readiness Level:** {plan['readiness_level']}")
        st.write(f"**Target Date:** {plan['target_readiness_date']}")

        if plan['development_plan']:
            st.markdown("#### Development Actions:")
            st.info(plan['development_plan'])
    else:
        st.info("You are not currently in a succession plan. Focus on your performance and development goals!")

def show_readiness_matrix():
    """Show readiness matrix"""
    st.markdown("### 📊 Succession Readiness Matrix")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT
                readiness_level,
                COUNT(*) as count
            FROM succession_plans
            WHERE successor_emp_id IS NOT NULL AND status = 'Active'
            GROUP BY readiness_level
            ORDER BY
                CASE readiness_level
                    WHEN 'Ready Now' THEN 1
                    WHEN '1-2 Years' THEN 2
                    WHEN '2-3 Years' THEN 3
                    ELSE 4
                END
        """)
        matrix = [dict(row) for row in cursor.fetchall()]

    if matrix:
        for item in matrix:
            st.metric(item['readiness_level'], item['count'])
    else:
        st.info("No succession readiness data available")
