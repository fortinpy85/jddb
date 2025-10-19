@echo off
REM ============================================================
REM JDDB Frontend Startup Script
REM ============================================================
REM This script starts the Vite development server
REM ============================================================

echo.
echo ============================================================
echo  JDDB Frontend - Starting...
echo ============================================================
echo.

REM Check if Node.js is installed
where node >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Node.js is not installed or not in PATH
    echo Please install Node.js: https://nodejs.org/
    pause
    exit /b 1
)

REM Check if npm is installed
where npm >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] npm is not installed or not in PATH
    echo Please install Node.js which includes npm: https://nodejs.org/
    pause
    exit /b 1
)

REM Check if package.json exists
if not exist "package.json" (
    echo [ERROR] Must run from project root directory
    echo Current directory: %CD%
    pause
    exit /b 1
)

REM Check if node_modules exists
echo [1/4] Checking npm dependencies...
if not exist "node_modules" (
    echo [WARNING] Dependencies not installed. Installing now...
    call npm install
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to install dependencies
        pause
        exit /b 1
    )
)
echo [OK] Dependencies are installed

REM Check if .env.local exists
echo [2/4] Checking environment configuration...
if not exist ".env.local" (
    echo [WARNING] .env.local not found. Creating default configuration...
    echo NEXT_PUBLIC_API_URL=http://localhost:8000/api > .env.local
    echo [OK] Created .env.local with default API URL
) else (
    echo [OK] Environment configuration found
)

REM Check if port 3006 is available (default port from docs)
echo [3/4] Checking port 3006 availability...
netstat -ano | findstr ":3006 " | findstr "LISTENING" >nul 2>&1
if %errorlevel% equ 0 (
    echo [WARNING] Port 3006 is already in use!
    echo Vite will automatically try the next available port (3007, 3008, etc.)
    echo.
)

REM Start the frontend
echo [4/4] Starting Vite development server...
echo.
echo ============================================================
echo  Frontend starting on http://localhost:3006 (or next available port)
echo  Vite will open the browser automatically
echo  Press Ctrl+C to stop the server
echo ============================================================
echo.

call npm run dev

pause
