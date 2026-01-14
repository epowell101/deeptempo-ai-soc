#!/bin/bash
# Complete installation script for DeepTempo AI SOC
# This script installs everything: Python deps, frontend, and PostgreSQL

set -e  # Exit on error

echo "=========================================="
echo "DeepTempo AI SOC - Complete Installation"
echo "=========================================="
echo ""

# Check prerequisites
echo "Checking prerequisites..."

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 is not installed"
    echo "Please install Python 3.10+ from https://www.python.org/downloads/"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
echo "✓ Python $PYTHON_VERSION found"

# Check Node.js
if ! command -v node &> /dev/null; then
    echo "⚠ Warning: Node.js is not installed"
    echo "Frontend will not be installed. Install Node.js from https://nodejs.org/"
    HAS_NODE=false
else
    NODE_VERSION=$(node --version)
    echo "✓ Node.js $NODE_VERSION found"
    HAS_NODE=true
fi

# Check npm
if ! command -v npm &> /dev/null; then
    echo "⚠ Warning: npm is not installed"
    HAS_NPM=false
else
    NPM_VERSION=$(npm --version)
    echo "✓ npm $NPM_VERSION found"
    HAS_NPM=true
fi

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "⚠ Warning: Docker is not installed"
    echo "PostgreSQL database will not be available. Install Docker from https://www.docker.com/"
    HAS_DOCKER=false
else
    echo "✓ Docker found"
    HAS_DOCKER=true
fi

echo ""
echo "=========================================="
echo "Step 1: Python Environment"
echo "=========================================="

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi

# Activate virtual environment
source venv/bin/activate

echo ""
echo "=========================================="
echo "Step 2: Python Dependencies"
echo "=========================================="

# Install Python dependencies
if [ -f "install_web_essentials.sh" ]; then
    chmod +x install_web_essentials.sh
    ./install_web_essentials.sh
else
    echo "Installing from requirements_web.txt..."
    pip install --upgrade pip
    pip install -r requirements_web.txt
fi

echo ""
echo "=========================================="
echo "Step 3: Frontend Installation"
echo "=========================================="

if [ "$HAS_NODE" = true ] && [ "$HAS_NPM" = true ]; then
    if [ -d "frontend" ]; then
        cd frontend
        if [ ! -d "node_modules" ]; then
            echo "Installing frontend dependencies..."
            npm install
            echo "✓ Frontend dependencies installed"
        else
            echo "✓ Frontend dependencies already installed"
        fi
        cd ..
    else
        echo "⚠ Warning: frontend directory not found"
    fi
else
    echo "⚠ Skipping frontend installation (Node.js/npm not available)"
fi

echo ""
echo "=========================================="
echo "Step 4: PostgreSQL Database"
echo "=========================================="

if [ "$HAS_DOCKER" = true ]; then
    # Copy environment file if it doesn't exist
    if [ ! -f ".env" ]; then
        if [ -f "env.example" ]; then
            echo "Creating .env file from env.example..."
            cp env.example .env
            echo "✓ Created .env file (please review and update passwords!)"
        fi
    fi
    
    # Start PostgreSQL
    if [ -f "start_database.sh" ]; then
        chmod +x start_database.sh
        echo "Starting PostgreSQL database..."
        ./start_database.sh
    else
        echo "⚠ start_database.sh not found, skipping database startup"
    fi
else
    echo "⚠ Skipping PostgreSQL installation (Docker not available)"
    echo "Application will use JSON file storage instead"
fi

echo ""
echo "=========================================="
echo "Step 5: Data Migration (Optional)"
echo "=========================================="

if [ -f "data/findings.json" ] && [ "$HAS_DOCKER" = true ]; then
    echo ""
    read -p "Migrate existing JSON data to PostgreSQL? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        if [ -f "database/migrate_json_to_db.py" ]; then
            python database/migrate_json_to_db.py
        else
            echo "⚠ Migration script not found"
        fi
    else
        echo "Skipping data migration"
    fi
else
    echo "No existing data to migrate or PostgreSQL not available"
fi

echo ""
echo "=========================================="
echo "Installation Complete!"
echo "=========================================="
echo ""
echo "📦 Installed Components:"
echo "  ✓ Python environment and dependencies"
if [ "$HAS_NODE" = true ] && [ "$HAS_NPM" = true ]; then
    echo "  ✓ Frontend UI (React + Vite)"
fi
if [ "$HAS_DOCKER" = true ]; then
    echo "  ✓ PostgreSQL database"
fi
echo ""
echo "🚀 Next Steps:"
echo ""
echo "  1. Review and update passwords in .env file"
echo "  2. Start the application:"
echo "     ./start_web.sh"
echo ""
echo "  3. Access the application:"
echo "     Frontend: http://localhost:6988"
echo "     Backend:  http://localhost:6987"
echo "     API Docs: http://localhost:6987/docs"
if [ "$HAS_DOCKER" = true ]; then
    echo "     PgAdmin:  http://localhost:5050 (if started)"
fi
echo ""
echo "📚 Documentation:"
echo "  - Quick Start: GETTING_STARTED_WITH_POSTGRES.md"
echo "  - Database:    DATABASE_SETUP.md"
echo "  - Ingestion:   DATA_INGESTION_GUIDE.md"
echo ""
echo "=========================================="

