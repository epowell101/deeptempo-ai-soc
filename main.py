#!/usr/bin/env python3
"""
DeepTempo AI SOC Desktop Application

Main entry point for the PyQt6 desktop application.
"""

import sys
import logging
from pathlib import Path
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

from ui.main_window import MainWindow
from ui.themes import apply_material_theme

# Configure logging
log_dir = Path.home() / '.deeptempo'
log_dir.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(log_dir / 'app.log')
    ]
)

logger = logging.getLogger(__name__)


def _load_theme_preference() -> str:
    """Load saved theme preference from config file."""
    try:
        config_file = Path.home() / '.deeptempo' / 'theme_config.json'
        if config_file.exists():
            import json
            with open(config_file, 'r') as f:
                config = json.load(f)
                return config.get('theme', 'dark_blue')
    except Exception:
        pass
    return 'dark_blue'  # Default theme


def main():
    """Main application entry point."""
    # Create application
    app = QApplication(sys.argv)
    app.setApplicationName("DeepTempo AI SOC")
    app.setOrganizationName("DeepTempo")
    
    # Apply Material Design theme
    # Try to load saved theme preference, default to dark_blue
    theme_name = _load_theme_preference()
    
    try:
        success = apply_material_theme(app, theme_name=theme_name)
        if success:
            logger.info(f"Applied Material Design theme: {theme_name}")
        else:
            logger.warning("Failed to apply Material theme, falling back to qdarkstyle")
            # Fallback to qdarkstyle if Material theme fails
            try:
                import qdarkstyle
                app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt6())
            except ImportError:
                logger.warning("qdarkstyle not available, using system default")
    except Exception as e:
        logger.error(f"Error applying Material theme: {e}")
        # Fallback to qdarkstyle
        try:
            import qdarkstyle
            app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt6())
        except ImportError:
            pass
    
    # Note: High DPI scaling is enabled by default in PyQt6
    # The AA_EnableHighDpiScaling and AA_UseHighDpiPixmaps attributes
    # from PyQt5 were removed in PyQt6 as they're always enabled
    
    # Create and show main window
    try:
        window = MainWindow()
        window.show()
        
        logger.info("Application started successfully")
        
        # Run event loop
        sys.exit(app.exec())
    
    except Exception as e:
        logger.critical(f"Failed to start application: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

