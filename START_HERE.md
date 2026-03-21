# 🚀 START HERE - Quick Deployment Guide

## You're Seeing IPv6 Connection Errors?

**READ THIS FIRST:** `CRITICAL_IPv4_FIX.md`

---

## 🎯 Quick 3-Step Deployment

### Step 1: Upload to GitHub (5 minutes)
1. Go to https://github.com/new
2. Create repository: `hr-system` (Private recommended)
3. **DON'T** add README
4. Click "uploading an existing file"
5. Drag ALL files from this folder (`HR_system_upload`)
6. Commit changes

### Step 2: Deploy on Streamlit Cloud (2 minutes)
1. Go to https://share.streamlit.io
2. Click "New app"
3. Select your `hr-system` repository
4. Main file: `app.py`
5. Click "Deploy"

### Step 3: Add Database Secret (1 minute) ⚠️ CRITICAL
1. In Streamlit dashboard: Click ⋮ → Settings → Secrets
2. Copy from `STREAMLIT_SECRETS.txt` file
3. Paste this EXACTLY:

```toml
[connections.postgresql]
url = "postgres://postgres.goblvamlyonthzsjfzgr:admin748745420701@aws-0-eu-central-1.pooler.supabase.com:5432/postgres"
```

4. Click Save
5. Wait 30 seconds for restart

---

## ✅ Success Checklist

After deployment:
- [ ] App loads without errors
- [ ] See login page
- [ ] Can login with: `admin` / `admin123`
- [ ] Dashboard shows all 32 HR modules
- [ ] No "Cannot assign requested address" errors in logs

---

## 📚 Detailed Documentation

- **`MANUAL_UPLOAD_GUIDE.md`** - Complete step-by-step instructions
- **`CRITICAL_IPv4_FIX.md`** - Why we use IPv4-only pooler
- **`STREAMLIT_SECRETS.txt`** - Connection string reference
- **`CONNECTION_TROUBLESHOOTING.md`** - If you have issues

---

## 🆘 Having Problems?

### Error: "Cannot assign requested address"
→ Read: `CRITICAL_IPv4_FIX.md`
→ Ensure you're using the IPv4-only AWS pooler endpoint

### Error: "Tenant or user not found"
→ Check username includes project reference: `postgres.goblvamlyonthzsjfzgr`

### Tables not appearing
→ Check Streamlit Cloud logs
→ Verify secrets are saved correctly

---

## 📞 Support

- Streamlit Community: https://discuss.streamlit.io/
- Supabase Support: https://supabase.com/support

---

**Total Time:** ~10 minutes to full deployment 🚀
