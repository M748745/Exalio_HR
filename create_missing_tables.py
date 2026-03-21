"""
Create Missing Tables - Adds 8 Missing Tables
Run this to create all tables that don't exist in your database
"""

import streamlit as st
from database import get_db_connection

st.title("🏗️ Create Missing Tables")
st.warning("⚠️ This will create 8 missing tables in your database. Run it ONCE.")

# SQL to create all missing tables
CREATE_TABLES_SQL = """
-- ============================================================
-- 1. PROMOTION_REQUESTS TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS promotion_requests (
    id SERIAL PRIMARY KEY,
    emp_id INTEGER NOT NULL,
    current_position TEXT,
    current_grade TEXT,
    current_salary REAL,
    proposed_position TEXT,
    proposed_grade TEXT,
    proposed_salary REAL,
    justification TEXT,
    performance_rating TEXT,
    status TEXT DEFAULT 'Pending' CHECK(status IN ('Pending', 'Manager Approved', 'HR Approved', 'Rejected')),
    requested_by INTEGER,
    requested_date TIMESTAMP DEFAULT NOW(),
    manager_approved_by INTEGER,
    manager_approval_date TIMESTAMP,
    hr_approved_by INTEGER,
    hr_approval_date TIMESTAMP,
    effective_date DATE,
    created_at TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (emp_id) REFERENCES employees(id),
    FOREIGN KEY (requested_by) REFERENCES employees(id),
    FOREIGN KEY (manager_approved_by) REFERENCES employees(id),
    FOREIGN KEY (hr_approved_by) REFERENCES employees(id)
);

-- ============================================================
-- 2. COMPLIANCE_REQUIREMENTS TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS compliance_requirements (
    id SERIAL PRIMARY KEY,
    requirement_name TEXT NOT NULL,
    requirement_type TEXT,
    description TEXT,
    frequency TEXT CHECK(frequency IN ('One-time', 'Annual', 'Quarterly', 'Monthly')),
    applicable_to TEXT,
    due_date DATE,
    status TEXT DEFAULT 'Active' CHECK(status IN ('Active', 'Completed', 'Expired')),
    created_by INTEGER,
    created_at TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (created_by) REFERENCES employees(id)
);

-- ============================================================
-- 3. SHIFT_SWAPS TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS shift_swaps (
    id SERIAL PRIMARY KEY,
    requester_emp_id INTEGER NOT NULL,
    swapper_emp_id INTEGER,
    shift_date DATE NOT NULL,
    shift_type TEXT,
    original_shift_start TIME,
    original_shift_end TIME,
    swap_shift_start TIME,
    swap_shift_end TIME,
    reason TEXT,
    status TEXT DEFAULT 'Pending' CHECK(status IN ('Pending', 'Accepted', 'Approved', 'Rejected', 'Cancelled')),
    request_date TIMESTAMP DEFAULT NOW(),
    approved_by INTEGER,
    approval_date TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (requester_emp_id) REFERENCES employees(id),
    FOREIGN KEY (swapper_emp_id) REFERENCES employees(id),
    FOREIGN KEY (approved_by) REFERENCES employees(id)
);

-- ============================================================
-- 4. CALIBRATION_SESSIONS TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS calibration_sessions (
    id SERIAL PRIMARY KEY,
    session_name TEXT NOT NULL,
    session_date DATE NOT NULL,
    review_period TEXT,
    departments TEXT,
    facilitator_id INTEGER,
    participants TEXT,
    notes TEXT,
    status TEXT DEFAULT 'Scheduled' CHECK(status IN ('Scheduled', 'In Progress', 'Completed', 'Cancelled')),
    created_by INTEGER,
    created_at TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (facilitator_id) REFERENCES employees(id),
    FOREIGN KEY (created_by) REFERENCES employees(id)
);

-- ============================================================
-- 5. CALIBRATION_SESSION_RATINGS TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS calibration_session_ratings (
    id SERIAL PRIMARY KEY,
    session_id INTEGER NOT NULL,
    emp_id INTEGER NOT NULL,
    appraisal_id INTEGER,
    initial_rating INTEGER,
    calibrated_rating INTEGER,
    calibration_notes TEXT,
    calibrated_by INTEGER,
    calibration_date TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (session_id) REFERENCES calibration_sessions(id) ON DELETE CASCADE,
    FOREIGN KEY (emp_id) REFERENCES employees(id),
    FOREIGN KEY (appraisal_id) REFERENCES appraisals(id),
    FOREIGN KEY (calibrated_by) REFERENCES employees(id)
);

-- ============================================================
-- 6. SUCCESSION_PLANS TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS succession_plans (
    id SERIAL PRIMARY KEY,
    key_position TEXT NOT NULL,
    key_position_emp_id INTEGER,
    successor_emp_id INTEGER,
    criticality TEXT CHECK(criticality IN ('Critical', 'High', 'Medium', 'Low')),
    readiness_level TEXT,
    development_plan TEXT,
    target_ready_date DATE,
    status TEXT DEFAULT 'Active',
    notes TEXT,
    created_by INTEGER,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP,
    FOREIGN KEY (key_position_emp_id) REFERENCES employees(id),
    FOREIGN KEY (successor_emp_id) REFERENCES employees(id),
    FOREIGN KEY (created_by) REFERENCES employees(id)
);

-- ============================================================
-- 7. PIPS TABLE (Performance Improvement Plans)
-- ============================================================
CREATE TABLE IF NOT EXISTS pips (
    id SERIAL PRIMARY KEY,
    emp_id INTEGER NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    performance_issues TEXT,
    improvement_goals TEXT,
    success_criteria TEXT,
    support_resources TEXT,
    consequences TEXT,
    review_frequency TEXT,
    status TEXT DEFAULT 'Active' CHECK(status IN ('Active', 'Completed', 'Extended', 'Terminated')),
    manager_id INTEGER,
    hr_reviewer INTEGER,
    created_by INTEGER,
    created_at TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (emp_id) REFERENCES employees(id),
    FOREIGN KEY (manager_id) REFERENCES employees(id),
    FOREIGN KEY (hr_reviewer) REFERENCES employees(id),
    FOREIGN KEY (created_by) REFERENCES employees(id)
);

-- ============================================================
-- 8. PIP_PROGRESS TABLE
-- ============================================================
CREATE TABLE IF NOT EXISTS pip_progress (
    id SERIAL PRIMARY KEY,
    pip_id INTEGER NOT NULL,
    review_date DATE NOT NULL,
    progress_summary TEXT,
    achievements TEXT,
    challenges TEXT,
    manager_feedback TEXT,
    next_steps TEXT,
    status TEXT CHECK(status IN ('On Track', 'Needs Improvement', 'Exceeded Expectations')),
    reviewed_by INTEGER,
    created_at TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (pip_id) REFERENCES pips(id) ON DELETE CASCADE,
    FOREIGN KEY (reviewed_by) REFERENCES employees(id)
);
"""

