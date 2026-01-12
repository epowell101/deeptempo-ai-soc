"""Investigation Workflow widget for managing multi-phase investigations."""

from typing import Optional

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTextEdit, QDialog, QDialogButtonBox, QMessageBox,
    QListWidget, QListWidgetItem, QGroupBox, QProgressBar
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QColor
from ui.utils.auto_resize import ButtonSizePolicy
import logging

logger = logging.getLogger(__name__)


class PhaseWidget(QGroupBox):
    """Widget representing a single investigation phase."""
    
    def __init__(self, phase_name: str, phase_result, parent=None):
        super().__init__(phase_name.replace('_', ' ').title(), parent)
        self.phase_name = phase_name
        self.phase_result = phase_result
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the phase widget UI."""
        layout = QVBoxLayout()
        
        # Status indicator
        status = self.phase_result.status if self.phase_result else "not_started"
        status_colors = {
            "not_started": "#9E9E9E",
            "in_progress": "#FFC107",
            "completed": "#4CAF50",
            "skipped": "#757575"
        }
        
        status_label = QLabel(f"Status: {status.replace('_', ' ').title()}")
        status_label.setStyleSheet(
            f"background-color: {status_colors.get(status, '#9E9E9E')}; "
            f"color: white; padding: 5px; border-radius: 3px;"
        )
        layout.addWidget(status_label)
        
        # Timing info
        if self.phase_result and self.phase_result.started_at:
            layout.addWidget(QLabel(f"Started: {self.phase_result.started_at.split('T')[0]}"))
        if self.phase_result and self.phase_result.completed_at:
            layout.addWidget(QLabel(f"Completed: {self.phase_result.completed_at.split('T')[0]}"))
        
        # Findings count
        if self.phase_result and self.phase_result.findings:
            layout.addWidget(QLabel(f"Findings: {len(self.phase_result.findings)}"))
        
        # Notes preview
        if self.phase_result and self.phase_result.notes:
            notes_preview = self.phase_result.notes[:100]
            if len(self.phase_result.notes) > 100:
                notes_preview += "..."
            layout.addWidget(QLabel(f"Notes: {notes_preview}"))
        
        self.setLayout(layout)


class InvestigationWorkflowWidget(QWidget):
    """Widget for managing investigation workflows."""
    
    workflow_updated = pyqtSignal(str)  # workflow_id
    
    def __init__(self, case_id: Optional[str] = None, parent=None):
        super().__init__(parent)
        self.case_id = case_id
        self.workflow = None
        self.workflow_service = None
        self.setup_ui()
        self.load_service()
        
        # Auto-refresh timer
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_workflow)
        self.refresh_timer.start(10000)  # Refresh every 10 seconds
    
    def setup_ui(self):
        """Set up the widget UI."""
        layout = QVBoxLayout()
        
        # Header
        header_layout = QHBoxLayout()
        
        self.title_label = QLabel("<h2>🔬 Investigation Workflow</h2>")
        header_layout.addWidget(self.title_label)
        header_layout.addStretch()
        
        refresh_btn = QPushButton("🔄 Refresh")
        ButtonSizePolicy.make_compact(refresh_btn, min_width=100)
        refresh_btn.clicked.connect(self.refresh_workflow)
        header_layout.addWidget(refresh_btn)
        
        layout.addLayout(header_layout)
        
        # Workflow info
        self.info_label = QLabel("No active workflow")
        self.info_label.setWordWrap(True)
        layout.addWidget(self.info_label)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(5)  # 5 phases
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Current phase indicator
        self.current_phase_label = QLabel()
        self.current_phase_label.setStyleSheet(
            "background-color: #2196F3; color: white; padding: 10px; "
            "border-radius: 5px; font-weight: bold;"
        )
        self.current_phase_label.setVisible(False)
        layout.addWidget(self.current_phase_label)
        
        # Phases container
        self.phases_widget = QWidget()
        self.phases_layout = QHBoxLayout(self.phases_widget)
        layout.addWidget(self.phases_widget)
        
        # Context section
        context_group = QGroupBox("Investigation Context")
        context_layout = QVBoxLayout()
        
        # Entities
        context_layout.addWidget(QLabel("<b>Discovered Entities:</b>"))
        self.entities_list = QListWidget()
        self.entities_list.setMaximumHeight(100)
        context_layout.addWidget(self.entities_list)
        
        # Hypotheses
        context_layout.addWidget(QLabel("<b>Hypotheses:</b>"))
        self.hypotheses_list = QListWidget()
        self.hypotheses_list.setMaximumHeight(100)
        context_layout.addWidget(self.hypotheses_list)
        
        # Queries
        context_layout.addWidget(QLabel("<b>Queries Executed:</b>"))
        self.queries_list = QListWidget()
        self.queries_list.setMaximumHeight(100)
        context_layout.addWidget(self.queries_list)
        
        context_group.setLayout(context_layout)
        layout.addWidget(context_group)
        
        # Action buttons
        button_layout = QHBoxLayout()
        
        self.create_btn = QPushButton("➕ Create Workflow")
        ButtonSizePolicy.make_flexible(self.create_btn, min_width=140)
        self.create_btn.clicked.connect(self.create_workflow)
        button_layout.addWidget(self.create_btn)
        
        self.update_phase_btn = QPushButton("💾 Update Current Phase")
        ButtonSizePolicy.make_flexible(self.update_phase_btn, min_width=160)
        self.update_phase_btn.clicked.connect(self.update_current_phase)
        self.update_phase_btn.setEnabled(False)
        button_layout.addWidget(self.update_phase_btn)
        
        self.advance_btn = QPushButton("➡️ Advance to Next Phase")
        ButtonSizePolicy.make_flexible(self.advance_btn, min_width=160)
        self.advance_btn.clicked.connect(self.advance_phase)
        self.advance_btn.setEnabled(False)
        self.advance_btn.setStyleSheet("background-color: #4CAF50; color: white;")
        button_layout.addWidget(self.advance_btn)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def load_service(self):
        """Load the workflow service."""
        try:
            from services.investigation_workflow_service import get_workflow_service
            self.workflow_service = get_workflow_service()
            self.refresh_workflow()
        except Exception as e:
            logger.error(f"Error loading workflow service: {e}")
    
    def set_case_id(self, case_id: str):
        """Set the case ID and load associated workflow."""
        self.case_id = case_id
        self.refresh_workflow()
    
    def refresh_workflow(self):
        """Refresh the workflow display."""
        if not self.workflow_service or not self.case_id:
            return
        
        try:
            # Load workflow for case
            self.workflow = self.workflow_service.get_workflow_by_case(self.case_id)
            
            if not self.workflow:
                self.info_label.setText(
                    f"No active workflow for case {self.case_id}. Create one to track investigation progress."
                )
                self.progress_bar.setVisible(False)
                self.current_phase_label.setVisible(False)
                self.create_btn.setEnabled(True)
                self.update_phase_btn.setEnabled(False)
                self.advance_btn.setEnabled(False)
                
                # Clear phases
                for i in reversed(range(self.phases_layout.count())):
                    self.phases_layout.itemAt(i).widget().setParent(None)
                
                # Clear context
                self.entities_list.clear()
                self.hypotheses_list.clear()
                self.queries_list.clear()
                return
            
            # Update info
            self.info_label.setText(
                f"<b>{self.workflow.title}</b><br/>"
                f"Status: {self.workflow.status.title()} | "
                f"Priority: {self.workflow.priority.title()}<br/>"
                f"Created: {self.workflow.created_at.split('T')[0]}"
            )
            
            # Update progress bar
            phase_order = ["initialize", "gather_context", "analyze", "correlate", "report"]
            try:
                current_index = phase_order.index(self.workflow.current_phase)
                self.progress_bar.setValue(current_index + 1)
                self.progress_bar.setVisible(True)
            except ValueError:
                self.progress_bar.setVisible(False)
            
            # Update current phase indicator
            self.current_phase_label.setText(
                f"Current Phase: {self.workflow.current_phase.replace('_', ' ').title()}"
            )
            self.current_phase_label.setVisible(True)
            
            # Update phases
            for i in reversed(range(self.phases_layout.count())):
                self.phases_layout.itemAt(i).widget().setParent(None)
            
            for phase_name in phase_order:
                phase_result = self.workflow.phases.get(phase_name)
                phase_widget = PhaseWidget(phase_name, phase_result)
                self.phases_layout.addWidget(phase_widget)
            
            # Update context
            self.entities_list.clear()
            for entity_type, entities in self.workflow.entities_discovered.items():
                for entity in entities:
                    item = QListWidgetItem(f"{entity_type}: {entity}")
                    self.entities_list.addItem(item)
            
            self.hypotheses_list.clear()
            for hypothesis in self.workflow.hypotheses:
                item = QListWidgetItem(
                    f"{hypothesis['hypothesis'][:50]}... "
                    f"(confidence: {hypothesis['confidence']:.0%})"
                )
                self.hypotheses_list.addItem(item)
            
            self.queries_list.clear()
            for query in self.workflow.queries_executed[-10:]:  # Last 10
                item = QListWidgetItem(
                    f"{query['type']}: {query['query'][:40]}... "
                    f"({query['results_count']} results)"
                )
                self.queries_list.addItem(item)
            
            # Enable buttons
            self.create_btn.setEnabled(False)
            is_active = self.workflow.status == "active"
            self.update_phase_btn.setEnabled(is_active)
            self.advance_btn.setEnabled(is_active)
        
        except Exception as e:
            logger.error(f"Error refreshing workflow: {e}")
    
    def create_workflow(self):
        """Create a new workflow for the case."""
        if not self.case_id:
            QMessageBox.warning(
                self,
                "No Case Selected",
                "Please select a case first."
            )
            return
        
        # Get workflow details
        from PyQt6.QtWidgets import QInputDialog
        
        title, ok = QInputDialog.getText(
            self,
            "Create Workflow",
            "Investigation Title:",
            text=f"Investigation for Case {self.case_id}"
        )
        
        if not ok or not title:
            return
        
        description, ok = QInputDialog.getMultiLineText(
            self,
            "Create Workflow",
            "Investigation Description:",
            ""
        )
        
        if not ok:
            return
        
        try:
            self.workflow = self.workflow_service.create_workflow(
                case_id=self.case_id,
                title=title,
                description=description or "Investigation workflow"
            )
            
            QMessageBox.information(
                self,
                "Workflow Created",
                f"Investigation workflow created: {self.workflow.workflow_id}"
            )
            
            self.refresh_workflow()
            self.workflow_updated.emit(self.workflow.workflow_id)
        
        except Exception as e:
            logger.error(f"Error creating workflow: {e}")
            QMessageBox.critical(
                self,
                "Error",
                f"Could not create workflow: {e}"
            )
    
    def update_current_phase(self):
        """Update the current phase with notes."""
        if not self.workflow:
            return
        
        from PyQt6.QtWidgets import QInputDialog
        
        notes, ok = QInputDialog.getMultiLineText(
            self,
            "Update Phase",
            f"Add notes for phase: {self.workflow.current_phase.replace('_', ' ').title()}",
            ""
        )
        
        if ok and notes:
            try:
                from services.investigation_workflow_service import InvestigationPhase
                phase = InvestigationPhase(self.workflow.current_phase)
                
                self.workflow_service.update_phase(
                    self.workflow.workflow_id,
                    phase,
                    notes=notes
                )
                
                QMessageBox.information(
                    self,
                    "Phase Updated",
                    "Phase notes have been saved."
                )
                
                self.refresh_workflow()
                self.workflow_updated.emit(self.workflow.workflow_id)
            
            except Exception as e:
                logger.error(f"Error updating phase: {e}")
                QMessageBox.critical(
                    self,
                    "Error",
                    f"Could not update phase: {e}"
                )
    
    def advance_phase(self):
        """Advance to the next investigation phase."""
        if not self.workflow:
            return
        
        from PyQt6.QtWidgets import QInputDialog
        
        reply = QMessageBox.question(
            self,
            "Advance Phase",
            f"Complete phase: {self.workflow.current_phase.replace('_', ' ').title()}\n\n"
            f"This will mark the current phase as complete and move to the next phase.\n\n"
            f"Add completion notes?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel
        )
        
        if reply == QMessageBox.StandardButton.Cancel:
            return
        
        notes = ""
        if reply == QMessageBox.StandardButton.Yes:
            notes, ok = QInputDialog.getMultiLineText(
                self,
                "Completion Notes",
                f"Notes for completed phase: {self.workflow.current_phase.replace('_', ' ').title()}",
                ""
            )
            if not ok:
                return
        
        try:
            self.workflow_service.advance_phase(
                self.workflow.workflow_id,
                notes=notes
            )
            
            QMessageBox.information(
                self,
                "Phase Advanced",
                "Investigation has advanced to the next phase."
            )
            
            self.refresh_workflow()
            self.workflow_updated.emit(self.workflow.workflow_id)
        
        except Exception as e:
            logger.error(f"Error advancing phase: {e}")
            QMessageBox.critical(
                self,
                "Error",
                f"Could not advance phase: {e}"
            )
