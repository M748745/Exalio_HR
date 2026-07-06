# HR Template Delete Button - Troubleshooting Guide

## ❌ **Problem: Delete Button Not Showing**

If you don't see the delete button in HR Templates, follow this checklist:

---

## ✅ **Step 1: Verify You're Logged In as HR Admin**

### Check Your Login
1. Look at the top of the HR Templates page
2. You should see: **"✅ You are logged in as HR Admin - Delete buttons will appear for uploaded templates"**
3. If you see: **"ℹ️ You are logged in as a regular user"** - you need to login as admin

### Login as HR Admin
```
Username: admin@exalio.com
Password: admin123
```

### Verify Role in Sidebar
- Check the sidebar profile section
- Should show: **"HR ADMIN"** under your name

---

## ✅ **Step 2: Verify Template is Uploaded to Database**

Delete buttons ONLY appear for templates that are **uploaded to the database**.

### Check Template Status
Look at the second column in the template list:

- **"✅ Uploaded (Can Delete)"** ✅ - Delete button will appear (Admin only)
- **"✅ Uploaded"** ✅ - Template in database (non-admin view)
- **"📥 Default (Not in DB)"** ❌ - NO delete button (template not uploaded yet)

### Why "Default" Templates Have No Delete Button
- Default templates are **predefined in code**, not in database
- They serve as a **template catalog/list**
- To delete them, you must first **upload them to database**

---

## ✅ **Step 3: Upload a Template First**

If template shows "📥 Default (Not in DB)", you need to upload it:

### Upload Process
1. Go to **📋 HR Templates**
2. Click **➕ Add Template** tab
3. Fill in:
   - Template Name: e.g., "Leave Request Form"
   - Category: "Forms"
   - Document Type: "Form"
   - Description: Brief description
4. Upload the actual file (PDF, DOCX, etc.)
5. Click **📤 Upload Template**

### After Upload
- Template status changes to **"✅ Uploaded (Can Delete)"**
- Delete button (🗑️) appears in 4th column
- You can now delete the template

---

## ✅ **Step 4: Look for Delete Button Location**

Delete button appears in different columns based on view:

### All Templates Tab
```
Column 1: Template Name
Column 2: Status (Uploaded/Default)
Column 3: View Button
Column 4: 🗑️ Delete Button (Admin only, uploaded templates only)
```

### Custom Templates Section
```
Column 1: Template Name
Column 2: Download Count
Column 3: Download Button
Column 4: 🗑️ Delete Button (Admin only)
```

### Popular Templates Tab
```
Column 1: Template Name
Column 2: Downloads Metric
Column 3: Size
Column 4: Download Button
Column 5: 🗑️ Delete Button (Admin only)
```

---

## ✅ **Step 5: Test with a Sample Template**

### Quick Test
1. Login as admin@exalio.com / admin123
2. Go to HR Templates → Add Template tab
3. Create a test template:
   - Name: "Test Template"
   - Category: "Forms"
   - Type: "Form"
   - Upload any PDF file
4. Go back to All Templates tab
5. Look for "Test Template" in Forms section
6. Should see 4 columns with delete button

---

## 🔍 **Debug Information**

### What You Should See (As Admin)

#### At the Top
```
✅ You are logged in as HR Admin - Delete buttons will appear for uploaded templates
```

#### For Uploaded Templates
```
Leave Request Form | ✅ Uploaded (Can Delete) | 📄 View | 🗑️ Delete
```

#### For Non-Uploaded Templates
```
Expense Claim Form | 📥 Default (Not in DB) | 📄 View | (no delete button)
```

---

## 🐛 **Common Issues**

### Issue 1: "I'm admin but no delete button"
**Cause**: Template not uploaded to database
**Solution**: Upload the template first using Add Template tab

### Issue 2: "I uploaded but still no delete button"
**Cause**: Template name mismatch
**Solution**:
- Ensure uploaded template name EXACTLY matches predefined name
- e.g., "Leave Request Form" not "leave request form" or "Leave Request"

