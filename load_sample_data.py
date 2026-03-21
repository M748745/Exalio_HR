"""
Load sample data into all 25 empty tables
"""

from database import get_db_connection

def load_all_sample_data():
    print('=' * 60)
    print('LOADING SAMPLE DATA INTO 25 TABLES')
    print('=' * 60)

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # 1. Announcements (2 records)
            print('\n1. Announcements...')
            cursor.execute('''
                INSERT INTO announcements (title, content, priority, target_audience, published_by, published_date, status, created_at)
                VALUES
                (%s, %s, %s, %s, %s, NOW(), %s, NOW()),
                (%s, %s, %s, %s, %s, NOW(), %s, NOW())
            ''', ('Welcome to Exalio HR System', 'We are excited to announce the launch of our new HR system!', 'High', 'All', 1, 'Active',
                  'Holiday Notice', 'Office will be closed on public holidays', 'Normal', 'All', 1, 'Active'))
            print('   ✅ 2 announcements')

            # 2. Appraisals (2 records)
            print('2. Appraisals...')
            cursor.execute('''
                INSERT INTO appraisals (emp_id, period, type, status, self_rating, self_comments, manager_rating, manager_comments, reviewer_id, due_date, created_at, updated_at)
                VALUES
                (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW()),
                (%s, %s, %s, %s, %s, %s, NULL, NULL, %s, %s, NOW(), NOW())
            ''', (3, '2024 Annual Review', 'Annual', 'Completed', 'Excellent', 'Great year!', 'Excellent', 'Outstanding performance', 2, '2024-12-31',
                  4, '2024 Annual Review', 'Annual', 'Manager Review', 'Good', 'Solid work', 2, '2024-12-31'))
            print('   ✅ 2 appraisals')

            # 3. Assets (3 records)
            print('3. Assets...')
            cursor.execute('''
                INSERT INTO assets (asset_name, asset_type, serial_number, purchase_date, purchase_cost, assigned_to, condition, status, created_at)
                VALUES
                (%s, %s, %s, %s, %s, %s, %s, %s, NOW()),
                (%s, %s, %s, %s, %s, %s, %s, %s, NOW()),
                (%s, %s, %s, %s, %s, %s, %s, %s, NOW())
            ''', ('Dell Laptop XPS 15', 'Laptop', 'DL12345', '2024-01-15', 1500.00, 3, 'Good', 'Assigned',
                  'iPhone 14 Pro', 'Mobile Phone', 'IP67890', '2024-02-01', 1200.00, 2, 'Excellent', 'Assigned',
                  'Standing Desk', 'Furniture', 'SD99999', '2024-01-10', 800.00, 3, 'Good', 'Assigned'))
            print('   ✅ 3 assets')

            # 4. Audit Logs (3 records)
            print('4. Audit Logs...')
            cursor.execute('''
                INSERT INTO audit_logs (user_id, action, entity_type, entity_id, details, timestamp)
                VALUES
                (%s, %s, %s, %s, %s, NOW()),
                (%s, %s, %s, %s, %s, NOW()),
                (%s, %s, %s, %s, %s, NOW())
            ''', (1, 'Login', 'User', 1, 'Admin logged in',
                  2, 'Create', 'Employee', 3, 'Added new employee',
                  1, 'Update', 'Leave Request', 1, 'Approved leave request'))
            print('   ✅ 3 audit logs')

            # 5. Bonuses (2 records)
            print('5. Bonuses...')
            cursor.execute('''
                INSERT INTO bonuses (emp_id, bonus_type, amount, calculation_method, period, status, recommended_by, created_at)
                VALUES
                (%s, %s, %s, %s, %s, %s, %s, NOW()),
                (%s, %s, %s, %s, %s, %s, %s, NOW())
            ''', (3, 'Performance Bonus', 5000.00, 'Annual Performance', '2024', 'Approved', 2,
                  4, 'Project Completion', 2000.00, 'Project Success', 'Q1 2024', 'Pending', 2))
            print('   ✅ 2 bonuses')

            # 6. Career Plans (2 records)
            print('6. Career Plans...')
            cursor.execute('''
                INSERT INTO career_plans (emp_id, current_level, target_level, timeline, skills_required, milestones, status, created_by, created_at)
                VALUES
                (%s, %s, %s, %s, %s, %s, %s, %s, NOW()),
                (%s, %s, %s, %s, %s, %s, %s, %s, NOW())
            ''', (3, 'Senior Developer', 'Tech Lead', '2 years', 'Leadership, Architecture, Mentoring', 'Lead 2 projects, Mentor juniors', 'Active', 2,
                  4, 'Developer', 'Senior Developer', '1.5 years', 'Advanced coding, System design', 'Complete certifications', 'Active', 2))
            print('   ✅ 2 career plans')

            # 7. Certificates (2 records)
            print('7. Certificates...')
            cursor.execute('''
                INSERT INTO certificates (emp_id, certificate_name, issuing_organization, issue_date, expiry_date, status, created_at)
                VALUES
                (%s, %s, %s, %s, %s, %s, NOW()),
                (%s, %s, %s, %s, %s, %s, NOW())
            ''', (3, 'AWS Certified Developer', 'Amazon Web Services', '2024-01-15', '2027-01-15', 'Active',
                  4, 'Python Professional Certificate', 'Python Institute', '2023-06-01', '2026-06-01', 'Active'))
            print('   ✅ 2 certificates')

            # 8. Compliance (2 records)
            print('8. Compliance...')
            cursor.execute('''
                INSERT INTO compliance (requirement_name, category, description, review_frequency, next_review_date, responsible_person, status, created_at)
                VALUES
                (%s, %s, %s, %s, %s, %s, %s, NOW()),
                (%s, %s, %s, %s, %s, %s, %s, NOW())
            ''', ('GDPR Compliance', 'Data Protection', 'General Data Protection Regulation', 'Annual', '2025-01-01', 1, 'Compliant',
                  'Security Training', 'Security', 'Annual security awareness training', 'Annual', '2024-12-31', 1, 'In Progress'))
            print('   ✅ 2 compliance records')

            # 9. Contracts (2 records)
            print('9. Contracts...')
            cursor.execute('''
                INSERT INTO contracts (emp_id, contract_type, start_date, end_date, salary, terms, status, created_at)
                VALUES
                (%s, %s, %s, NULL, %s, %s, %s, NOW()),
                (%s, %s, %s, NULL, %s, %s, %s, NOW())
            ''', (3, 'Full-time Permanent', '2021-03-15', 95000.00, 'Standard employment contract', 'Active',
                  4, 'Full-time Permanent', '2021-01-01', 75000.00, 'Standard employment contract', 'Active'))
            print('   ✅ 2 contracts')

            # 10. Documents (2 records)
            print('10. Documents...')
            cursor.execute('''
                INSERT INTO documents (title, category, document_type, file_path, uploaded_by, access_level, status, created_at)
                VALUES
                (%s, %s, %s, %s, %s, %s, %s, NOW()),
                (%s, %s, %s, %s, %s, %s, %s, NOW())
            ''', ('Employee Handbook 2024', 'HR Policies', 'PDF', '/docs/handbook_2024.pdf', 1, 'Public', 'Active',
                  'Code of Conduct', 'HR Policies', 'PDF', '/docs/code_of_conduct.pdf', 1, 'Public', 'Active'))
            print('   ✅ 2 documents')

            # 11. Exit Process (1 record)
            print('11. Exit Process...')
            cursor.execute('''
                INSERT INTO exit_process (emp_id, resignation_date, last_working_day, reason_for_leaving, clearance_status, created_at)
                VALUES (%s, %s, %s, %s, %s, NOW())
            ''', (10, '2026-03-01', '2026-03-31', 'Relocation', 'Pending'))
            print('   ✅ 1 exit process record')

            # 12. Expenses (2 records)
            print('12. Expenses...')
            cursor.execute('''
                INSERT INTO expenses (emp_id, expense_type, amount, currency, expense_date, description, status, created_at)
                VALUES
                (%s, %s, %s, %s, %s, %s, %s, NOW()),
                (%s, %s, %s, %s, %s, %s, %s, NOW())
            ''', (3, 'Travel', 250.00, 'USD', '2024-03-10', 'Client meeting in SF', 'Approved',
                  4, 'Equipment', 150.00, 'USD', '2024-03-12', 'Keyboard and mouse', 'Pending'))
            print('   ✅ 2 expenses')

            # 13. Goals (2 records)
            print('13. Goals...')
            cursor.execute('''
                INSERT INTO goals (emp_id, goal_title, description, target_date, status, progress, created_by, created_at)
                VALUES
                (%s, %s, %s, %s, %s, %s, %s, NOW()),
                (%s, %s, %s, %s, %s, %s, %s, NOW())
            ''', (3, 'Complete AWS Certification', 'Get AWS Solutions Architect certification', '2024-06-30', 'In Progress', 60, 3,
                  4, 'Lead Team Project', 'Successfully lead migration project', '2024-09-30', 'In Progress', 30, 2))
            print('   ✅ 2 goals')

            # 14. Insurance (2 records)
            print('14. Insurance...')
            cursor.execute('''
                INSERT INTO insurance (emp_id, insurance_type, provider, policy_number, coverage_amount, start_date, end_date, premium, status, created_at)
                VALUES
                (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW()),
                (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
            ''', (3, 'Health Insurance', 'Blue Cross', 'BC123456', 100000.00, '2024-01-01', '2024-12-31', 500.00, 'Active',
                  4, 'Health Insurance', 'Blue Cross', 'BC123457', 100000.00, '2024-01-01', '2024-12-31', 500.00, 'Active'))
            print('   ✅ 2 insurance policies')

            # 15. Jobs (2 records)
            print('15. Jobs...')
            cursor.execute('''
                INSERT INTO jobs (title, department, job_type, location, description, requirements, salary_range, status, posted_by, posted_date, created_at)
                VALUES
                (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW()),
                (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
            ''', ('Senior Full Stack Developer', 'Engineering', 'Full-time', 'Remote', 'Build scalable web applications', '5+ years experience, React, Node.js', '$120,000 - $150,000', 'Open', 1,
                  'Marketing Manager', 'Marketing', 'Full-time', 'San Francisco', 'Lead marketing initiatives', '3+ years in marketing', '$90,000 - $120,000', 'Open', 1))
            print('   ✅ 2 job postings')

            # 16. Job Applications (2 records)
            print('16. Job Applications...')
            cursor.execute('''
                INSERT INTO job_applications (job_id, candidate_name, candidate_email, candidate_phone, resume, status, applied_date, notes)
                VALUES
                (%s, %s, %s, %s, %s, %s, NOW(), %s),
                (%s, %s, %s, %s, %s, %s, NOW(), %s)
            ''', (1, 'Jane Smith', 'jane.smith@email.com', '+1234567899', '/resumes/jane_smith.pdf', 'Under Review', 'Strong candidate',
                  1, 'Bob Johnson', 'bob.j@email.com', '+1234567888', '/resumes/bob_johnson.pdf', 'Shortlisted', 'Excellent skills'))
            print('   ✅ 2 job applications')

            # 17. Onboarding Tasks (2 records)
            print('17. Onboarding Tasks...')
            cursor.execute('''
                INSERT INTO onboarding_tasks (emp_id, task_name, description, assigned_to, due_date, status, created_at)
                VALUES
                (%s, %s, %s, %s, %s, %s, NOW()),
                (%s, %s, %s, %s, %s, %s, NOW())
            ''', (10, 'Complete HR Paperwork', 'Fill out all employment forms', 1, '2026-03-20', 'Pending',
                  10, 'IT Setup', 'Get laptop and credentials', 1, '2026-03-20', 'Pending'))
            print('   ✅ 2 onboarding tasks')

            # 18. Payslips (2 records)
            print('18. Payslips...')
            cursor.execute('''
                INSERT INTO payslips (emp_id, period, base_salary, allowances, deductions, net_pay, generated_date, file_path)
                VALUES
                (%s, %s, %s, %s, %s, %s, NOW(), %s),
                (%s, %s, %s, %s, %s, %s, NOW(), %s)
            ''', (3, '2024-02', 8000.00, 1000.00, 500.00, 8500.00, '/payslips/sarah_feb2024.pdf',
                  4, '2024-02', 6000.00, 800.00, 400.00, 6400.00, '/payslips/mike_feb2024.pdf'))
            print('   ✅ 2 payslips')

            # 19. PIP Records (1 record)
            print('19. PIP Records...')
            cursor.execute('''
                INSERT INTO pip_records (emp_id, manager_id, reason, goals, expected_outcomes, start_date, end_date, status, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW())
            ''', (4, 2, 'Improve code quality', 'Reduce bug count by 50%', 'Better testing practices', '2024-01-01', '2024-04-01', 'Completed'))
            print('   ✅ 1 PIP record')

            # 20. Shifts (2 records)
            print('20. Shifts...')
            cursor.execute('''
                INSERT INTO shifts (shift_name, start_time, end_time, days, emp_id, shift_date, location, status, created_at)
                VALUES
                (%s, %s, %s, %s, %s, %s, %s, %s, NOW()),
                (%s, %s, %s, %s, %s, %s, %s, %s, NOW())
            ''', ('Morning Shift', '09:00', '17:00', 'Monday-Friday', 3, '2024-03-18', 'Office', 'Assigned',
                  'Afternoon Shift', '13:00', '21:00', 'Monday-Friday', 4, '2024-03-18', 'Office', 'Assigned'))
            print('   ✅ 2 shifts')

            # 21. Surveys (2 records)
            print('21. Surveys...')
            cursor.execute('''
                INSERT INTO surveys (title, description, questions, target_audience, created_by, start_date, end_date, status, created_at)
                VALUES
                (%s, %s, %s, %s, %s, NOW(), %s, %s, NOW()),
                (%s, %s, %s, %s, %s, NOW(), %s, %s, NOW())
            ''', ('Employee Satisfaction 2024', 'Annual employee satisfaction survey', '{"questions": ["How satisfied?", "Rate manager"]}', 'All', 1, '2024-12-31', 'Active',
                  'Remote Work Feedback', 'Gather feedback on remote work', '{"questions": ["Prefer remote?", "Productivity?"]}', 'All', 1, '2024-06-30', 'Active'))
            print('   ✅ 2 surveys')

            # 22. Survey Responses (2 records)
            print('22. Survey Responses...')
            cursor.execute('''
                INSERT INTO survey_responses (survey_id, emp_id, responses, submitted_at)
                VALUES
                (%s, %s, %s, NOW()),
                (%s, %s, %s, NOW())
            ''', (1, 3, '{"q1": "Very Satisfied", "q2": "Excellent"}',
                  1, 4, '{"q1": "Satisfied", "q2": "Good"}'))
            print('   ✅ 2 survey responses')

            # 23. Timesheets (2 records)
            print('23. Timesheets...')
            cursor.execute('''
                INSERT INTO timesheets (emp_id, work_date, hours_worked, project, task_description, status, created_at)
                VALUES
                (%s, %s, %s, %s, %s, %s, NOW()),
                (%s, %s, %s, %s, %s, %s, NOW())
            ''', (3, '2024-03-18', 8.0, 'HR System Migration', 'Database migration work', 'Approved',
                  4, '2024-03-18', 7.5, 'Client Portal', 'Frontend development', 'Pending'))
            print('   ✅ 2 timesheets')

            # 24. Training Catalog (2 records)
            print('24. Training Catalog...')
            cursor.execute('''
                INSERT INTO training_catalog (course_name, description, duration, instructor, capacity, start_date, end_date, status, created_at)
                VALUES
                (%s, %s, %s, %s, %s, %s, %s, %s, NOW()),
                (%s, %s, %s, %s, %s, %s, %s, %s, NOW())
            ''', ('Leadership Skills', 'Develop leadership and management skills', '2 days', 'John Smith', 20, '2024-06-01', '2024-06-02', 'Open',
                  'Python Advanced', 'Advanced Python programming', '3 days', 'Sarah Johnson', 15, '2024-07-01', '2024-07-03', 'Open'))
            print('   ✅ 2 training courses')

            # 25. Training Enrollments (2 records)
            print('25. Training Enrollments...')
            cursor.execute('''
                INSERT INTO training_enrollments (emp_id, course_id, enrollment_date, status, score, feedback)
                VALUES
                (%s, %s, NOW(), %s, NULL, NULL),
                (%s, %s, NOW(), %s, NULL, NULL)
            ''', (3, 1, 'Enrolled',
                  4, 2, 'Enrolled'))
            print('   ✅ 2 training enrollments')

            conn.commit()

            print('\n' + '=' * 60)
            print('✅ SUCCESS! ALL 25 TABLES NOW HAVE DATA!')
            print('=' * 60)

            return True

    except Exception as e:
        print(f'\n❌ ERROR: {str(e)}')
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    load_all_sample_data()
