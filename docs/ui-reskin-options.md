# UI Reskin Options - Dark Material Design

This document outlines several options for reskinning the DeepTempo AI SOC platform with a modern dark Material Design theme.

## Current State

- **Framework**: PyQt6
- **Current Theme**: qdarkstyle (basic dark theme)
- **Styling**: Mix of qdarkstyle + inline stylesheets

## Option 1: Custom Material Design Stylesheet (Recommended)

### Overview
Create a comprehensive custom Material Design 3 (Material You) stylesheet that replaces qdarkstyle with a modern, cohesive dark theme.

### Features
- **Material Design 3 Color Palette**: Deep purple/blue accent colors with proper elevation shadows
- **Elevation System**: Subtle shadows and layering for depth
- **Ripple Effects**: Button press animations (via QPropertyAnimation)
- **Typography**: Material Design font hierarchy (Roboto-inspired)
- **Component Styling**: Cards, buttons, inputs, tabs with Material Design principles
- **Dark Theme Variants**: Multiple dark theme options (Dark, Darker, OLED-friendly)

### Color Palette Suggestions

#### Option 1A: Deep Purple/Blue (Professional SOC)
```css
Primary: #6200EE (Deep Purple)
Primary Variant: #3700B3
Secondary: #03DAC6 (Cyan)
Background: #121212 (True Black)
Surface: #1E1E1E (Dark Gray)
Surface Variant: #2C2C2C
Error: #CF6679
On Primary: #FFFFFF
On Secondary: #000000
On Background: #FFFFFF
On Surface: #FFFFFF
```

#### Option 1B: Blue/Teal (Tech-focused)
```css
Primary: #2196F3 (Blue)
Primary Variant: #1976D2
Secondary: #00BCD4 (Cyan)
Background: #0D1117 (GitHub Dark)
Surface: #161B22
Surface Variant: #21262D
Error: #F85149
On Primary: #FFFFFF
On Secondary: #000000
On Background: #C9D1D9
On Surface: #C9D1D9
```

#### Option 1C: Amber/Orange (Security Alert Theme)
```css
Primary: #FF6F00 (Amber)
Primary Variant: #E65100
Secondary: #FFC107 (Yellow)
Background: #121212
Surface: #1E1E1E
Surface Variant: #2C2C2C
Error: #D32F2F (Red)
On Primary: #000000
On Secondary: #000000
On Background: #FFFFFF
On Surface: #FFFFFF
```

### Implementation Approach
1. Create `ui/themes/material_dark.py` module
2. Define color palettes and theme configuration
3. Generate comprehensive QSS (Qt Style Sheets)
4. Replace qdarkstyle in `main.py`
5. Add theme switcher in settings

### Pros
- Full control over appearance
- Consistent Material Design language
- Can optimize for SOC use case
- No external dependencies beyond PyQt6

### Cons
- Requires significant CSS/QSS work
- Need to handle all widget types
- Animation support limited in QSS

---

## Option 2: qt-material Library

### Overview
Use the `qt-material` library which provides Material Design components for PyQt/PySide.

### Features
- Pre-built Material Design components
- Multiple color themes
- Light and dark variants
- Easy integration

### Installation
```bash
pip install qt-material
```

### Usage Example
```python
from qt_material import apply_stylesheet

app = QApplication(sys.argv)
apply_stylesheet(app, theme='dark_teal.xml')
```

### Available Themes
- `dark_amber.xml`
- `dark_blue.xml`
- `dark_cyan.xml`
- `dark_lightgreen.xml`
- `dark_pink.xml`
- `dark_purple.xml`
- `dark_red.xml`
- `dark_teal.xml`
- `dark_yellow.xml`

### Pros
- Quick implementation
- Well-maintained library
- Multiple theme options
- Good documentation

### Cons
- Less customization control
- Additional dependency
- May need tweaking for specific widgets

---

## Option 3: Hybrid Approach (qt-material + Custom Overrides)

### Overview
Use qt-material as base, then apply custom QSS overrides for SOC-specific styling.

### Features
- Start with qt-material foundation
- Customize critical components (tables, charts, attack layers)
- Add SOC-specific color coding (severity levels, MITRE techniques)
- Maintain Material Design principles

### Implementation
1. Apply qt-material base theme
2. Create custom QSS file for overrides
3. Apply custom styles after qt-material
4. Focus custom styling on:
   - Finding severity colors
   - MITRE ATT&CK technique visualization
   - Timeline/chart components
   - Status indicators

### Pros
- Best of both worlds
- Faster initial implementation
- Customizable where needed
- Maintains Material Design consistency

### Cons
- Two styling systems to manage
- Potential conflicts between stylesheets

---

## Option 4: Material Design 3 with Custom Components

### Overview
Implement Material Design 3 (Material You) with custom-styled PyQt6 widgets.

