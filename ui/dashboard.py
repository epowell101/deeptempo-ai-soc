"""Main dashboard with tabbed interface."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QTabWidget, QPushButton, QHBoxLayout, QLabel
)
from PyQt6.QtCore import Qt, QTimer

from PyQt6.QtWidgets import QFileDialog, QMessageBox
from pathlib import Path
from datetime import datetime

from ui.widgets.finding_list import FindingListWidget
from ui.widgets.case_list import CaseListWidget
from ui.widgets.attack_layer_view import AttackLayerViewWidget
from services.data_service import DataService
from services.report_service import ReportService


class Dashboard(QWidget):
    """Main dashboard widget with tabbed interface."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.data_service = DataService()
        
        self._setup_ui()
        self._setup_refresh_timer()
    
    def _setup_ui(self):
        """Set up the UI."""
        layout = QVBoxLayout()
        
        # Toolbar
        toolbar = QHBoxLayout()
        
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.refresh_data)
        toolbar.addWidget(refresh_btn)
        
        report_btn = QPushButton("Generate Overall Report")
        report_btn.clicked.connect(self._generate_overall_report)
        toolbar.addWidget(report_btn)
        
        toolbar.addStretch()
        
        layout.addLayout(toolbar)
        
        # Tab widget
        self.tabs = QTabWidget()
        
        # Findings tab
        self.findings_widget = FindingListWidget(self)
        self.tabs.addTab(self.findings_widget, "Findings")
        
        # Cases tab
        self.cases_widget = CaseListWidget(self)
        self.tabs.addTab(self.cases_widget, "Cases")
        
        # Evidence tab (placeholder for now)
        evidence_widget = QWidget()
        evidence_layout = QVBoxLayout()
        evidence_label = QLabel("Evidence view coming soon...")
        evidence_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        evidence_layout.addWidget(evidence_label)
        evidence_widget.setLayout(evidence_layout)
        self.tabs.addTab(evidence_widget, "Evidence")
        
        # ATT&CK tab
        self.attack_widget = AttackLayerViewWidget(self)
        self.tabs.addTab(self.attack_widget, "ATT&CK")
        
        layout.addWidget(self.tabs)
        
        self.setLayout(layout)
    
    def _setup_refresh_timer(self):
        """Set up automatic refresh timer."""
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_data)
        self.refresh_timer.start(30000)  # Refresh every 30 seconds
    
    def refresh_data(self):
        """Refresh all data."""
        # Force refresh from data service
        self.data_service.get_findings(force_refresh=True)
        self.data_service.get_cases(force_refresh=True)
        
        # Refresh widgets
        if hasattr(self, 'findings_widget'):
            self.findings_widget.refresh()
        if hasattr(self, 'cases_widget'):
            self.cases_widget.refresh()
        if hasattr(self, 'attack_widget'):
            self.attack_widget.refresh()
    
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
        findings = self.data_service.get_findings()
        cases = self.data_service.get_cases()
        
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

