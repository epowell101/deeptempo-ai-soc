#!/bin/bash
# DeepTempo AI SOC - Installation Script
# This script sets up the environment and installs all dependencies

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}DeepTempo AI SOC - Installation${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check Python version
echo -e "${YELLOW}Checking Python version...${NC}"
PYTHON_CMD=""
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_VERSION=$(python --version 2>&1 | awk '{print $2}')
    PYTHON_CMD="python"
else
    echo -e "${RED}Error: Python 3.10+ is required but not found.${NC}"
    echo "Please install Python 3.10 or higher from https://www.python.org/"
    exit 1
fi

# Extract major and minor version
MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

if [ "$MAJOR" -lt 3 ] || ([ "$MAJOR" -eq 3 ] && [ "$MINOR" -lt 10 ]); then
    echo -e "${RED}Error: Python 3.10+ is required. Found: $PYTHON_VERSION${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Python $PYTHON_VERSION found${NC}"
echo ""

# Check if virtual environment exists
if [ -d "venv" ]; then
    echo -e "${YELLOW}Virtual environment already exists.${NC}"
    read -p "Do you want to recreate it? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}Removing existing virtual environment...${NC}"
        rm -rf venv
    else
        echo -e "${GREEN}Using existing virtual environment${NC}"
        SKIP_VENV=true
    fi
fi

# Create virtual environment
if [ -z "$SKIP_VENV" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    $PYTHON_CMD -m venv venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
    echo ""
fi

# Determine activation script
if [ -f "venv/bin/activate" ]; then
    ACTIVATE_SCRIPT="venv/bin/activate"
    PIP_CMD="venv/bin/pip"
    PYTHON_VENV="venv/bin/python"
elif [ -f "venv/Scripts/activate" ]; then
    ACTIVATE_SCRIPT="venv/Scripts/activate"
    PIP_CMD="venv/Scripts/pip"
    PYTHON_VENV="venv/Scripts/python"
else
    echo -e "${RED}Error: Could not find virtual environment activation script${NC}"
    exit 1
fi

# Activate virtual environment
echo -e "${YELLOW}Activating virtual environment...${NC}"
source "$ACTIVATE_SCRIPT"

# Upgrade pip
echo -e "${YELLOW}Upgrading pip...${NC}"
$PIP_CMD install --upgrade pip --quiet
echo -e "${GREEN}✓ pip upgraded${NC}"
echo ""

# Install requirements
echo -e "${YELLOW}Installing dependencies from requirements.txt...${NC}"
if [ -f "requirements.txt" ]; then
    $PIP_CMD install -r requirements.txt
    echo -e "${GREEN}✓ Dependencies installed${NC}"
else
    echo -e "${RED}Warning: requirements.txt not found${NC}"
fi
echo ""

# Install MCP SDK
echo -e "${YELLOW}Installing MCP SDK...${NC}"
$PIP_CMD install "mcp[cli]" --quiet
echo -e "${GREEN}✓ MCP SDK installed${NC}"
echo ""

# Install reportlab for PDF generation
echo -e "${YELLOW}Installing reportlab (PDF generation)...${NC}"
$PIP_CMD install reportlab --quiet
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ reportlab installed${NC}"
else
    echo -e "${YELLOW}Warning: Failed to install reportlab${NC}"
fi
echo ""

# Create data directory if it doesn't exist
if [ ! -d "data" ]; then
    echo -e "${YELLOW}Creating data directory...${NC}"
    mkdir -p data
    echo -e "${GREEN}✓ Data directory created${NC}"
    echo ""
fi

# Ask about generating sample data
echo -e "${YELLOW}Sample Data Generation${NC}"
read -p "Do you want to generate sample data? (Y/n): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Nn]$ ]]; then
    echo -e "${YELLOW}Generating sample data...${NC}"
    if [ -f "scripts/demo.py" ]; then
        $PYTHON_VENV -m scripts.demo
        echo -e "${GREEN}✓ Sample data generated${NC}"
    else
        echo -e "${YELLOW}Warning: scripts/demo.py not found, skipping sample data generation${NC}"
    fi
    echo ""
fi

# Make main.py executable
chmod +x main.py 2>/dev/null || true

# Summary
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}Installation Complete!${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "To run the application:"
echo -e "  ${YELLOW}source venv/bin/activate${NC}  (or ${YELLOW}venv\\Scripts\\activate${NC} on Windows)"
echo -e "  ${YELLOW}python main.py${NC}"
echo ""
echo -e "Or use the setup wizard from within the application:"
echo -e "  ${YELLOW}python main.py${NC}"
echo ""
echo -e "To configure Claude Desktop integration:"
echo -e "  1. Run the application"
echo -e "  2. Go to File > Configure Claude Desktop..."
echo -e "  3. Follow the configuration wizard"
echo ""
echo -e "${GREEN}Happy investigating!${NC}"

