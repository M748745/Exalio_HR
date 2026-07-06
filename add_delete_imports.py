"""
Script to add delete_utils import to all HR modules
"""

import os
import re

modules_dir = "modules"
modules_to_update = [
    "training.py",
    "assets.py",
    "timesheets.py",
    "documents.py",
    "performance.py",
    "certificates.py",
    "goals.py",
    "career_plans.py",
    "exit_management.py",
    "announcements.py",
    "onboarding.py",
    "shift_scheduling.py",
    "surveys.py",
    "compliance.py",
    "pip.py",
    "bonus.py",
    "insurance.py"
]

import_line = "from modules.delete_utils import render_delete_button\n"

for module_file in modules_to_update:
    file_path = os.path.join(modules_dir, module_file)

    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        continue

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Check if import already exists
    if "from modules.delete_utils import" in content:
        print(f"✅ Already has import: {module_file}")
        continue

    # Find the last import statement
    lines = content.split('\n')
    last_import_idx = -1

    for i, line in enumerate(lines):
        if line.startswith('import ') or line.startswith('from '):
            last_import_idx = i

    if last_import_idx != -1:
        # Insert after the last import
        lines.insert(last_import_idx + 1, import_line.rstrip())
        new_content = '\n'.join(lines)

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)

        print(f"✅ Added import to: {module_file}")
    else:
        print(f"⚠️ Could not find import section in: {module_file}")

print("\n✅ Import addition complete!")
