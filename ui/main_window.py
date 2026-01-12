"""Main application window for DeepTempo AI SOC."""

import sys
import logging
from pathlib import Path
from PyQt6.QtWidgets import (
    QMainWindow, QMenuBar, QStatusBar, QToolBar, QMessageBox, QApplication,
    QDockWidget
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QAction, QIcon

from PyQt6.QtWidgets import QFileDialog, QMessageBox
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)

from ui.dashboard import Dashboard
from ui.claude_chat_tabbed import TabbedClaudeChat
from ui.setup_wizard import SetupWizard
from ui.config_manager import ConfigManager
from ui.timesketch_config import TimesketchConfigDialog
from ui.settings_console import SettingsConsole
from services.data_service import DataService
from services.report_service import ReportService


class MainWindow(QMainWindow):
    """Main application window."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DeepTempo AI SOC")
        
        # Get screen size and set window to full available screen size
        screen = QApplication.primaryScreen()
        if screen:
            screen_geometry = screen.availableGeometry()
            # Use full available screen (excludes taskbar/dock)
            self.setGeometry(screen_geometry)
        else:
            # Fallback to default size if screen not available
            self.setGeometry(100, 100, 1200, 900)
        
        # Initialize components
        self.dashboard = None
        self.claude_chat = None
        self.claude_dock = None
        self.claude_toggle_action = None
        self.search_widget = None
        
        self._setup_ui()
        self._setup_menu()
        self._setup_toolbar()
        self._setup_statusbar()
        
        # Check if setup is needed
        self._check_setup()
        
        # Check and start Timesketch Docker if configured (after a short delay to not block startup)
        QTimer.singleShot(2000, self._check_and_start_timesketch_docker)
        
        # Check Timesketch availability (after Docker has time to start)
        QTimer.singleShot(5000, self._check_timesketch_availability)
    
    def _setup_ui(self):
        """Set up the main UI components."""
        # Default to dashboard view
        self._show_dashboard()
        
        # Set up Claude Chat as a side drawer
        self._setup_claude_drawer()
    
    def _setup_menu(self):
        """Set up the menu bar."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("&File")
        
        setup_action = QAction("&Setup Wizard...", self)
        setup_action.setShortcut("Ctrl+S")
        setup_action.triggered.connect(self._show_setup_wizard)
        file_menu.addAction(setup_action)
        
        config_action = QAction("&Configure Claude Desktop...", self)
        config_action.triggered.connect(self._show_config_manager)
        file_menu.addAction(config_action)
        
        ts_config_action = QAction("&Configure Timesketch...", self)
        ts_config_action.triggered.connect(self._show_timesketch_config)
        file_menu.addAction(ts_config_action)
        
        settings_action = QAction("&Settings Console...", self)
        settings_action.setShortcut("Ctrl+,")
        settings_action.triggered.connect(self._show_settings_console)
        file_menu.addAction(settings_action)
        
        file_menu.addSeparator()
        
        generate_report_action = QAction("&Generate Overall Report...", self)
        generate_report_action.setShortcut("Ctrl+R")
        generate_report_action.triggered.connect(self._generate_overall_report)
        file_menu.addAction(generate_report_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # View menu
        view_menu = menubar.addMenu("&View")
        
        dashboard_action = QAction("&Dashboard", self)
        dashboard_action.setShortcut("Ctrl+D")
        dashboard_action.triggered.connect(self._show_dashboard)
        view_menu.addAction(dashboard_action)
        
        view_menu.addSeparator()
        
        claude_action = QAction("&Toggle Claude Chat", self)
        claude_action.setShortcut("Ctrl+C")
        claude_action.triggered.connect(self._toggle_claude_drawer)
        view_menu.addAction(claude_action)
        
        # Help menu
        help_menu = menubar.addMenu("&Help")
        
        about_action = QAction("&About", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)
    
    def _setup_toolbar(self):
        """Set up the toolbar."""
        toolbar = QToolBar("Main Toolbar")
        self.addToolBar(toolbar)
        
        # Dashboard button
        dashboard_action = QAction("Dashboard", self)
        dashboard_action.triggered.connect(self._show_dashboard)
        toolbar.addAction(dashboard_action)
        
        toolbar.addSeparator()
        
        # Claude Chat toggle button
        claude_action = QAction("Claude Chat", self)
        claude_action.setCheckable(True)
        claude_action.triggered.connect(self._toggle_claude_drawer)
        toolbar.addAction(claude_action)
        self.claude_toggle_action = claude_action
        
        toolbar.addSeparator()
        
        # Settings Console button
        settings_action = QAction("Settings", self)
        settings_action.triggered.connect(self._show_settings_console)
        toolbar.addAction(settings_action)
    
    def _setup_statusbar(self):
        """Set up the status bar."""
        self.statusBar().showMessage("Ready")
        
        # Update status periodically
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self._update_status)
        self.status_timer.start(5000)  # Update every 5 seconds
    
    def _update_status(self):
        """Update status bar with system information."""
        from services.data_service import DataService
        data_service = DataService()
        
        findings_count = len(data_service.get_findings())
        cases_count = len(data_service.get_cases())
        
        status_text = f"Findings: {findings_count} | Cases: {cases_count}"
        self.statusBar().showMessage(status_text)
    
    def _check_setup(self):
        """Check if setup is needed."""
        venv_path = Path(__file__).parent.parent / "venv"
        if not venv_path.exists():
            reply = QMessageBox.question(
                self,
                "Setup Required",
                "Virtual environment not found. Would you like to run the setup wizard?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                self._show_setup_wizard()
    
    def _check_and_start_timesketch_docker(self):
        """Check if Timesketch Docker should be auto-started and start it if needed."""
        from ui.timesketch_config import TimesketchConfigDialog
        from services.timesketch_docker_service import TimesketchDockerService
        import json
        
        config_file = TimesketchConfigDialog.CONFIG_FILE
        if not config_file.exists():
            return
        
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
            
            # Check if auto-start is enabled
            if not config.get('auto_start_docker', False):
                return
            
            # Check if server URL is localhost (Docker management only for localhost)
            server_url = config.get('server_url', '')
            if not server_url or 'localhost' not in server_url:
                return
            
            # Initialize Docker service
            docker_service = TimesketchDockerService()
            
            if not docker_service.is_docker_available():
                logger.warning("Docker CLI is not available - cannot auto-start Timesketch")
                return
            
            # Check if Docker daemon is running
            if not docker_service.is_docker_daemon_running():
                logger.warning("Docker daemon is not running - cannot auto-start Timesketch container. Please start Docker Desktop.")
                return
            
            # Check if container is already running
            if docker_service.is_container_running():
                logger.info("Timesketch Docker container is already running")
                return
            
            # Start the container
            logger.info("Auto-starting Timesketch Docker container...")
            port = 5000  # default
            if ':' in server_url:
                try:
                    port_str = server_url.split(':')[-1].split('/')[0]
                    port = int(port_str)
                except ValueError:
                    pass
            
            success, message = docker_service.start_container(port=port)
            if success:
                logger.info(f"Timesketch Docker container started: {message}")
            else:
                logger.warning(f"Failed to auto-start Timesketch Docker: {message}")
        
        except Exception as e:
            logger.error(f"Error checking/starting Timesketch Docker: {e}")
    
    def _check_timesketch_availability(self):
        """Check if Timesketch server is available and show helpful message if not."""
        from ui.timesketch_config import TimesketchConfigDialog
        import json
        
        config_file = TimesketchConfigDialog.CONFIG_FILE
        if not config_file.exists():
            # Timesketch not configured - this is fine, just return
            return
        
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
            
            server_url = config.get('server_url', '')
            if not server_url:
                return
            
            # Try to test connection
            timesketch_service = TimesketchConfigDialog.load_service()
            if timesketch_service:
                success, message = timesketch_service.test_connection()
                if not success:
                    # Only show message if auto-start is not enabled (to avoid double messages)
                    auto_start = config.get('auto_start_docker', False)
                    if not auto_start:
                        # Show helpful message
                        reply = QMessageBox.question(
                            self,
                            "Timesketch Server Not Available",
                            f"Timesketch server is configured but not reachable:\n\n"
                            f"Server: {server_url}\n"
                            f"Error: {message}\n\n"
                            f"Timesketch is an external service that must be running separately.\n\n"
                            f"To start Timesketch:\n"
                            f"• Use Settings → Timesketch → Start Docker Server\n"
                            f"• Or enable 'Auto-start Docker server' in Settings\n"
                            f"• Or configure a different server URL\n\n"
                            f"Would you like to configure Timesketch now?",
                            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                            QMessageBox.StandardButton.No
                        )
                        if reply == QMessageBox.StandardButton.Yes:
                            self._show_settings_console()
        except Exception as e:
            # Silently fail - don't interrupt startup for this check
            pass
    
    def _show_setup_wizard(self):
        """Show the setup wizard."""
        wizard = SetupWizard(self)
        wizard.exec()
    
    def _show_config_manager(self):
        """Show the configuration manager."""
        manager = ConfigManager(self)
        manager.exec()
    
    def _show_timesketch_config(self):
        """Show the Timesketch configuration dialog."""
        dialog = TimesketchConfigDialog(self)
        dialog.exec()
    
    def _show_settings_console(self):
        """Show the unified settings console."""
        console = SettingsConsole(self)
        console.exec()
    
    def _show_dashboard(self):
        """Show the dashboard."""
        # Always create a new dashboard to avoid deleted widget issues
        self.dashboard = Dashboard(self)
        self.setCentralWidget(self.dashboard)
    
    def create_investigation_tab_for_finding(self, finding):
        """
        Create a new chat tab for a specific finding.
        This is called from the dashboard when user clicks "Analyze in New Tab".
        """
        # Create tab in Claude Chat drawer
        if self.claude_chat:
            self.claude_chat.create_tab_for_finding(finding)
            
            # Make sure drawer is visible
            if not self.claude_dock.isVisible():
                self.claude_dock.show()
                if self.claude_toggle_action:
                    self.claude_toggle_action.setChecked(True)
            
            # Show status message
            finding_id = finding.get('finding_id', 'Unknown')
            self.statusBar().showMessage(f"Created new chat tab for finding: {finding_id}", 5000)
    
    def _setup_claude_drawer(self):
        """Set up Claude Chat as a side drawer."""
        # Create dock widget
        self.claude_dock = QDockWidget("Claude Chat", self)
        self.claude_dock.setAllowedAreas(Qt.DockWidgetArea.RightDockWidgetArea | Qt.DockWidgetArea.LeftDockWidgetArea)
        
        # Configure dock widget features - allow moving, closing, and resizing
        self.claude_dock.setFeatures(
            QDockWidget.DockWidgetFeature.DockWidgetMovable |
            QDockWidget.DockWidgetFeature.DockWidgetClosable
        )
        
        # Create Tabbed Claude Chat widget
        self.claude_chat = TabbedClaudeChat(self)
        self.claude_dock.setWidget(self.claude_chat)
        
        # Set minimum and maximum width constraints
        self.claude_dock.setMinimumWidth(350)  # Increased from 250 for better readability
        self.claude_dock.setMaximumWidth(800)  # Prevent it from taking too much space
        
        # Add dock widget to main window (right side by default)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.claude_dock)
        
        # Initially hide the drawer
        self.claude_dock.setVisible(False)
        
        # Connect visibility changes to update toggle button
        self.claude_dock.visibilityChanged.connect(self._on_claude_drawer_visibility_changed)
        
        # Store initial window size to prevent expansion
        self._initial_window_size = None
    
    def _toggle_claude_drawer(self):
        """Toggle Claude Chat drawer visibility."""
        if self.claude_dock.isVisible():
            # Hide the drawer - content will expand back
            self.claude_dock.setVisible(False)
        else:
            # Store current window geometry before opening drawer
            current_geometry = self.geometry()
            
            # Temporarily lock window size to prevent expansion
            min_size = self.minimumSize()
            max_size = self.maximumSize()
            self.setFixedSize(self.size())
            
            # Show the drawer
            self.claude_dock.setVisible(True)
            
            # Set drawer width to 1/3 of window width (but not too wide)
            window_width = self.width()
            drawer_width = min(max(window_width // 3, 350), 600)  # Between 350-600px
            self.resizeDocks([self.claude_dock], [drawer_width], Qt.Orientation.Horizontal)
            
            # Restore window size constraints after a brief moment
            QTimer.singleShot(100, lambda: (
                self.setMinimumSize(min_size),
                self.setMaximumSize(max_size),
                self.setGeometry(current_geometry)
            ))
            
            # Focus the message input when opening
            if hasattr(self.claude_chat, 'message_edit'):
                self.claude_chat.message_edit.setFocus()
    
    def _on_claude_drawer_visibility_changed(self, visible: bool):
        """Update toggle button state when drawer visibility changes."""
        if hasattr(self, 'claude_toggle_action'):
            self.claude_toggle_action.setChecked(visible)
    
    def _show_mcp_manager(self):
        """Show the MCP manager in Settings Console."""
        # Open Settings Console and switch to MCP tab
        console = SettingsConsole(self)
        # Find the MCP tab index and set it as current
        for i in range(console.tabs.count()):
            if console.tabs.tabText(i) == "MCP Servers":
                console.tabs.setCurrentIndex(i)
                break
        console.exec()
    
    def _show_search(self):
        """Show the enhanced search widget."""
        from ui.widgets.search_widget import SearchWidget
        # Always create a new search widget to avoid deleted widget issues
        self.search_widget = SearchWidget(self)
        self.setCentralWidget(self.search_widget)
    
    def _start_auto_sync(self):
        """Start auto-sync service if configured."""
        try:
            from services.auto_sync_service import get_auto_sync_service
            from ui.timesketch_config import TimesketchConfigDialog
            import json
            
            auto_sync_service = get_auto_sync_service()
            config_file = TimesketchConfigDialog.CONFIG_FILE
            
            if config_file.exists():
                with open(config_file, 'r') as f:
                    config = json.load(f)
                    if config.get('auto_sync', False):
                        sync_interval = config.get('sync_interval', 300)
                        auto_sync_service.start(sync_interval)
        except Exception:
            pass  # Auto-sync will start when configured
    
    def _generate_overall_report(self):
        """Generate overall PDF report."""
        try:
            report_service = ReportService()
        except ImportError as e:
            QMessageBox.warning(
                self,
                "ReportLab Not Installed",
                f"PDF report generation requires reportlab.\n\n"
                f"Please install it with:\n"
                f"pip install reportlab\n\n"
                f"Or run the setup wizard to install all dependencies."
            )
            return
        
        # Get file path
        default_filename = f"deeptempo_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Overall Report",
            default_filename,
            "PDF Files (*.pdf)"
        )
        
        if not file_path:
            return
        
        # Get data
        data_service = DataService()
        findings = data_service.get_findings()
        cases = data_service.get_cases()
        
        if not findings and not cases:
            QMessageBox.warning(
                self,
                "No Data",
                "No findings or cases available to generate a report."
            )
            return
        
        # Generate report
        success = report_service.generate_overall_report(
            Path(file_path),
            findings,
            cases,
            include_findings_detail=True
        )
        
        if success:
            QMessageBox.information(
                self,
                "Success",
                f"Report generated successfully!\n\nSaved to: {file_path}"
            )
        else:
            QMessageBox.critical(
                self,
                "Error",
                "Failed to generate report. Please check the logs for details."
            )
    
    def analyze_finding_with_claude(self, finding):
        """
        Open Claude chat and start analyzing a finding.
        
        Args:
            finding: The finding dict to analyze
        """
        # Show Claude drawer if not visible (use toggle method to prevent window resize)
        if self.claude_dock and not self.claude_dock.isVisible():
            self._toggle_claude_drawer()
        
        # Send finding to Claude chat for analysis
        if self.claude_chat:
            self.claude_chat.analyze_finding(finding)
    
    def _show_about(self):
        """Show about dialog."""
        QMessageBox.about(
            self,
            "About DeepTempo AI SOC",
            "DeepTempo AI SOC Desktop Application\n\n"
            "Version 1.0.0\n\n"
            "An AI-powered Security Operations Center interface."
        )

