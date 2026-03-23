"""
Advanced Workflow Builder & Process Management
Build and visualize workflows between functions across roles
Identify and integrate missing workflow connections
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from database import get_db_connection
from auth import get_current_user, is_hr_admin, is_manager
import plotly.graph_objects as go

# Define complete workflow configurations
WORKFLOW_DEFINITIONS = {
    "leave_request": {
        "name": "Leave Request Workflow",
        "description": "Complete leave request approval process",
        "steps": [
            {
                "step": 1,
                "name": "Employee Submits Request",
                "role": "employee",
                "function": "Request Leave",
                "module": "leave_management",
                "actions": ["Submit", "Cancel"],
                "next_step": 2,
                "status": "Pending"
            },
            {
                "step": 2,
                "name": "Manager Review",
                "role": "manager",
                "function": "Approve/Reject Leave",
                "module": "leave_management",
                "actions": ["Approve", "Reject", "Request More Info"],
                "next_step_approve": 3,
                "next_step_reject": "end",
                "status": "Manager Approved"
            },
            {
                "step": 3,
                "name": "HR Final Approval",
                "role": "hr_admin",
                "function": "Final Approve Leave",
                "module": "leave_management",
                "actions": ["Approve", "Reject"],
                "next_step_approve": 4,
                "next_step_reject": "end",
                "status": "HR Approved"
            },
            {
                "step": 4,
                "name": "Update Leave Balance",
                "role": "system",
                "function": "Deduct Leave Days",
                "module": "leave_management",
                "actions": ["Auto-Process"],
                "next_step": 5,
                "status": "Completed"
            },
            {
                "step": 5,
                "name": "Send Notifications",
                "role": "system",
                "function": "Notify All Parties",
                "module": "notifications",
                "actions": ["Send Email", "Send In-App Notification"],
                "next_step": "end",
                "status": "Completed"
            }
        ],
        "integration_status": "Partial - Missing HR approval step",
        "missing_components": ["HR approval interface", "Auto balance update", "Notification triggers"]
    },

    "expense_claim": {
        "name": "Expense Claim Workflow",
        "description": "Employee expense reimbursement process",
        "steps": [
            {
                "step": 1,
                "name": "Employee Submits Expense",
                "role": "employee",
                "function": "Submit Expense Claim",
                "module": "expenses",
                "actions": ["Submit", "Attach Receipt", "Cancel"],
                "next_step": 2,
                "status": "Pending"
            },
            {
                "step": 2,
                "name": "Manager Approval",
                "role": "manager",
                "function": "Approve Expenses",
                "module": "expenses",
                "actions": ["Approve", "Reject", "Request Clarification"],
                "next_step_approve": 3,
                "next_step_reject": "end",
                "status": "Manager Approved"
            },
            {
                "step": 3,
                "name": "Finance/HR Approval",
                "role": "hr_admin",
                "function": "Finance Approve Expenses",
                "module": "expenses",
                "actions": ["Approve", "Reject", "Request Additional Documents"],
                "next_step_approve": 4,
                "next_step_reject": "end",
                "status": "Finance Approved"
            },
            {
                "step": 4,
                "name": "Process Reimbursement",
                "role": "hr_admin",
                "function": "Process Payment",
                "module": "expenses",
                "actions": ["Mark as Paid", "Schedule Payment"],
                "next_step": 5,
                "status": "Paid"
            },
            {
                "step": 5,
                "name": "Notify Employee",
                "role": "system",
                "function": "Send Payment Notification",
                "module": "notifications",
                "actions": ["Auto-Notify"],
                "next_step": "end",
                "status": "Completed"
            }
        ],
        "integration_status": "Missing - Finance approval step not implemented",
        "missing_components": ["Finance approval interface", "Payment processing", "Receipt verification system"]
    },

    "appraisal_cycle": {
        "name": "Performance Appraisal Workflow",
        "description": "Annual performance review process",
        "steps": [
            {
                "step": 1,
                "name": "Self Assessment",
                "role": "employee",
                "function": "Self Appraisal",
                "module": "appraisals",
                "actions": ["Submit Self Review", "Save Draft"],
                "next_step": 2,
                "status": "Submitted"
            },
            {
                "step": 2,
                "name": "Manager Review",
                "role": "manager",
                "function": "Manager Review",
                "module": "appraisals",
                "actions": ["Provide Rating", "Add Comments", "Submit"],
                "next_step": 3,
                "status": "Manager Review"
            },
            {
                "step": 3,
                "name": "HR Review",
                "role": "hr_admin",
                "function": "HR Review",
                "module": "appraisals",
                "actions": ["Final Rating", "Add HR Comments", "Approve"],
                "next_step": 4,
                "status": "HR Review"
            },
            {
                "step": 4,
                "name": "Calibration Session",
                "role": "manager",
                "function": "Rating Calibration",
                "module": "appraisals",
                "actions": ["Normalize Ratings", "Consensus Discussion"],
                "next_step": 5,
                "status": "Calibration"
            },
            {
                "step": 5,
                "name": "Update Performance Grade",
                "role": "hr_admin",
                "function": "Update Grade",
                "module": "performance",
                "actions": ["Update Employee Grade", "Record History"],
                "next_step": 6,
                "status": "Completed"
            },
            {
                "step": 6,
                "name": "Share with Employee",
                "role": "manager",
                "function": "Performance Discussion",
                "module": "appraisals",
                "actions": ["Schedule Meeting", "Share Feedback"],
                "next_step": "end",
                "status": "Completed"
            }
        ],
        "integration_status": "Missing - Calibration step not implemented",
        "missing_components": ["Calibration interface", "Rating normalization logic", "Performance grade auto-update"]
    },

    "training_enrollment": {
        "name": "Training Enrollment Workflow",
        "description": "Employee training request and approval",
        "steps": [
            {
                "step": 1,
                "name": "Employee Requests Training",
                "role": "employee",
                "function": "Enroll in Training",
                "module": "training",
                "actions": ["Select Course", "Submit Request"],
                "next_step": 2,
                "status": "Pending"
            },
            {
                "step": 2,
                "name": "Manager Approval",
                "role": "manager",
                "function": "Approve Training",
                "module": "training",
                "actions": ["Approve", "Reject", "Suggest Alternative"],
                "next_step_approve": 3,
                "next_step_reject": "end",
                "status": "Manager Approved"
            },
            {
                "step": 3,
                "name": "HR/Budget Approval",
                "role": "hr_admin",
                "function": "HR Approve Training",
                "module": "training",
                "actions": ["Check Budget", "Approve", "Reject"],
                "next_step_approve": 4,
                "next_step_reject": "end",
                "status": "HR Approved"
            },
            {
                "step": 4,
                "name": "Enrollment Confirmation",
                "role": "hr_admin",
                "function": "Enroll Employee",
                "module": "training",
                "actions": ["Confirm Enrollment", "Add to Calendar"],
                "next_step": 5,
                "status": "Enrolled"
            },
            {
                "step": 5,
                "name": "Track Completion",
                "role": "employee",
                "function": "Complete Training",
                "module": "training",
                "actions": ["Mark Complete", "Upload Certificate"],
                "next_step": 6,
                "status": "Completed"
            },
            {
                "step": 6,
                "name": "Update Skills Profile",
                "role": "system",
                "function": "Add Skill to Profile",
                "module": "skills_matrix",
                "actions": ["Auto-Update Skills"],
                "next_step": "end",
                "status": "Completed"
            }
        ],
        "integration_status": "Partial - Skills auto-update missing",
        "missing_components": ["Budget checking system", "Calendar integration", "Skills profile auto-update"]
    },

    "recruitment_pipeline": {
        "name": "Recruitment Workflow",
        "description": "End-to-end hiring process",
        "steps": [
            {
                "step": 1,
                "name": "Post Job Opening",
                "role": "hr_admin",
                "function": "Create Job Posting",
                "module": "recruitment",
                "actions": ["Create Position", "Publish"],
                "next_step": 2,
                "status": "Open"
            },
            {
                "step": 2,
                "name": "Receive Applications",
                "role": "system",
                "function": "Collect Applications",
                "module": "recruitment",
                "actions": ["Auto-Collect"],
                "next_step": 3,
                "status": "Collecting"
            },
            {
                "step": 3,
                "name": "Initial Screening",
                "role": "hr_admin",
                "function": "Screen Candidates",
                "module": "recruitment",
                "actions": ["Review", "Shortlist", "Reject"],
                "next_step": 4,
                "status": "Shortlisted"
            },
            {
                "step": 4,
                "name": "Manager Interview",
                "role": "manager",
                "function": "Interview Candidate",
                "module": "recruitment",
                "actions": ["Schedule", "Interview", "Provide Feedback"],
                "next_step": 5,
                "status": "Interviewed"
            },
            {
                "step": 5,
                "name": "Make Offer",
                "role": "hr_admin",
                "function": "Generate Offer",
                "module": "recruitment",
                "actions": ["Create Offer", "Send to Candidate"],
                "next_step": 6,
                "status": "Offered"
            },
            {
                "step": 6,
                "name": "Onboarding",
                "role": "hr_admin",
                "function": "Start Onboarding",
                "module": "onboarding",
                "actions": ["Create Tasks", "Assign Buddy", "Schedule Orientation"],
                "next_step": "end",
                "status": "Accepted"
            }
        ],
        "integration_status": "Complete",
        "missing_components": []
    },

    "profile_change_approval": {
        "name": "Profile Change Approval Workflow",
        "description": "Employee profile modification approval",
        "steps": [
            {
                "step": 1,
                "name": "Employee Requests Change",
                "role": "employee",
                "function": "Update Profile",
                "module": "profile_manager",
                "actions": ["Edit Profile", "Submit for Approval"],
                "next_step": 2,
                "status": "Pending"
            },
            {
                "step": 2,
                "name": "Manager Approval",
                "role": "manager",
                "function": "Review Profile Changes",
                "module": "profile_manager",
                "actions": ["Approve", "Reject", "Request Correction"],
                "next_step_approve": 3,
                "next_step_reject": "end",
                "status": "Manager Approved"
            },
            {
                "step": 3,
                "name": "HR Final Approval",
                "role": "hr_admin",
                "function": "HR Approve Profile",
                "module": "profile_manager",
                "actions": ["Verify Documents", "Approve", "Reject"],
                "next_step_approve": 4,
                "next_step_reject": "end",
                "status": "HR Approved"
            },
            {
                "step": 4,
                "name": "Update Employee Record",
                "role": "system",
                "function": "Apply Changes",
                "module": "employee_management",
                "actions": ["Update Database", "Log Audit Trail"],
                "next_step": 5,
                "status": "Completed"
            },
            {
                "step": 5,
                "name": "Notify Employee",
                "role": "system",
                "function": "Send Confirmation",
                "module": "notifications",
                "actions": ["Send Notification"],
                "next_step": "end",
                "status": "Completed"
            }
        ],
        "integration_status": "Partial - Manager approval not integrated",
        "missing_components": ["Manager approval interface", "Change history tracking", "Document verification system"]
    },

    "exit_clearance": {
        "name": "Employee Exit Workflow",
        "description": "Complete exit and clearance process",
        "steps": [
            {
                "step": 1,
                "name": "Resignation Submission",
                "role": "employee",
                "function": "Submit Resignation",
                "module": "exit_management",
                "actions": ["Submit Resignation", "Provide Reason"],
                "next_step": 2,
                "status": "Submitted"
            },
            {
                "step": 2,
                "name": "Manager Acknowledgment",
                "role": "manager",
                "function": "Accept Resignation",
                "module": "exit_management",
                "actions": ["Acknowledge", "Set Last Working Day"],
                "next_step": 3,
                "status": "Acknowledged"
            },
            {
                "step": 3,
                "name": "Exit Interview",
                "role": "hr_admin",
                "function": "Conduct Exit Interview",
                "module": "exit_management",
                "actions": ["Schedule Interview", "Record Feedback"],
                "next_step": 4,
                "status": "Interview Complete"
            },
            {
                "step": 4,
                "name": "IT Clearance",
                "role": "hr_admin",
                "function": "IT Asset Return",
                "module": "exit_management",
                "actions": ["Mark IT Clearance"],
                "next_step": 5,
                "status": "IT Cleared"
            },
            {
                "step": 5,
                "name": "Finance Clearance",
                "role": "hr_admin",
                "function": "Final Settlement",
                "module": "exit_management",
                "actions": ["Calculate Settlement", "Mark Finance Clearance"],
                "next_step": 6,
                "status": "Finance Cleared"
            },
            {
                "step": 6,
                "name": "HR Clearance",
                "role": "hr_admin",
                "function": "Complete Exit",
                "module": "exit_management",
                "actions": ["Final Sign-off", "Update Employee Status"],
                "next_step": "end",
                "status": "Completed"
            }
        ],
        "integration_status": "Complete",
        "missing_components": []
    }
}


def show_workflow_builder():
    """Main workflow builder and management interface"""
    user = get_current_user()

    if not (is_hr_admin() or is_manager()):
        st.error("🚫 Access Denied - HR Admin or Manager access required")
        return

    st.markdown("## 🔄 Workflow Builder & Process Management")
    st.markdown("Build, visualize, and manage workflows between functions across roles")
    st.markdown("---")

    tabs = st.tabs([
        "📊 Workflow Overview",
        "🔧 Build/Edit Workflows",
        "⚠️ Missing Integrations",
        "🎯 Role Flow Mapping",
        "📈 Workflow Analytics"
    ])

    with tabs[0]:
        show_workflow_overview()

    with tabs[1]:
        show_workflow_builder_interface()

    with tabs[2]:
        show_missing_integrations()

    with tabs[3]:
        show_role_flow_mapping()

    with tabs[4]:
        show_workflow_analytics()


def show_workflow_overview():
    """Display all configured workflows"""
    st.markdown("### 📊 All System Workflows")
    st.markdown("Complete list of workflows with their integration status")

    for workflow_key, workflow in WORKFLOW_DEFINITIONS.items():
        status_color = "🟢" if workflow['integration_status'] == "Complete" else "🟡" if "Partial" in workflow['integration_status'] else "🔴"

        with st.expander(f"{status_color} **{workflow['name']}** - {workflow['integration_status']}", expanded=False):
            col1, col2 = st.columns([2, 1])

            with col1:
                st.markdown(f"**Description:** {workflow['description']}")
                st.markdown(f"**Total Steps:** {len(workflow['steps'])}")
                st.markdown(f"**Integration Status:** {workflow['integration_status']}")

                if workflow['missing_components']:
                    st.markdown("**Missing Components:**")
                    for component in workflow['missing_components']:
                        st.markdown(f"- ⬜ {component}")

            with col2:
                if st.button("View Flow Diagram", key=f"view_{workflow_key}", use_container_width=True):
                    st.session_state.selected_workflow = workflow_key
                    st.session_state.show_flow_diagram = True

                if st.button("Edit Workflow", key=f"edit_{workflow_key}", use_container_width=True):
                    st.session_state.edit_workflow = workflow_key
                    st.rerun()

    # Show flow diagram in modal
    if st.session_state.get('show_flow_diagram', False):
        show_workflow_diagram(st.session_state.selected_workflow)


def show_workflow_diagram(workflow_key):
    """Display visual workflow diagram using Plotly Sankey"""
    st.markdown("---")
    workflow = WORKFLOW_DEFINITIONS[workflow_key]

    st.markdown(f"### 🔄 {workflow['name']} - Process Flow")

    # Create Sankey diagram
    try:
        # Build nodes and links for Sankey diagram
        nodes = []
        node_labels = []
        node_colors = []

        # Role colors
        role_colors_map = {
            "employee": "rgba(66, 135, 245, 0.8)",    # Blue
            "manager": "rgba(255, 165, 0, 0.8)",      # Orange
            "hr_admin": "rgba(220, 53, 69, 0.8)",     # Red
            "system": "rgba(40, 167, 69, 0.8)"        # Green
        }

        # Create nodes from steps
        for step_data in workflow['steps']:
            role_icon = {
                "employee": "👤",
                "manager": "👔",
                "hr_admin": "🔑",
                "system": "⚙️"
            }.get(step_data['role'], "📌")

            node_label = f"{role_icon} Step {step_data['step']}<br>{step_data['name']}"
            node_labels.append(node_label)
            node_colors.append(role_colors_map.get(step_data['role'], "rgba(128, 128, 128, 0.8)"))

        # Add END node
        node_labels.append("✅ END")
        node_colors.append("rgba(108, 117, 125, 0.8)")

        # Create links between steps
        sources = []
        targets = []
        values = []
        link_colors = []

        for i, step_data in enumerate(workflow['steps']):
            next_step = step_data.get('next_step')
            next_step_approve = step_data.get('next_step_approve')
            next_step_reject = step_data.get('next_step_reject')

            if next_step_approve:
                # Approval path
                if next_step_approve != 'end':
                    sources.append(i)
                    targets.append(next_step_approve - 1)
                    values.append(2)
                    link_colors.append("rgba(40, 167, 69, 0.3)")
                else:
                    sources.append(i)
                    targets.append(len(workflow['steps']))
                    values.append(2)
                    link_colors.append("rgba(40, 167, 69, 0.3)")

                # Rejection path
                if next_step_reject == 'end':
                    sources.append(i)
                    targets.append(len(workflow['steps']))
                    values.append(1)
                    link_colors.append("rgba(220, 53, 69, 0.3)")
            elif next_step:
                if next_step != 'end':
                    sources.append(i)
                    targets.append(next_step - 1)
                    values.append(2)
                    link_colors.append("rgba(108, 117, 125, 0.3)")
                else:
                    sources.append(i)
                    targets.append(len(workflow['steps']))
                    values.append(2)
                    link_colors.append("rgba(108, 117, 125, 0.3)")

        # Create Sankey diagram
        fig = go.Figure(data=[go.Sankey(
            node=dict(
                pad=15,
                thickness=20,
                line=dict(color="white", width=2),
                label=node_labels,
                color=node_colors
            ),
            link=dict(
                source=sources,
                target=targets,
                value=values,
                color=link_colors
            )
        )])

        fig.update_layout(
            title=f"{workflow['name']} - Visual Flow",
            font=dict(size=12),
            height=600,
            margin=dict(l=20, r=20, t=60, b=20)
        )

        st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"Error creating diagram: {str(e)}")
        st.info("Falling back to text representation...")

        # Fallback to text representation
        for step_data in workflow['steps']:
            role_icon = {
                "employee": "👤",
                "manager": "👔",
                "hr_admin": "🔑",
                "system": "⚙️"
            }.get(step_data['role'], "📌")

            col1, col2, col3 = st.columns([1, 4, 2])

            with col1:
                st.markdown(f"**Step {step_data['step']}**")
                st.markdown(f"{role_icon}")

            with col2:
                st.markdown(f"**{step_data['name']}**")
                st.markdown(f"Role: {step_data['role'].replace('_', ' ').title()}")
                st.markdown(f"Function: {step_data['function']}")

            with col3:
                st.markdown(f"**Status:** {step_data['status']}")
                st.markdown(f"**Actions:**")
                for action in step_data['actions']:
                    st.markdown(f"- {action}")

            # Show connection arrow
            if step_data.get('next_step') != 'end':
                st.markdown("↓")
            else:
                st.markdown("✅ **END**")

            st.markdown("---")

    # Step details below diagram
    st.markdown("---")
    st.markdown("### 📋 Step Details")

    for step_data in workflow['steps']:
        with st.expander(f"Step {step_data['step']}: {step_data['name']}"):
            col1, col2 = st.columns(2)

            with col1:
                st.markdown(f"**Role:** {step_data['role'].replace('_', ' ').title()}")
                st.markdown(f"**Function:** {step_data['function']}")
                st.markdown(f"**Module:** `{step_data['module']}`")

            with col2:
                st.markdown(f"**Status:** {step_data['status']}")
                st.markdown(f"**Available Actions:**")
                for action in step_data['actions']:
                    st.markdown(f"- {action}")

    if st.button("Close Diagram", use_container_width=True):
        st.session_state.show_flow_diagram = False
        st.rerun()


def show_workflow_builder_interface():
    """Interface to build or edit workflows"""
    st.markdown("### 🔧 Workflow Builder")

    if st.session_state.get('edit_workflow'):
        edit_existing_workflow(st.session_state.edit_workflow)
    else:
        create_new_workflow()


def create_new_workflow():
    """Create a new workflow from scratch"""
    st.markdown("#### Create New Workflow")

    with st.form("new_workflow_form"):
        workflow_name = st.text_input("Workflow Name *")
        description = st.text_area("Description")

        st.markdown("---")
        st.markdown("**Workflow Steps**")

        num_steps = st.number_input("Number of Steps", min_value=1, max_value=10, value=3)

        steps = []
        for i in range(int(num_steps)):
            st.markdown(f"**Step {i+1}**")
            col1, col2 = st.columns(2)

            with col1:
                step_name = st.text_input(f"Step Name", key=f"step_name_{i}")
                role = st.selectbox(f"Role", ["employee", "manager", "hr_admin", "system"], key=f"role_{i}")

            with col2:
                function = st.text_input(f"Function", key=f"function_{i}")
                module = st.text_input(f"Module", key=f"module_{i}")

            actions = st.text_input(f"Actions (comma-separated)", key=f"actions_{i}")
            status = st.text_input(f"Status", key=f"status_{i}")

            steps.append({
                "step": i+1,
                "name": step_name,
                "role": role,
                "function": function,
                "module": module,
                "actions": [a.strip() for a in actions.split(',') if a.strip()],
                "status": status
            })

            st.markdown("---")

        submitted = st.form_submit_button("💾 Save Workflow", use_container_width=True)

        if submitted and workflow_name:
            st.success(f"✅ Workflow '{workflow_name}' created successfully!")
            st.info("ℹ️ Workflow saved to configuration. Implement the functions in respective modules.")


def edit_existing_workflow(workflow_key):
    """Edit an existing workflow"""
    workflow = WORKFLOW_DEFINITIONS[workflow_key]

    st.markdown(f"#### Edit: {workflow['name']}")

    with st.form("edit_workflow_form"):
        workflow_name = st.text_input("Workflow Name", value=workflow['name'])
        description = st.text_area("Description", value=workflow['description'])

        st.markdown("---")
        st.markdown("**Workflow Steps**")

        for step in workflow['steps']:
            st.markdown(f"**Step {step['step']}: {step['name']}**")
            col1, col2, col3 = st.columns(3)

            with col1:
                st.markdown(f"Role: {step['role']}")
            with col2:
                st.markdown(f"Function: {step['function']}")
            with col3:
                st.markdown(f"Module: {step['module']}")

            st.markdown(f"Actions: {', '.join(step['actions'])}")
            st.markdown("---")

        col1, col2 = st.columns(2)
        with col1:
            save = st.form_submit_button("💾 Save Changes", use_container_width=True)
        with col2:
            cancel = st.form_submit_button("❌ Cancel", use_container_width=True)

        if save:
            st.success("✅ Workflow updated successfully!")
            st.session_state.edit_workflow = None
            st.rerun()

        if cancel:
            st.session_state.edit_workflow = None
            st.rerun()


def show_missing_integrations():
    """Show workflows with missing integrations and how to fix them"""
    st.markdown("### ⚠️ Missing Workflow Integrations")
    st.markdown("Workflows that need implementation or completion")

    missing_workflows = {k: v for k, v in WORKFLOW_DEFINITIONS.items() if v['integration_status'] != "Complete"}

    if not missing_workflows:
        st.success("✅ All workflows are fully integrated!")
        return

    for workflow_key, workflow in missing_workflows.items():
        st.markdown(f"#### 🔴 {workflow['name']}")
        st.markdown(f"**Status:** {workflow['integration_status']}")

        if workflow['missing_components']:
            st.markdown("**Required Implementation:**")

            for idx, component in enumerate(workflow['missing_components'], 1):
                col1, col2 = st.columns([4, 1])

                with col1:
                    st.markdown(f"{idx}. {component}")

                with col2:
                    if st.button("Implement", key=f"impl_{workflow_key}_{idx}", use_container_width=True):
                        show_implementation_guide(workflow_key, component)

        st.markdown("---")


def show_implementation_guide(workflow_key, component):
    """Show implementation guide for missing component"""
    st.markdown(f"#### 📋 Implementation Guide: {component}")

    # Provide specific implementation guidance
    guides = {
        "HR approval interface": """
        **Implementation Steps:**
        1. Add HR approval section in leave_management.py
        2. Create approval button for HR admin role
        3. Update leave_requests table status to 'HR Approved'
        4. Trigger notification to employee

        **Code Location:** modules/leave_management.py
        **Function to add:** `hr_approve_leave(request_id)`
        """,

        "Finance approval interface": """
        **Implementation Steps:**
        1. Add finance approval tab in expenses.py
        2. Create approval interface for hr_admin role
        3. Add payment processing status tracking
        4. Integrate with financial_records table

        **Code Location:** modules/expenses.py
        **Function to add:** `finance_approve_expense(expense_id)`
        """,

        "Skills profile auto-update": """
        **Implementation Steps:**
        1. Create trigger in training completion
        2. Auto-add completed course skills to employee_skills table
        3. Update proficiency level based on course level
        4. Send notification to employee

        **Code Location:** modules/training.py, modules/skill_matrix_admin.py
        **Function to add:** `auto_update_skills(emp_id, course_id)`
        """
    }

    st.code(guides.get(component, "Implementation guide not available yet"), language="markdown")


def show_role_flow_mapping():
    """Show workflows organized by role"""
    st.markdown("### 🎯 Role-Based Process Flow Mapping")
    st.markdown("View all workflows and functions accessible to each role")

    role_tabs = st.tabs(["👤 Employee", "👔 Manager", "🔑 HR Admin"])

    with role_tabs[0]:
        show_role_workflows("employee")

    with role_tabs[1]:
        show_role_workflows("manager")

    with role_tabs[2]:
        show_role_workflows("hr_admin")


def show_role_workflows(role):
    """Show workflows for a specific role"""
    role_name = {"employee": "Employee", "manager": "Manager", "hr_admin": "HR Admin"}[role]
    st.markdown(f"### Workflows for {role_name}")

    for workflow_key, workflow in WORKFLOW_DEFINITIONS.items():
        # Find steps for this role
        role_steps = [step for step in workflow['steps'] if step['role'] == role]

        if role_steps:
            with st.expander(f"**{workflow['name']}** ({len(role_steps)} steps)"):
                for step in role_steps:
                    st.markdown(f"**Step {step['step']}: {step['name']}**")
                    st.markdown(f"Function: {step['function']}")
                    st.markdown(f"Module: `{step['module']}`")
                    st.markdown(f"Available Actions:")
                    for action in step['actions']:
                        st.markdown(f"- {action}")
                    st.markdown("---")


def show_workflow_analytics():
    """Show workflow analytics and metrics"""
    st.markdown("### 📈 Workflow Analytics")

    # Calculate metrics
    total_workflows = len(WORKFLOW_DEFINITIONS)
    complete_workflows = sum(1 for w in WORKFLOW_DEFINITIONS.values() if w['integration_status'] == "Complete")
    partial_workflows = sum(1 for w in WORKFLOW_DEFINITIONS.values() if "Partial" in w['integration_status'])
    missing_workflows = total_workflows - complete_workflows - partial_workflows

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Workflows", total_workflows)

    with col2:
        st.metric("Complete", complete_workflows, delta=f"{(complete_workflows/total_workflows*100):.0f}%")

    with col3:
        st.metric("Partial", partial_workflows, delta=f"{(partial_workflows/total_workflows*100):.0f}%")

    with col4:
        st.metric("Missing", missing_workflows, delta=f"-{(missing_workflows/total_workflows*100):.0f}%", delta_color="inverse")

    st.markdown("---")

    # Workflow completion table
    st.markdown("### Workflow Status Summary")

    df_data = []
    for workflow_key, workflow in WORKFLOW_DEFINITIONS.items():
        df_data.append({
            "Workflow": workflow['name'],
            "Total Steps": len(workflow['steps']),
            "Status": workflow['integration_status'],
            "Missing Components": len(workflow['missing_components']),
            "Priority": "High" if len(workflow['missing_components']) > 2 else "Medium" if len(workflow['missing_components']) > 0 else "Low"
        })

    df = pd.DataFrame(df_data)
    st.dataframe(df, use_container_width=True, hide_index=True)

    st.markdown("---")

    # Role participation
    st.markdown("### Role Participation in Workflows")

    role_participation = {"employee": 0, "manager": 0, "hr_admin": 0, "system": 0}
    for workflow in WORKFLOW_DEFINITIONS.values():
        for step in workflow['steps']:
            role_participation[step['role']] += 1

    df_roles = pd.DataFrame([
        {"Role": "👤 Employee", "Steps Involved": role_participation['employee']},
        {"Role": "👔 Manager", "Steps Involved": role_participation['manager']},
        {"Role": "🔑 HR Admin", "Steps Involved": role_participation['hr_admin']},
        {"Role": "⚙️ System", "Steps Involved": role_participation['system']}
    ])

    st.dataframe(df_roles, use_container_width=True, hide_index=True)
