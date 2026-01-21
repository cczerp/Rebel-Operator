# Editable Drafts Implementation Guide

## Files Modified

### 1. `templates/drafts.html` - Complete Redesign
- **New CSS styling** for Excel-like spreadsheet appearance
- **Editable cells** with inline editing capability
- **Change tracking** with visual indicators (yellow highlight)
- **Bulk action bar** for multi-select operations
- **Floating changes indicator** with save/discard options
- **Enhanced JavaScript** for edit functionality

### 2. `routes_main.py` - New API Endpoint
- Added `PATCH /api/update-drafts` endpoint
- Handles bulk draft field updates
- Validates user authorization
- Supports partial updates (only changed fields)

---

## Features Breakdown

### Frontend (JavaScript)

#### State Management
```javascript
let draftChanges = {};  // Tracks all changes: {draftId: {field: value}}
let currentEditingCell = null;  // Prevents multiple edits
```

#### Key Functions

**`editCell(cell)`**
- Enters edit mode for a cell
- Creates appropriate input (text/number/select)
- Handles Tab/Enter/Escape navigation

**`recordChange(draftId, field, newValue)`**
- Tracks changes in `draftChanges` object
- Shows changes indicator and save button

**`saveAllChanges()`**
- Sends all changes to backend via PATCH
- Reloads page after successful save
- Shows success/error alerts

**`discardChanges()`**
- Clears changes object
- Resets UI
- Reloads page

#### Event Handling

- **Click editable cell** → Enter edit mode
- **Tab key** → Save and move to next cell
- **Enter key** → Save edit
- **Escape key** → Cancel edit
- **Blur event** → Save on field exit

### Backend (Python)

#### Update Endpoint
```python
@main_bp.route("/api/update-drafts", methods=["PATCH"])
@login_required
def update_drafts():
    # Receives: {"changes": {draftId: {field: value}}}
    # For each draft:
    #   - Validate ownership
    #   - Build update dictionary
    #   - Handle attributes (brand, size, color)
    #   - Call db.update_listing()
    # Returns: {success: true, message: "...", updated_count: N}
```

#### Field Mappings

| UI Field | DB Column | Type | Notes |
|----------|-----------|------|-------|
| Title | `listings.title` | String | Direct update |
| Price | `listings.price` | Float | Converted to float |
| Cost | `listings.cost` | Float | Converted to float |
| Condition | `listings.condition` | String | Direct update |
| Brand | `listings.attributes` | JSON | Parsed/updated/re-encoded |
| Size | `listings.attributes` | JSON | Parsed/updated/re-encoded |
| Color | `listings.attributes` | JSON | Parsed/updated/re-encoded |

---

## UI/UX Design

### Color Scheme
- **Background**: Dark (#1e1e1e)
- **Text**: Light (#e0e0e0)
- **Borders**: Dark gray (#3d3d3d)
- **Modified cells**: Yellow highlight (rgba(255, 193, 7, 0.15))
- **Editing border**: Cyan (#64c8ff)

### Table Styling
- **Sticky header** - Stays visible while scrolling
- **Row hover** - Slight background change
- **Cell hover** - Cyan tint on editable cells
- **Responsive** - Horizontal scrolling for wide tables

### Indicators
- **Yellow highlight** - Modified cell (with left border)
- **Cyan border** - Cell in edit mode
- **Green banner** - Unsaved changes notification
- **Opacity 0.5** - Deleted rows (pending refresh)

---

## Data Flow

### Editing Process
```
User Clicks Cell
    ↓
editCell() called
    ↓
Create input element (text/number/select)
    ↓
Focus input
    ↓
User types / selects value
    ↓
User presses Tab/Enter/clicks away
    ↓
recordChange() called → updates draftChanges object
    ↓
Cell highlighted yellow
    ↓
Changes indicator shown
    ↓
Save button visible
```

### Saving Process
```
User clicks "Save All Changes"
    ↓
saveAllChanges() called
    ↓
Send PATCH /api/update-drafts with all changes
    ↓
Backend validates each draft
    ↓
Backend updates database
    ↓
Backend returns success
    ↓
Frontend clears draftChanges
    ↓
Page reloads to show fresh data
    ↓
User sees updated values
```

---

## Input Validation

### Frontend
- **Title**: Any non-empty string
- **Price/Cost**: Numbers only, step=0.01, min=0
- **Condition**: Select dropdown (5 options)
- **Brand/Size/Color**: Any string value

### Backend
- Type conversion (float for prices)
- JSON parsing/encoding for attributes
- User ownership verification
- Database constraint validation

---

## Error Handling

### Client-Side
- Try/catch around fetch calls
- Alert messages for errors
- Graceful failure (no data loss)
- Automatic loading indicator

### Server-Side
- 404 if listing not found
- 403 if user unauthorized
- 400 if no changes provided
- 500 for other errors
- Detailed error messages

---

## Performance Considerations

- **Single batch update** - All changes sent in one request
- **Partial updates** - Only changed fields are processed
- **Transaction safety** - Database handles updates
- **Client-side tracking** - Minimal server overhead
- **Efficient DOM updates** - Only when necessary

---

## Browser Compatibility

- Modern browsers (Chrome, Firefox, Safari, Edge)
- ES6 JavaScript features
- Bootstrap 5 framework
- Fetch API (native)

---

## Future Enhancements

Possible additions:
- Undo/redo for individual cells
- Multi-cell selection and bulk edit
- Cell-level undo (without full page reload)
- Copy/paste support
- Date field editing
- Photo upload inline
- Validation rules per field
- Custom themes/dark mode toggle

---

## Security Notes

- ✅ CSRF protection (via Flask)
- ✅ User authorization checks
- ✅ SQL injection protection (parameterized queries)
- ✅ Session management (Flask-Login)
- ⚠️ Input validation (frontend + backend)

