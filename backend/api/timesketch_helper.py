"""Helper functions for Timesketch integration."""

import json
import logging
from pathlib import Path
from typing import Optional
from services.timesketch_service import TimesketchService

logger = logging.getLogger(__name__)


def load_timesketch_service_from_integrations() -> Optional[TimesketchService]:
    """
    Load Timesketch service from integrations configuration.
    
    Returns:
        TimesketchService instance if configured, None otherwise
    """
    try:
        # Load integrations config
        config_file = Path.home() / '.deeptempo' / 'integrations_config.json'
        
        if not config_file.exists():
            logger.debug("Integrations config file not found")
            return None
        
        with open(config_file, 'r') as f:
            config = json.load(f)
        
        # Check if Timesketch is enabled
        enabled_integrations = config.get('enabled_integrations', [])
        if 'timesketch' not in enabled_integrations:
            logger.debug("Timesketch integration not enabled")
            return None
        
        # Get Timesketch configuration
        integrations = config.get('integrations', {})
        timesketch_config = integrations.get('timesketch', {})
        
        if not timesketch_config:
            logger.debug("Timesketch integration not configured")
            return None
        
        # Extract configuration
        server_url = timesketch_config.get('server_url')
        if not server_url:
            logger.error("Timesketch server_url not configured")
            return None
        
        username = timesketch_config.get('username')
        password = timesketch_config.get('password')
        api_token = timesketch_config.get('api_token')
        verify_ssl = timesketch_config.get('verify_ssl', True)
        
        # Require either username/password or api_token
        if not api_token and not (username and password):
            logger.error("Timesketch authentication not configured (need api_token or username/password)")
            return None
        
        # Create and return service
        service = TimesketchService(
            server_url=server_url,
            username=username,
            password=password,
            api_token=api_token,
            verify_ssl=verify_ssl
        )
        
        logger.info("Timesketch service loaded from integrations config")
        return service
        
    except Exception as e:
        logger.error(f"Error loading Timesketch service from integrations: {e}")
        return None


def is_timesketch_configured() -> bool:
    """
    Check if Timesketch is configured in integrations.
    
    Returns:
        True if configured and enabled, False otherwise
    """
    try:
        config_file = Path.home() / '.deeptempo' / 'integrations_config.json'
        
        if not config_file.exists():
            return False
        
        with open(config_file, 'r') as f:
            config = json.load(f)
        
        enabled_integrations = config.get('enabled_integrations', [])
        if 'timesketch' not in enabled_integrations:
            return False
        
        integrations = config.get('integrations', {})
        timesketch_config = integrations.get('timesketch', {})
        
        # Check required fields
        server_url = timesketch_config.get('server_url')
        api_token = timesketch_config.get('api_token')
        username = timesketch_config.get('username')
        password = timesketch_config.get('password')
        
        # Need server_url and either api_token or username/password
        return bool(server_url and (api_token or (username and password)))
        
    except Exception as e:
        logger.error(f"Error checking Timesketch configuration: {e}")
        return False

