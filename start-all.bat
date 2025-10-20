@echo off
REM ============================================================
REM JDDB Full Stack Startup Script
REM ============================================================
REM This script starts both backend and frontend services
REM in separate windows for easy monitoring
REM ============================================================

echo.
echo ============================================================
echo  JDDB Full Stack Application
echo  Starting Backend and Frontend Services
echo ============================================================
echo.

REM Check if we're in the correct directory
if not exist "backend\pyproject.toml" (
    echo [ERROR] Must run from project root directory
    echo Current directory: %CD%
    pause
    exit /b 1
)

if not exist "package.json" (
    echo [ERROR] Must run from project root directory
    echo Current directory: %CD%
    pause
    exit /b 1
)

REM Check prerequisites
echo [1/3] Checking prerequisites...

REM Check Poetry
where poetry >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Poetry not found. Please install: https://python-poetry.org/
    pause
    exit /b 1
)

REM Check Node.js
where node >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Node.js not found. Please install: https://nodejs.org/
    pause
    exit /b 1
)

echo [OK] All prerequisites installed

REM Check port availability
echo [2/3] Checking port availability...

netstat -ano | findstr ":8000 " | findstr "LISTENING" >nul 2>&1
set BACKEND_PORT_STATUS=%errorlevel%

if "%BACKEND_PORT_STATUS%"=="0" (
    echo [WARNING] Port 8000 ^(backend^) already in use!
    echo.
    choice /C YN /M "Do you want to continue anyway"
    if errorlevel 2 exit /b 1
)

if not "%BACKEND_PORT_STATUS%"=="0" (
    echo [OK] Port 8000 available for backend
)

netstat -ano | findstr ":3006 " | findstr "LISTENING" >nul 2>&1
set FRONTEND_PORT_STATUS=%errorlevel%

if "%FRONTEND_PORT_STATUS%"=="0" (
    echo [INFO] Port 3006 ^(frontend^) in use, Vite will use next available port
)

REM Start services
echo [3/3] Starting services...
echo.

echo ============================================================
echo  Starting Backend Server (port 8000)...
echo ============================================================
start "JDDB Backend Server" cmd /k "server.bat"

REM Wait a moment for backend to initialize
echo Waiting 3 seconds for backend to initialize...
timeout /t 3 /nobreak >nul

echo.
echo ============================================================
echo  Starting Frontend Server (port 3006)...
echo ============================================================
start "JDDB Frontend Server" cmd /k "frontend.bat"

echo.
echo ============================================================
echo  Both services are starting in separate windows
echo ============================================================
echo.
echo  Backend:  http://localhost:8000
echo  API Docs: http://localhost:8000/api/docs
echo  Frontend: http://localhost:3006 (or next available port)
echo.
echo  To stop services: Close the respective command windows
echo  or press Ctrl+C in each window
echo.
echo ============================================================
echo.

pause
