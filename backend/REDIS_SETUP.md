# Redis Setup Guide for JDDB

## Overview

Redis is used in JDDB for:
- **Celery Task Queue**: Async job processing broker and result backend
- **Caching**: Performance optimization for API responses
- **Rate Limiting**: API request throttling (future feature)
- **Session Management**: User session storage (future feature)

**Note**: Redis is **optional** for development. The application will run without it, but background tasks and caching features will be disabled.

## Status

Currently, Redis is **not running**, resulting in these non-critical warnings:
```
Error 10061 connecting to localhost:6379. No connection could be made because the target machine actively refused it.
```

The application continues to work, but:
- Celery background tasks are unavailable
- Cache operations fall back to direct database queries
- Performance may be slightly slower

## Installation Options

### Option 1: Windows (WSL2 - Recommended)

Redis doesn't run natively on Windows. Use WSL2 for best compatibility:

```bash
# Install WSL2 if not already installed
wsl --install

# Inside WSL2, install Redis
sudo apt update
sudo apt install redis-server

# Start Redis server
sudo service redis-server start

# Verify it's running
redis-cli ping
# Should return: PONG
```

**Access from Windows**: Redis in WSL2 is accessible from Windows at `localhost:6379`

### Option 2: Windows (Docker - Alternative)

```bash
# Run Redis in Docker container
docker run --name jddb-redis -p 6379:6379 -d redis:7-alpine

# Verify it's running
docker ps
docker exec -it jddb-redis redis-cli ping
# Should return: PONG

# Stop Redis when done
docker stop jddb-redis

# Remove container when no longer needed
docker rm jddb-redis
```

### Option 3: Windows (Native - Not Recommended)

Microsoft's fork of Redis (deprecated but functional):

```bash
# Download from: https://github.com/microsoftarchive/redis/releases
# Or use Chocolatey:
choco install redis-64

# Start Redis
redis-server
```

**Note**: This version is outdated (3.2.100) and no longer maintained.

### Option 4: Linux/Mac

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install redis-server
sudo systemctl start redis-server
sudo systemctl enable redis-server

# macOS with Homebrew
brew install redis
brew services start redis

# Verify
redis-cli ping
# Should return: PONG
```

## Configuration

### Current Configuration (.env)

```env
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

### For Remote Redis

If Redis is on another machine:

```env
REDIS_URL=redis://username:password@hostname:6379/0
CELERY_BROKER_URL=redis://username:password@hostname:6379/0
CELERY_RESULT_BACKEND=redis://username:password@hostname:6379/0
```

### For Docker Redis with Authentication

```bash
# Run Redis with password
docker run --name jddb-redis \
  -p 6379:6379 \
  -d redis:7-alpine \
  redis-server --requirepass your_secure_password

# Update .env
REDIS_URL=redis://:your_secure_password@localhost:6379/0
```

## Verification

### Test Connection

```bash
# From command line
redis-cli ping

# Or with Python
python -c "import redis; r=redis.Redis(host='localhost', port=6379, db=0); print(r.ping())"
```

### Check Backend Logs

Once Redis is running, restart the backend and verify:

```bash
cd backend
set -a && source .env && set +a && poetry run uvicorn src.jd_ingestion.api.main:app --host 0.0.0.0 --port 8000 --reload
```

Look for:
```
✅ Cache service initialized with Redis
```

Instead of:
```
❌ Failed to initialize Redis monitoring error='Error 10061...'
```

## Starting Backend with Redis

### Current Method (with environment loading fix)

```bash
cd C:\jddb\backend
set -a && source .env && set +a && poetry run uvicorn src.jd_ingestion.api.main:app --host 0.0.0.0 --port 8000 --reload
```

**Why this is needed**: Pydantic-settings requires environment variables to be explicitly loaded on some systems. The `set -a && source .env && set +a` ensures all `.env` variables are exported to the environment before starting the server.

### Alternative: Use python-dotenv directly

Add to the top of `backend/src/jd_ingestion/api/main.py`:

```python
from dotenv import load_dotenv
load_dotenv()  # Load .env before anything else
```

Then start normally:
```bash
cd backend
poetry run uvicorn src.jd_ingestion.api.main:app --host 0.0.0.0 --port 8000 --reload
```

## Troubleshooting

### Error: "Connection refused" (10061)

**Cause**: Redis is not running
**Solution**: Start Redis using one of the installation methods above

### Error: "Authentication required"

**Cause**: Redis has password protection enabled
**Solution**: Add password to REDIS_URL: `redis://:password@localhost:6379/0`

### Error: "Could not connect to Redis at localhost:6379"

**Cause**: Redis is running on different port or host
**Solution**:
1. Find Redis port: `redis-cli ping` or `netstat -an | grep 6379`
2. Update REDIS_URL in .env with correct host:port

### Backend still shows "jd_user" errors

**Cause**: Environment variables not being loaded
**Solution**: Use the explicit environment loading command:
```bash
cd backend
set -a && source .env && set +a && poetry run uvicorn src.jd_ingestion.api.main:app --host 0.0.0.0 --port 8000 --reload
```

## Background Task Processing

### Starting Celery Workers

Once Redis is running, start Celery workers for background tasks:

```bash
cd backend

# Development (single worker)
poetry run celery -A src.jd_ingestion.tasks.celery_app worker --loglevel=info --pool=solo

# Production (multiple workers)
poetry run celery -A src.jd_ingestion.tasks.celery_app worker --loglevel=info --concurrency=4
```

### Monitoring Celery Tasks

```bash
# Flower - Web-based monitoring
poetry run celery -A src.jd_ingestion.tasks.celery_app flower

# Access at: http://localhost:5555
```

## Performance Impact

### With Redis
- API responses cached (50-90% faster for repeated queries)
- Background task processing for large operations
- Reduced database load
- Improved scalability

### Without Redis
- All queries hit database directly
- No background task processing
- Slightly increased latency (~50-200ms per request)
- **Still fully functional for development**

## Production Recommendations

For production deployment:

1. **Use Redis Cluster or Sentinel** for high availability
2. **Enable persistence**: Configure RDB snapshots and AOF logging
3. **Set memory limits**: Configure `maxmemory` and eviction policies
4. **Enable authentication**: Always use passwords in production
5. **Monitor performance**: Use Redis INFO and Celery Flower
6. **Backup regularly**: Export RDB files for disaster recovery

Example production Redis configuration:

```conf
# redis.conf
bind 0.0.0.0
protected-mode yes
requirepass your_strong_password_here
maxmemory 2gb
maxmemory-policy allkeys-lru
save 900 1
save 300 10
save 60 10000
appendonly yes
appendfsync everysec
```

## Summary

- **Development**: Redis is optional but recommended
- **Current Status**: Application works without Redis, but with warnings
- **Quick Start**: Use Docker or WSL2 for fastest setup
- **Backend Fix**: Use explicit environment loading command to fix database credentials
- **Production**: Redis is required for optimal performance and scalability
