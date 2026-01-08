# Database Connection Pool Exhaustion Fix

## 🚨 **Problem**

With Supabase Session Pooling mode (free/minimal tier), connection pool gets exhausted because:
- Cursors are not being closed
- Connections stay locked until cursors are closed
- Limited pool size (Session mode has strict limits)
- Multiple gunicorn workers each holding connections

## ✅ **Fixes Applied**

### 1. Fixed Critical Methods (Called on Every Request)
- ✅ `get_user_by_id()` - Called by Flask-Login on every request
- ✅ `get_user_by_email()` - Called during login
- ✅ `get_user_by_username()` - Called during login
- ✅ `create_user()` - Called during registration
- ✅ `update_last_login()` - Called after login
- ✅ `update_notification_email()` - Called in settings
- ✅ `get_active_price_alerts()` - Called in notifications
- ✅ `_ensure_connection()` - Fixed cursor cleanup in connection test

### 2. Fixed web_app.py
- ✅ `/listings` route - Fixed cursor not being closed

## ⚠️ **Remaining Issue**

There are **267 cursor operations** in `src/database/db.py` that still need cursor cleanup. The critical ones are fixed, but others may still cause issues under load.

## 🔧 **Long-Term Solutions**

### Option 1: Fix All Methods (Recommended)
Add try/finally blocks to all database methods to ensure cursors are closed:

```python
def some_method(self):
    cursor = None
    try:
        cursor = self._get_cursor()
        cursor.execute(...)
        return result
    finally:
        if cursor:
            try:
                cursor.close()
            except Exception:
                pass
```

### Option 2: Use Helper Method
Use the `_with_cursor()` helper for new code:

```python
def some_method(self):
    return self._with_cursor(lambda cursor: 
        cursor.execute(...)
        return cursor.fetchone()
    )
```

### Option 3: Connection Pooling (Advanced)
Implement application-level connection pooling with psycopg2.pool, but this requires significant refactoring.

## 📋 **Immediate Actions**

1. **Monitor connection pool usage** - Check Supabase dashboard for connection count
2. **Reduce gunicorn workers** - If using 2 workers, try 1 worker temporarily
3. **Fix remaining high-traffic methods** - Methods called frequently should be prioritized

## 🎯 **Priority Methods to Fix Next**

Based on usage patterns, these should be fixed next:
- All `get_*` methods (frequently called)
- All `create_*` methods (called during user actions)
- All `update_*` methods (called during edits)
- Methods in routes that handle form submissions

## 📝 **Session Pooling Constraints**

With Supabase Session Pooling:
- **Limited connections** - Pool size is small
- **One transaction per connection** - Can't have multiple active transactions
- **Cursors must be closed** - Connection stays locked until cursor closes
- **No Transaction Pooling** - Can't use transaction mode without IPv6

## ✅ **What's Working Now**

- Critical authentication methods fixed
- Connection test fixed
- Most frequently called methods fixed

The connection pool exhaustion should be significantly reduced, but may still occur under heavy load until all methods are fixed.

---

**Last Updated**: After fixing critical database cursor cleanup issues
**Status**: Critical methods fixed, remaining methods need attention

