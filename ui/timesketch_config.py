"""Timesketch configuration dialog."""

import json
import logging
from pathlib import Path
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QMessageBox, QGroupBox, QFormLayout, QCheckBox, QComboBox, QTextEdit
)
from PyQt6.QtCore import Qt
import keyring

from services.timesketch_service import TimesketchService

logger = logging.getLogger(__name__)


class TimesketchConfigDialog(QDialog):
    """Dialog for configuring Timesketch server connection."""
    
    CONFIG_FILE = Path.home() / '.deeptempo' / 'timesketch_config.json'
    SERVICE_NAME = "deeptempo-ai-soc"
    KEYRING_USERNAME = "timesketch_username"
    KEYRING_PASSWORD = "timesketch_password"
    KEYRING_TOKEN = "timesketch_api_token"
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Timesketch Configuration")
        self.setMinimumSize(600, 500)
        
        self.config = self._load_config()
        self.timesketch_service = None
        
        self._setup_ui()
        self._load_config_to_ui()
    
    def _load_config(self) -> dict:
        """Load configuration from file."""
        if self.CONFIG_FILE.exists():
            try:
                with open(self.CONFIG_FILE, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading Timesketch config: {e}")
        
        return {
            'server_url': 'http://localhost:5000',  # Default to localhost for local development
            'auth_method': 'password',  # 'password' or 'token'
            'username': '',
            'password': '',  # Will be stored in keyring
            'api_token': '',  # Will be stored in keyring
            'verify_ssl': True,
            'auto_sync': False,
            'sync_interval': 300
        }
    
    def _save_config(self, config: dict) -> bool:
        """Save configuration to file (without sensitive data)."""
        try:
            self.CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
            
            # Don't save passwords/tokens in config file
            safe_config = config.copy()
            safe_config['password'] = ''  # Stored in keyring
            safe_config['api_token'] = ''  # Stored in keyring
            
            with open(self.CONFIG_FILE, 'w') as f:
                json.dump(safe_config, f, indent=2)
            
            # Save sensitive data to keyring
            if config.get('username'):
                try:
                    keyring.set_password(self.SERVICE_NAME, self.KEYRING_USERNAME, config['username'])
                except Exception:
                    pass  # Keyring not available
            
            if config.get('password'):
                try:
                    keyring.set_password(self.SERVICE_NAME, self.KEYRING_PASSWORD, config['password'])
                except Exception:
                    pass
            
            if config.get('api_token'):
                try:
                    keyring.set_password(self.SERVICE_NAME, self.KEYRING_TOKEN, config['api_token'])
                except Exception:
                    pass
            
            return True
        except Exception as e:
            logger.error(f"Error saving Timesketch config: {e}")
            return False
    
    def _load_sensitive_data(self) -> dict:
        """Load sensitive data from keyring."""
        sensitive = {}
        
        try:
            username = keyring.get_password(self.SERVICE_NAME, self.KEYRING_USERNAME)
            if username:
                sensitive['username'] = username
        except Exception:
            pass
        
        try:
            password = keyring.get_password(self.SERVICE_NAME, self.KEYRING_PASSWORD)
            if password:
                sensitive['password'] = password
        except Exception:
            pass
        
        try:
            token = keyring.get_password(self.SERVICE_NAME, self.KEYRING_TOKEN)
            if token:
                sensitive['api_token'] = token
        except Exception:
            pass
        
        return sensitive
    
    def _setup_ui(self):
        """Set up the UI."""
        layout = QVBoxLayout()
        
        # Info section
        info_label = QLabel(
            "<b>Timesketch Configuration</b><br>"
            "Timesketch is an <b>external service</b> that must be deployed separately. "
            "This application connects to an existing Timesketch server via its REST API.<br><br>"
            "<i>Default URL (http://localhost:5000) assumes local development. "
            "For production, enter your Timesketch server URL.</i>"
        )
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # Server configuration
        server_group = QGroupBox("Server Configuration")
        server_layout = QFormLayout()
        
        self.server_url_edit = QLineEdit()
        self.server_url_edit.setPlaceholderText("http://localhost:5000 or https://timesketch.example.com")
        server_layout.addRow("Server URL:", self.server_url_edit)
        
        # Quick setup buttons
        quick_setup_layout = QHBoxLayout()
        localhost_btn = QPushButton("Use Localhost (Default)")
        localhost_btn.clicked.connect(lambda: self.server_url_edit.setText("http://localhost:5000"))
        quick_setup_layout.addWidget(localhost_btn)
        
        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(lambda: self.server_url_edit.clear())
        quick_setup_layout.addWidget(clear_btn)
        
        quick_setup_layout.addStretch()
        server_layout.addRow("", quick_setup_layout)
        
        self.verify_ssl_checkbox = QCheckBox("Verify SSL certificates")
        self.verify_ssl_checkbox.setChecked(True)
        server_layout.addRow("", self.verify_ssl_checkbox)
        
        server_group.setLayout(server_layout)
        layout.addWidget(server_group)
        
        # Authentication
        auth_group = QGroupBox("Authentication")
        auth_layout = QFormLayout()
        
        self.auth_method_combo = QComboBox()
        self.auth_method_combo.addItems(["Username/Password", "API Token"])
        self.auth_method_combo.currentIndexChanged.connect(self._on_auth_method_changed)
        auth_layout.addRow("Method:", self.auth_method_combo)
        
        self.username_edit = QLineEdit()
        self.username_edit.setPlaceholderText("Enter username...")
        auth_layout.addRow("Username:", self.username_edit)
        
        self.password_edit = QLineEdit()
        self.password_edit.setPlaceholderText("Enter password...")
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        auth_layout.addRow("Password:", self.password_edit)
        
        self.token_edit = QLineEdit()
        self.token_edit.setPlaceholderText("Enter API token...")
        self.token_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.token_edit.setVisible(False)
        auth_layout.addRow("API Token:", self.token_edit)
        
        auth_group.setLayout(auth_layout)
        layout.addWidget(auth_group)
        
        # Sync settings
        sync_group = QGroupBox("Sync Settings")
        sync_layout = QFormLayout()
        
        self.auto_sync_checkbox = QCheckBox("Enable auto-sync")
        sync_layout.addRow("", self.auto_sync_checkbox)
        
        self.sync_interval_edit = QLineEdit()
        self.sync_interval_edit.setPlaceholderText("300")
        self.sync_interval_edit.setToolTip("Sync interval in seconds (default: 300)")
        sync_layout.addRow("Sync Interval (seconds):", self.sync_interval_edit)
        
        sync_group.setLayout(sync_layout)
        layout.addWidget(sync_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        test_btn = QPushButton("Test Connection")
        test_btn.clicked.connect(self._test_connection)
        button_layout.addWidget(test_btn)
        
        button_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self._save_and_close)
        button_layout.addWidget(save_btn)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def _on_auth_method_changed(self, index: int):
        """Handle authentication method change."""
        if index == 0:  # Username/Password
            self.username_edit.setVisible(True)
            self.password_edit.setVisible(True)
            self.token_edit.setVisible(False)
        else:  # API Token
            self.username_edit.setVisible(False)
            self.password_edit.setVisible(False)
            self.token_edit.setVisible(True)
    
    def _load_config_to_ui(self):
        """Load configuration into UI fields."""
        # Load sensitive data from keyring
        sensitive = self._load_sensitive_data()
        self.config.update(sensitive)
        
        self.server_url_edit.setText(self.config.get('server_url', ''))
        self.verify_ssl_checkbox.setChecked(self.config.get('verify_ssl', True))
        
        auth_method = self.config.get('auth_method', 'password')
        if auth_method == 'token':
            self.auth_method_combo.setCurrentIndex(1)
        else:
            self.auth_method_combo.setCurrentIndex(0)
        
        self.username_edit.setText(self.config.get('username', ''))
        self.password_edit.setText(self.config.get('password', ''))
        self.token_edit.setText(self.config.get('api_token', ''))
        
        self.auto_sync_checkbox.setChecked(self.config.get('auto_sync', False))
        self.sync_interval_edit.setText(str(self.config.get('sync_interval', 300)))
    
    def _test_connection(self):
        """Test connection to Timesketch server."""
        server_url = self.server_url_edit.text().strip()
        if not server_url:
            QMessageBox.warning(self, "Validation Error", "Please enter a server URL.")
            return
        
        # Get auth credentials
        auth_method = self.auth_method_combo.currentIndex()
        if auth_method == 0:  # Username/Password
            username = self.username_edit.text().strip()
            password = self.password_edit.text().strip()
            if not username or not password:
                QMessageBox.warning(self, "Validation Error", "Please enter username and password.")
                return
            api_token = None
        else:  # API Token
            api_token = self.token_edit.text().strip()
            if not api_token:
                QMessageBox.warning(self, "Validation Error", "Please enter an API token.")
                return
            username = None
            password = None
        
        # Create service and test
        try:
            service = TimesketchService(
                server_url=server_url,
                username=username,
                password=password,
                api_token=api_token,
                verify_ssl=self.verify_ssl_checkbox.isChecked()
            )
            
            success, message = service.test_connection()
            
            if success:
                QMessageBox.information(self, "Success", f"Connection successful!\n\n{message}")
            else:
                QMessageBox.critical(self, "Connection Failed", f"Could not connect to Timesketch server:\n\n{message}")
        
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error testing connection:\n\n{str(e)}")
    
    def _save_and_close(self):
        """Save configuration and close dialog."""
        server_url = self.server_url_edit.text().strip()
        if not server_url:
            QMessageBox.warning(self, "Validation Error", "Please enter a server URL.")
            return
        
        # Build config
        config = {
            'server_url': server_url,
            'verify_ssl': self.verify_ssl_checkbox.isChecked(),
            'auth_method': 'token' if self.auth_method_combo.currentIndex() == 1 else 'password',
            'auto_sync': self.auto_sync_checkbox.isChecked(),
        }
        
        try:
            config['sync_interval'] = int(self.sync_interval_edit.text() or '300')
        except ValueError:
            config['sync_interval'] = 300
        
        # Get auth credentials
        if config['auth_method'] == 'password':
            config['username'] = self.username_edit.text().strip()
            config['password'] = self.password_edit.text().strip()
            config['api_token'] = ''
        else:
            config['api_token'] = self.token_edit.text().strip()
            config['username'] = ''
            config['password'] = ''
        
        # Save config
        if self._save_config(config):
            QMessageBox.information(self, "Success", "Timesketch configuration saved successfully!")
            self.accept()
        else:
            QMessageBox.critical(self, "Error", "Failed to save configuration.")
    
    @staticmethod
    def get_config() -> dict:
        """Get current Timesketch configuration."""
        dialog = TimesketchConfigDialog()
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Reload to get saved config
            return dialog._load_config()
        return {}
    
    @staticmethod
    def load_service() -> TimesketchService:
        """Load and return configured TimesketchService."""
        config_file = TimesketchConfigDialog.CONFIG_FILE
        if not config_file.exists():
            return None
        
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
        except Exception:
            return None
        
        # Load sensitive data from keyring
        sensitive = {}
        try:
            if config.get('auth_method') == 'password':
                username = keyring.get_password(TimesketchConfigDialog.SERVICE_NAME, 
                                              TimesketchConfigDialog.KEYRING_USERNAME)
                password = keyring.get_password(TimesketchConfigDialog.SERVICE_NAME,
                                              TimesketchConfigDialog.KEYRING_PASSWORD)
                if username:
                    sensitive['username'] = username
                if password:
                    sensitive['password'] = password
            else:
                token = keyring.get_password(TimesketchConfigDialog.SERVICE_NAME,
                                           TimesketchConfigDialog.KEYRING_TOKEN)
                if token:
                    sensitive['api_token'] = token
        except Exception:
            pass
        
        config.update(sensitive)
        
        return TimesketchService(
            server_url=config.get('server_url', ''),
            username=config.get('username'),
            password=config.get('password'),
            api_token=config.get('api_token'),
            verify_ssl=config.get('verify_ssl', True)
        )

