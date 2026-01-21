# 📋 Editable Drafts - User Guide

Your **Drafts page** is now an **interactive, Excel-like spreadsheet** where you can edit items directly without leaving the page!

---

## 🎯 Quick Start (2 Minutes)

### To Edit a Single Item:
1. Go to **Drafts** page
2. **Click on any cell** (Title, Price, Condition, etc.)
3. **Type your change**
4. Press **Tab** to move to next cell or **Enter** to save
5. When done editing, click **Save All Changes** button
6. Done! ✅

### To Delete Multiple Items:
1. ☑️ Check the boxes next to items you want to delete
2. Click **Delete Selected** (appears when items are checked)
3. Confirm deletion
4. Page auto-refreshes

### To Export to Your Platform:
1. ☑️ Check items to export
2. Click **Export Selected**
3. Choose platform (Poshmark, Mercari, eBay, etc.)
4. CSV downloads automatically

---

## ✨ Features

### ✏️ Inline Editing
- **Click any cell** to edit it directly
- Fields you can edit:
  - 📝 **Title** - Edit listing title
  - 💰 **Price** - Edit selling price
  - 💸 **Cost** - Edit acquisition cost
  - 🏷️ **Condition** - Select from dropdown (New, Like New, Good, Fair, Poor)
  - 🏢 **Brand** - Edit brand name
  - 📐 **Size** - Edit size
  - 🎨 **Color** - Edit color

### 🎯 Keyboard Navigation
- **Tab** - Move to next editable cell
- **Shift+Tab** - Move to previous cell
- **Enter** - Save edit and stay in cell
- **Escape** - Cancel edit without saving
- **Space** (on checkbox) - Toggle selection

### 💾 Change Tracking
- Changed cells are **highlighted in yellow**
- A **floating indicator** appears showing unsaved changes
- **Save All Changes** button to commit all edits at once
- **Discard** button to revert all unsaved changes

### ✅ Bulk Operations
- **Checkbox selection** for multiple drafts
- **Select All** to quickly select/deselect all items
- **Bulk Delete** for removing multiple drafts at once
- **Export Selected** to CSV for your chosen platform

### 📊 Spreadsheet Interface
- Clean, dark-themed table with sticky headers
- Hover effects show which rows are editable
- **Full Editor** link to open the complete editing form
- Photo previews with modal viewer
- Horizontal scrolling for large datasets

---

## 🎨 Visual Indicators

| Color/Style | Meaning |
|------------|---------|
| 🟨 **Yellow** | Cell has unsaved changes |
| 🟦 **Cyan border** | Cell is being edited |
| 🟩 **Green banner** | Unsaved changes exist (bottom-right) |
| ⚪ **Faded** | Row was deleted (pending refresh) |

---

## 📝 Editable Fields

| Field | Type | Example |
|-------|------|---------|
| **Title** | Text | "Vintage Leather Jacket" |
| **Price** | Money | 45.99 |
| **Cost** | Money | 15.00 |
| **Condition** | Dropdown | New / Like New / Good / Fair / Poor |
| **Brand** | Text | "Nike" |
| **Size** | Text | "M" or "10" |
| **Color** | Text | "Navy Blue" |

---

## 💾 Saving Your Changes

### How to Save:
- Click the big green **"Save All Changes"** button
- Wait for success message
- Page will automatically refresh

### What Happens If I Don't Save?
- Changes are **ONLY stored in your browser**
- If you close the page or refresh, **changes are lost**
- Use the **"Discard"** button if you need to cancel

### Can I Undo?
- **Before saving**: Click **"Discard"** to revert all changes
- **After saving**: Changes are permanent (edit again if needed)

---

## 🔄 Workflow Examples

### Example 1: Quick Price Updates
```
✓ Click on Price cell
✓ Change $20.00 → $25.00 (cell turns yellow)
✓ Press Tab → move to next price
✓ Change $30.00 → $32.00
✓ Continue for all items...
✓ Click "Save All Changes"
✓ Done!
```

### Example 2: Bulk Update Conditions
```
✓ Click Condition cell → "Good"
✓ Tab to next → "Good"
✓ Tab to next → "Like New"
✓ Save All Changes
```

### Example 3: Export Prepared Items
```
✓ Edit all the items you want to export
✓ Click "Save All Changes"
✓ Check boxes of items to export
✓ Click "Export Selected"
✓ Choose platform
✓ CSV downloads
```

---

## 🚀 Pro Tips

1. **Use Tab to fly through edits** - Much faster than clicking each time
2. **Edit first, save once** - Edit multiple items, then save all at once
3. **Check your yellow highlights** - Make sure you edited what you meant to
4. **Use condition dropdown** - Only valid options: New, Like New, Good, Fair, Poor
5. **Prices need numbers** - Can use decimals (45.99), not text
6. **No need to close/reopen** - Stay on this page to make bulk changes
7. **Batch updates** - Edit multiple drafts, then **Save All Changes** once
8. **Review changes** - Yellow highlighting shows what you've modified
9. **Photo preview** - Click photos to view them in a modal

---

## ❌ Troubleshooting

### "Can't edit a cell?"
- Make sure you're **clicking on the text**, not the borders
- Try double-clicking if single-click doesn't work
- Some fields may be read-only (creation date)
- Refresh the page and try again

### "Yellow highlight won't go away?"
- That's normal - it shows what you changed
- Disappears after you **Save All Changes**

### "Save button doesn't show?"
- Click **at least one cell** to trigger it
- Check for error messages at the top

### "Changes disappeared?"
- Did you click **Save All Changes**? (important!)
- Browser may have refreshed - edit again and save

### "Can't delete an item?"
- Item might already be deleted
- Try refreshing the page
- Ensure it's checked before clicking Delete

### "Changes not saving?"
- Click the **Save All Changes** button
- Check for error messages at top of page
- Verify you're not editing a deleted item

---

## ⚠️ Important Notes

- Changes are **only saved when you click "Save All Changes"**
- Use **Escape key** to cancel individual edits
- **Prices should be positive numbers** (decimals supported)
- **Conditions** can only be: New, Like New, Good, Fair, Poor
- **Bulk operations** (delete, export) cannot be undone after confirmation

---

## 📞 Common Questions

**"Why does it reload after saving?"**
- Normal behavior - ensures fresh data from server
- Takes ~2 seconds

**"Can I edit multiple cells at once?"**
- Edit them individually or all together
- Save all changes in one batch

**"Does bulk delete really delete everything?"**
- Yes! Confirm carefully
- Deleted items cannot be recovered from this page

**"What if I edit the wrong value?"**
- Before saving: Click **Discard** to revert ALL changes
- After saving: Edit the cell again and resave

---

## 🎓 Learn More

For technical implementation details, see:
- `EDITABLE_DRAFTS_TECHNICAL.md` - Developer implementation guide

---

**You're all set! Go edit some drafts! 🎉**
