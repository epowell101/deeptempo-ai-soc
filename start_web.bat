@echo off
REM Start DeepTempo AI SOC Web Application (Windows)

echo ==========================================
echo DeepTempo AI SOC - Startup
echo ==========================================

REM Check if venv exists
if not exist "venv" (
    echo Virtual environment not found. Creating...
    python -m venv venv
)

REM Activate venv
call venv\Scripts\activate.bat

REM Install/update dependencies
echo.
echo Checking Python dependencies...
if exist "install_web_essentials.bat" (
    echo Installing essential dependencies...
    call install_web_essentials.bat
) else (
    echo Installing from requirements_web.txt...
    pip install -r requirements_web.txt
)

REM Check and start PostgreSQL
echo.
echo Checking PostgreSQL database...
docker ps --format "{{.Names}}" 2>nul | findstr /C:"deeptempo-postgres" >nul
if %errorlevel% equ 0 (
    echo [OK] PostgreSQL is already running
) else (
    echo Starting PostgreSQL database...
    if exist "start_database.bat" (
        call start_database.bat
    ) else (
        echo Warning: start_database.bat not found
        if exist "docker-compose.yml" (
            docker-compose up -d postgres
            timeout /t 5 /nobreak >nul
        )
    )
)

REM Check and install frontend dependencies
echo.
echo Checking frontend dependencies...
if exist "frontend" (
    if not exist "frontend\node_modules" (
        echo Installing frontend dependencies...
        cd frontend
        call npm install
        cd ..
        echo [OK] Frontend dependencies installed
    ) else (
        echo [OK] Frontend dependencies already installed
    )
)

echo.
echo Starting backend API server...
start "Backend API" cmd /k "cd backend && uvicorn main:app --host 127.0.0.1 --port 6987 --reload"

REM Wait for backend to start
timeout /t 3 /nobreak >nul

REM Start frontend dev server
if exist "frontend\node_modules" (
    echo Starting frontend dev server...
    start "Frontend UI" cmd /k "cd frontend && npm run dev"
) else (
    echo Warning: Frontend dependencies not installed
)

echo.
echo ==========================================
echo DeepTempo AI SOC - Ready!
echo ==========================================
echo Backend API:   http://localhost:6987
echo Frontend UI:   http://localhost:6988
echo API Docs:      http://localhost:6987/docs
docker ps --format "{{.Names}}" 2>nul | findstr /C:"deeptempo-postgres" >nul
if %errorlevel% equ 0 (
    echo PostgreSQL:    Running (port 5432)
    echo PgAdmin:       http://localhost:5050 (if started)
)
echo.
echo Press any key to stop all servers...
echo ==========================================

pause >nul

REM Cleanup
echo.
echo Shutting down servers...
taskkill /FI "WindowTitle eq Backend API*" /T /F >nul 2>&1
taskkill /FI "WindowTitle eq Frontend UI*" /T /F >nul 2>&1
echo All servers stopped
echo.
echo Note: PostgreSQL is still running in Docker
echo To stop it: docker-compose stop postgres
