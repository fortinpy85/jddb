@echo off
echo ============================================
echo JDDB Quick Start Guide for Windows
echo ============================================
echo.
echo This script will help you get JDDB running on Windows
echo without needing to install 'make' or other Unix tools.
echo.
echo Prerequisites:
echo - Python 3.9+ installed
echo - PostgreSQL 17 installed and running
echo - Node.js 18+ installed
echo.

:menu
echo Choose an option:
echo.
echo 1. Full Setup (first time)
echo 2. Start Backend Server
echo 3. Start Frontend Server  
echo 4. Check Prerequisites
echo 5. Edit Environment Settings
echo 6. View Documentation
echo 7. Exit
echo.
set /p choice="Enter your choice (1-7): "

if "%choice%"=="1" goto setup
if "%choice%"=="2" goto backend
if "%choice%"=="3" goto frontend
if "%choice%"=="4" goto prereq
if "%choice%"=="5" goto config
if "%choice%"=="6" goto docs
if "%choice%"=="7" goto exit

echo Invalid choice. Please try again.
goto menu

:setup
echo.
echo Running full setup...
call setup.bat
pause
goto menu

:backend
echo.
echo Starting backend server...
start "JDDB Backend" cmd /c server.bat
echo Backend server started in new window.
echo Check http://localhost:8000/health to verify it's running.
pause
goto menu

:frontend
echo.
echo Starting frontend server...
start "JDDB Frontend" cmd /c frontend.bat
echo Frontend server started in new window.
echo Check http://localhost:3000 to access the application.
pause
goto menu

:prereq
echo.
echo Checking prerequisites...
echo.

echo Checking Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [✗] Python not found. Install from: https://python.org/downloads/
) else (
    for /f "tokens=2" %%i in ('python --version 2^>^&1') do echo [✓] Python %%i found
)

echo Checking Node.js...
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [✗] Node.js not found. Install from: https://nodejs.org/
) else (
    for /f %%i in ('node --version 2^>^&1') do echo [✓] Node.js %%i found
)

echo Checking PostgreSQL...
"C:\Program Files\PostgreSQL\17\bin\psql.exe" --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [✗] PostgreSQL 17 not found at default location
    echo     Install from: https://www.postgresql.org/download/windows/
) else (
    for /f "tokens=3" %%i in ('"C:\Program Files\PostgreSQL\17\bin\psql.exe" --version 2^>^&1') do echo [✓] PostgreSQL %%i found
)

echo.
pause
goto menu

:config
echo.
echo Opening environment configuration...
if exist backend\.env (
    notepad backend\.env
) else (
    echo Environment file not found. Run setup first.
)
pause
goto menu

:docs
echo.
echo Available documentation:
echo.
echo - README.md - Main project documentation  
echo - docs\DEPLOYMENT.md - Full deployment guide
echo - docs\SETUP.md - Unified setup guide
echo - docs\POSTGRESQL_17_NOTES.md - PostgreSQL 17 configuration
echo.
echo Opening main README...
start README.md
pause
goto menu

:exit
echo.
echo Thanks for using JDDB!
echo.
pause
exit