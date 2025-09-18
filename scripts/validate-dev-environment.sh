#!/bin/bash

# Development Environment Validation Script for JDDB
# This script validates that all required dependencies and services are properly configured

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Status counters
CHECKS_PASSED=0
CHECKS_FAILED=0
WARNINGS=0

# Function to print status
print_status() {
    local status=$1
    local message=$2
    case $status in
        "PASS")
            echo -e "${GREEN}✅ PASS${NC}: $message"
            ((CHECKS_PASSED++))
            ;;
        "FAIL")
            echo -e "${RED}❌ FAIL${NC}: $message"
            ((CHECKS_FAILED++))
            ;;
        "WARN")
            echo -e "${YELLOW}⚠️  WARN${NC}: $message"
            ((WARNINGS++))
            ;;
        "INFO")
            echo -e "${BLUE}ℹ️  INFO${NC}: $message"
            ;;
    esac
}

# Function to check command availability
check_command() {
    local cmd=$1
    local name=$2
    local required=${3:-true}

    if command -v "$cmd" >/dev/null 2>&1; then
        local version=$($cmd --version 2>/dev/null | head -n1 || echo "unknown")
        print_status "PASS" "$name is installed ($version)"
        return 0
    else
        if [ "$required" = true ]; then
            print_status "FAIL" "$name is not installed or not in PATH"
        else
            print_status "WARN" "$name is not installed (optional)"
        fi
        return 1
    fi
}

# Function to check service connectivity
check_service() {
    local host=$1
    local port=$2
    local name=$3
    local timeout=${4:-5}

    if timeout "$timeout" bash -c "</dev/tcp/$host/$port" 2>/dev/null; then
        print_status "PASS" "$name is accessible at $host:$port"
        return 0
    else
        print_status "FAIL" "$name is not accessible at $host:$port"
        return 1
    fi
}

# Function to check file exists
check_file() {
    local file=$1
    local description=$2
    local required=${3:-true}

    if [ -f "$file" ]; then
        print_status "PASS" "$description exists at $file"
        return 0
    else
        if [ "$required" = true ]; then
            print_status "FAIL" "$description not found at $file"
        else
            print_status "WARN" "$description not found at $file (optional)"
        fi
        return 1
    fi
}

# Function to check directory
check_directory() {
    local dir=$1
    local description=$2
    local required=${3:-true}

    if [ -d "$dir" ]; then
        print_status "PASS" "$description exists at $dir"
        return 0
    else
        if [ "$required" = true ]; then
            print_status "FAIL" "$description not found at $dir"
        else
            print_status "WARN" "$description not found at $dir (optional)"
        fi
        return 1
    fi
}

echo "🔍 JDDB Development Environment Validation"
echo "========================================"
echo ""

# Check if we're in the project root
print_status "INFO" "Checking project structure..."
if [ ! -f "package.json" ] || [ ! -f "backend/pyproject.toml" ]; then
    print_status "FAIL" "Not in JDDB project root directory"
    exit 1
fi

# Basic system tools
echo ""
print_status "INFO" "Checking system tools..."
check_command "git" "Git"
check_command "curl" "cURL"
check_command "make" "Make" false

# Python and backend dependencies
echo ""
print_status "INFO" "Checking Python and backend tools..."
check_command "python" "Python"
check_command "pip" "pip"
check_command "poetry" "Poetry" false

# Check Python version
if command -v python >/dev/null 2>&1; then
    PYTHON_VERSION=$(python --version 2>&1 | cut -d' ' -f2)
    if python -c "import sys; exit(0 if sys.version_info >= (3, 9) else 1)" 2>/dev/null; then
        print_status "PASS" "Python version $PYTHON_VERSION is supported (>=3.9)"
    else
        print_status "FAIL" "Python version $PYTHON_VERSION is too old (requires >=3.9)"
    fi
fi

# Node.js and frontend dependencies
echo ""
print_status "INFO" "Checking Node.js and frontend tools..."
check_command "node" "Node.js"
check_command "bun" "Bun"
check_command "npm" "npm" false

# Check Node.js version
if command -v node >/dev/null 2>&1; then
    NODE_VERSION=$(node --version | cut -d'v' -f2)
    if node -e "process.exit(process.version.match(/v(\d+)/)[1] >= 18 ? 0 : 1)" 2>/dev/null; then
        print_status "PASS" "Node.js version $NODE_VERSION is supported (>=18)"
    else
        print_status "FAIL" "Node.js version $NODE_VERSION is too old (requires >=18)"
    fi
fi

# Database and services
echo ""
print_status "INFO" "Checking database and service connectivity..."
check_service "localhost" "5432" "PostgreSQL" 3
check_service "localhost" "6379" "Redis" 3

# Project files and directories
echo ""
print_status "INFO" "Checking project files and directories..."
check_file "package.json" "Frontend package.json"
check_file "backend/pyproject.toml" "Backend pyproject.toml"
check_file ".env.local" "Frontend environment file" false
check_file "backend/.env" "Backend environment file" false
check_directory "backend/venv" "Python virtual environment" false
check_directory "node_modules" "Frontend node_modules" false
check_directory "backend/.venv" "Poetry virtual environment" false

