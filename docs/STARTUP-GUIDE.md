# JDDB Application Startup Guide

Comprehensive guide for starting the JDDB (Job Description Database) application with improved startup scripts and troubleshooting procedures.

## Quick Start

### Option 1: Start Everything at Once (Recommended)
```bash
start-all.bat
```
This launches both backend and frontend in separate windows.

### Option 2: Start Services Individually
```bash
# Terminal 1 - Backend
server.bat

# Terminal 2 - Frontend
frontend.bat
```

## Startup Scripts Overview

### 📋 Available Scripts

| Script | Purpose | Ports Used |
|--------|---------|------------|
| `server.bat` | Start FastAPI backend server | 8000 |
| `frontend.bat` | Start Vite frontend dev server | 3006 (auto-increments if busy) |
| `start-all.bat` | Launch both services together | 8000, 3006 |
| `cleanup.bat` | Kill orphaned processes on ports | 8000, 3006 |

## Detailed Script Descriptions

### server.bat - Backend Server

**Features:**
- ✅ Poetry installation check
- ✅ Port 8000 availability verification
- ✅ Dependency installation check (auto-install if missing)
- ✅ Environment configuration validation (.env file)
- ✅ Comprehensive error messages with solutions

**What it does:**
1. Verifies Poetry is installed and accessible
2. Checks if running from correct directory
3. Verifies port 8000 is available
4. Ensures Poetry dependencies are installed
5. Validates `.env` file exists in `backend/` directory
6. Starts FastAPI server with auto-reload via `dev_server.py`

**Access Points:**
- API Server: http://localhost:8000
- API Documentation: http://localhost:8000/api/docs
- OpenAPI Schema: http://localhost:8000/openapi.json

---

### frontend.bat - Frontend Server

**Features:**
- ✅ Node.js and npm installation checks
- ✅ Port 3006 availability detection (warns if busy)
- ✅ Dependency installation check (auto-install if missing)
- ✅ Auto-creates `.env.local` if missing
- ✅ Vite auto-port-increment handling

**What it does:**
1. Verifies Node.js and npm are installed
2. Checks if running from correct directory
3. Ensures npm dependencies are installed in `node_modules/`
4. Validates or creates `.env.local` with API URL
5. Checks port 3006 availability (warns if busy, Vite will auto-increment)
6. Starts Vite development server

**Access Points:**
- Frontend App: http://localhost:3006 (or next available port)
- Vite automatically opens browser

---

### start-all.bat - Unified Launcher

**Features:**
- ✅ Prerequisite checks (Poetry, Node.js)
- ✅ Port availability verification for both services
- ✅ Launches services in separate windows for easy monitoring
- ✅ 3-second delay between backend/frontend for proper initialization
- ✅ User confirmation if ports are occupied

**What it does:**
1. Validates all prerequisites (Poetry, Node.js)
2. Checks directory structure (backend/, package.json)
3. Verifies port 8000 is available (prompts if not)
4. Starts backend in new window via `server.bat`
5. Waits 3 seconds for backend initialization
6. Starts frontend in new window via `frontend.bat`
7. Displays access URLs for both services

**Advantages:**
- Single command to launch entire stack
- Separate windows allow monitoring both services
- Proper initialization sequence (backend first)
- Easy to stop individual services (close window)

---

### cleanup.bat - Process Cleanup Utility

**Features:**
- ✅ Scans ports 8000 and 3006 for listening processes
- ✅ Displays process IDs (PIDs) before termination
- ✅ User confirmation before killing processes
- ✅ Verifies ports are freed after cleanup
- ✅ Works with or without admin privileges (warns if needed)

**What it does:**
1. Scans for processes listening on port 8000 (backend)
2. Scans for processes listening on port 3006 (frontend)
3. Displays found PIDs and prompts for confirmation
4. Terminates processes using `taskkill /F`
5. Verifies ports are now available
6. Reports success/failure for each termination

**When to use:**
- Ports are occupied by orphaned processes
- Startup scripts report port conflicts
- Previous servers didn't shut down cleanly
- Need to free ports for fresh start

**Note:** Some processes may require administrator privileges to terminate.

---

## Prerequisites

### Required Software

| Software | Version | Purpose | Installation |
|----------|---------|---------|--------------|
| **Python** | 3.11+ | Backend runtime | https://python.org |
| **Poetry** | 2.0+ | Python dependency manager | https://python-poetry.org |
| **Node.js** | 18+ | Frontend runtime | https://nodejs.org |
| **npm** | 9+ | JavaScript package manager | Included with Node.js |
| **PostgreSQL** | 14+ | Database | https://postgresql.org |

### Verification Commands

