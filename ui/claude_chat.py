"""Claude chat interface with context-aware prompts."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton, QLineEdit,
    QLabel, QComboBox, QMessageBox, QGroupBox, QFormLayout, QInputDialog,
    QCheckBox, QSpinBox, QFileDialog, QListWidget, QListWidgetItem, QProgressBar
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QKeyEvent, QShortcut, QKeySequence, QPixmap
import asyncio
import json
from pathlib import Path

from services.claude_service import ClaudeService
from services.data_service import DataService


class ClaudeChatWorker(QThread):
    """Worker thread for Claude API calls."""
    
    response_chunk = pyqtSignal(str)
    finished = pyqtSignal(str)
    error = pyqtSignal(str)
    
    def __init__(self, service: ClaudeService, message: str, system_prompt: str = None,
                 context: list = None, use_streaming: bool = True, images: list = None,
                 enable_thinking: bool = False, thinking_budget: int = 10000):
        super().__init__()
        self.service = service
        self.message = message
        self.system_prompt = system_prompt
        self.context = context or []
        self.use_streaming = use_streaming
        self.images = images or []
        self.enable_thinking = enable_thinking
        self.thinking_budget = thinking_budget
    
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
                        context=self.context,
                        images=self.images if self.images else None,
                        enable_thinking=self.enable_thinking,
                        thinking_budget=self.thinking_budget
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
                    context=self.context,
                    images=self.images if self.images else None,
                    enable_thinking=self.enable_thinking,
                    thinking_budget=self.thinking_budget
                )
                self.finished.emit(response or "")
        
        except Exception as e:
            self.error.emit(str(e))


class ScrollableTextEdit(QTextEdit):
    """Custom QTextEdit that ensures scrolling works properly and prevents accidental clearing."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._max_document_length = 10 * 1024 * 1024  # 10MB limit to prevent memory issues
        self._auto_scroll = True
    
    def append(self, text: str):
        """Override append to ensure scrolling and handle long documents."""
        # Check document size and trim if necessary (only if getting very large)
        doc = self.document()
        char_count = doc.characterCount()
        
        if char_count > self._max_document_length:
            # Keep last 5MB of content by removing the first half
            cursor = self.textCursor()
            cursor.movePosition(cursor.MoveOperation.Start)
            # Move to middle of document
            blocks_to_remove = doc.blockCount() // 2
            if blocks_to_remove > 0:
                cursor.movePosition(cursor.MoveOperation.Down, cursor.MoveMode.MoveAnchor, blocks_to_remove)
                cursor.movePosition(cursor.MoveOperation.StartOfBlock)
                # Select from start to here
                start_cursor = self.textCursor()
                start_cursor.movePosition(cursor.MoveOperation.Start)
                start_cursor.setPosition(cursor.position(), cursor.MoveMode.KeepAnchor)
                start_cursor.removeSelectedText()
                start_cursor.insertText("\n[... Previous conversation truncated for performance ...]\n\n")
        
        # Append new text using parent's append method
        super().append(text)
        
        # Force scroll to bottom immediately and with a small delay to ensure it works
        if self._auto_scroll:
            self._force_scroll()
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(10, self._force_scroll)
            QTimer.singleShot(50, self._force_scroll)  # Double-check after rendering
    
    def _force_scroll(self):
        """Force scroll to bottom."""
        scrollbar = self.verticalScrollBar()
        max_val = scrollbar.maximum()
        if max_val > 0:
            scrollbar.setValue(max_val)
        # Also ensure cursor is visible at the end
        cursor = self.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.setTextCursor(cursor)
        self.ensureCursorVisible()
    
    def keyPressEvent(self, event: QKeyEvent):
        """Override to prevent Command+C from clearing and handle copy properly."""
        modifiers = event.modifiers()
        key = event.key()
        
        # On macOS, Command is Qt.KeyboardModifier.MetaModifier
        # On Windows/Linux, Ctrl is Qt.KeyboardModifier.ControlModifier
        is_command_or_ctrl = (modifiers & Qt.KeyboardModifier.MetaModifier) or (modifiers & Qt.KeyboardModifier.ControlModifier)
        
        # Handle copy (Command+C or Ctrl+C) - prevent it from clearing
        if is_command_or_ctrl and key == Qt.Key.Key_C:
            if self.textCursor().hasSelection():
                self.copy()
            # Always accept and prevent default behavior that might clear
            event.accept()
            return
        
        # Handle select all (Command+A or Ctrl+A)
        if is_command_or_ctrl and key == Qt.Key.Key_A:
            self.selectAll()
            event.accept()
            return
        
        # Block all other Command/Ctrl shortcuts to prevent accidental actions (like clearing)
        if is_command_or_ctrl:
            event.ignore()
            return
        
        # Allow normal navigation and selection for read-only widget
        super().keyPressEvent(event)


