# 🚀 Deploy to Streamlit Cloud - Complete Guide

## ✅ All Fixes Applied Locally

All database errors have been fixed in your local files:

### Fixed Modules (8 files)
1. ✅ `modules/compliance.py` - Fixed `due_date` column
2. ✅ `modules/documents.py` - Fixed `title` column + .str accessor
3. ✅ `modules/training.py` - Fixed `enrollment_date` column
4. ✅ `modules/certificate_tracking.py` - Fixed `issuing_organization` column
5. ✅ `modules/promotion_workflow.py` - Fixed `requested_by` column
6. ✅ `modules/asset_procurement.py` - Removed non-existent columns
7. ✅ `modules/goal_okr_review.py` - Fixed ORDER BY clause
8. ✅ `modules/team_position_admin.py` - Fixed GROUP BY clause

### New Fixes Applied
9. ✅ `modules/document_approval.py` - Fixed `uploaded_by` vs `created_by`
10. ✅ `modules/skill_matrix_admin.py` - Removed `updated_at` from GROUP BY
11. ✅ `modules/contract_renewal.py` - Added NULL check for days_remaining

### Database Updates
12. ✅ `run_migrations.py` - Added budgets table creation
13. ✅ `database.py` - Updated table definitions

---

## 📋 Step-by-Step Deployment

### Step 1: Commit All Changes

```bash
cd "D:\exalio_work\HR\HR_system_upload"

# Add all changed files
git add .

# Commit with descriptive message
git commit -m "Fix all database errors - column mismatches, missing tables, NULL checks"

# Push to GitHub
git push origin main
```

### Step 2: Wait for Streamlit Cloud Auto-Redeploy

Streamlit Cloud will automatically detect your push and redeploy the app. This takes **2-5 minutes**.

You can watch the deployment in real-time:
1. Go to Streamlit Cloud dashboard
2. Click on your app
3. Watch the deployment logs

### Step 3: Run Migration on Streamlit Cloud

After the app redeploys, you need to create the missing table on Streamlit Cloud.

**Option A: Create the table via Streamlit app (Recommended)**

Add this temporary migration button to your app:

```python
# Add to app.py sidebar temporarily
if st.sidebar.button("🔧 Run Database Migrations"):
    import subprocess
    result = subprocess.run(["python", "run_migrations.py"], capture_output=True, text=True)
    st.code(result.stdout)
    st.code(result.stderr)
```

**Option B: Run via Streamlit Cloud shell (Advanced)**

If you have shell access, run:
```bash
python run_migrations.py
```

**Option C: Manual SQL (if needed)**

Execute this SQL on your Neon PostgreSQL database:

