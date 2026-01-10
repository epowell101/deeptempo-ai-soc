@echo off
REM DeepTempo AI SOC - Installation Script for Windows
REM This script sets up the environment and installs all dependencies

setlocal enabledelayedexpansion

echo ========================================
echo DeepTempo AI SOC - Installation
echo ========================================
echo.

REM Check Python version
echo Checking Python version...
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python 3.10+ is required but not found.
    echo Please install Python 3.10 or higher from https://www.python.org/
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo Python %PYTHON_VERSION% found
echo.

REM Check if virtual environment exists
if exist "venv" (
    echo Virtual environment already exists.
    set /p RECREATE="Do you want to recreate it? (y/N): "
    if /i "!RECREATE!"=="y" (
        echo Removing existing virtual environment...
        rmdir /s /q venv
    ) else (
        echo Using existing virtual environment
        set SKIP_VENV=1
    )
)

REM Create virtual environment
if not defined SKIP_VENV (
    echo Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo Error: Failed to create virtual environment
        pause
        exit /b 1
    )
    echo Virtual environment created
    echo.
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip --quiet
if errorlevel 1 (
    echo Warning: Failed to upgrade pip
) else (
    echo pip upgraded
)
echo.

REM Install requirements
echo Installing dependencies from requirements.txt...
if exist "requirements.txt" (
    python -m pip install -r requirements.txt
    if errorlevel 1 (
        echo Error: Failed to install dependencies
        pause
        exit /b 1
    )
    echo Dependencies installed
) else (
    echo Warning: requirements.txt not found
)
echo.

REM Install MCP SDK
echo Installing MCP SDK...
python -m pip install "mcp[cli]" --quiet
if errorlevel 1 (
    echo Warning: Failed to install MCP SDK
) else (
    echo MCP SDK installed
)
echo.

REM Install reportlab for PDF generation
echo Installing reportlab (PDF generation)...
python -m pip install reportlab --quiet
if errorlevel 1 (
    echo Warning: Failed to install reportlab
) else (
    echo reportlab installed
)
echo.

REM Create data directory if it doesn't exist
if not exist "data" (
    echo Creating data directory...
    mkdir data
    echo Data directory created
    echo.
)

REM Ask about generating sample data
echo Sample Data Generation
set /p GENERATE_DATA="Do you want to generate sample data? (Y/n): "
if /i not "!GENERATE_DATA!"=="n" (
    echo Generating sample data...
    if exist "scripts\demo.py" (
        python -m scripts.demo
        if errorlevel 1 (
            echo Warning: Sample data generation had issues
        ) else (
            echo Sample data generated
        )
    ) else (
        echo Warning: scripts\demo.py not found, skipping sample data generation
    )
    echo.
)

REM Summary
echo ========================================
echo Installation Complete!
echo ========================================
echo.
echo To run the application:
echo   venv\Scripts\activate
echo   python main.py
echo.
echo Or use the setup wizard from within the application:
echo   python main.py
echo.
echo To configure Claude Desktop integration:
echo   1. Run the application
echo   2. Go to File ^> Configure Claude Desktop...
echo   3. Follow the configuration wizard
echo.
echo Happy investigating!
echo.
pause

