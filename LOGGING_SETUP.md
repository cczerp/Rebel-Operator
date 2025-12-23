# Logging to Supabase Storage

## Overview

Your application now automatically uploads errors and logs to a Supabase Storage bucket for centralized logging and debugging.

## Setup

### 1. Create Logs Bucket in Supabase

1. Go to your Supabase Dashboard → **Storage**
2. Click **"New bucket"**
3. Name it: `logs` (or whatever you prefer)
4. Make it **Public** (or configure RLS policies if you want private logs)
5. Click **"Create bucket"**

### 2. Configure Bucket Name (Optional)

If your logs bucket has a different name, set it in your environment variables:

```bash
# In Render or .env file
SUPABASE_LOGS_BUCKET=your-logs-bucket-name
```

Default is `logs` if not set.

## Using the Diagnostics Endpoint

### What It Does

The diagnostics endpoint checks your Supabase configuration and helps troubleshoot upload issues.

### How to Access

**Option 1: Browser (while logged in)**
```
https://your-app.com/api/supabase-diagnostics
```

**Option 2: curl**
```bash
curl https://your-app.com/api/supabase-diagnostics
```

**Option 3: JavaScript (from browser console)**
```javascript
fetch('/api/supabase-diagnostics')
  .then(r => r.json())
  .then(console.log)
```

### What It Returns

```json
{
  "environment_variables": {
    "SUPABASE_URL": {
      "set": true,
      "value_preview": "https://xxxxx.supabase.co...",
      "valid_format": true
    },
    "SUPABASE_SERVICE_ROLE_KEY": {
      "set": true,
      "length": 123
    },
    "SUPABASE_ANON_KEY": {
      "set": true,
      "length": 123
    }
  },
  "client_status": "✅ Client initialized successfully",
  "bucket_status": {
    "can_list": true,
    "available_buckets": ["listing-images", "logs"],
    "listing_images_exists": true,
    "logs_bucket_exists": true,
    "logs_bucket_name": "logs"
  },
  "errors": []
}
```

## Automatic Error Logging

Errors are automatically logged to your Supabase Storage bucket:

### What Gets Logged

- **Photo upload failures** - Full error details, traceback, context
- **Supabase Storage errors** - Upload exceptions with full details
- **User context** - User ID, file info, request details

### Log File Structure

Logs are stored as JSON files in your bucket:

```
logs/
  error/
    20250115_143022_123456.json
    20250115_143045_789012.json
  {user_id}/
    error/
      20250115_143100_345678.json
```

### Log File Format

```json
{
  "timestamp": "2025-01-15T14:30:22.123456",
  "type": "error",
  "data": {
    "error_message": "Failed to upload photo",
    "error_type": "PhotoUploadFailed",
    "traceback": "...",
    "context": {
      "files_attempted": 1,
      "user_id": "123",
      "mode": "temp"
    }
  },
  "user_id": "123"
}
```

## Viewing Logs

### Option 1: Supabase Dashboard

1. Go to **Storage** → **logs** bucket
2. Browse folders: `error/`, `info/`, `warning/`, `debug/`
3. Click any JSON file to view/download

### Option 2: Supabase Storage API

```bash
# List all error logs
curl "https://your-project.supabase.co/storage/v1/object/list/logs?prefix=error/"

# Download a specific log
curl "https://your-project.supabase.co/storage/v1/object/public/logs/error/20250115_143022_123456.json"
```

### Option 3: Programmatic Access

```python
from src.storage.log_storage import upload_log_to_storage

# Log an error
upload_log_to_storage(
    log_data={"error": "Something went wrong"},
    log_type="error",
    user_id="123"
)

# Log info
from src.storage.log_storage import log_info
log_info("User uploaded photo", {"photo_count": 3}, user_id="123")
```

## Troubleshooting

### Logs Not Uploading?

1. **Check bucket exists**: Use diagnostics endpoint
2. **Check bucket permissions**: Must be public OR have RLS policies allowing uploads
3. **Check environment variables**: `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY` must be set
4. **Check server logs**: Look for `[LOG_STORAGE ERROR]` messages

### Bucket Name Mismatch?

Set `SUPABASE_LOGS_BUCKET` environment variable to match your bucket name.

## Benefits

✅ **Centralized logging** - All errors in one place  
✅ **Easy debugging** - Full context and tracebacks  
✅ **User tracking** - See which users encounter errors  
✅ **Historical data** - Keep logs for analysis  
✅ **No database overhead** - Uses Storage, not PostgreSQL  