# Git configuration
echo ""
print_status "INFO" "Checking Git configuration..."
if git config user.name >/dev/null 2>&1; then
    print_status "PASS" "Git user.name configured: $(git config user.name)"
else
    print_status "WARN" "Git user.name not configured"
fi

if git config user.email >/dev/null 2>&1; then
    print_status "PASS" "Git user.email configured: $(git config user.email)"
else
    print_status "WARN" "Git user.email not configured"
fi

# Backend-specific checks
echo ""
print_status "INFO" "Checking backend configuration..."

# Check if virtual environment is activated or available
if [ -n "$VIRTUAL_ENV" ]; then
    print_status "PASS" "Python virtual environment is activated"
elif [ -d "backend/venv" ]; then
    print_status "WARN" "Virtual environment exists but not activated"
elif [ -d "backend/.venv" ]; then
    print_status "WARN" "Poetry virtual environment exists but not activated"
else
    print_status "FAIL" "No Python virtual environment found"
fi

# Check critical Python packages (if virtual env is available)
if [ -n "$VIRTUAL_ENV" ] || [ -d "backend/venv" ] || [ -d "backend/.venv" ]; then
    print_status "INFO" "Checking Python packages..."

    # Activate virtual environment if not already active
    if [ -z "$VIRTUAL_ENV" ]; then
        if [ -f "backend/venv/Scripts/activate" ]; then
            source backend/venv/Scripts/activate 2>/dev/null || true
        elif [ -f "backend/venv/bin/activate" ]; then
            source backend/venv/bin/activate 2>/dev/null || true
        fi
    fi

    # Check for key packages
    for pkg in fastapi uvicorn sqlalchemy psycopg2 alembic pytest; do
        if python -c "import $pkg" 2>/dev/null; then
            print_status "PASS" "Python package '$pkg' is available"
        else
            print_status "FAIL" "Python package '$pkg' is not installed"
        fi
    done
fi

# Frontend-specific checks
echo ""
print_status "INFO" "Checking frontend configuration..."

if [ -d "node_modules" ]; then
    print_status "PASS" "Frontend dependencies installed"

    # Check for key packages
    for pkg in react typescript tailwindcss; do
        if [ -d "node_modules/$pkg" ]; then
            print_status "PASS" "Frontend package '$pkg' is installed"
        else
            print_status "WARN" "Frontend package '$pkg' not found"
        fi
    done
else
    print_status "FAIL" "Frontend dependencies not installed (run 'bun install')"
fi

# Database connection test
echo ""
print_status "INFO" "Testing database connectivity..."
if command -v psql >/dev/null 2>&1; then
    # Try to connect to default database
    if psql -h localhost -p 5432 -U postgres -d postgres -c "SELECT 1;" >/dev/null 2>&1; then
        print_status "PASS" "PostgreSQL connection successful"
    else
        print_status "WARN" "Could not connect to PostgreSQL with default credentials"
    fi
else
    print_status "WARN" "psql client not available for testing"
fi

# API endpoints test (if backend is running)
echo ""
print_status "INFO" "Testing API endpoints..."
if curl -f -s http://localhost:8000/health >/dev/null 2>&1; then
    print_status "PASS" "Backend API is responding at http://localhost:8000"
else
    print_status "WARN" "Backend API not running at http://localhost:8000"
fi

if curl -f -s http://localhost:3000 >/dev/null 2>&1; then
    print_status "PASS" "Frontend is responding at http://localhost:3000"
else
    print_status "WARN" "Frontend not running at http://localhost:3000"
fi

# Summary
echo ""
echo "========================================"
echo "🏁 Validation Summary"
echo "========================================"
echo -e "✅ Checks passed: ${GREEN}$CHECKS_PASSED${NC}"
echo -e "❌ Checks failed: ${RED}$CHECKS_FAILED${NC}"
echo -e "⚠️  Warnings: ${YELLOW}$WARNINGS${NC}"
echo ""

if [ $CHECKS_FAILED -eq 0 ]; then
    echo -e "${GREEN}🎉 Environment validation successful!${NC}"
    echo "Your development environment is ready for JDDB development."

    if [ $WARNINGS -gt 0 ]; then
        echo ""
        echo -e "${YELLOW}Note: There are $WARNINGS warnings that might affect some features.${NC}"
        echo "Consider addressing them for the best development experience."
    fi
else
    echo -e "${RED}❌ Environment validation failed!${NC}"
    echo "Please address the failed checks before continuing development."
    echo ""
    echo "🔧 Common solutions:"
    echo "   • Install missing dependencies"
    echo "   • Start required services (PostgreSQL, Redis)"
    echo "   • Activate virtual environment"
    echo "   • Run 'bun install' for frontend dependencies"
    echo "   • Run 'pip install -r requirements.txt' for backend dependencies"
fi

echo ""
echo "📚 For setup instructions, see:"
echo "   • README.md"
echo "   • docs/setup/WINDOWS_QUICKSTART.md"
echo "   • CLAUDE.md"

exit $CHECKS_FAILED