"""Agent selector widget for choosing SOC agents."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QButtonGroup, QRadioButton, QTextEdit
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from services.soc_agents import AgentManager, AgentProfile


class AgentCard(QFrame):
    """Card widget for displaying an agent."""
    
    clicked = pyqtSignal(str)  # Emits agent_id
    
    def __init__(self, agent_info: dict, is_selected: bool = False, parent=None):
        super().__init__(parent)
        self.agent_id = agent_info["id"]
        self.is_selected = is_selected
        self.agent_info = agent_info
        
        self._setup_ui()
        self._update_style()
    
    def _setup_ui(self):
        """Set up the card UI."""
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(5)
        
        # Icon and name row
        header_layout = QHBoxLayout()
        
        # Icon label
        icon_label = QLabel(self.agent_info["icon"])
        icon_font = QFont()
        icon_font.setPointSize(24)
        icon_label.setFont(icon_font)
        header_layout.addWidget(icon_label)
        
        # Name label
        name_label = QLabel(self.agent_info["name"])
        name_font = QFont()
        name_font.setPointSize(12)
        name_font.setBold(True)
        name_label.setFont(name_font)
        header_layout.addWidget(name_label)
        header_layout.addStretch()
        
        layout.addLayout(header_layout)
        
        # Specialization
        spec_label = QLabel(self.agent_info["specialization"])
        spec_label.setWordWrap(True)
        spec_font = QFont()
        spec_font.setPointSize(9)
        spec_font.setItalic(True)
        spec_label.setFont(spec_font)
        spec_label.setStyleSheet("color: #888;")
        layout.addWidget(spec_label)
        
        # Description
        desc_label = QLabel(self.agent_info["description"])
        desc_label.setWordWrap(True)
        desc_font = QFont()
        desc_font.setPointSize(9)
        desc_label.setFont(desc_font)
        layout.addWidget(desc_label)
        
        self.setLayout(layout)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(120)
    
    def _update_style(self):
        """Update card style based on selection state."""
        if self.is_selected:
            self.setStyleSheet(f"""
                AgentCard {{
                    background-color: {self.agent_info['color']};
                    border: 2px solid #4a9eff;
                    border-radius: 8px;
                    color: #000;
                }}
            """)
        else:
            self.setStyleSheet(f"""
                AgentCard {{
                    background-color: #2a2a2a;
                    border: 1px solid #444;
                    border-radius: 8px;
                }}
                AgentCard:hover {{
                    background-color: #333;
                    border: 1px solid #666;
                }}
            """)
    
    def set_selected(self, selected: bool):
        """Set selection state."""
        self.is_selected = selected
        self._update_style()
    
    def mousePressEvent(self, event):
        """Handle mouse press."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.agent_id)
        super().mousePressEvent(event)


class AgentSelector(QWidget):
    """Widget for selecting SOC agents."""
    
    agent_changed = pyqtSignal(str, AgentProfile)  # Emits (agent_id, agent_profile)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.agent_manager = AgentManager()
        self.agent_cards = {}
        
        self._setup_ui()
        self._load_agents()
    
    def _setup_ui(self):
        """Set up the UI."""
        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(10)
        
        # Header
        header_layout = QHBoxLayout()
        
        title = QLabel("🤖 SOC AI Agents")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Quick select button
        quick_btn = QPushButton("Auto-Select")
        quick_btn.setToolTip("Automatically select agent based on your query")
        quick_btn.clicked.connect(self._show_quick_select)
        quick_btn.setMaximumWidth(100)
        header_layout.addWidget(quick_btn)
        
        layout.addLayout(header_layout)
        
        # Current agent display
        self.current_agent_label = QLabel()
        self.current_agent_label.setWordWrap(True)
        self.current_agent_label.setStyleSheet("""
            QLabel {
                background-color: #1a1a1a;
                border: 1px solid #444;
                border-radius: 5px;
                padding: 8px;
            }
        """)
        layout.addWidget(self.current_agent_label)
        
        # Scroll area for agent cards
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        # Container for agent cards
        scroll_widget = QWidget()
        self.cards_layout = QVBoxLayout()
        self.cards_layout.setSpacing(8)
        scroll_widget.setLayout(self.cards_layout)
        scroll.setWidget(scroll_widget)
        
        layout.addWidget(scroll, 1)
        
        self.setLayout(layout)
    
    def _load_agents(self):
        """Load all agents into the UI."""
        agents = self.agent_manager.get_agent_list()
        current_agent_id = self.agent_manager.current_agent_id
        
        for agent_info in agents:
            is_selected = agent_info["id"] == current_agent_id
            card = AgentCard(agent_info, is_selected)
            card.clicked.connect(self._on_agent_selected)
            
            self.agent_cards[agent_info["id"]] = card
            self.cards_layout.addWidget(card)
        
        # Add stretch at the end
        self.cards_layout.addStretch()
        
        # Update current agent display
        self._update_current_agent_display()
    
    def _on_agent_selected(self, agent_id: str):
        """Handle agent selection."""
        # Update selection state in cards
        for aid, card in self.agent_cards.items():
            card.set_selected(aid == agent_id)
        
        # Update agent manager
        self.agent_manager.set_current_agent(agent_id)
        
        # Update display
        self._update_current_agent_display()
        
        # Emit signal
        agent_profile = self.agent_manager.get_current_agent()
        self.agent_changed.emit(agent_id, agent_profile)
    
    def _update_current_agent_display(self):
        """Update the current agent display."""
        agent = self.agent_manager.get_current_agent()
        self.current_agent_label.setText(
            f"<b>{agent.icon} Active Agent:</b> {agent.name}<br>"
            f"<i>{agent.specialization}</i>"
        )
    
    def _show_quick_select(self):
        """Show quick select dialog (placeholder for now)."""
        # This could open a dialog asking "What do you want to do?"
        # and auto-select the best agent
        from PyQt6.QtWidgets import QInputDialog
        
        text, ok = QInputDialog.getText(
            self,
            "Auto-Select Agent",
            "What do you want to do?\n(e.g., 'triage alerts', 'investigate incident', 'hunt for threats')"
        )
        
        if ok and text:
            recommended_agent = self.agent_manager.get_agent_by_task(text)
            if recommended_agent:
                self._on_agent_selected(recommended_agent.id)
    
    def get_current_agent(self) -> AgentProfile:
        """Get the currently selected agent."""
        return self.agent_manager.get_current_agent()
    
    def set_current_agent(self, agent_id: str):
        """Programmatically set the current agent."""
        if agent_id in self.agent_cards:
            self._on_agent_selected(agent_id)


