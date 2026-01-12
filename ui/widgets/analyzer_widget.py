"""Timesketch analyzer integration widget."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QComboBox,
    QTableWidget, QTableWidgetItem, QMessageBox, QGroupBox, QTextEdit,
    QProgressBar, QListWidget, QListWidgetItem
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from typing import Optional
import logging

from services.timesketch_service import TimesketchService
from services.sketch_manager import SketchManager
from services.data_service import DataService
from ui.timesketch_config import TimesketchConfigDialog

logger = logging.getLogger(__name__)


class AnalyzerRunnerThread(QThread):
    """Thread for running Timesketch analyzers."""
    
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)
    
    def __init__(self, timesketch_service: TimesketchService, sketch_id: str,
                 analyzer_name: str, timeline_id: Optional[str] = None):
        super().__init__()
        self.timesketch_service = timesketch_service
        self.sketch_id = sketch_id
        self.analyzer_name = analyzer_name
        self.timeline_id = timeline_id
    
    def run(self):
        """Run the analyzer."""
        try:
            result = self.timesketch_service.run_analyzer(
                self.sketch_id,
                self.analyzer_name,
                self.timeline_id
            )
            if result:
                self.finished.emit(result)
            else:
                self.error.emit("Analyzer returned no results")
        except Exception as e:
            self.error.emit(str(e))


class AnalyzerWidget(QWidget):
    """Widget for running and managing Timesketch analyzers."""
    
    # Common Timesketch analyzers
    ANALYZERS = [
        ("sigma", "Sigma Analyzer - Detection rules"),
        ("feature_extraction", "Feature Extraction Analyzer"),
        ("hashr", "HashR Analyzer - Hash analysis"),
        ("llm", "LLM Analyzer - AI-powered log analysis"),
        ("tagger", "Tagger Analyzer - Event tagging"),
        ("domain", "Domain Analyzer - Domain analysis"),
        ("browser_search", "Browser Search Analyzer"),
        ("sessionize", "Sessionize Analyzer - Session analysis"),
        ("yara", "YARA Analyzer - YARA rule matching"),
        ("virustotal", "VirusTotal Analyzer"),
    ]
    
    def __init__(self, case_id: Optional[str] = None, parent=None):
        super().__init__(parent)
        self.case_id = case_id
        self.timesketch_service: Optional[TimesketchService] = None
        self.sketch_manager = SketchManager()
        self.data_service = DataService()
        
        self._setup_ui()
        self._load_service()
    
    def _setup_ui(self):
        """Set up the UI."""
        layout = QVBoxLayout()
        
        # Header
        header_label = QLabel(
            "<h3>Timesketch Analyzers</h3>"
            "<p>Run analyzers on your Timesketch sketches to extract insights and detect patterns.</p>"
        )
        header_label.setWordWrap(True)
        layout.addWidget(header_label)
        
        # Sketch selection
        sketch_group = QGroupBox("Sketch Selection")
        sketch_layout = QVBoxLayout()
        
        if self.case_id:
            case = self.data_service.get_case(self.case_id)
            case_label = QLabel(f"<b>Case:</b> {case.get('title', self.case_id) if case else self.case_id}")
            sketch_layout.addWidget(case_label)
            
            mapping = self.sketch_manager.get_sketch_for_case(self.case_id)
            if mapping:
                sketch_id = mapping.get('sketch_id')
                sketch_label = QLabel(f"<b>Sketch ID:</b> {sketch_id}")
                sketch_layout.addWidget(sketch_label)
                self.current_sketch_id = sketch_id
            else:
                no_sketch_label = QLabel("<b>No Timesketch sketch found for this case.</b>")
                no_sketch_label.setStyleSheet("color: red;")
                sketch_layout.addWidget(no_sketch_label)
                self.current_sketch_id = None
        else:
            sketch_layout.addWidget(QLabel("Select a case or sketch to run analyzers."))
            self.current_sketch_id = None
        
        sketch_group.setLayout(sketch_layout)
        layout.addWidget(sketch_group)
        
        # Analyzer selection
        analyzer_group = QGroupBox("Analyzer Configuration")
        analyzer_layout = QVBoxLayout()
        
        analyzer_layout.addWidget(QLabel("Select Analyzer:"))
        self.analyzer_combo = QComboBox()
        for analyzer_id, analyzer_desc in self.ANALYZERS:
            self.analyzer_combo.addItem(analyzer_desc, analyzer_id)
        analyzer_layout.addWidget(self.analyzer_combo)
        
        timeline_layout = QHBoxLayout()
        timeline_layout.addWidget(QLabel("Timeline (optional):"))
        self.timeline_combo = QComboBox()
        self.timeline_combo.addItem("All Timelines", None)
        timeline_layout.addWidget(self.timeline_combo)
        analyzer_layout.addLayout(timeline_layout)
        
        run_btn = QPushButton("Run Analyzer")
        run_btn.clicked.connect(self._run_analyzer)
        analyzer_layout.addWidget(run_btn)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        analyzer_layout.addWidget(self.progress_bar)
        
        analyzer_group.setLayout(analyzer_layout)
        layout.addWidget(analyzer_group)
        
        # Results
        results_group = QGroupBox("Analysis Results")
        results_layout = QVBoxLayout()
        
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(4)
        self.results_table.setHorizontalHeaderLabels([
            "Analyzer", "Status", "Started", "Results"
        ])
        
        # Make columns and rows resizable by user (like Excel)
        from PyQt6.QtWidgets import QHeaderView
        self.results_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.results_table.horizontalHeader().setStretchLastSection(False)
        self.results_table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.results_table.verticalHeader().setVisible(True)
        self.results_table.verticalHeader().setDefaultSectionSize(30)
        results_layout.addWidget(self.results_table)
        
        # Result details
        self.result_details = QTextEdit()
        self.result_details.setReadOnly(True)
        self.result_details.setMaximumHeight(200)
        self.results_table.itemSelectionChanged.connect(self._show_result_details)
        results_layout.addWidget(self.result_details)
        
        results_group.setLayout(results_layout)
        layout.addWidget(results_group)
        
        # Load previous analyses
        refresh_btn = QPushButton("Refresh Analyses")
        refresh_btn.clicked.connect(self._load_analyses)
        layout.addWidget(refresh_btn)
        
        self.setLayout(layout)
        
        # Load analyses if sketch is available
        if self.current_sketch_id:
            self._load_analyses()
    
    def _load_service(self):
        """Load Timesketch service."""
        self.timesketch_service = TimesketchConfigDialog.load_service()
        if not self.timesketch_service:
            QMessageBox.warning(
                self,
                "Timesketch Not Configured",
                "Please configure Timesketch first to use analyzers."
            )
    
    def _run_analyzer(self):
        """Run the selected analyzer."""
        if not self.timesketch_service:
            QMessageBox.warning(self, "Not Configured", "Timesketch is not configured.")
            return
        
        if not self.current_sketch_id:
            QMessageBox.warning(self, "No Sketch", "No sketch selected.")
            return
        
        analyzer_id = self.analyzer_combo.currentData()
        timeline_id = self.timeline_combo.currentData()
        
        # Show progress
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate
        
        # Run analyzer in thread
        self.runner_thread = AnalyzerRunnerThread(
            self.timesketch_service,
            self.current_sketch_id,
            analyzer_id,
            timeline_id
        )
        self.runner_thread.finished.connect(self._on_analyzer_finished)
        self.runner_thread.error.connect(self._on_analyzer_error)
        self.runner_thread.start()
    
    def _on_analyzer_finished(self, result: dict):
        """Handle analyzer completion."""
        self.progress_bar.setVisible(False)
        
        QMessageBox.information(
            self,
            "Analyzer Complete",
            f"Analyzer finished successfully.\n\nCheck the results table for details."
        )
        
        # Refresh analyses
        self._load_analyses()
    
    def _on_analyzer_error(self, error: str):
        """Handle analyzer error."""
        self.progress_bar.setVisible(False)
        QMessageBox.critical(self, "Analyzer Error", f"Error running analyzer:\n\n{error}")
    
    def _load_analyses(self):
        """Load analysis results for the current sketch."""
        if not self.timesketch_service or not self.current_sketch_id:
            return
        
        try:
            analyses = self.timesketch_service.get_sketch_analyses(self.current_sketch_id)
            
            self.results_table.setRowCount(len(analyses))
            
            for row, analysis in enumerate(analyses):
                analyzer_name = analysis.get('analyzer_name', 'Unknown')
                status = analysis.get('status', 'unknown')
                created = analysis.get('created_at', '')
                if created:
                    created = created.split('T')[0]
                
                self.results_table.setItem(row, 0, QTableWidgetItem(analyzer_name))
                
                status_item = QTableWidgetItem(status)
                if status == 'DONE':
                    status_item.setForeground(Qt.GlobalColor.green)
                elif status == 'ERROR':
                    status_item.setForeground(Qt.GlobalColor.red)
                self.results_table.setItem(row, 1, status_item)
                
                self.results_table.setItem(row, 2, QTableWidgetItem(created))
                
                # Store full analysis data
                result_text = f"Status: {status}\n"
                if analysis.get('result'):
                    result_text += f"Results: {analysis.get('result')}"
                self.results_table.setItem(row, 3, QTableWidgetItem(result_text[:100]))
                self.results_table.item(row, 3).setData(Qt.ItemDataRole.UserRole, analysis)
            
            self.results_table.resizeColumnsToContents()
        
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to load analyses:\n{e}")
    
    def _show_result_details(self):
        """Show details of selected analysis result."""
        row = self.results_table.currentRow()
        if row < 0:
            return
        
        item = self.results_table.item(row, 3)
        if not item:
            return
        
        analysis = item.data(Qt.ItemDataRole.UserRole)
        if not analysis:
            return
        
        # Build details text
        details = []
        details.append(f"Analyzer: {analysis.get('analyzer_name', 'Unknown')}")
        details.append(f"Status: {analysis.get('status', 'Unknown')}")
        details.append(f"Created: {analysis.get('created_at', 'N/A')}")
        details.append(f"Updated: {analysis.get('updated_at', 'N/A')}")
        details.append("")
        
        if analysis.get('result'):
            details.append("Results:")
            details.append(str(analysis.get('result')))
        
        if analysis.get('error'):
            details.append("")
            details.append("Error:")
            details.append(str(analysis.get('error')))
        
        self.result_details.setPlainText('\n'.join(details))

