#!/usr/bin/env python3
"""
Comprehensive Database Schema Audit
Compares all SQL queries in modules against actual database schema
"""

import re
import os
from pathlib import Path

# Define actual database schema (from database.py)
SCHEMA = {
    'employees': ['id', 'employee_id', 'first_name', 'last_name', 'email', 'phone', 'department',
                  'position', 'hire_date', 'status', 'salary', 'grade', 'team_tag', 'manager_id',
                  'created_at', 'team_id', 'position_id'],
    'users': ['id', 'employee_id', 'username', 'password', 'role', 'created_at'],
    'grades': ['id', 'emp_id', 'period', 'overall_grade', 'score', 'performance', 'technical',
               'teamwork', 'leadership', 'comments', 'evaluated_by', 'created_at', 'updated_at'],
    'appraisals': ['id', 'emp_id', 'period', 'type', 'status', 'self_rating', 'self_comments',
                   'manager_rating', 'manager_comments', 'hr_rating', 'hr_comments', 'reviewer_id',
                   'due_date', 'submitted_date', 'manager_review_date', 'hr_review_date',
                   'created_at', 'updated_at'],
    'career_plans': ['id', 'emp_id', 'current_level', 'target_level', 'timeline', 'skills_required',
                     'milestones', 'status', 'created_by', 'created_at', 'updated_at'],
    'jobs': ['id', 'title', 'department', 'job_type', 'location', 'description', 'requirements',
             'salary_range', 'status', 'posted_by', 'posted_date', 'closing_date', 'created_at'],
    'job_applications': ['id', 'job_id', 'emp_id', 'cover_letter', 'status', 'applied_date',
                         'reviewed_by', 'review_date', 'notes'],
    'financial_records': ['id', 'emp_id', 'base_salary', 'allowances', 'bonus', 'deductions',
                          'net_pay', 'currency', 'payment_date', 'period', 'created_at'],
    'bonuses': ['id', 'emp_id', 'bonus_type', 'amount', 'reason', 'approved_by', 'status', 'created_at'],
    'payslips': ['id', 'emp_id', 'month', 'year', 'basic_salary', 'allowances', 'deductions',
                 'net_salary', 'created_at'],
    'leave_requests': ['id', 'emp_id', 'leave_type', 'start_date', 'end_date', 'days', 'reason',
                       'status', 'approved_by', 'created_at'],
    'leave_balance': ['id', 'emp_id', 'year', 'annual_leave', 'sick_leave', 'casual_leave',
                      'used_annual', 'used_sick', 'used_casual'],
    'timesheets': ['id', 'emp_id', 'date', 'hours_worked', 'overtime_hours', 'regular_hours',
                   'project', 'task', 'status', 'approved_by', 'notes', 'created_at'],
    'shifts': ['id', 'emp_id', 'shift_date', 'shift_type', 'start_time', 'end_time', 'status', 'created_at'],
    'expenses': ['id', 'emp_id', 'category', 'amount', 'description', 'expense_date', 'status',
                 'receipt_path', 'approved_by', 'created_at'],
    'documents': ['id', 'emp_id', 'document_type', 'document_name', 'file_path', 'issue_date',
                  'expiry_date', 'status', 'approved_by', 'created_at', 'version', 'approval_status',
                  'approval_date', 'review_comments', 'effective_date', 'requires_manager_approval',
                  'auto_publish_on_approval', 'approval_notes', 'download_count', 'archived_date',
                  'content', 'description'],
    'exit_process': ['id', 'emp_id', 'resignation_date', 'last_working_day', 'reason',
                     'exit_interview_status', 'exit_interview_notes', 'clearance_status',
                     'final_settlement', 'created_at'],
    'assets': ['id', 'asset_type', 'asset_name', 'asset_tag', 'assigned_to', 'assigned_date',
               'return_date', 'condition', 'value', 'purchase_date', 'warranty_expiry', 'status',
               'notes', 'created_at'],
    'asset_requests': ['id', 'emp_id', 'asset_type', 'justification', 'priority', 'status',
                       'requested_date', 'approved_by', 'approval_date', 'notes', 'created_at'],
    'pips': ['id', 'emp_id', 'start_date', 'end_date', 'reason', 'goals', 'status', 'created_by',
             'created_at'],
    'pip_progress': ['id', 'pip_id', 'review_date', 'progress_notes', 'status', 'reviewed_by',
                     'created_at'],
    'certificates': ['id', 'emp_id', 'certificate_name', 'issuing_org', 'issue_date', 'expiry_date',
                     'file_path', 'status', 'verified_by', 'created_at'],
    'training_catalog': ['id', 'course_name', 'title', 'category', 'provider', 'description',
                         'duration', 'cost', 'status', 'created_at'],
    'training_enrollments': ['id', 'emp_id', 'course_id', 'enrollment_date', 'completion_date',
                             'status', 'score', 'feedback', 'created_at'],
    'audit_logs': ['id', 'user_id', 'action', 'table_name', 'record_id', 'old_values', 'new_values',
                   'ip_address', 'created_at'],
    'teams': ['id', 'team_name', 'department', 'team_lead_id', 'description', 'status', 'created_at'],
    'positions': ['id', 'position_name', 'team_id', 'level', 'description', 'status', 'created_at',
                  'updated_at'],
    'skills': ['id', 'skill_name', 'category', 'description', 'created_at', 'updated_at'],
    'team_skills': ['id', 'team_id', 'skill_id', 'position_id', 'required_level', 'priority', 'created_at'],
    'employee_skills': ['id', 'emp_id', 'skill_id', 'proficiency_level', 'years_experience',
                        'certified', 'last_used', 'verified_by', 'created_at'],
    'notifications': ['id', 'recipient_id', 'title', 'message', 'type', 'is_read', 'created_at'],
    'announcements': ['id', 'title', 'content', 'announcement_type', 'priority', 'target_audience',
                      'status', 'published_by', 'published_date', 'expiry_date', 'created_at'],
    'surveys': ['id', 'title', 'description', 'survey_type', 'status', 'created_by', 'start_date',
                'end_date', 'anonymous', 'created_at'],
    'survey_questions': ['id', 'survey_id', 'question_text', 'question_type', 'options', 'required',
                         'order_num'],
    'survey_responses': ['id', 'survey_id', 'emp_id', 'submitted_at'],
    'survey_answers': ['id', 'response_id', 'question_id', 'answer_text'],
    'contracts': ['id', 'emp_id', 'contract_type', 'start_date', 'end_date', 'terms', 'status',
                  'renewal_status', 'created_at'],
    'insurance_plans': ['id', 'plan_name', 'provider', 'coverage_type', 'premium_employee',
                        'premium_employer', 'coverage_amount', 'description', 'status', 'created_at'],
    'insurance_enrollments': ['id', 'emp_id', 'plan_id', 'enrollment_date', 'coverage_start',
                              'coverage_end', 'status', 'beneficiary_name', 'beneficiary_relation',
                              'created_at'],
    'goals': ['id', 'emp_id', 'goal_type', 'goal_title', 'description', 'key_results', 'target_date',
              'status', 'progress', 'weight', 'review_period', 'created_by', 'created_at', 'updated_at'],
    'promotion_requests': ['id', 'emp_id', 'current_position', 'proposed_position', 'current_grade',
                           'proposed_grade', 'justification', 'requested_by', 'status', 'reviewed_by',
                           'review_date', 'notes', 'effective_date', 'created_at'],
    'succession_plans': ['id', 'position_id', 'successor_id', 'readiness_level', 'development_plan',
                         'target_date', 'status', 'created_by', 'created_at'],
    'calibration_sessions': ['id', 'session_name', 'session_date', 'participants', 'status',
                             'notes', 'created_by', 'created_at'],
    'calibration_session_ratings': ['id', 'session_id', 'appraisal_id', 'original_rating',
                                     'calibrated_rating', 'notes'],
    'shift_templates': ['id', 'shift_name', 'shift_type', 'start_time', 'end_time', 'department',
                        'description', 'status', 'created_at', 'updated_at'],
    'shift_schedules': ['id', 'emp_id', 'template_id', 'schedule_date', 'start_time', 'end_time',
                        'status', 'notes', 'created_by', 'created_at'],
    'shift_swaps': ['id', 'requester_id', 'requested_shift_id', 'target_emp_id', 'target_shift_id',
                    'reason', 'status', 'approved_by', 'created_at'],
    'compliance_requirements': ['id', 'requirement_name', 'requirement_type', 'description', 'department',
                                'responsible_party', 'frequency', 'last_review_date', 'next_review_date',
                                'status', 'evidence_file_path', 'notes', 'created_by', 'created_at',
                                'updated_at'],
    'onboarding': ['id', 'emp_id', 'start_date', 'buddy_id', 'orientation_date', 'it_setup',
                   'workspace_setup', 'system_access', 'email_setup', 'team_introduction',
                   'policy_review', 'training_scheduled', 'status', 'completion_date', 'notes',
                   'created_by', 'created_at', 'updated_at'],
    'onboarding_tasks': ['id', 'emp_id', 'task_name', 'task_type', 'description', 'due_date',
                         'status', 'assigned_to', 'completed_date', 'notes', 'created_at'],
    'budgets': ['id', 'department', 'fiscal_year', 'period_month', 'amount', 'category', 'notes',
                'status', 'created_by', 'created_at', 'updated_at'],
    'pip_records': ['id', 'emp_id', 'start_date', 'end_date', 'reason', 'goals', 'status',
                    'created_by', 'created_at'],
    'compliance': ['id', 'requirement_name', 'description', 'due_date', 'status', 'assigned_to',
                   'created_at'],
    'document_history': ['id', 'document_id', 'version', 'changed_by', 'change_description',
                         'changed_at'],
}

