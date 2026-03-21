"""Verify Phase 1 Installation"""
from database import get_db_connection

with get_db_connection() as conn:
    cursor = conn.cursor()

    # Count tables
    cursor.execute('SELECT name FROM sqlite_master WHERE type="table"')
    tables = cursor.fetchall()
    print(f'✅ Total tables created: {len(tables)}')

    # Count employees
    cursor.execute('SELECT COUNT(*) as cnt FROM employees')
    emp_count = cursor.fetchone()['cnt']
    print(f'✅ Total employees: {emp_count}')

    # Count users
    cursor.execute('SELECT COUNT(*) as cnt FROM users')
    user_count = cursor.fetchone()['cnt']
    print(f'✅ Total users: {user_count}')

    # List roles
    cursor.execute('SELECT DISTINCT role FROM users')
    roles = cursor.fetchall()
    print(f'✅ Roles configured: {", ".join([r["role"] for r in roles])}')

    print('\n🎉 Phase 1 verification complete!')
    print('🚀 Run "streamlit run app.py" to start the application')
