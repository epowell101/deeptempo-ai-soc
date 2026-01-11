"""Main application window for DeepTempo AI SOC."""

import sys
from pathlib import Path
from PyQt6.QtWidgets import (
    QMainWindow, QMenuBar, QStatusBar, QToolBar, QMessageBox, QApplication
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QAction, QIcon

from PyQt6.QtWidgets import QFileDialog, QMessageBox
from pathlib import Path
from datetime import datetime

from ui.dashboard import Dashboard
from ui.claude_chat import ClaudeChat
from ui.mcp_manager import MCPManager
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
        self.setGeometry(100, 100, 1400, 900)
        
        # Initialize components
        self.dashboard = None
        self.claude_chat = None
        self.mcp_manager = None
        self.timesketch_manager = None
        self.search_widget = None
        
        self._setup_ui()
        self._setup_menu()
        self._setup_toolbar()
        self._setup_statusbar()
        
        # Check if setup is needed
        self._check_setup()
    
    def _setup_ui(self):
        """Set up the main UI components."""
        # Default to dashboard view
        self._show_dashboard()
    
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
        
        claude_action = QAction("&Claude Chat", self)
        claude_action.setShortcut("Ctrl+C")
        claude_action.triggered.connect(self._show_claude_chat)
        view_menu.addAction(claude_action)
        
        mcp_action = QAction("&MCP Manager", self)
        mcp_action.setShortcut("Ctrl+M")
        mcp_action.triggered.connect(self._show_mcp_manager)
        view_menu.addAction(mcp_action)
        
        ts_manager_action = QAction("&Timesketch Manager", self)
        ts_manager_action.setShortcut("Ctrl+T")
        ts_manager_action.triggered.connect(self._show_timesketch_manager)
        view_menu.addAction(ts_manager_action)
        
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
        
        # Claude Chat button
        claude_action = QAction("Claude Chat", self)
        claude_action.triggered.connect(self._show_claude_chat)
        toolbar.addAction(claude_action)
        
        toolbar.addSeparator()
        
        # MCP Manager button
        mcp_action = QAction("MCP Manager", self)
        mcp_action.triggered.connect(self._show_mcp_manager)
        toolbar.addAction(mcp_action)
        
        toolbar.addSeparator()
        
        # Timesketch Manager button
        ts_action = QAction("Timesketch", self)
        ts_action.triggered.connect(self._show_timesketch_manager)
        toolbar.addAction(ts_action)
        
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
    
    def _show_claude_chat(self):
        """Show the Claude chat interface."""
        # Always create a new chat widget to avoid deleted widget issues
        self.claude_chat = ClaudeChat(self)
        self.setCentralWidget(self.claude_chat)
    
    def _show_mcp_manager(self):
        """Show the MCP manager."""
        # Always create a new manager widget to avoid deleted widget issues
        self.mcp_manager = MCPManager(self)
        self.setCentralWidget(self.mcp_manager)
    
    def _show_timesketch_manager(self):
        """Show the Timesketch manager."""
        from ui.widgets.sketch_manager_widget import SketchManagerWidget
        # Always create a new manager widget to avoid deleted widget issues
        self.timesketch_manager = SketchManagerWidget(self)
        self.setCentralWidget(self.timesketch_manager)
    
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
    
    def _show_about(self):
        """Show about dialog."""
        QMessageBox.about(
            self,
            "About DeepTempo AI SOC",
            "DeepTempo AI SOC Desktop Application\n\n"
            "Version 1.0.0\n\n"
            "An AI-powered Security Operations Center interface."
        )

