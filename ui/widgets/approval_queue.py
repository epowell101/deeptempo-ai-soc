"""Approval Queue widget for managing pending autonomous actions."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,
    QTableWidgetItem, QLabel, QTextEdit, QDialog, QDialogButtonBox,
    QMessageBox, QHeaderView, QSplitter, QCheckBox
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QColor
import logging

logger = logging.getLogger(__name__)


class ActionDetailDialog(QDialog):
    """Dialog showing detailed information about a pending action."""
    
    def __init__(self, action, parent=None):
        super().__init__(parent)
        self.action = action
        self.setWindowTitle(f"Action Details - {action.action_id}")
        self.setMinimumSize(600, 500)
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the dialog UI."""
        layout = QVBoxLayout()
        
        # Basic info
        info_text = f"""
<h2>{self.action.title}</h2>
<p><b>Action ID:</b> {self.action.action_id}</p>
<p><b>Type:</b> {self.action.action_type}</p>
<p><b>Target:</b> {self.action.target}</p>
<p><b>Status:</b> {self.action.status}</p>
<p><b>Confidence:</b> {self.action.confidence:.2%}</p>
<p><b>Created:</b> {self.action.created_at}</p>
<p><b>Created By:</b> {self.action.created_by}</p>
<p><b>Requires Approval:</b> {'Yes' if self.action.requires_approval else 'No'}</p>
"""
        
        if self.action.approved_at:
            info_text += f"<p><b>Approved At:</b> {self.action.approved_at}</p>"
            info_text += f"<p><b>Approved By:</b> {self.action.approved_by}</p>"
        
        if self.action.rejection_reason:
            info_text += f"<p><b>Rejection Reason:</b> {self.action.rejection_reason}</p>"
        
        info_label = QLabel(info_text)
        info_label.setWordWrap(True)
        info_label.setTextFormat(Qt.TextFormat.RichText)
        layout.addWidget(info_label)
        
        # Description
        layout.addWidget(QLabel("<b>Description:</b>"))
        desc_text = QTextEdit()
        desc_text.setPlainText(self.action.description)
        desc_text.setReadOnly(True)
        desc_text.setMaximumHeight(80)
        layout.addWidget(desc_text)
        
        # Reason
        layout.addWidget(QLabel("<b>Reason:</b>"))
        reason_text = QTextEdit()
        reason_text.setPlainText(self.action.reason)
        reason_text.setReadOnly(True)
        reason_text.setMaximumHeight(100)
        layout.addWidget(reason_text)
        
        # Evidence
        if self.action.evidence:
            layout.addWidget(QLabel(f"<b>Evidence ({len(self.action.evidence)} items):</b>"))
            evidence_text = QTextEdit()
            evidence_text.setPlainText("\n".join(f"- {e}" for e in self.action.evidence))
            evidence_text.setReadOnly(True)
            evidence_text.setMaximumHeight(80)
            layout.addWidget(evidence_text)
        
        # Parameters
        if self.action.parameters:
            import json
            layout.addWidget(QLabel("<b>Parameters:</b>"))
            params_text = QTextEdit()
            params_text.setPlainText(json.dumps(self.action.parameters, indent=2))
            params_text.setReadOnly(True)
            params_text.setMaximumHeight(100)
            layout.addWidget(params_text)
        
        # Execution result (if executed)
        if self.action.execution_result:
            import json
            layout.addWidget(QLabel("<b>Execution Result:</b>"))
            result_text = QTextEdit()
            result_text.setPlainText(json.dumps(self.action.execution_result, indent=2))
            result_text.setReadOnly(True)
            result_text.setMaximumHeight(100)
            layout.addWidget(result_text)
        
        # Close button
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        self.setLayout(layout)


