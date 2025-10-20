@echo off
REM ============================================================
REM JDDB Backend Server Startup Script
REM ============================================================
REM This script starts the FastAPI backend server using Poetry
REM ============================================================

echo.
echo ============================================================
echo  JDDB Backend Server - Starting...
echo ============================================================
echo.

REM Check if Poetry is installed
where poetry >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Poetry is not installed or not in PATH
    echo Please install Poetry: https://python-poetry.org/docs/#installation
    pause
    exit /b 1
)

REM Check if we're in the correct directory
if not exist "backend\pyproject.toml" (
    echo [ERROR] Must run from project root directory
    echo Current directory: %CD%
    pause
    exit /b 1
)

REM Check if port 8000 is available
echo [1/4] Checking port 8000 availability...
netstat -ano | findstr ":8000 " | findstr "LISTENING" >nul 2>&1
if %errorlevel% equ 0 (
    echo [WARNING] Port 8000 is already in use!
    echo.
    echo A server may already be running. Options:
    echo   1. Stop the existing server first
    echo   2. Use 'cleanup.bat' to kill processes on port 8000
    echo.
    pause
    exit /b 1
) else (
    echo [OK] Port 8000 is available
)

REM Check if Poetry dependencies are installed
echo [2/4] Checking Poetry dependencies...
cd backend
poetry show >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARNING] Dependencies not installed. Installing now...
    poetry install --no-root
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to install dependencies
        cd ..
        pause
        exit /b 1
    )
)
echo [OK] Dependencies are installed

REM Check if .env file exists
echo [3/4] Checking environment configuration...
if not exist ".env" (
    echo [ERROR] .env file not found in backend directory
    echo Please create .env file with required configuration
    cd ..
    pause
    exit /b 1
)
echo [OK] Environment configuration found

REM Start the server
echo [4/4] Starting FastAPI server...
echo.
echo ============================================================
echo  Server starting on http://localhost:8000
echo  API Documentation: http://localhost:8000/api/docs
echo  Press Ctrl+C to stop the server
echo ============================================================
echo.

poetry run python scripts/dev_server.py

cd ..
pause
