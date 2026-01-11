"""Case list widget with create/update functionality."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLineEdit, QComboBox, QLabel, QDialog, QFormLayout,
    QTextEdit, QMessageBox, QListWidget, QListWidgetItem, QFileDialog, QFrame
)
from PyQt6.QtCore import Qt
from pathlib import Path
from datetime import datetime

from services.data_service import DataService
from services.report_service import ReportService
from services.sketch_manager import SketchManager
from services.timeline_service import TimelineService
from services.timesketch_service import TimesketchService
from ui.timesketch_config import TimesketchConfigDialog


class CreateCaseDialog(QDialog):
    """Dialog for creating a new case."""
    
    def __init__(self, available_findings: list, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Create New Case")
        self.setMinimumSize(500, 400)
        
        self.available_findings = available_findings
        self.case_data = None
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the UI."""
        layout = QVBoxLayout()
        
        form_layout = QFormLayout()
        
        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("Enter case title...")
        form_layout.addRow("Title:", self.title_edit)
        
        self.description_edit = QTextEdit()
        self.description_edit.setPlaceholderText("Enter case description...")
        self.description_edit.setMaximumHeight(100)
        form_layout.addRow("Description:", self.description_edit)
        
        self.priority_combo = QComboBox()
        self.priority_combo.addItems(["low", "medium", "high", "critical"])
        self.priority_combo.setCurrentText("medium")
        form_layout.addRow("Priority:", self.priority_combo)
        
        self.status_combo = QComboBox()
        self.status_combo.addItems(["new", "open", "in-progress", "resolved", "closed"])
        self.status_combo.setCurrentText("open")
        form_layout.addRow("Status:", self.status_combo)
        
        layout.addLayout(form_layout)
        
        # Findings selection
        findings_label = QLabel("Select Findings:")
        layout.addWidget(findings_label)
        
        self.findings_list = QListWidget()
        self.findings_list.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        
        for finding in self.available_findings:
            finding_id = finding.get('finding_id', 'Unknown')
            severity = finding.get('severity', 'unknown')
            item_text = f"{finding_id} ({severity})"
            item = QListWidgetItem(item_text)
            item.setData(Qt.ItemDataRole.UserRole, finding_id)
            self.findings_list.addItem(item)
        
        layout.addWidget(self.findings_list)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        create_btn = QPushButton("Create Case")
        create_btn.clicked.connect(self._create_case)
        button_layout.addWidget(create_btn)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def _create_case(self):
        """Create the case."""
        title = self.title_edit.text().strip()
        if not title:
            QMessageBox.warning(self, "Validation Error", "Title is required.")
            return
        
        # Get selected finding IDs
        selected_items = self.findings_list.selectedItems()
        finding_ids = [item.data(Qt.ItemDataRole.UserRole) for item in selected_items]
        
        if not finding_ids:
            reply = QMessageBox.question(
                self,
                "No Findings Selected",
                "No findings selected. Create case without findings?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.No:
                return
        
        self.case_data = {
            'title': title,
            'description': self.description_edit.toPlainText(),
            'priority': self.priority_combo.currentText(),
            'status': self.status_combo.currentText(),
            'finding_ids': finding_ids
        }
        
        self.accept()


class CaseListWidget(QWidget):
    """Widget for displaying and managing cases."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.data_service = DataService()
        self.cases = []
        
        self._setup_ui()
        self.refresh()
    
    def _setup_ui(self):
        """Set up the UI."""
        layout = QVBoxLayout()
        
        # Toolbar
        toolbar = QHBoxLayout()
        
        create_btn = QPushButton("Create Case")
        create_btn.clicked.connect(self._create_case)
        toolbar.addWidget(create_btn)
        
        update_btn = QPushButton("Update Case")
        update_btn.clicked.connect(self._update_case)
        toolbar.addWidget(update_btn)
        
        report_btn = QPushButton("Generate Case Report")
        report_btn.clicked.connect(self._generate_case_report)
        toolbar.addWidget(report_btn)
        
        # Add separator using QFrame
        separator1 = QFrame()
        separator1.setFrameShape(QFrame.Shape.VLine)
        separator1.setFrameShadow(QFrame.Shadow.Sunken)
        toolbar.addWidget(separator1)
        
        export_ts_btn = QPushButton("Export to Timesketch")
        export_ts_btn.clicked.connect(self._export_to_timesketch)
        toolbar.addWidget(export_ts_btn)
        
        view_timeline_btn = QPushButton("View Timeline")
        view_timeline_btn.clicked.connect(self._view_timeline)
        toolbar.addWidget(view_timeline_btn)
        
        # Add separator using QFrame
        separator2 = QFrame()
        separator2.setFrameShape(QFrame.Shape.VLine)
        separator2.setFrameShadow(QFrame.Shadow.Sunken)
        toolbar.addWidget(separator2)
        
        correlation_btn = QPushButton("Correlation Analysis")
        correlation_btn.clicked.connect(self._show_correlation)
        toolbar.addWidget(correlation_btn)
        
        analyzer_btn = QPushButton("Run Analyzers")
        analyzer_btn.clicked.connect(self._show_analyzers)
        toolbar.addWidget(analyzer_btn)
        
        collaboration_btn = QPushButton("Collaboration")
        collaboration_btn.clicked.connect(self._show_collaboration)
        toolbar.addWidget(collaboration_btn)
        
        toolbar.addStretch()
        
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.refresh)
        toolbar.addWidget(refresh_btn)
        
        layout.addLayout(toolbar)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "Case ID", "Title", "Status", "Priority", "Findings", "Timesketch", "Created"
        ])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        
        layout.addWidget(self.table)
        
        self.setLayout(layout)
    
    def refresh(self):
        """Refresh cases from data service."""
        self.cases = self.data_service.get_cases(force_refresh=True)
        self._populate_table()
    
    def _populate_table(self):
        """Populate the table with cases."""
        from services.sketch_manager import SketchManager
        
        sketch_manager = SketchManager()
        self.table.setRowCount(len(self.cases))
        
        for row, case in enumerate(self.cases):
            self.table.setItem(row, 0, QTableWidgetItem(case.get('case_id', '')))
            self.table.setItem(row, 1, QTableWidgetItem(case.get('title', '')))
            self.table.setItem(row, 2, QTableWidgetItem(case.get('status', '')))
            self.table.setItem(row, 3, QTableWidgetItem(case.get('priority', '')))
            
            finding_ids = case.get('finding_ids', [])
            self.table.setItem(row, 4, QTableWidgetItem(str(len(finding_ids))))
            
            # Timesketch status
            mapping = sketch_manager.get_sketch_for_case(case.get('case_id', ''))
            if mapping:
                status = mapping.get('sync_status', 'unknown')
                status_item = QTableWidgetItem("✓ Synced" if status == 'synced' else status)
                if status == 'synced':
                    status_item.setForeground(Qt.GlobalColor.green)
                self.table.setItem(row, 5, status_item)
            else:
                self.table.setItem(row, 5, QTableWidgetItem("Not exported"))
            
            created = case.get('created_at', '')
            if created:
                created = created.split('T')[0]
            self.table.setItem(row, 6, QTableWidgetItem(created))
        
        self.table.resizeColumnsToContents()
    
    def _get_selected_case(self):
        """Get the currently selected case."""
        row = self.table.currentRow()
        if row >= 0 and row < len(self.cases):
            return self.cases[row]
        return None
    
    def _create_case(self):
        """Create a new case."""
        findings = self.data_service.get_findings()
        
        dialog = CreateCaseDialog(findings, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            case_data = dialog.case_data
            case = self.data_service.create_case(
                title=case_data['title'],
                finding_ids=case_data['finding_ids'],
                priority=case_data['priority'],
                description=case_data['description'],
                status=case_data['status']
            )
            
            if case:
                QMessageBox.information(self, "Success", f"Case created: {case['case_id']}")
                self.refresh()
            else:
                QMessageBox.critical(self, "Error", "Failed to create case.")
    
    def _update_case(self):
        """Update selected case."""
        case = self._get_selected_case()
        if not case:
            QMessageBox.information(self, "No Selection", "Please select a case first.")
            return
        
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Update Case: {case['case_id']}")
        dialog.setMinimumSize(400, 300)
        
        layout = QVBoxLayout()
        
        form_layout = QFormLayout()
        
        status_combo = QComboBox()
        status_combo.addItems(["new", "open", "in-progress", "resolved", "closed"])
        status_combo.setCurrentText(case.get('status', 'open'))
        form_layout.addRow("Status:", status_combo)
        
        priority_combo = QComboBox()
        priority_combo.addItems(["low", "medium", "high", "critical"])
        priority_combo.setCurrentText(case.get('priority', 'medium'))
        form_layout.addRow("Priority:", priority_combo)
        
        notes_edit = QTextEdit()
        notes_edit.setPlaceholderText("Add notes...")
        notes_edit.setMaximumHeight(100)
        form_layout.addRow("Notes:", notes_edit)
        
        layout.addLayout(form_layout)
        
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(dialog.reject)
        button_layout.addWidget(cancel_btn)
        
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(lambda: self._save_case_update(
            dialog, case['case_id'], status_combo.currentText(),
            priority_combo.currentText(), notes_edit.toPlainText()
        ))
        button_layout.addWidget(save_btn)
        
        layout.addLayout(button_layout)
        dialog.setLayout(layout)
        
        dialog.exec()
    
    def _save_case_update(self, dialog, case_id, status, priority, notes):
        """Save case update."""
        updates = {
            'status': status,
            'priority': priority
        }
        
        if notes.strip():
            updates['notes'] = notes
        
        if self.data_service.update_case(case_id, **updates):
            QMessageBox.information(dialog, "Success", "Case updated.")
            dialog.accept()
            self.refresh()
        else:
            QMessageBox.critical(dialog, "Error", "Failed to update case.")
    
    def _generate_case_report(self):
        """Generate PDF report for selected case."""
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
        
        case = self._get_selected_case()
        if not case:
            QMessageBox.information(self, "No Selection", "Please select a case first.")
            return
        
        # Get file path
        case_id = case.get('case_id', 'case')
        default_filename = f"{case_id}_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Case Report",
            default_filename,
            "PDF Files (*.pdf)"
        )
        
        if not file_path:
            return
        
        # Get related findings
        finding_ids = case.get('finding_ids', [])
        findings = []
        for finding_id in finding_ids:
            finding = self.data_service.get_finding(finding_id)
            if finding:
                findings.append(finding)
        
        # Generate report
        success = report_service.generate_case_report(
            Path(file_path),
            case,
            findings
        )
        
        if success:
            QMessageBox.information(
                self,
                "Success",
                f"Case report generated successfully!\n\nSaved to: {file_path}"
            )
        else:
            QMessageBox.critical(
                self,
                "Error",
                "Failed to generate case report. Please check the logs for details."
            )
    
    def _export_to_timesketch(self):
        """Export selected case to Timesketch."""
        case = self._get_selected_case()
        if not case:
            QMessageBox.information(self, "No Selection", "Please select a case first.")
            return
        
        # Check if Timesketch is configured
        try:
            timesketch_service = TimesketchConfigDialog.load_service()
            if not timesketch_service:
                reply = QMessageBox.question(
                    self,
                    "Timesketch Not Configured",
                    "Timesketch is not configured. Would you like to configure it now?\n\n"
                    "You can configure it in Settings Console (File → Settings Console...).",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if reply == QMessageBox.StandardButton.Yes:
                    config_dialog = TimesketchConfigDialog(self)
                    if config_dialog.exec() == QDialog.DialogCode.Accepted:
                        timesketch_service = TimesketchConfigDialog.load_service()
                    else:
                        return
                else:
                    return
        except Exception as e:
            logger.error(f"Failed to load Timesketch service: {e}")
            QMessageBox.critical(self, "Error", f"Failed to load Timesketch service: {e}")
            return
        
        if not timesketch_service:
            QMessageBox.warning(
                self, 
                "Configuration Error", 
                "Timesketch service not available.\n\n"
                "Please configure Timesketch in Settings Console (File → Settings Console...)."
            )
            return
        
        # Get related findings
        finding_ids = case.get('finding_ids', [])
        findings = []
        for finding_id in finding_ids:
            finding = self.data_service.get_finding(finding_id)
            if finding:
                findings.append(finding)
        
        # Sync to Timesketch
        sketch_manager = SketchManager()
        timeline_service = TimelineService()
        
        success = sketch_manager.sync_case_to_sketch(
            case['case_id'],
            case,
            findings,
            timesketch_service,
            timeline_service
        )
        
        if success:
            mapping = sketch_manager.get_sketch_for_case(case['case_id'])
            sketch_id = mapping.get('sketch_id') if mapping else 'Unknown'
            
            QMessageBox.information(
                self,
                "Success",
                f"Case exported to Timesketch successfully!\n\n"
                f"Sketch ID: {sketch_id}\n"
                f"Events: {len(findings)}\n\n"
                f"You can view it in Timesketch or use 'View Timeline' to see it here."
            )
            self.refresh()
        else:
            QMessageBox.critical(
                self,
                "Error",
                "Failed to export case to Timesketch. Please check the logs for details."
            )
    
    def _view_timeline(self):
        """View timeline for selected case."""
        case = self._get_selected_case()
        if not case:
            QMessageBox.information(self, "No Selection", "Please select a case first.")
            return
        
        # Check if case has a Timesketch sketch
        sketch_manager = SketchManager()
        mapping = sketch_manager.get_sketch_for_case(case['case_id'])
        
        if not mapping:
            reply = QMessageBox.question(
                self,
                "No Timesketch Sketch",
                "This case has not been exported to Timesketch yet.\n\n"
                "Would you like to export it now?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                self._export_to_timesketch()
                mapping = sketch_manager.get_sketch_for_case(case['case_id'])
            else:
                return
        
        # Open timeline visualizer
        from ui.widgets.timesketch_timeline import TimesketchTimelineWidget
        
        timeline_widget = TimesketchTimelineWidget(case, mapping, self)
        timeline_widget.exec()
    
    def _show_correlation(self):
        """Show correlation analysis for selected case."""
        case = self._get_selected_case()
        if not case:
            QMessageBox.information(self, "No Selection", "Please select a case first.")
            return
        
        from ui.widgets.correlation_widget import CorrelationWidget
        correlation_widget = CorrelationWidget(case['case_id'], self)
        correlation_widget.show()
    
    def _show_analyzers(self):
        """Show analyzer widget for selected case."""
        case = self._get_selected_case()
        if not case:
            QMessageBox.information(self, "No Selection", "Please select a case first.")
            return
        
        from ui.widgets.analyzer_widget import AnalyzerWidget
        analyzer_widget = AnalyzerWidget(case['case_id'], self)
        analyzer_widget.show()
    
    def _show_collaboration(self):
        """Show collaboration widget for selected case."""
        case = self._get_selected_case()
        if not case:
            QMessageBox.information(self, "No Selection", "Please select a case first.")
            return
        
        from ui.widgets.collaboration_widget import CollaborationWidget
        collaboration_widget = CollaborationWidget(case['case_id'], self)
        collaboration_widget.show()

