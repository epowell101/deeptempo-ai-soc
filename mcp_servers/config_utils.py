"""
Utility module for MCP servers to read integration configurations.
This replaces the old ui.integrations_config module.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

def get_integration_config(integration_id: str) -> Dict[str, Any]:
    """
    Get configuration for a specific integration from the central config file.
    
    Args:
        integration_id: The ID of the integration (e.g., 'virustotal', 'jira', etc.)
    
    Returns:
        Dictionary containing the integration configuration, or empty dict if not found
    """
    config_file = Path.home() / '.deeptempo' / 'integrations_config.json'
    
    if not config_file.exists():
        logger.warning(f"Integration config file not found: {config_file}")
        return {}
    
    try:
        with open(config_file, 'r') as f:
            config_data = json.load(f)
        
        # Check if the integration is enabled
        enabled_integrations = config_data.get('enabled_integrations', [])
        if integration_id not in enabled_integrations:
            logger.info(f"Integration '{integration_id}' is not enabled")
            return {}
        
        # Get the integration's configuration
        integrations = config_data.get('integrations', {})
        integration_config = integrations.get(integration_id, {})
        
        if not integration_config:
            logger.warning(f"No configuration found for integration '{integration_id}'")
        
        return integration_config
    
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing integration config file: {e}")
        return {}
    except Exception as e:
        logger.error(f"Error loading integration config for '{integration_id}': {e}")
        return {}


def is_integration_enabled(integration_id: str) -> bool:
    """
    Check if an integration is enabled.
    
    Args:
        integration_id: The ID of the integration
    
    Returns:
        True if the integration is enabled, False otherwise
    """
    config_file = Path.home() / '.deeptempo' / 'integrations_config.json'
    
    if not config_file.exists():
        return False
    
    try:
        with open(config_file, 'r') as f:
            config_data = json.load(f)
        
        enabled_integrations = config_data.get('enabled_integrations', [])
        return integration_id in enabled_integrations
    
    except Exception as e:
        logger.error(f"Error checking if integration '{integration_id}' is enabled: {e}")
        return False


def get_all_enabled_integrations() -> list[str]:
    """
    Get a list of all enabled integration IDs.
    
    Returns:
        List of enabled integration IDs
    """
    config_file = Path.home() / '.deeptempo' / 'integrations_config.json'
    
    if not config_file.exists():
        return []
    
    try:
        with open(config_file, 'r') as f:
            config_data = json.load(f)
        
        return config_data.get('enabled_integrations', [])
    
    except Exception as e:
        logger.error(f"Error getting enabled integrations: {e}")
        return []


# Backward compatibility with old import style
class IntegrationsConfigDialog:
    """
    Legacy compatibility class for old MCP servers.
    Provides the same interface as the old ui.integrations_config module.
    """
    
    @staticmethod
    def get_integration_config(integration_id: str) -> Dict[str, Any]:
        """Get integration configuration (legacy interface)."""
        return get_integration_config(integration_id)

