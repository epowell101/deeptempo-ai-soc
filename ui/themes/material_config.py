"""Material Design theme configuration and application."""

import logging
from pathlib import Path
from typing import Optional, Dict, List
from PyQt6.QtWidgets import QApplication

logger = logging.getLogger(__name__)

# Available Material Design themes
AVAILABLE_THEMES = {
    'dark_blue': {
        'name': 'Dark Blue',
        'description': 'Professional blue theme for SOC operations',
        'file': 'dark_blue.xml'
    },
    'dark_teal': {
        'name': 'Dark Teal',
        'description': 'Tech-focused teal theme',
        'file': 'dark_teal.xml'
    },
    'dark_purple': {
        'name': 'Dark Purple',
        'description': 'Deep purple theme with modern aesthetics',
        'file': 'dark_purple.xml'
    },
    'dark_amber': {
        'name': 'Dark Amber',
        'description': 'Warm amber theme with security alert colors',
        'file': 'dark_amber.xml'
    },
    'dark_cyan': {
        'name': 'Dark Cyan',
        'description': 'Cool cyan theme',
        'file': 'dark_cyan.xml'
    },
}


class MaterialTheme:
    """Material Design theme manager."""
    
    def __init__(self, theme_name: str = 'dark_blue'):
        """
        Initialize Material theme.
        
        Args:
            theme_name: Name of the theme to use
        """
        self.theme_name = theme_name
        self.theme_config = AVAILABLE_THEMES.get(theme_name, AVAILABLE_THEMES['dark_blue'])
    
    def apply(self, app: QApplication, extra: Optional[Dict] = None) -> bool:
        """
        Apply Material theme to the application.
        
        Args:
            app: QApplication instance
            extra: Extra parameters for qt-material (if using qt-material)
            
        Returns:
            True if theme applied successfully, False otherwise
        """
        try:
            # Try qt-material first (if installed)
            try:
                from qt_material import apply_stylesheet
                
                theme_file = self.theme_config['file']
                extra_params = extra or {}
                
                # Default extra parameters for better Material Design
                default_extra = {
                    'density_scale': '-1',  # Compact density
                }
                default_extra.update(extra_params)
                
                apply_stylesheet(app, theme=theme_file, extra=default_extra)
                
                # Apply QSS overrides to change all blue accents to red
                override_qss = self._generate_red_accent_overrides()
                app.setStyleSheet(app.styleSheet() + override_qss)
                
                logger.info(f"Applied Material theme: {self.theme_name}")
                return True
                
            except ImportError:
                logger.warning("qt-material not installed. Using custom Material theme.")
                return self._apply_custom_theme(app)
                
        except Exception as e:
            logger.error(f"Failed to apply Material theme: {e}")
            return False
    
    def _apply_custom_theme(self, app: QApplication) -> bool:
        """
        Apply custom Material Design theme using QSS.
        
        This is a fallback if qt-material is not available.
        """
        try:
            custom_qss = self._generate_custom_qss()
            app.setStyleSheet(custom_qss)
            logger.info(f"Applied custom Material theme: {self.theme_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to apply custom theme: {e}")
            return False
    
    def _generate_custom_qss(self) -> str:
        """Generate custom Material Design QSS."""
        # Material Design 3 Dark Theme Colors
        colors = {
            'dark_blue': {
                'primary': '#F44336',
                'primary_variant': '#D32F2F',
                'secondary': '#00BCD4',
                'background': '#121212',
                'surface': '#1E1E1E',
                'surface_variant': '#2C2C2C',
                'error': '#F85149',
                'on_primary': '#FFFFFF',
                'on_background': '#E0E0E0',
                'on_surface': '#E0E0E0',
            },
            'dark_teal': {
                'primary': '#00BCD4',
                'primary_variant': '#0097A7',
                'secondary': '#4DD0E1',
                'background': '#0D1117',
                'surface': '#161B22',
                'surface_variant': '#21262D',
                'error': '#F85149',
                'on_primary': '#000000',
                'on_background': '#C9D1D9',
                'on_surface': '#C9D1D9',
            },
            'dark_purple': {
                'primary': '#6200EE',
                'primary_variant': '#3700B3',
                'secondary': '#03DAC6',
                'background': '#121212',
                'surface': '#1E1E1E',
                'surface_variant': '#2C2C2C',
                'error': '#CF6679',
                'on_primary': '#FFFFFF',
                'on_background': '#FFFFFF',
                'on_surface': '#FFFFFF',
            },
            'dark_amber': {
                'primary': '#FF6F00',
                'primary_variant': '#E65100',
                'secondary': '#FFC107',
                'background': '#121212',
                'surface': '#1E1E1E',
                'surface_variant': '#2C2C2C',
                'error': '#D32F2F',
                'on_primary': '#000000',
                'on_background': '#FFFFFF',
                'on_surface': '#FFFFFF',
            },
            'dark_cyan': {
                'primary': '#00BCD4',
                'primary_variant': '#0097A7',
                'secondary': '#4DD0E1',
                'background': '#121212',
                'surface': '#1E1E1E',
                'surface_variant': '#2C2C2C',
                'error': '#F85149',
                'on_primary': '#000000',
                'on_background': '#E0E0E0',
                'on_surface': '#E0E0E0',
            },
        }
        
        palette = colors.get(self.theme_name, colors['dark_blue'])
        
        # Generate Material Design QSS
        qss = f"""
        /* Material Design Dark Theme - {self.theme_name} */
        
        /* Main Window */
        QMainWindow {{
            background-color: {palette['background']};
            color: {palette['on_background']};
        }}
        
        /* Widgets */
        QWidget {{
            background-color: {palette['background']};
            /* Don't set color globally - it overrides programmatic setForeground() */
            font-family: "Roboto", "Segoe UI", sans-serif;
        }}
        
        /* Default text color for standard widgets (not table items - they set their own) */
        QLabel, QCheckBox, QRadioButton, QGroupBox, QListWidget, QTreeWidget {{
            color: {palette['on_background']};
        }}
        
        /* Buttons */
        QPushButton {{
            background-color: {palette['primary']};
            color: {palette['on_primary']};
            border: none;
            border-radius: 4px;
            padding: 8px 16px;
            font-weight: 500;
            min-height: 36px;
        }}
        
        QPushButton:hover {{
            background-color: {palette['primary_variant']};
        }}
        
        QPushButton:pressed {{
            background-color: {palette['primary_variant']};
        }}
        
        QPushButton:disabled {{
            background-color: {palette['surface_variant']};
            color: #666666;
        }}
        
        /* Line Edits */
        QLineEdit {{
            background-color: {palette['surface']};
            color: {palette['on_surface']};
            border: 1px solid {palette['surface_variant']};
            border-radius: 4px;
            padding: 8px 12px;
            min-height: 20px;
        }}
        
        QLineEdit:focus {{
            border: 2px solid {palette['primary']};
            background-color: {palette['surface_variant']};
        }}
        
        /* Text Edits */
        QTextEdit {{
            background-color: {palette['surface']};
            color: {palette['on_surface']};
            border: 1px solid {palette['surface_variant']};
            border-radius: 4px;
            padding: 8px;
        }}
        
        /* Combo Boxes */
        QComboBox {{
            background-color: {palette['surface']};
            color: {palette['on_surface']};
            border: 1px solid {palette['surface_variant']};
            border-radius: 4px;
            padding: 8px 12px;
            min-height: 20px;
        }}
        
        QComboBox:hover {{
            background-color: {palette['surface_variant']};
        }}
        
        QComboBox:focus {{
            border: 2px solid {palette['primary']};
        }}
        
        QComboBox::drop-down {{
            border: none;
            width: 30px;
        }}
        
        QComboBox::down-arrow {{
            image: none;
            border-left: 4px solid transparent;
            border-right: 4px solid transparent;
            border-top: 6px solid {palette['on_surface']};
            margin-right: 8px;
        }}
        
        /* Tab Widget */
        QTabWidget::pane {{
            border: 1px solid {palette['surface_variant']};
            background-color: {palette['surface']};
            border-radius: 4px;
        }}
        
        QTabBar::tab {{
            background-color: {palette['surface_variant']};
            color: {palette['on_surface']};
            padding: 8px 16px;
            margin-right: 2px;
            border-top-left-radius: 4px;
            border-top-right-radius: 4px;
        }}
        
        QTabBar::tab:selected {{
            background-color: #3C3C3C;
            color: #FFFFFF;
            border-bottom: 3px solid #F44336;
        }}
        
        QTabBar::tab {{
            border-bottom: 2px solid transparent;
        }}
        
        QTabBar::tab:hover {{
            background-color: {palette['surface']};
        }}
        
        /* Tables */
        QTableWidget {{
            background-color: {palette['surface']};
            border: 1px solid {palette['surface_variant']};
            gridline-color: {palette['surface_variant']};
            border-radius: 4px;
        }}
        
        QTableWidget::item {{
            padding: 4px;
            /* Note: Don't set color here - it overrides setForeground() calls */
            /* Items need to set their own colors programmatically */
        }}
        
        /* Default text color for headers */
        QHeaderView {{
            color: {palette['on_surface']};
        }}
        
        QTableWidget::item:selected {{
            background-color: {palette['primary']};
            /* Don't override text color on selection - let items keep their custom colors */
        }}
        
        QHeaderView::section {{
            background-color: {palette['surface_variant']};
            color: {palette['on_surface']};
            padding: 8px;
            border: none;
            font-weight: 500;
        }}
        
        /* Group Boxes */
        QGroupBox {{
            border: 1px solid {palette['surface_variant']};
            border-radius: 4px;
            margin-top: 12px;
            padding-top: 12px;
            font-weight: 500;
        }}
        
        QGroupBox::title {{
            subcontrol-origin: margin;
            subcontrol-position: top left;
            padding: 0 8px;
            color: {palette['primary']};
        }}
        
        /* Scrollbars */
        QScrollBar:vertical {{
            background-color: {palette['surface_variant']};
            width: 12px;
            border: none;
        }}
        
        QScrollBar::handle:vertical {{
            background-color: {palette['primary']};
            min-height: 20px;
            border-radius: 6px;
        }}
        
        QScrollBar::handle:vertical:hover {{
            background-color: {palette['primary_variant']};
        }}
        
        QScrollBar:horizontal {{
            background-color: {palette['surface_variant']};
            height: 12px;
            border: none;
        }}
        
        QScrollBar::handle:horizontal {{
            background-color: {palette['primary']};
            min-width: 20px;
            border-radius: 6px;
        }}
        
        QScrollBar::handle:horizontal:hover {{
            background-color: {palette['primary_variant']};
        }}
        
        /* Menu Bar */
        QMenuBar {{
            background-color: {palette['surface']};
            color: {palette['on_surface']};
            border-bottom: 1px solid {palette['surface_variant']};
        }}
        
        QMenuBar::item:selected {{
            background-color: {palette['surface_variant']};
        }}
        
        QMenu {{
            background-color: {palette['surface']};
            color: {palette['on_surface']};
            border: 1px solid {palette['surface_variant']};
        }}
        
        QMenu::item:selected {{
            background-color: {palette['primary']};
            color: {palette['on_primary']};
        }}
        
        /* Status Bar */
        QStatusBar {{
            background-color: {palette['surface']};
            color: {palette['on_surface']};
            border-top: 1px solid {palette['surface_variant']};
        }}
        
        /* Toolbar */
        QToolBar {{
            background-color: {palette['surface']};
            border: none;
            spacing: 4px;
        }}
        
        /* Labels */
        QLabel {{
            color: {palette['on_surface']};
        }}
        
        /* SOC-specific severity colors */
        QLabel[severity="critical"] {{
            color: #D32F2F;
            font-weight: 600;
        }}
        
        QLabel[severity="high"] {{
            color: #F57C00;
            font-weight: 600;
        }}
        
        QLabel[severity="medium"] {{
            color: #FBC02D;
        }}
        
        QLabel[severity="low"] {{
            color: #388E3C;
        }}
        """
        
        return qss
    
    def _generate_red_accent_overrides(self) -> str:
        """Generate QSS overrides to change all blue accent colors to red."""
        return """
        /* Override all blue accent colors to red */
        
        /* Buttons - borders, backgrounds, and text */
        QPushButton {
            border: 2px solid #F44336 !important;
            border-bottom: 2px solid #F44336 !important;
            background-color: transparent !important;
            color: #F44336 !important;
        }
        
        QPushButton:hover {
            border: 2px solid #D32F2F !important;
            border-bottom: 2px solid #D32F2F !important;
            background-color: rgba(244, 67, 54, 0.1) !important;
            color: #D32F2F !important;
        }
        
        QPushButton:pressed {
            border: 2px solid #D32F2F !important;
            border-bottom: 2px solid #D32F2F !important;
            background-color: rgba(244, 67, 54, 0.2) !important;
            color: #D32F2F !important;
        }
        
        /* Button text underline - target any text decoration */
        QPushButton * {
            color: #F44336 !important;
        }
        
        /* QMessageBox buttons specifically */
        QMessageBox QPushButton {
            color: #F44336 !important;
            border: 2px solid #F44336 !important;
        }
        
        QMessageBox QPushButton:hover {
            color: #D32F2F !important;
            border: 2px solid #D32F2F !important;
        }
        
        /* All labels and text in buttons */
        QPushButton QLabel {
            color: #F44336 !important;
        }
        
        /* Focus borders */
        QLineEdit:focus {
            border: 2px solid #F44336 !important;
        }
        
        QComboBox:focus {
            border: 2px solid #F44336 !important;
        }
        
        QTextEdit:focus {
            border: 2px solid #F44336 !important;
        }
        
        /* Tab selected indicators - darker gray instead of red */
        QTabBar::tab:selected {
            background-color: #3C3C3C !important;
            border-bottom: 3px solid #F44336 !important;
            color: #FFFFFF !important;
        }
        
        /* Ensure all tab borders and underlines are red */
        QTabBar::tab {
            border-bottom: 2px solid transparent !important;
        }
        
        QTabBar::tab:selected {
            border-bottom: 3px solid #F44336 !important;
        }
        
        /* Override any blue colors in tabs */
        QTabBar::tab:selected * {
            color: #FFFFFF !important;
        }
        
        /* Scrollbar handles */
        QScrollBar::handle:vertical {
            background-color: #F44336 !important;
        }
        
        QScrollBar::handle:vertical:hover {
            background-color: #D32F2F !important;
        }
        
        QScrollBar::handle:horizontal {
            background-color: #F44336 !important;
        }
        
        QScrollBar::handle:horizontal:hover {
            background-color: #D32F2F !important;
        }
        
        /* Selected table items - remove color override to preserve item text colors */
        QTableWidget::item:selected {
            background-color: rgba(244, 67, 54, 0.3) !important;
        }
        
        /* Group box titles */
        QGroupBox::title {
            color: #F44336 !important;
        }
        
        /* Selected menu items */
        QMenu::item:selected {
            background-color: #F44336 !important;
        }
        
        /* Links */
        QLabel a {
            color: #F44336 !important;
        }
        
        /* Any element with blue color - override to red */
        * {
            selection-background-color: #F44336 !important;
        }
        
        """


def apply_material_theme(app: QApplication, theme_name: str = 'dark_blue', 
                        extra: Optional[Dict] = None) -> bool:
    """
    Apply Material Design theme to the application.
    
    Args:
        app: QApplication instance
        theme_name: Name of the theme to apply
        extra: Extra parameters for qt-material
        
    Returns:
        True if theme applied successfully, False otherwise
    """
    theme = MaterialTheme(theme_name)
    return theme.apply(app, extra)


def get_available_themes() -> List[Dict]:
    """
    Get list of available themes.
    
    Returns:
        List of theme dictionaries with name, description, and file
    """
    return list(AVAILABLE_THEMES.values())


def get_theme_names() -> List[str]:
    """
    Get list of available theme names.
    
    Returns:
        List of theme name strings
    """
    return list(AVAILABLE_THEMES.keys())

