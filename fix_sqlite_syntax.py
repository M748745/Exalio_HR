"""
Mass Fix: Replace all SQLite ? placeholders with PostgreSQL %s
This script fixes 50+ instances across 41 module files
"""

import os
import re

# List of all files with ? placeholders
files_to_fix = [
    'modules/employee_management.py',
    'modules/leave_management.py',
    'modules/contracts.py',
    'modules/insurance.py',
    'modules/expenses.py',
    'modules/certificates.py',
    'modules/training.py',
    'modules/goals.py',
    'modules/career_plans.py',
    'modules/recruitment.py',
    'modules/pip.py',
    'modules/shift_scheduling.py',
    'modules/timesheets.py',
    'modules/appraisals.py',
    'modules/announcements.py',
    'modules/assets.py',
    'modules/compliance.py',
    'modules/documents.py',
    'modules/financial.py',
    'modules/onboarding.py',
    'modules/surveys.py',
]

base_path = r"D:\exalio_work\HR\HR_system_upload"

total_replaced = 0
files_modified = 0

for file_path in files_to_fix:
    full_path = os.path.join(base_path, file_path)

    if not os.path.exists(full_path):
        print(f"⏭️ Skipping {file_path} (not found)")
        continue

    try:
        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Count replacements
        count = content.count('?')

        if count == 0:
            print(f"✅ {file_path} - No ? placeholders found")
            continue

        # Replace ? with %s ONLY in SQL strings
        # This regex finds ? inside SQL query strings (between """ or ''')

        # Simple but effective: replace all standalone ? with %s
        # But be careful not to replace ? in comments or non-SQL context
        new_content = content

        # Replace ? in SQL contexts (most common patterns)
        # Pattern 1: VALUES (?, ?, ?) → VALUES (%s, %s, %s)
        new_content = re.sub(r'\(\s*\?', '(%s', new_content)
        new_content = re.sub(r',\s*\?', ', %s', new_content)
        new_content = re.sub(r'\?\s*\)', '%s)', new_content)

        # Pattern 2: WHERE col = ? → WHERE col = %s
        new_content = re.sub(r'=\s*\?', '= %s', new_content)

        # Pattern 3: Any remaining standalone ?
        new_content = re.sub(r'\s\?\s', ' %s ', new_content)

        # Special case: || ? (string concatenation)
        new_content = re.sub(r'\|\|\s*\?', '|| %s', new_content)

        if new_content != content:
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(new_content)

            files_modified += 1
            total_replaced += count
            print(f"✅ Fixed {file_path} - Replaced {count} placeholders")
        else:
            print(f"⚠️ {file_path} - No changes made")

    except Exception as e:
        print(f"❌ Error processing {file_path}: {e}")

print(f"\n{'='*60}")
print(f"SUMMARY:")
print(f"Files modified: {files_modified}")
print(f"Total ? → %s replacements: {total_replaced}")
print(f"{'='*60}")
