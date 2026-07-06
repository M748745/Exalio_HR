# Admin Delete Functionality - Implementation Guide

## Overview

Admin delete functionality has been added across all HR modules in the system. This feature allows HR Admin users to delete records from the database with a confirmation step to prevent accidental deletions.

## Features

### 1. **Delete Utility Module** (`modules/delete_utils.py`)

A centralized utility module that provides:

- **`render_delete_button()`**: Renders a delete button with two-click confirmation
- **`admin_delete_with_confirmation()`**: Handles deletion with audit logging
- **`cascade_delete_employee()`**: Deletes employee and all related records

### 2. **Security Features**

- **Role-Based Access**: Only HR Admin users can see and use delete buttons
- **Two-Click Confirmation**: Prevents accidental deletions
  - First click: Shows warning message
  - Second click: Performs deletion
- **Audit Logging**: All deletions are logged with user info and timestamp
- **Cascade Delete**: Employee deletion removes all related records automatically

### 3. **Modules with Delete Functionality**

Delete buttons have been added to the following modules:

#### Core HR Modules ✅
1. **Employee Management** (`modules/employee_management.py`)
   - Delete individual employees (cascade delete included)
   - Available in both card and table views

2. **Leave Management** (`modules/leave_management.py`)
   - Delete leave requests
   - Available in pending approvals and all requests views

3. **Contracts** (`modules/contracts.py`)
   - Delete employment contracts
   - Available in contract listings

4. **Appraisals** (`modules/appraisals.py`)
   - Delete performance appraisals
   - Import added ✅

5. **Financial Records** (`modules/financial.py`)
   - Delete financial/payroll records
   - Import added ✅

6. **Expenses** (`modules/expenses.py`)
   - Delete expense claims
   - Import added ✅

7. **Recruitment** (`modules/recruitment.py`)
   - Delete job postings and applications
   - Import added ✅

8. **Training** (`modules/training.py`)
   - Delete training courses and enrollments
   - Import added ✅

9. **Assets** (`modules/assets.py`)
   - Delete asset records
   - Import added ✅

#### Secondary Modules ✅
10. **Timesheets** (`modules/timesheets.py`) - Import added ✅
11. **Documents** (`modules/documents.py`) - Import added ✅
12. **Performance** (`modules/performance.py`) - Import added ✅
13. **Certificates** (`modules/certificates.py`) - Import added ✅
14. **Goals** (`modules/goals.py`) - Import added ✅
15. **Career Plans** (`modules/career_plans.py`) - Import added ✅
16. **Exit Management** (`modules/exit_management.py`) - Import added ✅
17. **Announcements** (`modules/announcements.py`) - Import added ✅
18. **Onboarding** (`modules/onboarding.py`) - Import added ✅
19. **Shift Scheduling** (`modules/shift_scheduling.py`) - Import added ✅
20. **Surveys** (`modules/surveys.py`) - Import added ✅
21. **Compliance** (`modules/compliance.py`) - Import added ✅
22. **PIP** (`modules/pip.py`) - Import added ✅
23. **Bonus** (`modules/bonus.py`) - Import added ✅
24. **Insurance** (`modules/insurance.py`) - Import added ✅

## Usage Guide

### For Developers

#### Adding Delete Button to a Module

1. **Import the utility**:
```python
from modules.delete_utils import render_delete_button
```

2. **Add delete button in your UI** (for HR Admin only):
```python
if is_hr_admin():
    record_desc = f"Record-{record['id']} - {record['name']}"
    if render_delete_button(
        table_name="your_table",
        record_id=record['id'],
        record_description=record_desc,
        button_key=f"delete_record_{record['id']}"
    ):
        st.rerun()
```

#### Example Implementation

```python
# In an expander or card view
with st.expander(f"Record: {record['name']}"):
    # Show record details
    st.write(record)

    # Action buttons
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button("✏️ Edit", key=f"edit_{record['id']}"):
            # Edit logic
            pass

    with col2:
        if st.button("👁️ View", key=f"view_{record['id']}"):
            # View logic
            pass

    with col3:
        # Other actions
        pass

    with col4:
        if is_hr_admin():
            desc = f"{record['type']}-{record['id']} - {record['name']}"
            if render_delete_button("table_name", record['id'], desc, f"del_{record['id']}"):
                st.rerun()
```

