"""Full agent panel for SOC operations."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QGroupBox, QScrollArea, QFrame, QSplitter
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from services.soc_agents import AgentManager
from ui.widgets.agent_selector import AgentCard


class AgentDetailPanel(QWidget):
    """Detailed view of an agent."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the UI."""
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Agent header
        self.header_label = QLabel()
        header_font = QFont()
        header_font.setPointSize(16)
        header_font.setBold(True)
        self.header_label.setFont(header_font)
        layout.addWidget(self.header_label)
        
        # Specialization
        self.spec_label = QLabel()
        spec_font = QFont()
        spec_font.setPointSize(11)
        spec_font.setItalic(True)
        self.spec_label.setFont(spec_font)
        self.spec_label.setStyleSheet("color: #888;")
        layout.addWidget(self.spec_label)
        
        # Description
        self.desc_label = QLabel()
        self.desc_label.setWordWrap(True)
        layout.addWidget(self.desc_label)
        
        # System prompt section
        prompt_group = QGroupBox("System Prompt")
        prompt_layout = QVBoxLayout()
        
        self.prompt_text = QTextEdit()
        self.prompt_text.setReadOnly(True)
        self.prompt_text.setMaximumHeight(200)
        prompt_layout.addWidget(self.prompt_text)
        
        prompt_group.setLayout(prompt_layout)
        layout.addWidget(prompt_group)
        
        # Capabilities section
        caps_group = QGroupBox("Capabilities")
        caps_layout = QVBoxLayout()
        
        self.caps_label = QLabel()
        self.caps_label.setWordWrap(True)
        caps_layout.addWidget(self.caps_label)
        
        caps_group.setLayout(caps_layout)
        layout.addWidget(caps_group)
        
        # Recommended tools
        tools_group = QGroupBox("Recommended Tools")
        tools_layout = QVBoxLayout()
        
        self.tools_label = QLabel()
        self.tools_label.setWordWrap(True)
        tools_layout.addWidget(self.tools_label)
        
        tools_group.setLayout(tools_layout)
        layout.addWidget(tools_group)
        
        layout.addStretch()
        
        self.setLayout(layout)
    
    def show_agent(self, agent_profile):
        """Display agent details."""
        self.header_label.setText(f"{agent_profile.icon} {agent_profile.name}")
        self.spec_label.setText(agent_profile.specialization)
        self.desc_label.setText(agent_profile.description)
        self.prompt_text.setPlainText(agent_profile.system_prompt)
        
        # Capabilities
        caps_text = f"<b>Max Tokens:</b> {agent_profile.max_tokens:,}<br>"
        caps_text += f"<b>Extended Thinking:</b> {'Enabled' if agent_profile.enable_thinking else 'Disabled'}<br>"
        caps_text += f"<b>Color Theme:</b> <span style='background-color: {agent_profile.color}; padding: 2px 8px; border-radius: 3px;'>{agent_profile.color}</span>"
        self.caps_label.setText(caps_text)
        
        # Tools
        tools_text = ", ".join(agent_profile.recommended_tools)
        self.tools_label.setText(tools_text)


class AgentPanel(QWidget):
    """Full agent management panel."""
    
    agent_selected = pyqtSignal(str)  # Emits agent_id
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.agent_manager = AgentManager()
        self.agent_cards = {}
        
        self._setup_ui()
        self._load_agents()
    
    def _setup_ui(self):
        """Set up the UI."""
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Create splitter for list and details
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left side - agent list
        left_widget = QWidget()
        left_layout = QVBoxLayout()
        left_layout.setContentsMargins(5, 5, 5, 5)
        
        # Header
        header = QLabel("🤖 Available Agents")
        header_font = QFont()
        header_font.setPointSize(14)
        header_font.setBold(True)
        header.setFont(header_font)
        left_layout.addWidget(header)
        
        # Search/filter (placeholder)
        filter_layout = QHBoxLayout()
        from PyQt6.QtWidgets import QLineEdit
        self.filter_edit = QLineEdit()
        self.filter_edit.setPlaceholderText("Search agents...")
        self.filter_edit.textChanged.connect(self._filter_agents)
        filter_layout.addWidget(self.filter_edit)
        left_layout.addLayout(filter_layout)
        
        # Scroll area for agents
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        scroll_widget = QWidget()
        self.cards_layout = QVBoxLayout()
        self.cards_layout.setSpacing(8)
        scroll_widget.setLayout(self.cards_layout)
        scroll.setWidget(scroll_widget)
        
        left_layout.addWidget(scroll, 1)
        left_widget.setLayout(left_layout)
        
        # Right side - agent details
        self.detail_panel = AgentDetailPanel()
        
        # Add to splitter
        splitter.addWidget(left_widget)
        splitter.addWidget(self.detail_panel)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        
        layout.addWidget(splitter)
        self.setLayout(layout)
    
    def _load_agents(self):
        """Load all agents."""
        agents = self.agent_manager.get_agent_list()
        current_agent_id = self.agent_manager.current_agent_id
        
        for agent_info in agents:
            is_selected = agent_info["id"] == current_agent_id
            card = AgentCard(agent_info, is_selected)
            card.clicked.connect(self._on_agent_clicked)
            
            self.agent_cards[agent_info["id"]] = card
            self.cards_layout.addWidget(card)
        
        self.cards_layout.addStretch()
        
        # Show initial agent details
        if current_agent_id:
            agent_profile = self.agent_manager.get_current_agent()
            self.detail_panel.show_agent(agent_profile)
    
    def _on_agent_clicked(self, agent_id: str):
        """Handle agent card click."""
        # Update selection
        for aid, card in self.agent_cards.items():
            card.set_selected(aid == agent_id)
        
        # Update agent manager
        self.agent_manager.set_current_agent(agent_id)
        
        # Show details
        agent_profile = self.agent_manager.get_current_agent()
        self.detail_panel.show_agent(agent_profile)
        
        # Emit signal
        self.agent_selected.emit(agent_id)
    
    def _filter_agents(self, text: str):
        """Filter agents by search text."""
        text_lower = text.lower()
        
        for agent_id, card in self.agent_cards.items():
            agent_info = card.agent_info
            matches = (
                text_lower in agent_info["name"].lower() or
                text_lower in agent_info["description"].lower() or
                text_lower in agent_info["specialization"].lower()
            )
            card.setVisible(matches)
    
    def get_current_agent_id(self) -> str:
        """Get current agent ID."""
        return self.agent_manager.current_agent_id

