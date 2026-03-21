"""
Workflow Management Module
Shows function categorization, role-based workflows, and workflow gaps
Accessible to HR Admin and Managers
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from database import get_db_connection
from auth import get_current_user, is_hr_admin, is_manager

# Complete HR System Function Categorization Tree
FUNCTION_TREE = {
    "🏢 Core HR Management": {
        "👥 Employee Management": {
            "functions": [
                "View Employees",
                "Add Employee",
                "Edit Employee",
                "Terminate Employee",
                "Employee Profile Management",
                "Employee Directory",
                "Organizational Chart"
            ],
            "roles": ["hr_admin", "manager"],
            "workflows": ["Onboarding", "Profile Updates", "Termination"]
        },
        "📊 Performance Management": {
            "functions": [
                "View Performance Grades",
                "Create Performance Review",
                "Update Performance Grade",
                "Performance Analytics",
                "Grade History"
            ],
            "roles": ["hr_admin", "manager"],
            "workflows": ["Annual Review", "Mid-year Review", "Probation Review"]
        },
        "📋 Appraisal System": {
            "functions": [
                "Self Appraisal",
                "Manager Review",
                "HR Review",
                "Appraisal Approval",
                "Appraisal History"
            ],
            "roles": ["employee", "manager", "hr_admin"],
            "workflows": ["Self Assessment → Manager Review → HR Review → Completion"]
        }
    },
    "💼 Workforce Operations": {
        "📅 Leave Management": {
            "functions": [
                "Request Leave",
                "View Leave Balance",
                "Approve/Reject Leave (Manager)",
                "Final Approve Leave (HR)",
                "Leave Calendar",
                "Leave Reports"
            ],
            "roles": ["employee", "manager", "hr_admin"],
            "workflows": ["Leave Request → Manager Approval → HR Approval"]
        },
        "⏰ Timesheet Management": {
            "functions": [
                "Submit Timesheet",
                "Approve Timesheet",
                "View Timesheet History",
                "Overtime Calculation",
                "Project Time Tracking"
            ],
            "roles": ["employee", "manager"],
            "workflows": ["Timesheet Entry → Manager Approval → Payroll Processing"]
        },
        "📅 Shift Scheduling": {
            "functions": [
                "View Schedule",
                "Create Shifts",
                "Request Shift Swap",
                "Approve Shift Changes"
            ],
            "roles": ["employee", "manager", "hr_admin"],
            "workflows": ["Schedule Creation → Shift Assignment → Swap Requests"]
        }
    },
    "💰 Compensation & Benefits": {
        "💵 Financial Management": {
            "functions": [
                "View Payroll",
                "Generate Payslips",
                "Financial Records",
                "Salary History",
                "Tax Documents"
            ],
            "roles": ["hr_admin"],
            "workflows": ["Payroll Calculation → Approval → Payment"]
        },
        "💎 Bonus Management": {
            "functions": [
                "Calculate Bonus",
                "Recommend Bonus",
                "Approve Bonus",
                "Track Bonus Payments"
            ],
            "roles": ["manager", "hr_admin"],
            "workflows": ["Bonus Calculation → Manager Recommendation → HR Approval → Payment"]
        },
        "🏥 Insurance Management": {
            "functions": [
                "View Insurance Plans",
                "Enroll in Insurance",
                "Update Dependents",
                "Track Premium Payments",
                "Insurance Claims"
            ],
            "roles": ["employee", "hr_admin"],
            "workflows": ["Enrollment → Verification → Activation"]
        },
        "💰 Expense Management": {
            "functions": [
                "Submit Expense Claim",
                "Attach Receipts",
                "Approve Expenses (Manager)",
                "Approve Expenses (Finance)",
                "Reimburse Expenses"
            ],
            "roles": ["employee", "manager", "hr_admin"],
            "workflows": ["Expense Submission → Manager Approval → Finance Approval → Reimbursement"]
        }
    },
    "📚 Learning & Development": {
        "🎓 Training Management": {
            "functions": [
                "View Training Catalog",
                "Enroll in Training",
                "Manager Approve Training",
                "HR Approve Training",
                "Track Completion",
                "Training Certificates"
            ],
            "roles": ["employee", "manager", "hr_admin"],
            "workflows": ["Training Request → Manager Approval → HR Approval → Enrollment → Completion"]
        },
        "🎯 Skills Matrix": {
            "functions": [
                "Manage Skills Library",
                "Assign Skills to Teams/Positions",
                "Employee Skill Assessment",
                "Skill Gap Analysis",
                "Skill Development Plans"
            ],
            "roles": ["hr_admin", "manager"],
            "workflows": ["Skill Definition → Team Assignment → Employee Assessment → Gap Analysis"]
        },
        "🚀 Career Development": {
            "functions": [
                "Create Career Plan",
                "Track Milestones",
                "Skills Assessment",
                "Succession Planning"
            ],
            "roles": ["employee", "manager", "hr_admin"],
            "workflows": ["Career Planning → Milestone Tracking → Review → Promotion"]
        }
    },
    "📄 Documents & Compliance": {
        "📄 Contract Management": {
            "functions": [
                "Create Contract",
                "View Contract",
                "Renew Contract",
                "Track Contract Expiry",
                "Contract Termination"
            ],
            "roles": ["hr_admin"],
            "workflows": ["Contract Creation → Review → Signing → Renewal/Termination"]
        },
        "🎓 Certificate Management": {
            "functions": [
                "Upload Certificate",
                "Verify Certificate",
                "Track Expiry",
                "Certificate Repository"
            ],
            "roles": ["employee", "hr_admin"],
            "workflows": ["Upload → Verification → Storage"]
        },
        "📁 Document Management": {
            "functions": [
                "Upload Documents",
                "Approve Documents",
                "Document Repository",
                "Access Control"
            ],
            "roles": ["employee", "manager", "hr_admin"],
            "workflows": ["Upload → Approval → Storage → Access"]
        },
        "⚖️ Compliance Tracking": {
            "functions": [
                "Track Compliance Requirements",
                "Submit Compliance Documents",
                "Monitor Deadlines",
                "Compliance Reports"
            ],
            "roles": ["hr_admin"],
            "workflows": ["Requirement Tracking → Document Submission → Verification → Reporting"]
        }
    },
    "💼 Talent Management": {
        "💼 Recruitment": {
            "functions": [
                "Post Job Opening",
                "Receive Applications",
                "Shortlist Candidates",
                "Schedule Interviews",
                "Make Offer",
                "Onboard New Hire"
            ],
            "roles": ["hr_admin", "manager"],
            "workflows": ["Job Posting → Application → Shortlisting → Interview → Offer → Onboarding"]
        },
        "🎯 Onboarding": {
            "functions": [
                "Create Onboarding Tasks",
                "Assign Tasks",
                "Track Completion",
                "New Hire Orientation"
            ],
            "roles": ["hr_admin", "manager"],
            "workflows": ["Task Creation → Assignment → Tracking → Completion"]
        },
        "🚪 Exit Management": {
            "functions": [
                "Resignation Submission",
                "Exit Interview",
                "IT Clearance",
                "Finance Clearance",
                "HR Clearance",
                "Final Settlement"
            ],
            "roles": ["employee", "manager", "hr_admin"],
            "workflows": ["Resignation → Exit Interview → Clearances → Final Settlement"]
        },
        "📈 PIP Management": {
            "functions": [
                "Create PIP",
                "Set Goals",
                "Track Progress",
                "Review Meetings",
                "PIP Completion"
            ],
            "roles": ["manager", "hr_admin"],
            "workflows": ["PIP Creation → Goal Setting → Progress Tracking → Reviews → Outcome"]
        }
    },
    "🔧 Configuration & Admin": {
        "🏢 Teams & Positions": {
            "functions": [
                "Create Team",
                "Edit Team",
                "Delete Team",
                "Create Position",
                "Edit Position",
                "Delete Position",
                "Assign Employees"
            ],
            "roles": ["hr_admin"],
            "workflows": ["Configuration → Assignment → Management"]
        },
        "💻 Asset Management": {
            "functions": [
                "Add Asset",
                "Assign Asset",
                "Track Asset",
                "Return Asset",
                "Asset Maintenance"
            ],
            "roles": ["hr_admin", "manager"],
            "workflows": ["Procurement → Assignment → Tracking → Return/Maintenance"]
        },
        "⚙️ System Administration": {
            "functions": [
                "User Management",
                "Role Configuration",
                "System Settings",
                "Email Integration",
                "Notifications Setup"
            ],
            "roles": ["hr_admin"],
            "workflows": ["Configuration → Testing → Deployment"]
        }
    },
    "📊 Analytics & Reporting": {
        "📊 Reports & Analytics": {
            "functions": [
                "Headcount Reports",
                "Turnover Analysis",
                "Leave Analytics",
                "Performance Reports",
                "Financial Reports",
                "Custom Reports"
            ],
            "roles": ["hr_admin", "manager"],
            "workflows": ["Data Collection → Analysis → Report Generation → Distribution"]
        },
        "🎯 Goals & OKRs": {
            "functions": [
                "Set Goals",
                "Track Progress",
                "Review Goals",
                "Goal Analytics"
            ],
            "roles": ["employee", "manager", "hr_admin"],
            "workflows": ["Goal Setting → Progress Tracking → Review → Completion"]
        },
        "📋 Surveys & Feedback": {
            "functions": [
                "Create Survey",
                "Distribute Survey",
                "Collect Responses",
                "Analyze Results"
            ],
            "roles": ["employee", "hr_admin"],
            "workflows": ["Survey Creation → Distribution → Response Collection → Analysis"]
        }
    },
    "📢 Communication": {
        "📢 Announcements": {
            "functions": [
                "Create Announcement",
                "View Announcements",
                "Target Audience",
                "Announcement Archive"
            ],
            "roles": ["hr_admin"],
            "workflows": ["Creation → Review → Publishing → Archival"]
        },
        "🔔 Notifications": {
            "functions": [
                "View Notifications",
                "Mark as Read",
                "Notification Preferences"
            ],
            "roles": ["employee", "manager", "hr_admin"],
            "workflows": ["Event Trigger → Notification → User Action"]
        },
        "📧 Email Integration": {
            "functions": [
                "Configure Email",
                "Send Email Notifications",
                "Email Templates"
            ],
            "roles": ["hr_admin"],
            "workflows": ["Configuration → Template Setup → Automated Sending"]
        }
    }
}

# Missing Workflows Identification
MISSING_WORKFLOWS = [
    {
        "workflow": "Profile Change Approval Workflow",
        "description": "Complete approval chain for employee profile changes",
        "current_state": "Partial - approval interface exists but not fully integrated",
        "required_components": [
            "Profile change request submission",
            "Manager approval step",
            "HR final approval",
            "Notification system",
            "Change history tracking"
        ],
        "priority": "High",
        "affected_modules": ["Employee Management", "Profile Manager"]
    },
    {
        "workflow": "Multi-level Expense Approval",
        "description": "Manager → Finance → Payment workflow for expenses",
        "current_state": "Partial - only manager approval implemented",
        "required_components": [
            "Finance approval step",
            "Amount-based routing (auto-approve small amounts)",
            "Receipt verification",
            "Payment processing integration",
            "Expense audit trail"
        ],
        "priority": "High",
        "affected_modules": ["Expense Management"]
    },
    {
        "workflow": "Training Approval & Enrollment",
        "description": "Complete training request to completion workflow",
        "current_state": "Basic structure exists",
        "required_components": [
            "Budget approval step",
            "Course availability check",
            "Automatic calendar integration",
            "Completion tracking",
            "Certificate upload and verification"
        ],
        "priority": "Medium",
        "affected_modules": ["Training Management"]
    },
    {
        "workflow": "Performance Review Calibration",
        "description": "Cross-team performance rating normalization",
        "current_state": "Missing",
        "required_components": [
            "Calibration session scheduling",
            "Rating distribution analysis",
            "Manager consensus workflow",
            "Final rating lock",
            "Communication to employees"
        ],
        "priority": "Medium",
        "affected_modules": ["Performance Management", "Appraisals"]
    },
    {
        "workflow": "Asset Lifecycle Management",
        "description": "Asset procurement to disposal workflow",
        "current_state": "Basic assignment tracking only",
        "required_components": [
            "Procurement request",
            "Approval workflow",
            "Maintenance scheduling",
            "Depreciation tracking",
            "Disposal workflow"
        ],
        "priority": "Low",
        "affected_modules": ["Asset Management"]
    },
    {
        "workflow": "Skill-based Team Assignment",
        "description": "Automatic team assignment based on skills",
        "current_state": "Missing - skill matrix exists but not integrated",
        "required_components": [
            "Skill gap identification",
            "Team requirement matching",
            "Automatic recommendation system",
            "Assignment approval",
            "Skills development tracking"
        ],
        "priority": "High",
        "affected_modules": ["Skills Matrix", "Teams & Positions"]
    },
    {
        "workflow": "Succession Planning Pipeline",
        "description": "Identify and develop successors for key positions",
        "current_state": "Missing",
        "required_components": [
            "Key position identification",
            "Successor nomination",
            "Development plan creation",
            "Readiness assessment",
            "Transition planning"
        ],
        "priority": "Medium",
        "affected_modules": ["Career Development", "Performance"]
    }
]


def show_workflow_management():
    """Main workflow management interface"""
    user = get_current_user()

    st.markdown("## 🔄 Workflow Management & Function Organization")
    st.markdown("Complete view of HR system functions, workflows, and role-based access")
    st.markdown("---")

    tabs = st.tabs([
        "🌳 Function Tree",
        "👤 Role-Based Workflows",
        "⚠️ Missing Workflows",
        "📊 Workflow Analytics"
    ])

    with tabs[0]:
        show_function_tree()

    with tabs[1]:
        show_role_workflows(user)

    with tabs[2]:
        show_missing_workflows()

    with tabs[3]:
        show_workflow_analytics()


def show_function_tree():
    """Display hierarchical function tree"""
    st.markdown("### 🌳 HR System Function Categorization Tree")
    st.markdown("Complete organizational structure of all system functions")
    st.markdown("---")

    for category, subcategories in FUNCTION_TREE.items():
        with st.expander(f"**{category}**", expanded=False):
            for subcat, details in subcategories.items():
                st.markdown(f"#### {subcat}")

                col1, col2 = st.columns([2, 1])

                with col1:
                    st.markdown("**Functions:**")
                    for func in details['functions']:
                        st.markdown(f"- {func}")

                with col2:
                    st.markdown("**Accessible Roles:**")
                    role_mapping = {
                        'employee': '👤 Employee',
                        'manager': '👔 Manager',
                        'hr_admin': '🔑 HR Admin'
                    }
                    for role in details['roles']:
                        st.markdown(f"- {role_mapping.get(role, role)}")

                st.markdown("**Workflows:**")
                if isinstance(details['workflows'], list):
                    for wf in details['workflows']:
                        st.markdown(f"- {wf}")

                st.markdown("---")


def show_role_workflows(user):
    """Show workflows specific to user's role"""
    st.markdown(f"### 👤 Your Role: {user['role'].upper().replace('_', ' ')}")
    st.markdown("Functions and workflows accessible to you")
    st.markdown("---")

    user_role = user['role']
    accessible_functions = {}

    # Filter functions by role
    for category, subcategories in FUNCTION_TREE.items():
        accessible_subcats = {}
        for subcat, details in subcategories.items():
            if user_role in details['roles']:
                accessible_subcats[subcat] = details

        if accessible_subcats:
            accessible_functions[category] = accessible_subcats

    # Display accessible functions
    for category, subcategories in accessible_functions.items():
        st.markdown(f"### {category}")

        for subcat, details in subcategories.items():
            with st.expander(f"**{subcat}**"):
                col1, col2 = st.columns(2)

                with col1:
                    st.markdown("**Available Functions:**")
                    for func in details['functions']:
                        st.markdown(f"✅ {func}")

                with col2:
                    st.markdown("**Workflow Steps:**")
                    for wf in details['workflows']:
                        st.markdown(f"🔄 {wf}")

    # Show workflow flowchart for specific module
    st.markdown("---")
    st.markdown("### 📊 Workflow Flowchart")

    selected_module = st.selectbox(
        "Select module to view detailed workflow:",
        ["Leave Management", "Appraisal System", "Expense Management", "Training Management", "Recruitment"]
    )

    if selected_module == "Leave Management":
        st.markdown("""
        ```
        Employee                Manager                HR Admin
           |                       |                      |
           |--- Request Leave ---->|                      |
           |                       |                      |
           |                  Review Request             |
           |                       |                      |
           |<-- Approve/Reject ----|                      |
           |                       |                      |
           |                  [If Approved]               |
           |                       |                      |
           |                       |--- Forward to HR --->|
           |                       |                      |
           |                       |                 Review Request
           |                       |                      |
           |<------------- Final Approval/Reject ---------|
           |                       |                      |
        [Update Leave Balance]     |                      |
        [Send Notification]        |                      |
        ```
        """)

    elif selected_module == "Appraisal System":
        st.markdown("""
        ```
        Employee                Manager                HR Admin
           |                       |                      |
           |-- Self Appraisal ---->|                      |
           |                       |                      |
           |                  Manager Review              |
           |                       |                      |
           |<--- Feedback ---------|                      |
           |                       |                      |
           |                       |--- Submit to HR ---->|
           |                       |                      |
           |                       |                  HR Review
           |                       |                      |
           |<------------- Final Grade & Comments --------|
           |                       |                      |
        [Performance Record Updated]                      |
        [Stored in Grade History]                         |
        ```
        """)

    elif selected_module == "Expense Management":
        st.markdown("""
        ```
        Employee                Manager              Finance/HR
           |                       |                      |
           |-- Submit Expense ---->|                      |
           |   (with receipt)      |                      |
           |                       |                      |
           |                  Review & Verify             |
           |                       |                      |
           |<-- Approve/Reject ----|                      |
           |                       |                      |
           |                  [If Approved]               |
           |                       |                      |
           |                       |--- Forward to ------>|
           |                       |    Finance           |
           |                       |                      |
           |                       |              Finance Approval
           |                       |                      |
           |<----------- Process Reimbursement ----------|
           |                       |                      |
        [Payment Made]             |                      |
        ```
        """)