if st.button("🏗️ CREATE ALL 8 MISSING TABLES", type="primary", use_container_width=True):
    progress_bar = st.progress(0)
    status_text = st.empty()

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # Split into individual CREATE TABLE statements
            statements = [s.strip() for s in CREATE_TABLES_SQL.split(';') if s.strip() and 'CREATE TABLE' in s]

            total = len(statements)
            success_count = 0
            skip_count = 0
            error_count = 0
            results = []

            for i, statement in enumerate(statements):
                # Extract table name
                table_match = statement.split('CREATE TABLE IF NOT EXISTS')[1].split('(')[0].strip()
                table_name = table_match

                status_text.text(f"[{i+1}/{total}] Creating table: {table_name}...")

                try:
                    cursor.execute(statement + ';')
                    conn.commit()
                    success_count += 1
                    results.append(('success', f"Table '{table_name}' created successfully"))
                except Exception as e:
                    error_msg = str(e).lower()
                    if 'already exists' in error_msg:
                        skip_count += 1
                        results.append(('skip', f"Table '{table_name}' already exists"))
                    else:
                        error_count += 1
                        results.append(('error', f"Table '{table_name}': {str(e)[:80]}"))
                        conn.rollback()

                progress_bar.progress((i + 1) / total)

            # Show results
            st.success(f"🎉 Table Creation Complete!")

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("✅ Created", success_count, delta="New tables")
            with col2:
                st.metric("⏭️ Skipped", skip_count, delta="Already exist")
            with col3:
                st.metric("❌ Errors", error_count, delta="Failed")

            # Show detailed results
            with st.expander(f"📋 Detailed Results ({len(results)} items)", expanded=error_count > 0):
                for status, msg in results:
                    if status == 'success':
                        st.success(f"✅ {msg}")
                    elif status == 'skip':
                        st.info(f"ℹ️ {msg}")
                    else:
                        st.error(f"❌ {msg}")

            if success_count > 0:
                st.balloons()

            st.success(f"""
            ✅ **Table Creation Complete! {success_count} tables created**

            **Next Steps:**
            1. Close this page
            2. Run check_remaining_errors.py again to verify
            3. If there are still missing columns, re-run run_migration.py
            4. Your app should work after fixing all issues!
            """)

    except Exception as e:
        st.error(f"❌ Critical Error: {str(e)}")
        st.code(str(e))
        import traceback
        st.code(traceback.format_exc())

else:
    st.info("""
    ### 📊 This will create 8 missing tables:

    1. **promotion_requests** - Employee promotion workflow
    2. **compliance_requirements** - Compliance tracking
    3. **shift_swaps** - Shift swap requests
    4. **calibration_sessions** - Appraisal calibration
    5. **calibration_session_ratings** - Calibration ratings
    6. **succession_plans** - Succession planning
    7. **pips** - Performance improvement plans
    8. **pip_progress** - PIP progress tracking

    **These tables are required by your modules but don't exist in the database.**
    """)

    st.warning("⚠️ Safe to run multiple times - existing tables will be skipped.")

st.markdown("---")
st.caption("Table Creation Tool v1.0 - Creates Missing Tables")
