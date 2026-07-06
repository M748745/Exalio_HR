# HR Templates - Delete Functionality Added

## ✅ **Feature Added**

HR Admin users can now delete HR templates from all template views!

---

## 🎯 **What Was Added**

### Delete Buttons in HR Templates Module

1. **All Templates View** (📚 All Templates tab)
   - Delete button for uploaded standard templates (Leave Form, Expense Form, etc.)
   - Shows as 4th column next to View button
   - Only visible when template is uploaded to database

2. **Custom Templates Section** (💾 Custom Uploaded Templates)
   - Delete button for custom/user-uploaded templates
   - Shows as 4th column next to Download button
   - Only visible to HR Admin

3. **Popular Templates View** (📊 Popular Templates tab)
   - Delete button for all popular templates
   - Shows as 5th column
   - Allows cleanup of frequently used templates

---

## 🔐 **Security Features**

✅ **HR Admin Only** - Only users with HR Admin role see delete buttons
✅ **Two-Click Confirmation** - Must click twice to delete (prevents accidents)
✅ **Audit Logging** - All deletions logged to audit_log table
✅ **Visual Feedback** - Button changes color on first click for confirmation

---

## 💡 **How To Use**

### For HR Admin - Delete a Template

1. Login as HR Admin
2. Go to **📋 HR Templates** from sidebar
3. Navigate to any tab:
   - **📚 All Templates** - for standard templates
   - **💾 Custom Templates** - for custom uploads
   - **📊 Popular Templates** - for frequently downloaded

4. Find the template you want to delete
5. Click the **🗑️ Delete** button (rightmost column)
6. Button changes to **⚠️ Confirm Delete**
7. Click again to confirm deletion
8. Template is removed from database
9. Page refreshes automatically

---

## 📊 **Template Views with Delete**

### 1. All Templates Tab
```
📝 Forms
├── Leave Request Form
│   ├── Name: "Leave Request Form"
│   ├── Status: "✅ Uploaded" or "📥 Default"
│   ├── Button: "📄 View"
│   └── Admin: "🗑️ Delete" (if uploaded)
│
├── Expense Claim Form
│   └── ...
```

### 2. Custom Templates Section
```
💾 Custom Uploaded Templates
├── Custom Form XYZ
│   ├── Downloads: "📥 15 downloads"
│   ├── Button: "📥 Download"
│   └── Admin: "🗑️ Delete"
```

### 3. Popular Templates Tab
```
📊 Most Popular Templates
├── 1. Employee Handbook
│   ├── Downloads: 45
│   ├── Size: "📦 250 KB"
│   ├── Button: "📥"
│   └── Admin: "🗑️ Delete"
```

---

## 🔄 **What Gets Deleted**

When you delete a template, the following is removed:

- ✅ File content (BLOB data)
- ✅ File metadata (name, size, MIME type)
- ✅ Template record from database
- ✅ Download count statistics
- ✅ All associated information

**Note**: Templates with `category = 'HR Template'` are deleted from the `documents` table.

---

## ⚠️ **Important Notes**

1. **Permanent Deletion**
   - Deletions are permanent
   - No undo functionality
   - File content is removed from database

2. **Default vs Uploaded**
   - "📥 Default" templates cannot be deleted (not in database)
   - "✅ Uploaded" templates can be deleted (stored in database)
   - Delete button only appears for uploaded templates

3. **Impact**
   - Deleting a popular template removes it from all views
   - Users can no longer download deleted templates
   - Template name remains in predefined list (but shows as "Default")

4. **Audit Trail**
   - All deletions logged with:
     - Admin username
     - Template name
     - Timestamp
     - Template ID

---

## 📁 **Files Modified**

```
modules/hr_templates.py
```

### Changes Made:
1. Added import: `from modules.delete_utils import render_delete_button`
2. Added delete button to standard templates (line ~120)
3. Added delete button to custom templates (line ~147)
4. Added delete button to popular templates (line ~298)
5. Added conditional column layouts (3 or 4/5 columns based on admin role)

---

## 🧪 **Testing Checklist**

- [ ] Login as HR Admin
- [ ] Go to HR Templates
- [ ] Upload a test template
- [ ] Verify delete button appears
- [ ] Click delete once - verify warning shows
- [ ] Click delete twice - verify template deleted
- [ ] Check audit log for deletion record
- [ ] Verify template no longer appears in list
- [ ] Login as regular user - verify no delete buttons visible

---

## 🔧 **Technical Details**

### Delete Button Implementation

```python
# Standard Templates
if is_hr_admin() and saved:
    with col4:
        template_desc = f"Template: {template}"
        if render_delete_button("documents", saved['id'], template_desc, f"del_tpl_{saved['id']}"):
            st.rerun()

# Custom Templates
if is_hr_admin():
    with col4:
        template_desc = f"Custom Template: {template['document_name']}"
        if render_delete_button("documents", template['id'], template_desc, f"del_custom_{template['id']}"):
            st.rerun()

# Popular Templates
if is_hr_admin():
    with col5:
        template_desc = f"Popular Template: {template['document_name']}"
        if render_delete_button("documents", template['id'], template_desc, f"del_pop_{template['id']}"):
            st.rerun()
```

### Database Query

```sql
DELETE FROM documents WHERE id = %s
```

The template is deleted from the `documents` table using the `render_delete_button` utility function.

---

## 📈 **Benefits**

1. **Template Management** - Easy cleanup of outdated templates
2. **Storage Control** - Remove large files to save database space
3. **Content Curation** - Keep only relevant templates
4. **Version Control** - Delete old versions, upload new ones
5. **Error Correction** - Remove incorrectly uploaded templates

---

## 🆘 **Troubleshooting**

### Issue: Delete button not visible
**Solution**:
- Verify you're logged in as HR Admin
- Check template is uploaded ("✅ Uploaded" status)
- Default templates cannot be deleted

### Issue: Delete not working
**Solution**:
- Click twice to confirm
- Check database connection
- Verify `delete_utils` module imported

### Issue: Template still shows after delete
**Solution**:
- Refresh the page
- Template name still in predefined list (shows as "Default")
- Only database record is deleted

---

## ✨ **Summary**

✅ Delete buttons added to all HR Template views
✅ HR Admin only access
✅ Two-click confirmation for safety
✅ Audit logging enabled
✅ Works with all template types
✅ Immediate page refresh after deletion

---

**Updated**: 2026-07-06
**Status**: ✅ Complete
**Security**: HR Admin Only
**Safety**: Two-click confirmation
**Logging**: Full audit trail
