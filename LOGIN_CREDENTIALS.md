# 🔐 Login Credentials for Your HR System

## Default Users (From Your Existing Data)

### 1. HR Admin
```
Username: admin@exalio.com
Password: admin123
Role: HR Admin (Full Access)
```

### 2. Manager
```
Username: john.manager@exalio.com
Password: manager123
Role: Manager (Team Management)
```

### 3. Employees (All use same password)
```
Username: sarah.dev@exalio.com
Password: emp123
Role: Employee

Username: mike.chen@exalio.com
Password: emp123
Role: Employee

Username: emily.brown@exalio.com
Password: emp123
Role: Employee

Username: david.wilson@exalio.com
Password: emp123
Role: Employee

Username: lisa.anderson@exalio.com
Password: emp123
Role: Employee

Username: tom.martinez@exalio.com
Password: emp123
Role: Employee
```

---

## Employee Details

| ID | Name | Department | Position | Manager | Grade |
|----|------|------------|----------|---------|-------|
| EXL-001 | Admin HR | Human Resources | HR Director | - | A+ |
| EXL-002 | John Manager | Engineering | Engineering Manager | - | A |
| EXL-003 | Sarah Developer | Engineering | Senior Developer | John Manager | A |
| EXL-004 | Mike Chen | Engineering | Developer | John Manager | B |
| EXL-005 | Emily Brown | Marketing | Marketing Manager | Admin HR | A |
| EXL-006 | David Wilson | Finance | Financial Analyst | Admin HR | B+ |
| EXL-007 | Lisa Anderson | Engineering | Data Engineer | John Manager | B+ |
| EXL-008 | Tom Martinez | Engineering | AI Engineer | John Manager | A |

---

## Team Structure

**Engineering Team** (Manager: John Manager)
- Sarah Developer (Senior Developer) - app team
- Mike Chen (Developer) - app team
- Lisa Anderson (Data Engineer) - data team
- Tom Martinez (AI Engineer) - ai team

**Marketing** (Reports to: Admin HR)
- Emily Brown (Marketing Manager)

**Finance** (Reports to: Admin HR)
- David Wilson (Financial Analyst)

---

## Access Levels

### HR Admin (admin@exalio.com)
- ✅ Full system access
- ✅ Manage all employees
- ✅ Approve all requests
- ✅ Access all reports
- ✅ System configuration

### Manager (john.manager@exalio.com)
- ✅ View team members (4 employees)
- ✅ Approve team leave requests
- ✅ Approve team expenses
- ✅ Conduct appraisals
- ✅ View team reports
- ❌ Cannot access other departments

### Employee (all other users)
- ✅ View own profile
- ✅ Submit leave requests
- ✅ Submit expense claims
- ✅ Complete self-appraisals
- ✅ View payslips
- ❌ Cannot view other employees

---

## After First Login

**Recommended:**
1. Login as admin@exalio.com
2. Change your password in Profile settings
3. Add more employees as needed
4. Customize department structure
5. Set up company policies

---

## Password Hashes (For Reference)

These are already in the database:

- `admin123` → `240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9`
- `manager123` → `866485796cfa8d7c0cf7111640205b83076433547577511d81f8030ae99ecea5`
- `emp123` → `e03d3ec8d5035f8721f5dc64546e59ed790dbcb3b7b598fe57057ccd7b683b00`

(SHA-256 hashed)

---

**All 8 users will be created automatically when you deploy!** 🎉
