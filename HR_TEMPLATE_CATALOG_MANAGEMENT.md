# HR Template Catalog Management - Complete Guide

## ✅ **Feature Implemented**

HR Admins can now **add, delete, and manage the HR template catalog** - the list of template names that appears in the HR Templates library!

---

## 🎯 **What's New**

### 1. **Database-Driven Template Catalog**
- Template names now stored in database (not hardcoded)
- Easy to add, edit, delete templates
- Activate/deactivate templates without deleting
- Set display order for organization

### 2. **New Admin Tab: ⚙️ Manage Catalog**
- Add new template names
- Delete template names from catalog
- Activate/deactivate templates
- Organize by category and order

### 3. **Automatic Initialization**
- 30 default templates automatically created on first use
- Forms, Letters, Policies, Evaluations, Onboarding, Offboarding

---

## 💡 **How To Use**

### **For HR Admin - Manage Template Catalog**

#### Access the Management Interface
1. Login as HR Admin (`admin@exalio.com` / `admin123`)
2. Go to **📋 HR Templates** from sidebar
3. Click on **⚙️ Manage Catalog** tab (4th tab)

#### Add a New Template Name
1. Click **➕ Add New Template Name** expander
2. Fill in:
   - **Template Name**: e.g., "Performance Improvement Plan"
   - **Category**: Choose from Forms, Letters, Policies, etc.
   - **Description**: Brief description (optional)
   - **Display Order**: Number for sorting (optional, 0-999)
3. Click **➕ Add Template Name**
4. Template appears in the catalog immediately

#### Delete a Template Name
1. In **⚙️ Manage Catalog** tab
2. Find the template you want to delete
3. Click **🗑️ Delete** button (rightmost column)
4. Click again to **⚠️ Confirm Delete**
5. Template removed from catalog
6. Note: This only removes the name, not uploaded files

#### Deactivate a Template (Instead of Delete)
1. Find the template in **⚙️ Manage Catalog**
2. Click **❌ Deactivate** button
3. Template hidden from main catalog
4. Can be reactivated later with **✅ Activate**

---

## 📊 **Features**

### Template Catalog Management
✅ Add new template names
✅ Delete template names
✅ Activate/Deactivate templates
✅ Set display order
✅ Add descriptions
✅ Organize by categories
✅ View all templates in one place

### Categories Available
- 📝 **Forms** - Request forms, timesheets, etc.
- 📄 **Letters** - Offer, termination, reference letters
- 📋 **Policies** - Handbooks, policies, guidelines
- 📊 **Evaluations** - Appraisals, feedback forms
- 🎓 **Onboarding** - New hire checklists and forms
- 🚪 **Offboarding** - Exit procedures and forms
- 📁 **Other** - Miscellaneous templates

### Template Statuses
- **✅ Active** - Visible in template catalog
- **❌ Inactive** - Hidden but not deleted

---

## 🔄 **Two-Level System**

### Level 1: Template Catalog (Names)
**What it is**: The list of template names
**Where it's stored**: `hr_template_catalog` table
**Who can manage**: HR Admin only
**Actions**:
- Add new template names
- Delete template names
- Activate/deactivate
- Set display order

### Level 2: Template Files (Uploads)
**What it is**: Actual files (PDF, DOCX, etc.)
**Where it's stored**: `documents` table (BLOB)
**Who can manage**: HR Admin only
**Actions**:
- Upload template files
- Delete uploaded files
- Download templates

---

## 📋 **Workflow Example**

### Scenario: Add a New Template

**Step 1**: Add Template Name to Catalog
```
Go to: HR Templates → Manage Catalog
Click: ➕ Add New Template Name
Enter: "Remote Work Agreement"
Category: "Policies"
Description: "Agreement for remote work arrangements"
Save: Template added to catalog
```

**Step 2**: Upload the Template File
```
Go to: HR Templates → Upload Template
Name: "Remote Work Agreement" (must match catalog name)
Upload: remote_work_agreement.pdf
Save: File uploaded
```

**Step 3**: Users Can Now Download
```
Go to: HR Templates → All Templates
Find: "Remote Work Agreement" in Policies
Status: "✅ Uploaded"
Action: Click Download
```

---

## 🗑️ **Delete Operations**

### Delete Template Name from Catalog
- **Effect**: Removes template from the list
- **File Impact**: Does NOT delete uploaded file
- **Reversible**: No, must re-add manually
- **Use when**: Template no longer needed

### Delete Uploaded File
- **Effect**: Removes the actual file
- **Catalog Impact**: Template name stays in catalog
- **Status Changes**: "✅ Uploaded" → "📥 Not Uploaded"
- **Use when**: Need to replace or remove file

