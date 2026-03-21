"""
Load sample data for new features:
- Teams
- Positions
- Skills
- Team Skills Matrix
- Employee Skills
- Custom Profile Fields
- Profile Update Requests
"""

from database import get_db_connection

def load_sample_data():
    print('=' * 60)
    print('LOADING SAMPLE DATA FOR NEW FEATURES')
    print('=' * 60)

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # 1. Teams (4 teams)
            print('\n1. Loading Teams...')
            cursor.execute('''
                INSERT INTO teams (team_name, department, team_lead_id, description, status) VALUES
                (%s, %s, %s, %s, %s),
                (%s, %s, %s, %s, %s),
                (%s, %s, %s, %s, %s),
                (%s, %s, %s, %s, %s)
                ON CONFLICT (team_name) DO NOTHING
            ''', ('App Development', 'Engineering', 2, 'Frontend and backend application development', 'Active',
                  'Data Engineering', 'Engineering', 2, 'Data pipeline and analytics', 'Active',
                  'AI/ML', 'Engineering', 2, 'Artificial intelligence and machine learning', 'Active',
                  'Marketing Team', 'Marketing', 5, 'Digital marketing and brand management', 'Active'))
            print('   ✅ 4 teams')

            # Get team IDs
            cursor.execute("SELECT id, team_name FROM teams ORDER BY id")
            teams = {row['team_name']: row['id'] for row in cursor.fetchall()}

            # 2. Positions (8 positions under teams)
            print('2. Loading Positions...')
            cursor.execute('''
                INSERT INTO positions (position_name, team_id, level, description, status) VALUES
                (%s, %s, %s, %s, %s),
                (%s, %s, %s, %s, %s),
                (%s, %s, %s, %s, %s),
                (%s, %s, %s, %s, %s),
                (%s, %s, %s, %s, %s),
                (%s, %s, %s, %s, %s),
                (%s, %s, %s, %s, %s),
                (%s, %s, %s, %s, %s)
                ON CONFLICT (position_name, team_id) DO NOTHING
            ''', ('Senior Developer', teams['App Development'], 'Senior', 'Senior full-stack developer', 'Active',
                  'Developer', teams['App Development'], 'Mid-level', 'Full-stack developer', 'Active',
                  'Data Engineer', teams['Data Engineering'], 'Mid-level', 'Data pipeline engineer', 'Active',
                  'Senior Data Engineer', teams['Data Engineering'], 'Senior', 'Lead data engineering projects', 'Active',
                  'AI Engineer', teams['AI/ML'], 'Mid-level', 'ML model development', 'Active',
                  'Senior AI Engineer', teams['AI/ML'], 'Senior', 'Lead AI/ML initiatives', 'Active',
                  'Marketing Manager', teams['Marketing Team'], 'Manager', 'Lead marketing campaigns', 'Active',
                  'Marketing Specialist', teams['Marketing Team'], 'Junior', 'Support marketing activities', 'Active'))
            print('   ✅ 8 positions')

            # Get position IDs
            cursor.execute("SELECT id, position_name, team_id FROM positions ORDER BY id")
            positions = {(row['position_name'], row['team_id']): row['id'] for row in cursor.fetchall()}

            # 3. Skills (15 skills)
            print('3. Loading Skills...')
            cursor.execute('''
                INSERT INTO skills (skill_name, category, description) VALUES
                (%s, %s, %s), (%s, %s, %s), (%s, %s, %s), (%s, %s, %s), (%s, %s, %s),
                (%s, %s, %s), (%s, %s, %s), (%s, %s, %s), (%s, %s, %s), (%s, %s, %s),
                (%s, %s, %s), (%s, %s, %s), (%s, %s, %s), (%s, %s, %s), (%s, %s, %s)
                ON CONFLICT (skill_name) DO NOTHING
            ''', ('Python', 'Programming', 'Python programming language',
                  'JavaScript', 'Programming', 'JavaScript programming',
                  'React', 'Frontend', 'React framework',
                  'Node.js', 'Backend', 'Node.js runtime',
                  'SQL', 'Database', 'SQL databases',
                  'MongoDB', 'Database', 'NoSQL database',
                  'AWS', 'Cloud', 'Amazon Web Services',
                  'Docker', 'DevOps', 'Containerization',
                  'Machine Learning', 'AI/ML', 'ML algorithms and models',
                  'Data Analysis', 'Analytics', 'Data analysis and visualization',
                  'Communication', 'Soft Skills', 'Effective communication',
                  'Leadership', 'Soft Skills', 'Team leadership',
                  'SEO', 'Marketing', 'Search engine optimization',
                  'Content Writing', 'Marketing', 'Content creation',
                  'Analytics Tools', 'Marketing', 'Google Analytics, etc'))
            print('   ✅ 15 skills')

            # Get skill IDs
            cursor.execute("SELECT id, skill_name FROM skills ORDER BY id")
            skills = {row['skill_name']: row['id'] for row in cursor.fetchall()}

            # 4. Team Skills Matrix
            print('4. Loading Team Skills Matrix...')
            app_dev = teams['App Development']
            data_eng = teams['Data Engineering']
            ai_ml = teams['AI/ML']
            marketing = teams['Marketing Team']

            senior_dev_pos = positions[('Senior Developer', app_dev)]
            dev_pos = positions[('Developer', app_dev)]
            data_eng_pos = positions[('Data Engineer', data_eng)]
            ai_eng_pos = positions[('AI Engineer', ai_ml)]
            mkt_mgr_pos = positions[('Marketing Manager', marketing)]

            cursor.execute('''
                INSERT INTO team_skills (team_id, skill_id, position_id, required_level, priority) VALUES
                (%s, %s, %s, %s, %s), (%s, %s, %s, %s, %s), (%s, %s, %s, %s, %s),
                (%s, %s, %s, %s, %s), (%s, %s, %s, %s, %s), (%s, %s, %s, %s, %s),
                (%s, %s, %s, %s, %s), (%s, %s, %s, %s, %s), (%s, %s, %s, %s, %s),
                (%s, %s, %s, %s, %s), (%s, %s, %s, %s, %s), (%s, %s, %s, %s, %s),
                (%s, %s, %s, %s, %s), (%s, %s, %s, %s, %s), (%s, %s, %s, %s, %s),
                (%s, %s, %s, %s, %s), (%s, %s, %s, %s, %s), (%s, %s, %s, %s, %s)
                ON CONFLICT (team_id, skill_id, position_id) DO NOTHING
            ''', (app_dev, skills['Python'], senior_dev_pos, 'Expert', 'High',
                  app_dev, skills['JavaScript'], senior_dev_pos, 'Expert', 'High',
                  app_dev, skills['React'], senior_dev_pos, 'Advanced', 'High',
                  app_dev, skills['Node.js'], senior_dev_pos, 'Advanced', 'Medium',
                  app_dev, skills['SQL'], senior_dev_pos, 'Advanced', 'High',
                  app_dev, skills['Python'], dev_pos, 'Advanced', 'High',
                  app_dev, skills['JavaScript'], dev_pos, 'Advanced', 'High',
                  app_dev, skills['React'], dev_pos, 'Intermediate', 'Medium',
                  data_eng, skills['Python'], data_eng_pos, 'Expert', 'High',
                  data_eng, skills['SQL'], data_eng_pos, 'Expert', 'High',
                  data_eng, skills['Data Analysis'], data_eng_pos, 'Advanced', 'High',
                  data_eng, skills['AWS'], data_eng_pos, 'Advanced', 'Medium',
                  ai_ml, skills['Python'], ai_eng_pos, 'Expert', 'High',
                  ai_ml, skills['Machine Learning'], ai_eng_pos, 'Expert', 'High',
                  ai_ml, skills['Data Analysis'], ai_eng_pos, 'Advanced', 'High',
                  marketing, skills['SEO'], mkt_mgr_pos, 'Expert', 'High',
                  marketing, skills['Content Writing'], mkt_mgr_pos, 'Advanced', 'High',
                  marketing, skills['Analytics Tools'], mkt_mgr_pos, 'Advanced', 'Medium'))
            print('   ✅ 18 team-skill mappings')

            # 5. Employee Skills
            print('5. Loading Employee Skills...')
            cursor.execute('''
                INSERT INTO employee_skills (emp_id, skill_id, proficiency_level, years_experience, certified) VALUES
                (3, %s, %s, %s, %s), (3, %s, %s, %s, %s), (3, %s, %s, %s, %s), (3, %s, %s, %s, %s),
                (4, %s, %s, %s, %s), (4, %s, %s, %s, %s), (4, %s, %s, %s, %s),
                (7, %s, %s, %s, %s), (7, %s, %s, %s, %s), (7, %s, %s, %s, %s),
                (8, %s, %s, %s, %s), (8, %s, %s, %s, %s), (8, %s, %s, %s, %s),
                (5, %s, %s, %s, %s), (5, %s, %s, %s, %s), (5, %s, %s, %s, %s)
                ON CONFLICT (emp_id, skill_id) DO NOTHING
            ''', (skills['Python'], 'Expert', 5, True,
                  skills['JavaScript'], 'Expert', 6, False,
                  skills['React'], 'Advanced', 4, False,
                  skills['SQL'], 'Expert', 5, True,
                  skills['Python'], 'Advanced', 3, False,
                  skills['JavaScript'], 'Advanced', 3, False,
                  skills['React'], 'Intermediate', 2, False,
                  skills['Python'], 'Expert', 4, True,
                  skills['SQL'], 'Expert', 5, True,
                  skills['Data Analysis'], 'Advanced', 4, False,
                  skills['Python'], 'Expert', 5, True,
                  skills['Machine Learning'], 'Expert', 4, True,
                  skills['Data Analysis'], 'Advanced', 3, False,
                  skills['SEO'], 'Expert', 6, True,
                  skills['Content Writing'], 'Advanced', 5, False,
                  skills['Analytics Tools'], 'Expert', 5, True))
            print('   ✅ 16 employee skills')

            # 6. Custom Profile Fields
            print('6. Loading Custom Profile Fields...')
            cursor.execute('''
                INSERT INTO custom_profile_fields (field_name, field_label, field_type, required, category, status) VALUES
                (%s, %s, %s, %s, %s, %s), (%s, %s, %s, %s, %s, %s),
                (%s, %s, %s, %s, %s, %s), (%s, %s, %s, %s, %s, %s),
                (%s, %s, %s, %s, %s, %s), (%s, %s, %s, %s, %s, %s),
                (%s, %s, %s, %s, %s, %s), (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (field_name) DO NOTHING
            ''', ('linkedin_url', 'LinkedIn Profile', 'text', False, 'Social Media', 'Active',
                  'github_url', 'GitHub Profile', 'text', False, 'Social Media', 'Active',
                  'languages_spoken', 'Languages Spoken', 'text', False, 'Personal', 'Active',
                  'education_level', 'Education Level', 'text', False, 'Education', 'Active',
                  'university', 'University', 'text', False, 'Education', 'Active',
                  'shirt_size', 'T-Shirt Size', 'text', False, 'Personal', 'Active',
                  'dietary_restrictions', 'Dietary Restrictions', 'text', False, 'Personal', 'Active',
                  'hobbies', 'Hobbies', 'text', False, 'Personal', 'Active'))
            print('   ✅ 8 custom profile fields')

            # Get custom field IDs
            cursor.execute("SELECT id, field_name FROM custom_profile_fields")
            custom_fields = {row['field_name']: row['id'] for row in cursor.fetchall()}

            # 7. Employee Custom Field Values
            print('7. Loading Employee Custom Field Values...')
            cursor.execute('''
                INSERT INTO employee_custom_fields (emp_id, field_id, field_value) VALUES
                (%s, %s, %s), (%s, %s, %s), (%s, %s, %s), (%s, %s, %s),
                (%s, %s, %s), (%s, %s, %s)
                ON CONFLICT (emp_id, field_id) DO NOTHING
            ''', (3, custom_fields['linkedin_url'], 'https://linkedin.com/in/sarah-developer',
                  3, custom_fields['github_url'], 'https://github.com/sarahdev',
                  3, custom_fields['languages_spoken'], 'English, Spanish',
                  3, custom_fields['education_level'], 'Bachelor of Computer Science',
                  4, custom_fields['linkedin_url'], 'https://linkedin.com/in/mike-chen',
                  4, custom_fields['languages_spoken'], 'English, Mandarin'))
            print('   ✅ 6 custom field values')

            # 8. Sample Profile Update Requests
            print('8. Loading Sample Profile Update Requests...')
            cursor.execute('''
                INSERT INTO profile_update_requests (emp_id, field_name, current_value, requested_value, reason, status) VALUES
                (%s, %s, %s, %s, %s, %s),
                (%s, %s, %s, %s, %s, %s)
            ''', (3, 'phone', '+1234567892', '+1555666777', 'Changed phone number', 'Pending',
                  4, 'address', None, '123 Main St, SF, CA', 'Updated home address', 'Pending'))
            print('   ✅ 2 profile update requests')

            conn.commit()

            print('\n' + '=' * 60)
            print('✅ ALL SAMPLE DATA LOADED SUCCESSFULLY!')
            print('=' * 60)

            print('\nSummary:')
            print('  • 4 Teams (App Dev, Data Eng, AI/ML, Marketing)')
            print('  • 8 Positions (under teams)')
            print('  • 15 Skills (Python, JS, React, SQL, ML, etc.)')
            print('  • 18 Team-Skill-Position mappings')
            print('  • 16 Employee skills assigned')
            print('  • 8 Custom profile fields')
            print('  • 6 Custom field values')
            print('  • 2 Profile update requests')

            return True

    except Exception as e:
        print(f'\n❌ ERROR: {str(e)}')
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    load_sample_data()
