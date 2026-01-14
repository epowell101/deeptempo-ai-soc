"""Configuration API endpoints."""

from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from pathlib import Path
import json
import logging

# Import new secrets manager
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from secrets_manager import get_secret, set_secret, delete_secret, get_secrets_manager

router = APIRouter()
logger = logging.getLogger(__name__)


class ClaudeConfig(BaseModel):
    """Claude API configuration."""
    api_key: str


class S3Config(BaseModel):
    """S3 configuration."""
    bucket_name: str
    region: str = "us-east-1"
    access_key_id: str
    secret_access_key: str
    findings_path: str = "findings.json"
    cases_path: str = "cases.json"




class ThemeConfig(BaseModel):
    """Theme configuration."""
    theme: str = "dark"  # dark or light




class IntegrationsConfig(BaseModel):
    """Integrations configuration."""
    enabled_integrations: list[str] = []
    integrations: dict = {}


class GeneralConfig(BaseModel):
    """General application settings."""
    auto_start_sync: bool = False
    show_notifications: bool = True
    theme: str = "dark"
    enable_keyring: bool = False  # Whether to use OS keyring for secrets


class GitHubConfig(BaseModel):
    """GitHub MCP server configuration."""
    token: str


class PostgreSQLConfig(BaseModel):
    """PostgreSQL MCP server configuration."""
    connection_string: str


@router.get("/claude")
async def get_claude_config():
    """
    Get Claude API configuration status.
    
    Returns:
        Configuration status (without exposing the key)
    """
    try:
        # Try new key names first, then legacy names
        api_key = (get_secret("CLAUDE_API_KEY") or 
                   get_secret("ANTHROPIC_API_KEY") or
                   get_secret("claude_api_key") or
                   get_secret("anthropic_api_key"))
        
        has_key = bool(api_key)
        
        return {
            "configured": has_key,
            "key_preview": f"{api_key[:8]}..." if has_key else None
        }
    except Exception as e:
        logger.error(f"Error getting Claude config: {e}")
        return {"configured": False, "error": str(e)}


@router.post("/claude")
async def set_claude_config(config: ClaudeConfig):
    """
    Set Claude API configuration.
    
    Args:
        config: Claude configuration
    
    Returns:
        Success status
    """
    try:
        # Use standard environment variable name
        success = set_secret("CLAUDE_API_KEY", config.api_key)
        if success:
            return {"success": True, "message": "API key saved securely"}
        else:
            raise HTTPException(status_code=500, detail="Failed to save API key")
    except Exception as e:
        logger.error(f"Error setting Claude config: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/s3")
async def get_s3_config():
    """
    Get S3 configuration status.
    
    Returns:
        Configuration status
    """
    config_file = Path.home() / '.deeptempo' / 's3_config.json'
    
    if not config_file.exists():
        return {"configured": False}
    
    try:
        with open(config_file, 'r') as f:
            config = json.load(f)
        
        return {
            "configured": True,
            "bucket_name": config.get('bucket_name'),
            "region": config.get('region'),
            "findings_path": config.get('findings_path'),
            "cases_path": config.get('cases_path')
        }
    except Exception as e:
        logger.error(f"Error getting S3 config: {e}")
        return {"configured": False, "error": str(e)}


@router.post("/s3")
async def set_s3_config(config: S3Config):
    """
    Set S3 configuration.
    
    Args:
        config: S3 configuration
    
    Returns:
        Success status
    """
    config_file = Path.home() / '.deeptempo' / 's3_config.json'
    config_file.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        # Save non-sensitive config to file
        config_data = {
            "bucket_name": config.bucket_name,
            "region": config.region,
            "findings_path": config.findings_path,
            "cases_path": config.cases_path
        }
        
        with open(config_file, 'w') as f:
            json.dump(config_data, f, indent=2)
        
        # Save credentials using secrets manager
        set_secret("AWS_ACCESS_KEY_ID", config.access_key_id)
        set_secret("AWS_SECRET_ACCESS_KEY", config.secret_access_key)
        
        return {"success": True, "message": "S3 configuration saved"}
    except Exception as e:
        logger.error(f"Error setting S3 config: {e}")
        raise HTTPException(status_code=500, detail=str(e))




@router.get("/theme")
async def get_theme_config():
    """
    Get theme configuration.
    
    Returns:
        Theme configuration
    """
    config_file = Path.home() / '.deeptempo' / 'theme_config.json'
    
    if not config_file.exists():
        return {"theme": "dark"}
    
    try:
        with open(config_file, 'r') as f:
            config = json.load(f)
        return {"theme": config.get('theme', 'dark')}
    except Exception as e:
        logger.error(f"Error getting theme config: {e}")
        return {"theme": "dark"}


