"""Enhanced search widget for Timesketch integration."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit,
    QTableWidget, QTableWidgetItem, QTextEdit, QComboBox, QMessageBox,
    QGroupBox, QListWidget, QListWidgetItem, QCheckBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from typing import Optional
import logging

from services.timesketch_service import TimesketchService
from services.sketch_manager import SketchManager
from services.data_service import DataService
from ui.timesketch_config import TimesketchConfigDialog
from ui.utils.auto_resize import TableAutoResize, ButtonSizePolicy

logger = logging.getLogger(__name__)


class SearchWidget(QWidget):
    """Enhanced search widget with Timesketch integration."""
    
    # Material Design severity colors
    SEVERITY_COLORS = {
        'critical': QColor('#D32F2F'),  # Red
        'high': QColor('#F57C00'),      # Orange
        'medium': QColor('#FBC02D'),    # Yellow
        'low': QColor('#388E3C')        # Green
    }
    
    # Predefined search queries
    PREDEFINED_QUERIES = [
        ("High Severity Findings", 'data_type:"security:finding" AND severity:"high"'),
        ("Critical Findings", 'data_type:"security:finding" AND severity:"critical"'),
        ("MITRE Technique T1071", 'mitre_techniques:"T1071.001"'),
        ("C2 Communication", 'message:"C2" OR message:"beacon"'),
        ("Lateral Movement", 'mitre_techniques:"T1021" OR mitre_techniques:"T1105"'),
        ("Data Exfiltration", 'mitre_techniques:"T1041" OR mitre_techniques:"T1048"'),
        ("Recent Events", 'timestamp:[NOW-7d TO NOW]'),
        ("Specific IP", 'entity_src_ip:"10.0.1.15" OR entity_dst_ip:"10.0.1.15"'),
    ]
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.timesketch_service: Optional[TimesketchService] = None
        self.sketch_manager = SketchManager()
        self.data_service = DataService()
        
        self.saved_queries = []
        
        self._setup_ui()
        self._load_service()
    
    def _setup_ui(self):
        """Set up the UI."""
        layout = QVBoxLayout()
        
        # Header
        header_label = QLabel(
            "<h3>Enhanced Search</h3>"
            "<p>Search across Timesketch sketches using powerful query syntax.</p>"
        )
        header_label.setWordWrap(True)
        layout.addWidget(header_label)
        
        # Search input
        search_group = QGroupBox("Search Query")
        search_layout = QVBoxLayout()
        
        # Query builder
        query_layout = QHBoxLayout()
        query_layout.addWidget(QLabel("Query:"))
        
        self.query_edit = QLineEdit()
        self.query_edit.setPlaceholderText('e.g., data_type:"security:finding" AND severity:"high"')
        self.query_edit.returnPressed.connect(self._execute_search)
        query_layout.addWidget(self.query_edit)
        
        search_btn = QPushButton("Search")
        ButtonSizePolicy.make_compact(search_btn, min_width=80)
        search_btn.clicked.connect(self._execute_search)
        query_layout.addWidget(search_btn)
        
        search_layout.addLayout(query_layout)
        
        # Predefined queries
        predefined_layout = QHBoxLayout()
        predefined_layout.addWidget(QLabel("Quick Searches:"))
        
        self.predefined_combo = QComboBox()
        self.predefined_combo.addItem("Select a predefined query...", None)
        for name, query in self.PREDEFINED_QUERIES:
            self.predefined_combo.addItem(name, query)
        self.predefined_combo.currentIndexChanged.connect(self._on_predefined_selected)
        predefined_layout.addWidget(self.predefined_combo)
        
        search_layout.addLayout(predefined_layout)
        
        # Search options
        options_layout = QHBoxLayout()
        
        self.sketch_combo = QComboBox()
        self.sketch_combo.addItem("All Sketches", None)
        self._load_sketches()
        options_layout.addWidget(QLabel("Sketch:"))
        options_layout.addWidget(self.sketch_combo)
        
        self.limit_spin = QComboBox()
        self.limit_spin.addItems(["10", "50", "100", "500", "1000"])
        self.limit_spin.setCurrentText("100")
        options_layout.addWidget(QLabel("Limit:"))
        options_layout.addWidget(self.limit_spin)
        
        options_layout.addStretch()
        search_layout.addLayout(options_layout)
        
        search_group.setLayout(search_layout)
        layout.addWidget(search_group)
        
        # Results
        results_group = QGroupBox("Search Results")
        results_layout = QVBoxLayout()
        
        results_toolbar = QHBoxLayout()
        results_toolbar.addWidget(QLabel(f"Results: 0"))
        self.results_count_label = results_toolbar.itemAt(0).widget()
        
        export_btn = QPushButton("Export Results")
        ButtonSizePolicy.make_compact(export_btn, min_width=110)
        export_btn.clicked.connect(self._export_results)
        results_toolbar.addWidget(export_btn)
        
        save_query_btn = QPushButton("Save Query")
        ButtonSizePolicy.make_compact(save_query_btn, min_width=90)
        save_query_btn.clicked.connect(self._save_query)
        results_toolbar.addWidget(save_query_btn)
        
        results_toolbar.addStretch()
        results_layout.addLayout(results_toolbar)
        
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(6)
        self.results_table.setHorizontalHeaderLabels([
            "Timestamp", "Message", "Source", "Severity", "Sketch", "Details"
        ])
        
        # Configure intelligent auto-resizing for columns
        from PyQt6.QtWidgets import QHeaderView
        TableAutoResize.configure(
            self.results_table,
            content_fit_columns=[2, 3, 4],  # Source, Severity, Sketch (auto-fit)
            stretch_columns=[1],  # Message (stretches to fill remaining space)
            interactive_columns=[0, 5]  # Timestamp, Details (user can resize)
        )
        self.results_table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.results_table.verticalHeader().setVisible(True)
        self.results_table.verticalHeader().setDefaultSectionSize(30)
        
        self.results_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.results_table.itemDoubleClicked.connect(self._view_event_details)
        # Make results table expand to fill available space (relative sizing)
        results_layout.addWidget(self.results_table, 2)  # Stretch factor of 2 (takes more space than details)
        
        # Event details - use relative sizing instead of fixed height
        self.event_details = QTextEdit()
        self.event_details.setReadOnly(True)
        # Use stretch factor to make it take a portion of available space
        results_layout.addWidget(self.event_details, 1)  # Stretch factor
        
        results_group.setLayout(results_layout)
        # Make results section expand to fill available space (relative sizing)
        layout.addWidget(results_group, 1)  # Stretch factor of 1
        
        # Saved queries
        saved_group = QGroupBox("Saved Queries")
        saved_layout = QVBoxLayout()
        
        self.saved_queries_list = QListWidget()
        self.saved_queries_list.itemDoubleClicked.connect(self._load_saved_query)
        saved_layout.addWidget(self.saved_queries_list)
        
        delete_query_btn = QPushButton("Delete Selected")
        ButtonSizePolicy.make_flexible(delete_query_btn, min_width=120)
        delete_query_btn.clicked.connect(self._delete_saved_query)
        saved_layout.addWidget(delete_query_btn)
        
        saved_group.setLayout(saved_layout)
        layout.addWidget(saved_group)
        
        self.setLayout(layout)
        
        # Load saved queries
        self._load_saved_queries()
    
    def _load_service(self):
        """Load Timesketch service."""
        self.timesketch_service = TimesketchConfigDialog.load_service()
        if not self.timesketch_service:
            QMessageBox.warning(
                self,
                "Timesketch Not Configured",
                "Please configure Timesketch first to use enhanced search."
            )
    
    def _load_sketches(self):
        """Load available sketches."""
        if not self.timesketch_service:
            return
        
        try:
            sketches = self.timesketch_service.list_sketches(limit=100)
            
            for sketch in sketches:
                sketch_name = sketch.get('name', f"Sketch {sketch.get('id')}")
                self.sketch_combo.addItem(sketch_name, sketch.get('id'))
        
        except Exception as e:
            logger.error(f"Error loading sketches: {e}")
    
    def _on_predefined_selected(self, index: int):
        """Handle predefined query selection."""
        query = self.predefined_combo.currentData()
        if query:
            self.query_edit.setText(query)
    
    def _execute_search(self):
        """Execute the search query."""
        if not self.timesketch_service:
            QMessageBox.warning(self, "Not Configured", "Timesketch is not configured.")
            return
        
        query = self.query_edit.text().strip()
        if not query:
            QMessageBox.warning(self, "Validation Error", "Please enter a search query.")
            return
        
        sketch_id = self.sketch_combo.currentData()
        limit = int(self.limit_spin.currentText())
        
        try:
            if sketch_id:
                # Search specific sketch
                results = self.timesketch_service.search_sketch(sketch_id, query, limit)
            else:
                # Search all sketches (iterate through them)
                all_sketches = self.timesketch_service.list_sketches(limit=100)
                results = []
                
                for sketch in all_sketches:
                    sketch_results = self.timesketch_service.search_sketch(
                        sketch.get('id'), query, limit
                    )
                    for result in sketch_results:
                        result['sketch_id'] = sketch.get('id')
                        result['sketch_name'] = sketch.get('name', 'Unknown')
                    results.extend(sketch_results)
                    
                    if len(results) >= limit:
                        results = results[:limit]
                        break
            
            self._display_results(results)
        
        except Exception as e:
            QMessageBox.critical(self, "Search Error", f"Error executing search:\n\n{e}")
    
    def _display_results(self, results: list):
        """Display search results."""
        self.results_table.setRowCount(len(results))
        self.results_count_label.setText(f"Results: {len(results)}")
        
        for row, result in enumerate(results):
            # Timestamp
            timestamp = result.get('timestamp', '')
            if 'T' in timestamp:
                timestamp = timestamp.split('T')[0] + ' ' + timestamp.split('T')[1].split('.')[0]
            self.results_table.setItem(row, 0, QTableWidgetItem(timestamp))
            
            # Message
            message = result.get('message', '')
            self.results_table.setItem(row, 1, QTableWidgetItem(message))
            
            # Source
            source = result.get('source_short', result.get('source', 'Unknown'))
            self.results_table.setItem(row, 2, QTableWidgetItem(source))
            
            # Severity with Material Design colors
            severity = result.get('severity', '').lower()
            severity_item = QTableWidgetItem(severity.capitalize() if severity else '')
            if severity in self.SEVERITY_COLORS:
                severity_item.setForeground(self.SEVERITY_COLORS[severity])
            self.results_table.setItem(row, 3, severity_item)
            
            # Sketch
            sketch_name = result.get('sketch_name', 'N/A')
            self.results_table.setItem(row, 4, QTableWidgetItem(sketch_name))
            
            # Store full result
            self.results_table.setItem(row, 5, QTableWidgetItem("Double-click for details"))
            self.results_table.item(row, 5).setData(Qt.ItemDataRole.UserRole, result)
        
        self.results_table.resizeColumnsToContents()
    
    def _view_event_details(self, item):
        """View details of selected event."""
        row = self.results_table.currentRow()
        if row < 0:
            return
        
        detail_item = self.results_table.item(row, 5)
        if not detail_item:
            return
        
        result = detail_item.data(Qt.ItemDataRole.UserRole)
        if not result:
            return
        
        # Build details text
        details = []
        for key, value in result.items():
            if value and key not in ['sketch_id', 'sketch_name']:
                details.append(f"{key}: {value}")
        
        self.event_details.setPlainText('\n'.join(details))
    
    def _save_query(self):
        """Save the current query."""
        query = self.query_edit.text().strip()
        if not query:
            QMessageBox.warning(self, "Validation Error", "No query to save.")
            return
        
        from PyQt6.QtWidgets import QInputDialog
        name, ok = QInputDialog.getText(self, "Save Query", "Query Name:")
        
        if ok and name:
            self.saved_queries.append({'name': name, 'query': query})
            self._save_queries_to_storage()
            self._load_saved_queries()
            QMessageBox.information(self, "Success", "Query saved successfully.")
    
    def _load_saved_queries(self):
        """Load saved queries."""
        # Load from storage (could be file or config)
        # For now, use in-memory list
        self.saved_queries_list.clear()
        
        for query_data in self.saved_queries:
            item = QListWidgetItem(query_data['name'])
            item.setData(Qt.ItemDataRole.UserRole, query_data['query'])
            self.saved_queries_list.addItem(item)
    
    def _load_saved_query(self, item: QListWidgetItem):
        """Load a saved query."""
        query = item.data(Qt.ItemDataRole.UserRole)
        if query:
            self.query_edit.setText(query)
    
    def _delete_saved_query(self):
        """Delete selected saved query."""
        current_item = self.saved_queries_list.currentItem()
        if not current_item:
            return
        
        reply = QMessageBox.question(
            self,
            "Delete Query",
            "Are you sure you want to delete this query?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            query_name = current_item.text()
            self.saved_queries = [q for q in self.saved_queries if q['name'] != query_name]
            self._save_queries_to_storage()
            self._load_saved_queries()
    
    def _save_queries_to_storage(self):
        """Save queries to persistent storage."""
        # Could save to file or config
        # For now, just keep in memory
        pass
    
    def _export_results(self):
        """Export search results."""
        from PyQt6.QtWidgets import QFileDialog
        from pathlib import Path
        
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Export Search Results",
            str(Path.home() / "timesketch_search_results.json"),
            "JSON Files (*.json);;All Files (*)"
        )
        
        if filename:
            try:
                import json
                results = []
                for row in range(self.results_table.rowCount()):
                    detail_item = self.results_table.item(row, 5)
                    if detail_item:
                        result = detail_item.data(Qt.ItemDataRole.UserRole)
                        if result:
                            results.append(result)
                
                with open(filename, 'w') as f:
                    json.dump(results, f, indent=2)
                
                QMessageBox.information(self, "Success", f"Exported {len(results)} results to {filename}")
            
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to export results:\n{e}")