class CompactAgentSelector(QWidget):
    """Compact agent selector for embedding in chat interface."""
    
    agent_changed = pyqtSignal(str, AgentProfile)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.agent_manager = AgentManager()
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up compact UI."""
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        
        # Label
        label = QLabel("Agent:")
        label.setStyleSheet("font-size: 10px;")
        layout.addWidget(label)
        
        # Agent dropdown (implemented as buttons for visual appeal)
        from PyQt6.QtWidgets import QComboBox
        
        self.agent_combo = QComboBox()
        self.agent_combo.setStyleSheet("font-size: 10px;")
        
        # Populate with agents
        agents = self.agent_manager.get_agent_list()
        for agent in agents:
            self.agent_combo.addItem(
                f"{agent['icon']} {agent['name']}",
                agent['id']
            )
        
        # Set current agent
        current_idx = next(
            (i for i, agent in enumerate(agents) 
             if agent['id'] == self.agent_manager.current_agent_id),
            0
        )
        self.agent_combo.setCurrentIndex(current_idx)
        self.agent_combo.currentIndexChanged.connect(self._on_agent_changed)
        
        layout.addWidget(self.agent_combo, 1)
        
        # Info button
        info_btn = QPushButton("ℹ️")
        info_btn.setMaximumWidth(25)
        info_btn.setMaximumHeight(20)
        info_btn.setStyleSheet("font-size: 10px; padding: 2px;")
        info_btn.setToolTip("Show agent details")
        info_btn.clicked.connect(self._show_agent_info)
        layout.addWidget(info_btn)
        
        self.setLayout(layout)
    
    def _on_agent_changed(self, index: int):
        """Handle agent selection change."""
        agent_id = self.agent_combo.itemData(index)
        self.agent_manager.set_current_agent(agent_id)
        agent_profile = self.agent_manager.get_current_agent()
        self.agent_changed.emit(agent_id, agent_profile)
    
    def _show_agent_info(self):
        """Show current agent information."""
        agent = self.agent_manager.get_current_agent()
        
        from PyQt6.QtWidgets import QMessageBox
        msg = QMessageBox(self)
        msg.setWindowTitle(f"{agent.icon} {agent.name}")
        msg.setText(f"<b>{agent.specialization}</b>")
        msg.setInformativeText(
            f"{agent.description}\n\n"
            f"<b>Recommended Tools:</b> {', '.join(agent.recommended_tools)}\n"
            f"<b>Thinking Enabled:</b> {'Yes' if agent.enable_thinking else 'No'}"
        )
        msg.setIcon(QMessageBox.Icon.Information)
        msg.exec()
    
    def get_current_agent(self) -> AgentProfile:
        """Get currently selected agent."""
        return self.agent_manager.get_current_agent()
    
    def set_current_agent(self, agent_id: str):
        """Set current agent."""
        agents = self.agent_manager.get_agent_list()
        idx = next(
            (i for i, agent in enumerate(agents) if agent['id'] == agent_id),
            -1
        )
        if idx >= 0:
            self.agent_combo.setCurrentIndex(idx)

