"""Main dashboard with tabbed interface."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QTabWidget, QPushButton, QHBoxLayout, QLabel,
    QComboBox, QFileDialog, QMessageBox
)
from PyQt6.QtCore import Qt, QTimer
from pathlib import Path
from datetime import datetime

from ui.widgets.finding_list import FindingListWidget
from ui.widgets.case_list import CaseListWidget
from ui.widgets.attack_layer_view import AttackLayerViewWidget
from ui.widgets.attack_flow_widget import AttackFlowWidget
from ui.widgets.entity_investigation_widget import EntityInvestigationWidget
from ui.widgets.workflow_widget import WorkflowWidget
from ui.widgets.sketch_manager_widget import SketchManagerWidget
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
        
        # Data source selector
        toolbar.addWidget(QLabel("Data Source:"))
        self.data_source_combo = QComboBox()
        self.data_source_combo.addItems(["Local Files", "S3 Bucket", "Select File..."])
        self.data_source_combo.currentIndexChanged.connect(self._on_data_source_changed)
        toolbar.addWidget(self.data_source_combo)
        
        toolbar.addWidget(QLabel("|"))
        
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.refresh_data)
        toolbar.addWidget(refresh_btn)
        
        report_btn = QPushButton("Generate Overall Report")
        report_btn.clicked.connect(self._generate_overall_report)
        toolbar.addWidget(report_btn)
        
        toolbar.addStretch()
        
        # Status label
        self.data_source_label = QLabel("Source: Local Files")
        toolbar.addWidget(self.data_source_label)
        
        layout.addLayout(toolbar)
        
        # Initialize data source
        self._initialize_data_source()
        
        # Tab widget
        self.tabs = QTabWidget()
        
        # Findings tab
        self.findings_widget = FindingListWidget(self)
        self.tabs.addTab(self.findings_widget, "Findings")
        
        # Cases tab
        self.cases_widget = CaseListWidget(self)
        self.tabs.addTab(self.cases_widget, "Cases")
        
        # Timelines tab (Timesketch integration)
        self.timelines_widget = SketchManagerWidget(self)
        self.tabs.addTab(self.timelines_widget, "Timelines")
        
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
        
        # Attack Flow tab
        self.attack_flow_widget = AttackFlowWidget(self)
        self.tabs.addTab(self.attack_flow_widget, "Attack Flow")
        
        # Entity Investigation tab
        self.entity_widget = EntityInvestigationWidget(self)
        self.tabs.addTab(self.entity_widget, "Entities")
        
        # Workflow tab
        self.workflow_widget = WorkflowWidget(self)
        self.tabs.addTab(self.workflow_widget, "Workflow")
        
        # Make tabs widget expand to fill available space (relative sizing)
        layout.addWidget(self.tabs, 1)  # Stretch factor of 1 makes it take available space
        
        self.setLayout(layout)
    
    def _setup_refresh_timer(self):
        """Set up automatic refresh timer."""
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_data)
        self.refresh_timer.start(30000)  # Refresh every 30 seconds
    
    def _initialize_data_source(self):
        """Initialize data source from settings."""
        # Try to load S3 config if available
        if self.data_service.load_s3_config():
            self.data_source_combo.setCurrentIndex(1)  # S3 Bucket
            self.data_source_label.setText("Source: S3 Bucket")
        else:
            self.data_source_combo.setCurrentIndex(0)  # Local Files
            self.data_source_label.setText("Source: Local Files")
    
    def _on_data_source_changed(self, index: int):
        """Handle data source change."""
        if index == 0:  # Local Files
            self.data_service.set_data_source("local")
            self.data_source_label.setText("Source: Local Files")
            self.refresh_data()
        elif index == 1:  # S3 Bucket
            if self.data_service.load_s3_config():
                self.data_source_label.setText("Source: S3 Bucket")
                self.refresh_data()
            else:
                QMessageBox.warning(
                    self,
                    "S3 Not Configured",
                    "S3 bucket is not configured. Please configure it in Settings → S3 Storage."
                )
                self.data_source_combo.setCurrentIndex(0)
        elif index == 2:  # Select File
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "Select Findings File",
                "",
                "JSON Files (*.json);;All Files (*)"
            )
            
            if file_path:
                self.data_service.set_data_source("file", file_path=file_path)
                self.data_source_label.setText(f"Source: {Path(file_path).name}")
                self.refresh_data()
            else:
                # Revert to previous selection
                self.data_source_combo.setCurrentIndex(0)
    
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
        if hasattr(self, 'timelines_widget'):
            self.timelines_widget.refresh()
        if hasattr(self, 'attack_widget'):
            self.attack_widget.refresh()
        if hasattr(self, 'attack_flow_widget'):
            self.attack_flow_widget.refresh()
        if hasattr(self, 'entity_widget'):
            self.entity_widget.refresh()
        if hasattr(self, 'workflow_widget'):
            self.workflow_widget.refresh()
    
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

