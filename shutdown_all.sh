#!/bin/bash

echo "=========================================="
echo "DeepTempo AI SOC - Complete Shutdown"
echo "=========================================="
echo ""

# Kill the main backend process
echo "1. Stopping main backend process..."
pkill -f "start_web.sh"
pkill -f "uvicorn main:app"
pkill -f "backend.main:app"

# Kill any FastAPI/Uvicorn processes on port 6987
echo "2. Stopping any processes on port 6987..."
lsof -ti:6987 | xargs kill -9 2>/dev/null || echo "   No processes found on port 6987"

# Kill any MCP server processes
echo "3. Stopping MCP server processes..."
pkill -f "mcp_servers.deeptempo_findings_server"
pkill -f "mcp_servers.case_store_server"
pkill -f "mcp_servers.evidence_snippets_server"
pkill -f "mcp_servers..*_server.server"

# Kill any Python processes related to MCP
echo "4. Cleaning up any remaining MCP-related processes..."
ps aux | grep -i "mcp_servers" | grep -v grep | awk '{print $2}' | xargs kill -9 2>/dev/null || echo "   No MCP processes found"

# Kill frontend dev server if running
echo "5. Stopping frontend dev server (if running)..."
lsof -ti:6988 | xargs kill -9 2>/dev/null || echo "   No processes found on port 6988"
pkill -f "vite.*deeptempo"

# Clean up any zombie processes
echo "6. Cleaning up zombie processes..."
ps aux | grep -i defunct | grep -v grep | awk '{print $2}' | xargs kill -9 2>/dev/null || echo "   No zombie processes found"

echo ""
echo "=========================================="
echo "Checking for remaining processes..."
echo "=========================================="

# Check if anything is still running
REMAINING=$(ps aux | grep -E "(uvicorn|mcp_servers|start_web)" | grep -v grep | grep -v shutdown_all)

if [ -z "$REMAINING" ]; then
    echo "✓ All processes successfully stopped!"
else
    echo "⚠ Some processes may still be running:"
    echo "$REMAINING"
fi

echo ""
echo "Port status:"
echo "  Port 6987 (Backend): $(lsof -ti:6987 | wc -l | xargs) process(es)"
echo "  Port 6988 (Frontend): $(lsof -ti:6988 | wc -l | xargs) process(es)"

echo ""
echo "=========================================="
echo "Cleanup complete!"
echo "=========================================="
echo ""
echo "You can now cleanly restart with:"
echo "  ./start_web.sh"
echo ""
