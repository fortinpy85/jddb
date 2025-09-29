@echo off
echo ============================================
echo JDDB Database Initialization
echo ============================================
echo.

cd ..\backend

echo Activating Python virtual environment...
call venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo ERROR: Virtual environment not found. Run setup-windows.bat first.
    pause
    exit /b 1
)

echo.
echo Checking database configuration...
if not exist .env (
    echo ERROR: Environment file not found.
    echo Please copy .env.example to .env and configure your database settings.
    pause
    exit /b 1
)

echo.
echo Initializing database...
echo This will create tables and set up the schema.
python scripts\init_db.py
if %errorlevel% neq 0 (
    echo.
    echo ERROR: Database initialization failed.
    echo.
    echo Common issues:
    echo 1. PostgreSQL is not running
    echo 2. Database credentials are incorrect in .env file
    echo 3. JDDB database doesn't exist
    echo.
    echo To fix:
    echo 1. Start PostgreSQL service
    echo 2. Create JDDB database: createdb -U postgres JDDB
    echo 3. Update .env with correct credentials
    echo.
    pause
    exit /b 1
)

echo.
echo Creating sample data...
python scripts\sample_data.py
if %errorlevel% neq 0 (
    echo WARNING: Sample data creation failed. This is optional.
    echo The database is initialized but without sample data.
)

echo.
echo ============================================
echo Database initialization complete!
echo ============================================
echo.
echo You can now:
echo 1. Run server.bat to start the backend API
echo 2. Run frontend.bat to start the web interface
echo 3. Visit http://localhost:8000/api/docs for API documentation
echo.
pause
