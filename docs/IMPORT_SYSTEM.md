# Listing Import System - Reverse Sync

Rebel Operator now supports **importing existing listings FROM platforms** into your app for unified management!

---

## 📥 What It Does

Pull your existing listings from connected platforms (eBay, Poshmark, etc.) into Rebel Operator so you can:
- ✅ Manage all listings in one place
- ✅ Export them to other platforms
- ✅ Track inventory uniformly
- ✅ Avoid manual re-entry

---

## 🚀 Supported Platforms

### API Import (Fully Automated)

| Platform | Status | What Gets Imported |
|----------|--------|-------------------|
| **eBay** | ✅ Ready | Active inventory items via Trading API |
| **Etsy** | ✅ Ready | Active listings via API v3 |
| **Shopify** | ✅ Ready | All products via Admin API |
| **WooCommerce** | ⚠️ Ready (needs testing) | Products via REST API |
| **TCGplayer** | ⚠️ Coming Soon | Card listings |

### CSV Import (Semi-Automated)

| Platform | Status | Instructions |
|----------|--------|--------------|
| **Poshmark** | ✅ Ready | Export CSV from Poshmark, upload here |
| **Mercari** | ✅ Ready | Export CSV from Mercari, upload here |
| **Grailed** | ✅ Ready | Export CSV from Grailed, upload here |
| **Bonanza** | ✅ Ready | Export CSV from Bonanza, upload here |

---

## 🔧 How It Works

### API Platforms (eBay, Etsy, Shopify)

1. **Platform API Call** → Fetch active listings
2. **Transform** → Convert to UnifiedListing format
3. **Deduplicate** → Check for existing listings
4. **Save** → Store in database with import metadata

### CSV Platforms (Poshmark, Mercari, Grailed)

1. **User exports CSV** from platform
2. **Upload CSV** to Rebel Operator
3. **Parse & Transform** → Convert to UnifiedListing
4. **Deduplicate** → Skip existing listings
5. **Save** → Store in database

---

## 📡 API Endpoints

### 1. Import from Platform API

```http
POST /api/import/platform
Content-Type: application/json

{
  "platform": "ebay",
  "limit": 50
}
```

**Response:**
```json
{
  "success": true,
  "imported": 25,
  "errors": []
}
```

**Requirements:**
- Platform credentials must be configured
- Platform must support API import

---

### 2. Import from CSV

```http
POST /api/import/csv
Content-Type: multipart/form-data

platform: poshmark
file: <csv_file>
```

**Response:**
```json
{
  "success": true,
  "imported": 15,
  "errors": ["Row 10: Invalid price"]
}
```

---

### 3. Get Supported Platforms

```http
GET /api/import/supported-platforms
```

**Response:**
```json
{
  "api_platforms": ["ebay", "etsy", "shopify"],
  "csv_platforms": ["poshmark", "mercari", "grailed", "bonanza"]
}
```

---

### 4. View Import History

```http
GET /api/import/history?platform=ebay&limit=50
```

**Response:**
```json
{
  "imports": [
    {
      "id": 123,
      "title": "Vintage Nike Hoodie",
      "platform_source": "ebay",
      "imported_at": "2026-01-21T10:30:00Z",
      "price": 45.00
    }
  ]
}
```

---

### 5. Validate CSV Format

```http
POST /api/import/validate-csv
Content-Type: multipart/form-data

platform: poshmark
file: <csv_file>
```

**Response:**
```json
{
  "valid": true,
  "message": "CSV format is valid",
  "preview": ["Title,Description,Price,...", "Item 1,Great condition,45.00,..."]
}
```

---

## 🎨 UI Integration Guide

### Add Import Button to Listings Page

**Location:** `templates/listings.html`