### Features
- Material Design 3 color system
- Custom widget classes (MaterialButton, MaterialCard, MaterialTextField)
- Dynamic color theming based on wallpaper/accent
- Adaptive layouts

### Key Components to Create
- `MaterialButton`: Ripple effect, elevation
- `MaterialCard`: Elevation, rounded corners
- `MaterialTextField`: Floating labels, underline focus
- `MaterialTabBar`: Animated indicator
- `MaterialProgressBar`: Circular and linear variants
- `MaterialChip`: For tags/labels

### Pros
- Most authentic Material Design experience
- Reusable component library
- Highly customizable
- Modern Material You features

### Cons
- Most development effort required
- Need to subclass many widgets
- Animation implementation complexity

---

## Option 5: Dark Theme with Material-Inspired Accents

### Overview
Keep current qdarkstyle base but enhance with Material Design accents and components.

### Features
- Minimal changes to existing code
- Material Design color accents
- Enhanced buttons and inputs
- Material-style cards and elevation

### Implementation
1. Keep qdarkstyle as base
2. Create accent color system
3. Override specific components with Material styling
4. Add elevation shadows via QSS
5. Enhance typography

### Pros
- Minimal disruption
- Quick to implement
- Gradual migration possible
- Low risk

### Cons
- Less cohesive than full Material theme
- May feel like a hybrid

---

## Recommended Implementation Plan

### Phase 1: Foundation (Week 1)
1. **Choose Option 2 or 3** (qt-material or hybrid)
   - Quickest path to Material Design
   - Can evaluate and iterate

2. **Install and test qt-material**
   ```bash
   pip install qt-material
   ```

3. **Create theme configuration module**
   - `ui/themes/__init__.py`
   - `ui/themes/material_config.py`

### Phase 2: Integration (Week 1-2)
1. Replace qdarkstyle with qt-material in `main.py`
2. Test all major views (Dashboard, Chat, Widgets)
3. Identify components needing custom styling
4. Create custom QSS overrides file

### Phase 3: Customization (Week 2-3)
1. Style SOC-specific components:
   - Finding severity indicators
   - MITRE ATT&CK visualization
   - Timeline components
   - Status badges
2. Add theme switcher to settings
3. Polish animations and transitions

### Phase 4: Enhancement (Week 3-4)
1. Create custom Material components if needed
2. Add elevation system
3. Implement ripple effects
4. Final polish and testing

---

## Specific Styling Considerations for SOC Platform

### Color Coding
- **Critical Severity**: #D32F2F (Red)
- **High Severity**: #F57C00 (Orange)
- **Medium Severity**: #FBC02D (Yellow)
- **Low Severity**: #388E3C (Green)
- **Info**: #1976D2 (Blue)

### MITRE ATT&CK Colors
- **Initial Access**: #E91E63 (Pink)
- **Execution**: #9C27B0 (Purple)
- **Persistence**: #673AB7 (Deep Purple)
- **Privilege Escalation**: #3F51B5 (Indigo)
- **Defense Evasion**: #2196F3 (Blue)
- **Credential Access**: #00BCD4 (Cyan)
- **Discovery**: #4CAF50 (Green)
- **Lateral Movement**: #8BC34A (Light Green)
- **Collection**: #FFC107 (Amber)
- **Command and Control**: #FF9800 (Orange)
- **Exfiltration**: #FF5722 (Deep Orange)
- **Impact**: #F44336 (Red)

### Component Priorities
1. **Tables** (Finding List, Case List): Material-style rows, hover effects
2. **Buttons**: Ripple effects, proper elevation
3. **Input Fields**: Floating labels, focus states
4. **Cards**: Elevation, rounded corners
5. **Tabs**: Animated indicator
6. **Charts/Graphs**: Material color palette
7. **Status Indicators**: Color-coded badges

---

## Code Structure Proposal

```
ui/
├── themes/
│   ├── __init__.py
│   ├── material_config.py      # Theme configuration
│   ├── material_styles.qss     # Custom QSS overrides
│   ├── color_palettes.py        # Color definitions
│   └── material_components.py   # Custom Material widgets (optional)
├── main_window.py
├── dashboard.py
└── ...
```

---

## Next Steps

1. **Decision**: Choose an option (recommend Option 2 or 3)
2. **Prototype**: Create a small test implementation
3. **Review**: Get feedback on color palette and styling
4. **Implement**: Full integration following the plan above

---

## Resources

- [Material Design 3 Guidelines](https://m3.material.io/)
- [qt-material Documentation](https://github.com/UN-GCPDS/qt-material)
- [PyQt6 Stylesheet Reference](https://doc.qt.io/qt-6/stylesheet-reference.html)
- [Material Design Color Tool](https://m2.material.io/design/color/the-color-system.html)

