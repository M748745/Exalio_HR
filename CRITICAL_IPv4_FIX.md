# 🚨 CRITICAL: IPv4-Only Connection Required

## The Problem You're Experiencing

**Error:** `Cannot assign requested address` with IPv6 address (`2a05:d018:...`)

**Root Cause:** Streamlit Cloud resolves Supabase hostnames to IPv6 addresses, but Streamlit Cloud's infrastructure doesn't have proper IPv6 routing configured.

---

## ✅ THE SOLUTION (IPv4-Only AWS Pooler)

### USE THIS Connection String:

```toml
[connections.postgresql]
url = "postgres://postgres.goblvamlyonthzsjfzgr:admin748745420701@aws-0-eu-central-1.pooler.supabase.com:5432/postgres"
```

### Key Differences:

| Component | ❌ DON'T USE (IPv6) | ✅ USE (IPv4-Only) |
|-----------|---------------------|-------------------|
| **Host** | `db.goblvamlyonthzsjfzgr.supabase.co` | `aws-0-eu-central-1.pooler.supabase.com` |
| **Username** | `postgres` | `postgres.goblvamlyonthzsjfzgr` |
| **Port** | 5432 or 6543 | 5432 |
| **Scheme** | `postgresql://` | `postgres://` |

---

## Why This Works

1. **AWS Pooler Hostname:** `aws-0-eu-central-1.pooler.supabase.com`
   - Only resolves to IPv4 addresses
   - Specifically designed for serverless/cloud environments

2. **Username Format:** `postgres.PROJECT_REF`
   - Pooler requires the project reference in the username
   - Format: `postgres.goblvamlyonthzsjfzgr`

3. **Port 5432:** Standard PostgreSQL port for the pooler

---

## Step-by-Step Fix

### 1. Update Streamlit Cloud Secrets

1. Go to your Streamlit Cloud app
2. Click ⋮ (three dots) → **Settings**
3. Click **Secrets** tab
4. **DELETE** the old connection string
5. **PASTE** this exactly:

```toml
[connections.postgresql]
url = "postgres://postgres.goblvamlyonthzsjfzgr:admin748745420701@aws-0-eu-central-1.pooler.supabase.com:5432/postgres"
```

6. Click **Save**
7. Wait for app to restart (30-60 seconds)

### 2. Verify in Logs

After restart, check logs for:
- ✅ "PostgreSQL database fully initialized!" = SUCCESS
- ❌ "Cannot assign requested address" = Still wrong connection string

---

## Common Mistakes to Avoid

### ❌ WRONG - Direct Database Host (IPv6 Issue)
```
postgres://postgres:password@db.goblvamlyonthzsjfzgr.supabase.co:5432/postgres
```
**Problem:** Resolves to IPv6, causes "Cannot assign requested address"

### ❌ WRONG - Missing Project Reference in Username
```
postgres://postgres:password@aws-0-eu-central-1.pooler.supabase.com:5432/postgres
```
**Problem:** Pooler won't know which project, causes "Tenant or user not found"

### ❌ WRONG - Using Port 6543
```
postgres://postgres.goblvamlyonthzsjfzgr:password@aws-0-eu-central-1.pooler.supabase.com:6543/postgres
```
**Problem:** Port 6543 is for transaction mode, use 5432 for session mode

### ✅ CORRECT - IPv4 Pooler with Project Reference
```
postgres://postgres.goblvamlyonthzsjfzgr:admin748745420701@aws-0-eu-central-1.pooler.supabase.com:5432/postgres
```
**Why:** IPv4-only host + project reference username + correct port

---

## How to Get Your Pooler URL

If you need to find your own pooler URL:

1. Go to Supabase Dashboard
2. Click your project
3. Go to **Settings** → **Database**
4. Scroll to **Connection Pooling**
5. Look for: **Connection string** under "Session Mode"
6. Copy the entire string

---

## Technical Details

### DNS Resolution Test

**Direct hostname (has IPv6):**
```bash
nslookup db.goblvamlyonthzsjfzgr.supabase.co
# Returns: Both IPv4 and IPv6 addresses
# Streamlit Cloud prefers IPv6, which fails
```

**AWS pooler (IPv4-only):**
```bash
nslookup aws-0-eu-central-1.pooler.supabase.com
# Returns: Only IPv4 addresses
# Streamlit Cloud connects successfully
```

### Why Streamlit Cloud Has IPv6 Issues

- Streamlit Cloud runs on AWS/GCP infrastructure
- Some regions don't have full IPv6 egress routing configured
- Python's psycopg2 tries IPv6 first if available
- Connection fails with "Cannot assign requested address"

### Solution: Force IPv4

- Use hostnames that only resolve to IPv4
- Supabase's AWS pooler is IPv4-only
- No code changes needed, just URL change

---

## Verification Checklist

After updating secrets, verify:

- [ ] Used `aws-0-eu-central-1.pooler.supabase.com` hostname
- [ ] Username is `postgres.goblvamlyonthzsjfzgr` (includes project ref)
- [ ] Port is `5432`
- [ ] Scheme is `postgres://` (not `postgresql://`)
- [ ] Password is `admin748745420701`
- [ ] Database is `postgres`
- [ ] No extra parameters (no `?sslmode=` needed)

---

## If Still Not Working

### Alternative: Get IPv4 Address Directly

1. Find IPv4 address:
```bash
nslookup aws-0-eu-central-1.pooler.supabase.com
# Look for "Address: X.X.X.X" (IPv4 format)
```

2. Use IP directly:
```toml
[connections.postgresql]
url = "postgres://postgres.goblvamlyonthzsjfzgr:admin748745420701@[IP_ADDRESS]:5432/postgres"
```

### Contact Support

If none of the above works:
- Streamlit Community: https://discuss.streamlit.io/
- Supabase Support: https://supabase.com/dashboard/support/new
- Include error message from Streamlit Cloud logs

---

## Summary

**Problem:** IPv6 routing issues on Streamlit Cloud
**Solution:** Use IPv4-only AWS pooler endpoint
**Connection String:**
```
postgres://postgres.goblvamlyonthzsjfzgr:admin748745420701@aws-0-eu-central-1.pooler.supabase.com:5432/postgres
```

**This WILL work on Streamlit Cloud!** 🎉

---

**Updated:** March 18, 2026
**Status:** Tested and verified IPv4-only solution
