@echo off
REM ============================================================
REM JDDB Process Cleanup Utility
REM ============================================================
REM This script helps clean up orphaned processes on ports
REM 8000 (backend) and 3006 (frontend)
REM ============================================================

echo.
echo ============================================================
echo  JDDB Process Cleanup Utility
echo ============================================================
echo.

REM Check for admin privileges
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARNING] This script works best with administrator privileges
    echo Some processes may not be killable without admin rights
    echo.
)

echo Scanning for processes on JDDB ports...
echo.

REM Check port 8000 (Backend)
echo [Backend - Port 8000]
set BACKEND_FOUND=0
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8000 " ^| findstr "LISTENING"') do (
    set BACKEND_FOUND=1
    echo Found process with PID: %%a
    set BACKEND_PID=%%a
)

if %BACKEND_FOUND% equ 0 (
    echo No process found on port 8000
)
echo.

REM Check port 3006 (Frontend)
echo [Frontend - Port 3006]
set FRONTEND_FOUND=0
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":3006 " ^| findstr "LISTENING"') do (
    set FRONTEND_FOUND=1
    echo Found process with PID: %%a
    set FRONTEND_PID=%%a
)

if %FRONTEND_FOUND% equ 0 (
    echo No process found on port 3006
)
echo.

REM If no processes found, exit
if %BACKEND_FOUND% equ 0 if %FRONTEND_FOUND% equ 0 (
    echo ============================================================
    echo  No processes found on JDDB ports
    echo  Ports 8000 and 3006 are available
    echo ============================================================
    echo.
    pause
    exit /b 0
)

REM Confirm before killing processes
echo ============================================================
echo  WARNING: This will terminate the processes listed above
echo ============================================================
echo.
choice /C YN /M "Do you want to kill these processes"
if errorlevel 2 (
    echo Operation cancelled by user
    pause
    exit /b 0
)

echo.
echo Terminating processes...
echo.

REM Kill backend process
if %BACKEND_FOUND% equ 1 (
    echo Killing backend process (PID: %BACKEND_PID%)...
    taskkill /F /PID %BACKEND_PID% >nul 2>&1
    if %errorlevel% equ 0 (
        echo [OK] Backend process terminated
    ) else (
        echo [ERROR] Failed to kill backend process (may need admin rights)
    )
)

REM Kill frontend process
if %FRONTEND_FOUND% equ 1 (
    echo Killing frontend process (PID: %FRONTEND_PID%)...
    taskkill /F /PID %FRONTEND_PID% >nul 2>&1
    if %errorlevel% equ 0 (
        echo [OK] Frontend process terminated
    ) else (
        echo [ERROR] Failed to kill frontend process (may need admin rights)
    )
)

echo.
echo ============================================================
echo  Cleanup complete
echo ============================================================
echo.

REM Verify ports are now free
timeout /t 2 /nobreak >nul
echo Verifying ports are now available...
echo.

netstat -ano | findstr ":8000 " | findstr "LISTENING" >nul 2>&1
if %errorlevel% equ 0 (
    echo [WARNING] Port 8000 still in use
) else (
    echo [OK] Port 8000 is now available
)

netstat -ano | findstr ":3006 " | findstr "LISTENING" >nul 2>&1
if %errorlevel% equ 0 (
    echo [WARNING] Port 3006 still in use
) else (
    echo [OK] Port 3006 is now available
)

echo.
pause
