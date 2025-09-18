@echo off
echo ============================================
echo JDDB Environment Configuration Helper
echo ============================================
echo.

cd backend

if not exist .env.example (
    echo ERROR: .env.example file not found.
    echo Please make sure you're in the correct directory.
    pause
    exit /b 1
)

echo This script will help you configure your environment settings.
echo.

if exist .env (
    echo Existing .env file found.
    set /p overwrite="Do you want to overwrite it? (y/N): "
    if /i not "%overwrite%"=="y" (
        echo Opening existing .env file for editing...
        notepad .env
        goto :end
    )
)

echo Creating new .env file from template...
copy .env.example .env >nul

echo.
echo ============================================
echo Environment Configuration
echo ============================================
echo.
echo Please provide the following information:
echo.

REM PostgreSQL Configuration
echo [1/4] PostgreSQL Database Configuration
echo.
set /p db_host="PostgreSQL host (default: localhost): "
if "%db_host%"=="" set db_host=localhost

set /p db_port="PostgreSQL port (default: 5432): "
if "%db_port%"=="" set db_port=5432

set /p db_user="PostgreSQL username (default: postgres): "
if "%db_user%"=="" set db_user=postgres

set /p db_password="PostgreSQL password: "
if "%db_password%"=="" (
    echo ERROR: PostgreSQL password is required.
    pause
    exit /b 1
)

set /p db_name="Database name (default: JDDB): "
if "%db_name%"=="" set db_name=JDDB

REM OpenAI Configuration
echo.
echo [2/4] OpenAI Configuration (Optional)
echo.
echo OpenAI API key is needed for future AI features like semantic search.
echo You can leave this blank for now and add it later.
echo.
set /p openai_key="OpenAI API key (optional): "
if "%openai_key%"=="" set openai_key=sk-your-openai-api-key-here

REM Data Directory
echo.
echo [3/4] Data Directory Configuration
echo.
set /p data_dir="Data directory (default: C:\JDDB\data): "
if "%data_dir%"=="" set data_dir=C:/JDDB/data

REM Debug Mode
echo.
echo [4/4] Debug Mode
echo.
set /p debug_mode="Enable debug mode for development? (Y/n): "
if /i "%debug_mode%"=="n" (
    set debug_setting=False
    set log_level=WARNING
) else (
    set debug_setting=True
    set log_level=INFO
)

echo.
echo ============================================
echo Updating .env file...
echo ============================================

REM Use PowerShell to update the .env file since batch is limited for string replacement
powershell -Command "(Get-Content .env) | ForEach-Object { $_ -replace 'DATABASE_URL=.*', 'DATABASE_URL=postgresql+asyncpg://%db_user%:%db_password%@%db_host%:%db_port%/%db_name%' } | Set-Content .env"

powershell -Command "(Get-Content .env) | ForEach-Object { $_ -replace 'DATABASE_SYNC_URL=.*', 'DATABASE_SYNC_URL=postgresql://%db_user%:%db_password%@%db_host%:%db_port%/%db_name%' } | Set-Content .env"

powershell -Command "(Get-Content .env) | ForEach-Object { $_ -replace 'OPENAI_API_KEY=.*', 'OPENAI_API_KEY=%openai_key%' } | Set-Content .env"

powershell -Command "(Get-Content .env) | ForEach-Object { $_ -replace 'DATA_DIR=.*', 'DATA_DIR=%data_dir%' } | Set-Content .env"

powershell -Command "(Get-Content .env) | ForEach-Object { $_ -replace 'DEBUG=.*', 'DEBUG=%debug_setting%' } | Set-Content .env"

powershell -Command "(Get-Content .env) | ForEach-Object { $_ -replace 'LOG_LEVEL=.*', 'LOG_LEVEL=%log_level%' } | Set-Content .env"

REM Generate a random secret key
powershell -Command "$secretKey = [System.Web.Security.Membership]::GeneratePassword(50, 10); (Get-Content .env) | ForEach-Object { $_ -replace 'SECRET_KEY=.*', ('SECRET_KEY=' + $secretKey) } | Set-Content .env" 2>nul

echo Configuration updated successfully!
echo.

echo ============================================
echo Configuration Summary
echo ============================================
echo.
echo Database: %db_user%@%db_host%:%db_port%/%db_name%
echo Data Directory: %data_dir%
echo Debug Mode: %debug_setting%
echo OpenAI API: %openai_key%
echo.

echo Would you like to:
echo 1. View the complete .env file
echo 2. Test database connection
echo 3. Continue to database initialization
echo 4. Exit
echo.
set /p choice="Choose an option (1-4): "

if "%choice%"=="1" (
    echo.
    echo Current .env file contents:
    echo ============================================
    type .env
    echo ============================================
    pause
) else if "%choice%"=="2" (
    echo.
    echo Testing database connection...
    call venv\Scripts\activate.bat 2>nul
    python -c "import psycopg2; conn = psycopg2.connect(host='%db_host%', port='%db_port%', user='%db_user%', password='%db_password%', database='postgres'); print('✓ PostgreSQL connection successful'); conn.close()" 2>nul
    if %errorlevel% neq 0 (
        echo ✗ Database connection failed. Please check your settings.
        echo.
        echo Common issues:
        echo - PostgreSQL service not running
        echo - Incorrect password
        echo - Database server not accessible
        pause
    ) else (
        echo ✓ Database connection successful!
        echo.
        set /p create_db="Create JDDB database? (Y/n): "
        if /i not "%create_db%"=="n" (
            python -c "import psycopg2; conn = psycopg2.connect(host='%db_host%', port='%db_port%', user='%db_user%', password='%db_password%', database='postgres'); conn.autocommit = True; cur = conn.cursor(); cur.execute('CREATE DATABASE \"%db_name%\" OWNER \"%db_user%\"'); print('✓ Database %db_name% created'); conn.close()" 2>nul
            if %errorlevel% neq 0 (
                echo Note: Database may already exist or creation failed.
            )
        )
        pause
    )
) else if "%choice%"=="3" (
    echo.
    echo Running database initialization...
    call init-db.bat
) else (
    goto :end
)

:end
echo.
echo Environment configuration complete!
echo.
echo Next steps:
echo 1. Run init-db.bat to set up the database
echo 2. Run server.bat to start the backend
echo 3. Run frontend.bat to start the web interface
echo.
pause