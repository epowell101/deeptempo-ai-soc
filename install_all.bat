@echo off
REM Complete installation script for DeepTempo AI SOC (Windows)
REM This script installs everything: Python deps, frontend, and PostgreSQL

echo ==========================================
echo DeepTempo AI SOC - Complete Installation
echo ==========================================
echo.

REM Check Python
echo Checking prerequisites...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Python is not installed
    echo Please install Python 3.10+ from https://www.python.org/downloads/
    exit /b 1
)
echo [OK] Python found

REM Check Node.js
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Warning: Node.js is not installed
    echo Frontend will not be installed. Install from https://nodejs.org/
    set HAS_NODE=false
) else (
    echo [OK] Node.js found
    set HAS_NODE=true
)

REM Check Docker
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Warning: Docker is not installed
    echo PostgreSQL will not be available. Install from https://www.docker.com/
    set HAS_DOCKER=false
) else (
    echo [OK] Docker found
    set HAS_DOCKER=true
)

echo.
echo ==========================================
echo Step 1: Python Environment
echo ==========================================

REM Create virtual environment
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
    echo [OK] Virtual environment created
) else (
    echo [OK] Virtual environment already exists
)

REM Activate virtual environment
call venv\Scripts\activate.bat

echo.
echo ==========================================
echo Step 2: Python Dependencies
echo ==========================================

echo Installing Python packages...
python -m pip install --upgrade pip
pip install -q sqlalchemy>=2.0.0
pip install -q psycopg2-binary>=2.9.9
pip install -q alembic>=1.13.0
pip install -q fastapi>=0.109.0
pip install -q uvicorn[standard]>=0.27.0
pip install -q anthropic>=0.18.0
pip install -q reportlab>=4.0.0
pip install -q pandas>=2.0.0
pip install -q numpy>=1.24.0
pip install -q requests>=2.31.0
pip install -q python-multipart>=0.0.6

echo [OK] Python dependencies installed

echo.
echo ==========================================
echo Step 3: Frontend Installation
echo ==========================================

if "%HAS_NODE%"=="true" (
    if exist "frontend" (
        cd frontend
        if not exist "node_modules" (
            echo Installing frontend dependencies...
            call npm install
            echo [OK] Frontend dependencies installed
        ) else (
            echo [OK] Frontend dependencies already installed
        )
        cd ..
    ) else (
        echo Warning: frontend directory not found
    )
) else (
    echo Skipping frontend installation (Node.js not available)
)

echo.
echo ==========================================
echo Step 4: PostgreSQL Database
echo ==========================================

if "%HAS_DOCKER%"=="true" (
    if not exist ".env" (
        if exist "env.example" (
            echo Creating .env file...
            copy env.example .env
            echo [OK] Created .env file (please update passwords!)
        )
    )
    
    if exist "start_database.bat" (
        echo Starting PostgreSQL database...
        call start_database.bat
    ) else (
        echo Warning: start_database.bat not found
    )
) else (
    echo Skipping PostgreSQL (Docker not available)
    echo Application will use JSON file storage
)

echo.
echo ==========================================
echo Installation Complete!
echo ==========================================
echo.
echo Installed Components:
echo   [OK] Python environment and dependencies
if "%HAS_NODE%"=="true" echo   [OK] Frontend UI (React + Vite)
if "%HAS_DOCKER%"=="true" echo   [OK] PostgreSQL database
echo.
echo Next Steps:
echo.
echo   1. Review and update passwords in .env file
echo   2. Start the application:
echo      start_web.bat
echo.
echo   3. Access the application:
echo      Frontend: http://localhost:6988
echo      Backend:  http://localhost:6987
echo      API Docs: http://localhost:6987/docs
if "%HAS_DOCKER%"=="true" echo      PgAdmin:  http://localhost:5050 (if started)
echo.
echo Documentation:
echo   - Quick Start: GETTING_STARTED_WITH_POSTGRES.md
echo   - Database:    DATABASE_SETUP.md
echo   - Ingestion:   DATA_INGESTION_GUIDE.md
echo.
echo ==========================================

pause

