# 🔧 PostgreSQL Connection Troubleshooting Guide

## Issue: IPv6 "Cannot assign requested address"

### Problem
Streamlit Cloud tries to connect via IPv6, but IPv6 routing may not be properly configured, causing connection failures.

### Solution ✅
Use the **Supabase Connection Pooler** with SSL instead of direct database connection:

```toml
[connections.postgresql]
url = "postgres://postgres:admin748745420701@db.goblvamlyonthzsjfzgr.supabase.co:6543/postgres?sslmode=require"
```

### Why This Works
1. **Connection Pooler (port 6543)** handles network routing better than direct connection (port 5432)
2. **SSL mode** ensures encrypted, stable connection
3. **Transaction mode** pooler is optimized for serverless environments like Streamlit Cloud

---

## Issue: "Tenant or user not found"

### Problem
Wrong URL format for connection pooler.

### Solution ✅
- Use `postgres://` (not `postgresql://`)
- Format: `postgres://user:password@host:6543/database?sslmode=require`

### Incorrect ❌
```
postgresql://postgres.PROJECT:password@pooler-host:6543/postgres
```

### Correct ✅
```
postgres://postgres:password@db.PROJECT.supabase.co:6543/postgres?sslmode=require
```

---

## Issue: Connection timeout

### Problem
Network timeout during connection attempt.

### Solution ✅
The database.py file now includes automatic connection parameters:
- `connect_timeout=10` - Wait up to 10 seconds
- `keepalives=1` - Enable TCP keepalives
- `keepalives_idle=30` - Send keepalive after 30s idle
- `keepalives_interval=10` - Retry every 10s
- `keepalives_count=5` - Try 5 times before giving up

---

## Issue: Connection works locally but not on Streamlit Cloud

### Problem
Local Windows DNS issues vs Streamlit Cloud Linux environment.

### Solution ✅
This is **expected behavior**:
- ❌ Windows may fail DNS resolution (IPv6 issues)
- ✅ Streamlit Cloud Linux will work fine

**Action:** Deploy to Streamlit Cloud and test there, not locally on Windows.

---

## Issue: SSL/TLS connection error

### Problem
SSL certificate verification issues.

### Solution ✅
Add `sslmode=require` to connection string:
```
postgres://user:pass@host:6543/db?sslmode=require
```

If still failing, try:
```
postgres://user:pass@host:6543/db?sslmode=prefer
```

---

## Testing Checklist

### ✅ Before Deployment
- [ ] Supabase project is active (check supabase.com dashboard)
- [ ] Password is correct in connection string
- [ ] Using port **6543** (pooler), not 5432 (direct)
- [ ] Using **postgres://** scheme, not postgresql://
- [ ] Added **?sslmode=require** parameter

### ✅ After Deployment
- [ ] Secrets added in Streamlit Cloud (Settings → Secrets)
- [ ] App restarted after adding secrets
- [ ] Check Streamlit Cloud logs for errors
- [ ] Verify tables created in Supabase dashboard

---

## Connection String Components

### Format
```
postgres://[USER]:[PASSWORD]@[HOST]:[PORT]/[DATABASE]?[PARAMETERS]
```

### Your Values
```
postgres://postgres:admin748745420701@db.goblvamlyonthzsjfzgr.supabase.co:6543/postgres?sslmode=require
```

Breakdown:
- **USER:** `postgres`
- **PASSWORD:** `admin748745420701`
- **HOST:** `db.goblvamlyonthzsjfzgr.supabase.co`
- **PORT:** `6543` (Transaction Pooler)
- **DATABASE:** `postgres`
- **SSL:** `sslmode=require`

---

## Alternative: Direct Connection (If Pooler Fails)

If connection pooler doesn't work, try direct connection:

```toml
[connections.postgresql]
url = "postgres://postgres:admin748745420701@db.goblvamlyonthzsjfzgr.supabase.co:5432/postgres?sslmode=require"
```

**Note:** Direct connection may have IPv6 issues on some Streamlit Cloud regions.

---

## Checking Supabase Status

1. Go to https://supabase.com/dashboard
2. Select project: `goblvamlyonthzsjfzgr`
3. Check **Project Status** (should be "Active")
4. Go to **Settings → Database**
5. Verify connection strings match

---

## Streamlit Cloud Logs

To check what's happening:
1. Go to Streamlit Cloud dashboard
2. Click your app
3. Click "Manage app"
4. Click "Logs" tab
5. Look for connection error messages

Common log messages:
- ✅ "PostgreSQL database fully initialized" = SUCCESS
- ❌ "Cannot assign requested address" = IPv6 issue (use pooler)
- ❌ "Tenant or user not found" = Wrong URL format
- ❌ "Connection timeout" = Network issue (check Supabase status)

---

## Still Having Issues?

### Option 1: Use Session Pooling (More Connections)
```
postgres://postgres:admin748745420701@db.goblvamlyonthzsjfzgr.supabase.co:6543/postgres?sslmode=require&pgbouncer=true
```

### Option 2: Use IPv4 Host (Bypass IPv6)
Get IPv4 address:
```bash
nslookup db.goblvamlyonthzsjfzgr.supabase.co
```

Then use IP directly:
```
postgres://postgres:admin748745420701@[IP_ADDRESS]:6543/postgres?sslmode=require
```

### Option 3: Contact Support
- Supabase Support: https://supabase.com/support
- Streamlit Support: https://discuss.streamlit.io/

---

**Updated:** March 18, 2026
**Connection Method:** Supabase Transaction Pooler with SSL
