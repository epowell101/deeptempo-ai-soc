# Auto-Resize Visual Examples

## Table Column Sizing Modes

### Before (Old Approach)
```python
# Old way - manual resizing
self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
self.table.resizeColumnsToContents()  # Called after populating
```

**Problems:**
- All columns treated the same
- Needed to call `resizeColumnsToContents()` after every data update
- No control over which columns should stretch
- Wasted space or cramped columns

### After (New Approach)
```python
# New way - intelligent auto-sizing
TableAutoResize.configure(
    self.table,
    content_fit_columns=[0, 2, 3],  # ID, Severity, Data Source
    stretch_columns=[6],            # MITRE Techniques
    interactive_columns=[1, 4, 5]   # Timestamp, Anomaly Score, Cluster
)
```

**Benefits:**
- Declarative - set once at creation
- Different columns behave differently
- Automatic - no need to call resize after updates
- Optimal space usage

## Visual Representation

### Finding List Table Layout

```
┌─────────────────────────────────────────────────────────────────────────┐
│ ID      │ Timestamp    │ Severity │ Data Source │ Score │ Cluster │ MITRE Techniques...         │ Actions │
│ (fit)   │ (resize)     │ (fit)    │ (fit)       │(resz) │ (resz)  │ (STRETCH TO FILL)           │ (fit)   │
├─────────┼──────────────┼──────────┼─────────────┼───────┼─────────┼─────────────────────────────┼─────────┤
│ F-001   │ 2026-01-12   │ Critical │ flow        │ 0.95  │ C-1     │ T1071.001, T1059.001, T1... │ Analyze │
│ F-002   │ 2026-01-12   │ High     │ dns         │ 0.87  │ C-2     │ T1071.004, T1568.002        │ Analyze │
└─────────┴──────────────┴──────────┴─────────────┴───────┴─────────┴─────────────────────────────┴─────────┘
         ↑              ↑          ↑             ↑       ↑         ↑                             ↑
    Auto-fit      User can    Auto-fit     Auto-fit  User   User    Stretches to fill      Auto-fit
    to content    resize      to content   to content resize resize  remaining space       to content
```

### Search Results Table Layout

```
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│ Timestamp    │ Message (STRETCH TO FILL ALL AVAILABLE SPACE)          │ Source │ Severity │ Sketch │ Details  │
│ (resize)     │                                                         │ (fit)  │ (fit)    │ (fit)  │ (resize) │
├──────────────┼─────────────────────────────────────────────────────────┼────────┼──────────┼────────┼──────────┤
│ 2026-01-12   │ Suspicious C2 beacon detected from 10.0.1.15 to...     │ flow   │ Critical │ SOC-1  │ View     │
│ 2026-01-12   │ DNS query to known malicious domain detected...        │ dns    │ High     │ SOC-1  │ View     │
└──────────────┴─────────────────────────────────────────────────────────┴────────┴──────────┴────────┴──────────┘
```

## Button Sizing Examples

### Compact Buttons (Toolbar Style)

```python
ButtonSizePolicy.make_compact(button, min_width=80, max_height=24)
```

```
┌─────────┐  ┌─────────┐  ┌─────────┐
│ Refresh │  │  Clear  │  │  Send   │  ← Fixed height, minimum width
└─────────┘  └─────────┘  └─────────┘
   (80px)      (50px)       (50px)
```

### Flexible Buttons (Dialog Style)

```python
ButtonSizePolicy.make_flexible(button, min_width=100)
```

```
Window Width: 400px
┌────────────────────┐  ┌────────────────────┐
│   View Details     │  │   Find Similar     │  ← Expand to fill space
└────────────────────┘  └────────────────────┘
     (expands)               (expands)

Window Width: 800px
┌──────────────────────────────────┐  ┌──────────────────────────────────┐
│         View Details             │  │         Find Similar             │
└──────────────────────────────────┘  └──────────────────────────────────┘
          (expands more)                        (expands more)
```