@router.post("/theme")
async def set_theme_config(config: ThemeConfig):
    """
    Set theme configuration.
    
    Args:
        config: Theme configuration
    
    Returns:
        Success status
    """
    config_file = Path.home() / '.deeptempo' / 'theme_config.json'
    config_file.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        with open(config_file, 'w') as f:
            json.dump({"theme": config.theme}, f, indent=2)
        
        return {"success": True, "message": "Theme saved"}
    except Exception as e:
        logger.error(f"Error setting theme config: {e}")
        raise HTTPException(status_code=500, detail=str(e))




@router.get("/integrations")
async def get_integrations_config():
    """
    Get integrations configuration.
    
    Returns:
        Configuration status and enabled integrations
    """
    config_file = Path.home() / '.deeptempo' / 'integrations_config.json'
    
    if not config_file.exists():
        return {"configured": False, "enabled_integrations": [], "integrations": {}}
    
    try:
        with open(config_file, 'r') as f:
            config = json.load(f)
        
        return {
            "configured": True,
            "enabled_integrations": config.get('enabled_integrations', []),
            "integrations": config.get('integrations', {})
        }
    except Exception as e:
        logger.error(f"Error getting integrations config: {e}")
        return {"configured": False, "enabled_integrations": [], "integrations": {}, "error": str(e)}


@router.post("/integrations")
async def set_integrations_config(config: IntegrationsConfig):
    """
    Set integrations configuration.
    
    Args:
        config: Integrations configuration
    
    Returns:
        Success status
    """
    config_file = Path.home() / '.deeptempo' / 'integrations_config.json'
    config_file.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        config_data = {
            "enabled_integrations": config.enabled_integrations,
            "integrations": config.integrations
        }
        
        with open(config_file, 'w') as f:
            json.dump(config_data, f, indent=2)
        
        return {"success": True, "message": "Integrations configuration saved"}
    except Exception as e:
        logger.error(f"Error setting integrations config: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/integrations/status")
async def get_integrations_status():
    """
    Get status of all integrations.
    
    Returns:
        Status information for all integrations
    """
    try:
        # Import here to avoid circular dependencies
        sys.path.insert(0, str(Path(__file__).parent.parent.parent))
        from services.integration_bridge_service import get_integration_bridge
        
        bridge = get_integration_bridge()
        statuses = bridge.get_all_integration_statuses()
        
        return {
            "success": True,
            "statuses": statuses
        }
    except Exception as e:
        logger.error(f"Error getting integration statuses: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/integrations/{integration_id}/test")
