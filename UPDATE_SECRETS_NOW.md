# 🚨 URGENT: UPDATE YOUR STREAMLIT CLOUD SECRETS NOW!

## The Error You're Seeing

```
connection to server at "db.goblvamlyonthzsjfzgr.supabase.co" (IPv6), port 6543 failed
```

**This means:** Your Streamlit Cloud app is still using the **OLD connection string** with the IPv6 hostname!

---

## ✅ FIX IT NOW (2 minutes)

### Step 1: Open Streamlit Cloud Settings

1. Go to https://share.streamlit.io
2. Find your deployed app
3. Click the **⋮** (three dots) menu
4. Click **"Settings"**

### Step 2: Update Secrets

1. Click the **"Secrets"** tab
2. **DELETE EVERYTHING** in the secrets box
3. Copy and paste this EXACTLY:

```toml
[connections.postgresql]
url = "postgres://postgres.goblvamlyonthzsjfzgr:admin748745420701@aws-0-eu-central-1.pooler.supabase.com:5432/postgres"
```

### Step 3: Save and Restart

1. Click **"Save"**
2. The app will restart automatically (wait 30-60 seconds)
3. Refresh your browser
4. Check if error is gone

---

## ⚠️ What You Had Before (WRONG)

Your current secrets probably have:
```toml
[connections.postgresql]
url = "postgres://postgres:admin748745420701@db.goblvamlyonthzsjfzgr.supabase.co:6543/postgres?sslmode=require"
```

**Problem:** `db.goblvamlyonthzsjfzgr.supabase.co` has IPv6!

---

## ✅ What You Need Now (CORRECT)

```toml
[connections.postgresql]
url = "postgres://postgres.goblvamlyonthzsjfzgr:admin748745420701@aws-0-eu-central-1.pooler.supabase.com:5432/postgres"
```

**Why:** `aws-0-eu-central-1.pooler.supabase.com` is IPv4-only!

---

## 🔍 How to Verify It's Working

### After saving secrets, check logs:

1. In Streamlit Cloud, click **"Manage app"**
2. Click **"Logs"** tab
3. Look for:

✅ **SUCCESS:**
```
✅ PostgreSQL database fully initialized!
```

❌ **STILL WRONG:**
```
connection to server at "db.goblvamlyonthzsjfzgr.supabase.co"
```
If you still see the old hostname, secrets weren't updated correctly.

---

## 🎯 Key Differences

| Component | ❌ OLD (IPv6 - FAILS) | ✅ NEW (IPv4 - WORKS) |
|-----------|----------------------|---------------------|
| **Hostname** | `db.goblvamlyonthzsjfzgr.supabase.co` | `aws-0-eu-central-1.pooler.supabase.com` |
| **Username** | `postgres` | `postgres.goblvamlyonthzsjfzgr` |
| **Port** | 6543 | 5432 |
| **Issue** | Resolves to IPv6 → FAILS | IPv4-only → WORKS |

---

## 📸 Screenshot Guide

### Where to Find Secrets:

```
Streamlit Cloud Dashboard
  └── Your App
      └── ⋮ (three dots menu)
          └── Settings
              └── Secrets tab ← UPDATE HERE!
```

---

## 🆘 If Still Not Working

### Option 1: Force Restart
1. Update secrets
2. Click **"Reboot app"** in Streamlit Cloud
3. Wait for fresh start

### Option 2: Check Secret Format
Make sure there are NO:
- Extra spaces
- Extra quotes
- Missing characters
- Wrong hostname

### Option 3: Redeploy
1. Update secrets
2. Go to Streamlit Cloud → Advanced → "Clear cache"
3. Redeploy app

---

## ✅ Exact Copy-Paste (No Typos!)

```toml
[connections.postgresql]
url = "postgres://postgres.goblvamlyonthzsjfzgr:admin748745420701@aws-0-eu-central-1.pooler.supabase.com:5432/postgres"
```

**Triple-check:**
- [ ] Hostname: `aws-0-eu-central-1.pooler.supabase.com`
- [ ] Username: `postgres.goblvamlyonthzsjfzgr`
- [ ] Password: `admin748745420701`
- [ ] Port: `5432`
- [ ] No extra parameters
- [ ] No typos

---

## 🎉 After Update

Once saved correctly, you'll see:
1. App restarts automatically
2. Logs show: "Initializing PostgreSQL database..."
3. Logs show: "✅ PostgreSQL database fully initialized!"
4. Login page loads
5. Can login with `admin` / `admin123`

---

**DO THIS NOW:** Update your Streamlit Cloud secrets with the IPv4 pooler connection string!