class ClaudeChat(QWidget):
    """Claude chat interface widget."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.claude_service = ClaudeService(use_mcp_tools=True)  # Enable MCP tools
        self.data_service = DataService()
        self.conversation_history = []
        self.current_worker = None
        self.attached_images = []  # List of image paths/content blocks
        self.enable_thinking = False
        self.thinking_budget = 10000
        self.estimated_tokens = 0  # Track estimated token usage
        
        self._setup_ui()
        self._check_api_key()
        self._show_mcp_status()
        self._update_context_indicator()
    
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
        
        
        # Chat history
        history_label = QLabel("Conversation:")
        layout.addWidget(history_label)
        
        self.chat_display = ScrollableTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        # Enable auto-scrolling to bottom
        self.chat_display.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        layout.addWidget(self.chat_display)
        
        # Attached images section (hidden until images are attached)
        self.images_group = QGroupBox("Attached Images")
        images_layout = QVBoxLayout()
        
        self.images_list = QListWidget()
        self.images_list.setMaximumHeight(80)
        images_layout.addWidget(self.images_list)
        
        images_buttons_layout = QHBoxLayout()
        remove_image_btn = QPushButton("Remove Selected")
        remove_image_btn.clicked.connect(self._remove_image)
        images_buttons_layout.addWidget(remove_image_btn)
        
        clear_images_btn = QPushButton("Clear All")
        clear_images_btn.clicked.connect(self._clear_images)
        images_buttons_layout.addWidget(clear_images_btn)
        
        images_buttons_layout.addStretch()
        images_layout.addLayout(images_buttons_layout)
        
        self.images_group.setLayout(images_layout)
        self.images_group.setVisible(False)  # Hidden by default
        layout.addWidget(self.images_group)
        
        # Input area
        input_layout = QHBoxLayout()
        
        self.message_edit = QLineEdit()
        self.message_edit.setPlaceholderText("Type your message to Claude...")
        self.message_edit.returnPressed.connect(self._send_message)
        self.message_edit.textChanged.connect(self._update_context_indicator)
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
        
        # Attach Image button (positioned with other options)
        attach_image_btn = QPushButton("Attach Image")
        attach_image_btn.setToolTip("Attach Image\nAdd an image file to your message. Supported formats: PNG, JPG, JPEG, GIF, WEBP")
        attach_image_btn.clicked.connect(self._attach_image)
        options_layout.addWidget(attach_image_btn)
        
        options_layout.addStretch()
        
        clear_btn = QPushButton("Clear History")
        clear_btn.clicked.connect(self._clear_history)
        options_layout.addWidget(clear_btn)
        
        layout.addLayout(options_layout)
        
        # Bottom status bar with context window info (compact)
        status_layout = QHBoxLayout()
        status_layout.setContentsMargins(5, 2, 5, 2)
        
        # Context window indicator (compact)
        self.context_label = QLabel("Tokens: 0 / 200,000 (0%) | Remaining: 200,000")
        self.context_label.setStyleSheet("font-size: 10px; color: #888;")
        status_layout.addWidget(self.context_label)
        
        # Compact progress bar
        self.context_progress = QProgressBar()
        self.context_progress.setMinimum(0)
        self.context_progress.setMaximum(200000)
        self.context_progress.setMaximumHeight(8)
        self.context_progress.setTextVisible(False)  # Hide text, just show bar
        self.context_progress.setStyleSheet("""
            QProgressBar {
                border: 1px solid #555;
                border-radius: 4px;
                background: #2a2a2a;
            }
            QProgressBar::chunk {
                background: #4a9eff;
                border-radius: 3px;
            }
        """)
        status_layout.addWidget(self.context_progress, 1)  # Allow it to stretch
        
        # Separator
        separator1 = QLabel("|")
        separator1.setStyleSheet("font-size: 10px; color: #555; margin: 0 5px;")
        status_layout.addWidget(separator1)
        
        # Extended thinking controls (compact)
        self.thinking_checkbox = QCheckBox("Extended Thinking")
        self.thinking_checkbox.setChecked(False)
        self.thinking_checkbox.setStyleSheet("font-size: 10px;")
        self.thinking_checkbox.setToolTip("Enable Extended Thinking\nAllows Claude to use extended reasoning for complex tasks. Uses additional tokens from the thinking budget.")
        self.thinking_checkbox.toggled.connect(self._on_thinking_toggled)
        status_layout.addWidget(self.thinking_checkbox)
        
        self.thinking_budget_spin = QSpinBox()
        self.thinking_budget_spin.setMinimum(1000)
        self.thinking_budget_spin.setMaximum(100000)
        self.thinking_budget_spin.setValue(10000)
        self.thinking_budget_spin.setSingleStep(1000)
        self.thinking_budget_spin.setSuffix(" tokens")
        self.thinking_budget_spin.setEnabled(False)
        self.thinking_budget_spin.setMaximumWidth(120)
        self.thinking_budget_spin.setStyleSheet("font-size: 10px;")
        self.thinking_budget_spin.setToolTip("Thinking Budget\nMaximum tokens to allocate for extended thinking. Higher values allow for more complex reasoning but use more tokens.")
        self.thinking_budget_spin.valueChanged.connect(self._on_thinking_budget_changed)
        status_layout.addWidget(self.thinking_budget_spin)
        
        # Separator
        separator2 = QLabel("|")
        separator2.setStyleSheet("font-size: 10px; color: #555; margin: 0 5px;")
        status_layout.addWidget(separator2)
        
        # MCP Tools Status (compact)
        self.mcp_status_label = QLabel("MCP: Loading...")
        self.mcp_status_label.setStyleSheet("font-size: 10px; color: #888;")
        self.mcp_status_label.setToolTip("Loading MCP tools...")
        status_layout.addWidget(self.mcp_status_label)
        
        refresh_mcp_btn = QPushButton("↻")
        refresh_mcp_btn.setMaximumWidth(25)
        refresh_mcp_btn.setMaximumHeight(20)
        refresh_mcp_btn.setToolTip("Refresh MCP Tools\nReloads the list of available MCP tools from running servers.")
        refresh_mcp_btn.setStyleSheet("font-size: 10px; padding: 2px;")
        refresh_mcp_btn.clicked.connect(self._refresh_mcp_tools)
        status_layout.addWidget(refresh_mcp_btn)
        
        # Separator
        separator3 = QLabel("|")
        separator3.setStyleSheet("font-size: 10px; color: #555; margin: 0 5px;")
        status_layout.addWidget(separator3)
        
        # Quick Actions (compact buttons)
        analyze_btn = QPushButton("Analyze")
        analyze_btn.setMaximumHeight(20)
        analyze_btn.setStyleSheet("font-size: 10px; padding: 2px 5px;")
        analyze_btn.setToolTip("Analyze Selected Finding\nOpens a dialog to enter a finding ID for analysis.")
        analyze_btn.clicked.connect(self._analyze_finding)
        status_layout.addWidget(analyze_btn)
        
        correlate_btn = QPushButton("Correlate")
        correlate_btn.setMaximumHeight(20)
        correlate_btn.setStyleSheet("font-size: 10px; padding: 2px 5px;")
        correlate_btn.setToolTip("Correlate Findings\nAnalyzes and correlates multiple security findings to identify patterns.")
        correlate_btn.clicked.connect(self._correlate_findings)
        status_layout.addWidget(correlate_btn)
        
        case_summary_btn = QPushButton("Case Summary")
        case_summary_btn.setMaximumHeight(20)
        case_summary_btn.setStyleSheet("font-size: 10px; padding: 2px 5px;")
        case_summary_btn.setToolTip("Generate Case Summary\nOpens a dialog to enter a case ID and generate a summary.")
        case_summary_btn.clicked.connect(self._generate_case_summary)
        status_layout.addWidget(case_summary_btn)
        
        layout.addLayout(status_layout)
        
        self.setLayout(layout)
    
    def _check_api_key(self):
        """Check if API key is configured."""
        if not self.claude_service.has_api_key():
            self.chat_display.setPlainText(
                "Please configure your Anthropic API key above to use Claude chat.\n\n"
                "You can get an API key from: https://console.anthropic.com/"
            )
    
    def _show_mcp_status(self):
        """Show MCP tools status."""
        if self.claude_service.mcp_tools:
            tool_count = len(self.claude_service.mcp_tools)
            tool_names = [tool['name'] for tool in self.claude_service.mcp_tools]
            tool_list = ', '.join(tool_names)
            
            # Compact display
            self.mcp_status_label.setText(f"MCP: {tool_count} tools")
            self.mcp_status_label.setStyleSheet("font-size: 10px; color: #4a9eff;")
            
            # Full tooltip with all information
            tooltip_text = (
                f"<b>✓ MCP Tools Enabled:</b> {tool_count} tools available<br><br>"
                f"<b>Available tools:</b><br>"
                f"{'<br>'.join(tool_names)}<br><br>"
                "Claude can now use MCP tools like list_findings, create_case, etc. "
                "Just ask Claude to use them in your conversation!"
            )
            self.mcp_status_label.setToolTip(tooltip_text)
        else:
            self.mcp_status_label.setText("MCP: Not available")
            self.mcp_status_label.setStyleSheet("font-size: 10px; color: #ff4444;")
            self.mcp_status_label.setToolTip(
                "<b>✗ MCP Tools:</b> Not available<br>"
                "<i>MCP servers may not be running. Use the MCP Manager to start them.</i>"
            )
    
    def _refresh_mcp_tools(self):
        """Refresh MCP tools."""
        self.claude_service._load_mcp_tools()
        self._show_mcp_status()
        # Show brief status update instead of dialog
        tool_count = len(self.claude_service.mcp_tools)
        if tool_count > 0:
            self.mcp_status_label.setText(f"MCP: {tool_count} tools ✓")
            self.mcp_status_label.setStyleSheet("font-size: 10px; color: #4a9eff;")
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
        if not message and not self.attached_images:
            return
        
        # Build image content blocks if images are attached
        image_blocks = []
        if self.attached_images:
            for img_path in self.attached_images:
                try:
                    img_block = self.claude_service.create_image_block(img_path, source_type="base64")
                    image_blocks.append(img_block)
                except Exception as e:
                    QMessageBox.warning(self, "Image Error", f"Failed to process image {img_path}: {e}")
                    continue
        
        # Add to chat display (append, don't replace)
        display_text = f"<b>You:</b> {message if message else '[Image only]'}"
        if image_blocks:
            display_text += f" <i>({len(image_blocks)} image(s) attached)</i>"
        self.chat_display.append(f"{display_text}<br>")
        self.message_edit.clear()
        
        # Add to conversation history
        user_content = message if message else ""
        if image_blocks:
            if user_content:
                user_content = [{"type": "text", "text": user_content}] + image_blocks
            else:
                user_content = image_blocks
        self.conversation_history.append({"role": "user", "content": user_content})
        
        # Clear attached images after sending
        self.attached_images = []
        self.images_list.clear()
        self.images_group.setVisible(False)  # Hide images group after sending
        self._update_context_indicator()
        
        # Show thinking indicator
        self.chat_display.append("<b>Claude:</b> <i>Thinking...</i>")
        self._response_started = False  # Reset flag for new response
        self._scroll_to_bottom()
        
        # Create worker
        use_streaming = self.streaming_checkbox.currentText() == "Streaming"
        self.current_worker = ClaudeChatWorker(
            self.claude_service,
            user_content if isinstance(user_content, str) else message,
            context=self.conversation_history[:-1],  # Exclude current message, it's added separately
            use_streaming=use_streaming,
            images=image_blocks if image_blocks else None,
            enable_thinking=self.enable_thinking,
            thinking_budget=self.thinking_budget
        )
        self.current_worker.response_chunk.connect(self._on_response_chunk)
        self.current_worker.finished.connect(self._on_response_finished)
        self.current_worker.error.connect(self._on_error)
        self.current_worker.start()
    
    def _on_response_chunk(self, chunk: str):
        """Handle streaming response chunk."""
        if not hasattr(self, '_response_started') or not self._response_started:
            # First chunk - replace "Thinking..." with the chunk
            html = self.chat_display.toHtml()
            if "<i>Thinking...</i>" in html:
                html = html.replace(
                    "<b>Claude:</b> <i>Thinking...</i>",
                    f"<b>Claude:</b> {chunk}"
                )
                self.chat_display.setHtml(html)
                # Ensure scroll after setHtml
                self._scroll_to_bottom()
            else:
                # Fallback: append (which auto-scrolls)
                self.chat_display.append(f"<b>Claude:</b> {chunk}")
            self._response_started = True
        else:
            # Subsequent chunks - append to existing response
            cursor = self.chat_display.textCursor()
            cursor.movePosition(cursor.MoveOperation.End)
            cursor.insertText(chunk)
            self.chat_display.setTextCursor(cursor)
            # Force scroll after inserting text
            self._scroll_to_bottom()
    
    def _on_response_finished(self, full_response: str):
        """Handle response completion."""
        # Add to conversation history
        self.conversation_history.append({"role": "assistant", "content": full_response})
        
        # Reset response flag
        self._response_started = False
        
        # Ensure the response ends with a line break for readability
        self.chat_display.append("")  # Add spacing between messages
        
        self._scroll_to_bottom()
    
    def _on_error(self, error: str):
        """Handle error."""
        # Reset response flag
        self._response_started = False
        
        # Remove "Thinking..." if present
        html = self.chat_display.toHtml()
        if "<i>Thinking...</i>" in html:
            html = html.replace(
                "<b>Claude:</b> <i>Thinking...</i>",
                f"<b>Claude:</b> <font color='red'>Error: {error}</font>"
            )
            self.chat_display.setHtml(html)
        else:
            self.chat_display.append(f"<b>Error:</b> <font color='red'>{error}</font><br>")
        
        self._scroll_to_bottom()
    
    def _scroll_to_bottom(self):
        """Scroll chat display to bottom."""
        # Use the custom append method which handles scrolling
        # But also ensure scrolling here as a fallback
        scrollbar = self.chat_display.verticalScrollBar()
        max_val = scrollbar.maximum()
        scrollbar.setValue(max_val)
        
        # Force update to ensure scrolling happens
        self.chat_display.ensureCursorVisible()
    
    def _clear_history(self):
        """Clear conversation history."""
        reply = QMessageBox.question(
            self,
            "Clear History",
            "Are you sure you want to clear the conversation history?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.conversation_history = []
            self.chat_display.clear()
            self.attached_images = []
            self.images_list.clear()
            self._update_context_indicator()
            if not self.claude_service.has_api_key():
                self.chat_display.setPlainText(
                    "Please configure your Anthropic API key above to use Claude chat.\n\n"
                    "You can get an API key from: https://console.anthropic.com/"
                )
    
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
                    # Add user message to chat
                    self.chat_display.append(f"<b>You:</b> Analyze finding {finding_id}<br>")
                    self.chat_display.append("<b>Claude:</b> <i>Analyzing...</i>")
                    self._scroll_to_bottom()
                    
                    analysis = self.claude_service.analyze_finding(finding)
                    
                    # Replace "Analyzing..." with the analysis
                    current_text = self.chat_display.toHtml()
                    new_text = current_text.replace(
                        "<b>Claude:</b> <i>Analyzing...</i>",
                        f"<b>Claude:</b> {analysis.replace(chr(10), '<br>')}<br>"
                    )
                    self.chat_display.setHtml(new_text)
                    
                    # Add to conversation history
                    self.conversation_history.append({"role": "user", "content": f"Analyze finding {finding_id}"})
                    self.conversation_history.append({"role": "assistant", "content": analysis})
                    
                    self._scroll_to_bottom()
                except Exception as e:
                    error_msg = f"Failed to analyze finding: {e}"
                    QMessageBox.critical(self, "Error", error_msg)
                    self.chat_display.append(f"<b>Error:</b> <font color='red'>{error_msg}</font><br>")
                    self._scroll_to_bottom()
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
            # Add user message to chat
            self.chat_display.append(f"<b>You:</b> Correlate {len(selected_findings)} findings<br>")
            self.chat_display.append("<b>Claude:</b> <i>Correlating...</i>")
            self._scroll_to_bottom()
            
            correlation = self.claude_service.correlate_findings(selected_findings)
            
            # Replace "Correlating..." with the correlation
            current_text = self.chat_display.toHtml()
            new_text = current_text.replace(
                "<b>Claude:</b> <i>Correlating...</i>",
                f"<b>Claude:</b> {correlation.replace(chr(10), '<br>')}<br>"
            )
            self.chat_display.setHtml(new_text)
            
            # Add to conversation history
            self.conversation_history.append({"role": "user", "content": f"Correlate {len(selected_findings)} findings"})
            self.conversation_history.append({"role": "assistant", "content": correlation})
            
            self._scroll_to_bottom()
        except Exception as e:
            error_msg = f"Failed to correlate findings: {e}"
            QMessageBox.critical(self, "Error", error_msg)
            self.chat_display.append(f"<b>Error:</b> <font color='red'>{error_msg}</font><br>")
            self._scroll_to_bottom()
    
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
                    # Add user message to chat
                    self.chat_display.append(f"<b>You:</b> Generate summary for case {case_id}<br>")
                    self.chat_display.append("<b>Claude:</b> <i>Generating summary...</i>")
                    self._scroll_to_bottom()
                    
                    summary = self.claude_service.generate_case_summary(case, findings)
                    
                    # Replace "Generating summary..." with the summary
                    current_text = self.chat_display.toHtml()
                    new_text = current_text.replace(
                        "<b>Claude:</b> <i>Generating summary...</i>",
                        f"<b>Claude:</b> {summary.replace(chr(10), '<br>')}<br>"
                    )
                    self.chat_display.setHtml(new_text)
                    
                    # Add to conversation history
                    self.conversation_history.append({"role": "user", "content": f"Generate summary for case {case_id}"})
                    self.conversation_history.append({"role": "assistant", "content": summary})
                    
                    self._scroll_to_bottom()
                except Exception as e:
                    error_msg = f"Failed to generate summary: {e}"
                    QMessageBox.critical(self, "Error", error_msg)
                    self.chat_display.append(f"<b>Error:</b> <font color='red'>{error_msg}</font><br>")
                    self._scroll_to_bottom()
            else:
                QMessageBox.warning(self, "Not Found", f"Case {case_id} not found.")
    
    def _attach_image(self):
        """Attach an image file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Image",
            "",
            "Image Files (*.png *.jpg *.jpeg *.gif *.webp);;All Files (*)"
        )
        
        if file_path:
            self.attached_images.append(file_path)
            item = QListWidgetItem(Path(file_path).name)
            item.setData(Qt.ItemDataRole.UserRole, file_path)
            self.images_list.addItem(item)
            
            # Show images group when first image is attached
            if len(self.attached_images) == 1:
                self.images_group.setVisible(True)
            
            self._update_context_indicator()
    
    def _remove_image(self):
        """Remove selected image from attachment list."""
        current_item = self.images_list.currentItem()
        if current_item:
            file_path = current_item.data(Qt.ItemDataRole.UserRole)
            if file_path in self.attached_images:
                self.attached_images.remove(file_path)
            self.images_list.takeItem(self.images_list.row(current_item))
            
            # Hide images group if no images remain
            if len(self.attached_images) == 0:
                self.images_group.setVisible(False)
            
            self._update_context_indicator()
    
    def _clear_images(self):
        """Clear all attached images."""
        self.attached_images = []
        self.images_list.clear()
        self.images_group.setVisible(False)  # Hide when cleared
        self._update_context_indicator()
    
    def _on_thinking_toggled(self, checked: bool):
        """Handle thinking checkbox toggle."""
        self.enable_thinking = checked
        self.thinking_budget_spin.setEnabled(checked)
        self._update_context_indicator()
    
    def _on_thinking_budget_changed(self, value: int):
        """Handle thinking budget change."""
        self.thinking_budget = value
        self._update_context_indicator()
    
    def _update_context_indicator(self):
        """Update context window indicator with estimated token usage."""
        # Simple token estimation: ~4 characters per token for text
        message_text = self.message_edit.text()
        text_tokens = len(message_text) // 4 if message_text else 0
        
        # Estimate tokens for conversation history
        history_tokens = sum(len(str(msg.get("content", ""))) // 4 for msg in self.conversation_history)
        
        # Estimate tokens for images (rough: ~1000 tokens per image)
        image_tokens = len(self.attached_images) * 1000
        
        # Estimate thinking tokens if enabled
        thinking_tokens = self.thinking_budget if self.enable_thinking else 0
        
        # Total estimated tokens
        total_tokens = text_tokens + history_tokens + image_tokens + thinking_tokens
        
        # Update progress bar
        self.context_progress.setValue(min(total_tokens, 200000))
        
        # Update label (compact format)
        remaining = max(0, 200000 - total_tokens)
        percentage = (total_tokens / 200000) * 100 if total_tokens > 0 else 0
        self.context_label.setText(
            f"Tokens: {total_tokens:,} / 200,000 ({percentage:.1f}%) | Remaining: {remaining:,}"
        )
        
        # Color coding for progress bar
        if total_tokens > 180000:
            self.context_progress.setStyleSheet("""
                QProgressBar {
                    border: 1px solid #555;
                    border-radius: 4px;
                    background: #2a2a2a;
                }
                QProgressBar::chunk {
                    background: #ff4444;
                    border-radius: 3px;
                }
            """)
        elif total_tokens > 150000:
            self.context_progress.setStyleSheet("""
                QProgressBar {
                    border: 1px solid #555;
                    border-radius: 4px;
                    background: #2a2a2a;
                }
                QProgressBar::chunk {
                    background: #ff8800;
                    border-radius: 3px;
                }
            """)
        else:
            self.context_progress.setStyleSheet("""
                QProgressBar {
                    border: 1px solid #555;
                    border-radius: 4px;
                    background: #2a2a2a;
                }
                QProgressBar::chunk {
                    background: #4a9eff;
                    border-radius: 3px;
                }
            """)

