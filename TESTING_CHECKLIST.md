# 🧪 TESTING CHECKLIST - NEW WORKFLOWS

## Application is running at: http://localhost:8502

---

## ✅ PRE-TEST SETUP

### 1. Login Credentials
Use existing credentials or create test users:
- **HR Admin:** username: `admin`, password: (your password)
- **Manager:** username: `manager`, password: (your password)
- **Employee:** username: `employee`, password: (your password)

### 2. Test Data Required
You'll need:
- At least 1-2 employees in the system
- At least 1 team configured
- At least 1-2 skills in the skills library
- At least 1 training course in the catalog

---

## 🧪 TEST 1: TRAINING SKILLS AUTO-UPDATE

### Setup:
1. Login as **HR Admin**
2. Go to "🎯 Skill Matrix" → "Skills Library"
3. Add a skill (e.g., "Python Programming", Category: "Programming")
4. Go to "🎓 Training & Development" → "Add Course"
5. Create a course with same name or category as the skill above

### Test Steps:
1. Login as **Employee**
2. Go to "🎓 Training & Development"
3. Enroll in the Python course
4. Wait for manager/HR approval
5. Mark course as "Completed"

### Expected Results:
- ✅ Training status changes to "Completed"
- ✅ Message appears: "✅ Training marked as completed! Skills profile auto-updated!"
- ✅ Message appears: "✨ New skill added to profile: Python Programming"
- ✅ Employee receives notification about skills update
- ✅ Go to "My Profile" → "My Skills" → Python Programming skill should appear with "Intermediate" proficiency

### Verification:
```sql
-- Check employee_skills table
SELECT * FROM employee_skills WHERE emp_id = [employee_id];
-- Should show new Python skill
```

### Test Again (Proficiency Upgrade):
1. Enroll in same course again
2. Complete it
3. Expected: Proficiency upgrades from "Intermediate" → "Advanced"
4. Years of experience increases by +0.5

---

## 🧪 TEST 2: PROFILE CHANGE APPROVAL WORKFLOW

### Setup:
1. Make sure employee has a manager assigned
2. Have HR Admin account ready

### Test Steps:

#### Step 1: Employee Submits Change
1. Login as **Employee**
2. Go to "👤 My Profile Manager"
3. Click "Update Requests" tab
4. Fill form:
   - Select Field: "phone"
   - New Value: "555-123-4567"
   - Reason: "Updated contact number"
5. Click "Submit Request"

**Expected:**
- ✅ Success message: "Profile update request submitted"
- ✅ Request appears in "My Update Requests" section with status "Pending"

#### Step 2: Manager Approval
1. Logout, login as **Manager**
2. Go to "📋 Approvals" (or check notifications)
3. Should see profile update request
4. Click expander to view details
5. Add optional comments
6. Click "✅ Approve"

**Expected:**
- ✅ Status changes to "Manager Approved"
- ✅ Employee receives notification: "Profile Update - Manager Approved"
- ✅ HR receives notification: "Profile Update - HR Approval Required"

#### Step 3: HR Final Approval
1. Logout, login as **HR Admin**
2. Go to "📋 Approvals" → "Profile Approvals"
3. Should see the manager-approved request
4. Click expander to view
5. Click "✅ Approve"

**Expected:**
- ✅ Status changes to "HR Approved"
- ✅ Employee phone number automatically updated in database
- ✅ Employee receives notification: "Profile Update Approved"
- ✅ Go to employee record → phone should show new number

### Test Rejection:
1. Submit another profile change
2. Have manager or HR click "❌ Reject" with reason
3. Expected: Employee receives rejection notification with reason

---

## 🧪 TEST 3: PROMOTION WORKFLOW (MOST IMPORTANT!)

### Setup:
1. Ensure employee has:
   - Been in role for at least 1 year (or adjust test data)
   - Performance appraisal with grade B+ or higher
   - Current salary in financial_records table

### Test Steps:

#### Step 1: Check Eligibility (Employee)
1. Login as **Employee**
2. Go to "🚀 Promotions"
3. Click "Eligibility Check" tab

