# Auto-Resize Implementation Guide

## Overview

This document describes the implementation of intelligent auto-sizing for UI elements (tables and buttons) across the DeepTempo AI SOC application using PyQt6's built-in resizing mechanisms.

## Implementation Summary

### Created Utility Module: `ui/utils/auto_resize.py`

A centralized utility module that provides consistent auto-sizing behavior across all widgets:

#### 1. **TableAutoResize Class**
Handles intelligent column sizing for QTableWidget with three modes:

- **Fixed Columns**: Set specific pixel widths (e.g., ID columns)
- **Content-Fit Columns**: Auto-resize to fit content (e.g., Severity, Status)
- **Stretch Columns**: Expand to fill remaining space (e.g., Description, Message)
- **Interactive Columns**: User can manually resize (e.g., Timestamps, IP addresses)

#### 2. **ButtonSizePolicy Class**
Handles responsive button sizing with helper methods:

- **`make_compact()`**: For toolbar/action buttons with minimum size
- **`make_flexible()`**: For dialog/primary buttons that expand with layout
- **`make_fixed()`**: For icon buttons or specific-sized controls

## Updated Widgets

### Core Widgets
1. **`ui/widgets/finding_list.py`**
   - Main findings table with intelligent column sizing
   - Action buttons (View Details, Find Similar, Refresh, Analyze)
   - Similar findings dialog table

2. **`ui/claude_chat.py`**
   - All control buttons (Send, Clear, Attach, Remove, etc.)
   - Quick action buttons (Analyze, Correlate, Summary)
   - MCP refresh button

3. **`ui/widgets/investigation_workflow.py`**
   - Workflow control buttons (Create, Update, Advance)
   - Refresh button

4. **`ui/widgets/search_widget.py`**
   - Search results table with intelligent column sizing
   - Action buttons (Search, Export, Save Query, Delete)

5. **`ui/widgets/event_analysis_widget.py`**
   - Similar events table
   - Correlated events table
   - IP addresses table
   - Devices table
   - Action buttons (Close, Refresh)

6. **`ui/widgets/timesketch_timeline.py`**
   - Timeline events table
   - Action buttons (Open in Timesketch, Refresh, Analyze, Close)

## Usage Examples

### For Tables

```python
from ui.utils.auto_resize import TableAutoResize

# Configure a table with intelligent column sizing
TableAutoResize.configure(
    table,
    content_fit_columns=[0, 2, 3],  # Auto-fit to content
    stretch_columns=[6],            # Stretch to fill space
    interactive_columns=[1, 4, 5]   # User can resize
)
```

### For Buttons

```python
from ui.utils.auto_resize import ButtonSizePolicy

# Compact button (toolbar/action)
button = QPushButton("Refresh")
ButtonSizePolicy.make_compact(button, min_width=80, max_height=24)

# Flexible button (dialog/primary action)
button = QPushButton("View Details")
ButtonSizePolicy.make_flexible(button, min_width=100)

# Fixed size button (icon button)
button = QPushButton("↻")
ButtonSizePolicy.make_fixed(button, width=20, height=18)
```

## Column Sizing Strategy by Widget

### Finding List Table
- **Content-Fit**: ID, Severity, Data Source, Actions
- **Stretch**: MITRE Techniques
- **Interactive**: Timestamp, Anomaly Score, Cluster

### Search Results Table
- **Content-Fit**: Source, Severity, Sketch
- **Stretch**: Message
- **Interactive**: Timestamp, Details

### Event Analysis Tables
- **Similar Events**:
  - Content-Fit: Similarity, Severity
  - Stretch: Message
  - Interactive: Timestamp, IPs

- **Correlated Events**:
  - Content-Fit: Correlation Type, Severity
  - Stretch: Message
  - Interactive: Timestamp, IPs

- **IP Addresses**:
  - Content-Fit: Type, Event Count
  - Stretch: IP Address, First Seen

- **Devices**:
  - Content-Fit: Event Count, Severity
  - Stretch: Hostname, IP Address

### Timeline Events Table
- **Content-Fit**: Source, Severity, Data Source
- **Stretch**: Message, MITRE
- **Interactive**: Timestamp

## Button Sizing Strategy

### Compact Buttons (min_width, max_height)
Used for toolbar and action buttons:
- Send (50px)
- Clear (50px)
- Attach (55px)
- Refresh (80px)
- Analyze (52px)
- Correlate (54px)
- Summary (54px)

### Flexible Buttons (min_width, expands)
Used for dialog and primary actions:
- View Details (100px)
- Find Similar (100px)
- Create Workflow (140px)
- Update Current Phase (160px)
- Advance to Next Phase (160px)
- Delete Selected (120px)

### Fixed Size Buttons (width x height)
Used for icon buttons:
- MCP Refresh "↻" (20x18)

## Benefits

1. **Consistency**: All tables and buttons use the same sizing logic
2. **Responsiveness**: UI adapts to different window sizes
3. **User Control**: Users can still manually resize interactive columns
4. **Readability**: Important columns (like messages) stretch to use available space
5. **Efficiency**: Short columns (like severity) don't waste space
6. **Maintainability**: Centralized logic makes updates easy

## PyQt6 Resize Modes Used

### QHeaderView.ResizeMode
- **Fixed**: Column has a fixed width (set with `setColumnWidth()`)
- **ResizeToContents**: Column automatically resizes to fit content
- **Stretch**: Column expands to fill available space
- **Interactive**: User can manually resize the column

### QSizePolicy.Policy
- **Fixed**: Widget has a fixed size
- **Minimum**: Widget can expand but has a minimum size
- **Expanding**: Widget expands to fill available space
- **Preferred**: Widget has a preferred size but can shrink/expand

## Future Enhancements

1. Add user preferences to save custom column widths
2. Implement column visibility toggles
3. Add preset layouts (compact, detailed, etc.)
4. Create widget-specific helper functions for common table patterns
5. Add keyboard shortcuts for resizing operations

## Testing

To verify the implementation:

1. **Table Columns**:
   - Resize the window - columns should adapt appropriately
   - Try manually resizing interactive columns
   - Verify content-fit columns don't waste space
   - Check that stretch columns fill remaining space

2. **Buttons**:
   - Resize the window - buttons should maintain minimum sizes
   - Flexible buttons should expand with their containers
   - Compact buttons should stay small
   - Fixed buttons should never change size

## Notes

- The `resizeColumnsToContents()` method is no longer needed with this approach
- All sizing is handled declaratively at widget setup time
- The system works seamlessly with PyQt6's layout managers
- Row resizing remains user-controlled via vertical header

