"""MCP server manager UI."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QTextEdit, QLabel, QGroupBox, QComboBox, QMessageBox
)
from PyQt6.QtCore import Qt, QTimer

from services.mcp_service import MCPService


class MCPManager(QWidget):
    """Widget for managing MCP servers."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.mcp_service = MCPService()
        
        self._setup_ui()
        self._setup_refresh_timer()
        self.refresh_status()
    
    def _setup_ui(self):
        """Set up the UI."""
        layout = QVBoxLayout()
        
        # Info label
        info_label = QLabel(
            "MCP Server Manager\n\n"
            "Manage and monitor MCP servers for Claude Desktop integration."
        )
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # Server status table
        status_group = QGroupBox("Server Status")
        status_layout = QVBoxLayout()
        
        self.status_table = QTableWidget()
        self.status_table.setColumnCount(4)
        self.status_table.setHorizontalHeaderLabels([
            "Server", "Status", "Actions", "Log"
        ])
        self.status_table.horizontalHeader().setStretchLastSection(True)
        self.status_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        
        status_layout.addWidget(self.status_table)
        status_group.setLayout(status_layout)
        layout.addWidget(status_group)
        
        # Control buttons
        control_layout = QHBoxLayout()
        
        start_all_btn = QPushButton("Start All")
        start_all_btn.clicked.connect(self._start_all)
        control_layout.addWidget(start_all_btn)
        
        stop_all_btn = QPushButton("Stop All")
        stop_all_btn.clicked.connect(self._stop_all)
        control_layout.addWidget(stop_all_btn)
        
        control_layout.addStretch()
        
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.refresh_status)
        control_layout.addWidget(refresh_btn)
        
        layout.addLayout(control_layout)
        
        # Log viewer
        log_group = QGroupBox("Server Logs")
        log_layout = QVBoxLayout()
        
        log_select_layout = QHBoxLayout()
        log_select_layout.addWidget(QLabel("Server:"))
        
        self.log_server_combo = QComboBox()
        self.log_server_combo.addItems(self.mcp_service.list_servers())
        self.log_server_combo.currentTextChanged.connect(self._update_log_view)
        log_select_layout.addWidget(self.log_server_combo)
        
        log_select_layout.addStretch()
        
        log_layout.addLayout(log_select_layout)
        
        self.log_view = QTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setMaximumHeight(200)
        log_layout.addWidget(self.log_view)
        
        log_group.setLayout(log_layout)
        layout.addWidget(log_group)
        
        self.setLayout(layout)
    
    def _setup_refresh_timer(self):
        """Set up automatic status refresh."""
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_status)
        self.refresh_timer.start(5000)  # Refresh every 5 seconds
    
    def refresh_status(self):
        """Refresh server status."""
        statuses = self.mcp_service.get_all_statuses()
        servers = self.mcp_service.list_servers()
        
        self.status_table.setRowCount(len(servers))
        
        for row, server_name in enumerate(servers):
            # Server name
            self.status_table.setItem(row, 0, QTableWidgetItem(server_name))
            
            # Status
            status = statuses.get(server_name, "unknown")
            status_item = QTableWidgetItem(status)
            
            if status == "running":
                status_item.setForeground(Qt.GlobalColor.green)
            elif status == "stopped":
                status_item.setForeground(Qt.GlobalColor.gray)
            else:
                status_item.setForeground(Qt.GlobalColor.red)
            
            self.status_table.setItem(row, 1, status_item)
            
            # Actions
            action_widget = QWidget()
            action_layout = QHBoxLayout()
            action_layout.setContentsMargins(2, 2, 2, 2)
            
            if status == "running":
                stop_btn = QPushButton("Stop")
                stop_btn.clicked.connect(lambda checked, name=server_name: self._stop_server(name))
                action_layout.addWidget(stop_btn)
            else:
                start_btn = QPushButton("Start")
                start_btn.clicked.connect(lambda checked, name=server_name: self._start_server(name))
                action_layout.addWidget(start_btn)
            
            action_widget.setLayout(action_layout)
            self.status_table.setCellWidget(row, 2, action_widget)
            
            # Log button
            log_btn = QPushButton("View Log")
            log_btn.clicked.connect(lambda checked, name=server_name: self._view_log(name))
            self.status_table.setCellWidget(row, 3, log_btn)
        
        self.status_table.resizeColumnsToContents()
        
        # Update log view if server is selected
        self._update_log_view()
    
    def _start_server(self, server_name: str):
        """Start a server."""
        if self.mcp_service.start_server(server_name):
            QMessageBox.information(self, "Success", f"Started server: {server_name}")
            self.refresh_status()
        else:
            QMessageBox.critical(self, "Error", f"Failed to start server: {server_name}")
    
    def _stop_server(self, server_name: str):
        """Stop a server."""
        if self.mcp_service.stop_server(server_name):
            QMessageBox.information(self, "Success", f"Stopped server: {server_name}")
            self.refresh_status()
        else:
            QMessageBox.critical(self, "Error", f"Failed to stop server: {server_name}")
    
    def _start_all(self):
        """Start all servers."""
        results = self.mcp_service.start_all()
        success_count = sum(1 for v in results.values() if v)
        total_count = len(results)
        
        if success_count == total_count:
            QMessageBox.information(self, "Success", f"Started all {total_count} servers.")
        else:
            QMessageBox.warning(
                self,
                "Partial Success",
                f"Started {success_count} of {total_count} servers."
            )
        
        self.refresh_status()
    
    def _stop_all(self):
        """Stop all servers."""
        reply = QMessageBox.question(
            self,
            "Confirm",
            "Stop all MCP servers?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            results = self.mcp_service.stop_all()
            success_count = sum(1 for v in results.values() if v)
            total_count = len(results)
            
            QMessageBox.information(self, "Success", f"Stopped {success_count} of {total_count} servers.")
            self.refresh_status()
    
    def _view_log(self, server_name: str):
        """View log for a server."""
        self.log_server_combo.setCurrentText(server_name)
        self._update_log_view()
    
    def _update_log_view(self):
        """Update log view."""
        server_name = self.log_server_combo.currentText()
        if server_name:
            log_content = self.mcp_service.get_server_log(server_name, lines=100)
            self.log_view.setPlainText(log_content)
            # Scroll to bottom
            self.log_view.verticalScrollBar().setValue(
                self.log_view.verticalScrollBar().maximum()
            )

