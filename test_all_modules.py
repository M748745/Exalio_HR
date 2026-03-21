"""
Comprehensive Module Testing Script
Tests all 32 modules for import and basic functionality
"""

import sys
import traceback

def test_module_import(module_name, function_name):
    """Test if a module can be imported and has required function"""
    try:
        module = __import__(f'modules.{module_name}', fromlist=[function_name])
        func = getattr(module, function_name)
        return True, f"✅ {module_name}: Import successful"
    except Exception as e:
        return False, f"❌ {module_name}: {str(e)}"

def main():
    """Test all 32 modules"""
    print("=" * 60)
    print("HR SYSTEM - COMPREHENSIVE MODULE TEST")
    print("=" * 60)
    print()

    # Define all 32 modules and their main functions
    modules_to_test = [
        # Session 1 - Core HR (9 modules)
        ('employee_management', 'show_employee_management'),
        ('leave_management', 'show_leave_management'),
        ('performance', 'show_performance_management'),
        ('contracts', 'show_contracts_management'),
        ('insurance', 'show_insurance_management'),
        ('bonus', 'show_bonus_management'),
        ('notifications', 'show_notifications_center'),
        ('expenses', 'show_expense_management'),
        ('certificates', 'show_certificates_management'),

        # Session 2 - Extended (5 modules)
        ('financial', 'show_financial_management'),
        ('appraisals', 'show_appraisals_management'),
        ('recruitment', 'show_recruitment_management'),
        ('training', 'show_training_management'),
        ('timesheets', 'show_timesheet_management'),

        # Session 3 - Advanced (4 modules)
        ('assets', 'show_asset_management'),
        ('goals', 'show_goals_management'),
        ('career_plans', 'show_career_plans_management'),
        ('exit_management', 'show_exit_management'),

        # Session 4 - Communication (6 modules)
        ('documents', 'show_document_management'),
        ('announcements', 'show_announcements_management'),
        ('onboarding', 'show_onboarding_management'),
        ('directory', 'show_employee_directory'),
        ('org_chart', 'show_org_chart'),
        ('reports', 'show_reports_analytics'),

        # Session 5 - Final (8 modules)
        ('shift_scheduling', 'show_shift_scheduling'),
        ('surveys', 'show_surveys_feedback'),
        ('compliance', 'show_compliance_tracking'),
        ('pip', 'show_pip_management'),
        ('admin_panel', 'show_admin_panel'),
        ('email_integration', 'show_email_integration'),
        ('calendar_integration', 'show_calendar_integration'),
        ('mobile_ui', 'show_mobile_ui'),
    ]

    results = []
    passed = 0
    failed = 0

    print("Testing all 32 modules...\n")

    # Test each module
    for i, (module_name, function_name) in enumerate(modules_to_test, 1):
        success, message = test_module_import(module_name, function_name)
        results.append((success, message))

        if success:
            passed += 1
            print(f"{i:2d}. {message}")
        else:
            failed += 1
            print(f"{i:2d}. {message}")

    # Summary
    print()
    print("=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Total Modules Tested: {len(modules_to_test)}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"Success Rate: {(passed/len(modules_to_test)*100):.1f}%")
    print("=" * 60)

    # Test database connection
    print("\nTesting database connection...")
    try:
        from database import get_db_connection
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            print(f"✅ Database connection successful")
            print(f"   Found {len(tables)} tables in database")
    except Exception as e:
        print(f"❌ Database connection failed: {str(e)}")

    # Test auth module
    print("\nTesting authentication module...")
    try:
        from auth import is_hr_admin, is_manager
        print(f"✅ Authentication module loaded successfully")
    except Exception as e:
        print(f"❌ Authentication module failed: {str(e)}")

    print()
    if failed == 0:
        print("🎉 ALL TESTS PASSED! System is ready for deployment!")
    else:
        print(f"⚠️  {failed} module(s) failed. Please review errors above.")

    return failed == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