```bash
# Check Python
python --version

# Check Poetry
poetry --version

# Check Node.js
node --version

# Check npm
npm --version

# Check PostgreSQL
psql --version
```

---

## Configuration Files

### Backend Configuration: `backend/.env`

Required environment variables:
```env
# Database
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/JDDB  # pragma: allowlist secret
DATABASE_SYNC_URL=postgresql://user:password@localhost:5432/JDDB  # pragma: allowlist secret

# Redis (optional for background tasks)
REDIS_URL=redis://localhost:6379/0

# OpenAI (for AI features)
OPENAI_API_KEY=sk-proj-...

# Application
DEBUG=True
LOG_LEVEL=INFO
SECRET_KEY=your-secret-key

# File Processing
DATA_DIR=C:/JDDB/data

# API Settings
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=1

# CORS (multiple frontend ports supported)
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:3006
```

### Frontend Configuration: `.env.local`

Required environment variables:
```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api
```

**Note:** `frontend.bat` automatically creates this file with default values if missing.

---

## First-Time Setup

### 1. Backend Setup

```bash
# Navigate to backend directory
cd backend

# Install dependencies with Poetry
poetry install --no-root

# Initialize database
poetry run python scripts/init_db.py

# Create sample data (optional)
poetry run python scripts/sample_data.py

# Return to project root
cd ..
```

### 2. Frontend Setup

```bash
# In project root (where package.json is located)

# Install dependencies
npm install

# Verify installation
npm list --depth=0
```

### 3. Database Setup

Ensure PostgreSQL is running and create the database:

```sql
-- Connect to PostgreSQL
psql -U postgres

-- Create database
CREATE DATABASE JDDB;

-- Create user (if needed)
CREATE USER barre WITH PASSWORD 'admin';  -- pragma: allowlist secret

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE JDDB TO barre;
```

---

## Troubleshooting

### Port Already in Use

**Problem:** `Port 8000 is already in use` or `Port 3006 is already in use`

**Solutions:**

1. **Use cleanup script:**
   ```bash
   cleanup.bat
   ```

2. **Manual port check:**
   ```bash
   # Check what's using port 8000
   netstat -ano | findstr ":8000"

   # Kill process by PID
   taskkill /F /PID <process_id>
   ```

3. **Use different port:**
   - Backend: Edit `backend/.env` → `API_PORT=8001`
   - Frontend: Vite automatically increments (3007, 3008, etc.)

---

### Poetry Not Found

**Problem:** `Poetry is not installed or not in PATH`

**Solutions:**

1. **Install Poetry:**
   ```bash
   # Windows PowerShell
   (Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | py -
   ```

2. **Add to PATH:**
   ```
   %APPDATA%\Python\Scripts
   ```

3. **Verify installation:**
   ```bash
   poetry --version
   ```

---

### Dependencies Not Installed

**Problem:** `Dependencies not installed` warning

**Solutions:**

1. **Let script auto-install:**
   - Both `server.bat` and `frontend.bat` auto-install missing dependencies

2. **Manual installation:**
   ```bash
   # Backend
   cd backend && poetry install --no-root

   # Frontend
   npm install
   ```

---

### Database Connection Error

**Problem:** Backend fails with database connection error

**Solutions:**

1. **Verify PostgreSQL is running:**
   ```bash
   # Windows services
   services.msc
   # Look for "postgresql-x64-14" or similar
   ```

2. **Check connection string in `backend/.env`:**
   ```env
   DATABASE_URL=postgresql+asyncpg://barre:admin@localhost:5432/JDDB  # pragma: allowlist secret
   ```

3. **Test connection:**
   ```bash
   psql -U barre -d JDDB
   ```

4. **Initialize database:**
   ```bash
   cd backend
   poetry run python scripts/init_db.py
   ```

---

### Frontend Can't Connect to Backend

**Problem:** Frontend shows API connection errors

**Solutions:**

1. **Verify backend is running:**
   - Check http://localhost:8000/api/docs loads

2. **Check `.env.local` configuration:**
   ```env
   NEXT_PUBLIC_API_URL=http://localhost:8000/api
   ```

3. **Verify CORS settings in `backend/.env`:**
   ```env
   CORS_ALLOWED_ORIGINS=http://localhost:3006
   ```

4. **Check browser console:**
   - F12 → Console tab for detailed error messages

---

### Module Not Found Errors

**Problem:** Python import errors or JavaScript module errors

**Solutions:**

1. **Backend - Reinstall dependencies:**
   ```bash
   cd backend
   poetry install --no-root
   poetry show  # Verify installation
   ```

2. **Frontend - Clear cache and reinstall:**
   ```bash
   rm -rf node_modules package-lock.json
   npm install
   ```

3. **Frontend - Clear Vite cache:**
   ```bash
   rm -rf node_modules/.vite
   npm run dev
   ```