**Expected:**
- ✅ Shows eligibility criteria with checkmarks:
  - Minimum 1 year in role: ✅ or ❌
  - Performance rating B+ or higher: ✅ or ❌
  - No active PIP: ✅
  - No pending promotion requests: ✅
- If all ✅: "🎉 You appear eligible for promotion!"

#### Step 2: Nominate for Promotion (Manager)
1. Logout, login as **Manager**
2. Go to "🚀 Promotions"
3. Click "Nominate Employee" tab
4. Select an employee from your team
5. System automatically shows:
   - Current Position
   - Current Grade
   - Current Salary
   - Years in Role
   - Performance Rating

6. Fill proposed details:
   - **Proposed Position:** "Senior Developer" (or next level)
   - **Proposed Grade:** "A"
   - **Proposed Salary:** (auto-calculates 15% increase, can adjust)
   - **Justification:** "Consistently exceeds expectations, led 3 major projects..."
   - **Manager Recommendation:** "Strongly recommend promotion..."
   - **Effective Date:** Select future date

7. Click "📤 Submit Promotion Request"

**Expected:**
- ✅ Success message with Request ID (e.g., "PR-1")
- ✅ Balloons animation
- ✅ Employee receives notification: "Promotion Nomination"
- ✅ HR receives notification: "New Promotion Request - HR Review Required"

#### Step 3: HR Review & Approval
1. Logout, login as **HR Admin**
2. Go to "🚀 Promotions"
3. Click "Pending Approvals" tab
4. Should see the promotion request with:
   - Employee name
   - Current vs Proposed position/grade/salary
   - Salary increase percentage
   - Justification
   - Manager recommendation

5. Review details
6. Add optional comments
7. Click "✅ Approve"

**Expected:**
- ✅ Status changes from "Manager Approved" → "HR Review"
- ✅ Success message

8. Click "✅ Approve" again

**Expected:**
- ✅ Status changes from "HR Review" → "Budget Approved"

9. Click "✅ Approve" one more time

**Expected:**
- ✅ Status changes from "Budget Approved" → "Approved"
- ✅ Employee receives notification about approval

#### Step 4: Implement Promotion
1. Still as **HR Admin**
2. In the same promotion request card
3. Click "🚀 Implement" button (should now be visible)

**Expected:**
- ✅ Success message: "🎉 Promotion implemented successfully!"
- ✅ Balloons animation
- ✅ Status changes to "Implemented"
- ✅ Employee receives congratulations notification

#### Step 5: Verify Implementation
1. Go to "👥 Employee Management"
2. Find the promoted employee
3. Click to view details

**Expected:**
- ✅ Position updated to new position
- ✅ Grade updated to new grade
- ✅ Salary shows new amount in financial records

**Database Verification:**
```sql
-- Check employee record updated
SELECT position, grade FROM employees WHERE id = [emp_id];

-- Check new salary record created
SELECT base_salary, created_at FROM financial_records
WHERE emp_id = [emp_id] ORDER BY created_at DESC LIMIT 1;

-- Check promotion status
SELECT status FROM promotion_requests WHERE id = [request_id];
-- Should be 'Implemented'
```

#### Step 6: View Promotion History (Employee)
1. Logout, login as **Employee**
2. Go to "🚀 Promotions"
3. Should see promotion history with status "Implemented"

#### Step 7: View Analytics (HR)
1. Login as **HR Admin**
2. Go to "🚀 Promotions" → "Analytics" tab

**Expected:**
- ✅ Shows total promotion requests
- ✅ Shows implemented count
- ✅ Shows pending count
- ✅ Breakdown by status
- ✅ Breakdown by department

---

## 🧪 TEST 4: WORKFLOW INTEGRATION

### Test Complete Flow
Test all 3 workflows together for one employee:

1. **Training:** Employee completes training → Skills updated
2. **Profile:** Employee updates contact info → Manager → HR approves
3. **Promotion:** Manager nominates → HR approves → Implement

**Verify:**
- All notifications sent correctly
- All database updates successful
- Audit logs created for each action
- No errors in console