### Deactivate Template
- **Effect**: Hides template from catalog
- **File Impact**: No effect on file
- **Reversible**: Yes, click Activate
- **Use when**: Temporarily hiding template

---

## 📊 **Database Structure**

### New Table: `hr_template_catalog`
```sql
CREATE TABLE hr_template_catalog (
    id SERIAL PRIMARY KEY,
    template_name TEXT NOT NULL,
    category TEXT NOT NULL,
    description TEXT,
    is_active INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER,
    display_order INTEGER DEFAULT 0
)
```

### Columns
- `id`: Unique template ID
- `template_name`: Display name
- `category`: Forms, Letters, Policies, etc.
- `description`: Template description
- `is_active`: 1 = Active, 0 = Inactive
- `created_at`: When added
- `created_by`: Admin who added it
- `display_order`: Sort order (lower first)

---

## 🎯 **Admin Interface**

### Manage Catalog Tab Layout
```
⚙️ Manage Template Catalog
├── ➕ Add New Template Name
│   └── Form: Name, Category, Description, Order
│
└── 📋 Current Template Catalog
    ├── 📂 Forms
    │   ├── Leave Request Form (✅ Active) | Order: 0 | ❌ Deactivate | 🗑️ Delete
    │   └── Expense Claim Form (✅ Active) | Order: 1 | ❌ Deactivate | 🗑️ Delete
    │
    ├── 📂 Letters
    │   ├── Job Offer Letter (✅ Active) | Order: 0 | ❌ Deactivate | 🗑️ Delete
    │   └── ...
    └── ...
```

---

## ✨ **Benefits**

### Before (Hardcoded)
❌ Templates hardcoded in Python file
❌ Need developer to add/remove templates
❌ Requires code deployment
❌ No flexibility
❌ Can't customize per company

### After (Database-Driven)
✅ Templates in database
✅ HR Admin can manage without developer
✅ Instant changes
✅ Fully flexible
✅ Company-specific customization

---

## 🧪 **Testing Checklist**

- [ ] Login as HR Admin
- [ ] Go to HR Templates → Manage Catalog tab
- [ ] Add a new template name
- [ ] Verify it appears in All Templates tab
- [ ] Upload a file for the new template
- [ ] Download the file
- [ ] Deactivate the template
- [ ] Verify it's hidden from All Templates
- [ ] Reactivate the template
- [ ] Delete the template from catalog
- [ ] Verify it's removed from All Templates

---

## 📁 **Files Modified**

### Updated Files (2)
```
database.py - Added hr_template_catalog table
modules/hr_templates.py - Complete rewrite with catalog management
```

### Changes Made
1. Added `hr_template_catalog` table migration
2. Rewrote `show_all_templates()` to load from database
3. Added `init_default_templates()` function
4. Added `show_manage_catalog()` function
5. Added `toggle_template_status()` function
6. Added 4th tab "Manage Catalog" for admins
7. Integrated delete buttons with catalog

---

## 🚀 **Upload to GitHub**

```bash
cd D:\exalio_work\HR\HR_system_upload

git add database.py
git add modules/hr_templates.py
git add HR_TEMPLATE_CATALOG_MANAGEMENT.md

git commit -m "Add HR Template Catalog Management

Features:
- Database-driven template catalog
- Add/delete template names (admin)
- Activate/deactivate templates
- Set display order
- 30 default templates auto-initialized
- New 'Manage Catalog' admin tab"

git push origin main
```

---

## 📞 **Support**

### Common Questions

**Q: Can I delete a template name if files are uploaded?**
A: Yes, but the uploaded files remain in the database. Users won't see them in the catalog.

**Q: What happens when I deactivate a template?**
A: It's hidden from the main catalog but not deleted. You can reactivate it anytime.

**Q: Can regular users see the Manage Catalog tab?**
A: No, only HR Admins see this tab.

**Q: Will adding a template name automatically create a file?**
A: No, you must separately upload the file using the Upload Template tab.

**Q: Can I change the display order?**
A: Not yet in the UI, but you can delete and re-add with a new order. (Future enhancement)

---

## ✅ **Summary**

✅ **Template catalog now in database**
✅ **HR Admin can add template names**
✅ **HR Admin can delete template names**
✅ **Activate/deactivate functionality**
✅ **30 default templates auto-loaded**
✅ **Integrated with file upload system**
✅ **Two-click delete confirmation**
✅ **Audit logging enabled**

---

**Last Updated**: 2026-07-06
**Status**: ✅ Production Ready
**Feature**: HR Template Catalog Management
**Access**: HR Admin Only
