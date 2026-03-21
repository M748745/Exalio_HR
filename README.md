# 🏢 Exalio HR System - Production Ready

A comprehensive HR management system with 32 modules, now migrated to Neon PostgreSQL for production deployment on Streamlit Cloud with full concurrent user support.

## 🌟 Features

### **32 Integrated HR Modules**

#### Core Functions (✅ All Completed)
- ✅ **Authentication System** - 3-tier role-based access (HR Admin, Manager, Employee)
- ✅ **Employee Management** - Complete employee lifecycle management
- ✅ **Role-Based Dashboard** - Customized dashboards for each role
- ✅ **Notification System** - Real-time alerts and updates
- ✅ **PostgreSQL Database** - Cloud database with 32 tables (Neon PostgreSQL)

#### All 32 HR Modules (✅ Production Ready)
1. Employee Management
2. Dashboard & Analytics
3. Grades & Performance
4. Appraisals (Multi-step workflow)
5. Career Development
6. Open Positions
7. Financial Records
8. Bonus Calculator
9. Medical Insurance
10. Contracts
11. Attendance & Leave
12. Certificates
13. HR Process Hub
14. Reports & Exports
15. Admin Panel
16. Notifications
17. Employee Portal
18. Leave Balance Tracking
19. Expense Claims
20. Payslip Generation
21. Training Management
22. Document Management
23. Exit Management
24. Timesheet Management
25. Asset Management
26. Performance Improvement Plans (PIP)
27. Onboarding Checklist
28. Goals & OKRs
29. Announcements & Policies
30. Shift Scheduling
31. Feedback & Surveys
32. Compliance Tracking

## 🎯 Role-Based Access Control

### **HR Admin** (Full System Access)
- Manage all employees and records
- Configure system settings
- Final approval on all workflows
- Access to all reports and analytics
- System-wide notifications

### **Manager** (Team Management)
- View and manage team members
- Approve leave requests, expenses, timesheets
- Conduct performance reviews
- Recommend bonuses and promotions
- Access team reports

### **Employee** (Self-Service)
- View own profile and documents
- Submit leave requests and expense claims
- Complete self-appraisals
- Apply for internal positions
- View payslips and benefits

## 🚀 Quick Start

### Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd HR_system
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Initialize database**
```bash
python database.py
```

4. **Run the application**
```bash
streamlit run app.py
```

5. **Access the portal**
Open your browser to `http://localhost:8501`

## 🔐 Demo Login Credentials

### HR Admin Access
- **Email:** admin@exalio.com
- **Password:** admin123

### Manager Access
- **Email:** john.manager@exalio.com
- **Password:** manager123

### Employee Access
- **Email:** sarah.dev@exalio.com
- **Password:** emp123

## 📊 Database Schema

The system uses Neon PostgreSQL with 32 interconnected tables (production-ready for concurrent multi-user access):

- **Authentication:** users, audit_logs
- **Core:** employees, departments
- **Performance:** grades, appraisals, career_plans, pip_records
- **Recruitment:** jobs, job_applications, onboarding_tasks
- **Compensation:** financial_records, bonuses, payslips
- **Benefits:** insurance, contracts
- **Time Off:** leave_requests, leave_balance
- **Documents:** certificates, documents
- **Operations:** expenses, timesheets, assets, shifts
- **Development:** training_catalog, training_enrollments, goals
- **Communication:** notifications, announcements, surveys
- **Exit:** exit_process
- **Compliance:** compliance

## 🔄 Workflow Examples

### Leave Request Workflow
```
Employee → Submit Leave Request
         ↓
Manager → Review & Approve/Reject
         ↓
HR Admin → Final Approval & Update Balance
```

### Appraisal Workflow
```
Employee → Complete Self-Appraisal
         ↓
Manager → Review & Rate Performance
         ↓
HR Admin → Final Review & Archive
```

### Expense Claim Workflow
```
Employee → Submit Claim + Receipt
         ↓
Manager → Approve/Reject
         ↓
Finance/HR → Process Reimbursement
```

## 🛠️ Technology Stack

- **Frontend:** Streamlit (Python web framework)
- **Database:** Neon PostgreSQL (Serverless, IPv4-compatible)
- **Database Driver:** psycopg2-binary with transaction pooling
- **Authentication:** SHA-256 password hashing
- **Data Processing:** Pandas
- **Visualization:** Plotly (for charts and graphs)
- **File Handling:** Pillow, openpyxl
- **Deployment:** Streamlit Cloud

