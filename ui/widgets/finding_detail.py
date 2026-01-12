"""Finding detail view widget."""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, QPushButton,
    QGroupBox, QFormLayout, QTableWidget, QTableWidgetItem
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QPalette
import json


class FindingDetailWidget(QDialog):
    """Dialog for viewing finding details."""
    
    # Material Design severity colors
    SEVERITY_COLORS = {
        'critical': QColor('#D32F2F'),  # Red
        'high': QColor('#F57C00'),      # Orange
        'medium': QColor('#FBC02D'),    # Yellow
        'low': QColor('#388E3C')        # Green
    }
    
    def __init__(self, finding: dict, parent=None):
        super().__init__(parent)
        self.finding = finding
        self.setWindowTitle(f"Finding Details: {finding.get('finding_id', 'Unknown')}")
        self.setMinimumSize(700, 600)
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the UI."""
        layout = QVBoxLayout()
        
        # Basic info
        basic_group = QGroupBox("Basic Information")
        basic_layout = QFormLayout()
        
        basic_layout.addRow("Finding ID:", QLabel(self.finding.get('finding_id', 'N/A')))
        basic_layout.addRow("Timestamp:", QLabel(self.finding.get('timestamp', 'N/A')))
        
        # Severity with color coding
        severity = self.finding.get('severity', 'N/A').lower()
        severity_label = QLabel(severity.capitalize())
        if severity in self.SEVERITY_COLORS:
            # Use inline style for stronger color application
            color = self.SEVERITY_COLORS[severity]
            severity_label.setStyleSheet(f"color: rgb({color.red()}, {color.green()}, {color.blue()}); font-weight: bold;")
        basic_layout.addRow("Severity:", severity_label)
        
        basic_layout.addRow("Data Source:", QLabel(self.finding.get('data_source', 'N/A')))
        basic_layout.addRow("Status:", QLabel(self.finding.get('status', 'N/A')))
        basic_layout.addRow("Anomaly Score:", QLabel(f"{self.finding.get('anomaly_score', 0):.4f}"))
        basic_layout.addRow("Cluster ID:", QLabel(self.finding.get('cluster_id', 'None')))
        
        basic_group.setLayout(basic_layout)
        layout.addWidget(basic_group)
        
        # Entity context
        entity_group = QGroupBox("Entity Context")
        entity_layout = QFormLayout()
        
        entity_context = self.finding.get('entity_context', {})
        for key, value in entity_context.items():
            entity_layout.addRow(f"{key}:", QLabel(str(value)))
        
        entity_group.setLayout(entity_layout)
        layout.addWidget(entity_group)
        
        # MITRE predictions
        mitre_group = QGroupBox("MITRE ATT&CK Predictions")
        mitre_layout = QVBoxLayout()
        
        mitre_table = QTableWidget()
        mitre_table.setColumnCount(2)
        mitre_table.setHorizontalHeaderLabels(["Technique", "Confidence"])
        # Make resizable
        from PyQt6.QtWidgets import QHeaderView
        mitre_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        mitre_table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        mitre_table.verticalHeader().setVisible(True)
        mitre_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
        predictions = self.finding.get('mitre_predictions', {})
        mitre_table.setRowCount(len(predictions))
        
        for row, (technique, confidence) in enumerate(sorted(
            predictions.items(), key=lambda x: x[1], reverse=True
        )):
            mitre_table.setItem(row, 0, QTableWidgetItem(technique))
            mitre_table.setItem(row, 1, QTableWidgetItem(f"{confidence:.3f}"))
        
        mitre_table.resizeColumnsToContents()
        mitre_layout.addWidget(mitre_table)
        mitre_group.setLayout(mitre_layout)
        layout.addWidget(mitre_group)
        
        # Evidence links
        evidence_group = QGroupBox("Evidence Links")
        evidence_layout = QVBoxLayout()
        
        evidence_text = QTextEdit()
        evidence_text.setReadOnly(True)
        evidence_text.setMaximumHeight(100)
        
        evidence_links = self.finding.get('evidence_links', [])
        if evidence_links:
            evidence_text.setPlainText(json.dumps(evidence_links, indent=2))
        else:
            evidence_text.setPlainText("No evidence links available.")
        
        evidence_layout.addWidget(evidence_text)
        evidence_group.setLayout(evidence_layout)
        layout.addWidget(evidence_group)
        
        # Raw JSON view
        raw_group = QGroupBox("Raw JSON")
        raw_layout = QVBoxLayout()
        
        raw_text = QTextEdit()
        raw_text.setReadOnly(True)
        raw_text.setMaximumHeight(150)
        
        # Remove embedding for display (too large)
        finding_copy = self.finding.copy()
        if 'embedding' in finding_copy:
            finding_copy['embedding'] = f"[{len(finding_copy['embedding'])}-dimensional vector]"
        
        raw_text.setPlainText(json.dumps(finding_copy, indent=2))
        raw_layout.addWidget(raw_text)
        raw_group.setLayout(raw_layout)
        layout.addWidget(raw_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)

