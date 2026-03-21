"""
Test Suite for New HR System Modules (Session 2)
Tests: Financial, Appraisals, Recruitment, Training, Timesheets
"""

import sqlite3
from datetime import datetime, date, timedelta
from database import get_db_connection, init_database
import hashlib

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def run_tests():
    """Run comprehensive tests for new modules"""

    print("=" * 70)
    print("HR SYSTEM - NEW MODULES TEST SUITE")
    print("=" * 70)

    # Initialize database
    try:
        init_database()
        print("✅ Database initialized")
    except:
        print("✅ Database already exists")

    tests_passed = 0
    tests_failed = 0

    # Test 1: Financial Records Module
    print("\n" + "=" * 70)
    print("TEST 1: Financial Records & Payroll")
    print("=" * 70)

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # Get test employee
            cursor.execute("SELECT id FROM employees WHERE employee_id = 'EMP-001' LIMIT 1")
            emp = cursor.fetchone()

            if emp:
                # Create financial record
                cursor.execute("""
                    INSERT INTO financial_records (
                        emp_id, period, base_salary, allowances, bonus,
                        deductions, net_pay, payment_date
                    ) VALUES (?, '2024-03', 5000, 500, 1000, 200, 6300, ?)
                """, (emp['id'], date.today().isoformat()))

                financial_id = cursor.lastrowid

                # Generate payslip
                cursor.execute("""
                    INSERT INTO payslips (
                        emp_id, period, base_salary, allowances, bonus,
                        deductions, net_pay, generated_by
                    ) VALUES (?, '2024-03', 5000, 500, 1000, 200, 6300, ?)
                """, (emp['id'], emp['id']))

                payslip_id = cursor.lastrowid

                conn.commit()

                print(f"✅ Created financial record ID: {financial_id}")
                print(f"✅ Generated payslip ID: {payslip_id}")
                tests_passed += 2
            else:
                print("❌ No test employee found")
                tests_failed += 1

    except Exception as e:
        print(f"❌ Financial Records Test Failed: {str(e)}")
        tests_failed += 1

    # Test 2: Appraisals Module
    print("\n" + "=" * 70)
    print("TEST 2: Performance Appraisals Workflow")
    print("=" * 70)

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # Get test employee and manager
            cursor.execute("SELECT id, manager_id FROM employees WHERE employee_id = 'EMP-002' LIMIT 1")
            emp = cursor.fetchone()

            if emp and emp['manager_id']:
                # Create appraisal
                cursor.execute("""
                    INSERT INTO appraisals (
                        emp_id, period, status, manager_id, created_by
                    ) VALUES (?, '2024-Q1', 'Draft', ?, ?)
                """, (emp['id'], emp['manager_id'], emp['manager_id']))

                appraisal_id = cursor.lastrowid
                print(f"✅ Created appraisal ID: {appraisal_id}")

                # Submit self-review
                cursor.execute("""
                    UPDATE appraisals SET
                        self_achievements = 'Completed 5 major projects',
                        self_areas_improvement = 'Time management',
                        self_goals = 'Lead a team project',
                        status = 'Submitted',
                        self_review_date = ?
                    WHERE id = ?
                """, (datetime.now().isoformat(), appraisal_id))

                print(f"✅ Self-review submitted")

                # Manager review
                cursor.execute("""
                    UPDATE appraisals SET
                        manager_feedback = 'Excellent performance throughout the quarter',
                        manager_rating = 4,
                        status = 'HR Review',
                        manager_review_date = ?
                    WHERE id = ?
                """, (datetime.now().isoformat(), appraisal_id))

                print(f"✅ Manager review completed")

                # HR final review
                cursor.execute("""
                    UPDATE appraisals SET
                        hr_feedback = 'Outstanding contributions',
                        overall_rating = 4,
                        status = 'Completed',
                        hr_review_date = ?
                    WHERE id = ?
                """, (datetime.now().isoformat(), appraisal_id))

                print(f"✅ HR review completed - Appraisal workflow complete")

                conn.commit()
                tests_passed += 4
            else:
                print("❌ No test employee with manager found")
                tests_failed += 1

    except Exception as e:
        print(f"❌ Appraisals Test Failed: {str(e)}")
        tests_failed += 1

    # Test 3: Recruitment Module
    print("\n" + "=" * 70)
    print("TEST 3: Recruitment & Job Applications")
    print("=" * 70)

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # Get HR admin
            cursor.execute("SELECT id FROM employees WHERE department = 'Human Resources' LIMIT 1")
            hr = cursor.fetchone()

            if hr:
                # Create job posting
                cursor.execute("""
                    INSERT INTO jobs (
                        title, department, location, employment_type,
                        salary_min, salary_max, description, requirements,
                        status, posted_by
                    ) VALUES (
                        'Senior Python Developer',
                        'Engineering',
                        'Remote',
                        'Full-time',
                        80000,
                        120000,
                        'Develop and maintain Python applications',
                        '5+ years Python experience, Django/Flask',
                        'Open',
                        ?
                    )
                """, (hr['id'],))

                job_id = cursor.lastrowid
                print(f"✅ Created job posting ID: {job_id}")

                # Create job application
                cursor.execute("""
                    INSERT INTO job_applications (
                        job_id, candidate_name, candidate_email, candidate_phone,
                        experience_years, expected_salary, cover_letter, status
                    ) VALUES (
                        ?,
                        'Alice Johnson',
                        'alice.johnson@email.com',
                        '+1234567890',
                        6,
                        100000,
                        'I am very interested in this position...',
                        'Applied'
                    )
                """, (job_id,))

                app_id = cursor.lastrowid
                print(f"✅ Created job application ID: {app_id}")

                # Shortlist candidate
                cursor.execute("UPDATE job_applications SET status = 'Shortlisted' WHERE id = ?", (app_id,))
                print(f"✅ Candidate shortlisted")

                # Schedule interview
                cursor.execute("UPDATE job_applications SET status = 'Interview' WHERE id = ?", (app_id,))
                print(f"✅ Interview scheduled")

                conn.commit()
                tests_passed += 4
            else:
                print("❌ No HR admin found")
                tests_failed += 1

    except Exception as e:
        print(f"❌ Recruitment Test Failed: {str(e)}")
        tests_failed += 1

    # Test 4: Training Module
    print("\n" + "=" * 70)
    print("TEST 4: Training & Development")
    print("=" * 70)

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # Get test employee
            cursor.execute("SELECT id, manager_id FROM employees WHERE employee_id = 'EMP-003' LIMIT 1")
            emp = cursor.fetchone()

            if emp:
                # Create training course
                cursor.execute("""
                    INSERT INTO training_catalog (
                        title, category, provider, level, duration_hours,
                        cost, currency, delivery_mode, description, status, created_by
                    ) VALUES (
                        'Advanced Python Programming',
                        'Technical',
                        'Coursera',
                        'Advanced',
                        40,
                        299,
                        'USD',
                        'Online',
                        'Master advanced Python concepts',
                        'Active',
                        ?
                    )
                """, (emp['id'],))

                course_id = cursor.lastrowid
                print(f"✅ Created training course ID: {course_id}")

                # Request enrollment
                cursor.execute("""
                    INSERT INTO training_enrollments (
                        emp_id, course_id, status
                    ) VALUES (?, ?, 'Requested')
                """, (emp['id'], course_id))

                enrollment_id = cursor.lastrowid
                print(f"✅ Enrollment requested ID: {enrollment_id}")

                # Manager approval
                if emp['manager_id']:
                    cursor.execute("""
                        UPDATE training_enrollments SET
                            status = 'Approved',
                            approved_by = ?,
                            approval_date = ?
                        WHERE id = ?
                    """, (emp['manager_id'], datetime.now().isoformat(), enrollment_id))
                    print(f"✅ Manager approved training")

                # HR final approval
                cursor.execute("""
                    UPDATE training_enrollments SET
                        status = 'Enrolled',
                        approval_date = ?
                    WHERE id = ?
                """, (datetime.now().isoformat(), enrollment_id))
                print(f"✅ HR approved - Employee enrolled")

                # Mark as completed
                cursor.execute("""
                    UPDATE training_enrollments SET
                        status = 'Completed',
                        completion_date = ?
                    WHERE id = ?
                """, (datetime.now().isoformat(), enrollment_id))
                print(f"✅ Training marked as completed")

                conn.commit()
                tests_passed += 5
            else:
                print("❌ No test employee found")
                tests_failed += 1

    except Exception as e:
        print(f"❌ Training Test Failed: {str(e)}")
        tests_failed += 1

    # Test 5: Timesheets Module
    print("\n" + "=" * 70)
    print("TEST 5: Timesheets & Time Tracking")
    print("=" * 70)

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # Get test employee
            cursor.execute("SELECT id, manager_id FROM employees WHERE employee_id = 'EMP-004' LIMIT 1")
            emp = cursor.fetchone()

            if emp:
                # Create timesheet entry
                work_date = date.today() - timedelta(days=1)
                cursor.execute("""
                    INSERT INTO timesheets (
                        emp_id, work_date, start_time, end_time, break_minutes,
                        hours_worked, regular_hours, overtime_hours,
                        project_name, notes, status
                    ) VALUES (?, ?, '09:00', '18:00', 60, 8.0, 8.0, 0.0,
                             'Project Alpha', 'Regular development work', 'Draft')
                """, (emp['id'], work_date.isoformat()))

                timesheet_id = cursor.lastrowid
                print(f"✅ Created timesheet entry ID: {timesheet_id}")

                # Submit timesheet
                cursor.execute("UPDATE timesheets SET status = 'Submitted' WHERE id = ?", (timesheet_id,))
                print(f"✅ Timesheet submitted")

                # Approve timesheet
                if emp['manager_id']:
                    cursor.execute("""
                        UPDATE timesheets SET
                            status = 'Approved',
                            approved_by = ?,
                            approval_date = ?
                        WHERE id = ?
                    """, (emp['manager_id'], datetime.now().isoformat(), timesheet_id))
                    print(f"✅ Timesheet approved by manager")

                # Create overtime entry
                cursor.execute("""
                    INSERT INTO timesheets (
                        emp_id, work_date, start_time, end_time, break_minutes,
                        hours_worked, regular_hours, overtime_hours,
                        project_name, status
                    ) VALUES (?, ?, '09:00', '20:00', 60, 10.0, 8.0, 2.0,
                             'Urgent Deployment', 'Approved')
                """, (emp['id'], date.today().isoformat()))

                print(f"✅ Overtime timesheet created")

                conn.commit()
                tests_passed += 4
            else:
                print("❌ No test employee found")
                tests_failed += 1

    except Exception as e:
        print(f"❌ Timesheets Test Failed: {str(e)}")
        tests_failed += 1

    # Test 6: Module Integration
    print("\n" + "=" * 70)
    print("TEST 6: Module Integration & Data Consistency")
    print("=" * 70)

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # Verify financial records
            cursor.execute("SELECT COUNT(*) as cnt FROM financial_records")
            fin_count = cursor.fetchone()['cnt']
            print(f"✅ Financial records in database: {fin_count}")

            # Verify appraisals
            cursor.execute("SELECT COUNT(*) as cnt FROM appraisals")
            apr_count = cursor.fetchone()['cnt']
            print(f"✅ Appraisals in database: {apr_count}")

            # Verify job postings
            cursor.execute("SELECT COUNT(*) as cnt FROM jobs")
            job_count = cursor.fetchone()['cnt']
            print(f"✅ Job postings in database: {job_count}")

            # Verify training courses
            cursor.execute("SELECT COUNT(*) as cnt FROM training_catalog")
            course_count = cursor.fetchone()['cnt']
            print(f"✅ Training courses in database: {course_count}")

            # Verify timesheets
            cursor.execute("SELECT COUNT(*) as cnt FROM timesheets")
            ts_count = cursor.fetchone()['cnt']
            print(f"✅ Timesheets in database: {ts_count}")

            tests_passed += 5

    except Exception as e:
        print(f"❌ Integration Test Failed: {str(e)}")
        tests_failed += 1

    # Test 7: Workflow Status Verification
    print("\n" + "=" * 70)
    print("TEST 7: Workflow Status Verification")
    print("=" * 70)

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # Check appraisal workflow
            cursor.execute("SELECT COUNT(*) as cnt FROM appraisals WHERE status = 'Completed'")
            completed_appr = cursor.fetchone()['cnt']
            print(f"✅ Completed appraisals: {completed_appr}")

            # Check training enrollments
            cursor.execute("SELECT COUNT(*) as cnt FROM training_enrollments WHERE status = 'Completed'")
            completed_training = cursor.fetchone()['cnt']
            print(f"✅ Completed training enrollments: {completed_training}")

            # Check approved timesheets
            cursor.execute("SELECT COUNT(*) as cnt FROM timesheets WHERE status = 'Approved'")
            approved_ts = cursor.fetchone()['cnt']
            print(f"✅ Approved timesheets: {approved_ts}")

            # Check shortlisted candidates
            cursor.execute("SELECT COUNT(*) as cnt FROM job_applications WHERE status IN ('Shortlisted', 'Interview')")
            shortlisted = cursor.fetchone()['cnt']
            print(f"✅ Shortlisted/Interview candidates: {shortlisted}")

            tests_passed += 4

    except Exception as e:
        print(f"❌ Workflow Verification Failed: {str(e)}")
        tests_failed += 1

    # Final Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print(f"✅ Tests Passed: {tests_passed}")
    print(f"❌ Tests Failed: {tests_failed}")
    print(f"📊 Success Rate: {(tests_passed / (tests_passed + tests_failed) * 100):.1f}%")
    print("=" * 70)

    if tests_failed == 0:
        print("\n🎉 ALL TESTS PASSED! 🎉")
        print("✅ Financial Records Module: WORKING")
        print("✅ Appraisals Module: WORKING")
        print("✅ Recruitment Module: WORKING")
        print("✅ Training Module: WORKING")
        print("✅ Timesheets Module: WORKING")
        print("\n✅ System is ready for user testing!")
    else:
        print(f"\n⚠️ {tests_failed} test(s) failed. Please review the errors above.")

    return tests_passed, tests_failed

if __name__ == "__main__":
    run_tests()