---

### Multiple Node Processes Running

**Problem:** Many node.exe processes consuming resources

**Solutions:**

1. **Use cleanup script:**
   ```bash
   cleanup.bat
   ```

2. **Kill all node processes (careful!):**
   ```bash
   taskkill /F /IM node.exe
   ```

3. **Check for zombie processes:**
   ```bash
   tasklist | findstr node
   ```

---

## Health Checks

### Verify Backend Health

```bash
# Option 1: Browser
# Open http://localhost:8000/api/docs

# Option 2: Command line
curl http://localhost:8000/api/docs

# Option 3: Check API status endpoint
curl http://localhost:8000/api/jobs/status
```

### Verify Frontend Health

```bash
# Option 1: Browser
# Open http://localhost:3006

# Option 2: Check if server is responding
curl http://localhost:3006
```

### Verify Database Connection

```bash
cd backend
poetry run python -c "from jd_ingestion.database.connection import get_db_session; print('✅ Database connected')"
```

---

## Performance Tips

### Backend Optimization

1. **Increase workers for production:**
   ```env
   # backend/.env
   API_WORKERS=4  # Increase from 1
   ```

2. **Optimize Poetry dependency resolution:**
   ```bash
   poetry lock --no-update
   poetry install --no-root --no-dev  # Production only
   ```

3. **Enable PostgreSQL query logging:**
   ```env
   LOG_LEVEL=DEBUG
   ```

### Frontend Optimization

1. **Use production build for testing:**
   ```bash
   npm run build
   npm run start  # Preview production build
   ```

2. **Clear Vite cache if slow:**
   ```bash
   rm -rf node_modules/.vite
   ```

3. **Optimize node_modules:**
   ```bash
   npm dedupe
   ```

---

## Development Workflow

### Typical Development Session

```bash
# 1. Start both services
start-all.bat

# 2. Develop in your IDE
# - Backend: backend/src/jd_ingestion/
# - Frontend: src/

# 3. Changes auto-reload
# - Backend: Uvicorn auto-reload
# - Frontend: Vite HMR

# 4. Run tests
cd backend && poetry run pytest tests/
npm test

# 5. Stop services
# Close terminal windows or Ctrl+C in each
```

### Making Configuration Changes

**Backend configuration changes:**
```bash
# Edit backend/.env
# Restart backend server (Ctrl+C + rerun server.bat)
```

**Frontend configuration changes:**
```bash
# Edit .env.local
# Restart frontend server (Ctrl+C + rerun frontend.bat)
```

---

## Production Deployment

**Note:** These scripts are for **development only**. For production deployment:

1. **Backend:**
   - Use production-grade WSGI server (Gunicorn, uWSGI)
   - Set `DEBUG=False` in environment
   - Use proper secret key management
   - Configure reverse proxy (Nginx, Caddy)

2. **Frontend:**
   - Build production bundle: `npm run build`
   - Serve with production server (Nginx, Caddy)
   - Configure proper CORS and CSP headers

3. **Database:**
   - Use managed PostgreSQL service
   - Enable connection pooling
   - Configure backups and monitoring

---

## Additional Resources

### Documentation
- Backend API Documentation: http://localhost:8000/api/docs (when running)
- Project README: [README.md](README.md)
- Architecture Guide: [DEVELOPMENT-GUIDE.md](DEVELOPMENT-GUIDE.md)

### Useful Commands

```bash
# Backend commands (from backend/ directory)
make help          # Show all available commands
make test          # Run test suite
make lint          # Run linting
make format        # Format code
make db-init       # Initialize database

# Frontend commands (from root directory)
npm run dev        # Development server
npm run build      # Production build
npm run start      # Preview production build
npm test           # Run unit tests
npm run test:e2e   # Run E2E tests
npm run lint       # Run linting
```

---

## Summary

### Key Improvements

✅ **Automated Checks:** All scripts verify prerequisites before running
✅ **Error Handling:** Clear error messages with actionable solutions
✅ **Port Management:** Automatic port conflict detection and resolution
✅ **Dependency Management:** Auto-installation of missing dependencies
✅ **Process Cleanup:** Utility to kill orphaned processes
✅ **Unified Launcher:** Single command to start entire stack
✅ **Health Verification:** Scripts confirm services are running properly

### Quick Reference

| Task | Command |
|------|---------|
| Start everything | `start-all.bat` |
| Start backend only | `server.bat` |
| Start frontend only | `frontend.bat` |
| Clean up ports | `cleanup.bat` |
| Check backend health | Open http://localhost:8000/api/docs |
| Check frontend health | Open http://localhost:3006 |

---

**Last Updated:** 2025-10-17
**Maintained By:** JDDB Development Team