### Fixed Size Buttons (Icon Style)

```python
ButtonSizePolicy.make_fixed(button, width=20, height=18)
```

```
┌───┐
│ ↻ │  ← Always 20x18, never changes
└───┘
```

## Real-World Example: Finding List Widget

### Button Row Layout

```
┌────────────────────────────────────────────────────────────────────────┐
│  ┌──────────────┐  ┌──────────────┐                      ┌─────────┐  │
│  │ View Details │  │ Find Similar │  [empty space]       │ Refresh │  │
│  └──────────────┘  └──────────────┘                      └─────────┘  │
│   (flexible)        (flexible)                           (compact)    │
└────────────────────────────────────────────────────────────────────────┘
```

When window is wider:
```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│  ┌─────────────────────┐  ┌─────────────────────┐                      ┌─────────┐    │
│  │   View Details      │  │   Find Similar      │  [empty space]       │ Refresh │    │
│  └─────────────────────┘  └─────────────────────┘                      └─────────┘    │
│     (expanded more)          (expanded more)                           (stays same)   │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

## Code Comparison

### Old Way (Manual)
```python
# Setup
self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)

# After every data update
def _populate_table(self):
    # ... add data ...
    self.table.resizeColumnsToContents()  # Must call this!
```

### New Way (Automatic)
```python
# Setup once
TableAutoResize.configure(
    self.table,
    content_fit_columns=[0, 2, 3],
    stretch_columns=[6],
    interactive_columns=[1, 4, 5]
)

# After data update - nothing needed!
def _populate_table(self):
    # ... add data ...
    # Columns automatically resize! ✓
```

## Responsive Behavior

### Window Resize Behavior

**Narrow Window (800px):**
```
┌──────────────────────────────────────────────────────────────┐
│ ID  │ Time  │ Sev │ Src │ Score │ Clus │ MITRE Tech │ Act │
├─────┼───────┼─────┼─────┼───────┼──────┼────────────┼─────┤
│ F-1 │ 01-12 │ Crt │ flw │ 0.95  │ C-1  │ T1071.001  │ Ana │
└─────┴───────┴─────┴─────┴───────┴──────┴────────────┴─────┘
```

**Wide Window (1600px):**
```
┌─────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│ ID    │ Timestamp    │ Severity │ Data Source │ Anomaly Score │ Cluster │ MITRE Techniques...           │ Actions │
├───────┼──────────────┼──────────┼─────────────┼───────────────┼─────────┼───────────────────────────────┼─────────┤
│ F-001 │ 2026-01-12   │ Critical │ flow        │ 0.95          │ C-1     │ T1071.001, T1059.001, T1...   │ Analyze │
└───────┴──────────────┴──────────┴─────────────┴───────────────┴─────────┴───────────────────────────────┴─────────┘
                                                                             ↑
                                                                    Expands to use extra space
```

## Best Practices

### When to Use Each Column Mode

1. **Content-Fit** (`content_fit_columns`):
   - Short, predictable text (IDs, status codes)
   - Severity levels (Critical, High, Medium, Low)
   - Data sources (flow, dns, waf)
   - Action buttons

2. **Stretch** (`stretch_columns`):
   - Long text that benefits from space (messages, descriptions)
   - Lists (MITRE techniques, tags)
   - Usually only 1-2 columns per table

3. **Interactive** (`interactive_columns`):
   - Timestamps (users may want different widths)
   - Numeric values (scores, counts)
   - IP addresses
   - Any column users might want to customize

### When to Use Each Button Style

1. **Compact** (`make_compact`):
   - Toolbar buttons
   - Quick actions
   - Secondary actions
   - Icon buttons with text

2. **Flexible** (`make_flexible`):
   - Primary dialog buttons
   - Main action buttons
   - Buttons in horizontal layouts that should share space

3. **Fixed** (`make_fixed`):
   - Icon-only buttons
   - Refresh/reload buttons
   - Buttons that need exact dimensions

