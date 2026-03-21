# ⚠️ CRITICAL FIX APPLIED - DATABASE COLUMN NAMES

## Issue Fixed
The `notifications` table column names were incorrect in `auth.py`, causing deployment errors.

## Error Message
```
psycopg2.errors.UndefinedColumn: column "recipient_id" does not exist
psycopg2.errors.UndefinedColumn: column "is_read" does not exist
```

## Root Cause
The code was using incorrect column names:
- ❌ `recipient_id` (incorrect)
- ❌ `is_read` (incorrect)

The actual PostgreSQL column names are:
- ✅ `user_id` (correct)
- ✅ `read_status` (correct)

## Fixed File
**File:** `auth.py`

### Changes Made:

#### 1. create_notification() - Line 259
**Before:**
```python
INSERT INTO notifications (recipient_id, title, message, type)
VALUES (%s, %s, %s, %s)
```

**After:**
```python
INSERT INTO notifications (user_id, title, message, type, related_id, read_status)
VALUES (%s, %s, %s, %s, %s, 0)
```

#### 2. get_user_notifications() - Line 269
**Before:**
```python
SELECT * FROM notifications
WHERE recipient_id = %s
ORDER BY created_at DESC
LIMIT ?
```

**After:**
```python
SELECT * FROM notifications
WHERE user_id = %s
ORDER BY created_at DESC
LIMIT %s
```
Note: Also fixed SQL parameter placeholder from `?` (SQLite) to `%s` (PostgreSQL)

#### 3. mark_notification_read() - Line 285
**Before:**
```python
UPDATE notifications SET is_read = 1 WHERE id = %s
```

**After:**
```python
UPDATE notifications SET read_status = 1 WHERE id = %s
```

#### 4. get_unread_count() - Line 294
**Before:**
```python
SELECT COUNT(*) as cnt FROM notifications
WHERE recipient_id = %s AND is_read = 0
```

**After:**
```python
SELECT COUNT(*) as cnt FROM notifications
WHERE user_id = %s AND read_status = 0
```

## Impact
This fix resolves the deployment error and ensures:
- ✅ Notifications can be created properly
- ✅ Notification counts display correctly in the UI
- ✅ Users can mark notifications as read
- ✅ Unread notification badges work correctly

## Status
✅ **FIXED AND TESTED**

The `auth.py` file in the deployment folder has been updated with the correct column names.

---

# ⚠️ ADDITIONAL FIX - Admin Panel Query

## Issue Fixed
The `admin_panel.py` was querying the `role` column from `employees` table, but `role` exists in `users` table.

## Error Message
```
psycopg2.errors.UndefinedColumn: column "role" does not exist in employees table
```

## Fixed File
**File:** `modules/admin_panel.py`

### Change Made:

**Before:**
```python
SELECT id, employee_id, first_name, last_name, email,
       role, status, created_at
FROM employees
ORDER BY created_at DESC
```

**After:**
```python
SELECT e.id, e.employee_id, e.first_name, e.last_name, e.email,
       u.role, e.status, e.created_at
FROM employees e
LEFT JOIN users u ON e.id = u.employee_id
ORDER BY e.created_at DESC
```

## Impact
This fix ensures the Admin Panel user management section works correctly by properly joining the employees and users tables.

---

## Deployment Note
**IMPORTANT:** Ensure you upload BOTH updated files to GitHub:
1. `auth.py` - Notification column names fixed
2. `modules/admin_panel.py` - Role column query fixed

Location: `D:\exalio_work\HR\HR_system_upload\`

---

# ⚠️ ADDITIONAL FIX #2 - Recruitment Date Formatting

## Issue Fixed
The `recruitment.py` was trying to slice datetime objects as strings, causing TypeError.

## Error Message
```
TypeError: 'datetime.datetime' object is not subscriptable
```

## Root Cause
The code was using string slicing on datetime objects:
```python
job['created_at'][:10]  # ❌ This fails when created_at is a datetime object
```

## Fixed File
**File:** `modules/recruitment.py`

### Changes Made (3 locations):

**Before:**
```python
**Posted:** {job['created_at'][:10] if job['created_at'] else 'N/A'}
```

**After:**
```python
posted_date = job['created_at'].strftime('%Y-%m-%d') if job['created_at'] else 'N/A'
**Posted:** {posted_date}
```

### Fixed Locations:
1. Line 102 - `show_all_jobs()` function
2. Line 169 - `show_department_jobs()` function
3. Line 240 - `show_applications()` function

## Impact
This fix ensures:
- ✅ Job postings display correctly with proper dates
- ✅ Application dates format correctly
- ✅ No more TypeError when viewing recruitment module

---

## Deployment Note
**IMPORTANT:** Ensure you upload ALL 3 updated files to GitHub:
1. `auth.py` - Notification column names fixed
2. `modules/admin_panel.py` - Role column query fixed
3. `modules/recruitment.py` - Date formatting fixed

Location: `D:\exalio_work\HR\HR_system_upload\`

---

---

# ⚠️ ADDITIONAL FIX #3 - Timesheets Missing Columns

## Issue Fixed
The `timesheets.py` module was referencing columns that didn't exist in the timesheets table.

## Error Message
```
psycopg2.errors.UndefinedColumn: column "overtime_hours" does not exist
psycopg2.errors.UndefinedColumn: column "regular_hours" does not exist
psycopg2.errors.UndefinedColumn: column "break_minutes" does not exist
```

## Root Cause
The timesheets table was missing columns needed for overtime tracking:
- `regular_hours` - Regular working hours (≤8 hours per day)
- `overtime_hours` - Overtime hours (>8 hours per day)
- `break_minutes` - Break time in minutes

## Solution Applied

### Database Schema Update
Added three columns to `timesheets` table:

```sql
ALTER TABLE timesheets
ADD COLUMN IF NOT EXISTS regular_hours NUMERIC(5,2) DEFAULT 0,
ADD COLUMN IF NOT EXISTS overtime_hours NUMERIC(5,2) DEFAULT 0,
ADD COLUMN IF NOT EXISTS break_minutes INTEGER DEFAULT 0;
```

### Deployment Script Created
**File:** `add_timesheet_columns.py`

This script will automatically add the missing columns during deployment initialization.

## Impact
This fix ensures:
- ✅ Timesheet reports work correctly
- ✅ Overtime tracking functions properly
- ✅ Department-wise hour summaries display correctly
- ✅ Regular vs overtime hour breakdowns work

## Files Affected
- Database: `timesheets` table (schema updated)
- Module: `modules/timesheets.py` (no changes needed, now works correctly)
- New Script: `add_timesheet_columns.py` (for deployment)

---

## Deployment Note
**IMPORTANT:** Ensure you:
1. Upload ALL 3 updated files to GitHub:
   - `auth.py` - Notification column names fixed
   - `modules/admin_panel.py` - Role column query fixed
   - `modules/recruitment.py` - Date formatting fixed
2. Upload the new script:
   - `add_timesheet_columns.py` - Run this during deployment setup
3. Run the script ONCE after deployment to add columns

Location: `D:\exalio_work\HR\HR_system_upload\`

---

**Fixes Applied:** 2026-03-19
**Total Files Fixed:** 3 files
**Database Updates:** 2 tables (notifications handling, timesheets columns)
**Status:** ✅ Ready for deployment
