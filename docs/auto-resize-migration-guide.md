# Auto-Resize Migration Guide

## Quick Start for Remaining Widgets

If you need to update additional widgets to use the new auto-resize system, follow this guide.

## Step 1: Import the Utilities

Add to your widget imports:

```python
from ui.utils.auto_resize import TableAutoResize, ButtonSizePolicy
```

## Step 2: Update Tables

### Find This Pattern:
```python
self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
self.table.horizontalHeader().setStretchLastSection(False)
# ... later in code ...
self.table.resizeColumnsToContents()
```

### Replace With:
```python
TableAutoResize.configure(
    self.table,
    content_fit_columns=[0, 2, 3],  # Columns that should auto-fit
    stretch_columns=[6],            # Columns that should stretch
    interactive_columns=[1, 4, 5]   # Columns users can resize
)
```

### Remove:
```python
self.table.resizeColumnsToContents()  # No longer needed!
```

## Step 3: Update Buttons

### Find This Pattern:
```python
button = QPushButton("Text")
button.setMinimumWidth(80)
button.setMaximumHeight(24)
```

### Replace With:
```python
button = QPushButton("Text")
ButtonSizePolicy.make_compact(button, min_width=80, max_height=24)
```

## Quick Reference

### Table Column Decision Tree

```
Is the column text...
├─ Short and predictable? (ID, Status, Severity)
│  └─ Use: content_fit_columns
│
├─ Long and benefits from space? (Message, Description)
│  └─ Use: stretch_columns
│
└─ Variable or user preference? (Timestamp, IP, Score)
   └─ Use: interactive_columns
```

### Button Decision Tree

```
What type of button is it?
├─ Toolbar/Quick action?
│  └─ Use: ButtonSizePolicy.make_compact()
│
├─ Primary dialog action?
│  └─ Use: ButtonSizePolicy.make_flexible()
│
└─ Icon only?
   └─ Use: ButtonSizePolicy.make_fixed()
```

## Common Patterns

### Pattern 1: Standard Data Table
```python
TableAutoResize.configure(
    table,
    content_fit_columns=[0, 2],     # ID, Status
    stretch_columns=[1],            # Description
    interactive_columns=[3, 4, 5]   # Timestamp, Score, etc.
)
```

### Pattern 2: Event/Log Table
```python
TableAutoResize.configure(
    table,
    content_fit_columns=[2, 3, 4],  # Source, Severity, Type
    stretch_columns=[1],            # Message
    interactive_columns=[0, 5]      # Timestamp, Details
)
```

### Pattern 3: Entity Table
```python
TableAutoResize.configure(
    table,
    content_fit_columns=[0, 1],     # Type, Count
    stretch_columns=[2, 3],         # Name, Related Items
    interactive_columns=[]          # None - all auto
)
```

### Pattern 4: Button Row
```python
# Left-aligned flexible buttons
view_btn = QPushButton("View Details")
ButtonSizePolicy.make_flexible(view_btn, min_width=100)

edit_btn = QPushButton("Edit")
ButtonSizePolicy.make_flexible(edit_btn, min_width=80)

# Right-aligned compact button
close_btn = QPushButton("Close")
ButtonSizePolicy.make_compact(close_btn, min_width=70)
```

## Widgets Already Updated ✓

- ✓ `ui/widgets/finding_list.py`
- ✓ `ui/claude_chat.py`
- ✓ `ui/widgets/investigation_workflow.py`
- ✓ `ui/widgets/search_widget.py`
- ✓ `ui/widgets/event_analysis_widget.py`
- ✓ `ui/widgets/timesketch_timeline.py`

## Widgets That May Need Updates

Check these widgets if they have tables or buttons:

- `ui/widgets/finding_detail.py`
- `ui/widgets/attack_layer_view.py`
- `ui/widgets/correlation_widget.py`
- `ui/widgets/entity_investigation_widget.py`
- `ui/widgets/collaboration_widget.py`
- `ui/widgets/case_list.py` (if exists)
- Any custom dialog widgets

## Testing Checklist

After updating a widget:

### For Tables:
- [ ] Resize window - columns adapt appropriately
- [ ] Content-fit columns don't waste space
- [ ] Stretch columns fill remaining space
- [ ] Interactive columns can be manually resized
- [ ] No horizontal scrollbar at default size
- [ ] Data populates correctly without calling `resizeColumnsToContents()`

### For Buttons:
- [ ] Buttons maintain minimum sizes
- [ ] Flexible buttons expand with window
- [ ] Compact buttons stay small
- [ ] Fixed buttons never change size
- [ ] Button text is fully visible
- [ ] Buttons align correctly in layouts

## Common Issues and Solutions

### Issue: Columns too narrow
**Solution:** Check if you're using the right mode. Short text should use `content_fit_columns`, not `interactive_columns`.

### Issue: Columns too wide
**Solution:** Long text columns should use `stretch_columns` with only 1-2 columns set to stretch.

### Issue: Buttons too small
**Solution:** Increase `min_width` parameter or switch from `make_compact()` to `make_flexible()`.

### Issue: Buttons too large
**Solution:** Switch from `make_flexible()` to `make_compact()` or use `make_fixed()` for icon buttons.

### Issue: Table has horizontal scrollbar
**Solution:** Too many `content_fit_columns`. Move some to `interactive_columns` or reduce the number of visible columns.

## Advanced Usage

### Custom Size Policies
```python
# For special cases, use the full API
ButtonSizePolicy.apply_responsive(
    button,
    horizontal="expanding",
    vertical="fixed",
    min_width=100,
    max_width=300,
    min_height=24,
    max_height=24
)
```

### Fixed Width Columns
```python
# If you need a specific pixel width
TableAutoResize.configure(
    table,
    fixed_columns={0: 100, 7: 80},  # Column 0: 100px, Column 7: 80px
    content_fit_columns=[2, 3],
    stretch_columns=[1]
)
```

### Multiple Stretch Columns
```python
# Multiple columns can stretch (they share space equally)
TableAutoResize.configure(
    table,
    content_fit_columns=[0, 1],
    stretch_columns=[2, 3, 4],  # All three will share remaining space
    interactive_columns=[]
)
```

## Need Help?

1. Check `docs/auto-resize-examples.md` for visual examples
2. Look at already-updated widgets for patterns
3. Refer to `ui/utils/auto_resize.py` for full API documentation
4. Test in the running application to see the behavior

## Performance Notes

- Auto-resizing happens once at widget creation
- No performance impact during data updates
- More efficient than calling `resizeColumnsToContents()` repeatedly
- Works seamlessly with PyQt6's layout system

