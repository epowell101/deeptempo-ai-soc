"""Finding list widget with filtering and search."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLineEdit, QComboBox, QLabel, QHeaderView, QMessageBox,
    QDialog, QFormLayout, QTextEdit
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor
import numpy as np

from services.data_service import DataService
from ui.widgets.finding_detail import FindingDetailWidget
from ui.utils.auto_resize import TableAutoResize, ButtonSizePolicy


class FindingListWidget(QWidget):
    """Widget for displaying and filtering findings."""
    
    finding_selected = pyqtSignal(dict)
    analyze_with_agent = pyqtSignal(dict)  # Signal to analyze finding (creates new tab in Claude Chat)
    
    # Material Design severity colors
    SEVERITY_COLORS = {
        'critical': QColor('#D32F2F'),  # Red
        'high': QColor('#F57C00'),      # Orange
        'medium': QColor('#FBC02D'),    # Yellow
        'low': QColor('#388E3C')        # Green
    }
    
    # Default text color for non-severity columns
    DEFAULT_TEXT_COLOR = QColor('#E0E0E0')  # on_surface color from theme
    
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
        self.table.setColumnCount(8)  # Added one column for Analyze button
        self.table.setHorizontalHeaderLabels([
            "ID", "Timestamp", "Severity", "Data Source", "Anomaly Score",
            "Cluster", "MITRE Techniques", "Actions"
        ])
        
        # Configure intelligent auto-resizing for columns
        TableAutoResize.configure(
            self.table,
            content_fit_columns=[0, 2, 3, 7],  # ID, Severity, Data Source, Actions (auto-fit)
            stretch_columns=[6],  # MITRE Techniques (stretches to fill remaining space)
            interactive_columns=[1, 4, 5]  # Timestamp, Anomaly Score, Cluster (user can resize)
        )
        
        # Make rows resizable by user (like Excel)
        self.table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.table.verticalHeader().setVisible(True)
        self.table.verticalHeader().setDefaultSectionSize(30)  # Default row height
        
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.itemDoubleClicked.connect(self._on_item_double_clicked)
        self.table.itemSelectionChanged.connect(self._on_selection_changed)
        
        # Make table expand to fill available space (relative sizing)
        layout.addWidget(self.table, 1)  # Stretch factor of 1
        
        # Action buttons with responsive sizing
        button_layout = QHBoxLayout()
        
        view_btn = QPushButton("View Details")
        ButtonSizePolicy.make_flexible(view_btn, min_width=100)
        view_btn.clicked.connect(self._view_details)
        button_layout.addWidget(view_btn)
        
        neighbors_btn = QPushButton("Find Similar")
        ButtonSizePolicy.make_flexible(neighbors_btn, min_width=100)
        neighbors_btn.clicked.connect(self._find_similar)
        button_layout.addWidget(neighbors_btn)
        
        button_layout.addStretch()
        
        refresh_btn = QPushButton("Refresh")
        ButtonSizePolicy.make_compact(refresh_btn, min_width=80)
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
            id_item = QTableWidgetItem(finding.get('finding_id', ''))
            id_item.setForeground(self.DEFAULT_TEXT_COLOR)
            self.table.setItem(row, 0, id_item)
            
            # Timestamp
            timestamp = finding.get('timestamp', '')
            if timestamp:
                timestamp = timestamp.split('T')[0]  # Just date
            timestamp_item = QTableWidgetItem(timestamp)
            timestamp_item.setForeground(self.DEFAULT_TEXT_COLOR)
            self.table.setItem(row, 1, timestamp_item)
            
            # Severity
            severity = finding.get('severity', 'unknown').lower()
            severity_item = QTableWidgetItem(severity.capitalize())
            # Color code severity with Material Design colors
            if severity in self.SEVERITY_COLORS:
                # Pass QColor directly, not QBrush (matches working pattern in other widgets)
                severity_item.setForeground(self.SEVERITY_COLORS[severity])
            else:
                severity_item.setForeground(self.DEFAULT_TEXT_COLOR)
            self.table.setItem(row, 2, severity_item)
            
            # Data source
            datasource_item = QTableWidgetItem(finding.get('data_source', ''))
            datasource_item.setForeground(self.DEFAULT_TEXT_COLOR)
            self.table.setItem(row, 3, datasource_item)
            
            # Anomaly score
            score = finding.get('anomaly_score', 0)
            score_item = QTableWidgetItem(f"{score:.3f}")
            score_item.setForeground(self.DEFAULT_TEXT_COLOR)
            self.table.setItem(row, 4, score_item)
            
            # Cluster
            cluster = finding.get('cluster_id', '')
            cluster_item = QTableWidgetItem(cluster if cluster else 'None')
            cluster_item.setForeground(self.DEFAULT_TEXT_COLOR)
            self.table.setItem(row, 5, cluster_item)
            
            # MITRE techniques
            techniques = finding.get('mitre_predictions', {})
            tech_str = ', '.join(list(techniques.keys())[:3])
            if len(techniques) > 3:
                tech_str += f" (+{len(techniques) - 3} more)"
            tech_item = QTableWidgetItem(tech_str)
            tech_item.setForeground(self.DEFAULT_TEXT_COLOR)
            self.table.setItem(row, 6, tech_item)
            
            # Analyze button - creates new tab in Claude Chat drawer
            analyze_btn = QPushButton("Analyze")
            analyze_btn.setToolTip("Analyze this finding in a new chat tab")
            ButtonSizePolicy.make_compact(analyze_btn, min_width=70, max_height=24)
            analyze_btn.setStyleSheet("background-color: #2196F3; color: white; padding: 4px;")
            analyze_btn.clicked.connect(lambda checked, f=finding: self._analyze_finding(f))
            self.table.setCellWidget(row, 7, analyze_btn)
        
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
    
    def _analyze_finding(self, finding):
        """Emit signal to analyze finding (creates new tab in Claude Chat drawer)."""
        self.analyze_with_agent.emit(finding)
    
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
        
        # Configure intelligent auto-resizing
        TableAutoResize.configure(
            table,
            content_fit_columns=[0, 1, 2, 3],  # Finding ID, Similarity, Severity, Data Source
            stretch_columns=[4]  # Cluster stretches to fill
        )
        table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        table.verticalHeader().setVisible(True)
        
        table.setRowCount(min(10, len(similarities)))
        
        for row, (other, sim) in enumerate(similarities[:10]):
            id_item = QTableWidgetItem(other.get('finding_id', ''))
            id_item.setForeground(self.DEFAULT_TEXT_COLOR)
            table.setItem(row, 0, id_item)
            
            sim_item = QTableWidgetItem(f"{sim:.4f}")
            sim_item.setForeground(self.DEFAULT_TEXT_COLOR)
            table.setItem(row, 1, sim_item)
            
            # Severity with color coding
            severity = other.get('severity', 'unknown').lower()
            severity_item = QTableWidgetItem(severity.capitalize())
            if severity in self.SEVERITY_COLORS:
                severity_item.setForeground(self.SEVERITY_COLORS[severity])
            else:
                severity_item.setForeground(self.DEFAULT_TEXT_COLOR)
            table.setItem(row, 2, severity_item)
            
            ds_item = QTableWidgetItem(other.get('data_source', ''))
            ds_item.setForeground(self.DEFAULT_TEXT_COLOR)
            table.setItem(row, 3, ds_item)
            
            cluster_item = QTableWidgetItem(other.get('cluster_id', '') or 'None')
            cluster_item.setForeground(self.DEFAULT_TEXT_COLOR)
            table.setItem(row, 4, cluster_item)
        
        layout.addWidget(table)
        
        close_btn = QPushButton("Close")
        ButtonSizePolicy.make_compact(close_btn, min_width=80)
        close_btn.clicked.connect(dialog.close)
        layout.addWidget(close_btn)
        
        dialog.setLayout(layout)
        dialog.exec()

