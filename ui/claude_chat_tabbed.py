"""Claude chat interface with tabbed conversations for isolated investigations."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton, QLineEdit,
    QLabel, QComboBox, QMessageBox, QGroupBox, QFormLayout, QInputDialog,
    QCheckBox, QSpinBox, QFileDialog, QListWidget, QListWidgetItem, QProgressBar,
    QTabWidget, QMenu
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QKeyEvent, QAction
import asyncio
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

from services.claude_service import ClaudeService
from services.claude_factory import create_claude_service
from services.data_service import DataService
from services.soc_agents import AgentManager
from ui.widgets.agent_selector import CompactAgentSelector


class ClaudeChatWorker(QThread):
    """Worker thread for Claude API calls."""
    
    response_chunk = pyqtSignal(str)
    finished = pyqtSignal(str)
    error = pyqtSignal(str)
    
    def __init__(self, service: ClaudeService, message: str, system_prompt: str = None,
                 context: list = None, use_streaming: bool = True, images: list = None,
                 enable_thinking: bool = False, thinking_budget: int = 10000, max_tokens: int = 4096):
        super().__init__()
        self.service = service
        self.message = message
        self.system_prompt = system_prompt
        self.context = context or []
        self.use_streaming = use_streaming
        self.images = images or []
        self.enable_thinking = enable_thinking
        self.thinking_budget = thinking_budget
        self.max_tokens = max_tokens
    
    def run(self):
        """Run the chat request."""
        try:
            if self.use_streaming:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                async def stream_chat():
                    full_response = ""
                    async for chunk in self.service.chat_stream(
                        self.message,
                        system_prompt=self.system_prompt,
                        context=self.context,
                        images=self.images if self.images else None,
                        enable_thinking=self.enable_thinking,
                        thinking_budget=self.thinking_budget,
                        max_tokens=self.max_tokens
                    ):
                        self.response_chunk.emit(chunk)
                        full_response += chunk
                    self.finished.emit(full_response)
                
                loop.run_until_complete(stream_chat())
                loop.close()
            else:
                response = self.service.chat(
                    self.message,
                    system_prompt=self.system_prompt,
                    context=self.context,
                    images=self.images if self.images else None,
                    enable_thinking=self.enable_thinking,
                    thinking_budget=self.thinking_budget,
                    max_tokens=self.max_tokens
                )
                self.finished.emit(response or "")
        
        except Exception as e:
            self.error.emit(str(e))


class ScrollableTextEdit(QTextEdit):
    """Custom QTextEdit with proper scrolling."""
    
    def append(self, text: str):
        """Override append to ensure proper scrolling."""
        super().append(text)
        self._scroll_to_bottom()
    
    def _scroll_to_bottom(self):
        """Force scroll to bottom."""
        scrollbar = self.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        cursor = self.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.setTextCursor(cursor)
        self.ensureCursorVisible()


class ChatTab(QWidget):
    """Individual chat tab with isolated conversation history."""
    
    def __init__(self, tab_id: str, title: str, claude_service: ClaudeService, 
                 data_service: DataService, agent_manager: AgentManager, 
                 finding: Optional[Dict] = None, parent=None):
        super().__init__(parent)
        self.tab_id = tab_id
        self.title = title
        self.claude_service = claude_service
        self.data_service = data_service
        self.agent_manager = agent_manager
        
        # ISOLATED state per tab
        self.conversation_history = []
        self.focused_finding = finding  # Store the finding this tab is about
        self.current_worker = None
        self.enable_thinking = False
        self.thinking_budget = 10000
        
        self._setup_ui()
        
        # Auto-analyze if finding provided
        if finding:
            self._analyze_finding(finding)
    
    def _setup_ui(self):
        """Set up the UI for this chat tab."""
        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(3)
        
        # Agent selector
        self.agent_selector = CompactAgentSelector()
        self.agent_selector.agent_changed.connect(self._on_agent_changed)
        layout.addWidget(self.agent_selector)
        
        # Chat display
        self.chat_display = ScrollableTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setPlaceholderText(f"Chat about: {self.title}")
        layout.addWidget(self.chat_display, 1)
        
        # Message input
        input_layout = QHBoxLayout()
        self.message_edit = QLineEdit()
        self.message_edit.setPlaceholderText("Message Claude...")
        self.message_edit.returnPressed.connect(self._send_message)
        input_layout.addWidget(self.message_edit, 1)
        
        send_btn = QPushButton("Send")
        send_btn.setMaximumWidth(50)
        send_btn.setMaximumHeight(24)
        send_btn.clicked.connect(self._send_message)
        input_layout.addWidget(send_btn)
        
        layout.addLayout(input_layout)
        
        # Controls row
        controls_layout = QHBoxLayout()
        
        self.streaming_combo = QComboBox()
        self.streaming_combo.addItems(["Streaming", "Non-streaming"])
        self.streaming_combo.setMaximumWidth(110)
        self.streaming_combo.setStyleSheet("font-size: 10px;")
        controls_layout.addWidget(self.streaming_combo)
        
        clear_btn = QPushButton("Clear")
        clear_btn.setMaximumWidth(50)
        clear_btn.setMaximumHeight(24)
        clear_btn.setStyleSheet("font-size: 10px;")
        clear_btn.clicked.connect(self._clear_chat)
        controls_layout.addWidget(clear_btn)
        
        controls_layout.addStretch()
        
        # Token counter
        self.token_label = QLabel("Tokens: 0")
        self.token_label.setStyleSheet("font-size: 9px; color: #888;")
        controls_layout.addWidget(self.token_label)
        
        layout.addLayout(controls_layout)
        
        self.setLayout(layout)
        
        # Auto-update token count
        self.message_edit.textChanged.connect(self._update_token_count)
    
    def _on_agent_changed(self, agent_id: str, agent_profile):
        """Handle agent selection change."""
        self.chat_display.append(
            f"<i style='color: #888;'>→ Switched to {agent_profile.icon} <b>{agent_profile.name}</b></i><br>"
        )
    
    def _send_message(self):
        """Send message to Claude (isolated to this tab)."""
        if not self.claude_service.has_api_key():
            QMessageBox.warning(self, "API Key Required", "Please configure your API key first.")
            return
        
        message = self.message_edit.text().strip()
        if not message:
            return
        
        # Get current agent
        current_agent = self.agent_selector.get_current_agent()
        
        # Add to chat display
        self.chat_display.append(
            f"<b>You</b> <i>(to {current_agent.icon} {current_agent.name}):</i> {message}<br>"
        )
        self.message_edit.clear()
        
        # Add to THIS TAB'S conversation history
        self.conversation_history.append({"role": "user", "content": message})
        
        # Show thinking indicator
        self.chat_display.append(f"<b>{current_agent.icon} {current_agent.name}:</b> <i>Thinking...</i>")
        self._response_started = False
        
        # Create worker
        use_streaming = self.streaming_combo.currentText() == "Streaming"
        self.current_worker = ClaudeChatWorker(
            self.claude_service,
            message,
            system_prompt=current_agent.system_prompt,
            context=self.conversation_history[:-1],
            use_streaming=use_streaming,
            enable_thinking=current_agent.enable_thinking or self.enable_thinking,
            thinking_budget=self.thinking_budget,
            max_tokens=current_agent.max_tokens
        )
        self.current_worker.response_chunk.connect(self._on_response_chunk)
        self.current_worker.finished.connect(self._on_response_finished)
        self.current_worker.error.connect(self._on_error)
        self.current_worker.start()
        
        self._update_token_count()
    
    def _on_response_chunk(self, chunk: str):
        """Handle streaming response chunk."""
        current_agent = self.agent_selector.get_current_agent()
        
        if not self._response_started:
            html = self.chat_display.toHtml()
            if "<i>Thinking...</i>" in html:
                html = html.replace("<i>Thinking...</i>", chunk)
                self.chat_display.setHtml(html)
            else:
                self.chat_display.append(f"<b>{current_agent.icon} {current_agent.name}:</b> {chunk}")
            self._response_started = True
        else:
            cursor = self.chat_display.textCursor()
            cursor.movePosition(cursor.MoveOperation.End)
            cursor.insertText(chunk)
            self.chat_display.setTextCursor(cursor)
    
    def _on_response_finished(self, full_response: str):
        """Handle response completion."""
        self.conversation_history.append({"role": "assistant", "content": full_response})
        self._response_started = False
        self.chat_display.append("")
        self._update_token_count()
    
    def _on_error(self, error: str):
        """Handle error."""
        self._response_started = False
        html = self.chat_display.toHtml()
        if "<i>Thinking...</i>" in html:
            html = html.replace("<i>Thinking...</i>", f"<font color='red'>Error: {error}</font>")
            self.chat_display.setHtml(html)
        else:
            self.chat_display.append(f"<b>Error:</b> <font color='red'>{error}</font><br>")
    
    def _clear_chat(self):
        """Clear chat history for THIS TAB ONLY."""
        reply = QMessageBox.question(
            self,
            "Clear Chat",
            f"Clear chat history for '{self.title}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.conversation_history = []
            self.chat_display.clear()
            self.chat_display.append(f"<i style='color: #888;'>Chat cleared for: {self.title}</i><br>")
            self._update_token_count()
    
    def _update_token_count(self):
        """Update token count estimate."""
        message_tokens = len(self.message_edit.text()) // 4
        history_tokens = sum(len(str(msg.get("content", ""))) // 4 for msg in self.conversation_history)
        total = message_tokens + history_tokens
        
        self.token_label.setText(f"Tokens: ~{total:,}")
    
    def _analyze_finding(self, finding: Dict):
        """Auto-analyze a finding when tab is created."""
        finding_id = finding.get('finding_id', 'unknown')
        severity = finding.get('severity', 'unknown')
        
        # Remove embedding for prompt
        finding_copy = finding.copy()
        if 'embedding' in finding_copy:
            finding_copy['embedding'] = f"[{len(finding.get('embedding', []))} dimensional vector]"
        
        finding_json = json.dumps(finding_copy, indent=2)
        
        prompt = f"""Analyze this security finding:

**Finding ID:** {finding_id}
**Severity:** {severity}

```json
{finding_json}
```

Please provide:
1. **Summary**: What is this finding about?
2. **Threat Assessment**: How serious is this threat?
3. **MITRE ATT&CK Analysis**: What techniques are involved?
4. **Recommended Actions**: What should we do?
5. **Investigation Steps**: What to investigate next?"""
        
        self.message_edit.setText(prompt)
        self.chat_display.append(
            f"<p style='color: #2196F3;'><b>🔬 Analyzing: {finding_id}</b></p>"
        )
        self._send_message()


class TabbedClaudeChat(QWidget):
    """Claude chat interface with multiple tabs for isolated conversations."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.claude_service = create_claude_service(use_mcp_tools=True)
        self.data_service = DataService()
        self.agent_manager = AgentManager()
        self.chat_tabs: Dict[str, ChatTab] = {}
        self.tab_counter = 0
        
        self._setup_ui()
        self._check_api_key()
        
        # Create initial tab
        self._create_new_tab("General Chat")
    
    def _setup_ui(self):
        """Set up the UI."""
        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(3)
        
        # API key section (if not configured)
        if not self.claude_service.has_api_key():
            api_group = QGroupBox("API Configuration")
            api_layout = QFormLayout()
            
            self.api_key_edit = QLineEdit()
            self.api_key_edit.setPlaceholderText("Enter your Anthropic API key...")
            self.api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
            api_layout.addRow("API Key:", self.api_key_edit)
            
            save_key_btn = QPushButton("Save API Key")
            save_key_btn.clicked.connect(self._save_api_key)
            api_layout.addRow("", save_key_btn)
            
            api_group.setLayout(api_layout)
            layout.addWidget(api_group)
        
        # Tab widget with toolbar
        tab_toolbar = QHBoxLayout()
        
        new_tab_btn = QPushButton("+ New")
        new_tab_btn.setMaximumWidth(60)
        new_tab_btn.setToolTip("Create new chat tab")
        new_tab_btn.clicked.connect(self._prompt_new_tab)
        tab_toolbar.addWidget(new_tab_btn)
        
        tab_toolbar.addStretch()
        
        # MCP status
        self.mcp_status_label = QLabel("MCP: Loading...")
        self.mcp_status_label.setStyleSheet("font-size: 9px; color: #888;")
        tab_toolbar.addWidget(self.mcp_status_label)
        
        layout.addLayout(tab_toolbar)
        
        # Tab widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.setMovable(True)
        self.tab_widget.tabCloseRequested.connect(self._close_tab)
        self.tab_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tab_widget.customContextMenuRequested.connect(self._show_tab_context_menu)
        
        layout.addWidget(self.tab_widget, 1)
        
        self.setLayout(layout)
        
        # Show MCP status
        self._show_mcp_status()
    
    def _check_api_key(self):
        """Check if API key is configured."""
        pass  # Already handled in UI setup
    
    def _show_mcp_status(self):
        """Show MCP tools status."""
        if self.claude_service.mcp_tools:
            tool_count = len(self.claude_service.mcp_tools)
            self.mcp_status_label.setText(f"MCP: {tool_count} tools")
            self.mcp_status_label.setStyleSheet("font-size: 10px; color: #4a9eff;")
            tool_names = [tool['name'] for tool in self.claude_service.mcp_tools]
            self.mcp_status_label.setToolTip(f"MCP Tools: {', '.join(tool_names)}")
        else:
            self.mcp_status_label.setText("MCP: Not available")
            self.mcp_status_label.setStyleSheet("font-size: 10px; color: #ff4444;")
    
    def _save_api_key(self):
        """Save API key."""
        api_key = self.api_key_edit.text().strip()
        if not api_key:
            QMessageBox.warning(self, "Validation Error", "Please enter an API key.")
            return
        
        if self.claude_service.set_api_key(api_key, save=True):
            QMessageBox.information(self, "Success", "API key saved successfully!")
            # Remove API key section
            for i in range(self.layout().count()):
                item = self.layout().itemAt(i)
                if item and item.widget() and isinstance(item.widget(), QGroupBox):
                    if item.widget().title() == "API Configuration":
                        item.widget().setParent(None)
                        break
        else:
            QMessageBox.critical(self, "Error", "Failed to save API key.")
    
    def _prompt_new_tab(self):
        """Prompt for new tab name."""
        name, ok = QInputDialog.getText(
            self,
            "New Chat",
            "Chat name:",
            text=f"Chat {self.tab_counter + 1}"
        )
        
        if ok and name:
            self._create_new_tab(name)
    
    def _create_new_tab(self, title: str, finding: Optional[Dict] = None) -> ChatTab:
        """Create a new chat tab."""
        self.tab_counter += 1
        tab_id = f"chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{self.tab_counter}"
        
        # Create chat tab with isolated context
        chat_tab = ChatTab(
            tab_id=tab_id,
            title=title,
            claude_service=self.claude_service,
            data_service=self.data_service,
            agent_manager=self.agent_manager,
            finding=finding
        )
        
        # Add to tab widget
        index = self.tab_widget.addTab(chat_tab, title)
        self.tab_widget.setCurrentIndex(index)
        
        # Store reference
        self.chat_tabs[tab_id] = chat_tab
        
        return chat_tab
    
    def _close_tab(self, index: int):
        """Close tab by index."""
        if self.tab_widget.count() <= 1:
            QMessageBox.information(
                self,
                "Cannot Close",
                "You must have at least one chat tab open."
            )
            return
        
        widget = self.tab_widget.widget(index)
        tab_title = self.tab_widget.tabText(index)
        
        # Confirm if there's chat history
        if isinstance(widget, ChatTab) and widget.conversation_history:
            reply = QMessageBox.question(
                self,
                "Close Chat",
                f"Close '{tab_title}'?\n\nThis chat has {len(widget.conversation_history)} messages.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply != QMessageBox.StandardButton.Yes:
                return
            
            # Remove from tracking
            if widget.tab_id in self.chat_tabs:
                del self.chat_tabs[widget.tab_id]
        
        # Remove tab
        self.tab_widget.removeTab(index)
    
    def _show_tab_context_menu(self, position):
        """Show context menu for tabs."""
        tab_bar = self.tab_widget.tabBar()
        index = tab_bar.tabAt(position)
        
        if index < 0:
            return
        
        menu = QMenu(self)
        
        rename_action = QAction("Rename", self)
        rename_action.triggered.connect(lambda: self._rename_tab(index))
        menu.addAction(rename_action)
        
        menu.addSeparator()
        
        close_action = QAction("Close", self)
        close_action.triggered.connect(lambda: self._close_tab(index))
        menu.addAction(close_action)
        
        close_others_action = QAction("Close Others", self)
        close_others_action.triggered.connect(lambda: self._close_other_tabs(index))
        menu.addAction(close_others_action)
        
        menu.exec(tab_bar.mapToGlobal(position))
    
    def _rename_tab(self, index: int):
        """Rename tab at index."""
        current_name = self.tab_widget.tabText(index)
        new_name, ok = QInputDialog.getText(
            self,
            "Rename Chat",
            "New name:",
            text=current_name
        )
        
        if ok and new_name:
            self.tab_widget.setTabText(index, new_name)
            widget = self.tab_widget.widget(index)
            if isinstance(widget, ChatTab):
                widget.title = new_name
    
    def _close_other_tabs(self, keep_index: int):
        """Close all tabs except the one at keep_index."""
        reply = QMessageBox.question(
            self,
            "Close Other Tabs",
            "Close all other chat tabs?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        # Close tabs in reverse order
        indices_to_close = []
        for i in range(self.tab_widget.count()):
            if i != keep_index:
                indices_to_close.append(i)
        
        for i in reversed(indices_to_close):
            widget = self.tab_widget.widget(i)
            if isinstance(widget, ChatTab) and widget.tab_id in self.chat_tabs:
                del self.chat_tabs[widget.tab_id]
            self.tab_widget.removeTab(i)
    
    def create_tab_for_finding(self, finding: Dict):
        """Create a new tab for analyzing a specific finding."""
        finding_id = finding.get('finding_id', 'Unknown')
        title = f"{finding_id[:20]}"
        
        # Create new tab with finding
        new_tab = self._create_new_tab(title, finding=finding)
        
        return new_tab
    
    def analyze_finding(self, finding: Dict):
        """
        Analyze a finding - creates a new tab automatically.
        This is the main entry point from the dashboard.
        """
        return self.create_tab_for_finding(finding)