def find_column_references(file_path):
    """Find all column references in SQL queries"""
    issues = []

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
        lines = content.split('\n')

    # Find SELECT statements
    select_pattern = r'SELECT\s+(.*?)\s+FROM\s+(\w+)'
    for match in re.finditer(select_pattern, content, re.IGNORECASE | re.DOTALL):
        columns_str = match.group(1)
        table = match.group(2)

        if table in SCHEMA:
            # Extract column names from SELECT
            if '*' not in columns_str:
                # Parse individual columns
                for col in re.findall(r'(\w+)\.(\w+)', columns_str):
                    table_alias, col_name = col
                    # Check if column exists
                    if col_name not in SCHEMA.get(table, []):
                        issues.append(f"Column '{col_name}' not in table '{table}'")

    # Find WHERE clauses
    where_pattern = r'WHERE\s+(.*?)(?:GROUP BY|ORDER BY|LIMIT|\)|$)'
    for match in re.finditer(where_pattern, content, re.IGNORECASE | re.DOTALL):
        clause = match.group(1)
        # Find column references
        for col_ref in re.findall(r'(\w+)\s*[=<>!]', clause):
            # Check against all tables
            found = False
            for table, cols in SCHEMA.items():
                if col_ref in cols:
                    found = True
                    break
            if not found and col_ref not in ['id', 'status', 'AND', 'OR']:
                issues.append(f"Possible undefined column in WHERE: '{col_ref}'")

    return issues

# Scan all module files
modules_dir = Path('modules')
all_issues = {}

for module_file in modules_dir.glob('*.py'):
    issues = find_column_references(module_file)
    if issues:
        all_issues[module_file.name] = issues

# Print report
if all_issues:
    print("=" * 80)
    print("DATABASE SCHEMA MISMATCH AUDIT REPORT")
    print("=" * 80)
    for module, issues in sorted(all_issues.items()):
        print(f"\n{module}:")
        for issue in issues:
            print(f"  - {issue}")
else:
    print("No schema mismatches found!")