### Issue 3: "Button appears but doesn't work"
**Cause**: JavaScript or connection issue
**Solution**:
- Refresh the page
- Check browser console for errors
- Try a different browser

### Issue 4: "I see info message not success message"
**Cause**: Not logged in as HR Admin
**Solution**:
- Logout
- Login with admin@exalio.com / admin123
- Check role in sidebar shows "HR ADMIN"

---

## 🧪 **Testing Checklist**

Run through this checklist:

- [ ] Logged in as admin@exalio.com?
- [ ] See "✅ You are logged in as HR Admin" message?
- [ ] Role shows "HR ADMIN" in sidebar?
- [ ] Template shows "✅ Uploaded (Can Delete)" status?
- [ ] Looking in correct column (4th column for standard templates)?
- [ ] Page fully loaded (no loading indicators)?
- [ ] Browser JavaScript enabled?
- [ ] Tried refreshing the page?

---

## 📊 **Expected Behavior**

### As HR Admin
✅ See admin confirmation message at top
✅ See delete buttons for all uploaded templates
✅ Templates show "Can Delete" in status
✅ Can upload new templates
✅ Can delete uploaded templates

### As Regular User
❌ See regular user message at top
❌ NO delete buttons visible
✅ Templates show "Uploaded" (without "Can Delete")
❌ Cannot access Add Template tab
✅ Can view and download templates

---

## 🔧 **Technical Details**

### Code Check
The delete button code (line 120-124):
```python
# Admin delete button for uploaded templates
if is_hr_admin() and saved:
    with col4:
        template_desc = f"Template: {template}"
        if render_delete_button("documents", saved['id'], template_desc, f"del_tpl_{saved['id']}"):
            st.rerun()
```

### Conditions for Delete Button to Show
1. `is_hr_admin()` must return `True`
2. `saved` must not be `None` (template exists in database)
3. Template must have `category = 'HR Template'`
4. Template must have `visibility = 'Public'`

---

## 📞 **Still Not Working?**

### Check These Files Uploaded
- [ ] `modules/hr_templates.py` - Latest version with delete buttons
- [ ] `modules/delete_utils.py` - Delete utility module
- [ ] `database.py` - BLOB storage migrations
- [ ] All changes pushed to GitHub
- [ ] Streamlit Cloud redeployed

### Check Database
```sql
-- Check if any templates exist
SELECT id, document_name, category, visibility
FROM documents
WHERE category = 'HR Template';

-- Check your user role
SELECT username, role
FROM users
WHERE username = 'admin@exalio.com';
```

### Check Session State
In Streamlit app, add debug:
```python
st.write("User Role:", st.session_state.get('user_data', {}).get('role'))
st.write("Is Admin:", is_hr_admin())
```

---

## ✨ **Quick Fix Summary**

1. **Login as admin** → admin@exalio.com / admin123
2. **Upload template** → Add Template tab
3. **Verify status** → Should show "✅ Uploaded (Can Delete)"
4. **Look for button** → 4th column, right side
5. **Refresh page** → If needed

---

## 📋 **Example: Successful Delete Flow**

```
1. Login: admin@exalio.com / admin123
   ✅ Sidebar shows: HR ADMIN

2. Go to: HR Templates
   ✅ See message: "You are logged in as HR Admin"

3. Upload: Leave Request Form
   ✅ File: leave_request.pdf
   ✅ Success message appears

4. View: All Templates → Forms section
   ✅ See: "Leave Request Form | ✅ Uploaded (Can Delete) | 📄 View | 🗑️ Delete"

5. Click: 🗑️ Delete button
   ✅ Button changes to: "⚠️ Confirm Delete"
   ✅ Warning message shows

6. Click: ⚠️ Confirm Delete (again)
   ✅ Template deleted
   ✅ Page refreshes
   ✅ Status changes to: "📥 Default (Not in DB)"
```

---

**Last Updated**: 2026-07-06
**Status**: Troubleshooting Guide
**For**: HR Template Delete Feature
