#!/bin/bash
# Start DeepTempo AI SOC Web Application

echo "=========================================="
echo "DeepTempo AI SOC - Startup"
echo "=========================================="

# Check if venv exists
if [ ! -d "venv" ]; then
    echo "Virtual environment not found. Creating..."
    python3 -m venv venv
fi

# Activate venv
source venv/bin/activate

# Install/update dependencies
echo ""
echo "Checking Python dependencies..."
if [ -f "install_web_essentials.sh" ]; then
    echo "Installing essential dependencies only..."
    ./install_web_essentials.sh
else
    echo "Installing from requirements_web.txt (may have issues with optional packages)..."
    pip install -r requirements_web.txt || echo "Warning: Some optional packages failed to install. Core functionality should still work."
fi

# Check and start PostgreSQL database
echo ""
echo "Checking PostgreSQL database..."
if command -v docker &> /dev/null; then
    # Check if PostgreSQL container is running
    if docker ps --format '{{.Names}}' | grep -q "deeptempo-postgres"; then
        echo "✓ PostgreSQL is already running"
    else
        echo "Starting PostgreSQL database..."
        if [ -f "start_database.sh" ]; then
            ./start_database.sh
        else
            echo "⚠ start_database.sh not found. Starting with docker-compose..."
            if [ -f "docker-compose.yml" ]; then
                docker-compose up -d postgres
                echo "Waiting for PostgreSQL to be ready..."
                for i in {1..30}; do
                    if docker exec deeptempo-postgres pg_isready -U deeptempo -d deeptempo_soc &> /dev/null; then
                        echo "✓ PostgreSQL is ready!"
                        break
                    fi
                    if [ $i -eq 30 ]; then
                        echo "⚠ Warning: PostgreSQL may not be ready. Application will use JSON fallback."
                    fi
                    sleep 1
                done
            else
                echo "⚠ docker-compose.yml not found. Skipping PostgreSQL. Application will use JSON files."
            fi
        fi
    fi
else
    echo "⚠ Docker not found. PostgreSQL disabled. Application will use JSON files."
fi

# Check and install frontend dependencies
echo ""
echo "Checking frontend dependencies..."
if [ -d "frontend" ]; then
    if [ ! -d "frontend/node_modules" ]; then
        echo "Installing frontend dependencies (this may take a few minutes)..."
        cd frontend
        npm install
        cd ..
        echo "✓ Frontend dependencies installed"
    else
        echo "✓ Frontend dependencies already installed"
    fi
else
    echo "⚠ Warning: frontend directory not found"
fi

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "Shutting down servers..."
    
    # Kill backend and frontend processes
    if [ ! -z "$BACKEND_PID" ]; then
        echo "Stopping backend server (PID: $BACKEND_PID)..."
        kill $BACKEND_PID 2>/dev/null
        wait $BACKEND_PID 2>/dev/null
    fi
    
    if [ ! -z "$FRONTEND_PID" ]; then
        echo "Stopping frontend server (PID: $FRONTEND_PID)..."
        kill $FRONTEND_PID 2>/dev/null
        wait $FRONTEND_PID 2>/dev/null
    fi
    
    # Kill any remaining uvicorn or npm processes for this project
    pkill -f "uvicorn main:app" 2>/dev/null
    pkill -f "vite.*deeptempo" 2>/dev/null
    
    echo ""
    echo "All servers stopped"
    echo ""
    echo "Note: PostgreSQL database is still running in Docker."
    echo "To stop it, run: ./stop_database.sh"
    echo "Or: docker-compose stop postgres"
    exit 0
}

# Trap signals for cleanup
trap cleanup INT TERM EXIT

# Start backend API server in background
echo "Starting backend API server..."
export PYTHONPATH="${PWD}:${PYTHONPATH}"
cd backend
uvicorn main:app --host 127.0.0.1 --port 6987 --reload &
BACKEND_PID=$!
cd ..

# Wait for backend to start
sleep 3

# Start frontend dev server if in development
if [ -d "frontend/node_modules" ]; then
    echo "Starting frontend dev server..."
    cd frontend
    npm run dev &
    FRONTEND_PID=$!
    cd ..
else
    echo "Frontend dependencies not installed. Run: cd frontend && npm install"
    FRONTEND_PID=""
fi

echo ""
echo "=========================================="
echo "DeepTempo AI SOC - Ready!"
echo "=========================================="
echo "Backend API:   http://localhost:6987"
echo "Frontend UI:   http://localhost:6988"
echo "API Docs:      http://localhost:6987/docs"
if docker ps --format '{{.Names}}' | grep -q "deeptempo-postgres" 2>/dev/null; then
    echo "PostgreSQL:    Running (port 5432)"
    echo "PgAdmin:       http://localhost:5050 (if started)"
fi
echo ""
echo "Press Ctrl+C to stop application servers"
echo "=========================================="

# Wait for processes
wait

