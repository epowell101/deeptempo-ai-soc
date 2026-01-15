#!/bin/bash
# Install essential web dependencies only (avoiding problematic packages)

echo "=========================================="
echo "Installing Essential Dependencies"
echo "=========================================="

# Activate virtual environment if not already active
if [ -z "$VIRTUAL_ENV" ]; then
    if [ -d "venv" ]; then
        source venv/bin/activate
    else
        echo "Creating virtual environment..."
        python3 -m venv venv
        source venv/bin/activate
    fi
fi

echo ""
echo "Installing core dependencies..."
# Core dependencies
pip install -q --upgrade pip
pip install -q "numpy>=1.24.0"

echo "Installing web backend..."
# Web Backend (FastAPI)
pip install -q "fastapi>=0.109.0"
pip install -q "uvicorn[standard]>=0.27.0"
pip install -q "python-multipart>=0.0.6"
pip install -q "websockets>=12.0"

echo "Installing AI and security packages..."
# Claude API
pip install -q "anthropic>=0.18.0"

# Security and Authentication
pip install -q "keyring>=24.0.0"

echo "Installing database packages..."
# Database (PostgreSQL)
pip install -q "sqlalchemy>=2.0.0"
pip install -q "psycopg2-binary>=2.9.9"
pip install -q "alembic>=1.13.0"

echo "Installing reporting and visualization..."
# PDF Reports
pip install -q "reportlab>=4.0.0"

# Visualization dependencies
pip install -q "networkx>=3.0"
pip install -q "pyvis>=0.3.0"
pip install -q "plotly>=5.17.0"
pip install -q "pandas>=2.0.0"

echo "Installing integration packages..."
# Timesketch integration
pip install -q "requests>=2.31.0"

# Splunk integration
pip install -q "urllib3>=2.0.0"

# AWS S3 integration
pip install -q "boto3>=1.34.0"

echo ""
echo "=========================================="
echo "✅ Python dependencies installed!"
echo "=========================================="
echo ""
echo "Installing frontend dependencies..."

# Install frontend dependencies
if [ -d "frontend" ]; then
    cd frontend
    if [ ! -d "node_modules" ]; then
        echo "Installing Node.js packages (this may take a few minutes)..."
        npm install
        if [ $? -eq 0 ]; then
            echo "✅ Frontend dependencies installed!"
        else
            echo "⚠ Warning: npm install had issues. Frontend may not work."
        fi
    else
        echo "✅ Frontend dependencies already installed"
    fi
    cd ..
else
    echo "⚠ Warning: frontend directory not found"
fi

echo ""
echo "=========================================="
echo "Installation Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "  1. Start PostgreSQL: ./start_database.sh"
echo "  2. Start application: ./start_web.sh"
echo ""
echo "Optional integrations are commented out in requirements_web.txt"
echo "Install them individually as needed with: pip install <package>"
echo ""

