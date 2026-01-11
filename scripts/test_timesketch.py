#!/usr/bin/env python3
"""Diagnostic script to test Timesketch connection and server status."""

import sys
import json
from pathlib import Path
import requests
import keyring
import urllib3

# Disable SSL warnings for self-signed certificates
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.timesketch_service import TimesketchService
from ui.timesketch_config import TimesketchConfigDialog


def test_timesketch_server(server_url: str) -> tuple[bool, str]:
    """Test if Timesketch server is reachable."""
    try:
        # Try to reach the server
        response = requests.get(server_url, timeout=5, verify=False)
        return True, f"Server is reachable (HTTP {response.status_code})"
    except requests.exceptions.ConnectionError as e:
        return False, f"Cannot connect to server - is it running?\n   Error: {str(e)}"
    except requests.exceptions.Timeout:
        return False, "Connection timeout - server may be slow or unreachable"
    except Exception as e:
        return False, f"Error: {str(e)}"


def test_timesketch_api(server_url: str) -> tuple[bool, str]:
    """Test Timesketch API endpoint."""
    try:
        api_url = f"{server_url.rstrip('/')}/api/v1"
        response = requests.get(f"{api_url}/sketches/", timeout=5, verify=False)
        if response.status_code == 200:
            return True, "API endpoint is accessible"
        elif response.status_code == 401:
            return True, "API requires authentication (this is normal)"
        else:
            return False, f"API returned HTTP {response.status_code}"
    except Exception as e:
        return False, f"API test error: {str(e)}"


def check_config() -> dict:
    """Check Timesketch configuration."""
    config_file = TimesketchConfigDialog.CONFIG_FILE
    
    print(f"\n{'='*60}")
    print("Timesketch Configuration Check")
    print(f"{'='*60}")
    
    if not config_file.exists():
        print(f"❌ Configuration file not found: {config_file}")
        print("   Timesketch is not configured.")
        return None
    
    print(f"✅ Configuration file found: {config_file}")
    
    try:
        with open(config_file, 'r') as f:
            config = json.load(f)
        
        print(f"\nConfiguration:")
        print(f"  Server URL: {config.get('server_url', 'Not set')}")
        print(f"  Auth Method: {config.get('auth_method', 'Not set')}")
        print(f"  Verify SSL: {config.get('verify_ssl', True)}")
        
        # Load sensitive data
        sensitive = {}
        try:
            if config.get('auth_method') == 'password':
                username = keyring.get_password(
                    TimesketchConfigDialog.SERVICE_NAME,
                    TimesketchConfigDialog.KEYRING_USERNAME
                )
                password = keyring.get_password(
                    TimesketchConfigDialog.SERVICE_NAME,
                    TimesketchConfigDialog.KEYRING_PASSWORD
                )
                if username:
                    sensitive['username'] = username
                    print(f"  Username: {username}")
                if password:
                    sensitive['password'] = '***'  # Don't print password
                    print(f"  Password: {'*' * len(password) if password else 'Not set'}")
            else:
                token = keyring.get_password(
                    TimesketchConfigDialog.SERVICE_NAME,
                    TimesketchConfigDialog.KEYRING_TOKEN
                )
                if token:
                    sensitive['api_token'] = token
                    print(f"  API Token: {'*' * 20} (set)")
        except Exception as e:
            print(f"  ⚠️  Could not load credentials from keyring: {e}")
        
        config.update(sensitive)
        return config
        
    except Exception as e:
        print(f"❌ Error reading configuration: {e}")
        return None


def main():
    """Run Timesketch diagnostics."""
    print("\n" + "="*60)
    print("Timesketch Connection Diagnostic Tool")
    print("="*60)
    
    # Check configuration
    config = check_config()
    
    if not config:
        print("\n❌ Cannot proceed without configuration.")
        print("\nTo configure Timesketch:")
        print("  1. Open the application")
        print("  2. Go to Settings → Timesketch Configuration")
        print("  3. Enter your Timesketch server URL and credentials")
        return 1
    
    server_url = config.get('server_url', '').strip()
    if not server_url:
        print("\n❌ Server URL is not configured.")
        return 1
    
    print(f"\n{'='*60}")
    print("Server Connectivity Test")
    print(f"{'='*60}")
    
    # Test server connectivity
    print(f"\nTesting server: {server_url}")
    server_ok, server_msg = test_timesketch_server(server_url)
    if server_ok:
        print(f"✅ {server_msg}")
    else:
        print(f"❌ {server_msg}")
        print("\n⚠️  Server is not reachable. Please check:")
        print("  1. Is the Timesketch server running?")
        print("  2. Is the URL correct?")
        print("  3. Are there any firewall/network issues?")
        return 1
    
    # Test API endpoint
    print(f"\nTesting API endpoint...")
    api_ok, api_msg = test_timesketch_api(server_url)
    if api_ok:
        print(f"✅ {api_msg}")
    else:
        print(f"⚠️  {api_msg}")
    
    print(f"\n{'='*60}")
    print("Authentication Test")
    print(f"{'='*60}")
    
    # Test authentication
    try:
        service = TimesketchService(
            server_url=server_url,
            username=config.get('username'),
            password=config.get('password'),
            api_token=config.get('api_token')
        )
        
        print("\nAttempting authentication...")
        success, message = service.test_connection()
        
        if success:
            print(f"✅ {message}")
            print("\n✅ Timesketch connection is working!")
            
            # Try to list sketches
            print("\nTesting API calls...")
            sketches = service.list_sketches(limit=5)
            print(f"✅ Successfully retrieved {len(sketches)} sketches")
            
            if sketches:
                print("\nSample sketches:")
                for sketch in sketches[:3]:
                    print(f"  - {sketch.get('name', 'Unknown')} (ID: {sketch.get('id', 'N/A')})")
            
            return 0
        else:
            print(f"❌ {message}")
            print("\n⚠️  Authentication failed. Please check:")
            print("  1. Username/password or API token is correct")
            print("  2. User has proper permissions")
            print("  3. Timesketch server authentication is working")
            return 1
            
    except Exception as e:
        print(f"❌ Error during authentication test: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