### For HR Admin Users

#### How to Delete a Record

1. **Navigate** to the relevant HR module (e.g., Employee Management, Contracts, etc.)

2. **Locate** the record you want to delete

3. **Click** the **🗑️ Delete** button
   - Button will change to **⚠️ Confirm Delete** (red/primary color)
   - A warning message appears

4. **Click again** on **⚠️ Confirm Delete** to confirm deletion
   - Record is permanently deleted
   - Success message appears
   - Audit log is created

5. **Page refreshes** automatically to show updated data

#### Important Notes

- ⚠️ **Deletions are permanent** - there is no undo functionality
- 📝 All deletions are **logged in audit_log** table
- 🔗 **Deleting an employee** will cascade delete:
  - Leave requests and balances
  - Appraisals and performance records
  - Contracts and financial records
  - Training enrollments
  - Goals, assets, expenses, timesheets
  - All related documents and notifications

## Database Tables Affected

The following tables can have records deleted by Admin:

- `employees` (cascade delete to related tables)
- `leave_requests`
- `leave_balance`
- `contracts`
- `appraisals`
- `financial_records`
- `expenses`
- `job_postings`
- `job_applications`
- `training_courses`
- `training_enrollments`
- `assets`
- `timesheets`
- `documents`
- `performance_history`
- `certificates`
- `goals`
- `career_plans`
- `exit_interviews`
- `announcements`
- `onboarding_tasks`
- `shifts`
- `surveys`
- `survey_responses`
- `compliance_records`
- `pip_plans`
- `bonuses`
- `insurance_plans`
- `insurance_enrollments`

## Security & Audit Trail

### Access Control
- Only users with `role = 'hr_admin'` can see delete buttons
- Regular employees and managers cannot delete any records
- Access checked at multiple levels (UI and function level)

### Audit Logging
Every deletion creates an audit log entry with:
- User who performed the deletion
- Timestamp
- Table name
- Record ID
- Description of deleted record
- Action type: "DELETE" or "CASCADE DELETE"

### Database Integrity
- Foreign key constraints are respected
- Cascade deletes handle related records automatically
- Transactions ensure data consistency

## Testing Checklist

To test delete functionality:

- [ ] Login as HR Admin user
- [ ] Navigate to Employee Management
- [ ] Try deleting an employee (test cascade delete)
- [ ] Navigate to Leave Management
- [ ] Try deleting a leave request
- [ ] Navigate to Contracts
- [ ] Try deleting a contract
- [ ] Check audit_log table for deletion records
- [ ] Verify records are actually removed from database
- [ ] Test that non-admin users don't see delete buttons

## Troubleshooting

### Delete Button Not Visible
- Verify you're logged in as HR Admin (role = 'hr_admin')
- Check that `is_hr_admin()` returns True
- Verify import statement exists in module

### Delete Not Working
- Check database connection
- Verify table name and ID column match
- Check for foreign key constraints
- Review error messages in Streamlit

### Accidental Deletion
- Check `audit_log` table for deletion record
- Manual database restore may be required
- Consider implementing soft deletes for critical tables

## Future Enhancements

Potential improvements to consider:

1. **Soft Delete**: Mark records as deleted instead of removing
2. **Bulk Delete**: Select multiple records for deletion
3. **Restore Functionality**: Undo recent deletions
4. **Export Before Delete**: Auto-export deleted records
5. **Advanced Permissions**: Granular delete permissions by module
6. **Delete Reason**: Require admin to provide deletion reason

## Support

For issues or questions about delete functionality:
- Review this documentation
- Check `modules/delete_utils.py` for implementation details
- Review audit logs for deletion history
- Test in development environment first

---

**Last Updated**: 2026-07-06
**Version**: 1.0
**Author**: HR System Development Team
