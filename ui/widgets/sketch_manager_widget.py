"""Sketch manager widget for managing Timesketch sketches."""

import logging
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QMessageBox, QGroupBox
)
from PyQt6.QtCore import Qt

from services.sketch_manager import SketchManager
from services.data_service import DataService
from services.timesketch_service import TimesketchService
from services.timeline_service import TimelineService
from ui.timesketch_config import TimesketchConfigDialog

logger = logging.getLogger(__name__)


class SketchManagerWidget(QWidget):
    """Widget for managing Timesketch sketches."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.sketch_manager = SketchManager()
        self.data_service = DataService()
        self.timeline_service = TimelineService()
        self.timesketch_service = None
        self.connection_status = "unknown"
        
        self._setup_ui()
        self.refresh()
    
    def _setup_ui(self):
        """Set up the UI."""
        layout = QVBoxLayout()
        
        # Status bar
        status_group = QGroupBox("Connection Status")
        status_layout = QVBoxLayout()
        
        self.status_label = QLabel("Checking connection...")
        self.status_label.setWordWrap(True)
        status_layout.addWidget(self.status_label)
        
        test_btn = QPushButton("Test Connection")
        test_btn.clicked.connect(self._test_connection)
        status_layout.addWidget(test_btn)
        
        config_btn = QPushButton("Configure Timesketch...")
        config_btn.clicked.connect(self._open_config)
        status_layout.addWidget(config_btn)
        
        status_group.setLayout(status_layout)
        layout.addWidget(status_group)
        
        # Info
        info_label = QLabel(
            "Timesketch Sketch Manager\n\n"
            "Manage the relationship between cases and Timesketch sketches."
        )
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # Toolbar
        toolbar = QHBoxLayout()
        
        sync_all_btn = QPushButton("Sync All Cases")
        sync_all_btn.clicked.connect(self._sync_all_cases)
        toolbar.addWidget(sync_all_btn)
        
        toolbar.addStretch()
        
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.refresh)
        toolbar.addWidget(refresh_btn)
        
        layout.addLayout(toolbar)
        
        # Sketches table
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "Case ID", "Case Title", "Sketch ID", "Status", "Last Sync", "Actions"
        ])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        
        # Make table expand to fill available space (relative sizing)
        layout.addWidget(self.table, 1)  # Stretch factor of 1
        
        # Empty state message
        self.empty_label = QLabel("No sketch mappings found. Create a mapping by syncing a case to Timesketch.")
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_label.setStyleSheet("color: gray; padding: 20px;")
        self.empty_label.setVisible(False)
        layout.addWidget(self.empty_label)
        
        self.setLayout(layout)
    
    def _test_connection(self):
        """Test Timesketch connection."""
        self.timesketch_service = TimesketchConfigDialog.load_service()
        
        if not self.timesketch_service:
            self._update_status("error", "Timesketch is not configured. Please configure it first.")
            return
        
        self._update_status("checking", "Testing connection...")
        
        try:
            success, message = self.timesketch_service.test_connection()
            if success:
                self._update_status("connected", f"✅ Connected successfully!\n{message}")
            else:
                self._update_status("error", f"❌ Connection failed:\n{message}")
        except Exception as e:
            logger.error(f"Error testing connection: {e}", exc_info=True)
            self._update_status("error", f"❌ Error testing connection:\n{str(e)}")
    
    def _update_status(self, status: str, message: str):
        """Update connection status display."""
        self.connection_status = status
        
        if status == "connected":
            self.status_label.setText(f"<b style='color: green;'>{message}</b>")
        elif status == "error":
            self.status_label.setText(f"<b style='color: red;'>{message}</b>")
        elif status == "checking":
            self.status_label.setText(f"<b>{message}</b>")
        else:
            self.status_label.setText(message)
    
    def _open_config(self):
        """Open Timesketch configuration dialog."""
        dialog = TimesketchConfigDialog(self)
        if dialog.exec() == dialog.DialogCode.Accepted:
            self.refresh()
    
    def refresh(self):
        """Refresh sketch mappings."""
        # Load Timesketch service and test connection
        self.timesketch_service = TimesketchConfigDialog.load_service()
        
        if not self.timesketch_service:
            self._update_status("error", "Timesketch is not configured. Click 'Configure Timesketch...' to set it up.")
        else:
            # Test connection in background (non-blocking)
            try:
                success, message = self.timesketch_service.test_connection()
                if success:
                    self._update_status("connected", f"✅ Connected to Timesketch")
                else:
                    self._update_status("error", f"⚠️ Connection issue: {message}")
            except Exception as e:
                logger.error(f"Error during refresh connection test: {e}")
                self._update_status("error", f"⚠️ Error: {str(e)}")
        
        mappings = self.sketch_manager.list_all_mappings()
        cases = self.data_service.get_cases()
        
        # Create case lookup
        case_lookup = {case.get('case_id'): case for case in cases}
        
        # Show/hide empty state
        if len(mappings) == 0:
            self.table.setVisible(False)
            self.empty_label.setVisible(True)
        else:
            self.table.setVisible(True)
            self.empty_label.setVisible(False)
        
        self.table.setRowCount(len(mappings))
        
        for row, mapping in enumerate(mappings):
            case_id = mapping.get('case_id', '')
            case = case_lookup.get(case_id, {})
            
            # Case ID
            self.table.setItem(row, 0, QTableWidgetItem(case_id))
            
            # Case Title
            self.table.setItem(row, 1, QTableWidgetItem(case.get('title', 'N/A')))
            
            # Sketch ID
            self.table.setItem(row, 2, QTableWidgetItem(mapping.get('sketch_id', 'N/A')))
            
            # Status
            status = mapping.get('sync_status', 'unknown')
            status_item = QTableWidgetItem(status)
            if status == 'synced':
                status_item.setForeground(Qt.GlobalColor.green)
            elif status == 'error':
                status_item.setForeground(Qt.GlobalColor.red)
            self.table.setItem(row, 3, status_item)
            
            # Last Sync
            last_sync = mapping.get('last_sync', '')
            if last_sync:
                last_sync = last_sync.split('T')[0]
            self.table.setItem(row, 4, QTableWidgetItem(last_sync))
            
            # Actions
            action_widget = QWidget()
            action_layout = QHBoxLayout()
            action_layout.setContentsMargins(2, 2, 2, 2)
            
            sync_btn = QPushButton("Sync")
            sync_btn.clicked.connect(lambda checked, cid=case_id: self._sync_case(cid))
            action_layout.addWidget(sync_btn)
            
            open_btn = QPushButton("Open")
            open_btn.clicked.connect(lambda checked, sid=mapping.get('sketch_id'): self._open_sketch(sid))
            action_layout.addWidget(open_btn)
            
            action_widget.setLayout(action_layout)
            self.table.setCellWidget(row, 5, action_widget)
        
        self.table.resizeColumnsToContents()
    
    def _sync_case(self, case_id: str):
        """Sync a specific case to Timesketch."""
        if not self.timesketch_service:
            QMessageBox.warning(
                self,
                "Timesketch Not Configured",
                "Please configure Timesketch first."
            )
            return
        
        case = self.data_service.get_case(case_id)
        if not case:
            QMessageBox.warning(self, "Not Found", f"Case {case_id} not found.")
            return
        
        # Get findings
        finding_ids = case.get('finding_ids', [])
        findings = []
        for finding_id in finding_ids:
            finding = self.data_service.get_finding(finding_id)
            if finding:
                findings.append(finding)
        
        # Sync
        success = self.sketch_manager.sync_case_to_sketch(
            case_id,
            case,
            findings,
            self.timesketch_service,
            self.timeline_service
        )
        
        if success:
            QMessageBox.information(self, "Success", f"Case {case_id} synced successfully!")
            self.refresh()
        else:
            QMessageBox.critical(self, "Error", f"Failed to sync case {case_id}.")
    
    def _sync_all_cases(self):
        """Sync all cases to Timesketch."""
        if not self.timesketch_service:
            QMessageBox.warning(
                self,
                "Timesketch Not Configured",
                "Please configure Timesketch first."
            )
            return
        
        reply = QMessageBox.question(
            self,
            "Confirm Sync All",
            "This will sync all cases to Timesketch. Continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        cases = self.data_service.get_cases()
        success_count = 0
        
        for case in cases:
            case_id = case.get('case_id')
            finding_ids = case.get('finding_ids', [])
            findings = []
            
            for finding_id in finding_ids:
                finding = self.data_service.get_finding(finding_id)
                if finding:
                    findings.append(finding)
            
            if self.sketch_manager.sync_case_to_sketch(
                case_id, case, findings,
                self.timesketch_service, self.timeline_service
            ):
                success_count += 1
        
        QMessageBox.information(
            self,
            "Sync Complete",
            f"Synced {success_count} of {len(cases)} cases to Timesketch."
        )
        self.refresh()
    
    def _open_sketch(self, sketch_id: str):
        """Open sketch in Timesketch web interface."""
        if not sketch_id:
            return
        
        if not self.timesketch_service:
            QMessageBox.warning(self, "Not Configured", "Timesketch is not configured.")
            return
        
        import webbrowser
        server_url = self.timesketch_service.server_url
        sketch_url = f"{server_url}/sketches/{sketch_id}/"
        webbrowser.open(sketch_url)

