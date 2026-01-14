@echo off
REM Start PostgreSQL database for DeepTempo AI SOC (Windows)

echo ==========================================
echo DeepTempo AI SOC - Database Startup
echo ==========================================

REM Check if Docker is installed
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Docker is not installed
    echo Please install Docker Desktop from https://www.docker.com/products/docker-desktop/
    exit /b 1
)

REM Load environment variables if .env exists
if exist .env (
    echo [OK] Loading environment variables from .env
    for /f "tokens=1,2 delims==" %%a in (.env) do (
        if not "%%a"=="" if not "%%b"=="" (
            set %%a=%%b
        )
    )
) else (
    echo Warning: .env file not found, using defaults
    echo Copy env.example to .env and customize for your environment
)

REM Start PostgreSQL
echo.
echo Starting PostgreSQL database...
docker-compose up -d postgres

REM Wait for PostgreSQL to be ready
echo.
echo Waiting for PostgreSQL to be ready...
set /a counter=0
:wait_loop
docker exec deeptempo-postgres pg_isready -U deeptempo -d deeptempo_soc >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] PostgreSQL is ready!
    goto :ready
)
set /a counter+=1
if %counter% geq 30 (
    echo Error: PostgreSQL failed to start within 30 seconds
    echo Check logs with: docker-compose logs postgres
    exit /b 1
)
timeout /t 1 /nobreak >nul
goto :wait_loop

:ready

REM Initialize database tables
echo.
echo Initializing database tables...
python -c "from database.connection import init_database; init_database(create_tables=True); print('[OK] Database tables created')" 2>nul
if %errorlevel% neq 0 (
    echo Warning: Could not initialize database tables
    echo You may need to run the migration script manually:
    echo   python database\migrate_json_to_db.py
)

REM Show status
echo.
echo ==========================================
echo Database Status
echo ==========================================
docker-compose ps

echo.
echo ==========================================
echo [OK] Database startup complete!
echo ==========================================
echo.
echo PostgreSQL is running at: localhost:5432
echo Database name: deeptempo_soc
echo.
echo Useful commands:
echo   - View logs:     docker-compose logs -f postgres
echo   - Stop database: docker-compose stop postgres
echo   - Connect to DB: docker exec -it deeptempo-postgres psql -U deeptempo -d deeptempo_soc
echo.
echo To migrate JSON data to PostgreSQL:
echo   python database\migrate_json_to_db.py
echo.

pause

