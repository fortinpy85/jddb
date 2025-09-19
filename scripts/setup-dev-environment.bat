@echo off
REM Automated development environment setup script for JDDB (Windows)
REM This script sets up the complete development environment for Phase 2 features

echo 🚀 JDDB Development Environment Setup
echo =====================================
echo.

REM Check prerequisites
echo [INFO] Checking prerequisites...

where node >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Node.js is required but not installed. Please install Node.js first.
    exit /b 1
)

where bun >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Bun is required but not installed. Please install Bun first.
    exit /b 1
)

where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is required but not installed. Please install Python 3.12+ first.
    exit /b 1
)

where poetry >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Poetry is required but not installed. Please install Poetry first.
    exit /b 1
)

where psql >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARN] PostgreSQL CLI tools not found. Make sure PostgreSQL is installed and accessible.
)

echo [INFO] ✅ Prerequisites check completed

REM Setup backend environment
echo.
echo [INFO] Setting up backend environment...

cd backend

if not exist ".env" (
    echo [INFO] Creating backend .env file...
    (
        echo # Database Configuration
        echo DATABASE_URL=postgresql://postgres:password@localhost:5432/jddb_dev
        echo.
        echo # OpenAI Configuration
        echo OPENAI_API_KEY=your-openai-api-key-here
        echo.
        echo # Application Configuration
        echo DEBUG=true
        echo LOG_LEVEL=INFO
        echo API_HOST=0.0.0.0
        echo API_PORT=8000
        echo.
        echo # CORS Configuration
        echo CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
        echo.
        echo # Redis Configuration (optional^)
        echo REDIS_URL=redis://localhost:6379/0
        echo.
        echo # JWT Configuration
        echo JWT_SECRET_KEY=change-this-secret-key-in-production
        echo.
        echo # Phase 2 Configuration
        echo ENABLE_WEBSOCKETS=true
        echo ENABLE_COLLABORATION=true
    ) > .env
    echo [WARN] Please update the .env file with your actual configuration values
) else (
    echo [INFO] Backend .env file already exists
)

REM Install backend dependencies
echo [INFO] Installing backend dependencies...
poetry install

REM Setup database
echo [INFO] Initializing database...
poetry run alembic current >nul 2>&1
if %errorlevel% equ 0 (
    echo [INFO] Database already initialized
) else (
    echo [INFO] Running database migrations...
    poetry run alembic upgrade head
)

REM Seed development data
echo [INFO] Seeding development data...
poetry run python scripts/simple_seed.py
if %errorlevel% equ 0 (
    echo [INFO] ✅ Database seeded successfully
) else (
    echo [WARN] Database seeding failed, continuing...
)

cd ..

REM Setup frontend environment
echo.
echo [INFO] Setting up frontend environment...

if not exist ".env.local" (
    echo [INFO] Creating frontend .env.local file...
    (
        echo # API Configuration
        echo NEXT_PUBLIC_API_URL=http://localhost:8000/api
        echo.
        echo # Development Configuration
        echo NODE_ENV=development
        echo.
        echo # Feature Flags
        echo NEXT_PUBLIC_ENABLE_WEBSOCKETS=true
        echo NEXT_PUBLIC_ENABLE_COLLABORATION=true
        echo NEXT_PUBLIC_ENABLE_TRANSLATION=true
    ) > .env.local
) else (
    echo [INFO] Frontend .env.local file already exists
)

REM Install frontend dependencies
echo [INFO] Installing frontend dependencies...
bun install

REM Create VS Code workspace configuration
echo.
echo [INFO] Setting up VS Code workspace...

if not exist "jddb.code-workspace" (
    (
        echo {
        echo     "folders": [
        echo         {
        echo             "name": "JDDB Root",
        echo             "path": "."
        echo         },
        echo         {
        echo             "name": "Backend",
        echo             "path": "./backend"
        echo         },
        echo         {
        echo             "name": "Frontend",
        echo             "path": "."
        echo         }
        echo     ],
        echo     "settings": {
        echo         "python.defaultInterpreterPath": "./backend/.venv/Scripts/python.exe",
        echo         "python.terminal.activateEnvironment": true,
        echo         "typescript.preferences.quoteStyle": "double",
        echo         "editor.formatOnSave": true,
        echo         "files.exclude": {
        echo             "**/__pycache__": true,
        echo             "**/*.pyc": true,
        echo             "**/node_modules": true,
        echo             "**/.git": true,
        echo             "**/venv": true,
        echo             "**/.venv": true
        echo         }
        echo     },
        echo     "extensions": {
        echo         "recommendations": [
        echo             "ms-python.python",
        echo             "ms-python.black-formatter",
        echo             "bradlc.vscode-tailwindcss",
        echo             "esbenp.prettier-vscode",
        echo             "ms-vscode.vscode-typescript-next"
        echo         ]
        echo     }
        echo }
    ) > jddb.code-workspace
    echo [INFO] ✅ VS Code workspace configuration created
) else (
    echo [INFO] VS Code workspace already exists
)

REM Create development scripts
echo.
echo [INFO] Creating development helper scripts...

REM Backend development script
(
    echo @echo off
    echo echo 🚀 Starting JDDB Backend Development Server...
    echo cd backend
    echo poetry run uvicorn jd_ingestion.api.main:app --host 0.0.0.0 --port 8000 --reload --log-level info
) > dev-backend.bat

REM Frontend development script
(
    echo @echo off
    echo echo 🚀 Starting JDDB Frontend Development Server...
    echo bun dev
) > dev-frontend.bat

REM Test the setup
echo.
echo [INFO] Testing the development setup...

cd backend
poetry run python -c "from jd_ingestion.api.main import app; print('✅ Backend imports successfully')" >nul 2>&1
if %errorlevel% equ 0 (
    echo [INFO] ✅ Backend setup verified
) else (
    echo [ERROR] ❌ Backend setup failed
)
cd ..

REM Final success message
echo.
echo 🎉 Development Environment Setup Complete!
echo.
echo 📋 Next Steps:
echo   1. Update backend\.env with your actual database and API credentials
echo   2. Start development servers:
echo      - Backend: dev-backend.bat
echo      - Frontend: dev-frontend.bat
echo.
echo 📚 Documentation:
echo   - API Documentation: http://localhost:8000/api/docs
echo   - WebSocket Testing: http://localhost:8000/api/docs#/websocket
echo   - Frontend: http://localhost:3000
echo.
echo 🔧 Development Tools:
echo   - VS Code workspace: Open jddb.code-workspace
echo   - Backend tests: cd backend ^&^& poetry run pytest
echo   - Frontend tests: bun test
echo   - Database seeding: cd backend ^&^& poetry run make seed-phase2
echo.
echo Happy coding! 🚀

pause