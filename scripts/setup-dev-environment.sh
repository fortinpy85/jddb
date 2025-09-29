#!/bin/bash
# Automated development environment setup script for JDDB
# This script sets up the complete development environment for Phase 2 features

set -e  # Exit on any error

echo "🚀 JDDB Development Environment Setup"
echo "=====================================​"
echo ""

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running on Windows (Git Bash/WSL)
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" ]]; then
    IS_WINDOWS=true
    log "Detected Windows environment (Git Bash)"
else
    IS_WINDOWS=false
    log "Detected Unix-like environment"
fi

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
echo ""
log "Checking prerequisites..."

# Check Node.js and Bun
if ! command_exists node; then
    error "Node.js is required but not installed. Please install Node.js first."
    exit 1
fi

if ! command_exists bun; then
    error "Bun is required but not installed. Please install Bun first."
    exit 1
fi

# Check Python
if ! command_exists python3 && ! command_exists python; then
    error "Python is required but not installed. Please install Python 3.12+ first."
    exit 1
fi

# Check Poetry
if ! command_exists poetry; then
    error "Poetry is required but not installed. Please install Poetry first."
    exit 1
fi

# Check PostgreSQL
if ! command_exists psql; then
    warn "PostgreSQL CLI tools not found. Make sure PostgreSQL is installed and accessible."
fi

# Check Redis (optional)
if ! command_exists redis-cli; then
    warn "Redis CLI not found. Redis is recommended for caching and sessions."
fi

log "✅ Prerequisites check completed"

# Setup backend environment
echo ""
log "Setting up backend environment..."

cd backend
if [ ! -f ".env" ]; then
    log "Creating backend .env file..."
    cat > .env << EOF
# Database Configuration
DATABASE_URL=postgresql://postgres:password@localhost:5432/jddb_dev

# OpenAI Configuration
OPENAI_API_KEY=your-openai-api-key-here

# Application Configuration
DEBUG=true
LOG_LEVEL=INFO
API_HOST=0.0.0.0
API_PORT=8000

# CORS Configuration
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

# Redis Configuration (optional)
REDIS_URL=redis://localhost:6379/0

# JWT Configuration
JWT_SECRET_KEY=$(openssl rand -base64 32 2>/dev/null || echo "change-this-secret-key-in-production")

# Phase 2 Configuration
ENABLE_WEBSOCKETS=true
ENABLE_COLLABORATION=true
EOF
    warn "Please update the .env file with your actual configuration values"
else
    log "Backend .env file already exists"
fi

# Install backend dependencies
log "Installing backend dependencies..."
poetry install

# Setup database
log "Initializing database..."
if poetry run alembic current 2>/dev/null; then
    log "Database already initialized"
else
    log "Running database migrations..."
    poetry run alembic upgrade head
fi

# Seed development data
log "Seeding development data..."
if poetry run python scripts/simple_seed.py; then
    log "✅ Database seeded successfully"
else
    warn "Database seeding failed, continuing..."
fi

cd ..

# Setup frontend environment
echo ""
log "Setting up frontend environment..."

if [ ! -f ".env.local" ]; then
    log "Creating frontend .env.local file..."
    cat > .env.local << EOF
# API Configuration
NEXT_PUBLIC_API_URL=http://localhost:8000/api

# Development Configuration
NODE_ENV=development

# Feature Flags
NEXT_PUBLIC_ENABLE_WEBSOCKETS=true
NEXT_PUBLIC_ENABLE_COLLABORATION=true
NEXT_PUBLIC_ENABLE_TRANSLATION=true
EOF
else
    log "Frontend .env.local file already exists"
fi

# Install frontend dependencies
log "Installing frontend dependencies..."
bun install

# Create VS Code workspace configuration
echo ""
log "Setting up VS Code workspace..."

