"""Unified settings console for configuring all services."""

import json
import logging
import subprocess
import platform
import urllib.request
import urllib.error
import ssl
import tempfile
import os
import re
import secrets
import string
import shutil
from pathlib import Path
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QMessageBox, QGroupBox, QFormLayout, QCheckBox, QComboBox, QTextEdit,
    QTabWidget, QWidget, QListWidget, QListWidgetItem, QScrollArea, QFileDialog
)
from PyQt6.QtCore import Qt, QTimer
import keyring

from services.timesketch_service import TimesketchService
from services.timesketch_docker_service import TimesketchDockerService
from services.claude_service import ClaudeService
from ui.timesketch_config import TimesketchConfigDialog
from ui.splunk_config import SplunkConfigDialog
from ui.mcp_manager import MCPManager
from ui.themes.material_config import get_available_themes, get_theme_names

logger = logging.getLogger(__name__)


def _download_file_with_ssl_fix(url: str, filepath: Path) -> bool:
    """
    Download a file from URL with SSL certificate handling.
    
    Args:
        url: URL to download from
        filepath: Path where to save the file
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Try with default SSL context first
        urllib.request.urlretrieve(url, filepath)
        return True
    except urllib.error.URLError as e:
        if "CERTIFICATE_VERIFY_FAILED" in str(e) or "SSL" in str(e):
            # SSL certificate issue - try with unverified context (less secure but works)
            logger.warning(f"SSL certificate verification failed, using unverified context: {e}")
            try:
                # Create unverified SSL context
                ssl_context = ssl.create_default_context()
                ssl_context.check_hostname = False
                ssl_context.verify_mode = ssl.CERT_NONE
                
                # Use the context
                req = urllib.request.Request(url)
                with urllib.request.urlopen(req, context=ssl_context) as response:
                    with open(filepath, 'wb') as out_file:
                        out_file.write(response.read())
                return True
            except Exception as e2:
                logger.error(f"Failed to download with unverified SSL: {e2}")
                return False
        else:
            logger.error(f"Failed to download file: {e}")
            return False
    except Exception as e:
        logger.error(f"Unexpected error downloading file: {e}")
        return False


class SettingsConsole(QDialog):
    """Unified settings console for all service configurations."""
    
    SERVICE_NAME = "deeptempo-ai-soc"
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings Console")
        self.setMinimumSize(800, 600)
        self.resize(900, 700)
        
        self._setup_ui()
        self._load_all_settings()
    
    def _setup_ui(self):
        """Set up the UI with tabs for each service."""
        layout = QVBoxLayout()
        
        # Header
        header_label = QLabel(
            "<h2>Settings Console</h2>"
            "<p>Configure all services and integrations in one place.</p>"
        )
        header_label.setWordWrap(True)
        layout.addWidget(header_label)
        
        # Tabs for different services
        self.tabs = QTabWidget()
        
        # Claude Configuration Tab
        claude_tab = self._create_claude_tab()
        self.tabs.addTab(claude_tab, "Claude AI")
        
        # Timesketch Configuration Tab
        timesketch_tab = self._create_timesketch_tab()
        self.tabs.addTab(timesketch_tab, "Timesketch")
        
        # MCP Configuration Tab
        mcp_tab = self._create_mcp_tab()
        self.tabs.addTab(mcp_tab, "MCP Servers")
        
        # S3 Configuration Tab
        s3_tab = self._create_s3_tab()
        self.tabs.addTab(s3_tab, "S3 Storage")
        
        # Splunk Configuration Tab
        splunk_tab = self._create_splunk_tab()
        self.tabs.addTab(splunk_tab, "Splunk")
        
        # General Settings Tab
        general_tab = self._create_general_tab()
        self.tabs.addTab(general_tab, "General")
        
        # Connect tab change signal to refresh Timesketch status when switching to that tab
        self.tabs.currentChanged.connect(self._on_tab_changed)
        
        layout.addWidget(self.tabs)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        test_all_btn = QPushButton("Test All Connections")
        test_all_btn.clicked.connect(self._test_all_connections)
        button_layout.addWidget(test_all_btn)
        
        button_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self._on_cancel)
        button_layout.addWidget(cancel_btn)
        
        save_btn = QPushButton("Save All")
        save_btn.clicked.connect(self._save_all_settings)
        button_layout.addWidget(save_btn)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def _create_claude_tab(self) -> QWidget:
        """Create Claude AI configuration tab."""
        # Create scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        # Create content widget
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Info
        info_label = QLabel(
            "<b>Claude AI Configuration</b><br>"
            "Configure your Anthropic API key for Claude AI integration."
        )
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # API Key
        key_group = QGroupBox("API Key")
        key_layout = QFormLayout()
        
        self.claude_key_edit = QLineEdit()
        self.claude_key_edit.setPlaceholderText("Enter your Anthropic API key...")
        self.claude_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        key_layout.addRow("API Key:", self.claude_key_edit)
        
        show_key_checkbox = QCheckBox("Show API Key")
        show_key_checkbox.toggled.connect(
            lambda checked: self.claude_key_edit.setEchoMode(
                QLineEdit.EchoMode.Normal if checked else QLineEdit.EchoMode.Password
            )
        )
        key_layout.addRow("", show_key_checkbox)
        
        key_group.setLayout(key_layout)
        layout.addWidget(key_group)
        
        # Model Selection
        model_group = QGroupBox("Model Settings")
        model_layout = QFormLayout()
        
        self.claude_model_combo = QComboBox()
        self.claude_model_combo.addItems([
            "claude-sonnet-4-5-20250929",
            "claude-haiku-4-5-20251001",
            "claude-opus-4-5-20251101",
            "claude-sonnet-4-20250514",
            "claude-3-5-sonnet-20240620",
            "claude-3-opus-20240229",
            "claude-3-sonnet-20240229",
            "claude-3-haiku-20240307"
        ])
        model_layout.addRow("Model:", self.claude_model_combo)
        
        self.claude_max_tokens_edit = QLineEdit()
        self.claude_max_tokens_edit.setPlaceholderText("4096")
        model_layout.addRow("Max Tokens:", self.claude_max_tokens_edit)
        
        model_group.setLayout(model_layout)
        layout.addWidget(model_group)
        
        # Test Connection
        test_btn = QPushButton("Test Connection")
        test_btn.clicked.connect(self._test_claude_connection)
        layout.addWidget(test_btn)
        
        # Status
        self.claude_status_label = QLabel("Status: Not configured")
        layout.addWidget(self.claude_status_label)
        
        # Claude Desktop Integration Instructions
        integration_group = QGroupBox("Claude Desktop Integration")
        integration_layout = QVBoxLayout()
        
        instructions_text = QLabel(
            "<b>To connect Claude Desktop to DeepTempo AI SOC MCP servers:</b><br><br>"
            "<b>Option 1: Use Local MCP Configuration (Recommended)</b><br>"
            "1. Go to File → Configure Claude Desktop... in this application<br>"
            "2. Configure your project and virtual environment paths<br>"
            "3. Click 'Save Configuration'<br>"
            "4. Restart Claude Desktop<br><br>"
            "<b>Option 2: Add Custom Connector in Claude Desktop</b><br>"
            "1. Open Claude Desktop<br>"
            "2. Go to Settings → Connectors<br>"
            "3. Click 'Add custom connector'<br>"
            "4. Enter connector name: <b>DeepTempoSOC</b><br>"
            "5. For Remote MCP server URL, use one of:<br>"
            "   • <code>http://localhost:8000</code> (if running MCP server locally)<br>"
            "   • Your remote MCP server URL<br>"
            "6. Click 'Add'<br><br>"
            "<b>Available MCP Servers:</b><br>"
            "• deeptempo-findings: Security findings management<br>"
            "• evidence-snippets: Evidence snippet storage<br>"
            "• case-store: Investigation case management<br><br>"
            "<i>Note: The local configuration method (Option 1) is recommended as it "
            "automatically configures all MCP servers correctly.</i>"
        )
        instructions_text.setWordWrap(True)
        instructions_text.setOpenExternalLinks(True)
        integration_layout.addWidget(instructions_text)
        
        # Show current MCP config path
        mcp_path_layout = QHBoxLayout()
        mcp_path_label = QLabel("<b>MCP Config Path:</b>")
        mcp_path_layout.addWidget(mcp_path_label)
        
        self.mcp_path_value = QLabel()
        mcp_path = self._get_mcp_config_path()
        if mcp_path:
            self.mcp_path_value.setText(f"<code>{mcp_path}</code>")
        else:
            self.mcp_path_value.setText("Not configured")
        self.mcp_path_value.setWordWrap(True)
        mcp_path_layout.addWidget(self.mcp_path_value)
        mcp_path_layout.addStretch()
        integration_layout.addLayout(mcp_path_layout)
        
        # Button to open MCP config
        open_mcp_btn = QPushButton("Open Claude Desktop Configuration Manager")
        open_mcp_btn.clicked.connect(self._open_mcp_config_from_claude_tab)
        integration_layout.addWidget(open_mcp_btn)
        
        integration_group.setLayout(integration_layout)
        layout.addWidget(integration_group)
        
        widget.setLayout(layout)
        scroll.setWidget(widget)
        return scroll
    
    def _create_timesketch_tab(self) -> QWidget:
        """Create Timesketch configuration tab."""
        # Create scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        # Create content widget
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Info
        info_label = QLabel(
            "<b>Timesketch Configuration</b><br>"
            "Configure your Timesketch server connection for timeline analysis."
        )
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # Timesketch Installation Section
        install_group = QGroupBox("Timesketch Installation")
        install_layout = QVBoxLayout()
        
        install_info = QLabel(
            "<b>Quick Install:</b> Automatically download and run the official Timesketch deployment script. "
            "This will set up Timesketch with all required services (PostgreSQL, OpenSearch, Redis, etc.)."
        )
        install_info.setWordWrap(True)
        install_layout.addWidget(install_info)
        
        # Installation status check
        self.ts_installation_status_label = QLabel("Checking installation status...")
        self.ts_installation_status_label.setWordWrap(True)
        install_layout.addWidget(self.ts_installation_status_label)
        
        install_btn_row = QHBoxLayout()
        self.ts_install_btn = QPushButton("🚀 Install Timesketch")
        self.ts_install_btn.setStyleSheet("font-weight: bold; padding: 8px;")
        self.ts_install_btn.clicked.connect(self._install_timesketch)
        install_btn_row.addWidget(self.ts_install_btn)
        
        self.ts_remove_btn = QPushButton("🗑️ Remove Timesketch")
        self.ts_remove_btn.setStyleSheet("font-weight: bold; padding: 8px;")
        self.ts_remove_btn.clicked.connect(self._remove_timesketch)
        install_btn_row.addWidget(self.ts_remove_btn)
        
        install_btn_row.addStretch()
        install_layout.addLayout(install_btn_row)
        
        self.ts_install_status_label = QLabel("")
        self.ts_install_status_label.setWordWrap(True)
        install_layout.addWidget(self.ts_install_status_label)
        
        install_group.setLayout(install_layout)
        layout.addWidget(install_group)
        
        # Docker Management Section
        docker_group = QGroupBox("Docker Server Management")
        docker_layout = QFormLayout()
        
        # Docker CLI status
        self.ts_docker_cli_status_label = QLabel("Checking...")
        docker_layout.addRow("Docker CLI:", self.ts_docker_cli_status_label)
        
        # Docker daemon status
        self.ts_docker_daemon_status_label = QLabel("Checking...")
        docker_layout.addRow("Docker Daemon:", self.ts_docker_daemon_status_label)
        
        # Container status
        self.ts_container_status_label = QLabel("Checking...")
        docker_layout.addRow("Container Status:", self.ts_container_status_label)
        
        # Docker daemon controls
        daemon_controls_row = QHBoxLayout()
        
        self.ts_start_daemon_btn = QPushButton("Start Docker Daemon")
        self.ts_start_daemon_btn.clicked.connect(self._start_docker_daemon)
        daemon_controls_row.addWidget(self.ts_start_daemon_btn)
        
        daemon_controls_row.addStretch()
        docker_layout.addRow("", daemon_controls_row)
        
        # Container controls
        container_controls_row = QHBoxLayout()
        
        self.ts_start_docker_btn = QPushButton("Start Timesketch Container")
        self.ts_start_docker_btn.clicked.connect(self._start_timesketch_docker)
        container_controls_row.addWidget(self.ts_start_docker_btn)
        
        self.ts_stop_docker_btn = QPushButton("Stop Timesketch Container")
        self.ts_stop_docker_btn.clicked.connect(self._stop_timesketch_docker)
        container_controls_row.addWidget(self.ts_stop_docker_btn)
        
        refresh_status_btn = QPushButton("Refresh Status")
        refresh_status_btn.clicked.connect(self._refresh_timesketch_docker_status)
        container_controls_row.addWidget(refresh_status_btn)
        
        container_controls_row.addStretch()
        docker_layout.addRow("", container_controls_row)
        
        # Docker configuration
        docker_config_info = QLabel(
            "<b>Note:</b> Timesketch requires a multi-service setup (PostgreSQL, Elasticsearch, etc.). "
            "A single-container image is not available. Use docker-compose or configure an existing server."
        )
        docker_config_info.setWordWrap(True)
        docker_config_info.setStyleSheet("color: #666; font-style: italic;")
        docker_layout.addRow("", docker_config_info)
        
        # Docker image configuration
        self.ts_docker_image_edit = QLineEdit()
        self.ts_docker_image_edit.setPlaceholderText("Leave empty to use docker-compose or custom image")
        self.ts_docker_image_edit.setToolTip(
            "Custom Docker image name (e.g., your-registry/timesketch:tag). "
            "Leave empty if using docker-compose."
        )
        docker_layout.addRow("Docker Image (optional):", self.ts_docker_image_edit)
        
        # Docker compose path
        docker_compose_row = QHBoxLayout()
        self.ts_docker_compose_edit = QLineEdit()
        self.ts_docker_compose_edit.setPlaceholderText("Path to docker-compose.yml (optional)")
        self.ts_docker_compose_edit.setToolTip(
            "Path to docker-compose.yml file for Timesketch. "
            "If provided, docker-compose will be used instead of single container."
        )
        docker_compose_row.addWidget(self.ts_docker_compose_edit)
        
        browse_compose_btn = QPushButton("Browse...")
        browse_compose_btn.clicked.connect(self._browse_docker_compose)
        docker_compose_row.addWidget(browse_compose_btn)
        docker_layout.addRow("Docker Compose File:", docker_compose_row)
        
        # Setup instructions link
        setup_instructions_btn = QPushButton("📖 View Timesketch Docker Setup Instructions")
        setup_instructions_btn.clicked.connect(self._show_timesketch_docker_instructions)
        docker_layout.addRow("", setup_instructions_btn)
        
        # Auto-start option
        self.ts_auto_start_docker_checkbox = QCheckBox("Auto-start Docker server on application launch")
        docker_layout.addRow("", self.ts_auto_start_docker_checkbox)
        
        docker_group.setLayout(docker_layout)
        layout.addWidget(docker_group)
        
        # Server Configuration
        server_group = QGroupBox("Server Configuration")
        server_layout = QFormLayout()
        
        self.ts_server_url_edit = QLineEdit()
        self.ts_server_url_edit.setPlaceholderText("http://localhost:5000 or https://timesketch.example.com")
        # Set default for local development
        self.ts_server_url_edit.setText("http://localhost:5000")
        server_layout.addRow("Server URL:", self.ts_server_url_edit)
        
        # Quick setup buttons
        quick_setup_layout = QHBoxLayout()
        localhost_btn = QPushButton("Use Localhost (Default)")
        localhost_btn.clicked.connect(lambda: self.ts_server_url_edit.setText("http://localhost:5000"))
        quick_setup_layout.addWidget(localhost_btn)
        
        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(lambda: self.ts_server_url_edit.clear())
        quick_setup_layout.addWidget(clear_btn)
        
        quick_setup_layout.addStretch()
        server_layout.addRow("", quick_setup_layout)
        
        self.ts_verify_ssl_checkbox = QCheckBox("Verify SSL certificates")
        self.ts_verify_ssl_checkbox.setChecked(True)
        server_layout.addRow("", self.ts_verify_ssl_checkbox)
        
        server_group.setLayout(server_layout)
        layout.addWidget(server_group)
        
        # Authentication
        auth_group = QGroupBox("Authentication")
        auth_layout = QFormLayout()
        
        self.ts_auth_method_combo = QComboBox()
        self.ts_auth_method_combo.addItems(["Username/Password", "API Token"])
        self.ts_auth_method_combo.currentIndexChanged.connect(self._on_ts_auth_method_changed)
        auth_layout.addRow("Method:", self.ts_auth_method_combo)
        
        self.ts_username_edit = QLineEdit()
        self.ts_username_edit.setPlaceholderText("Enter username...")
        auth_layout.addRow("Username:", self.ts_username_edit)
        
        self.ts_password_edit = QLineEdit()
        self.ts_password_edit.setPlaceholderText("Enter password...")
        self.ts_password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        auth_layout.addRow("Password:", self.ts_password_edit)
        
        self.ts_token_edit = QLineEdit()
        self.ts_token_edit.setPlaceholderText("Enter API token...")
        self.ts_token_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.ts_token_edit.setVisible(False)
        auth_layout.addRow("API Token:", self.ts_token_edit)
        
        auth_group.setLayout(auth_layout)
        layout.addWidget(auth_group)
        
        # Sync Settings
        sync_group = QGroupBox("Sync Settings")
        sync_layout = QFormLayout()
        
        self.ts_auto_sync_checkbox = QCheckBox("Enable auto-sync")
        sync_layout.addRow("", self.ts_auto_sync_checkbox)
        
        self.ts_sync_interval_edit = QLineEdit()
        self.ts_sync_interval_edit.setPlaceholderText("300")
        self.ts_sync_interval_edit.setToolTip("Sync interval in seconds (default: 300)")
        sync_layout.addRow("Sync Interval (seconds):", self.ts_sync_interval_edit)
        
        sync_group.setLayout(sync_layout)
        layout.addWidget(sync_group)
        
        # Test Connection
        test_btn = QPushButton("Test Connection")
        test_btn.clicked.connect(self._test_timesketch_connection)
        layout.addWidget(test_btn)
        
        # Status
        self.ts_status_label = QLabel("Status: Not configured")
        layout.addWidget(self.ts_status_label)
        
        widget.setLayout(layout)
        scroll.setWidget(widget)
        
        # Initialize Docker service and status timer AFTER widget is fully set up
        # Load Docker config if available
        docker_image = None
        docker_compose_path = None
        try:
            config_file = TimesketchConfigDialog.CONFIG_FILE
            if config_file.exists():
                with open(config_file, 'r') as f:
                    config = json.load(f)
                    # Only use image if it's explicitly set (not empty string)
                    docker_image = config.get('docker_image')
                    if docker_image and docker_image.strip():
                        docker_image = docker_image.strip()
                    else:
                        docker_image = None
                    docker_compose_path = config.get('docker_compose_path')
                    if docker_compose_path and docker_compose_path.strip():
                        docker_compose_path = docker_compose_path.strip()
                    else:
                        docker_compose_path = None
        except Exception:
            pass
        
        self.ts_docker_service = TimesketchDockerService(
            image=docker_image,
            docker_compose_path=docker_compose_path
        )
        self.ts_status_timer = QTimer()
        self.ts_status_timer.timeout.connect(self._refresh_timesketch_docker_status)
        self.ts_status_timer.start(5000)  # Update every 5 seconds
        # Initial status check after a short delay to ensure UI is ready
        QTimer.singleShot(500, self._refresh_timesketch_docker_status)
        
        return scroll
    
    def _create_mcp_tab(self) -> QWidget:
        """Create MCP servers configuration tab using the full MCPManager widget."""
        # Create scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        # Use the full MCPManager widget instead of a simple status view
        mcp_manager = MCPManager(self)
        scroll.setWidget(mcp_manager)
        return scroll
    
    def _create_s3_tab(self) -> QWidget:
        """Create S3 configuration tab."""
        # Create scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        # Create content widget
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Info
        info_label = QLabel(
            "<b>AWS S3 Configuration</b><br>"
            "Configure S3 bucket access to analyze findings and cases from cloud storage."
        )
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # Instructions Button
        instructions_btn = QPushButton("📖 View S3 Setup Instructions")
        instructions_btn.clicked.connect(self._show_s3_instructions)
        layout.addWidget(instructions_btn)
        
        # S3 Configuration
        s3_group = QGroupBox("S3 Bucket Configuration")
        s3_layout = QFormLayout()
        
        self.s3_bucket_edit = QLineEdit()
        self.s3_bucket_edit.setPlaceholderText("my-bucket-name")
        s3_layout.addRow("Bucket Name:", self.s3_bucket_edit)
        
        self.s3_region_combo = QComboBox()
        self.s3_region_combo.setEditable(True)
        self.s3_region_combo.addItems([
            "us-east-1", "us-east-2", "us-west-1", "us-west-2",
            "eu-west-1", "eu-west-2", "eu-central-1", "ap-southeast-1",
            "ap-southeast-2", "ap-northeast-1"
        ])
        self.s3_region_combo.setCurrentText("us-east-1")
        s3_layout.addRow("Region:", self.s3_region_combo)
        
        s3_group.setLayout(s3_layout)
        layout.addWidget(s3_group)
        
        # AWS Credentials
        creds_group = QGroupBox("AWS Credentials")
        creds_layout = QVBoxLayout()
        
        creds_info = QLabel(
            "You can provide AWS credentials here, or use the default credential chain "
            "(environment variables, IAM role, ~/.aws/credentials, etc.)."
        )
        creds_info.setWordWrap(True)
        creds_layout.addWidget(creds_info)
        
        # Access Key ID
        access_key_label = QLabel("Access Key ID:")
        creds_layout.addWidget(access_key_label)
        
        access_key_row = QHBoxLayout()
        self.s3_access_key_edit = QLineEdit()
        self.s3_access_key_edit.setPlaceholderText("Optional - leave empty to use default credentials")
        self.s3_access_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        access_key_row.addWidget(self.s3_access_key_edit)
        
        show_key_checkbox = QCheckBox("Show")
        show_key_checkbox.toggled.connect(
            lambda checked: self.s3_access_key_edit.setEchoMode(
                QLineEdit.EchoMode.Normal if checked else QLineEdit.EchoMode.Password
            )
        )
        access_key_row.addWidget(show_key_checkbox)
        creds_layout.addLayout(access_key_row)
        
        # Add spacing
        creds_layout.addSpacing(10)
        
        # Secret Access Key
        secret_key_label = QLabel("Secret Access Key:")
        creds_layout.addWidget(secret_key_label)
        
        secret_key_row = QHBoxLayout()
        self.s3_secret_key_edit = QLineEdit()
        self.s3_secret_key_edit.setPlaceholderText("Optional - leave empty to use default credentials")
        self.s3_secret_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        secret_key_row.addWidget(self.s3_secret_key_edit)
        
        show_secret_checkbox = QCheckBox("Show")
        show_secret_checkbox.toggled.connect(
            lambda checked: self.s3_secret_key_edit.setEchoMode(
                QLineEdit.EchoMode.Normal if checked else QLineEdit.EchoMode.Password
            )
        )
        secret_key_row.addWidget(show_secret_checkbox)
        creds_layout.addLayout(secret_key_row)
        
        creds_group.setLayout(creds_layout)
        layout.addWidget(creds_group)
        
        # File Paths
        paths_group = QGroupBox("S3 File Paths")
        paths_layout = QFormLayout()
        
        self.s3_findings_path_edit = QLineEdit()
        self.s3_findings_path_edit.setPlaceholderText("findings.json")
        self.s3_findings_path_edit.setText("findings.json")
        paths_layout.addRow("Findings File Path:", self.s3_findings_path_edit)
        
        self.s3_cases_path_edit = QLineEdit()
        self.s3_cases_path_edit.setPlaceholderText("cases.json")
        self.s3_cases_path_edit.setText("cases.json")
        paths_layout.addRow("Cases File Path:", self.s3_cases_path_edit)
        
        paths_group.setLayout(paths_layout)
        layout.addWidget(paths_group)
        
        # Test Connection
        test_btn = QPushButton("Test Connection")
        test_btn.clicked.connect(self._test_s3_connection)
        layout.addWidget(test_btn)
        
        # Status
        self.s3_status_label = QLabel("Status: Not configured")
        layout.addWidget(self.s3_status_label)
        
        widget.setLayout(layout)
        scroll.setWidget(widget)
        return scroll
    
    def _create_splunk_tab(self) -> QWidget:
        """Create Splunk configuration tab."""
        # Create scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        # Create content widget
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Info
        info_label = QLabel(
            "<b>Splunk Configuration</b><br>"
            "Configure connection to your Splunk server for data enrichment."
        )
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # Quick Config Button
        quick_config_btn = QPushButton("⚙️ Open Splunk Configuration Dialog")
        quick_config_btn.clicked.connect(self._open_splunk_config_dialog)
        layout.addWidget(quick_config_btn)
        
        # Connection Settings
        conn_group = QGroupBox("Connection Settings")
        conn_layout = QFormLayout()
        
        self.splunk_server_url_edit = QLineEdit()
        self.splunk_server_url_edit.setPlaceholderText("https://splunk.example.com:8089")
        conn_layout.addRow("Server URL:", self.splunk_server_url_edit)
        
        self.splunk_username_edit = QLineEdit()
        self.splunk_username_edit.setPlaceholderText("admin")
        conn_layout.addRow("Username:", self.splunk_username_edit)
        
        self.splunk_password_edit = QLineEdit()
        self.splunk_password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.splunk_password_edit.setPlaceholderText("Enter password...")
        conn_layout.addRow("Password:", self.splunk_password_edit)
        
        self.splunk_verify_ssl_checkbox = QCheckBox("Verify SSL Certificate")
        self.splunk_verify_ssl_checkbox.setChecked(False)
        conn_layout.addRow("", self.splunk_verify_ssl_checkbox)
        
        conn_group.setLayout(conn_layout)
        layout.addWidget(conn_group)
        
        # Test Connection
        test_btn = QPushButton("Test Connection")
        test_btn.clicked.connect(self._test_splunk_connection)
        layout.addWidget(test_btn)
        
        # Status
        self.splunk_status_label = QLabel("Status: Not configured")
        layout.addWidget(self.splunk_status_label)
        
        # Usage Instructions
        usage_group = QGroupBox("Using Splunk Enrichment")
        usage_layout = QVBoxLayout()
        
        usage_text = QLabel(
            "<b>How to enrich cases with Splunk data:</b><br><br>"
            "1. Configure your Splunk connection above<br>"
            "2. Click 'Test Connection' to verify it works<br>"
            "3. Save your settings<br>"
            "4. Go to Cases view<br>"
            "5. Select a case<br>"
            "6. Click 'Enrich with Splunk' button<br><br>"
            "<b>What happens during enrichment:</b><br>"
            "• Indicators (IPs, domains, hashes, etc.) are extracted from the case<br>"
            "• Splunk is queried for events related to those indicators<br>"
            "• Claude AI analyzes the data and provides insights<br>"
            "• Results are added to the case notes<br><br>"
            "<i>Note: Enrichment may take 1-2 minutes depending on the amount of data.</i>"
        )
        usage_text.setWordWrap(True)
        usage_text.setTextFormat(Qt.TextFormat.RichText)
        usage_layout.addWidget(usage_text)
        
        usage_group.setLayout(usage_layout)
        layout.addWidget(usage_group)
        
        layout.addStretch()
        
        widget.setLayout(layout)
        scroll.setWidget(widget)
        return scroll
    
    def _create_general_tab(self) -> QWidget:
        """Create general settings tab."""
        # Create scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        # Create content widget
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Info
        info_label = QLabel(
            "<b>General Settings</b><br>"
            "Configure general application preferences."
        )
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # Application Settings
        app_group = QGroupBox("Application Settings")
        app_layout = QFormLayout()
        
        self.auto_start_checkbox = QCheckBox("Start auto-sync on application start")
        app_layout.addRow("", self.auto_start_checkbox)
        
        self.show_notifications_checkbox = QCheckBox("Show desktop notifications")
        app_layout.addRow("", self.show_notifications_checkbox)
        
        app_group.setLayout(app_layout)
        layout.addWidget(app_group)
        
        # Theme Settings
        theme_group = QGroupBox("Theme Settings")
        theme_layout = QFormLayout()
        
        self.theme_combo = QComboBox()
        theme_names = get_theme_names()
        available_themes = get_available_themes()
        
        # Map theme names to display names
        for theme_name in theme_names:
            theme_info = next((t for t in available_themes if t.get('file', '').replace('.xml', '') == theme_name), None)
            if theme_info:
                display_name = theme_info['name']
            else:
                # Fallback: format theme name
                display_name = theme_name.replace('_', ' ').title()
            self.theme_combo.addItem(display_name, theme_name)
        
        # Load current theme
        current_theme = self._load_theme_preference()
        theme_index = self.theme_combo.findData(current_theme)
        if theme_index >= 0:
            self.theme_combo.setCurrentIndex(theme_index)
        
        theme_layout.addRow("Theme:", self.theme_combo)
        
        theme_info = QLabel(
            "<i>Theme changes will take effect after restarting the application.</i>"
        )
        theme_info.setWordWrap(True)
        theme_layout.addRow("", theme_info)
        
        theme_group.setLayout(theme_layout)
        layout.addWidget(theme_group)
        
        # Data Settings
        data_group = QGroupBox("Data Settings")
        data_layout = QFormLayout()
        
        data_path_label = QLabel()
        data_path = Path(__file__).parent.parent / "data"
        data_path_label.setText(f"<b>Data Directory:</b> {data_path}")
        data_layout.addRow("", data_path_label)
        
        data_group.setLayout(data_layout)
        layout.addWidget(data_group)
        
        # About
        about_group = QGroupBox("About")
        about_layout = QVBoxLayout()
        
        about_text = QLabel(
            "<b>DeepTempo AI SOC</b><br>"
            "Security Operations Center with AI-powered analysis<br><br>"
            "Version: 1.0.0"
        )
        about_text.setWordWrap(True)
        about_layout.addWidget(about_text)
        
        about_group.setLayout(about_layout)
        layout.addWidget(about_group)
        
        widget.setLayout(layout)
        scroll.setWidget(widget)
        return scroll
    
    def _on_tab_changed(self, index: int):
        """Handle tab change - refresh Timesketch status when switching to Timesketch tab."""
        if self.tabs.tabText(index) == "Timesketch":
            self._check_timesketch_installation_status()
    
    def _on_ts_auth_method_changed(self, index: int):
        """Handle Timesketch authentication method change."""
        if index == 0:  # Username/Password
            self.ts_username_edit.setVisible(True)
            self.ts_password_edit.setVisible(True)
            self.ts_token_edit.setVisible(False)
        else:  # API Token
            self.ts_username_edit.setVisible(False)
            self.ts_password_edit.setVisible(False)
            self.ts_token_edit.setVisible(True)
    
    def _load_all_settings(self):
        """Load all settings from storage."""
        # Load Claude settings
        self._load_claude_settings()
        
        # Load Timesketch settings
        self._load_timesketch_settings()
        
        # Check Timesketch installation status
        self._check_timesketch_installation_status()
        
        # Load S3 settings
        self._load_s3_settings()
        
        # Load Splunk settings
        self._load_splunk_settings()
        
        # Load general settings
        self._load_general_settings()
    
    def _load_claude_settings(self):
        """Load Claude AI settings."""
        try:
            # Try to get API key from keyring
            api_key = keyring.get_password(self.SERVICE_NAME, "claude_api_key")
            if api_key:
                self.claude_key_edit.setText(api_key)
                self.claude_status_label.setText("Status: ✓ Configured")
            else:
                self.claude_status_label.setText("Status: Not configured")
        except Exception:
            self.claude_status_label.setText("Status: Not configured")
        
        # Load model settings (from config file or defaults)
        try:
            config_file = Path.home() / '.deeptempo' / 'claude_config.json'
            if config_file.exists():
                with open(config_file, 'r') as f:
                    config = json.load(f)
                    model = config.get('model', 'claude-sonnet-4-5-20250929')
                    max_tokens = config.get('max_tokens', 4096)
                    
                    index = self.claude_model_combo.findText(model)
                    if index >= 0:
                        self.claude_model_combo.setCurrentIndex(index)
                    self.claude_max_tokens_edit.setText(str(max_tokens))
        except Exception:
            pass
    
    def _load_timesketch_settings(self):
        """Load Timesketch settings."""
        config_file = TimesketchConfigDialog.CONFIG_FILE
        if not config_file.exists():
            # Set default localhost URL if no config exists
            if not self.ts_server_url_edit.text():
                self.ts_server_url_edit.setText("http://localhost:5000")
            self.ts_status_label.setText("Status: Not configured (using default localhost)")
            return
        
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
            
            self.ts_server_url_edit.setText(config.get('server_url', ''))
            self.ts_verify_ssl_checkbox.setChecked(config.get('verify_ssl', True))
            
            auth_method = config.get('auth_method', 'password')
            if auth_method == 'token':
                self.ts_auth_method_combo.setCurrentIndex(1)
            else:
                self.ts_auth_method_combo.setCurrentIndex(0)
            
            # Load sensitive data from keyring
            try:
                if auth_method == 'password':
                    username = keyring.get_password(
                        self.SERVICE_NAME, TimesketchConfigDialog.KEYRING_USERNAME
                    )
                    password = keyring.get_password(
                        self.SERVICE_NAME, TimesketchConfigDialog.KEYRING_PASSWORD
                    )
                    if username:
                        self.ts_username_edit.setText(username)
                    if password:
                        self.ts_password_edit.setText(password)
                else:
                    token = keyring.get_password(
                        self.SERVICE_NAME, TimesketchConfigDialog.KEYRING_TOKEN
                    )
                    if token:
                        self.ts_token_edit.setText(token)
            except Exception:
                pass
            
            self.ts_auto_sync_checkbox.setChecked(config.get('auto_sync', False))
            self.ts_sync_interval_edit.setText(str(config.get('sync_interval', 300)))
            
            # Load Docker auto-start setting
            self.ts_auto_start_docker_checkbox.setChecked(config.get('auto_start_docker', False))
            
            # Load Docker configuration
            if hasattr(self, 'ts_docker_image_edit'):
                self.ts_docker_image_edit.setText(config.get('docker_image', ''))
            if hasattr(self, 'ts_docker_compose_edit'):
                docker_compose_path = config.get('docker_compose_path', '')
                # Auto-detect docker-compose.yml if not in config but timesketch directory exists
                if not docker_compose_path:
                    cwd = Path.cwd()
                    timesketch_dir = cwd / "timesketch"
                    if timesketch_dir.exists() and timesketch_dir.is_dir():
                        compose_file = timesketch_dir / "docker-compose.yml"
                        compose_file_yaml = timesketch_dir / "docker-compose.yaml"
                        
                        if compose_file.exists():
                            docker_compose_path = str(compose_file)
                        elif compose_file_yaml.exists():
                            docker_compose_path = str(compose_file_yaml)
                        
                        # Save to config if we auto-detected it
                        if docker_compose_path:
                            try:
                                config['docker_compose_path'] = docker_compose_path
                                with open(config_file, 'w') as f:
                                    json.dump(config, f, indent=2)
                            except Exception:
                                pass  # Don't fail if we can't update config
                
                self.ts_docker_compose_edit.setText(docker_compose_path)
            
            if config.get('server_url'):
                self.ts_status_label.setText("Status: ✓ Configured")
            else:
                self.ts_status_label.setText("Status: Not configured")
        
        except Exception as e:
            logger.error(f"Error loading Timesketch settings: {e}")
            self.ts_status_label.setText("Status: Error loading configuration")
    
    def _load_s3_settings(self):
        """Load S3 settings."""
        try:
            config_file = Path.home() / '.deeptempo' / 's3_config.json'
            if config_file.exists():
                with open(config_file, 'r') as f:
                    config = json.load(f)
                    
                    self.s3_bucket_edit.setText(config.get('bucket_name', ''))
                    self.s3_region_combo.setCurrentText(config.get('region', 'us-east-1'))
                    self.s3_findings_path_edit.setText(config.get('findings_path', 'findings.json'))
                    self.s3_cases_path_edit.setText(config.get('cases_path', 'cases.json'))
                    
                    if config.get('bucket_name'):
                        self.s3_status_label.setText("Status: ✓ Configured")
                    else:
                        self.s3_status_label.setText("Status: Not configured")
            
            # Load credentials from keyring
            try:
                access_key = keyring.get_password(self.SERVICE_NAME, "s3_access_key_id")
                secret_key = keyring.get_password(self.SERVICE_NAME, "s3_secret_access_key")
                
                if access_key:
                    self.s3_access_key_edit.setText(access_key)
                if secret_key:
                    self.s3_secret_key_edit.setText(secret_key)
            except Exception:
                pass
        except Exception as e:
            logger.error(f"Error loading S3 settings: {e}")
            self.s3_status_label.setText("Status: Error loading configuration")
    
    def _save_s3_settings(self) -> bool:
        """Save S3 settings."""
        bucket_name = self.s3_bucket_edit.text().strip()
        if not bucket_name:
            # Allow saving without bucket (user might configure later)
            pass
        
        try:
            config = {
                'bucket_name': bucket_name,
                'region': self.s3_region_combo.currentText(),
                'findings_path': self.s3_findings_path_edit.text().strip() or 'findings.json',
                'cases_path': self.s3_cases_path_edit.text().strip() or 'cases.json'
            }
            
            # Save config file
            config_file = Path.home() / '.deeptempo' / 's3_config.json'
            config_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=2)
            
            # Save credentials to keyring
            access_key = self.s3_access_key_edit.text().strip()
            secret_key = self.s3_secret_key_edit.text().strip()
            
            if access_key:
                keyring.set_password(self.SERVICE_NAME, "s3_access_key_id", access_key)
            if secret_key:
                keyring.set_password(self.SERVICE_NAME, "s3_secret_access_key", secret_key)
        except Exception as e:
            print(f"Error saving S3 settings: {e}")
            return False
        
        return True
    
    def _save_splunk_settings(self) -> bool:
        """Save Splunk settings."""
        server_url = self.splunk_server_url_edit.text().strip()
        username = self.splunk_username_edit.text().strip()
        password = self.splunk_password_edit.text()
        
        if not server_url or not username:
            # Allow saving without full config (user might configure later)
            pass
        
        try:
            config = {
                'server_url': server_url,
                'username': username,
                'password': password,
                'verify_ssl': self.splunk_verify_ssl_checkbox.isChecked(),
                'lookback_hours': 168  # Default 7 days
            }
            
            # Save config file
            config_file = SplunkConfigDialog.CONFIG_FILE
            config_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=2)
            
            logger.info("Splunk settings saved")
            return True
        
        except Exception as e:
            logger.error(f"Error saving Splunk settings: {e}")
            QMessageBox.critical(self, "Error", f"Failed to save Splunk settings:\n{e}")
            return False
            
            return True
        
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save S3 settings:\n{e}")
            return False
    
    def _test_s3_connection(self):
        """Test S3 connection."""
        bucket_name = self.s3_bucket_edit.text().strip()
        if not bucket_name:
            QMessageBox.warning(self, "Validation Error", "Please enter a bucket name first.")
            return
        
        region = self.s3_region_combo.currentText()
        access_key = self.s3_access_key_edit.text().strip()
        secret_key = self.s3_secret_key_edit.text().strip()
        
        try:
            from services.s3_service import S3Service
            
            service = S3Service(
                bucket_name=bucket_name,
                region_name=region,
                aws_access_key_id=access_key if access_key else None,
                aws_secret_access_key=secret_key if secret_key else None
            )
            
            success, message = service.test_connection()
            
            if success:
                QMessageBox.information(self, "Success", f"S3 connection successful!\n\n{message}")
                self.s3_status_label.setText("Status: ✓ Connected")
            else:
                QMessageBox.critical(self, "Connection Failed", f"Could not connect to S3:\n\n{message}")
                self.s3_status_label.setText("Status: ✗ Connection failed")
        
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Connection test failed:\n{e}")
            self.s3_status_label.setText("Status: ✗ Error")
    
    def _open_splunk_config_dialog(self):
        """Open the Splunk configuration dialog."""
        dialog = SplunkConfigDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Reload settings after successful configuration
            self._load_splunk_settings()
            QMessageBox.information(
                self,
                "Configuration Saved",
                "Splunk configuration has been saved.\n\n"
                "You can now use 'Enrich with Splunk' on your cases."
            )
    
    def _test_splunk_connection(self):
        """Test Splunk connection."""
        server_url = self.splunk_server_url_edit.text().strip()
        username = self.splunk_username_edit.text().strip()
        password = self.splunk_password_edit.text()
        
        if not server_url or not username or not password:
            QMessageBox.warning(self, "Validation Error", "Please enter server URL, username, and password first.")
            return
        
        verify_ssl = self.splunk_verify_ssl_checkbox.isChecked()
        
        try:
            from services.splunk_service import SplunkService
            
            service = SplunkService(
                server_url=server_url,
                username=username,
                password=password,
                verify_ssl=verify_ssl
            )
            
            success, message = service.test_connection()
            
            if success:
                QMessageBox.information(self, "Success", f"Splunk connection successful!\n\n{message}")
                self.splunk_status_label.setText("Status: ✓ Connected")
            else:
                QMessageBox.critical(self, "Connection Failed", f"Could not connect to Splunk:\n\n{message}")
                self.splunk_status_label.setText("Status: ✗ Connection failed")
        
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Connection test failed:\n{e}")
            self.splunk_status_label.setText("Status: ✗ Error")
    
    def _load_splunk_settings(self):
        """Load Splunk settings."""
        try:
            config_file = SplunkConfigDialog.CONFIG_FILE
            if config_file.exists():
                with open(config_file, 'r') as f:
                    config = json.load(f)
                
                self.splunk_server_url_edit.setText(config.get('server_url', ''))
                self.splunk_username_edit.setText(config.get('username', ''))
                self.splunk_password_edit.setText(config.get('password', ''))
                self.splunk_verify_ssl_checkbox.setChecked(config.get('verify_ssl', False))
                
                self.splunk_status_label.setText("Status: ✓ Configured")
            else:
                self.splunk_status_label.setText("Status: Not configured")
        
        except Exception as e:
            logger.error(f"Error loading Splunk settings: {e}")
            self.splunk_status_label.setText("Status: ✗ Error loading settings")
    
    def _load_general_settings(self):
        """Load general settings."""
        try:
            config_file = Path.home() / '.deeptempo' / 'app_config.json'
            if config_file.exists():
                with open(config_file, 'r') as f:
                    config = json.load(f)
                    self.auto_start_checkbox.setChecked(config.get('auto_start', False))
                    self.show_notifications_checkbox.setChecked(config.get('show_notifications', True))
        except Exception:
            pass
    
    def _load_theme_preference(self) -> str:
        """Load saved theme preference from config file."""
        try:
            config_file = Path.home() / '.deeptempo' / 'theme_config.json'
            if config_file.exists():
                with open(config_file, 'r') as f:
                    config = json.load(f)
                    return config.get('theme', 'dark_blue')
        except Exception:
            pass
        return 'dark_blue'  # Default theme
    
    def _save_all_settings(self):
        """Save all settings."""
        # Save Claude settings
        if not self._save_claude_settings():
            return
        
        # Save Timesketch settings
        if not self._save_timesketch_settings():
            return
        
        # Save S3 settings
        if not self._save_s3_settings():
            return
        
        # Save Splunk settings
        if not self._save_splunk_settings():
            return
        
        # Save general settings
        self._save_general_settings()
        
        QMessageBox.information(self, "Success", "All settings saved successfully!")
        # Stop status timer before closing
        if hasattr(self, 'ts_status_timer'):
            self.ts_status_timer.stop()
        self.accept()
    
    def _save_claude_settings(self) -> bool:
        """Save Claude AI settings."""
        api_key = self.claude_key_edit.text().strip()
        if not api_key:
            reply = QMessageBox.question(
                self,
                "No API Key",
                "No API key entered. Continue without saving Claude configuration?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.No:
                return False
        
        try:
            # Save API key to keyring
            if api_key:
                keyring.set_password(self.SERVICE_NAME, "claude_api_key", api_key)
            
            # Save model settings
            config_file = Path.home() / '.deeptempo' / 'claude_config.json'
            config_file.parent.mkdir(parents=True, exist_ok=True)
            
            config = {
                'model': self.claude_model_combo.currentText(),
                'max_tokens': int(self.claude_max_tokens_edit.text() or '4096')
            }
            
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=2)
            
            return True
        
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save Claude settings:\n{e}")
            return False
    
    def _save_timesketch_settings(self) -> bool:
        """Save Timesketch settings."""
        server_url = self.ts_server_url_edit.text().strip()
        if not server_url:
            # Allow saving without server URL (user might configure later)
            pass
        
        try:
            config = {
                'server_url': server_url,
                'verify_ssl': self.ts_verify_ssl_checkbox.isChecked(),
                'auth_method': 'token' if self.ts_auth_method_combo.currentIndex() == 1 else 'password',
                'auto_sync': self.ts_auto_sync_checkbox.isChecked(),
                'sync_interval': int(self.ts_sync_interval_edit.text() or '300'),
                'auto_start_docker': self.ts_auto_start_docker_checkbox.isChecked()
            }
            
            # Save Docker configuration
            if hasattr(self, 'ts_docker_image_edit'):
                docker_image = self.ts_docker_image_edit.text().strip()
                if docker_image:
                    config['docker_image'] = docker_image
            if hasattr(self, 'ts_docker_compose_edit'):
                docker_compose_path = self.ts_docker_compose_edit.text().strip()
                if docker_compose_path:
                    config['docker_compose_path'] = docker_compose_path
            
            # Save sensitive data to keyring
            if config['auth_method'] == 'password':
                username = self.ts_username_edit.text().strip()
                password = self.ts_password_edit.text().strip()
                if username:
                    keyring.set_password(self.SERVICE_NAME, TimesketchConfigDialog.KEYRING_USERNAME, username)
                if password:
                    keyring.set_password(self.SERVICE_NAME, TimesketchConfigDialog.KEYRING_PASSWORD, password)
            else:
                token = self.ts_token_edit.text().strip()
                if token:
                    keyring.set_password(self.SERVICE_NAME, TimesketchConfigDialog.KEYRING_TOKEN, token)
            
            # Save config file (without sensitive data)
            config_file = TimesketchConfigDialog.CONFIG_FILE
            config_file.parent.mkdir(parents=True, exist_ok=True)
            
            safe_config = config.copy()
            safe_config['password'] = ''
            safe_config['api_token'] = ''
            
            with open(config_file, 'w') as f:
                json.dump(safe_config, f, indent=2)
            
            return True
        
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save Timesketch settings:\n{e}")
            return False
    
    def _save_general_settings(self):
        """Save general settings."""
        try:
            config_file = Path.home() / '.deeptempo' / 'app_config.json'
            config_file.parent.mkdir(parents=True, exist_ok=True)
            
            config = {
                'auto_start': self.auto_start_checkbox.isChecked(),
                'show_notifications': self.show_notifications_checkbox.isChecked()
            }
            
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=2)
            
            # Save theme preference
            theme_config_file = Path.home() / '.deeptempo' / 'theme_config.json'
            selected_theme = self.theme_combo.currentData()
            if selected_theme:
                theme_config = {
                    'theme': selected_theme
                }
                with open(theme_config_file, 'w') as f:
                    json.dump(theme_config, f, indent=2)
        
        except Exception as e:
            logger.error(f"Error saving general settings: {e}")
    
    def _test_claude_connection(self):
        """Test Claude AI connection."""
        api_key = self.claude_key_edit.text().strip()
        if not api_key:
            QMessageBox.warning(self, "Validation Error", "Please enter an API key first.")
            return
        
        try:
            service = ClaudeService(api_key=api_key)
            # Simple test - try to create a client
            if service.client:
                QMessageBox.information(self, "Success", "Claude AI connection successful!")
                self.claude_status_label.setText("Status: ✓ Connected")
            else:
                QMessageBox.critical(self, "Error", "Failed to initialize Claude service.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Connection test failed:\n{e}")
    
    def _refresh_timesketch_docker_status(self):
        """Refresh Docker and container status."""
        # Check if widgets exist (might not be initialized yet)
        if not hasattr(self, 'ts_docker_service') or not hasattr(self, 'ts_docker_cli_status_label'):
            return
        
        try:
            # Check Docker CLI availability
            if not self.ts_docker_service.is_docker_available():
                self.ts_docker_cli_status_label.setText("✗ Not installed")
                if hasattr(self, 'ts_docker_daemon_status_label'):
                    self.ts_docker_daemon_status_label.setText("N/A")
                if hasattr(self, 'ts_container_status_label'):
                    self.ts_container_status_label.setText("N/A")
                if hasattr(self, 'ts_start_daemon_btn'):
                    self.ts_start_daemon_btn.setEnabled(False)
                if hasattr(self, 'ts_start_docker_btn'):
                    self.ts_start_docker_btn.setEnabled(False)
                if hasattr(self, 'ts_stop_docker_btn'):
                    self.ts_stop_docker_btn.setEnabled(False)
                return
            
            self.ts_docker_cli_status_label.setText("✓ Installed")
            
            # Check Docker daemon status
            daemon_status = self.ts_docker_service.get_docker_daemon_status()
            if hasattr(self, 'ts_docker_daemon_status_label'):
                if daemon_status.get('daemon_running'):
                    self.ts_docker_daemon_status_label.setText("✓ Running")
                    if hasattr(self, 'ts_start_daemon_btn'):
                        self.ts_start_daemon_btn.setEnabled(False)
                else:
                    self.ts_docker_daemon_status_label.setText("✗ Not running")
                    if hasattr(self, 'ts_start_daemon_btn'):
                        self.ts_start_daemon_btn.setEnabled(True)
                    # Disable container controls if daemon is not running
                    if hasattr(self, 'ts_start_docker_btn'):
                        self.ts_start_docker_btn.setEnabled(False)
                    if hasattr(self, 'ts_stop_docker_btn'):
                        self.ts_stop_docker_btn.setEnabled(False)
                    if hasattr(self, 'ts_container_status_label'):
                        self.ts_container_status_label.setText("N/A (daemon not running)")
                    return
            
            # Check container status (only if daemon is running)
            if daemon_status.get('daemon_running'):
                status = self.ts_docker_service.get_container_status()
                if hasattr(self, 'ts_container_status_label'):
                    if status.get('running'):
                        self.ts_container_status_label.setText("✓ Running")
                        if hasattr(self, 'ts_start_docker_btn'):
                            self.ts_start_docker_btn.setEnabled(False)
                        if hasattr(self, 'ts_stop_docker_btn'):
                            self.ts_stop_docker_btn.setEnabled(True)
                    elif status.get('exists'):
                        self.ts_container_status_label.setText("○ Stopped")
                        if hasattr(self, 'ts_start_docker_btn'):
                            self.ts_start_docker_btn.setEnabled(True)
                        if hasattr(self, 'ts_stop_docker_btn'):
                            self.ts_stop_docker_btn.setEnabled(True)
                    else:
                        self.ts_container_status_label.setText("○ Not found")
                        if hasattr(self, 'ts_start_docker_btn'):
                            self.ts_start_docker_btn.setEnabled(True)
                        if hasattr(self, 'ts_stop_docker_btn'):
                            self.ts_stop_docker_btn.setEnabled(False)
        except Exception as e:
            logger.error(f"Error refreshing Docker status: {e}")
    
    def _start_docker_daemon(self):
        """Start Docker daemon."""
        if not hasattr(self, 'ts_docker_service'):
            QMessageBox.warning(self, "Error", "Docker service not initialized")
            return
        
        # Check if already running
        if self.ts_docker_service.is_docker_daemon_running():
            QMessageBox.information(self, "Info", "Docker daemon is already running.")
            self._refresh_timesketch_docker_status()
            return
        
        reply = QMessageBox.question(
            self,
            "Start Docker Daemon",
            "This will attempt to start the Docker daemon. On macOS, this will open Docker Desktop.\n\n"
            "Continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.ts_start_daemon_btn.setEnabled(False)
            self.ts_start_daemon_btn.setText("Starting...")
            
            success, message = self.ts_docker_service.start_docker_daemon()
            
            self.ts_start_daemon_btn.setEnabled(True)
            self.ts_start_daemon_btn.setText("Start Docker Daemon")
            
            if success:
                QMessageBox.information(self, "Success", message)
                # Refresh status after a short delay to allow daemon to fully start
                QTimer.singleShot(2000, self._refresh_timesketch_docker_status)
            else:
                QMessageBox.warning(
                    self,
                    "Docker Daemon Start",
                    f"{message}\n\n"
                    "If Docker Desktop is not installed, please install it from:\n"
                    "https://www.docker.com/products/docker-desktop"
                )
                self._refresh_timesketch_docker_status()
    
    def _start_timesketch_docker(self):
        """Start Timesketch Docker container."""
        if not hasattr(self, 'ts_docker_service'):
            QMessageBox.warning(self, "Error", "Docker service not initialized")
            return
        
        # Check if Docker daemon is running first
        if not self.ts_docker_service.is_docker_daemon_running():
            reply = QMessageBox.question(
                self,
                "Docker Daemon Not Running",
                "Docker daemon is not running. Would you like to start it first?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self._start_docker_daemon()
                # Wait a bit and check again
                QTimer.singleShot(3000, lambda: self._check_and_start_container())
                return
            else:
                return
        
        self._check_and_start_container()
    
    def _check_and_start_container(self):
        """Check daemon status and start container if daemon is running."""
        if not self.ts_docker_service.is_docker_daemon_running():
            QMessageBox.warning(
                self,
                "Docker Daemon Not Running",
                "Docker daemon is still not running. Please start Docker Desktop manually and try again."
            )
            self._refresh_timesketch_docker_status()
            return
        
        # Get Docker configuration
        docker_image = None
        docker_compose_path = None
        if hasattr(self, 'ts_docker_image_edit'):
            docker_image = self.ts_docker_image_edit.text().strip() or None
        if hasattr(self, 'ts_docker_compose_edit'):
            docker_compose_path = self.ts_docker_compose_edit.text().strip() or None
        
        # Auto-detect docker-compose.yml if not set but timesketch directory exists
        if not docker_compose_path and not docker_image:
            cwd = Path.cwd()
            timesketch_dir = cwd / "timesketch"
            if timesketch_dir.exists() and timesketch_dir.is_dir():
                compose_file = timesketch_dir / "docker-compose.yml"
                compose_file_yaml = timesketch_dir / "docker-compose.yaml"
                
                if compose_file.exists():
                    docker_compose_path = str(compose_file)
                    # Update UI field
                    if hasattr(self, 'ts_docker_compose_edit'):
                        self.ts_docker_compose_edit.setText(docker_compose_path)
                elif compose_file_yaml.exists():
                    docker_compose_path = str(compose_file_yaml)
                    # Update UI field
                    if hasattr(self, 'ts_docker_compose_edit'):
                        self.ts_docker_compose_edit.setText(docker_compose_path)
        
        # Validate configuration - need either docker-compose or custom image
        if not docker_compose_path and not docker_image:
            QMessageBox.warning(
                self,
                "Docker Configuration Required",
                "Please configure Timesketch Docker setup before starting:\n\n"
                "Option 1: Set Docker Compose File path (recommended)\n"
                "Option 2: Enter a custom Docker image name\n\n"
                "Click 'View Timesketch Docker Setup Instructions' for help."
            )
            return
        
        # Update Docker service with configuration
        # Only set image if a custom one is provided (not the default)
        if docker_image:
            self.ts_docker_service.image = docker_image
        else:
            # Clear the default image to prevent using non-existent default
            self.ts_docker_service.image = None
        
        if docker_compose_path:
            self.ts_docker_service.docker_compose_path = docker_compose_path
        else:
            self.ts_docker_service.docker_compose_path = None
        
        # Get port from server URL
        server_url = self.ts_server_url_edit.text().strip()
        port = 5000  # default
        if server_url.startswith("http://localhost:"):
            try:
                port = int(server_url.split(":")[-1].split("/")[0])
            except ValueError:
                pass
        
        self.ts_start_docker_btn.setEnabled(False)
        self.ts_start_docker_btn.setText("Starting...")
        
        success, message = self.ts_docker_service.start_container(port=port)
        
        self.ts_start_docker_btn.setEnabled(True)
        self.ts_start_docker_btn.setText("Start Timesketch Container")
        
        if success:
            QMessageBox.information(self, "Success", message)
            self._refresh_timesketch_docker_status()
        else:
            QMessageBox.critical(self, "Error", f"Failed to start Docker container:\n\n{message}")
            self._refresh_timesketch_docker_status()
    
    def _stop_timesketch_docker(self):
        """Stop Timesketch Docker container."""
        if not hasattr(self, 'ts_docker_service'):
            QMessageBox.warning(self, "Error", "Docker service not initialized")
            return
        
        reply = QMessageBox.question(
            self,
            "Stop Container",
            "Are you sure you want to stop the Timesketch Docker container?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.ts_stop_docker_btn.setEnabled(False)
            success, message = self.ts_docker_service.stop_container()
            self.ts_stop_docker_btn.setEnabled(True)
            
            if success:
                QMessageBox.information(self, "Success", message)
                self._refresh_timesketch_docker_status()
            else:
                QMessageBox.critical(self, "Error", f"Failed to stop Docker container:\n\n{message}")
    
    def _test_timesketch_connection(self):
        """Test Timesketch connection."""
        server_url = self.ts_server_url_edit.text().strip()
        if not server_url:
            QMessageBox.warning(self, "Validation Error", "Please enter a server URL first.")
            return
        
        auth_method = self.ts_auth_method_combo.currentIndex()
        if auth_method == 0:  # Username/Password
            username = self.ts_username_edit.text().strip()
            password = self.ts_password_edit.text().strip()
            if not username or not password:
                QMessageBox.warning(self, "Validation Error", "Please enter username and password.")
                return
            api_token = None
        else:  # API Token
            api_token = self.ts_token_edit.text().strip()
            if not api_token:
                QMessageBox.warning(self, "Validation Error", "Please enter an API token.")
                return
            username = None
            password = None
        
        try:
            service = TimesketchService(
                server_url=server_url,
                username=username,
                password=password,
                api_token=api_token
            )
            
            success, message = service.test_connection()
            
            if success:
                QMessageBox.information(self, "Success", f"Timesketch connection successful!\n\n{message}")
                self.ts_status_label.setText("Status: ✓ Connected")
            else:
                QMessageBox.critical(self, "Connection Failed", f"Could not connect to Timesketch:\n\n{message}")
                self.ts_status_label.setText("Status: ✗ Connection failed")
        
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Connection test failed:\n{e}")
            self.ts_status_label.setText("Status: ✗ Error")
    
    def _test_all_connections(self):
        """Test all service connections."""
        results = []
        
        # Test Claude
        api_key = self.claude_key_edit.text().strip()
        if api_key:
            try:
                service = ClaudeService(api_key=api_key)
                if service.client:
                    results.append("✓ Claude AI: Connected")
                else:
                    results.append("✗ Claude AI: Failed")
            except Exception as e:
                results.append(f"✗ Claude AI: {str(e)}")
        else:
            results.append("○ Claude AI: Not configured")
        
        # Test S3
        bucket_name = self.s3_bucket_edit.text().strip()
        if bucket_name:
            try:
                from services.s3_service import S3Service
                region = self.s3_region_combo.currentText()
                access_key = self.s3_access_key_edit.text().strip()
                secret_key = self.s3_secret_key_edit.text().strip()
                
                service = S3Service(
                    bucket_name=bucket_name,
                    region_name=region,
                    aws_access_key_id=access_key if access_key else None,
                    aws_secret_access_key=secret_key if secret_key else None
                )
                
                success, message = service.test_connection()
                if success:
                    results.append("✓ S3: Connected")
                else:
                    results.append(f"✗ S3: {message}")
            except Exception as e:
                results.append(f"✗ S3: {str(e)}")
        else:
            results.append("○ S3: Not configured")
        
        # Test Timesketch
        server_url = self.ts_server_url_edit.text().strip()
        if server_url:
            try:
                auth_method = self.ts_auth_method_combo.currentIndex()
                if auth_method == 0:
                    username = self.ts_username_edit.text().strip()
                    password = self.ts_password_edit.text().strip()
                    service = TimesketchService(server_url=server_url, username=username, password=password)
                else:
                    token = self.ts_token_edit.text().strip()
                    service = TimesketchService(server_url=server_url, api_token=token)
                
                success, message = service.test_connection()
                if success:
                    results.append("✓ Timesketch: Connected")
                else:
                    results.append(f"✗ Timesketch: {message}")
            except Exception as e:
                results.append(f"✗ Timesketch: {str(e)}")
        else:
            results.append("○ Timesketch: Not configured")
        
        # Show results
        QMessageBox.information(
            self,
            "Connection Test Results",
            "Connection Test Results:\n\n" + "\n".join(results)
        )
    
    def _get_mcp_config_path(self) -> str:
        """Get MCP configuration file path."""
        from ui.config_manager import ConfigManager
        return str(ConfigManager.get_config_path())
    
    def _open_mcp_config(self):
        """Open MCP configuration."""
        from ui.config_manager import ConfigManager
        manager = ConfigManager(self)
        manager.exec()
    
    def _open_mcp_config_from_claude_tab(self):
        """Open MCP configuration from Claude tab."""
        self._open_mcp_config()
        # Refresh MCP path display after config might have changed
        mcp_path = self._get_mcp_config_path()
        if mcp_path:
            self.mcp_path_value.setText(f"<code>{mcp_path}</code>")
        else:
            self.mcp_path_value.setText("Not configured")
    
    def _on_cancel(self):
        """Handle cancel button - stop timers and close."""
        if hasattr(self, 'ts_status_timer'):
            self.ts_status_timer.stop()
        self.reject()
    
    def _check_timesketch_installation_status(self):
        """Check if Timesketch is already installed and configured."""
        if not hasattr(self, 'ts_installation_status_label'):
            return
        
        config_file = TimesketchConfigDialog.CONFIG_FILE
        cwd = Path.cwd()
        timesketch_dir = cwd / "timesketch"
        
        has_config = config_file.exists()
        has_directory = timesketch_dir.exists() and timesketch_dir.is_dir()
        
        # Check for docker-compose files
        compose_file = None
        compose_file_yaml = None
        has_compose = False
        
        if has_directory:
            compose_file = timesketch_dir / "docker-compose.yml"
            compose_file_yaml = timesketch_dir / "docker-compose.yaml"
            has_compose = compose_file.exists() or compose_file_yaml.exists()
            
            # Auto-populate docker-compose path if not already set
            if hasattr(self, 'ts_docker_compose_edit'):
                current_path = self.ts_docker_compose_edit.text().strip()
                if not current_path:
                    # Try docker-compose.yml first, then docker-compose.yaml
                    if compose_file.exists():
                        self.ts_docker_compose_edit.setText(str(compose_file))
                        # Also save to config if config file exists
                        if has_config:
                            try:
                                with open(config_file, 'r') as f:
                                    config = json.load(f)
                                config['docker_compose_path'] = str(compose_file)
                                with open(config_file, 'w') as f:
                                    json.dump(config, f, indent=2)
                            except Exception:
                                pass  # Don't fail if we can't update config
                    elif compose_file_yaml.exists():
                        self.ts_docker_compose_edit.setText(str(compose_file_yaml))
                        # Also save to config if config file exists
                        if has_config:
                            try:
                                with open(config_file, 'r') as f:
                                    config = json.load(f)
                                config['docker_compose_path'] = str(compose_file_yaml)
                                with open(config_file, 'w') as f:
                                    json.dump(config, f, indent=2)
                            except Exception:
                                pass  # Don't fail if we can't update config
            
            # Update Docker service with auto-detected path
            if hasattr(self, 'ts_docker_service'):
                detected_compose = None
                if compose_file.exists():
                    detected_compose = str(compose_file)
                elif compose_file_yaml.exists():
                    detected_compose = str(compose_file_yaml)
                
                if detected_compose and not self.ts_docker_service.docker_compose_path:
                    self.ts_docker_service.docker_compose_path = detected_compose
        
        # Status logic: If directory exists with docker-compose, it's installed
        # Config file is optional (only needed for connection settings)
        if has_directory and has_compose:
            if has_config:
                self.ts_installation_status_label.setText(
                    f"<b>Status:</b> ✓ Timesketch is installed and configured<br>"
                    f"• Configuration: {config_file}<br>"
                    f"• Installation directory: {timesketch_dir}<br>"
                    f"• Docker Compose: {compose_file.name if compose_file and compose_file.exists() else compose_file_yaml.name if compose_file_yaml and compose_file_yaml.exists() else 'Not found'}"
                )
                self.ts_installation_status_label.setStyleSheet("color: green;")
            else:
                self.ts_installation_status_label.setText(
                    f"<b>Status:</b> ✓ Timesketch is installed<br>"
                    f"• Installation directory: {timesketch_dir}<br>"
                    f"• Docker Compose: {compose_file.name if compose_file and compose_file.exists() else compose_file_yaml.name if compose_file_yaml and compose_file_yaml.exists() else 'Not found'}<br>"
                    f"• Connection settings: Not configured (optional)"
                )
                self.ts_installation_status_label.setStyleSheet("color: green;")
        elif has_directory:
            self.ts_installation_status_label.setText(
                f"<b>Status:</b> ⚠ Timesketch directory exists but docker-compose.yml not found<br>"
                f"• Installation directory: {timesketch_dir}<br>"
                f"• Docker Compose file missing"
            )
            self.ts_installation_status_label.setStyleSheet("color: orange;")
        elif has_config:
            self.ts_installation_status_label.setText(
                f"<b>Status:</b> ⚠ Timesketch is configured but installation directory not found<br>"
                f"• Configuration: {config_file}<br>"
                f"• Installation directory: {timesketch_dir} (not found)"
            )
            self.ts_installation_status_label.setStyleSheet("color: orange;")
        else:
            self.ts_installation_status_label.setText(
                "<b>Status:</b> Timesketch is not installed"
            )
            self.ts_installation_status_label.setStyleSheet("color: gray;")
    
    def _remove_timesketch(self):
        """Remove Timesketch installation (containers, directory, and optionally config)."""
        # Check if anything is installed
        config_file = TimesketchConfigDialog.CONFIG_FILE
        cwd = Path.cwd()
        timesketch_dir = cwd / "timesketch"
        
        has_config = config_file.exists()
        has_directory = timesketch_dir.exists() and timesketch_dir.is_dir()
        
        if not has_config and not has_directory:
            QMessageBox.information(
                self,
                "Nothing to Remove",
                "Timesketch is not installed. There's nothing to remove."
            )
            return
        
        # Build confirmation message
        items_to_remove = []
        if has_directory:
            items_to_remove.append(f"• Timesketch directory: {timesketch_dir}")
        if has_config:
            items_to_remove.append(f"• Configuration file: {config_file}")
        
        reply = QMessageBox.question(
            self,
            "Remove Timesketch Installation",
            "This will remove the following:\n\n" + "\n".join(items_to_remove) + "\n\n"
            "It will also:\n"
            "• Stop and remove all Docker containers\n"
            "• Remove Docker volumes (data will be lost)\n\n"
            "Do you want to continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        self.ts_remove_btn.setEnabled(False)
        self.ts_remove_btn.setText("Removing...")
        self.ts_install_status_label.setText("Removing Timesketch installation...")
        
        try:
            # Step 1: Stop and remove Docker containers if docker-compose path exists
            if has_directory:
                compose_file = timesketch_dir / "docker-compose.yml"
                if compose_file.exists():
                    self.ts_install_status_label.setText("Stopping Docker containers...")
                    compose_dir = compose_file.parent
                    
                    # Try to stop containers using docker-compose
                    try:
                        # Check for docker compose v2
                        result = subprocess.run(
                            ["docker", "compose", "version"],
                            capture_output=True,
                            text=True,
                            timeout=5,
                            stderr=subprocess.DEVNULL
                        )
                        
                        if result.returncode == 0:
                            compose_cmd = ["docker", "compose"]
                        else:
                            # Try legacy docker-compose
                            result = subprocess.run(
                                ["docker-compose", "--version"],
                                capture_output=True,
                                text=True,
                                timeout=5,
                                stderr=subprocess.DEVNULL
                            )
                            if result.returncode == 0:
                                compose_cmd = ["docker-compose"]
                            else:
                                compose_cmd = None
                        
                        if compose_cmd:
                            # Stop containers
                            subprocess.run(
                                compose_cmd + ["-f", "docker-compose.yml", "down", "-v"],
                                cwd=compose_dir,
                                capture_output=True,
                                text=True,
                                timeout=60
                            )
                            self.ts_install_status_label.setText("Docker containers stopped and removed.")
                    except Exception as e:
                        logger.warning(f"Error stopping Docker containers: {e}")
                        # Continue with removal even if Docker stop fails
            
            # Step 2: Remove the timesketch directory
            if has_directory:
                self.ts_install_status_label.setText("Removing Timesketch directory...")
                try:
                    shutil.rmtree(timesketch_dir)
                    logger.info(f"Removed Timesketch directory: {timesketch_dir}")
                except Exception as e:
                    logger.error(f"Error removing Timesketch directory: {e}")
                    QMessageBox.warning(
                        self,
                        "Partial Removal",
                        f"Could not remove Timesketch directory:\n{timesketch_dir}\n\n"
                        f"Error: {str(e)}\n\n"
                        "You may need to remove it manually."
                    )
            
            # Step 3: Ask about removing configuration
            if has_config:
                reply = QMessageBox.question(
                    self,
                    "Remove Configuration?",
                    "Do you also want to remove the Timesketch configuration file?\n\n"
                    f"{config_file}\n\n"
                    "This will remove all server connection settings.",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No
                )
                
                if reply == QMessageBox.StandardButton.Yes:
                    try:
                        config_file.unlink()
                        logger.info(f"Removed Timesketch config file: {config_file}")
                        
                        # Also remove from keyring
                        try:
                            keyring.delete_password(self.SERVICE_NAME, TimesketchConfigDialog.KEYRING_USERNAME)
                            keyring.delete_password(self.SERVICE_NAME, TimesketchConfigDialog.KEYRING_PASSWORD)
                            keyring.delete_password(self.SERVICE_NAME, TimesketchConfigDialog.KEYRING_TOKEN)
                        except Exception:
                            pass  # Keyring entries may not exist
                        
                        # Clear UI fields
                        self.ts_server_url_edit.clear()
                        self.ts_username_edit.clear()
                        self.ts_password_edit.clear()
                        self.ts_token_edit.clear()
                        if hasattr(self, 'ts_docker_compose_edit'):
                            self.ts_docker_compose_edit.clear()
                        if hasattr(self, 'ts_docker_image_edit'):
                            self.ts_docker_image_edit.clear()
                    except Exception as e:
                        logger.error(f"Error removing config file: {e}")
                        QMessageBox.warning(
                            self,
                            "Config Removal Failed",
                            f"Could not remove configuration file:\n{config_file}\n\n"
                            f"Error: {str(e)}"
                        )
            
            # Update status
            self._check_timesketch_installation_status()
            self.ts_install_status_label.setText("Timesketch installation removed successfully.")
            
            QMessageBox.information(
                self,
                "Removal Complete",
                "Timesketch installation has been removed successfully."
            )
            
        except Exception as e:
            logger.error(f"Error removing Timesketch: {e}")
            QMessageBox.critical(
                self,
                "Removal Error",
                f"An error occurred during removal:\n\n{str(e)}"
            )
            self.ts_install_status_label.setText("")
        finally:
            self.ts_remove_btn.setEnabled(True)
            self.ts_remove_btn.setText("🗑️ Remove Timesketch")
    
    def _install_timesketch(self):
        """Download and set up Timesketch using the appropriate method for the platform."""
        # Check if already installed
        cwd = Path.cwd()
        timesketch_dir = cwd / "timesketch"
        
        if timesketch_dir.exists():
            reply = QMessageBox.question(
                self,
                "Timesketch Already Installed",
                f"Timesketch directory already exists at:\n{timesketch_dir}\n\n"
                "Do you want to remove the existing installation first?\n\n"
                "Click 'Yes' to remove and reinstall, or 'No' to cancel.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                # Remove existing installation first
                self._remove_timesketch()
                # Wait a moment for cleanup
                import time
                time.sleep(1)
            else:
                return
        
        system = platform.system().lower()
        
        # For Linux, use the deployment script
        if system == "linux":
            self._install_timesketch_linux()
        # For macOS and Windows, use docker-compose directly
        elif system == "darwin":  # macOS
            self._install_timesketch_macos()
        elif system == "windows":
            self._install_timesketch_windows()
        else:
            QMessageBox.warning(
                self,
                "Platform Not Supported",
                f"Unsupported platform: {system}\n\n"
                "Please install Timesketch manually or use a Linux VM."
            )
    
    def _install_timesketch_linux(self):
        """Install Timesketch on Linux using the deployment script."""
        
        # Confirm installation
        reply = QMessageBox.question(
            self,
            "Install Timesketch (Linux)",
            "This will download and run the official Timesketch deployment script.\n\n"
            "Requirements:\n"
            "- Ubuntu 22.04 (or compatible Linux)\n"
            "- Docker and docker-compose installed\n"
            "- Root/sudo access\n"
            "- At least 8GB RAM\n\n"
            "The script will:\n"
            "1. Create a 'timesketch' directory in the current working directory\n"
            "2. Download and configure all Timesketch services\n"
            "3. Set up PostgreSQL, OpenSearch, Redis, and Nginx\n\n"
            "Continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        self.ts_install_btn.setEnabled(False)
        self.ts_install_btn.setText("Installing...")
        self.ts_install_status_label.setText("Downloading deployment script...")
        
        try:
            # Get current working directory (where script will create timesketch directory)
            cwd = Path.cwd()
            script_path = cwd / "deploy_timesketch.sh"
            
            # Check if script already exists
            if script_path.exists():
                reply = QMessageBox.question(
                    self,
                    "Script Already Exists",
                    f"The deployment script already exists at:\n{script_path}\n\n"
                    "Do you want to download it again?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No
                )
                if reply != QMessageBox.StandardButton.Yes:
                    self.ts_install_btn.setEnabled(True)
                    self.ts_install_btn.setText("🚀 Install Timesketch")
                    self.ts_install_status_label.setText("")
                    return
            
            # Check if timesketch directory already exists
            timesketch_dir = cwd / "timesketch"
            if timesketch_dir.exists():
                QMessageBox.warning(
                    self,
                    "Timesketch Already Installed",
                    f"Timesketch directory already exists at:\n{timesketch_dir}\n\n"
                    "The deployment script will not run if the directory exists.\n\n"
                    "If you want to reinstall, please remove or rename the existing directory first."
                )
                self.ts_install_btn.setEnabled(True)
                self.ts_install_btn.setText("🚀 Install Timesketch")
                self.ts_install_status_label.setText("")
                return
            
            # Download the script
            script_url = "https://raw.githubusercontent.com/google/timesketch/master/contrib/deploy_timesketch.sh"
            self.ts_install_status_label.setText(f"Downloading script from {script_url}...")
            
            if not _download_file_with_ssl_fix(script_url, script_path):
                error_msg = "Failed to download the deployment script.\n\n"
                system = platform.system()
                if system == "Darwin":  # macOS
                    error_msg += "SSL certificate verification failed. On macOS, you may need to:\n\n"
                    error_msg += "1. Install certificates (run in Terminal):\n"
                    error_msg += "   /Applications/Python\\ 3.x/Install\\ Certificates.command\n\n"
                    error_msg += "2. Or upgrade certifi:\n"
                    error_msg += "   python3 -m pip install --upgrade certifi\n\n"
                    error_msg += "The helper function should have retried with unverified SSL.\n"
                    error_msg += "If this error persists, please check your internet connection."
                else:
                    error_msg += "Please check your internet connection and SSL certificate configuration."
                
                self.ts_install_status_label.setText("")
                QMessageBox.critical(
                    self,
                    "Download Failed",
                    error_msg
                )
                self.ts_install_btn.setEnabled(True)
                self.ts_install_btn.setText("🚀 Install Timesketch")
                return
            
            # Make script executable
            self.ts_install_status_label.setText("Making script executable...")
            os.chmod(script_path, 0o755)
            
            # Run the script with sudo
            self.ts_install_status_label.setText(
                "Running deployment script with sudo...\n\n"
                "You will be prompted for your sudo password.\n"
                "This may take several minutes. Please wait..."
            )
            
            # Show a message about sudo
            QMessageBox.information(
                self,
                "Sudo Password Required",
                "The deployment script requires root access.\n\n"
                "A terminal window will open asking for your sudo password.\n\n"
                "After entering your password, the installation will proceed.\n\n"
                "You can monitor progress in the terminal window."
            )
            
            # Run the script in a new terminal window so user can see progress and enter sudo password
            # Try different terminal emulators
            terminal_cmd = None
            if os.path.exists("/usr/bin/gnome-terminal"):
                terminal_cmd = ["gnome-terminal", "--", "bash", "-c", f"cd {cwd} && sudo ./deploy_timesketch.sh; echo ''; echo 'Press Enter to close...'; read"]
            elif os.path.exists("/usr/bin/xterm"):
                terminal_cmd = ["xterm", "-e", f"cd {cwd} && sudo ./deploy_timesketch.sh; echo ''; echo 'Press Enter to close...'; read"]
            elif os.path.exists("/usr/bin/konsole"):
                terminal_cmd = ["konsole", "-e", f"bash -c 'cd {cwd} && sudo ./deploy_timesketch.sh; echo \"\"; echo \"Press Enter to close...\"; read'"]
            else:
                # Fallback: try to run directly (will fail if no sudo access, but user can run manually)
                QMessageBox.information(
                    self,
                    "Manual Installation Required",
                    f"The deployment script has been downloaded to:\n{script_path}\n\n"
                    "Please run it manually in a terminal:\n\n"
                    f"  cd {cwd}\n"
                    "  sudo ./deploy_timesketch.sh\n\n"
                    "After installation completes, configure the docker-compose path in Settings."
                )
                self.ts_install_btn.setEnabled(True)
                self.ts_install_btn.setText("🚀 Install Timesketch")
                self.ts_install_status_label.setText(f"Script downloaded to: {script_path}")
                return
            
            # Launch terminal with script
            try:
                subprocess.Popen(terminal_cmd)
                self.ts_install_status_label.setText(
                    f"Installation started in terminal window.\n\n"
                    f"Script location: {script_path}\n"
                    f"Timesketch will be installed in: {timesketch_dir}\n\n"
                    f"After installation completes:\n"
                    f"1. Configure docker-compose path: {timesketch_dir}/docker-compose.yml\n"
                    f"2. Click 'Start Timesketch Container' to start services"
                )
                
                QMessageBox.information(
                    self,
                    "Installation Started",
                    "The Timesketch installation has started in a terminal window.\n\n"
                    "Please:\n"
                    "1. Enter your sudo password when prompted\n"
                    "2. Follow the prompts in the terminal\n"
                    "3. Wait for installation to complete\n\n"
                    "After installation, configure the docker-compose path in Settings."
                )
            except Exception as e:
                logger.error(f"Failed to launch terminal: {e}")
                QMessageBox.warning(
                    self,
                    "Terminal Launch Failed",
                    f"Could not launch terminal window automatically.\n\n"
                    f"The script has been downloaded to:\n{script_path}\n\n"
                    "Please run it manually:\n\n"
                    f"  cd {cwd}\n"
                    "  sudo ./deploy_timesketch.sh"
                )
                self.ts_install_status_label.setText(f"Script downloaded to: {script_path}")
            
            self.ts_install_btn.setEnabled(True)
            self.ts_install_btn.setText("🚀 Install Timesketch")
            
        except Exception as e:
            logger.error(f"Error installing Timesketch: {e}")
            QMessageBox.critical(
                self,
                "Installation Error",
                f"An error occurred during installation:\n\n{str(e)}"
            )
            self.ts_install_btn.setEnabled(True)
            self.ts_install_btn.setText("🚀 Install Timesketch")
            self.ts_install_status_label.setText("")
    
    def _install_timesketch_macos(self):
        """Install Timesketch on macOS using docker-compose."""
        # Confirm installation
        reply = QMessageBox.question(
            self,
            "Install Timesketch (macOS)",
            "This will download Timesketch docker-compose files and set up Timesketch.\n\n"
            "Requirements:\n"
            "- Docker Desktop installed and running\n"
            "- At least 8GB RAM allocated to Docker\n"
            "- Internet connection\n\n"
            "The installation will:\n"
            "1. Create a 'timesketch' directory\n"
            "2. Download docker-compose.yml and configuration files\n"
            "3. Set up all Timesketch services\n\n"
            "Continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        self._install_timesketch_docker_compose("macOS")
    
    def _install_timesketch_windows(self):
        """Install Timesketch on Windows using docker-compose."""
        # Confirm installation
        reply = QMessageBox.question(
            self,
            "Install Timesketch (Windows)",
            "This will download Timesketch docker-compose files and set up Timesketch.\n\n"
            "Requirements:\n"
            "- Docker Desktop installed and running\n"
            "- WSL2 enabled (Docker Desktop requirement)\n"
            "- At least 8GB RAM allocated to Docker\n"
            "- Internet connection\n\n"
            "The installation will:\n"
            "1. Create a 'timesketch' directory\n"
            "2. Download docker-compose.yml and configuration files\n"
            "3. Set up all Timesketch services\n\n"
            "Continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        self._install_timesketch_docker_compose("Windows")
    
    def _install_timesketch_docker_compose(self, platform_name: str):
        """Download and set up Timesketch using docker-compose (for macOS/Windows)."""
        self.ts_install_btn.setEnabled(False)
        self.ts_install_btn.setText("Installing...")
        self.ts_install_status_label.setText("Setting up Timesketch...")
        
        try:
            # Check if Docker is available
            if not self.ts_docker_service.is_docker_available():
                QMessageBox.critical(
                    self,
                    "Docker Not Found",
                    "Docker is not installed or not in PATH.\n\n"
                    f"Please install Docker Desktop for {platform_name}:\n"
                    "https://www.docker.com/products/docker-desktop"
                )
                self.ts_install_btn.setEnabled(True)
                self.ts_install_btn.setText("🚀 Install Timesketch")
                self.ts_install_status_label.setText("")
                return
            
            # Check if Docker daemon is running
            if not self.ts_docker_service.is_docker_daemon_running():
                QMessageBox.warning(
                    self,
                    "Docker Not Running",
                    "Docker daemon is not running.\n\n"
                    "Please start Docker Desktop and try again."
                )
                self.ts_install_btn.setEnabled(True)
                self.ts_install_btn.setText("🚀 Install Timesketch")
                self.ts_install_status_label.setText("")
                return
            
            # Get current working directory
            cwd = Path.cwd()
            timesketch_dir = cwd / "timesketch"
            
            # Check if timesketch directory already exists
            if timesketch_dir.exists():
                reply = QMessageBox.question(
                    self,
                    "Directory Exists",
                    f"Timesketch directory already exists at:\n{timesketch_dir}\n\n"
                    "Do you want to continue? This will download/update files.",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No
                )
                if reply != QMessageBox.StandardButton.Yes:
                    self.ts_install_btn.setEnabled(True)
                    self.ts_install_btn.setText("🚀 Install Timesketch")
                    self.ts_install_status_label.setText("")
                    return
            
            # Create directory structure
            self.ts_install_status_label.setText("Creating directory structure...")
            timesketch_dir.mkdir(exist_ok=True)
            (timesketch_dir / "data" / "postgresql").mkdir(parents=True, exist_ok=True)
            (timesketch_dir / "data" / "opensearch").mkdir(parents=True, exist_ok=True)
            (timesketch_dir / "logs").mkdir(exist_ok=True)
            (timesketch_dir / "etc" / "timesketch" / "sigma" / "rules").mkdir(parents=True, exist_ok=True)
            (timesketch_dir / "upload").mkdir(exist_ok=True)
            (timesketch_dir / "etc" / "timesketch" / "llm_summarize").mkdir(parents=True, exist_ok=True)
            (timesketch_dir / "etc" / "timesketch" / "nl2q").mkdir(parents=True, exist_ok=True)
            
            base_url = "https://raw.githubusercontent.com/google/timesketch/master"
            
            # Download docker-compose.yml and config.env
            self.ts_install_status_label.setText("Downloading docker-compose.yml...")
            if not _download_file_with_ssl_fix(
                f"{base_url}/docker/release/docker-compose.yml",
                timesketch_dir / "docker-compose.yml"
            ):
                raise Exception("Failed to download docker-compose.yml. SSL certificate issue may need to be resolved.")
            
            self.ts_install_status_label.setText("Downloading config.env...")
            if not _download_file_with_ssl_fix(
                f"{base_url}/docker/release/config.env",
                timesketch_dir / "config.env"
            ):
                raise Exception("Failed to download config.env. SSL certificate issue may need to be resolved.")
            
            # Create .env file (copy on Windows, symlink on macOS/Linux)
            env_file = timesketch_dir / ".env"
            config_env = timesketch_dir / "config.env"
            if platform.system() == "Windows":
                # Windows doesn't support symlinks easily, so copy
                if env_file.exists():
                    env_file.unlink()
                shutil.copy(config_env, env_file)
            else:
                # Create symlink
                if env_file.exists() or env_file.is_symlink():
                    if env_file.is_symlink():
                        env_file.unlink()
                    else:
                        env_file.unlink()
                try:
                    env_file.symlink_to("config.env")
                except OSError:
                    # Fallback to copy if symlink fails
                    shutil.copy(config_env, env_file)
            
            # Download Timesketch configuration files
            self.ts_install_status_label.setText("Downloading Timesketch configuration files...")
            config_files = [
                ("data/timesketch.conf", "etc/timesketch/timesketch.conf"),
                ("data/tags.yaml", "etc/timesketch/tags.yaml"),
                ("data/plaso.mappings", "etc/timesketch/plaso.mappings"),
                ("data/generic.mappings", "etc/timesketch/generic.mappings"),
                ("data/regex_features.yaml", "etc/timesketch/regex_features.yaml"),
                ("data/winevt_features.yaml", "etc/timesketch/winevt_features.yaml"),
                ("data/ontology.yaml", "etc/timesketch/ontology.yaml"),
                ("data/intelligence_tag_metadata.yaml", "etc/timesketch/intelligence_tag_metadata.yaml"),
                ("data/sigma_config.yaml", "etc/timesketch/sigma_config.yaml"),
                ("data/sigma/rules/lnx_susp_zmap.yml", "etc/timesketch/sigma/rules/lnx_susp_zmap.yml"),
                ("data/plaso_formatters.yaml", "etc/timesketch/plaso_formatters.yaml"),
                ("data/context_links.yaml", "etc/timesketch/context_links.yaml"),
                ("contrib/nginx.conf", "etc/nginx.conf"),
                ("data/llm_summarize/prompt.txt", "etc/timesketch/llm_summarize/prompt.txt"),
                ("data/nl2q/data_types.csv", "etc/timesketch/nl2q/data_types.csv"),
                ("data/nl2q/prompt_nl2q", "etc/timesketch/nl2q/prompt_nl2q"),
                ("data/nl2q/examples_nl2q", "etc/timesketch/nl2q/examples_nl2q"),
            ]
            
            for remote_path, local_path in config_files:
                try:
                    if not _download_file_with_ssl_fix(
                        f"{base_url}/{remote_path}",
                        timesketch_dir / local_path
                    ):
                        logger.warning(f"Failed to download {remote_path}")
                        # Continue with other files
                except Exception as e:
                    logger.warning(f"Failed to download {remote_path}: {e}")
                    # Continue with other files
            
            # Generate random secrets
            def generate_secret(length=32):
                return ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(length))
            
            postgres_password = generate_secret(32)
            secret_key = generate_secret(32)
            
            # Read and update config.env
            self.ts_install_status_label.setText("Configuring Timesketch...")
            config_env_path = timesketch_dir / "config.env"
            with open(config_env_path, 'r') as f:
                config_content = f.read()
            
            # Update POSTGRES_PASSWORD if not set
            if "POSTGRES_PASSWORD=" in config_content:
                lines = config_content.split('\n')
                for i, line in enumerate(lines):
                    if line.startswith("POSTGRES_PASSWORD=") and not line.split('=')[1].strip():
                        lines[i] = f"POSTGRES_PASSWORD={postgres_password}"
                config_content = '\n'.join(lines)
            else:
                config_content += f"\nPOSTGRES_PASSWORD={postgres_password}\n"
            
            # Calculate OpenSearch memory (half of available, but cap at reasonable amount)
            try:
                import psutil
                total_mem_gb = psutil.virtual_memory().total / (1024**3)
                opensearch_mem = min(int(total_mem_gb / 2), 8)  # Cap at 8GB
            except ImportError:
                opensearch_mem = 4  # Default to 4GB if psutil not available
            
            if "OPENSEARCH_MEM_USE_GB=" in config_content:
                lines = config_content.split('\n')
                for i, line in enumerate(lines):
                    if line.startswith("OPENSEARCH_MEM_USE_GB=") and not line.split('=')[1].strip():
                        lines[i] = f"OPENSEARCH_MEM_USE_GB={opensearch_mem}"
                config_content = '\n'.join(lines)
            else:
                config_content += f"\nOPENSEARCH_MEM_USE_GB={opensearch_mem}\n"
            
            with open(config_env_path, 'w') as f:
                f.write(config_content)
            
            # Update timesketch.conf
            timesketch_conf = timesketch_dir / "etc" / "timesketch" / "timesketch.conf"
            if timesketch_conf.exists():
                with open(timesketch_conf, 'r') as f:
                    conf_content = f.read()
                
                # Update SECRET_KEY
                conf_content = re.sub(
                    r"SECRET_KEY = '.*?'",
                    f"SECRET_KEY = '{secret_key}'",
                    conf_content
                )
                
                # Update OpenSearch connection
                conf_content = re.sub(
                    r"OPENSEARCH_HOST = '127\.0\.0\.1'",
                    "OPENSEARCH_HOST = 'opensearch'",
                    conf_content
                )
                
                # Update Redis connection
                conf_content = re.sub(
                    r"^CELERY_BROKER_URL = .*",
                    "CELERY_BROKER_URL = 'redis://redis:6379'",
                    conf_content,
                    flags=re.MULTILINE
                )
                conf_content = re.sub(
                    r"^CELERY_RESULT_BACKEND = .*",
                    "CELERY_RESULT_BACKEND = 'redis://redis:6379'",
                    conf_content,
                    flags=re.MULTILINE
                )
                
                # Update PostgreSQL connection
                conf_content = re.sub(
                    r"postgresql://<USERNAME>:<PASSWORD>@localhost",
                    f"postgresql://timesketch:{postgres_password}@postgres:5432",
                    conf_content
                )
                
                # Enable upload
                conf_content = re.sub(
                    r"^UPLOAD_ENABLED = False",
                    "UPLOAD_ENABLED = True",
                    conf_content,
                    flags=re.MULTILINE
                )
                conf_content = re.sub(
                    r"^UPLOAD_FOLDER = '/tmp'",
                    "UPLOAD_FOLDER = '/usr/share/timesketch/upload'",
                    conf_content,
                    flags=re.MULTILINE
                )
                
                with open(timesketch_conf, 'w') as f:
                    f.write(conf_content)
            
            # Update docker-compose path in settings
            compose_file = timesketch_dir / "docker-compose.yml"
            if hasattr(self, 'ts_docker_compose_edit'):
                self.ts_docker_compose_edit.setText(str(compose_file))
            
            # Update Docker service with the compose path
            if hasattr(self, 'ts_docker_service'):
                self.ts_docker_service.docker_compose_path = str(compose_file)
            
            # Save docker-compose path to config file if it exists
            config_file = TimesketchConfigDialog.CONFIG_FILE
            if config_file.exists():
                try:
                    with open(config_file, 'r') as f:
                        config = json.load(f)
                    config['docker_compose_path'] = str(compose_file)
                    with open(config_file, 'w') as f:
                        json.dump(config, f, indent=2)
                except Exception:
                    pass  # Don't fail if we can't update config
            
            self.ts_install_status_label.setText(
                f"Timesketch installation completed!\n\n"
                f"Installation directory: {timesketch_dir}\n"
                f"Docker Compose file: {compose_file}\n\n"
                f"Next steps:\n"
                f"1. Click 'Start Timesketch Container' to start services\n"
                f"2. Wait for services to start (may take a few minutes)\n"
                f"3. Create a user: docker compose exec timesketch-web tsctl create-user <USERNAME>\n"
                f"4. Access Timesketch at: http://localhost"
            )
            
            QMessageBox.information(
                self,
                "Installation Complete",
                f"Timesketch has been installed successfully!\n\n"
                f"Location: {timesketch_dir}\n\n"
                f"The docker-compose path has been configured automatically.\n\n"
                f"You can now start Timesketch by clicking 'Start Timesketch Container'."
            )
            
            # Refresh installation status
            self._check_timesketch_installation_status()
            
            self.ts_install_btn.setEnabled(True)
            self.ts_install_btn.setText("🚀 Install Timesketch")
            
        except Exception as e:
            logger.error(f"Error installing Timesketch: {e}")
            QMessageBox.critical(
                self,
                "Installation Error",
                f"An error occurred during installation:\n\n{str(e)}\n\n"
                "Please check your internet connection and Docker Desktop status."
            )
            self.ts_install_btn.setEnabled(True)
            self.ts_install_btn.setText("🚀 Install Timesketch")
            self.ts_install_status_label.setText("")
    
    def _browse_docker_compose(self):
        """Browse for docker-compose.yml or docker-compose.yaml file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Docker Compose File",
            "",
            "Docker Compose Files (*.yml *.yaml docker-compose.yml docker-compose.yaml);;All Files (*)"
        )
        if file_path:
            if hasattr(self, 'ts_docker_compose_edit'):
                self.ts_docker_compose_edit.setText(file_path)
                # Also suggest setting server URL if not already set
                if not self.ts_server_url_edit.text().strip():
                    self.ts_server_url_edit.setText("http://localhost:5000")
    
    def _show_timesketch_docker_instructions(self):
        """Show Timesketch Docker setup instructions in a dialog window."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Timesketch Docker Setup Instructions")
        dialog.setMinimumSize(800, 600)
        dialog.resize(900, 700)
        
        layout = QVBoxLayout()
        
        # Instructions text
        instructions_text = QTextEdit()
        instructions_text.setReadOnly(True)
        instructions_text.setHtml("""
        <html>
        <head>
            <style>
                body { font-family: Arial, sans-serif; line-height: 1.6; }
                h2 { color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 5px; }
                h3 { color: #34495e; margin-top: 20px; }
                ol, ul { margin-left: 20px; }
                li { margin-bottom: 8px; }
                code { background-color: #f4f4f4; padding: 2px 6px; border-radius: 3px; font-family: monospace; }
                pre { background-color: #f4f4f4; padding: 15px; border-radius: 5px; overflow-x: auto; border-left: 4px solid #3498db; }
                a { color: #3498db; text-decoration: none; }
                a:hover { text-decoration: underline; }
                .note { background-color: #fff3cd; padding: 15px; border-radius: 5px; border-left: 4px solid #ffc107; margin-top: 20px; }
                .warning { background-color: #f8d7da; padding: 15px; border-radius: 5px; border-left: 4px solid #dc3545; margin-top: 20px; }
            </style>
        </head>
        <body>
            <h2>Timesketch Docker Setup Guide</h2>
            
            <div class="warning">
                <b>Important:</b> Timesketch does <b>not</b> have a single-container Docker image. 
                It requires multiple services (PostgreSQL, Elasticsearch, Redis, etc.) and must be 
                deployed using docker-compose or a similar orchestration tool.
            </div>
            
            <h3>Option 1: Use Official Timesketch Deployment Script (Recommended)</h3>
            <p><b>This is the official, tested, and actively maintained installation method.</b></p>
            <ol>
                <li><b>Prerequisites:</b>
                    <ul>
                        <li>Ubuntu 22.04 (or compatible Linux distribution)</li>
                        <li>At least 8GB RAM</li>
                        <li>Docker Engine installed</li>
                    </ul>
                </li>
                <li><b>Download and run the deployment script:</b>
                    <pre>curl -s -O https://raw.githubusercontent.com/google/timesketch/master/contrib/deploy_timesketch.sh
chmod 755 deploy_timesketch.sh
sudo ./deploy_timesketch.sh</pre>
                    <p>This script will:
                        <ul>
                            <li>Create a <code>timesketch</code> directory (default: in current directory)</li>
                            <li>Set up all necessary configuration files</li>
                            <li>Configure docker-compose.yaml with all required services</li>
                        </ul>
                    </p>
                </li>
                <li><b>Navigate to the timesketch directory:</b>
                    <pre>cd timesketch</pre>
                </li>
                <li><b>Start Timesketch services:</b>
                    <pre>sudo docker compose up -d</pre>
                    <p>Wait for all services to start (this may take a few minutes).</p>
                </li>
                <li><b>Create the first user:</b>
                    <pre>sudo docker compose exec timesketch-web tsctl create-user &lt;USERNAME&gt;</pre>
                    <p>Replace <code>&lt;USERNAME&gt;</code> with your desired username. You'll be prompted for a password.</p>
                </li>
                <li><b>Configure in DeepTempo:</b>
                    <ul>
                        <li>In Settings → Timesketch, click "Browse..." next to "Docker Compose File"</li>
                        <li>Navigate to the <code>timesketch</code> directory created by the script</li>
                        <li>Select <code>docker-compose.yaml</code></li>
                        <li>Set Server URL to <code>http://localhost:5000</code> (or the port configured in docker-compose)</li>
                        <li>Configure authentication with the username/password you created</li>
                        <li>Click "Start Timesketch Container" (it will use docker-compose automatically)</li>
                    </ul>
                </li>
            </ol>
            
            <div class="note">
                <b>Note:</b> The deployment script sets up:
                <ul>
                    <li>Timesketch web/api server</li>
                    <li>Timesketch importer/analysis worker</li>
                    <li>PostgreSQL database</li>
                    <li>OpenSearch single-node cluster</li>
                    <li>Redis key-value database</li>
                    <li>Nginx webserver</li>
                </ul>
            </div>
            
            <h3>Option 2: Manual Docker Compose Setup</h3>
            <p>If you prefer to set up docker-compose manually or have an existing setup:</p>
            <ol>
                <li>Clone the official Timesketch repository:
                    <pre>git clone https://github.com/google/timesketch.git
cd timesketch/docker</pre>
                </li>
                <li>Copy the example docker-compose file:
                    <pre>cp docker-compose.example.yml docker-compose.yml</pre>
                </li>
                <li>Edit <code>docker-compose.yml</code> as needed for your environment</li>
                <li>In Settings → Timesketch, click "Browse..." next to "Docker Compose File"</li>
                <li>Select your <code>docker-compose.yml</code> file</li>
                <li>Set Server URL to match your configuration</li>
                <li>Click "Start Timesketch Container" (it will use docker-compose automatically)</li>
            </ol>
            
            <h3>Option 3: Use Existing Timesketch Server</h3>
            <ol>
                <li>If you have a Timesketch server already running (on-premises or cloud)</li>
                <li>In Settings → Timesketch, enter the server URL</li>
                <li>Configure authentication (username/password or API token)</li>
                <li>Click "Test Connection" to verify</li>
            </ol>
            
            <h3>Option 4: Custom Docker Image</h3>
            <ol>
                <li>If you have a custom Timesketch Docker image in your registry</li>
                <li>In Settings → Timesketch, enter the image name (e.g., "my-registry/timesketch:tag")</li>
                <li>Click "Start Timesketch Container"</li>
                <li><b>Note:</b> This assumes your image is a complete Timesketch setup</li>
            </ol>
            
            <div class="note">
                <b>Default Credentials:</b> When using the official docker-compose setup, the default 
                credentials are typically:
                <ul>
                    <li>Username: <code>admin</code></li>
                    <li>Password: <code>admin</code></li>
                </ul>
                <p><b>Important:</b> Change these credentials in production!</p>
            </div>
            
            <h3>Useful Links</h3>
            <ul>
                <li><a href="https://timesketch.org/guides/admin/install-docker/">Official Timesketch Docker Installation Guide</a></li>
                <li><a href="https://github.com/google/timesketch">Timesketch GitHub Repository</a></li>
                <li><a href="https://raw.githubusercontent.com/google/timesketch/master/contrib/deploy_timesketch.sh">Deployment Script (deploy_timesketch.sh)</a></li>
                <li><a href="https://timesketch.org/">Timesketch Official Website</a></li>
            </ul>
            
            <h3>Troubleshooting</h3>
            <ul>
                <li><b>Image not found:</b> Make sure you're using docker-compose, not a single container</li>
                <li><b>Port already in use:</b> Change the port in docker-compose.yml or stop the conflicting service</li>
                <li><b>Services not starting:</b> Check docker-compose logs: <code>docker-compose logs</code></li>
                <li><b>Connection refused:</b> Wait a few minutes for all services to fully start</li>
            </ul>
        </body>
        </html>
        """)
        layout.addWidget(instructions_text)
        
        # Close button
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.accept)
        button_layout.addWidget(close_btn)
        layout.addLayout(button_layout)
        
        dialog.setLayout(layout)
        dialog.exec()
    
    def _show_s3_instructions(self):
        """Show S3 setup instructions in a dialog window."""
        dialog = QDialog(self)
        dialog.setWindowTitle("S3 Bucket Setup Instructions")
        dialog.setMinimumSize(800, 600)
        dialog.resize(900, 700)
        
        layout = QVBoxLayout()
        
        # Instructions text
        instructions_text = QTextEdit()
        instructions_text.setReadOnly(True)
        instructions_text.setHtml("""
        <html>
        <head>
            <style>
                body { font-family: Arial, sans-serif; line-height: 1.6; }
                h2 { color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 5px; }
                h3 { color: #34495e; margin-top: 20px; }
                ol { margin-left: 20px; }
                li { margin-bottom: 8px; }
                code { background-color: #f4f4f4; padding: 2px 6px; border-radius: 3px; font-family: monospace; }
                pre { background-color: #f4f4f4; padding: 15px; border-radius: 5px; overflow-x: auto; border-left: 4px solid #3498db; }
                a { color: #3498db; text-decoration: none; }
                a:hover { text-decoration: underline; }
                .note { background-color: #fff3cd; padding: 15px; border-radius: 5px; border-left: 4px solid #ffc107; margin-top: 20px; }
            </style>
        </head>
        <body>
            <h2>How to Configure S3 Bucket in AWS</h2>
            
            <h3>Step 1: Create an S3 Bucket</h3>
            <ol>
                <li>Log in to the <a href="https://console.aws.amazon.com/s3/">AWS S3 Console</a></li>
                <li>Click <b>"Create bucket"</b></li>
                <li>Enter a unique bucket name (e.g., "deeptempo-findings")</li>
                <li>Select your preferred AWS region</li>
                <li>Configure bucket settings (versioning, encryption, etc.) as needed</li>
                <li>Click <b>"Create bucket"</b></li>
            </ol>
            
            <h3>Step 2: Upload Your Data Files</h3>
            <ol>
                <li>Navigate to your bucket in the S3 Console</li>
                <li>Click <b>"Upload"</b></li>
                <li>Upload your <code>findings.json</code> and <code>cases.json</code> files</li>
                <li>Note the exact file names/paths (e.g., "findings.json" or "data/findings.json")</li>
            </ol>
            
            <h3>Step 3: Configure IAM Permissions</h3>
            <ol>
                <li>Go to the <a href="https://console.aws.amazon.com/iam/">IAM Console</a></li>
                <li>Create a new IAM user or use an existing one</li>
                <li>Attach a policy with the following permissions:
                    <pre>{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:GetObject",
                "s3:ListBucket"
            ],
            "Resource": [
                "arn:aws:s3:::YOUR-BUCKET-NAME",
                "arn:aws:s3:::YOUR-BUCKET-NAME/*"
            ]
        }
    ]
}</pre>
                    <p><b>Important:</b> Replace <code>YOUR-BUCKET-NAME</code> with your actual bucket name.</p>
                </li>
                <li>Create access keys for the user:
                    <ol>
                        <li>Select the IAM user</li>
                        <li>Go to the "Security credentials" tab</li>
                        <li>Click "Create access key"</li>
                        <li>Choose "Application running outside AWS" (or appropriate use case)</li>
                        <li>Save the Access Key ID and Secret Access Key securely</li>
                    </ol>
                </li>
            </ol>
            
            <h3>Step 4: Configure in DeepTempo</h3>
            <ol>
                <li>Enter your bucket name and region in the S3 Storage tab</li>
                <li>Enter the file paths (e.g., "findings.json" or "data/findings.json")</li>
                <li>Optionally enter your AWS credentials:
                    <ul>
                        <li>If you're running on an EC2 instance with an IAM role, leave credentials empty</li>
                        <li>If you have AWS credentials in environment variables or <code>~/.aws/credentials</code>, leave credentials empty</li>
                        <li>Otherwise, enter your Access Key ID and Secret Access Key</li>
                    </ul>
                </li>
                <li>Click <b>"Test Connection"</b> to verify access</li>
                <li>Click <b>"Save All"</b> to save configuration</li>
            </ol>
            
            <div class="note">
                <b>Note:</b> If you're running on an EC2 instance with an IAM role, or have AWS credentials configured 
                via environment variables (<code>AWS_ACCESS_KEY_ID</code> and <code>AWS_SECRET_ACCESS_KEY</code>) or 
                in <code>~/.aws/credentials</code>, you can leave the credentials fields empty. The application will 
                automatically use the default credential chain.
            </div>
            
            <h3>Troubleshooting</h3>
            <ul>
                <li><b>Bucket not found:</b> Verify the bucket name is correct and exists in the specified region</li>
                <li><b>Access denied:</b> Check that your IAM user has the correct permissions (s3:GetObject and s3:ListBucket)</li>
                <li><b>Credentials not found:</b> Ensure credentials are entered correctly or that default credentials are configured</li>
                <li><b>File not found:</b> Verify the file paths match exactly what's in your S3 bucket (case-sensitive)</li>
            </ul>
        </body>
        </html>
        """)
        layout.addWidget(instructions_text)
        
        # Close button
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.accept)
        button_layout.addWidget(close_btn)
        layout.addLayout(button_layout)
        
        dialog.setLayout(layout)
        dialog.exec()

