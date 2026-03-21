# 🚀 QUICK TEST GUIDE - 5 Minutes

## Application Running: http://localhost:8502

---

## ⚡ FASTEST WAY TO TEST (5 minutes)

### 1️⃣ TEST PROMOTIONS (2 minutes)

**Login as Manager or HR Admin:**

1. Click **"🚀 Promotions"** in sidebar
2. Click **"Nominate Employee"** tab
3. Select any employee
4. See auto-filled current details (position, grade, salary)
5. Fill proposed details:
   - Proposed Position: (choose from dropdown)
   - Proposed Grade: A
   - Proposed Salary: (auto-calculated, you can edit)
   - Justification: "Test promotion"
6. Click **"Submit"**
7. ✅ Should see: "Promotion request submitted successfully!"

**Now approve it:**
8. Click **"Pending Approvals"** tab
9. Click on the promotion request
10. Click **"✅ Approve"** (3 times to go through all stages)
11. Click **"🚀 Implement"**
12. ✅ Should see: "Promotion implemented successfully!" 🎉

**Verify:**
13. Go to **"Employee Management"**
14. Find that employee
15. Check position and grade updated!

---

### 2️⃣ TEST TRAINING SKILLS AUTO-UPDATE (1 minute)

**Login as HR Admin:**

1. Go to **"🎯 Skill Matrix"** → **"Skills Library"**
2. Click **"Add Skill"**
   - Skill Name: "Python"
   - Category: "Programming"
   - Click Save

3. Go to **"🎓 Training & Development"** → **"Add Course"**
   - Course Name: "Python Programming"
   - Category: "Programming"
   - Click Save

**Login as Employee:**

4. Go to **"🎓 Training & Development"**
5. Enroll in Python course
6. (If approval needed, approve as manager/HR first)
7. Mark as **"Complete"**
8. ✅ Should see: "Skills profile auto-updated!"
9. ✅ Should see: "New skill added: Python Programming"

**Verify:**
10. Go to **"My Profile"** → **"My Skills"**
11. Python skill should appear!

---

### 3️⃣ TEST PROFILE CHANGE APPROVAL (2 minutes)

**Login as Employee:**

1. Go to **"👤 My Profile Manager"**
2. Click **"Update Requests"** tab
3. Fill form:
   - Field: phone
   - New Value: 555-1234
   - Reason: "Test"
4. Click **"Submit Request"**
5. ✅ Should see success message

**Login as Manager:**

6. Go to **"📋 Approvals"** (or check notifications)
7. Find profile update request
8. Click **"✅ Approve"**

**Login as HR Admin:**

9. Go to **"📋 Approvals"**
10. Find the manager-approved request
11. Click **"✅ Approve"**
12. ✅ Should update employee phone automatically

**Verify:**
13. Go to **"Employee Management"**
14. Find employee
15. Phone number should be updated!

---

## ✅ QUICK CHECKS

If you see these, everything works:

**Promotions:**
- ✅ Nomination form loads
- ✅ Current details auto-fill
- ✅ Can submit request
- ✅ Can approve through stages
- ✅ Implement button appears
- ✅ Employee record updates

**Training Skills:**
- ✅ Can complete training
- ✅ Success message shows
- ✅ Skill appears in employee profile

**Profile Changes:**
- ✅ Can submit request
- ✅ Manager can approve
- ✅ HR can approve
- ✅ Employee data updates

---

## 🎯 ONE-CLICK TEST

**Want to test everything at once?**

1. Login as **HR Admin**
2. Pick one employee
3. Do all three:
   - Nominate for promotion → Approve → Implement
   - Add skill → Create training → Employee completes → Skill auto-adds
   - Employee submits profile change → Approve as manager → Approve as HR

If all three work, you're good! ✅

---

## 🐛 Common Issues

**"No employees to nominate"**
- Create an employee first in Employee Management

**"Skill didn't auto-add"**
- Make sure skill name or category matches training course name

**"Can't approve promotion"**
- Make sure you're logged in as Manager/HR
- Check the status matches your role (Pending → Manager, Manager Approved → HR)

**"Database error"**
- Check console for error details
- Database tables might not be created (old tables have syntax issues)

---

## 📱 NAVIGATION QUICK REFERENCE

**New Features:**
- Sidebar → **🚀 Promotions** (NEW!)
- Sidebar → **🔄 Workflow Builder** (shows all workflows)
- Sidebar → **🌳 Function Organization** (shows function tree)

**Testing Workflows:**
- **Promotions:** 🚀 Promotions
- **Training Skills:** 🎓 Training & Development
- **Profile Changes:** 👤 My Profile Manager
- **Approvals:** 📋 Approvals

---

**Ready! Open http://localhost:8502 and test!** 🚀
