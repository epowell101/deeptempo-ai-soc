# Material Design Theme - Quick Start Guide

This guide will help you quickly test and implement the Material Design dark theme for DeepTempo AI SOC.

## Quick Test (5 minutes)

### Option A: Using qt-material (Recommended for quickest results)

1. **Install qt-material:**
   ```bash
   pip install qt-material
   ```

2. **Test the theme:**
   ```bash
   # Use the example file
   python main_material_example.py
   ```

3. **Or integrate into main.py:**
   Replace the qdarkstyle section in `main.py` with:
   ```python
   from ui.themes import apply_material_theme
   
   # In main() function, replace:
   # app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt6())
   # With:
   apply_material_theme(app, theme_name='dark_blue')
   ```

### Option B: Using Custom QSS (No additional dependencies)

The custom Material theme will work without qt-material. Just use:

```python
from ui.themes import apply_material_theme

apply_material_theme(app, theme_name='dark_blue')
```

The system will automatically fall back to custom QSS if qt-material is not installed.

## Available Themes

Try different themes by changing the `theme_name` parameter:

- **`dark_blue`** - Professional blue theme (default)
- **`dark_teal`** - Tech-focused teal theme
- **`dark_purple`** - Deep purple theme
- **`dark_amber`** - Warm amber with security alert colors
- **`dark_cyan`** - Cool cyan theme

Example:
```python
apply_material_theme(app, theme_name='dark_teal')
```

## Customization

### Changing Colors

Edit `ui/themes/material_config.py` and modify the color palettes in the `_generate_custom_qss()` method.

### Adding Custom Styles

Create `ui/themes/material_styles.qss` for additional custom styles:

```python
# In material_config.py, after applying base theme:
custom_qss_file = Path(__file__).parent / 'material_styles.qss'
if custom_qss_file.exists():
    with open(custom_qss_file, 'r') as f:
        custom_qss = f.read()
    app.setStyleSheet(app.styleSheet() + custom_qss)
```

## SOC-Specific Styling

The theme includes special styling for SOC components:

### Severity Colors
- Critical: Red (#D32F2F)
- High: Orange (#F57C00)
- Medium: Yellow (#FBC02D)
- Low: Green (#388E3C)

Use in your widgets:
```python
label.setProperty('severity', 'critical')
label.style().unpolish(label)
label.style().polish(label)
```

## Next Steps

1. **Test the themes** - Try all available themes to see which fits best
2. **Customize colors** - Adjust the palette to match your brand
3. **Add custom components** - Style specific widgets as needed
4. **Add theme switcher** - Let users choose themes in settings

## Troubleshooting

### Theme not applying?
- Check that `ui/themes/__init__.py` and `material_config.py` are in place
- Check logs for error messages
- Try the fallback: the system will use custom QSS if qt-material fails

### qt-material not working?
- Make sure it's installed: `pip install qt-material`
- Check PyQt6 version compatibility
- The custom QSS fallback will work without qt-material

### Colors look wrong?
- Adjust the color palettes in `material_config.py`
- Check that your widgets aren't overriding styles with inline stylesheets

## Full Documentation

See `docs/ui-reskin-options.md` for complete documentation on all reskin options and implementation strategies.

