"""
Test script to verify HR Admin role detection
"""

import streamlit as st
from database import get_db_connection
from auth import is_hr_admin, get_current_user

# This would be run in the Streamlit app context
print("Testing HR Admin check...")

# Check if session state has user
if 'user_data' in st.session_state:
    user = get_current_user()
    print(f"Current user: {user.get('full_name', 'Unknown')}")
    print(f"Role: {user.get('role', 'Unknown')}")
    print(f"Is HR Admin: {is_hr_admin()}")

    # Check database for HR admins
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT username, role FROM users WHERE role = 'hr_admin'")
        admins = cursor.fetchall()
        print(f"\nHR Admins in database: {len(admins)}")
        for admin in admins:
            print(f"  - {admin['username']} ({admin['role']})")
else:
    print("No user logged in")
