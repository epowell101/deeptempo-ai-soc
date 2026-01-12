"""Timesketch timeline visualizer widget."""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget,
    QTableWidgetItem, QMessageBox, QGroupBox, QTextEdit, QLineEdit
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
import webbrowser

from services.timesketch_service import TimesketchService
from services.timeline_service import TimelineService
from services.data_service import DataService
from ui.timesketch_config import TimesketchConfigDialog
from ui.widgets.event_analysis_widget import EventAnalysisWidget
from ui.utils.auto_resize import TableAutoResize, ButtonSizePolicy


class TimesketchTimelineWidget(QDialog):
    """Widget for viewing Timesketch timeline."""
    
    # Material Design severity colors
    SEVERITY_COLORS = {
        'critical': QColor('#D32F2F'),  # Red
        'high': QColor('#F57C00'),      # Orange
        'medium': QColor('#FBC02D'),    # Yellow
        'low': QColor('#388E3C')        # Green
    }
    
    def __init__(self, case: dict, mapping: dict, parent=None):
        super().__init__(parent)
        self.case = case
        self.mapping = mapping
        self.setWindowTitle(f"Timeline: {case.get('title', 'Untitled Case')}")
        self.setMinimumSize(1000, 700)
        
        self.timesketch_service = None
        self.data_service = DataService()
        self.timeline_service = TimelineService()
        
        self._setup_ui()
        self._load_timeline()
    
    def _setup_ui(self):
        """Set up the UI."""
        layout = QVBoxLayout()
        
        # Header
        header_layout = QHBoxLayout()
        
        case_info = QLabel(
            f"<b>Case:</b> {self.case.get('title', 'Untitled')}<br>"
            f"<b>Sketch ID:</b> {self.mapping.get('sketch_id', 'N/A')}"
        )
        header_layout.addWidget(case_info)
        
        header_layout.addStretch()
        
        open_ts_btn = QPushButton("Open in Timesketch")
        ButtonSizePolicy.make_compact(open_ts_btn, min_width=140)
        open_ts_btn.clicked.connect(self._open_in_timesketch)
        header_layout.addWidget(open_ts_btn)
        
        refresh_btn = QPushButton("Refresh")
        ButtonSizePolicy.make_compact(refresh_btn, min_width=80)
        refresh_btn.clicked.connect(self._load_timeline)
        header_layout.addWidget(refresh_btn)
        
        layout.addLayout(header_layout)
        
        # Timeline events table
        events_group = QGroupBox("Timeline Events")
        events_layout = QVBoxLayout()
        
        # Search/filter
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Search:"))
        
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search events...")
        self.search_edit.textChanged.connect(self._filter_events)
        filter_layout.addWidget(self.search_edit)
        
        events_layout.addLayout(filter_layout)
        
        # Events table
        self.events_table = QTableWidget()
        self.events_table.setColumnCount(6)
        self.events_table.setHorizontalHeaderLabels([
            "Timestamp", "Message", "Source", "Severity", "Data Source", "MITRE"
        ])
        
        # Configure intelligent auto-resizing for columns
        from PyQt6.QtWidgets import QHeaderView
        TableAutoResize.configure(
            self.events_table,
            content_fit_columns=[2, 3, 4],  # Source, Severity, Data Source (auto-fit)
            stretch_columns=[1, 5],  # Message, MITRE (stretch to fill)
            interactive_columns=[0]  # Timestamp (user can resize)
        )
        self.events_table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.events_table.verticalHeader().setVisible(True)
        self.events_table.verticalHeader().setDefaultSectionSize(30)
        
        self.events_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.events_table.itemDoubleClicked.connect(self._view_event_details)
        
        # Analysis button
        analyze_btn = QPushButton("Analyze Event with Claude")
        ButtonSizePolicy.make_flexible(analyze_btn, min_width=180)
        analyze_btn.clicked.connect(self._analyze_selected_event)
        events_layout.addWidget(analyze_btn)
        
        events_layout.addWidget(self.events_table)
        events_group.setLayout(events_layout)
        layout.addWidget(events_group)
        
        # Event details
        details_group = QGroupBox("Event Details")
        details_layout = QVBoxLayout()
        
        self.details_text = QTextEdit()
        self.details_text.setReadOnly(True)
        self.details_text.setMaximumHeight(150)
        details_layout.addWidget(self.details_text)
        
        details_group.setLayout(details_layout)
        layout.addWidget(details_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        close_btn = QPushButton("Close")
        ButtonSizePolicy.make_compact(close_btn, min_width=80)
        close_btn.clicked.connect(self.close)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
        # Load Timesketch service
        self.timesketch_service = TimesketchConfigDialog.load_service()
        if not self.timesketch_service:
            QMessageBox.warning(
                self,
                "Timesketch Not Configured",
                "Timesketch is not configured. Timeline will show local data only."
            )
    
    def _load_timeline(self):
        """Load timeline events."""
        # Get findings for the case
        finding_ids = self.case.get('finding_ids', [])
        findings = []
        for finding_id in finding_ids:
            finding = self.data_service.get_finding(finding_id)
            if finding:
                findings.append(finding)
        
        # Convert to timeline events
        events = self.timeline_service.case_to_timeline_events(self.case, findings)
        
        # Try to load from Timesketch if available
        if self.timesketch_service and self.mapping.get('sketch_id'):
            try:
                sketch_id = self.mapping.get('sketch_id')
                timeline_id = self.mapping.get('timeline_id')
                
                if timeline_id:
                    ts_events = self.timesketch_service.get_timeline_events(
                        sketch_id, timeline_id, limit=1000
                    )
                    if ts_events:
                        # Merge with local events (prefer Timesketch data)
                        events = ts_events
            except Exception as e:
                QMessageBox.warning(
                    self,
                    "Timesketch Load Error",
                    f"Could not load events from Timesketch:\n{e}\n\nShowing local data."
                )
        
        self.all_events = events
        self._populate_table(events)
    
    def _populate_table(self, events: list):
        """Populate events table."""
        self.events_table.setRowCount(len(events))
        
        for row, event in enumerate(events):
            # Timestamp
            timestamp = event.get('timestamp', '')
            if 'T' in timestamp:
                timestamp = timestamp.split('T')[0] + ' ' + timestamp.split('T')[1].split('.')[0]
            self.events_table.setItem(row, 0, QTableWidgetItem(timestamp))
            
            # Message
            message = event.get('message', '')
            self.events_table.setItem(row, 1, QTableWidgetItem(message))
            
            # Source
            source = event.get('source_short', event.get('source', 'Unknown'))
            self.events_table.setItem(row, 2, QTableWidgetItem(source))
            
            # Severity with Material Design colors
            severity = event.get('severity', '').lower()
            severity_item = QTableWidgetItem(severity.capitalize() if severity else '')
            if severity in self.SEVERITY_COLORS:
                severity_item.setForeground(self.SEVERITY_COLORS[severity])
            self.events_table.setItem(row, 3, severity_item)
            
            # Data Source
            data_source = event.get('data_source', '')
            self.events_table.setItem(row, 4, QTableWidgetItem(data_source))
            
            # MITRE
            mitre = event.get('mitre_techniques_str', '')
            if not mitre and event.get('mitre_techniques'):
                mitre = ', '.join(event.get('mitre_techniques', [])[:3])
            self.events_table.setItem(row, 5, QTableWidgetItem(mitre))
        
        self.events_table.resizeColumnsToContents()
    
    def _filter_events(self):
        """Filter events by search text."""
        search_text = self.search_edit.text().lower()
        
        if not search_text:
            self._populate_table(self.all_events)
            return
        
        filtered = []
        for event in self.all_events:
            # Search in message, source, and other fields
            searchable = [
                event.get('message', ''),
                event.get('source', ''),
                event.get('data_source', ''),
                str(event.get('severity', '')),
            ]
            if any(search_text in str(s).lower() for s in searchable):
                filtered.append(event)
        
        self._populate_table(filtered)
    
    def _view_event_details(self, item):
        """View details of selected event."""
        row = self.events_table.currentRow()
        if row < 0 or row >= len(self.all_events):
            return
        
        event = self.all_events[row]
        
        # Build details text
        details = []
        details.append(f"Timestamp: {event.get('timestamp', 'N/A')}")
        details.append(f"Message: {event.get('message', 'N/A')}")
        details.append(f"Source: {event.get('source', 'N/A')}")
        details.append(f"Severity: {event.get('severity', 'N/A')}")
        details.append(f"Data Source: {event.get('data_source', 'N/A')}")
        
        if event.get('finding_id'):
            details.append(f"Finding ID: {event.get('finding_id')}")
        
        if event.get('case_id'):
            details.append(f"Case ID: {event.get('case_id')}")
        
        if event.get('mitre_techniques'):
            details.append(f"MITRE Techniques: {', '.join(event.get('mitre_techniques', []))}")
        
        if event.get('entity_src_ip'):
            details.append(f"Source IP: {event.get('entity_src_ip')}")
        
        if event.get('entity_dst_ip'):
            details.append(f"Destination IP: {event.get('entity_dst_ip')}")
        
        if event.get('anomaly_score'):
            details.append(f"Anomaly Score: {event.get('anomaly_score')}")
        
        self.details_text.setPlainText('\n'.join(details))
    
    def _analyze_selected_event(self):
        """Analyze selected event with Claude."""
        row = self.events_table.currentRow()
        if row < 0 or row >= len(self.all_events):
            QMessageBox.information(
                self,
                "No Selection",
                "Please select an event to analyze."
            )
            return
        
        event = self.all_events[row]
        
        # Open analysis dialog
        analysis_dialog = EventAnalysisWidget(event, self.all_events, self)
        analysis_dialog.exec()
    
    def _open_in_timesketch(self):
        """Open sketch in Timesketch web interface."""
        sketch_id = self.mapping.get('sketch_id')
        if not sketch_id:
            QMessageBox.warning(self, "No Sketch", "No Timesketch sketch ID available.")
            return
        
        if not self.timesketch_service:
            QMessageBox.warning(self, "Not Configured", "Timesketch is not configured.")
            return
        
        # Build Timesketch URL
        server_url = self.timesketch_service.server_url
        sketch_url = f"{server_url}/sketches/{sketch_id}/"
        
        # Open in browser
        webbrowser.open(sketch_url)
        
        QMessageBox.information(
            self,
            "Opened in Browser",
            f"Timesketch sketch opened in your browser:\n{sketch_url}"
        )