async def test_integration(integration_id: str):
    """
    Test an integration connection.
    
    Args:
        integration_id: Integration identifier
    
    Returns:
        Test result with success/failure and message
    """
    try:
        # Import here to avoid circular dependencies
        sys.path.insert(0, str(Path(__file__).parent.parent.parent))
        from services.integration_bridge_service import get_integration_bridge
        
        bridge = get_integration_bridge()
        status = bridge.get_integration_status(integration_id)
        
        if not status['configured']:
            raise HTTPException(status_code=400, detail="Integration not configured")
        
        if not status['server_available']:
            return {
                "success": False,
                "message": f"Integration server not yet implemented. The '{integration_id}' integration is planned but the backend MCP server needs to be created.",
                "status": status,
                "implementation_status": "pending"
            }
        
        if not status['enabled']:
            return {
                "success": False,
                "message": "Integration is configured but not enabled. Please enable it in the integrations list.",
                "status": status
            }
        
        # TODO: Implement actual connection test using MCP client
        # For now, we just verify the configuration is complete
        integration_config = bridge.get_integration_config(integration_id)
        
        # Check if required fields are present (basic validation)
        if not integration_config:
            raise HTTPException(status_code=400, detail="Integration configuration is empty")
        
        # Prepare environment variables to verify they're being set correctly
        env_vars = bridge._config_to_env_vars(integration_id, integration_config)
        
        return {
            "success": True,
            "message": f"Integration '{integration_id}' is configured and ready. Configuration will be passed to the MCP server as environment variables.",
            "status": status,
            "env_var_count": len(env_vars),
            "server_name": status.get('server_name', 'unknown')
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error testing integration '{integration_id}': {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/general")
async def get_general_config():
    """
    Get general application settings.
    
    Returns:
        General configuration
    """
    config_file = Path.home() / '.deeptempo' / 'general_config.json'
    
    if not config_file.exists():
        return {
            "auto_start_sync": False, 
            "show_notifications": True, 
            "theme": "dark",
            "enable_keyring": False
        }
    
    try:
        with open(config_file, 'r') as f:
            config = json.load(f)
        
        return {
            "auto_start_sync": config.get('auto_start_sync', False),
            "show_notifications": config.get('show_notifications', True),
            "theme": config.get('theme', 'dark'),
            "enable_keyring": config.get('enable_keyring', False)
        }
    except Exception as e:
        logger.error(f"Error getting general config: {e}")
        return {
            "auto_start_sync": False, 
            "show_notifications": True, 
            "theme": "dark",
            "enable_keyring": False
        }


@router.post("/general")
async def set_general_config(config: GeneralConfig):
    """
    Set general application settings.
    
    Args:
        config: General configuration
    
    Returns:
        Success status
    """
    config_file = Path.home() / '.deeptempo' / 'general_config.json'
    config_file.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        config_data = {
            "auto_start_sync": config.auto_start_sync,
            "show_notifications": config.show_notifications,
            "theme": config.theme,
            "enable_keyring": config.enable_keyring
        }
        
        with open(config_file, 'w') as f:
            json.dump(config_data, f, indent=2)
        
        # Update the global secrets manager if keyring setting changed
        try:
            from secrets_manager import get_secrets_manager
            # Force reinitialize with new setting
            import secrets_manager as sm_module
            sm_module._secrets_manager = None  # Reset global instance
            get_secrets_manager(enable_keyring=config.enable_keyring)
            logger.info(f"Secrets manager updated: enable_keyring={config.enable_keyring}")
        except Exception as e:
            logger.warning(f"Could not update secrets manager: {e}")
        
        return {"success": True, "message": "General settings saved"}
    except Exception as e:
        logger.error(f"Error setting general config: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/github")
async def get_github_config():
    """
    Get GitHub MCP server configuration status.
    
    Returns:
        Configuration status (without exposing the token)
    """
    try:
        token = get_secret("GITHUB_TOKEN")
        has_token = bool(token)
        
        return {
            "configured": has_token,
            "token_preview": f"{token[:12]}..." if has_token else None
        }
    except Exception as e:
        logger.error(f"Error getting GitHub config: {e}")
        return {"configured": False, "error": str(e)}


@router.post("/github")
async def set_github_config(config: GitHubConfig):
    """
    Set GitHub MCP server configuration.
    
    Args:
        config: GitHub configuration
    
    Returns:
        Success status
    """
    try:
        success = set_secret("GITHUB_TOKEN", config.token)
        if success:
            return {"success": True, "message": "GitHub token saved securely"}
        else:
            raise HTTPException(status_code=500, detail="Failed to save GitHub token")
    except Exception as e:
        logger.error(f"Error setting GitHub config: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/postgresql")
async def get_postgresql_config():
    """
    Get PostgreSQL MCP server configuration status.
    
    Returns:
        Configuration status
    """
    try:
        conn_str = get_secret("POSTGRESQL_CONNECTION_STRING")
        has_config = bool(conn_str)
        
        # Extract host from connection string for preview (if exists)
        preview = None
        if conn_str and "postgresql://" in conn_str:
            try:
                # Format: postgresql://user:pass@host:port/db
                parts = conn_str.split("@")
                if len(parts) > 1:
                    host_part = parts[1].split("/")[0]
                    preview = f"postgresql://***@{host_part}/***"
            except:
                preview = "postgresql://***:***@***/***"
        
        return {
            "configured": has_config,
            "connection_preview": preview
        }
    except Exception as e:
        logger.error(f"Error getting PostgreSQL config: {e}")
        return {"configured": False, "error": str(e)}


@router.post("/postgresql")
async def set_postgresql_config(config: PostgreSQLConfig):
    """
    Set PostgreSQL MCP server configuration.
    
    Args:
        config: PostgreSQL configuration
    
    Returns:
        Success status
    """
    try:
        success = set_secret("POSTGRESQL_CONNECTION_STRING", config.connection_string)
        if success:
            return {"success": True, "message": "PostgreSQL connection string saved securely"}
        else:
            raise HTTPException(status_code=500, detail="Failed to save PostgreSQL connection string")
    except Exception as e:
        logger.error(f"Error setting PostgreSQL config: {e}")
        raise HTTPException(status_code=500, detail=str(e))

