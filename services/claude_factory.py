"""Factory for creating Claude service instances - allows easy switching between implementations."""

import os
import json
from pathlib import Path
from typing import Literal

ClaudeImplementation = Literal["direct", "agent_sdk"]


class ClaudeServiceFactory:
    """Factory for creating Claude service instances."""
    
    CONFIG_FILE = Path.home() / ".deeptempo" / "claude_config.json"
    
    @classmethod
    def get_default_implementation(cls) -> ClaudeImplementation:
        """Get the default implementation from config."""
        try:
            if cls.CONFIG_FILE.exists():
                with open(cls.CONFIG_FILE, 'r') as f:
                    config = json.load(f)
                    impl = config.get('implementation', 'direct')
                    if impl in ['direct', 'agent_sdk']:
                        return impl
        except Exception:
            pass
        
        return "agent_sdk"  # Default to Claude Agent SDK (Python 3.10+ required)
    
    @classmethod
    def set_default_implementation(cls, implementation: ClaudeImplementation):
        """Set the default implementation in config."""
        cls.CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
        
        config = {}
        if cls.CONFIG_FILE.exists():
            try:
                with open(cls.CONFIG_FILE, 'r') as f:
                    config = json.load(f)
            except Exception:
                pass
        
        config['implementation'] = implementation
        
        with open(cls.CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
    
    @classmethod
    def create(cls, implementation: ClaudeImplementation = None, **kwargs):
        """
        Create a Claude service instance.
        
        Args:
            implementation: Which implementation to use ('direct' or 'agent_sdk').
                          If None, uses the default from config.
            **kwargs: Arguments to pass to the service constructor.
        
        Returns:
            ClaudeService or ClaudeAgentService instance.
        
        Raises:
            ImportError: If agent_sdk is requested but not installed.
            ValueError: If invalid implementation specified.
        """
        if implementation is None:
            implementation = cls.get_default_implementation()
        
        if implementation == "direct":
            from services.claude_service import ClaudeService
            return ClaudeService(**kwargs)
        
        elif implementation == "agent_sdk":
            try:
                from services.claude_agent_service import ClaudeAgentService
                return ClaudeAgentService(**kwargs)
            except ImportError as e:
                # Fall back to direct implementation if agent SDK not available
                import sys
                logger = __import__('logging').getLogger(__name__)
                logger.warning(
                    f"Claude Agent SDK not available (requires Python 3.10+, you have {sys.version_info.major}.{sys.version_info.minor}). "
                    f"Falling back to direct implementation."
                )
                from services.claude_service import ClaudeService
                return ClaudeService(**kwargs)
        
        else:
            raise ValueError(
                f"Invalid implementation: {implementation}. "
                f"Must be 'direct' or 'agent_sdk'."
            )
    
    @classmethod
    def get_info(cls) -> dict:
        """Get information about available implementations."""
        info = {
            "current_default": cls.get_default_implementation(),
            "available": []
        }
        
        # Check direct implementation
        try:
            from services.claude_service import ClaudeService
            info["available"].append({
                "name": "direct",
                "available": True,
                "description": "Direct Anthropic SDK (current stable implementation)"
            })
        except ImportError:
            info["available"].append({
                "name": "direct",
                "available": False,
                "description": "Direct Anthropic SDK (not installed)"
            })
        
        # Check agent SDK
        try:
            from services.claude_agent_service import ClaudeAgentService
            info["available"].append({
                "name": "agent_sdk",
                "available": True,
                "description": "Claude Agent SDK (experimental)"
            })
        except ImportError:
            info["available"].append({
                "name": "agent_sdk",
                "available": False,
                "description": "Claude Agent SDK (not installed - pip install claude-agent-sdk)"
            })
        
        return info


# Convenience function for simple usage
def create_claude_service(implementation: ClaudeImplementation = None, **kwargs):
    """
    Convenience function to create a Claude service.
    
    Usage:
        # Use default implementation
        service = create_claude_service(use_mcp_tools=True)
        
        # Force specific implementation
        service = create_claude_service(implementation="direct", use_mcp_tools=True)
        service = create_claude_service(implementation="agent_sdk", use_mcp_tools=True)
    
    Args:
        implementation: 'direct' or 'agent_sdk' (None = use default)
        **kwargs: Arguments for service constructor
    
    Returns:
        ClaudeService or ClaudeAgentService instance
    """
    return ClaudeServiceFactory.create(implementation, **kwargs)


# For backward compatibility - use direct implementation by default
def get_claude_service(**kwargs):
    """
    Get the default Claude service instance.
    
    This maintains backward compatibility with existing code.
    """
    return ClaudeServiceFactory.create(**kwargs)


if __name__ == "__main__":
    import sys
    
    # Command-line interface for switching implementations
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "info":
            info = ClaudeServiceFactory.get_info()
            print("Claude Service Factory - Implementation Info")
            print("=" * 60)
            print(f"Current Default: {info['current_default']}")
            print("\nAvailable Implementations:")
            for impl in info['available']:
                status = "✅" if impl['available'] else "❌"
                print(f"  {status} {impl['name']}: {impl['description']}")
        
        elif command == "set" and len(sys.argv) > 2:
            impl = sys.argv[2]
            if impl in ["direct", "agent_sdk"]:
                ClaudeServiceFactory.set_default_implementation(impl)
                print(f"✅ Default implementation set to: {impl}")
            else:
                print(f"❌ Invalid implementation: {impl}")
                print("   Valid options: direct, agent_sdk")
        
        else:
            print("Usage:")
            print("  python claude_factory.py info              - Show available implementations")
            print("  python claude_factory.py set direct        - Set direct SDK as default")
            print("  python claude_factory.py set agent_sdk     - Set Agent SDK as default")
    
    else:
        # Show info if no command
        info = ClaudeServiceFactory.get_info()
        print("Current implementation:", info['current_default'])
        print("\nRun 'python claude_factory.py info' for more details")

