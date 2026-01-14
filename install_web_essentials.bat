@echo off
REM Install essential web dependencies (Windows)

echo ==========================================
echo Installing Essential Dependencies
echo ==========================================

REM Activate virtual environment if not active
if not defined VIRTUAL_ENV (
    if exist "venv" (
        call venv\Scripts\activate.bat
    ) else (
        echo Creating virtual environment...
        python -m venv venv
        call venv\Scripts\activate.bat
    )
)

echo.
echo Installing core dependencies...
python -m pip install --quiet --upgrade pip
pip install --quiet numpy>=1.24.0

echo Installing web backend...
pip install --quiet fastapi>=0.109.0
pip install --quiet "uvicorn[standard]>=0.27.0"
pip install --quiet python-multipart>=0.0.6
pip install --quiet websockets>=12.0

echo Installing AI and security packages...
pip install --quiet anthropic>=0.18.0
pip install --quiet keyring>=24.0.0

echo Installing database packages...
pip install --quiet sqlalchemy>=2.0.0
pip install --quiet psycopg2-binary>=2.9.9
pip install --quiet alembic>=1.13.0

echo Installing reporting and visualization...
pip install --quiet reportlab>=4.0.0
pip install --quiet networkx>=3.0
pip install --quiet pyvis>=0.3.0
pip install --quiet plotly>=5.17.0
pip install --quiet pandas>=2.0.0

echo Installing integration packages...
pip install --quiet requests>=2.31.0
pip install --quiet urllib3>=2.0.0
pip install --quiet boto3>=1.34.0

echo.
echo ==========================================
echo [OK] Python dependencies installed!
echo ==========================================
echo.
echo Installing frontend dependencies...

REM Install frontend dependencies
if exist "frontend" (
    cd frontend
    if not exist "node_modules" (
        echo Installing Node.js packages...
        call npm install
        if %errorlevel% equ 0 (
            echo [OK] Frontend dependencies installed!
        ) else (
            echo Warning: npm install had issues
        )
    ) else (
        echo [OK] Frontend dependencies already installed
    )
    cd ..
) else (
    echo Warning: frontend directory not found
)

echo.
echo ==========================================
echo Installation Complete!
echo ==========================================
echo.
echo Next steps:
echo   1. Start PostgreSQL: start_database.bat
echo   2. Start application: start_web.bat
echo.