```html
<!-- Add to toolbar, next to "Create Listing" button -->
<div class="btn-group" role="group">
    <button type="button" class="btn btn-primary" data-bs-toggle="modal" data-bs-target="#importModal">
        📥 Import Listings
    </button>
</div>

<!-- Import Modal -->
<div class="modal fade" id="importModal" tabindex="-1">
    <div class="modal-dialog">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title">Import Listings</h5>
                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
            </div>
            <div class="modal-body">
                <ul class="nav nav-tabs" role="tablist">
                    <li class="nav-item">
                        <a class="nav-link active" data-bs-toggle="tab" href="#apiImport">API Import</a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" data-bs-toggle="tab" href="#csvImport">CSV Import</a>
                    </li>
                </ul>

                <div class="tab-content mt-3">
                    <!-- API Import Tab -->
                    <div class="tab-pane fade show active" id="apiImport">
                        <form id="apiImportForm">
                            <div class="mb-3">
                                <label class="form-label">Platform</label>
                                <select class="form-select" id="apiPlatform" required>
                                    <option value="">Select platform...</option>
                                    <option value="ebay">eBay</option>
                                    <option value="etsy">Etsy</option>
                                    <option value="shopify">Shopify</option>
                                </select>
                            </div>
                            <div class="mb-3">
                                <label class="form-label">Max Listings (optional)</label>
                                <input type="number" class="form-control" id="apiLimit" min="1" max="500" placeholder="All listings">
                            </div>
                            <button type="submit" class="btn btn-primary">
                                <span id="apiImportSpinner" class="spinner-border spinner-border-sm d-none"></span>
                                Import from Platform
                            </button>
                        </form>
                        <div id="apiImportResult" class="mt-3"></div>
                    </div>

                    <!-- CSV Import Tab -->
                    <div class="tab-pane fade" id="csvImport">
                        <form id="csvImportForm">
                            <div class="mb-3">
                                <label class="form-label">Platform</label>
                                <select class="form-select" id="csvPlatform" required>
                                    <option value="">Select platform...</option>
                                    <option value="poshmark">Poshmark</option>
                                    <option value="mercari">Mercari</option>
                                    <option value="grailed">Grailed</option>
                                    <option value="bonanza">Bonanza</option>
                                </select>
                            </div>
                            <div class="mb-3">
                                <label class="form-label">CSV File</label>
                                <input type="file" class="form-control" id="csvFile" accept=".csv" required>
                            </div>
                            <button type="submit" class="btn btn-primary">
                                <span id="csvImportSpinner" class="spinner-border spinner-border-sm d-none"></span>
                                Import from CSV
                            </button>
                        </form>
                        <div id="csvImportResult" class="mt-3"></div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>
```

### Add JavaScript

```javascript
// API Import
document.getElementById('apiImportForm').addEventListener('submit', async (e) => {
    e.preventDefault();

    const platform = document.getElementById('apiPlatform').value;
    const limit = document.getElementById('apiLimit').value;
    const spinner = document.getElementById('apiImportSpinner');
    const resultDiv = document.getElementById('apiImportResult');

    spinner.classList.remove('d-none');
    resultDiv.innerHTML = '';

    try {
        const response = await fetch('/api/import/platform', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                platform: platform,
                limit: limit ? parseInt(limit) : null
            })
        });

        const data = await response.json();

        if (data.success) {
            resultDiv.innerHTML = `
                <div class="alert alert-success">
                    ✅ Successfully imported ${data.imported} listings!
                    ${data.errors.length > 0 ? `<br><small>${data.errors.length} errors occurred</small>` : ''}
                </div>
            `;
            // Reload listings page after 2 seconds
            setTimeout(() => location.reload(), 2000);
        } else {
            resultDiv.innerHTML = `<div class="alert alert-danger">❌ ${data.error}</div>`;
        }
    } catch (error) {
        resultDiv.innerHTML = `<div class="alert alert-danger">❌ Import failed: ${error.message}</div>`;
    } finally {
        spinner.classList.add('d-none');
    }
});

// CSV Import
document.getElementById('csvImportForm').addEventListener('submit', async (e) => {
    e.preventDefault();

    const platform = document.getElementById('csvPlatform').value;
    const fileInput = document.getElementById('csvFile');
    const file = fileInput.files[0];
    const spinner = document.getElementById('csvImportSpinner');
    const resultDiv = document.getElementById('csvImportResult');

    if (!file) {
        resultDiv.innerHTML = '<div class="alert alert-warning">Please select a file</div>';
        return;
    }

    spinner.classList.remove('d-none');
    resultDiv.innerHTML = '';

    const formData = new FormData();
    formData.append('platform', platform);
    formData.append('file', file);

    try {
        const response = await fetch('/api/import/csv', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (data.success) {
            resultDiv.innerHTML = `
                <div class="alert alert-success">
                    ✅ Successfully imported ${data.imported} listings!
                    ${data.errors.length > 0 ? `
                        <details class="mt-2">
                            <summary>${data.errors.length} errors</summary>
                            <ul class="small">
                                ${data.errors.map(err => `<li>${err}</li>`).join('')}
                            </ul>
                        </details>
                    ` : ''}
                </div>
            `;
            // Reload listings page after 2 seconds
            setTimeout(() => location.reload(), 2000);
        } else {
            resultDiv.innerHTML = `<div class="alert alert-danger">❌ ${data.error}</div>`;
        }
    } catch (error) {
        resultDiv.innerHTML = `<div class="alert alert-danger">❌ Import failed: ${error.message}</div>`;
    } finally {
        spinner.classList.add('d-none');
    }
});
```