def show_missing_workflows():
    """Display missing and incomplete workflows"""
    st.markdown("### ⚠️ Missing & Incomplete Workflows")
    st.markdown("Workflows that need implementation or completion")
    st.markdown("---")

    # Priority filter
    priority_filter = st.multiselect(
        "Filter by Priority",
        ["High", "Medium", "Low"],
        default=["High", "Medium", "Low"]
    )

    filtered_workflows = [wf for wf in MISSING_WORKFLOWS if wf['priority'] in priority_filter]

    for wf in filtered_workflows:
        priority_color = {
            "High": "🔴",
            "Medium": "🟡",
            "Low": "🟢"
        }

        with st.expander(f"{priority_color[wf['priority']]} **{wf['workflow']}** - Priority: {wf['priority']}"):
            col1, col2 = st.columns([2, 1])

            with col1:
                st.markdown(f"**Description:**")
                st.markdown(wf['description'])

                st.markdown(f"**Current State:**")
                st.markdown(f"_{wf['current_state']}_")

                st.markdown(f"**Required Components:**")
                for component in wf['required_components']:
                    st.markdown(f"- ⬜ {component}")

            with col2:
                st.markdown(f"**Affected Modules:**")
                for module in wf['affected_modules']:
                    st.markdown(f"- 📦 {module}")

    st.markdown("---")
    st.info("💡 **Recommendation:** Implement high-priority workflows first to ensure critical business processes are complete.")


