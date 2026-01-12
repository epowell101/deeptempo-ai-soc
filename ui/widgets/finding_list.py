"""Finding list widget with filtering and search."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLineEdit, QComboBox, QLabel, QHeaderView, QMessageBox,
    QDialog, QFormLayout, QTextEdit
)
from PyQt6.QtCore import Qt, pyqtSignal
import numpy as np

from services.data_service import DataService
from ui.widgets.finding_detail import FindingDetailWidget


class FindingListWidget(QWidget):
    """Widget for displaying and filtering findings."""
    
    finding_selected = pyqtSignal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.data_service = DataService()
        self.findings = []
        self.filtered_findings = []
        
        self._setup_ui()
        self.refresh()
    
    def _setup_ui(self):
        """Set up the UI."""
        layout = QVBoxLayout()
        
        # Filter controls
        filter_layout = QHBoxLayout()
        
        # Search
        filter_layout.addWidget(QLabel("Search:"))
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search by ID, IP, hostname...")
        self.search_edit.textChanged.connect(self._apply_filters)
        filter_layout.addWidget(self.search_edit)
        
        # Severity filter
        filter_layout.addWidget(QLabel("Severity:"))
        self.severity_combo = QComboBox()
        self.severity_combo.addItems(["All", "Critical", "High", "Medium", "Low"])
        self.severity_combo.currentTextChanged.connect(self._apply_filters)
        filter_layout.addWidget(self.severity_combo)
        
        # Data source filter
        filter_layout.addWidget(QLabel("Data Source:"))
        self.source_combo = QComboBox()
        self.source_combo.addItems(["All", "flow", "dns", "waf"])
        self.source_combo.currentTextChanged.connect(self._apply_filters)
        filter_layout.addWidget(self.source_combo)
        
        filter_layout.addStretch()
        
        layout.addLayout(filter_layout)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "ID", "Timestamp", "Severity", "Data Source", "Anomaly Score",
            "Cluster", "MITRE Techniques"
        ])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.itemDoubleClicked.connect(self._on_item_double_clicked)
        self.table.itemSelectionChanged.connect(self._on_selection_changed)
        
        # Make table expand to fill available space (relative sizing)
        layout.addWidget(self.table, 1)  # Stretch factor of 1
        
        # Action buttons
        button_layout = QHBoxLayout()
        
        view_btn = QPushButton("View Details")
        view_btn.clicked.connect(self._view_details)
        button_layout.addWidget(view_btn)
        
        neighbors_btn = QPushButton("Find Similar")
        neighbors_btn.clicked.connect(self._find_similar)
        button_layout.addWidget(neighbors_btn)
        
        button_layout.addStretch()
        
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.refresh)
        button_layout.addWidget(refresh_btn)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def refresh(self):
        """Refresh findings from data service."""
        self.findings = self.data_service.get_findings(force_refresh=True)
        self._apply_filters()
    
    def _apply_filters(self):
        """Apply filters to findings."""
        search_text = self.search_edit.text().lower()
        severity_filter = self.severity_combo.currentText().lower()
        source_filter = self.source_combo.currentText().lower()
        
        self.filtered_findings = []
        
        for finding in self.findings:
            # Severity filter
            if severity_filter != "all":
                if finding.get('severity', '').lower() != severity_filter:
                    continue
            
            # Source filter
            if source_filter != "all":
                if finding.get('data_source', '').lower() != source_filter:
                    continue
            
            # Search filter
            if search_text:
                searchable = [
                    finding.get('finding_id', ''),
                    finding.get('entity_context', {}).get('src_ip', ''),
                    finding.get('entity_context', {}).get('dst_ip', ''),
                    finding.get('entity_context', {}).get('hostname', ''),
                ]
                if not any(search_text in str(s).lower() for s in searchable):
                    continue
            
            self.filtered_findings.append(finding)
        
        self._populate_table()
    
    def _populate_table(self):
        """Populate the table with filtered findings."""
        self.table.setRowCount(len(self.filtered_findings))
        
        for row, finding in enumerate(self.filtered_findings):
            # ID
            self.table.setItem(row, 0, QTableWidgetItem(finding.get('finding_id', '')))
            
            # Timestamp
            timestamp = finding.get('timestamp', '')
            if timestamp:
                timestamp = timestamp.split('T')[0]  # Just date
            self.table.setItem(row, 1, QTableWidgetItem(timestamp))
            
            # Severity
            severity = finding.get('severity', 'unknown')
            severity_item = QTableWidgetItem(severity)
            # Color code severity
            if severity == 'critical':
                severity_item.setForeground(Qt.GlobalColor.red)
            elif severity == 'high':
                severity_item.setForeground(Qt.GlobalColor.darkRed)
            elif severity == 'medium':
                severity_item.setForeground(Qt.GlobalColor.yellow)
            self.table.setItem(row, 2, severity_item)
            
            # Data source
            self.table.setItem(row, 3, QTableWidgetItem(finding.get('data_source', '')))
            
            # Anomaly score
            score = finding.get('anomaly_score', 0)
            self.table.setItem(row, 4, QTableWidgetItem(f"{score:.3f}"))
            
            # Cluster
            cluster = finding.get('cluster_id', '')
            self.table.setItem(row, 5, QTableWidgetItem(cluster if cluster else 'None'))
            
            # MITRE techniques
            techniques = finding.get('mitre_predictions', {})
            tech_str = ', '.join(list(techniques.keys())[:3])
            if len(techniques) > 3:
                tech_str += f" (+{len(techniques) - 3} more)"
            self.table.setItem(row, 6, QTableWidgetItem(tech_str))
        
        self.table.resizeColumnsToContents()
    
    def _on_item_double_clicked(self, item):
        """Handle double-click on table item."""
        self._view_details()
    
    def _on_selection_changed(self):
        """Handle selection change."""
        pass
    
    def _get_selected_finding(self):
        """Get the currently selected finding."""
        row = self.table.currentRow()
        if row >= 0 and row < len(self.filtered_findings):
            return self.filtered_findings[row]
        return None
    
    def _view_details(self):
        """View details of selected finding."""
        finding = self._get_selected_finding()
        if not finding:
            QMessageBox.information(self, "No Selection", "Please select a finding first.")
            return
        
        detail_widget = FindingDetailWidget(finding, self)
        detail_widget.exec()
    
    def _find_similar(self):
        """Find similar findings."""
        finding = self._get_selected_finding()
        if not finding:
            QMessageBox.information(self, "No Selection", "Please select a finding first.")
            return
        
        if 'embedding' not in finding:
            QMessageBox.warning(self, "No Embedding", "Selected finding has no embedding data.")
            return
        
        # Calculate similarities
        similarities = []
        finding_embedding = np.array(finding['embedding'])
        
        for other in self.findings:
            if other['finding_id'] == finding['finding_id']:
                continue
            
            if 'embedding' not in other:
                continue
            
            other_embedding = np.array(other['embedding'])
            similarity = float(np.dot(finding_embedding, other_embedding) / 
                             (np.linalg.norm(finding_embedding) * np.linalg.norm(other_embedding)))
            
            similarities.append((other, similarity))
        
        # Sort by similarity
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        # Show dialog with results
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Similar Findings to {finding['finding_id']}")
        dialog.setMinimumSize(600, 400)
        
        layout = QVBoxLayout()
        
        table = QTableWidget()
        table.setColumnCount(5)
        table.setHorizontalHeaderLabels([
            "Finding ID", "Similarity", "Severity", "Data Source", "Cluster"
        ])
        table.setRowCount(min(10, len(similarities)))
        
        for row, (other, sim) in enumerate(similarities[:10]):
            table.setItem(row, 0, QTableWidgetItem(other.get('finding_id', '')))
            table.setItem(row, 1, QTableWidgetItem(f"{sim:.4f}"))
            table.setItem(row, 2, QTableWidgetItem(other.get('severity', '')))
            table.setItem(row, 3, QTableWidgetItem(other.get('data_source', '')))
            table.setItem(row, 4, QTableWidgetItem(other.get('cluster_id', '') or 'None'))
        
        table.resizeColumnsToContents()
        layout.addWidget(table)
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.close)
        layout.addWidget(close_btn)
        
        dialog.setLayout(layout)
        dialog.exec()

