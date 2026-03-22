# Categorized Menu Structure for HR System

## Proposed Menu Categories

### 1️⃣ **Dashboard & Profile**
- 🏠 Dashboard
- 👤 My Profile
- ✅ Profile Approvals (Manager/HR)

### 2️⃣ **Employee Management**
- 👥 Employee Directory
- 📇 Employee List (HR/Manager)
- 🏢 Org Chart
- 🚀 Career Development
- 🚪 Exit Management (HR/Manager)

### 3️⃣ **Time & Attendance**
- 📅 Leave Management
  - Leave Requests
  - Leave Approvals
- ⏰ Timesheets
  - My Timesheets
  - Timesheet Approvals
- 📅 Shift Scheduling (HR/Manager)
- 🔄 Shift Swap

### 4️⃣ **Performance & Development**
- 🏅 Performance & Grades
- 📋 Appraisals
  - Self Appraisal
  - Manager Review
  - HR Review
- ⚖️ Appraisal Calibration (HR)
- 🎯 Goals & OKRs
- 📈 PIP Management
- 🎓 Training & Development
- 🎓 Certificates

### 5️⃣ **Compensation & Benefits**
- 💵 Financial Records (HR)
- 💎 Bonus Calculator (HR/Manager)
- 🏥 Medical Insurance
- 💰 Expense Claims
- 📄 Contracts (HR)
- 📄 Contract Renewal

### 6️⃣ **Recruitment & Onboarding**
- 💼 Recruitment (HR/Manager)
- 📋 Onboarding Tasks
- 🔄 Succession Planning

### 7️⃣ **Assets & Procurement**
- 💻 Asset Management (HR/Manager)
- 💼 Asset Procurement
- 💰 Budget Management

### 8️⃣ **Documents & Compliance**
- 📁 Documents
- 📋 Document Approval
- 🎓 Certificate Tracking
- 📋 Compliance Tracking

### 9️⃣ **Team Structure**
- 🏢 Org Chart
- 🏢 Teams & Positions (HR)
- 🎯 Skill Matrix (HR)
- 📇 Employee Directory

### 🔟 **Workflow & Approvals**
- 🚀 Promotions
- 🔄 Workflow Builder (HR/Manager)
- 🌳 Function Organization (HR)
- ✅ All Approvals Hub

### 1️⃣1️⃣ **Communication**
- 📢 Announcements
- 📊 Surveys
- 🔔 Notifications
- 📅 Calendar

### 1️⃣2️⃣ **Reports & Analytics**
- 📊 Reports (HR/Manager)
- 📈 Analytics Dashboard

### 1️⃣3️⃣ **Settings & Admin**
- ⚙️ Admin Panel (HR)
- 📧 Email Settings (HR)
- 📱 Mobile View

---

## Implementation Notes

- Use `st.expander()` for each category
- Categories collapse/expand independently
- Show role-based items only when applicable
- Add badge counts for pending approvals
- Use icons consistently
- Keep most frequently used categories expanded by default