class ApprovalQueueWidget(QWidget):
    """Widget for managing approval queue of pending actions."""
    
    action_approved = pyqtSignal(str)  # action_id
    action_rejected = pyqtSignal(str)  # action_id
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.approval_service = None
        self.setup_ui()
        self.load_service()
        
        # Auto-refresh timer
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_actions)
        self.refresh_timer.start(5000)  # Refresh every 5 seconds
    
    def setup_ui(self):
        """Set up the widget UI."""
        layout = QVBoxLayout()
        
        # Title and controls
        header_layout = QHBoxLayout()
        
        title_label = QLabel("<h2>🚦 Approval Queue</h2>")
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        
        self.stats_label = QLabel()
        header_layout.addWidget(self.stats_label)
        
        # Force manual approval checkbox
        self.force_approval_checkbox = QCheckBox("Force Manual Approval for All Actions")
        self.force_approval_checkbox.setToolTip(
            "When checked, ALL actions will require manual approval, "
            "even those with confidence >= 90%"
        )
        self.force_approval_checkbox.stateChanged.connect(self.on_force_approval_changed)
        header_layout.addWidget(self.force_approval_checkbox)
        
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.clicked.connect(self.refresh_actions)
        header_layout.addWidget(refresh_btn)
        
        layout.addLayout(header_layout)
        
        # Info label (dynamic based on force approval setting)
        self.info_label = QLabel()
        self.info_label.setWordWrap(True)
        self._update_info_label()
        layout.addWidget(self.info_label)
        
        # Splitter for table and details
        splitter = QSplitter(Qt.Orientation.Vertical)
        
        # Actions table
        self.actions_table = QTableWidget()
        self.actions_table.setColumnCount(8)
        self.actions_table.setHorizontalHeaderLabels([
            "ID", "Type", "Target", "Confidence", "Status", 
            "Created", "Created By", "Actions"
        ])
        self.actions_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Interactive
        )
        # Make rows resizable too
        self.actions_table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.actions_table.verticalHeader().setVisible(True)
        self.actions_table.verticalHeader().setDefaultSectionSize(30)
        
        self.actions_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self.actions_table.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers
        )
        self.actions_table.itemSelectionChanged.connect(self.on_selection_changed)
        
        splitter.addWidget(self.actions_table)
        
        # Details panel
        details_widget = QWidget()
        details_layout = QVBoxLayout(details_widget)
        
        details_layout.addWidget(QLabel("<b>Action Details:</b>"))
        self.details_text = QTextEdit()
        self.details_text.setReadOnly(True)
        details_layout.addWidget(self.details_text)
        
        # Action buttons
        button_layout = QHBoxLayout()
        
        self.view_btn = QPushButton("👁️ View Full Details")
        self.view_btn.clicked.connect(self.view_action_details)
        self.view_btn.setEnabled(False)
        button_layout.addWidget(self.view_btn)
        
        self.approve_btn = QPushButton("✅ Approve")
        self.approve_btn.clicked.connect(self.approve_action)
        self.approve_btn.setEnabled(False)
        self.approve_btn.setStyleSheet("background-color: #4CAF50; color: white;")
        button_layout.addWidget(self.approve_btn)
        
        self.reject_btn = QPushButton("❌ Reject")
        self.reject_btn.clicked.connect(self.reject_action)
        self.reject_btn.setEnabled(False)
        self.reject_btn.setStyleSheet("background-color: #f44336; color: white;")
        button_layout.addWidget(self.reject_btn)
        
        button_layout.addStretch()
        details_layout.addLayout(button_layout)
        
        splitter.addWidget(details_widget)
        splitter.setSizes([400, 200])
        
        layout.addWidget(splitter)
        
        self.setLayout(layout)
    
    def load_service(self):
        """Load the approval service."""
        try:
            from services.approval_service import get_approval_service
            self.approval_service = get_approval_service()
            
            # Load current force approval setting
            force_approval = self.approval_service.get_force_manual_approval()
            self.force_approval_checkbox.setChecked(force_approval)
            
            self.refresh_actions()
        except Exception as e:
            logger.error(f"Error loading approval service: {e}")
            QMessageBox.warning(
                self,
                "Service Error",
                f"Could not load approval service: {e}"
            )
    
    def _update_info_label(self):
        """Update the info label based on current settings."""
        if not self.approval_service:
            self.info_label.setText("Pending actions requiring approval.")
            return
        
        force_approval = self.approval_service.get_force_manual_approval()
        
        if force_approval:
            self.info_label.setText(
                "⚠️ <b>Force Manual Approval Enabled:</b> ALL actions require manual approval, "
                "regardless of confidence score."
            )
            self.info_label.setStyleSheet("color: #FF9800; font-weight: bold;")
        else:
            self.info_label.setText(
                "Pending actions requiring approval. High-confidence actions (≥90%) are auto-approved."
            )
            self.info_label.setStyleSheet("")
    
    def on_force_approval_changed(self, state):
        """Handle force approval checkbox change."""
        if not self.approval_service:
            return
        
        try:
            force_approval = (state == Qt.CheckState.Checked.value)
            self.approval_service.set_force_manual_approval(force_approval)
            
            # Update info label
            self._update_info_label()
            
            status_text = "enabled" if force_approval else "disabled"
            QMessageBox.information(
                self,
                "Setting Updated",
                f"Force manual approval has been {status_text}.\n\n"
                f"{'All actions will now require manual approval, regardless of confidence score.' if force_approval else 'Actions with confidence >= 90% will be auto-approved.'}"
            )
            
            logger.info(f"Force manual approval {status_text}")
        except Exception as e:
            logger.error(f"Error updating force approval setting: {e}")
            QMessageBox.critical(
                self,
                "Error",
                f"Could not update setting: {e}"
            )
    
    def refresh_actions(self):
        """Refresh the actions table."""
        if not self.approval_service:
            return
        
        try:
            # Get all actions
            actions = self.approval_service.list_actions()
            
            # Update stats
            stats = self.approval_service.get_stats()
            self.stats_label.setText(
                f"Total: {stats['total']} | "
                f"Pending: {stats['pending']} | "
                f"Approved: {stats['approved']} | "
                f"Executed: {stats['executed']}"
            )
            
            # Update table
            self.actions_table.setRowCount(len(actions))
            
            for row, action in enumerate(actions):
                # ID
                id_item = QTableWidgetItem(action.action_id.split('-')[-1][:8])
                id_item.setData(Qt.ItemDataRole.UserRole, action)
                self.actions_table.setItem(row, 0, id_item)
                
                # Type
                type_item = QTableWidgetItem(action.action_type.replace('_', ' ').title())
                self.actions_table.setItem(row, 1, type_item)
                
                # Target
                target_item = QTableWidgetItem(action.target)
                self.actions_table.setItem(row, 2, target_item)
                
                # Confidence
                confidence_item = QTableWidgetItem(f"{action.confidence:.1%}")
                if action.confidence >= 0.90:
                    confidence_item.setBackground(QColor("#4CAF50"))
                elif action.confidence >= 0.85:
                    confidence_item.setBackground(QColor("#FFC107"))
                else:
                    confidence_item.setBackground(QColor("#FF9800"))
                self.actions_table.setItem(row, 3, confidence_item)
                
                # Status
                status_item = QTableWidgetItem(action.status.upper())
                if action.status == "pending":
                    status_item.setBackground(QColor("#FFC107"))
                elif action.status == "approved":
                    status_item.setBackground(QColor("#4CAF50"))
                elif action.status == "rejected":
                    status_item.setBackground(QColor("#f44336"))
                elif action.status == "executed":
                    status_item.setBackground(QColor("#2196F3"))
                self.actions_table.setItem(row, 4, status_item)
                
                # Created
                created_item = QTableWidgetItem(action.created_at.split('T')[0])
                self.actions_table.setItem(row, 5, created_item)
                
                # Created by
                created_by_item = QTableWidgetItem(action.created_by)
                self.actions_table.setItem(row, 6, created_by_item)
                
                # Actions (empty - actions in button row below)
                self.actions_table.setItem(row, 7, QTableWidgetItem(""))
            
            # Resize columns
            self.actions_table.resizeColumnsToContents()
        
        except Exception as e:
            logger.error(f"Error refreshing actions: {e}")
    
    def on_selection_changed(self):
        """Handle selection change."""
        selected_items = self.actions_table.selectedItems()
        if not selected_items:
            self.details_text.clear()
            self.approve_btn.setEnabled(False)
            self.reject_btn.setEnabled(False)
            self.view_btn.setEnabled(False)
            return
        
        # Get selected action
        action = selected_items[0].data(Qt.ItemDataRole.UserRole)
        if not action:
            return
        
        # Update details
        details = f"""
Title: {action.title}

Description:
{action.description}

Reason:
{action.reason}

Target: {action.target}
Type: {action.action_type}
Confidence: {action.confidence:.2%}
Status: {action.status}
Created: {action.created_at}
Created By: {action.created_by}
Requires Approval: {'Yes' if action.requires_approval else 'No'}

Evidence: {len(action.evidence)} items
"""
        if action.evidence:
            details += "\n" + "\n".join(f"  - {e}" for e in action.evidence[:5])
            if len(action.evidence) > 5:
                details += f"\n  ... and {len(action.evidence) - 5} more"
        
        self.details_text.setPlainText(details)
        
        # Enable/disable buttons
        self.view_btn.setEnabled(True)
        is_pending = action.status == "pending"
        self.approve_btn.setEnabled(is_pending)
        self.reject_btn.setEnabled(is_pending)
    
    def get_selected_action(self):
        """Get the currently selected action."""
        selected_items = self.actions_table.selectedItems()
        if not selected_items:
            return None
        return selected_items[0].data(Qt.ItemDataRole.UserRole)
    
    def view_action_details(self):
        """View full action details in a dialog."""
        action = self.get_selected_action()
        if not action:
            return
        
        dialog = ActionDetailDialog(action, self)
        dialog.exec()
    
    def approve_action(self):
        """Approve the selected action."""
        action = self.get_selected_action()
        if not action:
            return
        
        # Confirm
        reply = QMessageBox.question(
            self,
            "Approve Action",
            f"Are you sure you want to approve this action?\n\n"
            f"Type: {action.action_type}\n"
            f"Target: {action.target}\n"
            f"Confidence: {action.confidence:.2%}\n\n"
            f"This will allow the action to be executed.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.approval_service.approve_action(action.action_id, "analyst")
                self.action_approved.emit(action.action_id)
                QMessageBox.information(
                    self,
                    "Action Approved",
                    f"Action {action.action_id} has been approved."
                )
                self.refresh_actions()
            except Exception as e:
                logger.error(f"Error approving action: {e}")
                QMessageBox.critical(
                    self,
                    "Error",
                    f"Could not approve action: {e}"
                )
    
    def reject_action(self):
        """Reject the selected action."""
        action = self.get_selected_action()
        if not action:
            return
        
        # Get rejection reason
        from PyQt6.QtWidgets import QInputDialog
        reason, ok = QInputDialog.getMultiLineText(
            self,
            "Reject Action",
            f"Why are you rejecting this action?\n\n"
            f"Type: {action.action_type}\n"
            f"Target: {action.target}",
            ""
        )
        
        if ok and reason:
            try:
                self.approval_service.reject_action(action.action_id, reason, "analyst")
                self.action_rejected.emit(action.action_id)
                QMessageBox.information(
                    self,
                    "Action Rejected",
                    f"Action {action.action_id} has been rejected."
                )
                self.refresh_actions()
            except Exception as e:
                logger.error(f"Error rejecting action: {e}")
                QMessageBox.critical(
                    self,
                    "Error",
                    f"Could not reject action: {e}"
                )