---

## 🗄️ Database Schema

### New Fields in `listings` Table

```sql
-- Platform import tracking
platform_source TEXT                    -- e.g., "ebay", "poshmark"
original_platform_listing_id TEXT       -- Original listing ID on that platform
imported_at TIMESTAMP                   -- When it was imported
```

### Indexes

```sql
-- For fast duplicate detection
CREATE INDEX idx_listings_platform_source_id
ON listings(platform_source, original_platform_listing_id);

CREATE INDEX idx_listings_sku
ON listings(sku);
```

---

## 🔍 Deduplication Logic

The system checks for duplicates using these methods (in order):

1. **Platform + Listing ID:** Same `platform_source` and `original_platform_listing_id`
2. **SKU Match:** Same SKU (if provided)
3. **Title + Price Match:** Same title (case-insensitive) and price within $0.01

If a duplicate is found, the listing is **skipped** (not imported).

---

## 🧪 Testing

### Test API Import (eBay Example)

```bash
# 1. Configure eBay credentials in Settings

# 2. Test import
curl -X POST http://localhost:5000/api/import/platform \
  -H "Content-Type: application/json" \
  -d '{"platform": "ebay", "limit": 10}'
```

### Test CSV Import (Poshmark Example)

```bash
# 1. Export CSV from Poshmark website

# 2. Test upload
curl -X POST http://localhost:5000/api/import/csv \
  -F "platform=poshmark" \
  -F "file=@poshmark_export.csv"
```

---

## 📊 Import Status Tracking

Imported listings are marked with:

- **platform_source:** Shows import source (e.g., "ebay badge")
- **imported_at:** Timestamp of import
- **Platform Status:** Set to "imported" initially

You can filter imported listings:

```sql
SELECT * FROM listings
WHERE platform_source = 'ebay'
ORDER BY imported_at DESC;
```

---

## ⚠️ Limitations & Notes

### API Platforms

- **Rate Limits:** APIs have daily limits (typically 5,000 calls/day)
- **Pagination:** Large catalogs may take multiple requests
- **Token Expiry:** OAuth tokens auto-refresh but may fail if expired
- **Permissions:** Ensure API credentials have read access

### CSV Platforms

- **Manual Export:** User must download CSV from platform first
- **Format Changes:** Platform CSV formats may change over time
- **No Auto-Sync:** CSV imports are one-time, not continuous
- **Validation:** Check CSV format before importing large files

### General

- **Images:** Image URLs are imported, not downloaded locally
- **Variants:** Shopify products with variants import first variant only
- **Categories:** Platform-specific categories may not map perfectly
- **Custom Fields:** Platform-specific fields may not all transfer

---

## 🚀 Next Steps

### Immediate Tasks

1. **Run database migration:**
   ```bash
   psql $DATABASE_URL < src/database/migrations/add_import_tracking.sql
   ```

2. **Add UI to listings page** (see UI Integration Guide above)

3. **Test with one platform:**
   - Configure credentials for eBay or Poshmark
   - Try importing 5-10 listings
   - Verify they appear in listings page

### Future Enhancements

- [ ] Scheduled auto-sync from API platforms
- [ ] Bulk edit imported listings
- [ ] Import inventory quantities from platforms
- [ ] Image downloading and local storage
- [ ] Variant support for Shopify
- [ ] More platform support (Amazon, Walmart, etc.)

---

## 📞 Support

### Troubleshooting

**"No credentials found for platform"**
- Configure platform credentials in Settings → Platform Integrations

**"CSV format invalid"**
- Use `/api/import/validate-csv` to check format first
- Ensure CSV matches platform's export format

**"Import failed: Connection timeout"**
- Platform API may be down
- Check internet connection
- Try again in a few minutes

**Duplicates being imported**
- Check SKU uniqueness
- Verify deduplication logic is working
- May need to manually delete duplicates

---

## 📚 Related Documentation

- `/docs/platforms/PLATFORM_ORGANIZATION.md` - Platform integration overview
- `/docs/platforms/api-integrations/` - API documentation per platform
- `/docs/platforms/csv-formats/` - CSV format specs per platform
- `/scripts/test_platform_connections.py` - Test platform API connections

---

**Last Updated:** 2026-01-21
**Status:** ✅ Functional, ready for UI integration
