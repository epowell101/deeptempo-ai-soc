"""Individual investigation tab with isolated chat and context."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QSplitter,
    QTextEdit, QLineEdit, QMessageBox, QGroupBox, QListWidget, QListWidgetItem,
    QComboBox, QInputDialog, QProgressBar
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QColor
import json
import asyncio
from pathlib import Path
from typing import Optional, Dict, List

from services.claude_service import ClaudeService
from services.claude_factory import create_claude_service
from services.data_service import DataService
from services.investigation_workflow_service import get_workflow_service, InvestigationPhase
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


class InvestigationTab(QWidget):
    """
    Individual investigation tab with isolated context.
    Each tab has its own:
    - Claude chat with isolated conversation history
    - Finding/event focus
    - Workflow tracking
    - Agent selection
    """
    
    tab_title_changed = pyqtSignal(str)  # New title
    tab_close_requested = pyqtSignal()
    
    def __init__(self, tab_id: str, title: str = "New Investigation", parent=None):
        super().__init__(parent)
        self.tab_id = tab_id
        self.title = title
        
        # Initialize services
        self.claude_service = create_claude_service(use_mcp_tools=True)
        self.data_service = DataService()
        self.workflow_service = get_workflow_service()
        self.agent_manager = AgentManager()
        
        # Tab-specific state (ISOLATED)
        self.conversation_history = []  # Isolated chat history for this tab
        self.focused_findings = []  # Findings being analyzed in this tab
        self.workflow_id = None  # Optional workflow associated with this tab
        self.case_id = None  # Optional case associated with this tab
        
        # UI state
        self.current_worker = None
        self.enable_thinking = False
        self.thinking_budget = 10000
        
        self._setup_ui()
        self._update_title()
    
    def _setup_ui(self):
        """Set up the UI."""
        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        # Header with tab info
        header_layout = QHBoxLayout()
        
        self.title_label = QLabel(f"<h3>{self.title}</h3>")
        header_layout.addWidget(self.title_label)
        
        rename_btn = QPushButton("Rename")
        rename_btn.setMaximumWidth(60)
        rename_btn.clicked.connect(self._rename_tab)
        header_layout.addWidget(rename_btn)
        
        header_layout.addStretch()
        
        # Context info
        self.context_info = QLabel("No findings loaded")
        self.context_info.setStyleSheet("color: #888; font-size: 10px;")
        header_layout.addWidget(self.context_info)
        
        layout.addLayout(header_layout)
        
        # Main splitter: Left (chat) | Right (context/findings)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # === LEFT SIDE: CHAT ===
        chat_widget = QWidget()
        chat_layout = QVBoxLayout(chat_widget)
        chat_layout.setContentsMargins(0, 0, 0, 0)
        
        # Agent selector
        self.agent_selector = CompactAgentSelector()
        self.agent_selector.agent_changed.connect(self._on_agent_changed)
        chat_layout.addWidget(self.agent_selector)
        
        # Chat display
        self.chat_display = ScrollableTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setPlaceholderText("Chat with Claude about this investigation...")
        chat_layout.addWidget(self.chat_display, 1)
        
        # Message input
        input_layout = QHBoxLayout()
        self.message_edit = QLineEdit()
        self.message_edit.setPlaceholderText("Type your message...")
        self.message_edit.returnPressed.connect(self._send_message)
        input_layout.addWidget(self.message_edit, 1)
        
        send_btn = QPushButton("Send")
        send_btn.clicked.connect(self._send_message)
        input_layout.addWidget(send_btn)
        
        chat_layout.addLayout(input_layout)
        
        # Chat controls
        controls_layout = QHBoxLayout()
        
        self.streaming_combo = QComboBox()
        self.streaming_combo.addItems(["Streaming", "Non-streaming"])
        self.streaming_combo.setMaximumWidth(120)
        controls_layout.addWidget(self.streaming_combo)
        
        clear_btn = QPushButton("Clear Chat")
        clear_btn.setMaximumWidth(80)
        clear_btn.clicked.connect(self._clear_chat)
        controls_layout.addWidget(clear_btn)
        
        controls_layout.addStretch()
        
        # Token counter
        self.token_label = QLabel("Tokens: 0")
        self.token_label.setStyleSheet("font-size: 9px; color: #888;")
        controls_layout.addWidget(self.token_label)
        
        chat_layout.addLayout(controls_layout)
        
        splitter.addWidget(chat_widget)
        
        # === RIGHT SIDE: CONTEXT/FINDINGS ===
        context_widget = QWidget()
        context_layout = QVBoxLayout(context_widget)
        context_layout.setContentsMargins(0, 0, 0, 0)
        
        # Focused Findings
        findings_group = QGroupBox("Focused Findings")
        findings_layout = QVBoxLayout()
        
        self.findings_list = QListWidget()
        self.findings_list.setMaximumHeight(150)
        findings_layout.addWidget(self.findings_list)
        
        findings_btn_layout = QHBoxLayout()
        
        add_finding_btn = QPushButton("Add Finding")
        add_finding_btn.clicked.connect(self._add_finding)
        findings_btn_layout.addWidget(add_finding_btn)
        
        remove_finding_btn = QPushButton("Remove")
        remove_finding_btn.clicked.connect(self._remove_finding)
        findings_btn_layout.addWidget(remove_finding_btn)
        
        analyze_btn = QPushButton("Analyze Selected")
        analyze_btn.setStyleSheet("background-color: #2196F3; color: white;")
        analyze_btn.clicked.connect(self._analyze_selected_finding)
        findings_btn_layout.addWidget(analyze_btn)
        
        findings_layout.addLayout(findings_btn_layout)
        findings_group.setLayout(findings_layout)
        context_layout.addWidget(findings_group)
        
        # Investigation Notes
        notes_group = QGroupBox("Investigation Notes")
        notes_layout = QVBoxLayout()
        
        self.notes_edit = QTextEdit()
        self.notes_edit.setPlaceholderText("Track your investigation notes here...")
        self.notes_edit.setMaximumHeight(100)
        notes_layout.addWidget(self.notes_edit)
        
        notes_group.setLayout(notes_layout)
        context_layout.addWidget(notes_group)
        
        # Quick Actions
        actions_group = QGroupBox("Quick Actions")
        actions_layout = QVBoxLayout()
        
        correlate_btn = QPushButton("Correlate All Focused Findings")
        correlate_btn.clicked.connect(self._correlate_findings)
        actions_layout.addWidget(correlate_btn)
        
        create_case_btn = QPushButton("Create Case from This Investigation")
        create_case_btn.clicked.connect(self._create_case)
        actions_layout.addWidget(create_case_btn)
        
        export_chat_btn = QPushButton("Export Chat History")
        export_chat_btn.clicked.connect(self._export_chat)
        actions_layout.addWidget(export_chat_btn)
        
        print_pdf_btn = QPushButton("📄 Print Chat as PDF")
        print_pdf_btn.setStyleSheet("background-color: #E91E63; color: white;")
        print_pdf_btn.clicked.connect(self._print_chat_pdf)
        actions_layout.addWidget(print_pdf_btn)
        
        actions_group.setLayout(actions_layout)
        context_layout.addWidget(actions_group)
        
        context_layout.addStretch()
        
        splitter.addWidget(context_widget)
        
        # Set initial splitter sizes (60% chat, 40% context)
        splitter.setSizes([600, 400])
        
        layout.addWidget(splitter, 1)
        
        self.setLayout(layout)
        
        # Auto-update token count
        self.message_edit.textChanged.connect(self._update_token_count)
    
    def _rename_tab(self):
        """Rename this investigation tab."""
        new_title, ok = QInputDialog.getText(
            self,
            "Rename Investigation",
            "Enter new name:",
            text=self.title
        )
        
        if ok and new_title:
            self.title = new_title
            self._update_title()
            self.tab_title_changed.emit(new_title)
    
    def _update_title(self):
        """Update the title label."""
        self.title_label.setText(f"<h3>{self.title}</h3>")
    
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
        
        # Create worker with agent's settings
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
        # Add to THIS TAB'S conversation history
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
            "Clear this tab's chat history? This will not affect other tabs.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.conversation_history = []
            self.chat_display.clear()
            self.chat_display.append(
                f"<i style='color: #888;'>Chat cleared for: {self.title}</i><br>"
            )
            self._update_token_count()
    
    def _add_finding(self):
        """Add a finding to focus on in this tab."""
        finding_id, ok = QInputDialog.getText(
            self,
            "Add Finding",
            "Enter finding ID:"
        )
        
        if ok and finding_id:
            finding = self.data_service.get_finding(finding_id)
            if finding:
                if finding not in self.focused_findings:
                    self.focused_findings.append(finding)
                    item = QListWidgetItem(
                        f"{finding.get('finding_id', 'N/A')[:30]} - {finding.get('severity', 'N/A')}"
                    )
                    self.findings_list.addItem(item)
                    self._update_context_info()
                else:
                    QMessageBox.information(self, "Already Added", "This finding is already in focus.")
            else:
                QMessageBox.warning(self, "Not Found", f"Finding {finding_id} not found.")
    
    def _remove_finding(self):
        """Remove a finding from focus."""
        current_row = self.findings_list.currentRow()
        if current_row >= 0:
            self.findings_list.takeItem(current_row)
            self.focused_findings.pop(current_row)
            self._update_context_info()
    
    def _analyze_selected_finding(self):
        """Analyze the selected finding."""
        current_row = self.findings_list.currentRow()
        if current_row < 0:
            QMessageBox.information(self, "No Selection", "Please select a finding to analyze.")
            return
        
        finding = self.focused_findings[current_row]
        self._analyze_finding(finding)
    
    def _analyze_finding(self, finding: Dict):
        """Analyze a specific finding with Claude."""
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
    
    def _correlate_findings(self):
        """Correlate all focused findings."""
        if len(self.focused_findings) < 2:
            QMessageBox.information(
                self,
                "Not Enough Findings",
                "Add at least 2 findings to correlate."
            )
            return
        
        findings_summary = "\n".join([
            f"- {f.get('finding_id', 'N/A')}: {f.get('severity', 'N/A')} severity, {f.get('data_source', 'N/A')}"
            for f in self.focused_findings
        ])
        
        prompt = f"""Correlate these {len(self.focused_findings)} findings and identify patterns:

{findings_summary}

Please analyze:
1. Common patterns or indicators
2. Potential attack chains
3. Shared entities (IPs, hosts, etc.)
4. Timeline correlation
5. Overall threat assessment"""
        
        self.message_edit.setText(prompt)
        self.chat_display.append(
            f"<p style='color: #FF9800;'><b>🔗 Correlating {len(self.focused_findings)} findings...</b></p>"
        )
        self._send_message()
    
    def _create_case(self):
        """Create a case from this investigation."""
        if not self.focused_findings:
            QMessageBox.information(
                self,
                "No Findings",
                "Add findings to this investigation first."
            )
            return
        
        title, ok = QInputDialog.getText(
            self,
            "Create Case",
            "Case Title:",
            text=self.title
        )
        
        if ok and title:
            finding_ids = [f.get('finding_id') for f in self.focused_findings]
            case = self.data_service.create_case(
                title=title,
                description=f"Investigation: {self.title}\n\nNotes:\n{self.notes_edit.toPlainText()}",
                finding_ids=finding_ids
            )
            
            self.case_id = case.get('case_id')
            
            QMessageBox.information(
                self,
                "Case Created",
                f"Case {self.case_id} created with {len(finding_ids)} findings."
            )
    
    def _export_chat(self):
        """Export chat history to file."""
        if not self.conversation_history:
            QMessageBox.information(self, "No History", "No chat history to export.")
            return
        
        from PyQt6.QtWidgets import QFileDialog
        
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Export Chat History",
            f"{self.tab_id}_chat.json",
            "JSON Files (*.json)"
        )
        
        if filename:
            try:
                with open(filename, 'w') as f:
                    json.dump({
                        "tab_id": self.tab_id,
                        "title": self.title,
                        "history": self.conversation_history,
                        "findings": [f.get('finding_id') for f in self.focused_findings],
                        "notes": self.notes_edit.toPlainText()
                    }, f, indent=2)
                
                QMessageBox.information(self, "Exported", f"Chat history exported to {filename}")
            except Exception as e:
                QMessageBox.critical(self, "Export Error", f"Failed to export: {e}")
    
    def _print_chat_pdf(self):
        """Generate a PDF report of the chat conversation."""
        if not self.conversation_history:
            QMessageBox.information(self, "No History", "No chat history to print.")
            return
        
        from PyQt6.QtWidgets import QFileDialog
        from services.report_service import ReportService
        from datetime import datetime
        
        # Generate default filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_filename = f"investigation_{self.tab_id}_{timestamp}.pdf"
        
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Save Investigation Report",
            str(Path("TestOutputs") / default_filename),
            "PDF Files (*.pdf)"
        )
        
        if filename:
            try:
                # Create report service
                report_service = ReportService()
                
                # Generate the PDF
                success = report_service.generate_investigation_chat_report(
                    output_path=Path(filename),
                    tab_title=self.title,
                    conversation_history=self.conversation_history,
                    focused_findings=self.focused_findings if self.focused_findings else None,
                    notes=self.notes_edit.toPlainText()
                )
                
                if success:
                    QMessageBox.information(
                        self,
                        "PDF Generated",
                        f"Investigation report saved to:\n{filename}"
                    )
                else:
                    QMessageBox.warning(
                        self,
                        "Generation Failed",
                        "Failed to generate PDF report. Check logs for details."
                    )
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "PDF Error",
                    f"Failed to generate PDF report:\n{str(e)}"
                )
    
    def _update_context_info(self):
        """Update context information display."""
        if self.focused_findings:
            self.context_info.setText(
                f"{len(self.focused_findings)} finding(s) in focus | "
                f"{len(self.conversation_history)} messages"
            )
        else:
            self.context_info.setText(
                f"No findings loaded | {len(self.conversation_history)} messages"
            )
    
    def _update_token_count(self):
        """Update token count estimate."""
        message_tokens = len(self.message_edit.text()) // 4
        history_tokens = sum(len(str(msg.get("content", ""))) // 4 for msg in self.conversation_history)
        total = message_tokens + history_tokens
        
        self.token_label.setText(f"Tokens: ~{total:,}")
        self._update_context_info()
    
    def add_finding_by_id(self, finding_id: str):
        """Add a finding to this tab by ID (called from external source)."""
        finding = self.data_service.get_finding(finding_id)
        if finding and finding not in self.focused_findings:
            self.focused_findings.append(finding)
            item = QListWidgetItem(
                f"{finding.get('finding_id', 'N/A')[:30]} - {finding.get('severity', 'N/A')}"
            )
            self.findings_list.addItem(item)
            self._update_context_info()
    
    def add_finding_object(self, finding: Dict):
        """Add a finding object directly to this tab."""
        if finding not in self.focused_findings:
            self.focused_findings.append(finding)
            item = QListWidgetItem(
                f"{finding.get('finding_id', 'N/A')[:30]} - {finding.get('severity', 'N/A')}"
            )
            self.findings_list.addItem(item)
            self._update_context_info()
            
            # Auto-analyze if this is the first finding
            if len(self.focused_findings) == 1:
                self._analyze_finding(finding)

