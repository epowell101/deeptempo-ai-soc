"""Collaboration features widget for Timesketch."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QTableWidget,
    QTableWidgetItem, QTextEdit, QLineEdit, QComboBox, QMessageBox,
    QGroupBox, QListWidget, QListWidgetItem, QDialog, QFormLayout
)
from PyQt6.QtCore import Qt, QTimer
from typing import Optional
import logging

from services.timesketch_service import TimesketchService
from services.sketch_manager import SketchManager
from services.data_service import DataService
from ui.timesketch_config import TimesketchConfigDialog

logger = logging.getLogger(__name__)


class ShareSketchDialog(QDialog):
    """Dialog for sharing a sketch with users."""
    
    def __init__(self, sketch_id: str, timesketch_service: TimesketchService, parent=None):
        super().__init__(parent)
        self.sketch_id = sketch_id
        self.timesketch_service = timesketch_service
        self.setWindowTitle("Share Sketch")
        self.setMinimumSize(400, 200)
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the UI."""
        layout = QFormLayout()
        
        self.username_edit = QLineEdit()
        self.username_edit.setPlaceholderText("Enter username...")
        layout.addRow("Username:", self.username_edit)
        
        self.permission_combo = QComboBox()
        self.permission_combo.addItems(["read", "write", "delete"])
        layout.addRow("Permission:", self.permission_combo)
        
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        share_btn = QPushButton("Share")
        share_btn.clicked.connect(self._share)
        button_layout.addWidget(share_btn)
        
        layout.addRow(button_layout)
        
        self.setLayout(layout)
    
    def _share(self):
        """Share the sketch."""
        username = self.username_edit.text().strip()
        if not username:
            QMessageBox.warning(self, "Validation Error", "Please enter a username.")
            return
        
        permission = self.permission_combo.currentText()
        
        success = self.timesketch_service.share_sketch(self.sketch_id, username, permission)
        
        if success:
            QMessageBox.information(self, "Success", f"Sketch shared with {username}.")
            self.accept()
        else:
            QMessageBox.critical(self, "Error", "Failed to share sketch.")


