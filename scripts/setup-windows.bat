@echo off
echo ============================================
echo JDDB Backend Setup Script for Windows
echo (Optimized version without complex dependencies)
echo ============================================
echo.

cd backend

echo [1/7] Checking Python version...
python --version
if %errorlevel% neq 0 (
    echo ERROR: Python not found. Please install Python 3.9+ from python.org
    pause
    exit /b 1
)

echo [2/7] Creating Python virtual environment...
python -m venv venv
if %errorlevel% neq 0 (
    echo ERROR: Failed to create virtual environment.
    pause
    exit /b 1
)

echo [3/7] Activating virtual environment...
call venv\Scripts\activate.bat

echo [4/7] Upgrading pip...
python -m pip install --upgrade pip

echo [5/7] Installing Windows-optimized Python dependencies...
echo This may take a few minutes...
pip install -r requirements-windows.txt
if %errorlevel% neq 0 (
    echo ERROR: Failed to install dependencies.
    echo.
    echo Trying individual installation of problematic packages...
    pip install fastapi uvicorn pydantic sqlalchemy
    pip install psycopg2-binary asyncpg alembic pgvector
    pip install pandas chardet python-multipart openai
    pip install pydantic-settings structlog python-dotenv
    pip install pytest black flake8 mypy
)

echo [6/7] Setting up environment configuration...
if not exist .env (
    copy .env.example .env
    echo Environment file created. Please edit backend\.env with your settings.
) else (
    echo Environment file already exists.
)

echo [7/7] Testing database connection (optional)...
echo Checking if PostgreSQL is available...
python -c "import psycopg2; print('psycopg2 imported successfully')" 2>nul
if %errorlevel% neq 0 (
    echo WARNING: Database connection test failed.
    echo Make sure PostgreSQL 17 is installed and running.
    echo You can continue and fix this later.
)

echo.
echo ============================================
echo Setup Complete!
echo ============================================
echo.
echo Next steps:
echo 1. Make sure PostgreSQL 17 is installed and running
echo 2. Edit backend\.env with your database settings
echo 3. Run scripts\init-db.bat to initialize the database
echo 4. Run server.bat to start the backend
echo 5. Run frontend.bat to start the frontend
echo.
echo Note: SpaCy was excluded due to Windows compilation issues.
echo The system will work without it for basic functionality.
echo You can install it later if needed for advanced NLP features.
echo.
pause
