# Poshmark CSV Format

## Overview
Poshmark supports bulk CSV upload through their web interface.

**Integration Type:** CSV Bulk Upload
**Automation Level:** Semi-automated (requires manual upload to Poshmark website)
**Connection Test:** Username/Password login validation

---

## CSV Format Specification

### Required Fields

| Field | Type | Max Length | Description | Example |
|-------|------|------------|-------------|---------|
| `Title` | String | 80 | Item title | "Vintage Nike Swoosh Hoodie Size L" |
| `Description` | String | 10,000 | Item description with condition details | "Great condition vintage..." |
| `Price` | Decimal | - | Price in USD (no $ sign) | 45.00 |
| `Category` | String | - | Poshmark category | "Women > Sweaters" |
| `Size` | String | - | Item size | "M", "Large", "8", "OS" |
| `Brand` | String | - | Brand name | "Nike" |
| `Condition` | String | - | See condition mapping below | "Like new" |
| `Color` | String | - | Primary color | "Blue" |

### Optional Fields

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `Quantity` | Integer | Stock quantity (default: 1) | 1 |
| `SKU` | String | Internal SKU for tracking | "NIKE-001" |
| `Image1` | URL | Primary image URL | https://... |
| `Image2-Image8` | URL | Additional image URLs (up to 8 total) | https://... |

---

## Condition Mapping

Poshmark uses these exact condition terms:

| Internal Condition | Poshmark Condition |
|-------------------|-------------------|
| `new_with_tags` | "New with tags" |
| `new_without_tags` | "New without tags" |
| `excellent` | "Like new" |
| `good` | "Good" |
| `fair` | "Fair" |
| `poor` | "Poor" |

---

## Category Structure

Poshmark uses a two-level category system: `Department > Category`

### Common Departments:
- Women
- Men
- Kids
- Home
- Electronics
- Pets

### Example Categories:
```
Women > Dresses
Women > Tops > Blouses
Men > Shoes > Sneakers
Kids > Toys
Home > Bedding
```

---

## Image Requirements

- **Format:** JPG, PNG
- **Count:** 1-8 images per listing
- **Resolution:** Minimum 400x400px, recommended 1200x1200px
- **Background:** Clean, uncluttered background recommended
- **Order:** First image is the cover photo

---

## Sample CSV

See `sample.csv` in this folder for a complete example.

---

## Upload Instructions

1. **Export CSV from Rebel Operator:**
   - Go to Listings page
   - Select listings to export
   - Click "Export" → "Poshmark CSV"

2. **Upload to Poshmark:**
   - Log in to Poshmark.com
   - Go to Account → Bulk Upload Tool
   - Upload the CSV file
   - Review and publish listings

3. **Credential Requirements:**
   - Username or Email
   - Password

---

## Limitations

- **No Direct API:** Poshmark does not offer a public API
- **Manual Upload Required:** CSV must be uploaded through Poshmark website
- **Rate Limits:** Poshmark may limit number of listings uploaded per day
- **Review Required:** Each listing may need manual review before going live

---

## Troubleshooting

### "Invalid Category" Error
- Ensure category matches Poshmark's exact format
- Use format: `Department > Category` or `Department > Category > Subcategory`

### "Invalid Condition" Error
- Use exact condition names from the mapping table above
- Capitalize correctly (e.g., "Like new" not "like new")

### Images Not Loading
- Ensure image URLs are publicly accessible
- Use HTTPS URLs
- Verify images are JPG or PNG format

### Character Limit Exceeded
- Title: Maximum 80 characters
- Description: Maximum 10,000 characters

---

## Automation Status

✅ **CSV Generation:** Fully automated
✅ **Credential Storage:** Supported
⚠️ **Upload:** Manual (TOS prohibits automated posting)
⚠️ **Inventory Sync:** Manual status updates required

**Note:** While we can generate the CSV automatically, Poshmark's Terms of Service prohibit automated posting. Users must manually upload the CSV through Poshmark's website.

---

## See Also

- `/src/csv_exporters/poshmark_exporter.py` - CSV generation code
- `/src/csv_field_mappings.py` - Field mapping configuration
- `/docs/platforms/credentials/poshmark/` - Authentication setup