## 📁 Project Structure

```
HR_system/
├── app.py                      # Main Streamlit application
├── database.py                 # PostgreSQL database connection & schema
├── auth.py                     # Authentication and authorization
├── init_postgres_on_cloud.py  # Auto-initialization for Streamlit Cloud
├── requirements.txt            # Python dependencies
├── README.md                   # This file
├── POSTGRESQL_MIGRATION.md    # PostgreSQL migration documentation
└── .streamlit/
    ├── config.toml             # Streamlit configuration
    └── secrets.toml            # Database connection (DO NOT commit)
```

## 🌐 Deployment to Streamlit Cloud

### Prerequisites
1. **Neon PostgreSQL Database** (Already configured)
   - Database: Neon (Serverless PostgreSQL)
   - Region: us-east-1 (AWS)
   - Connection: IPv4-only (Streamlit Cloud compatible)

### Deployment Steps

1. **Push to GitHub**
```bash
cd D:\exalio_work\HR\HR_system_upload
git init
git add .
git commit -m "Neon PostgreSQL migration complete"
git remote add origin https://github.com/YOUR_USERNAME/hr-system.git
git push -u origin main
```

2. **Deploy on Streamlit Cloud**
   - Go to [share.streamlit.io](https://share.streamlit.io)
   - Connect your GitHub account
   - Select your repository
   - Set main file path: `app.py`

3. **Configure Secrets**
   - In Streamlit Cloud dashboard, click "Settings" → "Secrets"
   - Add your Neon PostgreSQL connection:
   ```toml
   [connections.postgresql]
   url = "postgresql://neondb_owner:npg_R2UAT4WQkCMi@ep-weathered-pond-ammen3lb-pooler.c-5.us-east-1.aws.neon.tech/neondb?sslmode=require"
   ```

4. **First Deployment**
   - Database initialization runs automatically (~2-5 seconds)
   - All 32 tables created
   - 9 employees with complete data loaded
   - 9 users with hashed passwords created
   - Login with: `admin@exalio.com` / `admin123`

5. **Subsequent Loads**
   - Fast loading (~0.1 seconds)
   - No re-initialization
   - Data persists permanently

## 🔒 Security Features

- ✅ Password hashing (SHA-256)
- ✅ Role-based access control
- ✅ Session management
- ✅ Audit logging
- ✅ Data validation
- ✅ SQL injection prevention

## 📦 Pre-loaded Data

The system includes complete sample data exported from SQLite:

- **9 Employees** (EXL-001 to EXL-008, plus TEST-001)
- **9 Users** with roles (HR Admin, Manager, Employees)
- **27 Leave Balance Records** (Annual, Sick, Personal leave for all employees)
- **1 Grade Record** (Sarah's Q1 2024 performance review)
- **1 Financial Record** (Sarah's January 2024 payroll)
- **1 Leave Request** (Sarah's approved March 2026 leave)
- **2 Notifications** (Welcome messages)

See `LOGIN_CREDENTIALS.md` for complete list of all users and passwords.

## 📚 Documentation Files

- `DATA_LOADING_EXPLAINED.md` - How initialization works (loads once, not every time)
- `FINAL_DEPLOYMENT_CHECKLIST.md` - Complete deployment guide
- `LOGIN_CREDENTIALS.md` - All user credentials and team structure
- `NEON_CONNECTION_STRING.txt` - Database connection reference

## 🚀 Ready to Deploy

All files are prepared in `D:\exalio_work\HR\HR_system_upload\`

**Total Files: 37 required + 4 documentation**
- 4 core files (app.py, auth.py, database.py, init_postgres_on_cloud.py)
- 32 module files (modules/ folder)
- 1 requirements.txt

## 🔄 Migration Status

✅ **Completed:**
- SQLite to PostgreSQL migration
- SQL syntax conversion (? → %s)
- Neon PostgreSQL setup (IPv4-compatible)
- Complete data export and integration
- All 32 modules updated
- Authentication system verified
- Concurrent access enabled

## 📞 Support

### Neon Database Console:
https://console.neon.tech/

### Streamlit Cloud Dashboard:
https://share.streamlit.io/

### Documentation:
- Neon Docs: https://neon.tech/docs
- Streamlit Docs: https://docs.streamlit.io/

---

**Production-Ready HR System | Powered by Neon PostgreSQL & Streamlit** 🚀
