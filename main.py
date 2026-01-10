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
import qdarkstyle

from ui.main_window import MainWindow

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


def main():
    """Main application entry point."""
    # Create application
    app = QApplication(sys.argv)
    app.setApplicationName("DeepTempo AI SOC")
    app.setOrganizationName("DeepTempo")
    
    # Set application style (dark theme)
    try:
        app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt6())
    except Exception as e:
        logger.warning(f"Could not load dark theme: {e}")
    
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

