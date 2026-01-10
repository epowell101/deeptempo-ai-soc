"""Claude chat interface with context-aware prompts."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton, QLineEdit,
    QLabel, QComboBox, QMessageBox, QGroupBox, QFormLayout, QInputDialog
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
import asyncio
import json

from services.claude_service import ClaudeService
from services.data_service import DataService


class ClaudeChatWorker(QThread):
    """Worker thread for Claude API calls."""
    
    response_chunk = pyqtSignal(str)
    finished = pyqtSignal(str)
    error = pyqtSignal(str)
    
    def __init__(self, service: ClaudeService, message: str, system_prompt: str = None,
                 context: list = None, use_streaming: bool = True):
        super().__init__()
        self.service = service
        self.message = message
        self.system_prompt = system_prompt
        self.context = context or []
        self.use_streaming = use_streaming
    
    def run(self):
        """Run the chat request."""
        try:
            if self.use_streaming:
                # Use async streaming
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                async def stream_chat():
                    full_response = ""
                    async for chunk in self.service.chat_stream(
                        self.message,
                        system_prompt=self.system_prompt,
                        context=self.context
                    ):
                        self.response_chunk.emit(chunk)
                        full_response += chunk
                    self.finished.emit(full_response)
                
                loop.run_until_complete(stream_chat())
                loop.close()
            else:
                # Non-streaming
                response = self.service.chat(
                    self.message,
                    system_prompt=self.system_prompt,
                    context=self.context
                )
                self.finished.emit(response or "")
        
        except Exception as e:
            self.error.emit(str(e))


class ClaudeChat(QWidget):
    """Claude chat interface widget."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.claude_service = ClaudeService()
        self.data_service = DataService()
        self.conversation_history = []
        self.current_worker = None
        
        self._setup_ui()
        self._check_api_key()
    
    def _setup_ui(self):
        """Set up the UI."""
        layout = QVBoxLayout()
        
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
        
        # Quick actions
        actions_group = QGroupBox("Quick Actions")
        actions_layout = QHBoxLayout()
        
        analyze_btn = QPushButton("Analyze Selected Finding")
        analyze_btn.clicked.connect(self._analyze_finding)
        actions_layout.addWidget(analyze_btn)
        
        correlate_btn = QPushButton("Correlate Findings")
        correlate_btn.clicked.connect(self._correlate_findings)
        actions_layout.addWidget(correlate_btn)
        
        case_summary_btn = QPushButton("Generate Case Summary")
        case_summary_btn.clicked.connect(self._generate_case_summary)
        actions_layout.addWidget(case_summary_btn)
        
        actions_layout.addStretch()
        actions_group.setLayout(actions_layout)
        layout.addWidget(actions_group)
        
        # Chat history
        history_label = QLabel("Conversation:")
        layout.addWidget(history_label)
        
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        layout.addWidget(self.chat_display)
        
        # Input area
        input_layout = QHBoxLayout()
        
        self.message_edit = QLineEdit()
        self.message_edit.setPlaceholderText("Type your message to Claude...")
        self.message_edit.returnPressed.connect(self._send_message)
        input_layout.addWidget(self.message_edit)
        
        send_btn = QPushButton("Send")
        send_btn.clicked.connect(self._send_message)
        input_layout.addWidget(send_btn)
        
        layout.addLayout(input_layout)
        
        # Options
        options_layout = QHBoxLayout()
        
        self.streaming_checkbox = QComboBox()
        self.streaming_checkbox.addItems(["Streaming", "Non-streaming"])
        options_layout.addWidget(QLabel("Mode:"))
        options_layout.addWidget(self.streaming_checkbox)
        
        options_layout.addStretch()
        
        clear_btn = QPushButton("Clear History")
        clear_btn.clicked.connect(self._clear_history)
        options_layout.addWidget(clear_btn)
        
        layout.addLayout(options_layout)
        
        self.setLayout(layout)
    
    def _check_api_key(self):
        """Check if API key is configured."""
        if not self.claude_service.has_api_key():
            self.chat_display.setPlainText(
                "Please configure your Anthropic API key above to use Claude chat.\n\n"
                "You can get an API key from: https://console.anthropic.com/"
            )
    
    def _save_api_key(self):
        """Save API key."""
        api_key = self.api_key_edit.text().strip()
        if not api_key:
            QMessageBox.warning(self, "Validation Error", "Please enter an API key.")
            return
        
        if self.claude_service.set_api_key(api_key, save=True):
            QMessageBox.information(self, "Success", "API key saved successfully!")
            self._check_api_key()
            # Remove API key section
            for i in range(self.layout().count()):
                item = self.layout().itemAt(i)
                if item and item.widget() and isinstance(item.widget(), QGroupBox):
                    if item.widget().title() == "API Configuration":
                        item.widget().setParent(None)
                        break
        else:
            QMessageBox.critical(self, "Error", "Failed to save API key.")
    
    def _send_message(self):
        """Send message to Claude."""
        if not self.claude_service.has_api_key():
            QMessageBox.warning(self, "API Key Required", "Please configure your API key first.")
            return
        
        message = self.message_edit.text().strip()
        if not message:
            return
        
        # Add to chat display
        self.chat_display.append(f"<b>You:</b> {message}")
        self.message_edit.clear()
        
        # Add to conversation history
        self.conversation_history.append({"role": "user", "content": message})
        
        # Show thinking indicator
        self.chat_display.append("<b>Claude:</b> <i>Thinking...</i>")
        
        # Create worker
        use_streaming = self.streaming_checkbox.currentText() == "Streaming"
        self.current_worker = ClaudeChatWorker(
            self.claude_service,
            message,
            context=self.conversation_history,
            use_streaming=use_streaming
        )
        self.current_worker.response_chunk.connect(self._on_response_chunk)
        self.current_worker.finished.connect(self._on_response_finished)
        self.current_worker.error.connect(self._on_error)
        self.current_worker.start()
    
    def _on_response_chunk(self, chunk: str):
        """Handle streaming response chunk."""
        # Remove "Thinking..." and append chunk
        cursor = self.chat_display.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        cursor.select(cursor.SelectionType.BlockUnderCursor)
        
        text = cursor.selectedText()
        if "<i>Thinking...</i>" in text:
            cursor.removeSelectedText()
            cursor.insertHtml(f"<b>Claude:</b> {chunk}")
        else:
            cursor.insertText(chunk)
        
        self.chat_display.setTextCursor(cursor)
        self.chat_display.ensureCursorVisible()
    
    def _on_response_finished(self, full_response: str):
        """Handle response completion."""
        # Add to conversation history
        self.conversation_history.append({"role": "assistant", "content": full_response})
    
    def _on_error(self, error: str):
        """Handle error."""
        self.chat_display.append(f"<b>Error:</b> {error}")
    
    def _clear_history(self):
        """Clear conversation history."""
        self.conversation_history = []
        self.chat_display.clear()
    
    def _analyze_finding(self):
        """Analyze a selected finding."""
        # This would need integration with the findings widget
        # For now, prompt user to select a finding ID
        finding_id, ok = QInputDialog.getText(
            self,
            "Analyze Finding",
            "Enter finding ID:"
        )
        
        if ok and finding_id:
            finding = self.data_service.get_finding(finding_id)
            if finding:
                try:
                    analysis = self.claude_service.analyze_finding(finding)
                    self.chat_display.append(f"<b>Analysis of {finding_id}:</b>\n{analysis}")
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Failed to analyze finding: {e}")
            else:
                QMessageBox.warning(self, "Not Found", f"Finding {finding_id} not found.")
    
    def _correlate_findings(self):
        """Correlate findings."""
        findings = self.data_service.get_findings()
        if not findings:
            QMessageBox.information(self, "No Data", "No findings available to correlate.")
            return
        
        # Use first 10 findings for correlation
        selected_findings = findings[:10]
        
        try:
            correlation = self.claude_service.correlate_findings(selected_findings)
            self.chat_display.append(f"<b>Correlation Analysis:</b>\n{correlation}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to correlate findings: {e}")
    
    def _generate_case_summary(self):
        """Generate case summary."""
        case_id, ok = QInputDialog.getText(
            self,
            "Generate Case Summary",
            "Enter case ID:"
        )
        
        if ok and case_id:
            case = self.data_service.get_case(case_id)
            if case:
                # Get related findings
                finding_ids = case.get('finding_ids', [])
                findings = [self.data_service.get_finding(fid) for fid in finding_ids]
                findings = [f for f in findings if f is not None]
                
                try:
                    summary = self.claude_service.generate_case_summary(case, findings)
                    self.chat_display.append(f"<b>Case Summary for {case_id}:</b>\n{summary}")
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Failed to generate summary: {e}")
            else:
                QMessageBox.warning(self, "Not Found", f"Case {case_id} not found.")

