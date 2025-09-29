@echo off
REM Comprehensive test runner for JDDB application
REM This script runs all test suites: backend, frontend unit, and e2e tests

echo ========================================
echo JDDB Test Suite Runner
echo ========================================

echo.
echo [1/4] Checking test environment...
echo ----------------------------------------

REM Check if backend dependencies are installed
if not exist "backend\venv" (
    echo ERROR: Backend virtual environment not found
    echo Please run: cd backend ^&^& make setup
    exit /b 1
)

REM Check if frontend dependencies are installed
if not exist "node_modules" (
    echo ERROR: Frontend dependencies not installed
    echo Please run: bun install
    exit /b 1
)

echo Environment checks passed!

echo.
echo [2/4] Running Backend Tests...
echo ----------------------------------------
cd backend
call venv\Scripts\activate
python -m pytest tests/ --verbose --tb=short
if %errorlevel% neq 0 (
    echo FAILED: Backend tests failed
    cd ..
    exit /b 1
)
cd ..
echo Backend tests completed successfully!

echo.
echo [3/4] Running Frontend Unit Tests...
echo ----------------------------------------
call bun run test:unit
if %errorlevel% neq 0 (
    echo FAILED: Frontend unit tests failed
    exit /b 1
)
echo Frontend unit tests completed successfully!

echo.
echo [4/4] Running End-to-End Tests...
echo ----------------------------------------
REM Start backend server in background
echo Starting backend server...
start /B cmd /c "cd backend && call venv\Scripts\activate && python -m uvicorn jd_ingestion.main:app --host 0.0.0.0 --port 8000"

REM Wait for server to start
timeout /t 10 /nobreak > nul

REM Run E2E tests
echo Running E2E tests...
call npx playwright test --project chromium
set e2e_result=%errorlevel%

REM Stop background processes
taskkill /f /im python.exe 2>nul
taskkill /f /im uvicorn.exe 2>nul

if %e2e_result% neq 0 (
    echo FAILED: E2E tests failed
    exit /b 1
)
echo E2E tests completed successfully!

echo.
echo ========================================
echo ALL TESTS PASSED! ✓
echo ========================================
echo.
echo Test Summary:
echo - Backend tests: ✓ PASSED
echo - Frontend unit tests: ✓ PASSED
echo - End-to-end tests: ✓ PASSED
echo.
echo View detailed results:
echo - Backend: backend\htmlcov\index.html (if coverage was generated)
echo - Frontend: coverage\index.html (if coverage was generated)
echo - E2E: playwright-report\index.html
echo.