if [ ! -f "jddb.code-workspace" ]; then
    cat > jddb.code-workspace << EOF
{
    "folders": [
        {
            "name": "JDDB Root",
            "path": "."
        },
        {
            "name": "Backend",
            "path": "./backend"
        },
        {
            "name": "Frontend",
            "path": ".",
            "excludeFilterInExplorer": {
                "backend": true,
                "docs": true,
                "scripts": true,
                ".git": true,
                "node_modules": true
            }
        }
    ],
    "settings": {
        "python.defaultInterpreterPath": "./backend/.venv/bin/python",
        "python.terminal.activateEnvironment": true,
        "typescript.preferences.quoteStyle": "double",
        "editor.formatOnSave": true,
        "editor.codeActionsOnSave": {
            "source.fixAll.eslint": true
        },
        "files.exclude": {
            "**/__pycache__": true,
            "**/*.pyc": true,
            "**/node_modules": true,
            "**/.git": true,
            "**/venv": true,
            "**/.venv": true
        },
        "search.exclude": {
            "**/node_modules": true,
            "**/venv": true,
            "**/.venv": true,
            "**/dist": true,
            "**/.next": true
        }
    },
    "extensions": {
        "recommendations": [
            "ms-python.python",
            "ms-python.black-formatter",
            "bradlc.vscode-tailwindcss",
            "esbenp.prettier-vscode",
            "ms-vscode.vscode-typescript-next",
            "ms-vscode.vscode-json",
            "redhat.vscode-yaml"
        ]
    }
}
EOF
    log "✅ VS Code workspace configuration created"
else
    log "VS Code workspace already exists"
fi

# Create development scripts
echo ""
log "Creating development helper scripts..."

# Backend development script
cat > dev-backend.sh << 'EOF'
#!/bin/bash
echo "🚀 Starting JDDB Backend Development Server..."
cd backend
poetry run uvicorn jd_ingestion.api.main:app --host 0.0.0.0 --port 8000 --reload --log-level info
EOF
chmod +x dev-backend.sh

# Frontend development script
cat > dev-frontend.sh << 'EOF'
#!/bin/bash
echo "🚀 Starting JDDB Frontend Development Server..."
bun dev
EOF
chmod +x dev-frontend.sh

# Full development script
cat > dev-full.sh << 'EOF'
#!/bin/bash
echo "🚀 Starting JDDB Full Development Environment..."

# Function to cleanup background processes
cleanup() {
    echo "Stopping development servers..."
    jobs -p | xargs -r kill
    exit 0
}

# Trap cleanup function on script exit
trap cleanup EXIT

# Start backend in background
echo "Starting backend server..."
cd backend
poetry run uvicorn jd_ingestion.api.main:app --host 0.0.0.0 --port 8000 --reload --log-level info &
BACKEND_PID=$!
cd ..

# Give backend time to start
sleep 3

# Start frontend in background
echo "Starting frontend server..."
bun dev &
FRONTEND_PID=$!

echo ""
echo "✅ Development environment started!"
echo "📱 Frontend: http://localhost:3000"
echo "🔧 Backend API: http://localhost:8000"
echo "📚 API Docs: http://localhost:8000/api/docs"
echo ""
echo "Press Ctrl+C to stop all servers"

# Wait for processes
wait
EOF
chmod +x dev-full.sh

# Test the setup
echo ""
log "Testing the development setup..."

# Test backend
cd backend
if poetry run python -c "from jd_ingestion.api.main import app; print('✅ Backend imports successfully')"; then
    log "✅ Backend setup verified"
else
    error "❌ Backend setup failed"
fi
cd ..

# Test frontend
if bun run build --dry-run >/dev/null 2>&1; then
    log "✅ Frontend setup verified"
else
    warn "Frontend build test failed, but continuing..."
fi

# Final success message
echo ""
echo -e "${GREEN}🎉 Development Environment Setup Complete!${NC}"
echo ""
echo "📋 Next Steps:"
echo "  1. Update backend/.env with your actual database and API credentials"
echo "  2. Start development: ./dev-full.sh"
echo "  3. Or start individually:"
echo "     - Backend only: ./dev-backend.sh"
echo "     - Frontend only: ./dev-frontend.sh"
echo ""
echo "📚 Documentation:"
echo "  - API Documentation: http://localhost:8000/api/docs"
echo "  - WebSocket Testing: http://localhost:8000/api/docs#/websocket"
echo "  - Frontend: http://localhost:3000"
echo ""
echo "🔧 Development Tools:"
echo "  - VS Code workspace: Open jddb.code-workspace"
echo "  - Backend tests: cd backend && poetry run pytest"
echo "  - Frontend tests: bun test"
echo "  - Database seeding: cd backend && poetry run make seed-phase2"
echo ""
echo -e "${BLUE}Happy coding! 🚀${NC}"
