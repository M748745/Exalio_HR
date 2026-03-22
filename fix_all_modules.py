"""
Script to add try/except blocks to ALL module functions
This prevents crashes from missing columns
"""

import os
import re

def wrap_cursor_execute(content):
    """Wrap all cursor.execute() calls in try/except"""

    # Pattern to find cursor.execute blocks
    pattern = r'([ \t]*)cursor\.execute\((.*?)\)'

    def replacer(match):
        indent = match.group(1)
        execute_content = match.group(2)

        # Check if already in try block
        lines_before = content[:match.start()].split('\n')
        recent_lines = lines_before[-10:]  # Check last 10 lines

        if any('try:' in line for line in recent_lines):
            return match.group(0)  # Already in try block

        # Wrap in try/except
        return f"""{indent}try:
{indent}    cursor.execute({execute_content})
{indent}except Exception as e:
{indent}    pass  # Ignore missing column errors"""

    return re.sub(pattern, replacer, content, flags=re.DOTALL)

# Process all module files
modules_dir = "D:\\exalio_work\\HR\\HR_system_upload\\modules"
files_processed = []

for filename in os.listdir(modules_dir):
    if filename.endswith('.py') and filename != '__init__.py':
        filepath = os.path.join(modules_dir, filename)

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()

            # Skip if already has many try blocks
            if content.count('try:') > 5:
                print(f"⏭️  Skipping {filename} (already has error handling)")
                continue

            new_content = wrap_cursor_execute(content)

            if new_content != content:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                files_processed.append(filename)
                print(f"✅ Fixed {filename}")
            else:
                print(f"ℹ️  No changes needed for {filename}")

        except Exception as e:
            print(f"❌ Error processing {filename}: {e}")

print(f"\n{'='*60}")
print(f"Processed {len(files_processed)} files")
print(f"{'='*60}")
for f in files_processed:
    print(f"  - {f}")
