"""Investigation Workflow Widget - Track investigation status."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QTableWidget,
    QTableWidgetItem, QComboBox, QTextEdit, QMessageBox, QGroupBox, QProgressBar
)
from PyQt6.QtCore import Qt
from datetime import datetime
from pathlib import Path
import json
from typing import Dict, List

from services.data_service import DataService


class WorkflowWidget(QWidget):
    """Widget for tracking investigation workflow."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.data_service = DataService()
        self.workflow_file = self.data_service.data_dir / "workflow_status.json"
        
        self._setup_ui()
        self.refresh()
    
    def _setup_ui(self):
        """Set up the UI."""
        layout = QVBoxLayout()
        
        # Header
        header = QLabel("<h2>Investigation Workflow</h2>")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(header)
        
        # Summary metrics
        metrics_group = QGroupBox("Summary")
        metrics_layout = QHBoxLayout()
        
        self.total_label = QLabel("Total: 0")
        metrics_layout.addWidget(self.total_label)
        
        self.new_label = QLabel("New: 0")
        metrics_layout.addWidget(self.new_label)
        
        self.in_progress_label = QLabel("In Progress: 0")
        metrics_layout.addWidget(self.in_progress_label)
        
        self.resolved_label = QLabel("Resolved: 0")
        metrics_layout.addWidget(self.resolved_label)
        
        metrics_layout.addStretch()
        
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.refresh)
        metrics_layout.addWidget(refresh_btn)
        
        metrics_group.setLayout(metrics_layout)
        layout.addWidget(metrics_group)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(100)
        layout.addWidget(self.progress_bar)
        
        # Filter
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Filter:"))
        
        self.status_filter = QComboBox()
        self.status_filter.addItems(["All", "New", "In Progress", "Resolved"])
        self.status_filter.currentTextChanged.connect(self._filter_findings)
        filter_layout.addWidget(self.status_filter)
        
        filter_layout.addStretch()
        layout.addLayout(filter_layout)
        
        # Findings table
        self.findings_table = QTableWidget()
        self.findings_table.setColumnCount(6)
        self.findings_table.setHorizontalHeaderLabels([
            "Status", "ID", "Title", "Severity", "Timestamp", "Actions"
        ])
        self.findings_table.horizontalHeader().setStretchLastSection(True)
        self.findings_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.findings_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        # Make table expand to fill available space (relative sizing)
        layout.addWidget(self.findings_table, 2)  # Stretch factor of 2 (takes more space than detail)
        
        # Detail view
        detail_group = QGroupBox("Finding Details & Update")
        detail_layout = QVBoxLayout()
        
        self.detail_text = QTextEdit()
        self.detail_text.setReadOnly(True)
        # Use relative sizing instead of fixed height
        detail_layout.addWidget(self.detail_text, 1)  # Stretch factor
        
        # Update controls
        update_layout = QHBoxLayout()
        update_layout.addWidget(QLabel("Status:"))
        
        self.status_combo = QComboBox()
        self.status_combo.addItems(["new", "in_progress", "resolved"])
        update_layout.addWidget(self.status_combo)
        
        update_layout.addWidget(QLabel("Verdict:"))
        
        self.verdict_combo = QComboBox()
        self.verdict_combo.addItems(["", "true_positive", "false_positive", "needs_review"])
        update_layout.addWidget(self.verdict_combo)
        
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self._save_status)
        update_layout.addWidget(save_btn)
        
        update_layout.addStretch()
        detail_layout.addLayout(update_layout)
        
        detail_group.setLayout(detail_layout)
        layout.addWidget(detail_group)
        
        self.setLayout(layout)
        
        self.findings = []
        self.workflow_status = {}
        self.selected_finding_id = None
    
    def _load_workflow_status(self) -> Dict:
        """Load workflow status from file."""
        if not self.workflow_file.exists():
            return {}
        
        try:
            with open(self.workflow_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to load workflow status: {e}")
            return {}
    
    def _save_workflow_status(self):
        """Save workflow status to file."""
        try:
            self.workflow_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.workflow_file, 'w') as f:
                json.dump(self.workflow_status, f, indent=2)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save workflow status: {e}")
    
    def _filter_findings(self):
        """Filter findings by status."""
        filter_status = self.status_filter.currentText().lower()
        
        filtered = []
        for finding in self.findings:
            finding_id = finding.get("finding_id", "")
            status = self.workflow_status.get(finding_id, {}).get("status", "new")
            
            if filter_status == "all":
                filtered.append(finding)
            elif filter_status == "new" and status == "new":
                filtered.append(finding)
            elif filter_status == "in progress" and status == "in_progress":
                filtered.append(finding)
            elif filter_status == "resolved" and status == "resolved":
                filtered.append(finding)
        
        self._populate_table(filtered)
    
    def _populate_table(self, findings: List[Dict]):
        """Populate the findings table."""
        self.findings_table.setRowCount(len(findings))
        
        for row, finding in enumerate(findings):
            finding_id = finding.get("finding_id", "")
            status = self.workflow_status.get(finding_id, {}).get("status", "new")
            
            # Status
            status_item = QTableWidgetItem(status.replace("_", " ").title())
            if status == "resolved":
                status_item.setForeground(Qt.GlobalColor.green)
            elif status == "in_progress":
                status_item.setForeground(Qt.GlobalColor.darkYellow)
            else:
                status_item.setForeground(Qt.GlobalColor.blue)
            self.findings_table.setItem(row, 0, status_item)
            
            # ID
            self.findings_table.setItem(row, 1, QTableWidgetItem(finding_id[:20] + "..."))
            
            # Title
            title = finding.get("title", "Unknown")[:50]
            self.findings_table.setItem(row, 2, QTableWidgetItem(title))
            
            # Severity
            severity = finding.get("severity", "medium")
            severity_item = QTableWidgetItem(severity.upper())
            if severity == "critical":
                severity_item.setForeground(Qt.GlobalColor.red)
            elif severity == "high":
                severity_item.setForeground(Qt.GlobalColor.darkRed)
            elif severity == "medium":
                severity_item.setForeground(Qt.GlobalColor.darkYellow)
            self.findings_table.setItem(row, 3, severity_item)
            
            # Timestamp
            timestamp = finding.get("timestamp", "")[:16] if finding.get("timestamp") else "N/A"
            self.findings_table.setItem(row, 4, QTableWidgetItem(timestamp))
            
            # Actions button
            view_btn = QPushButton("View")
            view_btn.clicked.connect(lambda checked, fid=finding_id: self._view_finding(fid))
            self.findings_table.setCellWidget(row, 5, view_btn)
        
        self.findings_table.resizeColumnsToContents()
    
    def _view_finding(self, finding_id: str):
        """View and select a finding."""
        self.selected_finding_id = finding_id
        
        finding = None
        for f in self.findings:
            if f.get("finding_id") == finding_id:
                finding = f
                break
        
        if not finding:
            return
        
        # Update detail view
        detail_html = f"""
<b>Finding ID:</b> {finding.get('finding_id', 'N/A')}<br>
<b>Title:</b> {finding.get('title', 'N/A')}<br>
<b>Severity:</b> {finding.get('severity', 'N/A').upper()}<br>
<b>Timestamp:</b> {finding.get('timestamp', 'N/A')}<br>
<b>Description:</b> {finding.get('description', 'N/A')[:200]}...<br>
        """
        
        self.detail_text.setHtml(detail_html)
        
        # Update status combo
        status = self.workflow_status.get(finding_id, {}).get("status", "new")
        index = self.status_combo.findText(status)
        if index >= 0:
            self.status_combo.setCurrentIndex(index)
        
        # Update verdict combo
        verdict = self.workflow_status.get(finding_id, {}).get("verdict", "")
        index = self.verdict_combo.findText(verdict)
        if index >= 0:
            self.verdict_combo.setCurrentIndex(index)
        else:
            self.verdict_combo.setCurrentIndex(0)
    
    def _save_status(self):
        """Save workflow status for selected finding."""
        if not self.selected_finding_id:
            QMessageBox.warning(self, "No Selection", "Please select a finding first.")
            return
        
        status = self.status_combo.currentText()
        verdict = self.verdict_combo.currentText()
        
        self.workflow_status[self.selected_finding_id] = {
            "status": status,
            "verdict": verdict,
            "updated_at": datetime.now().isoformat()
        }
        
        self._save_workflow_status()
        self.refresh()
        
        QMessageBox.information(self, "Saved", "Workflow status updated successfully.")
    
    def refresh(self):
        """Refresh workflow data."""
        self.findings = self.data_service.get_findings()
        self.workflow_status = self._load_workflow_status()
        
        # Calculate metrics
        total = len(self.findings)
        reviewed = len([f for f in self.findings 
                       if self.workflow_status.get(f.get("finding_id", ""), {}).get("status") == "resolved"])
        in_progress = len([f for f in self.findings 
                          if self.workflow_status.get(f.get("finding_id", ""), {}).get("status") == "in_progress"])
        new_count = total - reviewed - in_progress
        
        self.total_label.setText(f"Total: {total}")
        self.new_label.setText(f"New: {new_count}")
        self.in_progress_label.setText(f"In Progress: {in_progress}")
        self.resolved_label.setText(f"Resolved: {reviewed}")
        
        # Progress bar
        progress = (reviewed / total * 100) if total > 0 else 0
        self.progress_bar.setValue(int(progress))
        self.progress_bar.setFormat(f"Triage Progress: {progress:.0f}%")
        
        # Filter and display
        self._filter_findings()

