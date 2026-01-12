"""Unified integrations configuration dialog for all MCP servers."""

import json
import logging
from pathlib import Path
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QMessageBox, QGroupBox, QFormLayout, QCheckBox, QComboBox,
    QTabWidget, QWidget, QScrollArea, QTextEdit
)
from PyQt6.QtCore import Qt
import keyring

logger = logging.getLogger(__name__)


class IntegrationsConfigDialog(QDialog):
    """
    Unified configuration dialog for all security integrations.
    Provides a clean, categorized interface without bloat.
    """
    
    CONFIG_FILE = Path.home() / '.deeptempo' / 'integrations_config.json'
    SERVICE_NAME = "deeptempo-ai-soc"
    
    # Integration categories
    CATEGORIES = {
        'threat_intel': 'Threat Intelligence',
        'ticketing': 'Incident Management',
        'communications': 'Communications',
        'edr_xdr': 'EDR/XDR Platforms',
        'cloud_security': 'Cloud Security',
        'network_security': 'Network Security',
        'vulnerability': 'Vulnerability Management',
        'malware_analysis': 'Malware Analysis',
        'identity': 'Identity & Access',
        'email_security': 'Email Security',
        'utilities': 'Utilities & Tools'
    }
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Integrations Configuration")
        self.setMinimumSize(900, 700)
        
        self.config = self._load_config()
        self.enabled_integrations = set()
        
        self._setup_ui()
        self._load_config_to_ui()
    
    def _load_config(self) -> dict:
        """Load configuration from file."""
        if self.CONFIG_FILE.exists():
            try:
                with open(self.CONFIG_FILE, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading integrations config: {e}")
        
        return {
            'enabled_integrations': [],
            'integrations': {}
        }
    
    def _save_config(self) -> bool:
        """Save configuration to file."""
        try:
            self.CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
            
            # Collect all integration configs
            config = {
                'enabled_integrations': list(self.enabled_integrations),
                'integrations': {}
            }
            
            # Save each integration's config
            for integration_id, fields in self.integration_fields.items():
                if integration_id in self.enabled_integrations:
                    integration_config = {}
                    for field_name, widget in fields.items():
                        if isinstance(widget, QLineEdit):
                            value = widget.text().strip()
                            # Don't save passwords in plaintext - use keyring
                            if 'password' in field_name.lower() or 'token' in field_name.lower() or 'key' in field_name.lower():
                                if value:
                                    try:
                                        keyring.set_password(self.SERVICE_NAME, f"{integration_id}_{field_name}", value)
                                    except Exception:
                                        pass  # Keyring not available
                                value = ''  # Don't store in config file
                            integration_config[field_name] = value
                        elif isinstance(widget, QCheckBox):
                            integration_config[field_name] = widget.isChecked()
                        elif isinstance(widget, QComboBox):
                            integration_config[field_name] = widget.currentText()
                    
                    config['integrations'][integration_id] = integration_config
            
            with open(self.CONFIG_FILE, 'w') as f:
                json.dump(config, f, indent=2)
            
            return True
        except Exception as e:
            logger.error(f"Error saving integrations config: {e}")
            return False
    
    def _setup_ui(self):
        """Set up the UI with categorized tabs."""
        layout = QVBoxLayout()
        
        # Header
        header = QLabel(
            "<h2>Security Integrations</h2>"
            "<p>Configure external security tools and services. Only enabled integrations are shown in Claude.</p>"
        )
        header.setWordWrap(True)
        layout.addWidget(header)
        
        # Tabs for categories
        self.tabs = QTabWidget()
        self.integration_fields = {}  # Track all input fields
        
        # Create tab for each category
        self._create_threat_intel_tab()
        self._create_ticketing_tab()
        self._create_communications_tab()
        self._create_edr_xdr_tab()
        self._create_cloud_security_tab()
        self._create_network_security_tab()
        self._create_vulnerability_tab()
        self._create_malware_analysis_tab()
        self._create_identity_tab()
        self._create_email_security_tab()
        self._create_utilities_tab()
        
        layout.addWidget(self.tabs)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        save_btn = QPushButton("Save Configuration")
        save_btn.clicked.connect(self._save_and_close)
        save_btn.setDefault(True)
        button_layout.addWidget(save_btn)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def _create_integration_section(self, integration_id: str, display_name: str, 
                                   fields: list, description: str = "") -> QGroupBox:
        """
        Create a standardized integration configuration section.
        
        Args:
            integration_id: Unique ID for the integration
            display_name: Display name shown in UI
            fields: List of (field_name, field_label, field_type, placeholder) tuples
            description: Optional description text
        """
        group = QGroupBox(display_name)
        layout = QVBoxLayout()
        
        # Enable checkbox
        enable_checkbox = QCheckBox(f"Enable {display_name}")
        enable_checkbox.toggled.connect(lambda checked, iid=integration_id: self._toggle_integration(iid, checked))
        layout.addWidget(enable_checkbox)
        
        # Description
        if description:
            desc_label = QLabel(f"<i>{description}</i>")
            desc_label.setWordWrap(True)
            desc_label.setStyleSheet("color: #888; padding: 5px;")
            layout.addWidget(desc_label)
        
        # Fields
        form_layout = QFormLayout()
        self.integration_fields[integration_id] = {'_enabled': enable_checkbox}
        
        for field_info in fields:
            field_name = field_info[0]
            field_label = field_info[1]
            field_type = field_info[2] if len(field_info) > 2 else 'text'
            placeholder = field_info[3] if len(field_info) > 3 else ''
            
            if field_type == 'password':
                widget = QLineEdit()
                widget.setPlaceholderText(placeholder)
                widget.setEchoMode(QLineEdit.EchoMode.Password)
            elif field_type == 'checkbox':
                widget = QCheckBox(field_label)
                form_layout.addRow("", widget)
                self.integration_fields[integration_id][field_name] = widget
                continue
            elif field_type == 'combo':
                widget = QComboBox()
                if isinstance(placeholder, list):
                    widget.addItems(placeholder)
            else:  # text
                widget = QLineEdit()
                widget.setPlaceholderText(placeholder)
            
            widget.setEnabled(False)  # Disabled until integration is enabled
            form_layout.addRow(f"{field_label}:", widget)
            self.integration_fields[integration_id][field_name] = widget
        
        layout.addLayout(form_layout)
        group.setLayout(layout)
        
        return group
    
    def _toggle_integration(self, integration_id: str, enabled: bool):
        """Toggle integration enabled state and enable/disable fields."""
        if enabled:
            self.enabled_integrations.add(integration_id)
        else:
            self.enabled_integrations.discard(integration_id)
        
        # Enable/disable all fields for this integration
        for field_name, widget in self.integration_fields[integration_id].items():
            if field_name != '_enabled':
                widget.setEnabled(enabled)
    
    def _create_threat_intel_tab(self):
        """Create Threat Intelligence integrations tab."""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        
        widget = QWidget()
        layout = QVBoxLayout()
        
        # VirusTotal
        virustotal = self._create_integration_section(
            'virustotal',
            'VirusTotal',
            [
                ('api_key', 'API Key', 'password', 'Enter your VirusTotal API key'),
                ('rate_limit', 'Rate Limit (req/min)', 'text', '4')
            ],
            'File/URL/IP/domain reputation checks and malware analysis'
        )
        layout.addWidget(virustotal)
        
        # MISP
        misp = self._create_integration_section(
            'misp',
            'MISP (Malware Information Sharing Platform)',
            [
                ('url', 'MISP URL', 'text', 'https://misp.example.com'),
                ('api_key', 'API Key', 'password', 'Enter your MISP API key'),
                ('verify_ssl', 'Verify SSL', 'checkbox', '')
            ],
            'Community threat intelligence sharing and IOC management'
        )
        layout.addWidget(misp)
        
        # OpenCTI
        opencti = self._create_integration_section(
            'opencti',
            'OpenCTI',
            [
                ('url', 'OpenCTI URL', 'text', 'https://opencti.example.com'),
                ('api_token', 'API Token', 'password', 'Enter your OpenCTI token'),
                ('verify_ssl', 'Verify SSL', 'checkbox', '')
            ],
            'Structured threat intelligence platform with advanced relationships'
        )
        layout.addWidget(opencti)
        
        # AlienVault OTX
        otx = self._create_integration_section(
            'alienvault_otx',
            'AlienVault OTX',
            [
                ('api_key', 'API Key', 'password', 'Enter your OTX API key')
            ],
            'Open threat exchange community intelligence'
        )
        layout.addWidget(otx)
        
        # ThreatConnect
        threatconnect = self._create_integration_section(
            'threatconnect',
            'ThreatConnect',
            [
                ('api_url', 'API URL', 'text', 'https://api.threatconnect.com'),
                ('access_id', 'Access ID', 'text', 'Your Access ID'),
                ('secret_key', 'Secret Key', 'password', 'Your Secret Key')
            ],
            'Commercial threat intelligence platform'
        )
        layout.addWidget(threatconnect)
        
        # Shodan
        shodan = self._create_integration_section(
            'shodan',
            'Shodan',
            [
                ('api_key', 'API Key', 'password', 'Enter your Shodan API key')
            ],
            'Internet-connected device search and vulnerability discovery'
        )
        layout.addWidget(shodan)
        
        layout.addStretch()
        widget.setLayout(layout)
        scroll.setWidget(widget)
        self.tabs.addTab(scroll, "Threat Intelligence")
    
    def _create_ticketing_tab(self):
        """Create Incident Management integrations tab."""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Jira
        jira = self._create_integration_section(
            'jira',
            'Jira',
            [
                ('url', 'Jira URL', 'text', 'https://yourcompany.atlassian.net'),
                ('email', 'Email', 'text', 'your-email@example.com'),
                ('api_token', 'API Token', 'password', 'Enter your Jira API token'),
                ('project_key', 'Default Project Key', 'text', 'SEC')
            ],
            'Atlassian Jira for ticket creation and workflow management'
        )
        layout.addWidget(jira)
        
        # PagerDuty
        pagerduty = self._create_integration_section(
            'pagerduty',
            'PagerDuty',
            [
                ('api_token', 'API Token', 'password', 'Enter your PagerDuty API token'),
                ('service_id', 'Default Service ID', 'text', 'Service ID for incidents'),
                ('escalation_policy', 'Escalation Policy ID', 'text', 'Optional')
            ],
            'Alerting, on-call management, and incident response coordination'
        )
        layout.addWidget(pagerduty)
        
        # ServiceNow
        servicenow = self._create_integration_section(
            'servicenow',
            'ServiceNow',
            [
                ('instance', 'Instance Name', 'text', 'yourcompany'),
                ('username', 'Username', 'text', 'your.name'),
                ('password', 'Password', 'password', 'Enter password'),
                ('default_assignment_group', 'Assignment Group', 'text', 'Security Operations')
            ],
            'Enterprise ITSM integration for incidents and change management'
        )
        layout.addWidget(servicenow)
        
        layout.addStretch()
        widget.setLayout(layout)
        scroll.setWidget(widget)
        self.tabs.addTab(scroll, "Incident Management")
    
    def _create_communications_tab(self):
        """Create Communications integrations tab."""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Slack
        slack = self._create_integration_section(
            'slack',
            'Slack',
            [
                ('bot_token', 'Bot Token', 'password', 'xoxb-your-bot-token'),
                ('default_channel', 'Default Channel', 'text', '#security-alerts')
            ],
            'Real-time team notifications and collaboration'
        )
        layout.addWidget(slack)
        
        # Microsoft Teams
        teams = self._create_integration_section(
            'microsoft_teams',
            'Microsoft Teams',
            [
                ('webhook_url', 'Webhook URL', 'password', 'Enter Teams webhook URL'),
                ('tenant_id', 'Tenant ID (Optional)', 'text', 'For advanced integration')
            ],
            'Enterprise collaboration and notifications'
        )
        layout.addWidget(teams)
        
        # Email
        email = self._create_integration_section(
            'email',
            'Email Notifications',
            [
                ('smtp_server', 'SMTP Server', 'text', 'smtp.gmail.com'),
                ('smtp_port', 'SMTP Port', 'text', '587'),
                ('username', 'Username', 'text', 'your-email@example.com'),
                ('password', 'Password', 'password', 'Email password or app password'),
                ('from_address', 'From Address', 'text', 'security@example.com'),
                ('default_recipients', 'Default Recipients', 'text', 'soc-team@example.com')
            ],
            'Email-based alerting and reporting'
        )
        layout.addWidget(email)
        
        layout.addStretch()
        widget.setLayout(layout)
        scroll.setWidget(widget)
        self.tabs.addTab(scroll, "Communications")
    
    def _create_edr_xdr_tab(self):
        """Create EDR/XDR platforms tab."""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Microsoft Defender
        defender = self._create_integration_section(
            'microsoft_defender',
            'Microsoft Defender for Endpoint',
            [
                ('tenant_id', 'Tenant ID', 'text', 'Your Azure AD Tenant ID'),
                ('client_id', 'Client ID', 'text', 'Application Client ID'),
                ('client_secret', 'Client Secret', 'password', 'Application Secret')
            ],
            'Windows endpoint protection and threat detection'
        )
        layout.addWidget(defender)
        
        # SentinelOne
        sentinelone = self._create_integration_section(
            'sentinelone',
            'SentinelOne',
            [
                ('console_url', 'Console URL', 'text', 'https://your-console.sentinelone.net'),
                ('api_token', 'API Token', 'password', 'Enter API token')
            ],
            'AI-powered endpoint detection and response'
        )
        layout.addWidget(sentinelone)
        
        # Carbon Black
        carbonblack = self._create_integration_section(
            'carbon_black',
            'VMware Carbon Black',
            [
                ('url', 'Carbon Black URL', 'text', 'https://defense.conferdeploy.net'),
                ('org_key', 'Org Key', 'text', 'Your organization key'),
                ('api_id', 'API ID', 'text', 'API credential ID'),
                ('api_secret', 'API Secret', 'password', 'API secret key')
            ],
            'Endpoint detection and response with detailed telemetry'
        )
        layout.addWidget(carbonblack)
        
        layout.addStretch()
        widget.setLayout(layout)
        scroll.setWidget(widget)
        self.tabs.addTab(scroll, "EDR/XDR")
    
    def _create_cloud_security_tab(self):
        """Create Cloud Security platforms tab."""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        
        widget = QWidget()
        layout = QVBoxLayout()
        
        # AWS Security Hub
        aws = self._create_integration_section(
            'aws_security_hub',
            'AWS Security Hub',
            [
                ('access_key_id', 'Access Key ID', 'text', 'Your AWS access key'),
                ('secret_access_key', 'Secret Access Key', 'password', 'Your AWS secret key'),
                ('region', 'Default Region', 'text', 'us-east-1'),
                ('account_id', 'Account ID', 'text', 'Optional')
            ],
            'AWS security findings aggregation and compliance'
        )
        layout.addWidget(aws)
        
        # Azure Sentinel
        azure = self._create_integration_section(
            'azure_sentinel',
            'Microsoft Azure Sentinel',
            [
                ('tenant_id', 'Tenant ID', 'text', 'Azure AD Tenant ID'),
                ('client_id', 'Client ID', 'text', 'Application Client ID'),
                ('client_secret', 'Client Secret', 'password', 'Application Secret'),
                ('workspace_id', 'Workspace ID', 'text', 'Log Analytics Workspace ID')
            ],
            'Cloud-native SIEM for security monitoring'
        )
        layout.addWidget(azure)
        
        # GCP Security Command Center
        gcp = self._create_integration_section(
            'gcp_security',
            'GCP Security Command Center',
            [
                ('project_id', 'Project ID', 'text', 'Your GCP project ID'),
                ('credentials_file', 'Service Account Key File', 'text', '/path/to/credentials.json')
            ],
            'Google Cloud security and risk management'
        )
        layout.addWidget(gcp)
        
        layout.addStretch()
        widget.setLayout(layout)
        scroll.setWidget(widget)
        self.tabs.addTab(scroll, "Cloud Security")
    
    def _create_network_security_tab(self):
        """Create Network Security platforms tab."""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Palo Alto Networks
        palo_alto = self._create_integration_section(
            'palo_alto',
            'Palo Alto Networks',
            [
                ('hostname', 'Firewall Hostname', 'text', 'firewall.example.com'),
                ('api_key', 'API Key', 'password', 'Enter PAN-OS API key'),
                ('verify_ssl', 'Verify SSL', 'checkbox', '')
            ],
            'Firewall management and threat prevention'
        )
        layout.addWidget(palo_alto)
        
        # Cisco Secure
        cisco = self._create_integration_section(
            'cisco_secure',
            'Cisco Secure (Umbrella/Firepower)',
            [
                ('api_url', 'API URL', 'text', 'https://api.umbrella.com'),
                ('api_key', 'API Key', 'password', 'Enter API key'),
                ('api_secret', 'API Secret', 'password', 'Enter API secret')
            ],
            'DNS security and next-gen firewall'
        )
        layout.addWidget(cisco)
        
        layout.addStretch()
        widget.setLayout(layout)
        scroll.setWidget(widget)
        self.tabs.addTab(scroll, "Network Security")
    
    def _create_vulnerability_tab(self):
        """Create Vulnerability Management tab."""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Tenable
        tenable = self._create_integration_section(
            'tenable',
            'Tenable (Nessus/io)',
            [
                ('access_key', 'Access Key', 'text', 'Your access key'),
                ('secret_key', 'Secret Key', 'password', 'Your secret key'),
                ('url', 'Tenable URL', 'text', 'https://cloud.tenable.com')
            ],
            'Vulnerability scanning and assessment'
        )
        layout.addWidget(tenable)
        
        # Qualys
        qualys = self._create_integration_section(
            'qualys',
            'Qualys',
            [
                ('api_url', 'API URL', 'text', 'https://qualysapi.qualys.com'),
                ('username', 'Username', 'text', 'Your username'),
                ('password', 'Password', 'password', 'Your password')
            ],
            'Vulnerability and compliance scanning'
        )
        layout.addWidget(qualys)
        
        layout.addStretch()
        widget.setLayout(layout)
        scroll.setWidget(widget)
        self.tabs.addTab(scroll, "Vulnerability Management")
    
    def _create_malware_analysis_tab(self):
        """Create Malware Analysis platforms tab."""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Hybrid Analysis
        hybrid = self._create_integration_section(
            'hybrid_analysis',
            'Hybrid Analysis',
            [
                ('api_key', 'API Key', 'password', 'Enter your Hybrid Analysis API key')
            ],
            'Automated malware analysis sandbox'
        )
        layout.addWidget(hybrid)
        
        # Joe Sandbox
        joe = self._create_integration_section(
            'joe_sandbox',
            'Joe Sandbox',
            [
                ('api_key', 'API Key', 'password', 'Enter your Joe Sandbox API key'),
                ('api_url', 'API URL', 'text', 'https://jbxcloud.joesecurity.org/api')
            ],
            'Advanced malware sandbox analysis'
        )
        layout.addWidget(joe)
        
        # ANY.RUN
        anyrun = self._create_integration_section(
            'anyrun',
            'ANY.RUN',
            [
                ('api_key', 'API Key', 'password', 'Enter your ANY.RUN API key')
            ],
            'Interactive malware sandbox'
        )
        layout.addWidget(anyrun)
        
        layout.addStretch()
        widget.setLayout(layout)
        scroll.setWidget(widget)
        self.tabs.addTab(scroll, "Malware Analysis")
    
    def _create_identity_tab(self):
        """Create Identity & Access Management tab."""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Okta
        okta = self._create_integration_section(
            'okta',
            'Okta',
            [
                ('domain', 'Okta Domain', 'text', 'yourcompany.okta.com'),
                ('api_token', 'API Token', 'password', 'Enter your Okta API token')
            ],
            'Identity and access management'
        )
        layout.addWidget(okta)
        
        # Azure AD
        azure_ad = self._create_integration_section(
            'azure_ad',
            'Azure Active Directory',
            [
                ('tenant_id', 'Tenant ID', 'text', 'Azure AD Tenant ID'),
                ('client_id', 'Client ID', 'text', 'Application Client ID'),
                ('client_secret', 'Client Secret', 'password', 'Application Secret')
            ],
            'Microsoft identity platform and directory services'
        )
        layout.addWidget(azure_ad)
        
        layout.addStretch()
        widget.setLayout(layout)
        scroll.setWidget(widget)
        self.tabs.addTab(scroll, "Identity & Access")
    
    def _create_email_security_tab(self):
        """Create Email Security platforms tab."""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Mimecast
        mimecast = self._create_integration_section(
            'mimecast',
            'Mimecast',
            [
                ('base_url', 'Base URL', 'text', 'https://us-api.mimecast.com'),
                ('app_id', 'App ID', 'text', 'Your application ID'),
                ('app_key', 'App Key', 'password', 'Your application key'),
                ('access_key', 'Access Key', 'text', 'Your access key'),
                ('secret_key', 'Secret Key', 'password', 'Your secret key')
            ],
            'Email security platform and threat protection'
        )
        layout.addWidget(mimecast)
        
        # Proofpoint
        proofpoint = self._create_integration_section(
            'proofpoint',
            'Proofpoint',
            [
                ('api_url', 'API URL', 'text', 'https://tap-api-v2.proofpoint.com'),
                ('service_principal', 'Service Principal', 'text', 'Your service principal'),
                ('secret', 'Secret', 'password', 'Your API secret')
            ],
            'Advanced email threat protection'
        )
        layout.addWidget(proofpoint)
        
        layout.addStretch()
        widget.setLayout(layout)
        scroll.setWidget(widget)
        self.tabs.addTab(scroll, "Email Security")
    
    def _create_utilities_tab(self):
        """Create Utilities & Tools tab."""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        
        widget = QWidget()
        layout = QVBoxLayout()
        
        # GitHub
        github = self._create_integration_section(
            'github',
            'GitHub',
            [
                ('api_token', 'Personal Access Token', 'password', 'Enter your GitHub PAT'),
                ('default_org', 'Default Organization', 'text', 'Optional')
            ],
            'Code repository management and IOC tracking'
        )
        layout.addWidget(github)
        
        # Elasticsearch
        elasticsearch = self._create_integration_section(
            'elasticsearch',
            'Elasticsearch',
            [
                ('hosts', 'Hosts', 'text', 'localhost:9200 (comma-separated)'),
                ('username', 'Username', 'text', 'elastic'),
                ('password', 'Password', 'password', 'Enter password'),
                ('use_ssl', 'Use SSL', 'checkbox', ''),
                ('verify_certs', 'Verify Certificates', 'checkbox', '')
            ],
            'Advanced log search and analytics'
        )
        layout.addWidget(elasticsearch)
        
        # PostgreSQL
        postgresql = self._create_integration_section(
            'postgresql',
            'PostgreSQL',
            [
                ('host', 'Host', 'text', 'localhost'),
                ('port', 'Port', 'text', '5432'),
                ('database', 'Database', 'text', 'deeptempo'),
                ('username', 'Username', 'text', 'postgres'),
                ('password', 'Password', 'password', 'Enter password')
            ],
            'Relational database for structured data'
        )
        layout.addWidget(postgresql)
        
        # IP Geolocation
        ipgeo = self._create_integration_section(
            'ip_geolocation',
            'IP Geolocation & ASN',
            [
                ('service', 'Service', 'combo', ['IPinfo', 'MaxMind', 'IP2Location']),
                ('api_key', 'API Key', 'password', 'Enter API key if required')
            ],
            'IP address intelligence and geolocation'
        )
        layout.addWidget(ipgeo)
        
        layout.addStretch()
        widget.setLayout(layout)
        scroll.setWidget(widget)
        self.tabs.addTab(scroll, "Utilities & Tools")
    
    def _load_config_to_ui(self):
        """Load configuration into UI fields."""
        enabled = set(self.config.get('enabled_integrations', []))
        self.enabled_integrations = enabled
        integrations = self.config.get('integrations', {})
        
        for integration_id, fields in self.integration_fields.items():
            # Set enabled state
            if '_enabled' in fields:
                is_enabled = integration_id in enabled
                fields['_enabled'].setChecked(is_enabled)
                
                # Load field values
                if integration_id in integrations:
                    integration_config = integrations[integration_id]
                    
                    for field_name, widget in fields.items():
                        if field_name == '_enabled':
                            continue
                        
                        # Try to load from config
                        value = integration_config.get(field_name, '')
                        
                        # For sensitive fields, try keyring
                        if not value and ('password' in field_name.lower() or 'token' in field_name.lower() or 'key' in field_name.lower()):
                            try:
                                value = keyring.get_password(self.SERVICE_NAME, f"{integration_id}_{field_name}") or ''
                            except Exception:
                                value = ''
                        
                        # Set widget value
                        if isinstance(widget, QLineEdit):
                            widget.setText(str(value))
                        elif isinstance(widget, QCheckBox):
                            widget.setChecked(bool(value))
                        elif isinstance(widget, QComboBox):
                            index = widget.findText(str(value))
                            if index >= 0:
                                widget.setCurrentIndex(index)
                
                # Enable/disable fields based on checkbox state
                self._toggle_integration(integration_id, is_enabled)
    
    def _save_and_close(self):
        """Save configuration and close dialog."""
        if self._save_config():
            QMessageBox.information(
                self,
                "Success",
                f"Configuration saved successfully!\n\n"
                f"Enabled integrations: {len(self.enabled_integrations)}"
            )
            self.accept()
        else:
            QMessageBox.critical(
                self,
                "Error",
                "Failed to save configuration. Check logs for details."
            )
    
    @staticmethod
    def get_integration_config(integration_id: str) -> dict:
        """
        Get configuration for a specific integration.
        
        Args:
            integration_id: The integration identifier
            
        Returns:
            Configuration dictionary with sensitive data from keyring
        """
        config_file = IntegrationsConfigDialog.CONFIG_FILE
        if not config_file.exists():
            return {}
        
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
            
            if integration_id not in config.get('enabled_integrations', []):
                return {}
            
            integration_config = config.get('integrations', {}).get(integration_id, {})
            
            # Load sensitive data from keyring
            for key in list(integration_config.keys()):
                if not integration_config[key] and ('password' in key.lower() or 'token' in key.lower() or 'key' in key.lower()):
                    try:
                        value = keyring.get_password(
                            IntegrationsConfigDialog.SERVICE_NAME,
                            f"{integration_id}_{key}"
                        )
                        if value:
                            integration_config[key] = value
                    except Exception:
                        pass
            
            return integration_config
        
        except Exception as e:
            logger.error(f"Error loading integration config for {integration_id}: {e}")
            return {}
    
    @staticmethod
    def is_integration_enabled(integration_id: str) -> bool:
        """Check if an integration is enabled."""
        config_file = IntegrationsConfigDialog.CONFIG_FILE
        if not config_file.exists():
            return False
        
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
            
            return integration_id in config.get('enabled_integrations', [])
        except Exception:
            return False

