"""Unified settings console for configuring all services."""

import json
import logging
from pathlib import Path
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QMessageBox, QGroupBox, QFormLayout, QCheckBox, QComboBox, QTextEdit,
    QTabWidget, QWidget, QListWidget, QListWidgetItem
)
from PyQt6.QtCore import Qt
import keyring

from services.timesketch_service import TimesketchService
from services.claude_service import ClaudeService
from ui.timesketch_config import TimesketchConfigDialog

logger = logging.getLogger(__name__)


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
        
        # General Settings Tab
        general_tab = self._create_general_tab()
        self.tabs.addTab(general_tab, "General")
        
        layout.addWidget(self.tabs)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        test_all_btn = QPushButton("Test All Connections")
        test_all_btn.clicked.connect(self._test_all_connections)
        button_layout.addWidget(test_all_btn)
        
        button_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        save_btn = QPushButton("Save All")
        save_btn.clicked.connect(self._save_all_settings)
        button_layout.addWidget(save_btn)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def _create_claude_tab(self) -> QWidget:
        """Create Claude AI configuration tab."""
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
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget
    
    def _create_timesketch_tab(self) -> QWidget:
        """Create Timesketch configuration tab."""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Info
        info_label = QLabel(
            "<b>Timesketch Configuration</b><br>"
            "Configure your Timesketch server connection for timeline analysis."
        )
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
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
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget
    
    def _create_mcp_tab(self) -> QWidget:
        """Create MCP servers configuration tab."""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Info
        info_label = QLabel(
            "<b>MCP Servers Configuration</b><br>"
            "Manage Model Context Protocol (MCP) servers for Claude Desktop integration."
        )
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # MCP Config Info
        config_group = QGroupBox("Claude Desktop Configuration")
        config_layout = QVBoxLayout()
        
        config_info = QLabel(
            "MCP servers are configured in Claude Desktop's configuration file.\n"
            "Use the 'Configure Claude Desktop...' option in the File menu to manage MCP servers."
        )
        config_info.setWordWrap(True)
        config_layout.addWidget(config_info)
        
        # Show config path
        config_path_label = QLabel()
        config_path = self._get_mcp_config_path()
        if config_path:
            config_path_label.setText(f"<b>Config Path:</b> {config_path}")
        else:
            config_path_label.setText("<b>Config Path:</b> Not found")
        config_layout.addWidget(config_path_label)
        
        open_config_btn = QPushButton("Open Claude Desktop Config")
        open_config_btn.clicked.connect(self._open_mcp_config)
        config_layout.addWidget(open_config_btn)
        
        config_group.setLayout(config_layout)
        layout.addWidget(config_group)
        
        # MCP Server Status
        status_group = QGroupBox("MCP Server Status")
        status_layout = QVBoxLayout()
        
        self.mcp_status_list = QListWidget()
        self._populate_mcp_status()
        status_layout.addWidget(self.mcp_status_list)
        
        refresh_btn = QPushButton("Refresh Status")
        refresh_btn.clicked.connect(self._populate_mcp_status)
        status_layout.addWidget(refresh_btn)
        
        status_group.setLayout(status_layout)
        layout.addWidget(status_group)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget
    
    def _create_s3_tab(self) -> QWidget:
        """Create S3 configuration tab."""
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
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget
    
    def _create_general_tab(self) -> QWidget:
        """Create general settings tab."""
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
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget
    
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
        
        # Load S3 settings
        self._load_s3_settings()
        
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
        
        # Save general settings
        self._save_general_settings()
        
        QMessageBox.information(self, "Success", "All settings saved successfully!")
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
                'sync_interval': int(self.ts_sync_interval_edit.text() or '300')
            }
            
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
    
    def _populate_mcp_status(self):
        """Populate MCP server status list."""
        self.mcp_status_list.clear()
        
        try:
            from ui.config_manager import ConfigManager
            config_path = ConfigManager.get_config_path()
            
            if not config_path or not Path(config_path).exists():
                self.mcp_status_list.addItem("MCP configuration file not found")
                return
            
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            mcp_servers = config.get('mcpServers', {})
            
            if not mcp_servers:
                self.mcp_status_list.addItem("No MCP servers configured")
                return
            
            for server_name, server_config in mcp_servers.items():
                command = server_config.get('command', 'N/A')
                status_item = QListWidgetItem(f"{server_name}: {command}")
                self.mcp_status_list.addItem(status_item)
        
        except Exception as e:
            self.mcp_status_list.addItem(f"Error loading MCP status: {e}")
    
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