---

## 🧪 TEST 5: EDGE CASES & ERROR HANDLING

### Training Skills Auto-Update:
- [ ] Complete training for skill employee already has → Proficiency upgrades
- [ ] Complete training for non-existent skill → Gracefully handles
- [ ] Complete multiple trainings same day → All skills added

### Profile Change:
- [ ] Submit duplicate field change → Should handle
- [ ] Manager rejects → Employee notified correctly
- [ ] HR rejects after manager approval → Status updated correctly

### Promotion:
- [ ] Nominate ineligible employee → Shows warnings but allows submission
- [ ] Reject at HR stage → Employee notified
- [ ] Try to implement before approved → Button not visible
- [ ] Implement twice → Should not duplicate (status check)

---

## 🧪 TEST 6: NOTIFICATIONS

Check that notifications appear in:
1. Click "🔔 Notifications" in sidebar
2. Verify notifications for:
   - Training completion
   - Skills update
   - Profile change (each approval stage)
   - Promotion nomination
   - Promotion approval stages
   - Promotion implementation

---

## 🧪 TEST 7: AUDIT LOGS

As HR Admin:
1. Check audit logs (if visible in UI)
2. Verify logs created for:
   - Training completion
   - Profile changes
   - Promotion stages

---

## 📋 TESTING SUMMARY CHECKLIST

### Training Skills Auto-Update:
- [ ] Skill auto-added on training completion
- [ ] Proficiency upgraded on repeat training
- [ ] Notification sent to employee
- [ ] Shows in employee's skills profile

### Profile Change Approval:
- [ ] Employee can submit change request
- [ ] Manager receives notification
- [ ] Manager can approve/reject
- [ ] HR receives notification after manager approval
- [ ] HR can approve/reject
- [ ] Employee record updates on HR approval
- [ ] Employee receives success notification

### Promotion Workflow:
- [ ] Employee can check eligibility
- [ ] Manager can nominate employee
- [ ] System shows current details
- [ ] System calculates salary increase
- [ ] Employee receives nomination notification
- [ ] HR receives approval request
- [ ] HR can advance through stages (3 approvals)
- [ ] Implement button appears when approved
- [ ] Clicking implement updates employee record
- [ ] Position updated
- [ ] Grade updated
- [ ] Salary record created
- [ ] Status changed to "Implemented"
- [ ] Employee receives congratulations
- [ ] Promotion appears in history
- [ ] Analytics show correct counts

---

## ❌ KNOWN ISSUES TO WATCH FOR

1. **Database Syntax:** If you get errors about "AUTOINCREMENT", the old tables need SQL syntax fix (AUTOINCREMENT → SERIAL for PostgreSQL)

2. **Missing Data:** If skills don't auto-add, check:
   - Skill exists in skills table
   - Skill name or category matches course

3. **Notifications:** If notifications don't appear:
   - Check notifications table has records
   - Check user is checking their own notifications

4. **Promotion Implementation:** If employee record doesn't update:
   - Check console for SQL errors
   - Verify transaction committed

---

## 🎯 SUCCESS CRITERIA

All workflows pass if:
- ✅ No Python errors in console
- ✅ All database updates successful
- ✅ All notifications sent
- ✅ All status transitions work correctly
- ✅ UI shows success messages
- ✅ Data persists after page refresh

---

## 🐛 IF YOU FIND BUGS

Report with:
1. Which workflow (Training/Profile/Promotion)
2. What step you were on
3. What you expected
4. What actually happened
5. Any error messages
6. Screenshots if possible

---

## 📝 MANUAL TESTING NOTES

Test Date: _____________
Tester Name: _____________

| Workflow | Status | Notes |
|----------|--------|-------|
| Training Skills Auto-Update | ⬜ Pass / ⬜ Fail | |
| Profile Change Approval | ⬜ Pass / ⬜ Fail | |
| Promotion Workflow | ⬜ Pass / ⬜ Fail | |

---

**Ready to test! Open http://localhost:8502 in your browser and follow the checklist above.**