```sql
CREATE TABLE IF NOT EXISTS budgets (
    id SERIAL PRIMARY KEY,
    department TEXT NOT NULL,
    fiscal_year INTEGER NOT NULL,
    period_month INTEGER CHECK(period_month BETWEEN 1 AND 12),
    amount REAL NOT NULL,
    category TEXT CHECK(category IN ('Operational', 'Capital', 'Project', 'General')),
    notes TEXT,
    status TEXT DEFAULT 'Active' CHECK(status IN ('Active', 'Inactive', 'Closed')),
    created_by INTEGER,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (created_by) REFERENCES employees(id)
);

-- Also ensure these other tables exist (they should already)
-- But just in case:

CREATE TABLE IF NOT EXISTS shift_templates (
    id SERIAL PRIMARY KEY,
    shift_name TEXT NOT NULL,
    shift_type TEXT CHECK(shift_type IN ('Morning', 'Afternoon', 'Evening', 'Night', 'Full Day', 'Flexible')),
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    department TEXT,
    description TEXT,
    status TEXT DEFAULT 'Active' CHECK(status IN ('Active', 'Inactive')),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS shift_schedules (
    id SERIAL PRIMARY KEY,
    emp_id INTEGER NOT NULL,
    shift_id INTEGER NOT NULL,
    shift_date DATE NOT NULL,
    location TEXT DEFAULT 'Office',
    notes TEXT,
    status TEXT DEFAULT 'Scheduled' CHECK(status IN ('Scheduled', 'Confirmed', 'Completed', 'Cancelled')),
    created_by INTEGER,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (emp_id) REFERENCES employees(id) ON DELETE CASCADE,
    FOREIGN KEY (shift_id) REFERENCES shift_templates(id),
    FOREIGN KEY (created_by) REFERENCES employees(id)
);

CREATE TABLE IF NOT EXISTS compliance_requirements (
    id SERIAL PRIMARY KEY,
    requirement_name TEXT NOT NULL,
    requirement_type TEXT CHECK(requirement_type IN ('Legal', 'Regulatory', 'Policy', 'Safety', 'Training', 'Certification', 'Other')),
    description TEXT,
    department TEXT,
    responsible_party TEXT,
    frequency TEXT CHECK(frequency IN ('One-Time', 'Monthly', 'Quarterly', 'Semi-Annual', 'Annual', 'Biennial')),
    last_review_date DATE,
    next_review_date DATE,
    due_date DATE NOT NULL,
    status TEXT DEFAULT 'Pending' CHECK(status IN ('Compliant', 'Pending', 'Non-Compliant', 'In Progress')),
    evidence_file_path TEXT,
    notes TEXT,
    created_by INTEGER,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (created_by) REFERENCES employees(id)
);

CREATE TABLE IF NOT EXISTS onboarding (
    id SERIAL PRIMARY KEY,
    emp_id INTEGER NOT NULL,
    start_date DATE NOT NULL,
    buddy_id INTEGER,
    orientation_date DATE,
    it_setup TEXT DEFAULT 'Pending' CHECK(it_setup IN ('Pending', 'In Progress', 'Completed')),
    workspace_setup TEXT DEFAULT 'Pending' CHECK(workspace_setup IN ('Pending', 'In Progress', 'Completed')),
    system_access TEXT DEFAULT 'Pending' CHECK(system_access IN ('Pending', 'In Progress', 'Completed')),
    email_setup TEXT DEFAULT 'Pending' CHECK(email_setup IN ('Pending', 'In Progress', 'Completed')),
    team_introduction TEXT DEFAULT 'Pending' CHECK(team_introduction IN ('Pending', 'In Progress', 'Completed')),
    policy_review TEXT DEFAULT 'Pending' CHECK(policy_review IN ('Pending', 'In Progress', 'Completed')),
    training_scheduled TEXT DEFAULT 'Pending' CHECK(training_scheduled IN ('Pending', 'In Progress', 'Completed')),
    status TEXT DEFAULT 'Pending' CHECK(status IN ('Pending', 'In Progress', 'Completed', 'Cancelled')),
    completion_date DATE,
    notes TEXT,
    created_by INTEGER,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (emp_id) REFERENCES employees(id) ON DELETE CASCADE,
    FOREIGN KEY (buddy_id) REFERENCES employees(id),
    FOREIGN KEY (created_by) REFERENCES employees(id)
);

-- Add missing columns to training_catalog if needed
ALTER TABLE training_catalog ADD COLUMN IF NOT EXISTS provider TEXT;
ALTER TABLE training_catalog ADD COLUMN IF NOT EXISTS cost REAL DEFAULT 0;
ALTER TABLE training_catalog ADD COLUMN IF NOT EXISTS title TEXT;
ALTER TABLE training_catalog ADD COLUMN IF NOT EXISTS category TEXT;
```

---

## ✅ Verification Checklist

After deployment and migrations, test these modules:

- [ ] Compliance Tracking - Should load without `due_date` error
- [ ] Goal/OKR Review - Should load without `goal_type` error
- [ ] Budget Management - Should load without `budgets table missing` error
- [ ] Document Approval - Should load without `created_by` error
- [ ] Skill Matrix Admin - Should load without `updated_at` error
- [ ] Contract Renewal - Should load without TypeError
- [ ] Certificate Tracking - Should load without `issuing_authority` error
- [ ] Promotion Workflow - Should load without `nominated_by` error
- [ ] Team/Position Admin - Should load without `updated_at` error
- [ ] Asset Procurement - Should load without column errors
- [ ] Training Management - Should load without column errors
- [ ] Document Management - Should load without .str accessor error

---

## 🎯 Expected Result

After deployment, your health check should show:

```
📊 Health Check Results
✅ Tables OK: 32
⚠️ Missing Columns: 0
❌ Missing Tables: 0
Total Issues: 0
```

**ALL ERRORS RESOLVED!** ✅

---

## 🔍 If Issues Persist

### Check Logs
Streamlit Cloud → Your App → Manage App → Logs

### Verify Table Creation
Use the health check or run this query:
```sql
SELECT table_name FROM information_schema.tables
WHERE table_schema = 'public'
ORDER BY table_name;
```

### Common Issues

**Issue**: "Table budgets does not exist"
**Solution**: Run the manual SQL from Option C above in your Neon database

**Issue**: "Column X does not exist"
**Solution**: The fix might not be deployed yet. Check that your git push succeeded.

---

## 📞 Support

If you encounter any issues:

1. Check the Streamlit Cloud deployment logs
2. Verify all files were pushed to GitHub
3. Ensure migrations ran successfully
4. Check your Neon PostgreSQL connection

---

**Ready to deploy?** Run the git commands in Step 1 above! 🚀
