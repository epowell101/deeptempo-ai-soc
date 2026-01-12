"""Tabbed investigations manager - multiple isolated investigation workspaces."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTabWidget,
    QInputDialog, QMessageBox, QMenu
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QAction
from datetime import datetime
from typing import Dict

from ui.widgets.investigation_tab import InvestigationTab


class TabbedInvestigations(QWidget):
    """
    Manager widget for multiple investigation tabs.
    Each tab is completely isolated with its own:
    - Chat history
    - Findings context  
    - Investigation state
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.investigation_tabs: Dict[str, InvestigationTab] = {}
        self.tab_counter = 0
        
        self._setup_ui()
        
        # Create initial tab
        self._create_new_tab("Initial Investigation")
    
    def _setup_ui(self):
        """Set up the UI."""
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Toolbar
        toolbar = QHBoxLayout()
        toolbar.setContentsMargins(5, 5, 5, 5)
        
        new_tab_btn = QPushButton("+ New Investigation")
        new_tab_btn.setStyleSheet(
            "background-color: #4CAF50; color: white; font-weight: bold; padding: 5px 15px;"
        )
        new_tab_btn.clicked.connect(self._prompt_new_tab)
        toolbar.addWidget(new_tab_btn)
        
        close_tab_btn = QPushButton("Close Current")
        close_tab_btn.clicked.connect(self._close_current_tab)
        toolbar.addWidget(close_tab_btn)
        
        toolbar.addStretch()
        
        # Info label
        self.info_label = QPushButton("ℹ️ About Tabbed Investigations")
        self.info_label.setFlat(True)
        self.info_label.clicked.connect(self._show_info)
        toolbar.addWidget(self.info_label)
        
        layout.addLayout(toolbar)
        
        # Tab widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.setMovable(True)
        self.tab_widget.setDocumentMode(True)
        self.tab_widget.tabCloseRequested.connect(self._close_tab_by_index)
        self.tab_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tab_widget.customContextMenuRequested.connect(self._show_tab_context_menu)
        
        layout.addWidget(self.tab_widget, 1)
        
        self.setLayout(layout)
    
    def _prompt_new_tab(self):
        """Prompt user for new investigation name."""
        name, ok = QInputDialog.getText(
            self,
            "New Investigation",
            "Investigation Name:",
            text=f"Investigation {self.tab_counter + 1}"
        )
        
        if ok and name:
            self._create_new_tab(name)
    
    def _create_new_tab(self, title: str = None) -> InvestigationTab:
        """Create a new investigation tab."""
        self.tab_counter += 1
        tab_id = f"inv_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{self.tab_counter}"
        
        if title is None:
            title = f"Investigation {self.tab_counter}"
        
        # Create new investigation tab with isolated context
        inv_tab = InvestigationTab(tab_id=tab_id, title=title)
        inv_tab.tab_title_changed.connect(
            lambda new_title, tid=tab_id: self._update_tab_title(tid, new_title)
        )
        
        # Add to tab widget
        index = self.tab_widget.addTab(inv_tab, title)
        self.tab_widget.setCurrentIndex(index)
        
        # Store reference
        self.investigation_tabs[tab_id] = inv_tab
        
        return inv_tab
    
    def _close_current_tab(self):
        """Close the current tab."""
        current_index = self.tab_widget.currentIndex()
        if current_index >= 0:
            self._close_tab_by_index(current_index)
    
    def _close_tab_by_index(self, index: int):
        """Close tab by index."""
        if self.tab_widget.count() <= 1:
            QMessageBox.information(
                self,
                "Cannot Close",
                "You must have at least one investigation tab open."
            )
            return
        
        widget = self.tab_widget.widget(index)
        tab_title = self.tab_widget.tabText(index)
        
        # Confirm close if there's activity
        if isinstance(widget, InvestigationTab):
            if widget.conversation_history or widget.focused_findings:
                reply = QMessageBox.question(
                    self,
                    "Close Investigation",
                    f"Close '{tab_title}'?\n\n"
                    f"This investigation has {len(widget.conversation_history)} messages "
                    f"and {len(widget.focused_findings)} findings.\n\n"
                    f"Consider exporting the chat history before closing.",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No
                )
                
                if reply != QMessageBox.StandardButton.Yes:
                    return
            
            # Remove from tracking
            if widget.tab_id in self.investigation_tabs:
                del self.investigation_tabs[widget.tab_id]
        
        # Remove tab
        self.tab_widget.removeTab(index)
    
    def _update_tab_title(self, tab_id: str, new_title: str):
        """Update tab title when investigation is renamed."""
        if tab_id in self.investigation_tabs:
            inv_tab = self.investigation_tabs[tab_id]
            for i in range(self.tab_widget.count()):
                if self.tab_widget.widget(i) == inv_tab:
                    self.tab_widget.setTabText(i, new_title)
                    break
    
    def _show_tab_context_menu(self, position):
        """Show context menu for tabs."""
        tab_bar = self.tab_widget.tabBar()
        index = tab_bar.tabAt(position)
        
        if index < 0:
            return
        
        menu = QMenu(self)
        
        rename_action = QAction("Rename", self)
        rename_action.triggered.connect(lambda: self._rename_tab_at_index(index))
        menu.addAction(rename_action)
        
        duplicate_action = QAction("Duplicate", self)
        duplicate_action.triggered.connect(lambda: self._duplicate_tab_at_index(index))
        menu.addAction(duplicate_action)
        
        menu.addSeparator()
        
        export_action = QAction("Export Chat", self)
        export_action.triggered.connect(lambda: self._export_tab_at_index(index))
        menu.addAction(export_action)
        
        menu.addSeparator()
        
        close_action = QAction("Close", self)
        close_action.triggered.connect(lambda: self._close_tab_by_index(index))
        menu.addAction(close_action)
        
        close_others_action = QAction("Close Others", self)
        close_others_action.triggered.connect(lambda: self._close_other_tabs(index))
        menu.addAction(close_others_action)
        
        menu.exec(tab_bar.mapToGlobal(position))
    
    def _rename_tab_at_index(self, index: int):
        """Rename tab at index."""
        widget = self.tab_widget.widget(index)
        if isinstance(widget, InvestigationTab):
            widget._rename_tab()
    
    def _duplicate_tab_at_index(self, index: int):
        """Duplicate tab at index (copies findings, not chat history)."""
        widget = self.tab_widget.widget(index)
        if isinstance(widget, InvestigationTab):
            new_title = f"{widget.title} (Copy)"
            new_tab = self._create_new_tab(new_title)
            
            # Copy focused findings
            for finding in widget.focused_findings:
                new_tab.add_finding_object(finding)
            
            # Copy notes
            new_tab.notes_edit.setPlainText(widget.notes_edit.toPlainText())
            
            QMessageBox.information(
                self,
                "Duplicated",
                f"Created duplicate investigation: {new_title}\n\n"
                "Findings and notes copied. Chat history is fresh."
            )
    
    def _export_tab_at_index(self, index: int):
        """Export chat from tab at index."""
        widget = self.tab_widget.widget(index)
        if isinstance(widget, InvestigationTab):
            widget._export_chat()
    
    def _close_other_tabs(self, keep_index: int):
        """Close all tabs except the one at keep_index."""
        reply = QMessageBox.question(
            self,
            "Close Other Tabs",
            "Close all other investigation tabs?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        # Close tabs in reverse order to maintain indices
        indices_to_close = []
        for i in range(self.tab_widget.count()):
            if i != keep_index:
                indices_to_close.append(i)
        
        for i in reversed(indices_to_close):
            widget = self.tab_widget.widget(i)
            if isinstance(widget, InvestigationTab):
                if widget.tab_id in self.investigation_tabs:
                    del self.investigation_tabs[widget.tab_id]
            self.tab_widget.removeTab(i)
    
    def _show_info(self):
        """Show information about tabbed investigations."""
        QMessageBox.information(
            self,
            "Tabbed Investigations",
            "<h3>About Tabbed Investigations</h3>"
            "<p>Each investigation tab is completely isolated:</p>"
            "<ul>"
            "<li><b>Separate Chat History:</b> Each tab has its own conversation with Claude</li>"
            "<li><b>Focused Findings:</b> Add specific findings to analyze in each tab</li>"
            "<li><b>Investigation Notes:</b> Track notes per investigation</li>"
            "<li><b>No Context Mixing:</b> Chats in different tabs don't interfere</li>"
            "</ul>"
            "<p><b>Use Cases:</b></p>"
            "<ul>"
            "<li>Analyze multiple unrelated events simultaneously</li>"
            "<li>Compare different hypotheses in separate tabs</li>"
            "<li>Work on multiple cases without mixing context</li>"
            "<li>Collaborate with different SOC agents per investigation</li>"
            "</ul>"
            "<p><b>Tips:</b></p>"
            "<ul>"
            "<li>Right-click tabs for more options</li>"
            "<li>Export chat history before closing important investigations</li>"
            "<li>Duplicate tabs to explore different analysis approaches</li>"
            "</ul>"
        )
    
    def create_tab_for_finding(self, finding: dict):
        """Create a new tab focused on a specific finding."""
        finding_id = finding.get('finding_id', 'Unknown')
        title = f"Investigation: {finding_id[:20]}"
        
        new_tab = self._create_new_tab(title)
        new_tab.add_finding_object(finding)
        
        return new_tab
    
    def get_current_tab(self) -> InvestigationTab:
        """Get the currently active investigation tab."""
        current_widget = self.tab_widget.currentWidget()
        if isinstance(current_widget, InvestigationTab):
            return current_widget
        return None

