-- Complete Database Migration
-- Run this SQL script directly on your PostgreSQL database
-- It will add ALL missing columns safely

-- notifications table
ALTER TABLE notifications ADD COLUMN IF NOT EXISTS is_read BOOLEAN DEFAULT FALSE;

-- announcements table
ALTER TABLE announcements ADD COLUMN IF NOT EXISTS is_pinned BOOLEAN DEFAULT FALSE;
ALTER TABLE announcements ADD COLUMN IF NOT EXISTS status TEXT DEFAULT 'Published';
ALTER TABLE announcements ADD COLUMN IF NOT EXISTS created_by INTEGER;
ALTER TABLE announcements ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT NOW();

-- appraisals table
ALTER TABLE appraisals ADD COLUMN IF NOT EXISTS overall_rating REAL;
ALTER TABLE appraisals ADD COLUMN IF NOT EXISTS manager_rating REAL;
ALTER TABLE appraisals ADD COLUMN IF NOT EXISTS hr_rating REAL;
ALTER TABLE appraisals ADD COLUMN IF NOT EXISTS self_rating REAL;
ALTER TABLE appraisals ADD COLUMN IF NOT EXISTS comments TEXT;
ALTER TABLE appraisals ADD COLUMN IF NOT EXISTS manager_comments TEXT;
ALTER TABLE appraisals ADD COLUMN IF NOT EXISTS hr_comments TEXT;

-- insurance table
ALTER TABLE insurance ADD COLUMN IF NOT EXISTS premium_monthly REAL DEFAULT 0;
ALTER TABLE insurance ADD COLUMN IF NOT EXISTS status TEXT DEFAULT 'Active';

-- certificates table
ALTER TABLE certificates ADD COLUMN IF NOT EXISTS issuing_org TEXT;
ALTER TABLE certificates ADD COLUMN IF NOT EXISTS issue_date DATE;
ALTER TABLE certificates ADD COLUMN IF NOT EXISTS expiry_date DATE;
ALTER TABLE certificates ADD COLUMN IF NOT EXISTS status TEXT DEFAULT 'Valid';

-- job_applications table (used by recruitment)
ALTER TABLE job_applications ADD COLUMN IF NOT EXISTS status TEXT DEFAULT 'Pending';
ALTER TABLE job_applications ADD COLUMN IF NOT EXISTS applied_date TIMESTAMP DEFAULT NOW();
ALTER TABLE job_applications ADD COLUMN IF NOT EXISTS resume_path TEXT;
ALTER TABLE job_applications ADD COLUMN IF NOT EXISTS phone TEXT;
ALTER TABLE job_applications ADD COLUMN IF NOT EXISTS email TEXT;

-- employees table
ALTER TABLE employees ADD COLUMN IF NOT EXISTS status TEXT DEFAULT 'Active';
ALTER TABLE employees ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT NOW();

-- contracts table
ALTER TABLE contracts ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT NOW();
ALTER TABLE contracts ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP;

-- leave_requests table
ALTER TABLE leave_requests ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT NOW();
ALTER TABLE leave_requests ADD COLUMN IF NOT EXISTS approved_by INTEGER;
ALTER TABLE leave_requests ADD COLUMN IF NOT EXISTS approval_date TIMESTAMP;

-- expenses table
ALTER TABLE expenses ADD COLUMN IF NOT EXISTS approved_by INTEGER;
ALTER TABLE expenses ADD COLUMN IF NOT EXISTS approval_date TIMESTAMP;

-- timesheets table
ALTER TABLE timesheets ADD COLUMN IF NOT EXISTS approved_by INTEGER;
ALTER TABLE timesheets ADD COLUMN IF NOT EXISTS approval_date TIMESTAMP;

-- training_enrollments table
ALTER TABLE training_enrollments ADD COLUMN IF NOT EXISTS status TEXT DEFAULT 'Enrolled';
ALTER TABLE training_enrollments ADD COLUMN IF NOT EXISTS completion_date DATE;
ALTER TABLE training_enrollments ADD COLUMN IF NOT EXISTS score REAL;

-- goals table
ALTER TABLE goals ADD COLUMN IF NOT EXISTS actual_completion_date DATE;
ALTER TABLE goals ADD COLUMN IF NOT EXISTS final_progress INTEGER DEFAULT 0;

-- surveys table
ALTER TABLE surveys ADD COLUMN IF NOT EXISTS start_date TIMESTAMP;
ALTER TABLE surveys ADD COLUMN IF NOT EXISTS end_date TIMESTAMP;
ALTER TABLE surveys ADD COLUMN IF NOT EXISTS status TEXT DEFAULT 'Active';

-- compliance table
ALTER TABLE compliance ADD COLUMN IF NOT EXISTS verified_by INTEGER;
ALTER TABLE compliance ADD COLUMN IF NOT EXISTS verification_date TIMESTAMP;

-- Print success message
SELECT 'Migration completed successfully!' AS result;