class CollaborationWidget(QWidget):
    """Widget for collaboration features."""
    
    def __init__(self, case_id: str, parent=None):
        super().__init__(parent)
        self.case_id = case_id
        self.timesketch_service: Optional[TimesketchService] = None
        self.sketch_manager = SketchManager()
        self.data_service = DataService()
        
        self.sketch_id = None
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self._refresh_activity)
        
        self._setup_ui()
        self._load_service()
        self._load_sketch()
    
    def _setup_ui(self):
        """Set up the UI."""
        layout = QVBoxLayout()
        
        # Header
        case = self.data_service.get_case(self.case_id)
        header_label = QLabel(
            f"<h3>Collaboration</h3>"
            f"<p><b>Case:</b> {case.get('title', self.case_id) if case else self.case_id}</p>"
        )
        layout.addWidget(header_label)
        
        # Collaborators
        collaborators_group = QGroupBox("Collaborators")
        collaborators_layout = QVBoxLayout()
        
        toolbar = QHBoxLayout()
        share_btn = QPushButton("Share Sketch")
        share_btn.clicked.connect(self._share_sketch)
        toolbar.addWidget(share_btn)
        
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self._load_collaborators)
        toolbar.addWidget(refresh_btn)
        
        toolbar.addStretch()
        collaborators_layout.addLayout(toolbar)
        
        self.collaborators_table = QTableWidget()
        self.collaborators_table.setColumnCount(3)
        self.collaborators_table.setHorizontalHeaderLabels([
            "Username", "Permission", "Added"
        ])
        # Make resizable
        from PyQt6.QtWidgets import QHeaderView
        self.collaborators_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.collaborators_table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.collaborators_table.verticalHeader().setVisible(True)
        collaborators_layout.addWidget(self.collaborators_table)
        
        collaborators_group.setLayout(collaborators_layout)
        layout.addWidget(collaborators_group)
        
        # Activity Feed
        activity_group = QGroupBox("Activity Feed")
        activity_layout = QVBoxLayout()
        
        activity_toolbar = QHBoxLayout()
        auto_refresh_checkbox = QLabel("Auto-refresh:")
        activity_toolbar.addWidget(auto_refresh_checkbox)
        
        self.auto_refresh_btn = QPushButton("Enable")
        self.auto_refresh_btn.setCheckable(True)
        self.auto_refresh_btn.toggled.connect(self._toggle_auto_refresh)
        activity_toolbar.addWidget(self.auto_refresh_btn)
        
        activity_toolbar.addStretch()
        
        refresh_activity_btn = QPushButton("Refresh")
        refresh_activity_btn.clicked.connect(self._refresh_activity)
        activity_toolbar.addWidget(refresh_activity_btn)
        
        activity_layout.addLayout(activity_toolbar)
        
        self.activity_list = QListWidget()
        activity_layout.addWidget(self.activity_list)
        
        activity_group.setLayout(activity_layout)
        layout.addWidget(activity_group)
        
        # Comments
        comments_group = QGroupBox("Comments")
        comments_layout = QVBoxLayout()
        
        self.comments_list = QListWidget()
        comments_layout.addWidget(self.comments_list)
        
        comment_input_layout = QHBoxLayout()
        self.comment_edit = QLineEdit()
        self.comment_edit.setPlaceholderText("Add a comment...")
        self.comment_edit.returnPressed.connect(self._add_comment)
        comment_input_layout.addWidget(self.comment_edit)
        
        add_comment_btn = QPushButton("Add Comment")
        add_comment_btn.clicked.connect(self._add_comment)
        comment_input_layout.addWidget(add_comment_btn)
        
        comments_layout.addLayout(comment_input_layout)
        
        comments_group.setLayout(comments_layout)
        layout.addWidget(comments_group)
        
        self.setLayout(layout)
    
    def _load_service(self):
        """Load Timesketch service."""
        self.timesketch_service = TimesketchConfigDialog.load_service()
        if not self.timesketch_service:
            QMessageBox.warning(
                self,
                "Timesketch Not Configured",
                "Please configure Timesketch first to use collaboration features."
            )
    
    def _load_sketch(self):
        """Load sketch for the case."""
        mapping = self.sketch_manager.get_sketch_for_case(self.case_id)
        if mapping:
            self.sketch_id = mapping.get('sketch_id')
            self._load_collaborators()
            self._refresh_activity()
        else:
            QMessageBox.warning(
                self,
                "No Sketch",
                "This case has not been exported to Timesketch yet."
            )
    
    def _load_collaborators(self):
        """Load collaborators for the sketch."""
        if not self.timesketch_service or not self.sketch_id:
            return
        
        try:
            collaborators = self.timesketch_service.get_sketch_collaborators(self.sketch_id)
            
            self.collaborators_table.setRowCount(len(collaborators))
            
            for row, collab in enumerate(collaborators):
                username = collab.get('username', 'Unknown')
                permission = collab.get('permission', 'read')
                added = collab.get('created_at', '')
                if added:
                    added = added.split('T')[0]
                
                self.collaborators_table.setItem(row, 0, QTableWidgetItem(username))
                self.collaborators_table.setItem(row, 1, QTableWidgetItem(permission))
                self.collaborators_table.setItem(row, 2, QTableWidgetItem(added))
            
            self.collaborators_table.resizeColumnsToContents()
        
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to load collaborators:\n{e}")
    
    def _share_sketch(self):
        """Share the sketch with a user."""
        if not self.timesketch_service or not self.sketch_id:
            QMessageBox.warning(self, "Not Available", "Timesketch service or sketch not available.")
            return
        
        dialog = ShareSketchDialog(self.sketch_id, self.timesketch_service, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self._load_collaborators()
    
    def _refresh_activity(self):
        """Refresh activity feed."""
        if not self.timesketch_service or not self.sketch_id:
            return
        
        try:
            activities = self.timesketch_service.get_sketch_activity(self.sketch_id, limit=50)
            
            self.activity_list.clear()
            
            for activity in activities:
                activity_type = activity.get('activity_type', 'unknown')
                user = activity.get('user', {}).get('username', 'Unknown')
                timestamp = activity.get('created_at', '')
                if timestamp:
                    timestamp = timestamp.split('T')[0] + ' ' + timestamp.split('T')[1].split('.')[0]
                
                description = activity.get('description', '')
                
                item_text = f"[{timestamp}] {user}: {activity_type}"
                if description:
                    item_text += f" - {description}"
                
                item = QListWidgetItem(item_text)
                self.activity_list.addItem(item)
        
        except Exception as e:
            logger.error(f"Error loading activity: {e}")
    
    def _toggle_auto_refresh(self, enabled: bool):
        """Toggle auto-refresh for activity feed."""
        if enabled:
            self.refresh_timer.start(30000)  # Refresh every 30 seconds
            self.auto_refresh_btn.setText("Disable")
        else:
            self.refresh_timer.stop()
            self.auto_refresh_btn.setText("Enable")
    
    def _add_comment(self):
        """Add a comment to the selected event."""
        # This would require selecting an event first
        # For now, show a message
        QMessageBox.information(
            self,
            "Add Comment",
            "To add a comment, select an event in the timeline view first."
        )

