#!/usr/bin/env python3
"""
Script to update all MCP servers to use the new config_utils module
instead of the old ui.integrations_config module.
"""

import os
import re
from pathlib import Path

# Get the mcp_servers directory
mcp_servers_dir = Path(__file__).parent.parent / 'mcp_servers'

# Pattern to match the old import style
old_pattern = re.compile(
    r'def get_(\w+)_config\(\):\s*\n'
    r'\s*"""[^"]*"""\s*\n'
    r'\s*try:\s*\n'
    r'\s*from ui\.integrations_config import IntegrationsConfigDialog\s*\n'
    r'\s*config = IntegrationsConfigDialog\.get_integration_config\([\'"]([^\'"]+)[\'"]\)\s*\n'
    r'\s*return config\s*\n'
    r'\s*except Exception as e:\s*\n'
    r'\s*logger\.error\([^)]+\)\s*\n'
    r'\s*return \{\}',
    re.MULTILINE
)

# New import template
new_template = '''def get_{func_name}_config():
    """Get {integration_name} configuration from integrations config."""
    try:
        import sys
        from pathlib import Path
        # Add parent directory to path to import config_utils
        parent_dir = str(Path(__file__).parent.parent)
        if parent_dir not in sys.path:
            sys.path.insert(0, parent_dir)
        from config_utils import get_integration_config
        config = get_integration_config('{integration_id}')
        return config
    except Exception as e:
        logger.error(f"Error loading {integration_name} config: {{e}}")
        return {{}}'''

def update_server_file(file_path: Path):
    """Update a single server file."""
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Check if file needs updating
        if 'ui.integrations_config' not in content:
            return False
        
        # Find and replace the pattern
        def replace_func(match):
            func_name = match.group(1)
            integration_id = match.group(2)
            
            # Convert integration_id to proper name (handle underscores to hyphens)
            integration_name = integration_id.replace('_', ' ').title()
            
            return new_template.format(
                func_name=func_name,
                integration_name=integration_name,
                integration_id=integration_id
            )
        
        updated_content = old_pattern.sub(replace_func, content)
        
        if updated_content != content:
            with open(file_path, 'w') as f:
                f.write(updated_content)
            return True
        
        return False
    
    except Exception as e:
        print(f"Error updating {file_path}: {e}")
        return False

def main():
    """Update all MCP server files."""
    updated_count = 0
    
    # Iterate through all server directories
    for server_dir in mcp_servers_dir.iterdir():
        if not server_dir.is_dir() or server_dir.name == '__pycache__':
            continue
        
        server_file = server_dir / 'server.py'
        if server_file.exists():
            if update_server_file(server_file):
                print(f"✓ Updated: {server_dir.name}")
                updated_count += 1
            else:
                print(f"- Skipped: {server_dir.name} (no changes needed)")
    
    print(f"\nTotal updated: {updated_count} servers")

if __name__ == '__main__':
    main()