def show_workflow_analytics():
    """Show analytics about workflow coverage"""
    st.markdown("### 📊 Workflow Analytics")

    # Calculate statistics
    total_categories = len(FUNCTION_TREE)
    total_subcategories = sum(len(subcats) for subcats in FUNCTION_TREE.values())
    total_functions = sum(
        len(details['functions'])
        for subcats in FUNCTION_TREE.values()
        for details in subcats.values()
    )

    # Display metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Function Categories", total_categories)

    with col2:
        st.metric("Sub-categories", total_subcategories)

    with col3:
        st.metric("Total Functions", total_functions)

    with col4:
        st.metric("Missing Workflows", len(MISSING_WORKFLOWS))

    st.markdown("---")

    # Workflow completion by priority
    st.markdown("### Missing Workflows by Priority")

    priority_counts = {}
    for wf in MISSING_WORKFLOWS:
        priority = wf['priority']
        priority_counts[priority] = priority_counts.get(priority, 0) + 1

    df_priority = pd.DataFrame([
        {"Priority": "🔴 High", "Count": priority_counts.get('High', 0)},
        {"Priority": "🟡 Medium", "Count": priority_counts.get('Medium', 0)},
        {"Priority": "🟢 Low", "Count": priority_counts.get('Low', 0)}
    ])

    st.dataframe(df_priority, use_container_width=True, hide_index=True)

    st.markdown("---")

    # Function distribution by role
    st.markdown("### Function Access by Role")

    role_access = {'employee': 0, 'manager': 0, 'hr_admin': 0}

    for subcats in FUNCTION_TREE.values():
        for details in subcats.values():
            for role in details['roles']:
                role_access[role] += len(details['functions'])

    df_roles = pd.DataFrame([
        {"Role": "👤 Employee", "Accessible Functions": role_access['employee']},
        {"Role": "👔 Manager", "Accessible Functions": role_access['manager']},
        {"Role": "🔑 HR Admin", "Accessible Functions": role_access['hr_admin']}
    ])

    st.dataframe(df_roles, use_container_width=True, hide_index=True)
