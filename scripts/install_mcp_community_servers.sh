#!/bin/bash
# Install Community MCP Servers
# This script installs the official community MCP servers for GitHub and PostgreSQL

set -e  # Exit on error

echo ""
echo "========================================="
echo "MCP Community Servers Installation"
echo "========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo -e "${RED}✗ Node.js is not installed${NC}"
    echo "  Please install Node.js from https://nodejs.org/"
    echo "  Recommended: Node.js 18.x or later"
    exit 1
fi

echo -e "${GREEN}✓ Node.js found:${NC} $(node --version)"

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    echo -e "${RED}✗ npm is not installed${NC}"
    exit 1
fi

echo -e "${GREEN}✓ npm found:${NC} $(npm --version)"
echo ""

# Install GitHub MCP Server
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Installing GitHub MCP Server..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
npm install -g @modelcontextprotocol/server-github
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ GitHub MCP Server installed successfully${NC}"
else
    echo -e "${RED}✗ Failed to install GitHub MCP Server${NC}"
    exit 1
fi
echo ""

# Install PostgreSQL MCP Server
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Installing PostgreSQL MCP Server..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
npm install -g @modelcontextprotocol/server-postgres
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ PostgreSQL MCP Server installed successfully${NC}"
else
    echo -e "${RED}✗ Failed to install PostgreSQL MCP Server${NC}"
    exit 1
fi
echo ""

# Summary
echo "========================================="
echo "Installation Complete!"
echo "========================================="
echo ""
echo -e "${GREEN}✓ Installed Servers:${NC}"
echo "  1. @modelcontextprotocol/server-github"
echo "  2. @modelcontextprotocol/server-postgres"
echo ""
echo -e "${YELLOW}Next Steps:${NC}"
echo ""
echo "1. Configure GitHub Access Token:"
echo "   - Create token at: https://github.com/settings/tokens"
echo "   - Required scopes: repo, read:org, read:user"
echo "   - Set environment variable: export GITHUB_TOKEN='ghp_your_token_here'"
echo ""
echo "2. Configure PostgreSQL Connection:"
echo "   - Set environment variable with connection string:"
echo "   - export POSTGRES_URL='postgresql://user:pass@host:5432/db'"
echo ""
echo "3. The servers are already configured in mcp-config.json"
echo ""
echo "4. Restart your MCP client to use the new servers"
echo ""
echo -e "${GREEN}✓ Migration complete!${NC}"
echo ""

# Test installations
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Testing Installations..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check if packages are installed
if npm list -g @modelcontextprotocol/server-github &> /dev/null; then
    echo -e "${GREEN}✓ GitHub MCP Server: Installed${NC}"
else
    echo -e "${YELLOW}⚠ GitHub MCP Server: May not be globally accessible${NC}"
fi

if npm list -g @modelcontextprotocol/server-postgres &> /dev/null; then
    echo -e "${GREEN}✓ PostgreSQL MCP Server: Installed${NC}"
else
    echo -e "${YELLOW}⚠ PostgreSQL MCP Server: May not be globally accessible${NC}"
fi

echo ""
echo "Installation script completed successfully!"

