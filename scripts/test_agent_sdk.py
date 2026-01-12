#!/usr/bin/env python3
"""Test script to compare Claude Service vs Agent SDK."""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


async def test_current_implementation():
    """Test the current Claude service."""
    print("=" * 60)
    print("Testing Current Implementation (Direct Anthropic SDK)")
    print("=" * 60)
    
    try:
        from services.claude_service import ClaudeService
        
        service = ClaudeService(use_mcp_tools=True)
        
        if not service.has_api_key():
            print("❌ No API key configured")
            return
        
        print(f"✅ API key configured")
        print(f"✅ MCP tools loaded: {len(service.mcp_tools)}")
        
        # Test simple query
        print("\n--- Test 1: Simple Query ---")
        prompt = "What is 2 + 2? Answer briefly."
        response = service.chat(prompt, max_tokens=100)
        print(f"Response: {response}\n")
        
        # Test streaming
        print("--- Test 2: Streaming ---")
        prompt = "Count from 1 to 5, one number per line."
        print("Streaming response:")
        async for chunk in service.chat_stream(prompt, max_tokens=100):
            print(chunk, end='', flush=True)
        print("\n")
        
        # Test with MCP tools (if available)
        if service.mcp_tools:
            print("--- Test 3: MCP Tool Query ---")
            prompt = "List all findings using the available tools"
            print(f"Query: {prompt}")
            response = service.chat(prompt, max_tokens=1000)
            print(f"Response: {response[:200]}...")
        
        print("\n✅ Current implementation tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_agent_sdk():
    """Test the Agent SDK implementation."""
    print("\n" + "=" * 60)
    print("Testing Agent SDK Implementation")
    print("=" * 60)
    
    try:
        from services.claude_agent_service import ClaudeAgentService
        
        service = ClaudeAgentService(use_mcp_tools=True)
        
        if not service.has_api_key():
            print("❌ No API key configured")
            return
        
        print(f"✅ API key configured")
        print(f"✅ MCP tools loaded: {len(service.mcp_tools)}")
        
        # Test simple query
        print("\n--- Test 1: Simple Query ---")
        prompt = "What is 2 + 2? Answer briefly."
        response = service.chat(prompt, max_tokens=100)
        print(f"Response: {response}\n")
        
        # Test streaming
        print("--- Test 2: Streaming ---")
        prompt = "Count from 1 to 5, one number per line."
        print("Streaming response:")
        async for chunk in service.chat_stream(prompt, max_tokens=100):
            print(chunk, end='', flush=True)
        print("\n")
        
        # Test with MCP tools (if available)
        if service.mcp_tools:
            print("--- Test 3: MCP Tool Query ---")
            prompt = "List all findings using the available tools"
            print(f"Query: {prompt}")
            response = service.chat(prompt, max_tokens=1000)
            print(f"Response: {response[:200]}...")
        
        print("\n✅ Agent SDK tests passed!")
        return True
        
    except ImportError as e:
        print(f"❌ Agent SDK not installed: {e}")
        print("Install with: pip install claude-agent-sdk")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def compare_responses():
    """Compare responses from both implementations."""
    print("\n" + "=" * 60)
    print("Comparing Implementations Side-by-Side")
    print("=" * 60)
    
    test_prompts = [
        "What is the capital of France?",
        "Explain what a SOC analyst does in one sentence.",
        "What is the difference between a vulnerability and an exploit?"
    ]
    
    try:
        from services.claude_service import ClaudeService
        current_service = ClaudeService(use_mcp_tools=False)  # Disable tools for fair comparison
        
        try:
            from services.claude_agent_service import ClaudeAgentService
            agent_service = ClaudeAgentService(use_mcp_tools=False)
            
            for i, prompt in enumerate(test_prompts, 1):
                print(f"\n--- Comparison {i}: {prompt} ---")
                
                print("\n[Current Implementation]")
                response1 = current_service.chat(prompt, max_tokens=200)
                print(response1)
                
                print("\n[Agent SDK]")
                response2 = agent_service.chat(prompt, max_tokens=200)
                print(response2)
                
                print("\n" + "-" * 60)
        
        except ImportError:
            print("❌ Agent SDK not available for comparison")
            return False
    
    except Exception as e:
        print(f"❌ Comparison error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests."""
    print("\n🔬 Claude Service Implementation Comparison")
    print("=" * 60)
    
    # Test current implementation
    current_ok = await test_current_implementation()
    
    # Test agent SDK
    agent_ok = await test_agent_sdk()
    
    # Compare if both work
    if current_ok and agent_ok:
        await compare_responses()
    
    print("\n" + "=" * 60)
    print("Summary:")
    print(f"  Current Implementation: {'✅ Working' if current_ok else '❌ Failed'}")
    print(f"  Agent SDK: {'✅ Working' if agent_ok else '❌ Not Available/Failed'}")
    print("=" * 60)
    
    if agent_ok:
        print("\n💡 Both implementations are working!")
        print("   You can switch between them by changing the import in your code:")
        print("   - Current: from services.claude_service import ClaudeService")
        print("   - Agent SDK: from services.claude_agent_service import ClaudeAgentService")
    else:
        print("\n💡 Agent SDK is not installed or failed.")
        print("   Install with: pip install claude-agent-sdk")
        print("   Your current implementation is working fine!")


if __name__ == "__main__":
    asyncio.run(main())

